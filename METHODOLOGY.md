# Methodology

## The claim this tool tests
"Model X can draft real prose well enough that I'd delegate the writing to it." Throughput
(tokens/sec) and prompt-prefill speed don't test that — a model can be fast and fluent and still
produce output you'd have to rewrite. This is a **blind, human-rated, task-oriented** eval of the
output itself.

## Design principles
1. **Same input, fair fight.** Every contestant drafts the *identical* task pack with the same minimal
   system prompt. The substance lives in the pack, so differences are the model's, not the prompt's.
2. **Fresh, un-gameable task.** The task is generated from a randomized premise each time you ask for a
   new one — no fixed corpus to overfit or leak into training. You reuse one task across all contestants
   in a round; you mint a new one only with `--new`.
3. **Blind rating.** Drafts are shuffled to opaque labels; the label→model map is sealed until after you
   score. A separate *reader* model (never a contestant) writes a neutral beat-list per draft so you can
   check sequence without re-reading everything and without praise/critique bias.
4. **Three axes that separate real writing:**
   - **Sequence** — are the task's beats all present, in order? (Most competent models pass; it rarely
     separates the field — which is the point: don't stop at "it hit the plot.")
   - **Voice** — does it hold the POV/voice/register the task demands, or is it generic? (This is usually
     where models actually differ, and where fluent-but-wrong hides.)
   - **Constraint** — does it honour the ONE hard stylistic rule the task sets (e.g. "no water imagery",
     "no -ly adverbs", "violence as aftermath not tactics")? A single, checkable rule surfaces the
     dangerous failure mode: a model that writes beautifully while quietly breaking the rules.

## The pack / beats schema (for bring-your-own or hand-authoring)
`task/beats.json`:
```json
{
  "title": "...",
  "premise": "one paragraph",
  "frame": "POV + voice + the ONE hard constraint, as one paragraph",
  "registers": "dialect cheat-sheet: who speaks how",
  "beats": [
    {"id":"1","title":"...","present":"who acts","narrator_status":"present|absent-relayed|off-page",
     "recap":"one sentence for the running summary","target_words":600,
     "canon":"what this beat must depict","locked":"verbatim dialogue to honour, or ''","flags":"branch/POV note or ''"}
  ]
}
```
`task/pack.md` is a human-readable render of the same thing — it's what contestants actually draft from.

## Reading the results
- Cluster the scores. Expect a few tiers: models that are *alive and usable*, models that are *faithful
  but flat* (they follow the beats but the voice is generic — "reads like the outline"), and models that
  *break* (loop, truncate, or violate the constraint).
- **Watch for fluent-but-wrong.** A high Voice score with a low Constraint score is the trap: polished
  prose that broke the rules. That's harder to catch in production than obviously-bad output.
- **Length is not quality.** Small models often either rush (single-shot) or balloon (per-beat loop)
  without gaining life. Judge the writing; the word count is just context.
- **Calibrate against a known tier.** Include one hosted frontier model and one mid model as anchors, so
  "how good is my local model" has a reference, not just a rank.

## Cost & reproducibility
Stdlib Python; one run is cents on OpenRouter (or free on a local endpoint). `generate_task.py --seed N`
reproduces a premise; `run_parity.py --seed N` reproduces the blind-label shuffle. `task/premise.json`
records what was generated, so you can disclose exactly what a run tested.

## Limitations (be honest about these)
- The rating is one human's judgement — that's the *point* (it's your prose taste that matters), but it's
  subjective; average multiple raters if you want robustness.
- The "author model" that writes the task and the "reader model" that summarizes are themselves models;
  a weak author model makes a weak task. Use a strong one.
- Model outputs can contain instruction-like text; the reader step only summarizes, so worst case a
  summary is slightly off — verify anything surprising against the draft itself.
