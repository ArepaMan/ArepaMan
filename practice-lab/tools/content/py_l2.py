from dsl import *
from tracegen import make_trace

TRACK = "python"


def steps_of(src):
    return {"steps": make_trace(src)["steps"]}


CONCEPTS = [
    C("py.comp", 2, "Comprehensions",
      "A comprehension builds a list, dict or set in one expression. It reads like the sentence you would say out loud.",
      [
          CODE("""
              nums = [1, 2, 3, 4, 5, 6]
              squares = [n * n for n in nums]                 # [1, 4, 9, 16, 25, 36]
              even_squares = [n * n for n in nums if n % 2 == 0]   # [4, 16, 36]
              lengths = {w: len(w) for w in ["bug", "billing"]}   # {'bug': 3, 'billing': 7}
              letters = {c for c in "banana"}                 # {'b', 'a', 'n'}
          """),
          P("The pattern is `[what  for item in things  if condition]`. The `if` is optional and filters items out."),
          VIZ("trace", title="What a comprehension does", **make_trace("""
              nums = [1, 2, 3, 4]
              result = [n * n for n in nums if n % 2 == 0]
              print(result)
          """)),
          TIP("If a comprehension needs more than one `if` or nested loops, a normal `for` loop is usually easier to read."),
          QUICK("What does `[c.upper() for c in \"ab\"]` produce?", ["\"AB\"", "['A', 'B']", "['a', 'b']", "{'A', 'B'}"], 1, "Square brackets build a list, with one uppercase letter per character."),
      ],
      [
          code("Write `squares_of_evens(nums)` that returns a list of the squares of only the even numbers, in the original order.",
               "def squares_of_evens(nums):\n    pass\n", """
              def squares_of_evens(nums):
                  return [n * n for n in nums if n % 2 == 0]
          """, """
              t("squares_of_evens([1, 2, 3, 4])", [4, 16])
              t("squares_of_evens([])", [])
              t("squares_of_evens([5, 7])", [])
              t("squares_of_evens([6, -2])", [36, 4])
          """, ["Filter with `if`, transform at the front.", "An even number has `n % 2 == 0`.", "`return [n * n for n in nums if n % 2 == 0]`"]),
          predict("What does this print?", """
              words = ["bug", "billing", "ui"]
              print({w: len(w) for w in words if len(w) > 2})
              print([x for x in "a1b2" if x.isdigit()])
          """, "{'bug': 3, 'billing': 7}\n['1', '2']", ["The first is a dict comprehension with a filter.", "`ui` has length 2, so the filter drops it.", "Digits stay as strings: `'1'`, not `1`."], diff=2),
          code("Write `word_lengths(text)` that returns a dict mapping each distinct lower-cased word in `text` to its length.",
               "def word_lengths(text):\n    pass\n", """
              def word_lengths(text):
                  return {w: len(w) for w in text.lower().split()}
          """, """
              t("word_lengths('Bug bug Billing')", {"bug": 3, "billing": 7})
              t("word_lengths('x y x')", {"x": 1, "y": 1})
              t("word_lengths('A b')", {"a": 1, "b": 1})
          """, ["`text.lower().split()` gives the list of words.", "A dict comprehension automatically keeps one entry per key.", "`return {w: len(w) for w in text.lower().split()}`"], diff=2),
      ], phases=["data"], minutes=4),

    C("py.unpack", 2, "Tuples, unpacking and sorting",
      "Tuples bundle values together. Unpacking splits them back out, and `sorted(..., key=...)` orders anything by anything.",
      [
          CODE("""
              point = (3, 4)               # a tuple: fixed, ordered
              x, y = point                 # unpacking
              first, *rest = [10, 20, 30]  # first=10, rest=[20, 30]

              names = ["ana", "ben", "cy"]
              ages = [31, 25, 40]
              pairs = list(zip(names, ages))   # [('ana', 31), ('ben', 25), ('cy', 40)]
              for i, name in enumerate(names, start=1):
                  print(i, name)

              scores = {"ana": 7, "ben": 9, "cy": 4}
              ranked = sorted(scores, key=scores.get, reverse=True)   # ['ben', 'ana', 'cy']
              longest = max(names, key=len)
          """),
          P("`key=` takes a function that turns each item into the thing to compare. `lambda` is a one-line function you write on the spot: `sorted(rows, key=lambda r: r[1])`."),
          WARN("`zip` stops at the shortest input. It never raises an error for mismatched lengths."),
          QUICK("What is `sorted([\"bb\", \"a\", \"ccc\"], key=len)`?", ["['a', 'bb', 'ccc']", "['ccc', 'bb', 'a']", "['a', 'bb', 'ccc'] only if reversed", "An error"], 0, "Sorting by length, shortest first."),
      ],
      [
          predict("What does this print?", """
              pairs = list(zip(["a", "b", "c"], [1, 2]))
              x, *rest = [10, 20, 30]
              print(pairs, x, rest)
          """, "[('a', 1), ('b', 2)] 10 [20, 30]", ["`zip` pairs items until the shorter list runs out.", "`*rest` collects whatever is left into a list.", "`x` is the first item."]),
          code("Write `top_n(scores, n)` where `scores` is a dict of name to score. Return a list of the `n` names with the highest scores, best first.",
               "def top_n(scores, n):\n    pass\n", """
              def top_n(scores, n):
                  return sorted(scores, key=scores.get, reverse=True)[:n]
          """, """
              t("top_n({'ana': 7, 'ben': 9, 'cy': 4}, 2)", ["ben", "ana"])
              t("top_n({'ana': 7}, 3)", ["ana"])
              t("top_n({}, 1)", [])
          """, ["Sort the dict's keys by their value.", "`sorted(scores, key=scores.get, reverse=True)`", "Then slice off the first `n` with `[:n]`."], diff=2, tags=["interview"]),
          code("Write `min_max(values)` that returns the smallest and largest value as a tuple `(lo, hi)`.",
               "def min_max(values):\n    pass\n", """
              def min_max(values):
                  return min(values), max(values)
          """, """
              t("min_max([3, 1, 2])", (1, 3))
              t("min_max([5])", (5, 5))
              tx("lo, hi = min_max([4, 9, 2])", "(lo, hi)", (2, 9))
          """, ["Python lets a function return several values at once.", "`return a, b` returns the tuple `(a, b)`.", "`return min(values), max(values)`"]),
      ], phases=["data"], minutes=4),

    C("py.errors", 2, "Exceptions",
      "Errors are normal. `try` and `except` let you handle the ones you expect, and `raise` lets you signal the ones your own code detects.",
      [
          CODE("""
              def parse(s):
                  try:
                      return int(s)
                  except ValueError:        # only the error we expect
                      return -1
                  finally:
                      print("done")         # runs no matter what
          """),
          UL("`ValueError` bad value, `TypeError` wrong type, `KeyError` missing dict key, `IndexError` list index too big, `ZeroDivisionError`.", "Catch **specific** exceptions. A bare `except:` hides real bugs.", "`raise ValueError(\"priority must be 1 to 3\")` stops the function and tells the caller what was wrong."),
          TIP("Python prefers asking forgiveness over permission: try the operation and handle the failure, instead of testing everything first."),
          QUICK("What does `int(\"x\")` raise?", ["TypeError", "ValueError", "KeyError", "Nothing, it returns 0"], 1, "The type is right (a string) but the value cannot be turned into a number."),
      ],
      [
          predict("What does this print?", """
              def parse(s):
                  try:
                      return int(s)
                  except ValueError:
                      return -1
                  finally:
                      print("done")

              print(parse("12"), parse("x"))
          """, "done\ndone\n12 -1", ["Both calls run before `print` shows anything.", "`finally` runs every time, even after a `return`.", "So `done` appears twice, then the results line."], diff=2,
                  explain=EXPLAIN("In your own words: why does `done` print before `12 -1`?",
                                  ["Both `parse(...)` calls are evaluated before `print` runs", "`finally` runs each time the function exits"],
                                  "The arguments to `print` are computed first, so both `parse` calls happen (each printing `done` from `finally`). Only then does `print` show `12 -1`.")),
          code("Write `safe_div(a, b)` that returns `a / b`, or `None` when `b` is zero. Other errors (like dividing text) must **not** be hidden.",
               "def safe_div(a, b):\n    pass\n", """
              def safe_div(a, b):
                  try:
                      return a / b
                  except ZeroDivisionError:
                      return None
          """, """
              t("safe_div(6, 3)", 2.0)
              t("safe_div(1, 0)", None)
              texc("safe_div('a', 2)", TypeError)
          """, ["Wrap the division in `try`.", "Catch the specific error: `ZeroDivisionError`.", "A `TypeError` is not caught, so it still reaches the caller."], diff=2),
          code("Write `parse_priority(text)` that converts text like `\"2\"` to an int and returns it, but raises `ValueError` if the number is not 1, 2 or 3.",
               "def parse_priority(text):\n    pass\n", """
              def parse_priority(text):
                  n = int(text)
                  if n not in (1, 2, 3):
                      raise ValueError("priority must be 1, 2 or 3")
                  return n
          """, """
              t("parse_priority('2')", 2)
              texc("parse_priority('9')", ValueError)
              texc("parse_priority('abc')", ValueError)
              t("parse_priority('3')", 3)
          """, ["`int(text)` already raises `ValueError` for bad text.", "After converting, check the range yourself.", "`if n not in (1, 2, 3): raise ValueError(...)`"], diff=2),
      ], phases=["data", "serving"], minutes=4),

    C("py.files", 2, "Files and paths",
      "Reading and writing files is just looping over lines. Use `with` so the file always closes, and `pathlib` to handle paths safely.",
      [
          CODE("""
              with open("tickets.csv") as f:      # closes automatically
                  for line in f:                  # one line at a time
                      name, count = line.strip().split(",")

              with open("report.txt", "w") as out:   # "w" = write (overwrites)
                  out.write("hello\\n")

              from pathlib import Path
              p = Path("data/raw/tickets.csv")
              print(p.name, p.suffix, p.parent)      # tickets.csv .csv data/raw
          """),
          P("A file object is just something you can loop over line by line. `io.StringIO` makes a fake file from a string, which is perfect for testing code that reads files."),
          CODE("""
              import io
              f = io.StringIO("bug,2\\nbilling,1\\n")
              rows = [line.strip().split(",") for line in f]
              print(rows)      # [['bug', '2'], ['billing', '1']]
          """),
          WARN("Everything you read from a text file is a string. Convert with `int(...)` or `float(...)` yourself."),
          QUICK("Why write `with open(...) as f:` instead of `f = open(...)`?", ["It is faster", "The file is closed even if an error happens", "It lets you read in binary", "It is required by Python 3"], 1, "`with` guarantees cleanup, even when the code inside raises."),
      ],
      [
          predict("What does this print?", """
              import io
              f = io.StringIO("bug,2\\nbilling,1\\n")
              rows = [line.strip().split(",") for line in f]
              print(rows, len(rows))
          """, "[['bug', '2'], ['billing', '1']] 2", ["Each line becomes a list after `strip().split(\",\")`.", "The numbers stay as strings.", "Two lines, so `len(rows)` is 2."]),
          code("Write `read_counts(f)` that takes a file-like object where each line is `name,count` and returns a dict mapping each name to its count as an `int`.",
               "def read_counts(f):\n    pass\n", """
              def read_counts(f):
                  counts = {}
                  for line in f:
                      name, n = line.strip().split(",")
                      counts[name] = int(n)
                  return counts
          """, """
              tx("import io", "read_counts(io.StringIO('bug,2\\\\nbilling,1\\\\n'))", {"bug": 2, "billing": 1})
              tx("import io", "read_counts(io.StringIO(''))", {})
          """, ["Loop over `f` one line at a time.", "`line.strip().split(\",\")` gives the two parts; convert the second with `int`.", "Store `counts[name] = int(n)` and return the dict."], diff=2, tags=["interview"]),
          fill("Complete the code that writes a line to a file.", "with ____(\"notes.txt\", \"w\") as f:\n    f.____(\"hello\\n\")", ["open", "write"], ["Which built-in opens files?", "The file object has a method that puts text into the file.", "`open` and `write`."], lang="python"),
      ], phases=["data"], minutes=4),

    C("py.classes", 2, "Classes",
      "A class bundles data with the functions that work on it. Each object made from the class carries its own copy of that data.",
      [
          CODE("""
              class Ticket:
                  def __init__(self, id, title, priority=1):
                      self.id = id
                      self.title = title
                      self.priority = priority

                  def is_urgent(self):
                      return self.priority >= 3

                  def __repr__(self):
                      return f"Ticket({self.id}, {self.title!r})"

              t = Ticket(7, "Login bug", priority=3)
              print(t.is_urgent(), t)    # True Ticket(7, 'Login bug')
          """),
          UL("`__init__` runs when you create an object. It sets up the data.", "`self` is the object the method was called on. Every method takes it as the first parameter.", "`__repr__` controls how the object prints."),
          VIZ("trace", title="Two objects, separate data", **make_trace("""
              class Counter:
                  def __init__(self):
                      self.n = 0
                  def hit(self):
                      self.n += 1

              a = Counter()
              b = Counter()
              a.hit()
              a.hit()
              print(a.n, b.n)
          """)),
          QUICK("What is `self` inside a method?", ["The class itself", "The specific object the method was called on", "A reserved word that does nothing", "The parent class"], 1, "`a.hit()` is the same as `Counter.hit(a)`, so `self` is `a`."),
      ],
      [
          predict("What does this print?", """
              class Counter:
                  def __init__(self):
                      self.n = 0
                  def hit(self):
                      self.n += 1
                      return self

              c = Counter()
              c.hit().hit()
              d = Counter()
              print(c.n, d.n)
          """, "2 0", ["Each object has its own `n`.", "`hit` returns `self`, so calls can be chained.", "`c` was hit twice, `d` never."], diff=2),
          code("Write a class `Ticket` with `__init__(self, id, title, priority=1)`, a method `is_urgent()` that is true when priority is 3 or more, and a `__repr__` that gives `Ticket(7, 'Login bug')`.",
               "class Ticket:\n    pass\n", """
              class Ticket:
                  def __init__(self, id, title, priority=1):
                      self.id = id
                      self.title = title
                      self.priority = priority

                  def is_urgent(self):
                      return self.priority >= 3

                  def __repr__(self):
                      return f"Ticket({self.id}, {self.title!r})"
          """, """
              t("Ticket(1, 'x').priority", 1)
              t("Ticket(1, 'x', priority=3).is_urgent()", True)
              t("Ticket(1, 'x', 2).is_urgent()", False)
              t("repr(Ticket(7, 'Login bug'))", "Ticket(7, 'Login bug')")
          """, ["Store each argument on `self` inside `__init__`.", "`is_urgent` just compares `self.priority` to 3.", "In `__repr__` use `{self.title!r}` to get the quotes."], diff=3, tags=["interview"]),
          spot("This class should count hits, but calling `c.hit()` crashes. Which line has the bug?", ["class Counter:", "    def __init__(self):", "        self.n = 0", "    def hit():", "        self.n += 1"], 4,
               ["Look at the parameter lists of the methods.", "`c.hit()` passes the object automatically as the first argument.", "Line 4 does not accept it."], lang="python",
               fix=FIX("What is the fix?", ["Write `def hit(self):`", "Write `def hit(c):` and call `hit(c)`", "Remove `self.` from line 5", "Move `hit` outside the class"], 0)),
      ], phases=["data", "serving"], minutes=5),

    C("py.modules", 2, "Imports and the standard library",
      "Python ships with batteries. Knowing a handful of standard modules saves you hours.",
      [
          CODE("""
              import math
              from collections import Counter, defaultdict
              import itertools

              Counter("banana").most_common(1)     # [('a', 3)]
              groups = defaultdict(list)
              groups["b"].append("bug")            # no KeyError, starts as []
              list(itertools.chain([1, 2], [3]))   # [1, 2, 3]
              math.sqrt(16)                        # 4.0
          """),
          P("Your own files are modules too. Code at the top level of a file runs when the file is imported. Guard script-only code like this:"),
          CODE("""
              def main():
                  print("running")

              if __name__ == "__main__":   # True only when run directly
                  main()
          """),
          TABLE(["Module", "Good for"], [["`collections`", "Counter, defaultdict, deque"], ["`itertools`", "chain, groupby, product, combinations"], ["`json`", "read and write JSON"], ["`pathlib`", "file paths"], ["`datetime`", "dates and times"], ["`random`, `statistics`", "sampling, mean, stdev"]]),
          QUICK("Why wrap script code in `if __name__ == \"__main__\":`?", ["It makes the code faster", "It stops the code running when the file is imported", "It is required for functions", "It enables type checking"], 1, "When imported, `__name__` is the module's name, not `\"__main__\"`."),
      ],
      [
          code("Write `top_words(text, n)` that returns the `n` most common words (lower case, split on spaces) as `(word, count)` pairs. Use `collections.Counter`.",
               "from collections import Counter\n\ndef top_words(text, n):\n    pass\n", """
              from collections import Counter

              def top_words(text, n):
                  return Counter(text.lower().split()).most_common(n)
          """, """
              t("top_words('a b a c a b', 2)", [("a", 3), ("b", 2)])
              t("top_words('X x', 1)", [("x", 2)])
              t("top_words('q', 3)", [("q", 1)])
          """, ["`Counter` counts any iterable of hashable items.", "`.most_common(n)` returns the top `n` as pairs.", "`Counter(text.lower().split()).most_common(n)`"], diff=2, tags=["interview"]),
          code("Write `group_by_first_letter(words)` returning a dict from first letter to the list of words that start with it (keep input order). Use `defaultdict`.",
               "from collections import defaultdict\n\ndef group_by_first_letter(words):\n    pass\n", """
              from collections import defaultdict

              def group_by_first_letter(words):
                  groups = defaultdict(list)
                  for w in words:
                      groups[w[0]].append(w)
                  return dict(groups)
          """, """
              t("group_by_first_letter(['bug', 'billing', 'feature'])", {"b": ["bug", "billing"], "f": ["feature"]})
              t("group_by_first_letter([])", {})
          """, ["`defaultdict(list)` creates an empty list for missing keys.", "The key is the first character, `w[0]`.", "Return `dict(groups)` so the result is a plain dict."], diff=2),
          predict("What does this print?", """
              def main():
                  print("running")

              if __name__ == "__main__":
                  main()
              print(__name__)
          """, "running\n__main__", ["The file is being run directly.", "So `__name__` equals the string `\"__main__\"`.", "`main()` runs first, then the last `print`."]),
      ], phases=["data", "serving"], minutes=4),

    C("py.mutable", 2, "Mutability and aliasing",
      "Assignment never copies. Two names can point at the same list, and changing one changes what the other sees.",
      [
          P("Step through this and watch the coloured badge: the same colour means the same object in memory."),
          VIZ("trace", title="Two names, one list", **make_trace("""
              a = [1, 2]
              b = a
              b.append(3)
              c = a.copy()
              c.append(4)
              print(a, b, c)
          """)),
          UL("**Mutable**: list, dict, set. They change in place.", "**Immutable**: int, float, str, tuple. Operations create new objects.", "`b = a.copy()` or `list(a)` makes a shallow copy. For nested data use `copy.deepcopy(a)`."),
          WARN("Never use a mutable default argument like `def f(x, items=[])`. The list is created **once** and shared by every call. Use `items=None` and create the list inside."),
          CODE("""
              def add_tag(tag, tags=None):
                  if tags is None:
                      tags = []
                  tags.append(tag)
                  return tags
          """),
          QUICK("`a = [1]`, `b = a`, `b.append(2)`. What is `a`?", ["[1]", "[1, 2]", "[2]", "An error"], 1, "`b` and `a` are two names for the same list."),
      ],
      [
          predict("What does this print?", """
              a = [1, 2]
              b = a
              b.append(3)
              c = a.copy()
              c.append(4)
              print(a, b, c)
          """, "[1, 2, 3] [1, 2, 3] [1, 2, 3, 4]", ["`b = a` does not copy.", "`a.copy()` makes a new list.", "`a` and `b` are the same object; `c` is separate."],
                  trace=steps_of("a = [1, 2]\nb = a\nb.append(3)\nc = a.copy()\nc.append(4)\nprint(a, b, c)"), diff=2),
          predict("What does this print?", """
              def add_tag(tag, tags=[]):
                  tags.append(tag)
                  return tags

              print(add_tag("a"))
              print(add_tag("b"))
          """, "['a']\n['a', 'b']", ["The default `[]` is created once, when the function is defined.", "Every call without `tags` uses that same list.", "The second call sees the `'a'` from the first."], diff=3, tags=["interview"],
                  explain=EXPLAIN("In your own words: why does the second call contain `'a'`?",
                                  ["The default list is created once at definition time", "Both calls share and mutate the same list object"],
                                  "Default values are evaluated when `def` runs, not at each call. So both calls get the very same list. The first call appended `'a'`, and the second call appends to that same list.")),
          code("Fix it: write `add_tag(tag, tags=None)` so that each call without `tags` starts with a fresh list, and a list you pass in is extended and returned.",
               "def add_tag(tag, tags=[]):\n    tags.append(tag)\n    return tags\n", """
              def add_tag(tag, tags=None):
                  if tags is None:
                      tags = []
                  tags.append(tag)
                  return tags
          """, """
              t("add_tag('a')", ["a"])
              t("add_tag('b')", ["b"])
              tx("x = [1]", "add_tag(2, x)", [1, 2])
              tx("y = [1]\\nadd_tag(2, y)", "y", [1, 2])
          """, ["The default value must not be a list.", "Use `None` as the default and check for it.", "`if tags is None: tags = []` before appending."], diff=3, tags=["interview"]),
      ], phases=["data"], minutes=5),

    C("py.args", 2, "Scope, closures and *args",
      "Where a name lives decides where you can use it. Functions can also accept any number of arguments and remember values from where they were made.",
      [
          P("Python looks up a name in this order: **L**ocal, **E**nclosing function, **G**lobal, **B**uilt-in (LEGB)."),
          CODE("""
              x = "global"
              def f():
                  x = "local"       # a new local variable
                  return x
              print(f(), x)         # local global

              def total(*nums):          # nums is a tuple
                  return sum(nums)
              def describe(**info):      # info is a dict
                  return info
              total(1, 2, 3)              # 6
              describe(a=1, b=2)          # {'a': 1, 'b': 2}
          """),
          P("A **closure** is an inner function that remembers variables from the function that created it."),
          VIZ("trace", title="A counter that remembers", **make_trace("""
              def make_counter():
                  count = 0
                  def inc():
                      nonlocal count
                      count += 1
                      return count
                  return inc

              c = make_counter()
              print(c(), c(), c())
          """)),
          WARN("Assigning inside a function creates a local. To change an outer function's variable use `nonlocal`; to change a global use `global` (and usually avoid it)."),
          QUICK("What type is `nums` inside `def f(*nums):`?", ["list", "tuple", "dict", "set"], 1, "`*args` collects extra positional arguments into a tuple."),
      ],
      [
          predict("What does this print?", """
              x = "global"

              def f():
                  x = "local"
                  return x

              print(f(), x)
          """, "local global", ["Assignment inside a function makes a new local name.", "The global `x` is untouched.", "`f()` returns the local value."]),
          code("Write `total(*nums)` that sums any number of arguments, and `describe(**info)` that returns the keyword arguments as a string like `a=1, b=2` (sorted by key, joined with `, `).",
               "def total(*nums):\n    pass\n\ndef describe(**info):\n    pass\n", """
              def total(*nums):
                  return sum(nums)

              def describe(**info):
                  return ", ".join(f"{k}={v}" for k, v in sorted(info.items()))
          """, """
              t("total(1, 2, 3)", 6)
              t("total()", 0)
              t("describe(b=2, a=1)", "a=1, b=2")
              t("describe()", "")
          """, ["`*nums` gives you a tuple, `**info` gives you a dict.", "`sorted(info.items())` orders the pairs by key.", "`\", \".join(f\"{k}={v}\" for k, v in sorted(info.items()))`"], diff=3),
          predict("What does this print?", """
              def make_counter():
                  count = 0
                  def inc():
                      nonlocal count
                      count += 1
                      return count
                  return inc

              c = make_counter()
              print(c(), c(), c())
          """, "1 2 3", ["`inc` remembers `count` from `make_counter`.", "`nonlocal` lets it change that variable.", "Each call adds 1."],
                  trace=steps_of("def make_counter():\n    count = 0\n    def inc():\n        nonlocal count\n        count += 1\n        return count\n    return inc\n\nc = make_counter()\nprint(c(), c(), c())"), diff=3),
      ], phases=["data", "serving"], minutes=5),
]
