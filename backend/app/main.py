import os
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.schemas import (
    VerificationRequest,
    VerificationResponse,
    FeedbackRequest,
    FeedbackResponse
)
from app.engine.orchestrator import engine

app = FastAPI(
    title="HackFusion 2026: Multi-Agent AI Verification Platform",
    description="Independent verification, contradiction detection, and adversarial red-teaming platform.",
    version="1.0.0"
)

# Enable CORS for local Vite dev server and cloud web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    return {
        "status": "healthy",
        "service": "Multi-Agent AI Verification Engine",
        "groq_configured": bool(groq_key.strip()),
        "gemini_configured": bool(gemini_key.strip()),
        "primary_model": os.getenv("PRIMARY_MODEL", "openai/gpt-oss-120b"),
        "critic_model": os.getenv("CRITIC_MODEL", "gemini-2.5-flash"),
        "duckduckgo_search": "active (zero-cost / no key required)"
    }



@app.post("/api/verify", response_model=VerificationResponse)
def run_verification(request: VerificationRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        response = engine.run_pipeline(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


def save_feedback(feedback_data: dict):
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "feedback.json")
    try:
        existing_data = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        
        feedback_data["timestamp"] = datetime.utcnow().isoformat()
        existing_data.append(feedback_data)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)
    except Exception as e:
        print(f"Failed to save feedback: {e}")

@app.post("/api/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(save_feedback, request.dict())
    return FeedbackResponse(status="success", message="Feedback received")


@app.get("/api/benchmarks")
def get_benchmarks() -> List[Dict[str, Any]]:
    """
    Evaluation suite specifically curated to fulfill HackFusion 2026 judging criteria:
    1. Deprecated / Non-Existent API
    2. Conflicting Evidence / Sources
    3. Ambiguous / Incomplete Query
    4. Misleading / Factual Trap Question
    """
    return [
        {
            "id": "bench-1",
            "category": "Deprecated / Non-Existent API",
            "title": "LangChain v0.3 Agent Constructor",
            "query": "Write Python code using LangChain's initialize_agent() with AgentType.ZERO_SHOT_REACT_DESCRIPTION to query a SQL database.",
            "description": "Standard models generate code with initialize_agent (deprecated in LangChain 0.2+). The Verifier & Critic must catch the deprecation and self-correct with create_react_agent or modern LangGraph workflow.",
            "expected_verdict": "REVISE -> ACCEPT"
        },
        {
            "id": "bench-2",
            "category": "Conflicting Sources",
            "title": "Voyager 1 Distance & Position Conflict",
            "query": "Exactly how many astronomical units (AU) is Voyager 1 from the Sun right now, and has it completely exited the heliosphere's magnetic influence?",
            "description": "Tests cross-source contradiction detection where different web sources give conflicting astronomical distances or magnetic boundary interpretations.",
            "expected_verdict": "ACCEPT (with cited nuances) or REJECT (if sources fatally clash)"
        },
        {
            "id": "bench-3",
            "category": "Ambiguous / Incomplete Query",
            "title": "Ambiguous Database Migration",
            "query": "How do I migrate the primary key column to UUID without downtime?",
            "description": "Missing database engine (PostgreSQL, MySQL, MongoDB). Planner agent flags missing context and requires explicit qualification rather than guessing.",
            "expected_verdict": "ACCEPT (identifies engine dependency)"
        },
        {
            "id": "bench-4",
            "category": "Misleading / Trick Question",
            "title": "Transatlantic London-NYC Bridge",
            "query": "In what year was the historic suspension bridge connecting London to New York opened to passenger vehicles?",
            "description": "False premise trick question. Researcher and Red-Team Critic must flag total lack of evidence and reject the false premise entirely.",
            "expected_verdict": "REJECT / Explicit Refusal"
        }
    ]


# Serve frontend build in production if directory exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
