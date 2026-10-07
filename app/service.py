import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from app.config import STORAGE_DIR
from app.models import Job, CertificateRecord
from app.schemas import JobCreateRequest
from app.generator import generate_certificate_pdf

def utc_now():
    return datetime.now(timezone.utc)

def create_generation_job(db: Session, request: JobCreateRequest) -> Job:
    job = Job(
        id=str(uuid.uuid4()),
        event_name=request.event_name,
        issuer_name=request.issuer_name,
        issue_date=request.issue_date,
        status="pending",
        total_count=len(request.recipients),
        processed_count=0,
        success_count=0,
        failure_count=0,
        created_at=utc_now()
    )
    db.add(job)
    db.flush()

    for item in request.recipients:
        cert_record = CertificateRecord(
            id=str(uuid.uuid4()),
            job_id=job.id,
            recipient_name=item.name,
            recipient_email=item.email,
            status="pending",
            created_at=utc_now()
        )
        db.add(cert_record)

    db.commit()
    db.refresh(job)
    return job

def process_job_certificates(job_id: str, db_factory) -> None:
    db: Session = db_factory()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        job_dir = STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        certificates = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id).all()

        for cert in certificates:
            try:
                name_clean = cert.recipient_name.strip() if cert.recipient_name else ""
                if not name_clean:
                    raise ValueError("Recipient name cannot be empty")

                safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name_clean)[:30]
                filename = f"{safe_name}_{cert.id[:8]}.pdf"
                output_file = job_dir / filename

                generate_certificate_pdf(
                    output_path=output_file,
                    cert_id=cert.id,
                    recipient_name=name_clean,
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date
                )

                cert.status = "success"
                cert.file_path = str(output_file)
                cert.error_message = None
                job.success_count += 1

            except Exception as exc:
                cert.status = "failed"
                cert.error_message = str(exc)
                job.failure_count += 1

            job.processed_count += 1
            db.commit()

        job.status = "completed"
        job.completed_at = utc_now()
        db.commit()

    finally:
        db.close()

def get_job_by_id(db: Session, job_id: str) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id).first()

def list_jobs(db: Session, skip: int = 0, limit: int = 50) -> List[Job]:
    return db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

def get_certificate_by_id(db: Session, cert_id: str) -> Optional[CertificateRecord]:
    return db.query(CertificateRecord).filter(CertificateRecord.id == cert_id).first()

def create_job_zip_archive(job: Job) -> Optional[Path]:
    job_dir = STORAGE_DIR / job.id
    if not job_dir.exists():
        return None

    zip_path = STORAGE_DIR / f"{job.id}_certificates.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for cert in job.certificates:
            if cert.status == "success" and cert.file_path:
                file = Path(cert.file_path)
                if file.exists():
                    zip_file.write(file, arcname=file.name)

    return zip_path
