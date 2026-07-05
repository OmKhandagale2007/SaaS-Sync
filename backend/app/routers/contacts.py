from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_org
from app.models import Contact, Organization
from app.schemas import ContactOut

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    return db.query(Contact).filter(Contact.org_id == org.id).order_by(Contact.created_at.desc()).all()
