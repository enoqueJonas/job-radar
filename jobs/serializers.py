from rest_framework import serializers
from .models import Job, JobSource, JobListing


class JobSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSource
        fields = "__all__"


class JobListingSerializer(
    serializers.ModelSerializer
):
    source_name = serializers.CharField(
        source="source.name",
        read_only=True,
    )

    class Meta:
        model = JobListing
        fields = "__all__"


class JobSerializer(
    serializers.ModelSerializer
):
    listings = JobListingSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Job
        fields = "__all__"
