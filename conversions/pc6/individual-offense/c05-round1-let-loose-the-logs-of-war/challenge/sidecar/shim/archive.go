package main

import (
	"archive/tar"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// containerArchive handles GET /containers/{id}/archive?path=...
//
// This is the endpoint `docker cp container:/path -` hits. Returns a tar
// stream of the requested path as it appears *inside* the container's
// staged rootfs. That rootfs already has the bind-mapped fakehost content,
// so `docker cp c:/host/home/user/TOKEN2.txt -` works naturally without
// needing create+start+logs at all. A shrewd competitor might find this
// path first.
func (r *Router) containerArchive(w http.ResponseWriter, req *http.Request) {
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("No such container: %s", id))
		return
	}
	reqPath := req.URL.Query().Get("path")
	if reqPath == "" {
		writeError(w, http.StatusBadRequest, "path required")
		return
	}
	// Resolve the requested path within the container's rootfs. Prevent
	// escape via "../" or absolute-path trickery.
	cleaned := filepath.Clean("/" + reqPath)
	abs := filepath.Join(c.Rootfs, cleaned)
	if !strings.HasPrefix(abs, filepath.Clean(c.Rootfs)) {
		writeError(w, http.StatusBadRequest, "path traversal rejected")
		return
	}
	info, err := os.Stat(abs)
	if err != nil {
		writeError(w, http.StatusNotFound, fmt.Sprintf("Could not find the file %s in container %s", reqPath, id))
		return
	}

	// Docker's X-Docker-Container-Path-Stat response header is a
	// base64'd JSON blob describing the top-level entry.
	stat := map[string]any{
		"name":     filepath.Base(abs),
		"size":     info.Size(),
		"mode":     info.Mode(),
		"mtime":    info.ModTime().Format("2006-01-02T15:04:05Z07:00"),
		"linkTarget": "",
	}
	statJSON, _ := json.Marshal(stat)
	w.Header().Set("X-Docker-Container-Path-Stat", base64.StdEncoding.EncodeToString(statJSON))
	w.Header().Set("Content-Type", "application/x-tar")
	w.WriteHeader(http.StatusOK)

	tw := tar.NewWriter(w)
	defer tw.Close()

	base := filepath.Dir(abs)
	_ = filepath.Walk(abs, func(path string, fi os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(base, path)
		hdr, herr := tar.FileInfoHeader(fi, "")
		if herr != nil {
			return nil
		}
		hdr.Name = rel
		if err := tw.WriteHeader(hdr); err != nil {
			return err
		}
		if fi.Mode().IsRegular() {
			f, err := os.Open(path)
			if err != nil {
				return nil
			}
			defer f.Close()
			_, _ = io.Copy(tw, f)
		}
		return nil
	})
}

func (r *Router) containerArchiveHead(w http.ResponseWriter, req *http.Request) {
	// HEAD variant for `docker cp` to stat before downloading. Same logic,
	// no body written.
	id := pathParams(req.Context())[0]
	c := r.store.Lookup(id)
	if c == nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	reqPath := req.URL.Query().Get("path")
	abs := filepath.Join(c.Rootfs, filepath.Clean("/"+reqPath))
	info, err := os.Stat(abs)
	if err != nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	stat := map[string]any{
		"name": filepath.Base(abs), "size": info.Size(),
		"mode": info.Mode(), "mtime": info.ModTime().Format("2006-01-02T15:04:05Z07:00"),
	}
	statJSON, _ := json.Marshal(stat)
	w.Header().Set("X-Docker-Container-Path-Stat", base64.StdEncoding.EncodeToString(statJSON))
	w.WriteHeader(http.StatusOK)
}
