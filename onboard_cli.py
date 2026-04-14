#!/usr/bin/env python3
"""
CLI Voice Onboarding.
Run this to onboard a new client from the terminal.
Produces a Voice Document and config.json in voices/{client_id}/

Usage:
    python onboard_cli.py
    python onboard_cli.py --client-id myprotocol
"""

import sys
import os
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import anthropic
from agents.voice_builder import VoiceIntakeData, build_voice_document, save_voice_document
from publishing.scheduler import save_client_config


def ask(prompt: str, required: bool = True) -> str:
    while True:
        val = input(f"\n{prompt}\n> ").strip()
        if val or not required:
            return val
        print("  (required — please enter a value)")


def ask_list(prompt: str) -> list[str]:
    print(f"\n{prompt}")
    print("  Enter one per line. Empty line when done.")
    items = []
    while True:
        val = input("  > ").strip()
        if not val:
            break
        items.append(val)
    return items


def main():
    parser = argparse.ArgumentParser(description="CLI Voice Onboarding")
    parser.add_argument("--client-id", help="Client ID (auto-generated if not set)")
    parser.add_argument("--voices-path", default="voices", help="Path to voices directory")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "=" * 60)
    print("AI CONTENT MACHINE — VOICE ONBOARDING")
    print("=" * 60)
    print("This takes ~30 minutes. The output is a Voice Document")
    print("that becomes the system prompt for all content generation.")
    print("=" * 60)

    intake = VoiceIntakeData()

    # ── Stage 1: Identity ─────────────────────────────────────
    print("\n\n[ STAGE 1: IDENTITY ]")

    intake.brand_name = ask("Brand or person name:")
    intake.one_liner = ask("What do they do in one sentence? (plain English, not the whitepaper version)")
    intake.target_audience = ask("Who reads their content? What do they care about?")
    intake.competitor_respect = ask("A competitor or brand they respect (study their tone):", required=False)
    intake.competitor_dislike = ask("A competitor or brand they dislike (avoid this register):", required=False)

    # Client ID
    if args.client_id:
        intake.client_id = args.client_id
    else:
        suggested = intake.brand_name.lower().replace(" ", "_")[:20]
        cid = input(f"\nClient ID for file storage [{suggested}]: ").strip()
        intake.client_id = cid or suggested

    # ── Stage 2: Writing Samples ──────────────────────────────
    print("\n\n[ STAGE 2: WRITING SAMPLES ]")
    print("The more samples you provide, the more accurate the voice.")

    print("\nPaste recent articles or posts.")
    print("Enter text directly, then type END on a new line when done.")
    print("(Press Enter then END to skip)")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    if lines:
        intake.writing_samples.append("\n".join(lines))

    num_best = input("\nHow many best-performing posts to add? (0-3): ").strip()
    num_best = int(num_best) if num_best.isdigit() else 0

    for i in range(num_best):
        print(f"\nBest post #{i+1} — paste text then type END:")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        post_text = "\n".join(lines)
        why = input("Why did it work? (optional): ").strip()
        if post_text:
            intake.best_posts.append({"text": post_text, "why_it_worked": why})

    print("\nAny raw writing that felt authentic (Discord messages, drafts, etc)?")
    print("Paste then type END, or just END to skip:")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    if lines:
        intake.raw_authentic.append("\n".join(lines))

    intake.content_hate = ask_list(
        "Content they NEVER want to produce (e.g. 'hype posts', 'price predictions'):"
    )

    # ── Stage 3: Voice Rules ──────────────────────────────────
    print("\n\n[ STAGE 3: VOICE RULES ]")

    print("\nTone position:")
    print("  1. degen       — Sharp, irreverent, crypto-native")
    print("  2. hybrid      — Technical credibility + accessible (recommended)")
    print("  3. institutional — Authoritative, clean, measured")
    print("  4. founder     — Direct, shows the work, no corporate polish")
    tone_choice = input("Choose (1-4) [2]: ").strip()
    tone_map = {"1": "degen", "2": "hybrid", "3": "institutional", "4": "founder"}
    intake.tone_position = tone_map.get(tone_choice, "hybrid")

    intake.owned_topics = ask_list(
        "Topics they own and post about with authority (aim for 5-7):"
    )
    intake.avoided_topics = ask_list(
        "Topics to avoid entirely (optional):"
    )
    intake.banned_words = ask_list(
        "Additional banned words beyond defaults (optional):"
    )
    intake.required_phrases = ask_list(
        "Phrases or terminology they always use (optional):"
    )
    intake.always_true = ask(
        "What should always be true about this content? (free text, optional):",
        required=False
    )

    # ── Stage 4: Calibration ──────────────────────────────────
    print("\n\n[ STAGE 4: CALIBRATION NOTES ]")
    intake.calibration_notes = ask(
        "Any final notes from this session? (optional):",
        required=False
    )

    # ── Build Voice Document ───────────────────────────────────
    print("\n\nBuilding Voice Document...")
    print("(Analysing writing samples with Claude — this takes ~30 seconds)")

    try:
        voice_doc = build_voice_document(intake, client)
        saved_path = save_voice_document(
            voice_doc, intake.client_id, intake.version, args.voices_path
        )

        # Save scheduler config
        config = {
            "pillars": intake.owned_topics or [
                "What founders get wrong about growth marketing",
                "DeFi growth tactics that move TVL and users"
            ],
            "keywords": None,
            "watch_accounts": [],
            "rss_interval_hours": 6,
            "x_interval_hours": 2,
            "auto_schedule_approved": True,
        }
        save_client_config(intake.client_id, config, args.voices_path)

        print("\n" + "=" * 60)
        print("VOICE DOCUMENT CREATED")
        print("=" * 60)
        print(f"Client ID:  {intake.client_id}")
        print(f"Version:    {intake.version}")
        print(f"Saved to:   {saved_path}")
        print(f"Doc length: {len(voice_doc)} chars")
        print()
        print("Next steps:")
        print(f"  1. Review: cat {saved_path}")
        print(f"  2. Start server: uvicorn backend.main:app --reload")
        print(f"  3. Generate content: POST /generate with client_id={intake.client_id}")
        print(f"  4. Run monitor: python backend/inputs/rss_monitor.py {intake.client_id}")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR building voice document: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
