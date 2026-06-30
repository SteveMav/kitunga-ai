from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import DetectionEvent
from .serializers import DetectionEventSerializer


@api_view(["GET"])
def detection_events(request):
    events = DetectionEvent.objects.select_related("basket").order_by("-created_at")[:50]
    serializer = DetectionEventSerializer(events, many=True)
    return Response(serializer.data)
