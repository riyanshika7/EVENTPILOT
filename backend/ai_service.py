import httpx
import json
import logging
from typing import Dict, Any, Tuple
from backend.config import settings

logger = logging.getLogger(__name__)

async def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama is running and whether the configured model is available."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_present = any(
                    settings.OLLAMA_MODEL in m or m.startswith(settings.OLLAMA_MODEL.split(":")[0])
                    for m in models
                )
                return {
                    "available": True,
                    "model_available": model_present,
                    "configured_model": settings.OLLAMA_MODEL,
                    "available_models": models,
                    "base_url": settings.OLLAMA_BASE_URL,
                    "message": "Ollama service is reachable and ready." if model_present else f"Ollama is reachable, but '{settings.OLLAMA_MODEL}' was not found in installed models."
                }
            return {
                "available": False,
                "model_available": False,
                "configured_model": settings.OLLAMA_MODEL,
                "available_models": [],
                "base_url": settings.OLLAMA_BASE_URL,
                "message": f"Ollama responded with status code {resp.status_code}"
            }
    except Exception as e:
        logger.warning(f"Ollama connection check failed: {e}")
        return {
            "available": False,
            "model_available": False,
            "configured_model": settings.OLLAMA_MODEL,
            "available_models": [],
            "base_url": settings.OLLAMA_BASE_URL,
            "message": f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. Ensure Ollama is running (`ollama serve`)."
        }

async def generate_raw_event_plan(prompt: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Call Ollama /api/generate with JSON format enforcement.
    Returns: (success: bool, parsed_data: dict, error_message: str)
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 2048
        }
    }

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                return False, {}, f"Ollama returned HTTP error {response.status_code}: {response.text}"
            
            result = response.json()
            raw_text = result.get("response", "").strip()
            if not raw_text:
                return False, {}, "Ollama returned an empty response."

            try:
                parsed = json.loads(raw_text)
                return True, parsed, ""
            except json.JSONDecodeError as jde:
                logger.error(f"Failed to decode Ollama JSON output: {jde}. Raw: {raw_text[:200]}")
                return False, {}, f"Model did not return valid JSON: {jde}"
    except httpx.ConnectError:
        return False, {}, f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}. Is Ollama running?"
    except httpx.TimeoutException:
        return False, {}, f"Ollama generation timed out after {settings.OLLAMA_TIMEOUT_SECONDS}s. Try a lighter model or increase timeout."
    except Exception as e:
        return False, {}, f"Unexpected AI service error: {str(e)}"
