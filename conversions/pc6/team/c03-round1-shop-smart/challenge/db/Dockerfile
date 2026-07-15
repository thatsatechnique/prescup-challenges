FROM mariadb:10.11

COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
RUN chmod -R 755 /docker-entrypoint-initdb.d/   
RUN chown -R root:root /docker-entrypoint-initdb.d/
