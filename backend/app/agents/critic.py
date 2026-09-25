import json
import logging
from typing import List
from app.models.schemas import CriticObjection, ObjectionSeverity, EvidenceItem
from app.llm.client import llm_client, clean_json_string

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the ADVERSARIAL RED-TEAM CRITIC AGENT.
Your mission is to aggressively challenge the candidate answer before it can be trusted.
Assume the role of a hostile, skeptical peer reviewer.

Specifically hunt for:
1. Deprecated, hallucinated, or non-existent API parameters, functions, or package versions.
2. Unstated assumptions, logical leaps, or hand-waving explanations.
3. Edge cases that cause the code/solution to fail.
4. Overconfidence where uncertainty or nuance should have been acknowledged.

If the answer is flawless and genuinely grounded, return: {"objections": []}

Return ONLY JSON:
{
  "objections": [
    {
      "id": "OBJ-1",
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "issue": "Specific vulnerability or error description",
      "target": "Exact sentence or code snippet challenged",
      "recommendation": "Prescriptive guidance for Correction Agent"
    }
  ]
}
"""


def critique_answer(
    query: str,
    candidate_answer: str,
    evidence_pool: List[EvidenceItem]
) -> List[CriticObjection]:
    evidence_snippets = "\n".join([f"[{e.id}] {e.snippet}" for e in evidence_pool[:5]])
    
    prompt = f"""USER QUERY:
{query}

CANDIDATE ANSWER TO CRITIQUE:
{candidate_answer}

EVIDENCE CONTEXT:
{evidence_snippets}

Attack this answer now. Find any technical defects, outdated APIs, or unsupported conclusions:"""

    raw_output = llm_client.call_llm(
        prompt=prompt,
        system_instruction=SYSTEM_PROMPT,
        model_type="critic",
        temperature=0.3,
        json_output=True
    )
    
    objections: List[CriticObjection] = []
    try:
        raw_clean = clean_json_string(raw_output)
        data = json.loads(raw_clean)
        obj_list = data.get("objections", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for item in obj_list:
            if not isinstance(item, dict):
                continue
            sev_str = str(item.get("severity", "MEDIUM")).upper().strip()
            if sev_str in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                sev = ObjectionSeverity(sev_str)
            elif "CRIT" in sev_str:
                sev = ObjectionSeverity.CRITICAL
            elif "HIGH" in sev_str:
                sev = ObjectionSeverity.HIGH
            else:
                sev = ObjectionSeverity.MEDIUM
                
            objections.append(CriticObjection(
                id=str(item.get("id", f"OBJ-{len(objections)+1}")),
                severity=sev,
                issue=str(item.get("issue", "")),
                target=str(item.get("target", "")),
                recommendation=str(item.get("recommendation", ""))
            ))
    except Exception as e:
        logger.warning(f"Critic parsing error: {e}")
        
    return objections

