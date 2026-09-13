from django.db import models


class JobSource(models.Model):
    class Kind(models.TextChoices):
        API = "api", "API"
        ATS = "ats", "ATS"
        SCRAPER = "scraper", "Scraper"
        MANUAL = "manual", "Manual"

    class ValidationStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"

    name = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    base_url = models.URLField(blank=True)
    enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.UNKNOWN,
    )
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_error = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SkillKeyword(models.Model):
    canonical_name = models.CharField(max_length=120, unique=True)
    aliases = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.canonical_name


class Job(models.Model):
    class RemoteType(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "On-site"
        UNKNOWN = "unknown", "Unknown"

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location_text = models.CharField(max_length=255, blank=True)
    remote_type = models.CharField(
        max_length=20, choices=RemoteType.choices, default=RemoteType.UNKNOWN
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    min_years_experience = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    max_years_experience = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    extracted_requirements = models.JSONField(default=list, blank=True)
    extraction_version = models.CharField(max_length=20, blank=True)
    skills = models.JSONField(default=list, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    employment_type = models.CharField(max_length=120, blank=True)
    team = models.CharField(max_length=160, blank=True)
    department = models.CharField(max_length=160, blank=True)
    fingerprint = models.CharField(max_length=64, unique=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["company"]),
            models.Index(fields=["active"]),
            models.Index(fields=["posted_at"]),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class JobListing(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="listings")
    source = models.ForeignKey(
        JobSource, on_delete=models.PROTECT, related_name="listings"
    )
    external_id = models.CharField(max_length=255)
    url = models.URLField(max_length=1000)
    apply_url = models.URLField(max_length=1000, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"], name="unique_listing_per_source"
            )
        ]
        indexes = [models.Index(fields=["source", "active"])]

    def __str__(self):
        return f"{self.job.title} @ {self.job.company} via {self.source.name}"


class CollectionRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with errors"
        FAILED = "failed", "Failed"

    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.RUNNING
    )
    requested_sources = models.JSONField(default=list, blank=True)
    fail_fast = models.BooleanField(default=False)
    source_count = models.PositiveIntegerField(default=0)
    successful_sources = models.PositiveIntegerField(default=0)
    failed_sources = models.PositiveIntegerField(default=0)
    collected_count = models.PositiveIntegerField(default=0)
    persisted_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Collection run #{self.pk} ({self.status})"


class CollectionSourceResult(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    run = models.ForeignKey(
        CollectionRun, on_delete=models.CASCADE, related_name="source_results"
    )
    source = models.ForeignKey(
        JobSource, on_delete=models.PROTECT, related_name="collection_results"
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    collected_count = models.PositiveIntegerField(default=0)
    persisted_count = models.PositiveIntegerField(default=0)
    error_type = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "source"], name="unique_collection_result_per_source"
            )
        ]
        ordering = ["source__name"]

    def __str__(self):
        return f"{self.source.name}: {self.status}"
