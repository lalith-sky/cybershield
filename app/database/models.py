"""
app/database/models.py
-----------------------
SQLAlchemy ORM models backing CyberShield AI's SQLite database.

Tables
------
User    - registered accounts (auth via Flask-Login)
Scan    - one row per prediction made through any /predict/* endpoint
Report  - a saved/exported write-up a user builds from one or more scans
Upload  - metadata for files submitted to the (future) file-analysis module
Threat  - lookup/reference table describing each detection module
Log     - lightweight audit trail (logins, registrations, failed attempts)

Only User and Scan are actively written to by this phase of the backend.
Report, Upload, and Threat are defined now so the schema is stable and
future phases (file analysis, dashboards, reporting) can build on top of it
without another migration; Log is used immediately for auth auditing.
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    last_login_at = db.Column(db.DateTime)

    scans = db.relationship("Scan", backref="user", lazy=True)
    reports = db.relationship("Report", backref="user", lazy=True)
    uploads = db.relationship("Upload", backref="user", lazy=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_public_dict(self) -> dict:
        """Safe subset of fields for JSON responses (never expose password_hash)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    # e.g. "job_scam", "phishing" — kept as a free string so new modules
    # (Phase 2) don't require a schema change, just a new value.
    module = db.Column(db.String(50), nullable=False, index=True)

    input_excerpt = db.Column(db.Text)  # truncated input, for history display
    prediction = db.Column(db.String(120))
    is_threat = db.Column(db.Boolean, default=False, index=True)
    confidence = db.Column(db.Float)
    top_terms = db.Column(db.Text)  # comma-separated, for quick display
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    reports = db.relationship("Report", backref="scan", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "module": self.module,
            "input_excerpt": self.input_excerpt,
            "prediction": self.prediction,
            "is_threat": self.is_threat,
            "confidence": self.confidence,
            "top_terms": self.top_terms.split(",") if self.top_terms else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)


class Upload(db.Model):
    __tablename__ = "uploads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filetype = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=_utcnow)


class Threat(db.Model):
    """Reference/lookup row describing a detection module (used to drive
    nav, the future 'threat categories' section, and module metadata APIs)."""

    __tablename__ = "threats"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # e.g. "job_scam"
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    status = db.Column(db.String(20), default="active")  # "active" | "coming_soon"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "icon": self.icon,
            "status": self.status,
        }


class Log(db.Model):
    """Lightweight audit trail for security-relevant events."""

    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)  # e.g. "login_success"
    detail = db.Column(db.String(255))
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)
