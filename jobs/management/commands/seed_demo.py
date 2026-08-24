from django.core.management.base import BaseCommand

from jobs.collectors.demo import DemoCollector
from jobs.models import JobSource, SkillKeyword
from jobs.services import persist_collected_jobs
from searches.models import SearchProfile, SearchRule


class Command(BaseCommand):
    help = "Seed demo jobs and a configurable QA search profile."

    def handle(self, *args, **options):
        skills = {
            "api testing": [
                "api testing",
                "api tests",
                "rest api testing",
            ],
            "postman": [
                "postman",
            ],
            "playwright": [
                "playwright",
                "microsoft playwright",
            ],
            "selenium": [
                "selenium",
                "selenium webdriver",
            ],
            "jira": [
                "jira",
            ],
            "sql": [
                "sql",
            ],
            "agile": [
                "agile",
                "scrum",
            ],
            "automation testing": [
                "test automation",
                "automated testing",
                "automation testing",
            ],
        }

        for canonical_name, aliases in skills.items():
            SkillKeyword.objects.update_or_create(
                canonical_name=canonical_name,
                defaults={
                    "aliases": aliases,
                    "enabled": True,
                },
            )
        source, _ = JobSource.objects.get_or_create(
            name="Demo",
            defaults={"kind": JobSource.Kind.MANUAL},
        )

        persist_collected_jobs(source, DemoCollector().collect())

        profile, _ = SearchProfile.objects.get_or_create(
            slug="qa-main",
            defaults={
                "name": "QA – Main Search",
                "description": "Initial configurable QA search profile",
                "minimum_score": 35,
            },
        )

        rules = [
            {
                "name": "Maximum 7 years required",
                "rule_type": "filter",
                "field": "min_years_experience",
                "operator": "lte",
                "value": 7,
                "required": True,
                "weight": 0,
                "order": 10,
            },
            {
                "name": "QA/Test title",
                "rule_type": "score",
                "field": "title",
                "operator": "contains",
                "value": ["qa", "quality assurance", "test engineer", "test analyst"],
                "required": False,
                "weight": 25,
                "order": 20,
            },
            {
                "name": "API testing",
                "rule_type": "score",
                "field": "skills",
                "operator": "contains",
                "value": ["api testing", "postman"],
                "required": False,
                "weight": 15,
                "order": 30,
            },
            {
                "name": "Banking / fintech / payments",
                "rule_type": "score",
                "field": "description",
                "operator": "contains",
                "value": ["banking", "fintech", "payments"],
                "required": False,
                "weight": 15,
                "order": 40,
            },
            {
                "name": "Remote",
                "rule_type": "score",
                "field": "remote_type",
                "operator": "eq",
                "value": "remote",
                "required": False,
                "weight": 10,
                "order": 50,
            },
        ]

        for data in rules:
            SearchRule.objects.update_or_create(
                profile=profile,
                name=data["name"],
                defaults=data,
            )

        self.stdout.write(self.style.SUCCESS(
            "Seeded demo source, jobs and QA profile."))
