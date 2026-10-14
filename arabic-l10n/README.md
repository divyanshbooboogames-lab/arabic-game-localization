# Arabic localization pipeline (13 Middle East markets)

The pipeline produces **one MSA master string table for all 13 countries**, plus Gulf, Levant and Egypt dialect versions for push, ad and store text. Everything else that differs by country (digits, calendar, currency, weekend, legal rules, content flags) lives in `locales.json`. The research behind each decision is in `../reports/Arabic game localization by country.md`.

"99%" here means an **MQM score of at least 99 with zero critical errors**. An independent native linguist measures it on at least 1,000 random source words per variant. The machine steps make that bar reachable, but only humans certify it.

## Setup

```bash
pip install anthropic fonttools
```

Then set `ANTHROPIC_API_KEY`. For a reviewer or a bake-off candidate from another provider, also install `openai` and set `OPENAI_API_KEY`. Setting `OPENAI_BASE_URL` points it at any OpenAI-compatible endpoint, for example Gemini at `https://generativelanguage.googleapis.com/v1beta/openai/` with your Gemini key.

To see what is wrong with your current Arabic today, run QA on it:

```bash
python localize.py qa current_ar.csv --col ar
```

## No API key? Use your Claude subscription

Run the tool with `--model claude-code --judge-model claude-code`, or tick **Use Claude subscription** in Unity (it is on by default there). The run works like this:

1. The run makes no API calls. It writes the work as job files and pauses.
2. It prints one line that starts with `Follow …CLAUDE_CODE_MODE.md`.
3. Paste that line into Claude Code. Claude Code translates, sends review jobs to a separate subagent so the reviewer is independent, and re-runs the tool until `review.csv` is written. That usually takes 2–3 rounds.

Everything after that is the same as API mode: checks, fixes, review sheet, scoring and export. Unchanged strings are still reused, so later releases only send new text.

**Limits:**
- Big games use real subscription usage. If Claude Code hits a limit, run the same command later. Answered jobs are kept, so it continues where it stopped.
- Someone has to paste the line into Claude Code; there's no unattended overnight run.

The details are in `CLAUDE_CODE_MODE.md`.

## Plural syntax: ICU or Unity Smart Strings

Both are supported. Plurals and gender choices can be written in either syntax:

- **ICU:** `{count, plural, one {...} other {...}}`
- **Unity Smart Strings:** `{count:plural:...|...}` and `{player_gender:choose(female):...|...}`

By default (`--syntax auto`, or **Plural syntax: Auto-detect** in Unity) the tool detects the syntax from the English strings. The translator, reviewer and checks then all use that syntax, and Arabic always gets all 6 plural forms. If the English has no plurals yet, the tool assumes ICU. Pass `--syntax smart` if your game uses Unity Localization's Smart Strings. Mixing the two syntaxes in one string is blocked at export.

## Use it from inside Unity

The tool runs on your machine before you build; nothing runs inside the shipped game.

**One-time setup per project:**

1. Copy this folder to `<project>/Tools/arabic-l10n`. Keep it outside `Assets` so Unity doesn't import the Python files.
2. Copy `unity/ArabicLocalizationWindow.cs` and `unity/ArabicLocQA.cs` into `Assets/Editor/`.
3. Install Python 3.10+, then run `pip install anthropic fonttools`.
4. Set `ANTHROPIC_API_KEY` as a user environment variable, then restart Unity Hub and Unity.
5. Open **Tools > Arabic Localization > Open** and check the settings. They are saved in `ProjectSettings/ArabicLocalization.json`, so the whole team gets them through version control.
6. In Unity Localization, export the English string table to CSV with the table's CSV extension, and point **English CSV** at that file. The `Key`, `English(en)` and `Shared Comments` headers are read as-is. For `type`, `speaker`, `listener` and `scene`, add those columns to the CSV yourself.
7. In the Arabic String Table Collection, add a CSV extension pointing at **Export to** (`Assets/Localization/Arabic/strings.csv`). Map the key column to `key`, and each Arabic locale to its column (`ar`, `ar-SA` … `ar-EG`).

**Before the first translation:** run **Fake-Arabic Test Strings**. It fills the Arabic table with placeholder right-to-left text about 30% longer than the English, wrapped in `[ ]`, so devs can fix layout, letter joining, cut-off text (a missing `[` or `]`) and plurals before any money is spent on translation.

**Each release, from the menu:**

1. **Check English Source** opens `source_lint.csv`.
2. **Translate** asks for confirmation first, because it uses your paid API account. It runs in the background, and the review sheet opens when it finishes.
3. **Open Review Sheet** is where linguists work.
4. **Score Linguist Audit** shows the MQM verdict.
5. **Export to Unity** copies `strings.csv` into Assets. Then press Import on the CSV extension.
6. **Font Check** and 7. **Render Check** catch display problems before testers do.

The C# scripts were not compiled here, so expect small fixes on their first run.

## Once per game: choose the translator model

Take 100–200 representative strings and run a bake-off:

```bash
python localize.py bakeoff sample.csv --models claude-opus-5-5 openai:<model> --judge-model <a third model>
```

A linguist fills the `mqm` column in `out/bakeoff/review.csv`. The sheet is blind: systems appear only as A/B/C, so don't open `systems.json` until scoring is done. Then `python localize.py score out/bakeoff/review.csv` ranks the models. Rankings change from one test set to another, so decide on your own strings.

## Per-release workflow

| # | Who | Step |
|---|---|---|
| 1 | Dev | `python localize.py lint strings_en.csv --suggest` lists strings that cannot become correct Arabic: counts without plurals, bare `%s %s`, concatenated fragments, missing context and dialogue that talks to the player. It also writes suggested English rewrites to `out/source_lint.csv`. Fix these in the game. If the game passes a player-gender variable, translate with `--gender-var player_gender`. |
| 2 | Dev | Add a `screenshot` column (an image path relative to the CSV) for the strings you can. Strings from the same screen are translated together and the model sees the screen. For dialogue, fill `speaker`, `listener` (a character name, or `player`/`group`/`none`) and `scene`, and list every character once in `characters.csv` next to the CSV (`name,ar,gender,notes`). A scene is always translated and reviewed as one ordered conversation. Arabic agreement follows the speaker for "I" and the listener for "you", and character names stay locked. See `sample/`. |
| 3 | Pipeline | `python localize.py translate strings_en.csv --model <bake-off winner> --judge-model openai:<model>`. Using a different provider as the reviewer catches more errors. Add `--batch-api` for half-price runs, which finish in about an hour. The run writes `out/review.csv` and `out/glossary_candidates.csv`. **Unchanged strings are free:** a string with the same key and English as an approved `tm.csv` entry is reused (`status=tm_reused`) with no AI call, so each update pays only for new or changed strings. Use `--no-reuse` after a style-guide change. Each run prints its token use and estimated cost and appends it to `out/costs.csv`. |
| 4 | Native linguist A | Revise in `out/review.csv`. Start with `status=needs_human`, reading `suggestion`, `judge`, `qa` and `note`. `INCONSISTENT` in `qa` means the same English was translated two ways, or two different English strings share one Arabic; pick one wording. Edit `final` and set `approved=y`. Set `approved=y` on the good rows in `glossary_candidates.csv`. |
| 5 | QA testers | Run in-build LQA (checklist below). |
| 6 | Native linguist B (independent) | Fill the `mqm` column on `audit=Y` rows with `none` or `major/accuracy; minor/fluency`. Then run `python localize.py score out/review.csv`. This gives the 99% verdict and shows how far the AI reviewer can be trusted per content type. The annotations are saved to `calibration.csv`, so the reviewer learns your linguists' standard next run. |
| 7 | Dev | `python localize.py export out/review.csv` blocks on rule errors and forbidden terms. It writes `out/strings.csv` (`key,en,ar,ar-SA…ar-EG`) for Unity Localization CSV import. Approved strings go into `tm.csv` and approved terms into `glossary.csv`, so every release starts better than the last. |
| 8 | Dev | `python localize.py fontcheck out/strings.csv --font <your font>.ttf --shaped` reports every glyph the font lacks; use `--shaped` with RTLTMPro. Then run **Tools > Arabic Loc QA** in Unity (`unity/ArabicLocQA.cs`) to find unshaped text, missing glyphs and overflow in your real text prefab. |

The score is only valid for the text that was audited. If revision continues after the audit, run the audit again. When `score` reports that a content type's AI reviewer agrees with humans at ≥ 99% over ≥ 300 strings, the linguist can skip revising that type's `auto_pass` rows. That is where review cost comes down.

## In-build LQA checklist (Unity)

- **Letters must join.** uGUI/TextMeshPro cannot shape Arabic. Use RTLTMPro (hk1ll3r fork v4+, with the **Farsi** option off) or UI Toolkit with the Advanced Text Generator on Unity 6.3+. The font atlas must include the presentation forms and be at least 512×512.
- **Mirroring.** Check RTL layout and arrows, and make sure no text is truncated. Check that diacritics are not clipped; raise line spacing if they are.
- **Plurals.** Check every plural key at 0, 1, 2, 3, 10, 11, 99, 100, 101, 102, 1000 and 1.5. If you use `--gender-var`, check both genders.
- **Bidi isolates in code.** Wrap player names in FSI…PDI, and wrap scores, versions and URLs in LRI…PDI. Never put these characters in the CSV.
- **Prices** use the store's formatted string. **Digits** are Western 0–9. Check dates, currency, weekends and feature flags against `locales.json`.

## Files

| File | What |
|---|---|
| `style_guide.md` | The translator and reviewer spec. It is also the LLM system prompt, so editing it changes the model's behavior. |
| `glossary.csv` · `tm.csv` · `calibration.csv` | Locked terms, approved translations, and linguist-annotated examples. All three grow with each release. |
| `locales.json` | Per-country config: overlay, formats, VAT, rating, legal rules, forbidden terms. |
| `ar_qa.py` | About 30 Arabic rule checks; `python ar_qa.py` runs its self-test. |
| `localize.py` | The `lint`, `translate`, `bakeoff`, `qa`, `score`, `export`, `fontcheck` and `pseudo` commands. |
| `unity/ArabicLocalizationWindow.cs` | The **Tools > Arabic Localization** menu, which runs every command from inside Unity. |
| `unity/ArabicLocQA.cs` | The Unity Editor render check. It was not compiled here, so expect small fixes for your TMP version. |
| `test_localize.py` | An offline end-to-end test with all model providers stubbed. |

## Still draft

`style_guide.md` and `glossary.csv` need sign-off from a native lead linguist, and native reviewers from each dialect cluster should check the overlay rules. Items marked "verify" in `locales.json` need a local check.
