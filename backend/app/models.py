import datetime
import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


class Organization(Base):
    """
    The tenant. Every other business record (contacts, invoices, sync runs,
    integrations) belongs to exactly one Organization, and every query is
    scoped by org_id. This is what makes the app multi-tenant instead of a
    single shared demo like the original frontend simulation.
    """
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    ops_used: Mapped[int] = mapped_column(Integer, default=0)
    ops_cap: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="organization")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="organization")
    sync_runs: Mapped[list["SyncRun"]] = relationship(back_populates="organization")
    integrations: Mapped[list["IntegrationConnection"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="users")


class Contact(Base):
    """
    A deduplicated CRM contact. The (org_id, email) unique constraint is what
    enforces "dedupe by email" at the database level -- the same guarantee
    the frontend used to fake with a JS Map that vanished on refresh.
    """
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("org_id", "email", name="uq_contact_org_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(64), default="")
    deal_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="contacts")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="contact")


class InvoiceStatus(str, enum.Enum):
    sent = "Sent"
    paid = "Paid"
    overdue = "Overdue"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    invoice_number: Mapped[str] = mapped_column(String(64))
    product: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    due_date: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default=InvoiceStatus.sent.value)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="invoices")
    contact: Mapped["Contact"] = relationship(back_populates="invoices")


class SyncRun(Base):
    """One record per 'Run sync' click -- lets the org see history over time
    instead of losing everything on refresh."""
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    source_filename: Mapped[str] = mapped_column(String(255), default="pasted-csv")
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    contacts_created: Mapped[int] = mapped_column(Integer, default=0)
    contacts_updated: Mapped[int] = mapped_column(Integer, default=0)
    invoices_created: Mapped[int] = mapped_column(Integer, default=0)
    ops_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="sync_runs")


class IntegrationConnection(Base):
    """
    Stores OAuth tokens for a real third-party CRM/invoicing provider
    (HubSpot, QuickBooks, ...). If no token is present, the sync engine runs
    in 'simulated' mode for that provider -- exactly like the original
    frontend demo. Once you complete the OAuth flow (see
    routers/integrations.py), it flips to 'live' mode and the connector
    classes in services/integrations/ make real API calls.
    """
    __tablename__ = "integration_connections"
    __table_args__ = (UniqueConstraint("org_id", "provider", name="uq_org_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    provider: Mapped[str] = mapped_column(String(64))  # "hubspot" | "quickbooks"
    access_token: Mapped[str] = mapped_column(String(2048), default="")
    refresh_token: Mapped[str] = mapped_column(String(2048), default="")
    external_account_id: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="disconnected")  # disconnected | connected
    connected_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="integrations")
