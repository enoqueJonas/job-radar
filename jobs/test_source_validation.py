from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from jobs.models import JobSource
from jobs.source_validation import validate_source


class SourceValidationHardeningTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="Acme Lever Hardened",
            kind=JobSource.Kind.ATS,
            enabled=False,
            config={
                "provider": "lever",
                "site": "acme",
                "company": "Acme",
                "region": "global",
            },
        )

    @patch("jobs.source_validation.requests.get")
    def test_server_error_stays_unknown_and_retryable(
        self,
        mock_get,
    ):
        response = Mock()
        response.status_code = 503
        mock_get.return_value = response

        result = validate_source(self.source)
        self.source.refresh_from_db()

        self.assertFalse(result.valid)
        self.assertTrue(result.retryable)
        self.assertFalse(self.source.enabled)
        self.assertEqual(
            self.source.validation_status,
            JobSource.ValidationStatus.UNKNOWN,
        )

    @patch("jobs.source_validation.requests.get")
    def test_rate_limit_stays_unknown_and_retryable(
        self,
        mock_get,
    ):
        response = Mock()
        response.status_code = 429
        mock_get.return_value = response

        result = validate_source(self.source)
        self.source.refresh_from_db()

        self.assertTrue(result.retryable)
        self.assertEqual(
            self.source.validation_status,
            JobSource.ValidationStatus.UNKNOWN,
        )

    @patch("jobs.source_validation.requests.get")
    def test_network_error_stays_unknown_and_retryable(
        self,
        mock_get,
    ):
        mock_get.side_effect = requests.Timeout(
            "validation timed out"
        )

        result = validate_source(self.source)
        self.source.refresh_from_db()

        self.assertFalse(result.valid)
        self.assertTrue(result.retryable)
        self.assertFalse(self.source.enabled)
        self.assertEqual(
            self.source.validation_status,
            JobSource.ValidationStatus.UNKNOWN,
        )
        self.assertIn(
            "validation timed out",
            self.source.validation_error,
        )

    @patch("jobs.source_validation.requests.get")
    def test_not_found_is_definitively_invalid(
        self,
        mock_get,
    ):
        response = Mock()
        response.status_code = 404
        mock_get.return_value = response

        result = validate_source(self.source)
        self.source.refresh_from_db()

        self.assertFalse(result.valid)
        self.assertFalse(result.retryable)
        self.assertEqual(
            self.source.validation_status,
            JobSource.ValidationStatus.INVALID,
        )
