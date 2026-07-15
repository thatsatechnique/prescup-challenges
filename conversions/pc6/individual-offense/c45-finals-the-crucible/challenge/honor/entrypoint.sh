#!/bin/sh

# Token arrives via env (tokenHonor); write it where server.py expects it.
echo "$tokenHonor" > /app/token.txt

# Serve the public directory listing (nginx daemonizes into the background)
nginx

# This infra does not honor compose "restart", so self-heal the PIN checker if it exits.
while true; do
  python3 /app/server.py || echo "[honor] PIN checker exited ($?); restarting in 1s"
  sleep 1
done
