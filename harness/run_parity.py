"""ARM 1 — fire the SAME task pack at every contestant model, in parallel, and write
each draft under a shuffled BLIND label plus a SEALED reveal map (label -> model).

Usage:
  python3 run_parity.py --task task/pack.md --out runs/round1
Models + settings come from config.json (copy config.example.json). Blind labels are
shuffled with --seed for reproducibility; the reveal map is written separately so rating
stays honest — do not open it until scores are in.
"""
import argparse, json, os, random, string, concurrent.futures
from models import call, load_config, load_key

SYSTEM_PROMPT = (
    "You are drafting one chapter of a literary novelization from the drafting pack that follows. "
    "Follow its beat sequence, POV/voice frame, dialect registers, locked dialogue, and its ONE hard "
    "stylistic constraint EXACTLY. Invent only in the gaps. Never contradict the pack. Let each beat "
    "breathe to roughly its word target. Output ONLY the finished chapter prose — no notes, no preamble, "
    "no headings, no bullet lists."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="task/pack.md")
    ap.add_argument("--out", default="runs/round1")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--seed", type=int, default=1234)
    a = ap.parse_args()
    cfg = load_config(a.config)
    key = load_key()
    pack = open(a.task).read()
    roster = [m["slug"] if isinstance(m, dict) else m for m in cfg["contestants"]]
    assert len(set(roster)) == len(roster), f"duplicate contestant slugs: {roster}"
    base = cfg.get("base_url", "https://openrouter.ai/api/v1/chat/completions")
    os.makedirs(a.out, exist_ok=True)

    labels = list(string.ascii_lowercase)[:len(roster)]
    order = list(range(len(roster)))
    random.Random(a.seed).shuffle(order)
    label_of = {roster[order[i]]: labels[i] for i in range(len(roster))}

    def one(slug):
        try:
            lab = label_of[slug]
            txt, usage = call(slug, SYSTEM_PROMPT, pack, key=key,
                              max_tokens=cfg.get("max_tokens", 8000),
                              temperature=cfg.get("temperature", 0.2), base_url=base,
                              role="contestant", label=lab)
            with open(f"{a.out}/draft_{lab}.md", "w", encoding="utf-8") as f:
                f.write(txt)
            return slug, lab, len(txt.split()), usage.get("cost"), None
        except Exception as e:
            return slug, label_of[slug], 0, None, str(e)[:160]

    print(f"Firing {len(roster)} models at {a.task} ...")
    reveal = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.get("parallel", 8)) as ex:
        for slug, lab, wc, cost, err in ex.map(one, roster):
            reveal[lab] = {"model": slug, "words": wc, "cost": cost, "error": err}
            print(f"  [{lab}] {slug:<42} {'FAIL '+err if err else f'{wc} words'}")
    json.dump(reveal, open(f"{a.out}/reveal_map.json", "w"), indent=2, ensure_ascii=False)
    print(f"\nDrafts + SEALED reveal_map.json -> {a.out}  (do not open reveal_map until rated)")


if __name__ == "__main__":
    main()
