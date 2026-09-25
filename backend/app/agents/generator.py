import logging
from typing import List, Tuple
from app.models.schemas import EvidenceItem, PlanTask
from app.llm.client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Specialist GENERATOR AGENT of a Multi-Agent AI Verification Platform.
Your goal is to answer the user query based ONLY on the provided Evidence Pool.

STRICT GROUNDING & FORMATTING RULES:
1. Every significant claim, fact, parameter, or conclusion MUST cite its source using inline bracket tags like [REF-1], [REF-2].
2. Do NOT invent APIs, facts, numbers, or dates that are not directly supported by the evidence.
3. If the evidence is incomplete, ambiguous, or lacks sufficient data, explicitly state what is missing instead of guessing.
4. FORMAT AS NORMAL PARAGRAPHS ONLY: Write the entire response strictly as standard, flowing narrative paragraphs of text.
5. NEVER use markdown tables (do NOT use pipes | or table syntax).
6. NEVER use formatting symbols: do NOT use asterisks (**bold** or *italic*), do NOT use markdown headers (###), do NOT use horizontal rules (---), and do NOT use bulleted lists.
7. Keep the writing natural, professional, and clear.
"""

BASELINE_PROMPT = """You are a standard AI assistant. Answer the user prompt directly and confidently in 1-2 paragraphs. Do not cite references."""


def generate_candidate_answer(
    query: str,
    evidence_pool: List[EvidenceItem],
    plan: PlanTask
) -> Tuple[str, str]:
    """
    Returns:
        (grounded_draft_answer, raw_unverified_baseline_answer)
    """
    evidence_text = "\n\n".join([
        f"[{item.id}] {item.title}\n{item.snippet}"
        for item in evidence_pool
    ])
    
    prompt = f"""User Query:
{query}

Plan Focus:
{', '.join(plan.focus_areas)}

Available Evidence Pool:
{evidence_text if evidence_text else "No external evidence available."}

Generate the grounded response now as standard, clean paragraphs of text, citing [REF-X] tags (do not use markdown tables or formatting symbols):"""

    grounded_answer = llm_client.call_llm(
        prompt=prompt,
        system_instruction=SYSTEM_PROMPT,
        model_type="primary",
        temperature=0.3
    )
    
    # Also generate raw unverified answer for side-by-side jury view
    raw_unverified = llm_client.call_llm(
        prompt=f"Answer this prompt: {query}",
        system_instruction=BASELINE_PROMPT,
        model_type="fast",
        temperature=0.7
    )
    
    return grounded_answer, raw_unverified
