from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_org
from app.models import Contact, Invoice, Organization, SyncRun
from app.schemas import SyncRequest, SyncResult
from app.services.csv_processor import CsvValidationError, parse_csv_text
from app.services.sync_engine import run_sync

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _contact_to_out(c: Contact) -> dict:
    return {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "deal_count": c.deal_count}


def _invoice_to_out(i: Invoice) -> dict:
    return {
        "id": i.id,
        "invoice_number": i.invoice_number,
        "product": i.product,
        "amount": i.amount,
        "due_date": i.due_date,
        "status": i.status,
        "customer_name": i.contact.name,
        "customer_email": i.contact.email,
    }


@router.post("/run", response_model=SyncResult)
def run_sync_json(
    payload: SyncRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    rows = [r.model_dump() for r in payload.rows]
    if not rows:
        raise HTTPException(status_code=400, detail="No rows to sync.")
    result = run_sync(db, org, rows, payload.source_filename)
    result["contacts"] = [_contact_to_out(c) for c in result["contacts"]]
    result["invoices"] = [_invoice_to_out(i) for i in result["invoices"]]
    return result


@router.post("/run-csv", response_model=SyncResult)
async def run_sync_csv(
    file: UploadFile,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    raw = (await file.read()).decode("utf-8", errors="replace")
    try:
        rows = parse_csv_text(raw)
    except CsvValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = run_sync(db, org, rows, file.filename or "uploaded.csv")
    result["contacts"] = [_contact_to_out(c) for c in result["contacts"]]
    result["invoices"] = [_invoice_to_out(i) for i in result["invoices"]]
    return result


@router.get("/history")
def sync_history(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    runs = (
        db.query(SyncRun)
        .filter(SyncRun.org_id == org.id)
        .order_by(SyncRun.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "source_filename": r.source_filename,
            "rows_processed": r.rows_processed,
            "contacts_created": r.contacts_created,
            "contacts_updated": r.contacts_updated,
            "invoices_created": r.invoices_created,
            "ops_used": r.ops_used,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


@router.post("/reset")
def reset_org_data(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    """Wipes this org's demo data (contacts/invoices/sync history/ops
    counter) without deleting the account. Useful for re-running the demo
    from a clean slate."""
    db.query(Invoice).filter(Invoice.org_id == org.id).delete()
    db.query(Contact).filter(Contact.org_id == org.id).delete()
    db.query(SyncRun).filter(SyncRun.org_id == org.id).delete()
    org.ops_used = 0
    db.commit()
    return {"status": "reset"}
