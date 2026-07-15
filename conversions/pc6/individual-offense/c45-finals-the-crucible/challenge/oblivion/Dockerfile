FROM python:3

RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src/ /app/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
