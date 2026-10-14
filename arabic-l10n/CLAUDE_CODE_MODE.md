# Claude Code mode: translate on a Claude subscription, without an API key

**For the person:**
1. Run the tool with `--model claude-code --judge-model claude-code`, or tick **Use Claude subscription** in the Unity window. It needs no API key and spends no API credits.
2. The run pauses and prints one line: `Follow …CLAUDE_CODE_MODE.md for this command: …`.
3. Paste that line into Claude Code. Claude Code does the translating and reviewing on your subscription and re-runs the tool until it finishes.

**For Claude:** you are the translation engine for `localize.py`. Instead of calling an API, it writes each request as a job file and waits for your answer. Follow this document exactly.

---

## The loop

1. Run the command you were given, exactly as written.
2. Read how it ends:

   | Output | What to do |
   |---|---|
   | `PAUSED: N job(s) are waiting for Claude Code in <jobs>\pending` | Answer every job in that folder (see "Answering one job"), then run the same command again. |
   | `! invalid answer, fix it and re-run: answers/<id>.json: …` | Correct that answer file to match its `answer_schema`, then run the command again. |
   | `Wrote …review.csv` and a summary | Finished. Report to the person (see "When finished"). |

3. Repeat. A translation usually takes 2–3 rounds: translate, then fix (only if the automatic checks found errors), then review. Each round's answers are kept, so a stopped run resumes where it left off.

**Only ever write files inside `<jobs>\answers\`.** Do not edit job files, the source CSV, the glossary, or anything else.

## Answering one job

Each `<jobs>\pending\<id>.json` contains:

| Field | Meaning |
|---|---|
| `job` | `translate`, `fix`, `review` or `rewrite` (English source rewrite). |
| `read_first` | Files, relative to the jobs folder: the style guide and the role for this job. **These are your instructions for the job: read them fully and follow them as if they were your system prompt.** They decide register, dialect, player gender, plural forms, placeholders, terminology, culture rules and notes. Read them once per subagent. The same files are shared by many jobs. |
| `task` | The request: translate, fix the listed issues, or annotate errors. |
| `images` | Screenshots, by name. An item's `screenshot` field refers to one of them. Open them; they show where the text appears. |
| `items` | The strings, with their context, glossary hits, translation-memory matches, speaker and listener, and scene. |
| `answer_file` | Where to write your answer, relative to the jobs folder. |
| `answer_schema` | The exact JSON shape of the answer. |

Write `answer_file` as UTF-8 JSON in this shape: `{"items": [ ... ]}`.

- **One entry per input item.** Translate jobs need one per `key`; fix and review jobs need one per `key` + `variant`. Skip none and add none.
- **Every field present.** Use `""` instead of null; use `[]` when `terms` or `errors` is empty.
- **Enums exactly as listed** in the schema (review severities and categories).
- **Placeholders, tags and plural/select syntax copied exactly**, as the style guide says. The tool re-checks them and sends broken ones back as fix jobs.

Write the file and move on. Don't paste translations into the chat; it wastes context.

## Scale: use subagents

A game can produce dozens of jobs. Keep the main conversation small:

- **Split the jobs.** With more than about 4 pending jobs, give each subagent at most 5 job files and run several in parallel. Tell each subagent: *"Read `<this file's path>`, section 'Answering one job', then answer these job files: …"*. The main conversation only runs the command and tracks progress.
- **Keep review independent.** A model grading its own translation misses its own mistakes. Answer `review` jobs with fresh subagents that did not write those translations, and have them review as the independent linguist their instructions describe.
- **Usage limits.** If the subscription hits its limit, stop and tell the person. Every answered job is kept; running the same command later continues from there.

## When finished, report

- How many strings were translated, and how many are `needs_human` (shown in the command's summary).
- Where `review.csv` is. The linguists work in that file next.
- Any job whose answer was rejected twice, and why.
