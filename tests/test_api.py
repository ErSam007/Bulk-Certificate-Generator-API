import zipfile
import io
from unittest.mock import patch
from app.service import process_job_certificates

def test_create_generation_job(client):
    payload = {
        "event_name": "Cloud Native Summit 2026",
        "issuer_name": "DevOps Institute",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"}
        ]
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["event_name"] == "Cloud Native Summit 2026"
    assert data["total_count"] == 2
    assert data["status"] == "pending"

def test_input_validation_empty_recipients(client):
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Tech Corp",
        "issue_date": "2026-10-07",
        "recipients": []
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_empty_recipient_name(client):
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Tech Corp",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "   ", "email": "empty@example.com"}
        ]
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_missing_event_name(client):
    payload = {
        "issuer_name": "Tech Corp",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422

def test_job_processing_and_status_tracking(client):
    payload = {
        "event_name": "Python Mastery",
        "issuer_name": "Code Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "David Miller", "email": "david@example.com"},
            {"name": "Emma Wilson", "email": "emma@example.com"}
        ]
    }
    create_res = client.post("/api/jobs", json=payload)
    job_id = create_res.json()["id"]

    process_job_certificates(job_id, client.session_factory)

    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200

    data = status_res.json()
    assert data["status"] == "completed"
    assert data["total_count"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert len(data["certificates"]) == 2

    for cert in data["certificates"]:
        assert cert["status"] == "success"
        assert cert["download_url"] is not None
        assert cert["error_message"] is None

def test_handling_individual_certificate_failure(client):
    payload = {
        "event_name": "Resilience Testing",
        "issuer_name": "QA Guild",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Frank White", "email": "frank@example.com"},
            {"name": "Grace Hopper", "email": "grace@example.com"}
        ]
    }
    create_res = client.post("/api/jobs", json=payload)
    job_id = create_res.json()["id"]

    real_generate = __import__("app.service", fromlist=["generate_certificate_pdf"]).generate_certificate_pdf

    def faulty_generate(*args, **kwargs):
        if kwargs.get("recipient_name") == "Grace Hopper":
            raise RuntimeError("Simulated render engine disk write failure")
        return real_generate(*args, **kwargs)

    with patch("app.service.generate_certificate_pdf", side_effect=faulty_generate):
        process_job_certificates(job_id, client.session_factory)

    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200

    data = status_res.json()
    assert data["status"] == "completed"
    assert data["total_count"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 1
    assert data["failure_count"] == 1

    cert_map = {c["recipient_name"]: c for c in data["certificates"]}
    assert cert_map["Frank White"]["status"] == "success"
    assert cert_map["Frank White"]["download_url"] is not None
    assert cert_map["Grace Hopper"]["status"] == "failed"
    assert "Simulated render engine disk write failure" in cert_map["Grace Hopper"]["error_message"]

def test_retrieve_single_certificate_download(client):
    payload = {
        "event_name": "Single Download Event",
        "issuer_name": "Authority",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Hannah Abbott", "email": "hannah@example.com"}
        ]
    }
    create_res = client.post("/api/jobs", json=payload)
    job_id = create_res.json()["id"]

    process_job_certificates(job_id, client.session_factory)

    status_res = client.get(f"/api/jobs/{job_id}")
    cert_id = status_res.json()["certificates"][0]["id"]

    dl_res = client.get(f"/api/certificates/{cert_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) > 1000

def test_retrieve_job_zip_download(client):
    payload = {
        "event_name": "Zip Download Event",
        "issuer_name": "Authority",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Ian Malcolm", "email": "ian@example.com"},
            {"name": "Julia Roberts", "email": "julia@example.com"}
        ]
    }
    create_res = client.post("/api/jobs", json=payload)
    job_id = create_res.json()["id"]

    process_job_certificates(job_id, client.session_factory)

    zip_res = client.get(f"/api/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        file_list = zf.namelist()
        assert len(file_list) == 2
        for fn in file_list:
            assert fn.endswith(".pdf")

def test_get_all_jobs(client):
    payload = {
        "event_name": "List Test Event",
        "issuer_name": "Authority",
        "issue_date": "2026-10-07",
        "recipients": [{"name": "Kevin Bacon", "email": "kevin@example.com"}]
    }
    client.post("/api/jobs", json=payload)

    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1

def test_non_existent_job_returns_404(client):
    res = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
