"""
Guard Agent — Adversarial & Misleading Input Detection
=======================================================
Inspects the raw user query BEFORE the pipeline begins.
Detects:
  - Prompt injection attempts ("ignore previous instructions", role-override)
  - Deliberately misleading framing ("prove that X is true" style demands)
  - Jailbreak patterns
  - Factually impossible / incoherent queries
Returns a GuardReport dataclass with a risk level and reason list.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# ── Heuristic rule sets ───────────────────────────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instruction",
    r"disregard\s+your\s+(system|previous)",
    r"forget\s+everything",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+you\s+are|a\s+)?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"override\s+(your\s+)?(safety|guideline|restriction)",
    r"do\s+not\s+follow\s+",
    r"your\s+new\s+instructions?\s+are",
    r"system\s*:\s*you\s+are",
]

_MISLEADING_FRAMING = [
    r"prove\s+(to\s+me\s+)?that\b",
    r"confirm\s+that\b",
    r"just\s+say\s+yes",
    r"answer\s+must\s+be\s+yes",
    r"assume\s+(it\s+is\s+)?true\s+that",
    r"everyone\s+knows\s+that",
    r"it\s+is\s+well\s+known\s+that",       # epistemic coercion
    r"(obviously|clearly|undeniably)\b",    # hidden premise amplifiers
]

_INCOHERENCE_PATTERNS = [
    r"\b(always|never|all|every)\b.{0,30}\b(always|never|all|every)\b",  # tautological loops
    r"\bprove\b.{0,60}\b(cannot\s+be\s+proved|unprovable)\b",
]

_RISK_LEVELS = ("NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL")


@dataclass
class GuardReport:
    risk_level: str = "NONE"   # NONE | LOW | MEDIUM | HIGH | CRITICAL
    signals: List[str] = field(default_factory=list)
    sanitised_query: str = ""  # cleaned query to pass downstream

    @property
    def is_safe(self) -> bool:
        return self.risk_level in ("NONE", "LOW")

    @property
    def is_suspicious(self) -> bool:
        return self.risk_level == "MEDIUM"

    @property
    def is_blocked(self) -> bool:
        return self.risk_level in ("HIGH", "CRITICAL")


def inspect_query(query: str) -> GuardReport:
    """
    Run heuristic guards on a raw user query.
    Returns a GuardReport; downstream orchestrator decides what to do with it.
    """
    signals: List[str] = []
    max_risk = 0

    q_lower = query.lower()

    # ── Injection patterns (CRITICAL risk) ──
    for pat in _INJECTION_PATTERNS:
        if re.search(pat, q_lower):
            signals.append(f"Prompt injection pattern detected: '{pat}'")
            max_risk = max(max_risk, 4)  # CRITICAL

    # ── Misleading framing (MEDIUM-HIGH) ──
    framing_hits = sum(1 for pat in _MISLEADING_FRAMING if re.search(pat, q_lower))
    if framing_hits >= 3:
        signals.append(f"Strong conclusion-forcing framing detected ({framing_hits} markers)")
        max_risk = max(max_risk, 3)  # HIGH
    elif framing_hits >= 1:
        signals.append(f"Conclusion-forcing framing detected ({framing_hits} marker(s))")
        max_risk = max(max_risk, 2)  # MEDIUM

    # ── Incoherence patterns (LOW) ──
    for pat in _INCOHERENCE_PATTERNS:
        if re.search(pat, q_lower):
            signals.append(f"Possible incoherent / unprovable query structure")
            max_risk = max(max_risk, 1)  # LOW
            break

    # ── Excessive length heuristic (possible jailbreak padding) ──
    if len(query) > 4000:
        signals.append("Query unusually long — may contain padding / context stuffing")
        max_risk = max(max_risk, 2)  # MEDIUM

    risk_label = _RISK_LEVELS[max_risk]
    logger.info("Guard: risk=%s signals=%d", risk_label, len(signals))

    # Sanitise: strip obvious injection sequences from the query
    sanitised = query
    for pat in _INJECTION_PATTERNS:
        sanitised = re.sub(pat, "[REDACTED]", sanitised, flags=re.IGNORECASE)

    return GuardReport(
        risk_level=risk_label,
        signals=signals,
        sanitised_query=sanitised,
    )
