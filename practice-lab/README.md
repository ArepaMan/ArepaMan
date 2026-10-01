# Skill Radar

A daily-practice artifact for the ReviewRadar stack: Python, SQL, Bash, YAML/Docker/Kubernetes/Terraform and the small formats
(regex, JSON, TOML, Markdown). Python and SQL run in the browser; everything else is spot-the-error, fill-in, ordering and
predict-the-output with checked answers.

This folder holds the **sources**. The published artifact is built from them.

## Layout

```
src/            app (core, srs, engines, widgets, exercise, session, views, main) + style.css + harness.py
tools/
  content/      THE EXERCISES. One Python file per track/level, written with a tiny DSL (tools/dsl.py)
  curriculum.py tracks, levels, ReviewRadar phases, shared SQL datasets
  make_content.py   compiles content/*.py -> content/*.json AND verifies every exercise
  build.py          assembles dist/ (page + vendor engines + content)
  setup.sh          downloads Brython, sql.js and CodeMirror into vendor/ (npm, no accounts)
  *.js              Playwright checks (verify_browser, solve_all, flow2, srs_sim, qa, shots)
content/        generated JSON (what the page loads)
vendor/, dist/  generated, git-ignored
```

## Add or change an exercise

1. Edit the concept in `tools/content/<track>_<level>.py`. Example (Python code exercise):

   ```python
   code("Write `double(x)` that returns twice x.",
        "def double(x):\n    pass\n",                    # starter
        "def double(x):\n    return x * 2\n",            # reference solution
        't("double(2)", 4)\nt("double(-1)", -2)',   # tests: t(expr, expected)
        ["Hint 1", "Hint 2", "Hint 3"], diff=1)
   ```
   Other types: `sql`, `predict`, `mcq`, `fill`, `spot`, `order`. Add `explain=EXPLAIN(...)` to make an exercise ask
   "explain it in your own words", `tags=["interview"]` to include it in interview drills, and `phases=[...]` on the concept to
   tag it with a ReviewRadar phase (`data`, `deep`, `serving`, `cloud`, `monitor`).
2. `python3 tools/make_content.py` runs every solution against its tests (and SQL against sqlite, bash answers against real bash,
   YAML/TOML answers against real parsers). A broken exercise stops the build.
3. `python3 tools/build.py`, then publish `dist/` again (or ask Claude to republish).

Test helpers inside `tests`: `t(expr, want)`, `tx(setup, expr, want)`, `texc(expr, ExceptionType)`, `tprint(want)`,
`tvar({"x": 5}, "expr", want)` (re-runs the learner's script with new values), `tvout({...}, want)`, `check(label, got, want)`.

## What is stored, and where

Progress is saved as three private documents in the artifact's database (owner-only read and write), mirrored in browser storage:

| Document | Contents |
|---|---|
| `practice/state` | streak and rest tokens, per-concept mastery and review schedule, level unlocks and checkpoint results, today's plan, per-day counts, theme |
| `practice/log` | the last 450 answers (exercise, result, hints, time) |
| `practice/notes` | your "explain in your own words" answers |

Stats tab: **Save backup file** / **Copy backup** / **Restore** gives a JSON backup. Claude can read these documents to see your weak spots
and write new exercises where you struggle.

## How the learning logic works

* Each concept has mastery 0 to 100. A clean answer on a **new day** adds 25 (same-day repeats add 5), a hinted answer 12, a miss subtracts 15.
* Reviews come back after 1, 3, 7, 14, 30, 60, 90, 180 days; a miss resets to tomorrow. Unreviewed concepts fade (Fresh, Fading, Rusty).
* A level unlocks at 80% average mastery, enough solved exercises (including 2 with no hints) and a 5-question no-hint checkpoint (4 right).
* Timelines on the Today tab use your own recent pace and accuracy.
