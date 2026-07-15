# va_list Adventure

## Summary

In va_list Adventure, the competitor exploits a buffer overflow into the va_list to leak arbitrary memory addresses.

## VMs

This challenge uses the PC6 Stock Topology competitor network only.

#### Competitor Network

- challenge-server-modfather [OS: Ubuntu 22.04.04 Desktop, Network: (competitor challenge-net), IPv4: (10.5.5.5), Unlinked]
    - Runs the [Grading Script](./challenge/scripts/grader.py) to check the leaked addresses
    - Hosts file downloads (the binary and source code)

- kali [OS: Kali, Network: (competitor), IPv4: (DHCP), Linked]
    - President's Cup 6 default Kali system 

- exploit [OS: Ubuntu 22.04.04 Server, Network: (competitor), IPv4: (DHCP), Unlinked]
    - Runs the game to be exploited
    - User: `user` Password: `PwnTh3Dr4g0n!`

## Grading

The first two tasks use a [Grading Script](./challenge/scripts/grader.py). 

The grading script retrieves the `pointers.txt` file from the home directory of the `exploit.us`. This file contains the most recently generated addresses. These values are compared to those entered at `challenge.us`

## Troubleshooting Tips

#### Quick Look

- The adventure game is hosted as a service on port 31337 using xinetd.
    - The grading server does *NOT* check if this port is open as the connection would cause the addresses to be updated and mess up the grading script.
    - The logs for xinetd, however, are forwarded to gray log.
- The addresses needed as answers are logged on each grading attempt.

#### Quick Tips

- It is not uncommon for the addresses to be generated with non-printing special characters that cause the exploit to fail (as input from stdin is terminated early).
    - This will be resolved on a new attempt as the server generates a new address. I noticed this ocurring in about 1/20 attempts.

## Spotting - What to look for when a competitor is solving

1. The competitor should be using the source code, gdb or other tools to work out the structure of the provided binary.
2. As the exploit requires generating a payload using values leaked from the service, they will need some sort of scripting (for example, pwntools with python).