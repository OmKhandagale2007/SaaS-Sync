from sqlalchemy.orm import Session

from app.models import IntegrationConnection, Organization
from app.services.integrations.base import BaseConnector, SimulatedConnector
from app.services.integrations.hubspot import HubSpotConnector
from app.services.integrations.quickbooks import QuickBooksConnector


def get_connector(db: Session, org: Organization, provider: str) -> BaseConnector:
    """Returns a live connector if the org has a connected OAuth token for
    this provider, otherwise a SimulatedConnector (matches the original
    frontend demo's behavior: everything is simulated by default)."""
    conn = (
        db.query(IntegrationConnection)
        .filter(IntegrationConnection.org_id == org.id, IntegrationConnection.provider == provider)
        .first()
    )
    if not conn or conn.status != "connected" or not conn.access_token:
        return SimulatedConnector()

    if provider == "hubspot":
        return HubSpotConnector(access_token=conn.access_token)
    if provider == "quickbooks":
        return QuickBooksConnector(access_token=conn.access_token, realm_id=conn.external_account_id)
    return SimulatedConnector()
