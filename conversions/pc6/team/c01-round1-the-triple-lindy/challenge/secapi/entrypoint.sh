#!/bin/bash
set -e

# Initialize camera status to enabled
echo "enabled" > /app/CameraStatus.txt

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
  "SecurityToken": "${SEC_API_TOKEN}",
  "ImageUrl": "${IMAGE_URL}"
}
EOF

exec dotnet SecurityApi.dll
