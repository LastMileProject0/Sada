"""Four-question text-evidence retrieval demonstration for Maymona's handoff."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lastmile_ai.knowledge.retrieval import retrieve_evidence

QUESTIONS = [
    ("Q1_CAP", "Is a missing protective instruction field automatically a CAP 1.2 violation?"),
    ("Q2_ACCESSIBILITY", "Does UAE digital accessibility policy support considering alternative alert formats for people who cannot use a voice or visual warning?"),
    ("Q3_PRIVACY", "Can a proposed outside emergency-alert partner automatically receive disability-related resident data under UAE personal-data law?"),
    ("Q4_NO_EVIDENCE", "ما سعر تذاكر القطار في كيوتو سنة 2042؟"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Save the results as JSON; otherwise print only")
    args = parser.parse_args()
    output = {name: retrieve_evidence(question, top_k=4) for name, question in QUESTIONS}
    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Saved retrieval demonstration to {args.output}")
    else:
        print(text)

if __name__ == "__main__":
    main()
