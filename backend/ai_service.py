"""
AI Inference Client for EventPilot AI.
Supports configurable open-weight Gemma models via:
1. Ollama local endpoint (:11434)
2. OpenAI-compatible hosted endpoints (e.g., Groq, Together, OpenRouter, or vLLM running Gemma)
3. Clearly-labeled Demo Mode for offline UI testing without fake AI claims
"""

import json
import logging
import httpx
from typing import Dict, Any, Tuple, Optional
from backend.config import settings
from backend.observability import AISpanContext

logger = logging.getLogger("eventpilot.ai_service")

async def check_gemma_status() -> Dict[str, Any]:
    """Check connectivity to the configured Gemma inference endpoint."""
    provider = settings.AI_PROVIDER.lower()
    model = settings.GEMMA_MODEL
    base_url = settings.INFERENCE_BASE_URL.rstrip("/")

    if provider == "demo":
        return {
            "available": True,
            "provider": "demo",
            "model_configured": "Rule-based Demo Generator",
            "model_available": True,
            "is_gemma": False,
            "message": "Demo mode active. Generating deterministic sample plans without external AI inference."
        }

    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    model_present = any(
                        model in m or m.startswith(model.split(":")[0])
                        for m in models
                    )
                    return {
                        "available": True,
                        "provider": "ollama",
                        "model_configured": model,
                        "model_available": model_present,
                        "available_models": models,
                        "is_gemma": "gemma" in model.lower(),
                        "base_url": base_url,
                        "message": (
                            f"Ollama is online and '{model}' is installed."
                            if model_present
                            else f"Ollama is running, but '{model}' is not in installed models. Run `ollama pull {model}`."
                        )
                    }
                return {
                    "available": False,
                    "provider": "ollama",
                    "model_configured": model,
                    "model_available": False,
                    "available_models": [],
                    "is_gemma": "gemma" in model.lower(),
                    "base_url": base_url,
                    "message": f"Ollama returned HTTP {resp.status_code}."
                }
        except Exception as e:
            return {
                "available": False,
                "provider": "ollama",
                "model_configured": model,
                "model_available": False,
                "available_models": [],
                "is_gemma": "gemma" in model.lower(),
                "base_url": base_url,
                "message": f"Cannot connect to Ollama at {base_url}. Verify it is running or switch to a hosted endpoint."
            }

    # OpenAI-compatible hosted provider (e.g. for Render or hosted Gemma)
    if provider in ["openai_compatible", "openai"]:
        headers = {}
        if settings.INFERENCE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.INFERENCE_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{base_url}/models", headers=headers)
                if resp.status_code in [200, 401, 403]:  # Endpoint exists
                    return {
                        "available": True,
                        "provider": "openai_compatible",
                        "model_configured": model,
                        "model_available": resp.status_code == 200,
                        "is_gemma": "gemma" in model.lower(),
                        "base_url": base_url,
                        "message": f"Hosted inference endpoint reached (HTTP {resp.status_code})."
                    }
                return {
                    "available": False,
                    "provider": "openai_compatible",
                    "model_configured": model,
                    "model_available": False,
                    "base_url": base_url,
                    "message": f"Inference endpoint returned HTTP {resp.status_code}."
                }
        except Exception as e:
            return {
                "available": False,
                "provider": "openai_compatible",
                "model_configured": model,
                "model_available": False,
                "base_url": base_url,
                "message": f"Could not connect to {base_url}: {str(e)}"
            }

    return {
        "available": False,
        "provider": provider,
        "model_configured": model,
        "model_available": False,
        "message": f"Unknown AI provider '{provider}'."
    }

async def generate_gemma_plan(prompt: str) -> Tuple[bool, Dict[str, Any], Optional[Dict[str, Any]], str]:
    """
    Invokes the configured Gemma model.
    Returns:
      (success: bool, parsed_data: dict, token_usage: Optional[dict], error_message: str)
    """
    provider = settings.AI_PROVIDER.lower()
    base_url = settings.INFERENCE_BASE_URL.rstrip("/")
    model = settings.GEMMA_MODEL
    timeout = settings.INFERENCE_TIMEOUT_SECONDS

    with AISpanContext(
        op="event_plan.model_inference",
        description=f"Inference via {provider} ({model})",
        data={"ai.model": model, "ai.provider": provider, "ai.prompt_chars": len(prompt)}
    ):
        if provider == "ollama":
            url = f"{base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 1536
                }
            }
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        return False, {}, None, f"Ollama HTTP {resp.status_code}: {resp.text[:200]}"
                    data = resp.json()
                    raw_text = data.get("response", "").strip()
                    
                    # Token usage from Ollama if present
                    token_usage = None
                    if "prompt_eval_count" in data or "eval_count" in data:
                        token_usage = {
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            "eval_duration_ms": round(data.get("eval_duration", 0) / 1e6, 2)
                        }

                    # Parse JSON
                    parsed = json.loads(raw_text)
                    return True, parsed, token_usage, ""
            except json.JSONDecodeError as jde:
                return False, {}, None, f"Gemma output could not be parsed as JSON: {jde}"
            except httpx.ConnectError:
                return False, {}, None, f"Could not connect to Ollama at {base_url}"
            except httpx.TimeoutException:
                return False, {}, None, f"Inference timed out after {timeout}s on {model}"
            except Exception as e:
                return False, {}, None, f"Ollama error: {str(e)}"

        elif provider in ["openai_compatible", "openai"]:
            url = f"{base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if settings.INFERENCE_API_KEY:
                headers["Authorization"] = f"Bearer {settings.INFERENCE_API_KEY}"
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are EventPilot AI. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        return False, {}, None, f"Inference API HTTP {resp.status_code}: {resp.text[:200]}"
                    
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        return False, {}, None, "No choices returned from inference provider"
                    
                    content = choices[0].get("message", {}).get("content", "").strip()
                    token_usage = data.get("usage", None)
                    parsed = json.loads(content)
                    return True, parsed, token_usage, ""
            except json.JSONDecodeError as jde:
                return False, {}, None, f"Hosted Gemma response could not be parsed as JSON: {jde}"
            except Exception as e:
                return False, {}, None, f"Hosted inference error: {str(e)}"

        else:
            return False, {}, None, f"Provider '{provider}' does not support live inference."
