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

# --- Basic mode (Anthropic SDK, single model) ---
ANTHROPIC_MODEL = "claude-opus-4-6"

# --- Multi-model mode (OpenRouter) ---
# Persona model is picked randomly per interview from this list
PERSONA_MODELS = [
    "google/gemma-4-31b-it:free",
    "arcee-ai/trinity-large-preview:free",
    "anthropic/claude-opus-4.6-fast",
    "openai/gpt-4o",
    "google/gemini-3-flash-preview",
    "mistralai/mistral-small-2603",
]

# Researcher model is picked randomly per turn from this list
RESEARCHER_MODELS = [
    "minimax/minimax-m2.5:free",
    "google/gemma-4-31b-it:free",
    "anthropic/claude-opus-4.6-fast",
    "openai/gpt-4o",
]

SUMMARY_MODEL = "anthropic/claude-opus-4.6-fast"

# --- Shared settings ---
OUTPUT_DIR = Path("transcripts")
NUM_TURNS = 12
MAX_TOKENS_TURN = 1500    # per interview turn (persona/researcher)
MAX_TOKENS_SUMMARY = 8192  # summary report
