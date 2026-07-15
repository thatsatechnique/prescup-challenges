package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// applyBind implements the subset of `docker -v src:dst[:ro]` semantics
// that matters for this challenge.
//
// Important: the "source" path the competitor names is interpreted as
// a path on the FAKE host (i.e., the sidecar's fakehost template), NOT on
// the sidecar's real root filesystem. This is the entire isolation
// boundary — regardless of what a competitor asks to mount, they can
// only ever see files we've put in the fakehost template.
//
// Given a bind spec like "/:/host", we:
//   - resolve src ("/") within the fakehost template root
//   - resolve dst ("/host") within the per-container rootfs
//   - cp -aR the resolved source into the resolved destination
func applyBind(fakeRoot, rootfs, spec string) error {
	parts := strings.Split(spec, ":")
	if len(parts) < 2 {
		return fmt.Errorf("malformed bind %q", spec)
	}
	src := parts[0]
	dst := parts[1]

	// Normalize + canonicalize src and dst (prevent "../" escapes).
	src = filepath.Clean("/" + src)
	dst = filepath.Clean("/" + dst)

	// Resolve src onto the fakehost template root
	realSrc := filepath.Join(fakeRoot, src)
	// Reject paths that canonicalize outside fakeRoot
	if !strings.HasPrefix(filepath.Clean(realSrc), filepath.Clean(fakeRoot)) {
		return fmt.Errorf("bind source %q escapes fakehost root", src)
	}
	if _, err := os.Stat(realSrc); err != nil {
		return fmt.Errorf("bind source %q not present in fakehost: %w", src, err)
	}

	// Resolve dst inside the per-container rootfs
	realDst := filepath.Join(rootfs, dst)
	if !strings.HasPrefix(filepath.Clean(realDst), filepath.Clean(rootfs)) {
		return fmt.Errorf("bind target %q escapes rootfs", dst)
	}

	// Remove any pre-existing dst (from the template) so the bind
	// "overrides" it, matching Docker's bind-mount semantics.
	_ = os.RemoveAll(realDst)
	if err := os.MkdirAll(filepath.Dir(realDst), 0755); err != nil {
		return err
	}

	cp := exec.Command("cp", "-a", realSrc+"/.", realDst+"/")
	// Handle file (not dir) case: cp -a SRC DST
	if st, err := os.Stat(realSrc); err == nil && !st.IsDir() {
		cp = exec.Command("cp", "-a", realSrc, realDst)
	}
	if out, err := cp.CombinedOutput(); err != nil {
		return fmt.Errorf("cp failed: %w (%s)", err, strings.TrimSpace(string(out)))
	}
	return nil
}

func wrapErr(prefix string, err error, detail string) error {
	if detail == "" {
		return fmt.Errorf("%s: %w", prefix, err)
	}
	return fmt.Errorf("%s: %w (%s)", prefix, err, strings.TrimSpace(detail))
}
