from django.contrib import admin
from .models import (
    CollectionRun,
    CollectionSourceResult,
    Job,
    JobListing,
    JobSource,
    SkillKeyword,
)


class JobListingInline(admin.TabularInline):
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


class CollectionSourceResultInline(admin.TabularInline):
    model = CollectionSourceResult
    extra = 0
    can_delete = False
    readonly_fields = (
        "source",
        "status",
        "collected_count",
        "persisted_count",
        "error_type",
        "error_message",
        "started_at",
        "finished_at",
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
    list_filter = ("kind", "enabled", "validation_status")
    search_fields = ("name", "base_url")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "remote_type", "posted_at", "active")
    list_filter = ("remote_type", "active")
    search_fields = (
        "title",
        "company",
        "description",
        "location_text",
        "fingerprint",
    )
    inlines = [JobListingInline]


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ("job", "source", "external_id", "active", "last_seen_at")
    list_filter = ("source", "active")
    search_fields = ("job__title", "job__company", "external_id")


@admin.register(CollectionRun)
class CollectionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "source_count",
        "successful_sources",
        "failed_sources",
        "persisted_count",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "fail_fast")
    readonly_fields = (
        "status",
        "requested_sources",
        "fail_fast",
        "source_count",
        "successful_sources",
        "failed_sources",
        "collected_count",
        "persisted_count",
        "started_at",
        "finished_at",
    )
    inlines = [CollectionSourceResultInline]


@admin.register(CollectionSourceResult)
class CollectionSourceResultAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "source",
        "status",
        "collected_count",
        "persisted_count",
        "finished_at",
    )
    list_filter = ("status", "source")
    search_fields = ("source__name", "error_type", "error_message")
    readonly_fields = (
        "run",
        "source",
        "status",
        "collected_count",
        "persisted_count",
        "error_type",
        "error_message",
        "started_at",
        "finished_at",
    )
