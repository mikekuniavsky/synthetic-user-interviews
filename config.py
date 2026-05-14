import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env.local")

# --- Mode ---
USE_OPENROUTER = True  # Set to True to use multi-model OpenRouter mode
RANDOMIZE_PERSONA_MODEL = True    # Pick a random persona model per interview
RANDOMIZE_RESEARCHER_MODEL = True  # Pick a random researcher model per turn

# --- API keys (set in .env.local) ---
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- OpenAI-compatible endpoints (local or hosted) ---
# Each entry covers one endpoint. Add models to whichever endpoint serves them.
# api_key: None means no Authorization header (e.g. Ollama running locally).
# Examples:
#   Ollama:                base_url="http://localhost:11434/v1",       api_key=None
#   HF Inference Endpoint: base_url="https://xyz.hf.space/v1",        api_key="hf_..."
#   LM Studio:             base_url="http://localhost:1234/v1",        api_key=None
#   vLLM:                  base_url="http://localhost:8000/v1",        api_key="token-..."
OPENAI_COMPAT_ENDPOINTS: list[dict] = [
    {
        "base_url": "http://localhost:11434/v1",
        "api_key": None,
        "models": [
            "gemma4:e4b",
            # "llama3.2",
            # "gemma3:12b",
        ],
    },
]

# --- Basic mode (Anthropic SDK, single model) ---
ANTHROPIC_MODEL = "claude-opus-4-6"

# --- Multi-model mode (OpenRouter) ---
# Persona model is picked randomly per interview from this list
PERSONA_MODELS = [
    "google/gemma-4-31b-it:free",
    "arcee-ai/trinity-large-preview:free",
 #   "anthropic/claude-opus-4.6-fast",
    "anthropic/claude-opus-4.7",
    "openai/gpt-5.1-chat",
    "google/gemini-3-flash-preview",
    "openrouter/elephant-alpha",
    "deepseek/deepseek-v3.2",
    "microsoft/phi-4",
    "mistralai/mistral-small-2603",
]

# Researcher model is picked randomly per turn from this list
RESEARCHER_MODELS = [
    "gemma4:e4b", # Available via Ollama
    "minimax/minimax-m2.5:free",
    "google/gemma-4-31b-it:free",
#    "anthropic/claude-opus-4.6-fast",
    "openai/gpt-5.1-chat",
]

SUMMARY_MODEL = "anthropic/claude-opus-4.6-fast"

# --- Shared settings ---
OUTPUT_DIR = Path("transcripts")
NUM_TURNS = 12
MAX_TOKENS_TURN = 1500    # per interview turn (persona/researcher)
MAX_TOKENS_SUMMARY = 8192  # summary report
REQUEST_TIMEOUT = 60       # seconds before a hanging model call is abandoned and retried
