from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from discovery.models import (
    DiscoveryRun,
)
from discovery.promotion import (
    promote_discovered_sources,
)


class Command(BaseCommand):
    help = (
        "Promote discovered ATS boards "
        "into JobSource records."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "run_id",
            type=int,
        )

    def handle(
        self,
        *args,
        **options,
    ):
        try:
            run = (
                DiscoveryRun.objects.get(
                    pk=options["run_id"]
                )
            )
        except DiscoveryRun.DoesNotExist:
            raise CommandError(
                "Discovery run not found."
            )

        result = (
            promote_discovered_sources(
                run
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Promotion complete."
            )
        )

        self.stdout.write(
            f"Created: {result.created}"
        )

        self.stdout.write(
            f"Already existed: "
            f"{result.existing}"
        )

        self.stdout.write(
            f"Ignored: {result.ignored}"
        )
