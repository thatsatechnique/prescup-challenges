package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"runtime"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Tier 1 handlers — the solve path
// ---------------------------------------------------------------------------

func (r *Router) ping(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Pragma", "no-cache")
	w.WriteHeader(http.StatusOK)
	if req.Method != "HEAD" {
		_, _ = io.WriteString(w, "OK")
	}
}

func (r *Router) version(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"Platform":      map[string]string{"Name": "Docker Engine - Community"},
		"Components":    dockerVersionComponents(),
		"Version":       "27.0.3",
		"ApiVersion":    "1.45",
		"MinAPIVersion": "1.24",
		"GitCommit":     "662f78c",
		"GoVersion":     runtime.Version(),
		"Os":            "linux",
		"Arch":          "amd64",
		"KernelVersion": "6.1.0-18-amd64",
		"BuildTime":     "2024-06-18T19:32:00.000000000+00:00",
		"Experimental":  false,
	})
}

func dockerVersionComponents() []map[string]any {
	return []map[string]any{
		{"Name": "Engine", "Version": "27.0.3", "Details": map[string]string{
			"ApiVersion":    "1.45",
			"Arch":          "amd64",
			"BuildTime":     "2024-06-18T19:32:00.000000000+00:00",
			"Experimental":  "false",
			"GitCommit":     "662f78c",
			"GoVersion":     "go1.21.11",
			"KernelVersion": "6.1.0-18-amd64",
			"MinAPIVersion": "1.24",
			"Os":            "linux",
		}},
		{"Name": "containerd", "Version": "1.7.18", "Details": map[string]string{"GitCommit": "ae71819c4f5e67bb4d5ae76a6b735f29cc25774e"}},
		{"Name": "runc", "Version": "1.7.18", "Details": map[string]string{"GitCommit": "v1.1.13-0-g58aa9203"}},
		{"Name": "docker-init", "Version": "0.19.0", "Details": map[string]string{"GitCommit": "de40ad0"}},
	}
}

func (r *Router) info(w http.ResponseWriter, _ *http.Request) {
	// Plausible-looking Docker info. Enough fields to satisfy the CLI's
	// `docker info` output without needing us to track them for real.
	writeJSON(w, http.StatusOK, map[string]any{
		"ID":                 "YLCT:FAKE:SHIM:HOST:XXXX:YYYY:ZZZZ:AAAA:BBBB:CCCC:DDDD:EEEE",
		"Containers":         len(r.store.List(true)),
		"ContainersRunning":  len(r.store.List(false)),
		"ContainersPaused":   0,
		"ContainersStopped":  0,
		"Images":             3,
		"Driver":             "overlay2",
		"DriverStatus":       [][]string{{"Backing Filesystem", "extfs"}, {"Supports d_type", "true"}},
		"Plugins":            map[string]any{"Volume": []string{"local"}, "Network": []string{"bridge", "host", "overlay"}, "Log": []string{"json-file", "local"}},
		"MemoryLimit":        true,
		"SwapLimit":          true,
		"KernelMemory":       true,
		"CpuCfsPeriod":       true,
		"CpuCfsQuota":        true,
		"CPUShares":          true,
		"CPUSet":             true,
		"PidsLimit":          true,
		"IPv4Forwarding":     true,
		"BridgeNfIptables":   true,
		"BridgeNfIp6tables":  true,
		"Debug":              false,
		"NFd":                42,
		"OomKillDisable":     true,
		"NGoroutines":        66,
		"SystemTime":         time.Now().UTC().Format(time.RFC3339Nano),
		"LoggingDriver":      "json-file",
		"CgroupDriver":       "systemd",
		"CgroupVersion":      "2",
		"NEventsListener":    0,
		"KernelVersion":      "6.1.0-18-amd64",
		"OperatingSystem":    "Ubuntu 22.04.3 LTS",
		"OSType":             "linux",
		"Architecture":       "x86_64",
		"IndexServerAddress": "https://index.docker.io/v1/",
		"ServerVersion":      "27.0.3",
		"Name":               "dockerhost",
		"NCPU":               4,
		"MemTotal":           8_388_608_000,
		"DockerRootDir":      "/var/lib/docker",
		"HttpProxy":          "",
		"HttpsProxy":         "",
		"NoProxy":            "",
		"Labels":             []string{},
		"ExperimentalBuild":  false,
		"Runtimes":           map[string]any{"runc": map[string]string{"path": "runc"}},
		"DefaultRuntime":     "runc",
		"LiveRestoreEnabled": false,
		"SecurityOptions":    []string{"name=seccomp,profile=builtin", "name=cgroupns"},
	})
}

// localImage describes one cached image on the fake host.
type localImage struct {
	ID       string
	RepoTags []string
	Digest   string
	Created  int64 // offset in seconds from now
	Size     int64
}

// localImages is the authoritative set of images available on the fake
// host. Both /images/json and /containers/create validate against this
// list. Matches the original legacy challenge: three Tomcat versions.
var localImages = []localImage{
	{
		ID:       "sha256:6c6b0cf3a6b1abc98ef8b43cde2d872a60c9a45e8ff77f5210ba3f42a19f1e21",
		RepoTags: []string{"tomcat:latest"},
		Digest:   "tomcat@sha256:6c6b0cf3a6b1abc98ef8b43cde2d872a60c9a45e8ff77f5210ba3f42a19f1e21",
		Created:  -86400 * 7,
		Size:     477_000_000,
	},
	{
		ID:       "sha256:a19b0ebcd65c1b9b9f3f42ea6e34d2f6f75cf8891120cf4c8ed6b0a19bd8a9a3",
		RepoTags: []string{"tomcat:10"},
		Digest:   "tomcat@sha256:a19b0ebcd65c1b9b9f3f42ea6e34d2f6f75cf8891120cf4c8ed6b0a19bd8a9a3",
		Created:  -86400 * 14,
		Size:     461_000_000,
	},
	{
		ID:       "sha256:d2c94e90c10c5ca8e5d82d52eca32aa1c9afeabdc9eaa4df28c8710b9e5bcb16",
		RepoTags: []string{"tomcat:9"},
		Digest:   "tomcat@sha256:d2c94e90c10c5ca8e5d82d52eca32aa1c9afeabdc9eaa4df28c8710b9e5bcb16",
		Created:  -86400 * 21,
		Size:     452_000_000,
	},
}

// resolveImage checks whether a given image reference (tag, name, name:tag,
// or sha256 ID/prefix) matches any locally cached image. Returns the matched
// image or nil. Mirrors real Docker's resolution order:
//   - exact tag match ("tomcat:latest")
//   - bare name defaults to :latest ("tomcat" → "tomcat:latest")
//   - sha256 ID or ID prefix
func resolveImage(ref string) *localImage {
	// Exact tag match
	for i := range localImages {
		for _, tag := range localImages[i].RepoTags {
			if tag == ref {
				return &localImages[i]
			}
		}
	}
	// Bare name → append :latest
	if !strings.Contains(ref, ":") && !strings.HasPrefix(ref, "sha256:") {
		for i := range localImages {
			for _, tag := range localImages[i].RepoTags {
				if tag == ref+":latest" {
					return &localImages[i]
				}
			}
		}
	}
	// SHA256 ID or prefix
	for i := range localImages {
		if localImages[i].ID == ref {
			return &localImages[i]
		}
		// Strip "sha256:" prefix for comparison
		id := strings.TrimPrefix(localImages[i].ID, "sha256:")
		refID := strings.TrimPrefix(ref, "sha256:")
		if len(refID) >= 6 && strings.HasPrefix(id, refID) {
			return &localImages[i]
		}
	}
	return nil
}

func (r *Router) imagesList(w http.ResponseWriter, _ *http.Request) {
	now := time.Now().Unix()
	out := make([]map[string]any, 0, len(localImages))
	for _, img := range localImages {
		out = append(out, map[string]any{
			"Id":          img.ID,
			"RepoTags":    img.RepoTags,
			"RepoDigests": []string{img.Digest},
			"Created":     now + img.Created,
			"Size":        img.Size,
			"VirtualSize": img.Size,
			"SharedSize":  -1,
			"Labels":      map[string]string{},
			"Containers":  -1,
		})
	}
	writeJSON(w, http.StatusOK, out)
}

// createSpec mirrors the subset of the Docker create body that we honor.
type createSpec struct {
	Image      string   `json:"Image"`
	Cmd        []string `json:"Cmd"`
	Entrypoint []string `json:"Entrypoint"`
	Env        []string `json:"Env"`
	WorkingDir string   `json:"WorkingDir"`
	Tty        bool     `json:"Tty"`
	HostConfig struct {
		Binds       []string `json:"Binds"`
		NetworkMode string   `json:"NetworkMode"`
		AutoRemove  bool     `json:"AutoRemove"`
		Privileged  bool     `json:"Privileged"`
	} `json:"HostConfig"`
}

func (r *Router) containerCreate(w http.ResponseWriter, req *http.Request) {
	defer req.Body.Close()
	var spec createSpec
	if err := json.NewDecoder(io.LimitReader(req.Body, 1<<20)).Decode(&spec); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body: "+err.Error())
		return
	}

	if spec.Image == "" {
		writeError(w, http.StatusBadRequest, "Image is required")
		return
	}

	// Validate image against the local cache. Real Docker on an
	// air-gapped host fails with "image not found locally" for any
	// image that wasn't pre-pulled. We replicate that behavior.
	img := resolveImage(spec.Image)
	if img == nil {
		writeError(w, http.StatusNotFound,
			fmt.Sprintf("No such image: %s: image not found locally and pull access is denied", spec.Image))
		return
	}

	// Honor ?name= query param if provided (docker run --name)
	name := req.URL.Query().Get("name")

	// Combine Entrypoint + Cmd the way Docker does.
	full := append([]string{}, spec.Entrypoint...)
	full = append(full, spec.Cmd...)

	c := &Container{
		Name:    name,
		Image:   spec.Image,
		Cmd:     full,
		Env:     spec.Env,
		Binds:   spec.HostConfig.Binds,
		Tty:     spec.Tty,
		WorkDir: spec.WorkingDir,
	}
	if err := r.store.Add(c); err != nil {
		logErr("container create: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to create container: "+err.Error())
		return
	}

	writeJSON(w, http.StatusCreated, map[string]any{
		"Id":       c.ID,
		"Warnings": []string{},
	})
}

func (r *Router) containerStart(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	if c.State == "running" || c.State == "exited" {
		// Docker returns 304 when the container is already in the target
		// state. Our containers are one-shot; once exited, re-starting is
		// a no-op rather than a restart (matches the ephemeral model).
		w.WriteHeader(http.StatusNotModified)
		return
	}
	// Kick off the execution synchronously so subsequent /logs gets output.
	// Real Docker's /start returns 204 immediately and the container runs
	// async; our commands are short-lived so synchronous is simpler and
	// closer to the natural latency the competitor expects.
	runContainer(c)

	// Matches real Docker's 204 No Content for successful start.
	w.WriteHeader(http.StatusNoContent)
}

// containerLogs returns the container's captured stdout/stderr.
// The Docker wire format multiplexes stdout/stderr with an 8-byte header
// per chunk:  [stream_type(1), 0, 0, 0, length_be32(4)] where stream_type
// is 1 for stdout and 2 for stderr. For Tty=true containers, output is
// streamed raw without framing.
func (r *Router) containerLogs(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}

	// Block briefly for the container to finish if it's still running.
	// The solve path does start -> logs back-to-back; real docker clients
	// use ?follow=1 for streaming. We don't implement follow, we just wait.
	select {
	case <-c.done:
	case <-time.After(maxWallTime + 2*time.Second):
	}

	showStdout := req.URL.Query().Get("stdout") == "1" || req.URL.Query().Get("stdout") == "true"
	showStderr := req.URL.Query().Get("stderr") == "1" || req.URL.Query().Get("stderr") == "true"
	if !showStdout && !showStderr {
		showStdout = true
	}

	if c.Tty {
		w.Header().Set("Content-Type", "application/vnd.docker.raw-stream")
		w.WriteHeader(http.StatusOK)
		if showStdout {
			_, _ = w.Write(c.Stdout)
		}
		if showStderr {
			_, _ = w.Write(c.Stderr)
		}
		return
	}

	w.Header().Set("Content-Type", "application/vnd.docker.multiplexed-stream")
	w.WriteHeader(http.StatusOK)
	if showStdout {
		writeFramed(w, 1, c.Stdout)
	}
	if showStderr {
		writeFramed(w, 2, c.Stderr)
	}
}

// writeFramed writes a Docker multiplexed-stream chunk.
func writeFramed(w io.Writer, stream byte, data []byte) {
	if len(data) == 0 {
		return
	}
	// Docker frames chunks by length; we frame everything as one chunk per
	// stream, which real Docker also does for small outputs.
	header := []byte{stream, 0, 0, 0,
		byte(len(data) >> 24),
		byte(len(data) >> 16),
		byte(len(data) >> 8),
		byte(len(data)),
	}
	_, _ = w.Write(header)
	_, _ = w.Write(data)
}

// ---------------------------------------------------------------------------
// Tier 2 handlers
// ---------------------------------------------------------------------------

func (r *Router) containersList(w http.ResponseWriter, req *http.Request) {
	all := req.URL.Query().Get("all") == "1" || req.URL.Query().Get("all") == "true"
	cs := r.store.List(all)
	out := make([]map[string]any, 0, len(cs))
	for _, c := range cs {
		out = append(out, map[string]any{
			"Id":              c.ID,
			"Names":           []string{"/" + firstNonEmpty(c.Name, c.ID[:12])},
			"Image":           c.Image,
			"ImageID":         "sha256:" + c.ID,
			"Command":         strings.Join(c.Cmd, " "),
			"Created":         c.Created.Unix(),
			"State":           c.State,
			"Status":          humanStatus(c),
			"Ports":           []any{},
			"Labels":          map[string]string{},
			"SizeRw":          0,
			"SizeRootFs":      0,
			"HostConfig":      map[string]any{"NetworkMode": "bridge"},
			"NetworkSettings": map[string]any{"Networks": map[string]any{}},
			"Mounts":          []any{},
		})
	}
	writeJSON(w, http.StatusOK, out)
}

func (r *Router) containerInspect(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"Id":      c.ID,
		"Created": c.Created.Format(time.RFC3339Nano),
		"Path":    firstOr(c.Cmd, "sh"),
		"Args":    c.Cmd[min(1, len(c.Cmd)):],
		"State": map[string]any{
			"Status":     c.State,
			"Running":    c.State == "running",
			"Paused":     false,
			"Restarting": false,
			"OOMKilled":  false,
			"Dead":       false,
			"Pid":        0,
			"ExitCode":   c.ExitCode,
			"Error":      "",
			"StartedAt":  c.Started.Format(time.RFC3339Nano),
			"FinishedAt": c.Exited.Format(time.RFC3339Nano),
		},
		"Image":    "sha256:" + c.ID,
		"Name":     "/" + firstNonEmpty(c.Name, c.ID[:12]),
		"Config":   map[string]any{"Image": c.Image, "Cmd": c.Cmd, "Env": c.Env, "Tty": c.Tty, "WorkingDir": c.WorkDir},
		"HostConfig": map[string]any{
			"Binds":       c.Binds,
			"NetworkMode": "bridge",
		},
		"NetworkSettings": map[string]any{"Networks": map[string]any{}},
		"Mounts":          []any{},
	})
}

func (r *Router) containerWait(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	// Block until the container finishes
	select {
	case <-c.done:
	case <-time.After(maxWallTime + 5*time.Second):
	}
	writeJSON(w, http.StatusOK, map[string]any{"StatusCode": c.ExitCode})
}

func (r *Router) containerStop(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	if c.cmd != nil && c.cmd.Process != nil {
		_ = c.cmd.Process.Kill()
	}
	w.WriteHeader(http.StatusNoContent)
}

func (r *Router) containerRemove(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	if !r.store.Remove(id) {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (r *Router) imageInspect(w http.ResponseWriter, req *http.Request) {
	name := pathParams(req.Context())[0]
	img := resolveImage(name)
	if img == nil {
		writeError(w, http.StatusNotFound,
			fmt.Sprintf("No such image: %s", name))
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"Id":            img.ID,
		"RepoTags":      img.RepoTags,
		"RepoDigests":   []string{img.Digest},
		"Parent":        "",
		"Comment":       "",
		"Created":       time.Now().Add(time.Duration(img.Created) * time.Second).Format(time.RFC3339Nano),
		"DockerVersion": "27.0.3",
		"Author":        "",
		"Architecture":  "amd64",
		"Os":            "linux",
		"Size":          img.Size,
		"VirtualSize":   img.Size,
		"Config": map[string]any{
			"Env":        []string{"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "CATALINA_HOME=/usr/local/tomcat"},
			"Cmd":        []string{"catalina.sh", "run"},
			"WorkingDir": "/usr/local/tomcat",
		},
	})
}

// imagePull simulates a pull attempt. On an air-gapped host (which is
// what this challenge simulates), pulls of images already in the local
// cache succeed with "already exists"; pulls of unknown images fail with
// a realistic error matching real Docker's behavior on disconnected hosts.
func (r *Router) imagePull(w http.ResponseWriter, req *http.Request) {
	from := firstNonEmpty(req.URL.Query().Get("fromImage"), "unknown")
	tag := firstNonEmpty(req.URL.Query().Get("tag"), "latest")
	ref := from + ":" + tag

	w.Header().Set("Content-Type", "application/json")
	flusher, _ := w.(http.Flusher)

	if img := resolveImage(ref); img != nil {
		// Image exists locally — return "up to date".
		w.WriteHeader(http.StatusOK)
		for _, line := range []string{
			`{"status":"Pulling from library/` + from + `","id":"` + tag + `"}`,
			`{"status":"Already exists","progressDetail":{},"id":"abc123"}`,
			`{"status":"Digest: ` + img.Digest + `"}`,
			`{"status":"Status: Image is up to date for ` + ref + `"}`,
		} {
			_, _ = io.WriteString(w, line+"\n")
			if flusher != nil {
				flusher.Flush()
			}
		}
		return
	}

	// Image not in local cache — fail like a disconnected host.
	w.WriteHeader(http.StatusNotFound)
	_, _ = io.WriteString(w,
		`{"message":"pull access denied for `+from+`, repository does not exist or may require 'docker login': denied: requested access to the resource is denied"}`+"\n")
}

// ---------------------------------------------------------------------------
// Tier 3 stubs
// ---------------------------------------------------------------------------

func (r *Router) emptyList(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, []any{})
}
func (r *Router) emptyVolumes(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"Volumes": []any{}, "Warnings": []string{}})
}
func (r *Router) notInSwarm(w http.ResponseWriter, _ *http.Request) {
	writeError(w, http.StatusServiceUnavailable, "This node is not a swarm manager. Use \"docker swarm init\" or \"docker swarm join\" to connect this node to swarm and try again.")
}
func (r *Router) systemDF(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"LayersSize": 0, "Images": []any{}, "Containers": []any{}, "Volumes": []any{}, "BuildCache": []any{},
	})
}

// events holds the connection open and sends nothing — matches dockerd when
// the daemon is idle. A client polling /events can Ctrl-C without error.
func (r *Router) events(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	<-req.Context().Done()
}

// ---------------------------------------------------------------------------
// Small utilities
// ---------------------------------------------------------------------------

func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

func firstOr(a []string, def string) string {
	if len(a) > 0 {
		return a[0]
	}
	return def
}

func humanStatus(c *Container) string {
	switch c.State {
	case "running":
		return fmt.Sprintf("Up %d seconds", int(time.Since(c.Started).Seconds()))
	case "exited":
		return fmt.Sprintf("Exited (%d) %d seconds ago", c.ExitCode, int(time.Since(c.Exited).Seconds()))
	default:
		return "Created"
	}
}
