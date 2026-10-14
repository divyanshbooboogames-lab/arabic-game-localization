"""English -> Arabic localization pipeline for 13 Middle East markets (one MSA master + Gulf/Levant/Egypt overlays).

  lint      strings_en.csv [--suggest]       source problems that make correct Arabic impossible (+ AI rewrites)
  translate strings_en.csv                   translate -> rule QA -> fix rule errors -> AI judge -> out/review.csv
  bakeoff   sample.csv --models A B ...      same strings through several models -> blind sheet for a linguist
  qa        current_ar.csv --col ar          rule QA only, on any CSV with `en` + a target column
  score     out/review.csv                   MQM from the human audit column (the 99% gate) + AI-judge calibration
  export    out/review.csv                   QA gate -> out/strings.csv; approved rows -> tm.csv, approved terms -> glossary.csv
  fontcheck out/strings.csv --font X.ttf     glyph coverage for every Arabic string (--shaped for RTLTMPro/ArabicSupport)
  pseudo    strings_en.csv                   fake Arabic (RTL, +30% length, placeholders kept) -> out/pseudo_strings.csv
Unchanged strings (same key + English as an approved tm.csv entry) are reused without AI calls; --no-reuse forces all.
Every AI run prints its token use and estimated cost and appends it to <out>/costs.csv.

Source CSV: key, en, [type, context, max_len, addressee, screenshot, speaker, listener, scene]
  type: ui | tutorial | dialogue | legal | push | ad | store   (push/ad/store also get gulf/levant/egypt overlays)
  addressee: player (default: gender-neutral) | male | female | group | none   (derived from `listener` when empty)
  screenshot: image path relative to the CSV (png/jpg/webp/gif, <= 5 MB); strings of one screen are sent together
  speaker / listener: a name from characters.csv, or player | group | none
  scene: conversation id; a scene's lines are always translated and judged together, in file order
characters.csv (next to the source CSV): name, ar, gender (female | male), notes   e.g. Olive,أوليف,female,anxious mother
Models: Claude ids (default claude-opus-5-5) use ANTHROPIC_API_KEY. `openai:<model>` uses `pip install openai`,
  OPENAI_API_KEY and optional OPENAI_BASE_URL, so any OpenAI-compatible endpoint (OpenAI, Gemini, Azure) works.
  `claude-code` uses NO API key: requests become job files that Claude Code answers on your subscription
  (see CLAUDE_CODE_MODE.md); re-run the same command after each round until it finishes.
"""
import argparse
import base64
import csv
import difflib
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import ar_qa

HERE = Path(__file__).parent
PROMPT_VERSION = "2026-10-13.2"
VARIANTS = ["ar", "gulf", "levant", "egypt"]
TYPES = {"ui", "tutorial", "dialogue", "legal", "push", "ad", "store"}
WEIGHTS = {"minor": 1, "major": 5, "critical": 25}  # MQM Council defaults
SEV = re.compile(r"(?:^|[|;])\s*(minor|major|critical)\b")  # entry starts: "major/accuracy; minor/fluency", not words in a `why`
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
REVIEW_FIELDS = ["key", "variant", "type", "status", "scene", "speaker", "listener", "context", "screenshot", "en", "final",
                 "suggestion", "judge", "qa", "note", "draft", "approved", "audit", "mqm", "pv"]
RESERVED = {"player", "group", "none"}  # speaker/listener values that are not characters

TRANSLATOR_ROLE = """You are the Arabic localization writer for a mobile game publisher. Apply the style guide above to every string. The user message either asks you to translate strings or to fix translations that failed automated QA; it says which.

When translating: return every key exactly once. `ar` is the MSA master shipped to all 13 countries. When `overlays` is true, also write `gulf`, `levant` and `egypt` as defined in the style guide; otherwise return them as empty strings. Use `context`, `type`, `addressee` and any attached screenshot (matched by the item's `screenshot` name) to decide meaning, register, gender and space. `glossary` entries are locked terminology; inflect them as the grammar needs. `tm` entries are approved past translations of similar strings; follow their terminology and style where the meaning matches. Put anything a reviewer must check in `note` with its tag (GENDER:, PLURAL:, CULTURE:, LENGTH:, CONTEXT:); otherwise leave it empty. In `terms`, list recurring game-specific names in the string (items, currencies, modes, features, characters) that are not in its `glossary`, with the Arabic you used; usually this is [].

Dialogue items may carry `speaker` and `listener` (characters with gender and voice notes) and `scene`. Items that share a `scene` are consecutive lines of one conversation, in the order given: keep tone, pronouns and terms consistent across them, and let each line follow from the previous one. The speaker's references to themselves agree with the speaker's gender (أنا متأكد / أنا متأكدة); second-person forms agree with `addressee` (the listener). Write character names exactly as their `ar` name."""

SYNTAX_NOTES = {
    "icu": "\n\nPlurals and selects use ICU MessageFormat, as in the style guide.",
    "smart": """

This game uses Unity Smart Strings, not ICU MessageFormat. Keep that syntax exactly. An Arabic plural is {count:plural:zero|one|two|few|many|other}: exactly six |-separated forms in that order, with {} standing for the number (like ICU #), e.g. {count:plural:لا توجد لديك عملات|لديك عملة واحدة|لديك عملتان|لديك {} عملات|لديك {} عملةً|لديك {} عملة}. Keep `plural`/`p`, `choose`, `{}` and `|` as they are.""",
}

GENDER_VARS = {
    "icu": """

The game passes {{{g}}} (female | male | other) to the message formatter. When a string must address the player and neutral wording is impossible, use {{{g}, select, female {{...}} other {{...}}}} with the masculine form under `other`, instead of flagging GENDER:.""",
    "smart": """

The game passes {{{g}}} (female | male | other) to the formatter. When a string must address the player and neutral wording is impossible, use {{{g}:choose(female):<feminine form>|<masculine form>}} instead of flagging GENDER:.""",
}

PLURAL_EXAMPLES = {
    "icu": '"You earned {amount} coins!" -> "{amount, plural, one {You earned # coin!} other {You earned # coins!}}"',
    "smart": '"You earned {amount} coins!" -> "You earned {amount:plural:{} coin|{} coins}!"',
}

JUDGE_ROLE = """You are an independent senior Arabic linguist doing MQM error annotation on translations produced by another system. The style guide above is the specification; judge against it, including its MQM severity definitions.

For each item, list every real error in `translation`. `variant` says what it should be: `ar` = MSA master, `gulf`/`levant`/`egypt` = dialect overlays that must genuinely be in that dialect. Most good translations have no errors: return an empty list for those, and do not report personal preferences as errors. But do not let a fluent string pass when it changes meaning, addresses the player in a gender the style guide forbids, is in the wrong variety, breaks number-noun agreement, or breaks a placeholder, tag or ICU form. Attached screenshots show where strings with a matching `screenshot` name appear. For dialogue, check that self-references agree with the `speaker`'s gender, second-person forms agree with `addressee`, and lines of one `scene` read as one consistent conversation. `translator_note` is a query the translator already raised for the human reviewer; judge the translation itself, and report an error only if the translation is wrong, not merely because the note exists. When an item has `calibration`, those are similar strings our own linguists annotated ("none" = no errors): match their standard of what counts as an error and how severe.

`span` is the exact erroneous substring of the translation ("" for omissions). `why` is one short English sentence. If there is any error, `suggestion` is the full corrected translation; otherwise "". """

FIX_INSTRUCTION = ("These translations failed automated QA. Fix the listed issues and anything they force you to change; "
                   "keep the rest as it is. Return the full corrected string in `fixed`.")

LINT_ROLE = """You fix English source strings of a mobile game so they can be translated into Arabic correctly. For each item, rewrite `en` to resolve its `issues` while keeping the meaning and every existing placeholder name:
- a count without plural support becomes a plural in the game's syntax using the existing variable, e.g. <<PLURAL>>;
- two or more bare %s/%d become positional %1$s, %2$s;
- a fragment that is concatenated in code becomes one full sentence with named placeholders; say in `why` what the code must change.
`why` is one short sentence for the developer."""

_str = {"type": "string"}


def _obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _items(props):
    return _obj({"items": {"type": "array", "items": _obj(props)}})


T_SCHEMA = _items({"key": _str, "ar": _str, "gulf": _str, "levant": _str, "egypt": _str, "note": _str,
                   "terms": {"type": "array", "items": _obj({"en": _str, "ar": _str})}})
FIX_SCHEMA = _items({"key": _str, "variant": _str, "fixed": _str})
J_SCHEMA = _items({"key": _str, "variant": _str, "suggestion": _str, "errors": {"type": "array", "items": _obj({
    "category": {"type": "string", "enum": ["accuracy", "terminology", "fluency", "style", "locale", "gender",
                                            "variety", "markup", "culture"]},
    "severity": {"type": "string", "enum": list(WEIGHTS)},
    "span": _str, "why": _str})}})
LINT_SCHEMA = _items({"key": _str, "suggested_en": _str, "why": _str})


# ---------- io ----------

def _col(name):
    """Header names are case-insensitive; Unity Localization's CSV export (Key, English(en), Shared Comments) works as-is."""
    n = name.strip().lower()
    return "en" if n.endswith("(en)") or n == "english" else "context" if n == "shared comments" else n


def read_csv(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{_col(k) if k else k: v for k, v in r.items()} for r in csv.DictReader(f)]


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:  # BOM: Excel/Sheets open Arabic correctly
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def is_yes(v):
    return (v or "").strip().lower() in ("y", "yes", "1", "true")


def load_glossary(path):
    return [{"en": r["en"].strip(), "ar": [a.strip() for a in (r.get("ar") or "").split("|") if a.strip()],
             "dnt": (r.get("type") or "").strip().lower() == "dnt", "notes": r.get("notes") or ""}
            for r in read_csv(path) if (r.get("en") or "").strip()]


def glossary_hits(text, terms):
    hits = [t for t in terms if re.search(rf"\b{re.escape(t['en'])}(?:e?s)?\b", text, re.I)]
    # drop terms nested in a longer hit ("Reward" inside "Daily Reward"): overlapping hints hurt Arabic grammar
    return [t for t in hits if not any(t is not o and t["en"].lower() in o["en"].lower() for o in hits)]


def near(text, keys, n, cutoff):
    # ponytail: linear fuzzy scan, fine to ~20k entries; switch to an index (rapidfuzz) beyond that
    return difflib.get_close_matches(text, keys, n=n, cutoff=cutoff)


def n_words(en):
    return len(re.findall(r"[A-Za-z0-9']+", ar_qa.plain(en)))


def fmt(issues):
    return " | ".join(f"{s}:{i}: {m}" for i, s, m in issues)


def resolve_syntax(choice, texts):
    """'icu' or 'smart': as given, or detected from the English strings (majority wins)."""
    if choice != "auto":
        return choice
    found = {s: sum(s in ar_qa.syntax(t) for t in texts) for s in ("icu", "smart")}
    if not any(found.values()):
        print("  note: no plural/select strings in the source; assuming ICU. Pass --syntax smart if the game uses Unity Smart Strings.")
        return "icu"
    pick = max(found, key=found.get)
    print(f"  plural/select syntax: {pick} (detected: ICU {found['icu']}, Smart Strings {found['smart']} strings)")
    return pick


def wilson(k, n, z=1.96):
    """95% interval for a proportion k/n (sound for small n and for k = 0)."""
    if not n:
        return 0.0, 1.0
    p, d = k / n, 1 + z * z / n
    c, h = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


# ---------- cost ----------

# $ per million tokens: input, output, cache read (a 5-minute cache write is 1.25 x input). List prices, Oct 2026.
# ponytail: fallback-model and long-prompt surcharges are ignored; this is a budgeting estimate, not an invoice.
PRICES = {"claude-opus-5-5": (4.00, 20.00, 0.20), "claude-sonnet-5-5": (2.00, 10.00, 0.20),
          "claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-fable-5-1": (10.00, 50.00, 0.25)}
COST_FIELDS = ["date", "command", "model", "calls", "input", "cache_write", "cache_read", "output", "usd"]
_usage, _usage_lock = {}, threading.Lock()


def track(model, inp, out, cache_write=0, cache_read=0, batch=False):
    with _usage_lock:
        u = _usage.setdefault((model, batch), dict.fromkeys(COST_FIELDS[3:8], 0))
        for k, v in (("calls", 1), ("input", inp), ("output", out), ("cache_write", cache_write), ("cache_read", cache_read)):
            u[k] += v or 0


def usd(model, u, batch=False):
    p = PRICES.get(model.removeprefix("anthropic:"))
    if not p:
        return None
    cost = (u["input"] * p[0] + u["cache_write"] * p[0] * 1.25 + u["cache_read"] * p[2] + u["output"] * p[1]) / 1e6
    return cost * (0.5 if batch else 1.0)


def report_cost(out_dir, command):
    """Print this run's token use and estimated cost, and append it to <out>/costs.csv for per-game budgeting."""
    if not _usage:
        print("Cost: no paid AI calls this run (answers came from the cache, or nothing to translate)")
        return
    rows = []
    for (model, batch), u in _usage.items():
        c = usd(model, u, batch)
        print(f"Cost: {model}{' (batch, 50% off)' if batch else ''}: {u['calls']} calls, "
              f"{u['input'] + u['cache_write'] + u['cache_read']:,} input tokens ({u['cache_read']:,} cached), "
              f"{u['output']:,} output tokens -> " + (f"~${c:.2f}" if c is not None else "price unknown (add it to PRICES)"))
        rows.append({"date": time.strftime("%Y-%m-%d %H:%M"), "command": command,
                     "model": model + (" (batch)" if batch else ""), **u, "usd": "" if c is None else f"{c:.4f}"})
    path = Path(out_dir) / "costs.csv"
    write_csv(path, read_csv(path) + rows, COST_FIELDS)
    _usage.clear()


# ---------- models ----------

_clients = {}


def anthropic_client():
    if "anthropic" not in _clients:
        import anthropic  # lazy: qa/score/export/fontcheck run without the SDK
        _clients["anthropic"] = anthropic.Anthropic(max_retries=5)
    return _clients["anthropic"]


def openai_client():
    if "openai" not in _clients:
        from openai import OpenAI  # pip install openai; OPENAI_BASE_URL picks any compatible endpoint
        _clients["openai"] = OpenAI(max_retries=5)
    return _clients["openai"]


def _anthropic_params(model, effort, req):
    system, content, schema = req
    return {"model": model, "max_tokens": 64000,
            "system": [{"type": "text", "text": t, "cache_control": {"type": "ephemeral"}} for t in system],
            "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            "messages": [{"role": "user", "content": content}]}


def _parse_anthropic(msg):
    if msg.stop_reason == "refusal":
        return None
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Output hit max_tokens: lower --batch")
    text = ""
    for b in msg.content:  # after a mid-stream fallback the answer restarts behind a `fallback` block
        if b.type == "fallback":
            text = ""
        elif b.type == "text":
            text += b.text
    return json.loads(text)


def _call_anthropic(model, effort, req):
    with anthropic_client().beta.messages.stream(
        **_anthropic_params(model, effort, req),
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # a safety-classifier decline is retried server-side on Anthropic's recommended model
    ) as stream:
        msg = stream.get_final_message()
    u = msg.usage
    track(model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens)
    return _parse_anthropic(msg)


def _call_openai(model, effort, req):
    # ponytail: `effort` is not forwarded; only reasoning models accept reasoning_effort
    system, content, schema = req
    parts = [{"type": "text", "text": b["text"]} if b["type"] == "text" else
             {"type": "image_url", "image_url": {"url": f"data:{b['source']['media_type']};base64,{b['source']['data']}"}}
             for b in content]
    r = openai_client().chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "\n\n".join(system)}, {"role": "user", "content": parts}],
        response_format={"type": "json_schema", "json_schema": {"name": "result", "schema": schema, "strict": True}})
    if r.usage:
        track("openai:" + model, r.usage.prompt_tokens, r.usage.completion_tokens)
    choice = r.choices[0]
    if getattr(choice.message, "refusal", None):
        return None
    if choice.finish_reason == "length":
        raise RuntimeError("Output hit the length limit: lower --batch")
    return json.loads(choice.message.content)


def _batch_anthropic(model, effort, reqs):
    """Message Batches API: 50% price, usually done within an hour. Server-side fallbacks are not available
    on batches, so a declined request leaves its strings for human review."""
    c = anthropic_client()
    batch = c.messages.batches.create(
        requests=[{"custom_id": k, "params": _anthropic_params(model, effort, r)} for k, r in reqs.items()])
    print(f"  batch {batch.id}: {len(reqs)} requests, polling every 30 s ...")
    while batch.processing_status != "ended":
        time.sleep(30)
        batch = c.messages.batches.retrieve(batch.id)
    out = {}
    for res in c.messages.batches.results(batch.id):
        try:
            if res.result.type != "succeeded":
                raise RuntimeError(res.result.type)
            u = getattr(res.result.message, "usage", None)
            if u:
                track(model, u.input_tokens, u.output_tokens, getattr(u, "cache_creation_input_tokens", 0),
                      getattr(u, "cache_read_input_tokens", 0), batch=True)
            out[res.custom_id] = _parse_anthropic(res.result.message)
        except RuntimeError as e:
            print(f"  ! batch request {res.custom_id}: {e}; its strings go to human review", file=sys.stderr)
    return out


class JobsPending(Exception):
    """Raised in claude-code mode when requests are waiting for Claude Code to answer them."""


def schema_errors(v, s, path="$"):
    """Errors in v against the JSON-schema subset this file uses (object, array, string, enum)."""
    if "enum" in s and v not in s["enum"]:
        return [f"{path}: {v!r} is not one of {s['enum']}"]
    t = s.get("type")
    if t == "object":
        if not isinstance(v, dict):
            return [f"{path}: expected an object"]
        errs = [f"{path}: missing '{k}'" for k in s.get("required", []) if k not in v]
        return errs + [e for k, sub in s.get("properties", {}).items() if k in v for e in schema_errors(v[k], sub, f"{path}.{k}")]
    if t == "array":
        if not isinstance(v, list):
            return [f"{path}: expected an array"]
        return [e for i, x in enumerate(v) for e in schema_errors(x, s["items"], f"{path}[{i}]")]
    if t == "string" and not isinstance(v, str):
        return [f"{path}: expected a string"]
    return []


def _claude_code_jobs(todo, cache_dir, save):
    """claude-code mode: no API call. A valid answer file becomes a cached result; every other request is
    written to <out>/jobs/pending/ for Claude Code (CLAUDE_CODE_MODE.md), and the run pauses with JobsPending.
    Requests are content-hashed, so the re-run asks for exactly the same jobs and picks the answers up."""
    jobs = Path(cache_dir).parent / "jobs"
    for d in ("pending", "answers", "context"):
        (jobs / d).mkdir(parents=True, exist_ok=True)
    kinds = {id(T_SCHEMA): "translate", id(FIX_SCHEMA): "fix", id(J_SCHEMA): "review", id(LINT_SCHEMA): "rewrite"}

    def stash(data, ext, mode="w"):  # shared context (style guide, roles, screenshots) is written once
        p = jobs / "context" / f"{hashlib.sha256(data if mode == 'wb' else data.encode()).hexdigest()[:16]}{ext}"
        if not p.exists():
            p.write_bytes(data) if mode == "wb" else p.write_text(data, encoding="utf-8")
        return f"context/{p.name}"

    for old in (jobs / "pending").glob("*.json"):  # leftovers from an earlier, different run: never worth answering
        if old.stem not in todo:
            old.unlink()
    waiting, bad = 0, []
    for k, (system, content, schema) in todo.items():
        answer, job = jobs / "answers" / f"{k}.json", jobs / "pending" / f"{k}.json"
        if answer.exists():
            try:
                data = json.loads(answer.read_text(encoding="utf-8-sig"))
                errs = schema_errors(data, schema)
            except json.JSONDecodeError as e:
                data, errs = None, [f"not valid JSON ({e})"]
            if not errs:
                save(k, data)
                job.unlink(missing_ok=True)
                continue
            bad.append(f"answers/{answer.name}: {'; '.join(errs[:3])}")
        images = {content[i]["text"].removeprefix("Screenshot ").rstrip(":"):
                  stash(base64.standard_b64decode(content[i + 1]["source"]["data"]),
                        "." + content[i + 1]["source"]["media_type"].split("/")[1], "wb")
                  for i in range(1, len(content) - 1, 2)}
        job.write_text(json.dumps({
            "job": kinds.get(id(schema), "task"), "read_first": [stash(s, ".md") for s in system],
            "task": content[0]["text"], "images": images, "items": json.loads(content[-1]["text"]),
            "answer_file": f"answers/{k}.json", "answer_schema": schema}, ensure_ascii=False, indent=1), encoding="utf-8")
        waiting += 1
    for b in bad:
        print(f"  ! invalid answer, fix it and re-run: {b}", file=sys.stderr)
    if waiting:
        raise JobsPending(f"{waiting} job(s) are waiting for Claude Code in {jobs / 'pending'}")


def call_many(reqs, model, effort, cache_dir, workers=4, batch_api=False):
    """Run (system_blocks, content_blocks, schema) requests; results come back in request order.
    Each result is cached on disk by content hash, so a crashed or repeated run never pays twice."""
    prov, name = model.split(":", 1) if model.startswith(("openai:", "anthropic:")) else (
        ("claude-code", model) if model == "claude-code" else ("anthropic", model))
    keys = [hashlib.sha256(json.dumps([model, effort, r], ensure_ascii=False).encode()).hexdigest()[:32] for r in reqs]
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    done = {k: json.loads((cache / f"{k}.json").read_text(encoding="utf-8")) for k in set(keys) if (cache / f"{k}.json").exists()}
    todo = {k: r for k, r in zip(keys, reqs) if k not in done}

    def save(k, v):
        if v is None:
            print(f"  ! request declined by {model}; its strings go to human review", file=sys.stderr)
            return
        (cache / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
        done[k] = v

    if todo and prov == "claude-code":
        _claude_code_jobs(todo, cache, save)
    elif todo and batch_api and prov == "anthropic":
        for k, v in _batch_anthropic(name, effort, todo).items():
            save(k, v)
    elif todo:
        fn = _call_openai if prov == "openai" else _call_anthropic
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(lambda k: save(k, fn(name, effort, todo[k])), todo))
    return [done.get(k, {"items": []}) for k in keys]


def content(instruction, batch, shots):
    """Instruction, each distinct screenshot the batch uses (labelled by name), then the JSON items."""
    blocks = [{"type": "text", "text": instruction}]
    for name in dict.fromkeys(i["screenshot"] for i in batch if i.get("screenshot")):
        if shots.get(name):
            blocks += [{"type": "text", "text": f"Screenshot {name}:"}, shots[name]]
    return blocks + [{"type": "text", "text": json.dumps(batch, ensure_ascii=False, indent=1)}]


def load_shot(path):
    p = Path(path)
    mt = IMAGE_TYPES.get(p.suffix.lower())
    if not p.is_file() or not mt or p.stat().st_size > 5 * 1024 * 1024:
        print(f"  ! screenshot skipped (missing, not png/jpg/webp/gif, or > 5 MB): {path}", file=sys.stderr)
        return None
    return {"type": "image", "source": {"type": "base64", "media_type": mt,
                                        "data": base64.standard_b64encode(p.read_bytes()).decode()}}


def pack(payload, size):
    """Batches of about `size` items. A scene, or the strings of one screenshot, is never split, so the model sees it whole."""
    # ponytail: a scene longer than `size` becomes one oversized request; split very long scenes in the CSV
    groups = {}
    for i, x in enumerate(payload):
        unit = ("scene", x["scene"]) if x.get("scene") else ("shot", x["screenshot"]) if x.get("screenshot") else ("one", i)
        groups.setdefault(unit, []).append(x)
    batches, cur = [], []
    for g in groups.values():
        if cur and len(cur) + len(g) > size:
            batches.append(cur)
            cur = []
        cur += g
    return batches + [cur] if cur else batches


def ask(ctx, system, instruction, payload, schema, model):
    a = ctx.args
    reqs = [(system, content(instruction, b, ctx.shots), schema) for b in pack(payload, a.batch)]
    return [x for r in call_many(reqs, model, a.effort, ctx.cache, a.workers, a.batch_api) for x in r.get("items", [])]


def load_characters(path):
    return {c["name"].strip().lower(): {"name": c["name"].strip(), "ar": (c.get("ar") or "").strip(),
                                        "gender": (c.get("gender") or "unknown").strip().lower(), "notes": c.get("notes") or ""}
            for c in read_csv(path) if (c.get("name") or "").strip()}


def characters_path(a):
    return Path(a.characters) if a.characters else Path(a.source).parent / "characters.csv"


def who(name, chars):
    """speaker/listener cell -> dict for the model; None when empty."""
    n = (name or "").strip()
    if not n:
        return None
    if n.lower() in RESERVED:
        return {"name": n.lower()}
    return chars.get(n.lower(), {"name": n, "gender": "unknown"})


# ---------- pipeline ----------

def load_context(a):
    cfg = json.loads((HERE / "locales.json").read_text(encoding="utf-8"))
    terms = load_glossary(a.glossary)
    chars = load_characters(characters_path(a))
    known = {t["en"].lower() for t in terms}
    terms += [{"en": c["name"], "ar": [c["ar"]], "dnt": False, "notes": f"character name ({c['gender']})"}
              for c in chars.values() if c["ar"] and c["name"].lower() not in known]  # names stay identical in every line
    tm_rows = read_csv(a.tm)
    tm = {r["en"]: r["ar"] for r in tm_rows if (r.get("variant") or "ar") == "ar"}  # fuzzy examples
    approved = {} if a.no_reuse else {(r["key"], r.get("variant") or "ar", r["en"]): r["ar"] for r in tm_rows if r.get("key")}
    calib = {}
    for c in read_csv(a.calibration):
        calib.setdefault(c["variant"], []).append(c)
    review_terms = dict(cfg["review_terms_en"])
    for c in cfg["locales"].values():
        review_terms.update({p: f"{c['country']}: {why}" for p, why in c.get("extra_review_terms_en", {}).items()})

    src = [r for r in read_csv(a.source) if (r.get("key") or "").strip()]
    keys = [r["key"] for r in src]
    if not src or len(set(keys)) != len(keys):
        sys.exit(f"No rows, or duplicate keys: {sorted({k for k in keys if keys.count(k) > 1})}")
    items, shots, tm_keys = [], {}, list(tm)
    for r in src:
        typ = (r.get("type") or "ui").strip().lower()
        if typ not in TYPES:
            print(f"  ! {r['key']}: unknown type '{typ}', using ui", file=sys.stderr)
            typ = "ui"
        shot = (r.get("screenshot") or "").strip()
        if shot and shot not in shots:
            shots[shot] = load_shot(Path(a.source).parent / shot)
        speaker, listener = who(r.get("speaker"), chars), who(r.get("listener"), chars)
        for p in (speaker, listener):
            if p and p.get("gender") == "unknown":
                print(f"  ! {r['key']}: '{p['name']}' has no gender in characters.csv; Arabic gender agreement is a guess", file=sys.stderr)
        addressee = (r.get("addressee") or "").strip().lower()
        if not addressee and listener:
            addressee = listener["name"] if listener["name"] in RESERVED else listener.get("gender")
        extra = {k: v for k, v in (("scene", (r.get("scene") or "").strip()), ("speaker", speaker), ("listener", listener)) if v}
        items.append({
            "key": r["key"], "type": typ, "context": r.get("context") or "", "en": r["en"], **extra,
            "addressee": addressee if addressee in ("male", "female", "group", "none") else "player",
            "max_len": int(r["max_len"]) if (r.get("max_len") or "").strip().isdigit() else None,
            "overlays": typ in cfg["overlay_types"], "screenshot": shot if shots.get(shot) else "",
            "glossary": [{"en": t["en"], "ar": t["ar"] or [t["en"]], "dnt": t["dnt"], "notes": t["notes"]}
                         for t in glossary_hits(r["en"], terms)],
            "tm": [{"en": k, "ar": tm[k], "similarity": round(difflib.SequenceMatcher(None, r["en"], k).ratio(), 2)}
                   for k in near(r["en"], tm_keys, 3, 0.6)],
        })
    return SimpleNamespace(args=a, cfg=cfg, terms=terms, calib=calib, review_terms=review_terms, items=items, approved=approved,
                           syntax=resolve_syntax(a.syntax, [r["en"] for r in src]),
                           shots=shots, style=(HERE / "style_guide.md").read_text(encoding="utf-8"),
                           cache=Path(a.out) / ".cache")


def calibration_examples(ctx, en, variant, n=3):
    pool = ctx.calib.get(variant, [])
    close = set(near(en, list(dict.fromkeys(c["en"] for c in pool)), n, 0.5))
    return [{"en": c["en"], "translation": c["translation"], "human_annotation": c["mqm"]}
            for c in pool if c["en"] in close][:n]


def pipeline(ctx, model, judge_model):
    """Translate -> rule QA -> fix rule errors -> AI judge. Returns review rows."""
    a, items = ctx.args, ctx.items
    allow = {(a.gender_var, "select")} if a.gender_var else set()
    t_sys = [ctx.style, TRANSLATOR_ROLE + SYNTAX_NOTES[ctx.syntax]
             + (GENDER_VARS[ctx.syntax].format(g=a.gender_var) if a.gender_var else "")]
    # Unchanged strings (same key + English as an approved TM entry, for every variant) skip translation and judging.
    reused = {}
    for it in items:
        texts = {v: ctx.approved.get((it["key"], v, it["en"])) for v in (VARIANTS if it["overlays"] else ["ar"])}
        if all(texts.values()):
            reused[it["key"]] = texts
    todo = [it for it in items if it["key"] not in reused]
    if reused:
        print(f"Reusing {len(reused)} unchanged approved strings from the translation memory ...")
    print(f"Translating {len(todo)} strings with {model} ...")
    got = {t["key"]: t for t in ask(ctx, t_sys, "Translate these strings.", todo, T_SCHEMA, model)} if todo else {}
    got.update({k: {**texts, "note": ""} for k, texts in reused.items()})

    rows = []
    for it in items:
        t = got.get(it["key"], {})
        src_flags = ar_qa.lint_source(it["en"]) + [("CULTURE_SOURCE", "warn", why) for p, why in ctx.review_terms.items()
                                                   if re.search(p, it["en"], re.I)]
        for v in (VARIANTS if it["overlays"] else ["ar"]):
            rows.append({"key": it["key"], "variant": v, "type": it["type"], "context": it["context"],
                         "scene": it.get("scene", ""), "speaker": (it.get("speaker") or {}).get("name", ""),
                         "listener": (it.get("listener") or {}).get("name", ""),
                         "screenshot": it["screenshot"], "en": it["en"], "final": t.get(v, ""), "note": t.get("note", ""),
                         "pv": PROMPT_VERSION, "_it": it, "_src": src_flags, "_terms": t.get("terms", []),
                         "_reused": it["key"] in reused})

    def dialogue(r):
        return {k: r["_it"][k] for k in ("scene", "speaker", "listener") if k in r["_it"]}

    def qa(r, text=None):
        return ar_qa.check(r["en"], r["final"] if text is None else text, r["_it"]["max_len"], r["_it"]["glossary"],
                           allow, ctx.syntax)

    def n_err(r, text=None):
        return sum(s == "error" for _, s, _ in qa(r, text))

    # Fix only rule-QA errors: they are mechanically verifiable, so a fix is kept only if it lowers the error count.
    for r in rows:
        r["_raw_errors"] = n_err(r)
    broken = [r for r in rows if r["_raw_errors"]]
    if broken:
        print(f"Fixing {len(broken)} strings that failed rule QA ...")
        fixes = {(f["key"], f["variant"]): f["fixed"] for f in ask(ctx, t_sys, FIX_INSTRUCTION, [
            {"key": r["key"], "variant": r["variant"], "type": r["type"], "context": r["context"], "en": r["en"],
             "addressee": r["_it"]["addressee"], **dialogue(r), "screenshot": r["screenshot"], "current": r["final"],
             "issues": [f"{i}: {m}" for i, s, m in qa(r) if s == "error"]} for r in broken], FIX_SCHEMA, model)}
        for r in broken:
            fixed = fixes.get((r["key"], r["variant"]))
            if fixed and n_err(r, fixed) < r["_raw_errors"]:
                r["draft"], r["final"] = r["final"], fixed

    fresh = [r for r in rows if not r["_reused"]]
    print(f"Judging {len(fresh)} translations with {judge_model} ...")
    payload = []
    for r in fresh:
        j = {"key": r["key"], "variant": r["variant"], "type": r["type"], "context": r["context"], "en": r["en"],
             "addressee": r["_it"]["addressee"], **dialogue(r), "glossary": r["_it"]["glossary"],
             "screenshot": r["screenshot"], "translation": r["final"]}
        if r["note"]:
            j["translator_note"] = r["note"]
        ex = calibration_examples(ctx, r["en"], r["variant"])
        if ex:
            j["calibration"] = ex
        payload.append(j)
    verdicts = {(j["key"], j["variant"]): j for j in ask(ctx, [ctx.style, JUDGE_ROLE + SYNTAX_NOTES[ctx.syntax]], "Annotate these translations.",
                                                        payload, J_SCHEMA, judge_model)} if payload else {}
    inconsistent = consistency(rows)
    for r in rows:
        j = verdicts.get((r["key"], r["variant"]), {})
        r["judge"] = " | ".join(f"{e['severity']}/{e['category']}: «{e['span']}» {e['why']}" for e in j.get("errors", []))
        r["suggestion"] = j.get("suggestion", "")
        target = qa(r) + inconsistent.get((r["key"], r["variant"]), [])
        r["qa"] = fmt(r["_src"] + target)
        if r["_reused"]:  # already approved by a linguist: stays approved unless the rules now find an error
            ok = not any(s == "error" for _, s, _ in target)
            r["status"], r["approved"] = ("tm_reused", "y") if ok else ("needs_human", "")
        else:
            r["status"] = "needs_human" if (r["qa"] or r["judge"] or r["note"] or not j) else "auto_pass"
    return rows


def consistency(rows):
    """Xbench-style check within each variant and speaker/listener pair (so gendered dialogue differences are allowed):
    the same English translated differently, or different English sharing one Arabic. Returns {(key, variant): issues}."""
    out = {}
    for src, tgt, msg in (("en", "final", "same English translated differently in"),
                          ("final", "en", "different English with the same Arabic in")):
        groups = {}
        for r in rows:
            if (r.get("final") or "").strip():
                groups.setdefault((r["variant"], r.get("speaker", ""), r.get("listener", ""), r[src].strip()), []).append(r)
        for g in groups.values():
            if len({r[tgt].strip() for r in g}) > 1:
                keys = ", ".join(sorted({r["key"] for r in g}))
                for r in g:
                    out.setdefault((r["key"], r["variant"]), []).append(("INCONSISTENT", "warn", f"{msg} {keys}"))
    return out


def mark_audit(rows, seed):
    """Random MQM audit sample: >= 1,000 source words per variant, scored later by an independent linguist."""
    rng = random.Random(seed)
    for v in VARIANTS:
        pool = [r for r in rows if r["variant"] == v]
        rng.shuffle(pool)
        words = 0
        for r in pool:
            if words >= 1000:
                break
            r["audit"], words = "Y", words + n_words(r["en"])


def glossary_candidates(rows, terms):
    known, cands = {t["en"].lower() for t in terms}, {}
    for r in rows:
        if r["variant"] == "ar":
            for t in r["_terms"]:
                en = t["en"].strip()
                if en and en.lower() not in known:
                    c = cands.setdefault(en.lower(), {"en": en, "ar": t["ar"], "count": 0, "keys": []})
                    c["count"] += 1
                    c["keys"].append(r["key"])
    return [{**c, "keys": " ".join(c["keys"])} for c in sorted(cands.values(), key=lambda c: -c["count"])]


def print_summary(rows):
    for v in VARIANTS:
        vr = [r for r in rows if r["variant"] == v]
        if vr:
            fresh = [r for r in vr if r["status"] != "tm_reused"]
            print(f"  {v:7} {len(vr):5} strings | reused {len(vr) - len(fresh):5} | needs_human "
                  f"{sum(r['status'] == 'needs_human' for r in vr):5} | judge-estimated MQM "
                  + (f"{mqm(fresh, 'judge')['score']:.1f} on new strings (triage only, not the gate)" if fresh else "-"))


def cmd_translate(a):
    ctx = load_context(a)
    if a.judge_model == a.model:
        print("  note: the judge is the translator's own model; a different provider judges more strictly (--judge-model openai:<model>)")
    rows = pipeline(ctx, a.model, a.judge_model)
    mark_audit(rows, a.seed)
    out = Path(a.out)
    write_csv(out / "review.csv", rows, REVIEW_FIELDS)
    print(f"\nWrote {out / 'review.csv'}")
    cands = glossary_candidates(rows, ctx.terms)
    if cands:
        write_csv(out / "glossary_candidates.csv", cands, ["en", "ar", "count", "keys", "approved"])
        print(f"Wrote {out / 'glossary_candidates.csv'}: {len(cands)} new terms; a linguist sets approved=y, export merges them")
    print_summary(rows)
    report_cost(a.out, "translate")


def cmd_bakeoff(a):
    a.no_reuse = True  # every model must translate every string
    ctx = load_context(a)
    if a.judge_model in a.models:
        print(f"  note: judge {a.judge_model} is also a candidate; judges favour their own output, prefer a neutral judge")
    rows, systems = [], {}
    for letter, m in zip("ABCDEFGHIJ", a.models):
        rs = pipeline(ctx, m, a.judge_model)
        for r in rs:
            r["system"], r["audit"] = letter, "Y"  # every row is scored, so every system is judged on the same strings
        rows += rs
        systems[letter] = m
    random.Random(a.seed).shuffle(rows)  # blind: the linguist sees letters in mixed order
    out = Path(a.out)
    write_csv(out / "review.csv", rows, ["system"] + REVIEW_FIELDS)
    (out / "systems.json").write_text(json.dumps(systems, indent=1), encoding="utf-8")
    print(f"\nWrote {out / 'review.csv'} (blind; model names are in systems.json - keep it from the linguist)")
    print("Automatic signals only. The decision is the linguist's `mqm` column -> `score`:")
    for letter, m in systems.items():
        rs = [r for r in rows if r["system"] == letter]
        print(f"  {letter} {m}: rule errors before fixing {sum(r['_raw_errors'] for r in rs)}, "
              f"needs_human {sum(r['status'] == 'needs_human' for r in rs)}/{len(rs)}, judge-estimated MQM {mqm(rs, 'judge')['score']:.1f}")
    report_cost(a.out, "bakeoff")


# ---------- lint / qa / score / export / fontcheck ----------

def cmd_lint(a):
    rows = [r for r in read_csv(a.source) if (r.get("key") or "").strip()]
    chars, flagged, counts = load_characters(characters_path(a)), [], {}
    for r in rows:
        issues = ar_qa.lint_source(r["en"])
        is_dialogue = (r.get("type") or "").strip().lower() == "dialogue"
        speaker, listener = (r.get("speaker") or "").strip(), (r.get("listener") or "").strip()
        if not (r.get("context") or "").strip():
            issues.append(("SRC_NO_CONTEXT", "warn", "No context: say where it appears and what it does"))
        if is_dialogue and not speaker:
            issues.append(("SRC_NO_SPEAKER", "warn", "Dialogue without `speaker`: Arabic needs the speaker's gender for 'I'"))
        for name in (speaker, listener):
            if name and name.lower() not in RESERVED:
                c = chars.get(name.lower())
                if not c:
                    issues.append(("SRC_UNKNOWN_CHARACTER", "warn", f"'{name}' is not in characters.csv (name, ar, gender, notes)"))
                elif c["gender"] not in ("female", "male"):
                    issues.append(("SRC_CHARACTER_GENDER", "warn", f"'{name}' has no gender in characters.csv"))
        if (is_dialogue and re.search(r"\byou(?:r|rs|rself)?\b", r["en"], re.I) and "select" not in r["en"]
                and listener.lower() in ("", "player") and (r.get("addressee") or "player").strip().lower() == "player"):
            issues.append(("SRC_GENDER", "warn", "Talks to the player: pass a gender variable and translate with --gender-var"))
        r["issues"] = fmt(issues)
        for i, _, _ in issues:
            counts[i] = counts.get(i, 0) + 1
        if any(i in ("SRC_FRAGMENT", "SRC_BARE_PRINTF", "SRC_COUNT_NO_PLURAL") for i, _, _ in issues):
            flagged.append(r)
    if a.suggest and flagged:
        print(f"Asking {a.model} for rewrites of {len(flagged)} strings ...")
        payload = [{"key": r["key"], "en": r["en"], "context": r.get("context") or "", "issues": r["issues"]} for r in flagged]
        role = LINT_ROLE.replace("<<PLURAL>>", PLURAL_EXAMPLES[resolve_syntax(a.syntax, [r["en"] for r in rows])])
        reqs = [([role], content("Rewrite these source strings.", payload[i:i + 50], {}), LINT_SCHEMA)
                for i in range(0, len(payload), 50)]
        try:
            sugg = {s["key"]: s for res in call_many(reqs, a.model, a.effort, Path(a.out) / ".cache", a.workers) for s in res["items"]}
        except JobsPending:
            raise  # claude-code mode: pause for Claude Code, not "rewrites failed"
        except Exception as e:  # rewrites are optional; the lint report must still be written
            print(f"  ! AI rewrites skipped ({type(e).__name__}: {e})", file=sys.stderr)
            sugg = {}
        for r in flagged:
            r["suggested_en"], r["why"] = sugg.get(r["key"], {}).get("suggested_en", ""), sugg.get(r["key"], {}).get("why", "")
        report_cost(a.out, "lint")
    out = Path(a.out) / "source_lint.csv"
    write_csv(out, rows, ["key", "en", "type", "scene", "speaker", "listener", "context", "issues", "suggested_en", "why"])
    print(f"{len(rows)} strings, {len(flagged)} need source changes before translation -> {out}")
    for i, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:5}  {i}")
    return 1 if flagged else 0


def cmd_qa(a):
    rows, terms = read_csv(a.csv), load_glossary(a.glossary)
    allow = {(a.gender_var, "select")} if a.gender_var else set()
    syn, counts = resolve_syntax(a.syntax, [r["en"] for r in rows]), {}
    inconsistent = consistency([{**r, "key": r.get("key") or str(n), "variant": "ar", "final": r.get(_col(a.col)) or ""}
                                for n, r in enumerate(rows)])
    for n, r in enumerate(rows):
        ml = (r.get("max_len") or "").strip()
        issues = ar_qa.lint_source(r["en"]) + ar_qa.check(r["en"], r.get(_col(a.col)) or "", int(ml) if ml.isdigit() else None,
                                                          glossary_hits(r["en"], terms), allow, syn)
        issues += inconsistent.get((r.get("key") or str(n), "ar"), [])
        r["qa"] = fmt(issues)
        for i, s, _ in issues:
            counts[(s, i)] = counts.get((s, i), 0) + 1
    out = Path(a.csv).with_suffix(".qa.csv")
    write_csv(out, rows, list(dict.fromkeys(list(rows[0]) + ["qa"])) if rows else ["qa"])
    bad = sum(1 for r in rows if "error:" in r["qa"])
    print(f"{len(rows)} strings, {bad} with errors -> {out}")
    for (s, i), n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:5}  {s:5}  {i}")
    return 1 if bad else 0


def mqm(rows, col):
    """MQM raw score = 100 * (1 - penalty / source words), weights 1/5/25."""
    words = sum(n_words(r["en"]) for r in rows)
    sevs = [s for r in rows for s in SEV.findall((r.get(col) or "").lower())]
    penalty = sum(WEIGHTS[s] for s in sevs)
    defects = sum(1 for r in rows if SEV.search((r.get(col) or "").lower()))
    return {"strings": len(rows), "words": words, "penalty": penalty, "critical": sevs.count("critical"),
            "score": 100 * (1 - penalty / words) if words else 0.0, "defects": defects,
            "defect_upper95": wilson(defects, len(rows))[1]}


def verdict(m, pending):
    if pending:
        return f"INCOMPLETE ({pending} audit rows not annotated)"
    if m["words"] < 1000:
        return "SAMPLE TOO SMALL (<1000 words)"
    return "PASS" if m["score"] >= 99 and m["critical"] == 0 else "FAIL"


def judge_agreement(rows):
    """How far the AI judge can be trusted, measured against your linguists' annotations."""
    has = lambda r, c: bool(SEV.search((r.get(c) or "").lower()))
    print("\nAI judge vs your linguists:")
    for typ in sorted({r["type"] for r in rows}):
        rs = [r for r in rows if r["type"] == typ]
        clean = [r for r in rs if not has(r, "judge")]
        agree = sum(not has(r, "mqm") for r in clean)
        human_found = [r for r in rs if has(r, "mqm")]
        lo = wilson(agree, len(clean))[0]
        advice = ("auto_pass strings of this type can skip revision" if len(clean) >= 300 and lo >= 0.99
                  else "keep revising auto_pass strings (needs >= 300 judge-clean strings at >= 99%)")
        print(f"  {typ:9} judge-clean that humans also found clean {agree}/{len(clean)} (>= {lo:.1%}) | judge caught "
              f"{sum(has(r, 'judge') for r in human_found)}/{len(human_found)} human-found errors | {advice}")


def save_calibration(rows, path):
    old = read_csv(path)
    seen = {(c["en"], c["variant"], c["translation"]) for c in old}
    new = {}
    for r in rows:
        k = (r["en"], r["variant"], r["final"])
        if k not in seen:
            new[k] = {"en": r["en"], "variant": r["variant"], "type": r["type"], "translation": r["final"], "mqm": r["mqm"]}
    if new:
        write_csv(path, old + list(new.values()), ["en", "variant", "type", "translation", "mqm"])
        print(f"Saved {len(new)} human-annotated strings to {path}; the AI judge uses them as examples next run")


def cmd_score(a):
    rows, ok = read_csv(a.review), True
    names = json.loads((Path(a.review).parent / "systems.json").read_text(encoding="utf-8")) \
        if (Path(a.review).parent / "systems.json").exists() else {}
    groups = sorted({(r.get("system") or "", r["variant"]) for r in rows},
                    key=lambda g: (g[0], VARIANTS.index(g[1]) if g[1] in VARIANTS else 9))
    for sysid, v in groups:
        audit = [r for r in rows if (r.get("system") or "", r["variant"]) == (sysid, v) and r.get("audit") == "Y"]
        if not audit:
            continue
        done = [r for r in audit if (r.get("mqm") or "").strip()]  # "none" = reviewed, no errors
        m, est = mqm(done, "mqm"), mqm(done, "judge")
        result = verdict(m, len(audit) - len(done))
        ok &= result == "PASS"
        label = f"{sysid} {names.get(sysid, '')} | " if sysid else ""
        print(f"{label}{v:7} MQM {m['score']:6.2f} | {m['words']} words, penalty {m['penalty']}, critical {m['critical']} | "
              f"strings with errors {m['defects']}/{m['strings']} (95% upper bound {m['defect_upper95']:.1%}) | "
              f"judge said {est['score']:.2f} on same rows | {result}")
    annotated = [r for r in rows if (r.get("mqm") or "").strip()]
    if annotated:
        judge_agreement(annotated)
        save_calibration(annotated, a.calibration)
    return 0 if ok else 1


def cmd_export(a):
    cfg = json.loads((HERE / "locales.json").read_text(encoding="utf-8"))
    allow = {(a.gender_var, "select")} if a.gender_var else set()
    rows, blocking, by_key = read_csv(a.review), 0, {}
    syn = resolve_syntax(a.syntax, [r["en"] for r in rows])
    for r in rows:
        errs = [x for x in ar_qa.check(r["en"], r["final"], allow=allow, syntax_=syn) if x[1] == "error"]
        if errs:
            blocking += 1
            print(f"  {r['key']}/{r['variant']}: {fmt(errs)}")
        by_key.setdefault(r["key"], {"en": r["en"]})[r["variant"]] = r["final"]
    out_rows, hits = [], {}
    for k, d in by_key.items():
        row = {"key": k, "en": d["en"], "ar": d.get("ar", "")}
        for loc, c in cfg["locales"].items():
            row[loc] = text = d.get(c.get("overlay") or "ar") or d.get("ar", "")
            for f in cfg["forbidden_ar"] + c.get("extra_forbidden_ar", []):
                if re.search(f["pattern"], text):
                    hits.setdefault((k, f["severity"], f["why"]), []).append(loc)
        out_rows.append(row)
    for (k, sev, why), locs in hits.items():
        print(f"  {k} {sev}: {why} [{', '.join(locs)}]")
        blocking += sev == "error"
    for (k, v), issues in sorted(consistency(rows).items()):
        print(f"  {k}/{v} warn: {issues[0][2]}")
    unapproved = sum(not is_yes(r.get("approved")) for r in rows)
    if unapproved:
        print(f"  note: {unapproved} rows not marked approved by a linguist")
    if blocking and not a.force:
        sys.exit(f"{blocking} blocking issues. Fix `final` in {a.review}, or pass --force for an internal test build.")
    out = Path(a.out) / "strings.csv"
    write_csv(out, out_rows, ["key", "en", "ar"] + list(cfg["locales"]))
    print(f"Wrote {out} ({len(out_rows)} keys x {len(cfg['locales'])} countries)")

    # TM entries are keyed by (key, variant, English): the next run reuses them for unchanged strings
    tm = {(t.get("key") or "", t.get("variant") or "ar", t["en"]): t["ar"] for t in read_csv(a.tm)}
    new = {(r["key"], r["variant"], r["en"]): r["final"] for r in rows if r["final"] and is_yes(r.get("approved"))}
    if new:
        tm.update(new)
        write_csv(a.tm, [{"key": k, "variant": v, "en": en, "ar": ar} for (k, v, en), ar in tm.items()],
                  ["key", "variant", "en", "ar"])
        print(f"Added/updated {len(new)} approved strings in {a.tm}")
    gl = read_csv(a.glossary)
    known = {g["en"].lower() for g in gl}
    add = [{"en": c["en"], "ar": c["ar"], "type": "term", "status": "approved", "notes": f"from {c['keys']}"}
           for c in read_csv(Path(a.review).parent / "glossary_candidates.csv")
           if is_yes(c.get("approved")) and c["en"].lower() not in known]
    if add:
        write_csv(a.glossary, gl + add, ["en", "ar", "type", "status", "notes"])
        print(f"Added {len(add)} approved terms to {a.glossary}")


PSEUDO_MAP = dict(zip("abcdefghijklmnopqrstuvwxyz", "ابجدهوزحطيكلمنسعفصقرشتثخذض"))
PSEUDO_KEEP = re.compile(r"(</?[A-Za-z][^<>]*>|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXoc@]|\\n"
                         r"|\{\s*[\w.]+\s*(?:,\s*\w+\s*,?|:\w+(?:\([^)]*\))?:)?"
                         r"|(?:\b(?:zero|one|two|few|many|other|male|female)|=\d+)\s*\{|[{}#|])")


def pseudo(s):
    """Fake Arabic for layout tests: real Arabic letters (so shaping, RTL and bidi are exercised), ~30% longer,
    wrapped in [ ] to reveal truncation; placeholders, tags and plural/select syntax are kept intact."""
    def word(m):
        w = "".join(PSEUDO_MAP.get(c, c) for c in m.group().lower())
        return w + w[:math.ceil(len(w) * 0.3)]
    parts = PSEUDO_KEEP.split(s)
    text = "".join(p if i % 2 else re.sub(r"[A-Za-z]+", word, p).replace("?", "؟").replace(",", "،")
                   for i, p in enumerate(parts))
    return "[" + pad_smart_plurals(text) + "]"


def pad_smart_plurals(s):
    """Smart Strings plurals with fewer than Arabic's 6 forms can throw at runtime: fill zero|one|two|few|many|other
    from the English one|other forms. (ICU falls back to `other` by itself.)"""
    for m in reversed(list(ar_qa.SMART_PLURAL.finditer(s))):
        depth, i, cuts = 1, m.end(), []
        while i < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[i], 0)
            if s[i] == "|" and depth == 1:
                cuts.append(i)
            i += 1
        bounds = [m.end()] + [c + 1 for c in cuts]
        forms = [s[b:e] for b, e in zip(bounds, cuts + [i - 1])]
        if len(forms) < 6:
            forms = [forms[-1], forms[0]] + [forms[-1]] * 4
            s = s[:m.end()] + "|".join(forms) + s[i - 1:]
    return s


def cmd_pseudo(a):
    cfg = json.loads((HERE / "locales.json").read_text(encoding="utf-8"))
    rows = [r for r in read_csv(a.source) if (r.get("key") or "").strip()]
    out_rows = [{"key": r["key"], "en": r["en"], **dict.fromkeys(["ar", *cfg["locales"]], pseudo(r["en"]))} for r in rows]
    out = Path(a.out) / "pseudo_strings.csv"
    write_csv(out, out_rows, ["key", "en", "ar"] + list(cfg["locales"]))
    print(f"Wrote {out}: {len(out_rows)} fake-Arabic strings in the strings.csv layout. Import them like real strings to test "
          "right-to-left layout, letter joining, truncation ([ ] must stay visible) and plurals before translating.")


def presentation_forms(chars):
    """Contextual forms (U+FB50-FDFF, U+FE70-FEFC) that shaping can produce from these letters, incl. lam-alef."""
    out = set()
    for cp in [*range(0xFB50, 0xFE00), *range(0xFE70, 0xFEFD)]:
        d = unicodedata.decomposition(chr(cp)).split()
        if len(d) < 2 or d[0] not in ("<isolated>", "<final>", "<initial>", "<medial>"):
            continue
        base = [chr(int(x, 16)) for x in d[1:]]
        lam_alef = len(base) == 2 and base[0] == "ل" and base[1] in "آأإا"
        if (len(base) == 1 or lam_alef) and all(b in chars for b in base):
            out.add(chr(cp))
    return out


def cmd_fontcheck(a):
    from fontTools.ttLib import TTFont  # pip install fonttools
    rows = read_csv(a.strings)
    cols = [c for c in (rows[0] if rows else {}) if c == "ar" or c.startswith("ar-")]
    used = {ch for r in rows for c in cols for ch in ar_qa.plain(r.get(c) or "") if not ch.isspace()}
    need = used | (presentation_forms(used) if a.shaped else set())
    cmap = TTFont(a.font).getBestCmap()
    missing = sorted(ch for ch in need if ord(ch) not in cmap)
    print(f"{len(need)} characters needed ({len(used)} used{' + contextual forms for pre-shaping' if a.shaped else ''}); "
          f"{len(missing)} missing from {a.font}")
    for ch in missing:
        print(f"  U+{ord(ch):04X} {unicodedata.name(ch, '(newer than this Python Unicode table, e.g. a 2025-26 currency sign)')}")
    if any(cp not in cmap for cp in range(0x2066, 0x206A)):
        print("  note: font lacks bidi isolates U+2066-2069; in TextMeshPro add zero-width glyphs or strip them at runtime")
    return 1 if missing else 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252, which cannot print Arabic
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    run = argparse.ArgumentParser(add_help=False)  # options shared by translate and bakeoff
    run.add_argument("source")
    run.add_argument("--glossary", default=str(HERE / "glossary.csv"))
    run.add_argument("--tm", default=str(HERE / "tm.csv"))
    run.add_argument("--calibration", default=str(HERE / "calibration.csv"))
    run.add_argument("--characters", help="default: characters.csv next to the source CSV")
    run.add_argument("--no-reuse", action="store_true", help="retranslate unchanged approved strings too (e.g. after a style-guide change)")
    run.add_argument("--judge-model", default="claude-opus-5-5", help="e.g. openai:<model> for a different provider")
    run.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    run.add_argument("--batch", type=int, default=25, help="strings per request (related strings share context)")
    run.add_argument("--workers", type=int, default=4)
    run.add_argument("--batch-api", action="store_true", help="Claude Message Batches: 50%% price, results usually within 1 h")
    run.add_argument("--gender-var", help="ICU variable the game passes for player gender, e.g. player_gender")
    run.add_argument("--syntax", default="auto", choices=["auto", "icu", "smart"], help="plural/select syntax: ICU or Unity Smart Strings")
    run.add_argument("--seed", type=int, default=42)
    t = sub.add_parser("translate", parents=[run])
    t.add_argument("--model", default="claude-opus-5-5")
    t.add_argument("--out", default="out")
    b = sub.add_parser("bakeoff", parents=[run])
    b.add_argument("--models", nargs="+", required=True, help="e.g. claude-opus-5-5 openai:<model>")
    b.add_argument("--out", default="out/bakeoff")
    li = sub.add_parser("lint")
    li.add_argument("source")
    li.add_argument("--out", default="out")
    li.add_argument("--suggest", action="store_true", help="ask the model for rewritten English")
    li.add_argument("--characters", help="default: characters.csv next to the source CSV")
    li.add_argument("--model", default="claude-opus-5-5")
    li.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    li.add_argument("--syntax", default="auto", choices=["auto", "icu", "smart"], help="plural/select syntax: ICU or Unity Smart Strings")
    li.add_argument("--workers", type=int, default=4)
    q = sub.add_parser("qa")
    q.add_argument("csv")
    q.add_argument("--col", default="ar")
    q.add_argument("--glossary", default=str(HERE / "glossary.csv"))
    q.add_argument("--syntax", default="auto", choices=["auto", "icu", "smart"], help="plural/select syntax: ICU or Unity Smart Strings")
    q.add_argument("--gender-var")
    s = sub.add_parser("score")
    s.add_argument("review")
    s.add_argument("--calibration", default=str(HERE / "calibration.csv"))
    e = sub.add_parser("export")
    e.add_argument("review")
    e.add_argument("--out", default="out")
    e.add_argument("--tm", default=str(HERE / "tm.csv"))
    e.add_argument("--glossary", default=str(HERE / "glossary.csv"))
    e.add_argument("--gender-var")
    e.add_argument("--syntax", default="auto", choices=["auto", "icu", "smart"], help="plural/select syntax: ICU or Unity Smart Strings")
    e.add_argument("--force", action="store_true")
    f = sub.add_parser("fontcheck")
    f.add_argument("strings")
    f.add_argument("--font", required=True)
    f.add_argument("--shaped", action="store_true", help="text is pre-shaped (RTLTMPro/ArabicSupport): need presentation forms")
    ps = sub.add_parser("pseudo")
    ps.add_argument("source")
    ps.add_argument("--out", default="out")
    a = p.parse_args(argv)
    try:
        return {"translate": cmd_translate, "bakeoff": cmd_bakeoff, "lint": cmd_lint, "qa": cmd_qa, "score": cmd_score,
                "export": cmd_export, "fontcheck": cmd_fontcheck, "pseudo": cmd_pseudo}[a.cmd](a)
    except JobsPending as e:
        cmd = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:]))
        print(f"\nPAUSED: {e}. No API key or credits used.\n"
              f"Open Claude Code and say:\n"
              f"  Follow {Path(__file__).resolve().with_name('CLAUDE_CODE_MODE.md')} for this command: {cmd}\n"
              f"Claude Code answers the jobs and re-runs the command until it finishes (usually 2-3 rounds).")
        return 3


if __name__ == "__main__":
    sys.exit(main() or 0)
