"""
app/routes/auth_routes.py
----------------------------
Registration, login, logout, and a minimal profile page.
Session management is handled by Flask-Login; passwords are hashed with
Werkzeug's generate_password_hash (PBKDF2) — never stored in plain text.

Enhanced with enterprise security logging and audit trail.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from datetime import datetime, timezone

from app.services.auth_service import AuthError, authenticate_user, register_user
from app.utils.validators import validate_login, validate_registration
from app.utils.logger import log_security_event
from app.database.models import Scan
from extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_client_ip():
    """Get the real client IP address, accounting for proxies."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    return request.remote_addr


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        ip_address = _get_client_ip()

        errors = validate_registration(username, email, password, confirm_password)
        if errors:
            for e in errors:
                flash(e, "error")
            log_security_event(
                "registration_failed",
                ip_address=ip_address,
                detail=f"Validation errors for username: {username}",
                success=False
            )
            return render_template("auth/register.html", username=username, email=email)

        try:
            user = register_user(username, email, password)
        except AuthError as e:
            flash(str(e), "error")
            log_security_event(
                "registration_failed",
                ip_address=ip_address,
                detail=f"Auth error: {str(e)}",
                success=False
            )
            return render_template("auth/register.html", username=username, email=email)

        login_user(user)
        
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        
        log_security_event(
            "registration_success",
            user_id=user.id,
            ip_address=ip_address,
            detail=f"New user: {username}",
            success=True
        )
        
        flash("Account created — welcome to CyberShield AI.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")
        
        ip_address = _get_client_ip()

        errors = validate_login(identifier, password)
        if errors:
            for e in errors:
                flash(e, "error")
            log_security_event(
                "login_failed",
                ip_address=ip_address,
                detail=f"Validation errors for identifier: {identifier}",
                success=False
            )
            return render_template("auth/login.html", identifier=identifier)

        try:
            user = authenticate_user(identifier, password)
        except AuthError as e:
            flash(str(e), "error")
            log_security_event(
                "login_failed",
                ip_address=ip_address,
                detail=f"Auth failed for identifier: {identifier}",
                success=False
            )
            return render_template("auth/login.html", identifier=identifier)

        login_user(user)
        
        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        
        log_security_event(
            "login_success",
            user_id=user.id,
            ip_address=ip_address,
            detail=f"User {user.username} logged in",
            success=True
        )
        
        flash(f"Welcome back, {user.username}.", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    user_id = current_user.id
    username = current_user.username
    ip_address = _get_client_ip()
    
    logout_user()
    
    log_security_event(
        "logout",
        user_id=user_id,
        ip_address=ip_address,
        detail=f"User {username} logged out",
        success=True
    )
    
    flash("You've been signed out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile")
@login_required
def profile():
    recent_scans = (
        Scan.query.filter_by(user_id=current_user.id)
        .order_by(Scan.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template("auth/profile.html", user=current_user, recent_scans=recent_scans)
