#!/bin/bash

PART=$1
V1=$2
V2=$3

curl -X POST \
  -H "Content-Type: application/json" \
  --data "{\"value1\": $V1, \"value2\": $V2}" \
  http://float-server:8000/part$PART
