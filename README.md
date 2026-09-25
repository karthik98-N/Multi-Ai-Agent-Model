# HackFusion 2026: Multi-Agent AI Verification Platform

> **"Our system does not blindly trust an AI answer. It plans, searches, generates, independently audits, red-team attacks, self-corrects, and only accepts when empirical evidence proves the claims."**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React Vite](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)](https://vitejs.dev)
[![Cost](https://img.shields.io/badge/API%20Cost-100%25%20Free-brightgreen.svg)](#100-free-tier-stack)
[![Hugging Face Spaces](https://img.shields.io/badge/Deploy-Hugging%20Face%20Spaces-yellow.svg)](#cloud-deployment-hugging-face-spaces)

---

## 1. Problem Statement & Solution

Standard LLMs suffer from blind trust vulnerabilities:
* Fabricating non-existent or deprecated APIs
* Hallucinating dates, statistics, and citations
* Jumping to conclusions when evidence is missing or ambiguous
* Falling for false premise trick questions

Our platform solves this with a **Multi-Agent Verification Pipeline** where generation is strictly decoupled from auditing and adversarial red-teaming.

```
USER TASK
   │
   ▼
[1. PLANNER AGENT] ─── Deconstructs task into verifiable claims & search queries
   │
   ▼
[2. RESEARCH AGENT] ── Gathers empirical evidence via DuckDuckGo & Vector Store
   │
   ▼
[3. GENERATOR AGENT] ─ Formulates candidate answer citing [REF-X] evidence tags
   │
   ▼
┌─────────────────────────────── INDEPENDENT AUDIT LAYER ───────────────────────────────┐
│                                                                                       │
│  [4. INDEPENDENT VERIFIER]       [5. CONTRADICTION CHECKER]    [6. RED-TEAM CRITIC]   │
│  Sentence-by-sentence check      Cross-source & logic checks   Adversarial attacks    │
│  (VERIFIED / UNSUPPORTED)        (Discrepancies / Paradoxes)   (Edge cases & leaks)   │
│                                                                                       │
└──────────────────────────────────────────┬────────────────────────────────────────────┘
                                           │
                                           ▼
                                 [7. DECISION ENGINE]
                                  Accept / Revise / Reject
                                           │
                     ┌─────────────────────┼─────────────────────┐
                     │                     │                     │
                     ▼                     ▼                     ▼
                 [ACCEPT]              [REVISE]              [REJECT]
          Grounding Verified        Errors detected       Unresolvable conflict
                     │                     │                     │
                     │           [8. CORRECTION AGENT]           ▼
                     │            Applies targeted fix   Explicit Refusal Notice
                     │                     │
                     │           [9. RE-VERIFICATION]
                     │                     │
                     ▼                     ▼
          [10. FINAL RESULT & GLASSBOX AUDIT REPORT]
```

---

## 2. 100% Free-Tier Stack

The entire system is engineered to run at **zero API cost**:

* **Primary Fast LLM**: **Groq Cloud API** (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) — free tier with sub-second latency.
* **Adversarial Red-Team Critic**: **Google Gemini 2.0 Flash** — free tier (15 requests/min).
* **Live Web Research**: **DuckDuckGo Search (`ddgs`)** — 100% free, requires zero signup or API keys.
* **Orchestrator Backend**: **FastAPI + Python 3.11**.
* **Observability UI**: **React + Vite** with rich dark-mode glassmorphism and real-time agent audit visualizer.
* **Cloud Hosting**: **Hugging Face Spaces** (Free Basic CPU: 2 vCPU, 16 GB RAM).

---

## 3. Local Setup & Execution (Native Windows — No Docker Required)

### Prerequisites
* Python 3.11+
* Node.js v20+

### Option A: One-Click Startup (Windows)
Double-click `run_local.bat` in the root folder, or run:
```powershell
.\run_local.bat
```

### Option B: Manual Terminal Execution

#### 1. Start Backend:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# (Optional) Add your free keys to backend/.env:
# GROQ_API_KEY=gsk_...
# GEMINI_API_KEY=...

uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`.

#### 2. Start Frontend:
In a separate terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 4. Cloud Deployment (Hugging Face Spaces)

Hugging Face Spaces builds and runs the container automatically for free:

1. Create a new Space on [huggingface.co/new-space](https://huggingface.co/new-space):
   * Space Name: `hackfusion-ai-verifier`
   * SDK: **Docker**
   * Hardware: **CPU Basic (Free - 16GB RAM)**
2. In Space **Settings $\rightarrow$ Variables and Secrets**:
   * Add `GROQ_API_KEY`: *(your free Groq key)*
   * Add `GEMINI_API_KEY`: *(your free Gemini key)*
3. Push to Hugging Face:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<your-space-name>
   git push space main
   ```
Your app will be live at `https://huggingface.co/spaces/<your-username>/<your-space-name>` on default port `7860`.

---

## 5. HackFusion Benchmark Evaluation Suite

Run the automated evaluation suite:
```powershell
.\backend\venv\Scripts\python eval/run_eval.py
```

| Benchmark Category | Prompt Tested | System Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Deprecated / Non-Existent API** | `initialize_agent` with `AgentType.ZERO_SHOT_REACT` in LangChain | Verifier & Critic detect deprecation $\rightarrow$ self-corrects | **PASS** |
| **Conflicting Sources** | Voyager 1 distance & heliopause boundary | Detects source discrepancies and cites nuances | **PASS** |
| **Ambiguous / Incomplete Query** | Zero-downtime UUID database migration | Planner flags missing database engine qualification | **PASS** |
| **Misleading / Factual Trap** | London-NYC suspension bridge in 1950 | Red-team critic catches false premise $\rightarrow$ issues refusal | **PASS** |

---

## 6. Key Features for Jury Presentation

1. **Live Multi-Agent Stepper**: Watch each agent (Planner, Research, Verifier, Critic) execute in sequence.
2. **Glassbox Claim Matrix**: Table showing each atomic sentence, matched evidence citations, and green/amber/red status badges.
3. **Side-by-Side Comparison**: Contrast the raw, unverified LLM output (with hallucinations) directly against the multi-agent verified result.
4. **Adversarial Red-Team Log**: View the hostile critic's objections and how the Correction Agent surgically resolved them.
