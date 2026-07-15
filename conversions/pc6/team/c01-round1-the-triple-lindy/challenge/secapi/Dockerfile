FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY SecurityApi/SecurityApi.csproj SecurityApi/
RUN dotnet restore SecurityApi/SecurityApi.csproj
COPY SecurityApi/ SecurityApi/
WORKDIR /src/SecurityApi
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app
COPY --from=build /app/publish .
COPY SecurityApi/img/ /app/img/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
