import json
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AuditEvent, Order, ServiceRequest

def api(view):
    @csrf_exempt
    @wraps(view)
    def w(request, *a, **k):
        if request.headers.get("Authorization") != f"Bearer {settings.API_TOKEN}":
            return JsonResponse({"error": "unauthorized"}, status=401)
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid JSON"}, status=400)
        try:
            return view(request, body, *a, **k)
        except (KeyError, ValueError) as e:
            return JsonResponse({"error": str(e)}, status=400)
        except (Order.DoesNotExist, ServiceRequest.DoesNotExist):
            return JsonResponse({"error": "not found"}, status=404)
    return w

def _ser(r): return {"id": r.id, "order": r.order.number, "title": r.title, "status": r.status, "assignee": r.assignee}

@api
def order_lookup(request, body, number):
    o = Order.objects.get(number=number)
    return JsonResponse({"number": o.number, "customer": o.customer, "status": o.status, "requests": [_ser(r) for r in o.requests.all()]})

@api
def requests_collection(request, body):
    if request.method == "POST":
        t = body["title"].strip()
        if not t: raise ValueError("title required")
        r = ServiceRequest.objects.create(order=Order.objects.get(number=body["order"]), title=t, description=body.get("description", ""))
        AuditEvent.objects.create(request=r, from_status="", to_status="NEW", actor=body.get("actor", "system"), note="created")
        return JsonResponse(_ser(r), status=201)
    qs = ServiceRequest.objects.select_related("order")
    if s := request.GET.get("status"): qs = qs.filter(status=s)
    return JsonResponse({"results": [_ser(r) for r in qs[:100]]})

@api
def update_status(request, body, pk):
    r = ServiceRequest.objects.select_related("order").get(pk=pk)
    if "assignee" in body: r.assignee = body["assignee"]; r.save(update_fields=["assignee"])
    r.transition(body["status"], body.get("actor", "system"), body.get("note", ""))
    return JsonResponse(_ser(r))

@api
def history(request, body, pk):
    h = ServiceRequest.objects.get(pk=pk).history.order_by("at", "id")
    return JsonResponse({"history": [{"from": e.from_status, "to": e.to_status, "actor": e.actor, "note": e.note} for e in h]})
