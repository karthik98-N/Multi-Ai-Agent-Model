"""
Resilience Engine
=================
Provides the four dependability primitives the pipeline plugs into:

1. source_credibility(evidence_pool)
   Scores each EvidenceItem 0-1 based on domain, snippet quality, and URL heuristics.

2. score_confidence(claims, contradictions, objections, evidence_pool)
   Weighted confidence score that accounts for source credibility + ambiguity.
   Returns ConfidenceBreakdown with sub-scores and an overall 0-100 figure.

3. detect_ambiguity(claims, evidence_pool)
   Returns an AmbiguityReport: fraction of claims that cannot be clearly resolved
   even after verification, and a human-readable summary.

4. build_epistemic_hedge(answer, breakdown, guard_report)
   Wraps the final answer with calibrated uncertainty language so consumers
   are never misled about confidence.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from app.models.schemas import AtomicClaim, ClaimStatus, EvidenceItem, ContradictionItem, CriticObjection, ObjectionSeverity

logger = logging.getLogger(__name__)

# ── Trusted domain whitelist (partial-match) ──────────────────────────────────
_HIGH_TRUST_DOMAINS = {
    "wikipedia.org", "britannica.com",
    "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov",
    "docs.python.org", "developer.mozilla.org", "docs.microsoft.com",
    "arxiv.org", "ieee.org", "acm.org",
    "gov", "edu",  # TLD suffix match
    "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
}

_LOW_TRUST_DOMAINS = {
    "reddit.com", "quora.com", "yahoo.answers",
    "medium.com",   # not categorically bad but user-generated
}

_SUSPICIOUS_SNIPPET_PATTERNS = [
    r"\bsource(s)?\s+say\b",          # vague attribution
    r"\bsome\s+(people|experts)\b",   # weasel words
    r"\bit\s+is\s+believed\b",
    r"\bapparently\b",
    r"\baccording\s+to\s+rumou?rs?\b",
]


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SourceScore:
    ref_id: str
    domain: str
    credibility: float      # 0.0 – 1.0
    flags: List[str] = field(default_factory=list)


@dataclass
class ConfidenceBreakdown:
    factual_score: float        # % verified claims
    source_score: float         # avg weighted credibility of cited evidence
    consistency_score: float    # penalty for contradictions
    critic_score: float         # penalty for critic objections
    overall: float              # composite 0-100
    label: str                  # "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT"
    explanation: str


@dataclass
class AmbiguityReport:
    ambiguous_fraction: float           # 0-1
    ambiguous_claim_ids: List[str]
    conflict_count: int
    summary: str
    is_ambiguous: bool                  # True when fraction > threshold


# ─────────────────────────────────────────────────────────────────────────────

def source_credibility(evidence_pool: List[EvidenceItem]) -> Dict[str, SourceScore]:
    """Score each evidence item's credibility 0-1."""
    scores: Dict[str, SourceScore] = {}
    for item in evidence_pool:
        url = (item.url or "").lower()
        domain = _extract_domain(url)
        flags: List[str] = []

        # Base credibility
        cred = 0.6  # neutral default

        # Domain boost
        if any(td in domain for td in _HIGH_TRUST_DOMAINS):
            cred += 0.3
            flags.append("trusted-domain")
        elif any(ld in domain for ld in _LOW_TRUST_DOMAINS):
            cred -= 0.2
            flags.append("low-trust-domain")

        # Snippet quality penalties
        snippet = (item.snippet or "").lower()
        for pat in _SUSPICIOUS_SNIPPET_PATTERNS:
            if re.search(pat, snippet):
                cred -= 0.1
                flags.append(f"weasel-language:{pat[:20]}")
                break  # one penalty per item

        # Short / empty snippets
        if len(snippet) < 50:
            cred -= 0.15
            flags.append("thin-snippet")

        cred = round(max(0.0, min(1.0, cred)), 3)
        scores[item.id] = SourceScore(ref_id=item.id, domain=domain, credibility=cred, flags=flags)

    return scores


def score_confidence(
    claims: List[AtomicClaim],
    contradictions: List[ContradictionItem],
    objections: List[CriticObjection],
    evidence_pool: List[EvidenceItem],
) -> ConfidenceBreakdown:
    """
    Weighted confidence score with source credibility applied to citations.
    """
    source_scores = source_credibility(evidence_pool)

    # ── Factual score ──
    if not claims:
        factual = 50.0
    else:
        total = len(claims)
        verified = [c for c in claims if c.status == ClaimStatus.VERIFIED]

        # Weight each verified claim by average credibility of its cited evidence
        weighted_verified = 0.0
        for c in verified:
            refs = c.evidence_refs or []
            if refs:
                avg_cred = sum(source_scores[r].credibility for r in refs if r in source_scores)
                avg_cred = avg_cred / len(refs) if refs else 0.7
            else:
                avg_cred = 0.7  # claim verified but no specific ref
            weighted_verified += avg_cred

        unverified_penalty = sum(
            0.1 for c in claims if c.status == ClaimStatus.UNSUPPORTED
        )
        contradicted_penalty = sum(
            0.4 for c in claims if c.status == ClaimStatus.CONTRADICTED
        )
        factual = max(
            0.0,
            (weighted_verified / total) - unverified_penalty - contradicted_penalty
        ) * 100.0

    # ── Source credibility score ──
    if source_scores:
        avg_source = (sum(s.credibility for s in source_scores.values()) / len(source_scores)) * 100.0
    else:
        avg_source = 40.0  # no evidence is a penalty

    # ── Consistency score (contra penalty) ──
    consistency = max(0.0, 100.0 - len(contradictions) * 30.0)

    # ── Critic score ──
    critic_penalty = (
        sum(30.0 for o in objections if o.severity == ObjectionSeverity.CRITICAL)
        + sum(15.0 for o in objections if o.severity == ObjectionSeverity.HIGH)
        + sum(5.0  for o in objections if o.severity == ObjectionSeverity.MEDIUM)
    )
    critic = max(0.0, 100.0 - critic_penalty)

    # ── Composite (weighted average) ──
    overall = round(
        0.40 * factual
        + 0.25 * avg_source
        + 0.20 * consistency
        + 0.15 * critic,
        1
    )

    if overall >= 80:
        label = "HIGH"
    elif overall >= 60:
        label = "MEDIUM"
    elif overall >= 35:
        label = "LOW"
    else:
        label = "INSUFFICIENT"

    explanation = (
        f"Factual grounding: {factual:.0f}/100 | "
        f"Source credibility: {avg_source:.0f}/100 | "
        f"Consistency: {consistency:.0f}/100 | "
        f"Critic clearance: {critic:.0f}/100"
    )

    return ConfidenceBreakdown(
        factual_score=round(factual, 1),
        source_score=round(avg_source, 1),
        consistency_score=round(consistency, 1),
        critic_score=round(critic, 1),
        overall=overall,
        label=label,
        explanation=explanation,
    )


def detect_ambiguity(
    claims: List[AtomicClaim],
    contradictions: List[ContradictionItem],
) -> AmbiguityReport:
    """
    Identify claims that remain genuinely unresolvable:
      - UNSUPPORTED (no evidence to confirm or deny)
      - Part of a detected contradiction (conflicting evidence)
    """
    if not claims:
        return AmbiguityReport(
            ambiguous_fraction=0.0,
            ambiguous_claim_ids=[],
            conflict_count=len(contradictions),
            summary="No atomic claims extracted — full-text ambiguity assessment unavailable.",
            is_ambiguous=len(contradictions) > 0,
        )

    # Claims involved in a contradiction
    contra_texts = set()
    for c in contradictions:
        contra_texts.add(c.claim_a[:60])
        contra_texts.add(c.claim_b[:60])

    ambiguous_ids = []
    for c in claims:
        is_unsupported = c.status == ClaimStatus.UNSUPPORTED
        is_conflicted = any(ct in c.text for ct in contra_texts)
        if is_unsupported or is_conflicted:
            ambiguous_ids.append(c.id)

    fraction = len(ambiguous_ids) / len(claims)
    is_ambiguous = fraction > 0.3 or len(contradictions) >= 2

    if fraction == 0 and not contradictions:
        summary = "All claims are clearly resolvable with available evidence."
    elif fraction < 0.3 and len(contradictions) <= 1:
        summary = (
            f"{len(ambiguous_ids)} of {len(claims)} claims lack clear evidence support. "
            "Answer may contain minor gaps."
        )
    else:
        summary = (
            f"High ambiguity: {len(ambiguous_ids)}/{len(claims)} claims unresolvable, "
            f"{len(contradictions)} source conflict(s) detected. "
            "Answer must be treated with significant caution."
        )

    return AmbiguityReport(
        ambiguous_fraction=round(fraction, 3),
        ambiguous_claim_ids=ambiguous_ids,
        conflict_count=len(contradictions),
        summary=summary,
        is_ambiguous=is_ambiguous,
    )


def strip_references(text: str) -> str:
    """
    Strips inline reference citation tags like [REF-1], [REF-1, REF-2], (REF-1),
    removes trailing bibliography/sources sections, converts markdown tables to flowing text,
    and strips formatting elements like asterisks (** or *), pipes (|), headers (###),
    and dividers (---) to produce clean, natural paragraphs of normal text.
    """
    if not text:
        return ""

    if text.strip() in ('{"contradictions": []}', '{"contradictions":[]}', '{"contradictions": [ ]}'):
        return "[verified successfully]"

    text = re.sub(r'\{"contradictions":\s*\[\]\}', '[verified successfully]', text)

    # 1. Remove trailing references / sources / bibliography section
    text = re.sub(r'(?i)\n+\s*(?:references?|sources?|citations?|evidence cited|evidence pool)\s*:?[\s\S]*$', '', text)

    # 2. Remove conversational sign-offs at the end
    text = re.sub(r'(?i)\n*(?:if you (?:need|have|require)|let me know|feel free to|please let me know)[\s\S]*$', '', text.strip())

    # 3. Remove inline citation tags like [REF-1], [REF-1, REF-2], (REF-1), etc.
    text = re.sub(r'\[\s*REF[-\s]?\w+(?:\s*,\s*REF[-\s]?\w+)*\s*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(\s*REF[-\s]?\w+(?:\s*,\s*REF[-\s]?\w+)*\s*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\s*REF[^\s\]]*\s*\]', '', text, flags=re.IGNORECASE)

    # 4. Convert markdown tables into plain text sentences
    lines = text.split('\n')
    new_lines = []
    table_rows = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            # Ignore separator row like |---|---|
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            # Ignore header row
            if any(h in cells[0].lower() for h in ['source', 'item', 'claim', 'parameter', 'name', 'field', 'id', 'key']):
                continue
            if len(cells) >= 2:
                col1 = re.sub(r'[*_#]', '', cells[0]).strip()
                col2 = re.sub(r'[*_#]', '', cells[1]).strip()
                if col1 and col2:
                    table_rows.append(f"{col1}: {col2}")
                elif col2:
                    table_rows.append(col2)
            elif len(cells) == 1:
                table_rows.append(re.sub(r'[*_#]', '', cells[0]).strip())
        else:
            if table_rows:
                new_lines.append(" ".join(r if r.endswith(('.', '!', '?')) else r + '.' for r in table_rows))
                new_lines.append("")
                table_rows = []
            new_lines.append(line)

    if table_rows:
        new_lines.append(" ".join(r if r.endswith(('.', '!', '?')) else r + '.' for r in table_rows))
        new_lines.append("")

    text = '\n'.join(new_lines)

    # 5. Remove horizontal rules (---, ___, ***)
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 6. Remove markdown headers (#, ##, ###) - turn into clean sentence or label
    text = re.sub(r'^\s*#{1,6}\s*(.+)$', r'\n\n\1:\n\n', text, flags=re.MULTILINE)

    # 7. Remove bold / italic asterisks and underscores
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)

    # 8. Remove list markers (e.g. '1. ', '2. ', '- ', '* ', '• ')
    text = re.sub(r'^\s*(?:\d+[\.\)]|[-*•])\s+', '', text, flags=re.MULTILINE)

    # 9. Remove any remaining pipes or backticks
    text = text.replace('|', '').replace('`', '')

    # 10. Clean up punctuation and spacing
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r':\s*([.,;])', r'\1', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # 11. Normalize paragraphs: join single-newline lines, merge short labels with next paragraph
    raw_paras = [p.replace('\n', ' ').strip() for p in re.split(r'\n\s*\n+', text) if p.strip()]
    merged_paras = []
    i = 0
    while i < len(raw_paras):
        p = raw_paras[i]
        if p.endswith(':') and len(p) < 60 and i + 1 < len(raw_paras):
            merged_paras.append(f"{p} {raw_paras[i + 1]}")
            i += 2
        else:
            merged_paras.append(p)
            i += 1

    return '\n\n'.join(merged_paras)


def build_epistemic_hedge(
    answer: str,
    breakdown: ConfidenceBreakdown,
    ambiguity: AmbiguityReport,
    guard_signals: List[str],
) -> str:
    """
    Ensure the answer is returned in clean, normal text form without citation tags.
    If there is an advisory or insufficient-evidence state, prepend a clear normal-text note.
    Detailed confidence badges, breakdown, and audit lines are rendered cleanly in the UI components.
    """
    clean_ans = strip_references(answer)
    parts: List[str] = []

    # ── Input warning (adversarial / misleading input) ──
    if guard_signals:
        parts.append(
            f"Advisory: Query triggered potential premise risks ({'; '.join(guard_signals[:2])}). "
            "The verified findings below reflect grounded evidence only."
        )

    # ── INSUFFICIENT — special handling ──
    if breakdown.label == "INSUFFICIENT":
        parts.append(
            "Advisory: Insufficient verifiable evidence was found to fully substantiate all claims. "
            "The text below represents the best available synthesis from limited sources."
        )

    parts.append(clean_ans)
    return "\n\n".join(p for p in parts if p.strip())


# ── Utility ──────────────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Cheaply extract the registered domain from a URL string."""
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0].split("?")[0]
