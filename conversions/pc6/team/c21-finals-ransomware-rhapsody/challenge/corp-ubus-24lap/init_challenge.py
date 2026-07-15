#!/usr/bin/env python3
"""
Ransomware Rhapsody (C21) — Local challenge initializer for corp-ubus-24lap.

Replaces the old pc6 SSH-based deployment (c21_stage1.py + c21_stage3.py).
All challenge setup now happens locally inside the victim container at boot.

Environment variables injected by CTF-NG via docker-compose:
  TOKEN1  — 12 hex chars — hidden folder name + decryptor name
  TOKEN2  — 12 hex chars — AES IV prefix (first 12 chars = first 6 bytes)
  TOKEN3  — 12 hex chars — ubuntu_service password
  TOKEN4  — PCCC{...}   — final flag revealed by Call_Mom
"""

import hashlib
import itertools
import os
import pwd
import random
import re
import secrets
import shutil
import stat
import string
import subprocess
import textwrap
from pathlib import Path

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ===========================================================================
# Constants
# ===========================================================================
PLAYER_USER = "user"
PLAYER_HOME = Path("/home/user")
PLAINTEXT_DIR = Path("/opt/challenge/plaintexts")
CACHE_DIR = Path("/tmp/.cache")
DEPLOY_MARKER = Path("/opt/challenge/.deployed")

# Read tokens from environment (injected by docker-compose)
TOKEN1 = os.environ["TOKEN1"]   # hidden folder name, 12 hex chars
TOKEN2 = os.environ["TOKEN2"]   # IV prefix, 12 hex chars
TOKEN3 = os.environ["TOKEN3"]   # service account password, 12 hex chars
TOKEN4 = os.environ["TOKEN4"]   # final PCCC token

# Total number of encrypted .wNTD files to generate (matches original ~100)
NUM_ENCRYPTED_FILES = 100


# ===========================================================================
# Helpers
# ===========================================================================
def run(cmd: str) -> None:
    """Run a shell command, raising on failure."""
    subprocess.run(cmd, shell=True, check=True)


def chown_recursive(path, user: str, group: str | None = None) -> None:
    path = str(path)
    if group is None:
        group = user
    run(f"chown -R {user}:{group} {path}")


def shlex_quote(s: str) -> str:
    """Shell-safe quoting."""
    return "'" + s.replace("'", "'\"'\"'") + "'"


def validate() -> None:
    """Sanity-check token formats before doing anything."""
    for name, value in {"TOKEN1": TOKEN1, "TOKEN2": TOKEN2, "TOKEN3": TOKEN3}.items():
        if not re.fullmatch(r"[0-9a-fA-F]{12}", value):
            raise ValueError(f"{name} must be exactly 12 hex characters, got: {value!r}")
    if not re.fullmatch(r"PCCC\{[A-Za-z0-9_-]+\}", TOKEN4):
        raise ValueError(f"TOKEN4 must look like PCCC{{...}}, got: {TOKEN4!r}")


def write_file(path: Path, content, mode: int = 0o644) -> None:
    """Write content (str or bytes) to a file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    os.chmod(path, mode)


def ensure_user(name: str, password: str) -> None:
    """Create a user if it doesn't exist; set its password either way."""
    try:
        pwd.getpwnam(name)
    except KeyError:
        run(f"useradd -m -s /bin/bash {name}")
    run(f"echo '{name}:{password}' | chpasswd")
    run(f"usermod -U {name}")
    run(f"usermod -s /bin/bash {name}")


def generate_random_hex(length: int = 32) -> str:
    """Generate a random hex string of the given length."""
    return secrets.token_hex(length // 2)


# ===========================================================================
# AES encryption (matches original pc6 encrypt_file)
# ===========================================================================
def aes_encrypt(content: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-CBC encrypt with PKCS7 padding."""
    padder = padding.PKCS7(128).padder()
    padded = padder.update(content) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    enc = cipher.encryptor()
    return enc.update(padded) + enc.finalize()


# ===========================================================================
# Zip password generation — matches original randomized L33T speak logic
# ===========================================================================
def generate_wanted_password() -> str:
    """
    Generate a randomized L33T speak password from the w4Nt3D word pool.
    This matches the original c21_stage1.py logic:
      - Pick 3 words from the pool
      - Randomize casing
      - Join with spaces
    """
    word_pool = [
        "w3", "we", "are", "4r3", "ar3", "th3", "the",
        "w4nt3d", "wanted", "w4nted", "want3d"
    ]

    # Pick 3 words (with replacement, then sample unique set)
    winners = [random.choice(word_pool) for _ in range(3)]
    chosen = random.sample(winners, 3)
    random.shuffle(chosen)
    base = " ".join(chosen)

    # Randomize casing
    randomized = "".join(
        c.upper() if random.choice([True, False]) else c.lower()
        for c in base
    )
    return randomized


# ===========================================================================
# Stage 1: Encrypted files + zip hint + decryptor placement
# ===========================================================================
def build_zip_hint(aes_key: bytes, zip_password: str) -> None:
    """Create the password-protected W3_WANT_Y0U.zip containing the AES key."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    hint_text = f" KEY: {aes_key.hex()}\n"
    hint_path = CACHE_DIR / "w4Nt3D.txt"
    write_file(hint_path, hint_text)
    zip_path = CACHE_DIR / "W3_WANT_Y0U.zip"
    run(f"zip -j -m -P {shlex_quote(zip_password)} {shlex_quote(str(zip_path))} {shlex_quote(str(hint_path))}")


def deterministic_decoy_name(seed: str, n: int) -> str:
    """Generate a deterministic 32-char hex filename for decoy files."""
    h = hashlib.sha256(f"{seed}-{n}".encode()).hexdigest()
    return f"{h[:32]}.wNTD"


def populate_tmp_clutter() -> None:
    """
    Create fake systemd-private directories and other /tmp artifacts that would
    normally exist on a real Ubuntu 22.04 system. This makes the real decryptor
    directory blend in rather than being the only thing in /tmp.
    """
    # Typical systemd-private directories seen on Ubuntu 22.04
    fake_services = [
        "systemd-logind.service",
        "systemd-resolved.service",
        "systemd-timesyncd.service",
        "ModemManager.service",
        "colord.service",
        "switcheroo-control.service",
        "upower.service",
    ]

    # Realistic files that would live inside each service's tmp/ subdir
    # on a real Ubuntu 22.04 system with active systemd services
    service_files = {
        "systemd-logind.service": [
            ("session-scope.conf", "# logind session scope config\nKillMode=process\nSlice=user.slice\n"),
            ("user-runtime-dir.lock", ""),
        ],
        "systemd-resolved.service": [
            ("resolved-stub.conf", "# Stub resolver config\nnameserver 127.0.0.53\noptions edns0 trust-ad\n"),
            ("dns-cache.tmp", os.urandom(256)),  # binary cache data
        ],
        "systemd-timesyncd.service": [
            ("clock", "2024-09-15T08:42:11+0000\n"),
            ("timesync.data", os.urandom(128)),
        ],
        "ModemManager.service": [
            ("mm-port-probe.log", "# port probe cache\n[2024-09-15] No modems detected\n"),
        ],
        "colord.service": [
            ("icc-profiles.cache", os.urandom(192)),
            ("mapping.db", os.urandom(320)),
        ],
        "switcheroo-control.service": [
            ("gpu-enum.cache", "# GPU enumeration\nRenderer: llvmpipe (LLVM 15.0.7, 256 bits)\nVendor: Mesa\n"),
        ],
        "upower.service": [
            ("history-charge.dat", "".join(
                f"1694769{i:04d}\t{random.uniform(45.0, 98.0):.1f}\t1\n" for i in range(20)
            )),
            ("history-rate.dat", "".join(
                f"1694769{i:04d}\t{random.uniform(8.0, 22.0):.1f}\t1\n" for i in range(15)
            )),
        ],
    }

    for svc in fake_services:
        fake_id = hashlib.md5(svc.encode()).hexdigest()
        svc_dir = Path(f"/tmp/systemd-private-{fake_id}-{svc}")
        tmp_subdir = svc_dir / "tmp"
        tmp_subdir.mkdir(parents=True, exist_ok=True)

        # Populate with realistic files
        for filename, content in service_files.get(svc, []):
            fpath = tmp_subdir / filename
            if isinstance(content, bytes):
                fpath.write_bytes(content)
            else:
                fpath.write_text(content, encoding="utf-8")

        # systemd-private dirs are owned by root and mode 700
        os.chmod(svc_dir, 0o700)

    # Other common /tmp artifacts
    misc_dirs = [
        "/tmp/.X11-unix",
        "/tmp/.ICE-unix",
        "/tmp/.font-unix",
        "/tmp/.XIM-unix",
        "/tmp/snap-private-tmp",
    ]
    for d in misc_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Socket files in X11-unix (typical on desktop Ubuntu)
    Path("/tmp/.X11-unix/X0").touch(exist_ok=True)

    # A few stale temp files
    for name in [".vscode-server-lock", ".bash_completion.tmp", "tracker-extract-files.0"]:
        p = Path(f"/tmp/{name}")
        p.touch(exist_ok=True)


def deploy_decryptor(hidden_name: str) -> None:
    """
    Place the decryptor in /tmp/systemd-private-<id>-ntpupdate-timezone.service/<TOKEN1>
    This mimics the original VM path structure. The directory blends in among
    the other fake systemd-private dirs created by populate_tmp_clutter().
    """
    # Generate a fake systemd private directory ID
    fake_id = hashlib.md5(TOKEN1.encode()).hexdigest()
    systemd_dir = Path(f"/tmp/systemd-private-{fake_id}-ntpupdate-timezone.service")
    systemd_dir.mkdir(parents=True, exist_ok=True)
    target = systemd_dir / hidden_name
    shutil.copy2("/opt/challenge/decrypt0r_v2.py", target)
    os.chmod(target, 0o755)
    chown_recursive(systemd_dir, PLAYER_USER)


def stage_encrypted_files(
    ransom_dir: Path,
    aes_key: bytes,
    aes_iv: bytes,
    zip_password: str,
) -> None:
    """
    Generate NUM_ENCRYPTED_FILES .wNTD files in the ransomed directory.

    One file contains XOR-encoded credentials (ubuntu_service / TOKEN3),
    matching the original c21_stage1.py behavior. One file is named after
    the AES IV hex (the "hidden in plain sight" clue). The rest are random.
    """
    cred_index = secrets.randbelow(NUM_ENCRYPTED_FILES)
    iv_index = secrets.randbelow(NUM_ENCRYPTED_FILES)

    # Ensure credential file and IV-named file are different
    while iv_index == cred_index:
        iv_index = secrets.randbelow(NUM_ENCRYPTED_FILES)

    for i in range(NUM_ENCRYPTED_FILES):
        if i == cred_index:
            # Build XOR-encoded credential file (matches original logic)
            target_size = 20840
            key_bytes = zip_password.encode()
            cred_set = f"| ubuntu_service / {TOKEN3} |".encode()
            payload_size = len(cred_set)
            pad_size = (target_size - payload_size - len(key_bytes)) // 2

            plain_content = (
                os.urandom(pad_size)
                + cred_set
                + os.urandom(target_size - payload_size - len(key_bytes) - pad_size)
                + key_bytes
            )

            # XOR everything except the trailing key_bytes (left as plaintext hint)
            xored = bytes(
                b ^ kb
                for b, kb in zip(
                    plain_content[: -len(key_bytes)],
                    itertools.cycle(key_bytes),
                )
            )
            content = xored + key_bytes
        else:
            content = os.urandom(20840)

        # Name one file after the full AES IV hex
        if i == iv_index:
            file_name = f"{aes_iv.hex()}.wNTD"
        else:
            file_name = deterministic_decoy_name(TOKEN1 + TOKEN2 + TOKEN3, i)

        encrypted_content = aes_encrypt(content, aes_key, aes_iv)
        write_file(ransom_dir / file_name, encrypted_content, 0o644)


def stage_player_workspace() -> None:
    """Add optional breadcrumb notes in the player's home directory."""
    home_notes = PLAYER_HOME / "Notes"
    write_file(
        home_notes / "incident_brief.txt",
        textwrap.dedent("""\
            Internal notes:
            - Encrypted files are still present on disk.
            - The actor liked hiding things in plain sight.
            - Do not assume every filename is random noise.
        """),
    )
    chown_recursive(home_notes, PLAYER_USER)


# ===========================================================================
# Stage 3: ubuntu_service user + Call_Mom binary + final token
# ===========================================================================
def stage_service_user() -> None:
    """
    Create the ubuntu_service account with TOKEN3 as password, place the
    Call_Mom script on its Desktop, and create the README hint.
    """
    ensure_user("ubuntu_service", TOKEN3)
    desktop = Path("/home/ubuntu_service/Desktop")
    desktop.mkdir(parents=True, exist_ok=True)

    # Combined password = "." + token1 + token2 + token3
    combined_password = "." + TOKEN1 + TOKEN2 + TOKEN3

    call_mom = textwrap.dedent(f"""\
        #!/bin/bash
        set -euo pipefail
        read -rsp 'Enter the password: ' INPUT_PASSWORD
        echo
        if [ "$INPUT_PASSWORD" == "{combined_password}" ]; then
            echo -n " Dialing"
            echo -e "................" | pv -qL 3
            echo -e "Connected\\n" | pv -qL 10
            echo -e "\\e[31m[!] ==== OPERATOR DETECTED ==== [!]\\e[0m\\n" | pv -qL 10
            echo -e "I guess it was inevitable but do know this is only the beginning.\\n" | pv -qL 20
            echo -e "If you are reading this, that means we failed ... for now :)\\n\\n" | pv -qL 10
            echo -e "[^_^] My regards: {TOKEN4}\\n" | pv -qL 10
            echo -e "\\e[32m[>] Signed [<]\\e[0m \\e[96mChase\\e[0m\\n\\n" | pv -qL 5
            echo -e "...\\n" | pv -qL 5
            echo -e "Disconnected"
        else
            echo "Incorrect password."
            exit 1
        fi
    """)

    readme = textwrap.dedent("""\
        Unity is key. All calls will be answered as they are received.

        Operator note:
        No one ever remembers the punctuation at the front.
    """)

    write_file(desktop / "Call_Mom", call_mom, 0o755)
    write_file(desktop / "README.txt", readme, 0o644)
    chown_recursive(Path("/home/ubuntu_service"), "ubuntu_service")


# ===========================================================================
# Main
# ===========================================================================
def main() -> None:
    # Idempotency guard — don't re-deploy on container restart
    if DEPLOY_MARKER.exists():
        print("[init_challenge] Already deployed, skipping.")
        return

    print("[init_challenge] Validating tokens...")
    validate()

    print("[init_challenge] Ensuring player user...")
    ensure_user(PLAYER_USER, "tartans")

    # Generate AES key material
    aes_key = secrets.token_bytes(32)
    aes_iv = bytes.fromhex(TOKEN2) + secrets.token_bytes(10)
    if len(aes_iv) != 16:
        raise RuntimeError(f"AES IV length is {len(aes_iv)}, expected 16")

    # Generate randomized L33T zip password (matches original behavior)
    zip_password = generate_wanted_password()
    print(f"[init_challenge] Zip password: {zip_password}")

    # Create the ransomed directory
    ransom_dir = PLAYER_HOME / f".{TOKEN1}"
    ransom_dir.mkdir(parents=True, exist_ok=True)

    print("[init_challenge] Populating /tmp with realistic clutter...")
    populate_tmp_clutter()

    print("[init_challenge] Building zip hint...")
    build_zip_hint(aes_key, zip_password)

    print("[init_challenge] Deploying decryptor...")
    deploy_decryptor(TOKEN1)

    print("[init_challenge] Staging encrypted files...")
    stage_encrypted_files(ransom_dir, aes_key, aes_iv, zip_password)

    print("[init_challenge] Setting up player workspace...")
    stage_player_workspace()

    print("[init_challenge] Creating ubuntu_service user + Call_Mom...")
    stage_service_user()

    # Fix ownership
    chown_recursive(ransom_dir, PLAYER_USER)
    chown_recursive(CACHE_DIR, PLAYER_USER)

    # Clean up bash history to match original VM behavior
    run("rm -f /root/.bash_history /home/user/.bash_history 2>/dev/null || true")

    # Mark as deployed
    write_file(DEPLOY_MARKER, "ok\n", 0o600)
    print("[init_challenge] Deployment complete.")


if __name__ == "__main__":
    main()
