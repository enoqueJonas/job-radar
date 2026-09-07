from django.test import TestCase

from discovery.detectors.ats import (
    detect_ats,
)
from discovery.models import (
    DiscoveredSource,
)
from discovery.query_builder import (
    build_discovery_queries,
)
from discovery.services import (
    create_discovery_run,
    register_discovered_url,
)
from searches.models import (
    SearchProfile,
)
from discovery.providers.base import (
    SearchProvider,
    SearchResult,
)
from discovery.services import (
    run_discovery,
)
from discovery.promotion import (
    promote_discovered_sources,
)
from jobs.models import JobSource


class ATSDetectorTests(TestCase):
    def test_detects_lever_board(self):
        result = detect_ats(
            "https://jobs.lever.co/gettyimages"
        )

        self.assertIsNotNone(
            result
        )

        self.assertEqual(
            result.provider,
            "lever",
        )

        self.assertEqual(
            result.identifier,
            "gettyimages",
        )

        self.assertEqual(
            result.region,
            "global",
        )

    def test_detects_lever_job_url(self):
        result = detect_ats(
            "https://jobs.lever.co/"
            "gettyimages/abc123"
        )

        self.assertEqual(
            result.identifier,
            "gettyimages",
        )

    def test_detects_eu_lever(self):
        result = detect_ats(
            "https://jobs.eu.lever.co/"
            "company/abc"
        )

        self.assertEqual(
            result.provider,
            "lever",
        )

        self.assertEqual(
            result.region,
            "eu",
        )

    def test_detects_greenhouse(self):
        result = detect_ats(
            "https://job-boards."
            "greenhouse.io/"
            "acme/jobs/123"
        )

        self.assertEqual(
            result.provider,
            "greenhouse",
        )

        self.assertEqual(
            result.identifier,
            "acme",
        )

    def test_unknown_site_returns_none(self):
        result = detect_ats(
            "https://example.com/jobs/123"
        )

        self.assertIsNone(
            result
        )


class DiscoveryQueryTests(TestCase):
    def setUp(self):
        self.profile = (
            SearchProfile.objects.create(
                name="QA Search",
                slug="qa-discovery",
                minimum_score=30,
                discovery_titles=[
                    "QA Engineer",
                    "Test Analyst",
                ],
                discovery_locations=[
                    "Remote",
                ],
            )
        )

    def test_builds_queries_from_profile(
        self,
    ):
        queries = (
            build_discovery_queries(
                self.profile
            )
        )

        self.assertTrue(
            any(
                query.query
                == '"QA Engineer"'
                for query in queries
            )
        )

        self.assertTrue(
            all(
                "jobs.lever.co"
                in query.include_domains
                for query in queries
            )
        )

    def test_does_not_hardcode_qa_titles(
        self,
    ):
        self.profile.discovery_titles = [
            "Security Analyst",
        ]

        self.profile.save()

        queries = (
            build_discovery_queries(
                self.profile
            )
        )

        self.assertTrue(
            any(
                "Security Analyst"
                in query.query
                for query in queries
            )
        )

        self.assertFalse(
            any(
                "QA Engineer"
                in query.query
                for query in queries
            )
        )


class DiscoveryServiceTests(TestCase):
    def setUp(self):
        self.profile = (
            SearchProfile.objects.create(
                name="QA Search",
                slug="qa-source-test",
            )
        )

        self.run = (
            create_discovery_run(
                self.profile,
                [
                    '"QA Engineer" '
                    "site:jobs.lever.co"
                ],
            )
        )

    def test_registers_detected_source(
        self,
    ):
        source = (
            register_discovered_url(
                run=self.run,
                url=(
                    "https://jobs.lever.co/"
                    "gettyimages/abc"
                ),
            )
        )

        self.assertEqual(
            source.provider,
            "lever",
        )

        self.assertEqual(
            source.provider_identifier,
            "gettyimages",
        )

    def test_marks_unknown_source_invalid(
        self,
    ):
        source = (
            register_discovered_url(
                run=self.run,
                url=(
                    "https://example.com/"
                    "jobs/123"
                ),
            )
        )

        self.assertEqual(
            source.status,
            DiscoveredSource
            .Status
            .INVALID,
        )


class FakeSearchProvider(
    SearchProvider
):
    def search(
        self,
        *,
        query,
        include_domains,
        max_results=10,
    ):
        return [
            SearchResult(
                title="QA Engineer",
                url=(
                    "https://jobs.lever.co/"
                    "acme/abc123"
                ),
                snippet="QA role",
                score=0.95,
            ),
            SearchResult(
                title="Test Engineer",
                url=(
                    "https://job-boards."
                    "greenhouse.io/"
                    "example/jobs/456"
                ),
                snippet="Testing role",
                score=0.90,
            ),
        ]


class DiscoveryRunnerTests(
    TestCase
):
    def setUp(self):
        self.profile = (
            SearchProfile.objects.create(
                name="QA Discovery",
                slug="qa-runner",
                discovery_titles=[
                    "QA Engineer",
                ],
                discovery_primary_titles=[],
                discovery_locations=[],
            )
        )

    def test_run_discovers_sources(
        self,
    ):
        run = run_discovery(
            profile=self.profile,
            provider=(
                FakeSearchProvider()
            ),
        )

        self.assertEqual(
            run.status,
            run.Status.COMPLETED,
        )

        self.assertEqual(
            run.sources.count(),
            2,
        )

        providers = set(
            run.sources.values_list(
                "provider",
                flat=True,
            )
        )

        self.assertEqual(
            providers,
            {
                "lever",
                "greenhouse",
            },
        )


class SourcePromotionTests(
    TestCase
):
    def setUp(self):
        self.profile = (
            SearchProfile.objects.create(
                name="QA",
                slug="qa-promotion",
            )
        )

        self.run = (
            create_discovery_run(
                self.profile,
                [],
            )
        )

    def test_multiple_job_urls_create_one_source(
        self,
    ):
        for url in [
            (
                "https://jobs.lever.co/"
                "acme/job-one"
            ),
            (
                "https://jobs.lever.co/"
                "acme/job-two"
            ),
        ]:
            register_discovered_url(
                run=self.run,
                url=url,
            )

        result = (
            promote_discovered_sources(
                self.run
            )
        )

        self.assertEqual(
            result.created,
            1,
        )

        self.assertEqual(
            JobSource.objects.count(),
            1,
        )

        source = (
            JobSource.objects.get()
        )

        self.assertEqual(
            source.config["provider"],
            "lever",
        )

        self.assertEqual(
            source.config["site"],
            "acme",
        )

    def test_existing_source_is_not_duplicated(
        self,
    ):
        JobSource.objects.create(
            name="Acme (Lever)",
            kind=JobSource.Kind.ATS,
            config={
                "provider": "lever",
                "site": "acme",
                "company": "Acme",
                "region": "global",
            },
        )

        register_discovered_url(
            run=self.run,
            url=(
                "https://jobs.lever.co/"
                "acme/job-one"
            ),
        )

        result = (
            promote_discovered_sources(
                self.run
            )
        )

        self.assertEqual(
            result.created,
            0,
        )

        self.assertEqual(
            result.existing,
            1,
        )

        self.assertEqual(
            JobSource.objects.count(),
            1,
        )

    def test_greenhouse_source_is_created(
        self,
    ):
        register_discovered_url(
            run=self.run,
            url=(
                "https://job-boards."
                "greenhouse.io/"
                "example/jobs/123"
            ),
        )

        promote_discovered_sources(
            self.run
        )

        source = (
            JobSource.objects.get()
        )

        self.assertEqual(
            source.config[
                "provider"
            ],
            "greenhouse",
        )

        self.assertEqual(
            source.config[
                "board_token"
            ],
            "example",
        )
