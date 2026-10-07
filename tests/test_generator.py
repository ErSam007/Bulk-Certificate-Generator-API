from pathlib import Path
from app.generator import generate_certificate_pdf

def test_generate_certificate_pdf_creates_valid_file(tmp_path):
    output_pdf = tmp_path / "test_certificate.pdf"
    
    generate_certificate_pdf(
        output_path=output_pdf,
        cert_id="CERT-TEST-001",
        recipient_name="John Doe",
        event_name="Full Stack Engineering Masterclass",
        issuer_name="Code Academy",
        issue_date="2026-10-07"
    )

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 1000

    with open(output_pdf, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"
