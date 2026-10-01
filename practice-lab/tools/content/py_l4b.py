from dsl import *

TRACK = "python"

CONCEPTS = [
    C("py.numpy4", 4, "NumPy: norms, sorting and vector similarity",
      "Embeddings are just vectors. Comparing them, normalising them and picking the top matches is a handful of NumPy moves.",
      [
          CODE("""
              import numpy as np
              a = np.array([3, 4])
              np.linalg.norm(a)                 # 5.0   the length of the vector
              np.argsort([30, 10, 20])          # [1 2 0]  positions that would sort the values (smallest first)
              np.argsort([30, 10, 20])[::-1][:2]   # [0 2]  positions of the 2 largest

              u = a / np.linalg.norm(a)         # a unit vector, length 1
              np.dot(u, u)                      # 1.0
              # cosine similarity of x and y = dot(x, y) / (|x| |y|) = dot of their unit vectors
          """),
          UL("`argsort` returns **positions**, not values. Reverse it for \"largest first\" and slice `[:k]` for top-k.", "Normalise vectors once, then similarity is a plain dot product, and a whole matrix of similarities is one `Q @ D.T`.", "Seed randomness (`np.random.default_rng(42)`) so splits, shuffles and weight initialisations repeat exactly."),
          TIP("Top-k with full sorting costs O(n log n). For huge arrays `np.argpartition` finds the top-k faster, and vector databases use approximate indexes instead."),
          QUICK("`np.argsort([30, 10, 20])` returns:", ["`[10 20 30]`", "`[1 2 0]`", "`[0 2 1]`", "`[2 1 0]`"], 1, "Position 1 holds the smallest (10), then position 2 (20), then position 0 (30)."),
      ],
      [
          predict("What does this print?", """
              import numpy as np
              a = np.array([3, 4])
              print(np.linalg.norm(a), np.argsort([30, 10, 20]), np.argsort([30, 10, 20])[::-1][:2])
          """, "5.0 [1 2 0] [0 2]", ["The length of the vector (3, 4) is the hypotenuse of a 3-4-5 triangle.", "`argsort` gives positions that would sort the values ascending.", "Reverse it, then take the first two positions."], diff=3),
          code("Without NumPy: write `top_k(scores, k)` returning the indexes of the `k` largest scores, best first. If two scores tie, the lower index comes first.",
               "def top_k(scores, k):\n    pass\n", """
              def top_k(scores, k):
                  return sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:k]
          """, """
              t("top_k([0.1, 0.9, 0.5], 2)", [1, 2])
              t("top_k([3, 3, 1], 2)", [0, 1])
              t("top_k([5], 3)", [0])
              t("top_k([], 2)", [])
          """, ["Sort the **indexes**, not the values.", "Sort by descending score, then by index to break ties.", "`sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:k]`"], diff=3, tags=["interview"]),
          code("Without NumPy: write `unit(v)` that scales a list of numbers to length 1 (divide each by the vector's length). Return the vector unchanged if its length is 0.",
               "def unit(v):\n    pass\n", """
              def unit(v):
                  n = sum(x * x for x in v) ** 0.5
                  return [x / n for x in v] if n else list(v)
          """, """
              t("unit([3, 4])", [0.6, 0.8])
              t("unit([0, 0])", [0, 0])
              t("[round(x, 6) for x in unit([1, 2, 3])]", [0.267261, 0.534522, 0.801784])
              t("round(sum(x * x for x in unit([5, 12])), 9)", 1.0)
          """, ["The length is the square root of the sum of squares.", "Divide every element by it.", "Guard against dividing by zero."], diff=2),
          mcq("Why do ML code bases set a random seed such as `np.random.default_rng(42)`?", ["It makes random numbers more random", "It makes splits, shuffles and initialisations repeat exactly, so results can be compared and debugged", "It speeds up NumPy", "It is required for `argsort`"], 1,
              ["Think about re-running an experiment next week.", "Without a seed every run draws different numbers.", "Repeatability is the point."], diff=1),
      ], phases=["data", "deep"], minutes=5),

    C("py.pandas3", 4, "Pandas: cleaning text and working with dates",
      "Real ticket data is messy: inconsistent case, stray spaces, duplicates and dates stored as strings. Cleaning it well is half of a baseline.",
      [
          CODE("""
              import pandas as pd
              s = pd.Series(["  Refund ", "refund", "Login BUG"])
              clean = s.str.strip().str.lower()        # vectorised string methods: no loop
              clean.nunique()                           # 2 distinct values
              clean.duplicated().tolist()              # [False, True, False]
              df = df.drop_duplicates(subset="text")    # keep the first of each repeated text

              d = pd.to_datetime(df["created"])         # strings -> real datetimes
              d.dt.dayofweek                            # 0 = Monday
              df.set_index("created").resample("D").size()   # tickets per day (index must be a datetime)
          """),
          UL("The `.str` accessor applies a string method to every element: `.str.contains(\"error\")`, `.str.replace(...)`, `.str.len()`.", "`pd.to_datetime` parses strings. After that `.dt` gives `.year`, `.month`, `.dayofweek`, `.date`.", "`resample` needs a datetime **index**. It groups rows into time buckets (day, week, month) like a GROUP BY on dates.", "Prefer vectorised methods to `.apply(lambda ...)`; they are much faster on big columns."),
          WARN("Always clean text the same way in training and in production (strip, lower, normalise whitespace). A mismatch silently lowers accuracy."),
          QUICK("You want tickets per day from a DataFrame with a `created` datetime column. What do you need before `.resample(\"D\")`?", ["Nothing", "`set_index(\"created\")` so the dates are the index", "`sort_values(\"id\")`", "`dropna()`"], 1, "`resample` works on a datetime index."),
      ],
      [
          predict("What does this print?", """
              import pandas as pd
              s = pd.Series(["  Refund ", "refund", "Login BUG"])
              clean = s.str.strip().str.lower()
              print(clean.tolist(), clean.nunique(), clean.duplicated().tolist())
          """, "['refund', 'refund', 'login bug'] 2 [False, True, False]", ["Cleaning makes the first two values identical.", "`nunique` counts distinct values.", "`duplicated` is True for repeats after the first."], diff=3),
          predict("What does this print? (Monday is 0.)", """
              import pandas as pd
              d = pd.to_datetime(["2026-09-01", "2026-09-03"])
              print((d[1] - d[0]).days, pd.Series(d).dt.dayofweek.tolist())
          """, "2 [1, 3]", ["Subtracting dates gives a timedelta.", "September 1st, 2026 is a Tuesday.", "Tuesday is 1 and Thursday is 3."], diff=3),
          code("Without pandas: write `clean_text(s)` that strips outer spaces, lower-cases and collapses runs of spaces into one. Then `dedupe(texts)` that returns the cleaned texts with duplicates removed, keeping the first occurrence order.",
               "def clean_text(s):\n    pass\n\ndef dedupe(texts):\n    pass\n", """
              def clean_text(s):
                  return " ".join(s.lower().split())

              def dedupe(texts):
                  seen = set()
                  out = []
                  for t in texts:
                      c = clean_text(t)
                      if c not in seen:
                          seen.add(c)
                          out.append(c)
                  return out
          """, """
              t("clean_text('  Refund   REQUEST ')", "refund request")
              t("clean_text('ok')", "ok")
              t("dedupe(['Refund', ' refund ', 'Login  bug', 'REFUND'])", ["refund", "login bug"])
              t("dedupe([])", [])
          """, ["`split()` with no argument also removes extra spaces.", "Join the words back with a single space.", "A set tracks what you have already seen; a list keeps the order."], diff=2, tags=["interview"]),
          spot("This code should count tickets per day but raises `TypeError: Only valid with DatetimeIndex`. Which line is the problem?", ["df = pd.read_csv(\"tickets.csv\")", "df[\"created\"] = pd.to_datetime(df[\"created\"])", "daily = df.resample(\"D\").size()"], 3,
               ["`resample` needs dates as the index.", "The dates are in a column, not the index.", "Set the index first."], lang="python",
               fix=FIX("What is the fix?", ["`daily = df.set_index(\"created\").resample(\"D\").size()`", "`daily = df.resample(\"created\").size()`", "`daily = df.groupby(\"D\").size()`", "Convert `created` back to strings"], 0), diff=3, tags=["interview"]),
      ], phases=["data"], minutes=6),

    C("py.sklearn2", 4, "Model selection: cross-validation, imbalance and macro metrics",
      "One train/test split is a noisy estimate. Cross-validation averages several splits, class weights help rare categories, and macro metrics keep rare classes from hiding.",
      [
          CODE("""
              from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
              from sklearn.linear_model import LogisticRegression

              X_train, X_test, y_train, y_test = train_test_split(
                  X, y, test_size=0.2, stratify=y, random_state=42)   # keep class proportions

              model = LogisticRegression(class_weight="balanced", max_iter=1000)
              cross_val_score(model, X_train, y_train, cv=5, scoring="f1_macro")   # 5 scores, one per fold

              grid = GridSearchCV(model, {"C": [0.1, 1, 10]}, cv=5, scoring="f1_macro")
              grid.fit(X_train, y_train)         # tune on TRAIN only
              grid.score(X_test, y_test)         # the test set is used once, at the very end
          """),
          UL("`stratify=y` keeps the proportion of each class in both splits. Essential when some categories are rare.", "`class_weight=\"balanced\"` makes rare classes count more during training.", "**Macro** F1 averages the per-class F1 equally, so a tiny class matters as much as a huge one. **Micro** pools all predictions and is dominated by big classes.", "Tune with cross-validation on the training data. The test set is touched once."),
          WARN("If you tune hyperparameters by looking at the test set, it is no longer a test set. Your final score is optimistic."),
          QUICK("A ticket category has only 2% of the data. Which setting helps the split keep it in both train and test?", ["`shuffle=False`", "`stratify=y`", "`test_size=0.5`", "`random_state=None`"], 1, "Stratifying preserves class proportions in each split."),
      ],
      [
          code("Without scikit-learn: write `macro_f1(y_true, y_pred)` for any labels. Compute precision, recall and F1 for each class that appears in either list (F1 is 0 when precision plus recall is 0), then return the plain average of the per-class F1 scores.",
               "def macro_f1(y_true, y_pred):\n    pass\n", """
              def macro_f1(y_true, y_pred):
                  classes = sorted(set(y_true) | set(y_pred))
                  scores = []
                  for c in classes:
                      tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
                      fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
                      fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
                      prec = tp / (tp + fp) if tp + fp else 0.0
                      rec = tp / (tp + fn) if tp + fn else 0.0
                      scores.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
                  return sum(scores) / len(scores)
          """, """
              t("round(macro_f1(['bug', 'bill', 'bug', 'feat', 'bill', 'bug'], ['bug', 'bug', 'bug', 'feat', 'bill', 'feat']), 6)", 0.666667)
              t("macro_f1(['a', 'a', 'b', 'b', 'c', 'c'], ['a', 'a', 'b', 'b', 'c', 'c'])", 1.0)
              t("round(macro_f1(['a', 'b', 'c', 'a'], ['b', 'b', 'c', 'a']), 6)", 0.777778)
          """, ["Treat each class as the positive class in turn.", "Per class: tp, fp, fn, then precision, recall, F1.", "Average the F1 values, giving every class equal weight."], diff=3, tags=["interview"]),
          spot("The team reports a surprisingly high final score. Which line is the problem?", ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)", "grid = GridSearchCV(model, {\"C\": [0.1, 1, 10]}, cv=5)", "grid.fit(X_test, y_test)", "print(grid.score(X_test, y_test))"], 3,
               ["Which data is the search allowed to learn from?", "The test set must stay unseen until the end.", "Line 3 tunes on the test data."], lang="python",
               fix=FIX("What is the fix?", ["Fit the search on `X_train, y_train`, and score on the test set once at the end", "Use a bigger test set", "Remove `cv=5`", "Score on the training data instead"], 0), diff=3, tags=["interview"]),
          predict("What does this print?", """
              from sklearn.model_selection import train_test_split
              train, test = train_test_split(list(range(10)), test_size=0.3, random_state=0)
              print(len(train), len(test))
          """, "7 3", ["`test_size=0.3` of 10 items.", "30% is 3 items.", "The rest is training data."], diff=2),
          fill("Make a model pay more attention to rare classes.", "model = LogisticRegression(class_weight=\"____\", max_iter=1000)", ["balanced"], ["There is a ready-made option named after the goal.", "It weights classes inversely to their frequency.", "`balanced`"], lang="python"),
      ], phases=["data"], minutes=6),

    C("py.stats2", 4, "Drift statistics: PSI and alert maths",
      "Models degrade when live data stops looking like training data. A few small statistics turn that worry into a number you can alert on.",
      [
          P("The **Population Stability Index (PSI)** compares how data is spread across bins in two periods. For each bin with share `e` (expected, from training) and `a` (actual, live):"),
          CODE("""
              PSI = sum over bins of (a - e) * ln(a / e)

              PSI < 0.1       stable
              0.1 to 0.25     moderate shift, investigate
              > 0.25          major shift, act
          """, "text"),
          CODE("""
              # shares per bin: training said 50% / 30% / 20%, live traffic shows 30% / 30% / 40%
              expected = [0.5, 0.3, 0.2]
              actual   = [0.3, 0.3, 0.4]
              # PSI ~ 0.24: a meaningful shift
          """),
          UL("Use PSI on a feature (message length, language) or on the model's score distribution.", "A **z-score alert** compares today's value with the recent mean and standard deviation: `abs(x - mean) / std`.", "Track shifts in inputs (data drift) and in the relationship between inputs and labels (concept drift). The first is visible immediately, the second needs labels."),
          QUICK("PSI between training and live data is 0.4. What does that mean?", ["Everything is fine", "A major distribution shift: investigate", "The model is 40% accurate", "The data is mislabeled"], 1, "Above 0.25 is conventionally a major shift."),
      ],
      [
          code("Write `bin_shares(values, edges)` that counts how many values fall in each bin and returns the shares (each count divided by the total). Bins are `[edges[0], edges[1])`, `[edges[1], edges[2])`, ... and the last bin includes its upper edge. Ignore values outside the edges.",
               "def bin_shares(values, edges):\n    pass\n", """
              def bin_shares(values, edges):
                  counts = [0] * (len(edges) - 1)
                  for v in values:
                      for i in range(len(edges) - 1):
                          last = i == len(edges) - 2
                          if edges[i] <= v < edges[i + 1] or (last and v == edges[i + 1]):
                              counts[i] += 1
                              break
                  total = sum(counts)
                  return [c / total for c in counts] if total else counts
          """, """
              t("bin_shares([1, 2, 5, 6, 9, 10], [0, 5, 10])", [1 / 3, 2 / 3])
              t("bin_shares([0, 4, 5, 10, 11, -1], [0, 5, 10])", [0.5, 0.5])
              t("bin_shares([1, 2, 3], [0, 10])", [1.0])
              t("bin_shares([], [0, 5, 10])", [0, 0])
          """, ["Make one counter per bin.", "A value belongs to the first bin where `edges[i] <= v < edges[i+1]`.", "The final bin also accepts the very last edge."], diff=3),
          code("Write `psi(expected, actual)` for two lists of bin shares: the sum of `(a - e) * ln(a / e)`. Skip any bin where either share is 0.",
               "import math\n\ndef psi(expected, actual):\n    pass\n", """
              import math

              def psi(expected, actual):
                  return sum((a - e) * math.log(a / e) for e, a in zip(expected, actual) if e > 0 and a > 0)
          """, """
              t("psi([0.5, 0.3, 0.2], [0.5, 0.3, 0.2])", 0.0)
              t("round(psi([0.5, 0.3, 0.2], [0.3, 0.3, 0.4]), 6)", 0.240795)
              t("round(psi([0.25, 0.25, 0.25, 0.25], [0.4, 0.3, 0.2, 0.1]), 6)", 0.228217)
          """, ["Apply the formula to each pair of bins, then add them up.", "`math.log` is the natural logarithm.", "A bin with a zero share has no usable ratio, so skip it."], diff=3, tags=["interview"]),
          code("Write `zscore_alerts(xs, window, threshold)` returning the indexes `i` (starting at `i = window`) where `abs(x - mean) / std` of the previous `window` values exceeds `threshold`. Use the population standard deviation. If the window's standard deviation is 0, flag the point only when it differs from the mean.",
               "def zscore_alerts(xs, window, threshold):\n    pass\n", """
              def zscore_alerts(xs, window, threshold):
                  out = []
                  for i in range(window, len(xs)):
                      w = xs[i - window:i]
                      mean = sum(w) / window
                      std = (sum((x - mean) ** 2 for x in w) / window) ** 0.5
                      if std == 0:
                          if xs[i] != mean:
                              out.append(i)
                      elif abs(xs[i] - mean) / std > threshold:
                          out.append(i)
                  return out
          """, """
              t("zscore_alerts([10, 10, 10, 10, 10, 50, 10], 5, 3)", [5])
              t("zscore_alerts([1, 2, 3, 4, 5, 6, 7, 8], 3, 3)", [])
              t("zscore_alerts([1, 2, 3, 4, 5, 6, 7, 8], 3, 2)", [3, 4, 5, 6, 7])
              t("zscore_alerts([5, 5], 3, 2)", [])
          """, ["For each position, look at the `window` values just before it.", "Compute their mean and population standard deviation.", "Handle `std == 0` separately, as the statement says."], diff=3),
      ], phases=["monitor"], minutes=7),
]
