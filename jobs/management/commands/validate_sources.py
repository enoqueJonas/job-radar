from django.core.management.base import (
    BaseCommand,
)

from jobs.models import JobSource
from jobs.source_validation import (
    validate_source,
)


class Command(BaseCommand):
    help = (
        "Validate ATS job sources and "
        "enable only valid ones."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--source",
            action="append",
            dest="sources",
        )

        parser.add_argument(
            "--timeout",
            type=int,
            default=15,
            help=(
                "Per-source HTTP timeout in seconds "
                "(default: 15)."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        timeout_seconds = options["timeout"]

        if timeout_seconds <= 0:
            self.stderr.write(
                self.style.ERROR(
                    "--timeout must be greater than 0."
                )
            )
            return

        queryset = (
            JobSource.objects
            .filter(
                kind=JobSource.Kind.ATS
            )
            .order_by("name")
        )

        if options["sources"]:
            queryset = queryset.filter(
                name__in=options["sources"]
            )

        valid = 0
        invalid = 0
        retryable = 0

        for source in queryset:
            self.stdout.write(
                f"Validating "
                f"{source.name}..."
            )

            result = validate_source(
                source,
                timeout_seconds=timeout_seconds,
            )

            if result.valid:
                valid += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        "  valid"
                    )
                )

            elif result.retryable:
                retryable += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"  retryable: "
                        f"{result.error}"
                    )
                )

            else:
                invalid += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"  invalid: "
                        f"{result.error}"
                    )
                )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Valid: {valid}"
            )
        )

        self.stdout.write(
            f"Invalid: {invalid}"
        )

        self.stdout.write(
            f"Retryable/unknown: {retryable}"
        )
