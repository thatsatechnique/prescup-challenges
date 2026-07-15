#!/bin/sh

# Wait for the database before serving. MySQL only opens port 3306 after its init/initdb
# finishes, so a successful TCP connect also means the schema and tokens are loaded.
# Without this, competitors hitting the site early get unexpected DB connection errors.
echo "[web] waiting for db:3306 ..."
until php -r 'exit(@fsockopen("db", 3306) ? 0 : 1);' 2>/dev/null; do
  echo "[web] db not ready yet; retrying in 2s"
  sleep 2
done
echo "[web] db is up"

# Tokens arrive via env: tokenProxy -> token.txt (printed after token.php),
# tokenSource -> source comment in hosts.php
echo "$tokenProxy" > /var/www/html/token.txt
sed -i "s/TOKENSOURCE/$tokenSource/g" /var/www/html/hosts.php

exec apache2-foreground
