import datetime
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_org
from app.models import IntegrationConnection, Organization
from app.schemas import IntegrationAuthUrl, IntegrationOut

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
settings = get_settings()

PROVIDERS = ("hubspot", "quickbooks")


def _get_or_create_connection(db: Session, org: Organization, provider: str) -> IntegrationConnection:
    conn = (
        db.query(IntegrationConnection)
        .filter(IntegrationConnection.org_id == org.id, IntegrationConnection.provider == provider)
        .first()
    )
    if not conn:
        conn = IntegrationConnection(org_id=org.id, provider=provider, status="disconnected")
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return conn


@router.get("", response_model=list[IntegrationOut])
def list_integrations(db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    out = []
    for provider in PROVIDERS:
        conn = _get_or_create_connection(db, org, provider)
        out.append(IntegrationOut(provider=provider, status=conn.status, connected_at=conn.connected_at))
    return out


@router.get("/{provider}/connect", response_model=IntegrationAuthUrl)
def connect(provider: str, org: Organization = Depends(get_current_org)):
    """Returns the authorization URL to redirect the user to. `configured`
    is False if you haven't set the provider's client ID/secret in .env yet
    -- in that case the frontend should explain that this integration needs
    real developer credentials before it can go live."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider.")

    state = str(org.id)  # ties the OAuth callback back to the right org

    if provider == "hubspot":
        configured = bool(settings.hubspot_client_id)
        params = {
            "client_id": settings.hubspot_client_id,
            "redirect_uri": settings.hubspot_redirect_uri,
            "scope": "crm.objects.contacts.write crm.objects.contacts.read crm.objects.deals.write crm.objects.deals.read",
            "state": state,
        }
        url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
    else:  # quickbooks
        configured = bool(settings.quickbooks_client_id)
        params = {
            "client_id": settings.quickbooks_client_id,
            "redirect_uri": settings.quickbooks_redirect_uri,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "state": state,
        }
        url = f"https://appcenter.intuit.com/connect/oauth2?{urlencode(params)}"

    return IntegrationAuthUrl(authorize_url=url, configured=configured)


@router.get("/hubspot/callback")
def hubspot_callback(code: str, state: str, db: Session = Depends(get_db)):
    org_id = int(state)
    token_resp = requests.post(
        "https://api.hubapi.com/oauth/v1/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.hubspot_client_id,
            "client_secret": settings.hubspot_client_secret,
            "redirect_uri": settings.hubspot_redirect_uri,
            "code": code,
        },
        timeout=10,
    )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"HubSpot token exchange failed: {token_resp.text}")

    tokens = token_resp.json()
    conn = (
        db.query(IntegrationConnection)
        .filter(IntegrationConnection.org_id == org_id, IntegrationConnection.provider == "hubspot")
        .first()
    )
    if not conn:
        conn = IntegrationConnection(org_id=org_id, provider="hubspot")
        db.add(conn)

    conn.access_token = tokens.get("access_token", "")
    conn.refresh_token = tokens.get("refresh_token", "")
    conn.status = "connected"
    conn.connected_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "connected", "provider": "hubspot"}


@router.get("/quickbooks/callback")
def quickbooks_callback(code: str, state: str, realmId: str, db: Session = Depends(get_db)):
    org_id = int(state)
    token_resp = requests.post(
        "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.quickbooks_redirect_uri,
        },
        auth=(settings.quickbooks_client_id, settings.quickbooks_client_secret),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"QuickBooks token exchange failed: {token_resp.text}")

    tokens = token_resp.json()
    conn = (
        db.query(IntegrationConnection)
        .filter(IntegrationConnection.org_id == org_id, IntegrationConnection.provider == "quickbooks")
        .first()
    )
    if not conn:
        conn = IntegrationConnection(org_id=org_id, provider="quickbooks")
        db.add(conn)

    conn.access_token = tokens.get("access_token", "")
    conn.refresh_token = tokens.get("refresh_token", "")
    conn.external_account_id = realmId
    conn.status = "connected"
    conn.connected_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "connected", "provider": "quickbooks"}


@router.delete("/{provider}")
def disconnect(provider: str, db: Session = Depends(get_db), org: Organization = Depends(get_current_org)):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider.")
    conn = _get_or_create_connection(db, org, provider)
    conn.status = "disconnected"
    conn.access_token = ""
    conn.refresh_token = ""
    db.commit()
    return {"status": "disconnected", "provider": provider}
