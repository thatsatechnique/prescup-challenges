package main

import (
	"crypto/subtle"
	"net/http"
	"strings"
)

// expectedAuth is the shared secret the bridge injects on every request.
// The web container's bridge binary must have the SAME value compiled in
// (or passed via -secret flag).
//
// This is a deliberately static string. A competitor who has already
// popped the web container with root can `strings /usr/local/bin/*`
// and find it — that's accepted. The goal of this check is to prevent
// casual internal-network scanning from bypassing the docker.sock
// narrative, not to resist a determined attacker who's already fully
// compromised the bridge host.
const expectedAuth = "c05-shim-auth-9a7f3e2b1d6c4850"

// authRequired wraps a handler with a constant-time bearer-token check.
// Responses on failure mimic real dockerd running in "restricted-client"
// mode so a player probing with curl sees a plausible Docker error.
func authRequired(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Always advertise the same server identity headers so the
		// 401 looks like it came from a real dockerd.
		w.Header().Set("Api-Version", "1.45")
		w.Header().Set("Server", "Docker/27.0.3 (linux)")

		hdr := r.Header.Get("Authorization")
		const prefix = "Bearer "
		if !strings.HasPrefix(hdr, prefix) {
			writeError(w, http.StatusUnauthorized,
				"Unauthorized: missing authorization")
			return
		}
		got := hdr[len(prefix):]
		if subtle.ConstantTimeCompare([]byte(got), []byte(expectedAuth)) != 1 {
			writeError(w, http.StatusUnauthorized,
				"Unauthorized: bad credentials")
			return
		}
		next.ServeHTTP(w, r)
	})
}
