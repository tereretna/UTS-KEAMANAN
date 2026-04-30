import base64
from Crypto.Cipher import AES # type: ignore
from Crypto.Protocol.KDF import PBKDF2 # type: ignore
from Crypto.Hash import SHA256, HMAC # type: ignore
from Crypto.Random import get_random_bytes # type: ignore

def _derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(password.encode('utf-8'), salt, dkLen=32, count=100_000, prf=lambda p, s: HMAC.new(p, s, SHA256).digest())

def encrypt_aes(plaintext: str, password: str) -> str:
    salt, nonce = get_random_bytes(16), get_random_bytes(16)
    key = _derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    return base64.b64encode(salt + nonce + tag + ciphertext).decode('utf-8')

def decrypt_aes(encoded_str: str, password: str) -> str:
    try:
        data = base64.b64decode(encoded_str)
        salt, nonce, tag, ciphertext = data[:16], data[16:32], data[32:48], data[48:]
        key = _derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
    except Exception:
        raise ValueError("Gagal mendekripsi! Password salah atau data telah dimanipulasi.")