from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_certificate_pdf(
    output_path: Path,
    cert_id: str,
    recipient_name: str,
    event_name: str,
    issuer_name: str,
    issue_date: str
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = landscape(A4)
    c = canvas.Canvas(str(output_path), pagesize=(width, height))

    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.rect(0, 0, width, height, stroke=0, fill=1)

    c.setStrokeColor(colors.HexColor("#0F172A"))
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)

    c.setStrokeColor(colors.HexColor("#D97706"))
    c.setLineWidth(1.5)
    c.rect(28, 28, width - 56, height - 56)

    corner_size = 24
    corners = [
        (28, height - 28 - corner_size),
        (width - 28 - corner_size, height - 28 - corner_size),
        (28, 28),
        (width - 28 - corner_size, 28)
    ]
    c.setFillColor(colors.HexColor("#E2E8F0"))
    c.setStrokeColor(colors.HexColor("#0F172A"))
    c.setLineWidth(1)
    for cx, cy in corners:
        c.rect(cx, cy, corner_size, corner_size, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#D97706"))
    c.rect(width / 2 - 100, height - 32, 200, 5, stroke=0, fill=1)

    c.setFont("Times-Bold", 30)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF ACHIEVEMENT")

    c.setStrokeColor(colors.HexColor("#D97706"))
    c.setLineWidth(1.5)
    c.line(width / 2 - 140, height - 132, width / 2 + 140, height - 132)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#B45309"))
    c.drawCentredString(width / 2, height - 165, "THIS IS PROUDLY PRESENTED TO")

    c.setFont("Times-Bold", 36)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawCentredString(width / 2, height - 230, recipient_name)

    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(0.8)
    c.line(width / 2 - 200, height - 245, width / 2 + 200, height - 245)

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(
        width / 2,
        height - 285,
        "For outstanding performance, dedication, and successful completion of"
    )

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawCentredString(width / 2, height - 325, event_name)

    left_x = 130
    right_x = width - 290
    sig_y = 100

    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(left_x, sig_y + 25, left_x + 160, sig_y + 25)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(left_x + 80, sig_y + 32, issue_date)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(left_x + 80, sig_y + 10, "DATE ISSUED")

    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(right_x, sig_y + 25, right_x + 160, sig_y + 25)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(right_x + 80, sig_y + 32, issuer_name)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(right_x + 80, sig_y + 10, "AUTHORIZED SIGNATURE")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawCentredString(width / 2, 45, f"Certificate ID: {cert_id}")

    c.showPage()
    c.save()
