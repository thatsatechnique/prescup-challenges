#!/bin/python
import logging
import paramiko
import subprocess
import os

##### PROGRESS SO FAR #####
# The start up for the SSH key task is done; just need to modify the variables below 
# I think the others will be similar (just copying tokens over), but need to actually do those first to confirm

## MITM CHALLENGE

MITMTOKEN_USER = "user"
MITMTOKEN_HOST1 = "phantom.us"
MITMTOKEN_HOST2 = "oblivion.us"
MITMTOKEN_TOPO = "tokenOblivion"
MITMTOKEN_FILE = f"/home/{MITMTOKEN_USER}/src/token.txt"  # File the MITM token should be stored to

## SSH CHALLENGE
SSHTOKEN_USER = "user"
SSHTOKEN_HOST = "champion.us"
SSHTOKEN_TOPO = "tokenChampion"  
SSHTOKEN_FILE = f"/home/{SSHTOKEN_USER}/token.txt"  # File the SSH token should be stored to

## VAULT CHALLENGE
VAULTTOKEN_USER = "user"
VAULTTOKEN_HOST = "honor.us"
VAULTTOKEN_TOPO = "tokenHonor"
VAULTTOKEN_FILE = f"/home/{VAULTTOKEN_USER}/src/token.txt"  # File the VAULT token should be stored to

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

# Retrieve the token value from vmtools
def getTopoValue(name, default = "11deadbeef313373"):
    out = subprocess.run(f"vmtoolsd --cmd 'info-get guestinfo.{name}'", shell=True, capture_output=True)
    val = out.stdout.decode('utf-8').strip()
    if 'no' in val or name in val or val == "":
        logging.warning(f"USING DEFAULT VALUE for {name}!!!")
        return str(default)
    return str(val)

# Just need to copy the token over for this one
#  The public key has already been copied over
def loadMITM():
    token = getTopoValue(MITMTOKEN_TOPO)

    # Need to place on two servers
    for server in [MITMTOKEN_HOST1, MITMTOKEN_HOST2]:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Use the original, working SSH key
            client.connect(server, username=MITMTOKEN_USER, key_filename="/home/user/.ssh/id_rsa")
            logging.info(f"Connected to {server}, loading tokens")
            
            try:
                stdin, stdout, stderr = client.exec_command(f"echo '{token}' > {MITMTOKEN_FILE}")
                for line in stderr.readlines():
                    logging.error(f"stderr line for the MITM token {MITMTOKEN_TOPO} on {server}: {line}")
                    exit(-1)
                logging.info(f"MITM token {MITMTOKEN_TOPO} inserted into {MITMTOKEN_FILE} on {server}")
            except Exception as e:
                logging.error(f"Error loading MITM token {MITMTOKEN_TOPO} on {server}: {e}")
                exit(-1)
            client.close()
        except Exception as e:
            logging.error(f"Error connecting to {server}: {e}")
            exit(-1) 

# Handles setup for the SSH token
# WARNING: SSH key must be manually created first, and loaded onto the server
# The server must not allow password ssh
def loadSSHToken():
    # Get the token value
    token = getTopoValue(SSHTOKEN_TOPO)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use the original, working SSH key
        client.connect(SSHTOKEN_HOST, username=SSHTOKEN_USER, key_filename="/home/user/challengeServer/custom_scripts/ssh_keys/original/id_rsa")
        logging.info(f"Connected to {SSHTOKEN_HOST}, loading tokens")
        
        try:
            stdin, stdout, stderr = client.exec_command(f"echo '{token}' > {SSHTOKEN_FILE}")
            for line in stderr.readlines():
                logging.error(f"stderr line for the SSH token {SSHTOKEN_TOPO}: {line}")
                exit(-1)
            logging.info(f"SSH token {SSHTOKEN_TOPO} inserted into {SSHTOKEN_FILE}")
        except Exception as e:
            logging.error(f"Error loading SSH token {SSHTOKEN_TOPO}: {e}")
            exit(-1)
        client.close()
    except Exception as e:
        logging.error(f"Error connecting to {SSHTOKEN_HOST}: {e}")
        exit(-1) 

# Also just copy over the token
def loadVaultToken():
    # Get the token value
    token = getTopoValue(VAULTTOKEN_TOPO)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use the original, working SSH key
        client.connect(VAULTTOKEN_HOST, username=VAULTTOKEN_USER, key_filename="/home/user/.ssh/id_rsa")
        logging.info(f"Connected to {VAULTTOKEN_HOST}, loading tokens")
        
        try:
            stdin, stdout, stderr = client.exec_command(f"echo '{token}' > {VAULTTOKEN_FILE}")
            for line in stderr.readlines():
                logging.error(f"stderr line for the VAULT token {VAULTTOKEN_TOPO}: {line}")
                exit(-1)
            logging.info(f"VAULT token {VAULTTOKEN_TOPO} inserted into {VAULTTOKEN_FILE}")
        except Exception as e:
            logging.error(f"Error loading VAULT token {VAULTTOKEN_TOPO}: {e}")
            exit(-1)
        client.close()
    except Exception as e:
        logging.error(f"Error connecting to {VAULTTOKEN_HOST}: {e}")
        exit(-1) 

def installSteghide():
    # They require steghide. Install it for them
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use the original, working SSH key
        client.connect("kali-crucible.us", username="user", key_filename="/home/user/.ssh/id_rsa")
        logging.info(f"Connected to kali-crucible.us, installing steghide")
        
        try:
            stdin, stdout, stderr = client.exec_command(f" echo tartans | sudo apt -qq -y install steghide ")
            errors = ""
            for line in stderr.readlines():
                if line.strip() != "":
                    errors += f"{line}"
            if errors != "":
                logging.warning(f"stderr from installing steghide (probably safe to ignore): {errors}")
            logging.info(f"Steghide installed on kali")
        except Exception as e:
            logging.error(f"Error installing steghide: {e}")
            exit(-1)
        client.close()
    except Exception as e:
        logging.error(f"Error connecting to kali: {e}")
        exit(-1) 


if __name__ == '__main__':
    loadMITM()
    loadSSHToken()  # Move the token for the SSH task to the correct host
    loadVaultToken()
    installSteghide()




