from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from jobs.models import CollectionRun, CollectionSourceResult, JobSource


class CollectionRunCommandTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="Acme ATS",
            kind=JobSource.Kind.ATS,
            enabled=True,
            config={"provider": "lever", "site": "acme"},
        )

    @patch("jobs.management.commands.collect_jobs.persist_collected_jobs")
    @patch("jobs.management.commands.collect_jobs.build_collector")
    def test_successful_collection_is_audited(self, build_collector, persist):
        collector = Mock()
        collector.collect.return_value = [Mock(), Mock()]
        build_collector.return_value = collector
        persist.return_value = [Mock(), Mock()]

        call_command("collect_jobs", stdout=StringIO(), stderr=StringIO())

        run = CollectionRun.objects.get()
        result = CollectionSourceResult.objects.get(run=run, source=self.source)

        self.assertEqual(run.status, CollectionRun.Status.COMPLETED)
        self.assertEqual(run.source_count, 1)
        self.assertEqual(run.successful_sources, 1)
        self.assertEqual(run.failed_sources, 0)
        self.assertEqual(run.collected_count, 2)
        self.assertEqual(run.persisted_count, 2)
        self.assertIsNotNone(run.finished_at)

        self.assertEqual(result.status, CollectionSourceResult.Status.SUCCESS)
        self.assertEqual(result.collected_count, 2)
        self.assertEqual(result.persisted_count, 2)
        self.assertEqual(result.error_message, "")
        self.assertIsNotNone(result.finished_at)

    @patch("jobs.management.commands.collect_jobs.build_collector")
    def test_failed_source_is_recorded_without_aborting_run(self, build_collector):
        collector = Mock()
        collector.collect.side_effect = RuntimeError("upstream unavailable")
        build_collector.return_value = collector

        call_command("collect_jobs", stdout=StringIO(), stderr=StringIO())

        run = CollectionRun.objects.get()
        result = CollectionSourceResult.objects.get(run=run, source=self.source)

        self.assertEqual(run.status, CollectionRun.Status.COMPLETED_WITH_ERRORS)
        self.assertEqual(run.successful_sources, 0)
        self.assertEqual(run.failed_sources, 1)
        self.assertEqual(run.persisted_count, 0)

        self.assertEqual(result.status, CollectionSourceResult.Status.FAILED)
        self.assertEqual(result.error_type, "RuntimeError")
        self.assertEqual(result.error_message, "upstream unavailable")
        self.assertIsNotNone(result.finished_at)
