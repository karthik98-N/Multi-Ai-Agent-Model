import logging
from typing import List
from app.models.schemas import EvidenceItem, PlanTask
from app.tools.web_search import search_web_ddg

logger = logging.getLogger(__name__)


def gather_evidence(plan: PlanTask, max_results_per_query: int = 2) -> List[EvidenceItem]:
    """
    Executes search queries defined by Planner and gathers structured evidence.
    """
    evidence_pool: List[EvidenceItem] = []
    seen_urls = set()
    current_index = 1
    
    queries = plan.search_queries if plan.search_queries else [plan.goal]
    for q in queries[:3]:  # Top 3 queries to keep pipeline snappy
        items = search_web_ddg(q, max_results=max_results_per_query, start_ref_index=current_index)
        for item in items:
            if item.url and item.url in seen_urls:
                continue
            if item.url:
                seen_urls.add(item.url)
            evidence_pool.append(item)
            current_index += 1
            
    logger.info(f"Gathered {len(evidence_pool)} evidence items.")
    return evidence_pool
