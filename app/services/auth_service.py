"""
app/services/auth_service.py
------------------------------
Business logic for registration, authentication, and audit logging.
Kept separate from app/routes/auth_routes.py so the route handlers stay
thin and this logic is independently testable.
"""

from datetime import datetime, timezone

from extensions import db
from app.database.models import Log, User


class AuthError(Exception):
    """Raised for any user-facing registration/login failure."""


def register_user(username: str, email: str, password: str) -> User:
    """Create a new user account.

    Raises AuthError with a human-readable message if validation fails or
    the username/email is already taken.
    """
    username = username.strip()
    email = email.strip().lower()

    if User.query.filter_by(username=username).first():
        raise AuthError("That username is already taken.")
    if User.query.filter_by(email=email).first():
        raise AuthError("An account with that email already exists.")

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    _log(user.id, "register", f"New account created: {username}")
    return user


def authenticate_user(identifier: str, password: str) -> User:
    """Verify credentials by username OR email. Raises AuthError on failure."""
    identifier = identifier.strip().lower()
    user = User.query.filter(
        (db.func.lower(User.username) == identifier) | (db.func.lower(User.email) == identifier)
    ).first()

    if not user or not user.check_password(password):
        # Deliberately vague message: never reveal whether the username
        # or the password was the wrong part.
        _log(user.id if user else None, "login_failed", f"Failed login attempt for '{identifier}'")
        raise AuthError("Invalid username/email or password.")

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    _log(user.id, "login_success", f"User '{user.username}' logged in")
    return user


def _log(user_id, action: str, detail: str, ip_address: str = None) -> None:
    entry = Log(user_id=user_id, action=action, detail=detail, ip_address=ip_address)
    db.session.add(entry)
    db.session.commit()
