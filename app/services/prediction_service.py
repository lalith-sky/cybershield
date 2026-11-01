"""
app/services/prediction_service.py
-----------------------------------
Business/ML logic for running a threat-detection model against raw text.

This is a refactor, not a rewrite: `run_prediction` and `get_top_terms` are
the same logic that used to live directly inside app.py's route handlers.
Moving them here means:
  - route handlers stay thin (parse request -> call service -> return JSON)
  - the same prediction logic is reusable from multiple routes, tests, or
    future modules (Phase 2) without copy-pasting
  - model loading happens once, at import time, exactly as before
"""

import json
import os

import joblib

from ml.preprocess import clean_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")


def _load_artifact(filename: str):
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing model artifact: {path}. Run the training scripts in ml/ first "
            f"(python ml/train_model.py job / phishing)."
        )
    return joblib.load(path)


def _load_metrics(filename: str) -> dict:
    with open(os.path.join(MODELS_DIR, filename)) as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Load trained models + vectorizers once at import time (module-level
# singletons, matching the original app.py behavior).
# ----------------------------------------------------------------------

job_model = _load_artifact("job_scam_model.pkl")
job_vectorizer = _load_artifact("job_scam_vectorizer.pkl")
job_metrics = _load_metrics("job_scam_metrics.json")

phishing_model = _load_artifact("phishing_model.pkl")
phishing_vectorizer = _load_artifact("phishing_vectorizer.pkl")
phishing_metrics = _load_metrics("phishing_metrics.json")


def get_top_terms(vec, vectorizer, model, pred, top_n: int = 5) -> list:
    """Return the highest-weighted TF-IDF terms present in this input that
    pushed the model toward its predicted class (simple linear-model
    explainability using coef_ * tfidf_value)."""
    try:
        feature_names = vectorizer.get_feature_names_out()
        coefs = model.coef_[0]
        row = vec.tocoo()
        contributions = []
        for idx, val in zip(row.col, row.data):
            score = val * coefs[idx]
            # keep only terms that support the predicted class
            if (pred == 1 and score > 0) or (pred == 0 and score < 0):
                contributions.append((feature_names[idx], abs(score)))
        contributions.sort(key=lambda x: x[1], reverse=True)
        return [term for term, _ in contributions[:top_n]]
    except Exception:
        return []


def run_prediction(raw_text: str, model, vectorizer, positive_label: str, negative_label: str) -> dict:
    """Run the full predict pipeline: clean -> vectorize -> predict -> explain."""
    cleaned = clean_text(raw_text)
    if not cleaned.strip():
        return {"error": "Please enter some text to analyze."}

    vec = vectorizer.transform([cleaned])
    proba = model.predict_proba(vec)[0]  # [P(class 0), P(class 1)]
    pred = model.predict(vec)[0]

    confidence = float(max(proba)) * 100
    is_threat = bool(pred == 1)
    top_terms = get_top_terms(vec, vectorizer, model, pred)

    return {
        "prediction": positive_label if is_threat else negative_label,
        "is_threat": is_threat,
        "confidence": round(confidence, 2),
        "probabilities": {
            negative_label: round(float(proba[0]) * 100, 2),
            positive_label: round(float(proba[1]) * 100, 2),
        },
        "top_terms": top_terms,
    }


def predict_job(text: str) -> dict:
    return run_prediction(
        text, job_model, job_vectorizer,
        positive_label="Fraudulent Job Offer",
        negative_label="Genuine Job Offer",
    )


def predict_phishing(text: str) -> dict:
    return run_prediction(
        text, phishing_model, phishing_vectorizer,
        positive_label="Phishing Email",
        negative_label="Legitimate Email",
    )
