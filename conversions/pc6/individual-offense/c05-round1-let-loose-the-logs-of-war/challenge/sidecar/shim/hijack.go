package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// The /attach and /exec/start endpoints use HTTP connection hijacking to
// bypass the Go HTTP server's request/response cycle and stream raw bytes
// directly. Real Docker does this so clients can have true bidirectional
// communication with a container's stdio.
//
// Our shim executes Cmd synchronously in the create→start→logs path. For
// /attach we support the "output side" of the hijack (stream stdout/stderr
// back on the hijacked connection) so that `docker run image cmd` — which
// internally issues create → attach → start → wait → rm — works end-to-end.

// containerAttach handles POST /containers/{id}/attach. Called by `docker run`
// and `docker attach`.
//
// The wire protocol:
//   1. Client sends POST with Upgrade/Connection: tcp headers and
//      query params stdin/stdout/stderr/stream=1.
//   2. Server responds 101 Switching Protocols + Content-Type
//      application/vnd.docker.raw-stream (or .multiplexed-stream).
//   3. Server then writes framed output until the container exits.
//
// Because our execution is synchronous (runContainer is called by /start),
// attach has to wait for start to finish OR race-ahead of it. The `docker
// run` sequence is attach-first-then-start, so our attach blocks waiting
// for the container to transition to "exited" and then streams the captured
// buffers. Not strictly real-time, but indistinguishable for non-TTY cmds
// that print their output in a burst at the end.
func (r *Router) containerAttach(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}

	hj, ok := w.(http.Hijacker)
	if !ok {
		writeError(w, http.StatusInternalServerError, "hijacking unsupported")
		return
	}

	showStdout := req.URL.Query().Get("stdout") == "1" || req.URL.Query().Get("stdout") == "true"
	showStderr := req.URL.Query().Get("stderr") == "1" || req.URL.Query().Get("stderr") == "true"
	if !showStdout && !showStderr {
		showStdout, showStderr = true, true
	}

	conn, buf, err := hj.Hijack()
	if err != nil {
		logErr("hijack: %v", err)
		return
	}
	defer conn.Close()

	// Send the 101 switching protocols response. Match Docker's exact
	// header ordering — some clients are picky.
	contentType := "application/vnd.docker.multiplexed-stream"
	if c.Tty {
		contentType = "application/vnd.docker.raw-stream"
	}
	fmt.Fprintf(buf,
		"HTTP/1.1 101 UPGRADED\r\n"+
			"Content-Type: %s\r\n"+
			"Connection: Upgrade\r\n"+
			"Upgrade: tcp\r\n\r\n",
		contentType,
	)
	_ = buf.Flush()

	// Wait for the container to have finished running (or time out). The
	// shim executes synchronously in /start, so c.done will close once
	// start has been invoked and returned.
	select {
	case <-c.done:
	case <-time.After(maxWallTime + 5*time.Second):
	}

	// Flush captured output over the hijacked conn.
	if c.Tty {
		if showStdout {
			_, _ = buf.Write(c.Stdout)
		}
		if showStderr {
			_, _ = buf.Write(c.Stderr)
		}
	} else {
		if showStdout {
			writeFramed(buf, 1, c.Stdout)
		}
		if showStderr {
			writeFramed(buf, 2, c.Stderr)
		}
	}
	_ = buf.Flush()
}

// Exec create + start.

type execCreateSpec struct {
	AttachStdin  bool     `json:"AttachStdin"`
	AttachStdout bool     `json:"AttachStdout"`
	AttachStderr bool     `json:"AttachStderr"`
	Tty          bool     `json:"Tty"`
	Cmd          []string `json:"Cmd"`
	Env          []string `json:"Env"`
	Privileged   bool     `json:"Privileged"`
	User         string   `json:"User"`
	WorkingDir   string   `json:"WorkingDir"`
}

func (r *Router) containerExecCreate(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	target := r.store.Lookup(id)
	if target == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	var spec execCreateSpec
	if err := json.NewDecoder(io.LimitReader(req.Body, 1<<20)).Decode(&spec); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON: "+err.Error())
		return
	}
	if len(spec.Cmd) == 0 {
		writeError(w, http.StatusBadRequest, "Cmd is required")
		return
	}
	e := &Exec{
		ContainerID: target.ID,
		Cmd:         spec.Cmd,
		Env:         spec.Env,
		AttachOut:   spec.AttachStdout,
		AttachErr:   spec.AttachStderr,
		Tty:         spec.Tty,
	}
	r.store.AddExec(e)
	writeJSON(w, http.StatusCreated, map[string]string{"Id": e.ID})
}

type execStartSpec struct {
	Detach bool `json:"Detach"`
	Tty    bool `json:"Tty"`
}

func (r *Router) execStart(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	e := r.store.LookupExec(id)
	if e == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such exec instance: %s", id))
		return
	}
	var spec execStartSpec
	_ = json.NewDecoder(io.LimitReader(req.Body, 1<<16)).Decode(&spec)

	target := r.store.Lookup(e.ContainerID)
	if target == nil {
		writeError(w, http.StatusNotFound, "target container vanished")
		return
	}

	if spec.Detach {
		go runExec(target, e)
		w.WriteHeader(http.StatusOK)
		return
	}

	// Attached exec: hijack the connection, run exec synchronously, stream
	// output back in Docker's framed format.
	hj, ok := w.(http.Hijacker)
	if !ok {
		writeError(w, http.StatusInternalServerError, "hijacking unsupported")
		return
	}
	conn, buf, err := hj.Hijack()
	if err != nil {
		return
	}
	defer conn.Close()

	contentType := "application/vnd.docker.multiplexed-stream"
	if e.Tty {
		contentType = "application/vnd.docker.raw-stream"
	}
	fmt.Fprintf(buf,
		"HTTP/1.1 101 UPGRADED\r\n"+
			"Content-Type: %s\r\n"+
			"Connection: Upgrade\r\n"+
			"Upgrade: tcp\r\n\r\n",
		contentType,
	)
	_ = buf.Flush()

	runExec(target, e)

	if e.Tty {
		if e.AttachOut {
			_, _ = buf.Write(e.Stdout)
		}
		if e.AttachErr {
			_, _ = buf.Write(e.Stderr)
		}
	} else {
		if e.AttachOut || !e.AttachErr {
			writeFramed(buf, 1, e.Stdout)
		}
		if e.AttachErr {
			writeFramed(buf, 2, e.Stderr)
		}
	}
	_ = buf.Flush()
}

func (r *Router) execInspect(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	e := r.store.LookupExec(id)
	if e == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such exec instance: %s", id))
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ID":          e.ID,
		"Running":     e.Running,
		"ExitCode":    e.ExitCode,
		"ContainerID": e.ContainerID,
		"ProcessConfig": map[string]any{
			"privileged": false,
			"user":       "",
			"tty":        e.Tty,
			"entrypoint": firstOr(e.Cmd, ""),
			"arguments":  e.Cmd[min(1, len(e.Cmd)):],
		},
		"OpenStdin":  false,
		"OpenStderr": e.AttachErr,
		"OpenStdout": e.AttachOut,
	})
}

