from django.core.management.base import BaseCommand, CommandError

from jobs.collectors.registry import UnsupportedCollectorError, build_collector
from jobs.models import JobSource
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

        total = 0
        failures = 0

        for source in sources:
            self.stdout.write(f"Collecting from {source.name}...")

            try:
                collector = build_collector(source)
                collected = collector.collect()
                persisted = persist_collected_jobs(source, collected)
            except Exception as exc:
                failures += 1
                self.stderr.write(
                    self.style.ERROR(f"{source.name}: {type(exc).__name__}: {exc}")
                )
                if options["fail_fast"]:
                    raise CommandError(f"Collection failed for {source.name}") from exc
                continue

            total += len(persisted)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{source.name}: collected {len(collected)}; persisted {len(persisted)}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {total} jobs persisted across {len(sources)} source(s); "
                f"{failures} source failure(s)."
            )
        )
