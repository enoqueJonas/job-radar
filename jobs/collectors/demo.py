from .base import BaseCollector, CollectedJob


class DemoCollector(BaseCollector):
    def collect(self):
        return [
            CollectedJob(
                external_id="demo-qa-001",
                title="QA Engineer",
                company="Demo Payments",
                url="https://example.com/jobs/demo-qa-001",
                description=(
                    "We are looking for a QA Engineer with 3+ years of experience. "
                    "Experience with API testing, Postman, Jira, SQL and Agile is preferred. "
                    "Fintech or payments experience is a bonus."
                ),
                location_text="Remote - EMEA",
                remote_type="remote",
                min_years_experience=3,
                skills=["api testing", "postman", "jira", "sql", "agile", "payments"],
            ),
            CollectedJob(
                external_id="demo-principal-001",
                title="Principal QA Architect",
                company="Demo Enterprise",
                url="https://example.com/jobs/demo-principal-001",
                description="Requires 10+ years of software quality engineering experience.",
                location_text="London",
                remote_type="hybrid",
                min_years_experience=10,
                skills=["test strategy", "leadership"],
            ),
        ]
