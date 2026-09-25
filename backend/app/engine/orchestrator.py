import os
import time
import logging
from typing import List, Optional
from app.models.schemas import (
    VerificationRequest,
    VerificationResponse,
    DecisionVerdict,
    ClaimStatus,
    ObjectionSeverity,
    AgentStepTrace,
    RevisionRecord,
    AtomicClaim,
    CriticObjection,
    ContradictionItem,
)
from app.agents.planner import plan_task
from app.agents.researcher import gather_evidence
from app.agents.generator import generate_candidate_answer
from app.agents.verifier import verify_claims
from app.agents.contradiction import check_contradictions
from app.agents.critic import critique_answer
from app.agents.corrector import correct_answer
from app.agents.synthesizer import synthesize_final_output
from app.agents.guard import inspect_query, GuardReport
from app.engine.resilience import (
    score_confidence,
    detect_ambiguity,
    build_epistemic_hedge,
    source_credibility,
    strip_references,
)

logger = logging.getLogger(__name__)

MAX_LOOPS = int(os.getenv("MAX_VERIFICATION_LOOPS", "3"))




def generate_verdict_lines(
    query: str,
    decision: str,
    confidence_score: float,
    confidence_label: str,
    claims_matrix,
    contradictions,
    critic_objections,
    iterations: int,
    ambiguity_summary: str,
    guard_signals,
) -> list:
    """
    Build a flat list of short, plain-text verdict lines that summarise
    what every agent found. No markdown, no JSON — just readable sentences.
    """
    lines = []

    # 1. Overall verdict
    verdict_map = {
        "ACCEPT": "Verdict: ACCEPTED — the answer passed all verification checks.",
        "REJECT": "Verdict: REJECTED — the answer could not be verified reliably.",
        "REVISE": "Verdict: CONDITIONALLY ACCEPTED — passed after corrections.",
    }
    lines.append(verdict_map.get(str(decision), f"Verdict: {decision}"))

    # 2. Confidence
    lines.append(
        f"Overall confidence: {confidence_score:.1f}% ({confidence_label}) "
        f"after {iterations} verification cycle(s)."
    )

    # 3. Guard signals
    if guard_signals:
        lines.append(
            f"Input warning: {len(guard_signals)} adversarial signal(s) detected "
            f"({guard_signals[0][:60]}{'...' if len(guard_signals[0]) > 60 else ''})."
        )
    else:
        lines.append("Input check: No adversarial or misleading signals found in the query.")

    # 4. Claims breakdown
    if claims_matrix:
        verified    = sum(1 for c in claims_matrix if c.status.value == "VERIFIED")
        unsupported = sum(1 for c in claims_matrix if c.status.value == "UNSUPPORTED")
        contradicted= sum(1 for c in claims_matrix if c.status.value == "CONTRADICTED")
        total = len(claims_matrix)
        lines.append(
            f"Claims checked: {total} atomic fact(s) — "
            f"{verified} verified, {unsupported} unsupported, {contradicted} contradicted."
        )
        # Top verified
        for c in [x for x in claims_matrix if x.status.value == "VERIFIED"][:2]:
            lines.append(f"  Confirmed: {c.text[:100]}{'...' if len(c.text) > 100 else ''}")
        # Top failed
        for c in [x for x in claims_matrix if x.status.value in ("CONTRADICTED", "UNSUPPORTED")][:2]:
            tag = "Contradicted" if c.status.value == "CONTRADICTED" else "Unverifiable"
            lines.append(f"  {tag}: {c.text[:100]}{'...' if len(c.text) > 100 else ''}")
    else:
        lines.append("Claims check: No individual claims were extracted for this query.")

    # 5. Contradictions
    if contradictions:
        lines.append(
            f"Source conflicts: {len(contradictions)} contradiction(s) found across evidence sources."
        )
        for con in contradictions[:2]:
            lines.append(f"  Conflict: {con.explanation[:100]}{'...' if len(con.explanation) > 100 else ''}")
    else:
        lines.append("Source conflicts: No contradictions detected across evidence sources.")

    # 6. Critic objections
    if critic_objections:
        critical_count = sum(1 for o in critic_objections if o.severity.value in ("CRITICAL", "HIGH"))
        lines.append(
            f"Red-Team Critic: {len(critic_objections)} objection(s) raised "
            f"({critical_count} critical/high severity)."
        )
        for obj in [o for o in critic_objections if o.severity.value in ("CRITICAL", "HIGH")][:2]:
            lines.append(f"  Issue: {obj.issue[:100]}{'...' if len(obj.issue) > 100 else ''}")
    else:
        lines.append("Red-Team Critic: No objections — answer passed adversarial review.")

    # 7. Ambiguity
    if ambiguity_summary:
        lines.append(f"Ambiguity: {ambiguity_summary}")

    return lines

class VerificationEngine:
    def __init__(self, max_iterations: Optional[int] = None):
        self.max_iterations = max_iterations or MAX_LOOPS

    def run_pipeline(self, request: VerificationRequest) -> VerificationResponse:
        steps_trace: List[AgentStepTrace] = []
        revisions: List[RevisionRecord] = []
        step_counter = 1

        # =================================================================
        # STEP 0: GUARD — adversarial / misleading input detection
        # =================================================================
        t0 = time.time()
        guard_report: GuardReport = inspect_query(request.query)
        steps_trace.append(AgentStepTrace(
            step=step_counter,
            agent="Guard Agent",
            duration_ms=int((time.time() - t0) * 1000),
            summary=(
                f"Input risk: {guard_report.risk_level}. "
                f"{len(guard_report.signals)} signal(s) detected."
                + (f" Signals: {'; '.join(guard_report.signals)}" if guard_report.signals else "")
            ),
            data={
                "risk_level": guard_report.risk_level,
                "signals": guard_report.signals,
                "query_sanitised": guard_report.is_blocked,
            }
        ))
        step_counter += 1

        # If CRITICAL risk — refuse immediately
        if guard_report.risk_level == "CRITICAL":
            refusal = (
                "SECURITY BLOCK: This query was identified as a prompt-injection or "
                "adversarial manipulation attempt and has been refused by the Guard Agent. "
                f"Signals: {'; '.join(guard_report.signals)}"
            )
            return VerificationResponse(
                query=request.query,
                decision=DecisionVerdict.REJECT,
                confidence_score=0.0,
                confidence_label="INSUFFICIENT",
                final_answer=f"🔴 **BLOCKED BY GUARD AGENT**\n\n{refusal}",
                iteration_count=0,
                steps_trace=steps_trace,
                guard_risk_level=guard_report.risk_level,
                guard_signals=guard_report.signals,
            )

        # Use sanitised query downstream when HIGH risk
        effective_query = (
            guard_report.sanitised_query
            if guard_report.risk_level in ("HIGH",)
            else request.query
        )

        # =================================================================
        # STEP 1: PLANNER AGENT
        # =================================================================
        t0 = time.time()
        plan = plan_task(effective_query, request.context or "")
        steps_trace.append(AgentStepTrace(
            step=step_counter,
            agent="Planner Agent",
            duration_ms=int((time.time() - t0) * 1000),
            summary=f"Plan generated: {len(plan.focus_areas)} focus areas, {len(plan.search_queries)} search queries.",
            data={"plan": plan.model_dump()}
        ))
        step_counter += 1

        # =================================================================
        # STEP 2: RESEARCH / EVIDENCE AGENT
        # =================================================================
        t0 = time.time()
        evidence_pool = gather_evidence(plan)

        # Score source credibility upfront so orchestrator can use it
        src_scores = source_credibility(evidence_pool)
        low_trust = [s.ref_id for s in src_scores.values() if s.credibility < 0.4]

        steps_trace.append(AgentStepTrace(
            step=step_counter,
            agent="Research Agent",
            duration_ms=int((time.time() - t0) * 1000),
            summary=(
                f"Retrieved {len(evidence_pool)} evidence references. "
                f"Avg credibility: {sum(s.credibility for s in src_scores.values()) / max(len(src_scores), 1):.2f}. "
                + (f"Low-trust sources: {low_trust}." if low_trust else "All sources within trust threshold.")
            ),
            data={
                "evidence_count": len(evidence_pool),
                "evidence": [e.model_dump() for e in evidence_pool],
                "source_credibility": {k: {"credibility": v.credibility, "flags": v.flags} for k, v in src_scores.items()},
            }
        ))
        step_counter += 1

        # Handle zero evidence — incomplete information scenario
        if not evidence_pool:
            logger.warning("No evidence retrieved — entering low-confidence path")

        # =================================================================
        # STEP 3: GENERATOR AGENT
        # =================================================================
        t0 = time.time()
        current_draft, raw_unverified = generate_candidate_answer(effective_query, evidence_pool, plan)
        steps_trace.append(AgentStepTrace(
            step=step_counter,
            agent="Generator Agent",
            duration_ms=int((time.time() - t0) * 1000),
            summary="Candidate answer formulated citing evidence pool with baseline unverified comparison.",
            data={"draft": current_draft, "raw_unverified": raw_unverified}
        ))
        step_counter += 1

        # =================================================================
        # VERIFICATION & SELF-CORRECTION LOOP
        # =================================================================
        iteration = 1
        decision = DecisionVerdict.REVISE
        claims_matrix: List[AtomicClaim] = []
        critic_objections: List[CriticObjection] = []
        contradictions: List[ContradictionItem] = []
        confidence_score = 0.0
        confidence_label = "LOW"
        confidence_breakdown = {}
        refusal_reason: Optional[str] = None

        while iteration <= self.max_iterations:

            # ── Step 4: Independent Verifier ────────────────────────────
            t0 = time.time()
            claims_matrix = verify_claims(current_draft, evidence_pool)
            verified_count = sum(1 for c in claims_matrix if c.status == ClaimStatus.VERIFIED)
            steps_trace.append(AgentStepTrace(
                step=step_counter,
                agent="Independent Verifier",
                duration_ms=int((time.time() - t0) * 1000),
                summary=f"Iteration {iteration}: {verified_count}/{len(claims_matrix)} claims verified against evidence.",
                data={"claims": [c.model_dump() for c in claims_matrix]}
            ))
            step_counter += 1

            # ── Step 5: Contradiction Checker ────────────────────────────
            t0 = time.time()
            contradictions = check_contradictions(claims_matrix, evidence_pool)
            steps_trace.append(AgentStepTrace(
                step=step_counter,
                agent="Contradiction Checker",
                duration_ms=int((time.time() - t0) * 1000),
                summary=f"Iteration {iteration}: Identified {len(contradictions)} internal/source contradictions.",
                data={"contradictions": [c.model_dump() for c in contradictions]}
            ))
            step_counter += 1

            # ── Step 6: Adversarial Red-Team Critic ─────────────────────
            t0 = time.time()
            critic_objections = []
            if request.enable_red_team:
                critic_objections = critique_answer(effective_query, current_draft, evidence_pool)
            steps_trace.append(AgentStepTrace(
                step=step_counter,
                agent="Red-Team Critic",
                duration_ms=int((time.time() - t0) * 1000),
                summary=f"Iteration {iteration}: Raised {len(critic_objections)} adversarial objections.",
                data={"objections": [o.model_dump() for o in critic_objections]}
            ))
            step_counter += 1

            # ── Step 7: Decision Engine with resilience scoring ──────────
            breakdown = score_confidence(claims_matrix, contradictions, critic_objections, evidence_pool)
            ambiguity  = detect_ambiguity(claims_matrix, contradictions)

            confidence_score   = breakdown.overall
            confidence_label   = breakdown.label
            confidence_breakdown = {
                "factual":     breakdown.factual_score,
                "source":      breakdown.source_score,
                "consistency": breakdown.consistency_score,
                "critic":      breakdown.critic_score,
                "label":       breakdown.label,
                "explanation": breakdown.explanation,
            }

            failed_claims       = [c for c in claims_matrix if c.status in (ClaimStatus.UNSUPPORTED, ClaimStatus.CONTRADICTED)]
            critical_objections = [o for o in critic_objections if o.severity in (ObjectionSeverity.CRITICAL, ObjectionSeverity.HIGH)]
            has_fatal_contradiction = (
                any(c.status == ClaimStatus.CONTRADICTED for c in claims_matrix)
                or len(contradictions) > 0
            )

            decision_summary = (
                f"Confidence {confidence_score:.1f}% [{confidence_label}] | "
                f"Ambiguity: {ambiguity.ambiguous_fraction:.0%} | "
                f"Contradictions: {len(contradictions)} | "
                f"Critic flags: {len(critic_objections)}"
            )

            # Acceptance gate
            can_accept = (
                not has_fatal_contradiction
                and not critical_objections
                and len(failed_claims) == 0
                and confidence_score >= 70.0
                and not ambiguity.is_ambiguous
            )

            if can_accept:
                decision = DecisionVerdict.ACCEPT
                steps_trace.append(AgentStepTrace(
                    step=step_counter,
                    agent="Decision Engine",
                    summary=f"VERDICT: ACCEPT. {decision_summary}",
                    data={"decision": "ACCEPT", "iteration": iteration, "breakdown": confidence_breakdown}
                ))
                step_counter += 1
                break

            # Max iterations reached
            if iteration >= self.max_iterations:
                if confidence_score < 40.0 or has_fatal_contradiction:
                    decision = DecisionVerdict.REJECT
                    refusal_reason = (
                        f"Rejected after {iteration} iteration(s). "
                        f"{decision_summary}. "
                        "Unresolved contradictions or critically insufficient evidence prevent a reliable answer."
                    )
                elif ambiguity.is_ambiguous:
                    # Ambiguous but not outright wrong — accept with heavy hedging
                    decision = DecisionVerdict.ACCEPT
                    refusal_reason = (
                        f"Accepted with caveats after {iteration} iteration(s). "
                        f"{ambiguity.summary}"
                    )
                else:
                    decision = DecisionVerdict.ACCEPT

                steps_trace.append(AgentStepTrace(
                    step=step_counter,
                    agent="Decision Engine",
                    summary=f"VERDICT: {decision} (max iterations). {decision_summary}",
                    data={"decision": str(decision), "reason": refusal_reason, "breakdown": confidence_breakdown}
                ))
                step_counter += 1
                break

            # Needs revision
            decision = DecisionVerdict.REVISE
            t0 = time.time()
            corrected_draft, diff_summary = correct_answer(
                query=effective_query,
                current_draft=current_draft,
                failed_claims=failed_claims,
                objections=critic_objections,
                evidence_pool=evidence_pool,
            )

            revisions.append(RevisionRecord(
                iteration=iteration,
                draft_answer=current_draft,
                feedback_applied=[f"Claims: {len(failed_claims)} failed", f"Critic: {len(critic_objections)} issues"],
                diff_summary=diff_summary,
            ))
            steps_trace.append(AgentStepTrace(
                step=step_counter,
                agent="Correction Agent",
                duration_ms=int((time.time() - t0) * 1000),
                summary=f"Iteration {iteration} repair: {diff_summary}",
                data={"corrected_draft": corrected_draft, "diff_summary": diff_summary}
            ))
            step_counter += 1

            current_draft = corrected_draft
            iteration += 1

        # =================================================================
        # STEP 6: FINAL SYNTHESIZER AGENT
        # =================================================================
        verified_answer_clean = strip_references(current_draft)

        if decision == DecisionVerdict.REJECT:
            final_answer = (
                "Verification Rejection Notice:\n\n"
                "The Multi-Agent AI Verification Platform cannot guarantee the integrity of this answer.\n\n"
                f"Reason: {refusal_reason}\n\n"
                "Identified Defects:\n"
                + "\n".join([f"- Contradiction: {c.explanation}" for c in contradictions])
                + "\n"
                + "\n".join([f"- Unresolved Critic Flag [{o.severity}]: {o.issue}" for o in critic_objections])
            )
        else:
            t0 = time.time()
            final_synthesized = synthesize_final_output(
                query=effective_query,
                verified_answer=verified_answer_clean,
                raw_unverified_answer=raw_unverified,
                claims_matrix=claims_matrix,
                contradictions=contradictions,
                critic_objections=critic_objections,
                evidence_pool=evidence_pool,
            )
            steps_trace.append(AgentStepTrace(
                step=step_counter,
                agent="Final Synthesizer Agent",
                duration_ms=int((time.time() - t0) * 1000),
                summary="Synthesized final verified output integrating verified answer and baseline context under safety rules.",
                data={
                    "primary_source": "Verified Multi-Agent Answer",
                    "secondary_source": "Raw Baseline AI Output",
                    "output_preview": final_synthesized[:160] + "..." if len(final_synthesized) > 160 else final_synthesized
                }
            ))
            step_counter += 1
            final_answer = final_synthesized

        # Wrap with epistemic hedge (uncertainty language + confidence badge)
        ambiguity_final = detect_ambiguity(claims_matrix, contradictions)
        breakdown_final = score_confidence(claims_matrix, contradictions, critic_objections, evidence_pool)
        final_answer = build_epistemic_hedge(
            answer=final_answer,
            breakdown=breakdown_final,
            ambiguity=ambiguity_final,
            guard_signals=guard_report.signals,
        )

        verdict_lines = generate_verdict_lines(
            query=request.query,
            decision=decision,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            claims_matrix=claims_matrix,
            contradictions=contradictions,
            critic_objections=critic_objections,
            iterations=iteration,
            ambiguity_summary=ambiguity_final.summary,
            guard_signals=guard_report.signals,
        )

        return VerificationResponse(
            query=request.query,
            decision=decision,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            confidence_breakdown=confidence_breakdown,
            final_answer=final_answer,
            verified_answer=verified_answer_clean,
            raw_unverified_answer=raw_unverified,
            iteration_count=iteration,
            plan=plan,
            evidence_pool=evidence_pool,
            claims_matrix=claims_matrix,
            critic_objections=critic_objections,
            contradictions=contradictions,
            revisions=revisions,
            steps_trace=steps_trace,
            refusal_reason=refusal_reason,
            guard_risk_level=guard_report.risk_level,
            guard_signals=guard_report.signals,
            ambiguity_fraction=ambiguity_final.ambiguous_fraction,
            ambiguity_summary=ambiguity_final.summary,
            is_ambiguous=ambiguity_final.is_ambiguous,
            verdict_lines=verdict_lines,
        )


engine = VerificationEngine()
