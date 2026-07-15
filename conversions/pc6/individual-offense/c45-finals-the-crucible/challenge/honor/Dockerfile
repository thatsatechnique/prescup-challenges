FROM python:3

# nginx serves the public directory listing; python runs the PIN checker (one VM, two halves)
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bake the PIN-checker source and the public directory (with oblivion.jpg) in
COPY src/ /app/
COPY public/ /public/
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Writes the token, starts nginx, then runs the PIN checker with self-heal (see entrypoint.sh)
CMD ["/app/entrypoint.sh"]
