# Ransomware Rhapsody

In this challenge, challengers have stumbled upon a compromised system containing a collection of encrypted files. The adversary, in a bashful and hasty fashion, made a critical error on their exit. Your mission is to investigate the remnants of their work and let them know you're on to them.

**NICE Work Roles**
* [Digital Forensics](https://niccs.cisa.gov/workforce-development/nice-framework/work-role/digital-forensics)
* [Incident Response](https://niccs.cisa.gov/workforce-development/nice-framework/work-role/incident-response)
* [Exploitation Analysis](https://niccs.cisa.gov/workforce-development/nice-framework/work-role/exploitation-analysis)

**NICE Tasks**
* [T0108](https://niccs.cisa.gov/workforce-development/nice-framework/): Perform analysis of the incident to identify the affected systems, networks, and potential perpetrators.
* [T0115](https://niccs.cisa.gov/workforce-development/nice-framework/): Analyze collected information to identify vulnerabilities and leverage them to achieve objectives.

## Background
A crime syndicate called "The w4Nt3D" has infiltrated a corporate network. The asset challengers will have access to has been isolated and acts as the only point of access for triage.

As a Rapid Response Team (RRT), you and a team of incident responders and threat hunters are tasked to:
* Investigate the compromised system for encrypted corporate files
* Decrypt the associated files using any discovered encryption key sets
* Investigate the decrypted files to find a key used to communicate with the W4nt3D
* Execute the beacon to let them know you're on to them

## Getting Started

SSH into `corp-ubus-24lap` with the credentials below to begin.

## System and Tool Credentials

| System               | OS           | Username | Password |
|----------------------|--------------|----------|----------|
| corp-ubus-24lap      | Ubuntu 22.04 | user     | tartans  |

## Intelligence Brief

The Intelligence Community (IC) has recently released a light version of a dossier on "The w4Nt3D". Details below:

| Category               | Data |
|------------------------|------|
| **Leader**             | xCh4$3x |
| **Known Members**      | 36 |
| **Last Known Location**| Paris, France |
| **Tactics**            | The syndicate involved with this cyber event is named "The w4Nt3D". Be on the look out for any artifacts or references to this. They are notorious for hiding their payloads and malware in plain sight for the thrill of being chased by authorities and to mock their victims. They tend to play games with their victims in order to illicit a response from them. |
| **Signature**          | This syndicate has a tendency to put short form variants of their name in critical files on their victim's machines. |
| **Slogans**            | In primary communications, they often use slogans and "L33T Speak". |

## Tactics, Techniques and Procedures
* This syndicate will occasionally concatenate stolen tokens to create a master key that operators can use to `call home`.

**[IMPORTANT] NOTE**
Attacking or unauthorized access to the challenge server is **forbidden**. To complete this challenge, root is not required.
