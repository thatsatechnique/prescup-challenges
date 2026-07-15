# syntax=docker/dockerfile:1.6
#
# sidecar: the container that plays the role of the "host" running Docker.
# It exposes a TCP Docker-API-shaped listener that the web container's
# bridge binary connects to, so from the competitor's perspective
# /var/run/docker.sock inside the web container behaves exactly like a
# real host docker.sock.
#
# Multi-stage build:
#   1) build the Go shim as a static binary
#   2) assemble a minimal runtime image with the shim + a staged "fakehost"
#      tree that the shim chroots into for each player-requested container
# ---------------------------------------------------------------------------

FROM golang:1.22-alpine AS shim-build

WORKDIR /src
COPY shim/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags='-s -w' -o /out/shim .

# ---------------------------------------------------------------------------

FROM alpine:3.19

# busybox is already in alpine; we also want a proper static busybox to
# seed the fakehost tree so the chrooted "container" has a usable shell.
RUN apk add --no-cache busybox-static

# Copy the shim binary
COPY --from=shim-build /out/shim /usr/local/bin/shim

# Stage the fakehost template tree at /opt/fakehost.template. 
# The shim copies this tree into a per-container rootfs on each /containers/start
# Destructive commands cannot corrupt the template for later containers.
RUN mkdir -p /opt/fakehost.template/bin \
             /opt/fakehost.template/sbin \
             /opt/fakehost.template/etc \
             /opt/fakehost.template/home/user/Desktop \
             /opt/fakehost.template/home/user/Documents \
             /opt/fakehost.template/home/user/Downloads \
             /opt/fakehost.template/home/user/Music \
             /opt/fakehost.template/home/user/Pictures \
             /opt/fakehost.template/home/user/Public \
             /opt/fakehost.template/home/user/Templates \
             /opt/fakehost.template/home/user/Videos \
             /opt/fakehost.template/home/user/.config \
             /opt/fakehost.template/home/user/.local/share \
             /opt/fakehost.template/root \
             /opt/fakehost.template/tmp \
             /opt/fakehost.template/var/log \
             /opt/fakehost.template/var/run \
             /opt/fakehost.template/proc \
             /opt/fakehost.template/dev \
             /opt/fakehost.template/usr/bin \
             /opt/fakehost.template/usr/sbin \
             /opt/fakehost.template/usr/lib \
 && cp /bin/busybox.static /opt/fakehost.template/bin/busybox \
 && chmod +x /opt/fakehost.template/bin/busybox

# Populate busybox applet symlinks so sh/ls/cat/etc. work after chroot
RUN for applet in sh ls cat echo cp mv rm mkdir rmdir ln touch find grep \
                  head tail wc sort uniq awk sed cut tr printf env id \
                  whoami uname hostname ps top df du stat readlink \
                  basename dirname xargs pwd chmod chown date sleep \
                  which tar gzip gunzip tee cmp diff wget nc; do \
        ln -sf /bin/busybox /opt/fakehost.template/bin/${applet}; \
    done \
 && ln -sf /bin/busybox /opt/fakehost.template/sbin/init

# Plausible host identity files
RUN printf 'root:x:0:0:root:/root:/bin/sh\nuser:x:1000:1000:Linux User,,,:/home/user:/bin/sh\nnobody:x:65534:65534:nobody:/nonexistent:/bin/false\n' \
        > /opt/fakehost.template/etc/passwd \
 && printf 'root:x:0:\nuser:x:1000:\nnogroup:x:65534:\n' \
        > /opt/fakehost.template/etc/group \
 && printf 'dockerhost\n' \
        > /opt/fakehost.template/etc/hostname \
 && printf 'NAME="Ubuntu"\nVERSION="22.04.3 LTS (Jammy Jellyfish)"\nID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu 22.04.3 LTS"\nVERSION_ID="22.04"\n' \
        > /opt/fakehost.template/etc/os-release \
 && printf '127.0.0.1 localhost\n127.0.1.1 dockerhost\n' \
        > /opt/fakehost.template/etc/hosts \
 && printf 'dockerhost\n' \
        > /opt/fakehost.template/etc/debian_version

# Plausible log files in /var/log so enumeration reveals "normal" activity
RUN printf '%s\n' \
    "Apr 13 02:17:01 dockerhost CRON[1042]: (root) CMD (/usr/sbin/logrotate -f /etc/logrotate.conf)" \
    "Apr 13 02:17:03 dockerhost systemd[1]: logrotate.service: Deactivated successfully." \
    "Apr 13 03:05:12 dockerhost dockerd[812]: time=\"2026-04-13T03:05:12Z\" level=info msg=\"Starting up\"" \
    "Apr 13 03:05:13 dockerhost dockerd[812]: time=\"2026-04-13T03:05:13Z\" level=info msg=\"containerd successfully booted in 0.041s\"" \
    "Apr 13 03:05:15 dockerhost dockerd[812]: time=\"2026-04-13T03:05:15Z\" level=info msg=\"Loading containers: start.\"" \
    "Apr 13 03:05:16 dockerhost dockerd[812]: time=\"2026-04-13T03:05:16Z\" level=info msg=\"Loading containers: done.\"" \
    "Apr 13 03:05:16 dockerhost dockerd[812]: time=\"2026-04-13T03:05:16Z\" level=info msg=\"Daemon has completed initialization\"" \
    "Apr 13 03:05:16 dockerhost dockerd[812]: time=\"2026-04-13T03:05:16Z\" level=info msg=\"API listen on /var/run/docker.sock\"" \
    > /opt/fakehost.template/var/log/syslog \
 && cp /opt/fakehost.template/var/log/syslog /opt/fakehost.template/var/log/messages

# Populate /home/user with realistic dotfiles and correct ownership.
# Standard XDG dirs + dotfiles that a default Ubuntu user would have.
RUN printf '# ~/.bashrc: executed by bash for non-login shells.\nalias ll="ls -alF"\nalias la="ls -A"\nexport PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"\n' \
        > /opt/fakehost.template/home/user/.bashrc \
 && printf '# ~/.profile: executed by the command interpreter for login shells.\nif [ -f "$HOME/.bashrc" ]; then\n    . "$HOME/.bashrc"\nfi\n' \
        > /opt/fakehost.template/home/user/.profile \
 && printf 'sudo docker ps\nsudo docker logs tomcat\nls -la\ncat TOKEN2.txt\nexit\n' \
        > /opt/fakehost.template/home/user/.bash_history \
 && touch /opt/fakehost.template/home/user/.sudo_as_admin_successful \
 && chown -R 1000:1000 /opt/fakehost.template/home/user \
 && chmod 0755 /opt/fakehost.template/home/user

# Entrypoint writes TOKEN2 into the template and launches the shim listening on :2375.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 2375

ENTRYPOINT ["/entrypoint.sh"]
