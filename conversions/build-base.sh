#!/usr/bin/env bash
# Build the local challenge-server base image.
#
# A few challenges use a customized challenge server (grading, hosted files,
# startup scripts) whose Dockerfile builds `FROM pccc/challenge-server:base`.
# That tag isn't on a public registry — build it locally once with this script,
# then `docker compose up --build` those challenges normally.
#
# Challenges that need it: va_list_adventure, finsta, kessel-run, throw-me-a-bone.
# Harmless to run regardless — every other challenge builds the base directly
# from its own compose file.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker build -t pccc/challenge-server:base "$DIR/challenge-server"
echo "Built image: pccc/challenge-server:base"
