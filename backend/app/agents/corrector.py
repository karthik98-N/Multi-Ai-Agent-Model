import logging
from typing import List, Tuple
from app.models.schemas import AtomicClaim, CriticObjection, EvidenceItem, ClaimStatus
from app.llm.client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the SURGICAL CORRECTION AGENT in a Multi-Agent AI Verification Platform.
Your task is to revise and repair the candidate answer based on audit failures from the Verifier and Critic.

REPAIR GUIDELINES:
1. Fix or remove any claim flagged as CONTRADICTED or UNSUPPORTED.
2. Address each CRITICAL or HIGH severity Critic objection.
3. Preserve already-verified sections without unnecessary rewrites.
4. Keep all factual claims strictly cited with [REF-X] brackets.
5. If an unverified assertion cannot be supported with available evidence, explicitly state the limitation or omit it.
6. FORMAT AS NORMAL PARAGRAPHS ONLY: Output strictly as standard, flowing narrative paragraphs of plain text.
7. NEVER use markdown tables (no pipes |).
8. NEVER use formatting symbols: no asterisks (**bold** or *italic*), no headers (###), no horizontal rules (---), and no bullet lists.
"""


def correct_answer(
    query: str,
    current_draft: str,
    failed_claims: List[AtomicClaim],
    objections: List[CriticObjection],
    evidence_pool: List[EvidenceItem]
) -> Tuple[str, str]:
    """
    Returns:
        (corrected_draft, diff_summary)
    """
    audit_notes = []
    for c in failed_claims:
        audit_notes.append(f"- Claim [{c.id}] was {c.status}: '{c.text}'. Reason: {c.reasoning}")
        
    for obj in objections:
        audit_notes.append(f"- Critic [{obj.severity}]: {obj.issue} (Target: {obj.target}). Fix: {obj.recommendation}")
        
    audit_text = "\n".join(audit_notes) if audit_notes else "General grounding enhancement required."
    evidence_text = "\n".join([f"[{e.id}] {e.title}: {e.snippet}" for e in evidence_pool])

    prompt = f"""USER QUERY:
{query}

CURRENT DRAFT:
{current_draft}

AUDIT DEFECTS TO FIX:
{audit_text}

AVAILABLE EVIDENCE:
{evidence_text}

Output the corrected answer strictly as standard, clean paragraphs of text with proper [REF-X] citations (no markdown tables or formatting symbols):"""

    corrected_draft = llm_client.call_llm(
        prompt=prompt,
        system_instruction=SYSTEM_PROMPT,
        model_type="primary",
        temperature=0.2
    )

    diff_summary = f"Repaired {len(failed_claims)} failed claims and addressed {len(objections)} critic objections."
    return corrected_draft, diff_summary
