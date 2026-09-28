import hashlib
import hmac
import secrets
from .db import fetch_one, execute

ITERATIONS = 310_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"),
            bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def register_user(name, email, password, phone=""):
    email = email.strip().lower()
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        return False, "An account with this email already exists."
    user_id = execute(
        "INSERT INTO users(name,email,phone,password_hash,role) VALUES(?,?,?,?,?)",
        (name.strip(), email, phone.strip(), hash_password(password), "customer")
    )
    return True, f"Account created successfully. User ID: {user_id}"

def authenticate(email, password):
    user = fetch_one("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    if user and verify_password(password, user["password_hash"]):
        return dict(user)
    return None
