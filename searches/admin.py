from django.contrib import admin
from .models import JobMatch, SearchProfile, SearchRule


class SearchRuleInline(admin.TabularInline):
    model = SearchRule
    extra = 1


@admin.register(SearchProfile)
class SearchProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active", "minimum_score", "updated_at")
    fieldsets = (
        (
            "Profile",
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "active",
                    "minimum_score",
                )
            },
        ),
        (
            "Discovery",
            {
                "fields": (
                    "discovery_titles",
                    "discovery_locations",
                )
            },
        ),
    )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SearchRuleInline]


@admin.register(SearchRule)
class SearchRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name", "profile", "rule_type", "field", "operator",
        "value", "required", "weight", "enabled"
    )
    list_filter = ("profile", "rule_type", "field", "enabled")


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("profile", "job", "eligible", "score", "evaluated_at")
    list_filter = ("profile", "eligible")
    search_fields = ("job__title", "job__company")
