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

## Ground rules

- **Never handle API keys.** Do not ask for a key, type one, print one, store one in a file, or commit one. The developer sets `ANTHROPIC_API_KEY` themselves (step 4). You may only check whether it is *present*.
- **Do not run paid commands without the developer's explicit OK.** These cost API money: `translate`, `bakeoff`, and `lint --suggest`. Everything in this setup is free, including the test suite, `pseudo`, `qa` and `fontcheck`.
- **Ask before you write into the Unity project.** Confirm the project path first, and never overwrite an existing file without asking.
- **Leave game code alone.** Do not change it, and do not change Unity packages except as described here.
- **Ask the developer to do Unity Editor UI steps.** You can't click in the Unity UI. Explain exactly what to click and wait for them to confirm.

---

## Step 0: Collect facts (ask the developer)

Ask for, or find:

1. **The Unity project root:** the folder that contains `Assets/` and `ProjectSettings/`.
2. **Where to clone the tool repo.** Default: next to the Unity project. Example: game at `D:\Projects\MyGame`, tool at `D:\Projects\arabic-game-localization`.
3. **GitHub access.** Has the developer accepted the GitHub invite to the private repo `divyanshbooboogames-lab/arabic-game-localization`?

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

Install the packages:
```bash
py -m pip install anthropic fonttools
```

**Check:**
```bash
py -c "import anthropic, fontTools; print('python packages ok')"
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

**Check:** the output ends with `ar_qa self-test ok` and `localize end-to-end test ok`. If not, stop and report the full error.

## Step 4: API key (the developer does this, not you)

Tell the developer:

1. Get the team's Anthropic API key from whoever manages it.
2. Run this in a terminal, with the real key in place of the placeholder:
   ```bash
   setx ANTHROPIC_API_KEY "paste-key-here"
   ```
3. Fully quit Unity Hub and Unity, and open a new terminal. Programs only see the key after a restart.

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
    "font": "Assets/Fonts/ArabicFont.ttf",
    "shaped": true,
    "exportTo": "Assets/Localization/Arabic/strings.csv"
}
```

Adjust these fields:

- **`toolDir`:** the relative path from the project root to `arabic-l10n`. Check that `<project>\<toolDir>\localize.py` exists.
- **`font`:** the `.ttf` or `.otf` behind the game's Arabic TextMeshPro font asset. Search `Assets/` for fonts and ask the developer which one is used for Arabic.
- **`shaped`:** `true` when RTLTMPro is used; `false` for UI Toolkit with the Advanced Text Generator.
- **`python`:** change it to `python` if `py` didn't work in step 1.
- **`source` and `exportTo`:** keep the defaults unless the developer wants other locations.

Then add this line to the Unity project's `.gitignore` (create the file if needed). It keeps cached AI responses out of the game repo:
```
Localization/arabic_out/.cache/
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

**Check:** there are no `error CS` lines, and **Tools > Arabic Localization** appears in the Unity menu bar. Ask the developer to confirm.

## Step 8: Connect Unity Localization (the developer clicks, you guide)

1. **Export the English source.** In the English **String Table Collection**, add a **CSV Extension** and export to `<project>\Localization\strings_en.csv`. The tool reads Unity's `Key`, `English(en)` and `Shared Comments` columns as they are. Optional extra columns: `type`, `context`, `speaker`, `listener`, `scene`, `max_len`. See `arabic-l10n/README.md`.
2. **Set up the Arabic import.** In the Arabic **String Table Collection**, add a **CSV Extension** pointing at `Assets/Localization/Arabic/strings.csv`. Map the key column to `key` and each Arabic locale to its column (`ar`, `ar-SA` … `ar-EG`).

## Step 9: Smoke test (free)

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

---

## When done, report to the developer

- Each step: ✅ done, or what's blocked and why.
- Python version, Unity version, and whether Localization and RTLTMPro are installed.
- Whether the scripts compiled, and any fixes you made (with file and line).
- Whether `ANTHROPIC_API_KEY` is visible (True or False only).
- The smoke-test result, if the developer ran it.

## Daily use (for the developer)

From **Tools > Arabic Localization**:

1. **Check English Source:** finds English strings that can't become correct Arabic.
2. **Translate:** asks for confirmation (paid), runs in the background, then opens the review sheet.
3. **Open Review Sheet:** linguists edit `final` and set `approved=y`.
4. **Score Linguist Audit:** the 99% pass/fail check.
5. **Export to Unity:** blocks on errors; on success, press **Import** on the CSV extension.
6. **Font Check** / 7. **Render Check:** display problems.

**Unchanged strings are reused for free on the next run.** After every Export:

1. In `arabic-game-localization`, commit and push `arabic-l10n/tm.csv`, `glossary.csv` and `calibration.csv`, so the whole team shares approved translations and linguist feedback.
2. Run `git pull` there regularly. If `arabic-l10n/unity/*.cs` changed, copy the scripts into `Assets/Editor/` again.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Could not start 'py'" in the window | Set **Python command** to `python`, or to the full path of `python.exe`. |
| "localize.py not found" | **Tool folder** is wrong; it's relative to the Unity project root. |
| ANTHROPIC_API_KEY warning in the window | Set the key (step 4), then fully restart Unity Hub and Unity. |
| Arabic letters separate or reversed in game | RTLTMPro is missing, or the text component isn't an RTL one. |
| □ boxes | The font lacks glyphs: run Font Check, then add the missing glyphs to the font asset or atlas. |
| Export blocked | Fix the rows it lists in `review.csv` (`final` column), then export again. |
| Plural strings crash or show the wrong form | Set **Plural syntax** to Unity Smart Strings if the game uses Unity Localization. Arabic needs all 6 forms. |
