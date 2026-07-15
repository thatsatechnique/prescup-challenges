// bridge listens on a local unix socket (the docker.sock fiction) and
// forwards every HTTP request to a remote TCP endpoint (the shim),
// injecting a shared-secret Authorization header on the way through.
//
// The bridge is the ONLY legitimate caller of the shim — the shim
// rejects unauthenticated requests with a 401. A player who has popped
// the web container via the Tomcat exploit sees a normal-looking
// /var/run/docker.sock and their curl commands work transparently
// because the bridge transparently stamps the required header. A
// player who scans the internal network, finds `sidecar:2375`, and
// tries to hit it directly gets a 401 — the casual-discovery path is
// closed.
//
// This is NOT a cryptographic boundary. A competitor with root inside
// the web container can `strings /usr/local/bin/dockerapi-bridge` and
// extract the secret. That's acceptable: at that point they've
// understood the architecture enough that the lesson (Docker API
// abuse via exposed socket) is already learned. The bridge only
// stops casual network scanning from bypassing the intended path.
//
// Additionally, the bridge supports the HTTP "connection hijacking"
// that the /attach, /exec/start endpoints use, by detecting 101
// Switching Protocols responses and tunneling raw bytes from then on.
package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

var (
	flagListen = flag.String("listen", "/var/run/docker.sock",
		"unix socket path to listen on")
	flagUpstream = flag.String("upstream", "",
		"upstream HTTP endpoint (e.g. http://sidecar:2375)")
	flagSecret = flag.String("secret", "",
		"shared secret to inject as Authorization: Bearer <secret>")
)

func main() {
	flag.Parse()
	if *flagUpstream == "" || *flagSecret == "" {
		log.Fatalf("bridge: -upstream and -secret are required")
	}

	upstreamURL, err := url.Parse(*flagUpstream)
	if err != nil {
		log.Fatalf("bridge: bad upstream URL: %v", err)
	}

	// Clean up any stale socket from a previous run.
	_ = os.Remove(*flagListen)

	// Retry loop: the sidecar might not be listening yet on first boot.
	// We create the unix socket immediately (so curl doesn't fail with
	// ENOENT) but defer upstream connections until requests arrive. The
	// reverse proxy handles upstream retries on a per-request basis.
	lis, err := net.Listen("unix", *flagListen)
	if err != nil {
		log.Fatalf("bridge: listen %s: %v", *flagListen, err)
	}
	if err := os.Chmod(*flagListen, 0666); err != nil {
		log.Printf("bridge: chmod socket: %v", err)
	}
	log.Printf("bridge: listening on unix:%s, forwarding to %s",
		*flagListen, upstreamURL)

	proxy := &httputil.ReverseProxy{
		Rewrite: func(pr *httputil.ProxyRequest) {
			pr.SetURL(upstreamURL)
			pr.Out.Host = upstreamURL.Host
			// The sentinel header. Shim requires this on every request.
			pr.Out.Header.Set("Authorization", "Bearer "+*flagSecret)
			// Preserve the original User-Agent; the shim logs it.
		},
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout:   5 * time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			// The shim handles multiple endpoints that do HTTP "upgrade"
			// (101 Switching Protocols) for bidirectional streaming.
			// ReverseProxy handles this via its support for the
			// Upgrade header, provided Transport doesn't strip it.
			ResponseHeaderTimeout: 0, // no timeout — /events etc. are long-poll
		},
		ErrorLog: log.New(os.Stderr, "bridge-proxy: ", log.LstdFlags),
		// Flush immediately so streaming endpoints (/events, /logs?follow)
		// behave correctly.
		FlushInterval: 100 * time.Millisecond,
		// Custom error handler so a transient upstream failure doesn't
		// leak a Go http stdlib error page to curl.
		ErrorHandler: func(w http.ResponseWriter, r *http.Request, err error) {
			log.Printf("bridge: upstream error on %s %s: %v",
				r.Method, r.URL.Path, err)
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadGateway)
			fmt.Fprintf(w, `{"message":"upstream unavailable: %s"}`,
				strings.ReplaceAll(err.Error(), `"`, `\"`))
		},
	}

	// Wrap the proxy to handle HTTP hijacking manually for /attach and
	// /exec/start. Go's stdlib ReverseProxy does support Upgrade flow
	// natively on 1.22+, but only for clients that already sent the
	// Upgrade header. Docker clients don't set Upgrade on
	// /containers/{id}/attach; they rely on the server to initiate the
	// protocol switch. We detect 101 responses and switch to raw bytes.
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if isHijackEndpoint(r) {
			hijackProxy(w, r, upstreamURL, *flagSecret)
			return
		}
		proxy.ServeHTTP(w, r)
	})

	srv := &http.Server{
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		if err := srv.Serve(lis); err != nil && err != http.ErrServerClosed {
			log.Fatalf("bridge: serve: %v", err)
		}
	}()

	// Graceful shutdown.
	sigc := make(chan os.Signal, 1)
	signal.Notify(sigc, syscall.SIGTERM, syscall.SIGINT)
	<-sigc
	log.Printf("bridge: shutting down")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
	_ = os.Remove(*flagListen)
}

// isHijackEndpoint returns true for Docker API paths that respond with
// 101 Switching Protocols + raw byte streams. These need manual tunneling
// rather than the ReverseProxy's request/response cycle.
func isHijackEndpoint(r *http.Request) bool {
	p := r.URL.Path
	// Normalize /v1.xx prefix
	if strings.HasPrefix(p, "/v") {
		if idx := strings.Index(p[1:], "/"); idx >= 0 {
			p = p[1+idx:]
		}
	}
	if r.Method == http.MethodPost {
		if strings.HasSuffix(p, "/attach") && strings.Contains(p, "/containers/") {
			return true
		}
		if strings.HasSuffix(p, "/start") && strings.Contains(p, "/exec/") {
			return true
		}
	}
	return false
}

// hijackProxy tunnels a connection-upgrade request to the upstream. It
// dials the upstream itself, forwards the request with the auth header
// injected, and then splices raw bytes in both directions.
func hijackProxy(w http.ResponseWriter, r *http.Request, upstream *url.URL, secret string) {
	hj, ok := w.(http.Hijacker)
	if !ok {
		http.Error(w, "hijacking unsupported", http.StatusInternalServerError)
		return
	}

	// Dial upstream.
	dialer := &net.Dialer{Timeout: 5 * time.Second}
	upConn, err := dialer.Dial("tcp", upstream.Host)
	if err != nil {
		http.Error(w, "upstream dial failed: "+err.Error(), http.StatusBadGateway)
		return
	}
	defer upConn.Close()

	// Forward request with injected auth header.
	r.Header.Set("Authorization", "Bearer "+secret)
	// Make the request line path absolute again for the upstream.
	if err := r.Write(upConn); err != nil {
		http.Error(w, "upstream write failed: "+err.Error(), http.StatusBadGateway)
		return
	}

	// Hijack the client connection and splice.
	clientConn, clientBuf, err := hj.Hijack()
	if err != nil {
		return
	}
	defer clientConn.Close()

	// Relay both directions. Drain any buffered-but-unread client bytes
	// from the http server's reader first.
	go func() {
		_, _ = io.Copy(upConn, clientBuf)
	}()
	upBuf := bufio.NewReader(upConn)
	_, _ = io.Copy(clientConn, upBuf)
}
