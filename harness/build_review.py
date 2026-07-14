"""Build a phone-friendly BLIND review page from a run dir. Each draft shows its neutral
beat-list + full text, rated on three axes (Sequence, Voice, Constraint) + notes, with a
"Copy all scores" button. The reveal map is NOT embedded — stays sealed until rating is done.

Usage:
  python3 build_review.py --run runs/round1   # -> runs/round1/review.html
"""
import argparse, glob, os, html

AXES = [
    ("seq",  "Sequence",   "Are the task's beats all present, in the right order? (5 = perfect, 1 = scrambled/missing)"),
    ("voice", "Voice",     "Does it nail the task's POV/voice/register? (5 = fully in-voice, 1 = generic)"),
    ("con",  "Constraint", "Does it honour the ONE hard stylistic constraint? (5 = flawless, 1 = broken repeatedly)"),
]

CSS = """
:root{--bg:#faf9f7;--fg:#1e1c1a;--card:#fff;--line:#d9d4cc;--accent:#3d5a80;--muted:#6b6459}
@media (prefers-color-scheme:dark){:root{--bg:#141518;--fg:#e8e6e3;--card:#1e2024;--line:#343841;--accent:#8fb3d9;--muted:#9a938a}}
:root[data-theme=dark]{--bg:#141518;--fg:#e8e6e3;--card:#1e2024;--line:#343841;--accent:#8fb3d9;--muted:#9a938a}
:root[data-theme=light]{--bg:#faf9f7;--fg:#1e1c1a;--card:#fff;--line:#d9d4cc;--accent:#3d5a80;--muted:#6b6459}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Georgia,serif;-webkit-text-size-adjust:100%}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;z-index:10}
h1{font-size:18px;margin:0 0 4px}
.sub{font:13px/1.4 system-ui,sans-serif;color:var(--muted)}
main{max-width:820px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 22px;overflow:hidden}
.card>h2{font:600 20px/1.2 system-ui,sans-serif;margin:0;padding:14px 16px;border-bottom:1px solid var(--line)}
.wc{font:12px/1 system-ui,sans-serif;color:var(--muted);font-weight:400}
details{border-bottom:1px solid var(--line)}
summary{cursor:pointer;padding:11px 16px;font:600 14px/1.3 system-ui,sans-serif;color:var(--accent)}
.body,.beats{padding:4px 18px 18px;white-space:pre-wrap}
.beats{font:14px/1.55 system-ui,sans-serif}
.rate{padding:14px 16px;display:flex;flex-direction:column;gap:14px}
.row{display:flex;flex-direction:column;gap:6px}
.row label{font:600 13px/1.2 system-ui,sans-serif}
.hint{font:12px/1.3 system-ui,sans-serif;color:var(--muted);font-weight:400}
.scale{display:flex;gap:6px}
.scale button{flex:1;min-height:44px;font:600 16px system-ui,sans-serif;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:8px;cursor:pointer}
.scale button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
textarea{width:100%;min-height:60px;font:15px/1.4 system-ui,sans-serif;padding:9px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);resize:vertical}
.copy{position:sticky;bottom:0;background:var(--bg);border-top:1px solid var(--line);padding:12px 16px;text-align:center}
.copy button{width:100%;max-width:820px;min-height:50px;font:600 16px system-ui,sans-serif;background:var(--accent);color:#fff;border:none;border-radius:10px;cursor:pointer}
.ok{color:#2e7d32;font:13px system-ui,sans-serif;margin-top:6px}
"""


def esc(s):
    return html.escape(s)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); a = ap.parse_args()
    labels = sorted(os.path.basename(p).split("_", 1)[1].rsplit(".", 1)[0]
                    for p in glob.glob(os.path.join(a.run, "draft_*.md")))
    cards = []
    for lab in labels:
        draft = open(os.path.join(a.run, f"draft_{lab}.md")).read()
        bp = os.path.join(a.run, f"beats_{lab}.md")
        beats = open(bp).read() if os.path.exists(bp) else "(no beat-list; run summarize.py)"
        wc = len(draft.split())
        rows = "".join(
            f'<div class="row" data-axis="{ax}"><label>{name} <span class="hint">— {esc(hint)}</span></label>'
            f'<div class="scale">{"".join(f"<button type=button data-v={v}>{v}</button>" for v in range(1,6))}</div></div>'
            for ax, name, hint in AXES)
        cards.append(
            f'<div class="card" data-label="{lab}"><h2>Draft {lab} <span class="wc">· {wc:,} words</span></h2>'
            f'<details><summary>▸ Neutral beat-list (check sequence)</summary><div class="beats">{esc(beats)}</div></details>'
            f'<details><summary>▸ Full chapter text</summary><div class="body">{esc(draft)}</div></details>'
            f'<div class="rate">{rows}'
            f'<div class="row" data-axis="notes"><label>Notes</label><textarea placeholder="anything you noticed"></textarea></div>'
            f'</div></div>')

    js = """
document.querySelectorAll('.scale').forEach(sc=>sc.addEventListener('click',e=>{
  if(e.target.tagName!=='BUTTON')return;
  sc.querySelectorAll('button').forEach(b=>b.classList.remove('on'));e.target.classList.add('on');}));
document.getElementById('copy').addEventListener('click',()=>{
  let out=[];
  document.querySelectorAll('.card').forEach(c=>{
    let parts=[];
    c.querySelectorAll('.row').forEach(r=>{
      const ax=r.dataset.axis;
      if(ax==='notes'){const t=r.querySelector('textarea').value.trim();if(t)parts.push('notes: '+t);}
      else{const on=r.querySelector('.scale button.on');parts.push(ax+':'+(on?on.dataset.v:'-'));}
    });
    out.push('['+c.dataset.label+'] '+parts.join('  '));
  });
  const txt=out.join('\\n');
  navigator.clipboard.writeText(txt).then(
    ()=>document.getElementById('okmsg').textContent='Copied — paste it back.',
    ()=>document.getElementById('okmsg').textContent=txt);
});
"""
    page = (f"<!doctype html><html><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>Prose parity — blind review</title><style>{CSS}</style></head><body>"
            f"<header><h1>Prose parity — blind review</h1><div class=sub>Rate each draft on the three "
            f"scales, add notes, then tap Copy all scores. Length varies by design — judge the writing, "
            f"not the word count.</div></header><main>{''.join(cards)}</main>"
            f"<div class=copy><button id=copy>Copy all scores</button><div class=ok id=okmsg></div></div>"
            f"<script>{js}</script></body></html>")
    open(os.path.join(a.run, "review.html"), "w").write(page)
    print(f"Wrote {a.run}/review.html ({len(labels)} drafts: {', '.join(labels)})")


if __name__ == "__main__":
    main()
