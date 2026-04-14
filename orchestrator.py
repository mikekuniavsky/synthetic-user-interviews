import json
import random
import datetime
from pathlib import Path

from config import (
    USE_OPENROUTER,
    RANDOMIZE_PERSONA_MODEL,
    RANDOMIZE_RESEARCHER_MODEL,
    ANTHROPIC_MODEL,
    PERSONA_MODELS,
    RESEARCHER_MODELS,
    SUMMARY_MODEL,
    OUTPUT_DIR,
    NUM_TURNS,
)
from personas import PERSONAS
from researcher_prompt import RESEARCHER_PROMPT
from summary_prompt import SUMMARY_PROMPT
from interview_guide import OPENING_PROMPTS

if USE_OPENROUTER:
    from api import call_openrouter as call_api
else:
    from api import call_claude as call_api


def _pick_researcher(researcher_models: list) -> str:
    return random.choice(researcher_models) if RANDOMIZE_RESEARCHER_MODEL else researcher_models[0]


def run_interview(persona: dict, researcher_models: list) -> list:
    """
    Run a single interview between the researcher and a persona.
    Returns the full conversation history as a list of dicts.
    """

    print(f"\n{'='*60}")
    print(f"Starting interview with: {persona['name']}")
    print(f"Persona model: {persona['model']}")
    print(f"Researcher models: {researcher_models}")
    print(f"{'='*60}\n")

    # Separate conversation histories for each agent.
    # Each agent only sees the conversation, not the other's system prompt.
    researcher_messages = []
    persona_messages = []

    # Shared conversation log for saving
    transcript = []

    # Researcher opens the interview with a randomly chosen starting direction
    opening_prompt = random.choice(OPENING_PROMPTS)
    opening = call_api(
        model=_pick_researcher(researcher_models),
        system_prompt=RESEARCHER_PROMPT,
        messages=[{"role": "user", "content": opening_prompt}],
    )

    print(f"RESEARCHER: {opening}\n")
    transcript.append({"role": "researcher", "content": opening})

    # Seed researcher history with the bootstrap turn that was used to generate
    # the opening, so subsequent calls always start with a user message.
    researcher_messages.append({"role": "user", "content": opening_prompt})
    researcher_messages.append({"role": "assistant", "content": opening})
    persona_messages.append({"role": "user", "content": opening})

    # Main conversation loop
    for turn in range(NUM_TURNS):

        # Persona responds
        persona_response = call_api(
            model=persona["model"],
            system_prompt=persona["prompt"],
            messages=persona_messages,
        )

        print(f"{persona['name'].upper()}: {persona_response}\n")
        transcript.append({"role": persona["name"], "content": persona_response})

        persona_messages.append({"role": "assistant", "content": persona_response})
        researcher_messages.append({"role": "user", "content": persona_response})

        # Researcher follows up — pick a fresh random model each turn
        researcher_response = call_api(
            model=_pick_researcher(researcher_models),
            system_prompt=RESEARCHER_PROMPT,
            messages=researcher_messages,
        )

        print(f"RESEARCHER: {researcher_response}\n")
        transcript.append({"role": "researcher", "content": researcher_response})

        researcher_messages.append({"role": "assistant", "content": researcher_response})
        persona_messages.append({"role": "user", "content": researcher_response})

    return transcript


def save_transcript(persona: dict, transcript: list, output_dir: Path) -> Path:
    """Save a single interview transcript to a JSON file."""

    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"interview_{persona['name']}_{timestamp}.json"

    output = {
        "persona_name": persona["name"],
        "discipline": persona["discipline"],
        "persona_model": persona["model"],
        "timestamp": timestamp,
        "transcript": transcript,
    }

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Transcript saved to {filename}")
    return filename


def format_transcripts_for_summary(transcript_files: list) -> str:
    """Load all transcripts and format them for the summary agent."""

    all_transcripts = []

    for filepath in transcript_files:
        with open(filepath) as f:
            data = json.load(f)

        formatted = f"\n\n--- Interview with {data['persona_name']} "
        formatted += f"({data['discipline'].replace('_', ' ').title()}) ---\n"

        for turn in data["transcript"]:
            speaker = turn["role"].upper()
            content = turn["content"]
            formatted += f"\n{speaker}: {content}\n"

        all_transcripts.append(formatted)

    return "\n".join(all_transcripts)


def run_summary(transcript_files: list, summary_model: str) -> str:
    """Run the summary agent across all transcripts."""

    print(f"\n{'='*60}")
    print(f"Running summary across {len(transcript_files)} interviews")
    print(f"Summary model: {summary_model}")
    print(f"{'='*60}\n")

    formatted_transcripts = format_transcripts_for_summary(transcript_files)

    summary = call_api(
        model=summary_model,
        system_prompt=SUMMARY_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Here are the interview transcripts:\n{formatted_transcripts}\n\nPlease provide your synthesis.",
        }],
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = OUTPUT_DIR / f"summary_{timestamp}.md"

    with open(summary_file, "w") as f:
        f.write(summary)

    print(f"Summary saved to {summary_file}")
    print(f"\n{summary}")

    return summary


def main():

    # In basic mode, every call uses ANTHROPIC_MODEL.
    # In OpenRouter mode, persona gets a random model per interview;
    # researcher gets a random model per turn (handled inside run_interview).
    if USE_OPENROUTER:
        researcher_models = RESEARCHER_MODELS
        summary_model = SUMMARY_MODEL
    else:
        researcher_models = [ANTHROPIC_MODEL]
        summary_model = ANTHROPIC_MODEL

    transcript_files = []

    for i, persona in enumerate(PERSONAS):
        if USE_OPENROUTER:
            persona["model"] = random.choice(PERSONA_MODELS) if RANDOMIZE_PERSONA_MODEL else PERSONA_MODELS[0]
        else:
            persona["model"] = ANTHROPIC_MODEL

        transcript = run_interview(persona, researcher_models)
        filepath = save_transcript(persona, transcript, OUTPUT_DIR)
        transcript_files.append(filepath)

        print(f"\nCompleted {i+1}/{len(PERSONAS)} interviews\n")

    run_summary(transcript_files, summary_model)


if __name__ == "__main__":
    main()
