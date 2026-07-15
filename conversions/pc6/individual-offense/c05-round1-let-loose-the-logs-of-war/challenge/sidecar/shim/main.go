// Package main implements a fake Docker Engine API endpoint ("shim") that
// speaks enough of the protocol to be indistinguishable from the real thing
// for a CTF attacker who has discovered /var/run/docker.sock and wants to
// create containers, execute commands, and read the output.
//
// The shim is intentionally NOT a general-purpose Docker replacement. It
// implements the endpoints competitors are likely to use during the
// exploitation phase of a socket-escape challenge, and returns realistic
// Docker-shaped responses for everything else. Any unknown request is
// logged (to stderr) with full body so the author can discover gaps after
// playtest.
//
// The shim does NOT run real containers. For each /containers/start it
// copies the fakehost template into a per-container rootfs, chroots into
// it, drops privileges to nobody, applies resource limits, and execs the
// requested Cmd. Output is captured with a size cap for retrieval via
// /containers/{id}/logs, /archive, /attach, and /exec.
package main

import (
	"context"
	"flag"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var (
	flagListen   = flag.String("listen", "0.0.0.0:2375", "address to listen on")
	flagTemplate = flag.String("template", "/opt/fakehost.template", "fakehost rootfs template")
	flagWorkdir  = flag.String("workdir", "/var/lib/shim/containers", "per-container rootfs staging area")
)

func main() {
	flag.Parse()

	// Sanity-check that the template and workdir are usable.
	if st, err := os.Stat(*flagTemplate); err != nil || !st.IsDir() {
		log.Fatalf("shim: template %q unusable: %v", *flagTemplate, err)
	}
	if err := os.MkdirAll(*flagWorkdir, 0755); err != nil {
		log.Fatalf("shim: workdir %q unusable: %v", *flagWorkdir, err)
	}

	store := NewStore(*flagTemplate, *flagWorkdir)
	router := NewRouter(store)

	// Wrap the router in the auth middleware. Every request must carry
	// `Authorization: Bearer <secret>` or it's rejected at the door.
	// The bridge binary in the web container injects this automatically;
	// a player hitting the shim directly from the internal network gets
	// a 401 before any Docker API logic runs.
	handler := authRequired(router)

	srv := &http.Server{
		Addr:              *flagListen,
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
		// No WriteTimeout; hijacked connections (/attach, /exec/start) and
		// long polls (/events) need to stay open.
	}

	lc := net.ListenConfig{}
	lis, err := lc.Listen(context.Background(), "tcp", *flagListen)
	if err != nil {
		log.Fatalf("shim: listen %s: %v", *flagListen, err)
	}
	log.Printf("shim: listening on %s (template=%s workdir=%s)",
		*flagListen, *flagTemplate, *flagWorkdir)

	go func() {
		if err := srv.Serve(lis); err != nil && err != http.ErrServerClosed {
			log.Fatalf("shim: serve: %v", err)
		}
	}()

	// Graceful shutdown on SIGTERM/SIGINT so the orchestrator teardown is clean.
	sigc := make(chan os.Signal, 1)
	signal.Notify(sigc, syscall.SIGTERM, syscall.SIGINT)
	<-sigc
	log.Printf("shim: shutting down")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
	store.Shutdown()
}
