#!/bin/sh

# The infra launches each container independently (not via compose), so the relay
# (oblivion) may not exist yet when the sender starts. victim.py resolves oblivion.pccc
# once at startup and exits on failure, so wait until the name resolves before launching.
until python3 -c "import socket; socket.gethostbyname('oblivion.pccc')" 2>/dev/null; do
  echo "[phantom] waiting for oblivion.pccc to resolve..."
  sleep 2
done
echo "[phantom] oblivion.pccc resolved; starting sender"

# Token arrives via env (tokenOblivion); write it where victim.py expects it.
echo "$tokenOblivion" > /app/token.txt

# This infra does not honor compose "restart", so self-heal if the sender exits.
while true; do
  python3 /app/victim.py || echo "[phantom] sender exited ($?); restarting in 2s"
  sleep 2
done
