import pytest
from unittest.mock import patch, MagicMock
import httpx
from backend.ai_service import check_gemma_status, generate_gemma_plan
from backend.config import settings

@pytest.mark.asyncio
async def test_check_gemma_status_demo():
    original = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "demo"
        status = await check_gemma_status()
        assert status["available"] is True
        assert status["provider"] == "demo"
        assert status["model_available"] is True
    finally:
        settings.AI_PROVIDER = original

@pytest.mark.asyncio
async def test_check_gemma_status_ollama_offline():
    original = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "ollama"
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
            status = await check_gemma_status()
            assert status["available"] is False
            assert status["model_available"] is False
            assert "Cannot connect to Ollama" in status["message"]
    finally:
        settings.AI_PROVIDER = original

@pytest.mark.asyncio
async def test_check_gemma_status_hosted_openai():
    original = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "openai_compatible"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            status = await check_gemma_status()
            assert status["available"] is True
            assert status["model_available"] is True
    finally:
        settings.AI_PROVIDER = original

@pytest.mark.asyncio
async def test_generate_gemma_plan_ollama_success():
    original_provider = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "ollama"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={
            "response": '{"tagline": "Cozy celebration", "overview": "A warm gathering"}',
            "prompt_eval_count": 120,
            "eval_count": 80,
            "eval_duration": 500000000
        })
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            success, parsed, tokens, err = await generate_gemma_plan("Plan a party")
            assert success is True
            assert parsed["tagline"] == "Cozy celebration"
            assert tokens["prompt_tokens"] == 120
            assert tokens["completion_tokens"] == 80
            assert err == ""
    finally:
        settings.AI_PROVIDER = original_provider

@pytest.mark.asyncio
async def test_generate_gemma_plan_hosted_openai_success():
    original_provider = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "openai_compatible"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={
            "choices": [{"message": {"content": '{"tagline": "Hosted Gemma plan", "overview": "Tested via OpenAI format"}'}}],
            "usage": {"total_tokens": 150}
        })
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            success, parsed, tokens, err = await generate_gemma_plan("Plan a party")
            assert success is True
            assert parsed["tagline"] == "Hosted Gemma plan"
            assert tokens["total_tokens"] == 150
            assert err == ""
    finally:
        settings.AI_PROVIDER = original_provider

@pytest.mark.asyncio
async def test_generate_gemma_plan_invalid_json():
    original_provider = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "ollama"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"response": "This is raw text without JSON brackets."})
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            success, parsed, tokens, err = await generate_gemma_plan("Plan a party")
            assert success is False
            assert "could not be parsed as JSON" in err
    finally:
        settings.AI_PROVIDER = original_provider

@pytest.mark.asyncio
async def test_generate_gemma_plan_timeout():
    original_provider = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "ollama"
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
            success, parsed, tokens, err = await generate_gemma_plan("Plan a party")
            assert success is False
            assert "timed out after" in err
    finally:
        settings.AI_PROVIDER = original_provider

@pytest.mark.asyncio
async def test_generate_gemma_plan_rate_limit_or_http_error():
    original_provider = settings.AI_PROVIDER
    try:
        settings.AI_PROVIDER = "openai_compatible"
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit reached. Quota exceeded."
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            success, parsed, tokens, err = await generate_gemma_plan("Plan a party")
            assert success is False
            assert "HTTP 429" in err
    finally:
        settings.AI_PROVIDER = original_provider
