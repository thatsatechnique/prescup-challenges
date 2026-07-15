# Throw Me A Bone

*Solution Guide*

## Overview

There are two components to this challenge. The first asks competitors to identify weak or commonly used passwords present in the `merch.codes` Active Directory. The second asks competitors to review a vulnerability report and make remediations on systems in the environment. 

Reminder, the credentials for the challenge systems/tools are:

- **kali:** user / password
- **all other servers:** user / tartans

## Question 1

*What is the username of the MERCH Domain account which is using a weak and/or commonly used password?*

1. On the **kali** system, in Firefox, download the `ntds.zip` and `wordlist.txt` files from `http://challenge.pccc/files`.
2. Extract the `ntds` folder from `ntds.zip`. Inside of the extracted `ntds` folder are the files `ntds.dit` and `SYSTEM`.
3. In the same folder as the `ntds.dit` and `SYSTEM` files, create a folder called `OUTPUT`. This is where the created hashdump files will be saved.
4. `Right-Click` in the `ntds` folder window and select `Open Terminal Here`.
5. Dump the hashes from the NTDS file using the following  `impacket-secretsdump` command in the Terminal window you just opened.  

```bash
impacket-secretsdump -ntds ntds.dit -system SYSTEM local -output ./OUTPUT/hash.txt
```

6. After the command has run, there will be three files in the `OUTPUT` directory. Rename the file `hash.txt.ntds` to just `hash.txt`. This is the hashdump file we will use to attempt to crack the passwords.
7. Move the files so that the `hash.txt` and `wordlist.txt` files are in the same directory.
8. Use `hashcat` to check for any weak or commonly used passwords. 

```bash
hashcat hash.txt wordlist.txt
```

9. In the `hashcat` output we see a hash that was cracked with a password `Winter2024!`. 

![hashcat output for NTLM mode 1000 against hash.txt using wordlist.txt. The status is Exhausted with 1/6 digests recovered; the cracked result `7209d1e2b55d242551d2e7aba8604e47:Winter2024!` is highlighted at the top, revealing the password "Winter2024!".](./img/hashcat-output.png "Cracking the NTLM hash with hashcat")


```bash
Approaching final keyspace - workload adjusted.           

7209d1e2b55d242551d2e7aba8604e47:Winter2024!  
```

10. Using the cracked hash, compare to the hashes in the `hash.txt` file. 

```bash
cat hash.txt | grep 7209d1e2b55d242551d2e7aba8604e47
```

It matches the password hash for user `ejohnson`.

![A Kali terminal running `cat hash.txt | grep 7209d1e2b55d242551d2e7aba8604e47`, returning the line `merch.codes\ejohnson:1103:...:7209d1e2b55d242551d2e7aba8604e47:::` with the username ejohnson highlighted — mapping the cracked NTLM hash to the user ejohnson.](./img/ejohnson.png "Cracked hash belongs to user ejohnson")

The answer to Question 1 is: `ejohnson`.

## Question 2

*What is the 8-digit hexadecimal code you received from the grading check (`challenge.pccc`) after remediating vulnerabilities on all servers in the environment?*

### Step 1: Identify the undocumented systems

On the **kali** system, in Firefox, download the *Scan Report* (`vulnerabilityReport.pdf`) from `http://challenge.pccc/files`.

The challenge instructions tell us there are six servers in the environment which need to be reviewed. However, only three systems are listed in the *Scan Report*. This detail is important because it suggests there are servers in the environment that haven't been scanned. You'll need to identify these undocumented systems. For reference, the six servers are:

- **Documented servers (in report):** `app-server`, `k3s-server`, `cato`
- **Undocumented servers (not in report):** `virginia`, `amicus`, `cassius`

Use `nmap` to perform a ping sweep of the network and identify all hosts with SSH (port 22) open. 

```bash
nmap -sn <network_range>
```

The scan results will reveal hosts running SSH services. Compare the discovered hosts against the servers listed in the vulnerability report to identify the undocumented systems.

### Step 2: Use the scanner application to check systems 

Within the challenge environment, the Scanner Application (`http://challenge.pccc:5555`) should be used to check the current remediation status of systems. Use this application to verify your remediations have been properly implemented. 

### Step 3: Implement remediations

#### Prevent login as root 

The targeted systems are: `app-server`, `virginia`, and `amicus`. To address this vulnerability, the `sshd_config` file needs to be modified to remove `PermitRootLogin yes`. Two approaches can be taken:

1. Comment out the line so it is no longer a part of the configuration. This is done by adding a `#` to the beginning of the line.
2. Change `yes` to `no` on the configuration line. 

Either approach will yield success when the Grading Check is run, provided it is applied to the correct systems. On each of the targeted systems, do the following: 

1. Access the targeted systems via SSH using the credentials from the challenge instructions. For example:

```bash
ssh user@app-server
```

2. With elevated permissions, use a text editor to open `sshd_config`. 

```bash
sudo nano /etc/ssh/sshd_config
```

3. Locate the `PermitRootLogin` configuration and add a `#` in front of the line. 

```text
#PermitRootLogin yes 
```

4. Exit, and save your change.
5. Restart the `sshd` service.

```bash
sudo systemctl restart sshd.service
```

6. Repeat the procedure above for each system.

#### Remove inactive user accounts and move `/home` directories

The targeted systems are: `cato`, `virginia`, and `cassius`. In the example below, user `jdoe` is removed and their home directory moved to the `archived_users` directory. The same commands can be used to remove users from the targeted systems; replace`jdoe` with the username you wish to remove.

```bash
sudo deluser jdoe
sudo mv /home/jdoe /home/archived_users/
```

But first, you have to identify the inactive user accounts. The challenge instructions say: “*(t)he list of users is confirmed and all of them are currently active.*” The `hash.txt` file created when you identified the commonly used passwords provides the usernames associated with each password hash. In other words, these are the active users for the environment. Compare *that* list of usernames against the user home directories on each system. The user directories that don't match the active list are considered *inactive* and should be removed. 

|System|Accounts to Remove| 
|------|------------------| 
|cato|dgreen, hcarter| 
|virginia|lrobinson, awright, dgreen| 
|cassius|eclark, sscott, hcarter| 

You may ask, "*Why the requirement to move home directories?*" Deleting a user account does not remove their `home` folder. If the folder is not deleted, it is possible a user added later could have the same UID and gain access to that folder. Moving the folder helps prevent this from happening while still allowing administrators access to the home directory if required. 

#### Change file permissions 

The targeted systems are: `app-server`, `amicus`, and  `cassius`. Depending on the system, either the `passwd` file or the `shadow` file needs to have file permissions changed. Run the appropriate command below on a targeted system.

```bash
sudo chmod 644 /etc/passwd
sudo chmod 640 /etc/shadow
```

## Challenge Grading 

> **Info** Prior to grading your results, you can use the the Scanner Application (`http://challenge.pccc:5555`) to check the current remediation status of systems. If everything in the scan results is green (i.e., **Pass**), then your remediations have been properly implemented. 

Once all remediations are applied, use an in-game browser to navigate to `http://challenge.pccc`. Click **Grade Challenge**. If all the necessary remediations are in place, you will receive an eight-character hexadecimal token. Enter this token as the answer to Question 2.