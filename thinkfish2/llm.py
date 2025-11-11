from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

VOIDAI_API_URL = os.getenv("VOIDAI_API_URL", "https://api.voidai.app/v1/chat/completions")
VOIDAI_API_KEY = os.getenv("VOIDAI_API_KEY")
VOIDAI_MODEL = os.getenv("VOIDAI_MODEL", "kimi-k2-instruct")


def chat_completion(
    messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs: Any
) -> str:
    """
    Call VoidAI-compatible chat completions API and return assistant content.
    Requires VOIDAI_API_KEY in the environment. If missing, raises RuntimeError.
    """
    api_key = VOIDAI_API_KEY
    if not api_key:
        raise RuntimeError("VOIDAI_API_KEY is not set in environment")
    mdl = model or VOIDAI_MODEL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": mdl,
        "messages": messages,
    }
    payload.update(kwargs)
    resp = requests.post(VOIDAI_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # OpenAI-like response structure assumption
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Unexpected response from VoidAI: {data}") from e
