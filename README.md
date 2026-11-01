# 🛡️ CyberShield AI — AI-Powered Cyber Threat Detection Platform

A Flask-based Security Operations dashboard that detects **phishing emails**, **fake job offers** and **malicious URLs** using machine learning and heuristic analysis, with explainable results and live analytics.

## Project Repository

This project is maintained at [github.com/lalith-sky/cybershield](https://github.com/lalith-sky/cybershield).

## Features
| Module | How it works |
|---|---|
| **Phishing Email Detector** | TF-IDF (1–2 grams) + Logistic Regression, with per-prediction explainability (top contributing terms) |
| **Fake Job Offer Detector** | Same NLP pipeline trained on recruitment-scam text |
| **URL Risk Scanner** | Offline heuristic engine: Shannon entropy, IP-literal hosts, punycode/homograph, brand impersonation, suspicious TLDs, shorteners, `@` tricks, optional live TLS check → 0–100 risk score |
| **SOC Dashboard** | Live KPIs, threat-distribution + 24h timeline charts (Chart.js), activity feed, auto-refresh |
| **ML Models page** | Live accuracy / precision / recall / F1 pulled from trained-model metrics |
| **Threat Intel** | Detection categories mapped to **MITRE ATT&CK** techniques with live detection counts |
| **Activity / Audit** | Filterable event timeline, one-click CSV report export |
| **Auth & Security** | Flask-Login, hashed passwords, OWASP security headers, rate limiting, security audit logging, custom error pages |

## Tech Stack
Python · Flask · scikit-learn · pandas · SQLAlchemy (embedded SQLite — no DB server to install) · Chart.js · vanilla JS/CSS · pytest

## Run locally
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                                        # http://localhost:5000
python -m pytest tests -q                            # run tests
python ml/train_model.py job && python ml/train_model.py phishing   # optional retrain
```

## API
| Endpoint | Description |
|---|---|
| `POST /predict/job` · `/predict/phishing` | `{"text": "..."}` → verdict, confidence, probabilities, top terms |
| `POST /api/scan-url` | `{"url": "...", "check_ssl": false}` → risk score, verdict, indicators |
| `GET /api/stats · /activity · /models · /threats` | Dashboard data |
| `GET /api/export` | CSV report of all scans |

## Project layout
```
app/        routes (main, auth, predict, api) · services (ML, URL, auth) · middleware · utils
ml/         dataset generation, preprocessing, training (with 5-fold CV)
models/     trained .pkl artifacts + metrics JSON
static/ templates/   dashboard UI
tests/      pytest suite
```

## ⚠️ Honest note on model metrics
The bundled datasets (1,100 samples each) are **synthetically generated from templates** (`ml/generate_datasets.py`), so held-out accuracy is ~100% — it reflects template similarity, not real-world performance. The models do generalise to hand-written samples in testing, but for production use, retrain on real corpora (e.g. UCI SMS Spam, Enron/Nazario phishing, the EMSCAD fake-job dataset). Be ready to explain this in interviews — it shows maturity.

## Resume bullets (copy/adapt)
- Built **CyberShield AI**, a full-stack threat-detection platform (Flask, scikit-learn) detecting phishing, fake job offers and malicious URLs through TF-IDF + Logistic Regression models with explainable term-level outputs.
- Engineered an offline URL risk engine (entropy, homograph, brand-impersonation and TLD heuristics) producing a 0–100 risk score, exposed via REST APIs.
- Developed a real-time SOC dashboard (Chart.js) with live KPIs, MITRE ATT&CK-mapped threat intel, audit timeline and CSV export; added OWASP security headers, rate limiting and a pytest suite.
