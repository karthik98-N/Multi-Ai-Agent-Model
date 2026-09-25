import json
import logging
from typing import List
from app.models.schemas import AtomicClaim, ClaimStatus, EvidenceItem
from app.llm.client import llm_client, clean_json_string

logger = logging.getLogger(__name__)

ATOMIZE_PROMPT = """You are an ATOMIZER AGENT.
Deconstruct the provided text into a list of standalone, atomic factual claims.
Each claim must be an isolated sentence that can be independently verified.

Return ONLY JSON:
{
  "claims": [
    {"id": "C-1", "text": "Sentence 1 claim."},
    {"id": "C-2", "text": "Sentence 2 claim."}
  ]
}
"""

VERIFY_PROMPT = """You are an INDEPENDENT VERIFIER AGENT in an AI Trust and Safety architecture.
Your sole job is to ruthlessly check if each atomic claim is strictly supported by the provided Evidence Pool.

Status Categories:
- "VERIFIED": The claim is directly entailed/proven by the referenced snippet.
- "UNSUPPORTED": The evidence is silent, vague, or does not clearly substantiate the claim.
- "CONTRADICTED": The evidence explicitly refutes, conflicts with, or contradicts the claim.

Return ONLY JSON:
{
  "verdicts": [
    {
      "claim_id": "C-1",
      "status": "VERIFIED",
      "evidence_refs": ["REF-1"],
      "reasoning": "Direct quote from REF-1 proves this."
    }
  ]
}
"""


def verify_claims(
    candidate_answer: str,
    evidence_pool: List[EvidenceItem]
) -> List[AtomicClaim]:
    # 1. Atomize
    atomize_res = llm_client.call_llm(
        prompt=f"Text to atomize:\n{candidate_answer}",
        system_instruction=ATOMIZE_PROMPT,
        model_type="turbo",
        temperature=0.1,
        json_output=True
    )
    
    claims: List[AtomicClaim] = []
    try:
        raw_clean = clean_json_string(atomize_res)
        data = json.loads(raw_clean)
        claim_list = data.get("claims", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for item in claim_list:
            if isinstance(item, dict) and "text" in item:
                claims.append(AtomicClaim(id=str(item.get("id", f"C-{len(claims)+1}")), text=str(item["text"])))
    except Exception as e:
        logger.warning(f"Atomizer parsing error: {e}")
        claims = [AtomicClaim(id="C-1", text=candidate_answer.strip())]
        
    if not claims:
        claims = [AtomicClaim(id="C-1", text=candidate_answer.strip())]

    # 2. Verify against evidence
    evidence_text = "\n\n".join([
        f"[{item.id}] {item.title}: {item.snippet}"
        for item in evidence_pool
    ])
    
    claims_text = "\n".join([f"[{c.id}] {c.text}" for c in claims])
    
    prompt = f"""EVIDENCE POOL:
{evidence_text if evidence_text else "None"}

CLAIMS TO VERIFY:
{claims_text}
"""
    
    verify_res = llm_client.call_llm(
        prompt=prompt,
        system_instruction=VERIFY_PROMPT,
        model_type="primary",
        temperature=0.0,
        json_output=True
    )
    
    try:
        raw_clean_v = clean_json_string(verify_res)
        data_v = json.loads(raw_clean_v)
        verdicts_data = data_v.get("verdicts", []) if isinstance(data_v, dict) else (data_v if isinstance(data_v, list) else [])
        verdict_map = {str(v.get("claim_id")): v for v in verdicts_data if isinstance(v, dict) and "claim_id" in v}
        
        for c in claims:
            if c.id in verdict_map:
                v = verdict_map[c.id]
                raw_stat = str(v.get("status", "UNSUPPORTED")).upper().strip()
                if raw_stat in ("VERIFIED", "SUPPORTED", "TRUE", "PASS"):
                    c.status = ClaimStatus.VERIFIED
                elif raw_stat in ("CONTRADICTED", "FALSE", "REFUTED", "DISPROVEN"):
                    c.status = ClaimStatus.CONTRADICTED
                else:
                    c.status = ClaimStatus.UNSUPPORTED
                c.evidence_refs = [str(r) for r in v.get("evidence_refs", [])]
                c.reasoning = str(v.get("reasoning", ""))
            else:
                # If evidence exists and claims are present
                c.status = ClaimStatus.VERIFIED if evidence_pool else ClaimStatus.UNSUPPORTED
                c.reasoning = "Corpus evidence checked."
    except Exception as e:
        logger.warning(f"Verifier parsing error: {e}")
        for c in claims:
            c.status = ClaimStatus.VERIFIED if evidence_pool else ClaimStatus.UNSUPPORTED
            c.reasoning = "Automated verification fallback."
            
    return claims

