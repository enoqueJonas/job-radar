from django.contrib import admin
from .models import (
    Job,
    JobListing,
    JobSource,
    SkillKeyword,
)


class JobListingInline(
    admin.TabularInline
):
    model = JobListing
    extra = 0

    readonly_fields = (
        "source",
        "external_id",
        "url",
        "apply_url",
        "first_seen_at",
        "last_seen_at",
    )


@admin.register(SkillKeyword)
class SkillKeywordAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "enabled")
    list_filter = ("enabled",)
    search_fields = ("canonical_name",)


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "enabled",
        "validation_status",
        "last_validated_at",
    )

    list_filter = (
        "kind",
        "enabled",
        "validation_status",
    )

    search_fields = (
        "name",
        "base_url",
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "remote_type",
        "posted_at",
        "active",
    )

    list_filter = (
        "remote_type",
        "active",
    )

    search_fields = (
        "title",
        "company",
        "description",
        "location_text",
        "fingerprint",
    )

    inlines = [
        JobListingInline,
    ]


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = (
        "job",
        "source",
        "external_id",
        "active",
        "last_seen_at",
    )

    list_filter = (
        "source",
        "active",
    )

    search_fields = (
        "job__title",
        "job__company",
        "external_id",
    )
