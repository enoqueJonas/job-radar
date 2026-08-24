from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Iterable

from jobs.collectors.base import CollectedJob


EXTRACTION_VERSION = "0.1"


@dataclass(frozen=True)
class ExperienceRequirement:
    minimum: float | None
    maximum: float | None
    required: bool
    confidence: float
    context: str

    def as_dict(self) -> dict:
        return {
            "kind": "experience",
            "minimum": self.minimum,
            "maximum": self.maximum,
            "required": self.required,
            "confidence": self.confidence,
            "context": self.context,
        }


PREFERENCE_MARKERS = (
    "preferred",
    "preferably",
    "nice to have",
    "nice-to-have",
    "bonus",
    "desirable",
    "advantage",
    "ideally",
    "would be a plus",
)


NON_CANDIDATE_CONTEXT_MARKERS = (
    "company has",
    "company with",
    "operating for",
    "in business for",
    "founded",
    "established",
    "years in business",
    "years of operation",
    "years operating",
)


EXPERIENCE_CONTEXT_MARKERS = (
    "experience",
    "experienced",
    "qa",
    "quality assurance",
    "testing",
    "test engineer",
    "software",
    "engineering",
    "automation",
    "development",
    "technical",
    "technology",
)


RANGE_PATTERN = re.compile(
    r"""
    (?P<minimum>\d+(?:\.\d+)?)
    \s*
    (?:-|–|—|to)
    \s*
    (?P<maximum>\d+(?:\.\d+)?)
    \s*
    years?
    """,
    re.IGNORECASE | re.VERBOSE,
)


AT_LEAST_PATTERN = re.compile(
    r"""
    (?:at\s+least|minimum\s+of|min(?:imum)?\.?)
    \s*
    (?P<minimum>\d+(?:\.\d+)?)
    \s*
    years?
    """,
    re.IGNORECASE | re.VERBOSE,
)


PLUS_PATTERN = re.compile(
    r"""
    (?P<minimum>\d+(?:\.\d+)?)
    \s*
    \+
    \s*
    years?
    """,
    re.IGNORECASE | re.VERBOSE,
)


YEARS_EXPERIENCE_PATTERN = re.compile(
    r"""
    (?P<minimum>\d+(?:\.\d+)?)
    \s*
    years?
    (?:\s+of)?
    \s+
    (?:
        relevant\s+
        |
        professional\s+
        |
        hands-on\s+
        |
        practical\s+
        |
        software\s+
        |
        qa\s+
        |
        testing\s+
        |
        engineering\s+
    )*
    experience
    """,
    re.IGNORECASE | re.VERBOSE,
)


UP_TO_PATTERN = re.compile(
    r"""
    (?:up\s+to|maximum\s+of|max(?:imum)?\.?)
    \s*
    (?P<maximum>\d+(?:\.\d+)?)
    \s*
    years?
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _sentences(text: str) -> list[str]:
    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)

    return [
        part.strip()
        for part in parts
        if part and part.strip()
    ]


def _is_preference(text: str) -> bool:
    lowered = text.casefold()

    return any(
        marker in lowered
        for marker in PREFERENCE_MARKERS
    )


def _looks_like_candidate_experience(text: str) -> bool:
    lowered = text.casefold()

    if any(
        marker in lowered
        for marker in NON_CANDIDATE_CONTEXT_MARKERS
    ):
        return False

    return any(
        marker in lowered
        for marker in EXPERIENCE_CONTEXT_MARKERS
    )


def extract_experience_requirements(
    text: str,
) -> list[ExperienceRequirement]:
    requirements: list[ExperienceRequirement] = []

    for sentence in _sentences(text):
        if not _looks_like_candidate_experience(sentence):
            continue

        required = not _is_preference(sentence)

        range_match = RANGE_PATTERN.search(sentence)

        if range_match:
            requirements.append(
                ExperienceRequirement(
                    minimum=float(range_match.group("minimum")),
                    maximum=float(range_match.group("maximum")),
                    required=required,
                    confidence=0.95,
                    context=sentence,
                )
            )
            continue

        minimum_match = (
            AT_LEAST_PATTERN.search(sentence)
            or PLUS_PATTERN.search(sentence)
            or YEARS_EXPERIENCE_PATTERN.search(sentence)
        )

        if minimum_match:
            requirements.append(
                ExperienceRequirement(
                    minimum=float(
                        minimum_match.group("minimum")
                    ),
                    maximum=None,
                    required=required,
                    confidence=0.9,
                    context=sentence,
                )
            )
            continue

        maximum_match = UP_TO_PATTERN.search(sentence)

        if maximum_match:
            requirements.append(
                ExperienceRequirement(
                    minimum=None,
                    maximum=float(
                        maximum_match.group("maximum")
                    ),
                    required=required,
                    confidence=0.85,
                    context=sentence,
                )
            )

    return requirements


def extract_skills(
    text: str,
    skill_keywords: Iterable,
) -> list[str]:
    lowered = text.casefold()

    detected: set[str] = set()

    for skill in skill_keywords:
        terms = {
            skill.canonical_name.casefold(),
            *[
                str(alias).casefold()
                for alias in skill.aliases
            ],
        }

        for term in terms:
            if not term:
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(term)
                + r"(?!\w)"
            )

            if re.search(pattern, lowered):
                detected.add(skill.canonical_name)
                break

    return sorted(detected)


def enrich_collected_job(
    job: CollectedJob,
    skill_keywords: Iterable,
) -> tuple[CollectedJob, list[dict]]:
    searchable_text = "\n".join(
        part
        for part in (
            job.title,
            job.description,
        )
        if part
    )

    experience_requirements = (
        extract_experience_requirements(
            searchable_text
        )
    )

    required_experience = [
        requirement
        for requirement in experience_requirements
        if requirement.required
    ]

    minimum_values = [
        requirement.minimum
        for requirement in required_experience
        if requirement.minimum is not None
    ]

    maximum_values = [
        requirement.maximum
        for requirement in required_experience
        if requirement.maximum is not None
    ]

    extracted_minimum = (
        max(minimum_values)
        if minimum_values
        else None
    )

    extracted_maximum = (
        max(maximum_values)
        if maximum_values
        else None
    )

    extracted_skills = extract_skills(
        searchable_text,
        skill_keywords,
    )

    existing_skills = {
        skill.casefold(): skill
        for skill in job.skills
    }

    for skill in extracted_skills:
        existing_skills[skill.casefold()] = skill

    enriched = replace(
        job,
        min_years_experience=(
            job.min_years_experience
            if job.min_years_experience is not None
            else extracted_minimum
        ),
        max_years_experience=(
            job.max_years_experience
            if job.max_years_experience is not None
            else extracted_maximum
        ),
        skills=sorted(existing_skills.values()),
    )

    extracted_requirements = [
        requirement.as_dict()
        for requirement in experience_requirements
    ]

    return enriched, extracted_requirements
