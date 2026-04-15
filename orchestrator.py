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
    MAX_TOKENS_SUMMARY,
)
from personas import PERSONAS
from researcher_prompt import RESEARCHER_PROMPT
from summary_prompt import SUMMARY_PROMPT
from interview_guide import OPENING_PROMPTS

if USE_OPENROUTER:
    from api import call_any as call_api
else:
    from api import call_claude as call_api


class Agent:
    """Wraps a model + system prompt + message history for one participant in an interview.

    send() always receives a user message and returns the assistant response,
    keeping the history in the correct alternating shape. self.model updates
    to the actual model used if a fallback fires (switch-and-stay behaviour).
    """

    def __init__(self, model: str, system_prompt: str):
        self.model = model
        self.system_prompt = system_prompt
        self.messages: list = []

    def send(self, user_content: str) -> str:
        self.messages.append({"role": "user", "content": user_content})
        response, model_used = call_api(self.model, self.system_prompt, self.messages)
        self.messages.append({"role": "assistant", "content": response})
        self.model = model_used
        return response


def _pick_researcher(researcher_models: list) -> str:
    return random.choice(researcher_models) if RANDOMIZE_RESEARCHER_MODEL else researcher_models[0]


def run_interview(persona: dict, researcher_models: list) -> tuple[list, str]:
    """
    Run a single interview between the researcher and a persona.
    Returns (transcript, researcher_model).
    """

    researcher = Agent(_pick_researcher(researcher_models), RESEARCHER_PROMPT)
    persona_agent = Agent(persona["model"], persona["prompt"])

    print(f"\n{'='*60}")
    print(f"Starting interview with: {persona['name']}")
    print(f"Persona model: {persona_agent.model}")
    print(f"Researcher model: {researcher.model}")
    print(f"{'='*60}\n")

    transcript = []

    # Researcher generates the opening question from a random prompt seed
    opening_prompt = random.choice(OPENING_PROMPTS)
    current_question = researcher.send(opening_prompt)
    print(f"RESEARCHER ({researcher.model}): {current_question}\n")
    transcript.append({"role": "researcher", "model": researcher.model, "content": current_question})

    for turn in range(NUM_TURNS):

        # Persona answers the current question
        persona_response = persona_agent.send(current_question)
        print(f"{persona['name'].upper()}: {persona_response}\n")
        transcript.append({"role": persona["name"], "content": persona_response})

        # Last turn: interview ends on the persona's answer
        if turn == NUM_TURNS - 1:
            break

        # Second-to-last turn: cue the researcher to close with Topic 7 so the
        # persona's final answer wraps up the interview naturally
        researcher_input = persona_response
        if turn == NUM_TURNS - 2:
            researcher_input += (
                "\n\n[Note to interviewer: This is your second-to-last question. "
                "Move to Topic 7 (Close) — ask what one thing they would change "
                "about their early-stage process. The next response will be their last.]"
            )

        # Researcher follows up
        current_question = researcher.send(researcher_input)
        print(f"RESEARCHER ({researcher.model}): {current_question}\n")
        transcript.append({"role": "researcher", "model": researcher.model, "content": current_question})

    return transcript, researcher.model


def save_transcript(persona: dict, transcript: list, researcher_model: str, output_dir: Path) -> Path:
    """Save a single interview transcript to a JSON file."""

    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"interview_{persona['name']}_{timestamp}.json"

    output = {
        "persona_name": persona["name"],
        "discipline": persona["discipline"],
        "persona_model": persona["model"],
        "researcher_model": researcher_model,
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

    summary, _ = call_api(
        model=summary_model,
        system_prompt=SUMMARY_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Here are the interview transcripts:\n{formatted_transcripts}\n\nPlease provide your synthesis.",
        }],
        max_tokens=MAX_TOKENS_SUMMARY,
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
    # In OpenRouter mode, persona and researcher each get one random model per interview.
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

        transcript, researcher_model = run_interview(persona, researcher_models)
        filepath = save_transcript(persona, transcript, researcher_model, OUTPUT_DIR)
        transcript_files.append(filepath)

        print(f"\nCompleted {i+1}/{len(PERSONAS)} interviews\n")

    run_summary(transcript_files, summary_model)


if __name__ == "__main__":
    main()
