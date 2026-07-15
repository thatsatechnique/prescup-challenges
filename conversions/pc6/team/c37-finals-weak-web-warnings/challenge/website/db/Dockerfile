FROM mysql:8.0

# mysqld.sh tails this dir to stdout; create it so the script's truncate doesn't fail
RUN mkdir -p /var/logs/mysql

# Query/error logging config (was a bind mount)
COPY my.cnf /etc/mysql/conf.d/my.cnf

# Custom command wrapper that tails logs then runs the real entrypoint (initdb.d still runs)
COPY mysqld.sh /usr/local/bin/mysqld.sh

# Schema first (01), then token insertion from env (02) once the Token table exists
COPY db.sql /docker-entrypoint-initdb.d/01-db.sql
COPY token-init.sh /docker-entrypoint-initdb.d/02-token-init.sh

# chmod the config so MySQL doesn't ignore it as "world-writable" (COPY preserves the
# permissive Windows source perms otherwise)
RUN chmod +x /usr/local/bin/mysqld.sh /docker-entrypoint-initdb.d/02-token-init.sh \
    && chmod 644 /etc/mysql/conf.d/my.cnf
