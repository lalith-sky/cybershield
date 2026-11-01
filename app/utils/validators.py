"""
app/utils/validators.py
-------------------------
Small, dependency-free input validators shared across routes/services.
Kept simple and explicit rather than pulling in a forms library, since the
validation surface today is limited to auth fields.
"""

import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration(username: str, email: str, password: str, confirm_password: str) -> list:
    """Return a list of human-readable error strings (empty list = valid)."""
    errors = []

    if not username or not USERNAME_PATTERN.match(username.strip()):
        errors.append("Username must be 3-30 characters: letters, numbers, or underscores only.")

    if not email or not EMAIL_PATTERN.match(email.strip()):
        errors.append("Please enter a valid email address.")

    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    return errors


def validate_login(identifier: str, password: str) -> list:
    errors = []
    if not identifier or not identifier.strip():
        errors.append("Enter your username or email.")
    if not password:
        errors.append("Enter your password.")
    return errors
