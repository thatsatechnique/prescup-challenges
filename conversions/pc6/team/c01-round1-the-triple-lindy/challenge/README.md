# The Triple Lindy

*Challenge Artifacts*

## Services

- `pool_web/`: .NET 6 MVC web application hosting the Townsville Pool website. Source code in [pool_web/pool](./pool_web/pool/).

- `secapi/`: .NET 6 Web API hosting the security camera API. Source code in [secapi/SecurityApi](./secapi/SecurityApi/).

- `vendor_web/`: .NET 6 MVC web application hosting the Automated Pool Management vendor website. Source code in [vendor_web/vendor](./vendor_web/vendor/).

- `modbus_server/`: Python SCADA server simulating pool chemical monitoring.
  - [poolserver.py](./modbus_server/poolserver.py) - Modbus TCP server

- `dns/`: Lightweight dnsmasq DNS server providing forward and reverse DNS for all `.pccc` hostnames.

## DNS

A DNS server at `dns.pccc` resolves challenge hostnames. Use it with tools like nmap by adding the `--dns-servers dns.pccc` flag.
