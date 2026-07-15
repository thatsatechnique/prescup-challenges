#!/bin/bash
set -e

# The mirrors resolve the `perspective` pivot host via Docker's embedded DNS
# (they share the internal mirror_net with it). No challenge-server DNS needed.
cd /opt/mirror
exec python3 server.py
