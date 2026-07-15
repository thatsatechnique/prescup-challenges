# WWW (Weak Web Warnings)

## Summary

In WWW (Weak Web Warnings), the competitor is tasked with solving a variety of web exploitation challenges. Each vulnerability is a well-known issue, but are implemented so that they are either hard to detect, exploit, or both. For example, there is a blind SQL injection that cannot be detected or exploited with sqlmap by default. In addition to SQLi, there is also HTTP smuggling, PHP serialization, and source code leakage through PHP file inclusion.

## VMs

This challenge uses the PC6 Stock Topology competitor networks only.

### Competitor Network

- challenge-server-weak [OS: Ubuntu 22.04.04 Desktop, Network: (competitor challenge-net), IPv4: 10.5.5.5, Unlinked]
 - No grading or hosted files, only a [start-up script](./challenge/scripts/start.py) to move tokens onto `web.us`

- kali-weak [OS: Kali, Network: competitor, IPv4: DHCP, Linked]
  - President's Cup 6 default Kali system

- web [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - The `web.us` web server to target
    - Uses three docker containers: an Apache proxy, PHP Apache web server, and a MySQL Database
    - Configured using docker compose
  - User: `user` Password: `B4dW3bAl3rt!@`

## Grading

This challenge does no grading. All tokens are retrieved directly by exploiting `web.us`.

## Troubleshooting Tips

### Quick Look

- Docker compose was used to configure the containers.
  - View logs on the system with `cd website; docker compose logs`.
    - `proxy-1` will be the Apache proxy, `web-1` is the PHP Apache server, and `db-1` is the MySQL server.
    - MySQL logs the queries it receives so you can check their SQLi attempts under `website/storage/logs/mysql_general.log`.
  - Container logs are passed to the docker service, which are then sent to Graylog.
    - In Graylog, you can analyze a particular service by searching for their container name but with `website-` prepended.
      - For example, use `website-proxy-1` to find the proxy logs.
      - Database errors are sent, but database queries are not (they need to make 100s of queries since it's blind SQLi).

### Quick Tips

- If needed, the site can be rebuilt with `cd website; docker compose down && docker compose build && docker compose up -d`.
  - If the database still won't start, delete the consistent partition then try again: `sudo rm -r storage/db/*`. The database will be rebuilt from scratch.
  - Rebuilding the database from scratch will absolutely flood the MySQL logs with a bunch of create statements. Not a problem, but will make the file much harder to read.
- Use `docker exec -it website-[proxy,web,db]-1 bash` if you need to check something inside the docker container.
  - Most likely this would be to check if the `success.txt` file in the `web` container exists or not for the token awarded for HTTP smuggling (Token 2). The file is created when `token.php` is executed.

## Spotting - What to look for when a competitor is solving

By task:

1. Task 1 is PHP file inclusion. This occurs on every page; they should be trying different URLs like "web.us/x", where x is their file inclusion. A "web.us/php://" URI is close, need to double URL encode it.
  - Could use a tool like curl or burpsuite, but could also just be typing directly into the browser.
2. Task 2 is HTTP smuggling. This will look similar to task 1, as the error also occurs in the URL. This time, though, they should be making a fake HTTP request (looking like `web.us/a %0a ... GET x HTTP 1.1...`)
  - The token will be visible at the top of any page after they succeed
3. Task 3 is blind SQL injection. The SQL injection occurs in the `t` GET param of `web.us/alerts`, but they will need a script of some kind since this is a Blind injection.
4. Task 4 is php serialization. They will need to run some PHP of their own to generate the correct serial input. This is uploaded at `web.us/hosts`

