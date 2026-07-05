"""
Real QuickBooks Online API connector. Used only when an org has completed
the QuickBooks OAuth flow and holds a valid access token + realm (company) id.

Docs: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice
"""
import requests

from app.config import get_settings
from app.services.integrations.base import BaseConnector

settings = get_settings()


class QuickBooksConnector(BaseConnector):
    def __init__(self, access_token: str, realm_id: str):
        self.access_token = access_token
        self.realm_id = realm_id
        base = (
            "https://sandbox-quickbooks.api.intuit.com"
            if settings.quickbooks_environment == "sandbox"
            else "https://quickbooks.api.intuit.com"
        )
        self.base_url = f"{base}/v3/company/{realm_id}"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _find_or_create_customer_id(self, contact) -> str | None:
        query = f"select * from Customer where PrimaryEmailAddr = '{contact.email}'"
        resp = requests.get(
            f"{self.base_url}/query", params={"query": query}, headers=self._headers(), timeout=10
        )
        if resp.status_code == 200:
            customers = resp.json().get("QueryResponse", {}).get("Customer", [])
            if customers:
                return customers[0]["Id"]

        body = {
            "DisplayName": contact.name or contact.email,
            "PrimaryEmailAddr": {"Address": contact.email},
            "PrimaryPhone": {"FreeFormNumber": contact.phone} if contact.phone else None,
        }
        create_resp = requests.post(
            f"{self.base_url}/customer", json=body, headers=self._headers(), timeout=10
        )
        if create_resp.status_code == 200:
            return create_resp.json().get("Customer", {}).get("Id")
        return None

    def upsert_contact(self, contact) -> None:
        # QuickBooks contacts live as "Customers"; ensured lazily in
        # create_invoice() so we only create them when there's a real invoice.
        return None

    def create_invoice(self, invoice, contact) -> None:
        customer_id = self._find_or_create_customer_id(contact)
        if not customer_id:
            return
        body = {
            "Line": [
                {
                    "Amount": invoice.amount,
                    "DetailType": "SalesItemLineDetail",
                    "Description": invoice.product,
                    "SalesItemLineDetail": {"Qty": 1, "UnitPrice": invoice.amount},
                }
            ],
            "CustomerRef": {"value": customer_id},
            "DueDate": invoice.due_date,
        }
        requests.post(f"{self.base_url}/invoice", json=body, headers=self._headers(), timeout=10)
