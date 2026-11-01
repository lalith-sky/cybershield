"""
api_routes.py
-------------
JSON APIs powering the dashboard: URL scan, live stats, activity feed,
model info, and threat intelligence. Scan history is stored in SQLite
(embedded, zero-setup — no database server required).
"""

import csv
import io
from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user

from extensions import db
from app.database.models import Scan
from app.services import prediction_service, url_service

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Static MITRE ATT&CK reference mapping for the modules this platform detects.
THREAT_CATALOG = [
    {"id": "T1566", "name": "Phishing", "module": "phishing", "severity": "critical",
     "mitre": "T1566.001", "tactic": "Initial Access",
     "desc": "Malicious emails that trick users into revealing credentials or opening links."},
    {"id": "T1598", "name": "Phishing for Information", "module": "job_scam", "severity": "high",
     "mitre": "T1598.003", "tactic": "Reconnaissance",
     "desc": "Fake recruitment offers used to harvest fees and personal data from candidates."},
    {"id": "T1204", "name": "User Execution (Malicious Link)", "module": "url", "severity": "high",
     "mitre": "T1204.001", "tactic": "Execution",
     "desc": "Users lured into clicking links that lead to malicious or spoofed sites."},
    {"id": "T1583", "name": "Acquire Infrastructure: Domains", "module": "url", "severity": "medium",
     "mitre": "T1583.001", "tactic": "Resource Development",
     "desc": "Lookalike or randomly generated domains registered to host attacks."},
    {"id": "T1656", "name": "Impersonation", "module": "phishing", "severity": "medium",
     "mitre": "T1656", "tactic": "Defense Evasion",
     "desc": "Attackers posing as trusted brands, banks or recruiters."},
]


def _ago(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - dt).total_seconds())
    if s < 60: return f"{s}s ago"
    if s < 3600: return f"{s // 60} min ago"
    if s < 86400: return f"{s // 3600} h ago"
    return f"{s // 86400} d ago"


@api_bp.route("/scan-url", methods=["POST"])
def scan_url():
    data = request.get_json(silent=True) or {}
    result = url_service.analyze_url(data.get("url", ""), check_ssl=bool(data.get("check_ssl")))
    if "error" in result:
        return jsonify(result), 400
    try:
        db.session.add(Scan(
            user_id=current_user.id if current_user.is_authenticated else None,
            module="url", input_excerpt=result["url"][:300], prediction=result["verdict"],
            is_threat=result["is_threat"], confidence=float(result["risk_score"]),
            top_terms=",".join(i["text"][:40] for i in result["indicators"][:3]).replace(",", ";"),
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify(result)


@api_bp.route("/stats")
def stats():
    total = Scan.query.count()
    threats = Scan.query.filter_by(is_threat=True).count()
    by_module = {m: c for m, c in db.session.query(Scan.module, db.func.count(Scan.id)).group_by(Scan.module)}
    threat_by_module = {m: c for m, c in db.session.query(Scan.module, db.func.count(Scan.id))
                        .filter(Scan.is_threat.is_(True)).group_by(Scan.module)}

    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).replace(tzinfo=None)
    recent = Scan.query.filter(Scan.created_at >= since).all()
    buckets = [{"t": 0, "s": 0} for _ in range(24)]
    labels = [(now - timedelta(hours=23 - i)).strftime("%H:00") for i in range(24)]
    for s in recent:
        idx = 23 - int((now.replace(tzinfo=None) - s.created_at).total_seconds() // 3600)
        if 0 <= idx < 24:
            buckets[idx]["t" if s.is_threat else "s"] += 1

    rate = round(threats / total * 100, 1) if total else 0.0
    risk = round(min(10, rate / 10), 1)
    return jsonify({
        "total": total, "threats": threats, "safe": total - threats,
        "threat_rate": rate, "risk_score": risk,
        "risk_label": "Critical" if risk >= 7 else "Elevated" if risk >= 4 else "Low",
        "by_module": by_module, "threat_by_module": threat_by_module,
        "timeline": {"labels": labels, "threats": [b["t"] for b in buckets],
                     "safe": [b["s"] for b in buckets]},
    })


@api_bp.route("/activity")
def activity():
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))
    kind = request.args.get("type", "all")
    q = Scan.query
    if kind == "threat":
        q = q.filter_by(is_threat=True)
    elif kind in ("job_scam", "phishing", "url"):
        q = q.filter_by(module=kind)
    names = {"job_scam": "Job Scam Model", "phishing": "Phishing Model", "url": "URL Scanner"}
    out = []
    for s in q.order_by(Scan.created_at.desc()).limit(limit).all():
        out.append({
            "id": s.id, "module": names.get(s.module, s.module), "prediction": s.prediction,
            "is_threat": s.is_threat, "confidence": s.confidence, "excerpt": (s.input_excerpt or "")[:90],
            "ago": _ago(s.created_at),
            "level": "critical" if s.is_threat and (s.confidence or 0) >= 85 else "warning" if s.is_threat else "safe",
        })
    return jsonify(out)


@api_bp.route("/models")
def models():
    jm, pm = prediction_service.job_metrics, prediction_service.phishing_metrics
    return jsonify([
        {"key": "job_scam", "name": "JOB_SCAM_DETECTOR", "algo": "TF-IDF + Logistic Regression", "status": "active", "metrics": jm},
        {"key": "phishing", "name": "PHISH_DETECTOR", "algo": "TF-IDF + Logistic Regression", "status": "active", "metrics": pm},
        {"key": "url", "name": "URL_RISK_ENGINE", "algo": "Rule-based heuristic scoring", "status": "active", "metrics": None},
    ])


@api_bp.route("/threats")
def threats():
    counts = {m: c for m, c in db.session.query(Scan.module, db.func.count(Scan.id))
              .filter(Scan.is_threat.is_(True)).group_by(Scan.module)}
    items = [dict(t, detections=counts.get(t["module"], 0)) for t in THREAT_CATALOG]
    sev = Counter(t["severity"] for t in THREAT_CATALOG)
    return jsonify({"items": items, "severity_counts": sev, "total_detections": sum(counts.values())})


@api_bp.route("/export")
def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "time_utc", "module", "prediction", "is_threat", "confidence", "input_excerpt"])
    for s in Scan.query.order_by(Scan.created_at.desc()).limit(5000):
        w.writerow([s.id, s.created_at, s.module, s.prediction, s.is_threat, s.confidence,
                    (s.input_excerpt or "").replace("\n", " ")])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=cybershield_report.csv"})
