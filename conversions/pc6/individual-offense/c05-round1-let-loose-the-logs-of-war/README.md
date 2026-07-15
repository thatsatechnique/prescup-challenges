# Let Loose the Logs of War

Cry "Havoc!", and exploit a web server running in a Docker container to retrieve tokens.

**NICE Work Roles**

- [Exploitation Analyst](https://niccs.cisa.gov/tools/nice-framework/)
- [Vulnerability Analyst](https://niccs.cisa.gov/tools/nice-framework/)

**NICE Tasks**

- [T0266](https://niccs.cisa.gov/tools/nice-framework/): Perform penetration testing as required for new or updated applications.
- [T0591](https://niccs.cisa.gov/tools/nice-framework/): Perform analysis for target infrastructure exploitation activities.

## Background

Exploit a web server running in a Docker container to retrieve two tokens. One from inside the container, one from the host that runs it.

## Getting Started

Navigate to `http://web` and probe for any vulnerabilities in the web server. Use the `/home/user/wordlist.txt` on Kali to perform a brute force attack with the username `Admin`. Once you've gained access, explore the system to uncover and retrieve the two tokens.

Please note: The web server may take several minutes to start up.

## System and Tool Credentials

|system/tool|username|password|
|-----------|--------|--------|
|kali|user|password|

## Tokens

- Token 1: Enter Token 1 found in the `/` directory of the web server container.
- Token 2: Enter Token 2 found in the `/home/user/` directory of the host system after breaking out of the Tomcat container accessed in Question 1.
