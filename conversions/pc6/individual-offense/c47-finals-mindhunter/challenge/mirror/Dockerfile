# ---- build stage: install deps to an isolated prefix ---------------------- #
FROM python:3.11-slim AS build
WORKDIR /wheels
RUN pip install --no-cache-dir --target /out flask requests

# ---- runtime stage: source is copied in, only what's needed --------------- #
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends dnsutils \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /out /usr/local/lib/python3.11/site-packages
WORKDIR /opt/mirror
COPY app/ /opt/mirror/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
