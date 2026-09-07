from django.db import models

from searches.models import SearchProfile


class DiscoveryRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    profile = models.ForeignKey(
        SearchProfile,
        on_delete=models.CASCADE,
        related_name="discovery_runs",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    queries = models.JSONField(
        default=list,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.profile.name} "
            f"discovery #{self.pk}"
        )


class DiscoveredSource(models.Model):
    class Provider(models.TextChoices):
        LEVER = "lever", "Lever"
        GREENHOUSE = "greenhouse", "Greenhouse"
        UNKNOWN = "unknown", "Unknown"

    class Status(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        REGISTERED = "registered", "Registered"
        IGNORED = "ignored", "Ignored"
        INVALID = "invalid", "Invalid"

    run = models.ForeignKey(
        DiscoveryRun,
        on_delete=models.CASCADE,
        related_name="sources",
    )

    url = models.URLField(
        max_length=1000,
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.UNKNOWN,
    )

    provider_identifier = models.CharField(
        max_length=255,
        blank=True,
    )

    company_name = models.CharField(
        max_length=255,
        blank=True,
    )

    confidence = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0,
    )

    provider_region = models.CharField(
        max_length=20,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCOVERED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "run",
                    "url",
                ],
                name="unique_discovered_url_per_run",
            )
        ]

    def __str__(self):
        return (
            f"{self.provider}: "
            f"{self.provider_identifier}"
        )
