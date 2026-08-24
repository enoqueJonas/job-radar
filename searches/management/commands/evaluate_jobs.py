from django.core.management.base import BaseCommand
from searches.models import SearchProfile
from searches.services import evaluate_profile


class Command(BaseCommand):
    help = "Evaluate active jobs against active search profiles."

    def add_arguments(self, parser):
        parser.add_argument("--profile", help="Optional profile slug")

    def handle(self, *args, **options):
        profiles = SearchProfile.objects.filter(active=True)
        if options["profile"]:
            profiles = profiles.filter(slug=options["profile"])

        for profile in profiles:
            matches = evaluate_profile(profile)
            eligible = sum(1 for match in matches if match.eligible)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{profile.name}: evaluated {len(matches)} jobs; "
                    f"{eligible} eligible."
                )
            )
