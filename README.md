# Bulk Certificate Generator API

Backend API built with Python, FastAPI, SQLAlchemy, and ReportLab to process bulk certificate generation requests asynchronously, track job progress, handle partial failures gracefully, and provide individual or bundled ZIP retrieval of generated certificates.

---

## Architecture & Design Decisions

1. **Framework (FastAPI)**:
   - Provides high-throughput async request handling, native Pydantic schema validation, and interactive OpenAPI documentation (`/docs`).

2. **Relational Database (SQLAlchemy + SQLite)**:
   - Tracks generation jobs and individual certificate records with explicit foreign-key relationships.
   - Statuses (`pending`, `processing`, `completed`, `failed`) and counters (`total_count`, `processed_count`, `success_count`, `failure_count`) are updated transactionally.

3. **Background Processing**:
   - Bulk certificate creation is dispatched to background workers (`BackgroundTasks`), returning an immediate `201 Created` response containing the `job_id` so clients can poll status without HTTP timeouts.

4. **Failure Isolation**:
   - Each recipient is processed in an isolated try-except block.
   - If rendering or data processing fails for one recipient, that individual record is marked as `failed` with its error reason stored in the database, while the remaining valid certificates continue processing uninterrupted.

5. **Predefined Vector Template (ReportLab)**:
   - Generates high-resolution, print-ready landscape A4 PDF certificates with geometric double borders, gold ribbon accents, dynamic typography, and unique certificate identifiers.

---

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── generator.py
│   ├── main.py
│   ├── models.py
│   ├── router.py
│   ├── schemas.py
│   └── service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   └── test_generator.py
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- `pip` package manager

### 2. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

---

## Running the Application

Start the development server using `uvicorn`:

```bash
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## Running Tests

Run the automated test suite with `pytest`:

```bash
py -m pytest -v
```

The test suite covers:
- Job creation and status tracking
- Schema validation (empty list, blank names, missing event fields)
- Background processing and counter tracking
- Resilient per-recipient failure isolation
- Single certificate PDF download
- Bulk certificates ZIP archive download
- Direct PDF vector generation and file integrity

---

## API Usage Guide

### 1. Submit a Certificate Generation Request

**Endpoint**: `POST /api/jobs`  
**Header**: `Content-Type: application/json`

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Cloud Native Architecture Masterclass",
    "issuer_name": "DevOps Global Academy",
    "issue_date": "2026-10-07",
    "recipients": [
      {
        "name": "Sarah Connor",
        "email": "sarah@example.com"
      },
      {
        "name": "John Smith",
        "email": "john@example.com"
      }
    ]
  }'
```

**Response (201 Created)**:
```json
{
  "id": "e4b2d358-1f63-4927-b8f9-467f56cf2821",
  "event_name": "Cloud Native Architecture Masterclass",
  "issuer_name": "DevOps Global Academy",
  "issue_date": "2026-10-07",
  "status": "pending",
  "total_count": 2,
  "processed_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "created_at": "2026-10-07T14:00:00Z",
  "completed_at": null
}
```

---

### 2. Check Job Status & Progress

**Endpoint**: `GET /api/jobs/{job_id}`

```bash
curl http://localhost:8000/api/jobs/e4b2d358-1f63-4927-b8f9-467f56cf2821
```

**Response (200 OK)**:
```json
{
  "id": "e4b2d358-1f63-4927-b8f9-467f56cf2821",
  "event_name": "Cloud Native Architecture Masterclass",
  "issuer_name": "DevOps Global Academy",
  "issue_date": "2026-10-07",
  "status": "completed",
  "total_count": 2,
  "processed_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "created_at": "2026-10-07T14:00:00Z",
  "completed_at": "2026-10-07T14:00:01Z",
  "certificates": [
    {
      "id": "90db2082-cd38-4e1b-b461-9f93976694e2",
      "recipient_name": "Sarah Connor",
      "recipient_email": "sarah@example.com",
      "status": "success",
      "error_message": null,
      "download_url": "/api/certificates/90db2082-cd38-4e1b-b461-9f93976694e2/download",
      "created_at": "2026-10-07T14:00:00Z"
    },
    {
      "id": "76fa9112-9c3e-4682-9f6b-71a25bc20da7",
      "recipient_name": "John Smith",
      "recipient_email": "john@example.com",
      "status": "success",
      "error_message": null,
      "download_url": "/api/certificates/76fa9112-9c3e-4682-9f6b-71a25bc20da7/download",
      "created_at": "2026-10-07T14:00:00Z"
    }
  ]
}
```

---

### 3. Download an Individual Certificate PDF

**Endpoint**: `GET /api/certificates/{certificate_id}/download`

```bash
curl http://localhost:8000/api/certificates/90db2082-cd38-4e1b-b461-9f93976694e2/download --output certificate.pdf
```

---

### 4. Download All Generated Certificates as ZIP

**Endpoint**: `GET /api/jobs/{job_id}/download`

```bash
curl http://localhost:8000/api/jobs/e4b2d358-1f63-4927-b8f9-467f56cf2821/download --output all_certificates.zip
```

---

### 5. List All Jobs

**Endpoint**: `GET /api/jobs?skip=0&limit=50`

```bash
curl http://localhost:8000/api/jobs
```
