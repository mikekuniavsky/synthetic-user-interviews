import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env.local")

# --- Mode ---
USE_OPENROUTER = True  # Set to True to use multi-model OpenRouter mode

# --- API keys (set in .env.local) ---
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- Basic mode (Anthropic SDK, single model) ---
ANTHROPIC_MODEL = "claude-opus-4-6"

# --- Multi-model mode (OpenRouter) ---
# Persona model is picked randomly per interview from this list
PERSONA_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
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
