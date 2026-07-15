# The Crucible

## Summary

In The Crucible, the competitors must recover a corrupted SSH key and accompanying public key to access the `champion.us` server. The two parts of the key can be found by performing a timing-based side-channel attack on a PIN verifier on `honor.us` and a MitM attack on `phantom.us` and `oblivion.us`. With the two parts recovered, the competitor must dissect them and use the public key's modulus field to repair the private key.

## VMs

This challenge uses the PC6 Stock Topology [competitor] networks only.

### Competitor Network

- challenge-server [OS: Ubuntu 22.04.04 Desktop, Network: (competitor challenge-net), IPv4: 10.5.5.5, Unlinked]
  - No grading or hosted files, only a [start-up script](./challenge/scripts/start.py) to load tokens (and install steghide)
- kali [OS: Kali, Network: competitor, IPv4: DHCP, Linked]
  - President's Cup 6 default Kali system
- honor [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - Hosts simple HTTP file directory listing and a Python script using docker
    - The directory is set up using nginx; this should not give you any issues at all
      - The shared directory is `/home/user/public`
      - By default, contains `oblivion.jpg`, which has data hidden using `steghide`
    - The Python script checks PINs entered on port `61234`, vulnerable to a timing side-channel attack; container named `server`
      - When the correct PIN is entered, moves `token.txt` and `id_rsa` into the public directory listing folder
    - Configured using docker compose
    - Containers logged using `systemd`; all logs are thus forwarded to Graylog
  - Standard `user` / `password`; SSH access via `publickey` only
- oblivion [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - Hosts a Python script using docker
    - The Python script listens on port `1337` for `UDP` packets; container is named `server`
      - Packets are encrypted; goal is to steal them via MitM with `arpspoof`
    - Configured using docker compose
    - Shares the host network
    - Containers logged using `systemd`; all logs are thus forwarded to Graylog
  - Standard `user` / `password`; SSH access via `publickey` only
- phantom [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - Hosts a Python script using docker
    - The Python script sends `UDP` packets to `oblivion`; container is named `victim`
      - Packets are encrypted; goal is to steal them via MitM with `arpspoof`
    - Configured using docker compose
    - Shares the host network
    - Containers logged using `systemd`; all logs are thus forwarded to Graylog
  - Standard `user` / `password`; SSH access via `publickey` only
- champion [OS: Ubuntu 22.04.04 Server, Network: competitor, IPv4: DHCP, Unlinked]
  - Simply holds a `~/token.txt` loaded by the start script
  - Standard `user` / `password`; SSH access via `publickey` only
    - Needs the private key repaired as part of the challenge

Note that, in order to work with the `publickey` only SSH setting, I slightly modified the servicelogger script to accept a path to an `id_rsa` file. That code is included in the following dropdown.

<details><summary>Code to Implement ServiceChecker with id_rsa</summary>

```python
def get_ssh_command(service):
    if os.path.exists(service['password']):
        logging.info("Password is a file path, using it as an identity file for SSH.")
        return f"ssh -i {service['password']} -o StrictHostKeyChecking=no {service['user']}@{service['host']}"
    else:
        return f"sshpass -p {service['password']} ssh -o StrictHostKeyChecking=no {service['user']}@{service['host']}"

def get_logs(service):
    log_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    host_info = {"host":service['host'],"service":service['service']}
    ssh_command = get_ssh_command(service)
    while True:
        time.sleep(10)
        # `er` variable is intended to track if a service is 'fve' and then when same logs are grabbed they are logged with `.error` rather than `.info` to make for easier tracking.
        er = False
        ## below SSH cmd uses `is-active` option with `systemctl` where the response should be either `active`, `failed`, or `inactive` and then Log info accordingly.
        try:
            get_status_cmd = f"{ssh_command} 'systemctl is-active {service['service']}'"
            status_response = subprocess.run(get_status_cmd, shell=True,capture_output=True, timeout=10)
        except subprocess.TimeoutExpired:
            logger.error(f"SSH connection to host timed out.",extra=host_info)
            continue
        except Exception as e:
            logger.error(f"Exception has occurred when attempting to retrieve service status.",extra=host_info)
            logger.error(f"Exception: {e}",extra=host_info)
            continue
        if status_response.stdout.decode('utf-8') == '':
            logger.error(f"Error has occurred when attempting to get service status.",extra=host_info)
            logger.error(f"Error: {status_response.stderr.decode('utf-8')}",extra=host_info)
            continue
        if status_response.stdout.decode('utf-8').strip('\n') == 'failed':
            er = "SERVICE FAILED: "
            logger.error(f"{er} {service['service']} is in failed state.",extra=host_info)
        elif status_response.stdout.decode('utf-8').strip('\n') == 'inactive':
            er = "SERVICE INACTIVE: "
            logger.error(f"{er} {service['service']} is in inactive state.",extra=host_info)
        ## grab logs
        try:
            get_log_cmd = f"{ssh_command} 'journalctl --since \"{log_time}\" -u {service['service']}'"
            log_response = subprocess.run(get_log_cmd, shell=True,capture_output=True,timeout=10)
            cur_logs = log_response.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            logger.error(f"SSH connection to host timed out.",extra=host_info)
            continue
        except Exception as e:
            logger.error(f"Exception has occurred when attempting to retrieve logs.",extra=host_info)
            logger.error(f"Exception: {e}")
            continue
        if log_response.stdout.decode('utf-8') == '':
            logger.error(f"Error has occurred when attempting to collect logs.",extra=host_info)
            logger.error(f"Error: {log_response.stderr.decode('utf-8')}",extra=host_info)
            continue
        if "No entries" in cur_logs:
            if er != False:
                logger.error(f"{er} No new logs found at this time.",extra=host_info)
            else:
                logger.info(f"No new logs found at this time.",extra=host_info)
            continue
        output = cur_logs.split("\n")
        output.remove("")
        for line in output:
            if er == False:
                logger.info(line,extra=host_info)
            else:
                logger.error(er + line,extra=host_info)
        log_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
```

</details>


## Grading

No grading! All tokens are discovered directly.

## Troubleshooting Tips

### Quick Look

- You can view any of the docker logs on the server with `docker compose logs`
  - Alternatively, use `journalctl -u docker.service` or check Graylog
- The `phantom` and `oblivion` Python docker containers have `arp` installed to check for the `MitM` attack
  - For example, to check `oblivion`, use `docker compose exec server arp`
- Graylog will keep track of the attempted PINs for `honor.us` and will log when the correct PIN has been entered
- In Graylog, the `arpspoof` attack will be visible in the logs. The script monitors the `MAC` address and logs any changes
  - Note that when the attack is occurring, the script may output that the `MAC` address is `ens32`, then send another message with the new, real `MAC` address. This is expected and normal
  - There will also be lots of timeouts before/after the attack as the ARP tables are fixed  
- Connect to `oblivion.us`, `phantom.us`, or `honor.us` with the private key on the challenge server
  - e.g., `ssh oblivion.us` works
- Connect to `champion.us` with `ssh -i ~/challengeServer/custom_scripts/ssh_keys/original/id_rsa champion.us`

### Quick Tips

- You can reset any of the docker containers with `docker compose restart`
  - Alternatively, they are all set to restart `always`; you can reboot if needed
- The `honor.us` server has `steghide` installed so you can verify `oblivion.jpg` if needed
  - `cd /tmp; cp ~/public/oblivion.jpg /tmp/; steghide extract -sf oblivion.jpg`
  - Do not put anything in the public directory or it will be available for download!

## Spotting - What to look for when a competitor is solving

By task:

1. On `honor.us`, they should start by investigating the web server. From there, they might pivot to task two with the `oblivion.jpg` file.
   1. They should use `nmap` to discover port `61234`.
   2. They should use `nc` or similar to discover the purpose of `51234`.
   3. They will need to write a script that uses timing to perform a sidechannel attack
2. For `oblivion.us` and `phantom.us`, they will need to use `steghide` to recover the `protocol.txt` file from the image recovered on the web server of `honor.us`
   1. They should use `Wireshark` to monitor for incoming traffic, and then use `arpspoof` to try and redirect the traffic to themselves.
   2. They should see the encrypted packets; they can use something like cyberchef to decrypt them based on the protocol document
   3. They then need to either write a script using something like `scapy` to complete the `MitM` attack, decrypting the packets and passing them back and forth
      1. Alternatively, they can do this by hand, slowly uncovering each of the intended call/responses
3. For `champion.us`, they will need both the private and public keys. They will then need to use `xxd` and/or a hex editor to repair the private key. They will need to first Base64 decode both keys. 

