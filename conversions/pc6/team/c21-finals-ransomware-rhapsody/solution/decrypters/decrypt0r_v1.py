#!/usr/bin/env python
# The Original Decrypter

import os
import subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from getpass import getpass
from glob import glob

def decrypt_file(file_path, output_path, key, iv):
    with open(file_path, 'rb') as encrypted_file:
        encrypted_data = encrypted_file.read()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
   
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()  
    unpadder = padding.PKCS7(AES.block_size).unpadder()
    decrypted_data = unpadder.update(decrypted_data) + unpadder.finalize()
    
    with open(output_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data)

if __name__ == '__main__':

    print("[<|]3CRYPT0R]")
    encrypted_dir = input("Enter encrypted file folder without ending slash (e.g. /home/user/file/subfile): ")
    aes_key = bytes.fromhex(getpass("Enter the AES key (hex format): "))
    aes_iv = bytes.fromhex(getpass("Enter the AES IV (hex format): "))
    decrypted_dir = input("Enter the directory to save decrypted files without ending slash: ")

    # Find a test file to check the key and IV
    test_files = glob(f"{encrypted_dir}/*.wNTD")
    if not test_files:
        print("NIC3 TRY! but no dice. Try AG41N...")
        exit(0)
    else:
        # Create directory only if right
        os.makedirs(decrypted_dir, exist_ok=True)

    success = True
    for file_path in test_files:
        basename = os.path.basename(file_path).replace('.wNTd', '')
        try:
            decrypt_file(file_path, f"{decrypted_dir}/{basename}.txt", aes_key, aes_iv)
        except Exception as e:
            print(f"Files failed to decrypt: {e}")
            success = False
            break

    if success:
        print(f" Decryption successful. Files saved in: {decrypted_dir}")
