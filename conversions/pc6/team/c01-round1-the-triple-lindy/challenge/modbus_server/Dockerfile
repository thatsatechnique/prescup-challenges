FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pymodbus==3.5.4

COPY poolserver.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 502

ENTRYPOINT ["/app/entrypoint.sh"]
