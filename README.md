# llm-prose-parity

**A blind, task-oriented eval for one question the benchmarks won't answer: can a model you can run yourself actually *write* as well as a frontier model — well enough to trust with real prose?**

Most "local LLM" content measures tokens/sec and prompt-prefill speed. Those numbers tell you how *fast* a model is wrong. They don't tell you whether the output does the job. This tool measures the job: every model drafts the **same** chapter-length prose task from an identical brief, you rate the results **blind**, and you get a tier ladder — sequence, voice, and constraint-adherence — instead of a throughput chart.

It exists to help people deciding **what hardware to buy for local LLMs** (a 48GB Mac mini? a 128GB box? just keep paying for a hosted model?) answer it with *their own eyes on real output*, not influencer vibes.

> Origin: built while deciding whether a local model could draft chapters of a novel-in-progress as well as a hosted frontier model. Short answer that run: no — the small local models were fast and fluent and still failed on *voice*, and some quietly broke hard style rules under fluent prose (the most dangerous kind of failure to delegate). Your mileage — and the models — will change. That's why you re-run it.

## Why it's not gameable
The drafting task is **generated fresh** (a randomized premise → a strong "author model" expands it into a full brief with beats, locked dialogue, dialect registers, and one hard stylistic constraint). There is **no fixed benchmark corpus** to train against, so a run tells you how models do on *new* material. You generate a task once, test every contestant on that same task, and mint a new one only when you choose.

## Quickstart
```bash
git clone https://github.com/afluffywaffle/llm-prose-parity && cd llm-prose-parity
cp config.example.json config.json          # edit models; slugs are OpenRouter ids
export OPENROUTER_API_KEY=sk-or-...          # or ~/.config/openrouter.key

# run everything from the repo root:
python3 harness/generate_task.py                              # 1. invent a fresh random task (once)
python3 harness/run_parity.py   --task task/pack.md --out runs/r1   # 2. all models draft it, blind
python3 harness/summarize.py    --run  runs/r1                      # 3. neutral beat-lists
python3 harness/build_review.py --run  runs/r1                      # 4. -> runs/r1/review.html
# 5. open runs/r1/review.html, rate each draft blind, tap "Copy all scores"
# 6. THEN open runs/r1/reveal_map.json to see which label was which model
```
Optional rolling-context loop (drafts beat-by-beat; fixes "rushed endings"):
`python3 harness/beat_loop.py --beats task/beats.json --model <slug> --out runs/loop`

## Bring your own project
Don't want a random task? Point it at *your* world:
```bash
python3 generate_task.py --from-brief my_project.txt
```
`my_project.txt` is free text — your setting, voice, hard constraints, and rough beats (your
"spine"/references). The author model structures it into the same pack + manifest, so you test
models on **your** prose task. See `METHODOLOGY.md` for the pack/beats schema if you'd rather
hand-author them. Nothing about the tool assumes any particular fandom or project.

## Running truly local (no cloud)
Point `base_url` in `config.json` at any OpenAI-compatible server — e.g. Ollama at
`http://localhost:11434/v1` — and list its model names as `contestants`. Then the throughput you
*do* care about (your box, your models) is measured against output you can actually judge.

## What you need
- Python 3 (standard library only — no pip installs).
- An OpenRouter key (a whole run costs cents), **or** a local OpenAI-compatible endpoint.
- No secrets live in the repo; `config.json` and `*.key` are gitignored.

## Files
- `harness/generate_task.py` — fresh randomized drafting task (or structure your own brief).
- `harness/run_parity.py` — every model drafts the task, blind labels + sealed reveal map.
- `harness/beat_loop.py` — optional rolling-context per-beat drafting loop.
- `harness/summarize.py` — neutral beat-lists (a reader model, never a contestant).
- `harness/build_review.py` — phone-friendly blind rating page (Sequence / Voice / Constraint).
- `harness/models.py` — shared API-call helper (retries, null-content guard).
- `METHODOLOGY.md` — the full method, schema, and how to read the results.

## License
MIT. See `LICENSE`.
