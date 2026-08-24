from django.core.management.base import BaseCommand
from django.utils.text import slugify

from jobs.models import JobSource


class Command(BaseCommand):
    help = "Create or update a Lever job source."

    def add_arguments(self, parser):
        parser.add_argument("site", help="Lever site slug, e.g. 'leverdemo'.")
        parser.add_argument("company", help="Human-readable company name.")
        parser.add_argument(
            "--region",
            choices=["global", "eu"],
            default="global",
        )
        parser.add_argument(
            "--name",
            help="Optional source name. Defaults to '<company> (Lever)'.",
        )

    def handle(self, *args, **options):
        name = options["name"] or f"{options['company']} (Lever)"
        source, created = JobSource.objects.update_or_create(
            name=name,
            defaults={
                "kind": JobSource.Kind.ATS,
                "enabled": True,
                "base_url": (
                    "https://jobs.eu.lever.co/"
                    if options["region"] == "eu"
                    else "https://jobs.lever.co/"
                ) + options["site"],
                "config": {
                    "provider": "lever",
                    "site": options["site"],
                    "company": options["company"],
                    "region": options["region"],
                },
            },
        )
        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} source: {source.name}"))
