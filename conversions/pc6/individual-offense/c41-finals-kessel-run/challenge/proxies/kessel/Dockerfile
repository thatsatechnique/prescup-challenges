FROM python:3.10.5
WORKDIR /app
COPY . /app
# Just routes back to itself as it doesn't need a proxy
# No restart policy in this infra; self-heal if the proxy exits (e.g. on non-UTF-8 input)
CMD ["sh", "-c", "while true; do /usr/bin/python3 ./kessel.py -X kessel.pccc || echo '[kessel] exited; restarting in 1s'; sleep 1; done"]
