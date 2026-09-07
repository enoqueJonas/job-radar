from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from discovery.query_builder import (
    build_discovery_queries,
)
from searches.models import SearchProfile


class Command(BaseCommand):
    help = (
        "Preview generated discovery "
        "queries for a search profile."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "profile",
            help="Search profile slug.",
        )

    def handle(
        self,
        *args,
        **options,
    ):
        try:
            profile = (
                SearchProfile.objects.get(
                    slug=options["profile"],
                )
            )
        except SearchProfile.DoesNotExist:
            raise CommandError(
                "Search profile not found."
            )

        queries = (
            build_discovery_queries(
                profile
            )
        )

        self.stdout.write(
            f"Generated {len(queries)} "
            f"queries:\n"
        )

        for query in queries:
            self.stdout.write(
                f"- {query.query}"
            )

            self.stdout.write(
                "  domains: "
                + ", ".join(
                    query.include_domains
                )
            )
