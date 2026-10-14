# Arabic game localization style guide (English → Arabic)

Version 2026-10-13.1, draft. A native Arabic lead linguist must sign this off before it is treated as final. This one document is the spec for translators, reviewers and the LLM pipeline, so a rule changed here changes all three.

## Who reads our Arabic

One Modern Standard Arabic (MSA) master ships to all 13 markets: Saudi Arabia, UAE, Kuwait, Qatar, Bahrain, Oman, Yemen, Iraq, Jordan, Lebanon, Syria, Palestine and Egypt. Players in surveys prefer MSA for on-screen game text, and MSA is the only variety every one of these players reads comfortably. Per-country differences (digits, dates, currency, content flags) are handled in game config, not in the strings. Only marketing text gets dialect versions (section 2).

More than a third of players in the region are women, and many are teenagers. Write friendly, clear, modern game Arabic that reads as if an Arab game writer wrote it. Translate meaning, not words; a literal translation that sounds foreign is an error.

## 1. Register by content type

| type | Register |
|---|---|
| ui | Plain, short MSA. Buttons and labels are 1–3 words. |
| tutorial | Short, simple, low-register MSA. One instruction per sentence. |
| dialogue | "Light MSA": MSA grammar, simple everyday vocabulary, warm and playful, matched to the character. Avoid classical or literary constructions. |
| legal | Precise, formal MSA. Never simplify legal meaning. |
| push, ad, store | `ar` is "White Arabic": simple, friendly MSA that sounds natural in every country. Dialect versions go in the overlays. |

## 2. Dialect overlays (push, ad and store only)

Overlays are requested only for push, ad and store strings. Each one must carry the same meaning, call to action and placeholders as the master.

- `gulf`: everyday Gulf (Khaleeji) Arabic understood across Saudi Arabia, UAE, Kuwait, Qatar, Bahrain and Oman. Neutral urban Gulf, not one city's slang. Typical markers: الحين، يلا، تبي/تبغى.
- `levant`: everyday urban Levantine for Jordan, Lebanon, Syria and Palestine. Typical markers: هلّق، كتير، بدّك، شو.
- `egypt`: everyday Cairene Egyptian. Typical markers: دلوقتي، أوي، عايز، إيه.

An overlay must actually sound like that dialect. An MSA sentence placed in the `gulf` field is an error. Never mix two dialects in one string. Write in Arabic script only (no Arabizi), and use no vulgar slang. If a dialect version would sound forced, write it close to White Arabic and say so in `note`.

## 3. Addressing the player (gender)

English "you" has no gender, but Arabic does. Because so many players are women, a masculine default is an error, not a style choice. The written forms below are gender-neutral:

- **Verbal nouns for buttons and labels**, not imperatives: شراء (Buy), متابعة (Continue), إعادة المحاولة (Retry), تخطي (Skip), جمع (Collect), فتح (Unlock), بدء (Start).
- **Possessive ـك and past-tense ـت** are neutral when unvocalized: لديك، مكافأتك، حصلت على. Never add the vowel marks that would fix a gender.
- **يمكنك + verbal noun** or **يُرجى + verbal noun** for instructions: يمكنك النقر في أي مكان للمتابعة، يُرجى التحقق من الاتصال.
- **Inclusive "let's"** (يلا + we-form) works well in overlays: يلا نكمّل اللعب.
- **Avoid** imperatives (اضغط، العب) and second-person present verbs (تريد، تحصل), because they fix a gender.

When `addressee` is `male` or `female`, use that gender. When it is `group`, use the plural (أنتم، ـكم); use the feminine plural only if the context says everyone addressed is a woman. When it is `none`, do not address anyone.

### Dialogue between characters

Gender-neutral wording is only for addressing the player. When one character talks to another, Arabic must commit to genders, so commit to the right ones:

- The **speaker** is the person saying "I". Adjectives and participles about themselves follow the speaker's gender: a man says أنا متأكد, a woman says أنا متأكدة.
- The **listener** is "you". Imperatives, verbs and adjectives addressed to them follow the listener's gender: لا تقلق to a man, لا تقلقي to a woman.
- Write a **character's name** exactly as their `ar` name in every line. Role nouns also take the character's gender: المحامي for a male lawyer, المحامية for a female lawyer.
- Lines of one **scene** form one conversation. Keep forms of address, tone, register and terms consistent from line to line. For example, a lawyer who calls Olive سيدة أوليف keeps doing so.
- Match each character's voice notes: a calm lawyer, a frightened mother, a child.

Never add a placeholder that the source does not have, such as a gender variable. If neutral wording is truly impossible, write the most neutral version you can and flag it with `GENDER:`. If the source already contains an ICU `select` on gender, fill every branch.

## 4. Numbers, counts and plurals

- **Digits.** Keep Western digits 0–9 exactly as in the source, in every market; runtime formatting handles locale numbers. Never write ٠–٩ or Persian ۰–۹, and never change a value.
- **Fixed numbers in text** follow Arabic number grammar:
  - 1 becomes the singular noun, optionally with واحد/واحدة (عملة واحدة).
  - 2 becomes the dual, with no digit (حياتان إضافيتان).
  - 3–10 take the digit and a plural noun.
  - 11 and above take the digit and a singular noun.
- **ICU plurals.** Arabic needs all six CLDR categories, even when the English has only `one` and `other`. Keep `#` and the variable name. The forms are:
  - `zero`: a negation phrase, without the number.
  - `one`: the singular noun with واحد/واحدة, without `#`.
  - `two`: the dual, without `#`.
  - `few` (3–10): `#` and the plural noun.
  - `many` (11–99): `#` and the singular noun (accusative).
  - `other` (100 and up, and decimals): `#` and the singular noun.

  ```
  {count, plural, zero {لا توجد لديك عملات} one {لديك عملة واحدة} two {لديك عملتان} few {لديك # عملات} many {لديك # عملةً} other {لديك # عملة}}
  ```
- **Unity Smart Strings plurals.** A game may use this syntax instead of ICU; the tool detects which one. The same six forms go in the same order, separated by `|`, with `{}` for the number:

  ```
  {count:plural:لا توجد لديك عملات|لديك عملة واحدة|لديك عملتان|لديك {} عملات|لديك {} عملةً|لديك {} عملة}
  ```

  Fewer than six forms is a critical error, because the game can fail at runtime on Arabic counts.
- **A count placeholder without ICU** (for example "{amount} coins") can hold any number, so use a construction that is grammatical for every number, such as "{amount} من العملات" or a label like "العملات: {amount}". Then add the note `PLURAL: needs ICU plural`.
- **Prices** come from the store as the `{price}` placeholder. Never write a currency symbol or code yourself.

## 5. Placeholders, tags and ICU syntax

- Keep every placeholder (`{name}`, `{0}`, `%s`, `%1$s`), rich-text tag (`<color=…>`, `</color>`, `<b>`, `<size=…>`, `<sprite …>`) and `\n` with the same spelling and the same count. Move them to wherever Arabic grammar needs them. Never translate, transliterate, respace, add or drop one.
- Tags wrap the Arabic words that correspond to the wrapped English words.
- ICU keywords (`plural`, `select`, `zero` … `other`, `#`) stay in Latin. So do the Smart Strings syntax pieces (`plural`/`p`, `choose`, `{}`, `|`). Never mix the two syntaxes in one string.
- Never glue an Arabic letter to a placeholder: not `ال{item}`, `ب{name}` or `{count}عملة`. A placeholder value may be a name, a number or a word that already has its article. Rephrase instead: "العنصر {item}", "بواسطة {name}", or put a space in between.
- Player names and other runtime text are isolated by the engine. Never insert bidi control characters (LRM, RLM, LRI, FSI, PDI) or tatweel (ـ).

## 6. Punctuation, spelling and typography

- After Arabic text, use ، ؛ ؟ instead of , ; ?. Full stops, ! and … stay as they are.
- Use Arabic ي and ك, never Persian ی and ک. Write hamza seats (أ إ ؤ ئ), ta marbuta (ة vs ه) and final ي vs ى correctly.
- Use no diacritics, except a shadda or tanween where a word would otherwise be misread.
- Arabic has no capital letters. Show English ALL CAPS emphasis through wording or the source's own tags.
- Keep quotation marks in the same style as the source.

## 7. Terminology

- Glossary terms are locked. Inflect them as the grammar requires (ال، بـ، لـ, dual, plural, attached pronouns), but do not swap in synonyms.
- Do-not-translate (DNT) terms, such as brand names, the game title and "VIP", stay in Latin script.
- The same English UI term must get the same Arabic term everywhere. Follow the approved translation-memory examples when the meaning matches.
- The master uses established Arabic terms (مستوى, not ليفل). Loanwords that players actually use are allowed only in the dialect overlays.

## 8. Length

When `max_len` is set, the string must fit within that many characters. Use shorter synonyms and drop filler words; never shorten a word with a dot. If it cannot fit, write the best version you can and flag it with `LENGTH:`.

## 9. Culture and compliance (all 13 markets)

Translate faithfully, but render sensitive content in the most neutral acceptable Arabic and flag it with `CULTURE:` so the team decides on the content itself. Sensitive content includes:

- alcohol and pork or pigs
- gambling wording (casino, bet, lottery, jackpot)
- the holidays, symbols or deities of any religion (Christmas, Halloween, Easter, temples, gods)
- magic presented as worship
- romance, dating and revealing clothing
- LGBTQ+ references
- politics, maps, borders and country names

Some wording is fixed:

- **Gambling words.** Never use قمار، رهان، مراهنة، يانصيب or كازينو. Prefer neutral game wording, for example "jackpot" becomes المكافأة الكبرى. Flag `CULTURE:` on any prize draw that involves a purchase, because Saudi law bans paid prize draws.
- **The Gulf.** Write الخليج العربي or just الخليج, never الخليج الفارسي.
- **Israel.** Never write إسرائيل. If the source names it, flag `CULTURE:`.
- **Religious phrasing.** Never use the name of God in jokes, casual exclamations or UI; use يا للروعة! or يا للهول! instead. Never quote or paraphrase Quranic text.
- **Seasonal greetings.** رمضان كريم, عيد مبارك and عيد سعيد are welcome in live-ops text.

## 10. Notes to reviewers

`note` stays empty unless a reviewer must check something. When it is used, it starts with a tag:

- `GENDER:` the wording could not be made neutral.
- `PLURAL:` the string needs an ICU plural.
- `CULTURE:` the source content may not suit these markets.
- `LENGTH:` the string does not fit `max_len`.
- `CONTEXT:` the meaning is ambiguous, and the note states the assumption made.

## 11. Examples

| en (type, context) | ar |
|---|---|
| Buy (ui, shop button) | شراء |
| Retry? (ui, after losing a level) | إعادة المحاولة؟ |
| Tap anywhere to continue (tutorial) | يمكنك النقر في أي مكان للمتابعة |
| Welcome back, {player_name}! (ui) | مرحبًا بعودتك يا {player_name}! |
| You earned {amount} coins! (ui) | حصلت على {amount} من العملات! (note: `PLURAL: needs ICU plural`) |
| They took my child from me. (dialogue; speaker Olive, a woman; listener her lawyer, a man; her son) | لقد أخذوا طفلي مني. |
| Don't worry, I'm sure we'll find your child. (dialogue; speaker the lawyer, a man; listener Olive, a woman) | لا تقلقي، أنا متأكد أننا سنجد طفلك. |
| Your lives are full! Come back and play. (push) | ar: أرواحك ممتلئة! حان وقت العودة إلى اللعب. · gulf: أرواحك كاملة! يلا نكمّل اللعب الحين · levant: أرواحك كاملة! يلا نكمّل اللعب هلّق · egypt: أرواحك كاملة! يلا نكمّل اللعب دلوقتي |

## 12. How quality is scored (MQM)

Every error gets a severity weight: minor 1, major 5, critical 25. The score is 100 × (1 − penalty ÷ source words). The pass mark is at least 99 with zero critical errors. It is measured by an independent native linguist on a random sample of at least 1,000 source words for each variant (master, gulf, levant, egypt).

- **critical:** the string breaks or goes blank (a placeholder, tag or ICU form is broken), shows a wrong number or price, inverts an instruction or a purchase action, or is religiously, politically or sexually offensive in these markets.
- **major:** the meaning is changed or unclear, a game mechanic gets the wrong term, the player is addressed in the wrong gender, the variety is wrong, or there is a grammar error any native reader would notice.
- **minor:** a small fluency, style or punctuation issue that does not hinder understanding.
