#!/usr/bin/python

import os
import sys
import paramiko
import sqlite3
import subprocess
import logging

server = os.environ.get("FINSTA_HOST", "finsta.pccc")
username = os.environ.get("FINSTA_SSH_USER", "user")
password = os.environ.get("FINSTA_SSH_PASSWORD", "L1k3AndSubscr1b3!?")

# ALL LOGGING GOES TO STDERR. stdout is reserved for the `key: Success/Failure - message`
# lines consumed by the challenge-server grader.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s')


def getTopoValue(name, default="11deadbeef313373"):
    val = os.environ.get(name, "").strip()
    if val == "":
        logging.warning(f"USING DEFAULT TOKEN for {name}!!!")
        return str(default)
    return str(val)


DB_LOCAL_PATH = "/tmp/socialmedia.db"


# Download the SQLite database so we can see which users we should visit
def getDB():
    logging.info("Downloading socialmedia.db...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, username=username, password=password)

        sftp = client.open_sftp()
        sftp.get("/home/user/app/instance/socialmedia.db", DB_LOCAL_PATH)
        sftp.close()
        client.close()
    except Exception as e:
        logging.error(f"Error retrieving socialmedia.db: {e}")
        print("GradingXSS: Failure - Greg did not find any posts about his interests")
        sys.exit(0)

    logging.info("Downloaded socialmedia.db")


def readPosts():
    try:
        con = sqlite3.connect(DB_LOCAL_PATH)
        cur = con.cursor()
        res = cur.execute("SELECT username, tags FROM Posts")
        posts = res.fetchall()
        con.close()
    except Exception as e:
        logging.error(f"Error querying socialmedia.db: {e}")
        print("GradingXSS: Failure - Greg did not find any posts about his interests")
        sys.exit(0)

    good_posts = []
    great_posts = []
    for post in posts:
        count = 0
        for hobby in ["SunBattles", "FightTool40k", "PuzzleofChairs", "KingoftheBracelets"]:
            if hobby in post[1]:
                count += 1
        if count >= 4:
            great_posts.append(post)
            continue  # So we don't also add to good_posts
        if count >= 1:
            good_posts.append(post)

    if len(great_posts) == 0:
        if len(good_posts) == 0:
            logging.info("Greg found no posts tagged with his interests")
            print("GradingXSS: Failure - Greg did not find any posts about his interests")
        else:
            logging.info("Greg found no posts tagged with all of his interests")
            print("GradingXSS: Failure - Greg found a post(s) that covered some of his interests, but kept scrolling")
        sys.exit(0)

    users_to_visit = []
    for post in great_posts:
        if post[0] not in users_to_visit:
            users_to_visit.append(post[0])
    return users_to_visit


# Call doXSS.js for each user
def runXSS(user, token):
    logging.info(f"Running XSS, visiting http://{server}/profile/{user}")
    try:
        result = subprocess.run(
            ["node", "/custom_scripts/xss/doXSS.js", user, token],
            shell=False,
            capture_output=True,
            cwd="/custom_scripts/xss",
        )
        logging.info(f"Got the following from stdout: {result.stdout}")
        logging.info(f"Got the following from stderr: {result.stderr}")
    except Exception as e:
        logging.warning(f"Potential error running XSS (note this may be acceptable): {e}")


if __name__ == '__main__':
    getDB()
    users = readPosts()
    token = getTopoValue("tokenXSS")
    for user in users:
        runXSS(user, token)
    if len(users) > 0:
        print(
            f"GradingXSS: Greg visited the profiles of the following users: "
            f"{', '.join(users)}. The token is in his cookie for you to extract."
        )
