#!/bin/bash
# DNS is now served by the challenge server (see challengeserver HOSTS_JSON in
# docker-compose.yml). This service is retained only as a tombstone: it prints a
# notice and exits so anyone inspecting the stack sees where DNS moved.
# The original dnsmasq logic is preserved (commented out) below in case DNS ever
# needs to move back to this dedicated service.
echo "DNS now down by challenge.pccc, exiting"
exit 0

# --- Original dnsmasq DNS server (disabled; challenge server now serves DNS) ---
# set -e
#
# HOSTS=("townsville-pool.pccc" "secapi.pccc" "apm.pccc" "modbus.pccc")
# HOSTS_FILE="/etc/dnsmasq-hosts"
# CONF="/etc/dnsmasq.d/challenge.conf"
# mkdir -p /etc/dnsmasq.d
#
# # Determine this container's network IP to avoid conflict with Docker DNS on 127.0.0.11:53.
# SELF_HOSTNAME=$(hostname)
# LISTEN_IP=$(getent hosts "$SELF_HOSTNAME" 2>/dev/null | awk '{print $1}')
# if [ -z "$LISTEN_IP" ]; then
#     LISTEN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
# fi
# if [ -z "$LISTEN_IP" ]; then
#     LISTEN_IP=$(ip -4 addr show scope global 2>/dev/null | awk '/inet / {split($2,a,"/"); print a[1]; exit}')
# fi
# if [ -z "$LISTEN_IP" ]; then
#     echo "ERROR: Could not determine container IP"
#     exit 1
# fi
#
# # Write config: forward to Docker DNS, use an additional hosts file for PTR records.
# # addn-hosts entries serve both A (forward) and PTR (reverse) records.
# > "$HOSTS_FILE"
# cat > "$CONF" <<EOF
# no-resolv
# server=127.0.0.11
# addn-hosts=$HOSTS_FILE
# EOF
#
# # Phase 1: Start dnsmasq as a forwarder (no PTR records yet)
# echo "Starting dnsmasq on $LISTEN_IP (forwarding to Docker DNS)"
# dnsmasq --no-daemon --conf-dir=/etc/dnsmasq.d --listen-address="$LISTEN_IP" --bind-dynamic &
# DNSMASQ_PID=$!
# sleep 1
#
# # Phase 2: Resolve FQDNs through Docker DNS and write hosts file for PTR records
# echo "Resolving hostnames for PTR records..."
# while true; do
#     all_resolved=true
#     > "$HOSTS_FILE"
#     for fqdn in "${HOSTS[@]}"; do
#         ip=$(getent hosts "$fqdn" 2>/dev/null | awk '{print $1}')
#         if [ -z "$ip" ]; then
#             echo "Could not resolve $fqdn, retrying..."
#             all_resolved=false
#             break
#         fi
#         echo "$ip $fqdn" >> "$HOSTS_FILE"
#     done
#
#     if [ "$all_resolved" = true ]; then
#         break
#     fi
#     sleep 2
# done
#
# echo "All hosts resolved. Reloading dnsmasq to pick up PTR records."
# cat "$HOSTS_FILE"
# kill -HUP "$DNSMASQ_PID"
#
# # Keep the container running on dnsmasq
# wait "$DNSMASQ_PID"
