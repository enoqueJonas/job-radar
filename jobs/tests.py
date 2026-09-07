from django.test import TestCase

from jobs.collectors.lever import CollectorConfigurationError, LeverCollector
from jobs.collectors.base import CollectedJob
from jobs.extractors.requirements import (
    enrich_collected_job,
    extract_experience_requirements,
)
from jobs.deduplication.fingerprints import (
    build_job_fingerprint,
)

from jobs.models import (
    Job,
    JobListing,
    JobSource,
)
from jobs.services import (
    persist_collected_jobs,
)
from jobs.collectors.greenhouse import (
    GreenhouseCollector,
    GreenhouseConfigurationError,
)
from unittest.mock import patch, Mock

from jobs.source_validation import (
    validate_source,
)

SAMPLE = {
    "id": "abc-123",
    "text": "QA Engineer",
    "categories": {
        "location": "Remote - EMEA",
        "commitment": "Full-time",
        "team": "Engineering",
        "department": "Product",
    },
    "country": "PT",
    "descriptionPlain": "Test APIs and web applications.",
    "lists": [
        {
            "text": "Requirements",
            "content": "<ul><li>3+ years QA</li><li>Postman</li></ul>",
        }
    ],
    "additionalPlain": "Fintech experience is a bonus.",
    "hostedUrl": "https://jobs.lever.co/acme/abc-123",
    "applyUrl": "https://jobs.lever.co/acme/abc-123/apply",
    "workplaceType": "remote",
}

GREENHOUSE_SAMPLE = {
    "id": 123456,
    "title": "QA Engineer",
    "location": {
        "name": "Remote - Europe",
    },
    "absolute_url": (
        "https://boards.greenhouse.io/"
        "acme/jobs/123456"
    ),
    "content": (
        "<p>We are looking for a "
        "QA Engineer.</p>"
        "<p>3+ years of QA experience "
        "required.</p>"
        "<p>Experience with Postman "
        "and API testing.</p>"
    ),
    "departments": [
        {
            "id": 10,
            "name": "Engineering",
        }
    ],
    "offices": [
        {
            "id": 20,
            "name": "Remote",
            "location": "Europe",
        }
    ],
    "updated_at": (
        "2026-08-24T10:00:00Z"
    ),
}


class LeverCollectorTests(TestCase):
    def setUp(self):
        self.collector = LeverCollector(
            {"site": "acme", "company": "Acme", "region": "global"}
        )

    def test_normalizes_public_posting(self):
        job = self.collector._normalize(SAMPLE)

        self.assertEqual(job.external_id, "abc-123")
        self.assertEqual(job.title, "QA Engineer")
        self.assertEqual(job.company, "Acme")
        self.assertEqual(job.remote_type, "remote")
        self.assertEqual(job.country_code, "PT")
        self.assertEqual(job.employment_type, "Full-time")
        self.assertEqual(job.team, "Engineering")
        self.assertEqual(job.department, "Product")
        self.assertIn("3+ years QA", job.description)
        self.assertEqual(
            job.apply_url,
            "https://jobs.lever.co/acme/abc-123/apply",
        )

    def test_maps_on_site(self):
        self.assertEqual(
            self.collector._normalize_workplace_type("on-site"),
            "onsite",
        )

    def test_rejects_missing_site(self):
        with self.assertRaises(CollectorConfigurationError):
            LeverCollector({"company": "Acme"})


class ExperienceExtractionTests(TestCase):
    def test_extracts_plus_years_as_required(self):
        requirements = extract_experience_requirements(
            "We require 3+ years of QA experience."
        )

        self.assertEqual(len(requirements), 1)

        requirement = requirements[0]

        self.assertEqual(
            requirement.minimum,
            3,
        )

        self.assertTrue(
            requirement.required
        )

    def test_extracts_range(self):
        requirements = extract_experience_requirements(
            "Candidates should have 3-5 years of software testing experience."
        )

        requirement = requirements[0]

        self.assertEqual(
            requirement.minimum,
            3,
        )

        self.assertEqual(
            requirement.maximum,
            5,
        )

    def test_preferred_experience_is_not_required(self):
        requirements = extract_experience_requirements(
            "5+ years of automation testing experience preferred."
        )

        requirement = requirements[0]

        self.assertFalse(
            requirement.required
        )

    def test_company_age_is_not_candidate_experience(self):
        requirements = extract_experience_requirements(
            "Our company has 15 years of experience in the banking industry."
        )

        self.assertEqual(
            requirements,
            [],
        )

    def test_extracts_required_minimum(self):
        requirements = extract_experience_requirements(
            "At least 4 years of QA experience required."
        )

        self.assertEqual(
            requirements[0].minimum,
            4,
        )


class JobFingerprintTests(TestCase):
    def test_same_job_with_formatting_variation_matches(self):
        first = build_job_fingerprint(
            company="Acme Ltd.",
            title="QA Engineer",
            location="Maputo, Mozambique",
        )

        second = build_job_fingerprint(
            company="ACME LTD",
            title="qa engineer",
            location="Maputo Mozambique",
        )

        self.assertEqual(
            first,
            second,
        )

    def test_different_title_does_not_match(self):
        qa = build_job_fingerprint(
            company="Acme",
            title="QA Engineer",
            location="Maputo",
        )

        developer = build_job_fingerprint(
            company="Acme",
            title="Backend Engineer",
            location="Maputo",
        )

        self.assertNotEqual(
            qa,
            developer,
        )


class JobDeduplicationTests(TestCase):
    def setUp(self):
        self.lever = JobSource.objects.create(
            name="Acme Lever",
            kind=JobSource.Kind.ATS,
        )

        self.other = JobSource.objects.create(
            name="Acme Careers",
            kind=JobSource.Kind.SCRAPER,
        )

    def test_same_job_from_two_sources_creates_one_job(self):
        first = CollectedJob(
            external_id="lever-123",
            title="QA Engineer",
            company="Acme",
            location_text="Remote",
            url="https://example.com/lever/123",
        )

        second = CollectedJob(
            external_id="career-456",
            title="QA Engineer",
            company="Acme",
            location_text="Remote",
            url="https://example.com/jobs/456",
        )

        persist_collected_jobs(
            self.lever,
            [first],
        )

        persist_collected_jobs(
            self.other,
            [second],
        )

        self.assertEqual(
            Job.objects.count(),
            1,
        )

        self.assertEqual(
            JobListing.objects.count(),
            2,
        )


class GreenhouseCollectorTests(
    TestCase
):
    def setUp(self):
        self.collector = (
            GreenhouseCollector(
                {
                    "board_token": "acme",
                    "company": "Acme",
                }
            )
        )

    def test_normalizes_public_posting(
        self,
    ):
        job = self.collector._normalize(
            GREENHOUSE_SAMPLE
        )

        self.assertEqual(
            job.external_id,
            "123456",
        )

        self.assertEqual(
            job.title,
            "QA Engineer",
        )

        self.assertEqual(
            job.company,
            "Acme",
        )

        self.assertEqual(
            job.location_text,
            "Remote - Europe",
        )

        self.assertEqual(
            job.remote_type,
            "remote",
        )

        self.assertEqual(
            job.department,
            "Engineering",
        )

        self.assertIn(
            "3+ years of QA experience",
            job.description,
        )

    def test_absolute_url_is_used_for_apply(
        self,
    ):
        job = self.collector._normalize(
            GREENHOUSE_SAMPLE
        )

        self.assertEqual(
            job.url,
            job.apply_url,
        )

    def test_detects_hybrid_location(
        self,
    ):
        self.assertEqual(
            self.collector
            ._detect_remote_type(
                "Lisbon - Hybrid"
            ),
            "hybrid",
        )

    def test_physical_location_is_onsite(
        self,
    ):
        self.assertEqual(
            self.collector
            ._detect_remote_type(
                "Maputo, Mozambique"
            ),
            "onsite",
        )

    def test_rejects_missing_board_token(
        self,
    ):
        with self.assertRaises(
            GreenhouseConfigurationError
        ):
            GreenhouseCollector(
                {
                    "company": "Acme",
                }
            )


class SourceValidationTests(TestCase):
    def setUp(self):
        self.lever = (
            JobSource.objects.create(
                name="Acme Lever",
                kind=JobSource.Kind.ATS,
                enabled=False,
                config={
                    "provider": "lever",
                    "site": "acme",
                    "company": "Acme",
                    "region": "global",
                },
            )
        )

    @patch(
        "jobs.source_validation.requests.get"
    )
    def test_valid_lever_source_is_enabled(
        self,
        mock_get,
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = []

        mock_get.return_value = response

        result = validate_source(
            self.lever
        )

        self.lever.refresh_from_db()

        self.assertTrue(
            result.valid
        )

        self.assertTrue(
            self.lever.enabled
        )

        self.assertEqual(
            self.lever.validation_status,
            JobSource
            .ValidationStatus
            .VALID,
        )

    @patch(
        "jobs.source_validation.requests.get"
    )
    def test_invalid_source_is_disabled(
        self,
        mock_get,
    ):
        response = Mock()
        response.status_code = 404

        mock_get.return_value = response

        result = validate_source(
            self.lever
        )

        self.lever.refresh_from_db()

        self.assertFalse(
            result.valid
        )

        self.assertFalse(
            self.lever.enabled
        )

        self.assertEqual(
            self.lever.validation_status,
            JobSource
            .ValidationStatus
            .INVALID,
        )
