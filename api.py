import anthropic
import requests
from config import ANTHROPIC_API_KEY, OPENROUTER_API_KEY

_anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def call_claude(model: str, system_prompt: str, messages: list) -> str:
    """Make a single API call to Anthropic directly."""

    # Anthropic requires at least one user message; bootstrap if none exist yet
    effective_messages = messages if messages else [{"role": "user", "content": "Please begin."}]

    response = _anthropic_client.messages.create(
        model=model,
        system=system_prompt,
        messages=effective_messages,
        temperature=1.0,
        max_tokens=500,
    )
    return response.content[0].text


def call_openrouter(model: str, system_prompt: str, messages: list) -> str:
    """Make a single API call via OpenRouter."""

    # Anthropic requires at least one user message; bootstrap if none exist yet
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
        "max_tokens": 500,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
    )

    if not response.ok:
        print(f"API error {response.status_code}: {response.text}")
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
