FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends dnsmasq bash iproute2 && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 53/udp 53/tcp

ENTRYPOINT ["/entrypoint.sh"]
