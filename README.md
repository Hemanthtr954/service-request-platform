# Enterprise Order & Service Request Management Platform

A Django service-request workflow (intake → assignment → approval → escalation → closure) with a REST API, a full audit trail, and a Flask integration gateway with payload transformation, retries and failed-transaction logging.

> Independent portfolio project using invented data. It reproduces the architecture and engineering practices of enterprise workflow systems I have built; it contains no employer code or data.

## Features
- **Workflow state machine** with explicit allowed transitions; illegal transitions return `400` (`requests_app/models.py`).
- **Audit history**: every transition records actor, note and timestamp (`AuditEvent`).
- **REST API** (token auth, JSON validation, exception handling): order lookup, request submission, status updates, workflow history, status filtering.
- **Data model**: `Order` → `ServiceRequest` → `AuditEvent`, with indexes on order number and status; `select_related` to avoid N+1 queries.
- **Integration gateway** (`integration/gateway.py`, Flask): transforms upstream payloads, retries with exponential backoff, logs failures to a queue endpoint (`/failed`).
- **Tests**: 6 tests covering auth, lifecycle + audit order, illegal transitions, invalid payloads (bad JSON, unknown order, blank title), lookup/filter, and gateway transform + retry. CI via GitHub Actions.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/orders/<number>/` | order lookup with its requests |
| GET/POST | `/api/requests/` | list (`?status=`) / submit |
| POST | `/api/requests/<id>/status/` | assign/transition |
| GET | `/api/requests/<id>/history/` | audit trail |

Header: `Authorization: Bearer demo-token`

## Run it
```bash
pip install -r requirements.txt
python manage.py migrate && python manage.py shell -c "from requests_app.models import Order; Order.objects.create(number='ORD-1', customer='Acme')"
python manage.py runserver
pytest -q
python integration/gateway.py   # optional: Flask gateway on :5001
```
