"""Neutral beat-list step. For each draft in a run dir, a READER model (from config,
ideally NOT one of the contestants) writes a factual "what happens, in order" list so the
human can check sequence against the task without re-reading every draft. No praise/critique.

Usage:
  python3 summarize.py --run runs/round1
Writes runs/round1/beats_<label>.md next to each draft_<label>.md.
"""
import argparse, glob, os
from models import call, load_config, load_key

READER_SYS = (
    "Read the draft chapter and write a NEUTRAL, numbered, in-order list of the story beats it depicts "
    "— one plain sentence each (location, who acts, what happens). NO praise, criticism, or style "
    "commentary; purely what happens, in what order. At the end add a line 'CONSTRAINT:' stating "
    "factually whether the draft appears to honour or violate the task's hard stylistic constraint "
    "(quote a short example if violated). Output only the list."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--config", default="config.json")
    a = ap.parse_args()
    cfg = load_config(a.config)
    key = load_key()
    base = cfg.get("base_url", "https://openrouter.ai/api/v1/chat/completions")
    reader = cfg.get("reader_model") or cfg["author_model"]
    for path in sorted(glob.glob(f"{a.run}/draft_*.md")):
        lab = os.path.basename(path).split("_", 1)[1].rsplit(".", 1)[0]
        draft = open(path).read()
        try:
            txt, _ = call(reader, READER_SYS, draft, key=key, max_tokens=2000,
                          temperature=0.0, base_url=base)
            open(f"{a.run}/beats_{lab}.md", "w").write(txt)
            print(f"  {lab}: summarized")
        except Exception as e:
            print(f"  {lab}: FAIL {str(e)[:120]}")


if __name__ == "__main__":
    main()
