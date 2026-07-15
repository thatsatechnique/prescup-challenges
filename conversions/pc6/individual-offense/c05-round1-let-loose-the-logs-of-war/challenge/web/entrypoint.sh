#!/bin/bash
set -e

#TOKEN1="${TOKEN1_FLAG:-PCCC{a1b2c3d4}}"
SHIM_HOST="${SHIM_HOST:-sidecar}"
SHIM_PORT="${SHIM_PORT:-2375}"
WORDLIST="/opt/wordlist.txt"
USERS_XML="${CATALINA_HOME}/conf/tomcat-users.xml"

# ---------------------------------------------------------------
# Pick a random word from the shipped wordlist to use as the
# manager admin password. The same wordlist is loaded into the
# competitor workspace, so hydra against this list will converge.
# ---------------------------------------------------------------
if [ ! -r "${WORDLIST}" ]; then
    echo "[entrypoint] FATAL: wordlist missing at ${WORDLIST}"
    exit 1
fi
ADMIN_PASS="$(shuf -n 1 "${WORDLIST}")"
# Wordlist is only needed once at startup; delete it so a post-shell
# competitor cannot inspect it and confirm the password-generation
# mechanism. The wordlist they get on Kali is their own copy.
rm -f "${WORDLIST}"

echo "[entrypoint] Injecting admin password into tomcat-users.xml"
sed -i "s/##PASS##/${ADMIN_PASS}/g" "${USERS_XML}"

# ---------------------------------------------------------------
# Place Token 1 at the container root. This is the first-stage
# flag awarded for getting a shell inside the web container.
# ---------------------------------------------------------------
echo "[entrypoint] Writing Token 1 to /TOKEN1.txt"
echo "TOKEN 1: $TOKEN1_FLAG" > /TOKEN1.txt
chmod 0644 /TOKEN1.txt

# Stage realistic log files so the warlog viewer on :80 has content.
echo "[entrypoint] Staging log files for warlog"
/opt/stage-logs.sh
rm -f /opt/stage-logs.sh

# Start Apache on :80 in the background. It proxies / -> /warlog and /warlog -> localhost:8080/warlog
echo "[entrypoint] Starting Apache on :80"
. /etc/apache2/envvars
mkdir -p "${APACHE_RUN_DIR}" "${APACHE_LOCK_DIR}" "${APACHE_LOG_DIR}"
apache2 -DFOREGROUND > >(sed 's/^/[apache] /') 2>&1 &

# ---------------------------------------------------------------
# Start the dockerapi-bridge in the background.
#
# The bridge listens on /var/run/docker.sock and forwards requests
# to the shim on the sidecar container over TCP, injecting a
# shared-secret Authorization header on every request. This gives
# the competitor a /var/run/docker.sock that behaves identically
# to a real exposed host socket while preventing casual internal-
# network scanning from bypassing the intended attack path.
# ---------------------------------------------------------------
mkdir -p /var/run
rm -f /var/run/docker.sock

/usr/local/bin/dockerapi-bridge \
    -listen /var/run/docker.sock \
    -upstream "http://${SHIM_HOST}:${SHIM_PORT}" \
    -secret "c05-shim-auth-9a7f3e2b1d6c4850" \
    > >(sed 's/^/[bridge] /') 2>&1 &

# Self-delete the entrypoint
rm -f /entrypoint.sh

echo "[entrypoint] Starting Tomcat"
exec catalina.sh run
