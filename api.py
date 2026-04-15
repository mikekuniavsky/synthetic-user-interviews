import anthropic
import random
import time
import requests
from requests.exceptions import Timeout
from config import (
    ANTHROPIC_API_KEY,
    OPENROUTER_API_KEY,
    OPENAI_COMPAT_ENDPOINTS,
    PERSONA_MODELS,
    RESEARCHER_MODELS,
    MAX_TOKENS_TURN,
    REQUEST_TIMEOUT,
)

_anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Map from model name -> endpoint config, built from OPENAI_COMPAT_ENDPOINTS.
_COMPAT_MODEL_MAP: dict[str, dict] = {
    model: endpoint
    for endpoint in OPENAI_COMPAT_ENDPOINTS
    for model in endpoint["models"]
}

_ALL_MODELS = list(set(PERSONA_MODELS + RESEARCHER_MODELS + list(_COMPAT_MODEL_MAP)))


def _provider(model: str) -> str:
    if model in _COMPAT_MODEL_MAP:
        return _COMPAT_MODEL_MAP[model]["base_url"]
    return "openrouter"


def _pick_fallback(failed_model: str) -> str | None:
    alternatives = [m for m in _ALL_MODELS if m != failed_model]
    if not alternatives:
        return None
    fallback = random.choice(alternatives)
    if _provider(fallback) != _provider(failed_model):
        print(f"  WARNING: crossing provider boundary ({_provider(failed_model)} -> {_provider(fallback)})")
    return fallback


def _handle_openai_compat_response(
    response: requests.Response,
    model: str,
    system_prompt: str,
    messages: list,
    max_tokens: int,
) -> tuple[str, str]:
    """Extract content from an OpenAI-compatible response, falling back on null content."""
    choice = response.json()["choices"][0]
    content = choice["message"]["content"]
    if content is None:
        finish_reason = choice.get("finish_reason")
        print(f"Null content from {model} (finish_reason={finish_reason!r}, message={choice['message']})")
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Retrying with {fallback}")
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)
        raise ValueError(f"{model} returned null content and no fallback models are available")
    return content, model


def call_claude(model: str, system_prompt: str, messages: list, max_tokens: int = MAX_TOKENS_TURN) -> tuple[str, str]:
    """Make a single API call to Anthropic directly. Returns (content, model_used)."""

    effective_messages = messages if messages else [{"role": "user", "content": "Please begin."}]

    response = _anthropic_client.messages.create(
        model=model,
        system=system_prompt,
        messages=effective_messages,
        temperature=1.0,
        max_tokens=max_tokens,
    )
    return response.content[0].text, model


def call_openai_compat(
    base_url: str,
    api_key: str | None,
    model: str,
    system_prompt: str,
    messages: list,
    max_tokens: int = MAX_TOKENS_TURN,
) -> tuple[str, str]:
    """Call any OpenAI-compatible endpoint (Ollama, HF Inference Endpoints, LM Studio, vLLM, etc.).
    Returns (content, model_used)."""

    effective_messages = messages if messages else [{"role": "user", "content": "Please begin."}]

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *effective_messages,
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except Timeout:
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Timeout on {model} ({base_url}), retrying with {fallback}")
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)
        raise

    if not response.ok:
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Error {response.status_code} on {model} ({base_url}), retrying with {fallback}")
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)
        print(f"API error {response.status_code}: {response.text}")
        response.raise_for_status()

    return _handle_openai_compat_response(response, model, system_prompt, messages, max_tokens)


def call_openrouter(model: str, system_prompt: str, messages: list, max_tokens: int = MAX_TOKENS_TURN) -> tuple[str, str]:
    """Make a single API call via OpenRouter. Returns (content, model_used)."""

    effective_messages = messages if messages else [{"role": "user", "content": "Please begin."}]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-name.com",
        "X-Title": "Synthetic User Research",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *effective_messages,
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except Timeout:
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Timeout on {model}, retrying with {fallback}")
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)
        raise

    if response.status_code == 402:
        raise SystemExit("OpenRouter credits exhausted. Add more at https://openrouter.ai/settings/credits")

    if response.status_code == 429:
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Rate limited on {model}, waiting 5s then retrying with {fallback}")
            time.sleep(5)
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)

    if response.status_code == 404:
        fallback = _pick_fallback(model)
        if fallback:
            print(f"Error 404 on {model}, retrying with {fallback}")
            return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)

    if response.status_code == 400:
        error_msg = response.json().get("error", {}).get("message", "")
        if "context length" in error_msg or "context_length" in error_msg or "maximum context" in error_msg:
            fallback = _pick_fallback(model)
            if fallback:
                print(f"Context length exceeded on {model}, retrying with {fallback}")
                return call_any(fallback, system_prompt, messages, max_tokens=max_tokens)

    if not response.ok:
        print(f"API error {response.status_code}: {response.text}")
    response.raise_for_status()

    return _handle_openai_compat_response(response, model, system_prompt, messages, max_tokens)


def call_any(model: str, system_prompt: str, messages: list, max_tokens: int = MAX_TOKENS_TURN) -> tuple[str, str]:
    """Route a call to the right backend based on model name."""
    if model in _COMPAT_MODEL_MAP:
        endpoint = _COMPAT_MODEL_MAP[model]
        return call_openai_compat(
            base_url=endpoint["base_url"],
            api_key=endpoint["api_key"],
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
        )
    return call_openrouter(model, system_prompt, messages, max_tokens=max_tokens)
