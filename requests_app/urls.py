from django.urls import path
from . import views
urlpatterns = [
    path("api/orders/<str:number>/", views.order_lookup),
    path("api/requests/", views.requests_collection),
    path("api/requests/<int:pk>/status/", views.update_status),
    path("api/requests/<int:pk>/history/", views.history),
]
