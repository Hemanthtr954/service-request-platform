from django.db import models

# Allowed workflow transitions (intake -> assignment -> approval -> escalation -> closure)
TRANSITIONS = {
    "NEW": {"ASSIGNED", "CLOSED"}, "ASSIGNED": {"PENDING_APPROVAL", "CLOSED"},
    "PENDING_APPROVAL": {"APPROVED", "REJECTED", "ESCALATED"}, "ESCALATED": {"APPROVED", "REJECTED"},
    "APPROVED": {"CLOSED"}, "REJECTED": {"ASSIGNED", "CLOSED"}, "CLOSED": set(),
}


class Order(models.Model):
    number = models.CharField(max_length=20, unique=True, db_index=True)
    customer = models.CharField(max_length=120); status = models.CharField(max_length=20, default="OPEN")
    created = models.DateTimeField(auto_now_add=True)


class ServiceRequest(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="requests")
    title = models.CharField(max_length=200); description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="NEW", db_index=True)
    assignee = models.CharField(max_length=80, blank=True); created = models.DateTimeField(auto_now_add=True)

    def transition(self, new, actor, note=""):
        if new not in TRANSITIONS[self.status]:
            raise ValueError(f"illegal transition {self.status} -> {new}")
        AuditEvent.objects.create(request=self, from_status=self.status, to_status=new, actor=actor, note=note)
        self.status = new; self.save(update_fields=["status"])


class AuditEvent(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20); to_status = models.CharField(max_length=20)
    actor = models.CharField(max_length=80); note = models.TextField(blank=True); at = models.DateTimeField(auto_now_add=True)
