from rest_framework import viewsets
from .models import JobMatch, SearchProfile
from .serializers import JobMatchSerializer, SearchProfileSerializer


class SearchProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SearchProfile.objects.prefetch_related(
        "rules").filter(active=True)
    serializer_class = SearchProfileSerializer


class JobMatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        qs = (
            JobMatch.objects
            .select_related(
                "profile",
                "job",
            )
            .prefetch_related(
                "job__listings__source"
            )
            .order_by(
                "-eligible",
                "-score",
                "-evaluated_at",
            )
        )
        profile = self.request.query_params.get("profile")
        eligible = self.request.query_params.get("eligible")

        if profile:
            qs = qs.filter(profile__slug=profile)
        if eligible in {"true", "false"}:
            qs = qs.filter(eligible=(eligible == "true"))
        return qs
