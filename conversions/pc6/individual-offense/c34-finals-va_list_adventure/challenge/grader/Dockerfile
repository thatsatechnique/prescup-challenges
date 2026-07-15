# Builder: compile the public (fake-token) binary with the SAME toolchain as the live
# service (ubuntu:22.04 + clang) so the downloaded binary matches the target's layout.
FROM ubuntu:22.04 AS builder
RUN apt-get update \
    && apt-get install -y --no-install-recommends clang \
    && rm -rf /var/lib/apt/lists/*
COPY main.c /main.c
RUN clang /main.c -o /adventure -g

FROM 253388214223.dkr.ecr.us-east-1.amazonaws.com/pc7/challenge-server

# Grading config + script
COPY ./grader_config.yml /config.yml
COPY ./grading.py /custom_scripts/

# Hosted downloads: the source (fake token) and the matching compiled binary
COPY main.c /hosted_files/main.c
COPY --from=builder /adventure /hosted_files/adventure

# Private key to reach the exploit box (publickey) for pointers.txt
COPY ./id_ed25519 ./
RUN chmod 600 ./id_ed25519 && chmod -R +x /custom_scripts
