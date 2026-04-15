# Synthetic User Interviews

Runs AI-powered synthetic user research interviews. A researcher agent interviews a set of persona agents, then synthesizes findings across all interviews into a structured report.

Each persona represents a professional defined by their work context — where they work, what kind of work they do, and the constraints they operate under — without prescribing their tools or workflow. That's what the interview is for. The researcher follows a discussion guide and probes naturally. Neither agent can see the other's system prompt — they only see the conversation.

## How it works

1. For each persona, one researcher model and one persona model are chosen for the entire interview
2. The researcher's opening is randomized from a set of starting directions to vary interview trajectories
3. The loop runs for `NUM_TURNS` turns; on the second-to-last turn the researcher is cued to close with Topic 7 so the interview ends naturally on the persona's final answer
4. All transcripts are saved to `transcripts/` as JSON, including which model asked each question
5. After all interviews, a summary agent synthesizes findings into a research report

## Setup

### Install dependencies

With [uv](https://docs.astral.sh/uv/) (recommended):
```bash
uv sync
```

Or with pip:
```bash
pip install .
```

### Configure API keys

Copy the example env file and fill in your keys:
```bash
cp .env.local.example .env.local
```

Then edit `.env.local`:
```
ANTHROPIC_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here  # only needed for multi-model mode
```

Get an Anthropic API key at [console.anthropic.com](https://console.anthropic.com).
Get an OpenRouter API key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Usage

```bash
python orchestrator.py
```

Transcripts are saved to `transcripts/interview_<name>_<timestamp>.json`.
The summary report is saved to `transcripts/summary_<timestamp>.md`.

## Configuration

All settings are in `config.py`.

### Basic mode vs. multi-model mode

**Basic mode** uses the Anthropic SDK with a single Claude model for all roles — simpler, no OpenRouter account needed.

**Multi-model mode** uses OpenRouter (and optionally local models) to assign different models to different interviews, which reduces systematic bias in the synthetic responses.

```python
USE_OPENROUTER = True  # set to False to use basic mode (Anthropic SDK only)
```

In basic mode, `ANTHROPIC_MODEL` is used for every call and all randomization settings are ignored.

### Randomization (multi-model mode only)

One model is chosen per interview for each role — the persona model stays fixed for that interview, and so does the researcher model. This keeps each interview internally coherent and makes it possible to compare interview quality across models.

```python
RANDOMIZE_PERSONA_MODEL = True    # pick a random model per interview; False = always use PERSONA_MODELS[0]
RANDOMIZE_RESEARCHER_MODEL = True  # pick a random model per interview; False = always use RESEARCHER_MODELS[0]
```

### Changing models

```python
# Basic mode
ANTHROPIC_MODEL = "claude-opus-4-6"

# Multi-model mode — persona gets one random model per interview
PERSONA_MODELS = [
    "openai/gpt-4o",
    "google/gemini-3-flash-preview",
    "mistralai/mistral-small-2603",
    ...
]

# Researcher gets one random model per interview
RESEARCHER_MODELS = [
    "openai/gpt-4o",
    "google/gemma-4-31b-it:free",
]

# Model used to synthesize all transcripts into a final report
SUMMARY_MODEL = "anthropic/claude-opus-4.6-fast"
```

Free models (`:free` suffix) are available via OpenRouter but may be rate-limited or return null responses. The system automatically retries with a fallback model on 429, 404, or null content errors. To use your own provider API keys for higher rate limits, add them at [openrouter.ai/settings/integrations](https://openrouter.ai/settings/integrations).

### Local and hosted models (OpenAI-compatible endpoints)

In addition to OpenRouter, you can use any OpenAI-compatible endpoint — Ollama, HuggingFace Inference Endpoints, LM Studio, vLLM, etc. Add entries to `OPENAI_COMPAT_ENDPOINTS` in `config.py`, then include the model names in `PERSONA_MODELS` or `RESEARCHER_MODELS` as usual.

```python
OPENAI_COMPAT_ENDPOINTS = [
    # Ollama running locally
    {
        "base_url": "http://localhost:11434/v1",
        "api_key": None,
        "models": ["llama3.2", "gemma3:12b"],
    },
    # HuggingFace Inference Endpoint
    {
        "base_url": "https://xyz.endpoints.huggingface.cloud/v1",
        "api_key": "hf_...",
        "models": ["meta-llama/Llama-3-8B-Instruct"],
    },
]
```

Local and remote models can be mixed freely in `PERSONA_MODELS` and `RESEARCHER_MODELS`. If a model fails, the system falls back to any available model in the combined pool. A warning is printed when a fallback crosses provider boundaries (e.g. local → OpenRouter).

### Number of turns

```python
NUM_TURNS = 12  # researcher questions per interview
```

Each turn is one researcher question followed by one persona answer. The interview always ends on the persona's final answer.

## Customizing personas

Personas are defined in `personas.py`. Each is a dict with a name, discipline, and a system prompt. Personas should describe *where someone works and what kind of work they do* — not their tools, workflows, or frustrations. The interview exists to discover those things.

```python
{
    "name": "Alex",
    "discipline": "in_house_brand_designer",
    "prompt": """
You are Alex, a product designer on the in-house brand team at a large
retailer. Your team designs and sells its own line of home goods...
"""
}
```

## Customizing the interview

- **Discussion guide**: `interview_guide.py` — the topics and probes the researcher works through
- **Opening prompts**: also in `interview_guide.py` — randomly chosen to vary how each interview starts
- **Researcher system prompt**: `researcher_prompt.py`
- **Summary prompt**: `summary_prompt.py`

## Output

Each transcript is a JSON file:
```json
{
  "persona_name": "Jordan",
  "discipline": "product_designer",
  "persona_model": "openai/gpt-4o",
  "researcher_model": "google/gemini-3-flash-preview",
  "timestamp": "20260414_122416",
  "transcript": [
    {"role": "researcher", "model": "google/gemini-3-flash-preview", "content": "..."},
    {"role": "Jordan", "content": "..."},
    ...
  ]
}
```

`researcher_model` at the top level is the model chosen for the interview. The `model` field on each researcher turn reflects the model that actually responded — these will differ if a fallback was triggered mid-interview.

The summary report is a Markdown file structured as a qualitative research deliverable, including key findings, pain points, assumption validation, and recommended next steps.
