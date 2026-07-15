package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"regexp"
	"strings"
)

// NewRouter wires up the Docker Engine API endpoints the shim supports.
// Routes are version-agnostic: /_ping, /v1.43/_ping, /v999.99/_ping all
// hit the same handler. This matches real dockerd behavior.
//
// Tier 1 (solve path): ping, version, info, images/json, containers/create,
//                      containers/{id}/start, containers/{id}/logs.
// Tier 2 (realism):    containers list/inspect/wait/remove, attach, exec,
//                      archive, image inspect, image pull sim.
// Tier 3 (stubs):      networks, volumes, events, swarm, plugins, services.
// Tier 4 (catch-all):  404 with Docker-shaped error + full request log.
type Router struct {
	store  *Store
	routes []route
}

type route struct {
	method  string
	pattern *regexp.Regexp
	handler http.HandlerFunc
}

// versioned strips an optional /v<major>.<minor> prefix so one regex matches
// both versioned and unversioned paths.
func versioned(p string) *regexp.Regexp {
	// allow /v1.43, /v1, /v99.99 etc.
	return regexp.MustCompile(`^(?:/v\d+(?:\.\d+)?)?` + p + `$`)
}

func NewRouter(s *Store) *Router {
	r := &Router{store: s}
	r.routes = []route{
		// --- Tier 1 ---
		{"GET", versioned(`/_ping`), r.ping},
		{"HEAD", versioned(`/_ping`), r.ping},
		{"GET", versioned(`/version`), r.version},
		{"GET", versioned(`/info`), r.info},
		{"GET", versioned(`/images/json`), r.imagesList},
		{"POST", versioned(`/containers/create`), r.containerCreate},
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/start`), r.containerStart},
		{"GET", versioned(`/containers/([a-zA-Z0-9_.-]+)/logs`), r.containerLogs},

		// --- Tier 2 ---
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/attach`), r.containerAttach},
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/exec`), r.containerExecCreate},
		{"POST", versioned(`/exec/([a-zA-Z0-9_.-]+)/start`), r.execStart},
		{"GET", versioned(`/exec/([a-zA-Z0-9_.-]+)/json`), r.execInspect},
		{"GET", versioned(`/containers/([a-zA-Z0-9_.-]+)/archive`), r.containerArchive},
		{"HEAD", versioned(`/containers/([a-zA-Z0-9_.-]+)/archive`), r.containerArchiveHead},
		{"GET", versioned(`/containers/json`), r.containersList},
		{"GET", versioned(`/containers/([a-zA-Z0-9_.-]+)/json`), r.containerInspect},
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/wait`), r.containerWait},
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/stop`), r.containerStop},
		{"POST", versioned(`/containers/([a-zA-Z0-9_.-]+)/kill`), r.containerStop},
		{"DELETE", versioned(`/containers/([a-zA-Z0-9_.-]+)`), r.containerRemove},
		{"GET", versioned(`/images/([^/]+)/json`), r.imageInspect},
		{"POST", versioned(`/images/create`), r.imagePull},

		// --- Tier 3 stubs ---
		{"GET", versioned(`/networks`), r.emptyList},
		{"GET", versioned(`/volumes`), r.emptyVolumes},
		{"GET", versioned(`/events`), r.events},
		{"GET", versioned(`/swarm`), r.notInSwarm},
		{"GET", versioned(`/plugins`), r.emptyList},
		{"GET", versioned(`/services`), r.emptyList},
		{"GET", versioned(`/tasks`), r.emptyList},
		{"GET", versioned(`/nodes`), r.emptyList},
		{"GET", versioned(`/secrets`), r.emptyList},
		{"GET", versioned(`/configs`), r.emptyList},
		{"GET", versioned(`/system/df`), r.systemDF},
	}
	return r
}

// ServeHTTP implements http.Handler. Dispatches to the matching route,
// falling back to the Tier-4 catch-all which logs the full request body
// for post-playtest gap analysis.
func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	// Log every request at INFO — priceless for QA.
	log.Printf("req %s %s ua=%q", req.Method, req.URL.Path, req.UserAgent())

	// Standard Docker response headers. Version lies; it's what real
	// Docker 27.0.3 returns, which avoids version-skew warnings from
	// recent CLIs.
	w.Header().Set("Api-Version", "1.45")
	w.Header().Set("Docker-Experimental", "false")
	w.Header().Set("Ostype", "linux")
	w.Header().Set("Server", "Docker/27.0.3 (linux)")

	for _, route := range r.routes {
		if route.method != req.Method {
			continue
		}
		m := route.pattern.FindStringSubmatch(req.URL.Path)
		if m == nil {
			continue
		}
		// Stash captured path groups for handlers.
		req = req.WithContext(withPathParams(req.Context(), m[1:]))
		route.handler(w, req)
		return
	}

	// Tier 4: catch-all. Log body for analysis, return Docker-shaped 404.
	bodyPeek := ""
	if req.Body != nil {
		buf, _ := io.ReadAll(io.LimitReader(req.Body, 4096))
		_ = req.Body.Close()
		bodyPeek = strings.ReplaceAll(string(buf), "\n", "\\n")
	}
	log.Printf("unhandled %s %s body=%q — returning 404", req.Method, req.URL.Path, bodyPeek)

	writeError(w, http.StatusNotFound, "page not found")
}

// writeError sends a Docker-shaped error response.
func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"message": msg})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
