from dsl import *

TRACK = "sql"
D = "support"

CONCEPTS = [
    C("sql.window1", 4, "Window functions: ranking and running totals",
      "A window function calculates across related rows **without collapsing them**. Unlike `GROUP BY`, every row stays in the result.",
      [
          P("Switch the function and toggle the partition to see how rows are numbered and totalled."),
          VIZ("window", title="Windows keep the rows", table="tickets", cols=["id", "category", "words"], part="category", order="words", value="words",
              rows=[[1, "billing", 42], [2, "bug", 118], [4, "bug", 95], [6, "billing", 38], [7, "bug", 150], [9, "billing", 70], [10, "bug", 210], [13, "billing", 30]]),
          CODE("""
              SELECT id, category, words,
                     ROW_NUMBER() OVER (PARTITION BY category ORDER BY words DESC) AS rn
              FROM tickets;

              SELECT id, SUM(words) OVER (ORDER BY id) AS running FROM tickets;   -- running total
          """, "sql"),
          UL("`OVER (...)` defines the window: `PARTITION BY` splits rows into groups, `ORDER BY` orders inside each group.", "`ROW_NUMBER()` 1,2,3...; `RANK()` leaves gaps after ties; `DENSE_RANK()` does not.", "A window function runs **after** `WHERE`, so you cannot filter on it directly. Wrap the query in a CTE and filter there."),
          WARN("For **top-N per group**, rank in a CTE and then keep `rn <= N` in the outer query. This is a classic interview question."),
          QUICK("Three rows have scores 90, 90, 80 (high first). What does `RANK()` give?", ["1, 2, 3", "1, 1, 2", "1, 1, 3", "1, 2, 2"], 2, "Tied rows share rank 1, and the next rank skips to 3."),
      ],
      [
          sql(D, "Number each ticket within its category from longest to shortest. Show `id`, `category` and the number as `rn`.", "-- ROW_NUMBER() OVER (PARTITION BY ...)\n", "SELECT id, category, ROW_NUMBER() OVER (PARTITION BY category ORDER BY words DESC) AS rn FROM tickets", ["The numbering restarts for every category.", "`PARTITION BY category ORDER BY words DESC`", "`ROW_NUMBER() OVER (PARTITION BY category ORDER BY words DESC) AS rn`"], names=True, diff=3),
          sql(D, "Show each ticket `id` with the running total of `words` in `id` order, named `running`.", "-- SUM(...) OVER (ORDER BY ...)\n", "SELECT id, SUM(words) OVER (ORDER BY id) AS running FROM tickets", ["A running total is a sum over a growing window.", "Add `OVER (ORDER BY id)` after `SUM(words)`.", "`SUM(words) OVER (ORDER BY id) AS running`"], names=True, diff=3),
          sql(D, "Show the **two longest tickets in each category**: `id`, `category`, `words`.", "-- rank in a CTE, filter outside\n", "WITH ranked AS (SELECT id, category, words, ROW_NUMBER() OVER (PARTITION BY category ORDER BY words DESC) AS rn FROM tickets) SELECT id, category, words FROM ranked WHERE rn <= 2", ["You cannot filter on a window function in the same query.", "Compute the row number in a CTE.", "Then `WHERE rn <= 2` in the outer query."], diff=3, tags=["interview"],
              explain=EXPLAIN("In your own words: why do you need a CTE for top-N per group?",
                              ["Window functions are evaluated after WHERE", "So you must compute the rank first and filter on it in an outer query"],
                              "`WHERE` is applied before window functions run, so the rank does not exist yet at that point. Computing it in a CTE (or subquery) makes it an ordinary column the outer `WHERE` can use.")),
          mcq("Scores 90, 90, 80 ordered high to low. What does `DENSE_RANK()` return?", ["1, 2, 3", "1, 1, 2", "1, 1, 3", "1, 2, 2"], 1,
              ["Tied rows share a rank.", "`DENSE_RANK` never skips numbers.", "The 80 gets rank 2."], diff=2, tags=["interview"]),
      ], phases=["monitor", "data"], minutes=7),

    C("sql.window2", 4, "Windows for monitoring: LAG, daily metrics and drift",
      "Window functions shine for time series: compare each day with the previous one, or compute a metric per day. This is the SQL behind ReviewRadar's monitoring.",
      [
          P("The `predictions` table logs every model prediction with the true label once known. Open **Tables you can query** to see it."),
          CODE("""
              -- accuracy per day
              SELECT day,
                     ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy
              FROM predictions
              GROUP BY day
              ORDER BY day;

              -- compare with the previous row
              SELECT id, confidence, LAG(confidence) OVER (ORDER BY id) AS prev_conf
              FROM predictions;
          """, "sql"),
          UL("`LAG(col)` is the value from the previous row, `LEAD(col)` from the next. The first row has `NULL`.", "Averaging a 1/0 flag gives the fraction of rows where it is 1. That is how you compute accuracy in SQL.", "Daily accuracy, confidence and class mix are the first things to chart when watching for **drift**."),
          WARN("In PostgreSQL you cannot average a boolean directly, so use `CASE WHEN ... THEN 1.0 ELSE 0.0 END` as above. It works everywhere."),
          QUICK("What does `LAG(x) OVER (ORDER BY day)` give for the very first day?", ["0", "NULL", "the same day's x", "an error"], 1, "There is no previous row, so the result is NULL."),
      ],
      [
          sql("ml", "For each prediction show `id`, `confidence` and the previous row's confidence (ordered by `id`) as `prev_conf`.", "-- LAG(...) OVER (ORDER BY id)\n", "SELECT id, confidence, LAG(confidence) OVER (ORDER BY id) AS prev_conf FROM predictions", ["You need the value from the row before.", "`LAG(confidence)` needs an `OVER (ORDER BY id)`.", "`LAG(confidence) OVER (ORDER BY id) AS prev_conf`"], names=True, diff=2),
          sql("ml", "Compute the model's accuracy for each `day`: show `day` and `accuracy` (the fraction of rows where `pred_label` equals `true_label`, rounded to 2 decimals), in day order.", "-- AVG of a 1/0 flag\n", "SELECT day, ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy FROM predictions GROUP BY day ORDER BY day", ["Turn each row into 1 (correct) or 0 (wrong) with `CASE`.", "The average of those flags is the accuracy.", "`GROUP BY day ORDER BY day`"], names=True, ordered=True, diff=3, tags=["interview"]),
          sql("ml", "Compare the two model versions: show `model` and its `accuracy` rounded to 2 decimals.", "-- same idea, grouped by model\n", "SELECT model, ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy FROM predictions GROUP BY model", ["Reuse the accuracy expression.", "Group by `model` instead of `day`.", "`GROUP BY model`"], names=True, diff=2),
          sql("ml", "Drift check: for each `day` show `accuracy` (rounded to 2 decimals) and `change`, the difference from the previous day's accuracy (rounded to 2 decimals). Order by day.", "-- CTE for daily accuracy, then LAG\n", "WITH daily AS (SELECT day, ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy FROM predictions GROUP BY day) SELECT day, accuracy, ROUND(accuracy - LAG(accuracy) OVER (ORDER BY day), 2) AS change FROM daily ORDER BY day", ["Build the daily accuracy first, in a CTE.", "Then subtract `LAG(accuracy) OVER (ORDER BY day)`.", "The first day has no previous day, so `change` is NULL."], names=True, ordered=True, diff=3, tags=["interview"]),
      ], phases=["monitor"], minutes=7),

    C("sql.design", 4, "Schema design: keys, constraints and normalisation",
      "Good tables make bad data impossible. Keys identify rows, foreign keys link tables, and normalising stops the same fact living in two places.",
      [
          CODE("""
              CREATE TABLE labels (
                  ticket_id INTEGER PRIMARY KEY,                -- unique, never NULL
                  label     TEXT NOT NULL,                      -- must have a value
                  FOREIGN KEY (ticket_id) REFERENCES tickets(id) -- must point at a real ticket
              );
          """, "sql"),
          UL("**Primary key**: uniquely identifies a row. **Foreign key**: a column that must match a primary key elsewhere.", "**Normalisation**: store each fact once. Keep the customer's name in `customers`, and refer to it by id from `tickets`.", "Pick types deliberately: integers for ids and counts, `TEXT` for strings, a real date type for dates, `REAL`/`NUMERIC` for decimals."),
          WARN("Storing a customer's name in every ticket row means renaming a customer requires updating hundreds of rows, and missing one leaves the data inconsistent."),
          QUICK("A foreign key guarantees that:", ["The column is unique", "The value matches an existing row in the referenced table", "The column is indexed", "The column is never NULL"], 1, "It protects the link between the tables."),
      ],
      [
          fill("Complete the table definition.", "CREATE TABLE labels (\n    ticket_id INTEGER ____ KEY,\n    label TEXT ____ NULL,\n    FOREIGN KEY (ticket_id) ____ tickets(id)\n);", ["PRIMARY", "NOT", "REFERENCES"], ["The first makes each ticket id appear only once.", "The second forbids a missing label.", "`PRIMARY`, `NOT`, `REFERENCES`."], lang="sql", ci=True),
          sql(D, "Create a table `reviews` with `id INTEGER PRIMARY KEY` and `score INTEGER NOT NULL`, then insert two rows: `(1, 5)` and `(2, 3)`.", "-- CREATE TABLE ...; INSERT ...;\n", "CREATE TABLE reviews (id INTEGER PRIMARY KEY, score INTEGER NOT NULL); INSERT INTO reviews VALUES (1, 5); INSERT INTO reviews VALUES (2, 3)", ["Two statements: one creates the table, one inserts.", "Separate statements with semicolons.", "`INSERT INTO reviews VALUES (1, 5);`"], after="SELECT id, score FROM reviews ORDER BY id", diff=2),
          mcq("Why is storing `customer_name` in every row of `tickets` a design problem?", ["It makes queries impossible", "The same fact is repeated, so updates can leave the data inconsistent", "SQL does not allow text columns", "It breaks the primary key"], 1,
              ["Think about renaming one customer.", "Which rows must change?", "Repeated facts can disagree."], diff=2, tags=["interview"]),
      ], phases=["serving", "monitor"], minutes=5),
]
