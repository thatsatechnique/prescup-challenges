#!/usr/bin/env bash
set -e

# Insert the DB token (Token 3) from the environment into the Token table.
# Runs during MySQL initdb, after 01-db.sql has created the table.
mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" web_alerts <<SQL
INSERT INTO Token (TokenID, Token) VALUES (1, '${tokenSQL}')
  ON DUPLICATE KEY UPDATE Token='${tokenSQL}';
SQL
