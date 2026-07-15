#!/usr/bin/env python3
"""
Ransomware Rhapsody (C21) — AES IV Bruteforcer & Batch Decryptor
 
The encrypted directory has ~100 .wNTD files. One filename IS the AES IV
(32 hex chars = 16 bytes). All other filenames are also 32 hex chars
(SHA256 fragments), so they're indistinguishable by format alone.
 
KEY INSIGHT: In AES-CBC mode, a wrong IV only corrupts the first 16 bytes
of the decrypted output — everything from byte 17 onward is correct. Since
the credential data is buried deep in the file (~byte 10000+), we can
decrypt with ANY valid-length IV and still recover the important content.
 
This script:
  1. Decrypts ALL .wNTD files using the first valid IV-length filename
  2. Scans decrypted files for the credential pattern (ubuntu_service/TOKEN3)
  3. Reports the credentials and lists all IV candidates
 
Usage:
    python3 iv_finder.py <encrypted_dir> <aes_key_hex>
    python3 iv_finder.py /home/user/Desktop/Ransomed deadbeef01234567...
 
After finding credentials, su to ubuntu_service and run Call_Mom.
"""
 
import argparse
import glob
import itertools
import os
import re
import sys
import time
 
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
 
 
def decrypt_file(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-CBC decrypt with PKCS7 unpadding."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(decrypted) + unpadder.finalize()
 
 
def find_cred_file(decrypted_files: dict[str, bytes]) -> tuple[str, str, str] | None:
    """
    Scan decrypted files for the credential pattern.
 
    The credential file contains XOR-encoded data with the zip password
    appended in plaintext at the end. The zip password is 3 L33T words
    separated by spaces (e.g., "aRE wE 4r3").
 
    We try multiple tail lengths since random bytes before the password
    may also be printable ASCII. For each candidate tail, we XOR-decode
    and search for 'ubuntu_service / <TOKEN3>'.
 
    Returns (filename, username, token3) or None.
    """
    # The zip password is 3 words from the pool, each 2-6 chars, with spaces.
    # Min length: "w3 w3 w3" = 8, Max: "wanted wanted wanted" = 20
    # With casing randomization, length stays the same.
 
    for fname, data in decrypted_files.items():
        # Try different tail lengths from 6 to 25 characters
        for tail_len in range(6, 26):
            if tail_len > len(data):
                continue
 
            candidate_tail = data[-tail_len:]
 
            # Check if this tail is entirely printable ASCII
            if not all(0x20 <= b <= 0x7E for b in candidate_tail):
                continue
 
            zip_pw = candidate_tail.decode("ascii")
 
            # Quick sanity: should contain at least one space (3 words)
            if " " not in zip_pw:
                continue
 
            # XOR-decode the content (minus tail) with this candidate password
            key_bytes = zip_pw.encode()
            encoded_portion = data[: len(data) - len(key_bytes)]
            decoded = bytes(
                b ^ kb
                for b, kb in zip(encoded_portion, itertools.cycle(key_bytes))
            )
 
            # Search for the credential pattern: | ubuntu_service / <hex> |
            match = re.search(rb"\|\s*(\w+)\s*/\s*([0-9a-fA-F]{8,})\s*\|", decoded)
            if match:
                username = match.group(1).decode()
                token3 = match.group(2).decode()
                return fname, username, token3
 
    return None
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Brute-force AES IV from .wNTD filenames and decrypt all files"
    )
    parser.add_argument("encrypted_dir", help="Directory containing .wNTD files")
    parser.add_argument("aes_key", help="AES key in hex (from the cracked zip)")
    parser.add_argument(
        "-o", "--output",
        help="Output dir for decrypted files (default: <dir>_decrypted)",
    )
    args = parser.parse_args()
 
    print("=" * 60)
    print("  Ransomware Rhapsody — IV Finder & Batch Decryptor")
    print("=" * 60)
    print()
 
    # Validate key
    try:
        key = bytes.fromhex(args.aes_key)
    except ValueError:
        print(f"[!] Invalid hex key")
        sys.exit(1)
    if len(key) not in (16, 24, 32):
        print(f"[!] AES key must be 16/24/32 bytes, got {len(key)}")
        sys.exit(1)
 
    # Find all .wNTD files
    wntd_files = sorted(glob.glob(os.path.join(args.encrypted_dir, "*.wNTD")))
    if not wntd_files:
        print(f"[!] No .wNTD files found in {args.encrypted_dir}")
        sys.exit(1)
 
    print(f"[*] Found {len(wntd_files)} .wNTD files")
    print(f"[*] AES key: {args.aes_key[:16]}...{args.aes_key[-8:]}")
 
    # Filter filenames that are valid 32-hex-char IVs
    iv_candidates = []
    for fpath in wntd_files:
        basename = os.path.basename(fpath).replace(".wNTD", "")
        try:
            candidate = bytes.fromhex(basename)
            if len(candidate) == 16:
                iv_candidates.append((basename, fpath))
        except ValueError:
            continue
 
    print(f"[*] {len(iv_candidates)} filenames are valid IV candidates (32 hex chars)")
    print()
 
    if not iv_candidates:
        print("[!] No valid IV-length filenames found!")
        sys.exit(1)
 
    # In AES-CBC, wrong IV only corrupts first 16 bytes.
    # The credential data is at byte ~10000+, so ANY IV works to recover it.
    # Use the first candidate to decrypt everything.
    chosen_iv_hex, _ = iv_candidates[0]
    iv = bytes.fromhex(chosen_iv_hex)
 
    print(f"[*] Decrypting all files (using IV candidate: {chosen_iv_hex[:16]}...)")
    print(f"    NOTE: In CBC mode, wrong IV only corrupts first 16 bytes.")
    print(f"    Credential data is deep in the file, so it's recovered regardless.")
    print()
 
    output_dir = args.output or f"{args.encrypted_dir.rstrip('/')}_decrypted"
    os.makedirs(output_dir, exist_ok=True)
 
    decrypted_files = {}
    errors = 0
    start = time.time()
 
    for fpath in wntd_files:
        basename = os.path.basename(fpath).replace(".wNTD", "")
        with open(fpath, "rb") as f:
            encrypted_data = f.read()
        try:
            plaintext = decrypt_file(encrypted_data, key, iv)
            out_path = os.path.join(output_dir, f"{basename}.txt")
            with open(out_path, "wb") as f:
                f.write(plaintext)
            decrypted_files[basename] = plaintext
        except Exception as e:
            errors += 1
            print(f"  [!] Failed: {basename} -> {e}")
 
    elapsed = time.time() - start
    print(f"[+] Decrypted {len(decrypted_files)} files in {elapsed:.1f}s")
    if errors:
        print(f"[!] {errors} files failed (wrong AES key?)")
    print(f"[+] Output: {output_dir}/")
    print()
 
    # Now search for the credential file
    print("[*] Scanning decrypted files for credentials...")
    result = find_cred_file(decrypted_files)
 
    if result:
        fname, username, token3 = result
        print()
        print("=" * 60)
        print(f"  🔑 CREDENTIALS FOUND in: {fname}.wNTD")
        print(f"  Username: {username}")
        print(f"  Password: {token3}")
        print("=" * 60)
        print()
        print(f"  Next steps:")
        print(f"    su {username}        # enter password: {token3}")
        print(f"    cd ~/Desktop")
        print(f"    ./Call_Mom           # password hint: '.' + token1 + token2 + token3")
    else:
        print("[!] Credential pattern not found automatically.")
        print(f"[*] Try searching manually:")
        print(f"    strings {output_dir}/*.txt | grep -i 'ubuntu\\|service\\|token'")
 
    print()
    print(f"[*] All {len(iv_candidates)} IV candidates (one is the real IV):")
    for iv_hex, fpath in iv_candidates:
        print(f"    {iv_hex}")
 
 
if __name__ == "__main__":
    main()
