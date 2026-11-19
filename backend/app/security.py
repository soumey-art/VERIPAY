import hashlib, hmac, os, time
import jwt
from . import config


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + "$" + h.hex()

def check_password(pw: str, stored: str) -> bool:
    salt_hex, h_hex= stored.split("$")
    h = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(h.hex(), h_hex)

def make_token(user_id: int, role: str) -> str:
    return jwt.encode({"sub": str(user_id), "role": role, "exp": int(time.time()) + 8 * 3600}, config.JWT_SECRET, "HS256")


def read_token(token: str) -> dict:
    return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])