import json, pathlib, sys
import pytest
from django.test import Client
from requests_app.models import Order, ServiceRequest

H = {"HTTP_AUTHORIZATION": "Bearer demo-token"}
pytestmark = pytest.mark.django_db


def post(c, url, data): return c.post(url, json.dumps(data), content_type="application/json", **H)


@pytest.fixture
def setup():
    Order.objects.create(number="ORD-1", customer="Acme"); return Client()


def test_requires_auth(setup):
    assert setup.get("/api/requests/").status_code == 401


def test_full_lifecycle_and_audit(setup):
    r = post(setup, "/api/requests/", {"order": "ORD-1", "title": "Replace router"}); assert r.status_code == 201
    pk = r.json()["id"]
    for s in ["ASSIGNED", "PENDING_APPROVAL", "ESCALATED", "APPROVED", "CLOSED"]:
        assert post(setup, f"/api/requests/{pk}/status/", {"status": s, "actor": "ana", "assignee": "bob"}).status_code == 200
    h = setup.get(f"/api/requests/{pk}/history/", **H).json()["history"]
    assert [e["to"] for e in h] == ["NEW", "ASSIGNED", "PENDING_APPROVAL", "ESCALATED", "APPROVED", "CLOSED"]


def test_illegal_transition_rejected(setup):
    pk = post(setup, "/api/requests/", {"order": "ORD-1", "title": "x"}).json()["id"]
    r = post(setup, f"/api/requests/{pk}/status/", {"status": "APPROVED"}); assert r.status_code == 400


def test_invalid_payloads(setup):
    assert post(setup, "/api/requests/", {"order": "NOPE", "title": "x"}).status_code == 404
    assert post(setup, "/api/requests/", {"order": "ORD-1", "title": "  "}).status_code == 400
    assert setup.post("/api/requests/", "{bad", content_type="application/json", **H).status_code == 400


def test_order_lookup_and_filter(setup):
    post(setup, "/api/requests/", {"order": "ORD-1", "title": "a"})
    assert setup.get("/api/orders/ORD-1/", **H).json()["requests"][0]["title"] == "a"
    assert len(setup.get("/api/requests/?status=NEW", **H).json()["results"]) == 1


def test_gateway_transform_and_retry(monkeypatch):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "integration"))
    import gateway
    assert gateway.transform({"order_no": " ord-9 ", "cust_name": "jane doe"}) == {"number": "ORD-9", "customer": "Jane Doe"}
    with pytest.raises(ValueError): gateway.transform({"order_no": ""})
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3: raise RuntimeError("boom")
        return "ok"
    assert gateway.with_retry(flaky, base=0) == "ok" and calls["n"] == 3
