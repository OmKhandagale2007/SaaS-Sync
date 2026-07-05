from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, contacts, integrations, invoices, sync

settings = get_settings()

# Creates tables on startup if they don't exist yet. Fine for a learning
# project / small deployment; for a real production app you'd switch to
# Alembic migrations so schema changes are versioned instead of implicit.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SyncLine API",
    description="Backend for the SyncLine Excel → CRM → Invoicing sync demo.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(contacts.router)
app.include_router(invoices.router)
app.include_router(integrations.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
