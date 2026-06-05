"""
LLM Client for BhoomiSetu.

Supports three providers via env vars:
  - LLM_PROVIDER="gemini"      → uses GEMINI_API_KEY
  - LLM_PROVIDER="azure_openai" → uses AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT
  - LLM_PROVIDER="anthropic"    → uses ANTHROPIC_API_KEY

Exposes a single function:
    generate(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str
"""

import os
import json
import httpx
from typing import Optional

# ───────────────────────────────
# ENV VAR LOADING
# ───────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Default model names / versions
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


# ───────────────────────────────
# PROVIDER-SPECIFIC CALLERS
# ───────────────────────────────

async def _call_gemini(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """Call Google Gemini API."""
    if not GEMINI_API_KEY:
        return "[ERROR] GEMINI_API_KEY not set in environment"

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
        f":generateContent?key={GEMINI_API_KEY}"
    )

    # Gemini uses "parts" array; system instruction goes in systemInstruction field
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 8192,
        }
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract text from candidates
            candidates = data.get("candidates", [])
            if not candidates:
                return "[ERROR] Gemini returned no candidates"

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return "[ERROR] Gemini candidate has no text parts"

            return parts[0].get("text", "[ERROR] Empty text from Gemini")

        except httpx.HTTPStatusError as e:
            err_body = e.response.text[:500]
            return f"[ERROR] Gemini HTTP {e.response.status_code}: {err_body}"
        except httpx.RequestError as e:
            return f"[ERROR] Gemini request failed: {str(e)}"
        except Exception as e:
            return f"[ERROR] Gemini unexpected error: {str(e)}"


async def _call_azure_openai(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """Call Azure OpenAI Chat Completions API."""
    if not AZURE_OPENAI_API_KEY:
        return "[ERROR] AZURE_OPENAI_API_KEY not set in environment"
    if not AZURE_OPENAI_ENDPOINT:
        return "[ERROR] AZURE_OPENAI_ENDPOINT not set in environment"
    if not AZURE_OPENAI_DEPLOYMENT:
        return "[ERROR] AZURE_OPENAI_DEPLOYMENT not set in environment"

    url = (
        f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}"
        f"/chat/completions?api-version=2024-02-01"
    )

    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if not choices:
                return "[ERROR] Azure OpenAI returned no choices"

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if not content:
                return "[ERROR] Empty content from Azure OpenAI"

            return content

        except httpx.HTTPStatusError as e:
            err_body = e.response.text[:500]
            return f"[ERROR] Azure OpenAI HTTP {e.response.status_code}: {err_body}"
        except httpx.RequestError as e:
            return f"[ERROR] Azure OpenAI request failed: {str(e)}"
        except Exception as e:
            return f"[ERROR] Azure OpenAI unexpected error: {str(e)}"


async def _call_anthropic(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """Call Anthropic Claude Messages API."""
    if not ANTHROPIC_API_KEY:
        return "[ERROR] ANTHROPIC_API_KEY not set in environment"

    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            content_blocks = data.get("content", [])
            if not content_blocks:
                return "[ERROR] Anthropic returned no content blocks"

            # Claude returns a list of content blocks; text is in type="text" blocks
            text_parts = [
                block["text"] for block in content_blocks
                if block.get("type") == "text"
            ]
            if not text_parts:
                return "[ERROR] No text content in Anthropic response"

            return "\n".join(text_parts)

        except httpx.HTTPStatusError as e:
            err_body = e.response.text[:500]
            return f"[ERROR] Anthropic HTTP {e.response.status_code}: {err_body}"
        except httpx.RequestError as e:
            return f"[ERROR] Anthropic request failed: {str(e)}"
        except Exception as e:
            return f"[ERROR] Anthropic unexpected error: {str(e)}"


# ───────────────────────────────
# MAIN PUBLIC FUNCTION
# ───────────────────────────────

async def generate(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """
    Generate text from the configured LLM provider.

    Args:
        system_prompt: The system / role instruction.
        user_prompt: The user query / task.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).

    Returns:
        The LLM response text, or an "[ERROR] ..." string on failure.
    """
    if LLM_PROVIDER == "gemini":
        return await _call_gemini(system_prompt, user_prompt, temperature)
    elif LLM_PROVIDER == "azure_openai":
        return await _call_azure_openai(system_prompt, user_prompt, temperature)
    elif LLM_PROVIDER == "anthropic":
        return await _call_anthropic(system_prompt, user_prompt, temperature)
    else:
        return (
            f"[ERROR] Unknown LLM_PROVIDER \"{LLM_PROVIDER}\". "
            f"Expected: gemini | azure_openai | anthropic"
        )


# ───────────────────────────────
# SYNC WRAPPER (for non-async contexts)
# ───────────────────────────────

def generate_sync(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Synchronous wrapper around generate()."""
    import asyncio
    return asyncio.run(generate(system_prompt, user_prompt, temperature))
