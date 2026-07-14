"""Shared model-call helpers. Stdlib only (urllib). OpenRouter by default; any
OpenAI-compatible endpoint works via --base-url (e.g. a local Ollama server).

API key resolution (never hard-code a key): $OPENROUTER_API_KEY, then
~/.config/openrouter.key, then ~/.openrouter.key. For a keyless local endpoint
(Ollama) pass base_url and any dummy key.
"""
import json, os, sys, time, urllib.request, urllib.error

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k.strip()
    for p in ("~/.config/openrouter.key", "~/.openrouter.key"):
        fp = os.path.expanduser(p)
        if os.path.exists(fp):
            return open(fp).read().strip()
    sys.exit("No API key. Set $OPENROUTER_API_KEY or put it in ~/.config/openrouter.key "
             "(for a local Ollama endpoint, any non-empty value works).")


def load_config(path="config.json"):
    # look in cwd, then the parent dir, then next to this file's repo root,
    # so it works whether you run from the repo root or from harness/
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (path, os.path.join("..", path), os.path.join(here, "..", path)):
        if os.path.exists(cand):
            return json.load(open(cand))
    sys.exit(f"No {path} found. Copy config.example.json to config.json and edit it.")


def call(model, system, user, key=None, max_tokens=8000, temperature=0.2,
         base_url=OPENROUTER_URL, retries=4, extra=None):
    """Return (text, usage_dict). Retries transient 429/5xx and empty/null content
    (e.g. a reasoning model that spent its whole budget thinking)."""
    key = key or load_key()
    body = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    if extra:
        body.update(extra)
    data = json.dumps(body).encode()
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(base_url, data=data, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=600))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:160]}"
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(6 * (attempt + 1)); continue
            raise
        content = (r.get("choices") or [{}])[0].get("message", {}).get("content")
        if content and content.strip():
            return content.strip(), r.get("usage", {})
        last = "empty/null content"
        if attempt < retries - 1:
            time.sleep(4 * (attempt + 1)); continue
    raise RuntimeError(f"no usable content after {retries} tries ({last})")


def extract_json(text):
    """Pull the first JSON object out of a model reply (tolerates code fences / prose)."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("no JSON object in reply")
    return json.loads(s[a:b + 1])
