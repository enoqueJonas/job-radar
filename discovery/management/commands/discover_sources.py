from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from discovery.providers.tavily import (
    TavilySearchProvider,
)
from discovery.services import (
    run_discovery,
)
from searches.models import (
    SearchProfile,
)


class Command(BaseCommand):
    help = (
        "Discover ATS job sources "
        "for a search profile."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "profile",
            help="Search profile slug.",
        )

        parser.add_argument(
            "--max-results",
            type=int,
            default=10,
        )

    def handle(
        self,
        *args,
        **options,
    ):
        try:
            profile = (
                SearchProfile.objects
                .get(
                    slug=(
                        options["profile"]
                    )
                )
            )
        except SearchProfile.DoesNotExist:
            raise CommandError(
                "Search profile not found."
            )

        provider = (
            TavilySearchProvider()
        )

        run = run_discovery(
            profile=profile,
            provider=provider,
            max_results_per_query=(
                options["max_results"]
            ),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Discovery run #{run.id} "
                f"completed."
            )
        )

        self.stdout.write(
            f"Discovered "
            f"{run.sources.count()} "
            f"ATS URLs."
        )
