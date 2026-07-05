import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    organization_id: int
    organization_name: str
    ops_used: int
    ops_cap: int

    class Config:
        from_attributes = True


# ---------- Contacts / Invoices ----------

class ContactOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    deal_count: int

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    product: str
    amount: float
    due_date: str
    status: str
    customer_name: str
    customer_email: str

    class Config:
        from_attributes = True


# ---------- Sync ----------

class SyncRowIn(BaseModel):
    customer_name: str = ""
    email: str = ""
    phone: str = ""
    product: str = ""
    amount: str = ""
    due_date: str = ""


class SyncRequest(BaseModel):
    """Used when the client sends already-parsed rows as JSON instead of a CSV file upload."""
    rows: list[SyncRowIn]
    source_filename: str = "pasted-csv"


class LogEntry(BaseModel):
    message: str
    level: str = "info"  # info | ok | warn | err


class SyncResult(BaseModel):
    sync_run_id: int
    rows_processed: int
    log: list[LogEntry]
    contacts: list[ContactOut]
    invoices: list[InvoiceOut]
    stats: dict
    ops_used: int
    ops_cap: int


# ---------- Integrations ----------

class IntegrationOut(BaseModel):
    provider: str
    status: str
    connected_at: datetime.datetime | None = None

    class Config:
        from_attributes = True


class IntegrationAuthUrl(BaseModel):
    authorize_url: str
    configured: bool
