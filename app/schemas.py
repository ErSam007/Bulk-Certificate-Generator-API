from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RecipientInput(BaseModel):
    name: str = Field(..., description="Full name of recipient")
    email: Optional[str] = Field(None, description="Email of recipient")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Recipient name cannot be empty")
        return clean

class JobCreateRequest(BaseModel):
    event_name: str = Field(..., description="Event or Course name")
    issuer_name: str = Field(..., description="Issuing Authority")
    issue_date: str = Field(..., description="Date of issuance")
    recipients: List[RecipientInput] = Field(..., description="List of recipients")

    @field_validator("event_name", "issuer_name", "issue_date")
    @classmethod
    def validate_strings(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be empty")
        return clean

    @field_validator("recipients")
    @classmethod
    def validate_recipients_non_empty(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipients list cannot be empty")
        return v

class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    issuer_name: str
    issue_date: str
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

class JobDetailResponse(JobSummaryResponse):
    certificates: List[CertificateResponse] = []
