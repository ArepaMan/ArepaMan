from dsl import *

TRACK = "light"

PYPROJECT = """
[project]
name = "reviewradar"
version = "0.1.0"
dependencies = ["fastapi", "uvicorn"]

[tool.pytest.ini_options]
addopts = "-q"
"""

CONCEPTS = [
    C("rx.basics", 1, "Regular expressions: the basics",
      "A regular expression (regex) is a pattern for text. It finds, checks and extracts things like ticket ids, emails and dates.",
      [
          P("Type a pattern and watch it highlight the text. Try `\\d+`, then `[A-Z]{3}-\\d{4}`."),
          VIZ("regex", title="Test a pattern", pattern="[A-Z]{3}-\\d{4}", flags="g", text="Tickets TCK-1042 and BUG-7 were merged with TCK-2210.\nContact: ana@acme.com"),
          TABLE(["Pattern", "Matches"], [["`abc`", "the literal text abc"], ["`.`", "any one character"], ["`\\d` `\\w` `\\s`", "a digit, a word character, a whitespace"], ["`[abc]` `[a-z]`", "one character from a set or range"], ["`*` `+` `?`", "0 or more, 1 or more, 0 or 1"], ["`{4}` `{2,5}`", "exactly 4, between 2 and 5"], ["`^` `$`", "start and end of the text"]]),
          WARN("`.` and `*` are special. To match a literal dot write `\\.`. In Python always write patterns as raw strings: `r\"\\d+\"`."),
          QUICK("Which pattern matches exactly a 4-digit year such as 2026 (and nothing longer)?", ["`\\d{4}`", "`\\d+`", "`\\d{2,5}`", "`.{4}`"], 0, "`\\d{4}` is four digits; add `^...$` to anchor it to the whole string."),
      ],
      [
          mcq("Which pattern matches ticket ids like `TCK-1042` (three capital letters, a dash, four digits)?", ["`[A-Z]{3}-\\d{4}`", "`[A-Z]+\\d+`", "`\\w{3}\\d{4}`", "`TCK.\\d`"], 0,
              ["Three capitals is `[A-Z]{3}`.", "The dash is a literal character.", "Four digits is `\\d{4}`."], diff=2),
          predict("What does this print?", """
              import re
              print(re.findall(r"\\d+", "a1b22c333"))
          """, "['1', '22', '333']", ["`\\d+` means one or more digits in a row.", "Each separate run of digits is one match.", "Matches come back as strings."], diff=2),
          fill("Complete the pattern so it matches ids like `TCK-1042`.", "pattern = r\"TCK-____\"", [["\\d{4}", "[0-9]{4}"]], ["Four digits in a row.", "`\\d` is a digit; a number in braces repeats it.", "`\\d{4}`"], lang="regex", diff=2),
      ], phases=["data", "monitor"], minutes=4),

    C("json.basics", 1, "JSON",
      "JSON is the universal data format of web APIs. It looks like Python dicts and lists, but the rules are stricter.",
      [
          CODE("""
              {
                "id": 7,
                "text": "App crashes on login",
                "labels": ["bug", "login"],
                "urgent": true,
                "assignee": null
              }
          """, "json"),
          UL("Keys are **always double-quoted strings**. Strings use double quotes, never single quotes.", "Values: string, number, `true`/`false`, `null`, list, object. (Python writes `True`, `False`, `None`.)", "No trailing commas and no comments."),
          CODE("""
              import json
              data = json.loads('{"id": 7, "labels": ["bug"]}')   # text -> Python
              text = json.dumps(data, indent=2)                    # Python -> text
          """),
          QUICK("Which is valid JSON?", ["`{'id': 7}`", "`{\"id\": 7,}`", "`{\"id\": 7}`", "`{id: 7}`"], 2, "Only double-quoted keys with no trailing comma are valid."),
      ],
      [
          spot("This payload is rejected by the API as invalid JSON. Which line is the problem?", "{\n  \"id\": 7,\n  \"labels\": [\"bug\", \"login\"],\n}", 3,
               ["Look at the end of the last entry.", "JSON does not allow a comma after the last item.", "Line 3 ends with a comma before the closing brace."], lang="json",
               fix=FIX("What is the fix?", ["Remove the trailing comma on line 3", "Change double quotes to single quotes", "Add a comma after the `}`", "Remove the brackets"], 0), diff=2, invalid="json"),
          predict("What does this print?", """
              import json
              print(json.dumps({"a": [1, None, True]}))
          """, "{\"a\": [1, null, true]}", ["`json.dumps` produces JSON text, not Python.", "`None` becomes `null`, `True` becomes `true`.", "Keys and strings use double quotes."], diff=2),
          code("Write `top_label(text)` that takes JSON text like `{\"labels\": [\"bug\", \"login\"]}` and returns the first label.",
               "import json\n\ndef top_label(text):\n    pass\n", """
              import json

              def top_label(text):
                  return json.loads(text)["labels"][0]
          """, """
              t("top_label('{\\\"labels\\\": [\\\"bug\\\", \\\"login\\\"]}')", "bug")
              t("top_label('{\\\"id\\\": 1, \\\"labels\\\": [\\\"billing\\\"]}')", "billing")
          """, ["`json.loads` turns text into Python dicts and lists.", "Then index the dict and the list.", "`json.loads(text)[\"labels\"][0]`"], diff=2),
      ], phases=["serving", "data"], minutes=4),

    C("md.basics", 1, "Markdown for READMEs",
      "Markdown is plain text that renders as formatted text. Your README, PR descriptions and notebooks are all written in it.",
      [
          CODE("""
              # ReviewRadar                          <- level-1 heading (one per page)
              ## Quickstart                          <- level-2 heading

              Short description with **bold**, *italic* and `inline code`.

              - bullet one
              - bullet two
              1. numbered item

              [Docs](https://example.com/docs)       <- link

              ```bash
              docker compose up                      <- fenced code block with a language
              ```

              | Model | F1 |                        <- table
              |-------|----|
              | v1    | 0.81 |
          """, "markdown"),
          UL("Leave a **blank line** between paragraphs and before lists.", "Fence code with three backticks and name the language for highlighting.", "A good README answers: what is this, how do I run it, how do I use it, how do I contribute."),
          QUICK("Which line makes a level-2 heading?", ["`# Title`", "`## Title`", "`2. Title`", "`**Title**`"], 1, "Two hashes give a level-2 heading."),
      ],
      [
          order("Put these README lines in a sensible order.", "# ReviewRadar\nClassifies support tickets and answers with retrieval.\n## Quickstart\n```bash\ndocker compose up\n```\n## License", ["The title comes first, then a short description.", "A fenced block opens and closes with three backticks.", "License is usually last."], lang="markdown", diff=2),
          fill("Write a link to the docs.", "[Docs](____://example.com/docs)", ["https"], ["The text goes in square brackets, the address in round brackets.", "The address starts with the protocol.", "`https`"], lang="markdown"),
          mcq("How do you show a block of shell commands in Markdown?", ["Indent with tabs only", "Fence it with three backticks and `bash`", "Wrap it in `<code>` tags only", "Use `>` at the start of each line"], 1,
              ["Fences use a special character three times.", "The language name after the opening fence enables highlighting.", "Triple backticks."], diff=1),
      ], phases=["serving"], minutes=3),

    C("rx.groups", 2, "Regex groups, alternation and greedy matching",
      "Brackets capture parts of a match. `|` means or. By default patterns are greedy, taking as much as they can.",
      [
          VIZ("regex", title="Groups", pattern="(\\w+)@(\\w+)\\.com", flags="g", text="ana@acme.com, ben@globex.com, someone@example.org"),
          CODE("""
              (\\w+)@(\\w+)\\.com          # two capture groups: user and domain
              ERROR|WARN                  # either word
              (?P<level>[A-Z]+)           # a NAMED group (Python syntax)
              <.+>                        # greedy: <a><b> matches the WHOLE string
              <.+?>                       # lazy: matches <a>, then <b>
              \\bcat\\b                    # \\b = word boundary: 'cat' but not 'concatenate'
          """, "regex"),
          UL("Groups are numbered by their opening bracket: `\\1`, `\\2`, or `m.group(1)`.", "`(?:...)` groups without capturing. `(?P<name>...)` captures with a name.", "Greedy `.*` grabs as much as possible. Add `?` (`.*?`) to take as little as possible."),
          QUICK("`re.findall(r\"<.+>\", \"<a><b>\")` returns:", ["`['<a>', '<b>']`", "`['<a><b>']`", "`['a', 'b']`", "`[]`"], 1, "`.+` is greedy, so it runs to the last `>`."),
      ],
      [
          predict("What does this print?", """
              import re
              print(re.sub(r"(\\w+)@(\\w+)\\.com", r"\\2:\\1", "ana@acme.com"))
          """, "acme:ana", ["Group 1 is the user, group 2 the domain.", "`\\2:\\1` swaps their order.", "The `.com` is part of the matched text, so it is replaced too."], diff=3),
          code("Write `ticket_number(s)` that returns the number in a ticket id like `\"TCK-1042\"` as an `int`, or `None` if the whole string is not exactly three capital letters, a dash and four digits.",
               "import re\n\ndef ticket_number(s):\n    pass\n", """
              import re

              def ticket_number(s):
                  m = re.match(r"[A-Z]{3}-(\\d{4})$", s)
                  return int(m.group(1)) if m else None
          """, """
              t("ticket_number('TCK-1042')", 1042)
              t("ticket_number('BUG-0007')", 7)
              t("ticket_number('TCK-12')", None)
              t("ticket_number('xTCK-1042')", None)
              t("ticket_number('tck-1042')", None)
          """, ["Capture the digits in a group.", "Anchor the end with `$`. `re.match` already anchors the start.", "`m.group(1)` is the captured text, convert it with `int`. (Note: the in-browser runner loses groups with `re.fullmatch`, so use `re.match(r\"...$\")`.)"], diff=3, tags=["interview"]),
          mcq("`re.findall(r\"<.+?>\", \"<a><b>\")` returns:", ["`['<a><b>']`", "`['<a>', '<b>']`", "`['a', 'b']`", "`[]`"], 1,
              ["The `?` after `+` makes it lazy.", "Lazy takes the shortest possible match each time.", "Two short matches."], diff=3, tags=["interview"]),
      ], phases=["data", "monitor"], minutes=5),

    C("rx.python", 2, "Regex in Python: the re module",
      "`re` has a handful of functions that cover almost everything: search, match, findall, sub and compile.",
      [
          CODE("""
              import re

              re.search(r"\\d+", "ticket 42 open")        # first match anywhere -> match object (or None)
              re.match(r"\\d+", "ticket 42")              # must match at the START -> None here
              re.fullmatch(r"\\d+", "42")                 # the WHOLE string must match
              re.findall(r"\\d+", "a1b22")                # list of all matches
              re.sub(r"\\d+", "#", "a1b22")               # replace -> 'a#b#'

              m = re.match(r"(?P<level>[A-Z]+) (?P<msg>.*)", "ERROR disk full")
              m.group("level"), m.groupdict()            # ('ERROR', {...})

              pat = re.compile(r"\\d+", re.IGNORECASE)    # compile once, reuse
          """),
          UL("A match object is truthy, `None` is falsy, so `if m:` works.", "Always use raw strings `r\"...\"` so backslashes reach `re` untouched.", "`re.IGNORECASE`, `re.MULTILINE` and `re.VERBOSE` change behaviour."),
          WARN("`re.match` only matches at the beginning. If you want \"anywhere\", use `re.search`. This trips up almost everyone once."),
          TIP("The in-browser Python runner on this page is Brython, whose `re.fullmatch` drops capture groups. In real Python it works fine; here, use `re.match(r\"...$\")` when you need groups."),
          QUICK("`re.match(\"b\", \"abc\")` returns:", ["a match for `b`", "`None`", "an error", "`['b']`"], 1, "`match` only looks at the start of the string, which is `a`."),
      ],
      [
          code("Write `parse_log(line)` for lines like `2026-09-01 12:00:03 ERROR disk full`. Return a dict with keys `level` and `msg`, or `None` if the line does not fit the pattern `DATE TIME LEVEL message` (LEVEL in capitals).",
               "import re\n\ndef parse_log(line):\n    pass\n", """
              import re

              def parse_log(line):
                  m = re.match(r"\\S+ \\S+ (?P<level>[A-Z]+) (?P<msg>.*)", line)
                  return {"level": m.group("level"), "msg": m.group("msg")} if m else None
          """, """
              t("parse_log('2026-09-01 12:00:03 ERROR disk full')", {"level": "ERROR", "msg": "disk full"})
              t("parse_log('2026-09-01 12:00:04 INFO started')", {"level": "INFO", "msg": "started"})
              t("parse_log('garbage')", None)
          """, ["Two whitespace-free chunks (date and time), then the level, then the message.", "Named groups make the result easy to read.", "Return `None` when `re.match` finds nothing."], diff=3, tags=["interview"]),
          code("Write `redact_emails(text)` that replaces every email address with `[email]`. Treat an email as word characters, dots or dashes, then `@`, then a domain with at least one dot.",
               "import re\n\ndef redact_emails(text):\n    pass\n", """
              import re

              def redact_emails(text):
                  return re.sub(r"[\\w.-]+@[\\w-]+(\\.[\\w-]+)+", "[email]", text)
          """, """
              t("redact_emails('Contact ana@acme.com now')", "Contact [email] now")
              t("redact_emails('a@b.co and c.d@e-f.org')", "[email] and [email]")
              t("redact_emails('no address here')", "no address here")
          """, ["`re.sub(pattern, replacement, text)` does the swap.", "The local part: `[\\w.-]+`; then `@`; then the domain.", "Domains look like `name.tld`, possibly with more dots."], diff=3),
          mcq("What does `re.match(r\"\\d+\", \"ticket 42\")` return?", ["a match for `42`", "`None`", "`['42']`", "an error"], 1,
              ["`match` anchors at the beginning of the string.", "The string starts with `t`.", "Use `search` to find it anywhere."], diff=2, tags=["interview"]),
      ], phases=["data", "monitor"], minutes=5),

    C("toml.basics", 2, "TOML and pyproject.toml",
      "TOML is a small, readable config format. Python projects use it for `pyproject.toml`, which holds dependencies, tool settings and metadata.",
      [
          CODE("""
              [project]                                   # a table (section)
              name = "reviewradar"                         # strings MUST be quoted
              version = "0.1.0"
              dependencies = ["fastapi", "uvicorn"]        # an array

              [tool.pytest.ini_options]                    # nested table: tool -> pytest -> ini_options
              addopts = "-q"

              [tool.ruff]
              line-length = 100                            # numbers and booleans are not quoted
          """, "toml"),
          TABLE(["Format", "Comments", "Best for"], [["JSON", "no", "data exchange between programs"], ["YAML", "yes", "CI and Kubernetes config (indentation based)"], ["TOML", "yes", "tool and project config (explicit and hard to get wrong)"]]),
          UL("`[table]` headers group keys. Dots nest: `[tool.ruff]` is the table `ruff` inside `tool`.", "Read it in Python 3.11+ with `tomllib.loads(text)` (or `tomllib.load(file)` on a binary file)."),
          QUICK("In TOML, how do you write the text `reviewradar`?", ["`name = reviewradar`", "`name = \"reviewradar\"`", "`name: reviewradar`", "`name := reviewradar`"], 1, "Strings need quotes in TOML."),
      ],
      [
          predict("The text below is parsed with `tomllib.loads` into `cfg`. What does `cfg[\"project\"][\"dependencies\"][1]` give?", PYPROJECT, "uvicorn", ["`[project]` is a table, `dependencies` an array.", "Arrays are indexed from 0.", "The second item."], lang="toml", diff=2, verify={"toml": 'cfg["project"]["dependencies"][1]'}),
          spot("`tomllib` refuses to load this file. Which line is the problem?", "[project]\nname = reviewradar\nversion = \"0.1.0\"", 2,
               ["Compare how the two values are written.", "TOML strings must be quoted.", "Line 2 is a bare word."], lang="toml",
               fix=FIX("What is the fix?", ["`name = \"reviewradar\"`", "`name: reviewradar`", "`name = 'reviewradar` (open quote only)", "Remove the `[project]` line"], 0), diff=2, invalid="toml"),
          mcq("You need a config file that holds comments and is hard to mis-indent. Which format fits best?", ["JSON", "TOML", "CSV", "Plain text"], 1,
              ["JSON has no comments.", "YAML relies on indentation.", "TOML is explicit."], diff=1),
      ], phases=["serving", "cloud"], minutes=4),
]
