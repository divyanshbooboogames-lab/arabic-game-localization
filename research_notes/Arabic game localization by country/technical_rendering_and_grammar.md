# Technical and Grammatical Failure Modes of Arabic in Games (Unity first, Unreal/Godot briefly) and Their Fixes

Research date: 2026-10-13. Note: GitHub release pages show month/day only, and some Unity issue-tracker pages could not be fetched directly (redirect). These are flagged where relevant.

---

## 1. Rendering: shaping, RTL/bidi, mixed text, UI mirroring, and engine status (Unity TMP / UI Toolkit / Unity 6, RTLTMPro, ArabicSupport, Unreal, Godot)

### Takeaway
In Unity, **uGUI + TextMeshPro still has no Arabic shaping or real bidi as of October 2026**. `isRightToLeftText` only reverses glyph order. You need RTLTMPro (or a paid equivalent), or you need to move the text to **UI Toolkit with the Advanced Text Generator (ATG)**. ATG uses HarfBuzz + ICU + FreeType. It is the default for UI Toolkit runtime from Unity 6.5, and its features are backported to 6.3 LTS. uGUI opt-in ATG is only targeted for about Unity 6.8. Unreal (HarfBuzz, `FullShaping`) and Godot 4 (TextServerAdvanced: HarfBuzz/ICU/Graphite, default) shape and run bidi natively. In those engines the usual failures are settings (KerningOnly, fallback text server), fonts that lack GSUB/GPOS, and mirroring.

### Cited Findings

**Why Arabic "looks broken" in stock TMP**
- TMP sends codepoints to the font in stored order. Without help, Arabic shows **isolated (unjoined) letters in left-to-right order**. `isRightToLeftText` reverses the order but joins nothing. It fixes direction only, not shaping. — [Bugnet: fix Unity localization Arabic RTL mirrored](https://bugnet.io/blog/fix-unity-localization-arabic-rtl-text-mirrored-wrong); [UnityGameTranslator issue #24](https://github.com/djethino/UnityGameTranslator/issues/24)
- A font with full Arabic coverage does not fix this, because the problem sits in text processing before TMP receives the string. — [UnityGameTranslator issue #24](https://github.com/djethino/UnityGameTranslator/issues/24)
- Allcorrect Games (2021): Unity "returns Arabic characters in left to right order and doesn't connect them at all". TMP "can change text direction but does not join letters", so an extra RTL solution is required. The article names Easy Alphabet Arabic (paid, $20 at the time), ArabicSupport (Konash), and RTLTMPro. — [Allcorrect Games, "Unity from right to left" (10.11.2021)](https://allcorrectgames.com/insights/unity-from-right-to-left/)
- A Unity issue-tracker entry (TMP `textInfo.wordCount` too high for words with Arabic diacritics) was reportedly closed "By Design". The resolution note says TextMesh Pro "currently does not properly support Arabic languages" and that a fix needs work that does not qualify as a bug fix. — [Unity Issue Tracker (via search snippet; page redirect not fetched)](https://issuetracker.unity3d.com/issues/tmp-textinfo-dot-wordcount-value-is-higher-for-words-with-arabic-diacritics)
- **Word-wrap failure mechanism:** text that is reordered *before* layout cannot wrap correctly. After reversal, the last word of the paragraph becomes the leftmost item on the first line, so multi-line paragraphs read in the wrong line order. Forum threads report that line breaking stays broken even after RTL detection improved. — [Bugnet](https://bugnet.io/blog/fix-unity-localization-arabic-rtl-text-mirrored-wrong); [Unity forum: proper RTL support](https://forum.unity.com/threads/proper-rtl-support.1077431/)
- Double-reversal pitfall: if text is already shaped and reordered before it reaches TMP, turning on `isRightToLeftText` reverses it again. — [Bugnet](https://bugnet.io/blog/fix-unity-localization-arabic-rtl-text-mirrored-wrong)

**Unity UI Toolkit / ATG (Unity 6.x)**
- ATG is "a text rendering module that employs Harfbuzz, ICU, and FreeType", supporting RTL languages such as Arabic and Hebrew. The basic language-direction option alone gives only "basic RTL support like text reversal". Line breaking, word wrapping, and shaping require ATG. — [Unity Manual 6.0: Advanced Text Generator](https://docs.unity3d.com/6/Documentation/Manual/UIE-advanced-text-generator.html); [Unity 6.2 Manual: language direction](https://docs.unity.cn/Manual/ui-systems/language-direction.html)
- How to enable ATG: **Edit > Project Settings > UI Toolkit > "Enable Advanced Text Generator"**. In UI Builder: Inlined Styles > Text > **Text Generator Type = Advanced**. In USS: `-unity-text-generator: advanced`. In C#, set `TextGeneratorType` to Advanced. Set it on the root element so it cascades. Direction is set by the `dir`-style attribute (Inherited / LTR / RTL), which also affects ellipsis and punctuation placement. ATG supports **dynamic font assets only**. — [Unity Manual: Advanced Text Generator](https://docs.unity3d.com/6/Documentation/Manual/UIE-advanced-text-generator.html) (summarized via search); [Unity 6000.4 Manual: Enable and use ATG](https://docs.unity3d.com/6000.4/Documentation/Manual/ui-systems/enable-and-use-atg.html)
- Announcement: "Full RTL Language Support" in UI Toolkit with Unity 6.0, opt-in (Oct 28, 2024, HugoBD-Unity). Staff confirmed it was "Only UI Toolkit" and "not yet at full parity with the old Text backend". Supported rich text tags listed: `<link>`, `<a>`, `<b>`, `<i>`, `<u>`, `<s>`, `<color>`. The ICU data file `/Assets/UI Toolkit/icudt73l.bytes` used to be required. Since **6000.0.29f1** it is added to builds automatically. — [Unity Discussions: Announcing Full RTL Language Support](https://discussions.unity.com/t/announcing-full-rtl-language-support/1544214)
- Older (2023.3) docs warned that the ICU data file `icudt73l` adds about **4.8 MB** of memory. — [Unity 2023.3 Manual: ATG](https://docs.unity3d.com/2023.3/Documentation/Manual/UIE-advanced-text-generator.html) (via search summary)
- **ATG timeline (forum post, April 8, 2026):** 6.0 opt-in. **6.3**: UI Toolkit *editor* uses ATG by default. **6.4**: IMGUI moved to ATG. **6.5**: ATG is "the default text system for UI Toolkit" runtime. All 6.5 ATG features are backported to 6.3. Shaping uses HarfBuzz and "all OpenType features are supported". Static font assets are no longer supported. Opt-out will eventually be removed. **uGUI:** the roadmap to 6.7 is full. uGUI will be looked at after 6.7 as an opt-in (project-wide in TextSettings or per TextObject), **targeted for 6.8**, "still far away". There is **no separate TMP timeline**. — [Unity Discussions: ATG Now Default in 6.5](https://discussions.unity.com/t/advanced-text-generator-atg-now-default-in-6-5/1715871)
- Known ATG issues reported by users: in an RTL TextField, Backspace does not delete correctly; Paragraph Spacing does not work with ATG; line height is miscalculated; character/word/paragraph spacing is listed as unsupported. 6.5 Alpha docs cover cursor movement in bidirectional input fields. — [Unity Discussions: UI Toolkit Issues with RTL Input and ATG](https://discussions.unity.com/t/ui-toolkit-issues-with-rtl-input-and-advanced-text-generator/1707868); [ATG Now Default in 6.5 thread](https://discussions.unity.com/t/advanced-text-generator-atg-now-default-in-6-5/1715871); [Unity 6.5 Alpha Manual](https://docs.unity.cn/6000.5/Documentation/Manual/UIE-advanced-text-generator.html)
- A user-reported open topic says ATG does not automatically fall back to OS fonts. — [ATG Now Default in 6.5 thread](https://discussions.unity.com/t/advanced-text-generator-atg-now-default-in-6-5/1715871)

**RTLTMPro (pnarimani / hk1ll3r fork, MIT)**
- Adds RTL to TMP for Arabic, Farsi, and Hebrew: multiline, AutoSize, rich text ("all TextMeshPro tags"), realtime RTL InputField and Dropdown, `GameObject/UI/* - RTLTMP` menu items, tashkeel, English/Farsi/Arabic digits, and ZWNJ insertion with Ctrl+Shift+2. — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro)
- Inspector options: **Farsi** (checked: English digits become Farsi digits; unchecked: they become Arabic digits), **Preserve Numbers** (no digit conversion), **Force Fix** (convert even if text starts with an English character; multiline English text breaks with this on), and **Fix Tags** (best-effort repair of rich-text tags). — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro)
- Install: TMP via Package Manager (not the Asset Store). Git URL `https://github.com/hk1ll3r/RTLTMPro.git?path=/UPMPackage`, or OpenUPM package `com.nosuchstudio.rtltmpro`. Build the font asset with the Unicode-range character lists in `Assets/RTLTMPro/Ranges`, at an atlas of **512x512 minimum for Arabic**. — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro); range files `LetterRanges.txt`, `NumberRanges.txt`, `TashkilRanges.txt` per [Allcorrect](https://allcorrectgames.com/insights/unity-from-right-to-left/)
- hk1ll3r fork releases: **v4.0.0 "(Unity 6+)", 21 Apr, "Fix issues with Unity 6"**; v3.4.2 added UTF-32 (emoji) support and fixed 3D text; v3.4.1 added Hebrew. Years are not shown on the page. A secondary search summary dates v4.0.0 to April 2026. — [hk1ll3r/RTLTMPro releases](https://github.com/hk1ll3r/RTLTMPro/releases)
- **Open RTLTMPro issues relevant to QA:**
  - #70 RTL+LTR mixing; #55 multiline English with ForceFix; #75 input starting with English shows wrong order
  - #128 mixed English-Arabic with rich tags places the space wrongly; #102 style tags reversed
  - #95 numbers with characters between them swap: **"2.5 → 5.2"**
  - #28 tashkeel inflates word count
  - #152 caret/selection wrong in InputField
  - #134 shaders not working in Unity 6
  - #156 trailing punctuation wrong next to English
  - #76 / #36 brackets and parentheses render or format incorrectly
  - #129 words not properly connected
  - #116 asks for UI Toolkit support
  - — [RTLTMPro issues](https://github.com/pnarimani/RTLTMPro/issues)

**ArabicSupport for Unity (Konash)**
- `using ArabicSupport; ArabicFixer.Fix(text)`, with an overload for tashkeel and Hindu numerals. Harakat are shown by default; Hindu digits are off by default. It handles only 4 Persian letters (چ ژ گ پ). **Multi-line text: you must insert line breaks yourself before calling Fix.** It works only on text set from script. Some fonts render harakat badly (Arial and Arabic Typesetting were tested). — [Konash/arabic-support-unity](https://github.com/Konash/arabic-support-unity)

**Other Unity options (vendor claims, unverified)**
- Qalam is a paid TMP add-on that claims shaping (joining plus ligatures) and RTL for uGUI TMP. — [Qalam (itch.io)](https://imariyah01.itch.io/qalam-arabic-support-for-textmeshpro)
- UnityDirectTMP "Direct Text" claims to shape, order, and wrap by laying the label out twice. — [AmirCollider/UnityDirectTMP](https://github.com/AmirCollider/UnityDirectTMP)
- Another route is pre-shaping outside Unity, for example with Python `arabic_reshaper` + `bidi`. — [Bugnet](https://bugnet.io/blog/fix-unity-localization-arabic-rtl-text-mirrored-wrong)

**HarfBuzz scope (relevant to any custom pipeline)**
- HarfBuzz does **not** do bidi. Apply the bidi algorithm first (ICU, fribidi). Shape each run of the same font/script/direction separately. HarfBuzz "knows nothing about paragraphs, lines or line lengths", so line breaking belongs in the layout layer. — [HarfBuzz manual](https://skia.googlesource.com/third_party/harfbuzz/+/1.0.6/docs/usermanual-ch02.xml) (via search summary)
- Unreal Engine is listed among products using HarfBuzz. — [HarfBuzz wiki](https://github.com/behdad/harfbuzz/wiki/Home)

**Unreal Engine**
- `ETextShapingMethod`:
  - `Auto` picks KerningOnly or FullShaping by reading direction.
  - `KerningOnly` "won't render complex right-to-left or bi-directional glyphs (such as Arabic) correctly".
  - `FullShaping` gives accurate rendering of RTL/bidi glyphs such as Arabic.
  - — [UE API: ETextShapingMethod](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/SlateCore/ETextShapingMethod); [Python TextShapingMethod](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextShapingMethod)
- `ETextFlowDirection`: `Auto` (detect per paragraph from the text), `Culture` (from the active culture), `LeftToRight`, `RightToLeft`. Each widget can override through `FShapedTextOptions`. Engine defaults come from the CVars behind `CVarDefaultTextShapingMethod` / `CVarDefaultTextFlowDirection`. — [UE Python TextFlowDirection](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextFlowDirection); [UE API FShapedTextOptions](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/UMG/FShapedTextOptions)

**Godot 4**
- TextServerAdvanced uses HarfBuzz, ICU, and SIL Graphite for BiDi, complex layout, and OpenType features, and it is the **default** TextServer. The fallback server has no BiDi, shaping, OpenType features, or kashida justification. A Bugnet post claims the default lacks full bidi; this conflicts with the official docs. — [Godot 4.4 TextServerAdvanced](https://docs.godotengine.org/de/4.4/classes/class_textserveradvanced.html); [Godot CTL progress report 1](https://godotengine.org/article/complex-text-layouts-progress-report-1/); [Bugnet Godot RTL](https://bugnet.io/blog/how-to-fix-godot-rtl-bidi-text-reordering-arabic-shaping)
- Text direction and mirroring settings: `text_direction` (`auto` uses the first strong character per UAX #9); `language` overrides locale per control; `layout_direction` overrides mirroring; `structured_text_bidi_override` with a "File" type, or the `_structured_text_parser` callback, handles paths, URIs, and similar structured text.
- Automatic RTL mirroring covers: anchors and margins; left/right alignment swap; horizontal container child order; Tree and ItemList; OptionButton, CheckBox, and column order; TreeItem icons. The coordinate system and non-UI nodes such as sprites are **not** mirrored. Directional arrow icons (back/forward) may need manual reversing.
- Pseudolocalization "is not an effective test" for RTL fonts. The default project font covers only a Latin-1 subset, and the docs recommend Noto fonts. Pluralization uses `tr_n()`.
- — [Godot docs: Internationalizing games](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
- Disconnected letters even with shaping on: the font lacks the GSUB/GPOS tables for contextual forms. — [Bugnet Godot RTL](https://bugnet.io/blog/how-to-fix-godot-rtl-bidi-text-reordering-arabic-shaping)

### Inferences
- **Decision rule for Unity mobile (Oct 2026):**
  - uGUI/TMP on Unity 2022 LTS or Unity 6.x: use RTLTMPro. Use hk1ll3r v4.0.0+ on Unity 6; v3.x on 2022 LTS (version mapping inferred from the release labels).
  - New UI in Unity 6.3 LTS+: build it in UI Toolkit with ATG (HarfBuzz/ICU = real UAX #9 bidi, line breaking, shaping) and set `dir`/language direction to RTL on the root.
  - Do not expect ATG for uGUI before about 6.8, opt-in.
- RTLTMPro and ArabicFixer work by **converting logical text into presentation-form codepoints in visual order** (they "connect letters" and "reverse"). Consequences:
  1. The TMP font atlas must contain Arabic Presentation Forms-A/B glyphs (U+FB50–U+FDFF, U+FE70–U+FEFF), and lam-alef ligatures live at U+FEF5–U+FEFC. These are standard Unicode block ranges from the Unicode code charts, not re-fetched here.
  2. Stored strings must stay **logical/unshaped**. Shaping happens at display time only. Never round-trip displayed TMP text back into data (save files, chat, analytics).
  3. Copy/paste and InputField caret logic are fragile (issues #152, #100).
- Bracket and parenthesis bugs (#36, #76) are expected when a plugin reverses strings instead of running UAX #9 with Bidi_Mirrored glyph substitution. A real UAX #9 engine (ATG, Unreal, Godot) mirrors `( ) [ ] { } < >` automatically in RTL runs.
- Unreal QA checks: assert no Arabic-displaying widget has `TextShapingMethod=KerningOnly`. With culture `ar`, `TextFlowDirection` should be `Auto` or `Culture`.
- Godot QA checks: assert TextServerAdvanced is active, plus font GSUB/GPOS presence.

### Gaps
- No official Unity statement confirms that `TMP_Text.isRightToLeftText` behavior changed in TMP / uGUI 2.0 (Unity 6). The finding that it only reverses comes from third-party sources plus the issue-tracker "By Design" note.
- Unreal UMG **layout mirroring**: I did not verify the widget-level "Flow Direction Preference" / automatic Slate mirroring docs this session. Treat it as unknown and verify in the engine docs.
- Whether RTLTMPro honours UAX #9 isolates (U+2066–2069) is undocumented. It probably does not, because it is not a UAX #9 implementation. This needs a test.
- No Unity source states whether ATG supports TMP `<sprite>` inside RTL runs beyond the "SpriteAsset support backported to 6.3" note and the `<nobr>` regression.

---

## 2. Line breaking/wrapping, text expansion, fonts and atlases, diacritics clipping, kashida/tatweel

### Takeaway
Arabic wraps **between words only** (no hyphenation in the requirements). Mixed-direction lines are laid out so lines never read bottom-to-top. Pre-reversed strings break this. Published length deltas vs English conflict: about +25–30% versus about −6%. Budget for **+30% rendered width** and test real strings. Diacritic clipping is mostly a **font-metric/line-box problem**: marks sit outside the ascent/descent. Tatweel (U+0640) is a fixed-width stretch character that pollutes search and length, while true kashida justification is an engine feature (Godot advanced only).

### Cited Findings
- Line breaking: text that does not fit wraps to the next line **between words**. Mixed-direction text is arranged so that lines are never read bottom to top. — [W3C Arabic & Persian Layout Requirements (alreq), Group Draft Note 02 Oct 2025, §7.1](https://www.w3.org/TR/alreq/)
- Justification mechanisms: inter-word spacing, intra-word spacing (only where letters do not join), alternative shapes, ligatures, kashida, tatweel. **Joined letters must not be spaced apart**, so letter-spacing/tracking breaks Arabic. Excessive or long kashidas give uneven color; avoid multiple kashidas per word. Tatweel U+0640 has fixed width and suits constrained environments. For joining control, the note recommends **ZWJ over tatweel**. — [W3C alreq §4.3.4.2, §7.2](https://www.w3.org/TR/alreq/)
- Microsoft's Saudi Arabic style guide recommends the **Kashida/tatweel character instead of a hyphen/dash** "due to the horizontal alignment" with Arabic fonts. This conflicts with treating tatweel as purely an error. — [Microsoft Arabic (ara-sau) Localization Style Guide, §4.1.14](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Unity ATG docs list character, word, and paragraph spacing as unsupported. — [ATG thread summary](https://discussions.unity.com/t/advanced-text-generator-atg-now-default-in-6-5/1715871)
- The Godot fallback TextServer lacks kashida justification; TextServerAdvanced supports it. — [Godot CTL progress report 1](https://godotengine.org/article/complex-text-layouts-progress-report-1/)
- Text length, sources conflict:
  - Eriksen guideline: Arabic +25% from English. — [American Express design guidelines](https://designinternet-qaeusw1green.americanexpress.com/guidelines/internationalization/localization)
  - Saudi vendor: about 30% expansion. — [Saudisoft](https://localization.saudisoft.com/?p=32893)
  - Text-volume study: Arabic about **6.25% shorter** than English. — [Game World Observer](https://gameworldobserver.com/?p=231)
  - Arabic glyphs become illegible at small sizes, so a shorter string does not make shrinking the font safe. — [Game World Observer](https://gameworldobserver.com/?p=231) (via search summary)
- Diacritics clipping:
  - Many multipurpose fonts place harakat in the space between lines, **outside the line height**, so marks on the top and bottom lines are clipped. — [LibreOffice bug 119608](https://www.libreoffice.org/bugzilla/show_bug.cgi?id=119608)
  - Not all Arabic fonts support diacritics over ascenders or under descenders. — [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/a/10733352)
  - Clipping at text-block edges depends on where lines wrap. — [Noesis bug 2379](https://www.noesisengine.com/bugs/view.php?id=2379)
  - Wrong line-height coefficients for Noto Naskh Arabic caused about 36% excess height in one engine. — [Stimulsoft forum](https://forum.stimulsoft.com/viewtopic.php?p=176591)
- Font atlas: RTLTMPro recommends a **512x512 minimum** atlas for Arabic and building from its range files. — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro)
- Allcorrect's workflow: Font Asset Creator > Character Sequence (Hex), e.g. `0600-06FF` plus the RTLTMPro letter, number, and tashkeel ranges. — [Allcorrect](https://allcorrectgames.com/insights/unity-from-right-to-left/)
- Guides recommend including the Arabic Presentation Forms blocks in TMP atlases because the shaping plugins output them. — [thegamingnest: Arabic fonts & shaping in Unity](https://thegamingnest.com/en/articles/0febb621-1188-4226-a4d1-68c2d3e4b2a4) (via search summary)
- TMP missing-glyph behavior:
  - TMP searches the local fallback list, then the global fallback list. If no font has the glyph, it draws `TMP_Settings.missingGlyphCharacter`, which defaults to **U+25A1 □**. — [TMP Settings docs](https://docs.unity3d.com/Packages/com.unity.textmeshpro@4.0/manual/Settings.html); [Unity Discussions: KeyNotFoundException](https://discussions.unity.com/t/textmesh-pro-keynotfoundexception/876672)
  - Anything not baked into the atlas or reachable through fallbacks shows as tofu. — [Bugnet TMP ellipsis](https://bugnet.io/blog/how-to-fix-font-asset-has-no-characters-the-character-used-for-ellipsis-was-not-found-in-textmeshpro)
- ATG supports **dynamic font assets only**. — [Unity ATG docs](https://docs.unity3d.com/6/Documentation/Manual/UIE-advanced-text-generator.html)
- Microsoft style guide on diacritics: vowelization is not required except to resolve ambiguity (e.g. قَبل vs قِبَل). Tanween fath goes **on the alef, not before it** (قلماً). — [MS ara-sau Style Guide §4.1.7](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Microsoft style guide on spacing: use **no-break spaces** between a number and its unit or currency, and in product name + version. — [MS ara-sau Style Guide §4.1.15](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)

### Inferences
- Fix for TMP clipping:
  - Regenerate the atlas with larger padding.
  - Raise line spacing for Arabic font assets, or check the Face Info ascent/descent (font asset > Face Info: Ascent Line, Descent Line, Line Height) so the line box covers marks.
  - Avoid `Overflow: Masking`/`Truncate` on Arabic labels with harakat.
  - Pick fonts designed for UI Arabic.
- Automated clipping check: render every string at its target rect in a headless scene (Unity Test Runner / Godot `--headless`) and compare glyph bounding boxes (`TMP_TextInfo.characterInfo[i].topLeft/bottomRight`, including marks) to the RectTransform bounds.
- Width budget check: measure rendered width with the engine (`TMP_Text.GetPreferredValues`, UI Toolkit `MeasureTextSize`, Godot `Font.get_string_size`) rather than character count, because cursive Arabic and harakat make character ratios meaningless.
- Do not apply letter-spacing (`characterSpacing` in TMP, `letter-spacing` USS) to Arabic labels. It inserts gaps inside joined letters, which alreq says must not happen.

### Gaps
- Font recommendations: I did not verify glyph coverage, presentation-form cmap coverage, or licenses for Noto Sans Arabic, Cairo, Tajawal, or IBM Plex Sans Arabic this session. Godot docs only recommend "Noto Fonts" generally. Some modern fonts may not map the presentation-form codepoints in `cmap`, which breaks plugin-shaped text. Check per font with fontTools: `TTFont(path).getBestCmap()` keys ∩ U+FB50–FDFF / U+FE70–FEFC.
- No source gives an exact TMP atlas size or point size for Arabic with full tashkeel beyond "512x512 minimum".
- No authoritative, methodology-backed Arabic-vs-English expansion figure was found. All the figures are vendor or guideline averages.

---

## 3. Unicode control characters: LRM/RLM/ALM, isolates LRI/RLI/FSI/PDI, embeddings/overrides; when to insert them around placeholders and numbers

### Takeaway
Wrap every **runtime-inserted value of unknown direction** (player names, guild names, chat, item names from servers) in **FSI…PDI** (U+2068…U+2069). Wrap known-LTR fragments (Latin brand names, version strings, URLs, ranges like "5-3") in **LRI…PDI**. Use single **RLM/LRM/ALM** marks only for one-character fixes such as trailing punctuation. Avoid the legacy embeddings and overrides (U+202A–202E). These only work if the engine implements UAX #9 (UI Toolkit ATG, Unreal, Godot). In TMP + RTLTMPro they may be ignored or drawn as □ if the font lacks them, so test before relying on them, or strip them.

### Cited Findings
- UAX #9 is at revision 52 (Unicode 18.0.0, 2026-09-01). Control characters and how they act:
  - **Embeddings and overrides:** LRE U+202A, RLE U+202B, PDF U+202C, LRO U+202D, RLO U+202E.
  - **Isolates:** LRI U+2066, RLI U+2067, FSI U+2068, PDI U+2069.
  - **Implicit marks:** LRM U+200E acts as L; RLM U+200F acts as R; **ALM U+061C acts as AL**.
  - Isolates are "encouraged in new documents" over embeddings. max_depth = 125.
  - All embeddings and isolates end at paragraph end (X8). Unmatched isolate initiators extend to the end of the paragraph.
  - — [UAX #9 rev 52](https://www.unicode.org/reports/tr9/)
- **Number rule W2:** a European number (EN) preceded by an AL (Arabic letter) context becomes an Arabic Number (AN), i.e. "AL EN → AL AN". W4: a single CS between two numbers of the same type takes that type. W5: ET sequences next to EN become EN. W6: remaining separators become ON. This is why "5-3", "1/2", "2.5", "+10%", or "10:30" can reorder in Arabic context. — [UAX #9 rev 52](https://www.unicode.org/reports/tr9/)
- W3C: follow Unicode and use **RLI/LRI rather than RLE/LRE**. Embeddings let text spill over, e.g. a number after an embedded RTL phrase gets pulled into the wrong direction; switching RLE…PDF to RLI…PDI fixes it. Wrap tightly and nest properly. Use RLM/LRM for single-character fixes only, since they cannot set a range direction. The controls are invisible, and named HTML entities exist only for `&lrm;`/`&rlm;`. — [W3C: How to use Unicode controls for bidi text](https://www.w3.org/International/questions/qa-bidi-unicode-controls)
- Numerals and bidi classes: European digits U+0030–0039 are **EN** (used in Algeria and Morocco). Arabic-Indic digits U+0660–0669 are **AN** (Egypt, Saudi Arabia, Iraq). Extended Arabic-Indic U+06F0–06F9 are **EN** (Iran, Afghanistan). Numbers are written LTR even in RTL text, and the AN/EN difference changes display order. Arabic-Indic numbers use decimal separator U+066B and thousands separator U+066C. — [W3C alreq §6.1](https://www.w3.org/TR/alreq/)
- Godot exposes `structured_text_bidi_override` because UAX #9 handles file names, URIs, emails, regexes, and code poorly. — [Godot i18n docs](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
- TMP renders codepoints absent from the font and its fallbacks as the missing glyph (default U+25A1). — [TMP Settings](https://docs.unity3d.com/Packages/com.unity.textmeshpro@4.0/manual/Settings.html); [Unity Discussions](https://discussions.unity.com/t/textmesh-pro-keynotfoundexception/876672)

### Inferences
- Code pattern (C#, any engine with UAX #9):
  ```csharp
  static string Isolate(string v)    => "⁨" + v + "⁩"; // FSI..PDI: unknown direction (player names, UGC)
  static string IsolateLtr(string v) => "⁦" + v + "⁩"; // LRI..PDI: known LTR (URLs, "v1.2.3", "5-3", emails)
  // var msg = string.Format(loc["ar"]["defeated"], Isolate(playerName));
  ```
  Insert at **format time in code**, not in translation files. Translators should never have to type invisible characters.
- For TMP + RTLTMPro, isolates probably are not interpreted, because RTLTMPro is not a UAX #9 implementation. Either (a) add U+200E/U+200F/U+061C/U+2066–2069 to the font asset as zero-width glyphs, or (b) strip them before assigning `text`, and handle mixed runs with RTLTMPro's own logic. Then run a QA check: any bidi control codepoint not in the font asset's character table means a tofu risk.
- Numbers: in Arabic UI, prefer one digit system per locale (see §6). Wrap compound numeric expressions (scores "3-1", ratios "1/2", times "10:30", ranges "1–5", signed values "+20%") in LRI…PDI so W2/W4–W6 cannot reorder them.

### Gaps
- No official TMP documentation states whether TMP treats U+200E/U+200F/U+2066–2069 as zero-width, non-rendering characters. The search found nothing specific. Test per TMP version.
- No source confirms UI Toolkit ATG's handling of isolates in rich-text runs. ICU's bidi implementation supports them, but this was not verified in Unity docs.

---

## 4. Grammar: CLDR plural categories, ICU MessageFormat, dual, number–noun agreement, gender (player and nouns), and why "{count} coins" and concatenation break

### Takeaway
Arabic uses **all six CLDR cardinal categories**. Each maps onto a different grammatical construction:
- `zero`: negation phrase
- `one`: singular + واحد
- `two`: dual
- `few` (n%100 = 3–10): plural, genitive, gender-reversed number
- `many` (n%100 = 11–99): singular accusative (tamyīz)
- `other` (100–102, 200–202, …, decimals): singular genitive

So a single "{count} coins" template is wrong for most numbers. Second-person UI text must also pick a gender. Microsoft's guidance is to avoid it with verbal nouns (maṣdar) and يُرجى/يمكنك + gerund.

### Cited Findings
- **CLDR Arabic cardinal rules (exact):**

  | Category | Rule | Examples |
  |---|---|---|
  | zero | `n = 0` | 0, 0.0 |
  | one | `n = 1` | 1 |
  | two | `n = 2` | 2 |
  | few | `n % 100 = 3..10` | 3–10, 103–110, 1003 |
  | many | `n % 100 = 11..99` | 11–26, 111, 1011 |
  | other | everything else | 100–102, 200–202, …, 1000, 10000, 0.1–0.9, 1.1–1.7, 10.1 |

  Arabic **ordinals** have a single category, `other`. — [CLDR Language Plural Rules chart](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html)
- Runtime check of the above in this session with Node v24.18.0 `new Intl.PluralRules('ar')`: 0→zero, 1→one, 2→two, 3→few, 10→few, 11→many, 99→many, 100→other, 101→other, 102→other, 103→few, 110→few, 111→many, 199→many, 200→other, 1000→other, 1011→many, 1.5→other. (Own verification, consistent with the CLDR chart.)
- ICU MessageFormat: exact `=N` selectors win over categories. `select` requires `other`, and `other` is not a synonym for "unknown". `plural` and `select` can be nested. Library support for `zero` and the other categories varies, and some libraries need custom rules injected for Arabic. Test boundary values. — [SimpleLocalize pluralization guide](https://simplelocalize.io/blog/posts/pluralization-guide/); [intlayer ICU guide](https://intlayer.org/blog/icu-message-format); [WebTranslateIt ICU guide](https://webtranslateit.com/learn/locales/icu-messageformat-guide)
- **Unity Localization Smart Strings plural formatter:**
  - Follows CLDR. Uses the String Table's locale by default, and `(xx)` overrides it.
  - Syntax: `{0:plural:an apple|{} apples}`, short form `{0:p:...}`, locale override `{0:plural(en):is 1 item|are items}`. `{}` is the current value.
  - Categories are zero/one/two/few/many/other, and `other` is required.
  - Older 0.x docs said to specify all forms "in smallest-to-largest order (eg. zero|one|two|few|many)".
  - No Arabic example is documented.
  - — [Unity Localization 1.5: Plural Formatter](https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/Smart/Plural-Formatter.html); [Unity Localization 0.7 Plurals](https://docs.unity3d.com/Packages/com.unity.localization@0.7/manual/Pluralization.html)
- Godot: `tr_n()` for plurals, meant for positive or zero integers. Use named placeholders (`String.format()`) so translators can reorder them. — [Godot i18n docs](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
- **Number–noun agreement (العدد والمعدود):**
  - **3–10:** counted noun is **plural, genitive**. The number takes the **opposite gender** of the noun's singular, e.g. ثَلَاثَةُ كُتُبٍ.
  - **11–99:** counted noun is **singular, accusative** (tamyīz), e.g. إحدى وأربعونَ غرفةً. In 21–99 the units 1–2 agree with the noun and 3–9 take the opposite gender. Sources disagree on gender for 11–19.
  - **100s/1000s:** counted noun is **singular, indefinite genitive**.
  - — [Kalimah Center](https://kalimah-center.com/arabic-numbers-grammar/); [al-dirassa](https://www.al-dirassa.com/en/the-numbers-and-its-usage-in-arabic); [FluentArabic](https://www.fluentarabic.net/numbers-in-arabic/)
- Microsoft Arabic style guide on numbers:
  - "0, 1, and 2 in Arabic are not written in digits". 0 becomes a negation (لا يوجد طلاب), 1 is spelled out (طالب واحد), 2 uses the dual (طالبان).
  - English plural maps to **both** Arabic plural (جمع) and dual (مثنى), e.g. "Spin Arrows" = سهمان, not أسهم.
  - — [MS ara-sau Style Guide §4.1.11–4.1.12](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- **Gender of addressee and of UI objects (Microsoft):**
  - Use gender-neutral alternatives such as collective or plural nouns.
  - Use **يجب/يمكنك/يُرجى + gerund** rather than the imperative.
  - For instructions, avoid the imperative and use a gerund introduced by a phrase like "following the steps below".
  - Use **verbal nouns (المصدر) in tooltips**, because "icon" is feminine and "button" is masculine. Example: "Displays full pages…" becomes عرض الصفحات بأكملها… rather than choosing between تعرض and يعرض.
  - "Gender-neutral language should be used in new products".
  - — [MS ara-sau Style Guide §3.1](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Microsoft on placeholders: find out what will replace each placeholder to keep the sentence grammatical. `%d/%ld/%u/%lu` = number, `%c` = letter, `%s` = string. — [MS ara-sau Style Guide, "Error messages containing placeholders"](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Word order: Arabic adjectives follow nouns. In genitive constructions with an English word between the parts, place the English after the Arabic words. — [MS ara-sau Style Guide §4.1.8](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)

### Inferences
- **Category-to-grammar mapping for messages.** This is an illustrative ICU message for "coins" (عملة, feminine; plural عملات) built from the rules above. It needs native review.
  ```
  {count, plural,
    zero  {لا توجد لديك عملات}
    one   {لديك عملة واحدة}
    two   {لديك عملتان}
    few   {لديك # عملات}
    many  {لديك # عملةً}
    other {لديك # عملة}
  }
  ```
  Unity Smart Strings equivalent (form order assumed to be zero|one|two|few|many|other per the 0.x docs; verify on your package version):
  `{0:plural(ar):لا توجد عملات|عملة واحدة|عملتان|{} عملات|{} عملةً|{} عملة}`
- Why English-style code breaks Arabic:
  - `count + " coins"`, `count == 1 ? "coin" : "coins"`, or `.NET string.Format("{0} coins")` only covers two forms.
  - Arabic needs six. Noun case and number change by category, and the number word order differs for 1–2, where the noun comes first ("عملة واحدة") or the number disappears into the dual ("عملتان").
  - Concatenation such as `"You got " + item + " x" + n` also fixes word order, the gender of the verb and adjective, and the definite article (ال) attachment. Arabic attaches prepositions and articles to the noun (بـ, لـ, الـ).
  - Rule: **one full sentence per key, with named placeholders, and plural/select inside the message**.
- **Gender of the player.** For second-person messages ("You won!" = فزتَ m / فزتِ f; "Tap" = اضغط m / اضغطي f), either:
  - (a) use neutral constructions (maṣdar: "الضغط للمتابعة", passive, or يُرجى + maṣdar), per Microsoft; or
  - (b) store a `{gender, select, female {…} other {…}}` branch keyed on a player-chosen setting.
  - A defaulted masculine imperative is common in practice but excludes female players. That is a product decision, not a QA error.
- **Gender of nouns in placeholders.** If `{item}` can be masculine or feminine, the surrounding verb or adjective must agree ("تم فتح {item}" is neutral; "{item} جديد/جديدة" is not). Store grammatical gender as metadata on item names and pass it to `select`, or rewrite templates to be agreement-free.
- QA test vectors for every Arabic plural key: `0, 1, 2, 3, 10, 11, 99, 100, 101, 102, 103, 111, 1000, 1011, 1.5`.

### Gaps
- No Unity doc explicitly confirms the segment-to-category order for Arabic in Smart Strings 1.x. Verify by previewing 0/1/2/3/11/100.
- .NET has no built-in CLDR plural API. I did not verify which C# ICU MessageFormat libraries (e.g. ICU4N, MessageFormat.NET, jeffijoe/messageformat.net) fully support Arabic `zero/two/few/many` this session.
- No authoritative source was found for game-specific player-gender handling in Arabic, such as a GDC talk or a Keywords/Gridly/Lokalise article with concrete examples.

---

## 5. Placeholder and tag integrity: rich-text tags, {0}/%s/%d, ordering, truncation

### Takeaway
Arabic breaks placeholders and tags in four ways:
1. Translators or LLMs drop, alter, or translate placeholders.
2. RTL-reversal plugins reverse or mis-space tags (RTLTMPro #102, #128).
3. Positional `%s` prevents the reordering Arabic needs.
4. Truncation or ellipsis cuts mid-word, or the ellipsis lands on the wrong side.

Enforce **multiset parity** of placeholders and tags between source and target, require **named or positional** placeholders, and render-test truncation.

### Cited Findings
- RTLTMPro "Fix Tags" is a best-effort attempt to repair rich-text tags. Open bugs: style tags reversed (#102), wrong space position with mixed English-Arabic plus tags (#128), "2.5 → 5.2" swaps (#95). — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro); [RTLTMPro issues](https://github.com/pnarimani/RTLTMPro/issues)
- ATG in UI Toolkit lists supported rich-text tags `<link>`, `<a>`, `<b>`, `<i>`, `<u>`, `<s>`, `<color>`. `<font-weight>` is supported per staff. A `<nobr>` regression broke SpriteAsset tags and a fix is being backported. — [Announcing Full RTL Language Support](https://discussions.unity.com/t/announcing-full-rtl-language-support/1544214); [ATG Now Default in 6.5](https://discussions.unity.com/t/advanced-text-generator-atg-now-default-in-6-5/1715871)
- In ATG, language direction affects ellipsis position and punctuation. — [Unity ATG docs](https://docs.unity3d.com/6/Documentation/Manual/UIE-advanced-text-generator.html)
- Godot: use named placeholders with `String.format()` so translators can reorder them. Pseudolocalization keeps placeholders intact, e.g. `[Ĥéłłô ŵôŕłd́, ŧh̀íš íš %s!]`. — [Godot i18n docs](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
- Microsoft: placeholder letters carry meaning (`%d` number, `%s` string, `%1!d!` positional). Prompt-style placeholder tags like `<placeholder>…</placeholder>` must be preserved in Arabic. — [MS ara-sau Style Guide](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- RTLTMPro: Force Fix plus multiline English is broken. Text starting with English shows the wrong order (#75). Trailing punctuation next to English is wrong (#156). — [RTLTMPro issues](https://github.com/pnarimani/RTLTMPro/issues)

### Inferences
- Placeholder regex (tested in this session; see §7):
  `\{[^{}]*\}|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXoc@]|%\d+!?[^!\s]*!?`
  Compare `Counter(findall(src)) == Counter(findall(tgt))`.
- For ICU messages, compare the **argument names**, not the raw braces, because plural branches nest braces. Parse with an ICU parser (e.g. `@formatjs/icu-messageformat-parser` in Node) and compare argument sets.
- Tag regex: `</?[A-Za-z][\w-]*(?:=[^>]*)?\s*/?>`. Require the same multiset and well-formed nesting via a stack check. TMP `<sprite name=…>`, `<sprite=N>`, `<link=…>`, `<color=#RRGGBB>`, `<size=…>`, `<br>`, `<nobr>`, `<noparse>` must survive unchanged. Tag attribute values must not be translated.
- Placeholder ordering: forbid bare `%s %s` in source strings that will be localized. Require `%1$s`/`{0}`/`{name}`. A positional-only source with two or more args is a lint error in the source, not in the translation.
- Truncation: avoid `Overflow=Ellipsis`/`Truncate` in TMP for Arabic. With visual-order (plugin-reversed) strings, TMP truncates the logical *beginning* of the sentence, because the visual string ends with the logical start. Prefer auto-size within bounds plus a length-budget QA check. This is inferred from the reversal mechanism and has not been tested here.
- Placeholder adjacent to an Arabic prefix (e.g. `ب{item}`, `ال{0}`) is a red flag. Arabic clitics would attach to a runtime value that may be Latin, a number, or already definite. Flag `[بلكفو]?ال?\{` and `[ء-ي]\{` (Arabic letter immediately before a placeholder) for review.

### Gaps
- No primary-source documentation found on how RTLTMPro's Fix Tags algorithm handles nested tags or `<sprite>` inside reversed runs. Only issue titles are available.
- No game-localization vendor article (Gridly, Lokalise, Crowdin, Localazy, Keywords) was retrieved in this session with Arabic-specific placeholder statistics.

---

## 6. Encoding and normalization pitfalls: Persian vs Arabic letters, alef/hamza variants, ta marbuta, NFC/NFKC, ZWJ/ZWNJ, invisible characters

### Takeaway
Store **NFC, logical-order, unshaped** text using Arabic (not Persian) codepoints:
- yeh U+064A, not U+06CC
- kaf U+0643, not U+06A9
- Arabic-Indic U+0660–0669 or Western digits, never Extended U+06F0–06F9

NFC/NFKC does **not** unify Arabic and Persian letters. NFKC also destructively folds presentation forms, so never apply NFKC to stored strings. Strip or flag zero-width and odd spaces. Treat NBSP as allowed only between a number and its unit.

### Cited Findings
- Persian uses U+06CC (Farsi yeh) instead of U+064A because the glyphs of certain joining forms differ. **Unicode normalization does not unify them.** U+0626 (yeh with hamza) decomposes to U+064A + U+0654 (Arabic yeh), so applications must handle the equivalence themselves. — [W3C i18n list, charmod-norm #216](https://lists.w3.org/Archives/Public/public-i18n-archive/2021JulSep/0253.html)
- Wikimedia: searching with Arabic ي/ك fails to find Persian articles spelled ی/ک. The proposed mapping is U+064A/U+0649/U+06CD/U+06D0 → U+06CC and U+0643/U+06AA/U+FED9/U+FEDA → U+06A9. Lucene's Persian analyzer maps the other way (Farsi yeh → Arabic yeh, keheh → Arabic kaf). The Sorani analyzer maps U+064A/U+0649 → U+06CC and U+0643 → U+06A9. — [Wikimedia Phabricator T72899](https://phabricator.wikimedia.org/T72899); [Lucene SoraniNormalizer](https://lucene.apache.org/core/5_5_0/analyzers-common/org/apache/lucene/analysis/ckb/SoraniNormalizer.html); [Lucene.NET PersianNormalizer](https://svn.apache.org/repos/asf/lucene.net/trunk/src/contrib/Analyzers/Fa/PersianNormalizer.cs)
- Perso-Arabic graphemic normalization is a known problem area with dedicated tooling. — [Graphemic Normalization of the Perso-Arabic Script (arXiv 2210.12273)](https://arxiv.org/pdf/2210.12273); [Beyond Arabic (arXiv 2301.11406)](https://arxiv.org/pdf/2301.11406)
- Digits by region:
  - W3C alreq: Arabic-Indic U+0660–0669 in Egypt, Saudi Arabia, Iraq; European digits in Algeria and Morocco; Extended U+06F0–06F9 in Iran and Afghanistan. — [W3C alreq §6.1](https://www.w3.org/TR/alreq/)
  - Microsoft's Saudi guide says "always use the Western Arabic Numbers (1, 2, 3…) which are becoming standard almost all over the Arab World". — [MS ara-sau Style Guide §4.1.12](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
  - These two sources conflict for Saudi Arabia. Make it a per-title or per-market decision and enforce consistency.
- RTLTMPro's **Farsi** checkbox converts English digits to **Farsi** digits (U+06F0–06F9). Leaving it on for Arabic produces Persian digits. — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro)
- ArabicSupport handles only four Persian letters (چ ژ گ پ). — [Konash/arabic-support-unity](https://github.com/Konash/arabic-support-unity)
- Arabic punctuation:
  - Arabic comma (typed Shift+ن) with no space before and a space after.
  - Mirrored question mark ؟ (هل تريد إعادة المحاولة؟).
  - Percent: no space, and the % sign shown on the left of the number (%50).
  - Version numbers stay as in source (4.2). In Arabic context, Hindi digits use the Arabic decimal comma.
  - — [MS ara-sau Style Guide §4.1.14–4.1.15](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
  - alreq: the percent sign goes before the number with no space (٪١٢); the currency sign goes before the number. — [W3C alreq §6.1.4](https://www.w3.org/TR/alreq/)
- Invisible characters:
  - Typical detector set: NBSP U+00A0, ZWSP U+200B, ZWNJ U+200C, ZWJ U+200D, WJ U+2060, BOM U+FEFF.
  - U+202F (narrow NBSP) has been **reported anecdotally** in chat-model output in place of ordinary spaces, with no official confirmation. Some detectors do **not** flag U+202F by default.
  - These characters also come from Word and web copy/paste, so their presence is not proof of LLM origin.
  - — [unicodefyi invisible char detection](https://unicodefyi.com/guide/invisible-char-detection/); [listdiff](https://listdiff.com/learn/how-to-find-invisible-characters-in-text); [levelup.gitconnected](https://levelup.gitconnected.com/find-invisible-unicode-characters-aka-ai-watermarks-4dd7acf7deca); [teimurjan/unllm](https://github.com/teimurjan/unllm)
- ZWNJ is a supported input feature in RTLTMPro (Ctrl+Shift+2) because it is normal in Persian orthography. — [RTLTMPro README](https://github.com/pnarimani/RTLTMPro)
- alreq prefers ZWJ over tatweel for forcing joining. — [W3C alreq §4.3.4.2](https://www.w3.org/TR/alreq/)

### Inferences
- **NFKC hazard.** Arabic presentation forms (U+FB50–FDFF, U+FE70–FEFC) have compatibility decompositions. NFKC folds already-shaped strings back to base letters, and it expands ligatures such as ﷲ U+FDF2 or ﷺ U+FDFA into multi-letter sequences. So:
  - (a) Never NFKC-normalize stored game text.
  - (b) If presentation forms show up in source strings, someone pasted pre-shaped or visual-order text, often from an old tool or a screenshot OCR. Fix the source.
  - Based on Unicode decomposition data from general knowledge; not re-fetched this session.
- NFC is safe and should be enforced. It composes decomposed hamza/madda (ا+ٔ → أ, ي+ٔ → ئ, ا+ٓ → آ). Note that NFC also canonically reorders stacked harakat by combining class. Fonts handle this, but string-equality tests on vocalized text must normalize both sides.
- Spelling-variant consistency (not auto-fixable, but auto-detectable). Within one string table, build a "loose key" per word:
  - أ/إ/آ/ٱ → ا
  - ى → ي
  - ة → ه
  - strip harakat and tatweel

  If one loose key has more than one surface form across the project (e.g. "مستوى" and "مستوي", or "اللاعب" and "الاعب"), flag it for linguist review. Egyptian practice of writing final ي as ى and inconsistent hamza spelling are the common sources.
- Ta marbuta vs heh (ة/ه) and alef maksura vs yeh (ى/ي) confusions are real-word errors. Only a dictionary/spellchecker (e.g. Hunspell ar) or LLM review catches them. Regex cannot.

### Gaps
- No Unicode or W3C page on NFKC behavior for Arabic presentation forms was fetched this session (see the inference above).
- No reliable data on which invisible characters specific LLM translation engines insert into Arabic output. Evidence is anecdotal or from vendors.

---

## 7. Which checks can be automated, and how (concrete rule set)

### Takeaway
About 20 checks are reliably automatable with regex plus Unicode properties (placeholders, tags, script and codepoint hygiene, bidi-control balance, NFC, digits, punctuation, pre-shaped or reversed storage). Another set needs engine-side rendering checks (font coverage, clipping, width, line order). Grammar (plural completeness is automatable; agreement and gender are not) needs ICU parsing plus linguist or LLM review. A tested Python reference implementation is below.

### Cited Findings
- Basis for each rule (sources in §§1–6):
  - Persian letters and digits. — [Wikimedia T72899](https://phabricator.wikimedia.org/T72899); [W3C alreq](https://www.w3.org/TR/alreq/)
  - Isolates over embeddings. — [W3C bidi controls](https://www.w3.org/International/questions/qa-bidi-unicode-controls); [UAX #9](https://www.unicode.org/reports/tr9/)
  - Arabic punctuation ؟ ، and tanween on alef. — [MS ara-sau Style Guide](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
  - Six CLDR categories. — [CLDR chart](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html)
  - Missing glyphs become U+25A1. — [TMP Settings](https://docs.unity3d.com/Packages/com.unity.textmeshpro@4.0/manual/Settings.html)
  - Invisible-character set. — [unicodefyi](https://unicodefyi.com/guide/invisible-char-detection/)
  - Number test values. — [SimpleLocalize](https://simplelocalize.io/blog/posts/pluralization-guide/); CLDR chart above
- The script below was written and run in this session (Python 3, `python -I`). All its self-test assertions passed ("ok").

### Inferences

**A. String-table (static) checks: regex/Unicode, tested**

| ID | Sev | Regex / test (on Arabic target) | Catches |
|---|---|---|---|
| PLACEHOLDER_MISMATCH | error | multiset of `\{[^{}]*\}\|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXoc@]\|%\d+!?[^!\s]*!?` differs src vs tgt | dropped, translated, or altered `{0}` `{name}` `%s` `%1$d` `%1!d!` |
| TAG_MISMATCH | error | multiset of `</?[A-Za-z][\w-]*(?:=[^>]*)?\s*/?>` differs; plus stack balance | lost or broken `<color>`, `<b>`, `<sprite>`, `<link>` |
| ICU_PLURAL_INCOMPLETE | error/warn | parse ICU; `plural` in ar must have `other` (error) and `zero,one,two,few,many` (warn if missing) | English-shaped one/other only |
| PERSIAN_YEH_KAF | error | `[یک]` | ی ک instead of ي ك |
| PERSIAN_DIGITS | error | `[۰-۹]` | RTLTMPro "Farsi" left on; Persian keyboard |
| PERSIAN_LETTERS | warn | `[پچژگ]` | پ چ ژ گ (loanwords OK, else wrong locale) |
| PRESHAPED | error | `[ﭐ-﷿ﹰ-ﻼ]` | presentation forms stored in data (pre-shaped/visual text) |
| REVERSED_START | error | `^[؟،.!:]\s*[ء-ي]` | visual-order (reversed) storage |
| REVERSED_BRACKETS | warn | `^[^()]*\)[^()]*\(` | hand-mirrored parentheses |
| EMBED_OVERRIDE | warn | `[‪-‮]` | legacy LRE/RLE/PDF/LRO/RLO |
| UNBALANCED_ISOLATE | error | running depth over `[⁦-⁨]` (+1) / `⁩` (−1) never < 0 and ends at 0 | unmatched FSI/LRI/RLI/PDI |
| INVISIBLE | warn | `[​‍⁠﻿­᠎]` | ZWSP, ZWJ, WJ, BOM, soft hyphen |
| NBSP | info | `[  ]` | allowed between number and unit (MS), else suspicious (LLM/Word paste) |
| ZWNJ | warn | `‌` | Persian-style ZWNJ in Arabic |
| TATWEEL | warn | `ـ` | stretched words (MS allows it as a dash; make it a project setting) |
| LATIN_PUNCT | warn | `[ء-ي][ ]?[?;,](?!\d)` | `?` `;` `,` instead of ؟ ؛ ، |
| MIXED_DIGITS | warn | `[0-9]` and `[٠-٩]` both present | inconsistent digit systems |
| MARK_STACK | warn | `[ً-ٰٟ]{3,}` | over-stacked harakat |
| ORPHAN_MARK | error | `(?:^\|[^ؠ-يٮ-ۓً-ٰٟ])[ً-ٰٟ]` | harakat with no Arabic base (dotted circle/tofu) |
| TANWEEN_BEFORE_ALEF | warn | `ًا` | fathatan placed before the alef (MS: put it on the alef) |
| DECOMPOSED_HAMZA | error | `[اوي]ٔ\|إ\|آ` | decomposed hamza/madda |
| NOT_NFC | error | `not unicodedata.is_normalized("NFC", s)` | any non-NFC text |
| CLITIC_PLACEHOLDER | warn | `[ء-ي]\{` or `ال\{` | Arabic prefix glued to a runtime value |
| SPELLING_VARIANTS | warn | loose-key grouping (أإآٱ→ا, ى→ي, ة→ه, strip harakat/tatweel) has more than one surface form | inconsistent orthography across the table |
| LENGTH_RATIO | info | `len(tgt)/len(src) > 1.3` (proxy only; prefer rendered width) | likely overflow |
| SOURCE_LINT | error | in the *source* language: ≥2 bare `%s` / `%d`; code doing `+ count +`, `count == 1 ?` near loc lookups | non-reorderable and English-only plural patterns |

**Reference implementation** (tested; all assertions pass):
```python
import re, unicodedata
from collections import Counter

PH  = re.compile(r"\{[^{}]*\}|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXoc@]|%\d+!?[^!\s]*!?")
TAG = re.compile(r"</?[A-Za-z][\w-]*(?:=[^>]*)?\s*/?>")
RULES = [(i, s, re.compile(r), m) for i, s, r, m in [
  ("PERSIAN_YEH_KAF","error",r"[یک]","Persian yeh/keheh; use U+064A/U+0643"),
  ("PERSIAN_DIGITS","error",r"[۰-۹]","Extended (Persian) digits"),
  ("PERSIAN_LETTERS","warn",r"[پچژگ]","p/ch/zh/g: loanword or wrong locale?"),
  ("PRESHAPED","error",r"[ﭐ-﷿ﹰ-ﻼ]","Presentation forms in source string"),
  ("EMBED_OVERRIDE","warn",r"[‪-‮]","Prefer LRI/RLI/FSI+PDI"),
  ("INVISIBLE","warn",r"[​‍⁠﻿­᠎]","Invisible char"),
  ("NBSP","info",r"[  ]","NBSP/NNBSP"),
  ("ZWNJ","warn",r"‌","ZWNJ rare in Arabic"),
  ("TATWEEL","warn",r"ـ","Tatweel"),
  ("LATIN_PUNCT","warn",r"[ء-ي][ ]?[?;,](?!\d)","Use ؟ ؛ ،"),
  ("MARK_STACK","warn",r"[ً-ٰٟ]{3,}",">2 stacked harakat"),
  ("ORPHAN_MARK","error",r"(?:^|[^ؠ-يٮ-ۓً-ٰٟ])[ً-ٰٟ]","Mark without Arabic base"),
  ("TANWEEN_BEFORE_ALEF","warn",r"ًا","Fathatan should sit on alef"),
  ("DECOMPOSED_HAMZA","error",r"[اوي]ٔ|إ|آ","Decomposed hamza/madda"),
  ("REVERSED_START","error",r"^[؟،.!:]\s*[ء-ي]","Visual-order storage?"),
  ("REVERSED_BRACKETS","warn",r"^[^()]*\)[^()]*\(","Hand-mirrored brackets?"),
]]

def check(src, tgt):
    out = [(i, s, m) for i, s, r, m in RULES if r.search(tgt)]
    if Counter(PH.findall(src)) != Counter(PH.findall(tgt)):  out.append(("PLACEHOLDER_MISMATCH","error",""))
    if Counter(TAG.findall(src)) != Counter(TAG.findall(tgt)): out.append(("TAG_MISMATCH","error",""))
    if re.search(r"[0-9]", tgt) and re.search(r"[٠-٩]", tgt): out.append(("MIXED_DIGITS","warn",""))
    d = 0
    for ch in tgt:
        d += ch in "⁦⁧⁨"; d -= ch == "⁩"
        if d < 0: break
    if d != 0: out.append(("UNBALANCED_ISOLATE","error",""))
    if not unicodedata.is_normalized("NFC", tgt): out.append(("NOT_NFC","error",""))
    return out
```
Self-test cases that passed:
- `"لديك {0} عملة"` gives no findings.
- Missing `{0}` gives PLACEHOLDER_MISMATCH.
- `"کتاب"` gives PERSIAN_YEH_KAF.
- `"ﻟﻤﺴ"` gives PRESHAPED.
- An unclosed FSI gives UNBALANCED_ISOLATE.
- `"…المحاولة?"` gives LATIN_PUNCT.
- `"؟ةلواحملا"` gives REVERSED_START.
- A leading orphan fatha gives ORPHAN_MARK.
- `ي+ٔ` gives DECOMPOSED_HAMZA.
- `"5 … ١٠"` gives MIXED_DIGITS.
- `قلمًا` written as fathatan before the alef gives TANWEEN_BEFORE_ALEF.

**B. ICU / plural checks (parser-based)**
- Parse every Arabic message (Node `@formatjs/icu-messageformat-parser`, or ICU4J `MessagePattern`). For each `plural` argument: require `other`; warn on any missing `zero|one|two|few|many` unless `=0`/`=1`/`=2` cover them. Also verify that `#` appears in the few/many/other branches and not in `one`/`two` if the style is "number spelled out or dual".
- Render each plural key with `[0,1,2,3,10,11,99,100,101,102,103,111,1000,1011,1.5]` (categories as verified with `Intl.PluralRules('ar')`) into a review sheet for a linguist or an LLM grammar checker.
- `select` must contain `other`. If the project has a player-gender setting, require a `female` branch, or require the string to be tagged "gender-neutral" in metadata.

**C. Engine-side / rendering checks (automated in CI with headless rendering)**
1. **Font coverage.** For each Arabic font asset, take the union of codepoints in all `ar` strings, plus U+FE70–FEFC/FB50–FDFF if using RTLTMPro/ArabicFixer, plus any bidi controls kept. Check them against the TMP font asset character table (`TMP_FontAsset.HasCharacters(string, out List<char> missing)`) or the font `cmap` (fontTools). Any miss means a □ (U+25A1) risk.
2. **Shaping applied.** In TMP + RTLTMPro builds, assert that the displayed text (`RTLTextMeshPro.text` after fix, or `TMP_Text.textInfo.characterInfo[].character`) contains presentation-form codepoints and **no** base Arabic letters U+0621–064A. Base letters at display time mean the plugin was bypassed, e.g. plain `TextMeshProUGUI` used, or text set via a path the plugin does not intercept.
3. **No double reversal.** Assert `isRightToLeftText == false` on RTLTMPro components, or follow the plugin's own expectation, and that plain TMP objects showing Arabic do not exist.
4. **Line order.** For multi-line labels, use `textInfo.lineInfo` with first-character indices. The logical first word must be on line 0, at the right edge. Catches the "reversed-then-wrapped" bug.
5. **Clipping.** Glyph bounds (including marks) must lie inside the RectTransform, with no TMP overflow (`isTextOverflowing == false`) at target resolution and smallest supported device size.
6. **Engine flags.**
   - Unreal: no Arabic widget uses `TextShapingMethod=KerningOnly`; FlowDirection is Auto or Culture.
   - Godot: `TextServerManager.get_primary_interface().get_name()` is the Advanced server; Controls showing `ar` use `text_direction` auto or RTL.
   - Unity UI Toolkit: root has `-unity-text-generator: advanced` and RTL direction.
7. **Mirroring snapshot.** Screenshot diff of key screens with `ar` vs `en` mirrored. Directional icons (back/next arrows, progress bars, sliders) flipped; non-directional icons (play, checkmarks, logos, clocks) not flipped. This follows Godot's guidance, and the same applies in Unity.
8. **Bidi stress strings (pseudo-locale for RTL).** Godot's accent pseudolocalization does not test RTL, so generate an Arabic pseudo-locale. Wrap each source string in RLM…, insert an Arabic word plus `{0}` plus an English brand plus `5-3` plus `?`. This exposes W2/W6 reordering and missing isolates before real translations arrive.

### Gaps
- No standard off-the-shelf linter covering this Arabic rule set was identified (e.g. in Gridly, Lokalise, or Crowdin QA settings). Vendor QA feature lists were not retrieved this session.
- No source quantifies false-positive rates for heuristics such as REVERSED_START, REVERSED_BRACKETS, or PERSIAN_LETTERS. Tune them on a real string table.
