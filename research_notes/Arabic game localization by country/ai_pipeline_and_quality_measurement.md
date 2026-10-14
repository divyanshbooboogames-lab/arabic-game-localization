# AI/LLM-Assisted English→Arabic Game Localization: Pipeline Best Practice and Rigorous Quality Measurement

Scope note: Evidence is 2024-2026 unless labelled "[older]". English→Arabic-specific evidence is flagged "[EN→AR]". Where only general (other language pair) evidence exists, it is flagged "[general]". Primary sources were read directly where possible (WMT25 General MT findings, WMT25 Automated Evaluation findings, MQM Council scoring page, Moslem et al. 2023, Zou et al. 2025, Yakhni & Chehab 2025). Items sourced only from search-result summaries are marked "(snippet-level)".

---

## 1. Measuring quality: MQM, LQA scoring, thresholds, ISO standards, and what "99%" actually means

### Takeaway
"99%" only has a precise meaning in the MQM framework: a Raw Quality Score of 99 means no more than 10 severity-weighted penalty points per 1,000 evaluated words. With the default 1/5/25 weights, that allows 10 minor errors, or 2 major errors, or zero critical errors. The MQM Council's own example uses 99 as the default raw pass threshold, so a 99 target is attainable but strict. It has to be stated with the weights, the sample size (at least about 1,000 words), and who annotates. It should never be read as "99% of words correct".

### Cited Findings
**MQM scoring mechanics (official MQM Council page)**
- Default severity multipliers are 0 (Neutral), 1 (Minor), 5 (Major), 25 (Critical). The page recommends exponential progression and allows custom multipliers. — [MQM Council, The MQM Scoring Models](https://themqm.org/error-types-2/the-mqm-scoring-models/)
- Formula chain: Error Type Penalty Total = (minor×1 + major×5 + critical×25) × Error Type Weight. Absolute Penalty Total (APT) = sum of ETPTs. Per-Word Penalty Total = APT / Evaluation Word Count. Normed Penalty Total = PWPT × Reference Word Count, where RWC is typically 1,000 words. Maximum Score Value is 100. — [MQM Council](https://themqm.org/error-types-2/the-mqm-scoring-models/)
- Raw scoring: "any quality score between 100–99 ... produces the Pass rating". The Passing Threshold is 99 (0.99). The example of acceptable penalty is "10 minor errors OR 2 major errors per 1000 words, which yields a Raw Quality Score of 99." — [MQM Council](https://themqm.org/error-types-2/the-mqm-scoring-models/)
- The MQM page's content-type examples: 99.5 for legal translation (5 penalty points per 1,000 words) and 97.2 for user-to-user technical help (28 penalty points per 1,000 words). Calibrated scoring rescales so that the passing threshold can be any value, e.g. 90 or 95 (example: threshold 90 ↔ NPT of 10 per 1,000 words). — [MQM Council](https://themqm.org/error-types-2/the-mqm-scoring-models/)
- Older/academic MQM usage weights critical at 10 rather than 25. Google's large-scale MQM study (Freitag et al.) dropped the Critical category because "its definition is often context-specific" [older, 2021]. — [Freitag et al., Experts, Errors, and Context](https://arxiv.org/pdf/2104.14478) (snippet-level); [Localazy MQM glossary](https://localazy.com/dictionary/multidimensional-quality-metric-mqm) gives 0/1/5/25 or auto-fail for critical.
- Vendor implementations follow the same per-word model. Smartling's documented example is 1 − ((1×25)+(1×5)+(1×1)+(1×0))/231 = 86.58%, with an example passing threshold of 90 (snippet-level). XTM computes TS = 1 − (AP / word count) and applies issue-type weights. — [Smartling help](https://help.smartling.com/hc/en-us/articles/19513205210651); [XTM LQA feature](https://xtm-cloud.atlassian.net/wiki/spaces/EXKB/pages/3273497105/LQA+feature)
- A games-oriented vendor framework (Loxily) suggests weighting dimensions rather than relying on MQM severity alone: Accuracy 35%, Terminology consistency 20%, Register 20%, Format 15%, Cultural compliance 10%. It recommends different weights for UI, dialogue, and marketing. This is a vendor opinion, not a standard. — [Loxily AI LQA Scoring Framework](https://loxily.com/en/blog/ai-lqa-scoring-framework)

**Sample size and statistical rigor**
- The MQM Council's "Multi-Range" theory (2024-2025) says linear per-word scoring over-penalizes short samples and under-penalizes long ones. It recommends three regimes. Micro (<~250 words): deterministic tolerance curves are "statistically unreliable", so use Statistical Quality Control. Meso (~250–3,000 words): use a calibrated linear model near its anchor. Macro (>3,000 words): use a non-linear (logarithmic) tolerance E(x) = a·ln(1 + b·x). Switch models when the sample size deviates more than ~20% from the anchor (e.g., a 1,000-word anchor is valid for 579–1,460 words). — [Gladkoff et al., Non-Linear Scoring Model for TQE (arXiv 2511.13467)](https://arxiv.org/html/2511.13467v1); [Slator coverage](https://slator.com/mqm-council-releases-multi-range-theory-of-translation-quality-evaluation-with-new-scoring/)
- In that paper, survey data showed linear models overestimate acceptable error counts in the macro range by up to 50%. In a 5,000-word marketing case, a linear model passed a text with 23 minor errors that human reviewers rejected; the log model's threshold of 16 matched the experts. The paper recommends Wilson or Agresti–Coull confidence intervals for small samples. At 5 errors/1,000 words, a 200-word sample expects only about 1 error, so pass/fail on such a sample is mostly noise. — [arXiv 2511.13467](https://arxiv.org/html/2511.13467v1)
- Inter-annotator agreement matters. In WMT25 human evaluation (ESA protocol), English→Arabic (Egyptian) used 3 professional annotators with pairwise Pearson IAA of 0.96 on a control subset, the highest of all pairs (e.g., EN→Czech 0.41, EN→Japanese 0.28). — [WMT25 General MT Findings, Table 9](https://aclanthology.org/2025.wmt-1.22.pdf)
- A second human annotator reproducing the first human's error spans for EN→AR(EG) achieved only 77.96% character-level F1 (WMT25 Task 2 "Human2" row). So even human MQM-style span annotation for Arabic agrees only about 78% at span level. — [WMT25 Automated Translation Evaluation Findings, Table 13](https://aclanthology.org/2025.wmt-1.24.pdf)

**Process standards**
- ISO 17100:2015 makes revision by a second person (not the translator) an obligatory step. The reviser must have translator-level competences, and the revision is bilingual (source vs. target). "Review" (monolingual, by a domain expert) is optional. ISO has opened a revision (ISO/AWI 17100), and whether a second person must always revise is reportedly under discussion. — [Wikipedia: ISO 17100](https://en.wikipedia.org/wiki/ISO_17100); [ATC ISO 17100 review blog](https://atc.org.uk/wp-content/uploads/ATC-ISO-Blog-17100-Translation-Services-Review.pdf)
- ISO 18587:2017 covers full human post-editing of MT so that quality is "comparable to that of a human translation". It includes stylistic edits beyond meaning, and post-editor competences are aligned with those of translators. A revision is under development that adds more focus on customer requirements, needs analysis and risk assessment, with a structure aligned to ISO 17100. — [ATC ISO 18587 blog](https://atc.org.uk/wp-content/uploads/ISO-Blog-18587-Machine-translation-post-editing.pdf); [Interpro ISO 18587 guide](https://www.interproinc.com/what-is-iso-18587-machine-translation-post-editing-guide/)
- A comparable professional benchmark is the ATA certification exam, which uses error points of 1/2/4/8/16 and requires fewer than 18 points per ~225–275-word text to pass. Its pass rate is under 20%. — [Zou, Saeedi & Koby 2025, SKASE JTI](https://www.skase.sk/Volumes/JTI29/08.pdf)

### Inferences
- Recommended definition of the target: "MQM Raw Quality Score ≥ 99 (default 1/5/25 weights, Critical = 25) on a randomly drawn sample of ≥1,000 source words per locale per milestone, annotated by a qualified native Arabic linguist who did not produce or post-edit the text, with any Critical error triggering automatic fail regardless of score." Under these rules, one Critical error in 1,000 words gives 97.5 and fails, and one Major error gives 99.5 and passes.
- "99% of strings error-free" is a different and much stricter metric. A game UI with thousands of short strings can have a raw MQM ≥ 99 while still having dozens of defective strings. Report both: the MQM score per 1,000 words, and the defect rate per string with a confidence interval.
- Because sample size drives volatility, for macro-scale game scripts (tens of thousands of words) adopt the non-linear model or fix the sample at the calibrated anchor size. Otherwise pass/fail results will swing between milestones for statistical reasons alone.
- ESA/DA-style scores used in WMT (0–100 slider) are not MQM scores. A WMT ESA score of 77 does not mean "77% accurate", so do not mix the two scales in reporting.

### Gaps
- I found no public game-vendor document (Keywords, Lionbridge Games, Localize Direct, etc.) that states a specific LQA pass threshold such as 98 or 99. Practitioner lore says 98–99, but it is unsourced here.
- TAUS DQF: I did not retrieve a primary source on the DQF error typology, its harmonization with MQM, or its current status. That needs a separate lookup.
- I could not access the normative ISO 17100/18587 text, so clause numbers are unconfirmed.

---

## 2. LLM vs MT for English→Arabic (2025-2026): benchmarks, DeepL, Arabic-centric models, and dialect ability

### Takeaway
WMT25 (2025) was the first WMT general task with English→Arabic, specifically Egyptian Arabic. Under professional human evaluation, GPT-4.1 came within 1.5 points of the human reference (77.0 vs 78.5 ESA). It beat Gemini 2.5 Pro (60.6) and Claude 4 (55.7). Most dedicated MT systems and an anonymized online MT engine scored near zero, largely because they produced MSA instead of the requested dialect. Frontier LLMs are now at or near professional level for EN→AR, but dialect control is unreliable, and model rankings vary by test set. Arabic-centric models (Jais, AceGPT, Fanar) trail frontier LLMs on translation where measured. DeepL added Arabic in 2024, but I found no independent large-scale benchmark.

### Cited Findings
**WMT25 General MT, English→Arabic (Egyptian) [EN→AR, 2025]**
- Official human ranking (ESA, professional annotators; human score / AutoRank): Human reference 78.5; GPT-4.1 77.0; CommandA 74.0; Gemini-2.5-Pro 60.6; DeepSeek-V3 56.8; Claude-4 55.7; IRB-MT 51.9; Mistral-Medium 36.0; CommandA-WMT 34.6; UvA-MT 29.0; CommandR7B 3.7; GemTrans 3.7; Algharb 3.2; Shy-hunyuan-MT 3.2; AyaExpanse-8B 2.0; ONLINE-B (anonymized commercial online MT) 1.7. 19 further systems were not human-evaluated. — [WMT25 General MT Findings, Sec. 7.4](https://aclanthology.org/2025.wmt-1.22.pdf)
- EN→Arabic (Egyptian) and EN→Italian "proved to be the most challenging" pairs. The top-system human score by domain for EN→AR(EG) was Literary 88.4, Speech 80.8, Social 84.3, News 74.7 (avg 82.0). — [WMT25 Findings, Table 10](https://aclanthology.org/2025.wmt-1.22.pdf)
- Organizers' diagnosis: "systems tend to output Modern Standard Arabic (MSA)" instead of Egyptian, and "this type of error would likely be overlooked by quality estimation metrics". Annotator guidelines said: "If the translation is in the wrong language, mark it fully and assign it 0." — [WMT25 Findings](https://aclanthology.org/2025.wmt-1.22.pdf)
- Across all 16 pairs, Gemini 2.5 Pro was the best overall system (top cluster in 14 of 16 pairs). It was collected with "thinking" mode on. Human references reached the top cluster in only 6 of 15 pairs. Automatic rankings (AutoRank) diverged from human rankings: Shy-hunyuan-MT ranked first automatically in almost all pairs but not under human evaluation, which the authors attribute to it being trained with xCOMET/GEMBA as reward signals. — [WMT25 Findings](https://aclanthology.org/2025.wmt-1.22.pdf); [machinetranslate.org WMT25 summary](https://machinetranslate.org/wmt25)

**Other 2025 EN→AR comparisons**
- Zou, Saeedi & Koby (2025) put GPT-4o and Google Translate through retired ATA certification exams graded by ATA-certified graders. Only GPT-4o EN→AR passed both texts with both graders (error points at 61%/72% and 61%/39% of the 18-point threshold). Google Translate EN→AR failed one text with one grader (72%/133%). COMET averaged ~0.97 for both and showed no significant difference. The dominant EN→AR error types for both systems were Terminology and Literalness. Small sample: 2 source texts. — [SKASE JTI 2025](https://www.skase.sk/Volumes/JTI29/08.pdf)
- Intento's "State of Translation Automation 2025" covered 46 MT engines/LLMs on 11 language pairs. A multi-agent workflow (translator → reviewer → post-editor) scored best on average and was rated "best" in 9 of 11 pairs. Customized setups beat off-the-shelf ones, and human evaluators often could not distinguish AI from human translation. A secondary source says LLMs were 89% of top performers, up from ~55%. I could not confirm whether EN→AR was among the 11 pairs. — [Slator on Intento 2025](https://slator.com/intento-releases-9th-annual-state-of-translation-automation-2025-industry-report/)
- An Arabic LLM benchmarking platform (ArabicNLP 2025) found GPT-4o, Gemini 2.0 and DeepSeek V3 "significantly outperform" smaller Arabic-centric models such as Jais and Fanar. In its translation column GPT-4o scored 0.17 and Claude 3.5 Sonnet 0.12; the metric is unclear, and Jais/Fanar were not scored on translation. (snippet-level) — [ArabicNLP 2025 platform paper](https://aclanthology.org/2025.arabicnlp-main.21.pdf)
- [Older, 2023, GPT-3.5 era] Moslem et al.: zero-shot GPT-3 (text-davinci-003) EN→AR scored COMET 41.28, versus Google API 65.5, NLLB-3.3B 66.8, ModernMT+TM 71.0. EN→AR was the pair where LLM few-shot did not catch up with dedicated MT (best LLM: 7 fuzzy matches, 64.01). This shows how weak earlier LLMs were for Arabic and how much the field has moved by 2025. — [Moslem et al., EAMT 2023](https://arxiv.org/abs/2301.13294)

**DeepL**
- DeepL added Arabic in 2024, its first right-to-left language. The rollout was staged: web/desktop/mobile first, then API/browser extensions, with document translation, a formality selector and glossary planned later. Its quality claims are company claims from internal blind tests. — [DeepL blog: launching Arabic](https://www.deepl.com/en/blog/meet-deepl-for-arabic-speakers); [DeepL press release](https://www.deepl.com/nl/press-release/deepl-expands-language-offering-through-addition-of-arabic)
- Independent evidence is limited to small academic studies. They report that DeepL struggles with Arabic polysemy and context-dependent idioms, and that it is more literal and accurate on religious expressions than Google but less communicative (Masameer animation case). (snippet-level) — [UNESA proceeding](https://proceeding.unesa.ac.id/index.php/pijcu/article/download/7106/2094/28978)

**Arabic-centric models and dialects**
- In Lebanese→English (dialect source, not EN→AR target; xCOMET): GPT-4o 0.793 and Command-R+ 0.810 led on the culturally rich LW dataset. Jais-adapted-70B scored 0.751, AceGPT-70B 0.754, Jais-13B 0.707, Google Translate 0.665, NLLB-3.3B 0.635. LLMs beat NMT mainly on authentic, culturally loaded content; on non-native benchmarks such as FLoRes the two families were similar. — [Yakhni & Chehab, AbjadNLP 2025](https://aclanthology.org/2025.abjadnlp-1.13.pdf)
- A 2025 study translating Levantine, Egyptian and Gulf dialects into MSA with six LLMs found few-shot prompting consistently beat zero-shot, chain-of-thought, and the authors' proposed "Ara-TEaR" refinement method. A secondary summary reports that a LoRA-tuned 9B model (49.88 chrF++) beat zero-shot GPT-4o (44.58) (unverified). — [Advancing Dialectal Arabic to MSA MT (arXiv 2507.20301)](https://arxiv.org/html/2507.20301)
- Dialect generation benchmarks exist but have thin results. AraDiCE (~45k MT+post-edited samples; Levantine, Egyptian, plus a Gulf/Egypt/Levant cultural set) and AL-QASIDA (8 country-level dialects incl. Egyptian, Kuwaiti, Saudi, Syrian, Palestinian; tests monolingual generation, cross-lingual generation and MT) both find persistent dialect gaps. Iraqi Arabic is absent from most of them. (snippet-level) — [Mizan benchmark paper, related-work summary](https://arxiv.org/html/2609.13980v1)
- One source sentence can have several valid regional renderings (e.g., "I want" → MSA ’urīdu, Egyptian ’āyez, Levantine biddī). A 2026 region- and register-controlled framework for Levantine/Egyptian/Gulf reports self-rated 5.0/5 authenticity versus 1.0/5 for NLLB/Helsinki (self-reported, unverified). — [Context-Aware Dialectal Arabic MT (arXiv 2604.06456)](https://arxiv.org/html/2604.06456v1)
- LQM (ACL 2026) is an MQM-style, linguistically motivated taxonomy validated on Arabic: 3,850 sentences across 7 dialects (Egyptian, Emirati, Jordanian, Mauritanian, Moroccan, Palestinian, Yemeni), 6 LLMs evaluated zero-shot, and 6,113 expert-labelled error spans. I could not access per-model scores. — [LQM, arXiv 2604.18490](https://arxiv.org/abs/2604.18490)

### Inferences
- For MSA game localization, the most common target, frontier general LLMs (GPT-4.1/GPT-class, Gemini 2.5, Claude 4-class) are the right base translators. Model ranking is test-set dependent: in WMT25, Claude-4 trailed GPT-4.1 by ~21 ESA points on Egyptian, but that task measures dialect compliance as much as translation quality. Run a project-specific bake-off on your own strings before picking a model.
- If any dialect output is required (e.g., Egyptian or Saudi NPC voice), treat dialect adherence as a separate, explicitly checked requirement. Every evaluated system frequently fell back to MSA, and automatic metrics do not catch this reliably (see Q4).
- Dedicated NMT (Google/DeepL/online engines) is no longer clearly superior for EN→AR and lacks controllable context. Its main remaining role is as a secondary "MT hint" or a comparison signal.

### Gaps
- No WMT25 data for EN→MSA; the EN→AR pair was Egyptian only. No independent large-scale DeepL Arabic benchmark found.
- No head-to-head EN→AR translation benchmark including Jais, ALLaM, Fanar and the frontier models with COMET/MQM was found. ALLaM and Fanar papers report general Arabic benchmarks, not translation.
- No evaluation found of Gulf-dialect (Saudi/Emirati) generation quality from English sources with numbers.

---

## 3. Prompting techniques that measurably improve LLM translation

### Takeaway
Two techniques have the strongest measured evidence. Injecting glossary terms raised EN→AR term adherence from 67% to 94%. Supplying translation-memory fuzzy matches as few-shot examples raised EN→AR COMET from 41 to 64 in older-model experiments. Self-critique and refine loops (TEaR, MAPS) give modest gains of about +1 COMET point. 2025 evidence shows automatic refinement adds little, and can make output worse, when the first-pass translation is already strong. Use it selectively, triggered by QE flags, not blindly on every string.

### Cited Findings
- **Fuzzy-match few-shot (retrieval-augmented MT) [EN→AR, older 2023]:** EN→AR COMET by context: zero-shot 41.28 → random 2-shot 43.32 → fuzzy 1-shot 55.10 → 2-shot 57.36 → 3-shot 59.68 → 5-shot 62.65 → 7-shot 64.01. spBLEU went 27.6 → 41.81. Relevant examples beat random ones, and gains kept growing with more matches. Arabic was capped at 7 matches because Arabic tokenizes into many more tokens. — [Moslem et al. 2023, Table 1](https://arxiv.org/abs/2301.13294)
- **Glossary injection [EN→AR, older 2023, professional linguist evaluation]:** Zero-shot, human score (1–4) 2.80 with term adherence 0.67. Zero-shot plus up to 5 glossary terms: 3.19 and 0.94. Fuzzy 2-shot: 2.89 and 0.80. Fuzzy 2-shot plus glossary: 3.03 and 0.94. Evaluators noted that forcing terms sometimes harmed grammatical accuracy, and that overlapping or contradictory terms hurt quality. The authors suggest dropping shorter terms that overlap longer ones. — [Moslem et al. 2023, Table 7](https://arxiv.org/abs/2301.13294)
- **MT hint plus fuzzy matches [EN→AR, older]:** Adding an NMT draft (OPUS) to 5 fuzzy matches lifted EN→AR COMET from 62.65 to 67.74. That beat both the MT alone (63.64) and the LLM alone. The benefit was largest for pairs where the LLM was weaker. — [Moslem et al. 2023, Table 4](https://arxiv.org/abs/2301.13294)
- **LLM terminology extraction [EN→AR, older]:** GPT-3.5 extracted bilingual terms with 97.08% accuracy (2,427/2,500), per human evaluation. — [Moslem et al. 2023, Table 5](https://arxiv.org/abs/2301.13294)
- **TEaR (Translate → Estimate with MQM-style error list → Refine) [general]:** Reported COMET-22 gain of 83.29 → 84.22 (+0.93). Larger gains on semantic metrics than on BLEU, across high- and low-resource pairs. Findings of NAACL 2025. — [TEaR, arXiv 2402.16379](https://arxiv.org/html/2402.16379v3)
- **MAPS (Multi-Aspect Prompting & Selection: extract keywords/topic/demonstrations, then QE-based selection) [general, TACL 2024]:** Significant COMET/BLEURT gains across 11 WMT22 directions. MQM human evaluation showed fewer mistranslation, awkward-style, untranslated and omission errors. — [He et al., TACL 2024](https://aclanthology.org/2024.tacl-1.13.pdf)
- **Refinement can fail [general, 2025]:** In WMT25's quality-informed post-editing task, the best LLM post-editor gained only +0.020 ΔCOMET on average. Several submissions, including o3-based ones, had negative average ΔCOMET (−0.006 to −0.011). The organizers note that gains "tend to diminish" when the initial translation is already high quality. — [WMT25 Automated Evaluation Findings, Table 15](https://aclanthology.org/2025.wmt-1.24.pdf)
- **Refinement vs few-shot for Arabic dialects [2025]:** For dialect→MSA, plain few-shot beat CoT and Ara-TEaR self-refinement. — [arXiv 2507.20301](https://arxiv.org/html/2507.20301)
- **Multi-agent translate→review→post-edit [2025]:** Best average performer in Intento's 2025 evaluation (best in 9 of 11 pairs), but it "require[s] language-specific customization". — [Slator on Intento 2025](https://slator.com/intento-releases-9th-annual-state-of-translation-automation-2025-industry-report/)
- **Prompt structure for gender [general, EN→Catalan/Spanish]:** Base LLMs showed more gender bias than NMT. A structured prompt reduced gender bias by up to 12% on WinoMT. — [Sant et al., arXiv 2407.18786](https://arxiv.org/pdf/2407.18786)

### Inferences
- Recommended prompt payload per string or batch, in priority order: (1) locked glossary entries matched in the source, including do-not-translate names; (2) top-k TM fuzzy matches or approved neighbouring strings as examples; (3) string metadata: screen/UI element, speaker and addressee with gender and number, max character length, placeholder semantics, plural category; (4) a compact style guide (MSA register, numeral style, honorifics, tone per character); (5) structured output (JSON with id, translation, flags) so placeholders and IDs can be validated by machine.
- Gender and number of the addressee or speaker cannot be inferred from English "you". This context is the single highest-value metadata field for Arabic. See Q8.
- Run self-critique/refine only on segments flagged by QE or rule checks, not on everything, given the diminishing or negative returns on already-good output.
- Re-validate the 2023 numbers on current models. The direction of the gains (TM and glossary help) is robust, but the size of the gains on frontier models is likely smaller.

### Gaps
- No 2024-2026 EN→AR-specific ablation found for glossary, TM few-shot, or context metadata on frontier models (GPT-4.1/5, Claude 4, Gemini 2.5).
- Provider documentation on translation prompting (Anthropic, OpenAI, Google) was not retrieved in this pass.
- No controlled evidence found that JSON/structured output improves translation quality itself, as opposed to parseability and placeholder integrity.

---

## 4. LLM-as-judge and automatic QE (GEMBA-MQM, xCOMET, MetricX, CometKiwi): reliability for Arabic

### Takeaway
For EN→Arabic, automatic evaluators are not good enough to certify 99%. In WMT25 EN→AR(EG), the best LLM judges (GPT-4.1, Gemini 2.5 Pro) reached system-level accuracy of 0.81–0.86. At segment level only about 0.54–0.56, and simple string metrics scored higher. Trained QE/metrics (CometKiwi-22, MetricX-25) were near chance at segment level. Automatic error-span detection for EN→AR reached only 5–21% F1, against 78% human-human agreement. Use auto-raters for triage and routing, use a different model family as judge, and keep humans as the final arbiter.

### Cited Findings
**WMT25 Automated Translation Evaluation shared task, EN→AR(EG) [EN→AR, 2025] — system-level SPA / segment-level acc\*eq**
- LLM-as-judge: GPT-4.1 0.860 / 0.556; Gemini-2.5-Pro 0.810 / 0.537; CommandA 0.731 / 0.439; Claude-4 0.720 / 0.398; DeepSeek-V3 0.548 / 0.323; Qwen3-235B 0.521 / 0.320. — [WMT25 Auto-Eval Findings, Table 19](https://aclanthology.org/2025.wmt-1.24.pdf)
- Submitted/learned metrics: GEMBA-v2 0.623 / 0.365; COMET-22 0.656 / 0.468; MetricX-25 0.352 / 0.314; MetricX-25-QE 0.326 / 0.314; COMETKiwi-22 0.121 / 0.313. Many systems sit at ~0.313, which appears to be the tie/constant baseline floor. — [WMT25 Auto-Eval Findings, Table 19](https://aclanthology.org/2025.wmt-1.24.pdf)
- String baselines did best at segment level for EN→AR: BERTScore 0.869 / 0.656; spBLEU 0.850 / 0.625; BLEU 0.858 / 0.619; chrF 0.844 / 0.608. The task-wide conclusion was that "large LLMs perform strongly at the system level, while reference-based baseline metrics outperform LLMs at the segment level." The title is "Linguistic Diversity is Challenging and References Still Help". — [WMT25 Auto-Eval Findings](https://aclanthology.org/2025.wmt-1.24.pdf)
- Catastrophic-translation detection (ESA < 10, mostly wrong dialect/MSA) for EN→AR: best threshold F1 by auto-rater was GPT-4 84%, COMETKiwi-22 83%, BERTScore 83%, Polyic-3 81%, Gemini-2.5-Pro 78%, MetricX-25-QE 77%, Claude-4 76%. EN→AR was the easiest pair for this; for Serbian script and Bhojpuri, metrics largely failed. — [WMT25 Auto-Eval Findings, Table 8](https://aclanthology.org/2025.wmt-1.24.pdf)
- Span-level error detection (MQM-like) for EN→AR(EG), micro-F1: xCOMET-XL 14.54; xCOMET-XXL 11.51; AutoLQA 15.28; AIP 4.63; GemSpanEval 20.60. A second human reached 77.96. Many EN→AR segments had full-span errors because of wrong dialect. — [WMT25 Auto-Eval Findings, Table 13](https://aclanthology.org/2025.wmt-1.24.pdf)
- Gender bias in QE (GAMBIT+ challenge set, 11 gendered targets including Arabic): all auto-raters scored masculine and feminine versions significantly differently. "English sources and target languages such as Arabic, Russian, and Icelandic" showed stronger disparities, and most raters favoured masculine forms. — [WMT25 Auto-Eval Findings](https://aclanthology.org/2025.wmt-1.24.pdf)
- Metric-trained systems can game automatic metrics. Shy-hunyuan-MT, trained with xCOMET-XXL and GEMBA (DeepSeek-V3) as GRPO rewards, topped AutoRank but not the human ranking. — [WMT25 General MT Findings](https://aclanthology.org/2025.wmt-1.22.pdf)

**Other evidence**
- xCOMET-10.7B correlated r = 0.606 / ρ = 0.631 with human judgments on Lebanese→English (dialect source), versus BLEU r = 0.098. Based on 150 sentences and 3 annotators. — [Yakhni & Chehab, AbjadNLP 2025](https://aclanthology.org/2025.abjadnlp-1.13.pdf)
- For formal EN→AR, COMET (~0.97 for both systems) failed to separate GPT-4o, which passed ATA certification, from Google Translate, which failed one text. — [Zou et al. 2025](https://www.skase.sk/Volumes/JTI29/08.pdf)
- GEMBA-MQM (GPT-4, 3-shot, reference-free MQM span marking) claimed "state-of-the-art accuracy for system ranking". The authors themselves caution against using it to show improvements in academic work because it depends on a proprietary black-box model [older, 2023]. — [Kocmi & Federmann, arXiv 2310.13988](https://arxiv.org/abs/2310.13988)
- RUBRIC-MQM (ACL 2025 Industry) found existing LLM judges show "label biases" and an "inability to assess near-perfect translations", which is exactly the regime of a 99% target. A rubric-based span scoring scheme improved correlation for top-tier systems. — [RUBRIC-MQM](https://aclanthology.org/2025.acl-industry.12/)
- Self-preference: LLM evaluators favour their own translations, more so in lower-resource directions, linked to self-recognition and lower perplexity of own outputs. — [When LLMs Benchmark Themselves, arXiv 2509.26600](https://arxiv.org/pdf/2509.26600); [Self-Preference Bias in LLM-as-a-Judge, arXiv 2410.21819](https://arxiv.org/pdf/2410.21819); [Panickssery et al., arXiv 2404.13076](https://arxiv.org/pdf/2404.13076v1)
- An Arabic LLM-evaluation survey notes that most benchmarks adopting LLM-as-judge "lack validation specifically in Arabic contexts". — [Evaluating Arabic LLMs survey, arXiv 2510.13430](https://arxiv.org/html/2510.13430v1)
- Production QE: Phrase QPS predicts an MQM-like 0–100 score, and its Auto LQA labels MQM categories and severities. The suggested workflow is to run QPS, send jobs below threshold to Auto LQA, then route flagged segments to linguists. Phrase claims "up to 80%" LQA time/cost savings (vendor claim; no published correlation found). — [Phrase blog: QPS and Auto LQA](https://phrase.com/blog/posts/understanding-phrase-quality-performance-score-phrase-qps-and-auto-lqa-how-they-unlock-hyperautomation-on-the-phrase-localization-platform)
- Gaming LQA by LLMs (AMTA 2026; 8 LLMs, EN→6 languages, ~48k samples, RPG/strategy): Claude Sonnet 4 had the best issue-detection F1 = 0.766, then Qwen-2.5-72B 0.711 and Gemini 2.0 Flash 0.691. Arabic is not confirmed among the languages. — [Tian & Wu, AMTA 2026](https://aclanthology.org/2026.amta-research.12/)

### Inferences
- Use auto-raters at three levels. (a) System or model selection and regression testing: LLM judges are adequate here. (b) Segment triage: send low-scoring strings to human review, accepting high false-negative rates. (c) Not for certifying the final score.
- Use a different model family as judge than as translator, because of self-preference bias. An ensemble (e.g., GPT-class judge + Gemini judge + xCOMET/MetricX + rule checks) where any strong negative triggers review is a sound practice. I found no EN→AR study quantifying ensemble gains.
- Add an explicit language/variety check (MSA vs dialect, Arabic script vs Latin, untranslated English). Trained QE models do not use target-language labels and miss variety errors.
- Calibrate any auto-rater on a few hundred human-MQM-annotated project strings before trusting its thresholds. WMT25 shows segment-level reliability for Arabic is low and varies widely by metric.

### Gaps
- No EN→MSA meta-evaluation found. WMT25's Arabic data is Egyptian, and wrong-dialect errors dominate it, which may distort metric comparisons for MSA game text.
- No published correlation for commercial QE (Phrase QPS, Smartling, Unbabel, Lokalise AI) against human MQM for Arabic.

---

## 5. Back-translation (round-trip translation): does it catch errors?

### Takeaway
Round-trip translation is a weak, indirect signal. With BLEU it correlates poorly with quality. With semantic embeddings it can be competitive with older QE, but correlations range from weak to moderate and vary by language pair. It cannot detect target-side errors that survive back-translation, such as wrong register, wrong gender agreement visible only in Arabic, unnatural phrasing, or MSA/dialect mismatch. Direct source-target QE plus bilingual human review is the better investment. Back-translation is mainly useful as a communication aid for non-Arabic-speaking stakeholders.

### Cited Findings
- [Older] In the early 2000s, RTT was "not recommended as a translation evaluation method" because RTT-BLEU correlated poorly with reference BLEU. Surface metrics penalize valid paraphrase. — [Moon, Cho & Park, EAMT 2020](https://arxiv.org/pdf/2004.13937)
- [Older, 2020] Using semantic embeddings, RTT-based QE achieved the highest correlations with human judgments relative to WMT19 QE metric submissions, and was robust to the choice of backward MT system. — [Moon et al., EAMT 2020](https://arxiv.org/pdf/2004.13937)
- [Older, 2021] An embedding-based RTT-QE "does not reach the performance of current state of the art methods". Correlations were reportedly weak for EN-DE and moderate for EN-ZH. — [Crone, Power & Weldon 2021](https://ar5iv.labs.arxiv.org/html/2111.00554)
- [2026] A recent paper uses RTT to score multilingual LLM quality (0–100 plus a 10-category error taxonomy) and argues it reveals issues that benchmarks miss. I only saw the abstract, so its findings are unverified. — [Round-Trip Translation Reveals What Frontier Multilingual Benchmarks Miss, arXiv 2604.12911](https://arxiv.org/pdf/2604.12911)

### Inferences
- Arabic morphology encodes gender, number, and definiteness, which English back-translation collapses. A wrong feminine imperative addressed to a male player back-translates as a correct English "you". RTT is structurally blind to the most frequent Arabic game error classes.
- An LLM back-translating its own output tends to "repair" errors (the same model's biases, plus self-preference), which further reduces detection power. Prefer a direct bilingual LLM judge from a different family, plus rules.

### Gaps
- No study found that measures RTT error-detection recall specifically for English→Arabic, or for game text.

---

## 6. Automated QA checks used in professional LQA tools

### Takeaway
Rule-based QA is mature and cheap, and it catches the "mechanical" error classes that ship-blocking game bugs often come from: placeholders and tags, numbers, untranslated text, length overflow, glossary violations, and inconsistency. It should run on 100% of strings before any human or LLM review. Arabic needs locale-specific configuration: Arabic-Indic vs Western digits, Arabic punctuation (، ؛ ؟), bidi and RTL markers, ICU plurals with 6 categories, and gendered variants.

### Cited Findings
- Crowdin QA checks: empty translation; length vs. character limit; tags mismatch; spaces mismatch; placeholders mismatch; unified placeholder mismatch; punctuation mismatch (target-language conventions); character case; special characters (brackets, quotes, entities, line breaks, currency); incorrect translation (reported issues); spelling; ICU syntax (including a missing `other` plural form); consistent terminology (glossary, not-recommended or obsolete terms); duplicate translation; FTL syntax; Android syntax; numbers mismatch (accounts for language-specific digits); AI-powered check (custom prompt); outdated translation; MDX syntax. — [Crowdin QA checks docs](https://support.crowdin.com/qa-checks/)
- Xbench (2.9 and 3.0): untranslated segments, target = source, source/target inconsistency, tag mismatch, numeric mismatch, key-term mismatch, double spaces, customizable checklists (forbidden words/characters). 3.0 adds URL, alphanumeric, unpaired symbol, unpaired quote, leading/trailing space and CamelCase checks. — [Satsuma: Xbench 2.9 vs 3.0](https://www.satsuma.com.br/en/what-are-the-differences-between-xbench-2-9-and-3-0/); [Trusted Translations on Xbench](https://www.trustedtranslations.com/blog/xbench)
- Verifika: terminology, consistency, spelling, punctuation, numbers, configurable profiles and per-language rules (third-party review; vendor documentation not retrieved). — [Localization QA tools review](https://www.rajeshkumar.xyz/blog/localization-qa-tools/)
- A game LSP (Inlingo) describes an automated pre-human QA layer that includes length checks and a custom rule system of "around 100,000 rules" (vendor claim). — [Inlingo: AI-powered translation & QA](https://inlingogames.com/blog/ai-powered-translation-quality-assurance/)

### Inferences
- Arabic-specific rules to add: digit policy (Western 0–9 vs Arabic-Indic ٠–٩, per project style); Arabic comma/semicolon/question mark; no Latin punctuation in RTL runs; bidi control characters around placeholders and Latin terms (LRM/RLM/FSI); tatweel and diacritics policy; ICU plural completeness for zero/one/two/few/many/other; gendered string variants present when the source has an addressee-gender key; detection of Latin-script leakage; MSA vs dialect lexical blacklist when MSA is required.
- Run rule QA before and after every LLM refinement step, since refinement can break placeholders.

### Gaps
- No public data found on defect-escape rates (what share of LQA bugs rule-QA prevents) for games or for Arabic.
- memoQ QA and Lokalise QA check lists were not retrieved; they are likely similar to the Crowdin and Xbench lists.

---

## 7. Human-in-the-loop: native linguist review, in-context LQA, sampling, cost

### Takeaway
Evidence and standards both point to mandatory native-linguist bilingual revision (ISO 17100 / ISO 18587 full post-editing) plus in-context, in-game LQA. Automatic tools leave large residual error rates: LLM LQA F1 is about 0.77 at best, and auto span detection for Arabic is about 5–21% F1. Many Arabic game defects (RTL layout, font shaping, truncation, context and gender) are visible only in the build. Risk-based sampling is defensible for low-visibility text, but only with statistically sized samples. Statistical guidance says samples under about 250 words are unreliable for pass/fail. No public data was found on the cost or turnaround of 100% review vs sampling.

### Cited Findings
- ISO 17100 requires second-person bilingual revision. ISO 18587 full post-editing targets human-translation-equivalent quality with translator-level competence. — [Wikipedia: ISO 17100](https://en.wikipedia.org/wiki/ISO_17100); [ATC ISO 18587 blog](https://atc.org.uk/wp-content/uploads/ISO-Blog-18587-Machine-translation-post-editing.pdf)
- Game LQA vendors describe LQA as a separate stage after TEP (translation-edit-proofread), done by different people. At least one plans projects around verifying all localized strings in their in-game context (full coverage). — [Localize Direct LQA guide](https://localizedirect.com/posts/lqa-what-is-game-localization-testing); [IGDA LQA best practices](https://igda.org/?p=7293)
- A string can pass linguistic review and still fail in context (visual fit; sense after a player's earlier choice). — [Alconost: native-speaker testing in game localization](https://alconost.com/en/blog/game-localization-lqa)
- Arabic-specific in-build defects documented in shipped games: The Witcher 3's UI and menus were not designed for Arabic RTL, causing layout issues. Fighting games (Tekken 7/8, Street Fighter 6, Mortal Kombat 1) show improper text directionality, font rendering and menu alignment problems. Arabic UI terms tend to run longer than English. — [Beyond Translation: Arabic Localisation of The Witcher 3](https://ejournal.ukm.my/3l/article/view/61425); [Issues in Arabic Video Game Localization](https://research.uaeu.ac.ae/en/publications/issues-in-arabic-video-game-localization-a-descriptive-study/)
- Best LLM for gaming LQA issue detection: F1 0.766 (Claude Sonnet 4), so roughly a quarter of issues are missed or misflagged. — [AMTA 2026](https://aclanthology.org/2026.amta-research.12/)
- Auto span-error detection for EN→AR(EG) was ≤ 20.6% F1, versus 78% for a second human. — [WMT25 Auto-Eval, Table 13](https://aclanthology.org/2025.wmt-1.24.pdf)
- Sampling statistics: below ~250 words, deterministic pass/fail is "statistically unreliable"; use SQC and Wilson/Agresti–Coull intervals. — [arXiv 2511.13467](https://arxiv.org/html/2511.13467v1)
- In WMT25, professional human references were themselves not error-free. They sat in the top cluster in only 6 of 15 pairs (though alone at the top for EN→AR), and the organizers note WMT references do not get the post-editing of high-stakes translation. — [WMT25 Findings](https://aclanthology.org/2025.wmt-1.22.pdf)
- Game translators perceive MTPE as slower than vendors claim (research project summary, snippet-level). — [The Name of the Game, Mikael journal](https://journal.fi/mikael/article/view/163989)
- Vendor claim: AI-assisted LQA (Phrase Auto LQA) can cut LQA time and cost "by up to 80%" (not independently verified). — [Phrase blog](https://phrase.com/blog/posts/understanding-phrase-quality-performance-score-phrase-qps-and-auto-lqa-how-they-unlock-hyperautomation-on-the-phrase-localization-platform)

### Inferences
- Pipeline blueprint (synthesis):
  1. Prep: glossary, character bible (gender and number of every speaker and addressee), style guide, string metadata, length limits.
  2. LLM translation with glossary, TM few-shot and context. Use a frontier model chosen by project bake-off.
  3. 100% rule QA (Q6).
  4. Second-family LLM judge in MQM-span mode, plus a variety/gender check, with targeted refinement only on flagged strings.
  5. 100% native Arabic linguist bilingual revision (ISO 17100-style) for player-facing narrative, UI, legal and store text. Risk-tier lower-visibility text such as long-tail item descriptions for sampled review, using statistically sized samples.
  6. In-build LQA by native testers covering RTL, font shaping, truncation, context and gender branches.
  7. Independent MQM scoring on ≥1,000-word random samples per milestone to verify the ≥99 target, plus tracked per-string defect rates.
- "How top vendors reach 99%+" in practice appears to combine human revision with in-context LQA and feedback loops into the glossary and TM. I found no vendor publishing audited LQA score distributions.

### Gaps
- No public cost or turnaround data comparing 100% review with risk-based sampling for games or Arabic.
- No published data on what share of residual errors in-context LQA catches after linguistic revision.
- No public LQA score distributions from Keywords, Lionbridge Games, Localize Direct or Gridly.

---

## 8. Common reasons AI Arabic game translations come out bad

### Takeaway
The documented failure modes, roughly in order of evidence strength, are:
- Wrong language variety (MSA vs dialect)
- Literalness and terminology errors
- Gender errors from English's ungendered "you" and default-masculine bias
- Missing context in fragmented strings
- Register and cultural misfit
- Technical RTL, font and length problems

Most are context failures rather than model-capability failures, so they are fixable with metadata, glossaries and in-context review.

### Cited Findings
- **Wrong variety:** In WMT25, systems asked for Egyptian Arabic often produced MSA. This put most dedicated MT systems and an online engine at ESA ≈ 0–4, and many EN→AR segments were marked as full-span errors. — [WMT25 Findings](https://aclanthology.org/2025.wmt-1.22.pdf); [WMT25 Auto-Eval](https://aclanthology.org/2025.wmt-1.24.pdf)
- **Terminology and literalness:** In ATA-graded EN→AR output, the dominant errors for both GPT-4o and Google Translate were Terminology and Literalness. Human graders also flagged rhetorical expressions and idioms that COMET did not penalize. — [Zou et al. 2025](https://www.skase.sk/Volumes/JTI29/08.pdf)
- **Literal translation of cultural expressions:** GPT-4o translated a culturally loaded Lebanese expression literally instead of idiomatically (dialect→English direction). Authentic cultural content separated systems far more than standard benchmarks did (xCOMET 0.63–0.81 on authentic content vs 0.85–0.93 on non-native sets). — [Yakhni & Chehab 2025](https://aclanthology.org/2025.abjadnlp-1.13.pdf)
- **Gender:** Arabic marks gender on 2nd-person pronouns, verbs and adjectives. The Arabic Parallel Gender Corpus 2.0 was built specifically because first- and second-person gender must be chosen independently for speaker and addressee [older, 2022]. LLMs and MT show default-masculine and stereotyped choices (e.g., "nurse" rendered feminine) [abstract-level]. QE metrics also score masculine and feminine Arabic differently. — [APGC 2.0, LREC 2022](https://preview.aclanthology.org/setup/2022.lrec-1.199); [MESA abstract on AI translation bias](https://my-mesa.org/program/abstracts/view/eyJpdiI6IkIzMVllSnVWa1pqaGhJekMrb0J0cUE9PSIsInZhbHVlIjoiYVJkemV2NEZZZHZyMWpNUEdDeDZtdz09IiwibWFjIjoiMDk3NmQyZmUwYmIzYjNmYWEwN2YyMzA2M2QyMmQwZjQ0NTU0OWQ4ZTlkMWE1NjUzMzE3ODMzODM0NzYxNjE4MyIsInRhZyI6IiJ9); [WMT25 Auto-Eval GAMBIT+](https://aclanthology.org/2025.wmt-1.24.pdf); [Gender bias in MT and LLMs, arXiv 2401.10016](https://arxiv.org/pdf/2401.10016)
- **Gender in game MT specifically:** Studied for French, not Arabic, with Google, DeepL and SmartCat on raw game content. Errors were attributed to "the predominance of the masculine" in NLP (snippet-level). Arabic localizers also note gendered forms lengthen strings, and the Arabic version of *Detroit: Become Human* showed "poor specification of gender". — [JDMDH game MT gender study](https://jdmdh.episciences.org/9065/pdf); [Issues in Arabic Video Game Localization](https://research.uaeu.ac.ae/en/publications/issues-in-arabic-video-game-localization-a-descriptive-study/)
- **RTL, fonts, length:** Shipped AAA games had RTL UI, directionality, font-rendering and alignment defects. Arabic UI terms run longer than English. — [Witcher 3 Arabic study](https://ejournal.ukm.my/3l/article/view/61425); [UAEU descriptive study](https://research.uaeu.ac.ae/en/publications/issues-in-arabic-video-game-localization-a-descriptive-study/)
- **Unnatural phrasing:** Arabic game subtitle studies found unnatural phrasing and grammatical errors that break immersion (snippet-level). — [UAEU descriptive study](https://research.uaeu.ac.ae/en/publications/issues-in-arabic-video-game-localization-a-descriptive-study/)
- **Older-model tokenization limits:** Arabic consumes many more tokens, which limited in-context examples, e.g. a cap of 7 vs 10 fuzzy matches in GPT-3.5 [older]. — [Moslem et al. 2023](https://arxiv.org/abs/2301.13294)

### Inferences
- **String fragmentation and concatenation** (e.g., "{player} found {n} {item}") is likely the largest Arabic-specific engineering risk. Arabic requires agreement of verb, number and noun gender, plus six plural forms and dual. A fragment translated without its sibling strings cannot agree. Mitigate with full-sentence ICU messages, gender and plural keys, and batching related strings into one LLM call.
- **Inconsistent terminology** across batches is mitigated by a locked glossary plus TM few-shot plus an Xbench-style key-term check, all of which have measured effects (Q3, Q6).
- **Wrong register** (overly formal or classical MSA in casual UI, or the reverse) needs an explicit register spec in the style guide. No quantitative Arabic game study was found.

### Gaps
- No quantitative study found on error-type distribution in AI-translated English→Arabic game text, e.g., the share of gender vs terminology vs truncation errors.
- No evidence found specifically on string concatenation or fragmentation errors in Arabic MT or LLM output.
- The LQM (ACL 2026) Arabic error-span dataset may contain per-category error rates for LLMs, but its full text was not accessed. GitHub: UBC-NLP/LQM_MT (per arXiv 2604.18490).
