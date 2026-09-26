import os
import re
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier definitions (overridden by .env)
# ---------------------------------------------------------------------------
#   turbo   allam-2-7b           ~129 ms  claim atomisation, contradiction
#   fast    qwen/qwen3.8-27b     ~148 ms  verification, planning passes
#   primary openai/gpt-oss-20b   ~440 ms  generation, correction (quality)
#   critic  gemini-3.8-flash     cross-vendor adversarial critique (Gemini)
# ---------------------------------------------------------------------------

_DEFAULTS: Dict[str, str] = {
    "TURBO_MODEL":   "llama3-8b-8192",
    "FAST_MODEL":    "llama-3.3-70b-versatile",
    "PRIMARY_MODEL": "llama-3.3-70b-versatile",
    "CRITIC_MODEL":  "gemini-2.5-flash",
}

# Max tokens per tier — keeps latency predictable
_TIER_MAX_TOKENS: Dict[str, int] = {
    "turbo":   512,
    "fast":    1024,
    "primary": 4096,
    "critic":  4096,
}

# Groq models that do NOT support response_format=json_object
# Models that do NOT support response_format=json_object on Groq
_NO_JSON_MODE: set = {"llama3-8b-8192"}


def clean_json_string(raw: str) -> str:
    """Extract the first JSON object/array from a possibly markdown-wrapped string."""
    if not raw:
        return "{}"
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if match:
        raw = match.group(1).strip()
    start_obj, end_obj = raw.find("{"), raw.rfind("}")
    start_arr, end_arr = raw.find("["), raw.rfind("]")
    if start_obj != -1 and end_obj > start_obj:
        if start_arr != -1 and start_arr < start_obj and end_arr > end_obj:
            return raw[start_arr:end_arr + 1]
        return raw[start_obj:end_obj + 1]
    if start_arr != -1 and end_arr > start_arr:
        return raw[start_arr:end_arr + 1]
    return raw


class LLMClient:
    """
    Unified 4-tier LLM client.

    Usage::

        llm_client.call_llm(prompt, model_type="fast")

    Model tiers
    -----------
    turbo   Fastest structural tasks: claim atomisation, contradiction detection.
    fast    Quick reasoning: verification passes, search-query generation.
    primary Quality generation and correction.
    critic  Cross-vendor adversarial critique via Google Gemini Flash.
    """

    def __init__(self) -> None:
        self.groq_client = None
        self.gemini_client = None
        self.available_groq_models: List[str] = []
        self._resolved: Dict[str, str] = {}
        self._groq_key_cache = ""
        self._gemini_key_cache = ""
        self._ensure_clients()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _ensure_clients(self) -> None:
        """(Re)initialise API clients and resolve model tiers from .env."""
        load_dotenv(override=True)
        groq_key   = os.getenv("GROQ_API_KEY",   "").strip()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

        if groq_key and groq_key != self._groq_key_cache:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_key)
                self._groq_key_cache = groq_key
                try:
                    self.available_groq_models = [
                        m.id for m in self.groq_client.models.list().data
                    ]
                    logger.info("Groq: %d models available", len(self.available_groq_models))
                except Exception as exc:
                    logger.warning("Could not list Groq models: %s", exc)
                self._resolve_model_tiers()
            except Exception as exc:
                logger.error("Failed to initialise Groq client: %s", exc)

        if gemini_key and gemini_key != self._gemini_key_cache:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_key)
                self._gemini_key_cache = gemini_key
                logger.info("Gemini client ready.")
            except Exception as exc:
                logger.error("Failed to initialise Gemini client: %s", exc)

    def _resolve_model_tiers(self) -> None:
        """Map each tier to a concrete Groq model id, falling back gracefully."""
        available = set(self.available_groq_models)

        def pick(env_key: str) -> str:
            wanted = os.getenv(env_key, _DEFAULTS[env_key]).strip()
            if wanted in available:
                return wanted
            chat = [m for m in self.available_groq_models
                    if any(k in m for k in ("gpt", "llama", "qwen", "allam"))]
            fallback = (
                chat[0] if chat
                else (self.available_groq_models[0] if self.available_groq_models else wanted)
            )
            logger.warning(
                "[tier] %s preferred '%s' unavailable -> using '%s'",
                env_key, wanted, fallback,
            )
            return fallback

        self._resolved = {
            "turbo":   pick("TURBO_MODEL"),
            "fast":    pick("FAST_MODEL"),
            "primary": pick("PRIMARY_MODEL"),
            "critic":  pick("FAST_MODEL"),   # Groq fallback for critic tier
        }
        logger.info(
            "Model tiers resolved  turbo:%s  fast:%s  primary:%s  critic-fb:%s",
            self._resolved["turbo"], self._resolved["fast"],
            self._resolved["primary"], self._resolved["critic"],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call_llm(
        self,
        prompt: str,
        system_instruction: str = "You are a specialized AI agent.",
        model_type: str = "primary",
        temperature: float = 0.2,
        json_output: bool = False,
    ) -> str:
        """
        Route a completion to the appropriate model tier.

        Parameters
        ----------
        prompt:             The user / task prompt.
        system_instruction: System-level context.
        model_type:         One of turbo | fast | primary | critic.
        temperature:        Sampling temperature 0-1.
        json_output:        Whether to request structured JSON output.
        """
        self._ensure_clients()

        # 1. Critic -> Gemini first (cross-vendor adversarial diversity)
        if model_type == "critic":
            result = self._call_gemini(prompt, system_instruction, json_output)
            if result:
                return result
            # fall through to Groq critic-fallback

        # 2. All tiers -> Groq with per-tier model selection
        if self.groq_client and self._resolved:
            model_id   = self._resolved.get(model_type) or self._resolved.get("primary", "")
            max_tokens = _TIER_MAX_TOKENS.get(model_type, 2048)
            result = self._call_groq(
                prompt, system_instruction, model_id, temperature, json_output, max_tokens
            )
            if result:
                return result

        # 3. General Gemini fallback for all tiers
        result = self._call_gemini(prompt, system_instruction, json_output)
        if result:
            return result

        # 4. Offline mock (no keys / network failure)
        logger.info("All providers unavailable - returning mock response.")
        return self._generate_mock_response(prompt, system_instruction, json_output)

    # ------------------------------------------------------------------
    # Provider helpers
    # ------------------------------------------------------------------

    def _call_groq(
        self,
        prompt: str,
        system_instruction: str,
        model_id: str,
        temperature: float,
        json_output: bool,
        max_tokens: int = 2048,
    ) -> Optional[str]:
        """Single Groq call with JSON-mode guard and one plain-text retry."""
        sys_prompt = system_instruction
        if json_output and "json" not in sys_prompt.lower():
            sys_prompt += " Provide your output in valid JSON format only."

        use_json_mode = json_output and model_id not in _NO_JSON_MODE

        kwargs: Dict[str, Any] = {
            "model":       model_id,
            "messages":    [
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            completion = self.groq_client.chat.completions.create(**kwargs)
            out = completion.choices[0].message.content or ""
            if out:
                logger.debug(
                    "[groq] model=%s tokens=%s",
                    model_id, getattr(completion.usage, "total_tokens", "?"),
                )
                return out
        except Exception as exc:
            logger.warning("[groq] call failed (model=%s): %s", model_id, exc)
            if use_json_mode:
                # Retry without JSON mode constraint
                try:
                    kwargs.pop("response_format", None)
                    kwargs["messages"] = [
                        {
                            "role": "system",
                            "content": system_instruction + "\nRespond with valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ]
                    completion = self.groq_client.chat.completions.create(**kwargs)
                    out = completion.choices[0].message.content or ""
                    if out:
                        return out
                except Exception as retry_exc:
                    logger.warning("[groq] plain-text retry failed: %s", retry_exc)
        return None

    def _call_gemini(
        self,
        prompt: str,
        system_instruction: str,
        json_output: bool,
    ) -> Optional[str]:
        """Single Gemini call — used for critic tier and general fallback."""
        if not self.gemini_client:
            return None

        model = os.getenv("CRITIC_MODEL", _DEFAULTS["CRITIC_MODEL"]).strip()
        if "gemini" not in model:
            model = "gemini-2.5-flash"

        full_prompt = f"{system_instruction}\n\nTask:\n{prompt}"
        if json_output:
            full_prompt += (
                "\n\nCRITICAL: Respond with strict valid JSON only. "
                "No markdown fences or commentary outside the JSON."
            )

        try:
            response = self.gemini_client.models.generate_content(
                model=model,
                contents=full_prompt,
            )
            if response and response.text:
                logger.debug("[gemini] model=%s responded ok", model)
                return response.text
        except Exception as exc:
            logger.warning("[gemini] call failed (model=%s): %s", model, exc)
        return None

    # ------------------------------------------------------------------
    # Offline mock
    # ------------------------------------------------------------------

    def _generate_mock_response(
        self, prompt: str, system_instruction: str, json_output: bool
    ) -> str:
        """
        Structurally valid stub responses so the pipeline can be exercised
        locally without any API keys.
        """
        lower = system_instruction.lower()
        if "synthesizer" in lower or "final" in lower:
            return "All factual claims have been verified successfully against empirical evidence with zero contradictions or unsupported statements."
        if "planner" in lower:
            return json.dumps({
                "id":   "PLAN-1",
                "goal": "Verify user prompt and test core claims",
                "focus_areas":           ["Factual accuracy", "Evidence validity", "Edge cases"],
                "search_queries":        ["ground truth evidence", "official documentation"],
                "verification_criteria": [
                    "All factual claims supported by verifiable sources",
                    "Zero unresolved contradictions",
                ],
            })
        if "atomizer" in lower or "extractor" in lower:
            return json.dumps({
                "claims": [{"id": "C-1", "text": "The primary claim is stated here for verification."}]
            })
        if "verifier" in lower:
            return json.dumps({
                "verdicts": [{
                    "claim_id":     "C-1",
                    "status":       "VERIFIED",
                    "evidence_refs": ["REF-1"],
                    "reasoning":    "Directly backed by retrieved reference evidence.",
                }]
            })
        if "contradiction & risk detector" in lower or "contradiction detector" in lower or ("contradiction" in lower and "detect" in lower):
            return json.dumps({"contradictions": []})
        if "critic" in lower:
            return json.dumps({"objections": []})
        if "corrector" in lower:
            return "This is the verified and refined response, grounded in empirical evidence."
        if "contradiction" in lower:
            return json.dumps({"contradictions": []})
        return "Based on the retrieved evidence, all claims have been verified successfully."


# Global singleton instance
llm_client = LLMClient()
