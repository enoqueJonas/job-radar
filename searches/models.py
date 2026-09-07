from django.db import models
from jobs.models import Job


class SearchProfile(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    discovery_titles = models.JSONField(
        default=list,
        blank=True,
    )

    discovery_primary_titles = models.JSONField(
        default=list,
        blank=True,
    )

    discovery_locations = models.JSONField(
        default=list,
        blank=True,
    )

    # Minimum final percentage needed to surface a passing match.
    minimum_score = models.PositiveSmallIntegerField(default=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def __str__(self):
    return self.name


class SearchRule(models.Model):
    class RuleType(models.TextChoices):
        FILTER = "filter", "Filter"
        SCORE = "score", "Score"

    class Operator(models.TextChoices):
        CONTAINS = "contains", "Contains"
        NOT_CONTAINS = "not_contains", "Does not contain"
        IN = "in", "In"
        LTE = "lte", "Less than or equal"
        GTE = "gte", "Greater than or equal"
        EQ = "eq", "Equals"

    class MissingBehavior(models.TextChoices):
        IGNORE = "ignore", "Ignore"
        FAIL = "fail", "Fail"

    class Field(models.TextChoices):
        TITLE = "title", "Title"
        DESCRIPTION = "description", "Description"
        LOCATION = "location_text", "Location"
        REMOTE_TYPE = "remote_type", "Remote type"
        MIN_EXPERIENCE = "min_years_experience", "Minimum required experience"
        SKILLS = "skills", "Skills"
        COMPANY = "company", "Company"

    profile = models.ForeignKey(
        SearchProfile, on_delete=models.CASCADE, related_name="rules")
    name = models.CharField(max_length=160)
    rule_type = models.CharField(max_length=10, choices=RuleType.choices)
    field = models.CharField(max_length=40, choices=Field.choices)
    operator = models.CharField(max_length=20, choices=Operator.choices)

    missing_behavior = models.CharField(
        max_length=10,
        choices=MissingBehavior.choices,
        default=MissingBehavior.IGNORE,
    )
    # JSON supports strings, numbers and arrays without schema changes.
    value = models.JSONField()

    # FILTER: true means failure excludes the job.
    # SCORE: points awarded when the rule matches.
    required = models.BooleanField(default=False)
    weight = models.IntegerField(default=0)

    enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return f"{self.profile}: {self.name}"


class JobMatch(models.Model):
    profile = models.ForeignKey(
        SearchProfile, on_delete=models.CASCADE, related_name="matches")
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name="matches")

    eligible = models.BooleanField(default=True)
    score = models.PositiveSmallIntegerField(default=0)
    matched_weight = models.IntegerField(default=0)
    possible_weight = models.IntegerField(default=0)
    reasons = models.JSONField(default=list)
    rejection_reasons = models.JSONField(default=list)

    evaluated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "job"], name="unique_job_match_per_profile"
            )
        ]
        indexes = [
            models.Index(fields=["profile", "eligible", "score"]),
        ]

    def __str__(self):
        return f"{self.profile} / {self.job}: {self.score}%"
