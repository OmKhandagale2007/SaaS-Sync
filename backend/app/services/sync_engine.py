"""
This is the real backend replacement for the frontend's old in-memory
`runSync()` function. Same business rules (dedupe by email, only invoice
when amount > 0, ops counter), but now:
  - persisted in the database instead of a JS variable that resets on refresh
  - scoped per-organization (multi-tenant)
  - optionally pushed to a real connected CRM/invoicing provider
"""
from sqlalchemy.orm import Session

from app.models import Contact, Invoice, Organization, SyncRun
from app.services.integrations import get_connector


def _next_invoice_number(db: Session, org: Organization) -> str:
    count = db.query(Invoice).filter(Invoice.org_id == org.id).count()
    return f"INV-{1000 + count + 1}"


def run_sync(db: Session, org: Organization, rows: list[dict], source_filename: str) -> dict:
    log: list[dict] = []
    contacts_touched: dict[int, Contact] = {}
    invoices_created: list[Invoice] = []
    contacts_created = 0
    contacts_updated = 0
    ops_this_run = 0

    def add_ops(n: int):
        nonlocal ops_this_run
        ops_this_run += n
        org.ops_used += n

    # Connectors are no-ops (simulated) unless the org has connected real
    # credentials for that provider -- see services/integrations/.
    crm = get_connector(db, org, "hubspot")
    invoicing = get_connector(db, org, "quickbooks")

    for row in rows:
        name = row.get("customer_name", "").strip()
        email = row.get("email", "").strip().lower()
        phone = row.get("phone", "").strip()
        product = row.get("product", "").strip()
        due_date = row.get("due_date", "").strip()

        try:
            amount = float(row.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0

        if not email:
            log.append({"message": f'Skipped "{name or "unnamed row"}" — missing email, cannot dedupe safely.', "level": "err"})
            continue

        add_ops(1)
        contact = db.query(Contact).filter(Contact.org_id == org.id, Contact.email == email).first()
        if contact:
            contact.deal_count += 1
            if name:
                contact.name = name
            if phone:
                contact.phone = phone
            contacts_updated += 1
            log.append({"message": f"Found existing contact for {email} — updating instead of duplicating.", "level": "warn"})
        else:
            contact = Contact(org_id=org.id, name=name, email=email, phone=phone, deal_count=1)
            db.add(contact)
            db.flush()  # get contact.id without a full commit
            contacts_created += 1
            log.append({"message": f"Created CRM contact: {name} ({email})", "level": "ok"})

        add_ops(1)
        crm.upsert_contact(contact)
        contacts_touched[contact.id] = contact

        if not (amount > 0):
            log.append({"message": f"Filter blocked invoice for {name} — amount is 0 or invalid.", "level": "warn"})
            continue

        add_ops(1)
        invoice_number = _next_invoice_number(db, org)
        invoice = Invoice(
            org_id=org.id,
            contact_id=contact.id,
            invoice_number=invoice_number,
            product=product,
            amount=amount,
            due_date=due_date,
            status="Sent",
        )
        db.add(invoice)
        db.flush()
        invoicing.create_invoice(invoice, contact)
        invoices_created.append(invoice)
        log.append({"message": f"Generated invoice {invoice_number} for {name} — ${amount:.2f}, due {due_date}", "level": "ok"})

    sync_run = SyncRun(
        org_id=org.id,
        source_filename=source_filename,
        rows_processed=len(rows),
        contacts_created=contacts_created,
        contacts_updated=contacts_updated,
        invoices_created=len(invoices_created),
        ops_used=ops_this_run,
    )
    db.add(sync_run)
    db.commit()
    db.refresh(sync_run)
    db.refresh(org)

    total_contacts = db.query(Contact).filter(Contact.org_id == org.id).count()
    total_invoices_amount = sum(
        i.amount for i in db.query(Invoice).filter(Invoice.org_id == org.id).all()
    )

    return {
        "sync_run_id": sync_run.id,
        "rows_processed": len(rows),
        "log": log,
        "contacts": list(contacts_touched.values()),
        "invoices": invoices_created,
        "stats": {
            "total_contacts": total_contacts,
            "duplicates_this_run": contacts_updated,
            "total_invoices": db.query(Invoice).filter(Invoice.org_id == org.id).count(),
            "total_invoiced_value": total_invoices_amount,
        },
        "ops_used": org.ops_used,
        "ops_cap": org.ops_cap,
    }
