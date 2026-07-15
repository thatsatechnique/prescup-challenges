# Kessel Run

## Summary

In Kessel Run, the competitor must exploit a series of HTTP smuggling vulnerabilities in three proxy servers. Each proxy server is based off the same Python source code, but are slightly modified to introduce a different vulnerability. Getting the final token requires combining all of these vulnerabilities into a single request.

## VMs

This challenge uses the PC6 Stock Topology competitor networks only.

### Competitor Network

- challenge-server [OS: Ubuntu 22.04.04 Desktop, Network: (competitor challenge-net), IPv4: 10.5.5.5, Unlinked]
 - No grading or hosted files, only a [start-up script](./challenge/scripts/start.py) to move tokens onto `channel.pccc`

- kali-kessel [OS: Kali, Network: competitor, IPv4: DHCP, Linked]
  - President's Cup 6 default Kali system

- channel [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - The `channel.pccc` server hosts all four proxy servers as docker containers
    - These containers are named `channel`, `maelstrom`, `maw`, and `kessel`
    - Configured using docker compose
  - User: `user` Password: `Sc4nS0l0B3stSmuggl3r!!`

## Grading

This challenge does no grading. All tokens are retrieved directly by accessing `/token` on each proxy server.

## Troubleshooting Tips

### Quick Look

- Docker compose was used to configure the containers.
  - View logs on the system with `cd proxies; docker compose logs`.
    - `channel-1` is the first proxy, then `maelstrom-1`, `maw-1`, and `kessel-1`
  - Container logs are passed to the docker service, which are then sent to Graylog.
    - In Graylog, you can analyze a particular service by searching for their container name but with `proxies-` prepended.
      - For example, use `proxies-channel-1` to find the logs for `channel`.

### Quick Tips

- If needed, the proxies can be rebuilt with `cd proxies; docker compose down && docker compose build && docker compose up -d`.
  - The proxies each use their own volume, which contains their source code and two HTML files. For example, `channel` has their volume under `~/proxies/channel`
- Use `docker exec -it proxies-[proxyName]-1 bash` if you need to check something inside the docker container, where `proxyName` is the name of the proxy you need to check.

## Spotting - What to look for when a competitor is solving

By task:

1. For the first task, they should be developing a malicious HTTP request exploiting a CL.TE vulnerability. They might be doing this in Python, Burpsuite, or something else.
2. This will look similar to Task 1, but now with a TE.CL vulnerability. They should likely be working in Python at this point, as using other tools will be cumbersome due to needing to combine three requests.
3. For task 3, they will be extending their smuggling request to take advantage of `\r\n` and `\n` misuse.


