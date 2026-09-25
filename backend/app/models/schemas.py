from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class DecisionVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"


class ObjectionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceItem(BaseModel):
    id: str = Field(description="Unique reference tag e.g. REF-1")
    title: str = Field(description="Title of source document or webpage")
    url: Optional[str] = Field(default=None, description="Web URL if retrieved online")
    snippet: str = Field(description="Extracted verbatim snippet or evidence summary")
    source_type: str = Field(default="web", description="web | document | knowledge_base")


class AtomicClaim(BaseModel):
    id: str = Field(description="Claim identifier e.g. C-1")
    text: str = Field(description="Single factual sentence or assertion")
    status: ClaimStatus = Field(default=ClaimStatus.UNSUPPORTED)
    evidence_refs: List[str] = Field(default_factory=list, description="IDs of matching evidence")
    reasoning: str = Field(default="", description="Justification for verdict")


class CriticObjection(BaseModel):
    id: str = Field(description="Objection identifier e.g. OBJ-1")
    severity: ObjectionSeverity = Field(default=ObjectionSeverity.MEDIUM)
    issue: str = Field(description="Flaw, ungrounded assumption, or edge case detected")
    target: str = Field(description="Specific sentence, API, or calculation challenged")
    recommendation: str = Field(description="Concrete direction for Correction Agent")


class ContradictionItem(BaseModel):
    id: str = Field(description="Contradiction ID")
    claim_a: str = Field(description="First claim or premise")
    claim_b: str = Field(description="Conflicting claim or source evidence")
    conflict_type: str = Field(description="Cross-source conflict | Internal logic paradox | Temporal mismatch")
    explanation: str


class PlanTask(BaseModel):
    id: str
    goal: str
    focus_areas: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    verification_criteria: List[str] = Field(default_factory=list)


class RevisionRecord(BaseModel):
    iteration: int
    draft_answer: str
    feedback_applied: List[str]
    diff_summary: str


class AgentStepTrace(BaseModel):
    step: int
    agent: str
    status: str = "completed"
    duration_ms: Optional[int] = None
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)


class VerificationRequest(BaseModel):
    query: str
    context: Optional[str] = None
    force_search: bool = True
    enable_red_team: bool = True


class VerificationResponse(BaseModel):
    query: str
    decision: DecisionVerdict
    confidence_score: float = Field(description="0-100 composite confidence metric")
    confidence_label: str = Field(default="MEDIUM", description="HIGH | MEDIUM | LOW | INSUFFICIENT")
    confidence_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Sub-score breakdown")
    final_answer: str
    verified_answer: Optional[str] = Field(default=None, description="Verified Multi-Agent Answer before final synthesis")
    raw_unverified_answer: Optional[str] = Field(default=None, description="Baseline unverified output for side-by-side comparison")
    iteration_count: int
    plan: Optional[PlanTask] = None
    evidence_pool: List[EvidenceItem] = Field(default_factory=list)
    claims_matrix: List[AtomicClaim] = Field(default_factory=list)
    critic_objections: List[CriticObjection] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    revisions: List[RevisionRecord] = Field(default_factory=list)
    steps_trace: List[AgentStepTrace] = Field(default_factory=list)
    refusal_reason: Optional[str] = None
    # Resilience fields
    guard_risk_level: str = Field(default="NONE", description="NONE | LOW | MEDIUM | HIGH | CRITICAL")
    guard_signals: List[str] = Field(default_factory=list, description="Detected adversarial/misleading signals")
    ambiguity_fraction: float = Field(default=0.0, description="Fraction of claims that are ambiguous (0-1)")
    ambiguity_summary: str = Field(default="", description="Human-readable ambiguity assessment")
    is_ambiguous: bool = Field(default=False)
    verdict_lines: List[str] = Field(default_factory=list, description="Plain-text summary lines for the Final Verdict panel")

class FeedbackRequest(BaseModel):
    query: str
    raw_answer: Optional[str] = None
    verified_answer: str
    feedback_type: int = Field(description="1 for positive, -1 for negative")
    feedback_tags: List[str] = Field(default_factory=list)
    user_correction: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    message: str
