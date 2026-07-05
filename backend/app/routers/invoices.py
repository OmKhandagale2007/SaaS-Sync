import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_org
from app.models import Invoice, Organization
from app.schemas import InvoiceOut

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    invoices = (
        db.query(Invoice).filter(Invoice.org_id == org.id).order_by(Invoice.created_at.desc()).all()
    )
    return [
        InvoiceOut(
            id=i.id,
            invoice_number=i.invoice_number,
            product=i.product,
            amount=i.amount,
            due_date=i.due_date,
            status=i.status,
            customer_name=i.contact.name,
            customer_email=i.contact.email,
        )
        for i in invoices
    ]


@router.get("/export")
def export_invoices(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    invoices = (
        db.query(Invoice).filter(Invoice.org_id == org.id).order_by(Invoice.created_at.asc()).all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Invoice", "Customer", "Email", "Product", "Amount", "Due Date", "Status"])
    for i in invoices:
        writer.writerow(
            [i.invoice_number, i.contact.name, i.contact.email, i.product, f"{i.amount:.2f}", i.due_date, i.status]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoice-batch.csv"},
    )
