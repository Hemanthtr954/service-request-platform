from django.urls import include, path
urlpatterns = [path("", include("requests_app.urls"))]
