"""Offline end-to-end check, model providers stubbed: `python test_localize.py`."""
import csv
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

import localize

LEVEL = "\u0627\u0644\u0645\u0633\u062A\u0648\u0649 {0}"
REWARD_OK = "\u062D\u0635\u0644\u062A \u0639\u0644\u0649 {amount} \u0645\u0646 \u0627\u0644\u0639\u0645\u0644\u0627\u062A!"
REWARD_BROKEN = "\u062D\u0635\u0644\u062A \u0639\u0644\u0649 \u0639\u0645\u0644\u0627\u062A!"  # placeholder dropped
RETRY = "\u0625\u0639\u0627\u062F\u0629 \u0627\u0644\u0645\u062D\u0627\u0648\u0644\u0629\u061F"
SELECT = ("{player_gender, select, female {\u0647\u0644 \u062A\u0633\u0627\u0639\u062F\u064A\u0646\u0646\u064A\u061F} "
          "other {\u0647\u0644 \u062A\u0633\u0627\u0639\u062F\u0646\u064A\u061F}}")
PUSH = {"ar": "\u0623\u0631\u0648\u0627\u062D\u0643 \u0645\u0645\u062A\u0644\u0626\u0629!",
        "gulf": "\u0623\u0631\u0648\u0627\u062D\u0643 \u0643\u0627\u0645\u0644\u0629! \u064A\u0644\u0627 \u0646\u0643\u0645\u0644 \u0627\u0644\u062D\u064A\u0646",
        "levant": "\u0623\u0631\u0648\u0627\u062D\u0643 \u0643\u0627\u0645\u0644\u0629! \u064A\u0644\u0627 \u0646\u0643\u0645\u0644 \u0647\u0644\u0642",
        "egypt": "\u0623\u0631\u0648\u0627\u062D\u0643 \u0643\u0627\u0645\u0644\u0629! \u064A\u0644\u0627 \u0646\u0643\u0645\u0644 \u062F\u0644\u0648\u0642\u062A\u064A"}
AR = {"hud_level": LEVEL, "reward": REWARD_BROKEN, "btn_retry": RETRY, "npc_help": SELECT,
      "olive_01": "لقد أخذوا طفلي مني.",
      "lawyer_01": "لا تقلقي يا أوليف، سنجد طفلك.",
      "stranger": "من أنت؟",
      "coins_smart": "{count:plural:لا توجد عملات|عملة واحدة|"
                     "عملتان|{} عملات|{} عملةً|{} عملة}"}
SOURCE = ("key,en,type,context,screenshot,speaker,listener,scene\n"
          "hud_level,Level {0},ui,HUD,hud.png,,,\nreward,You earned {amount} coins!,ui,Popup,,,,\n"
          "btn_retry,Retry?,ui,After losing,,,,\npush_lives,Your lives are full!,push,Push,,,,\n"
          "npc_help,Can you help me?,dialogue,Sami (male NPC) to the player,,,,\n"
          "olive_01,They took my child from me.,dialogue,Her son,,Olive,Lawyer,s2\n"
          "lawyer_01,\"Don't worry, Olive. We will find your child.\",dialogue,Reassuring,,Lawyer,Olive,s2\n"
          "stranger,Who are you?,dialogue,,,Olive,Ghost,s2\n")
CHARACTERS = "name,ar,gender,notes\nOlive,أوليف,female,frightened mother\nLawyer,المحامي,male,calm\n"
calls = []  # (provider, model, request)


def fake(provider):
    def answer(model, effort, req):
        system, content, schema = req
        calls.append((provider, model, req))
        assert "style guide" in system[0].lower() or schema is localize.LINT_SCHEMA
        items = json.loads(content[-1]["text"])
        if schema is localize.T_SCHEMA:
            return {"items": [{"key": i["key"], "note": "", "gulf": "", "levant": "", "egypt": "",
                               "terms": [{"en": "Star Pass", "ar": "\u062A\u0630\u0643\u0631\u0629 \u0627\u0644\u0646\u062C\u0648\u0645"}] if i["key"] == "hud_level" else [],
                               **(PUSH if i["overlays"] else {"ar": AR[i["key"]]})} for i in items]}
        if schema is localize.FIX_SCHEMA:
            assert [i["key"] for i in items] == ["reward"] and "PLACEHOLDER_MISMATCH" in items[0]["issues"][0]
            return {"items": [{"key": "reward", "variant": "ar", "fixed": REWARD_OK}]}
        if schema is localize.LINT_SCHEMA:
            return {"items": [{"key": i["key"], "suggested_en": "{amount, plural, one {You earned # coin!} other {You earned # coins!}}",
                               "why": "ICU plural"} for i in items]}
        return {"items": [{"key": i["key"], "variant": i["variant"], "suggestion": "",
                           "errors": [{"category": "style", "severity": "minor", "span": "", "why": "a major point, but minor"}]
                           if i["key"] == "btn_retry" else []} for i in items]}
    return answer


class FakeBatches:  # Message Batches stub: answers each request with the same fake model
    created = []

    def create(self, requests):
        self.created.append(requests)
        usage = NS(input_tokens=1000, output_tokens=500, cache_creation_input_tokens=0, cache_read_input_tokens=2000)
        self.out = [NS(custom_id=r["custom_id"], result=NS(type="succeeded", message=NS(stop_reason="end_turn", usage=usage, content=[
            NS(type="text", text=json.dumps(fake("batch")(r["params"]["model"], None, (
                [b["text"] for b in r["params"]["system"]], r["params"]["messages"][0]["content"],
                r["params"]["output_config"]["format"]["schema"]))))]))) for r in requests]
        return NS(id="msgbatch_test", processing_status="ended")

    def results(self, batch_id):
        return self.out


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    localize._call_anthropic, localize._call_openai = fake("anthropic"), fake("openai")
    localize.anthropic_client = lambda: NS(messages=NS(batches=FakeBatches()))
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "src.csv").write_text(SOURCE, encoding="utf-8")
        (d / "characters.csv").write_text(CHARACTERS, encoding="utf-8")
        (d / "hud.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        gl, tm, cal = d / "glossary.csv", d / "tm.csv", d / "calibration.csv"
        gl.write_text((localize.HERE / "glossary.csv").read_text(encoding="utf-8"), encoding="utf-8")
        common = ["--glossary", str(gl), "--tm", str(tm), "--calibration", str(cal), "--gender-var", "player_gender"]

        # 1. translate: screenshot, gender variable, judge from a different provider
        localize.main(["translate", str(d / "src.csv"), "--out", str(d / "out"), "--judge-model", "openai:judge-x"] + common)
        rv = {(r["key"], r["variant"]): r for r in rows(d / "out" / "review.csv")}
        assert len(rv) == 11, sorted(rv)                                    # 7 single-variant + push x 4
        t_items = {i["key"]: i for p, m, r in calls if r[2] is localize.T_SCHEMA for i in json.loads(r[1][-1]["text"])}
        assert t_items["olive_01"]["speaker"]["gender"] == "female" and t_items["olive_01"]["addressee"] == "male"
        assert t_items["lawyer_01"]["addressee"] == "female" and t_items["lawyer_01"]["scene"] == "s2"   # from listener Olive
        assert {"en": "Olive", "ar": ["أوليف"]}.items() <= next(
            g for g in t_items["lawyer_01"]["glossary"] if g["en"] == "Olive").items()                 # name locked
        assert t_items["stranger"]["addressee"] == "player" and "scene" not in t_items["hud_level"]    # unknown gender -> neutral
        assert (rv[("lawyer_01", "ar")]["speaker"], rv[("lawyer_01", "ar")]["listener"]) == ("Lawyer", "Olive")
        assert "error:" not in rv[("lawyer_01", "ar")]["qa"]
        assert [len(b) for b in localize.pack([{"scene": "s"}] * 3 + [{}, {}], 2)] == [3, 2]          # scene never split
        assert rv[("reward", "ar")]["final"] == REWARD_OK and rv[("reward", "ar")]["draft"] == REWARD_BROKEN
        assert "error:" not in rv[("reward", "ar")]["qa"] and "SRC_COUNT_NO_PLURAL" in rv[("reward", "ar")]["qa"]
        assert rv[("npc_help", "ar")]["final"] == SELECT and "error:" not in rv[("npc_help", "ar")]["qa"]
        assert rv[("hud_level", "ar")]["status"] == "auto_pass" and rv[("hud_level", "ar")]["screenshot"] == "hud.png"
        assert rv[("btn_retry", "ar")]["status"] == "needs_human"
        assert localize.mqm([rv[("btn_retry", "ar")]], "judge")["penalty"] == 1  # "major"/"minor" inside `why` not counted
        t_req = next(r for p, m, r in calls if r[2] is localize.T_SCHEMA)
        assert {"type": "text", "text": "Screenshot hud.png:"} in t_req[1] and any(b["type"] == "image" for b in t_req[1])
        assert "player_gender" in t_req[0][1]                                # gender instruction reached the translator
        assert {p for p, m, r in calls if r[2] is localize.J_SCHEMA} == {"openai"}
        assert {m for p, m, r in calls if r[2] is localize.J_SCHEMA} == {"judge-x"}
        cands = rows(d / "out" / "glossary_candidates.csv")
        assert [c["en"] for c in cands] == ["Star Pass"]

        # 2. human audit -> score (saves calibration) -> export (approved terms + TM)
        review = d / "out" / "review.csv"
        rs = rows(review)
        for r in rs:
            r["mqm"], r["approved"] = ("minor/fluency" if r["key"] == "btn_retry" else "none"), "y"
        localize.write_csv(review, rs, localize.REVIEW_FIELDS)
        localize.write_csv(d / "out" / "glossary_candidates.csv", [{**cands[0], "approved": "y"}], ["en", "ar", "count", "keys", "approved"])
        assert localize.main(["score", str(review), "--calibration", str(cal)]) == 1  # < 1000 words -> not a PASS
        assert len(rows(cal)) == 11
        exp = ["export", str(review), "--out", str(d / "out"), "--tm", str(tm), "--glossary", str(gl)]
        try:
            localize.main(exp)                                              # gender select without --gender-var
            raise AssertionError("export should block")
        except SystemExit as e:
            assert "blocking" in str(e)
        localize.main(exp + ["--gender-var", "player_gender"])
        st = {r["key"]: r for r in rows(d / "out" / "strings.csv")}
        assert len([c for c in st["push_lives"] if c.startswith("ar-")]) == 13
        assert st["push_lives"]["ar-SA"] == PUSH["gulf"] and st["push_lives"]["ar-EG"] == PUSH["egypt"]
        assert st["push_lives"]["ar-JO"] == PUSH["levant"] and st["push_lives"]["ar-IQ"] == PUSH["ar"]
        assert {r["en"] for r in rows(tm)} >= {"Level {0}", "Retry?"}
        assert ("push_lives", "gulf") in {(r["key"], r["variant"]) for r in rows(tm)}   # TM keeps key + variant
        assert "Star Pass" in {g["en"] for g in rows(gl)}

        # 2b. next release, nothing changed: every string reused, zero AI calls, still approved
        calls.clear()
        localize.main(["translate", str(d / "src.csv"), "--out", str(d / "out_reuse")] + common)
        assert calls == []
        re_rows = rows(d / "out_reuse" / "review.csv")
        assert {r["status"] for r in re_rows} == {"tm_reused"} and all(r["approved"] == "y" for r in re_rows)
        # ... and one changed English string is the only thing sent to the AI
        (d / "src2.csv").write_text(SOURCE.replace("Retry?,ui", "Try again?,ui"), encoding="utf-8")
        localize.main(["translate", str(d / "src2.csv"), "--out", str(d / "out_delta")] + common)
        sent = [i["key"] for p, m, r in calls if r[2] is localize.T_SCHEMA for i in json.loads(r[1][-1]["text"])]
        assert sent == ["btn_retry"], sent

        # 3. second run via the Batches API: judge now sees the linguists' calibration examples
        calls.clear()
        localize.main(["translate", str(d / "src.csv"), "--out", str(d / "out2"), "--batch-api", "--no-reuse"] + common)
        assert FakeBatches.created and {p for p, m, r in calls} == {"batch"}
        cost = rows(d / "out2" / "costs.csv")                                # per-run cost log, batch at 50%
        assert cost[0]["model"] == "claude-opus-5-5 (batch)" and float(cost[0]["usd"]) > 0
        assert abs(float(cost[0]["usd"]) - 0.0072 * int(cost[0]["calls"])) < 1e-6
        j_items = [i for p, m, r in calls if r[2] is localize.J_SCHEMA for i in json.loads(r[1][-1]["text"])]
        retry = next(i for i in j_items if i["key"] == "btn_retry")
        assert retry["calibration"][0]["human_annotation"] == "minor/fluency"

        # 4. bake-off: blind sheet, scored per system
        localize.main(["bakeoff", str(d / "src.csv"), "--out", str(d / "bake"), "--models", "claude-opus-5-5",
                       "openai:gpt-test"] + common)
        bk = rows(d / "bake" / "review.csv")
        assert {r["system"] for r in bk} == {"A", "B"} and all(r["audit"] == "Y" for r in bk)
        assert json.loads((d / "bake" / "systems.json").read_text()) == {"A": "claude-opus-5-5", "B": "openai:gpt-test"}
        for r in bk:
            r["mqm"] = "none"
        localize.write_csv(d / "bake" / "review.csv", bk, ["system"] + localize.REVIEW_FIELDS)
        assert localize.main(["score", str(d / "bake" / "review.csv"), "--calibration", str(d / "cal2.csv")]) == 1

        # Claude Code mode: no API key. Jobs are written, "Claude Code" answers them, the re-run continues.
        calls.clear()
        cc = ["translate", str(d / "src.csv"), "--out", str(d / "cc"), "--model", "claude-code",
              "--judge-model", "claude-code", "--no-reuse"] + common
        schemas = {"translate": localize.T_SCHEMA, "fix": localize.FIX_SCHEMA, "review": localize.J_SCHEMA}
        jobs, rounds, broke = d / "cc" / "jobs", [], False
        while localize.main(cc) == 3:
            pend = sorted((jobs / "pending").glob("*.json"))
            rounds.append(sorted(json.loads(p.read_text(encoding="utf-8"))["job"] for p in pend))
            for p in pend:
                job = json.loads(p.read_text(encoding="utf-8"))
                if job["job"] == "translate":
                    assert all((jobs / f).exists() for f in [*job["read_first"], *job["images"].values()])
                system = [(jobs / f).read_text(encoding="utf-8") for f in job["read_first"]]
                ans = fake("claude-code")("claude-code", None, (system, [{"type": "text", "text": json.dumps(job["items"])}],
                                                                schemas[job["job"]]))
                if not broke:  # the first answer is malformed: it must be rejected and re-asked, never cached
                    ans, broke = {"items": [{"key": "olive_01"}]}, True
                (jobs / job["answer_file"]).write_text(json.dumps(ans, ensure_ascii=False), encoding="utf-8")
            assert len(rounds) < 6, rounds
        assert rounds == [["translate"], ["translate"], ["fix"], ["review"]], rounds
        assert not list((jobs / "pending").glob("*.json")) and {p for p, m, r in calls} == {"claude-code"}  # no API
        cc_rows = {(r["key"], r["variant"]): r for r in rows(d / "cc" / "review.csv")}
        assert cc_rows[("reward", "ar")]["final"] == REWARD_OK and cc_rows[("btn_retry", "ar")]["judge"].startswith("minor/")
        assert localize.schema_errors({"items": [{"key": "a"}]}, localize.FIX_SCHEMA) == [
            "$.items[0]: missing 'variant'", "$.items[0]: missing 'fixed'"]

        # fake-Arabic test strings: same layout as strings.csv, placeholders intact, Arabic script, longer
        localize.main(["pseudo", str(d / "src.csv"), "--out", str(d / "pseudo")])
        ps = {r["key"]: r for r in rows(d / "pseudo" / "pseudo_strings.csv")}
        assert len([c for c in ps["lawyer_01"] if c.startswith("ar-")]) == 13 and ps["lawyer_01"]["ar-SA"] == ps["lawyer_01"]["ar"]
        for k, r in ps.items():
            errs = [i for i, s, _ in localize.ar_qa.check(r["en"], r["ar"]) if s == "error"]
            assert not errs and len(r["ar"]) > len(r["en"]), (k, errs, r["ar"])

        # 5. lint with AI rewrites
        assert localize.main(["lint", str(d / "src.csv"), "--out", str(d / "lint"), "--suggest"]) == 1
        lint = {r["key"]: r for r in rows(d / "lint" / "source_lint.csv")}
        assert "SRC_COUNT_NO_PLURAL" in lint["reward"]["issues"] and "plural" in lint["reward"]["suggested_en"]
        assert "SRC_GENDER" in lint["npc_help"]["issues"] and "SRC_NO_SPEAKER" in lint["npc_help"]["issues"]
        assert "SRC_UNKNOWN_CHARACTER" in lint["stranger"]["issues"] and "SRC_GENDER" not in lint["lawyer_01"]["issues"]
        assert lint["olive_01"]["issues"] == ""

        # Unity Smart Strings source: syntax detected, prompted, QA'd in that syntax
        assert localize.resolve_syntax("auto", ["Level {0}"]) == "icu"
        assert localize.resolve_syntax("auto", ["{n:p:{} a|{} b}", "x"]) == "smart" and localize.resolve_syntax("smart", []) == "smart"
        (d / "smart.csv").write_text("key,en,type,context\ncoins_smart,{count:plural:You have {} coin|You have {} coins},ui,Wallet\n",
                                     encoding="utf-8")
        calls.clear()
        localize.main(["translate", str(d / "smart.csv"), "--out", str(d / "smart_out")] + common)
        sm = rows(d / "smart_out" / "review.csv")[0]
        assert sm["final"] == AR["coins_smart"] and "error:" not in sm["qa"], sm["qa"]
        t_sys = next(r[0][1] for p, m, r in calls if r[2] is localize.T_SCHEMA)
        assert "Unity Smart Strings" in t_sys and "player_gender:choose(female)" in t_sys
        assert "Unity Smart Strings" in next(r[0][1] for p, m, r in calls if r[2] is localize.J_SCHEMA)

        # Unity Localization CSV export headers are accepted as-is
        (d / "unity_en.csv").write_text("Key,Id,English(en),Shared Comments\nbtn_buy,123,Buy,Shop button\n", encoding="utf-8")
        assert localize.read_csv(d / "unity_en.csv") == [{"key": "btn_buy", "id": "123", "en": "Buy", "context": "Shop button"}]
        localize._call_anthropic = lambda *x: (_ for _ in ()).throw(RuntimeError("no API key"))   # rewrites fail ...
        localize.main(["lint", str(d / "src.csv"), "--out", str(d / "lint2"), "--suggest"])
        assert rows(d / "lint2" / "source_lint.csv")                                             # ... report still written
        localize._call_anthropic = fake("anthropic")

        # 6. font coverage (Windows Arial has Arabic, not the 2025 Saudi riyal sign)
        assert localize.presentation_forms({"\u0628"}) == {chr(c) for c in range(0xFE8F, 0xFE93)}
        assert {"\uFEFB", "\uFEFC"} <= localize.presentation_forms({"\u0644", "\u0627"})   # lam-alef ligature
        font = Path("C:/Windows/Fonts/arial.ttf")
        if font.exists():
            localize.write_csv(d / "fs.csv", [{"key": "k", "ar": "\u0628\u0627\u0628", "ar-SA": "\u20C1 5"}], ["key", "ar", "ar-SA"])
            assert localize.main(["fontcheck", str(d / "fs.csv"), "--font", str(font), "--shaped"]) == 1

    # MQM math: 10 minor errors / 1000 words = 99.0; one critical fails even at 97.5
    m = localize.mqm([{"en": "word " * 1000, "mqm": "; ".join(["minor/fluency"] * 10)}], "mqm")
    assert m["words"] == 1000 and abs(m["score"] - 99.0) < 1e-9 and localize.verdict(m, 0) == "PASS"
    m = localize.mqm([{"en": "word " * 1000, "mqm": "critical/markup"}], "mqm")
    assert abs(m["score"] - 97.5) < 1e-9 and localize.verdict(m, 0) == "FAIL"
    assert localize.mqm([{"en": "a b", "mqm": "none"}], "mqm")["penalty"] == 0
    assert 0.012 < localize.wilson(0, 300)[1] < 0.013 and localize.wilson(300, 300)[0] > 0.987

    # consistency: same English two ways is flagged; same English to different listeners (gender) is not
    r = lambda k, en, ar, listener="": {"key": k, "variant": "ar", "en": en, "final": ar, "speaker": "", "listener": listener}
    inc = localize.consistency([r("a", "Shop", "المتجر"), r("b", "Shop", "السوق"),
                                r("c", "Go!", "اذهب!", "Sami"), r("d", "Go!", "اذهبي!", "Olive")])
    assert set(inc) == {("a", "ar"), ("b", "ar")} and "a, b" in inc[("a", "ar")][0][2]

    # cost: 1M uncached in + 1M cache reads + 0.1M out on Opus 5.5 = $4 + $0.20 + $2; batch halves it
    u = {"input": 1_000_000, "cache_write": 0, "cache_read": 1_000_000, "output": 100_000}
    assert abs(localize.usd("claude-opus-5-5", u) - 6.2) < 1e-9 and abs(localize.usd("claude-opus-5-5", u, batch=True) - 3.1) < 1e-9
    assert localize.usd("openai:some-model", u) is None

    # pseudo keeps Smart Strings plurals runnable: padded to Arabic's 6 forms
    assert [len(f) for f in localize.ar_qa.smart_plurals(localize.pseudo("{n:plural:{} coin|{} coins} left"))] == [6]
    print("localize end-to-end test ok")


if __name__ == "__main__":
    main()
