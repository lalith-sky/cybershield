"""
extensions.py
-------------
Flask extension instances are created here, uninitialized, and bound to the
app later via `init_app()` inside the application factory
(`app/__init__.py`). This indirection is what lets `app/database/models.py`,
`app/services/*`, and `app/routes/*` all import `db` / `login_manager`
without any circular-import issues.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to access that page."
login_manager.login_message_category = "warning"
