import sys
import os

# Priority: put backend/ at head of sys.path, and avoid root app.py name collision
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(".") and p != ""]
sys.path.insert(0, backend_dir)

from app.main import app

# Mount Gradio if available (for Hugging Face Spaces health detection)
try:
    import gradio as gr
    with gr.Blocks(title="HackFusion Verification Engine") as demo:
        gr.Markdown("# 🛡️ HackFusion Multi-Agent AI Verification Platform")
        gr.Markdown(
            "The full interactive Glassbox Audit Dashboard is running live at **[/](/)]**.\n\n"
            "Interactive API Swagger documentation is at **[/docs](/docs)**."
        )
    app = gr.mount_gradio_app(app, demo, path="/gradio")
except ImportError:
    pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
