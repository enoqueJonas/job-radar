from django.contrib import admin

from .models import (
    DiscoveredSource,
    DiscoveryRun,
)


class DiscoveredSourceInline(
    admin.TabularInline
):
    model = DiscoveredSource
    extra = 0

    readonly_fields = (
        "url",
        "provider",
        "provider_identifier",
        "company_name",
        "confidence",
        "status",
        "created_at",
    )


@admin.register(DiscoveryRun)
class DiscoveryRunAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "profile",
        "status",
        "started_at",
        "finished_at",
        "created_at",
    )

    list_filter = (
        "status",
        "profile",
    )

    inlines = [
        DiscoveredSourceInline,
    ]


@admin.register(DiscoveredSource)
class DiscoveredSourceAdmin(
    admin.ModelAdmin
):
    list_display = (
        "provider",
        "provider_identifier",
        "company_name",
        "confidence",
        "status",
        "run",
    )

    list_filter = (
        "provider",
        "status",
    )

    search_fields = (
        "provider_identifier",
        "company_name",
        "url",
    )
