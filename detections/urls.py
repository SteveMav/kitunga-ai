from django.urls import path

from . import views

app_name = "detections"

urlpatterns = [
    path("", views.detection_events, name="events"),
]
