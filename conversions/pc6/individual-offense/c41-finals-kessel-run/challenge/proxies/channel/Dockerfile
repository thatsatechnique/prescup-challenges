FROM python:3.10.5
WORKDIR /app
COPY . /app
# No restart policy in this infra; self-heal if the proxy exits (e.g. on non-UTF-8 input)
CMD ["sh", "-c", "while true; do /usr/bin/python3 ./channel.py -X maelstrom.pccc || echo '[channel] exited; restarting in 1s'; sleep 1; done"]
