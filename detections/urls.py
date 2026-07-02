from django.urls import path

from . import views

app_name = "detections"

urlpatterns = [
    path("", views.detection_events, name="events"),
    path("capture-frame/", views.capture_frame, name="capture_frame"),
    path("capture-and-detect/", views.capture_and_detect, name="capture_and_detect"),
    path("live-detect-frame/", views.live_detect_frame, name="live_detect_frame"),
]
