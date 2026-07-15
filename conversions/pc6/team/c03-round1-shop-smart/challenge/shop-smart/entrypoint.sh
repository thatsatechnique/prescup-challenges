#!/bin/bash
set -e

# ---------------------------------------------------------------
# Wait for the database to become available
# ---------------------------------------------------------------
echo "[entrypoint] Waiting for database..."
max_attempts=30
attempt=0
until mariadb -h"${DB_HOST:-db}" -u"${DB_USER:-website}" -p"${DB_PASS:-tartans@1}" -e "SELECT 1" "${DB_NAME:-ecommerce}" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$max_attempts" ]; then
        echo "[entrypoint] ERROR: Database not reachable after ${max_attempts} attempts."
        exit 1
    fi
    echo "[entrypoint]   attempt ${attempt}/${max_attempts} — retrying in 2s..."
    sleep 2
done
echo "[entrypoint] Database is ready."

# ---------------------------------------------------------------
# Inject runtime flags into PHP source files
# ---------------------------------------------------------------
TOKEN1="${TOKEN1_FLAG:-a1b2c3d4}"
TOKEN2="${TOKEN2_FLAG:-e5f6a7b8}"
TOKEN3="${TOKEN3_FLAG:-c9d0e1f2}"
TOKEN4="${TOKEN4_FLAG:-a3b4c5d6}"

echo "[entrypoint] Injecting flags..."

# Token 1 — displayed on login.php and index.php when logged in as admin
sed -i "s/########/${TOKEN1}/g" /var/www/html/login.php
sed -i "s/########/${TOKEN1}/g" /var/www/html/index.php

# Token 2 — displayed on orders.php when logged in as bcampbell
sed -i "s/########/${TOKEN2}/g" /var/www/html/orders.php

# Token 3 — written to /var/www/token3.txt (path traversal target)
echo "${TOKEN3}" > /var/www/token3.txt

# Token 4 — displayed on checkout.php when cart contains hidden product
sed -i "s/########/${TOKEN4}/g" /var/www/html/checkout.php

# Prevent CSS text-transform: uppercase from mangling token display
sed -i 's/text-transform: uppercase;//g' /var/www/html/css/style.css

echo "[entrypoint] Flags injected."

# ---------------------------------------------------------------
# Self-delete this script so flags cannot be read from it
# ---------------------------------------------------------------
rm -f /entrypoint.sh

# ---------------------------------------------------------------
# Start Apache in foreground
# ---------------------------------------------------------------
exec apache2-foreground
