"""
Connector interface that every real CRM/invoicing integration implements.

Design: the sync engine always calls crm.upsert_contact(...) and
invoicing.create_invoice(...) without caring whether a real provider is
connected. If IntegrationConnection.status == "connected" for that provider,
the real subclass fires an actual HTTP request. Otherwise SimulatedConnector
just logs and does nothing -- which is exactly what the original frontend
demo did for every provider, all the time.

This is the extension point: to go from "prototype" to "actually moves data
into HubSpot/QuickBooks", you connect the provider via OAuth (see
routers/integrations.py) and nothing else in the app needs to change.
"""
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    @abstractmethod
    def upsert_contact(self, contact) -> None:
        ...

    @abstractmethod
    def create_invoice(self, invoice, contact) -> None:
        ...


class SimulatedConnector(BaseConnector):
    """Used whenever no live OAuth connection exists for a provider."""

    def upsert_contact(self, contact) -> None:
        return None

    def create_invoice(self, invoice, contact) -> None:
        return None
