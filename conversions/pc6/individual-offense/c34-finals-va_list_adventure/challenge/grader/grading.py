#!/usr/bin/python3
import subprocess
import sys
import logging

logging.basicConfig(format='%(levelname)s | %(message)s', level=logging.INFO)

KEY = "/app/id_ed25519"
HOST = "user@exploit.pccc"
PTR = "/home/user/pointers.txt"
SSH_OPTS = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"


def fetch_addresses():
    """Pull the most recently generated addresses from the exploit box, then clear them so
    each guess requires a fresh run of the game (prevents brute-forcing the addresses)."""
    subprocess.run(f"scp -i {KEY} {SSH_OPTS} {HOST}:{PTR} /tmp/pointers.txt",
                   shell=True, capture_output=True)
    subprocess.run(f"ssh -i {KEY} {SSH_OPTS} {HOST} \"echo '' > {PTR}\"",
                   shell=True, capture_output=True)
    try:
        with open("/tmp/pointers.txt") as f:
            lines = [line.rstrip() for line in f if line.rstrip()]
        return lines[0], lines[1]
    except (IndexError, FileNotFoundError):
        return None, None


def matches(guess, answer):
    try:
        return int(guess, 16) == int(answer, 16)
    except (ValueError, TypeError):
        return None


def report(label, guess, answer):
    if answer is None:
        print(f"{label}: Run the adventure on exploit.pccc:31337 to generate new addresses, then grade.")
        return
    if guess is None:
        print(f"{label}: No value provided")
        return
    result = matches(guess, answer)
    if result is None:
        print(f"{label}: Invalid hexadecimal value {guess} (reconnect to exploit.pccc:31337 to try again)")
    elif result:
        print(f"{label}: Success - that is the correct address.")
    else:
        print(f"{label}: Incorrect address (reconnect to exploit.pccc:31337 to generate a new one and try again)")


if __name__ == '__main__':
    name_answer, player_answer = fetch_addresses()
    name_guess = sys.argv[1] if len(sys.argv) > 1 else None
    player_guess = sys.argv[2] if len(sys.argv) > 2 else None

    report("GradingName", name_guess, name_answer)
    report("GradingPlayer", player_guess, player_answer)
