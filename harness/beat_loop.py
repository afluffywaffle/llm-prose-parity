"""ARM 1b (optional) — rolling-context per-beat drafting loop for ONE model.

Drafts the chapter one beat at a time from task/beats.json, giving each call: the global
frame + registers, a running plot-recap, the last ~120 words verbatim (continue, don't
restart), and that beat's canon + locked dialogue + word target. Stitches into one draft.
Fixes single-shot 'length collapse / rushed ending' (each beat gets its own budget) — but
it does NOT fix voice, and weak models can loop/degenerate; that's a finding, not a bug.

Usage:
  python3 beat_loop.py --beats task/beats.json --model <slug> --out runs/loop
"""
import argparse, json, os, re
from models import call, load_config, load_key

TAIL_WORDS = 120
MIN_TOKENS = 4000  # per-beat floor so reasoning models keep room for prose after thinking


def tail(text, n=TAIL_WORDS):
    w = text.split()
    return " ".join(w[-n:]) if len(w) > n else text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", default="task/beats.json")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default="runs/loop")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--label", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    key = load_key()
    base = cfg.get("base_url", "https://openrouter.ai/api/v1/chat/completions")
    spec = json.load(open(a.beats))
    os.makedirs(a.out, exist_ok=True)
    label = a.label or re.sub(r"[^a-z0-9]+", "-", a.model.lower()).strip("-")

    system = (
        "You are drafting ONE BEAT of a chapter written continuously, beat by beat.\n"
        f"FRAME / POV / VOICE / CONSTRAINT: {spec['frame']}\n"
        f"DIALECT REGISTERS: {spec['registers']}\n"
        "You get the story so far (recap), the LAST LINES already written (continue seamlessly — do "
        "NOT restart or re-describe), and THIS BEAT. Honour locked lines' meaning, re-voiced in dialect. "
        "Obey the hard constraint. Let the beat breathe to its target. Output ONLY the prose for this beat."
    )
    parts, recaps, prev_tail, log = [], [], "", []
    for b in spec["beats"]:
        tgt = int(b.get("target_words", 600))
        user = (f"STORY SO FAR:\n" + ("\n".join(f"- {r}" for r in recaps) or "(opening beat)") +
                f"\n\nLAST LINES (continue from here):\n{prev_tail or '(none — first beat)'}\n\n"
                f"=== WRITE THIS BEAT ({tgt} words) ===\nTitle: {b.get('title','')}\n"
                f"Present: {b.get('present','')} · Narrator: {b.get('narrator_status','')}\n"
                f"Flags: {b.get('flags','') or 'none'}\n\nDepict:\n{b.get('canon','')}\n\n"
                f"Locked dialogue (re-voice, keep meaning):\n{b.get('locked','') or '(none — invent fitting dialogue)'}")
        mt = min(cfg.get("max_tokens", 8000), max(int(tgt * 2.2) + 400, MIN_TOKENS))
        try:
            prose, _ = call(a.model, system, user, key=key, max_tokens=mt,
                            temperature=cfg.get("temperature", 0.2), base_url=base,
                            role="contestant", label=f"{label}:{b['id']}")
        except Exception as e:
            log.append({"beat": b["id"], "error": str(e)[:160]})
            print(f"  beat {b['id']:<3} FAIL"); continue
        parts.append(prose); recaps.append(b.get("recap", b.get("title", b["id"])))
        prev_tail = tail(prose); log.append({"beat": b["id"], "words": len(prose.split())})
        print(f"  beat {b['id']:<3} OK  {len(prose.split()):>4} words")
    chapter = "\n\n".join(parts)
    with open(f"{a.out}/draft_{label}.md", "w", encoding="utf-8") as f:
        f.write(chapter)
    with open(f"{a.out}/meta_{label}.json", "w", encoding="utf-8") as f:
        json.dump({"model": a.model, "beats": log, "total_words": len(chapter.split())},
                  f, indent=2)
    print(f"\n{a.model}: {len(chapter.split())} words over {len(parts)} beats -> {a.out}/draft_{label}.md")


if __name__ == "__main__":
    main()
