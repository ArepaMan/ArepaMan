"""Tracks, levels, ReviewRadar phases and shared SQL datasets."""

PHASES = [
    {"id": "data", "name": "Data and baselines", "short": "Data", "blurb": "Clean tickets, build features, train a first scikit-learn baseline."},
    {"id": "deep", "name": "Deep model", "short": "Deep", "blurb": "Fine-tune a transformer with PyTorch and Hugging Face."},
    {"id": "serving", "name": "Serving", "short": "Serving", "blurb": "FastAPI endpoint, tests, a lean Docker image."},
    {"id": "cloud", "name": "Cloud and CI/CD", "short": "Cloud", "blurb": "GitHub Actions, Kubernetes manifests, Terraform on AWS."},
    {"id": "monitor", "name": "Monitoring", "short": "Monitor", "blurb": "Track predictions and drift with SQL, shell scripts and Python stats."},
]

TRACKS = [
    {"id": "python", "name": "Python", "short": "Python", "blurb": "Core language to NumPy, Pandas, scikit-learn, PyTorch and FastAPI.", "requires": [], "unlockText": "",
     "levels": [
         {"n": 1, "name": "Foundations", "blurb": "Variables, loops, functions, lists, dicts."},
         {"n": 2, "name": "Working", "blurb": "Comprehensions, classes, errors, mutability."},
         {"n": 3, "name": "Fluent", "blurb": "Typing, generators, decorators, pytest, complexity."},
         {"n": 4, "name": "Advanced", "blurb": "NumPy, Pandas, SciPy, scikit-learn, metrics."},
         {"n": 5, "name": "Expert", "blurb": "PyTorch shapes, Hugging Face, FastAPI, performance."}]},
    {"id": "sql", "name": "SQL", "short": "SQL", "blurb": "From SELECT to window functions, indexes and pgvector ideas.", "requires": [], "unlockText": "",
     "levels": [
         {"n": 1, "name": "Foundations", "blurb": "SELECT, WHERE, ORDER BY."},
         {"n": 2, "name": "Working", "blurb": "Aggregates, joins, changing data."},
         {"n": 3, "name": "Fluent", "blurb": "Subqueries, CTEs, CASE, set operations."},
         {"n": 4, "name": "Advanced", "blurb": "Window functions and schema design."},
         {"n": 5, "name": "Expert", "blurb": "Indexes, query plans, vector search."}]},
    {"id": "bash", "name": "Bash and shell", "short": "Bash", "blurb": "Navigate, pipe, search, script and automate.", "requires": [], "unlockText": "",
     "levels": [
         {"n": 1, "name": "Foundations", "blurb": "Paths, files, globs."},
         {"n": 2, "name": "Working", "blurb": "Pipes, redirection, grep, find."},
         {"n": 3, "name": "Fluent", "blurb": "sed, awk, environment variables, quoting."},
         {"n": 4, "name": "Advanced", "blurb": "Scripts, exit codes, strict mode."},
         {"n": 5, "name": "Expert", "blurb": "Makefiles and CI-style scripting."}]},
    {"id": "devops", "name": "YAML, Docker and Terraform", "short": "Config", "blurb": "Read and fix GitHub Actions, Dockerfiles, Kubernetes and Terraform.",
     "requires": [{"track": "python", "cleared": 1}, {"track": "bash", "cleared": 1}], "unlockText": "Unlocks after you clear Level 1 of Python and of Bash, so the config makes sense.",
     "levels": [
         {"n": 1, "name": "Foundations", "blurb": "YAML syntax and its traps."},
         {"n": 2, "name": "Working", "blurb": "GitHub Actions workflows."},
         {"n": 3, "name": "Fluent", "blurb": "Dockerfiles, layers, multi-stage builds."},
         {"n": 4, "name": "Advanced", "blurb": "Kubernetes manifests."},
         {"n": 5, "name": "Expert", "blurb": "Terraform on AWS."}]},
    {"id": "light", "name": "Regex, JSON, TOML, Markdown", "short": "Light", "blurb": "The small formats you touch every day.", "requires": [], "unlockText": "",
     "levels": [
         {"n": 1, "name": "Basics", "blurb": "Regex, JSON, Markdown."},
         {"n": 2, "name": "Working", "blurb": "Groups, TOML, Python re."}]},
]

ROTATION = ["sql", "bash", "sql", "devops", "light", "bash", "sql", "devops", "bash", "light"]


def _support():
    cust = [(1, "Ana Ruiz", "pro", "ES"), (2, "Ben Carter", "free", "US"), (3, "Chika Obi", "enterprise", "NG"), (4, "Dmitri Volkov", "pro", "RU"),
            (5, "Elena Rossi", "free", "IT"), (6, "Farid Haddad", "enterprise", "MA"), (7, "Grace Lee", "pro", "US"), (8, "Hiro Tanaka", "free", "JP"),
            (9, "Isla Murphy", "pro", "IE"), (10, "Jorge Pena", "free", "MX")]
    tick = [
        (1, 1, "billing", 2, "closed", "2026-09-01", "2026-09-02", 42, 1), (2, 2, "bug", 3, "closed", "2026-09-01", "2026-09-04", 118, 2),
        (3, 3, "account", 1, "closed", "2026-09-02", "2026-09-02", 20, 1), (4, 4, "bug", 3, "open", "2026-09-03", None, 95, 2),
        (5, 5, "feature", 1, "open", "2026-09-03", None, 60, None), (6, 6, "billing", 2, "closed", "2026-09-04", "2026-09-05", 38, 3),
        (7, 7, "bug", 2, "closed", "2026-09-05", "2026-09-08", 150, 2), (8, 1, "account", 1, "closed", "2026-09-06", "2026-09-06", 15, 1),
        (9, 2, "billing", 3, "open", "2026-09-07", None, 70, 3), (10, 3, "bug", 3, "closed", "2026-09-08", "2026-09-10", 210, 4),
        (11, None, "other", 1, "open", "2026-09-08", None, 12, None), (12, 4, "feature", 2, "closed", "2026-09-09", "2026-09-15", 88, 4),
        (13, 5, "billing", 1, "closed", "2026-09-10", "2026-09-11", 30, 1), (14, 6, "bug", 3, "open", "2026-09-10", None, 132, 2),
        (15, 7, "account", 2, "closed", "2026-09-11", "2026-09-12", 25, 3), (16, 8, "bug", 2, "closed", "2026-09-12", "2026-09-14", 77, 2),
        (17, 9, "feature", 1, "open", "2026-09-12", None, 64, None), (18, 1, "bug", 3, "closed", "2026-09-13", "2026-09-16", 140, 4),
        (19, 3, "billing", 2, "closed", "2026-09-14", "2026-09-14", 33, 3), (20, 8, "billing", 1, "closed", "2026-09-15", "2026-09-16", 29, 1),
        (21, 9, "bug", 2, "open", "2026-09-15", None, 101, 2), (22, 4, "account", 1, "closed", "2026-09-16", "2026-09-16", 18, 1),
        (23, 2, "feature", 2, "closed", "2026-09-17", "2026-09-20", 72, 4), (24, 6, "billing", 3, "open", "2026-09-18", None, 55, 3)]
    agents = [(1, "Mia", "tier1"), (2, "Noah", "tier2"), (3, "Olu", "tier1"), (4, "Priya", "tier2")]

    def v(x):
        return "NULL" if x is None else ("'%s'" % x if isinstance(x, str) else str(x))
    s = ["CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, plan TEXT, country TEXT);",
         "CREATE TABLE agents(id INTEGER PRIMARY KEY, name TEXT, team TEXT);",
         "CREATE TABLE tickets(id INTEGER PRIMARY KEY, customer_id INTEGER, category TEXT, priority INTEGER, status TEXT, created_at TEXT, resolved_at TEXT, words INTEGER, agent_id INTEGER);"]
    s += ["INSERT INTO customers VALUES(%s);" % ",".join(v(x) for x in r) for r in cust]
    s += ["INSERT INTO agents VALUES(%s);" % ",".join(v(x) for x in r) for r in agents]
    s += ["INSERT INTO tickets VALUES(%s);" % ",".join(v(x) for x in r) for r in tick]
    return "\n".join(s)


def _ml():
    labels = ["billing", "bug", "account", "feature"]
    wrong = {3: "bug", 6: "account", 9: "billing", 14: "bug", 17: "feature", 18: "billing", 22: "bug", 23: "account", 24: "bug"}
    conf = [0.97, 0.91, 0.88, 0.62, 0.95, 0.58, 0.93, 0.89, 0.55, 0.96, 0.92, 0.9, 0.87, 0.51, 0.94, 0.9, 0.49, 0.6, 0.92, 0.88, 0.95, 0.47, 0.52, 0.45]
    rows = []
    for i in range(1, 25):
        model = "v1" if i <= 12 else "v2"
        day = "2026-09-%02d" % (1 + (i - 1) // 2)
        true = labels[(i * 3 + i // 4) % 4]
        pred = wrong.get(i, true)
        if pred == true and i in wrong:
            pred = labels[(labels.index(true) + 1) % 4]
        rows.append((i, model, day, true, pred, conf[i - 1]))
    s = ["CREATE TABLE predictions(id INTEGER PRIMARY KEY, model TEXT, day TEXT, true_label TEXT, pred_label TEXT, confidence REAL);"]
    s += ["INSERT INTO predictions VALUES(%d,'%s','%s','%s','%s',%s);" % r for r in rows]
    return "\n".join(s)


DATASETS = {"support": {"setup": _support()}, "ml": {"setup": _ml()}}
