FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY pool/PoolWeb.csproj pool/
RUN dotnet restore pool/PoolWeb.csproj
COPY pool/ pool/
WORKDIR /src/pool
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app
COPY --from=build /app/publish .
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
