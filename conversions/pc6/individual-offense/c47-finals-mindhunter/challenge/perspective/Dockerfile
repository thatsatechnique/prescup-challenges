FROM debian:12-slim

# The pivot box: an SSH server the competitor tunnels through (ssh -D / proxychains)
# to reach the internal mirror network. Ships the tooling the challenge assumes on
# the jump host (curl, python3, nmap, proxychains4) so it can also be worked from
# directly (solution "Choice #1").
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server \
        ca-certificates \
        curl \
        python3 \
        python3-requests \
        nmap \
        iproute2 \
        dnsutils \
        proxychains4 \
        procps \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd

# Competitor account (credentials published in the README, matching the original).
ARG PIVOT_USER=user
ARG PIVOT_PASS=tartans
RUN useradd -m -s /bin/bash ${PIVOT_USER} \
    && echo "${PIVOT_USER}:${PIVOT_PASS}" | chpasswd

# Harden: no root login, password auth only for the competitor user, allow the
# TCP forwarding the SOCKS pivot depends on.
RUN sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/^#*AllowTcpForwarding.*/AllowTcpForwarding yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && printf '\nAllowUsers user\nGatewayPorts no\n' >> /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22
CMD ["/entrypoint.sh"]
