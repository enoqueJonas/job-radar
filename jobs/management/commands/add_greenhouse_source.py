from django.core.management.base import (
    BaseCommand,
)

from jobs.models import JobSource


class Command(BaseCommand):
    help = (
        "Create or update a Greenhouse "
        "job source."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "board_token",
            help=(
                "Greenhouse job board token."
            ),
        )

        parser.add_argument(
            "company",
            help=(
                "Human-readable company name."
            ),
        )

        parser.add_argument(
            "--name",
            help=(
                "Optional source name. "
                "Defaults to "
                "'<company> (Greenhouse)'."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        board_token = (
            options["board_token"]
        )

        company = (
            options["company"]
        )

        name = (
            options["name"]
            or f"{company} (Greenhouse)"
        )

        source, created = (
            JobSource.objects
            .update_or_create(
                name=name,
                defaults={
                    "kind": (
                        JobSource.Kind.ATS
                    ),
                    "enabled": True,
                    "base_url": (
                        "https://boards."
                        "greenhouse.io/"
                        f"{board_token}"
                    ),
                    "config": {
                        "provider": (
                            "greenhouse"
                        ),
                        "board_token": (
                            board_token
                        ),
                        "company": company,
                    },
                },
            )
        )

        verb = (
            "Created"
            if created
            else "Updated"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} source: "
                f"{source.name}"
            )
        )
