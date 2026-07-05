"""
Real HubSpot CRM v3 API connector. Used only when an org has completed the
HubSpot OAuth flow (routers/integrations.py) and holds a valid access token.

Docs: https://developers.hubspot.com/docs/api/crm/contacts
"""
import requests

from app.services.integrations.base import BaseConnector

HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotConnector(BaseConnector):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _find_contact_id_by_email(self, email: str) -> str | None:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
        body = {
            "filterGroups": [
                {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
            ],
            "limit": 1,
        }
        resp = requests.post(url, json=body, headers=self._headers(), timeout=10)
        if resp.status_code != 200:
            return None
        results = resp.json().get("results", [])
        return results[0]["id"] if results else None

    def upsert_contact(self, contact) -> None:
        properties = {
            "email": contact.email,
            "firstname": contact.name.split(" ")[0] if contact.name else "",
            "lastname": " ".join(contact.name.split(" ")[1:]) if contact.name else "",
            "phone": contact.phone,
        }
        existing_id = self._find_contact_id_by_email(contact.email)
        if existing_id:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{existing_id}"
            requests.patch(url, json={"properties": properties}, headers=self._headers(), timeout=10)
        else:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts"
            requests.post(url, json={"properties": properties}, headers=self._headers(), timeout=10)

    def create_invoice(self, invoice, contact) -> None:
        # HubSpot models this as a "deal" -- actual invoicing happens in the
        # invoicing.create_invoice() call to the QuickBooks connector.
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals"
        properties = {
            "dealname": f"{invoice.product} - {contact.name}",
            "amount": str(invoice.amount),
            "closedate": invoice.due_date,
        }
        requests.post(url, json={"properties": properties}, headers=self._headers(), timeout=10)
