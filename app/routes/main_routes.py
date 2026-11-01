"""
app/routes/main_routes.py
---------------------------
General-purpose, non-ML, non-auth routes: the landing page and health check.
"""

from flask import Blueprint, jsonify, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Redirect to the new enterprise dashboard"""
    from flask import redirect, url_for
    return redirect(url_for('main.dashboard'))


@main_bp.route("/dashboard")
def dashboard():
    """Enterprise cyberpunk dashboard"""
    return render_template("dashboard.html")


@main_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "CyberShield AI"})
