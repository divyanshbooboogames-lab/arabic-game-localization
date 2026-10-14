# Arabic Country Variants and Locale Data for Game Localization (Middle East, as of Oct 2026)

Method note for the report writer: the per-locale formatting values below (digits, separators, currency strings, month names, week data) come from running `Intl` in **Node.js v24.18.0 with ICU 78.3 / CLDR 48.0 / Unicode 17.0** on 2026-10-13. That is stock ICU/CLDR data, so it is what any ICU-based runtime (browsers, Android ICU4J, Node, Unity packages that wrap ICU) will output at that CLDR version. Cited as "[CLDR 48 via ICU 78.3 runtime]" linking to the CLDR 48 release page. Web sources were used for policy, preference and currency-symbol facts.

## 1. Register per content type (MSA vs light MSA vs dialect)

### Takeaway
Written game text (UI, tutorials, store pages) is almost always MSA, and the one sizeable player survey found a strong player preference for MSA. Dialect turns up mainly in voiced content and in casual/marketing copy ("White Arabic"). No public player study splits preference by content type (push, UA creatives) or by country, so those choices rest on practitioner opinion.

### Cited Findings
- Survey of **382 Arabic mobile gamers** (Al-batineh, UAE University, 2024, book chapter in *User-Centric Studies in Game Translation and Accessibility*, Taylor & Francis, pp. 129–147): "strong preference for Modern Standard Arabic over colloquial dialects". It also found that female mobile gamers dominate the sample, that players prefer free games (freemium plus IAP/ads fits the region), and that "one-size-fits-all" localization may not be effective. The page gives no nationality breakdown. — [UAEU Research portal](https://research.uaeu.ac.ae/en/publications/arabic-mobile-game-localizations-gamer-profiles-preferences-and-i-2/)
- A separate 2022 study found most Arab gamers prefer **"partially localized"** games (Arabic text but no Arabic dubbing or re-voiced cutscenes) over fully localized ones, and proposed "localization levels". (Seen via search summary; the full text was not fetched.) — [UAEU: Current trends in localizing video games into Arabic](https://research.uaeu.ac.ae/en/publications/current-trends-in-localizing-video-games-into-arabic-localization/)
- Altagram (game LSP, undated page, ©2026): "Text localization tends to always be done in MSA, because it is cost-effective and scalable", and MSA gives a standard quality metric. Dialects are "more flexible and vibrant" and suit dubbing. MSA can sound stiff in voiced pop-culture content. Marketing and copywriting often use a neutral **"White Arabic"**. A high-register translation can alienate players in fantasy games. Children's dubbing uses "toned-down MSA". — [Altagram](https://altagram.com/challenges-in-arabic-localization-altagram/)
- Altagram on dialect reach: Egyptian is the most widely understood dialect because of the region's media output. Gulf Arabic is an umbrella term, understood less widely than Egyptian, and suits projects aimed at a specific Gulf market (a large share of Arab players). Levantine is growing in dubbing. Maghrebi is the least accessible region-wide. — [Altagram](https://altagram.com/challenges-in-arabic-localization-altagram/)
- Inlingo × Belka Games case study (Solitaire Cruise, Arabic added in 2021; PocketGamer.biz, 22 Aug 2022): the game was translated into MSA because "MSA is understood in all Arab countries", and the style guide **explicitly prevents dialectal forms**. — [PocketGamer.biz](https://www.pocketgamer.biz/cruise-to-the-east-how-to-successfully-localize-a-game-into-arabic/)
- Microsoft Arabic (ara-SAU) Localization Style Guide: "a more informal, playful and inspiring tone may be used for most Microsoft products, games etc.", versus formal and factual for technical text. Voice-over should use "the right language variant/dialect/accent". — [Microsoft ara-sau Style Guide (PDF)](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Vendor marketing view (via search snippet, not verified page by page): MSA for strategy, historical RPG and text-heavy games; **Gulf Arabic for casual, sports and competitive games**; **Egyptian for mass-market mobile** aimed at the widest audience. — [Tarjama](https://tarjama.com/how-to-localize-your-game-to-conquer-the-mena-market/) (practitioner opinion, no data)
- Tamatem (Jordan-based Arabic mobile publisher) says it "included local dialects and colloquialisms to enhance the immersive experience" (July 2024). Its users skew heavily Saudi: about **70% Saudi Arabia, 20% rest of GCC** (2016), and about 70% Saudi at Series B. — [Tamatem blog](https://tamatem.co/industry/the-role-of-cultural-sensitivity-in-game-localization-how-tamatem-navigates-cultural-nuances/); [Wamda 2016](https://www.wamda.com/index.php/en/2016/08/tamatem-18-million-users); [TechCrunch 2018](https://techcrunch.com/2018/02/01/tamatem/)

### Inferences
- Suggested per-content-type defaults (synthesized from the sources above, not measured):
  - **In-game UI, buttons, system messages, IAP/store UI, legal**: MSA (single shared `ar` string set).
  - **Tutorial**: plain, short MSA, avoiding high-register vocabulary (Altagram's warning about alienating players).
  - **Character dialogue (text)**: "light MSA" (MSA grammar and simple vocabulary, a few widely understood colloquial interjections). Full dialect only if the title targets one market.
  - **VO**: per Altagram/Microsoft, dialect or "white" (pan-regional) voice is acceptable, but the 2022 survey suggests many players don't demand Arabic VO at all, so VO is a low-priority cost.
  - **Push notifications and UA ad creatives**: Altagram's "White Arabic for marketing" plus the vendor genre view support a light-colloquial register. A Gulf (Saudi-leaning) variant is the obvious candidate given Saudi revenue weight (Tamatem 70%). This is not backed by any published A/B data.
  - **App Store / Google Play listings**: MSA for title, subtitle and keywords (search terms are MSA and must match across countries). Promotional text and screenshots can carry the lighter marketing register.
- Encode register as a per-string-category attribute (`register: msa | light | dialect`) rather than per locale, because most strings stay MSA in every country.

### Gaps
- No public player study measures register preference per content type (push, UA ads, store copy) or per country. The 382-player survey has no country split available on the abstract page.
- No published A/B test results (CTR/IPM) comparing MSA and dialect UA creatives in MENA were found.
- Najdi vs Hejazi (within-Saudi) preference for marketing copy: no source found.

## 2. Dialect clusters: which countries can share one variant

### Takeaway
Arabic NLP work usually groups dialects into five regions: Egypt, Gulf, Iraq, Levant, Maghreb. Closely related dialects are hard to separate even for classifiers, which supports one Gulf variant for SA/AE/KW/QA/BH/OM and one Levantine variant for JO/LB/SY/PS. Egypt, Iraq and Yemen are the outliers if dialect strings are produced at all. CLDR's month-name data splits along a different line (Levant plus Iraq vs Gulf plus Egypt plus Yemen), so the dialect cluster and the locale-data cluster are not the same thing.

### Cited Findings
- Dialect-ID datasets commonly use five regions, **Egypt, Gulf, Iraq, Levant, North Africa/Maghreb**, with Gulf and Levant kept separate. — [Similarities between Arabic Dialects (arXiv 2105.04221)](https://arxiv.org/pdf/2105.04221) (via search summary)
- MADAR covers 25 city dialects plus MSA in a travel-domain parallel corpus. The MADAR shared task had a 21-country Twitter subtask and a 25-city subtask. — [MADAR LREC 2018](https://camel.abudhabi.nyu.edu/madar/static/pdfs/2018-LREC-MADAR-Resources.pdf); [NADI 2020 (21 countries)](https://arxiv.org/pdf/2010.11334)
- Error analysis of MADAR-26 (Olsen, Touileb and Velldal, ArabicNLP 2023): **identical sentences appear across dialect classes**, and no tested approach captures "the subtle distinctions between closely related dialects". — [ACL Anthology 2023.arabicnlp-1.30](https://preview.aclanthology.org/credits/2023.arabicnlp-1.30)
- Altagram describes "Gulf Arabic" as an umbrella for several dialects and groups Lebanon, Syria, Palestine and Jordan as Levantine. — [Altagram](https://altagram.com/challenges-in-arabic-localization-altagram/)
- CLDR 48 month-name split: **ar-IQ, ar-JO, ar-LB, ar-SY, ar-PS** use Syriac-derived names (كانون الثاني …). **ar-SA, AE, KW, QA, BH, OM, YE, EG** use transliterated Gregorian names (يناير …). — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)

### Inferences
- Recommended string variants (if dialect strings exist at all):
  - `ar` (MSA master): all 13 countries.
  - `ar-x-gulf` (Khaleeji, Saudi-leaning): SA, AE, KW, QA, BH, OM. The cross-Gulf intelligibility risk is low.
  - `ar-x-levant`: JO, LB, SY, PS.
  - `ar-EG` dialect: Egypt only. Egyptian is also the most widely understood fallback for humour.
  - Iraq and Yemen: fall back to MSA or "light MSA". A Gulf variant is a weak fit for Iraq (a separate NLP region) and only partially fits Yemen.
- Keep **dialect variant** and **locale formatting** as two independent config axes. Example: ar-IQ = MSA strings + Levant-style month names + Arabic-Indic digits + Fri–Sat weekend. ar-AE = Gulf strings + Latin digits + Sat–Sun weekend.

### Gaps
- No source quantifies how acceptable Saudi-flavoured Gulf copy is to Omani, Kuwaiti or Emirati players, or how acceptable Gulf copy is to Yemeni players.
- Per-pair confusion numbers (e.g., Kuwaiti vs Qatari) from NADI/MADAR were not extracted. Only the qualitative conclusion is cited.

## 3. Numerals (CLDR default vs player expectation)

### Takeaway
In CLDR 48, **only ar-AE (and generic `ar`) default to Latin digits (`latn`)**. The other 12 Middle East locales default to Arabic-Indic (`arab`) with the Arabic separators ٬ and ٫. Microsoft's Saudi Arabic style guide, however, says to "always use the Western Arabic Numbers (1, 2, 3…)". A game should therefore treat numbering system as an explicit per-locale config value, not rely on the CLDR default.

### Cited Findings
- CLDR 48 default numbering system per locale (`Intl.NumberFormat(tag).resolvedOptions().numberingSystem`) — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48):
  - `arab`: ar-SA, ar-KW, ar-QA, ar-BH, ar-OM, ar-YE, ar-IQ, ar-JO, ar-LB, ar-SY, ar-PS, ar-EG → `1234567.89` = `١٬٢٣٤٬٥٦٧٫٨٩` (thousands U+066C ٬, decimal U+066B ٫); percent `٢٥٪؜` (U+066A plus ALM U+061C).
  - `latn`: **ar-AE** and **generic `ar`** → `1,234,567.89`; percent `25‎%‎` (with LRM marks).
  - Maghreb (relevant only to an `ar` fallback): ar-MA, ar-DZ, ar-TN, ar-LY = `latn` with **European separators** `1.234.567,89`.
- Override syntax works: `ar-SA-u-nu-latn` → `1,234,567.89`. Hijri date with Latin digits: `ar-SA-u-ca-islamic-umalqura-nu-latn` → `الثلاثاء، 2 جمادى الأولى 1448 هـ`. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- **History / version change:** in 2019 a CLDR maintainer wrote that for Arabic "the default is to use 'native' (Arabic-script) digits", that Morocco and Algeria override to ASCII digits, that "the data for all Arabic regional variants has overrides for the region preference" so generic `ar` could change without affecting region locales, and that some had "proposed to change the generic Arabic default to ASCII digits". — [CLDR-users, Apr 2019](https://corp.unicode.org/pipermail/cldr-users/2019-April/000917.html). A WebKit bug noted that stock/Apple ICU then used `arab` for `ar` while Google's fork used `latn` (CLDR-10825 `latndigi` alternate). — [WebKit bug 236121](https://bugs.webkit.org/show_bug.cgi?id=236121). In CLDR 48, generic `ar` now resolves to `latn` and ar-AE to `latn` (runtime observation above), so the change was made at some version between 2019 and 48.
- CLDR 48 release notes have **no Arabic-specific numbering change**. They do say number patterns without an explicit numberSystem were finally removed. — [CLDR 48 release notes](https://cldr.unicode.org/downloads/cldr-48)
- Microsoft Arabic style guide (ara-SAU): "As a general rule, always use the Western Arabic Numbers (1, 2, 3, 4, 5, etc.) which are becoming standard almost all over the Arab World." It also says: 0 is removed ("0 students" → لا يوجد طلاب); 1 is spelled out (طالب واحد); 2 uses the dual (طالبان); version numbers keep a period (الإصدار 4.2). — [Microsoft ara-sau Style Guide](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- RTL bidi bug in practice: Solitaire Cruise prices were mirrored, so **$4.99 displayed as $99.4**. Spreadsheets and doc editors can also corrupt mixed Arabic/Latin strings. — [PocketGamer.biz](https://www.pocketgamer.biz/cruise-to-the-east-how-to-successfully-localize-a-game-into-arabic/)

### Inferences
- Pipeline default suggestion: `nu=latn` for all 13 locales in gameplay HUD (scores, timers, coin counts, level numbers). This matches Microsoft's guidance and the ar-AE/`ar` CLDR default, and it avoids ICU-version drift. Expose `arab` as an optional per-locale override (most likely wanted for formal content in EG/SA/IQ). This is a product decision, because the CLDR default and the Microsoft guidance conflict for ar-SA.
- **Fallback trap:** if a pipeline falls back from an unsupported region tag (e.g., `ar-SD`, or a device reporting `ar`) to `ar`, it gets Latin digits, while `ar-SA` gets Arabic-Indic. Players in neighbouring countries could see different digits for the same build. Pin `nu` explicitly.
- Store-platform rendering (iOS and Android system digit settings) can override app formatting if the app uses the system locale formatter. Test both device settings.

### Gaps
- The exact CLDR version where generic `ar` (and ar-AE) switched to `latn` was not confirmed in release notes. Checking `common/main/ar.xml` and `ar_AE.xml` history in the CLDR GitHub would settle it.
- No player survey on digit preference by country was found. The Al-batineh abstract does not cover numerals.
- The default digits iOS and Android show for each Arabic region in 2026 were not verified.

## 4. Dates, calendars, first day of week, weekend

### Takeaway
CLDR 48 uses the **Gregorian calendar by default for all 13 locales, including ar-SA**. Hijri (Umm al-Qura) is opt-in via `-u-ca-islamic-umalqura`. Month names split into Levant+Iraq (Syriac names) and the rest (transliterated). Week data varies: Saturday-first is most common, Sunday-first in SA/YE, Monday-first in AE/LB/PS. The weekend is Fri–Sat almost everywhere except AE/LB/PS, which are Sat–Sun in CLDR.

### Cited Findings
- Default calendar `gregory` for every ar-XX tested. Long date for 15 Jan 2026: ar-SA `١٥ يناير ٢٠٢٦`; ar-AE `15 يناير 2026`; ar-IQ/JO/LB/SY/PS `١٥ كانون الثاني ٢٠٢٦`. Short date `١٥‏/١‏/٢٠٢٦` (d/M/y with RLM U+200F after each separator). Time `٢:٠٥ م`; all 13 ME locales use **h12 with ص/م** (ar-MA uses h23). — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- Month name sets (CLDR 48) — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48):
  - Transliterated (SA, AE, KW, QA, BH, OM, YE, EG, and generic `ar`): يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر
  - Syriac/Levantine (IQ, JO, LB, SY, PS): كانون الثاني شباط آذار نيسان أيار حزيران تموز آب أيلول تشرين الأول تشرين الثاني كانون الأول
  - Maghreb (only for an `ar` fallback): ar-DZ/TN use French-derived names (جانفي، أفريل); ar-MA uses شتنبر for September.
- Weekday names (ar-SA): الأحد الاثنين الثلاثاء الأربعاء الخميس الجمعة السبت. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- Hijri formatting for 13 Oct 2026: `ar-SA-u-ca-islamic-umalqura` → `الثلاثاء، ٢ جمادى الأولى ١٤٤٨ هـ`. `ar-EG-u-ca-islamic-civil` → `١ جمادى الأولى ١٤٤٨ هـ`, so **tabular Islamic and Umm al-Qura can differ by a day**. CLDR 48 also adds a new era "Before Hijri" (`bh`) to all Islamic calendars. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48); [CLDR 48 release notes](https://cldr.unicode.org/downloads/cldr-48)
- Saudi Arabia moved government dealings to the Gregorian calendar effective **1 Oct 2016**, as a cost-cutting measure. Hijri remains for religious dates. — [Anglican Ink 2016](https://anglican.ink/2016/10/08/saudi-arabia-adopts-gregorian-calendar). In a later Council of Ministers decision (reported Nov 2023, not cross-checked), **all durations in official procedures are calculated in Gregorian**, except durations tied to Sharia rulings or explicitly stipulated in Hijri. — [Gulf News](https://gulfnews.com/world/gulf/saudi/saudi-arabia-adopts-gregorian-calendar-use-in-official-dealings-1.99118179)
- .NET `UmAlQuraCalendar` uses a table licensed from the Saudi government and supports only **1900-04-30 to 2077-11-16 (Gregorian)**. — [Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/api/system.globalization.umalquracalendar)
- CLDR 48 week data (`Intl.Locale.getWeekInfo()`; 1=Mon … 7=Sun) — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48):

  | Locale | firstDay | weekend |
  |---|---|---|
  | ar-SA | 7 (Sun) | Fri–Sat |
  | ar-YE | 7 (Sun) | Fri–Sat |
  | ar-AE | 1 (Mon) | **Sat–Sun** |
  | ar-LB | 1 (Mon) | Sat–Sun |
  | ar-PS | 1 (Mon) | Sat–Sun |
  | ar-KW, QA, BH, OM, IQ, JO, SY, EG | 6 (Sat) | Fri–Sat |

- Real-world weekend policy: the **UAE federal government moved to a Sat–Sun weekend (plus a Friday half-day) from 1 Jan 2022**. Before that it was Fri–Sat. **Sharjah uses a Fri–Sat–Sun** three-day weekend. Private companies may differ. — [Khaleej Times](https://www.khaleejtimes.com/uae/government/new-uae-weekend-and-working-hours-in-2022-all-your-questions-answered); [Gulf News (Sharjah)](https://gulfnews.com/uae/education/new-uae-weekend-sharjah-private-schools-to-have-three-days-off-1.84348363). **Saudi Arabia moved from Thu–Fri to Fri–Sat in 2013**, aligning with Bahrain, Kuwait, Oman, Qatar and the then-UAE. — [Fox News / AP](https://www.foxnews.com/world/saudi-arabia-moves-to-friday-saturday-weekend-to-align-with-region); [The National: weekend in the Arab world](https://thenationalnews.com/mena/2021/12/07/when-is-the-weekend-in-the-arab-world)
- CLDR 48 changed the default week-numbering mechanism to be identical to ISO, rather than based on the calendar week. — [CLDR 48 release notes](https://cldr.unicode.org/downloads/cldr-48)

### Inferences
- LiveOps scheduling ("weekend event", "Friday reward") should key off a per-country weekend config, not a single MENA value. Friday is the peak day in Fri–Sat countries. In the UAE Friday is a half working day, and in Sharjah it is a day off.
- Show Gregorian dates by default in all 13 countries. Show Hijri only for religious/seasonal events (Ramadan, Eid), using `islamic-umalqura` (Saudi official) rather than `islamic-civil`. The actual start of Ramadan is announced by moon sighting and can differ by country and from the computed date, so drive event start times from server config, not on-device calendar math.
- If Unity uses .NET `CultureInfo("ar-SA")`, check the default calendar and digits. On Windows/.NET Framework, ar-SA has historically defaulted to a Hijri calendar (unverified here; see Gaps), which can produce Hijri dates in `DateTime.ToString()`. Format with `CultureInfo.InvariantCulture` plus explicit patterns, or use an ICU-backed formatter.

### Gaps
- **ar-PS week data (Mon-first, Sat–Sun weekend) looks doubtful**: Palestinian practice is generally thought to include Friday. No authoritative source on the Palestinian official weekend was found. Verify before relying on CLDR for PS.
- ar-LB: CLDR says Sat–Sun. The real-world official schedule (Saturday half-day for some sectors) was not verified.
- Whether .NET/Mono in Unity (IL2CPP on Android/iOS) defaults `ar-SA` to the UmAlQura or Hijri calendar was not confirmed. The Microsoft doc fetched does not state the ar-SA default.
- How widely Iraqi and Levantine players expect the Syriac month names in a game UI, versus accepting يناير-style names, was not found. Syrian/Lebanese/Jordanian print media often show both, which is not verified here.

## 5. Currency: symbols, codes, separators, placement, new symbols

### Takeaway
CLDR 48 still formats SAR as `ر.س.‏` and AED as `د.إ.‏`, **after** the number. The new official signs (Saudi riyal U+20C1, Unicode 17.0; UAE dirham U+20C3, Unicode 18.0; Omani rial U+20C4, Unicode 18.0) are not yet CLDR primary symbols and lack broad font support. Both central banks specify that the new sign goes **before** the number. Several currencies use 3 or 0 fraction digits, which a price formatter must respect.

### Cited Findings
- CLDR 48 currency formatting of 1234.5 (`style:'currency'`, default symbol; all strings begin with RLM U+200F) — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48):

  | Locale | ISO | Default output | Decimals | Narrow symbol | Name (n=3) |
  |---|---|---|---|---|---|
  | ar-SA | SAR | `١٬٢٣٤٫٥٠ ر.س.‏` | 2 | ر.س.‏ | ريال سعودي |
  | ar-AE | AED | `1,234.50 د.إ.‏` | 2 | د.إ.‏ | درهم إماراتي |
  | ar-KW | KWD | `١٬٢٣٤٫٥٠٠ د.ك.‏` | **3** | د.ك.‏ | دينار كويتي |
  | ar-QA | QAR | `١٬٢٣٤٫٥٠ ر.ق.‏` | 2 | ر.ق.‏ | ريال قطري |
  | ar-BH | BHD | `١٬٢٣٤٫٥٠٠ د.ب.‏` | **3** | د.ب.‏ | دينار بحريني |
  | ar-OM | OMR | `١٬٢٣٤٫٥٠٠ ر.ع.‏` | **3** | ر.ع.‏ | ريال عماني |
  | ar-YE | YER | `١٬٢٣٥ ر.ي.‏` | **0** | ر.ي.‏ | ريال يمني |
  | ar-IQ | IQD | `١٬٢٣٥ د.ع.‏` | **0** | د.ع.‏ | دينار عراقي |
  | ar-JO | JOD | `١٬٢٣٤٫٥٠٠ د.أ.‏` | **3** | د.أ.‏ | دينار أردني |
  | ar-LB | LBP | `١٬٢٣٥ ل.ل.‏` | **0** | **L£** | **جنيه لبناني** |
  | ar-SY | SYP | `١٬٢٣٥ ل.س.‏` | **0** | **£** | ليرة سورية |
  | ar-PS | ILS (CLDR default) | `١٬٢٣٤٫٥٠ ₪` | 2 | ₪ | — |
  | ar-PS | JOD | `١٬٢٣٤٫٥٠٠ د.أ.‏` | 3 | د.أ.‏ | دينار أردني |
  | ar-EG | EGP | `١٬٢٣٤٫٥٠ ج.م.‏` | 2 | **E£** | جنيهات مصرية |
  | `ar` | USD | `1,234.50 US$` | 2 | — | — |
- Code display: `‏1,234.50 AED` / `‏١٬٢٣٤٫٥٠ SAR`. `en-SA` formats `SAR 10.00`. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- **Saudi riyal sign**: approved by King Salman on 20 Feb 2025 and announced by SAMA. Encoded **U+20C1 SAUDI RIYAL SIGN** in **Unicode 17.0 (released 9 Sep 2025)**. It is distinct from U+FDFC RIAL SIGN (in Unicode since 2002, RTL-only, tied to the Iranian rial). The new sign must work in both directions. — [Unicode blog, 13 Mar 2025](https://blog.unicode.org/2025/03/support-for-new-saudi-riyal-currency.html); [SAMA proposal L2/25-075](https://www.unicode.org/L2/L2025/25075-saudi-central-bank.pdf); [SEW recommendation L2/25-076](https://www.unicode.org/L2/L2025/25076-sew-recommendations-saudi-riyal.pdf)
- SAMA usage rules: the sign goes **to the left of the number in all languages, with a space**; its direction follows the surrounding text; there are eight rules in total (proportion, height alignment, clear space = 1/3 of symbol height, contrast). A preliminary CLDR update (Oct 2025) classed U+20C1 as an **alternate**, not the primary, symbol because of limited font support. — [Wikipedia: Saudi riyal sign](https://en.wikipedia.org/wiki/Saudi_riyal_sign). Confirmed: CLDR 48 default and narrow SAR symbols are still `ر.س.‏`. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- **UAE dirham sign**: unveiled by the Central Bank of the UAE on **27 Mar 2025**. Encoded **U+20C3 UAE DIRHAM SIGN** in **Unicode 18.0 (Sept 2026)**, alongside **U+20C4 OMANI RIAL SIGN** and U+20C2 RUFIYAA SIGN. Device support depends on Apple, Google, Samsung and Microsoft shipping Unicode 18 fonts and keyboards. The CBUAE style guide suggests the 6 key on keyboards. — [The National, 22 Sep 2026](https://thenationalnews.com/future/technology/2026/09/22/uae-dirham-symbol-keyboard-unicode); [tbreak](https://tbreak.com/uae-dirham-symbol-unicode-18-0/). CBUAE: the symbol must always come **before** the numeral, and a standard short form was introduced (previously only AED/Dhs/Dh). — [Gulf News: how to use the new dirham symbol](https://gulfnews.com/business/banking/how-to-use-the-new-uae-dirham-symbol-the-right-way-spot-incorrect-use-1.500160926); [Gulf News: CBUAE 8 mistakes](https://gulfnews.com/business/banking/watch-uae-central-bank-warns-of-8-mistakes-when-using-new-dirham-symbol-1.500253031) (via search summary)
- Font and OS support for U+20C1 was still lagging in 2026 per vendor guides; until supported, a .notdef box shows. — [riyal.js.org guide (2026-05-08)](https://riyal.js.org/blog/saudi-riyal-symbol-in-react/); [Unicode blog](https://blog.unicode.org/2025/03/support-for-new-saudi-riyal-currency.html)

### Inferences
- For real-money prices, use the store-provided localized price string (Google Play Billing `formattedPrice`, StoreKit `displayPrice`/`priceLocale`) rather than formatting yourself. It reflects the store's currency and symbol choice and avoids bidi bugs like Solitaire Cruise's $99.4.
- To show the new Saudi, UAE or Omani signs in-game, embed the glyph in your own font (TextMeshPro atlas or sprite) mapped to U+20C1/U+20C3/U+20C4, and **place it before the number** with a space, per SAMA and CBUAE. That is the opposite of CLDR's trailing `ر.س.‏`. Keep CLDR's abbreviation as a fallback while fonts lack support.
- **CLDR display-name quirk**: CLDR names LBP "جنيه لبناني", but the Lebanese currency is normally called الليرة اللبنانية (the narrow `L£` and `ل.ل.‏` reflect "livre/lira"). Syria's narrow symbol is a bare `£`. Override these rather than relying on CLDR names or narrow symbols. (Common knowledge, not sourced here.)
- Palestine has no single currency: ILS is the CLDR default; JOD and USD are also in common use (not sourced here). Store prices will come from the storefront's currency anyway.

### Gaps
- The exact CBUAE dirham short form and the official SAMA/CBUAE PDF guidelines were not fetched directly (facts come from Wikipedia and Gulf News).
- Whether CLDR 49 (due 2026) or a later version will promote U+20C1 or U+20C3 to primary symbols was not confirmed.
- Apple/Google/Microsoft font shipping status for U+20C1 and U+20C3 as of Oct 2026 was not verified.
- Iraq and Lebanon have very high nominal prices (0-decimal currencies with large values). Whether stores price in local currency or USD in those countries was not checked.

## 6. Gaming vocabulary differences and gender-neutral player addressing

### Takeaway
Little published, sourced data exists on country-by-country gaming vocabulary. Practitioner guidance converges on a single MSA glossary and on gender-neutral addressing via **verbal nouns (masdar)**, collective/plural nouns, and "يُرجى + masdar" instead of masculine imperatives. Masculine remains the grammatical default when neutrality is impossible.

### Cited Findings
- Arabic nouns, verbs and adjectives are masculine or feminine, and masculine is the default. For gender neutrality the Solitaire Cruise team used **verbal nouns (masdar)**, e.g. **شراء** for the "Buy" button, because Arabic has no neutral infinitive. They maintained a glossary and a style guide with native speakers. — [PocketGamer.biz (Inlingo/Belka, 2022)](https://www.pocketgamer.biz/cruise-to-the-east-how-to-successfully-localize-a-game-into-arabic/)
- Microsoft ara-SAU style guide on gender: use gender-neutral alternatives and collective nouns (e.g., فريق عمل instead of موظفون/موظفات; الحضور instead of المشاركون/المشاركات; فريق المبيعات instead of مندوب مبيعات); use both forms for roles (معلم ومعلمة); use plural nouns for generalizations (الأشخاص، الأفراد). In instructions, **avoid the imperative** and use **يجب/يمكنك/يُرجى + masdar** or a masdar preceded by "following the steps below". Example: للاتصال بأحد الأشخاص، يُرجى تحديد اسم هذا الشخص… rather than حدد اسمه. Tooltips use a masdar (عرض الصفحات بأكملها… rather than choosing تعرض/يعرض). Gender-neutral language applies to new content, and legacy text need not be updated. — [Microsoft ara-sau Style Guide](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- Microsoft on plurals: English plural maps to the Arabic dual or plural depending on count. Example: "Spin Arrows" → **سهمان** (dual), not أسهم. Colloquialisms and idioms are replaced with a natural Arabic equivalent or the meaning is translated. — [Microsoft ara-sau Style Guide](https://download.microsoft.com/download/5/6/d/56d1774f-ac3f-4ad9-80af-a6dfd5df419d/ara-sau-StyleGuide.pdf)
- CLDR plural categories for Arabic: **zero / one / two / few (3–10) / many (11–99) / other (100+, and 0 decimals)**. Tested: 0→zero, 1→one, 2→two, 3→few, 11→many, 100→other. The ordinal rule is `other` for all values. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- Content sensitivities affecting vocabulary and assets: references to pigs were removed from a LiveOps event; some translators declined the card game as gambling-adjacent; Ramadan and national-day events were reviewed by native speakers; for Saudi/UAE national-day events players wear flag colours, and women's outfits must cover the skin. — [PocketGamer.biz](https://www.pocketgamer.biz/cruise-to-the-east-how-to-successfully-localize-a-game-into-arabic/). Tamatem changed music some Saudi players would consider religiously forbidden. — [GamesBeat](https://gamesbeat.com/tamatem-has-built-a-thriving-mobile-business-by-bringing-games-to-the-arab-world/)
- The 382-player survey found **female players dominant** among Arab mobile gamers. — [UAEU Research portal](https://research.uaeu.ac.ae/en/publications/arabic-mobile-game-localizations-gamer-profiles-preferences-and-i-2/)

### Inferences
- Because female players dominate casual mobile in the survey, masculine-default imperatives (e.g., العب، اجمع) address the majority in the wrong gender. Use masdar CTAs (شراء، جمع، متابعة، إعادة المحاولة), noun-phrase labels, and passive/impersonal notifications. For dialogue that must address the player directly, consider storing a player-gender variant (ICU `select` on gender), defaulting to masdar or neutral phrasing.
- Use full ICU MessageFormat plural selectors with all six categories for counts (lives, coins, levels). For 0/1/2, follow Microsoft's pattern (لا يوجد / spelled-out واحد / dual) rather than "0 قلوب".
- Candidate MSA glossary terms. **These are unsourced, from general knowledge; native review is required**: coins = عملات (or عملات ذهبية); gems = جواهر / أحجار كريمة; level = مستوى (or مرحلة for a stage); lives = أرواح / قلوب (hearts); shop = متجر; gift = هدية; rewards = مكافآت; daily bonus = مكافأة يومية; booster = معزِّز. Loanword transliterations (ليفل، كوينز) are common in Gulf and Egyptian gamer slang but should be limited to marketing copy (unverified).
- Compact number formats are handy for coin counters: `١٫٣ مليون` / `١٣ ألف` (arab) or `1.3 مليون` / `13 ألف` (latn). Relative time: `أمس`, `خلال ٣ ساعات`. List: `ذهب وفضة وماس`. — values from [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)

### Gaps
- **No sourced, country-by-country gaming vocabulary comparison was found** (e.g., whether Egyptian, Saudi or Levantine players use different words for coins, lives or shop). Vendor pages (Altagram, Tarjama, Inlingo) give no term lists. Building this needs native-player glossary review or a term survey.
- No source compares player reaction to masculine-default vs gender-neutral vs dual-form ("you" m/f) addressing in games.
- Apple and Google Arabic store and localization guidelines were not fetched.

## 7. CLDR/ICU data a pipeline should pull rather than hard-code, plus per-locale config summary

### Takeaway
Pull formatting data (numbers, currency, dates, months, plural rules, week data) from ICU/CLDR at a **pinned CLDR version**. Explicitly override the fields where CLDR conflicts with product policy or reality: numbering system, currency symbol and placement for SAR/AED/OMR, LBP/SYP names, and PS week data. CLDR defaults have changed across versions (generic `ar` digits), so a version bump can silently change output.

### Cited Findings
- CLDR fields to pull, with the BCP 47 `-u-` extensions that override them: numbering system (`-u-nu-latn|arab`), calendar (`-u-ca-gregory|islamic-umalqura|islamic-civil`), hour cycle (`-u-hc-h12|h23`), first day of week (`-u-fw-`), plus currency data, plural rules (6 categories), month and day names, and compact/relative/list patterns. All were exercised and work in ICU 78.3/CLDR 48. `Intl.supportedValuesOf('calendar')` includes `islamic-umalqura`. — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48)
- CLDR 48 removed deprecated number patterns that lack an explicit numberSystem, changed default week numbering to ISO-identical, and added the `bh` era for Islamic calendars. RBNF rules (including `ar-OrdinalRules.txt`) are now referenced via `_rbnfRulesFile` in JSON. — [CLDR 48 release notes](https://cldr.unicode.org/downloads/cldr-48)
- Regional Arabic locales carry their own overrides, so a change to `ar` doesn't propagate to them, and vice versa. — [CLDR-users 2019](https://corp.unicode.org/pipermail/cldr-users/2019-April/000917.html)
- Per-locale snapshot (CLDR 48 values; "Weekend" column for AE also matches the 2022 federal change) — [CLDR 48 via ICU 78.3 runtime](https://cldr.unicode.org/downloads/cldr-48); [Khaleej Times](https://www.khaleejtimes.com/uae/government/new-uae-weekend-and-working-hours-in-2022-all-your-questions-answered):

  | Locale | CLDR nu | Separators | Months | firstDay | Weekend | Currency (CLDR symbol, dp) | Cluster (dialect) |
  |---|---|---|---|---|---|---|---|
  | ar-SA | arab | ٬ ٫ | يناير | Sun | Fri–Sat | SAR ر.س.‏ 2 (new U+20C1 before number) | Gulf (Najdi/Hejazi) |
  | ar-AE | **latn** | , . | يناير | Mon | **Sat–Sun** | AED د.إ.‏ 2 (new U+20C3 before number) | Gulf |
  | ar-KW | arab | ٬ ٫ | يناير | Sat | Fri–Sat | KWD د.ك.‏ 3 | Gulf |
  | ar-QA | arab | ٬ ٫ | يناير | Sat | Fri–Sat | QAR ر.ق.‏ 2 | Gulf |
  | ar-BH | arab | ٬ ٫ | يناير | Sat | Fri–Sat | BHD د.ب.‏ 3 | Gulf |
  | ar-OM | arab | ٬ ٫ | يناير | Sat | Fri–Sat | OMR ر.ع.‏ 3 (new U+20C4) | Gulf |
  | ar-YE | arab | ٬ ٫ | يناير | Sun | Fri–Sat | YER ر.ي.‏ 0 | Yemeni |
  | ar-IQ | arab | ٬ ٫ | **كانون الثاني** | Sat | Fri–Sat | IQD د.ع.‏ 0 | Iraqi |
  | ar-JO | arab | ٬ ٫ | **كانون الثاني** | Sat | Fri–Sat | JOD د.أ.‏ 3 | Levantine |
  | ar-LB | arab | ٬ ٫ | **كانون الثاني** | Mon | Sat–Sun | LBP ل.ل.‏ 0 | Levantine |
  | ar-SY | arab | ٬ ٫ | **كانون الثاني** | Sat | Fri–Sat | SYP ل.س.‏ 0 | Levantine |
  | ar-PS | arab | ٬ ٫ | **كانون الثاني** | Mon (?) | Sat–Sun (?) | ILS ₪ 2 | Levantine |
  | ar-EG | arab | ٬ ٫ | يناير | Sat | Fri–Sat | EGP ج.م.‏ 2 | Egyptian |
  | ar (fallback) | **latn** | , . | يناير | Sat | Fri–Sat | — | MSA |

### Inferences
- Minimal per-locale config to encode (everything else comes from CLDR): `{ stringVariant: msa|gulf|levant|egypt, nu: latn|arab (explicit), calendarDefault: gregory, hijriCalendar: islamic-umalqura, currencySymbolOverride: {SAR:'⃁', AED:'⃃', OMR:'⃄'} + placement: before, fontHasGlyph: bool, weekendOverride (PS, LB, Sharjah), currencyNameOverride (LBP→ليرة لبنانية) }`.
- Pin the ICU/CLDR version in the build (Unity's Localization package uses .NET `CultureInfo`, which on IL2CPP/Mono may not match ICU/CLDR). Snapshot-test formatted strings per locale so a CLDR bump (e.g., generic `ar` digits, U+20C1 becoming primary) shows up as a test diff, not a player-facing change.
- Bidi handling: CLDR strings contain RLM (U+200F), ALM (U+061C) and LRM (U+200E) marks. TextMeshPro and RTL plugins must preserve or handle these. Removing them reintroduces the mirrored-price bug.

### Gaps
- Unity's own Arabic locale handling (Localization package, `CultureInfo` data source per platform, IL2CPP globalization mode) was not researched here.
- CLDR 49 data (if released by Oct 2026) was not checked. The values above are CLDR 48.
