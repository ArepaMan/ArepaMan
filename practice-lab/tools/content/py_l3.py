from dsl import *
from tracegen import make_trace

TRACK = "python"


def steps_of(src):
    return {"steps": make_trace(src)["steps"]}


CONCEPTS = [
    C("py.typing", 3, "Type hints and dataclasses",
      "Type hints document what a function expects and returns. Tools like mypy and your editor use them to catch mistakes before you run the code.",
      [
          CODE("""
              from dataclasses import dataclass

              def double(x: int) -> int:
                  return x * 2

              def first(xs: list[str]) -> str | None:   # may return nothing
                  return xs[0] if xs else None

              @dataclass
              class Ticket:
                  id: int
                  title: str
                  priority: int = 1
          """),
          WARN("Python does **not** enforce hints when the code runs. `double(\"ab\")` happily returns `\"abab\"`. A checker such as mypy or pyright reads the hints separately."),
          UL("`list[int]`, `dict[str, float]`, `tuple[int, str]` describe containers.", "`X | None` (or `Optional[X]`) means the value might be missing.", "`@dataclass` writes `__init__`, `__repr__` and `==` for you from the annotated fields."),
          TIP("Hints are most useful at function boundaries. FastAPI and Pydantic go one step further and use them to validate real data."),
          QUICK("Which hint says a function returns either a string or nothing?", ["`-> str`", "`-> str | None`", "`-> list[str]`", "`-> None`"], 1, "`str | None` allows both."),
      ],
      [
          predict("What does this print?", """
              def double(x: int) -> int:
                  return x * 2

              print(double("ab"))
          """, "abab", ["Does Python check the `int` annotation when the code runs?", "No. It just multiplies.", "A string times 2 repeats the string."], diff=2, tags=["interview"],
                  explain=EXPLAIN("In your own words: why does this run without an error even though we passed a string?",
                                  ["Type hints are not enforced at runtime", "`*` also works on strings, repeating them"],
                                  "Annotations are only metadata. Python never checks them while running, so `double(\"ab\")` just evaluates `\"ab\" * 2`. A separate tool such as mypy would flag the call.")),
          code("Write a dataclass `Ticket` with fields `id: int`, `title: str` and `priority: int = 1`.",
               "from dataclasses import dataclass\n\n@dataclass\nclass Ticket:\n    pass\n", """
              from dataclasses import dataclass

              @dataclass
              class Ticket:
                  id: int
                  title: str
                  priority: int = 1
          """, """
              t("Ticket(1, 'x').priority", 1)
              t("Ticket(1, 'x') == Ticket(1, 'x')", True)
              t("Ticket(1, 'x') == Ticket(2, 'x')", False)
              t("repr(Ticket(7, 'Login bug', 3))", "Ticket(id=7, title='Login bug', priority=3)")
          """, ["List each field with a type annotation.", "Fields with defaults go last.", "`id: int`, `title: str`, `priority: int = 1`"]),
          spot("This function promises to return an `int`, but a type checker complains. Which line?", ["def first(xs: list[int]) -> int:", "    if not xs:", "        return None", "    return xs[0]"], 1,
               ["Think about the empty-list case.", "What does line 3 return?", "The hint on line 1 does not allow `None`."], lang="python",
               fix=FIX("What is the correct fix?", ["Change the hint to `-> int | None`", "Change `xs` to `list`", "Remove the `if`", "Return `0` and keep the hint as it is"], 0,
                       whys=[None, "That does not address returning `None`.", "Then an empty list would raise `IndexError`.", "That would silently invent a value; the honest hint is better."])),
      ], phases=["data", "serving"], minutes=4),

    C("py.gens", 3, "Iterators and generators",
      "A generator produces values one at a time, only when asked. That keeps memory flat for huge data and lets you build pipelines.",
      [
          CODE("""
              def count_up(n):
                  i = 1
                  while i <= n:
                      yield i       # pause here and hand back i
                      i += 1

              g = count_up(3)
              next(g)               # 1
              next(g)               # 2
              list(g)               # [3]  (it remembers where it was)

              total = sum(x * x for x in range(1_000_000))   # no giant list built
          """),
          VIZ("trace", title="A generator pausing and resuming", **make_trace("""
              def count_up(n):
                  i = 1
                  while i <= n:
                      yield i
                      i += 1

              g = count_up(2)
              print(next(g))
              print(next(g))
          """)),
          UL("`yield` pauses the function and remembers its place; `return` ends it.", "A generator can be used **once**. After it runs out it is empty.", "A generator expression `(x*x for x in xs)` is the lazy version of a list comprehension."),
          WARN("`len(g)` and `g[0]` do not work on generators. Convert with `list(g)` if you really need them, but then you lose the memory benefit."),
          QUICK("What does `sum(x for x in range(4))` equal?", ["6", "10", "4", "A generator object"], 0, "0 + 1 + 2 + 3. `sum` consumes the generator."),
      ],
      [
          predict("What does this print?", """
              def count_up(n):
                  i = 1
                  while i <= n:
                      yield i
                      i += 1

              g = count_up(3)
              print(next(g), next(g))
              print(list(g))
          """, "1 2\n[3]", ["Each `next` resumes after the last `yield`.", "After two values, one is left.", "`list(g)` collects what remains."], diff=2),
          code("Write a generator `chunks(items, size)` that yields consecutive lists of at most `size` items.",
               "def chunks(items, size):\n    pass\n", """
              def chunks(items, size):
                  for i in range(0, len(items), size):
                      yield items[i:i + size]
          """, """
              t("list(chunks([1, 2, 3, 4, 5], 2))", [[1, 2], [3, 4], [5]])
              t("list(chunks([], 3))", [])
              t("list(chunks([1, 2], 5))", [[1, 2]])
          """, ["Step through the list in jumps of `size`.", "`range(0, len(items), size)` gives the start of each chunk.", "`yield items[i:i + size]`"], diff=2, tags=["interview"]),
          code("Write a generator `running_total(nums)` that yields the total so far after each number.",
               "def running_total(nums):\n    pass\n", """
              def running_total(nums):
                  total = 0
                  for n in nums:
                      total += n
                      yield total
          """, """
              t("list(running_total([1, 2, 3, 4]))", [1, 3, 6, 10])
              t("list(running_total([]))", [])
              t("list(running_total([5, -5]))", [5, 0])
          """, ["Keep a running variable outside the loop.", "Yield after adding each number.", "`total += n` then `yield total`."], diff=2),
      ], phases=["data", "deep"], minutes=4),

    C("py.decor", 3, "Decorators and higher-order functions",
      "Functions are values. A decorator is a function that takes a function and returns an improved one.",
      [
          CODE("""
              def shout(fn):
                  def wrapper(*args, **kwargs):
                      return fn(*args, **kwargs).upper() + "!"
                  return wrapper

              @shout                 # same as: greet = shout(greet)
              def greet(name):
                  return "hi " + name

              print(greet("ana"))    # HI ANA!
          """),
          P("Because `@shout` just means `greet = shout(greet)`, a decorator is plain Python: a closure that remembers `fn` and wraps the call."),
          CODE("""
              from functools import wraps, lru_cache

              def logged(fn):
                  @wraps(fn)                       # keep fn's name and docstring
                  def wrapper(*a, **k):
                      print("calling", fn.__name__)
                      return fn(*a, **k)
                  return wrapper

              @lru_cache(maxsize=None)             # a ready-made decorator: remembers results
              def slow_square(n): return n * n
          """),
          TIP("In real projects you meet decorators constantly: `@app.get(\"/\")` in FastAPI, `@pytest.fixture`, `@property`, `@dataclass`."),
          QUICK("`@deco` placed above `def f():` is the same as:", ["`f = deco`", "`f = deco(f)`", "`deco = f(deco)`", "`f()` then `deco()`"], 1, "The decorator is called with the function and its return value replaces the name."),
      ],
      [
          predict("What does this print?", """
              def shout(fn):
                  def wrapper(*args):
                      return fn(*args).upper() + "!"
                  return wrapper

              @shout
              def greet(name):
                  return "hi " + name

              print(greet("ana"))
          """, "HI ANA!", ["`@shout` replaces `greet` with `wrapper`.", "`wrapper` calls the original, then changes the result.", "Upper-case first, then add `!`."], diff=2),
          code("Write a decorator `count_calls` that counts how often the decorated function runs. Store the count on the wrapper as `wrapper.calls` (starting at 0) and still return the original result.",
               "def count_calls(fn):\n    pass\n", """
              def count_calls(fn):
                  def wrapper(*args, **kwargs):
                      wrapper.calls += 1
                      return fn(*args, **kwargs)
                  wrapper.calls = 0
                  return wrapper
          """, """
              tx("@count_calls\\ndef f(x):\\n    return x + 1", "f.calls", 0)
              tx("@count_calls\\ndef g(x):\\n    return x + 1\\ng(1)\\ng(2)\\ng(3)", "g.calls", 3)
              tx("@count_calls\\ndef h(x):\\n    return x * 10", "h(4)", 40)
          """, ["The decorator returns a new function (`wrapper`).", "Functions can have attributes: `wrapper.calls = 0`.", "Increment inside `wrapper`, then `return fn(*args, **kwargs)`."], diff=3, tags=["interview"]),
          mcq("A decorator was written without `functools.wraps`. What is the visible side effect?", ["It runs twice as slowly", "The decorated function loses its original `__name__` and docstring", "It can no longer take arguments", "Nothing, `wraps` is optional decoration"], 1,
              ["Think about what `greet.__name__` shows.", "The returned function is a different object called `wrapper`.", "`@wraps(fn)` copies the metadata across."], diff=2),
      ], phases=["serving"], minutes=5),

    C("py.oop", 3, "Inheritance, dunder methods and properties",
      "Subclasses reuse and specialise a parent. Dunder methods like `__add__` let your objects behave like built-ins.",
      [
          CODE("""
              class Classifier:
                  def predict(self, text):
                      raise NotImplementedError

                  def predict_all(self, texts):
                      return [self.predict(t) for t in texts]   # uses the subclass's predict

              class KeywordClassifier(Classifier):
                  def predict(self, text):
                      return "bug" if "error" in text.lower() else "other"
          """),
          UL("A subclass inherits everything and can **override** methods.", "`super().__init__(...)` runs the parent's setup.", "`__add__`, `__eq__`, `__len__`, `__repr__` hook your class into `+`, `==`, `len()` and printing."),
          CODE("""
              class Box:
                  def __init__(self, w, h):
                      self.w, self.h = w, h

                  @property
                  def area(self):          # used like an attribute: box.area
                      return self.w * self.h
          """),
          TIP("Prefer **composition** (an object holds another object) over deep inheritance trees. Inherit when the child really *is a* kind of the parent."),
          QUICK("A `@property` is accessed as:", ["`box.area()`", "`box.area`", "`box[area]`", "`area(box)`"], 1, "A property looks like a plain attribute but runs code."),
      ],
      [
          code("Write a base class `Classifier` with `predict_all(texts)` returning `[self.predict(t) for t in texts]`, and a subclass `KeywordClassifier` whose `predict(text)` returns `\"bug\"` if the word `error` appears in the text (any case), otherwise `\"other\"`.",
               "class Classifier:\n    def predict(self, text):\n        raise NotImplementedError\n\nclass KeywordClassifier(Classifier):\n    pass\n", """
              class Classifier:
                  def predict(self, text):
                      raise NotImplementedError

                  def predict_all(self, texts):
                      return [self.predict(t) for t in texts]

              class KeywordClassifier(Classifier):
                  def predict(self, text):
                      return "bug" if "error" in text.lower() else "other"
          """, """
              t("KeywordClassifier().predict('Got an ERROR 500')", "bug")
              t("KeywordClassifier().predict('please refund')", "other")
              t("KeywordClassifier().predict_all(['error!', 'hello'])", ["bug", "other"])
              texc("Classifier().predict('x')", NotImplementedError)
          """, ["`predict_all` belongs on the base class and calls `self.predict`.", "Override `predict` in the subclass.", "Use `text.lower()` so the match ignores case."], diff=3, tags=["interview"]),
          code("Write a class `Vec` with `x` and `y`, an `__add__` that returns a new `Vec`, an `__eq__` that compares both coordinates, and a `__repr__` like `Vec(1, 2)`.",
               "class Vec:\n    pass\n", """
              class Vec:
                  def __init__(self, x, y):
                      self.x = x
                      self.y = y

                  def __add__(self, other):
                      return Vec(self.x + other.x, self.y + other.y)

                  def __eq__(self, other):
                      return self.x == other.x and self.y == other.y

                  def __repr__(self):
                      return f"Vec({self.x}, {self.y})"
          """, """
              t("repr(Vec(1, 2) + Vec(3, 4))", "Vec(4, 6)")
              t("Vec(1, 2) == Vec(1, 2)", True)
              t("Vec(1, 2) == Vec(2, 1)", False)
              t("repr(Vec(0, 0))", "Vec(0, 0)")
          """, ["Each special method has a fixed name with double underscores.", "`__add__` should create and return a **new** `Vec`.", "`__eq__` compares `x` with `x` and `y` with `y`."], diff=3),
          predict("What does this print?", """
              class Box:
                  def __init__(self, w, h):
                      self.w, self.h = w, h

                  @property
                  def area(self):
                      return self.w * self.h

              b = Box(2, 3)
              b.w = 5
              print(b.area)
          """, "15", ["`area` is computed each time it is read.", "`b.w` was changed to 5 before the read.", "5 times 3."], diff=2),
      ], phases=["deep", "serving"], minutes=5),

    C("py.pytest", 3, "Testing with pytest",
      "A test is a function that fails loudly when behaviour is wrong. Good tests catch bugs; the exercise below measures exactly that.",
      [
          CODE("""
              # test_utils.py
              import pytest
              from utils import parse_priority

              def test_valid():
                  assert parse_priority("2") == 2

              def test_rejects_bad_value():
                  with pytest.raises(ValueError):
                      parse_priority("9")

              @pytest.mark.parametrize("text, expected", [("1", 1), ("3", 3)])
              def test_many(text, expected):
                  assert parse_priority(text) == expected
          """),
          UL("pytest finds files named `test_*.py` and functions named `test_*`.", "A plain `assert` is enough. On failure pytest shows both sides.", "`parametrize` runs one test with many inputs. `@pytest.fixture` shares setup between tests."),
          WARN("`assert (x == 1, \"message\")` with brackets asserts a **tuple**, which is always true, so the test can never fail. Write `assert x == 1, \"message\"`."),
          P("The best test also fails when the code is wrong. That is how you judge a test suite, and it is the idea behind the first exercise."),
          QUICK("What makes a pytest function a test?", ["It ends with `_test`", "It is named `test_...` in a file named `test_*.py`", "It uses `unittest`", "It returns True"], 1, "That is pytest's discovery rule."),
      ],
      [
          code("Write test functions (names starting with `test_`) for `is_palindrome(s)`, which ignores case and punctuation: `\"A man, a plan, a canal: Panama\"` is a palindrome. The checker runs **your tests** against one correct and three buggy implementations. Your tests must pass on the correct one and fail on every buggy one.",
               "# is_palindrome is provided for you when your tests run.\n\ndef test_simple():\n    assert is_palindrome(\"level\")\n", """
              def test_simple():
                  assert is_palindrome("level")
                  assert not is_palindrome("hello")

              def test_case_and_punctuation():
                  assert is_palindrome("A man, a plan, a canal: Panama")

              def test_empty_and_single():
                  assert is_palindrome("")
                  assert is_palindrome("x")

              def test_near_miss():
                  assert not is_palindrome("abca")
          """, """
              def correct(s):
                  s = "".join(c.lower() for c in s if c.isalnum())
                  return s == s[::-1]

              def bug_case(s):          # forgets to ignore case and punctuation
                  return s == s[::-1]

              def bug_always_true(s):
                  return True

              def bug_only_first_half(s):   # only compares the first and last letters
                  s = "".join(c.lower() for c in s if c.isalnum())
                  return len(s) == 0 or s[0] == s[-1]

              def passes(impl):
                  g = globals()
                  g["is_palindrome"] = impl
                  names = [n for n in list(g) if n.startswith("test_")]
                  try:
                      for n in names:
                          g[n]()
                      return True
                  except BaseException:
                      return False

              check("at least one test function exists", len([n for n in list(globals()) if n.startswith("test_")]) >= 1, True)
              check("passes on the correct implementation", passes(correct), True)
              check("fails when case and punctuation are ignored wrongly", not passes(bug_case), True)
              check("fails when the function always says True", not passes(bug_always_true), True)
              check("fails when only first and last letters are compared", not passes(bug_only_first_half), True)
          """, ["You need at least one palindrome and one non-palindrome.", "Add a case with capitals and punctuation, and one that matches at the ends but not in the middle.", "Try `\"abca\"`: first and last letters match but it is not a palindrome."], diff=3, tags=["interview"],
               explain=EXPLAIN("In your own words: how do you know a test suite is good?",
                               ["It passes on correct code", "It fails when the code is wrong (it catches bugs)", "It covers edge cases such as empty input"],
                               "A good suite passes when the code is right and fails when the code is wrong. You show that by checking edge cases and near misses, not only the happy path.")),
          fill("Complete the test so it checks that a `ValueError` is raised.", "import pytest\n\ndef test_bad_priority():\n    with pytest.____(ValueError):\n        parse_priority(\"9\")\n    assert parse_priority(\"2\") ____ 2", ["raises", "=="], ["The context manager is named after what you expect.", "A test compares values with `==` inside an `assert`.", "`pytest.raises` and `==`."], lang="python"),
          spot("This test can never fail. Which line is the problem?", ["def test_total():", "    total = 2 + 2", "    assert (total == 5, \"math is broken\")"], 3,
               ["Look at the brackets on the last line.", "What type is `(a, b)`?", "A non-empty tuple is always truthy."], lang="python",
               fix=FIX("What is the fix?", ["`assert total == 5, \"math is broken\"`", "`assert (total == 5) and \"math is broken\"` with extra brackets", "`assert total, \"math is broken\"`", "Remove the `assert`"], 0), tags=["interview"]),
      ], phases=["serving"], minutes=6),

    C("py.context", 3, "Context managers",
      "`with` guarantees that cleanup runs, even when the code inside fails. You can build your own in a few lines.",
      [
          CODE("""
              from contextlib import contextmanager

              @contextmanager
              def opened(log, name):
                  log.append("open " + name)
                  try:
                      yield name              # the body of `with` runs here
                  finally:
                      log.append("close " + name)   # always runs

              log = []
              with opened(log, "db") as handle:
                  log.append("use " + handle)
              print(log)   # ['open db', 'use db', 'close db']
          """),
          P("Under the hood `with` calls `__enter__` on the way in and `__exit__` on the way out, even if an exception happens. Files, locks, database transactions and `torch.no_grad()` are all context managers."),
          WARN("The code after `yield` only runs reliably if it is inside `finally`. Without it an exception skips your cleanup."),
          QUICK("Why is `torch.no_grad()` written as a `with` block?", ["So it also runs faster on CPU", "So gradient tracking is switched back on automatically afterwards", "Because it needs two files", "It is not a context manager"], 1, "The `with` block restores the previous state on exit."),
      ],
      [
          predict("What does this print?", """
              class Tracker:
                  def __enter__(self):
                      print("enter")
                      return self
                  def __exit__(self, exc_type, exc, tb):
                      print("exit")

              with Tracker():
                  print("inside")
              print("after")
          """, "enter\ninside\nexit\nafter", ["`__enter__` runs when the block starts.", "`__exit__` runs when it ends.", "The statement after the block runs last."]),
          code("Write a context manager `opened(log, name)` using `@contextmanager`. It appends `\"open NAME\"` to `log` on entry, yields `name`, and appends `\"close NAME\"` on exit, even if the body raises.",
               "from contextlib import contextmanager\n\n@contextmanager\ndef opened(log, name):\n    pass\n", """
              from contextlib import contextmanager

              @contextmanager
              def opened(log, name):
                  log.append("open " + name)
                  try:
                      yield name
                  finally:
                      log.append("close " + name)
          """, """
              tx("log = []\\nwith opened(log, 'a') as x:\\n    log.append('use ' + x)", "log", ["open a", "use a", "close a"])
              tx("log2 = []\\ntry:\\n    with opened(log2, 'b'):\\n        raise ValueError('boom')\\nexcept ValueError:\\n    pass", "log2", ["open b", "close b"])
          """, ["A `@contextmanager` function has one `yield`.", "Code before `yield` is setup, code after is cleanup.", "Put the cleanup in `finally` so it runs on errors too."], diff=3),
          mcq("What is the main benefit of using `with open(path) as f:` over `f = open(path)`?", ["The file reads faster", "The file is closed when the block ends, even after an error", "You can read the file twice", "It makes `f` read-only"], 1,
              ["Think about what happens if an error occurs halfway through.", "Resources must be released.", "`with` runs the cleanup in all cases."]),
      ], phases=["deep", "serving"], minutes=4),

    C("py.algo", 3, "Complexity and choosing data structures",
      "Interviewers (and your users) care how code scales. The right data structure often turns a slow solution into a fast one.",
      [
          TABLE(["Operation", "list", "set / dict"], [["`x in container`", "O(n) scans everything", "O(1) on average"], ["append / add", "O(1)", "O(1)"], ["insert at front", "O(n)", "n/a"], ["sort", "O(n log n)", "n/a"]]),
          P("O(n²) means doubling the data makes the work four times bigger. Two nested loops over the same list is the usual culprit."),
          CODE("""
              # O(n^2): compares every pair
              def has_dup_slow(xs):
                  for i in range(len(xs)):
                      for j in range(i + 1, len(xs)):
                          if xs[i] == xs[j]:
                              return True
                  return False

              # O(n): remember what you have seen
              def has_dup(xs):
                  seen = set()
                  for x in xs:
                      if x in seen:
                          return True
                      seen.add(x)
                  return False
          """),
          TIP("When a loop contains `x in some_list`, ask whether `some_list` should be a `set` or `dict`."),
          WARN("The practice runner stops code after about a million loop steps. If your solution is cut off with a timeout message, it is probably the slow O(n²) one."),
          QUICK("Which membership test is fastest on a million items?", ["`x in my_list`", "`x in my_set`", "`my_list.count(x) > 0`", "`any(x == y for y in my_list)`"], 1, "A set uses hashing: about one step regardless of size."),
      ],
      [
          code("Write `has_duplicates(items)` that returns True if any value appears twice. It must handle 20,000 items quickly (so avoid comparing every pair).",
               "def has_duplicates(items):\n    pass\n", """
              def has_duplicates(items):
                  seen = set()
                  for x in items:
                      if x in seen:
                          return True
                      seen.add(x)
                  return False
          """, """
              t("has_duplicates([1, 2, 3, 1])", True)
              t("has_duplicates([])", False)
              t("has_duplicates(list(range(20000)))", False)
              t("has_duplicates(list(range(20000)) + [5])", True)
          """, ["Comparing every pair is O(n squared).", "A set remembers what you have seen in O(1) per check.", "Return True as soon as an item is already in the set."], diff=2, tags=["interview"]),
          code("Write `two_sum(nums, target)` returning the indexes `[i, j]` (with `i < j`) of two numbers that add up to `target`, or `None` if there are none. It must handle 20,000 numbers.",
               "def two_sum(nums, target):\n    pass\n", """
              def two_sum(nums, target):
                  seen = {}
                  for j, n in enumerate(nums):
                      if target - n in seen:
                          return [seen[target - n], j]
                      seen[n] = j
                  return None
          """, """
              t("two_sum([2, 7, 11, 15], 9)", [0, 1])
              t("two_sum([3, 2, 4], 6)", [1, 2])
              t("two_sum([1, 2], 10)", None)
              t("two_sum(list(range(0, 40000, 2)), 3)", None)
              t("two_sum(list(range(20000)), 39997)", [19998, 19999])
          """, ["For each number, the partner you need is `target - n`.", "Store numbers you have seen in a dict mapping value to index.", "Check the dict **before** adding the current number."], diff=3, tags=["interview"],
               explain=EXPLAIN("In your own words: why is this faster than trying every pair?",
                               ["Each lookup in the dict is O(1)", "The list is scanned only once, so O(n) overall"],
                               "Instead of checking every pair (O(n²)), we scan once and ask the dict whether the needed partner was seen already. Dict lookups are constant time, so the total is O(n).")),
          mcq("You must check membership 10 million times against 1 million fixed words. What should the words be stored in?", ["a list", "a set", "a sorted list with a linear scan", "a string"], 1,
              ["The collection never changes, only lookups matter.", "A list lookup scans, which is O(n).", "A set (or dict) does O(1) lookups."], tags=["interview"]),
      ], phases=["data", "serving"], minutes=5),

    C("py.recursion", 3, "Recursion and memoization",
      "A recursive function solves a problem by calling itself on a smaller version. Memoization remembers answers so work is never repeated.",
      [
          P("Every recursive function needs a **base case** (stops the recursion) and a **recursive case** (a smaller problem). Step through `sum_digits` and watch the call stack grow and shrink."),
          VIZ("trace", title="Recursion and the call stack", **make_trace("""
              def sum_digits(n):
                  if n < 10:
                      return n
                  return n % 10 + sum_digits(n // 10)

              print(sum_digits(123))
          """)),
          CODE("""
              from functools import lru_cache

              @lru_cache(maxsize=None)        # remembers fib(k) once computed
              def fib(n):
                  return n if n < 2 else fib(n - 1) + fib(n - 2)

              fib(80)   # instant. Without the cache this would take years.
          """),
          WARN("Python limits recursion depth to about 1000 calls. Very deep problems should use a loop."),
          QUICK("Without memoization, how does `fib(n)` grow?", ["Linearly", "Exponentially", "Logarithmically", "It does not grow"], 1, "Each call makes two more calls, so the number of calls roughly doubles each step."),
      ],
      [
          predict("What does this print?", """
              def sum_digits(n):
                  if n < 10:
                      return n
                  return n % 10 + sum_digits(n // 10)

              print(sum_digits(1234))
          """, "10", ["The last digit plus the sum of the rest.", "4 + 3 + 2 + 1.", "The base case is a single digit."],
                  trace=steps_of("def sum_digits(n):\n    if n < 10:\n        return n\n    return n % 10 + sum_digits(n // 10)\n\nprint(sum_digits(123))"), diff=2),
          code("Write `fib(n)` (with `fib(0) == 0`, `fib(1) == 1`) that stays fast for `n = 80`. Use memoization.",
               "def fib(n):\n    pass\n", """
              from functools import lru_cache

              @lru_cache(maxsize=None)
              def fib(n):
                  return n if n < 2 else fib(n - 1) + fib(n - 2)
          """, """
              t("fib(0)", 0)
              t("fib(1)", 1)
              t("fib(10)", 55)
              t("fib(80)", 23416728348467685)
          """, ["The plain recursive version recomputes the same values many times.", "Remember results: a dict, or `functools.lru_cache`.", "`@lru_cache(maxsize=None)` above the function does it for you."], diff=3, tags=["interview"]),
          code("Write `flatten(nested)` that turns a list with arbitrarily nested lists into one flat list: `[1, [2, [3, 4]], 5]` becomes `[1, 2, 3, 4, 5]`.",
               "def flatten(nested):\n    pass\n", """
              def flatten(nested):
                  out = []
                  for item in nested:
                      if isinstance(item, list):
                          out.extend(flatten(item))
                      else:
                          out.append(item)
                  return out
          """, """
              t("flatten([1, [2, [3, 4]], 5])", [1, 2, 3, 4, 5])
              t("flatten([])", [])
              t("flatten([[[]]])", [])
              t("flatten([1, 2])", [1, 2])
          """, ["Loop over the items. A list inside needs the same treatment.", "Use `isinstance(item, list)` to tell them apart.", "If it is a list, extend the output with `flatten(item)`; otherwise append it."], diff=3, tags=["interview"]),
      ], phases=["data"], minutes=5),
]
