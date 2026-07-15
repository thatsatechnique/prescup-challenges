#!/bin/bash
set -e

# Write token files from environment variables
echo -n "$TOKEN1" > /app/token1.txt
echo -n "$TOKEN2" > /app/token2.txt
echo -n "$TOKEN3" > /app/token3.txt
echo -n "$TOKEN4" > /app/token4.txt

# Generate appsettings.json with injected values
cat > /app/appsettings.json <<EOF
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "SiteUser": "jamie.johns@townsvillepool.pccc",
  "Password": "${POOL_PASSWORD}",
  "SecurityToken": "${SEC_API_TOKEN}",
  "APIImageUrl": "${API_IMAGE_URL}",
  "InternalAPIUrl": "${INTERNAL_API_URL}",
  "PoolScadaServerIp": "${POOL_SCADA_SERVER_IP}"
}
EOF

exec dotnet PoolWeb.dll
