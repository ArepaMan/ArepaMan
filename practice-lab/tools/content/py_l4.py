from dsl import *
from tracegen import make_trace

TRACK = "python"

CONCEPTS = [
    C("py.numpy1", 4, "NumPy arrays: shape, dtype, indexing",
      "A NumPy array is a grid of numbers of one type. Its **shape** tells you how many numbers lie along each axis, and almost every ML bug is a shape bug.",
      [
          CODE("""
              import numpy as np

              a = np.arange(12).reshape(3, 4)   # 3 rows, 4 columns
              a.shape        # (3, 4)
              a.ndim         # 2
              a.dtype        # int64
              a[1, 2]        # 6        row 1, column 2
              a[:, 1]        # [1 5 9]  every row, column 1
              a[1:, :2]      # rows 1.., columns 0..1
          """),
          VIZ("slice", title="1-D slicing works like lists", seq=["0", "1", "2", "3", "4", "5", "6", "7"], name="a", a=2, b=6),
          UL("`shape` is a tuple, one number per axis: `(rows, columns)`.", "`reshape` changes the shape, not the data. The total number of items must stay the same. `-1` means \"work it out\".", "`.T` transposes (swaps axes).", "One dtype per array: `[1, 2.5]` becomes `float64`."),
          TIP("Print `x.shape` constantly while developing. It is the cheapest debugger in machine learning."),
          QUICK("What is the shape of `np.zeros((2, 3)).T`?", ["(2, 3)", "(3, 2)", "(6,)", "(3,)"], 1, "Transposing swaps the two axes."),
      ],
      [
          predict("What does this print? (`np` is NumPy)", """
              import numpy as np
              a = np.arange(12).reshape(3, 4)
              print(a.shape, a[1, 2], a[:, 1], a[1:, :2].tolist())
          """, "(3, 4) 6 [1 5 9] [[4, 5], [8, 9]]", ["`arange(12)` is 0..11 laid out in 3 rows of 4.", "Row 1 is `[4 5 6 7]`.", "`a[:, 1]` is the whole second column."], diff=2),
          code("Without NumPy: write `shape_of(nested)` that returns the shape tuple of a rectangular nested list, e.g. `[[1, 2, 3], [4, 5, 6]]` has shape `(2, 3)`.",
               "def shape_of(nested):\n    pass\n", """
              def shape_of(nested):
                  shape = []
                  while isinstance(nested, list):
                      shape.append(len(nested))
                      nested = nested[0] if nested else None
                  return tuple(shape)
          """, """
              t("shape_of([[1, 2, 3], [4, 5, 6]])", (2, 3))
              t("shape_of([1, 2, 3, 4])", (4,))
              t("shape_of([[[0, 0]], [[0, 0]], [[0, 0]]])", (3, 1, 2))
              t("shape_of(5)", ())
          """, ["The shape lists the length at each level of nesting.", "Go one level deeper by looking at the first element.", "Stop when the thing is no longer a list."], diff=3, tags=["interview"]),
          fill("Create the numbers 0 to 9 and arrange them in 2 rows.", "import numpy as np\nx = np.____(10).____(2, 5)", ["arange", "reshape"], ["The first function builds a range of numbers.", "The second changes the shape without changing the data.", "`arange` and `reshape`."], lang="python"),
      ], phases=["data", "deep"], minutes=5),

    C("py.numpy2", 4, "Broadcasting and vectorization",
      "Instead of looping, NumPy applies an operation to whole arrays at once. Broadcasting stretches smaller arrays so shapes line up.",
      [
          P("Rule: line the shapes up from the **right**. Each pair of sizes must be equal, or one of them must be 1. Try the widget."),
          VIZ("broadcast", title="Will these shapes broadcast?", a="3,1", b="1,4"),
          CODE("""
              import numpy as np
              a = np.array([[1, 2, 3], [4, 5, 6]])
              a.sum(axis=0)    # [5 7 9]  collapse rows, one total per column
              a.sum(axis=1)    # [ 6 15]  collapse columns, one total per row
              a.mean(axis=1)   # [2. 5.]
              a + np.array([10, 20, 30])   # row vector added to every row
          """),
          WARN("`axis=0` collapses the **rows** (you move down). The axis you name is the one that disappears from the shape."),
          TIP("Vectorized code is typically 10 to 100 times faster than a Python loop, because the loop runs in C."),
          QUICK("`a` has shape `(2, 3)`. What is the shape of `a.sum(axis=0)`?", ["(2,)", "(3,)", "(2, 3)", "()"], 1, "Axis 0 (size 2) disappears, leaving `(3,)`."),
      ],
      [
          predict("What does this print?", """
              import numpy as np
              a = np.array([[1, 2, 3], [4, 5, 6]])
              print(a.sum(axis=0), a.mean(axis=1))
          """, "[5 7 9] [2. 5.]", ["Axis 0 runs down the rows, so you get one value per column.", "`mean(axis=1)` averages each row.", "Means are floats, sums of ints stay ints."], diff=2),
          mcq("Which pair of shapes **cannot** be added with broadcasting?", ["(3, 1) and (1, 4)", "(5, 3) and (3,)", "(5, 3) and (5,)", "(2, 3, 4) and (3, 4)"], 2,
              ["Align shapes from the right and compare pairs.", "`(5, 3)` and `(5,)`: the last pair is 3 vs 5.", "3 and 5 differ and neither is 1."],
              whys=["Right-aligned pairs (1,4) and (3,1) each contain a 1: fine.", "Right-aligned: 3 vs 3 matches, the missing dimension is stretched.", None, "Right-aligned: 4 vs 4, 3 vs 3, and the extra leading axis is fine."], diff=3, tags=["interview"],
              explain=EXPLAIN("In your own words: how do you decide if two shapes broadcast?",
                              ["Align the shapes from the right", "Each pair of sizes must match or one must be 1"],
                              "Write the shapes one under the other, aligned on the right. For each column the two sizes must be equal or one of them 1. Missing leading dimensions count as 1.")),
          code("Without NumPy: write `standardize(xs)` that returns the z-scores `(x - mean) / std` using the **population** standard deviation (divide by `n`).",
               "def standardize(xs):\n    pass\n", """
              def standardize(xs):
                  n = len(xs)
                  mean = sum(xs) / n
                  std = (sum((x - mean) ** 2 for x in xs) / n) ** 0.5
                  return [(x - mean) / std for x in xs]
          """, """
              t("standardize([1, 2, 3, 4, 5])", [-1.4142135623730951, -0.7071067811865476, 0.0, 0.7071067811865476, 1.4142135623730951])
              t("standardize([10, 20])", [-1.0, 1.0])
              t("round(sum(standardize([3, 8, 1, 9])), 9)", 0.0)
          """, ["Compute the mean, then the standard deviation, then transform each value.", "Variance is the average of squared distances from the mean.", "std = `(sum((x - mean) ** 2 for x in xs) / n) ** 0.5`"], diff=3, tags=["interview"]),
      ], phases=["data", "deep"], minutes=5),

    C("py.numpy3", 4, "Masks, indexing tricks and matrix multiplication",
      "Boolean masks select by condition. Matrix multiplication needs the inner sizes to match, and it is the heart of every neural network layer.",
      [
          CODE("""
              import numpy as np
              b = np.array([3, -1, 4, -1, 5])
              mask = b > 0              # [ True False  True False  True]
              b[mask]                   # [3 4 5]
              (b > 0).sum()             # 3   (True counts as 1)
              b.argmax()                # 4   index of the largest value

              X = np.ones((100, 3))     # 100 samples, 3 features
              W = np.ones((3, 2))       # 3 inputs -> 2 outputs
              (X @ W).shape             # (100, 2)
          """),
          UL("Matrix multiply `(m, n) @ (n, k)` gives `(m, k)`. The two inner numbers must match.", "`reshape(-1, 2)` makes 2 columns and works out the rows.", "`np.concatenate`, `np.stack` join arrays; `np.where(cond, a, b)` chooses element-wise."),
          WARN("`*` is element-wise multiplication. Use `@` or `np.dot` for matrix multiplication."),
          QUICK("What is the shape of `(4, 3) @ (3, 5)`?", ["(4, 5)", "(3, 3)", "(4, 3, 5)", "It fails"], 0, "Inner sizes (3 and 3) match and disappear, leaving `(4, 5)`."),
      ],
      [
          predict("What does this print?", """
              import numpy as np
              b = np.array([3, -1, 4, -1, 5])
              print(b[b > 0], (b > 0).sum(), b.argmax())
          """, "[3 4 5] 3 4", ["The mask keeps positive values.", "Summing booleans counts the True ones.", "`argmax` returns a position, not a value."], diff=2),
          spot("This code is supposed to compute a layer's output for 100 samples, but it raises a shape error. Which line is the problem?", ["import numpy as np", "X = np.ones((100, 3))", "W = np.ones((4, 2))", "y = X @ W"], 3,
               ["Check the inner sizes of `(100, 3) @ (4, 2)`.", "3 and 4 do not match.", "Either `X` or `W` has the wrong shape; the multiplication line is where it fails."], lang="python",
               fix=FIX("What is the correct fix?", ["Make `W` shape `(3, 2)`", "Transpose `X`", "Use `*` instead of `@`", "Make `X` shape `(100, 4)` and keep `W` as it is"], 0,
                       whys=[None, "`(3, 100) @ (4, 2)` still does not match.", "`*` would try to broadcast and fail differently.", "That also works, but it changes the data to fit a mistake; `W` should take 3 inputs because `X` has 3 features."]), tags=["interview"]),
          code("Without NumPy: write `matmul(A, B)` for matrices stored as lists of lists, returning their product.",
               "def matmul(A, B):\n    pass\n", """
              def matmul(A, B):
                  return [[sum(a * b for a, b in zip(row, col)) for col in zip(*B)] for row in A]
          """, """
              t("matmul([[1, 2], [3, 4]], [[1, 0], [0, 1]])", [[1, 2], [3, 4]])
              t("matmul([[1, 2, 3]], [[4], [5], [6]])", [[32]])
              t("matmul([[1, 2], [3, 4]], [[5, 6], [7, 8]])", [[19, 22], [43, 50]])
              t("matmul([[2], [3]], [[1, 2, 3]])", [[2, 4, 6], [3, 6, 9]])
          """, ["Entry (i, j) is the dot product of row i of A with column j of B.", "`zip(*B)` gives the columns of B.", "A nested comprehension: for each row, for each column, `sum(a * b ...)`."], diff=3, tags=["interview"]),
      ], phases=["deep"], minutes=5),

    C("py.pandas1", 4, "Pandas: DataFrames, selecting and filtering",
      "A DataFrame is a table with named columns. Selecting, filtering and adding columns covers most day-to-day cleaning.",
      [
          CODE("""
              import pandas as pd
              df = pd.DataFrame({"id": [1, 2, 3, 4],
                                 "cat": ["bug", "bill", "bug", "bill"],
                                 "prio": [3, 1, 2, None]})

              df["id"]                      # one column -> Series
              df[["id", "cat"]]             # list of columns -> DataFrame
              df[df["prio"] >= 2]           # filter rows with a boolean mask
              df.loc[df["cat"] == "bug", "prio"]   # rows by condition, column by name
              df.iloc[1]                    # row by position
              df["urgent"] = df["prio"] >= 3       # add a column
          """),
          UL("`df.shape` is `(rows, columns)`; `df.head()` shows the top.", "`.loc` selects by **labels and conditions**, `.iloc` by **integer position**.", "A missing number is `NaN` (not a number) and turns an int column into float."),
          WARN("Do not assign through a filtered copy: `df[df.x > 0][\"y\"] = 1` may silently change nothing. Use `df.loc[df.x > 0, \"y\"] = 1`."),
          QUICK("`df[\"id\"]` and `df[[\"id\"]]` differ because:", ["The first is a Series, the second is a one-column DataFrame", "The second is faster", "The first copies the data", "They are identical"], 0, "Single name gives a Series (1-D); a list gives a DataFrame (2-D)."),
      ],
      [
          predict("What does this print?", """
              import pandas as pd
              df = pd.DataFrame({"id": [1, 2, 3, 4],
                                 "cat": ["bug", "bill", "bug", "bill"],
                                 "prio": [3, 1, 2, None]})
              print(df[df.prio >= 2]["id"].tolist(), df.shape, df[["id"]].shape, df["id"].shape)
          """, "[1, 3] (4, 3) (4, 1) (4,)", ["`NaN >= 2` is False, so row 4 is dropped.", "A list of columns gives a 2-D result.", "A single column name gives a 1-D Series."], diff=3),
          spot("The goal is to set `flag` to 1 for rows where `x` is positive. It silently does nothing. Which line is the bug?", ["import pandas as pd", "df = pd.DataFrame({\"x\": [1, -2, 3], \"flag\": [0, 0, 0]})", "df[df[\"x\"] > 0][\"flag\"] = 1"], 3,
               ["Look at how the assignment is made.", "`df[mask]` returns a copy.", "You assign into the copy, not into `df`."], lang="python",
               fix=FIX("How do you fix it?", ["`df.loc[df[\"x\"] > 0, \"flag\"] = 1`", "`df[df[\"x\"] > 0].flag = 1`", "`df.flag = 1`", "`df = df[df[\"x\"] > 0]`"], 0), tags=["interview"]),
          mcq("Which expression gives the number of rows in a DataFrame `df`?", ["`df.shape[0]`", "`df.shape[1]`", "`df.size()`", "`df.columns`"], 0,
              ["`shape` is `(rows, columns)`.", "Rows come first.", "`len(df)` also works."]),
      ], phases=["data"], minutes=5),

    C("py.pandas2", 4, "Pandas: groupby, merge and missing data",
      "Group, aggregate and join tables, and decide what to do with gaps. This is the core of feature building.",
      [
          CODE("""
              df.groupby("cat")["prio"].mean()          # one value per group
              df.groupby("cat").agg(n=("id", "count"), avg=("prio", "mean"))
              df["cat"].value_counts()                   # frequency table

              df.isna().sum()                            # missing values per column
              df["prio"].fillna(0)                       # fill gaps
              df.dropna(subset=["prio"])                 # drop rows with gaps

              a.merge(b, on="k", how="left")             # join two tables
          """),
          P("`merge` behaves like SQL joins: `inner` keeps only matching keys, `left` keeps every row from the left table and fills missing matches with NaN, `outer` keeps everything."),
          UL("`groupby` splits into groups, applies a function, and combines the results (split, apply, combine).", "After a left merge, count `NaN` in a right-hand column to see how many rows found no partner.", "`df.sort_values(\"col\", ascending=False)` orders rows."),
          QUICK("Left table has keys 1,2,3; right table has 2,3,4. How many rows does a **left** merge on that key give?", ["2", "3", "4", "1"], 1, "All three left rows are kept; key 1 gets NaN on the right."),
      ],
      [
          predict("What does this print?", """
              import pandas as pd
              a = pd.DataFrame({"k": [1, 2, 3], "x": ["a", "b", "c"]})
              b = pd.DataFrame({"k": [2, 3, 4], "y": ["p", "q", "r"]})
              print(len(a.merge(b, on="k")), len(a.merge(b, on="k", how="left")),
                    len(a.merge(b, on="k", how="outer")), a.merge(b, on="k", how="left")["y"].isna().sum())
          """, "2 3 4 1", ["Default `how` is `inner`: only keys in both.", "Left keeps all of `a`; outer keeps keys 1 to 4.", "Only key 1 has no partner."], diff=3, tags=["interview"]),
          order("Put the pandas steps in order: read the file, keep only open tickets, average priority per category, and print it.",
                ["df = pd.read_csv(\"tickets.csv\")", "open_df = df[df[\"status\"] == \"open\"]", "avg = open_df.groupby(\"cat\")[\"prio\"].mean()", "print(avg)"],
                ["You cannot filter before the data exists.", "Group after filtering so closed tickets are excluded.", "Printing is last."], lang="python"),
          code("Without pandas: write `group_mean(rows, key, value)` for a list of dicts. Return a dict mapping each distinct `row[key]` to the mean of `row[value]` for that group.",
               "def group_mean(rows, key, value):\n    pass\n", """
              def group_mean(rows, key, value):
                  sums, counts = {}, {}
                  for r in rows:
                      k = r[key]
                      sums[k] = sums.get(k, 0) + r[value]
                      counts[k] = counts.get(k, 0) + 1
                  return {k: sums[k] / counts[k] for k in sums}
          """, """
              rows = [{"cat": "bug", "p": 3}, {"cat": "bill", "p": 1}, {"cat": "bug", "p": 2}]
              t("group_mean(rows, 'cat', 'p')", {"bug": 2.5, "bill": 1.0})
              t("group_mean([], 'cat', 'p')", {})
              t("group_mean([{'a': 'x', 'v': 4}], 'a', 'v')", {"x": 4.0})
          """, ["Keep a running sum and a count per group.", "At the end divide each sum by its count.", "Two dicts: `sums` and `counts`, filled in one pass."], diff=3, tags=["interview"]),
      ], phases=["data", "monitor"], minutes=6),

    C("py.scipy", 4, "SciPy and statistics essentials",
      "Means, spreads, percentiles and correlation describe data. Distributions and p-values tell you whether a difference is real or luck.",
      [
          CODE("""
              import numpy as np
              from scipy import stats

              np.mean([1, 2, 3, 4])            # 2.5
              np.std([2, 4, 4, 4, 5, 5, 7, 9]) # 2.0   population std (divides by n)
              np.percentile([1, 2, 3, 4], 50)  # 2.5   the median
              stats.norm.cdf(0)                # 0.5   half of a normal curve lies below 0
              stats.pearsonr(x, y)             # correlation and p-value
              stats.ttest_ind(a, b)            # are two groups' means different?
          """),
          UL("**Standard deviation** is the typical distance from the mean.", "**Correlation** ranges from -1 to 1. It measures straight-line relationships, not causation.", "A **p-value** is the chance of seeing a result at least this extreme **if there were no real effect**. It is not the probability the effect is real."),
          WARN("`np.std` divides by `n` by default; pandas `.std()` divides by `n - 1`. The same data can give two different answers."),
          QUICK("A p-value of 0.03 means:", ["There is a 97% chance the effect is real", "If there were no effect, results this extreme would happen about 3% of the time", "The effect is large", "The test failed"], 1, "It is a statement about the data under the no-effect assumption."),
      ],
      [
          predict("What does this print?", """
              import numpy as np
              from scipy import stats
              print(stats.norm.cdf(0), np.percentile([1, 2, 3, 4], 50), np.std([2, 4, 4, 4, 5, 5, 7, 9]))
          """, "0.5 2.5 2.0", ["The normal curve is symmetric around 0.", "The 50th percentile is the median of 1,2,3,4.", "This data has mean 5; compute the squared distances."], diff=3),
          code("Without SciPy: write `pearson(xs, ys)` returning the Pearson correlation coefficient of two equal-length lists.",
               "def pearson(xs, ys):\n    pass\n", """
              def pearson(xs, ys):
                  n = len(xs)
                  mx, my = sum(xs) / n, sum(ys) / n
                  cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                  sx = sum((x - mx) ** 2 for x in xs) ** 0.5
                  sy = sum((y - my) ** 2 for y in ys) ** 0.5
                  return cov / (sx * sy)
          """, """
              t("round(pearson([1, 2, 3, 4], [2, 4, 5, 9]), 6)", 0.964764)
              t("round(pearson([1, 2, 3, 4, 5], [10, 8, 6, 4, 2]), 6)", -1.0)
              t("round(pearson([1, 2, 3], [5, 5.5, 6]), 6)", 1.0)
          """, ["Correlation is covariance divided by the product of the spreads.", "Use deviations from each mean.", "`cov / (sx * sy)` where the three sums use the same deviations."], diff=3),
          mcq("A model's validation accuracy is 92% on one run and 90% on another. A paired test gives p = 0.4. What is the sensible conclusion?", ["The first model is clearly better", "The difference could easily be random noise", "The models are identical", "The test is broken"], 1,
              ["A large p-value means the difference is not unusual under no effect.", "It does not prove the models are the same.", "Ignore the small gap until you have more evidence."], tags=["interview"]),
      ], phases=["data", "monitor"], minutes=5),

    C("py.sklearn", 4, "scikit-learn: the fit / predict API",
      "Every scikit-learn model follows the same pattern: create it, `fit` on training data, then `predict` or `transform`. Pipelines chain the steps safely.",
      [
          CODE("""
              from sklearn.model_selection import train_test_split
              from sklearn.feature_extraction.text import TfidfVectorizer
              from sklearn.linear_model import LogisticRegression
              from sklearn.pipeline import Pipeline
              from sklearn.metrics import accuracy_score

              X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

              pipe = Pipeline([("tfidf", TfidfVectorizer()),
                               ("clf", LogisticRegression())])
              pipe.fit(X_train, y_train)          # learns from training data only
              pred = pipe.predict(X_test)
              print(accuracy_score(y_test, pred))
          """),
          UL("`fit(X, y)` learns. `predict(X)` outputs labels. `transform(X)` converts data (scalers, vectorisers).", "`fit_transform` = fit then transform, for the **training** data only.", "`X` is 2-D `(n_samples, n_features)`; `y` is 1-D `(n_samples,)`."),
          WARN("**Data leakage**: if you fit a scaler or vectoriser on all the data before splitting, information from the test set leaks into training and your score is too optimistic. Put the steps in a `Pipeline` and fit only on the training split."),
          QUICK("For new data you should call:", ["`scaler.fit_transform(X_new)`", "`scaler.transform(X_new)`", "`scaler.fit(X_new)`", "`scaler.predict(X_new)`"], 1, "Reuse what was learned on the training set; do not learn again."),
      ],
      [
          order("Put the standard supervised-learning workflow in order.",
                ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)", "model = LogisticRegression()", "model.fit(X_train, y_train)", "pred = model.predict(X_test)", "print(accuracy_score(y_test, pred))"],
                ["Split the data before training anything.", "A model must be created before it is fitted, and fitted before it predicts.", "Evaluate on the test set last."], lang="python"),
          spot("This pipeline leaks information from the test set. Which line is the problem?", ["X_scaled = StandardScaler().fit_transform(X)", "X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)", "model = LogisticRegression().fit(X_train, y_train)", "print(model.score(X_test, y_test))"], 1,
               ["Which line learns statistics (mean, std) from data?", "It runs on **all** of `X`, before the split.", "The test rows influenced the scaler."], lang="python",
               fix=FIX("How should it be fixed?", ["Split first, fit the scaler on the training part only, then `transform` the test part", "Scale after predicting", "Use `fit_transform` on the test set as well", "Remove the scaler"], 0), diff=3, tags=["interview"],
               explain=EXPLAIN("In your own words: why is that a problem?",
                               ["The scaler computed mean and std using test rows", "So the test set is no longer unseen and the score is optimistic"],
                               "Fitting on all the data lets test information shape the preprocessing. The test set should be treated as the future: unseen when anything is learned. Fit on train, transform both.")),
          predict("What does this print?", """
              from sklearn.feature_extraction.text import CountVectorizer
              cv = CountVectorizer()
              m = cv.fit_transform(["bug bug fix", "fix login"])
              print(m.shape, sorted(cv.vocabulary_), m.toarray().tolist())
          """, "(2, 3) ['bug', 'fix', 'login'] [[2, 1, 0], [0, 1, 1]]", ["Rows are documents, columns are distinct words.", "Words are sorted alphabetically: bug, fix, login.", "Row 1 has `bug` twice and `fix` once."], diff=3),
      ], phases=["data"], minutes=6),

    C("py.metrics", 4, "Evaluation metrics",
      "Accuracy can lie. Precision, recall and F1 tell you what kind of mistakes a classifier makes, and the decision threshold trades one against the other.",
      [
          P("Move the threshold and watch the confusion matrix change."),
          VIZ("metrics", title="Move the threshold", data=[[0.05, 0], [0.12, 0], [0.2, 0], [0.31, 1], [0.38, 0], [0.44, 0], [0.52, 1], [0.6, 0], [0.67, 1], [0.78, 1], [0.86, 1], [0.93, 1]]),
          TABLE(["Metric", "Formula", "Answers"], [["precision", "TP / (TP + FP)", "Of the tickets I flagged, how many were right?"], ["recall", "TP / (TP + FN)", "Of the real ones, how many did I find?"], ["F1", "2PR / (P + R)", "One number balancing both"], ["accuracy", "(TP + TN) / all", "Overall fraction correct. Misleading when classes are imbalanced."]]),
          WARN("If only 1 ticket in 100 is urgent, a model that always says \"not urgent\" is 99% accurate and completely useless. Check recall."),
          CODE("""
              import math
              def softmax(xs):                    # turns scores into probabilities
                  m = max(xs)                     # subtract the max for numerical stability
                  e = [math.exp(x - m) for x in xs]
                  s = sum(e)
                  return [v / s for v in e]
          """),
          QUICK("Your spam filter must never miss real spam, even if it flags some good mail. Which metric matters most?", ["Precision", "Recall", "Accuracy", "Loss"], 1, "Recall measures how much of the real spam you caught."),
      ],
      [
          code("Write `precision_recall_f1(y_true, y_pred)` for binary labels (1 is the positive class). Return a tuple `(precision, recall, f1)`. If a denominator would be zero, use `0.0` for that value.",
               "def precision_recall_f1(y_true, y_pred):\n    pass\n", """
              def precision_recall_f1(y_true, y_pred):
                  tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
                  fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
                  fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
                  precision = tp / (tp + fp) if tp + fp else 0.0
                  recall = tp / (tp + fn) if tp + fn else 0.0
                  f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
                  return precision, recall, f1
          """, """
              t("precision_recall_f1([1, 0, 1, 1, 0, 0, 1, 0], [1, 0, 0, 1, 0, 1, 1, 0])", (0.75, 0.75, 0.75))
              t("precision_recall_f1([1, 1, 1, 0], [1, 0, 0, 0])", (1.0, 1 / 3, 0.5))
              t("precision_recall_f1([0, 0], [0, 0])", (0.0, 0.0, 0.0))
          """, ["Count true positives, false positives and false negatives first.", "Guard each division against a zero denominator.", "f1 = 2 * precision * recall / (precision + recall)"], diff=3, tags=["interview"]),
          code("Write `softmax(xs)` that returns the probabilities `exp(x) / sum(exp(x))`. Subtract the maximum first so large scores do not overflow.",
               "import math\n\ndef softmax(xs):\n    pass\n", """
              import math

              def softmax(xs):
                  m = max(xs)
                  e = [math.exp(x - m) for x in xs]
                  s = sum(e)
                  return [v / s for v in e]
          """, """
              t("softmax([1, 2, 3])", [0.09003057317038046, 0.24472847105479764, 0.6652409557748218])
              t("round(sum(softmax([5, -2, 0.3])), 9)", 1.0)
              t("softmax([1000, 1000])", [0.5, 0.5])
          """, ["Probabilities must be positive and add up to 1.", "Dividing by the total normalises them.", "`math.exp(1000)` overflows, so use `x - max(xs)`."], diff=3, tags=["interview"]),
          mcq("A dataset is 95% negative. A model predicts negative for everything. Which statement is true?", ["Accuracy is 95%, recall for the positive class is 0", "Accuracy is 0%", "Precision is 100% and recall is 100%", "F1 is 0.95"], 0,
              ["Count what fraction is right overall.", "It never predicts the positive class.", "No positives found means recall 0."], diff=2, tags=["interview"]),
      ], phases=["data", "monitor"], minutes=6),
]
