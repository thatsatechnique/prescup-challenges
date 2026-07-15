#!/bin/sh

# oblivion binds 0.0.0.0 and resolves no external names, so it has no startup dependency.
# Token arrives via env (tokenOblivion); write it where server.py expects it.
echo "$tokenOblivion" > /app/token.txt

# This infra does not honor compose "restart", so self-heal here: the UDP server can exit
# on a malformed packet (e.g. a <5-byte packet -> empty ciphertext -> unpad IndexError).
while true; do
  python3 /app/server.py || echo "[oblivion] server exited ($?); restarting in 1s"
  sleep 1
done
