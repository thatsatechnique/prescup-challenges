FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY vendor/PoolVendorWeb.csproj vendor/
RUN dotnet restore vendor/PoolVendorWeb.csproj
COPY vendor/ vendor/
WORKDIR /src/vendor
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 80

CMD ["dotnet", "PoolVendorWeb.dll"]
