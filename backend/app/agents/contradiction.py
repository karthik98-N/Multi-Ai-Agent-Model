import json
import logging
from typing import List
from app.models.schemas import ContradictionItem, EvidenceItem, AtomicClaim
from app.llm.client import llm_client, clean_json_string

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the CONTRADICTION & RISK DETECTOR AGENT.
Your job is to detect:
1. Discrepancies between different sources in the evidence pool (e.g., conflicting statistics, opposite conclusions).
2. Internal contradictions within the generated claims.
3. Unsafe, broken, or logically impossible statements.

If no contradictions are found, return: {"contradictions": []}

Return ONLY JSON:
{
  "contradictions": [
    {
      "id": "CONTRA-1",
      "claim_a": "First contradictory statement or source premise",
      "claim_b": "Second statement or evidence that conflicts",
      "conflict_type": "Cross-source conflict | Internal logic paradox | Unsafe recommendation",
      "explanation": "Detailed rationale explaining the exact contradiction"
    }
  ]
}
"""


def check_contradictions(
    claims: List[AtomicClaim],
    evidence_pool: List[EvidenceItem]
) -> List[ContradictionItem]:
    claims_text = "\n".join([f"Claim {c.id}: {c.text}" for c in claims])
    evidence_text = "\n".join([f"[{e.id}] {e.title}: {e.snippet}" for e in evidence_pool])
    
    prompt = f"""CLAIMS:
{claims_text}

EVIDENCE SOURCES:
{evidence_text}

Inspect both the claims and evidence for mutual conflicts or paradoxes:"""

    raw_output = llm_client.call_llm(
        prompt=prompt,
        system_instruction=SYSTEM_PROMPT,
        model_type="turbo",
        temperature=0.1,
        json_output=True
    )
    
    contradictions: List[ContradictionItem] = []
    try:
        raw_clean = clean_json_string(raw_output)
        data = json.loads(raw_clean)
        items_list = data.get("contradictions", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for item in items_list:
            if not isinstance(item, dict):
                continue
            contradictions.append(ContradictionItem(
                id=str(item.get("id", f"CONTRA-{len(contradictions)+1}")),
                claim_a=str(item.get("claim_a", "")),
                claim_b=str(item.get("claim_b", "")),
                conflict_type=str(item.get("conflict_type", "Cross-source conflict")),
                explanation=str(item.get("explanation", ""))
            ))
    except Exception as e:
        logger.warning(f"Contradiction checker parsing error: {e}")
        
    return contradictions

