# The Triple Lindy

Your team is tasked with performing a penetration test against a local community swimming pool. Find and exploit various web and SCADA/ICS vulnerabilities to ensure the pool's safe operation.

**NICE Work Roles**

- [Exploitation Analyst](https://niccs.cisa.gov/workforce-development/nice-framework/)
- [Cyber Operations](https://niccs.cisa.gov/workforce-development/nice-framework/)

**NICE Tasks**

- [T0028](https://niccs.cisa.gov/workforce-development/nice-framework/): Conduct and/or support authorized penetration testing on enterprise network assets.
- [T0570](https://niccs.cisa.gov/workforce-development/nice-framework/): Apply and utilize authorized cyber capabilities to enable access to targeted networks.
- [T0591](https://niccs.cisa.gov/workforce-development/nice-framework/): Perform analysis for target infrastructure exploitation activities.

## Background

Use the provided Kali machine to explore and exploit websites and SCADA/ICS systems while gathering data related to the operations of a local swimming pool.

## Getting Started

Log in to the Kali VM and browse to `http://townsville-pool.pccc` to start gathering information about the **Townsville Community Pool** technical operations.

If you are following along with the solution guide, please note that the domain names now end in `.pccc` rather than `.merch.codes`. 
The referenced `ctmodbus` program can be installed with `pip install ctmodbus`, then copy and execute the following Python script:
```Python
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from ctmodbus.commands import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
```

A DNS server is available at dns.pccc for resolving challenge hostnames. Use it with tools like nmap by adding the --dns-servers dns.pccc flag.

## Submissions

There are four (4) tokens to retrieve in this challenge. All tokens become available on the Townsville Community Pool website as they are unlocked by completing the tasks below. You may need to refresh the web page to see the token. Here are some additional details about each token:

- **Token 1:** Login to the Townsville Community Pool website as the Pool President.
- **Token 2:** Raise the pool temperature to at least 110 degrees Fahrenheit.
- **Token 3:** Disable the pool video camera system.
- **Token 4:** Complete the "Triple Lindy" by changing these three pool water balance values:
    1. Decrease the pH from 7.0 to 6.0.
    2. Increase the chlorine level from 3 ppm to 4 ppm.
    3. Decrease total alkalinity from 100 ppm to 70 ppm.

## System and Tool Credentials

|system/tool|username|password|
|-----------|--------|--------|
|kali|user|password|

