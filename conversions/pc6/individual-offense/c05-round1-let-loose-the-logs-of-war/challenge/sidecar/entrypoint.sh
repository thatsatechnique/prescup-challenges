#!/bin/sh
set -e

#TOKEN2="${TOKEN2_FLAG:-PCCC{e5f6a7b8}}"

# Write TOKEN2 into the fakehost template at /home/user/TOKEN2.txt.
echo "[entrypoint] Writing Token 2 to fakehost /home/user/TOKEN2.txt"
printf 'TOKEN 2: %s\n' "$TOKEN2_FLAG" > /opt/fakehost.template/home/user/TOKEN2.txt
chmod 0644 /opt/fakehost.template/home/user/TOKEN2.txt
chown 1000:1000 /opt/fakehost.template/home/user/TOKEN2.txt

# Drop some decoy files that a player might grep for tokens in, making the challenge feel like a real poorly-configured host.
printf 'admin:$6$salt$%s\n' "$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')" \
    > /opt/fakehost.template/etc/shadow
chmod 0640 /opt/fakehost.template/etc/shadow

# Working area the shim uses for per-container rootfs copies
mkdir -p /var/lib/shim/containers
chmod 0755 /var/lib/shim

# Self-delete the entrypoint
rm -f /entrypoint.sh

echo "[entrypoint] Starting Docker API shim on :2375"
exec /usr/local/bin/shim \
    -listen 0.0.0.0:2375 \
    -template /opt/fakehost.template \
    -workdir /var/lib/shim/containers
