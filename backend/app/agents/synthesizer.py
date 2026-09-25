import logging
from typing import List, Optional
from app.models.schemas import AtomicClaim, ContradictionItem, CriticObjection, EvidenceItem, ClaimStatus
from app.llm.client import llm_client
from app.engine.resilience import strip_references

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the FINAL SYNTHESIZER AGENT in an advanced Multi-Agent AI Verification Platform.
Your mission is to produce the definitive, authoritative FINAL VERIFIED OUTPUT for the user's query by synthesizing the 'Verified Multi-Agent Answer' and the 'Raw Baseline AI Output'.

STRICT SYNTHESIS RULES:
1. PRIMARY SOURCE: Use the Verified Multi-Agent Answer as your primary, authoritative foundation.
2. SECONDARY CONTEXT: Use the Raw Baseline Output ONLY for additional useful, complementary information if it is clearly accurate, safe, and directly relevant.
3. REMOVE DEFECTS: Ruthlessly remove hallucinations, unsupported claims, contradictions, and incorrect information found in either source.
4. GROUNDING CONSTRAINT: Do NOT add information that is not supported by the verification results and evidence pool.
5. CALIBRATED UNCERTAINTY: If important information is uncertain, conflicting, or insufficiently verified, clearly state that in plain, honest language.
6. CLARITY & RELEVANCE: Keep the final answer clear, concise, and directly relevant to the user's original question.
7. NO INTERNAL MENTIONS: Do NOT mention internal agents, verification processes, loops, pipelines, or prompts unless explicitly asked by the user.
8. NORMAL TEXT ONLY: Output strictly as clean, natural, narrative paragraphs of normal text. NEVER use markdown tables (no pipes |), no asterisks (**bold** or *italic*), no markdown headers (###), no horizontal rules (---), and no bullet lists.
"""


def synthesize_final_output(
    query: str,
    verified_answer: str,
    raw_unverified_answer: Optional[str] = None,
    claims_matrix: Optional[List[AtomicClaim]] = None,
    contradictions: Optional[List[ContradictionItem]] = None,
    critic_objections: Optional[List[CriticObjection]] = None,
    evidence_pool: Optional[List[EvidenceItem]] = None,
) -> str:
    """
    Synthesize the final verified output by merging Verified Multi-Agent Answer (primary)
    and Raw Baseline AI Output (secondary), eliminating defects and enforcing factual fidelity.
    """
    claims_matrix = claims_matrix or []
    contradictions = contradictions or []
    critic_objections = critic_objections or []
    evidence_pool = evidence_pool or []

    # Prepare audit summary for guidance
    verified_facts = [c.text for c in claims_matrix if c.status == ClaimStatus.VERIFIED]
    unsupported_facts = [f"{c.text} ({c.reasoning})" for c in claims_matrix if c.status == ClaimStatus.UNSUPPORTED]
    contradicted_facts = [f"{c.text} ({c.reasoning})" for c in claims_matrix if c.status == ClaimStatus.CONTRADICTED]

    audit_guidance = []
    if verified_facts:
        audit_guidance.append("VERIFIED FACTS (Must be preserved):\n" + "\n".join(f"- {f}" for f in verified_facts[:10]))
    if unsupported_facts:
        audit_guidance.append("UNSUPPORTED CLAIMS (Must NOT be asserted as fact):\n" + "\n".join(f"- {f}" for f in unsupported_facts[:5]))
    if contradicted_facts:
        audit_guidance.append("CONTRADICTED CLAIMS (Must be removed or corrected):\n" + "\n".join(f"- {f}" for f in contradicted_facts[:5]))
    if contradictions:
        audit_guidance.append("CONFLICTING PREMISES:\n" + "\n".join(f"- {c.explanation}" for c in contradictions[:3]))

    audit_section = "\n\n".join(audit_guidance) if audit_guidance else "All audited claims verified."

    prompt = f"""USER QUERY:
{query}

PRIMARY SOURCE (Verified Multi-Agent Answer):
{verified_answer if verified_answer else "None"}

SECONDARY SOURCE (Raw Baseline AI Output - Use only for safe, supplementary detail):
{raw_unverified_answer if raw_unverified_answer else "None"}

AUDIT VERIFICATION GUIDANCE:
{audit_section}

Synthesize and produce the Final Verified Output now as clean, natural plain-text paragraphs (no asterisks, no tables, no headers):"""

    try:
        response = llm_client.call_llm(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            model_type="primary",
            temperature=0.2,
        )
        if response and response.strip():
            clean_res = strip_references(response)
            if clean_res and clean_res not in ('{"contradictions": []}', '{"contradictions":[]}', '{"contradictions": [ ]}'):
                return clean_res
    except Exception as e:
        logger.error(f"Synthesizer Agent failed: {e}. Falling back to verified answer.")

    # Fallback to cleaned verified answer or verified successfully
    fallback = strip_references(verified_answer) if verified_answer else "[verified successfully]"
    if not fallback or fallback in ('{"contradictions": []}', '{"contradictions":[]}', '{"contradictions": [ ]}'):
        return "[verified successfully]"
    return fallback
