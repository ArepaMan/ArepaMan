from dsl import *
from tracegen import make_trace

TRACK = "python"


def steps_of(src):
    return {"steps": make_trace(src)["steps"]}


CONCEPTS = [
    C("py.vars", 1, "Variables and types",
      "A variable is a name attached to a value. Python works out the type from the value you give it.",
      [
          P("Think of `=` as sticking a label on a value. The label is the variable name, and the value lives wherever Python keeps it."),
          CODE("""
              tickets = 24          # int
              price = 9.99          # float
              name = "ReviewRadar"  # str (text)
              is_open = True        # bool
              print(type(tickets), type(price))
          """),
          P("Step through this tiny program. Watch how `count` changes, and notice the right side is worked out **before** the name is updated."),
          VIZ("trace", title="Assignment, one line at a time", **make_trace("""
              count = 3
              count = count + 1
              label = "tickets"
              print(label, count)
          """)),
          UL("`int` whole numbers: `7`, `-2`", "`float` decimals: `3.14`", "`str` text in quotes: `\"hi\"`", "`bool` `True` or `False` (capital first letter)"),
          TIP("Use `snake_case` names like `ticket_count`. Names are case sensitive, so `Count` and `count` are different variables."),
          QUICK("After `x = 5` and then `x = x + 2`, what does `x` hold?", ["5", "7", "`x + 2`", "An error"], 1, "The right side is computed first (5 + 2), then the name `x` is attached to 7."),
      ],
      [
          predict("What does this print?", """
              a = 4
              b = a
              a = 10
              print(a, b)
          """, "10 4",
                  ["`b = a` copies the **value** 4 at that moment.", "Changing `a` later does not move the label `b`.", "`a` is 10, `b` is still 4."],
                  trace=steps_of("a = 4\nb = a\na = 10\nprint(a, b)"),
                  explain=EXPLAIN("In your own words: why is `b` still 4 after `a` changed?",
                                  ["`b = a` took the value of `a` at that moment", "Reassigning `a` later does not affect `b`"],
                                  "When Python runs `b = a`, `b` gets the value 4. Later `a = 10` re-labels `a` only, so `b` keeps 4.")),
          code("Create these variables: `tickets_open` equal to `12`, `tickets_closed` equal to `30`, and `total` which adds the two variables together (use the variables, not the number 42).",
               "# write your code here\n", """
              tickets_open = 12
              tickets_closed = 30
              total = tickets_open + tickets_closed
          """, """
              t("tickets_open", 12)
              t("tickets_closed", 30)
              t("total", 42)
              tvar({"tickets_open": 5}, "total", 35)
          """, ["Make three lines, one per variable.", "`total = tickets_open + tickets_closed`", "Type the names exactly, including the underscores."]),
          mcq("Which of these is a valid Python variable name?", ["2nd_ticket", "ticket-count", "ticket_count", "class"], 2,
              ["Names can use letters, digits and underscores.", "A name cannot start with a digit and cannot contain a dash.", "`class` is reserved by Python."],
              whys=["Names cannot start with a digit.", "A dash means subtraction in Python.", None, "`class` is a reserved word."]),
      ], phases=["data"], minutes=3),

    C("py.arith", 1, "Numbers and arithmetic",
      "Python is a calculator with two kinds of division, a remainder operator and a power operator.",
      [
          TABLE(["Operator", "Meaning", "Example", "Result"], [["`+ - *`", "add, subtract, multiply", "`6 * 7`", "42"], ["`/`", "true division (always a float)", "`7 / 2`", "3.5"], ["`//`", "floor division", "`7 // 2`", "3"], ["`%`", "remainder", "`7 % 2`", "1"], ["`**`", "power", "`2 ** 5`", "32"]]),
          P("`//` and `%` work as a pair. If you have 3725 seconds, `3725 // 60` is the whole minutes and `3725 % 60` is the seconds left over."),
          VIZ("trace", title="Minutes and seconds", **make_trace("""
              total_seconds = 3725
              minutes = total_seconds // 60
              seconds = total_seconds % 60
              print(minutes, seconds)
          """)),
          WARN("Operators follow school order: `**` first, then `* / // %`, then `+ -`. Use brackets when in doubt: `(1 + 2) * 3` is 9."),
          QUICK("What is `10 % 3`?", ["3", "1", "3.33", "0"], 1, "10 = 3 * 3 + 1, so the remainder is 1."),
      ],
      [
          predict("What does this print? Careful with the separate operators.", "print(7 / 2, 7 // 2, 7 % 2, 2 ** 5)", "3.5 3 1 32",
                  ["Work out each one on its own.", "`/` keeps the decimals, `//` throws them away.", "`7 % 2` is the remainder of 7 divided by 2."]),
          code("`total_seconds` is given. Make `minutes` the number of whole minutes and `seconds` the seconds left over. Your code must work for any value of `total_seconds`.",
               "total_seconds = 3725\n# compute minutes and seconds\n", """
              total_seconds = 3725
              minutes = total_seconds // 60
              seconds = total_seconds % 60
          """, """
              t("minutes", 62)
              t("seconds", 5)
              tvar({"total_seconds": 125}, "minutes", 2)
              tvar({"total_seconds": 125}, "seconds", 5)
              tvar({"total_seconds": 59}, "minutes", 0)
          """, ["Whole minutes means dividing and dropping the remainder.", "`//` is floor division, `%` gives the remainder.", "`minutes = total_seconds // 60` and `seconds = total_seconds % 60`."]),
          mcq("Which expression gives the remainder when 17 is divided by 5?", ["17 // 5", "17 % 5", "17 / 5", "17 ** 5"], 1,
              ["The remainder operator is a symbol you may know from percentages.", "`17 // 5` is 3, which is the quotient.", "It is `%`."], tags=["interview"]),
      ], phases=["data"], minutes=3),

    C("py.strings", 1, "Strings",
      "Text in Python is a string. You can index it, slice it, and call methods that return cleaned-up copies.",
      [
          P("A string is a row of characters numbered from 0. Negative numbers count from the end. Try the slice explorer: leave a box empty to omit it."),
          VIZ("slice", title="Slice explorer", seq="TICKET42", name="word", a=1, b=4),
          CODE("""
              title = "  Refund Request  "
              print(title.strip())          # remove outer spaces
              print(title.strip().lower())  # lower case
              print(len(title.strip()))     # length
              name, n = "Ana", 3
              print(f"Hello {name}, you have {n} open tickets")  # f-string
          """),
          WARN("Strings never change in place. `title.strip()` returns a **new** string. If you want to keep it, assign it: `title = title.strip()`."),
          QUICK("What is `\"python\"[1:3]`?", ["\"py\"", "\"yt\"", "\"yth\"", "\"pyt\""], 1, "Indexes 1 and 2 are included; stop 3 is excluded. That gives `y` and `t`."),
      ],
      [
          predict("What does this print?", """
              s = "ticket"
              print(s[0], s[-1], s[1:4], s.upper())
          """, "t t ick TICKET", ["`s[0]` is the first character, `s[-1]` the last.", "A slice includes the start index and excludes the stop index.", "`s[1:4]` takes indexes 1, 2 and 3."]),
          code("`title` is given with messy spacing and capitals. Make `clean` the title with outer spaces removed and everything in lower case.",
               "title = \"  Refund REQUEST  \"\n# make clean\n", """
              title = "  Refund REQUEST  "
              clean = title.strip().lower()
          """, """
              t("clean", "refund request")
              tvar({"title": " Login BUG "}, "clean", "login bug")
              tvar({"title": "x"}, "clean", "x")
          """, ["Two string methods, one after the other.", "`.strip()` removes outer spaces, `.lower()` lowers the case.", "`clean = title.strip().lower()`"]),
          code("`name` and `n` are given. Build `message` with an f-string that gives exactly: `Hello Ana, you have 3 open tickets` (using the values of the variables).",
               "name = \"Ana\"\nn = 3\n# build message\n", """
              name = "Ana"
              n = 3
              message = f"Hello {name}, you have {n} open tickets"
          """, """
              t("message", "Hello Ana, you have 3 open tickets")
              tvar({"name": "Ben", "n": 12}, "message", "Hello Ben, you have 12 open tickets")
          """, ["An f-string starts with `f` before the quote.", "Put a variable inside braces: `{name}`.", "`message = f\"Hello {name}, you have {n} open tickets\"`"], diff=2),
      ], phases=["data"], minutes=4),

    C("py.lists", 1, "Lists",
      "A list is an ordered, changeable collection. It is the workhorse for holding rows, scores and tokens.",
      [
          CODE("""
              queue = ["bug", "billing", "account"]
              print(queue[0], queue[-1])      # bug account
              queue.append("feature")         # add to the end
              queue.insert(0, "urgent")       # add at a position
              done = queue.pop()              # remove and return the last
              print(len(queue), "bug" in queue)
          """),
          P("Lists use the same slicing as strings. Try it on a list of five items."),
          VIZ("slice", title="List slices", seq=["a", "b", "c", "d", "e"], name="items", a=1, b=-1),
          WARN("Lists **change in place**. `queue.append(x)` returns `None`, so `queue = queue.append(x)` destroys your list."),
          UL("`len(xs)` size", "`sum(xs)`, `min(xs)`, `max(xs)` for numbers", "`sorted(xs)` returns a new sorted list; `xs.sort()` sorts in place"),
          QUICK("What is `[1, 2, 3, 4, 5][1:3]`?", ["[1, 2]", "[2, 3]", "[2, 3, 4]", "[1, 2, 3]"], 1, "Start index 1 is included, stop index 3 is excluded."),
      ],
      [
          predict("What does this print?", """
              queue = ["bug", "billing"]
              queue.append("feature")
              queue.insert(0, "urgent")
              last = queue.pop()
              print(queue, len(queue), last)
          """, "['urgent', 'bug', 'billing'] 3 feature",
                  ["Write the list after each line.", "`insert(0, ...)` puts the item at the front.", "`pop()` removes and returns the **last** item, so `last` is 'feature' and the list is shorter."],
                  trace=steps_of("queue = ['bug', 'billing']\nqueue.append('feature')\nqueue.insert(0, 'urgent')\nlast = queue.pop()\nprint(queue, len(queue), last)"), diff=2),
          code("`scores` is given. Make `best` the highest score and `average` the mean of all scores.",
               "scores = [3, 9, 4, 7]\n# compute best and average\n", """
              scores = [3, 9, 4, 7]
              best = max(scores)
              average = sum(scores) / len(scores)
          """, """
              t("best", 9)
              t("average", 5.75)
              tvar({"scores": [5, 1]}, "best", 5)
              tvar({"scores": [5, 1]}, "average", 3.0)
          """, ["Python has built-ins for these.", "`max(...)` for the biggest; the mean is the sum divided by the count.", "`best = max(scores)` and `average = sum(scores) / len(scores)`."]),
          mcq("`names = ['ana', 'ben']` then `names = names.append('cy')`. What is `names` afterwards?", ["['ana', 'ben', 'cy']", "None", "['cy']", "An error"], 1,
              ["What does `append` return?", "Methods that change a list in place return `None`.", "The assignment overwrites `names` with that return value."],
              whys=["That would be right without the `names =` part.", None, None, None], tags=["interview"],
              why="`append` mutates the list and returns `None`. The assignment then replaces `names` with `None`. Just call `names.append('cy')`."),
      ], phases=["data"], minutes=4),

    C("py.cond", 1, "Decisions: if, elif, else",
      "Code can choose. An `if` runs its block only when the condition is true, and Python reads the branches top to bottom.",
      [
          CODE("""
              priority = 2
              if priority >= 3:
                  print("page oncall")
              elif priority == 2:
                  print("same day")
              else:
                  print("backlog")
          """),
          P("Only the **first** branch whose condition is true runs. Indentation (4 spaces) is how Python knows what belongs inside."),
          TABLE(["Operator", "Means"], [["`==` `!=`", "equal, not equal"], ["`< <= > >=`", "ordering"], ["`and` `or` `not`", "combine conditions"], ["`in`", "membership: `\"a\" in \"cat\"`"]]),
          WARN("`=` assigns, `==` compares. Writing `if x = 5:` is a syntax error."),
          VIZ("trace", title="Which branch runs?", **make_trace("""
              priority = 2
              if priority >= 3:
                  label = "page oncall"
              elif priority == 2:
                  label = "same day"
              else:
                  label = "backlog"
              print(label)
          """)),
          QUICK("With `n = 7`, what does `n > 3 and n < 5` evaluate to?", ["True", "False", "7", "An error"], 1, "`n > 3` is True but `n < 5` is False, and `and` needs both."),
      ],
      [
          predict("What does this print?", """
              n = 15
              if n % 3 == 0 and n % 5 == 0:
                  print("both")
              elif n % 3 == 0:
                  print("three")
              else:
                  print("neither")
          """, "both", ["Work out `n % 3` and `n % 5` first.", "Both remainders are 0, so the first condition is true.", "Once a branch runs, the rest are skipped."]),
          code("`words` is the length of a ticket in words. Set `size` to `\"short\"` if it is under 20, `\"medium\"` if it is under 100, otherwise `\"long\"`.",
               "words = 45\n# set size\n", """
              words = 45
              if words < 20:
                  size = "short"
              elif words < 100:
                  size = "medium"
              else:
                  size = "long"
          """, """
              t("size", "medium")
              tvar({"words": 5}, "size", "short")
              tvar({"words": 19}, "size", "short")
              tvar({"words": 20}, "size", "medium")
              tvar({"words": 99}, "size", "medium")
              tvar({"words": 100}, "size", "long")
              tvar({"words": 400}, "size", "long")
          """, ["Use an `if`, an `elif` and an `else`.", "Check the smallest range first. The `elif` only runs if the `if` failed.", "Test the boundaries: 19, 20, 99 and 100."], diff=2,
               explain=EXPLAIN("In your own words: why do you only need `< 100` in the `elif`, not `20 <= words < 100`?",
                               ["Python reaches `elif` only when the `if` was false", "So words is already 20 or more at that point"],
                               "The branches are checked in order. If we reach the `elif`, the first test already failed, so `words` is at least 20. That makes the lower bound redundant.")),
          spot("This code should print `five`. Which line has the bug?", ["n = 5", "if n = 5:", "    print(\"five\")"], 2,
               ["Look at what each line is meant to do.", "One line uses a symbol for assigning where it needs one for comparing.", "Line 2."],
               lang="python", fix=FIX("What is the fix?", ["Replace `=` with `==`", "Replace `if` with `while`", "Indent the first line", "Add a colon after `print`"], 0)),
      ], phases=["data"], minutes=4),

    C("py.loops", 1, "Loops",
      "A loop repeats code. Use `for` to go through a collection and `while` to repeat until a condition changes.",
      [
          CODE("""
              total = 0
              for n in range(1, 5):   # 1, 2, 3, 4
                  total = total + n
              print(total)            # 10

              count = 3
              while count > 0:
                  print(count)
                  count -= 1
          """),
          VIZ("trace", title="A for loop accumulating a total", **make_trace("""
              total = 0
              for n in range(1, 4):
                  total = total + n
              print(total)
          """)),
          UL("`range(5)` gives 0 to 4. `range(2, 6)` gives 2 to 5. The stop is excluded.", "`for x in items:` visits every item. `for i, x in enumerate(items):` also gives the index.", "`break` leaves the loop early; `continue` skips to the next pass."),
          WARN("A `while` loop needs something inside that eventually makes the condition false. If not, it runs forever."),
          QUICK("How many times does `for i in range(3):` run its body?", ["2", "3", "4", "It depends"], 1, "`range(3)` is 0, 1, 2: three values."),
      ],
      [
          order("Put the lines in order to build `squares = [1, 4, 9, 16]` and print it.",
                ["squares = []", "for n in range(1, 5):", "    squares.append(n * n)", "print(squares)"],
                ["Start by creating the empty list.", "The `append` line must be inside the loop, so it comes right after the `for` line.", "`print` comes last, after the loop."], lang="python"),
          code("`n` is given. Make `total` the sum of all the **even** numbers from 1 up to and including `n`.",
               "n = 10\ntotal = 0\n# loop here\n", """
              n = 10
              total = 0
              for i in range(1, n + 1):
                  if i % 2 == 0:
                      total += i
          """, """
              t("total", 30)
              tvar({"n": 7}, "total", 12)
              tvar({"n": 1}, "total", 0)
              tvar({"n": 2}, "total", 2)
          """, ["`range(1, n + 1)` includes `n`.", "An even number has `i % 2 == 0`.", "Loop, test with `if`, then `total += i`."], diff=2),
          predict("What does this print?", """
              n = 3
              while n > 0:
                  print(n)
                  n -= 1
              print("go")
          """, "3\n2\n1\ngo", ["Write `n` before each check.", "The loop stops when `n > 0` becomes false.", "`go` is printed once, after the loop."],
                  explain=EXPLAIN("In your own words: why does this loop stop?",
                                  ["The condition `n > 0` is checked before every pass", "`n` goes down by 1 each pass until it reaches 0", "When it is false the loop ends and the next line runs"],
                                  "Each pass prints `n` and makes it smaller. After the pass with `n = 1`, `n` becomes 0, the condition `n > 0` is false, and Python moves on to `print(\"go\")`.")),
      ], phases=["data"], minutes=4),

    C("py.funcs", 1, "Functions",
      "A function packages code under a name. It takes inputs (parameters) and hands back a result with `return`.",
      [
          CODE("""
              def ticket_label(priority, category="general"):
                  return f"[P{priority}] {category}"

              print(ticket_label(2))            # [P2] general
              print(ticket_label(3, "bug"))     # [P3] bug
          """),
          VIZ("trace", title="Calling a function", **make_trace("""
              def double(x):
                  return x * 2

              answer = double(21)
              print(answer)
          """)),
          WARN("`print` shows a value on screen. `return` hands a value back to the caller. A function without `return` gives back `None`."),
          UL("Parameters with `=` are **defaults**, used when the caller leaves them out.", "You can pass arguments by name: `ticket_label(3, category=\"bug\")`.", "Variables created inside a function stay inside it."),
          QUICK("What does `def f(x): x * 2` return when called as `f(4)`?", ["8", "None", "4", "An error"], 1, "There is no `return`, so the function returns `None`."),
      ],
      [
          code("Write a function `ticket_label(priority, category=\"general\")` that returns a string like `[P2] general`.",
               "def ticket_label(priority, category=\"general\"):\n    pass\n", """
              def ticket_label(priority, category="general"):
                  return f"[P{priority}] {category}"
          """, """
              t("ticket_label(1)", "[P1] general")
              t("ticket_label(3, 'bug')", "[P3] bug")
              t("ticket_label(2, category='billing')", "[P2] billing")
          """, ["The function should `return` a string, not print it.", "Use an f-string with two placeholders.", "`return f\"[P{priority}] {category}\"`"]),
          predict("What does this print?", """
              def add(a, b):
                  print(a + b)

              result = add(2, 3)
              print(result)
          """, "5\nNone", ["`add` prints inside the function. What does it return?", "There is no `return` statement.", "So `result` is `None`."],
                  explain=EXPLAIN("In your own words: why is the second line `None`?",
                                  ["`add` has no `return` so it returns None", "The 5 came from `print` inside the function, not from a returned value"],
                                  "The `5` is printed while `add` runs. Because the function never returns anything, `result` is `None`, and the last `print` shows that."), tags=["interview"], diff=2),
          code("Write `clamp(x, lo, hi)` that returns `lo` if `x` is below `lo`, `hi` if `x` is above `hi`, otherwise `x`.",
               "def clamp(x, lo, hi):\n    pass\n", """
              def clamp(x, lo, hi):
                  if x < lo:
                      return lo
                  if x > hi:
                      return hi
                  return x
          """, """
              t("clamp(5, 0, 10)", 5)
              t("clamp(-3, 0, 10)", 0)
              t("clamp(42, 0, 10)", 10)
              t("clamp(0, 0, 10)", 0)
              t("clamp(10, 0, 10)", 10)
          """, ["Three cases: too low, too high, fine.", "An early `return` ends the function.", "Check `x < lo`, then `x > hi`, then `return x`."], diff=2),
      ], phases=["data", "serving"], minutes=4),

    C("py.dicts", 1, "Dictionaries and sets",
      "A dict looks things up by key. A set keeps unique items. Between them you can count, group and de-duplicate almost anything.",
      [
          CODE("""
              counts = {"bug": 2, "billing": 1}
              counts["bug"] += 1             # update
              counts["feature"] = 4          # add
              print(counts.get("account", 0))  # 0 (no KeyError)
              print("billing" in counts)       # True
              for key, value in counts.items():
                  print(key, value)

              unique = set(["a", "b", "a"])    # {'a', 'b'}
          """),
          WARN("`counts[\"missing\"]` raises `KeyError`. Use `counts.get(\"missing\", 0)` when a missing key is normal."),
          P("The classic pattern: count how often each thing appears."),
          CODE("""
              tally = {}
              for word in ["bug", "bug", "billing"]:
                  tally[word] = tally.get(word, 0) + 1
              print(tally)   # {'bug': 2, 'billing': 1}
          """),
          UL("Keys must be hashable: strings, numbers and tuples work; lists do not.", "Sets have no order and no duplicates: `{1, 2} | {2, 3}` is `{1, 2, 3}`."),
          QUICK("`d = {\"a\": 1}`. What does `d.get(\"b\")` return?", ["0", "None", "An error", "\"b\""], 1, "`get` returns `None` unless you pass a default."),
      ],
      [
          predict("What does this print?", """
              counts = {"bug": 2, "billing": 1}
              counts["bug"] += 1
              counts["feature"] = 4
              print(counts.get("account", 0), len(counts), "billing" in counts)
          """, "0 3 True", ["Write the dict after each line.", "`get` with a default never raises.", "After the two changes the dict has three keys."]),
          code("Write `count_categories(categories)` that takes a list of strings and returns a dict mapping each category to how many times it appears.",
               "def count_categories(categories):\n    pass\n", """
              def count_categories(categories):
                  counts = {}
                  for c in categories:
                      counts[c] = counts.get(c, 0) + 1
                  return counts
          """, """
              t("count_categories(['bug', 'bug', 'billing'])", {"bug": 2, "billing": 1})
              t("count_categories([])", {})
              t("count_categories(['a'])", {"a": 1})
          """, ["Start with an empty dict and loop over the list.", "For each item, add 1 to its current count (0 if unseen).", "`counts[c] = counts.get(c, 0) + 1`, then `return counts`."], diff=2, tags=["interview"]),
          code("Write `unique_sorted(items)` that returns the unique items as a sorted list.",
               "def unique_sorted(items):\n    pass\n", """
              def unique_sorted(items):
                  return sorted(set(items))
          """, """
              t("unique_sorted([3, 1, 3, 2, 1])", [1, 2, 3])
              t("unique_sorted(['b', 'a', 'b'])", ['a', 'b'])
              t("unique_sorted([])", [])
          """, ["A set removes duplicates.", "`sorted(...)` turns any iterable into a sorted list.", "`return sorted(set(items))`"]),
      ], phases=["data"], minutes=4),
]
