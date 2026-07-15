# syntax=docker/dockerfile:1.6
#
# web: the competitor-facing Tomcat service.
#
# Three build stages:
#   1) builder — pre-arranges the Tomcat tree (manager app, context.xml,
#      server.xml with LockOutRealm disabled, tomcat-users.xml with placeholder password, warlog.war).
#   2) bridge-build — compiles the Go bridge binary with auth header injection.
#   3) final runtime — assembles the running image.
# ---------------------------------------------------------------------------

FROM tomcat:9-jdk17-temurin AS builder

# Enable the manager app by moving it out of webapps.dist
RUN cp -r /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/

# Misconfigured context allows access from any IP (normally locked to localhost)
COPY context.xml /usr/local/tomcat/webapps/manager/META-INF/context.xml

# server.xml with LockOutRealm commented out -> hydra-able
COPY server.xml /usr/local/tomcat/conf/server.xml

# tomcat-users.xml has ##PASS## placeholder; entrypoint seds the real value in
COPY tomcat-users.xml /usr/local/tomcat/conf/tomcat-users.xml

# Drop the log-viewer WAR (the visible service on :8080)
COPY warlog.war /usr/local/tomcat/webapps/warlog.war

# ---------------------------------------------------------------------------

FROM golang:1.22-alpine AS bridge-build

WORKDIR /src
COPY bridge/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags='-s -w' -o /out/dockerapi-bridge .

# ---------------------------------------------------------------------------

FROM tomcat:9-jdk17-temurin

ENV CATALINA_HOME=/usr/local/tomcat
ENV PATH=$CATALINA_HOME/bin:$PATH

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        apache2 tini curl ca-certificates \
 && a2enmod rewrite proxy proxy_http \
 && a2dissite 000-default \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder       /usr/local/tomcat        /usr/local/tomcat
COPY --from=bridge-build  /out/dockerapi-bridge    /usr/local/bin/dockerapi-bridge

# Apache vhost: redirect / -> /warlog and proxy /warlog -> localhost:8080
COPY apacheconf /etc/apache2/sites-available/warlog.conf
RUN a2ensite warlog

# Script to stage realistic log files for the warlog viewer.
COPY stage-logs.sh /opt/stage-logs.sh
RUN chmod +x /opt/stage-logs.sh

# Wordlist used by entrypoint to pick a random admin password at startup.
# The entrypoint deletes this file immediately after consuming it
COPY wordlist.txt /opt/wordlist.txt

# Entrypoint handles runtime flag + password injection, starts the
# bridge, apache, and tomcat.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 8080

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
