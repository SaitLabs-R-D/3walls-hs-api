import string, re
from urllib.parse import urlparse

_ALLOWED_DOMAIN_CHARS = string.ascii_letters + string.digits + "-."

_ALLOWED_EMAIL_CHARS = string.ascii_letters + string.digits + "!#$%&'*+-/=?^_`{|}~@."


def valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False

    if not 1 <= len(email) <= 320:
        return False
    elif not "@" in email:
        return False
    elif not "." in email:
        return False

    email_username, email_domain = email.rsplit("@", 1)

    if not 1 <= len(email_username) <= 64:
        return False
    elif not 1 <= len(email_domain) <= 255:
        return False
    elif not 1 <= email_domain.count("."):
        return False
    elif email_domain.startswith(".") or email_domain.endswith("."):
        return False
    elif set(email_domain).difference(_ALLOWED_DOMAIN_CHARS):
        return False
    elif set(email_username).difference(_ALLOWED_EMAIL_CHARS):
        return False

    return True


def valid_password(password: str) -> bool:
    if not isinstance(password, str):
        return False

    if not 8 <= len(password) <= 64:
        return False

    if not re.search(r"[a-zA-Z]", password):
        return False
    elif not re.search(r"[0-9]", password):
        return False

    return True


def valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
