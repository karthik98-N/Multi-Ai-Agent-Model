import os
import sys
import json
import time

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.models.schemas import VerificationRequest
from app.engine.orchestrator import engine


def run_benchmark():
    dataset_path = os.path.join(os.path.dirname(__file__), "benchmark_queries.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("================================================================================")
    print(" HackFusion 2026: Multi-Agent AI Verification Platform - Benchmark Evaluator")
    print("================================================================================\n")

    summary_results = []

    for i, c in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] Testing Category: {c['category']}")
        print(f"Query: \"{c['query']}\"")
        print(f"Expected Outcome: {c['expected_decision']}")

        t0 = time.time()
        req = VerificationRequest(query=c["query"], context=c.get("context", ""), force_search=True)
        res = engine.run_pipeline(req)
        elapsed = round(time.time() - t0, 2)

        status_passed = False
        decision_str = str(res.decision.value if hasattr(res.decision, 'value') else res.decision)
        if "REJECT" in c["expected_decision"]:
            status_passed = (decision_str == "REJECT") or any(
                phrase in res.final_answer.lower()
                for phrase in ["no such", "not exist", "does not exist", "false premise", "never built", "impossible", "fictional"]
            )
        elif "ACCEPT" in c["expected_decision"]:
            status_passed = (decision_str == "ACCEPT") and (res.confidence_score >= c.get("minimum_confidence", 60.0))
        else:
            status_passed = res.confidence_score >= c.get("minimum_confidence", 60.0)

        print(f"  -> Decision: {decision_str} | Confidence: {res.confidence_score}% | Time: {elapsed}s")
        print(f"  -> Iterations: {res.iteration_count} | Claims Audited: {len(res.claims_matrix)}")
        print(f"  -> Status: {'[PASS]' if status_passed else '[FLAGGED]'}\n")

        summary_results.append({
            "id": c["id"],
            "category": c["category"],
            "decision": res.decision,
            "confidence": res.confidence_score,
            "passed": status_passed,
            "elapsed_s": elapsed
        })

    print("================================================================================")
    print(" EVALUATION SUMMARY")
    print("================================================================================")
    passed_count = sum(1 for s in summary_results if s["passed"])
    print(f"Total Scenarios: {len(summary_results)} | Passed: {passed_count}/{len(summary_results)}")
    for s in summary_results:
        print(f"- {s['category']}: Decision={s['decision']} (Score: {s['confidence']}%, Time: {s['elapsed_s']}s)")
    print("================================================================================")


if __name__ == "__main__":
    run_benchmark()
