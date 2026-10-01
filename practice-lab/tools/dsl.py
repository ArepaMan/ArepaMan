"""Tiny DSL for authoring Skill Radar content. Everything compiles to plain JSON.

Concepts:  C(id, level, title, lede, blocks, [exercises], phases=[...])
Blocks:    P, H, CODE, TIP, WARN, UL, TABLE, VIZ, QUICK
Exercises: code, sql, predict, mcq, fill, spot, order  (ids are assigned automatically)
"""
import json
import textwrap

PHASES = ["data", "deep", "serving", "cloud", "monitor"]


def dd(s):
    return textwrap.dedent(s).strip("\n")


def P(x):
    return {"t": "p", "x": dd(x)}


def H(x):
    return {"t": "h", "x": x}


def CODE(x, lang="python", label=None):
    b = {"t": "code", "lang": lang, "x": dd(x)}
    if label:
        b["label"] = label
    return b


def TIP(x):
    return {"t": "tip", "x": dd(x)}


def WARN(x):
    return {"t": "warn", "x": dd(x)}


def UL(*items):
    return {"t": "ul", "x": [dd(i) for i in items]}


def TABLE(cols, rows):
    return {"t": "table", "cols": cols, "rows": rows}


def VIZ(kind, **data):
    return {"t": "viz", "kind": kind, "data": data}


def QUICK(q, choices, a, why=""):
    return {"t": "quick", "q": q, "choices": choices, "a": a, "why": why}


def _ex(type_, prompt, hints, diff, tags, explain, why, extra):
    e = {"type": type_, "prompt": dd(prompt), "hints": [dd(h) for h in hints], "diff": diff}
    if tags:
        e["tags"] = list(tags)
    if explain:
        e["explain"] = explain
    if why:
        e["why"] = dd(why)
    e.update(extra)
    return e


def EXPLAIN(ask, points, model):
    return {"ask": ask, "points": points, "model": dd(model)}


def code(prompt, starter, solution, tests, hints, diff=1, tags=(), explain=None, why=None, lines=None):
    return _ex("code", prompt, hints, diff, tags, explain, why,
               {"starter": dd(starter) + "\n", "solution": dd(solution) + "\n", "tests": dd(tests), **({"lines": lines} if lines else {})})


def sql(dataset, prompt, starter, solution, hints, diff=1, tags=(), explain=None, why=None, ordered=False, names=False, after=None, lines=None):
    ex = {"dataset": dataset, "starter": dd(starter) + "\n", "solution": dd(solution), "ordered": ordered, "names": names}
    if after:
        ex["after"] = dd(after)
    if lines:
        ex["lines"] = lines
    return _ex("sql", prompt, hints, diff, tags, explain, why, ex)


def predict(prompt, code_, answer, hints, diff=1, tags=(), explain=None, why=None, lang="python", accept=(), trace=None, verify=None):
    ex = {"code": dd(code_), "answer": answer.strip("\n"), "lang": lang}
    if accept:
        ex["accept"] = list(accept)
    if trace is not None:
        ex["trace"] = trace
    if verify is not None:
        ex["verify"] = verify
    return _ex("predict", prompt, hints, diff, tags, explain, why, ex)


def mcq(prompt, choices, answer, hints, diff=1, tags=(), explain=None, why=None, whys=None, code_=None, lang="python"):
    ex = {"choices": choices, "answer": answer}
    if whys:
        ex["whys"] = whys  # optional per-choice feedback shown after a wrong pick
    if code_:
        ex["code"] = dd(code_)
        ex["lang"] = lang
    return _ex("mcq", prompt, hints, diff, tags, explain, why, ex)


def fill(prompt, template, blanks, hints, diff=1, tags=(), explain=None, why=None, lang="text", ci=False):
    return _ex("fill", prompt, hints, diff, tags, explain, why,
               {"template": dd(template), "blanks": [b if isinstance(b, list) else [b] for b in blanks], "lang": lang, "ci": ci})


def spot(prompt, lines, bad, hints, diff=1, tags=(), explain=None, why=None, lang="text", fix=None, yaml_invalid=False, invalid=None):
    lines = dd(lines).split("\n") if isinstance(lines, str) else lines
    ex = {"lines": lines, "bad": bad if isinstance(bad, list) else [bad], "lang": lang}
    if fix:
        ex["fix"] = fix
    if yaml_invalid:
        ex["yaml_invalid"] = True
    if invalid:
        ex["invalid"] = invalid
    return _ex("spot", prompt, hints, diff, tags, explain, why, ex)


def FIX(q, choices, answer, whys=None):
    f = {"q": q, "choices": choices, "answer": answer}
    if whys:
        f["why"] = whys
    return f


def order(prompt, lines, hints, diff=1, tags=(), explain=None, why=None, lang="text", extra=(), alts=()):
    lines = dd(lines).split("\n") if isinstance(lines, str) else lines
    ex = {"lines": lines, "lang": lang}
    if extra:
        ex["extra"] = list(extra)
    if alts:
        ex["alts"] = [list(a) for a in alts]
    return _ex("order", prompt, hints, diff, tags, explain, why, ex)


def C(id_, level, title, lede, blocks, exercises, phases=(), minutes=3):
    c = {"id": id_, "level": level, "title": title, "lede": dd(lede), "minutes": minutes,
         "phases": list(phases), "lesson": {"blocks": blocks}, "exercises": []}
    for i, e in enumerate(exercises):
        e = dict(e)
        e["id"] = "%s.%d" % (id_, i + 1)
        c["exercises"].append(e)
    return c


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
