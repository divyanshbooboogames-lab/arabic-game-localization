# Unity setup: Arabic localization tool

**For the developer:** open Claude Code in an empty folder or in your Unity project and say: *"Follow UNITY_SETUP.md to set up the Arabic localization tool for my Unity project."* Claude does the steps and asks you when it needs you.

**For Claude:** you are setting up an existing tool on a Windows PC that has a Unity game project. Work through the steps in order. Run each step's **Check** before moving on, and report what you did at the end (see the final section).

---

## What this tool is

The repo `arabic-game-localization` contains `arabic-l10n/`, a Python command-line tool (`localize.py`):

1. It translates the game's English strings into Arabic with Claude.
2. It checks the Arabic with about 30 rules.
3. It produces a review sheet for native linguists.
4. It exports `strings.csv`, which has an `ar` column plus one column per country (`ar-SA` … `ar-EG`).

Two Unity Editor scripts (`arabic-l10n/unity/*.cs`) add a **Tools > Arabic Localization** menu. That menu runs the tool in the background and copies the result into the Unity project. Nothing runs inside the shipped game. Full documentation is in `arabic-l10n/README.md`.

The AI work (translating and reviewing) can run two ways:

| Mode | What it needs | How it works |
|---|---|---|
| **Claude subscription** (default) | Claude Code with a Claude plan. **No API key, no API credits.** | The tool writes the work as job files and pauses. You paste one line into Claude Code, which does the translating and reviewing on your subscription and re-runs the tool until it finishes. See `arabic-l10n/CLAUDE_CODE_MODE.md`. |
| **API key** | `ANTHROPIC_API_KEY` and paid API credits | The tool calls the API itself and runs unattended. |

## Ground rules

- **Never handle API keys.** Do not ask for a key, type one, print one, store one in a file, or commit one. Subscription mode needs no key at all. In API-key mode the developer sets it themselves (step 4), and you may only check whether it is *present*.
- **Do not start real translation runs without the developer's explicit OK.** `translate`, `bakeoff` and `lint --suggest` spend API credits in API-key mode, or the developer's Claude usage in subscription mode. Everything else in this setup is free: the test suite, `pseudo`, `qa` and `fontcheck`.
- **Ask before you write into the Unity project.** Confirm the project path first, and never overwrite an existing file without asking.
- **Leave game code alone.** Do not change it, and do not change Unity packages except as described here.
- **Ask the developer to do Unity Editor UI steps.** You can't click in the Unity UI. Explain exactly what to click and wait for them to confirm.

---

## Step 0: Collect facts (ask the developer)

Ask for, or find:

1. **The Unity project root:** the folder that contains `Assets/` and `ProjectSettings/`.
2. **Where to clone the tool repo.** Default: next to the Unity project. Example: game at `D:\Projects\MyGame`, tool at `D:\Projects\arabic-game-localization`.
3. **GitHub access.** Has the developer accepted the GitHub invite to the private repo `divyanshbooboogames-lab/arabic-game-localization`?
4. **Which mode:** Claude subscription (default) or API key? If they don't know, use subscription mode; it can be switched later with one checkbox in the Unity window.

**Check:** read `<project>\ProjectSettings\ProjectVersion.txt` and note `m_EditorVersion`.

## Step 1: Prerequisites

```bash
git --version
```
```bash
py --version
```

- **Python missing or older than 3.10:** ask the developer to install Python 3.10+ from python.org with **"Add python.exe to PATH"** ticked. Then reopen the terminal.
- **`py` doesn't exist but `python` does:** use `python` everywhere below, and use it again in step 6.

Install the packages. Subscription mode only needs `fonttools`; API-key mode also needs `anthropic`.
```bash
py -m pip install fonttools
```
```bash
py -m pip install anthropic
```
Run the second command only in API-key mode.

**Check:**
```bash
py -c "import fontTools; print('python packages ok')"
```
In API-key mode, also check:
```bash
py -c "import anthropic; print('anthropic ok')"
```

## Step 2: Clone the tool repo

From the parent folder chosen in step 0:
```bash
git clone https://github.com/divyanshbooboogames-lab/arabic-game-localization.git
```

**Check:**
```bash
git -C arabic-game-localization log --oneline -1
```

"Repository not found" means the developer has not accepted the GitHub invite yet, or is signed in to a different GitHub account. Ask them to sort that out, then retry.

## Step 3: Run the offline test suite (free, no key needed)

```bash
py arabic-game-localization/arabic-l10n/ar_qa.py
```
```bash
py arabic-game-localization/arabic-l10n/test_localize.py
```

**Check:** the output ends with `ar_qa self-test ok` and `localize end-to-end test ok`. If not, stop and report the full error. The suite also runs a full subscription-mode cycle with simulated answers, so a pass means the job and answer handling works on this PC.

## Step 4: Choose how the AI runs

### A. Claude subscription (default): nothing to set up here

There's no key to set. Confirm the developer can use **Claude Code** with their Claude plan: the same app you are running in now. Keep `"useSubscription": true` in step 6.

**Check:** none needed; step 10 tests the full loop.

### B. API key (only if the developer chose it)

The developer does this, not you. Tell them:

1. Get the team's Anthropic API key from whoever manages it.
2. Run this in a terminal, with the real key in place of the placeholder:
   ```bash
   setx ANTHROPIC_API_KEY "paste-key-here"
   ```
3. Fully quit Unity Hub and Unity, and open a new terminal. Programs only see the key after a restart.

Set `"useSubscription": false` in step 6.

**Check** (prints only True or False, never the key; run it in a *new* terminal):
```bash
py -c "import os; print(bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

## Step 5: Unity packages

Read `<project>\Packages\manifest.json` and check for each of these:

| Needed | How to tell | If missing |
|---|---|---|
| **Localization** (`com.unity.localization`) | listed in manifest.json | Ask the developer to install it: **Window > Package Manager > Unity Registry > Localization > Install**. |
| **TextMeshPro** | Unity 6: part of `com.unity.ugui`. Older versions: `com.unity.textmeshpro`. | It's normally already there. |
| **RTLTMPro** (Arabic letter joining for TextMeshPro) | search the project and `Packages/` for `RTLTMPro` | Ask the developer to install the **hk1ll3r fork of RTLTMPro, v4 or newer**, following that repo's README. Without it, Arabic shows as disconnected, reversed letters. Its "Farsi" option must stay **off**. |

If the game uses UI Toolkit with the Advanced Text Generator (Unity 6.3+) instead of TextMeshPro, it doesn't need RTLTMPro. Ask the developer which one the game uses.

The developer must also add the Arabic locales in **Edit > Project Settings > Localization**: `ar`, plus the country locales the game targets (`ar-SA`, `ar-AE`, `ar-EG`, and so on).

## Step 6: Install the Editor scripts and settings

1. Create `<project>\Assets\Editor\` if it doesn't exist.
2. Copy `arabic-game-localization\arabic-l10n\unity\ArabicLocalizationWindow.cs` and `ArabicLocQA.cs` into it. If files with those names already exist, ask before overwriting.
3. Create `<project>\ProjectSettings\ArabicLocalization.json`. The menu reads its settings from this file; paths are relative to the Unity project root.

```json
{
    "python": "py",
    "toolDir": "../arabic-game-localization/arabic-l10n",
    "source": "Localization/strings_en.csv",
    "outDir": "Localization/arabic_out",
    "model": "claude-opus-5-5",
    "judgeModel": "claude-opus-5-5",
    "genderVar": "",
    "syntax": "auto",
    "batchApi": false,
    "retranslateAll": false,
    "useSubscription": true,
    "font": "Assets/Fonts/ArabicFont.ttf",
    "shaped": true,
    "exportTo": "Assets/Localization/Arabic/strings.csv"
}
```

Adjust these fields:

- **`useSubscription`:** `true` for subscription mode, `false` for API-key mode (step 4). In subscription mode, `model`, `judgeModel` and `batchApi` are ignored.
- **`toolDir`:** the relative path from the project root to `arabic-l10n`. Check that `<project>\<toolDir>\localize.py` exists.
- **`font`:** the `.ttf` or `.otf` behind the game's Arabic TextMeshPro font asset. Search `Assets/` for fonts and ask the developer which one is used for Arabic.
- **`shaped`:** `true` when RTLTMPro is used; `false` for UI Toolkit with the Advanced Text Generator.
- **`python`:** change it to `python` if `py` didn't work in step 1.
- **`source` and `exportTo`:** keep the defaults unless the developer wants other locations.

Then add these lines to the Unity project's `.gitignore` (create the file if needed). They keep cached AI answers and subscription-mode job files out of the game repo:
```
Localization/arabic_out/.cache/
Localization/arabic_out/jobs/
```

## Step 7: Check that the scripts compile

The two C# scripts have never been compiled in a real Unity project, so expect possible small API differences.

**If the Unity Editor is closed for this project**, compile in batch mode. Use the `m_EditorVersion` from step 0:
```bash
"C:\Program Files\Unity\Hub\Editor\<m_EditorVersion>\Editor\Unity.exe" -batchmode -nographics -quit -projectPath "<project>" -logFile "<project>\Logs\arabic_setup_compile.log"
```
Search that log for `error CS`. A large project can take a while on its first import.

**If the Editor is open**, ask the developer to switch to Unity, wait for the recompile, and paste any red errors from the **Console**.

**If there are errors:**
1. Fix them in `Assets/Editor/`, keeping the fixes minimal.
2. Apply the same fixes to `arabic-game-localization/arabic-l10n/unity/`.
3. Tell the developer which lines changed, so the fixes can be committed to the tool repo for everyone.

**Check:** there are no `error CS` lines, and **Tools > Arabic Localization** appears in the Unity menu bar. Ask the developer to confirm. In subscription mode, the window should show **Use Claude subscription (no API key)** ticked, with no API-key warning.

## Step 8: Connect Unity Localization (the developer clicks, you guide)

1. **Export the English source.** In the English **String Table Collection**, add a **CSV Extension** and export to `<project>\Localization\strings_en.csv`. The tool reads Unity's `Key`, `English(en)` and `Shared Comments` columns as they are. Optional extra columns: `type`, `context`, `speaker`, `listener`, `scene`, `max_len`. See `arabic-l10n/README.md`.
2. **Set up the Arabic import.** In the Arabic **String Table Collection**, add a **CSV Extension** pointing at `Assets/Localization/Arabic/strings.csv`. Map the key column to `key` and each Arabic locale to its column (`ar`, `ar-SA` … `ar-EG`).

## Step 9: Layout smoke test (free)

1. Ask the developer to run **Tools > Arabic Localization > Fake-Arabic Test Strings** and confirm the dialog. This replaces the Arabic table with fake Arabic, so no real translations are lost at this stage.
2. Then ask them to press **Import** on the Arabic CSV extension, switch the game to Arabic, and look for:
   - **Letters joined:** joined, not separate boxes or isolated letters. If they're separate, RTLTMPro is missing or misconfigured.
   - **Direction:** text reads right-to-left.
   - **Truncation:** both `[` and `]` are visible. If one is missing, the text is cut off.
   - **Glyphs:** no □ boxes. If there are, the font lacks glyphs; run **6. Font Check**.

If Unity isn't set up yet, the same test works from the command line:
```bash
py arabic-game-localization/arabic-l10n/localize.py pseudo "<project>/Localization/strings_en.csv" --out "<project>/Localization/arabic_out"
```

## Step 10: Subscription-mode test on the sample game (ask first)

This proves the whole no-API-key loop on this PC. It translates the tool's 24-string sample game and uses a small amount of the developer's Claude usage. **Ask the developer before running it.** Skip it in API-key mode.

1. From the parent folder used in step 2, start the run into a scratch folder `arabic_sample_run`. It sits outside both the game and the tool repo, so it can be deleted afterwards.
   ```bash
   py arabic-game-localization/arabic-l10n/localize.py translate arabic-game-localization/arabic-l10n/sample/source.csv --out arabic_sample_run --model claude-code --judge-model claude-code
   ```
   It should end with `PAUSED: 1 job(s) are waiting for Claude Code…` and a `Follow …CLAUDE_CODE_MODE.md for this command: …` line.
2. Do exactly what that line says: read `arabic-l10n/CLAUDE_CODE_MODE.md` and follow it.
   1. Answer the translate job.
   2. Re-run the command.
   3. Answer the review jobs with a **separate subagent** that did not translate.
   4. Re-run until it prints `Wrote …review.csv`.

   That usually takes 2–3 rounds.

**Check:** the final run ends with `Wrote …review.csv` and a summary like `ar 24 strings | … needs_human …`. A few `needs_human` rows are expected; the sample deliberately includes a Christmas event, a paid lucky wheel and a count without a plural.

---

## When done, report to the developer

- Each step: ✅ done, or what's blocked and why.
- Which mode is set (subscription or API key).
- Python version, Unity version, and whether Localization and RTLTMPro are installed.
- Whether the scripts compiled, and any fixes you made (with file and line).
- API-key mode only: whether `ANTHROPIC_API_KEY` is visible (True or False only).
- The results of the layout smoke test and of the subscription-mode test, if they ran.

## Daily use (for the developer)

From **Tools > Arabic Localization**:

1. **Check English Source:** finds English strings that can't become correct Arabic. In subscription mode, its suggested English rewrites also come back as Claude Code jobs.
2. **Translate:** asks for confirmation, then runs in the background.
   - **Subscription mode (default):**
     1. The window log shows `PAUSED: … job(s) are waiting for Claude Code` and a `Follow …CLAUDE_CODE_MODE.md for this command: …` line.
     2. Open Claude Code **in the Unity project folder** and paste that line. Claude Code works through the jobs and re-runs the tool until it finishes. It splits big games across subagents, and review is done by a separate subagent.
     3. If Claude Code asks for permission to read the `arabic-game-localization` folder, allow it.
     4. When it reports `Wrote …review.csv`, carry on with step 3 here.
   - **API-key mode:** paid; the run finishes unattended, and the review sheet opens by itself.
3. **Open Review Sheet:** linguists edit `final` and set `approved=y`.
4. **Score Linguist Audit:** the 99% pass/fail check.
5. **Export to Unity:** blocks on errors; on success, press **Import** on the CSV extension.
6. **Font Check** / 7. **Render Check:** display problems.

**Unchanged strings are reused for free on the next run.** A string with the same key and English as an approved one is not sent to the AI again, so after the first full translation, each release only uses Claude for new or changed text. That matters most in subscription mode, where usage is limited.

After every Export:

1. In `arabic-game-localization`, commit and push `arabic-l10n/tm.csv`, `glossary.csv` and `calibration.csv`, so the whole team shares approved translations and linguist feedback.
2. Run `git pull` there regularly. If `arabic-l10n/unity/*.cs` changed, copy the scripts into `Assets/Editor/` again.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `PAUSED: N job(s) are waiting for Claude Code` | Normal in subscription mode. Paste the `Follow …` line into Claude Code. |
| `! invalid answer, fix it and re-run: answers/<id>.json: …` | Claude Code wrote an answer in the wrong shape. Tell Claude Code to fix that answer file to match its `answer_schema`, then re-run the same command. |
| Claude Code hits its usage limit partway | Wait for the limit to reset, then paste the same `Follow …` line again. Every answered job is kept, so it continues where it stopped. |
| Claude Code can't read `CLAUDE_CODE_MODE.md` or the tool folder | Allow it access to the `arabic-game-localization` folder when asked, or open Claude Code in the folder that contains both the game and the tool. |
| ANTHROPIC_API_KEY warning in the window | Either tick **Use Claude subscription (no API key)**, or set the key (step 4B) and fully restart Unity Hub and Unity. |
| "Could not start 'py'" in the window | Set **Python command** to `python`, or to the full path of `python.exe`. |
| "localize.py not found" | **Tool folder** is wrong; it's relative to the Unity project root. |
| Arabic letters separate or reversed in game | RTLTMPro is missing, or the text component isn't an RTL one. |
| □ boxes | The font lacks glyphs: run Font Check, then add the missing glyphs to the font asset or atlas. |
| Export blocked | Fix the rows it lists in `review.csv` (`final` column), then export again. |
| Plural strings crash or show the wrong form | Set **Plural syntax** to Unity Smart Strings if the game uses Unity Localization. Arabic needs all 6 forms. |
