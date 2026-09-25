@echo off
echo ==============================================================================
echo  Starting HackFusion 2026: Multi-Agent AI Verification Platform (Local Mode)
echo ==============================================================================

cd backend
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo [2/3] Starting Multi-Agent AI Verification Engine on http://localhost:8000 ...
start cmd /k "venv\Scripts\uvicorn app.main:app --reload --port 8000"

cd ..\frontend
echo [3/3] Starting Observability Dashboard on http://localhost:5173 ...
npm run dev

pause
