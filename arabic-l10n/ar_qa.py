"""Rule QA for English -> Arabic game strings. `python ar_qa.py` runs the self-test.

check(src, tgt, max_len=None, terms=(), allow=(), syntax=None)  -> [(rule_id, severity, message)]
lint_source(src)                                                -> [(rule_id, severity, message)]
severity "error" blocks export; "warn" routes the string to a human.
Plurals/selects in both syntaxes: ICU {n, plural, one {...} other {...}} and Unity Smart Strings {n:plural:a|b}.
"""
import re
import unicodedata
from collections import Counter

AR = "ء-ي"            # Arabic letters
MARKS = "ً-ٰٟ"   # harakat, tanween, shadda, sukun, dagger alef

# ICU branch openers (`one {`, `=0 {`, `female {`) are not placeholders.
# ponytail: only CLDR plural keywords + male/female; custom select keys (`ios {`) would read as args.
BRANCH = re.compile(r"(?:\b(?:zero|one|two|few|many|other|male|female)|=\d+)\s*\{")
ARG = re.compile(r"\{\s*([A-Za-z_][\w.]*|\d+)\s*(?:,\s*(\w+)|:(\w+))?")  # ICU `{n, plural` or Smart `{n:plural`
SMART_TYPES = {"p": "plural", "choose": "select", "c": "select"}       # so ICU and Smart args compare alike
ICU_SYNTAX = re.compile(r"\{\s*[\w.]+\s*,\s*(?:plural|select|selectordinal)\s*,")
SMART_SYNTAX = re.compile(r"\{\s*[\w.]+\s*:(?:plural|p|choose|c)\b")
SMART_PLURAL = re.compile(r"\{\s*[\w.]+\s*:(?:plural|p)(?:\([^)]*\))?:")
PRINTF = re.compile(r"%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXoc@]")
TAG = re.compile(r"</?[A-Za-z][\w-]*(?:[= ][^<>]*)?/?>")
CATS = {"zero", "one", "two", "few", "many", "other"}
ICU_WORDS = CATS | {"plural", "select", "selectordinal", "number", "date", "time", "male", "female", "choose"}

RULES = [(i, s, re.compile(r), m) for i, s, r, m in [
    ("PERSIAN_YEH_KAF", "error", "[یک]", "Persian yeh/keheh: use Arabic ي ك"),
    ("PERSIAN_DIGITS", "error", "[۰-۹]", "Persian digits: keep Western 0-9"),
    ("ARABIC_INDIC_DIGITS", "error", "[٠-٩]", "Arabic-Indic digits: policy is Western 0-9 in strings"),
    ("PERSIAN_LETTERS", "warn", "[پچژگ]", "پ چ ژ گ are not Arabic letters"),
    ("PRESHAPED", "error", "[ﭐ-﷿ﹰ-ﻼ]", "Presentation forms (pre-shaped text): store logical, unshaped Arabic"),
    ("BIDI_CONTROL", "error", "[\u200E\u200F\u061C\u202A-\u202E\u2066-\u2069]", "Bidi control char: insert isolates in code at format time"),
    ("INVISIBLE", "warn", "[\u200B\u200C\u200D\u2060\uFEFF\u00AD\u180E]", "Invisible char (ZWSP/ZWNJ/ZWJ/WJ/BOM/SHY)"),
    ("TATWEEL", "warn", "ـ", "Tatweel in UI string"),
    ("LATIN_PUNCT", "warn", f"[{AR}][{MARKS}]*\\s?[?;,](?!\\d)", "Use ؟ ؛ ، after Arabic text"),
    ("MARK_STACK", "warn", f"[{MARKS}]{{3,}}", "3+ stacked diacritics"),
    ("ORPHAN_MARK", "error", f"(?:^|[^ؠ-يٮ-ۓ{MARKS}])[{MARKS}]", "Diacritic with no Arabic base letter"),
    ("REVERSED_START", "error", f"^[؟،.!:]\\s*[{AR}]", "Starts with terminal punctuation: stored in visual (reversed) order?"),
    ("REVERSED_BRACKETS", "warn", r"^[^()]*\)[^()]*\(", "')' before '(': brackets mirrored by hand?"),
    ("ATTACHED_PLACEHOLDER", "warn", f"[{AR}]\\{{|\\}}[{AR}]", "Arabic letter glued to a placeholder (e.g. ال{item}): rephrase"),
]]


def args(s):
    """Argument set, e.g. {('count', 'plural'), ('name', '')}. Sets, because Arabic has 6 branches."""
    return {(n, icu or SMART_TYPES.get(smart, smart)) for n, icu, smart in ARG.findall(BRANCH.sub(" ", s))}


def syntax(s):
    """Which plural/select syntax a string uses: subset of {'icu', 'smart'}."""
    return {name for name, rx in (("icu", ICU_SYNTAX), ("smart", SMART_SYNTAX)) if rx.search(s)}


def smart_plurals(s):
    """The |-separated forms of each Smart Strings plural, e.g. '{n:plural:{} coin|{} coins}' -> [['{} coin', '{} coins']]."""
    out = []
    for m in SMART_PLURAL.finditer(s):
        depth, start, forms, i = 1, m.end(), [], m.end()
        while i < len(s) and depth:
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
            elif s[i] == "|" and depth == 1:
                forms.append(s[start:i])
                start = i + 1
            i += 1
        out.append(forms + [s[start:i - 1]])
    return out


def plain(s):
    """Text with tags, printf, ICU/Smart args and branch openers removed (for word/number/Latin checks)."""
    s = TAG.sub(" ", PRINTF.sub(" ", BRANCH.sub(" ", s)))
    return re.sub(r"\{\s*(?:[A-Za-z_][\w.]*|\d+)\s*(?:,\s*\w+\s*,?|:\w+(?:\([^)]*\))?:?)?\}?|[{}#|]", " ", s)


def _nums(s):
    return Counter(n for n in re.findall(r"\d+(?:[.,]\d+)?", plain(s)) if n not in ("0", "1", "2"))  # 0/1/2 may be spelled out / dual


def check(src, tgt, max_len=None, terms=(), allow=(), syntax_=None):
    """terms: glossary hits for src, dicts with en, ar (list of accepted forms), dnt (bool).
    allow: args the target may add, e.g. {("player_gender", "select")} when the game passes a gender variable.
    syntax_: the game's plural/select syntax ('icu' or 'smart') for strings whose source has none."""
    if not tgt.strip():
        return [("EMPTY", "error", "No translation")]
    out = [(i, s, m) for i, s, r, m in RULES if r.search(tgt)]
    if args(src) - set(allow) != args(tgt) - set(allow):
        show = lambda s: " ".join(sorted("{" + ", ".join(filter(None, a)) + "}" for a in args(s))) or "none"
        out.append(("PLACEHOLDER_MISMATCH", "error", f"source has {show(src)}, target has {show(tgt)}"))
    if Counter(PRINTF.findall(src)) != Counter(PRINTF.findall(tgt)):
        out.append(("PRINTF_MISMATCH", "error", f"{PRINTF.findall(src)} vs {PRINTF.findall(tgt)}"))
    if Counter(TAG.findall(src)) != Counter(TAG.findall(tgt)):
        out.append(("TAG_MISMATCH", "error", f"{TAG.findall(src)} vs {TAG.findall(tgt)}"))
    expected = syntax(src) or ({syntax_} if syntax_ else syntax(tgt))  # unknown game syntax: nothing to compare
    if syntax(tgt) - expected:
        out.append(("SYNTAX_MISMATCH", "error", f"Target uses {sorted(syntax(tgt))} plural/select syntax, game uses {sorted(expected) or 'none here'}"))
    if re.search(r"\{\s*[\w.]+\s*,\s*plural\s*,", tgt):
        missing = CATS - set(re.findall(r"\b(zero|one|two|few|many|other)\s*\{", tgt))
        if missing:
            out.append(("ICU_PLURAL_INCOMPLETE", "error", f"Arabic needs all 6 plural forms; missing {sorted(missing)}"))
    for forms in smart_plurals(tgt):
        if len(forms) != 6:  # Unity/SmartFormat Arabic rule indexes 6 forms; fewer throws at runtime
            out.append(("SMART_PLURAL_INCOMPLETE", "error",
                        f"Arabic needs 6 forms zero|one|two|few|many|other, found {len(forms)}"))
    if src.count("\\n") + src.count("\n") != tgt.count("\\n") + tgt.count("\n"):
        out.append(("NEWLINES", "warn", "Line-break count differs from source"))
    if (src[:1].isspace(), src[-1:].isspace()) != (tgt[:1].isspace(), tgt[-1:].isspace()):
        out.append(("WHITESPACE", "warn", "Leading/trailing space differs from source"))
    if not unicodedata.is_normalized("NFC", tgt):
        out.append(("NOT_NFC", "error", "Not NFC-normalized"))
    if _nums(src) != _nums(tgt):
        out.append(("NUMBER_MISMATCH", "warn", f"{sorted(_nums(src).elements())} vs {sorted(_nums(tgt).elements())}"))

    dnt = {t["en"].lower() for t in terms if t.get("dnt")}
    src_words = set(re.findall(r"[A-Za-z]{2,}", plain(src).lower()))
    if src_words and not src_words <= dnt and not re.search(f"[{AR}]", tgt):
        out.append(("UNTRANSLATED", "error", "No Arabic letters in target"))
    latin = {w for w in re.findall(r"[A-Za-z]{2,}", plain(tgt)) if w.lower() not in ICU_WORDS}
    latin -= {w for w in latin if any(w.lower() in d.split() for d in dnt)}
    if latin and re.search(f"[{AR}]", tgt):
        out.append(("LATIN_WORD", "warn", f"Latin words left in Arabic: {sorted(latin)}"))
    for t in terms:
        if t.get("dnt"):
            if t["en"].lower() not in tgt.lower():
                out.append(("DNT_MISSING", "error", f"Keep '{t['en']}' untranslated"))
        elif t.get("ar") and not any((a[2:] if a.startswith("ال") and len(a) > 3 else a) in tgt for a in t["ar"]):
            out.append(("GLOSSARY_MISS", "warn", f"'{t['en']}' should be {' / '.join(t['ar'])}"))
    if max_len and not syntax(tgt) and len(tgt) > max_len:
        out.append(("TOO_LONG", "warn", f"{len(tgt)} chars > max {max_len}"))
    return out


def lint_source(src):
    """English-side problems that make correct Arabic impossible."""
    out = []
    if src != src.strip():
        out.append(("SRC_FRAGMENT", "warn", "Leading/trailing space: concatenated fragment? Arabic needs full sentences"))
    if len(re.findall(r"%[sd@]", src)) >= 2:
        out.append(("SRC_BARE_PRINTF", "warn", "2+ bare %s/%d: use positional %1$s so Arabic can reorder"))
    if not syntax(src) and (re.search(r"\{\s*(?:count|num|number|amount|qty|quantity|n)\s*\}", src, re.I)
                            or re.search(r"(?:\{\s*\w+\s*\}|%\d*\$?d)\s+[A-Za-z]+s\b", src)):
        out.append(("SRC_COUNT_NO_PLURAL", "warn", "Count without plural support: Arabic needs 6 forms (ICU or Smart Strings plural)"))
    return out


def ids(src, tgt, **kw):
    return {i for i, _, _ in check(src, tgt, **kw)}


if __name__ == "__main__":
    coins_en = "{count, plural, one {You have # coin} other {You have # coins}}"
    coins_ar = ("{count, plural, zero {لا توجد لديك عملات} "
                "one {لديك عملة واحدة} "
                "two {لديك عملتان} "
                "few {لديك # عملات} "
                "many {لديك # عملةً} "
                "other {لديك # عملة}}")
    ar = "لديك"  # "you have"
    assert ids("You have {0} coins", f"{ar} {{0}} عملة") == set()
    assert ids(coins_en, coins_ar) == set(), ids(coins_en, coins_ar)
    assert "ICU_PLURAL_INCOMPLETE" in ids(coins_en, coins_ar.replace("two {لديك عملتان} ", ""))
    assert "PLACEHOLDER_MISMATCH" in ids("You have {0} coins", f"{ar} عملات")
    sel = "{player_gender, select, female {هل تساعدينني؟} other {هل تساعدني؟}}"
    assert "PLACEHOLDER_MISMATCH" in ids("Can you help me?", sel)
    assert ids("Can you help me?", sel, allow={("player_gender", "select")}) == set()
    assert "PRINTF_MISMATCH" in ids("Ends in %1$s", "ينتهي")
    assert "TAG_MISMATCH" in ids("<b>Win</b>", "<b>فوز")
    assert ids("<color=#FFD700>Double</color>", "<color=#FFD700>مضاعف</color>") == set()
    assert "PERSIAN_YEH_KAF" in ids("x", "کتاب جدید")
    assert "ARABIC_INDIC_DIGITS" in ids("Level 5", "المستوى ٥")
    assert "PRESHAPED" in ids("x", "ﻟﻤﺴ")
    assert "BIDI_CONTROL" in ids("Hi {0}", "مرحبا \u2068{0}\u2069")
    assert "LATIN_PUNCT" in ids("Retry?", "إعادة المحاولة?")
    assert "REVERSED_START" in ids("Retry?", "؟ةلواحملا")
    assert "ORPHAN_MARK" in ids("x", "َabc م")
    assert "NOT_NFC" in ids("x", "أ")
    assert "ATTACHED_PLACEHOLDER" in ids("Get {item}", "ال{item}")
    assert "UNTRANSLATED" in ids("Play now", "Play now")
    assert "UNTRANSLATED" not in ids("VIP", "VIP", terms=[{"en": "VIP", "dnt": True}])
    assert "DNT_MISSING" in ids("Join VIP", "انضم", terms=[{"en": "VIP", "dnt": True}])
    assert "GLOSSARY_MISS" in ids("Shop", "السوق", terms=[{"en": "Shop", "ar": ["المتجر"]}])
    assert "GLOSSARY_MISS" not in ids("Open shop", "فتح متجر", terms=[{"en": "Shop", "ar": ["المتجر"]}])
    assert "NUMBER_MISMATCH" in ids("Win 50 coins", "اربح 500")
    assert "NUMBER_MISMATCH" not in ids("Get 2 lives", "حياتان")  # dual, no digit: fine
    assert "TOO_LONG" in ids("Play", "العب الآن معنا", max_len=5)
    assert "LATIN_WORD" in ids("Open the shop", "افتح shop")
    assert {i for i, _, _ in lint_source("You earned {amount} coins!")} == {"SRC_COUNT_NO_PLURAL"}
    assert {i for i, _, _ in lint_source("Score: ")} == {"SRC_FRAGMENT"}
    assert {i for i, _, _ in lint_source("%s gave %s")} == {"SRC_BARE_PRINTF"}
    assert lint_source(coins_en) == []

    # Unity Smart Strings: same 6 forms, |-separated, {} = the number
    smart_en = "{count:plural:You have {} coin|You have {} coins}"
    smart_ar = ("{count:plural:لا توجد لديك عملات|"
                "لديك عملة واحدة|لديك عملتان|"
                "لديك {} عملات|لديك {} عملةً|لديك {} عملة}")
    assert syntax(smart_en) == {"smart"} and syntax(coins_en) == {"icu"} and syntax("Level {0}") == set()
    assert [len(f) for f in smart_plurals(smart_ar)] == [6]
    assert ids(smart_en, smart_ar) == set(), ids(smart_en, smart_ar)
    assert "SMART_PLURAL_INCOMPLETE" in ids(smart_en, "{count:plural:عملة|{} عملات}")
    assert "SYNTAX_MISMATCH" in ids(smart_en, coins_ar) and "SYNTAX_MISMATCH" in ids(coins_en, smart_ar)
    assert [len(f) for f in smart_plurals("{n:p:{name} {}|b|c|d|e|f} x")] == [6]          # nested braces, short name
    choose = "{player_gender:choose(female):هل تساعدينني؟|هل تساعدني؟}"
    g = {("player_gender", "select")}
    assert ids("Can you help me?", choose, allow=g, syntax_="smart") == set()
    assert "SYNTAX_MISMATCH" in ids("Can you help me?", choose, allow=g, syntax_="icu")
    assert "SYNTAX_MISMATCH" in ids("Can you help me?", sel, allow=g, syntax_="smart")
    assert lint_source(smart_en) == [] and lint_source("You earned {amount:p:{} coin|{} coins}!") == []
    print("ar_qa self-test ok")
