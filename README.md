# Synthetic User Interviews

Runs AI-powered synthetic user research interviews. A researcher agent interviews a set of persona agents, then synthesizes findings across all interviews into a structured report.

Each persona is a fictional professional with a detailed background, workflow, and set of frustrations. The researcher follows a discussion guide and probes naturally. Neither agent can see the other's system prompt — they only see the conversation.

## How it works

1. For each persona, a researcher LLM and a persona LLM alternate turns
2. The researcher's opening is randomized from a set of starting directions to vary interview trajectories
3. All transcripts are saved to `transcripts/` as JSON
4. After all interviews, a summary agent synthesizes findings into a research report

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

**Basic mode** (default) uses the Anthropic SDK with a single model for everything — simpler and more reliable.

**Multi-model mode** uses OpenRouter to rotate different models across personas and researcher turns, which reduces systematic bias in the synthetic responses.

```python
# config.py
USE_OPENROUTER = False  # flip to True for multi-model mode
```

### Changing models

```python
# Basic mode
ANTHROPIC_MODEL = "claude-opus-4-6"

# Multi-model mode — persona gets a random model per interview
PERSONA_MODELS = [
    "anthropic/claude-opus-4.6-fast",
    "openai/gpt-4o",
    ...
]

# Researcher gets a fresh random model each turn
RESEARCHER_MODELS = [
    "anthropic/claude-opus-4.6-fast",
    "openai/gpt-4o",
]
```

### Number of turns

```python
NUM_TURNS = 12  # back-and-forth exchanges per interview
```

## Customizing personas

Personas are defined in `personas.py`. Each is a dict with a name, discipline, and a system prompt written in second person:

```python
{
    "name": "Alex",
    "discipline": "industrial_designer",
    "prompt": """
You are Alex, a 34-year-old industrial designer at a consumer electronics
company in Seattle...
"""
}
```

The more specific and contradictory the persona (opinions, pet peeves, habits), the more interesting the interview.

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
  "persona_model": "claude-opus-4-6",
  "timestamp": "20260413_164252",
  "transcript": [
    {"role": "researcher", "content": "..."},
    {"role": "Jordan", "content": "..."},
    ...
  ]
}
```

The summary report is a Markdown file structured as a qualitative research deliverable, including key findings, pain points, assumption validation, and recommended next steps.
