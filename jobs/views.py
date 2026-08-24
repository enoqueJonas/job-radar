from rest_framework import viewsets
from .models import Job
from .serializers import JobSerializer


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Job.objects
        .prefetch_related(
            "listings__source"
        )
        .order_by(
            "-posted_at",
            "-first_seen_at",
        )
    )
    serializer_class = JobSerializer
