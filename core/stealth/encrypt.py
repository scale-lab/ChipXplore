from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os

SECRET_KEY = os.environ.get("DB_ENCRYPTION_KEY", "this_is_a_32_byte_key".ljust(32).encode())

def encrypt_data(data, key=SECRET_KEY):
    """Encrypt data using AES (CBC mode)"""
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ciphertext).decode()

def decrypt_data(enc_data, key=SECRET_KEY):
    """Decrypt data using AES (CBC mode)"""
    enc_data = base64.b64decode(enc_data)
    iv, ciphertext = enc_data[:16], enc_data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size).decode()

# Example: Encrypting a database query result
query_result = "Design name: ChipX, Area: 100mm^2"
encrypted_result = encrypt_data(query_result)
print("Encrypted Query Result:", encrypted_result)