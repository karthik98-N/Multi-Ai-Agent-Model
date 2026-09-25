import json
import logging
from app.models.schemas import PlanTask
from app.llm.client import llm_client, clean_json_string

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Lead PLANNER AGENT of a Multi-Agent AI Verification Platform.
Your mission is to rigorously deconstruct the user's task or query before any answer is generated.

You must identify:
1. The core objective of the user.
2. Specific factual assertions, APIs, dates, or numeric assertions that MUST be verified.
3. 2-3 precise web search queries to locate authoritative grounding evidence.
4. Concrete acceptance criteria (what must be true for this answer to be trusted).

Return ONLY valid JSON matching this schema:
{
  "id": "PLAN-1",
  "goal": "Concise summary of goal",
  "focus_areas": ["area 1", "area 2"],
  "search_queries": ["query 1", "query 2"],
  "verification_criteria": ["criterion 1", "criterion 2"]
}
"""


def plan_task(query: str, context: str = "") -> PlanTask:
    user_prompt = f"User Query:\n{query}\n"
    if context:
        user_prompt += f"Context:\n{context}\n"
        
    raw_output = llm_client.call_llm(
        prompt=user_prompt,
        system_instruction=SYSTEM_PROMPT,
        model_type="primary",
        temperature=0.1,
        json_output=True
    )
    
    try:
        data = json.loads(clean_json_string(raw_output))
        return PlanTask(
            id=data.get("id", "PLAN-1"),
            goal=data.get("goal", query),
            focus_areas=data.get("focus_areas", []),
            search_queries=data.get("search_queries", [query]),
            verification_criteria=data.get("verification_criteria", [])
        )
    except Exception as e:
        logger.warning(f"Planner JSON parsing fallback: {e}")
        return PlanTask(
            id="PLAN-1",
            goal=query,
            focus_areas=["Core facts", "Source grounding"],
            search_queries=[query],
            verification_criteria=["Factual claims must match evidence"]
        )
