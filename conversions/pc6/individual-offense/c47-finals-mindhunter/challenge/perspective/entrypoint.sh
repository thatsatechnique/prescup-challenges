#!/bin/bash
set -e

# Generate host keys on first boot if they are missing.
ssh-keygen -A

# Point proxychains at a local dynamic tunnel by default (competitor runs
# `ssh -f -N -D 9050 user@perspective` from their own box; when working ON this
# host they can tunnel to localhost). socks5 keeps DNS local; socks5h defers it.
if [ ! -f /etc/proxychains4.conf ] || ! grep -q "9050" /etc/proxychains4.conf; then
  cat > /etc/proxychains4.conf <<'EOF'
strict_chain
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks5 127.0.0.1 9050
EOF
fi

exec /usr/sbin/sshd -D -e
