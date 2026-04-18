"""
Confidence scoring for MedGemma AI diagnosis results.

Applies heuristic rules on top of the model's raw confidence
to determine whether human review is required.
"""


DEFAULT_THRESHOLD = 0.7
HIGH_RISK_KEYWORDS = [
    "malignant", "tumor", "cancer", "fracture", "hemorrhage",
    "stroke", "embolism", "aneurysm", "sepsis", "cardiac arrest",
]


def score_confidence(result: dict, threshold: float = DEFAULT_THRESHOLD) -> float:
    """
    Calculate a calibrated confidence score.

    Factors:
    - Raw model confidence
    - Presence of high-risk findings (lowers effective threshold)
    - Number of findings (more findings = more complex = lower confidence)
    - Reasoning length (very short reasoning may indicate low quality)
    """
    raw = result.get("confidence", 0.5)

    findings = result.get("findings", [])
    diagnosis_text = (result.get("diagnosis", "") + " " + result.get("reasoning", "")).lower()

    penalty = 0.0

    has_high_risk = any(kw in diagnosis_text for kw in HIGH_RISK_KEYWORDS)
    if has_high_risk:
        penalty += 0.15

    if len(findings) > 5:
        penalty += 0.05 * (len(findings) - 5)

    reasoning = result.get("reasoning", "")
    if len(reasoning) < 50:
        penalty += 0.1

    calibrated = max(0.0, min(1.0, raw - penalty))
    return round(calibrated, 3)


def needs_human_review(result: dict, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """Determine if a diagnosis requires human review."""
    confidence = result.get("confidence", 0)
    if confidence < threshold:
        return True

    diagnosis_text = (result.get("diagnosis", "") + " " + result.get("reasoning", "")).lower()
    if any(kw in diagnosis_text for kw in HIGH_RISK_KEYWORDS):
        return True

    if result.get("error"):
        return True

    return False


def categorize_urgency(result: dict) -> str:
    """Categorize the urgency level of a diagnosis."""
    confidence = result.get("confidence", 0)
    diagnosis_text = (result.get("diagnosis", "") + " " + result.get("reasoning", "")).lower()

    critical_keywords = ["cardiac arrest", "stroke", "hemorrhage", "sepsis", "aneurysm"]
    if any(kw in diagnosis_text for kw in critical_keywords):
        return "critical"

    if any(kw in diagnosis_text for kw in HIGH_RISK_KEYWORDS):
        return "high"

    if confidence < 0.5:
        return "high"
    elif confidence < 0.7:
        return "medium"
    else:
        return "low"
