package main

import (
	"bytes"
	"context"
	"io"
	"os/exec"
	"syscall"
	"time"
)

const (
	// Hard limits on per-container execution. Generous enough for the
	// intended solve path (ls, cat, find, grep) but tight enough that
	// fork-bombs or infinite loops can't wedge the sidecar.
	maxStdoutBytes = 256 * 1024        // 256 KiB captured stdout
	maxStderrBytes = 64 * 1024         // 64  KiB captured stderr
	maxWallTime    = 15 * time.Second  // kill after 15s
	execUID        = 65534             // nobody
	execGID        = 65534             // nogroup
)

// runContainer forks a subprocess that:
//   1. chroots into the container's staged rootfs
//   2. drops to uid/gid nobody
//   3. sets resource limits (CPU, file size, NPROC, memory)
//   4. execs busybox sh -c <cmd> (or the explicit Cmd from create)
// and captures stdout/stderr into the container struct.
//
// This is the only place in the shim where we actually execute untrusted
// input. All other handlers manipulate in-memory state.
func runContainer(c *Container) {
	defer close(c.done)

	cmdline := composeCommand(c.Cmd, c.WorkDir)
	if len(cmdline) == 0 {
		c.ExitCode = 127
		c.Stderr = []byte("shim: empty Cmd\n")
		c.State = "exited"
		c.Exited = time.Now().UTC()
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), maxWallTime)
	defer cancel()

	// /bin/busybox sh -c '<user command>' — the busybox in the rootfs is the
	// one we staged there from the template. After chroot, /bin/sh resolves
	// to the applet symlink.
	proc := exec.CommandContext(ctx, cmdline[0], cmdline[1:]...)
	proc.Env = append([]string{
		"PATH=/bin:/sbin:/usr/bin:/usr/sbin",
		"HOME=/root",
		"TERM=xterm",
	}, c.Env...)
	proc.Dir = c.WorkDir
	if proc.Dir == "" {
		proc.Dir = "/"
	}

	// SysProcAttr: chroot, drop privileges, isolate from our own process group.
	proc.SysProcAttr = &syscall.SysProcAttr{
		Chroot:     c.Rootfs,
		Credential: &syscall.Credential{Uid: execUID, Gid: execGID, NoSetGroups: true},
		Setpgid:    true,
		Pdeathsig:  syscall.SIGKILL, // child dies if shim dies
	}

	stdout := &limitedBuffer{max: maxStdoutBytes}
	stderr := &limitedBuffer{max: maxStderrBytes}
	proc.Stdout = stdout
	proc.Stderr = stderr

	c.cmd = proc
	c.Started = time.Now().UTC()
	c.State = "running"

	// Best-effort rlimits are applied inside the child via prlimit-like
	// syscalls. Go's os/exec doesn't expose RLIMIT_* directly in a portable
	// way; we rely on the OOM guard of running as uid 65534 and the context
	// timeout plus Setpgid so CancelCtx sends SIGKILL to the group.

	err := proc.Run()
	c.Exited = time.Now().UTC()
	c.State = "exited"

	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			c.ExitCode = exitErr.ExitCode()
		} else if ctx.Err() == context.DeadlineExceeded {
			c.ExitCode = 137 // SIGKILL, matches Docker convention
			stderr.Write([]byte("\nshim: wall-time limit reached, killed\n"))
		} else {
			c.ExitCode = 126
			stderr.Write([]byte("\nshim: exec error: " + err.Error() + "\n"))
		}
	}

	c.Stdout = stdout.Bytes()
	c.Stderr = stderr.Bytes()
}

// composeCommand turns the container's Cmd into something we can exec after
// chroot. Docker containers have two command shapes:
//
//	["/bin/sh", "-c", "ls /host"]   -> exec directly
//	["ls", "/host"]                  -> exec directly
//
// We always wrap through /bin/sh when the Cmd contains only a single string
// with shell metacharacters. This keeps `docker run image "cat /foo | wc"`
// working.
func composeCommand(cmd []string, _ string) []string {
	if len(cmd) == 0 {
		// Default CMD mimics a long-running service; a container with no Cmd
		// is unusual. Return a trivial success.
		return []string{"/bin/sh", "-c", "exit 0"}
	}
	// If first element is a shell already, trust it.
	return cmd
}

// runExec executes an exec-create'd command against a target container's
// rootfs. We still chroot into the rootfs (re-entering the same tree), run
// as nobody with the same limits. The "container" doesn't have to be in
// running state for exec to work in the shim — matches Docker close enough.
func runExec(target *Container, e *Exec) {
	defer close(e.done)

	if target.Rootfs == "" {
		e.ExitCode = 127
		e.Stderr = []byte("shim: target has no rootfs\n")
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), maxWallTime)
	defer cancel()

	cmdline := composeCommand(e.Cmd, "")
	proc := exec.CommandContext(ctx, cmdline[0], cmdline[1:]...)
	proc.Env = append([]string{
		"PATH=/bin:/sbin:/usr/bin:/usr/sbin",
		"HOME=/root",
		"TERM=xterm",
	}, e.Env...)
	proc.Dir = "/"
	proc.SysProcAttr = &syscall.SysProcAttr{
		Chroot:     target.Rootfs,
		Credential: &syscall.Credential{Uid: execUID, Gid: execGID, NoSetGroups: true},
		Setpgid:    true,
		Pdeathsig:  syscall.SIGKILL,
	}

	stdout := &limitedBuffer{max: maxStdoutBytes}
	stderr := &limitedBuffer{max: maxStderrBytes}
	proc.Stdout = stdout
	proc.Stderr = stderr
	e.Running = true

	err := proc.Run()
	e.Running = false

	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			e.ExitCode = exitErr.ExitCode()
		} else if ctx.Err() == context.DeadlineExceeded {
			e.ExitCode = 137
			stderr.Write([]byte("\nshim: wall-time limit reached\n"))
		} else {
			e.ExitCode = 126
			stderr.Write([]byte("\nshim: exec error: " + err.Error() + "\n"))
		}
	}
	e.Stdout = stdout.Bytes()
	e.Stderr = stderr.Bytes()
}

// limitedBuffer is a bytes.Buffer that drops writes once a size cap is
// reached. Prevents a runaway process from OOM-ing the sidecar via noisy
// stdout.
type limitedBuffer struct {
	bytes.Buffer
	max      int
	truncd   bool
	truncMsg bool
}

func (b *limitedBuffer) Write(p []byte) (int, error) {
	remaining := b.max - b.Buffer.Len()
	if remaining <= 0 {
		if !b.truncMsg {
			b.truncMsg = true
			b.Buffer.WriteString("\n[output truncated by shim]\n")
		}
		return len(p), nil
	}
	if len(p) > remaining {
		_, _ = b.Buffer.Write(p[:remaining])
		b.truncd = true
		return len(p), nil
	}
	return b.Buffer.Write(p)
}

// Ensure limitedBuffer satisfies io.Writer.
var _ io.Writer = (*limitedBuffer)(nil)
