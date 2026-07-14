"""Generate a FRESH, RANDOMIZED prose-drafting task each run, so the benchmark
can't be gamed or trained against — every run tests the models on new material.

A random premise (genre, setting, narrator stance, a HARD stylistic constraint, and
character voice registers) is assembled from pools, then expanded by a strong "author
model" into a full drafting pack + a beat-by-beat manifest with some locked dialogue.
Output:
  task/pack.md    — the shared brief every contestant drafts from
  task/beats.json — the per-beat manifest (frame, registers, beats[]) for the loop
  task/premise.json — the random premise + seed (for reproducibility / disclosure)

Usage:
  python3 generate_task.py                 # fresh random task via config's author_model
  python3 generate_task.py --seed 123      # reproducible premise
  python3 generate_task.py --from-brief my_notes.txt   # structure YOUR project instead

Bring-your-own: pass --from-brief with a plain-text description of your world, voice,
constraints, and rough beats; the author model structures it into the same pack+manifest
so you can test models on YOUR prose task instead of a random one.
"""
import argparse, json, os, random
from models import call, load_config, extract_json

GENRE = ["low fantasy", "space opera", "gothic mystery", "hardboiled noir", "folk horror",
         "literary domestic drama", "seafaring adventure (no water on your world? invert it)",
         "post-apocalyptic pastoral", "mythic retelling", "cozy small-town intrigue"]
SETTING = ["a city built vertically into a cliff", "a slow generation-ship", "a drowned cathedral town",
           "a border outpost in perpetual dusk", "a floating market between two warring skies",
           "a walled orchard-kingdom", "a mining colony under a dead star", "a river-delta of a thousand islands"]
STANCE = ["a first-person retrospective memoir, decades later, elegiac and self-examining",
          "a close-third present-tense account, breathless and immediate",
          "an unreliable first-person narrator who flatters themselves",
          "a witness's diary written the same night, raw and partial",
          "an oral tale, embellished, told to a crowd"]
CONSTRAINT = ["NO water/sea/ocean imagery at all — purge every tide/current/adrift metaphor",
              "NO modern idioms or anachronisms; period-plain diction only",
              "NO adverbs ending in -ly in narration",
              "render all violence as aftermath and cost, never as tactics or blow-by-blow",
              "NO colour words; describe by light, texture, and temperature instead",
              "the narrator never names their own emotion directly — show it only in the body/world"]
REGISTERS = ["a gruff old captain (heavy, grounded, archaic); a quick-tongued youth (light, slangy)",
             "a formal aristocrat (measured RP); a blunt frontier mechanic (clipped, profane-adjacent)",
             "a pious elder (scriptural cadence); a sardonic clerk (dry, precise)",
             "a foreign merchant (second-language rhythm); a local child (simple, wondering)"]


def build_premise(seed):
    r = random.Random(seed)
    return {
        "seed": seed, "genre": r.choice(GENRE), "setting": r.choice(SETTING),
        "narrator_stance": r.choice(STANCE), "hard_constraint": r.choice(CONSTRAINT),
        "registers": r.choice(REGISTERS),
    }


AUTHOR_SYS = (
    "You are a story architect. Design a SELF-CONTAINED single-chapter drafting brief for a prose "
    "novelization test. It must give contestant writers everything needed to draft the SAME chapter: "
    "a clear sequence of 10-14 beats, some LOCKED dialogue lines that must be honoured, a POV/voice "
    "frame, dialect registers, and ONE hard stylistic constraint that is easy to check and easy to "
    "violate. Invent original characters and place-names (do NOT use any existing copyrighted work). "
    "Output ONLY a JSON object, no prose, with keys: title, premise (1 paragraph), frame (POV/voice/"
    "constraint rules as one paragraph), registers (dialect cheat-sheet string), beats (array). Each "
    "beat: id (string), title, present (who acts), narrator_status (present|absent-relayed|off-page), "
    "recap (one sentence for a running plot-summary), target_words (int 400-900), canon (what this beat "
    "must depict, plain prose), locked (verbatim dialogue lines to honour, or ''), flags (branch/POV "
    "notes or '')."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None, help="reproducible premise; omit for fresh random")
    ap.add_argument("--from-brief", help="plain-text file of YOUR project to structure instead of random")
    ap.add_argument("--out", default="task")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--new", action="store_true",
                    help="regenerate a fresh task even if one already exists (overwrites task/)")
    a = ap.parse_args()
    cfg = load_config(a.config)

    # Generate ONCE, then reuse. Only make a new task on first run or explicit --new,
    # so every contestant model is compared on the SAME task within a round.
    if os.path.exists(f"{a.out}/beats.json") and not a.from_brief and not a.new:
        print(f"A task already exists at {a.out}/. Reusing it (all models draft the same task).\n"
              f"To test on fresh material, run again with --new.")
        return
    os.makedirs(a.out, exist_ok=True)

    if a.from_brief:
        brief = open(a.from_brief).read()
        user = ("Structure the following author's brief into the JSON schema. Keep THEIR world, voice, "
                "constraints, and beats; fill only gaps needed to make it draftable.\n\n" + brief)
        premise = {"source": a.from_brief}
    else:
        seed = a.seed if a.seed is not None else random.SystemRandom().randint(1, 10**9)
        premise = build_premise(seed)
        user = ("Design the brief around this randomized premise (expand it, invent specifics):\n"
                + json.dumps(premise, indent=2))
        print(f"Random premise (seed {seed}): {premise['genre']} / {premise['setting']}")

    txt, _ = call(cfg["author_model"], AUTHOR_SYS, user,
                  max_tokens=cfg.get("author_max_tokens", 6000),
                  temperature=cfg.get("author_temperature", 0.9),
                  base_url=cfg.get("base_url", "https://openrouter.ai/api/v1/chat/completions"))
    spec = extract_json(txt)
    json.dump(spec, open(f"{a.out}/beats.json", "w"), indent=2, ensure_ascii=False)
    json.dump(premise, open(f"{a.out}/premise.json", "w"), indent=2, ensure_ascii=False)

    # render a human-readable pack.md that every contestant drafts from
    lines = [f"# {spec['title']}", "", f"**Premise:** {spec['premise']}", "",
             f"**Frame / POV / voice:** {spec['frame']}", "",
             f"**Dialect registers:** {spec['registers']}", "",
             "## Beats (draft in this order — sequence is inviolable)", ""]
    for b in spec["beats"]:
        lines += [f"### Beat {b['id']} — {b['title']}  ({b.get('target_words',600)} words)",
                  f"- Present: {b.get('present','')}  · Narrator: {b.get('narrator_status','')}",
                  f"- {b.get('canon','')}"]
        if b.get("locked"):
            lines.append(f"- Locked dialogue (honour meaning; re-voice in dialect): {b['locked']}")
        if b.get("flags"):
            lines.append(f"- Flags: {b['flags']}")
        lines.append("")
    open(f"{a.out}/pack.md", "w").write("\n".join(lines))
    print(f"Wrote {a.out}/pack.md ({len(spec['beats'])} beats), beats.json, premise.json")


if __name__ == "__main__":
    main()
