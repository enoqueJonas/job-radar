import hashlib
import re
import unicodedata


def normalize_text(value: str) -> str:
    value = value or ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    value = value.casefold()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def build_job_fingerprint(
    *,
    company: str,
    title: str,
    location: str = "",
) -> str:
    normalized = "|".join(
        [
            normalize_text(company),
            normalize_text(title),
            normalize_text(location),
        ]
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()
