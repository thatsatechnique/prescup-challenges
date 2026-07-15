#!/usr/bin/env python3
"""
Ransomware Rhapsody (C21) — Token 2 Solver

Token 2 is the first 12 characters of the AES IV used to encrypt the .wNTD
files. One of the ~100 .wNTD filenames IS the IV in hex (32 chars = 16 bytes).

The challenge decryptor (decrypt0r_v2.py) is interactive and uses getpass,
making it awkward to automate. This solver replaces it entirely: it performs
AES-CBC decryption directly, testing each 32-hex-char filename as a candidate
IV against the encrypted files.

How to identify the correct IV:
  In AES-CBC, a wrong IV only corrupts the first 16 bytes of the first block.
  Since all plaintext is random bytes, we can't tell correct from incorrect by
  looking at content. HOWEVER, the decryptor validates ALL files — if even one
  file fails PKCS7 unpadding, it's the wrong key (not wrong IV though).

  The real trick: with the CORRECT key, ALL IVs produce valid unpadding (since
  padding depends only on the last block, not the IV). So the solver uses the
  decryptor's own behavior as the oracle — it feeds each IV to the decryptor
  via pexpect and checks for "Decryption successful".

  BUT since we've determined that any IV works with the correct key, we instead
  take a smarter approach: decrypt all files with each candidate IV and check
  which IV produces the cleanest first-block output on the CREDENTIAL file
  (the one with the XOR-encoded ubuntu_service creds). With the correct IV,
  the credential file's first 16 bytes will be proper random padding bytes
  matching the original os.urandom() output.

  In practice, the simplest reliable method is: try each candidate IV with the
  actual decryptor and see which one it accepts. This solver automates that.

Prerequisites:
  - Know the encrypted directory path (the hidden folder from Token 1)
  - Have the AES key (from cracking and unzipping W3_WANT_Y0U.zip)
  - The decryptor binary is on the system (named same as Token 1)

Usage:
    # Automated: feed each IV to the decryptor
    python3 token2_solver.py <encrypted_dir> --aes-key <hex> --decryptor <path>

    # List-only mode: just show all IV candidates (try them yourself)
    python3 token2_solver.py <encrypted_dir> --list-only

    # Direct mode: skip the decryptor, decrypt with each IV using cryptography
    python3 token2_solver.py <encrypted_dir> --aes-key <hex> --direct

Example:
    python3 token2_solver.py /home/user/Desktop/.ab12cd34ef56/Ransomed \\
        --aes-key deadbeef0123456789abcdef01234567 \\
        --decryptor /home/user/ab12cd34ef56
"""

import argparse
import glob
import os
import sys
import tempfile

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("[!] 'cryptography' package required: pip3 install cryptography")
    sys.exit(1)


def get_iv_candidates(encrypted_dir: str) -> list[tuple[str, str]]:
    """
    Collect all .wNTD filenames that are valid 32-hex-char IV candidates.
    Returns list of (hex_string, filepath).
    """
    wntd_files = sorted(glob.glob(os.path.join(encrypted_dir, "*.wNTD")))
    candidates = []
    for fpath in wntd_files:
        basename = os.path.basename(fpath).replace(".wNTD", "")
        if len(basename) != 32:
            continue
        try:
            raw = bytes.fromhex(basename)
            if len(raw) == 16:
                candidates.append((basename, fpath))
        except ValueError:
            continue
    return candidates


def aes_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-CBC decrypt with PKCS7 unpadding."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(data) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(decrypted) + unpadder.finalize()


def try_iv_with_decryptor(
    decryptor_path: str, encrypted_dir: str, aes_key_hex: str, iv_hex: str
) -> bool:
    """
    Feed the IV to the interactive decryptor via pexpect.
    Returns True if decryptor reports success.
    """
    try:
        import pexpect
    except ImportError:
        print("[!] pexpect required for --decryptor mode: pip3 install pexpect")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        child = pexpect.spawn(decryptor_path, timeout=30)

        child.expect(r".*folder.*:")
        child.sendline(encrypted_dir)

        child.expect(r".*Key.*:")
        child.sendline(aes_key_hex)

        child.expect(r".*IV.*:")
        child.sendline(iv_hex)

        idx = child.expect([
            r".*save.*:",          # Accepted — asking for output dir
            r".*funny stuff.*",    # Rejected
            r".*TRY.*",           # Wrong key/IV
            pexpect.EOF,
        ])

        if idx == 0:
            child.sendline(tmpdir)
            child.expect(pexpect.EOF)
            output = child.before.decode()
            return "successful" in output.lower()
        else:
            child.close()
            return False


def try_iv_direct(
    encrypted_dir: str, key: bytes, iv: bytes, max_test: int = 5
) -> bool:
    """
    Directly decrypt a few .wNTD files with the given IV.
    Returns True if all succeed (PKCS7 unpadding valid).

    NOTE: In practice, PKCS7 unpadding succeeds for any IV when the key is
    correct (padding depends on last block, not IV). This method confirms
    the key is correct but can't distinguish the real IV from decoys.
    """
    wntd_files = sorted(glob.glob(os.path.join(encrypted_dir, "*.wNTD")))
    tested = 0
    for fpath in wntd_files[:max_test]:
        with open(fpath, "rb") as f:
            data = f.read()
        try:
            aes_decrypt(data, key, iv)
            tested += 1
        except Exception:
            return False
    return tested > 0


def main():
    parser = argparse.ArgumentParser(
        description="Ransomware Rhapsody — Token 2 Solver (AES IV finder)"
    )
    parser.add_argument("encrypted_dir", help="Directory containing .wNTD files")
    parser.add_argument("--aes-key", help="AES key in hex (from cracked zip)")
    parser.add_argument(
        "--decryptor",
        help="Path to the decryptor binary (for interactive testing mode)",
    )
    parser.add_argument(
        "--direct", action="store_true",
        help="Use direct AES decryption instead of the decryptor binary",
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="Just list all IV candidates — don't test them",
    )
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  Ransomware Rhapsody — Token 2 Solver")
    print("  Finds the AES IV from .wNTD filenames")
    print("=" * 60)
    print()

    # Collect IV candidates
    candidates = get_iv_candidates(args.encrypted_dir)
    wntd_total = len(glob.glob(os.path.join(args.encrypted_dir, "*.wNTD")))

    print(f"[*] {wntd_total} total .wNTD files")
    print(f"[*] {len(candidates)} are valid IV candidates (32 hex chars)")
    print()

    if not candidates:
        print("[!] No valid IV candidates found!")
        sys.exit(1)

    # --list-only: just print candidates
    if args.list_only:
        print("[*] All IV candidates (first 12 chars = TOKEN2 answer):")
        print()
        for iv_hex, fpath in candidates:
            print(f"    {iv_hex}  ->  TOKEN2 = {iv_hex[:12]}")
        print()
        print(f"[*] One of these is the real IV. Try each with the decryptor,")
        print(f"    or use --direct / --decryptor mode to test automatically.")
        return

    # Need AES key for testing modes
    if not args.aes_key:
        print("[!] --aes-key required for testing mode (or use --list-only)")
        sys.exit(1)

    try:
        key = bytes.fromhex(args.aes_key)
    except ValueError:
        print("[!] Invalid hex for --aes-key")
        sys.exit(1)
    if len(key) not in (16, 24, 32):
        print(f"[!] AES key must be 16/24/32 bytes, got {len(key)}")
        sys.exit(1)

    # --decryptor mode: use the interactive decryptor as oracle
    if args.decryptor:
        if not os.path.isfile(args.decryptor):
            print(f"[!] Decryptor not found: {args.decryptor}")
            sys.exit(1)

        print(f"[*] Testing each IV against decryptor: {args.decryptor}")
        print()

        for i, (iv_hex, fpath) in enumerate(candidates, 1):
            print(f"  [{i}/{len(candidates)}] Trying IV: {iv_hex[:16]}...", end="  ")
            if try_iv_with_decryptor(
                args.decryptor, args.encrypted_dir, args.aes_key, iv_hex
            ):
                print("SUCCESS!")
                print()
                print("=" * 60)
                print(f"  TOKEN 2 = {iv_hex[:12]}")
                print(f"  Full IV = {iv_hex}")
                print("=" * 60)
                return
            else:
                print("failed")

        print()
        print("[!] No IV worked — is the AES key correct?")
        sys.exit(1)

    # --direct mode: decrypt directly (validates key, lists all passing IVs)
    if args.direct:
        print("[*] Direct mode: testing each IV via AES-CBC decryption")
        print()
        print("    NOTE: In CBC mode, wrong IV only corrupts the first 16 bytes.")
        print("    PKCS7 padding (last block) is unaffected by IV choice.")
        print("    All candidates will likely pass if the key is correct.")
        print("    The real IV is the one whose first 12 chars = TOKEN2.")
        print()

        valid = []
        for i, (iv_hex, fpath) in enumerate(candidates, 1):
            iv = bytes.fromhex(iv_hex)
            ok = try_iv_direct(args.encrypted_dir, key, iv)
            status = "PASS" if ok else "FAIL"
            print(f"  [{i}/{len(candidates)}] {iv_hex}  {status}")
            if ok:
                valid.append(iv_hex)

        print()
        if valid:
            print(f"[+] {len(valid)} IVs passed (key is correct)")
            print()
            print("[*] All valid IVs and their TOKEN2 values:")
            for v in valid:
                print(f"    {v}  ->  TOKEN2 = {v[:12]}")
            print()
            if len(valid) == len(candidates):
                print("[*] All candidates passed (expected — padding is IV-independent).")
                print("[*] Submit each TOKEN2 candidate until one is accepted,")
                print("    or use --decryptor mode for exact identification.")
        else:
            print("[!] No IVs passed — wrong AES key?")
            sys.exit(1)


if __name__ == "__main__":
    main()
