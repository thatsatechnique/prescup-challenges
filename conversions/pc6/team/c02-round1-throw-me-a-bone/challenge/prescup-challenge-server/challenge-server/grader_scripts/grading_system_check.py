#!/usr/bin/env python3

import paramiko, logging

# Define Static Variables
username = 'scanuser' # Username to connect to remote system with
password = '2th3st@rs' # Password to connect to remote system with
user_list = ['lrobinson', 'eclark', 'awright', 'sscott', 'dgreen', 'hcarter'] # Define list of usernames to check if present on a given system

# Configure basic logging
logging.basicConfig(filename='/var/log/gradingCheck.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def check_system(host):
    '''
    This is a variation of the system_check.py script used by the Scanner Application
    It is modified and used as a helper function for the c02_grading_check.py script
    '''

    result = {"rootLogin": None, "users": {}, "homeDir": {}, "passwdPerm": None, "shdwPerm": None}

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=15) # Connect to remote system via username and password, timeout after 15 seconds
        logging.info(f"Connecting to host: {host}")

        # Check if PermitRootLogin is still configured
        stdin, stdout, stderr = ssh.exec_command("(sudo egrep -q '^\s*PermitRootLogin\s+yes' /etc/ssh/sshd_config && echo fail) || (sudo egrep -q '^\s*#\s*PermitRootLogin\s+' /etc/ssh/sshd_config && echo pass) || echo pass")
        root_output = stdout.read().decode().strip()
        if root_output == "pass":
            result["rootLogin"] = "Pass"
        else:
            result["rootLogin"] = "Fail"
            logging.info(f"Fail - Login as root is still permitted on {host}")

        # Check if users are present on system using exit code from id command
        # A successful exit code means the user is still present on the system
        for user in user_list:
            stdin, stdout, stderr = ssh.exec_command(f'id -u {user}')
            if stdout.channel.recv_exit_status() == 0:
                result["users"][user] = "Fail"
                logging.info(f"Fail - User {user} is still present on {host}")
            else:
                result["users"][user] = "Pass"

        # Check if a user's /home directory was moved to /archived_users
        for user in user_list:
            stdin, stdout, stderr = ssh.exec_command(f"(test -d '/home/{user}/' && echo 'fail') || (test -d '/home/archived_users/{user}/' && echo 'pass')")
            user_dir = stdout.read().decode().strip()
            if user_dir == "pass":
                result["homeDir"][user] = "Pass"
            else:
                result["homeDir"][user] = "Fail"
                logging.info(f"Fail - User {user}'s home directory has not been moved on {host}")

        # Check the file permissions of etc/passwd
        stdin, stdout, stderr = ssh.exec_command("stat -c %a /etc/passwd")
        pass_perm = stdout.read().decode().strip()
        if pass_perm == "644":
            result["passwdPerm"] = "Pass"
        else:
            result["passwdPerm"] = "Fail"
            logging.info(f"Fail - /etc/passwd is currently set to {pass_perm}")

        # Check the file permissions of /etc/shadow
        stdin, stdout, stderr = ssh.exec_command("stat -c %a /etc/shadow")
        shdw_perm = stdout.read().decode().strip()
        if shdw_perm == "640":
            result["shdwPerm"] = "Pass"
        else:
            result["shdwPerm"] = "Fail"
            logging.info(f"Fail - /etc/shadow is currently set to {shdw_perm}")

        ssh.close()
    except Exception as e:
        logging.error(f"Grading Check Error on {host}: Error Message is {e}")

    logging.info(f"Overall Result of {host} : {result}")
    return result
