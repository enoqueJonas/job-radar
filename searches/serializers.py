from rest_framework import serializers
from jobs.serializers import JobSerializer
from .models import JobMatch, SearchProfile, SearchRule


class SearchRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchRule
        fields = "__all__"


class SearchProfileSerializer(serializers.ModelSerializer):
    rules = SearchRuleSerializer(many=True, read_only=True)

    class Meta:
        model = SearchProfile
        fields = "__all__"


class JobMatchSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    profile_name = serializers.CharField(source="profile.name", read_only=True)

    class Meta:
        model = JobMatch
        fields = "__all__"
