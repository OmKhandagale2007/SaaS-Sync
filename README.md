# SaaS-Sync
# SyncFlow — Python Sync Engine

Excel → CRM → Invoice integration backend.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the API server (demo mode — no API keys needed)
cd ..
uvicorn syncflow.api.server:app --reload --port 8000

# 3. Open the interactive docs
open http://localhost:8000/docs
```

## Run the tests

```bash
pip install pytest
cd ..   # project root (parent of syncflow/)
python -m pytest syncflow/tests/ -v
```

## Trigger a sync via curl

```bash
# Full chain: Excel → CRM → Invoice
curl -X POST http://localhost:8000/sync \
  -H "Content-Type: application/json" \
  -d '{"direction": "full_chain", "conflict_strategy": "source_wins"}'

# Dry run (no writes)
curl -X POST http://localhost:8000/sync \
  -d '{"dry_run": true}' -H "Content-Type: application/json"

# View CRM state after sync
curl http://localhost:8000/records/crm

# View invoices
curl http://localhost:8000/records/invoice

# Health check
curl http://localhost:8000/health
```

## Project structure

```
syncflow/
├── core/
│   ├── models.py       # SyncRecord, SyncResult, FieldMapping, etc.
│   ├── engine.py       # SyncEngine — main pipeline orchestrator
│   ├── conflicts.py    # Conflict detection + resolution logic
│   └── audit.py        # Structured audit logger (JSONL files)
├── connectors/
│   ├── base.py         # BaseConnector interface
│   ├── excel.py        # Excel / CSV / Sheets connector
│   ├── crm.py          # HubSpot CRM connector (demo + real stub)
│   └── invoice.py      # Xero invoice connector (demo + real stub)
├── api/
│   └── server.py       # FastAPI REST API
├── tests/
│   └── test_engine.py  # Full test suite (pytest)
└── requirements.txt
```

## Connecting real systems

### HubSpot CRM
1. Get your API key: https://developers.hubspot.com/docs/api/overview
2. Set env var: `export HUBSPOT_API_KEY=your_key`
3. In `connectors/crm.py`, implement `_hubspot_list_contacts()` and `_hubspot_upsert()`

### Xero Invoices
1. Create an app: https://developer.xero.com/app/manage
2. Complete OAuth2 flow to get `access_token`
3. Set env var: `export XERO_ACCESS_TOKEN=your_token`
4. In `connectors/invoice.py`, implement `_xero_list_invoices()` and `_xero_create_invoice()`

### Excel / Google Sheets
- For local files: `ExcelConnector(file_path="customers.xlsx")`
- For Google Sheets: replace `read()` in `connectors/excel.py` with the Sheets API call

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sync` | Trigger a sync run |
| GET | `/sync/{run_id}` | Fetch run results + audit log |
| GET | `/sync` | List all runs |
| GET | `/health` | Connector health check |
| GET | `/records/crm` | List CRM records |
| GET | `/records/invoice` | List invoices |
| GET | `/records/excel` | List source records |

## Conflict strategies

| Strategy | Behaviour |
|----------|-----------|
| `source_wins` | Incoming Excel data overwrites CRM (default) |
| `target_wins` | Existing CRM data is preserved |
| `manual` | Conflicting records are flagged, not written |

## What to build next

- [ ] Postgres persistence (swap `_runs` dict for SQLAlchemy)
- [ ] Scheduled syncs (APScheduler or Celery beat)
- [ ] Webhook triggers (receive a POST from HubSpot → auto-sync)
- [ ] Multi-tenant support (per-user connector credentials)
- [ ] Frontend dashboard (connect to the React prototype)
