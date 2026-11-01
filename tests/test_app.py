import pytest
from app import create_app
from config import TestingConfig


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    with app.test_client() as c:
        yield c


def test_health(client):
    assert client.get("/health").json["status"] == "ok"


def test_job_scam_detected(client):
    r = client.post("/predict/job", json={"text": "Pay Rs 5000 registration fee via UPI to confirm your work from home job"})
    assert r.json["is_threat"] is True


def test_legit_email_safe(client):
    r = client.post("/predict/phishing", json={"text": "Hi team, attaching the minutes from today's sprint review."})
    assert r.json["is_threat"] is False


def test_empty_input_error(client):
    assert "error" in client.post("/predict/job", json={"text": ""}).json


def test_url_scanner_malicious_and_safe(client):
    bad = client.post("/api/scan-url", json={"url": "http://secure-paypal-login-verify.xyz/account"}).json
    good = client.post("/api/scan-url", json={"url": "https://github.com/user/repo"}).json
    assert bad["verdict"] == "MALICIOUS" and good["verdict"] == "SAFE"


def test_url_scanner_rejects_empty(client):
    assert client.post("/api/scan-url", json={"url": ""}).status_code == 400


def test_stats_reflect_scans(client):
    before = client.get("/api/stats").json["total"]
    client.post("/predict/job", json={"text": "Earn daily cash, pay $99 for kit"})
    assert client.get("/api/stats").json["total"] == before + 1


def test_dashboard_apis(client):
    for path in ["/api/activity", "/api/models", "/api/threats", "/api/export", "/dashboard"]:
        assert client.get(path).status_code == 200


def test_activity_handles_invalid_and_out_of_range_limits(client):
    assert client.get("/api/activity?limit=invalid").status_code == 200
    assert client.get("/api/activity?limit=0").status_code == 200
    assert client.get("/api/activity?limit=999").status_code == 200
