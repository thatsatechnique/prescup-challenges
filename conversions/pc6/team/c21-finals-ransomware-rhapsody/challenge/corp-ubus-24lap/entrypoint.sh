#!/bin/bash
set -euo pipefail

echo "[entrypoint] Running challenge initialization..."
python3 /opt/challenge/init_challenge.py

# --- Configure ubuntu_service profile (user created by init_challenge.py) ---
if id ubuntu_service &>/dev/null; then
    echo "[entrypoint] Setting up ubuntu_service banner + PS1..."
    cat /etc/profile_ubuntu_service.sh >> /home/ubuntu_service/.bashrc
    chown ubuntu_service:ubuntu_service /home/ubuntu_service/.bashrc
fi

echo "[entrypoint] Starting SSH daemon..."
mkdir -p /var/run/sshd
exec /usr/sbin/sshd -D -e

