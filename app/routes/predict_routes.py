"""
app/routes/predict_routes.py
-------------------------------
ML prediction endpoints. `/predict/job` and `/predict/phishing` return the
exact same JSON shape as the original single-file app.py — no breaking
changes for the existing frontend.

New in this phase (additive, non-breaking):
  - Every successful prediction is now persisted as a Scan row, tagged to
    the current user if logged in (or anonymous if not).
  - GET /api/history        -> the current user's past scans (auth required)
  - GET /api/modules        -> metadata for every detection module, sourced
                                from the Threat lookup table
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from app.database.models import Scan, Threat
from app.services import prediction_service

predict_bp = Blueprint("predict", __name__)


def _record_scan(module: str, raw_text: str, result: dict) -> None:
    """Persist a completed prediction as scan history. Never lets a logging
    failure break the API response — errors are swallowed intentionally."""
    if "error" in result:
        return
    try:
        scan = Scan(
            user_id=current_user.id if current_user.is_authenticated else None,
            module=module,
            input_excerpt=raw_text[:300],
            prediction=result.get("prediction"),
            is_threat=result.get("is_threat", False),
            confidence=result.get("confidence"),
            top_terms=",".join(result.get("top_terms", [])),
        )
        db.session.add(scan)
        db.session.commit()
    except Exception:
        db.session.rollback()


@predict_bp.route("/predict/job", methods=["POST"])
def predict_job():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    result = prediction_service.predict_job(text)
    _record_scan("job_scam", text, result)
    return jsonify(result)


@predict_bp.route("/predict/phishing", methods=["POST"])
def predict_phishing():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    result = prediction_service.predict_phishing(text)
    _record_scan("phishing", text, result)
    return jsonify(result)


@predict_bp.route("/api/metrics")
def api_metrics():
    return jsonify({
        "job_scam": prediction_service.job_metrics,
        "phishing": prediction_service.phishing_metrics,
    })


@predict_bp.route("/api/modules")
def api_modules():
    """Metadata for every detection module (active + coming soon), read
    from the Threat lookup table so the frontend nav/threat-categories
    section (Phase 3) can be driven by data instead of hardcoded HTML."""
    threats = Threat.query.order_by(Threat.id.asc()).all()
    return jsonify([t.to_dict() for t in threats])


@predict_bp.route("/api/history")
@login_required
def api_history():
    """The current logged-in user's scan history, most recent first."""
    scans = (
        Scan.query.filter_by(user_id=current_user.id)
        .order_by(Scan.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([s.to_dict() for s in scans])
