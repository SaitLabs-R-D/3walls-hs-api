import secrets
import string
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

ALPHABET = string.ascii_letters + string.digits


def generate_password() -> str:

    return "".join(secrets.choice(ALPHABET) for _ in range(16))


def hash_password(password: str) -> str:
    return ph.hash(password)


# compare a given password with a hashed password
def check_password(hashed_password: str, password: str) -> bool:

    try:
        ph.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
