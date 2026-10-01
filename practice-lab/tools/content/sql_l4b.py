from dsl import *

TRACK = "sql"
M = "ml"

DAILY = "WITH daily AS (SELECT day, AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END) AS acc FROM predictions GROUP BY day) "

CONCEPTS = [
    C("sql.window3", 4, "Windows: moving averages, frames and buckets",
      "A window can be a sliding frame, a bucket or a running total. Frames give you moving averages, which smooth noisy daily metrics.",
      [
          CODE("""
              -- 3-day moving average: the current row and the two before it
              SELECT day,
                     AVG(acc) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving
              FROM daily;

              -- compare each row with its own group's average
              SELECT id, confidence,
                     AVG(confidence) OVER (PARTITION BY day) AS day_avg
              FROM predictions;

              -- buckets
              SELECT id, NTILE(4) OVER (ORDER BY confidence, id) AS quartile FROM predictions;

              -- value from the first row of the group
              SELECT id, FIRST_VALUE(confidence) OVER (PARTITION BY day ORDER BY id) AS first_of_day FROM predictions;
          """, "sql"),
          UL("`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` is a frame of exactly three rows. It decides which rows the function sees.", "`OVER (PARTITION BY g)` with no `ORDER BY` computes over the whole group, like a group average attached to every row.", "`NTILE(n)` splits rows into `n` equal buckets, `FIRST_VALUE` / `LAST_VALUE` read the edges of the frame."),
          WARN("With `ORDER BY` and no frame, the default is `RANGE ... CURRENT ROW`, which treats rows with the same sort value as one group. Two rows on the same day get the **same** running total. Write `ROWS` when you want row-by-row behaviour."),
          QUICK("`AVG(x) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` averages how many rows (once enough rows exist)?", ["2", "3", "5", "All of them"], 1, "The current row plus the two before it."),
      ],
      [
          sql(M, "Daily accuracy and its 3-day moving average: show `day`, `accuracy` (daily, rounded to 2 decimals) and `moving` (the average of the daily accuracy over the current and two previous days, rounded to 2 decimals). Order by day.", "-- CTE for daily accuracy, then a frame\n",
              DAILY + "SELECT day, ROUND(acc, 2) AS accuracy, ROUND(AVG(acc) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving FROM daily ORDER BY day",
              ["Compute one accuracy number per day first, in a CTE.", "Then average it over a frame of three rows.", "`AVG(acc) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`"], names=True, ordered=True, diff=3, tags=["interview"]),
          sql(M, "For each prediction show `id`, `confidence` and `below_day_avg`: 1 if its confidence is below the average confidence of its own `day`, otherwise 0.", "-- AVG(...) OVER (PARTITION BY day)\n",
              "SELECT id, confidence, CASE WHEN confidence < AVG(confidence) OVER (PARTITION BY day) THEN 1 ELSE 0 END AS below_day_avg FROM predictions",
              ["You need each day's average attached to every row.", "A window with only `PARTITION BY` does that.", "Compare with `confidence < AVG(confidence) OVER (PARTITION BY day)` inside a `CASE`."], names=True, diff=3),
          sql(M, "Split all predictions into 4 confidence quartiles. Show `id`, `confidence` and `quartile` (1 is the lowest confidence). Order the rows by confidence and then `id` inside the window.", "-- NTILE(4)\n",
              "SELECT id, confidence, NTILE(4) OVER (ORDER BY confidence, id) AS quartile FROM predictions",
              ["`NTILE(n)` creates `n` equal buckets.", "The window must be ordered by confidence, with `id` as the tie-breaker.", "`NTILE(4) OVER (ORDER BY confidence, id) AS quartile`"], names=True, diff=2),
          sql(M, "For every prediction show `id` and `first_of_day`: the confidence of the first prediction (lowest `id`) on the same `day`.", "-- FIRST_VALUE\n",
              "SELECT id, FIRST_VALUE(confidence) OVER (PARTITION BY day ORDER BY id) AS first_of_day FROM predictions",
              ["Partition by day, order by id inside each day.", "`FIRST_VALUE(col)` returns the value from the first row of the frame.", "`FIRST_VALUE(confidence) OVER (PARTITION BY day ORDER BY id)`"], names=True, diff=3),
          mcq("Two rows share the same `day`. What does `SUM(x) OVER (ORDER BY day)` return for them?", ["The running total up to each row separately", "The same running total for both (rows with an equal sort value are treated together)", "NULL for the second row", "An error"], 1,
              ["Think about what \"up to the current row\" means when two rows tie.", "The default frame groups equal sort values together.", "Use `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` for strict row-by-row totals."], diff=3, tags=["interview"],
              explain=EXPLAIN("In your own words: why do tied rows get the same running total?",
                              ["The default frame is RANGE, which includes all rows with the same ORDER BY value", "ROWS makes the frame count physical rows instead"],
                              "With `ORDER BY` and no frame clause, SQL uses `RANGE UNBOUNDED PRECEDING`. A range frame includes every peer, meaning every row with the same sort value, so both tied rows see the same set of rows and get the same total.")),
      ], phases=["monitor"], minutes=7),

    C("sql.monitor1", 4, "Monitoring a model in SQL: calibration, drift and per-class metrics",
      "Accuracy alone hides problems. Check whether confidence means anything, whether the label mix is shifting, and which classes fail.",
      [
          P("Three questions every deployed classifier needs answered, each one query on the `predictions` table:"),
          UL("**Calibration**: when the model says 90% confident, is it right about 90% of the time? Bucket by confidence and compare to accuracy.", "**Drift**: did the mix of predicted labels change between model versions or over time?", "**Per-class recall**: which categories does the model miss? A good overall number can hide a class that fails."),
          CODE("""
              -- calibration buckets
              SELECT CASE WHEN confidence >= 0.9 THEN 'high'
                          WHEN confidence >= 0.6 THEN 'mid' ELSE 'low' END AS bucket,
                     COUNT(*) AS n,
                     ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy
              FROM predictions GROUP BY bucket;

              -- share of each predicted label within its model
              SELECT model, pred_label,
                     ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model), 2) AS share
              FROM predictions GROUP BY model, pred_label;
          """, "sql"),
          TIP("`SUM(COUNT(*)) OVER (PARTITION BY model)` is a window over an aggregate: first `GROUP BY` counts, then the window adds those counts up per model."),
          QUICK("A model's confidence is 0.95 on predictions that are right only 60% of the time. It is:", ["well calibrated", "overconfident", "underconfident", "perfect"], 1, "High confidence with lower accuracy means overconfident."),
      ],
      [
          sql(M, "Check calibration. Put each prediction in a `bucket`: `high` (confidence at least 0.9), `mid` (at least 0.6) or `low`. Show `bucket`, `n` (how many) and `accuracy` (share correct, rounded to 2 decimals).", "-- CASE bucket, then GROUP BY\n",
              "SELECT CASE WHEN confidence >= 0.9 THEN 'high' WHEN confidence >= 0.6 THEN 'mid' ELSE 'low' END AS bucket, COUNT(*) AS n, ROUND(AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END), 2) AS accuracy FROM predictions GROUP BY bucket",
              ["Build the bucket with `CASE`, then group by it.", "Accuracy is the average of a 1/0 correctness flag.", "`GROUP BY bucket`"], names=True, diff=3, tags=["interview"]),
          sql(M, "Check label drift. For each model and predicted label show `model`, `pred_label` and `share`: the fraction of that model's predictions with that label, rounded to 2 decimals.", "-- window over an aggregate\n",
              "SELECT model, pred_label, ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model), 2) AS share FROM predictions GROUP BY model, pred_label",
              ["Count rows per model and label first.", "Divide each count by the model's total.", "`SUM(COUNT(*)) OVER (PARTITION BY model)` is that total."], names=True, diff=3),
          sql(M, "Per-class recall. For each `true_label` show `label`, `total`, `correct` (how many were predicted correctly) and `recall` (correct divided by total, rounded to 2 decimals).", "-- group by true_label\n",
              "SELECT true_label AS label, COUNT(*) AS total, SUM(CASE WHEN pred_label = true_label THEN 1 ELSE 0 END) AS correct, ROUND(1.0 * SUM(CASE WHEN pred_label = true_label THEN 1 ELSE 0 END) / COUNT(*), 2) AS recall FROM predictions GROUP BY true_label",
              ["Group by the true label.", "Count rows, and count the correct ones with `SUM(CASE ...)`.", "Recall = correct / total."], names=True, diff=3, tags=["interview"]),
          sql(M, "Which mistakes happen most? Among the wrong predictions only, show `true_label`, `pred_label` and `n`, most frequent first (break ties by `true_label`, then `pred_label`).", "-- confusion pairs\n",
              "SELECT true_label, pred_label, COUNT(*) AS n FROM predictions WHERE pred_label <> true_label GROUP BY true_label, pred_label ORDER BY n DESC, true_label, pred_label",
              ["Keep only rows where the prediction is wrong.", "Group by the pair of labels.", "`ORDER BY n DESC, true_label, pred_label`"], names=True, ordered=True, diff=3),
          mcq("True labels for ReviewRadar's predictions arrive days later, once agents close tickets. Which signal can you watch **immediately** to catch a problem early?", ["Accuracy", "The distribution of predicted labels and the confidence scores", "Recall per class", "Nothing until labels arrive"], 1,
              ["Which numbers need ground truth, and which do not?", "Predicted labels and confidences exist the moment the model answers.", "A sudden shift in either is an early warning."], diff=2, tags=["interview"],
              why="Accuracy and recall need true labels. The label mix and confidence distribution are available instantly, so a sudden change is the earliest hint that inputs or the model have shifted."),
      ], phases=["monitor"], minutes=7),
]
