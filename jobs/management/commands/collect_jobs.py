from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from jobs.collectors.registry import build_collector
from jobs.models import CollectionRun, CollectionSourceResult, JobSource
from jobs.services import persist_collected_jobs


class Command(BaseCommand):
    help = "Collect jobs from enabled configured sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            action="append",
            dest="sources",
            help="Limit collection to a source name. May be repeated.",
        )
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Stop immediately if one source fails.",
        )

    def handle(self, *args, **options):
        queryset = JobSource.objects.filter(enabled=True).order_by("name")
        if options["sources"]:
            queryset = queryset.filter(name__in=options["sources"])

        sources = list(queryset)
        if not sources:
            raise CommandError("No enabled job sources matched the request.")

        run = CollectionRun.objects.create(
            requested_sources=options["sources"] or [],
            fail_fast=options["fail_fast"],
            source_count=len(sources),
        )

        total_collected = 0
        total_persisted = 0
        successes = 0
        failures = 0

        self.stdout.write(f"Collection run #{run.pk} started for {len(sources)} source(s).")

        for source in sources:
            self.stdout.write(f"Collecting from {source.name}...")
            source_result = CollectionSourceResult.objects.create(
                run=run,
                source=source,
                status=CollectionSourceResult.Status.FAILED,
            )

            try:
                collector = build_collector(source)
                collected = collector.collect()
                persisted = persist_collected_jobs(source, collected)
            except Exception as exc:
                failures += 1
                source_result.error_type = type(exc).__name__
                source_result.error_message = str(exc)
                source_result.finished_at = timezone.now()
                source_result.save(
                    update_fields=["error_type", "error_message", "finished_at"]
                )

                self.stderr.write(
                    self.style.ERROR(f"{source.name}: {type(exc).__name__}: {exc}")
                )

                if options["fail_fast"]:
                    self._finish_run(
                        run,
                        status=CollectionRun.Status.FAILED,
                        successes=successes,
                        failures=failures,
                        collected=total_collected,
                        persisted=total_persisted,
                    )
                    raise CommandError(f"Collection failed for {source.name}") from exc
                continue

            collected_count = len(collected)
            persisted_count = len(persisted)
            successes += 1
            total_collected += collected_count
            total_persisted += persisted_count

            source_result.status = CollectionSourceResult.Status.SUCCESS
            source_result.collected_count = collected_count
            source_result.persisted_count = persisted_count
            source_result.finished_at = timezone.now()
            source_result.save(
                update_fields=[
                    "status",
                    "collected_count",
                    "persisted_count",
                    "finished_at",
                ]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{source.name}: collected {collected_count}; "
                    f"persisted {persisted_count}."
                )
            )

        status = (
            CollectionRun.Status.COMPLETED_WITH_ERRORS
            if failures
            else CollectionRun.Status.COMPLETED
        )
        self._finish_run(
            run,
            status=status,
            successes=successes,
            failures=failures,
            collected=total_collected,
            persisted=total_persisted,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: run #{run.pk}; {total_persisted} jobs persisted across "
                f"{len(sources)} source(s); {failures} source failure(s)."
            )
        )

    @staticmethod
    def _finish_run(run, *, status, successes, failures, collected, persisted):
        run.status = status
        run.successful_sources = successes
        run.failed_sources = failures
        run.collected_count = collected
        run.persisted_count = persisted
        run.finished_at = timezone.now()
        run.save(
            update_fields=[
                "status",
                "successful_sources",
                "failed_sources",
                "collected_count",
                "persisted_count",
                "finished_at",
            ]
        )
