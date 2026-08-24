from dataclasses import dataclass, field
from typing import Any

from jobs.models import Job
from .models import SearchProfile, SearchRule


@dataclass
class Evaluation:
    eligible: bool = True
    score: int = 0
    matched_weight: int = 0
    possible_weight: int = 0
    reasons: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)


def _normalize(value: Any):
    if isinstance(value, str):
        return value.casefold().strip()
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def rule_matches(
    job: Job,
    rule: SearchRule,
) -> bool | None:
    actual = getattr(job, rule.field, None)
    expected = rule.value

    actual_n = _normalize(actual)
    expected_n = _normalize(expected)

    if rule.operator == SearchRule.Operator.CONTAINS:
        if isinstance(actual_n, list):
            values = expected_n if isinstance(
                expected_n, list) else [expected_n]
            return any(v in actual_n for v in values)
        if isinstance(expected_n, list):
            return any(str(v) in str(actual_n or "") for v in expected_n)
        return str(expected_n) in str(actual_n or "")

    if rule.operator == SearchRule.Operator.NOT_CONTAINS:
        if isinstance(expected_n, list):
            return all(str(v) not in str(actual_n or "") for v in expected_n)
        return str(expected_n) not in str(actual_n or "")

    if rule.operator == SearchRule.Operator.IN:
        expected_values = expected_n if isinstance(
            expected_n, list) else [expected_n]
        return actual_n in expected_values

    # Missing structured values do not satisfy numeric/equality constraints.
    if actual_n is None:
        return None

    if rule.operator == SearchRule.Operator.LTE:
        return float(actual_n) <= float(expected_n)

    if rule.operator == SearchRule.Operator.GTE:
        return float(actual_n) >= float(expected_n)

    if rule.operator == SearchRule.Operator.EQ:
        return actual_n == expected_n

    raise ValueError(f"Unsupported operator: {rule.operator}")


def evaluate_job(job: Job, profile: SearchProfile) -> Evaluation:
    result = Evaluation()
    rules = profile.rules.filter(enabled=True)

    score_rules = [r for r in rules if r.rule_type ==
                   SearchRule.RuleType.SCORE]
    result.possible_weight = sum(max(0, r.weight) for r in score_rules)

    for rule in rules:
        matched = rule_matches(
            job,
            rule,
        )

        if (
            matched is None
            and rule.missing_behavior
            == SearchRule.MissingBehavior.IGNORE
        ):
            continue

        if (
            matched is None
            and rule.missing_behavior
            == SearchRule.MissingBehavior.FAIL
        ):
            result.eligible = False
            result.rejection_reasons.append(
                f"{rule.name}: value unavailable"
            )
            continue

        if (
            rule.rule_type
            == SearchRule.RuleType.FILTER
        ):
            if rule.required and matched is False:
                result.eligible = False
                result.rejection_reasons.append(
                    rule.name
                )

            elif matched is True:
                result.reasons.append(
                    rule.name
                )
            continue

        if (
            rule.rule_type
            == SearchRule.RuleType.SCORE
        ):
            if matched is True:
                awarded = max(
                    0,
                    rule.weight,
                )

                result.matched_weight += awarded

                result.reasons.append(
                    f"{rule.name} (+{awarded})"
                )

            continue

    if result.possible_weight > 0:
        result.score = round(
            (result.matched_weight / result.possible_weight) * 100)

    if result.score < profile.minimum_score:
        result.eligible = False
        result.rejection_reasons.append(
            f"Score {result.score}% below profile minimum {profile.minimum_score}%"
        )

    return result
