#!/usr/bin/env python3
"""Compile tools/content/*.py into content/*.json and VERIFY every exercise.

 * code      : reference solution passes all tests, starter does not.
 * predict   : python answers are produced by really running the code (or a bash script).
 * sql       : reference query runs on sqlite and returns rows, starter does not match.
 * others    : structural checks (indexes, blanks, ordering).
Exit status is non-zero if anything fails, so a broken exercise never ships.
"""
import contextlib
import importlib
import io
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import curriculum  # noqa: E402
import dsl  # noqa: E402
import harness  # noqa: E402
import tracegen as tracelib  # noqa: E402

MODULES = [
    "py_l1", "py_l2", "py_l3", "py_l4", "py_l4b", "py_l5", "py_l5b",
    "sql_l1", "sql_l2", "sql_l3", "sql_l4", "sql_l4b", "sql_l5", "sql_l5b",
    "bash_a", "bash_b", "bash_c", "devops_a", "devops_b", "devops_c", "light_a",
]
errors = []


def err(ex_id, msg):
    errors.append("%s: %s" % (ex_id, msg))


def norm(s):
    return "\n".join(l.rstrip() for l in str(s).replace("\r", "").split("\n")).strip("\n")


def run_py(code_):
    buf = io.StringIO()
    ns = {"__name__": "__main__"}
    with contextlib.redirect_stdout(buf):
        exec(compile(code_, "<predict>", "exec"), ns)
    return buf.getvalue()


def sqlite_rows(dataset, sql_text, after=None):
    con = sqlite3.connect(":memory:")
    con.executescript(curriculum.DATASETS[dataset]["setup"])
    parts = [p.strip() for p in sql_text.strip().split(";") if p.strip()]
    rows = None
    for p in parts:
        cur = con.execute(p)
        if cur.description:
            rows = cur.fetchall()
    if after:
        rows = con.execute(after).fetchall()
    con.close()
    return rows


def nrows(rows):
    if rows is None:
        return None
    out = []
    for r in rows:
        out.append(tuple(round(x, 6) if isinstance(x, float) else x for x in r))
    return out


def verify(ex):
    i = ex["id"]
    t = ex["type"]
    n = len(ex.get("hints", []))
    if not 2 <= n <= 3:
        err(i, "needs 2-3 hints, has %d" % n)
    if len(ex["prompt"]) < 8:
        err(i, "prompt too short")
    if t == "code":
        r = json.loads(harness.run(ex["solution"], ex["tests"]))
        if r["error"]:
            err(i, "solution error: " + r["error"])
        elif not r["cases"]:
            err(i, "no test cases ran")
        else:
            bad = [c for c in r["cases"] if not c["ok"]]
            if bad:
                err(i, "solution fails: %s" % bad[:2])
            if len(r["cases"]) < 2:
                err(i, "only %d test case" % len(r["cases"]))
        s = json.loads(harness.run(ex["starter"], ex["tests"]))
        if not s["error"] and s["cases"] and all(c["ok"] for c in s["cases"]):
            err(i, "starter already passes the tests")
    elif t == "predict":
        v = ex.get("verify")
        if v is False:
            pass  # cannot be executed here (e.g. PyTorch); answer was checked by hand
        elif v is None and ex.get("lang") == "python":
            try:
                out = run_py(ex["code"])
            except Exception as e:  # noqa: BLE001
                err(i, "predict code raised %r" % e)
                return
            if norm(out) != norm(ex["answer"]):
                err(i, "predict answer %r != real output %r" % (ex["answer"], out))
        elif isinstance(v, dict) and "toml" in v:
            import tomllib
            cfg = tomllib.loads(ex["code"])
            got = eval(v["toml"], {"cfg": cfg})
            if str(got) != ex["answer"].strip():
                err(i, "toml answer %r != real value %r" % (ex["answer"], got))
        elif isinstance(v, dict) and "yaml" in v:
            import yaml
            cfg = yaml.safe_load(ex["code"])
            got = eval(v["yaml"], {"cfg": cfg})
            if str(got) != ex["answer"].strip():
                err(i, "yaml answer %r != real value %r" % (ex["answer"], got))
        elif isinstance(v, dict) and "bash" in v:
            out = tracelib.run_bash(v["bash"], v.get("files"))

            def loose(x):
                return "\n".join(" ".join(l.split()) for l in str(x).strip("\n").split("\n"))
            if loose(out) != loose(ex["answer"]):
                err(i, "bash answer %r != real output %r" % (ex["answer"], out))
        elif v is None and ex.get("lang") not in ("python", None):
            err(i, "non-python predict needs verify=... or verify=False")
        if ex.get("trace") is not None:
            ex["trace"] = ex["trace"]
    elif t == "sql":
        try:
            exp = nrows(sqlite_rows(ex["dataset"], ex["solution"], ex.get("after")))
        except Exception as e:  # noqa: BLE001
            err(i, "solution SQL error: %s" % e)
            return
        if exp is None or (not exp and not ex.get("allow_empty")):
            err(i, "solution returns no rows")
        try:
            got = nrows(sqlite_rows(ex["dataset"], ex["starter"], ex.get("after")))
        except Exception:  # noqa: BLE001
            got = "error"
        if got == exp:
            err(i, "starter already returns the expected result")
        if ex.get("ordered") and "order by" not in ex["solution"].lower() and "over" not in ex["solution"].lower():
            err(i, "ordered=True but solution has no ORDER BY")
    elif t == "mcq":
        a = ex["answer"]
        k = len(ex["choices"])
        if not 3 <= k <= 5:
            err(i, "mcq needs 3-5 choices")
        for x in (a if isinstance(a, list) else [a]):
            if not 0 <= x < k:
                err(i, "answer index out of range")
        if len(set(ex["choices"])) != k:
            err(i, "duplicate choices")
        if ex.get("whys") and len(ex["whys"]) != k:
            err(i, "whys length mismatch")
    elif t == "fill":
        nb = ex["template"].count("____")
        if nb != len(ex["blanks"]):
            err(i, "template has %d blanks, %d answers" % (nb, len(ex["blanks"])))
    elif t == "spot":
        for b in ex["bad"]:
            if not 1 <= b <= len(ex["lines"]):
                err(i, "bad line out of range")
        f = ex.get("fix")
        if f and not 0 <= f["answer"] < len(f["choices"]):
            err(i, "fix answer out of range")
        if ex.get("invalid") in ("json", "toml"):
            text = "\n".join(ex["lines"])
            try:
                if ex["invalid"] == "json":
                    json.loads(text)
                else:
                    import tomllib
                    tomllib.loads(text)
                err(i, "expected invalid %s but it parsed" % ex["invalid"])
            except Exception:  # noqa: BLE001
                pass
        if ex.get("lang") == "yaml" and ex.get("yaml_invalid"):
            import yaml
            try:
                yaml.safe_load("\n".join(ex["lines"]))
                err(i, "expected invalid YAML but it parsed")
            except Exception:  # noqa: BLE001
                pass
    elif t == "order":
        if len(set(ex["lines"])) != len(ex["lines"]):
            err(i, "order lines must be unique")
        if len(ex["lines"]) < 3:
            err(i, "order needs >=3 lines")
    else:
        err(i, "unknown type " + t)


def main():
    by_track = {}
    for m in MODULES:
        if not os.path.exists(os.path.join(HERE, "content", m + ".py")):
            continue
        mod = importlib.import_module("content." + m)
        by_track.setdefault(mod.TRACK, []).extend(mod.CONCEPTS)
    seen = set()
    tracks_meta = {t["id"]: t for t in curriculum.TRACKS}
    for tid, cs in by_track.items():
        levels = len(tracks_meta[tid]["levels"])
        cs.sort(key=lambda c: c["level"])  # stable: keeps declared order within a level
        for c in cs:
            if c["id"] in seen:
                err(c["id"], "duplicate concept id")
            seen.add(c["id"])
            if not 1 <= c["level"] <= levels:
                err(c["id"], "bad level")
            if len(c["exercises"]) < 2:
                err(c["id"], "needs >= 2 exercises")
            if not any(b["t"] == "quick" for b in c["lesson"]["blocks"]):
                err(c["id"], "lesson needs a quick check")
            for p in c["phases"]:
                if p not in dsl.PHASES:
                    err(c["id"], "bad phase " + p)
            for e in c["exercises"]:
                if e["id"] in seen:
                    err(e["id"], "duplicate id")
                seen.add(e["id"])
                verify(e)
    os.makedirs(os.path.join(ROOT, "content"), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "content")):
        os.remove(os.path.join(ROOT, "content", f))
    # strip build-only keys
    for cs in by_track.values():
        for c in cs:
            for e in c["exercises"]:
                e.pop("verify", None)
                e.pop("allow_empty", None)
                e.pop("yaml_invalid", None)
    cur = {"tracks": [t for t in curriculum.TRACKS if t["id"] in by_track or True], "phases": curriculum.PHASES, "rotation": curriculum.ROTATION, "datasets": curriculum.DATASETS}
    dsl.dump(cur, os.path.join(ROOT, "content", "curriculum.json"))
    for t in curriculum.TRACKS:
        dsl.dump({"concepts": by_track.get(t["id"], [])}, os.path.join(ROOT, "content", t["id"] + ".json"))
    # summary
    print("%-8s %s" % ("track", "concepts / exercises per level"))
    total_c = total_e = 0
    for t in curriculum.TRACKS:
        cs = by_track.get(t["id"], [])
        row = []
        for L in range(1, len(t["levels"]) + 1):
            lc = [c for c in cs if c["level"] == L]
            row.append("L%d:%d/%d" % (L, len(lc), sum(len(c["exercises"]) for c in lc)))
        total_c += len(cs)
        total_e += sum(len(c["exercises"]) for c in cs)
        print("%-8s %s" % (t["id"], "  ".join(row)))
    print("TOTAL: %d concepts, %d exercises" % (total_c, total_e))
    if errors:
        print("\n%d PROBLEM(S):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("all exercises verified")


if __name__ == "__main__":
    main()
