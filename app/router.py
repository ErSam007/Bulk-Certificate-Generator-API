from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas import (
    JobCreateRequest,
    JobSummaryResponse,
    JobDetailResponse,
    CertificateResponse
)
from app.service import (
    create_generation_job,
    process_job_certificates,
    get_job_by_id,
    list_jobs,
    get_certificate_by_id,
    create_job_zip_archive
)

router = APIRouter(prefix="/api", tags=["Certificates"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Bulk Certificate Generator API"
    }

@router.post("/jobs", response_model=JobSummaryResponse, status_code=status.HTTP_201_CREATED)
def submit_generation_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = create_generation_job(db, request)
    background_tasks.add_task(process_job_certificates, job.id, SessionLocal)
    return job

@router.get("/jobs", response_model=List[JobSummaryResponse])
def get_all_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return list_jobs(db, skip=skip, limit=limit)

@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found"
        )

    cert_responses = []
    for cert in job.certificates:
        cert_responses.append(
            CertificateResponse(
                id=cert.id,
                recipient_name=cert.recipient_name,
                recipient_email=cert.recipient_email,
                status=cert.status,
                error_message=cert.error_message,
                download_url=f"/api/certificates/{cert.id}/download" if cert.status == "success" else None,
                created_at=cert.created_at
            )
        )

    return JobDetailResponse(
        id=job.id,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        created_at=job.created_at,
        completed_at=job.completed_at,
        certificates=cert_responses
    )

@router.get("/jobs/{job_id}/download")
def download_job_certificates_zip(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found"
        )

    if job.status == "pending" or job.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is still '{job.status}'. Please wait until completion."
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No certificates were generated successfully for this job."
        )

    zip_file = create_job_zip_archive(job)
    if not zip_file or not zip_file.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate ZIP archive."
        )

    return FileResponse(
        path=str(zip_file),
        media_type="application/zip",
        filename=f"job_{job_id[:8]}_certificates.zip"
    )

@router.get("/certificates/{certificate_id}/download")
def download_single_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    cert = get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found"
        )

    if cert.status != "success" or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation did not succeed. Status: {cert.status}"
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file does not exist on disk."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name
    )
