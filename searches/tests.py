from django.test import TestCase

from jobs.models import Job
from searches.matcher import evaluate_job
from searches.models import (
    SearchProfile,
    SearchRule,
)


class MatcherTests(TestCase):
    def setUp(self):
        self.profile = (
            SearchProfile.objects.create(
                name="QA Search",
                slug="qa-test",
                minimum_score=30,
            )
        )

    def test_score_rule_awards_points(self):
        SearchRule.objects.create(
            profile=self.profile,
            name="QA title",
            rule_type=(
                SearchRule.RuleType.SCORE
            ),
            field=SearchRule.Field.TITLE,
            operator=(
                SearchRule.Operator.CONTAINS
            ),
            value=["qa", "test engineer"],
            weight=20,
        )

        job = Job.objects.create(
            fingerprint="score-test-1",
            title="QA Engineer",
            company="Acme",
        )

        result = evaluate_job(
            job,
            self.profile,
        )

        self.assertEqual(
            result.matched_weight,
            20,
        )

        self.assertEqual(
            result.score,
            100,
        )

    def test_missing_experience_does_not_reject_when_ignored(
        self,
    ):
        SearchRule.objects.create(
            profile=self.profile,
            name="Maximum 7 years",
            rule_type=(
                SearchRule.RuleType.FILTER
            ),
            field=(
                SearchRule.Field.MIN_EXPERIENCE
            ),
            operator=(
                SearchRule.Operator.LTE
            ),
            value=7,
            required=True,
            missing_behavior=(
                SearchRule
                .MissingBehavior
                .IGNORE
            ),
        )

        job = Job.objects.create(
            fingerprint="experience-test-1",
            title="QA Engineer",
            company="Acme",
        )

        self.profile.minimum_score = 0
        self.profile.save()

        result = evaluate_job(
            job,
            self.profile,
        )

        self.assertTrue(
            result.eligible
        )

    def test_excessive_required_experience_rejects_job(
        self,
    ):
        SearchRule.objects.create(
            profile=self.profile,
            name="Maximum 7 years",
            rule_type=(
                SearchRule.RuleType.FILTER
            ),
            field=(
                SearchRule.Field.MIN_EXPERIENCE
            ),
            operator=(
                SearchRule.Operator.LTE
            ),
            value=7,
            required=True,
        )

        job = Job.objects.create(
            fingerprint="experience-test-2",
            title="QA Architect",
            company="Acme",
            min_years_experience=10,
        )

        self.profile.minimum_score = 0
        self.profile.save()

        result = evaluate_job(
            job,
            self.profile,
        )

        self.assertFalse(
            result.eligible
        )

        self.assertIn(
            "Maximum 7 years",
            result.rejection_reasons,
        )

    def test_matching_experience_passes_filter(
        self,
    ):
        SearchRule.objects.create(
            profile=self.profile,
            name="Maximum 7 years",
            rule_type=(
                SearchRule.RuleType.FILTER
            ),
            field=(
                SearchRule.Field.MIN_EXPERIENCE
            ),
            operator=(
                SearchRule.Operator.LTE
            ),
            value=7,
            required=True,
        )

        job = Job.objects.create(
            fingerprint="experience-test-3",
            title="QA Engineer",
            company="Acme",
            min_years_experience=3,
        )

        self.profile.minimum_score = 0
        self.profile.save()

        result = evaluate_job(
            job,
            self.profile,
        )

        self.assertTrue(
            result.eligible
        )
