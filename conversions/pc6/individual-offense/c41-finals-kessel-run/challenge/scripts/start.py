#!/bin/python
import logging
import paramiko
import subprocess

server = "channel.us"
username = "user"
password = "Sc4nS0l0B3stSmuggl3r!!"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

def getTopoValue(name, default = "11deadbeef313373"):
    out = subprocess.run(f"vmtoolsd --cmd 'info-get guestinfo.{name}'", shell=True, capture_output=True)
    val = out.stdout.decode('utf-8').strip()
    if 'no' in val or name in val or val == "":
        logging.warning(f"USING DEFAULT VALUE for {name}!!!")
        return str(default)
    return str(val)

def loadToken(client, type):
    token = getTopoValue(f"token{type}")

    src = f"./proxies/{type.lower()}/token.original.html"
    dst = f"./proxies/{type.lower()}/token.html"
    try:
        stdin, stdout, stderr = client.exec_command(f"sed 's/TOKEN/{token}/g' {src} > {dst}")
        for line in stderr.readlines():
            logging.error(f"stderr line from token{type}: {line}")
            exit(-1)
        logging.info(f"Token{type} inserted into {dst}")
    except Exception as e:
        logging.error(f"Error loading token{type}: {e}")
        exit(-1)
        
if __name__ == '__main__':
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, username=username, password=password)
        logging.info(f"Connected to {server}, loading tokens")
        
        # Load 3 simple tokens
        loadToken(client, "Maelstrom")
        loadToken(client, "Maw")
        loadToken(client, "Kessel")

        client.close()
    except Exception as e:
        logging.error(f"Error connecting to {server}: {e}")
        exit(-1)    
    logging.info("Finished start up")



