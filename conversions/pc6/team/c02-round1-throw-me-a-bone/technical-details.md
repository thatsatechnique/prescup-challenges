# Throw Me A Bone

*Technical Details*

## Summary

### MERCH Domain

A Microsoft Server 2022 system was created outside of the challenge environment. Active Directory roles were installed and it was promoted to Domain Controller for the MERCH domain. Basic configurations, including users, were added. The NTDS.dit file was then extracted, as well as the HKLM/SYSTEM HIVE, for use in this challenge.

These two files are provided to the competitor. They are asked to identify any user accounts which are using weak or easily guessed passwords.

### Shared User

This user account is configured on all servers to allow the scanner and grading applications to work correctly.

| Username | Password |
| :---: | :---: |
| scanuser | 2th3st@rs |

## Docker Services

All services run on the `competitor_net` Docker network.

#### Challenge Infrastructure

- challenge-server [Image: prescup challenge-server, Network: competitor\_net]
    - Runs the [Grading Script](./challenge/prescup-challenge-server/challenge-server/grader_scripts/c02_grading_check.py) to check that each task has been completed
    - Runs the [Scanner Application](./challenge/prescup-challenge-server/challenge-server/scanner/) on port 5555
    - Hosts file downloads at `/files`

#### Target Servers

- k3s-server [OS: Ubuntu 22.04, Network: competitor\_net]
    - No vulnerabilities reported. This is intended to be the "gold" system to compare to

- app-server [OS: Ubuntu 22.04, Network: competitor\_net]
    - Introduced Vulnerabilities:
        - SSH allows `root` login
        - Incorrect permission on `shadow` file

- cato [OS: Ubuntu 22.04, Network: competitor\_net]
    - Introduced Vulnerabilities:
        - Inactive user accounts still on system [dgreen, hcarter]

- virginia [OS: Ubuntu 22.04, Network: competitor\_net]
    - Introduced Vulnerabilities:
        - SSH allows `root` login
        - Inactive user accounts still on system [lrobinson, awright, dgreen]

- amicus [OS: Ubuntu 22.04, Network: competitor\_net]
    - Introduced Vulnerabilities:
        - Incorrect permissions on `passwd` file
        - SSH allows `root` login

- cassius [OS: Ubuntu 22.04, Network: competitor\_net]
    - Introduced Vulnerabilities:
        - Incorrect permission on `shadow` file
        - Inactive user accounts still on system [eclark, sscott, hcarter]

## Troubleshooting Tips

#### Quick Look:

- View challenge-server logs: `docker compose logs challenge-server`
- Grading check logs are at `/var/log/gradingCheck.log` inside the challenge-server container
- Scanner application logs are at `/var/log/scannerApp.log` inside the challenge-server container

#### Quick Check:

- Checks run by both the grading check and Scanner Application rely on the `scanuser` account on each system.
- From the challenge-server container, verify SSH access: `ssh scanuser@<hostname>` using password `2th3st@rs`

### Competitor reports "There was an error grading your challenge" message.

Check the grading logs inside the challenge-server container:
```bash
docker compose exec challenge-server cat /var/log/gradingCheck.log | grep ERROR
```

### Competitor is reporting an error message on the Scanner Application

Check the scanner logs:
```bash
docker compose exec challenge-server cat /var/log/scannerApp.log | grep ERROR
```

### "The scanner says everything is resolved, but the grading check fails; what gives?"

A component of this challenge is that three (3) servers are not documented on the provided report. If a competitor reports the scanner shows everything resolved, but the grading check is failing, they have likely not identified these undocumented systems (virginia, amicus, cassius).

Check if they have scanned the undocumented servers in the scanner logs. If not, they haven't discovered them yet.

## Spotting - What to look for when a competitor is solving

The console window/command line is used frequently in this challenge. The commands being run by the competitor will determine what portion of the challenge is being worked on.

- A console window open and the `hashcat` command being run indicates the competitor is close to answering the first question. Once they have cracked the hash, comparing it to the hash values is the final step to determine the username.
- The "scanner" application webpage open and all results returning "Pass" as signified by a circled checkmark icon, a green background, and the word pass. This indicates that the server with the hostname they are checking has been fully remediated. Once all six servers are remediated, running the grading check is the final step before completing the challenge.
