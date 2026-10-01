from dsl import *

TRACK = "devops"

CFG = """
model:
  name: distilbert
  labels: [bug, billing, feature]
train:
  epochs: 3
  lr: 0.00002
  use_gpu: true
"""

CONCEPTS = [
    C("yaml.syntax", 1, "YAML syntax",
      "YAML is how most tools are configured: GitHub Actions, Kubernetes, Docker Compose, MLflow. It is just maps, lists and values, held together by indentation.",
      [
          CODE("""
              # a comment
              model:                      # a map (key: value pairs), nested by indenting 2 spaces
                name: distilbert          # text, no quotes needed
                labels: [bug, billing]    # a list, inline style
              train:
                epochs: 3                 # a number
                use_gpu: true             # a boolean
                steps:                    # a list, block style: one dash per item
                  - load
                  - fit
              notes: |                    # | keeps line breaks
                first line
                second line
          """, "yaml"),
          UL("**Indentation is structure.** Use spaces, never tabs. Two spaces per level is the convention.", "A map is `key: value` (a space after the colon is required). A list item starts with `- `.", "`|` keeps newlines in a text block; `>` folds them into one line."),
          WARN("Everything under the same parent must line up exactly. One extra or missing space either changes the meaning or makes the file invalid."),
          QUICK("How do you write a list of two items in block style?", ["`items: a, b`", "`items:` then `- a` and `- b` on their own lines", "`items = [a, b]`", "`items: {a, b}`"], 1, "Each list item gets its own `- ` line, indented under the key."),
      ],
      [
          predict("A config file is loaded in Python as `cfg = yaml.safe_load(text)`. What does `cfg[\"train\"][\"epochs\"] + len(cfg[\"model\"][\"labels\"])` evaluate to?", CFG, "6",
                  ["Read the number under `train`.", "Count the items in the `labels` list.", "3 + 3."], lang="yaml", verify={"yaml": 'cfg["train"]["epochs"] + len(cfg["model"]["labels"])'}),
          spot("This GitHub Actions snippet is invalid YAML. Which line is the problem?", "steps:\n  - name: Install\n    run: pip install -r requirements.txt\n   - name: Test\n    run: pytest", 4,
               ["Look at how far each `- name:` is indented.", "The two list items must start in the same column.", "Line 4 is one space off."], lang="yaml",
               fix=FIX("What is the fix?", ["Indent line 4 by 2 spaces, like line 1's list items", "Remove the dash on line 4", "Add a colon after `Test`", "Use a tab instead of spaces"], 0), diff=2, yaml_invalid=True),
          fill("Keep the line breaks in this multi-line command.", "run: ____\n  pip install -r requirements.txt\n  pytest -q", ["|"], ["A single character introduces a literal block.", "It looks like a vertical bar.", "`|`"], lang="yaml"),
      ], phases=["cloud"], minutes=4),

    C("yaml.pitfalls", 1, "YAML traps that bite in real projects",
      "YAML guesses types from how a value looks. Those guesses cause some of the most confusing bugs in CI and config files.",
      [
          CODE("""
              python-version: 3.10        # loads as the NUMBER 3.1, not the text "3.10"!
              python-version: "3.10"      # quote it and it stays text

              country: NO                 # PyYAML reads this as the boolean false (the "Norway problem")
              country: "NO"               # safe

              defaults: &d                # an anchor: name a block
                retries: 3
              prod:
                <<: *d                    # merge the anchored block here
                timeout: 30
          """, "yaml"),
          UL("**Quote** anything that could be mistaken for a number, boolean, null or date: versions, `yes`/`no`/`on`/`off`, country codes, zip codes.", "Keys must be unique. Duplicates are silently overwritten by many parsers.", "Anchors `&name` and aliases `*name` avoid repetition. `<<:` merges a map."),
          TIP("When a pipeline behaves strangely, load the file in Python (`yaml.safe_load`) and print the result. You will see exactly what the tool sees."),
          QUICK("You write `python-version: 3.10` in a workflow. Which Python do you get?", ["3.10", "3.1", "3.100", "An error"], 1, "YAML reads 3.10 as the number 3.1 and drops the trailing zero. Write `\"3.10\"`."),
      ],
      [
          predict("A workflow contains the line `python-version: 3.10`. What value does `yaml.safe_load` produce for it?", "python-version: 3.10", "3.1", ["Does the value look like a number?", "As a number the trailing zero disappears.", "It becomes `3.1`."], lang="yaml", diff=2, tags=["interview"],
                  verify={"yaml": 'cfg["python-version"]'},
                  explain=EXPLAIN("In your own words: why does `3.10` turn into `3.1`, and what is the fix?",
                                  ["YAML sees an unquoted number and stores it as a float", "Quote the value so it stays a string: \"3.10\""],
                                  "Unquoted, `3.10` is a float, and floats do not keep trailing zeros. Quoting it makes it a string, so the tool receives exactly `3.10`.")),
          predict("What does `yaml.safe_load` produce for `country: NO`?", "country: NO", "{'country': False}", ["YAML 1.1 treats some words as booleans.", "`yes`, `no`, `on` and `off` are among them.", "`NO` becomes `False`."], lang="yaml", diff=2, accept=["False"],
                  verify={"yaml": "cfg"}),
          spot("The file is meant to describe two settings, but loading it fails. Which line is the problem?", "name: ReviewRadar\nversion:2", 2,
               ["Look at the colon in each line.", "A map entry needs a space after the colon.", "`version:2` is one text blob, not a key and value."], lang="yaml",
               fix=FIX("What is the fix?", ["Write `version: 2`", "Write `version = 2`", "Write `\"version\":2`", "Add a dash before `version`"], 0), yaml_invalid=True),
      ], phases=["cloud"], minutes=4),

    C("gha.basic", 2, "GitHub Actions: your first workflow",
      "A workflow is a YAML file in `.github/workflows/`. GitHub runs its jobs on a fresh machine whenever the trigger happens.",
      [
          CODE("""
              name: CI
              on:
                push:
                  branches: [main]
                pull_request:
              jobs:
                test:
                  runs-on: ubuntu-latest
                  steps:
                    - uses: actions/checkout@v4          # a ready-made step from the marketplace
                    - uses: actions/setup-python@v5
                      with:
                        python-version: "3.12"
                    - run: pip install -r requirements.txt   # a shell command
                    - run: pytest -q
          """, "yaml"),
          TABLE(["Key", "Meaning"], [["`on`", "what triggers the workflow"], ["`jobs`", "named groups of steps; each runs on its own machine"], ["`runs-on`", "the machine type"], ["`steps`", "ordered list of steps"], ["`uses`", "run a reusable action; `with:` passes its inputs"], ["`run`", "run shell commands"]]),
          UL("A job's steps run in order and share one machine. Separate jobs run in parallel unless one `needs` another.", "If any step fails (non-zero exit code), the job stops and the check goes red."),
          WARN("Actions need to download your code first. Almost every job starts with `actions/checkout`."),
          QUICK("Which key lists the commands and actions a job runs?", ["`jobs`", "`steps`", "`on`", "`needs`"], 1, "A job contains a `steps` list."),
      ],
      [
          order("Put the lines in order to build a minimal workflow.",
                "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pytest",
                ["`jobs` must come before the job name.", "A job's `runs-on` and `steps` are indented under the job name.", "`checkout` runs before the tests."], lang="yaml", alts=[["on: [push]", "name: CI", "jobs:", "  test:", "    runs-on: ubuntu-latest", "    steps:", "      - uses: actions/checkout@v4", "      - run: pytest"]]),
          fill("Run the workflow on pushes to `main`, on an Ubuntu machine.", "on:\n  ____:\n    branches: [main]\njobs:\n  test:\n    runs-on: ____\n    steps:\n      - uses: actions/checkout@v4\n      - run: pytest", [["push"], ["ubuntu-latest"]], ["The event that fires when commits are pushed.", "GitHub's hosted Linux runner has a `-latest` label.", "`push` and `ubuntu-latest`."], lang="yaml", diff=2),
          spot("This workflow never starts any job. Which line is the problem?", "name: CI\non: [push]\njobs:\n  test:\n    runs_on: ubuntu-latest\n    steps:\n      - run: pytest", 5,
               ["Check the spelling of each key.", "GitHub's key uses a hyphen, not an underscore.", "`runs_on` is not recognised."], lang="yaml",
               fix=FIX("What is the fix?", ["Rename it to `runs-on`", "Rename `steps` to `step`", "Move it under `steps`", "Quote the value"], 0), diff=2),
      ], phases=["cloud", "serving"], minutes=5),

    C("gha.advanced", 2, "GitHub Actions: matrix, needs, secrets and caching",
      "Real pipelines test on several versions, deploy only after tests pass, and keep credentials out of the repo.",
      [
          CODE("""
              jobs:
                test:
                  runs-on: ${{ matrix.os }}
                  strategy:
                    matrix:
                      os: [ubuntu-latest, windows-latest]
                      python: ["3.10", "3.11"]        # 2 x 2 = 4 jobs
                  steps:
                    - uses: actions/checkout@v4
                    - uses: actions/setup-python@v5
                      with:
                        python-version: ${{ matrix.python }}
                        cache: pip                    # reuse downloaded packages
                    - run: pytest -q

                deploy:
                  needs: test                          # wait for every test job to pass
                  if: github.ref == 'refs/heads/main'  # only on main
                  runs-on: ubuntu-latest
                  steps:
                    - run: ./deploy.sh
                      env:
                        AWS_SECRET: ${{ secrets.AWS_SECRET }}   # from Settings > Secrets, never in the file
          """, "yaml"),
          UL("`matrix` multiplies jobs: every combination of its lists runs.", "`needs: test` makes a job wait for another and skip if it failed.", "`${{ ... }}` is an expression. Secrets are read as `${{ secrets.NAME }}` and are masked in logs.", "Add `cache:` or `actions/cache` to avoid re-downloading dependencies on every run."),
          WARN("Never paste credentials into the YAML or print them with `echo`. Store them as repository or environment secrets."),
          QUICK("A matrix has `os: [linux, windows]` and `python: [\"3.10\", \"3.11\", \"3.12\"]`. How many jobs run?", ["2", "3", "5", "6"], 3, "Every combination: 2 x 3 = 6."),
      ],
      [
          mcq("A matrix defines `os: [ubuntu-latest, windows-latest]` and `python: [\"3.10\", \"3.11\"]`, plus a `deploy` job with `needs: test`. How many `test` jobs run, and when does `deploy` start?", ["2 jobs; immediately", "4 jobs; after all 4 pass", "4 jobs; after the first one passes", "2 jobs; after both fail"], 1,
              ["Multiply the list lengths.", "`needs` waits for the whole job, which includes every matrix combination.", "A single failure stops `deploy`."], diff=2, tags=["interview"]),
          spot("The deploy step cannot authenticate: the token arrives as the literal text `secrets.AWS_TOKEN`. Which line is the problem?", "- run: ./deploy.sh\n  env:\n    AWS_TOKEN: secrets.AWS_TOKEN", 3,
               ["Compare with how expressions are written elsewhere in workflows.", "GitHub only evaluates expressions inside `${{ }}`.", "Without the braces it is just text."], lang="yaml",
               fix=FIX("What is the fix?", ["`AWS_TOKEN: ${{ secrets.AWS_TOKEN }}`", "`AWS_TOKEN: \"secrets.AWS_TOKEN\"`", "`AWS_TOKEN: $secrets.AWS_TOKEN`", "Hard-code the token"], 0), diff=2, tags=["interview"]),
          fill("Make `deploy` wait for `test` and run only on the `main` branch.", "deploy:\n  needs: ____\n  if: github.ref == 'refs/heads/____'", ["test", "main"], ["`needs` takes the name of another job.", "The branch name goes at the end of the ref.", "`test` and `main`."], lang="yaml", diff=2),
      ], phases=["cloud"], minutes=6),
]
