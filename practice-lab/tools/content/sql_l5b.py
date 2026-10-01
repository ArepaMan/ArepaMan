from dsl import *

TRACK = "sql"
D = "support"
M = "ml"

CONCEPTS = [
    C("sql.txn", 5, "Transactions, upserts and locking",
      "A transaction makes several changes succeed or fail together. Knowing isolation levels and locks separates \"it works on my laptop\" from \"it works under load\".",
      [
          CODE("""
              BEGIN;
              UPDATE tickets SET status = 'closed' WHERE id = 4;
              UPDATE tickets SET status = 'closed' WHERE id = 5;
              COMMIT;                     -- both changes become permanent together (ROLLBACK undoes both)

              -- upsert: insert, or update if the key already exists
              INSERT INTO customers (id, name, plan, country)
              VALUES (3, 'Chika Obi', 'pro', 'NG')
              ON CONFLICT (id) DO UPDATE SET plan = excluded.plan;

              -- PostgreSQL: lock the rows you are about to change
              SELECT * FROM tickets WHERE id = 4 FOR UPDATE;
          """, "sql"),
          TABLE(["ACID", "Means"], [["Atomic", "all changes in a transaction happen, or none"], ["Consistent", "constraints always hold"], ["Isolated", "concurrent transactions do not see each other's half-done work"], ["Durable", "committed data survives a crash"]]),
          TABLE(["Anomaly", "What happens"], [["dirty read", "you read another transaction's uncommitted change"], ["non-repeatable read", "you read a row twice and get different values because someone committed in between"], ["phantom read", "a repeated query returns new rows that someone committed in between"]]),
          UL("Higher isolation levels prevent more anomalies but allow less concurrency. PostgreSQL's default is **read committed**.", "A **deadlock** happens when two transactions each hold a lock the other needs. Always update rows in the same order.", "Make writes **idempotent** with upserts so a retried request does not create duplicates. That matters for any API that may be called twice."),
          QUICK("What does `ROLLBACK` do?", ["Commits the transaction", "Undoes every change since `BEGIN`", "Deletes the table", "Restarts the database"], 1, "All changes in the open transaction are discarded."),
      ],
      [
          sql(D, "Customer 3 already exists on the `enterprise` plan. Write **one statement** that inserts `(3, 'Chika Obi', 'pro', 'NG')` and, because id 3 already exists, updates the `plan` instead (an upsert).", "-- INSERT ... ON CONFLICT ... DO UPDATE\n",
              "INSERT INTO customers (id, name, plan, country) VALUES (3, 'Chika Obi', 'pro', 'NG') ON CONFLICT (id) DO UPDATE SET plan = excluded.plan",
              ["A normal `INSERT` would fail on the duplicate key.", "Add `ON CONFLICT (id) DO UPDATE SET ...`.", "`excluded.plan` is the value you tried to insert."], after="SELECT id, name, plan FROM customers WHERE id = 3", diff=3, tags=["interview"]),
          sql(D, "Close tickets 4 and 5 together in one transaction: `BEGIN`, two updates setting `status` to `closed`, then `COMMIT`.", "-- BEGIN; ...; COMMIT;\n",
              "BEGIN; UPDATE tickets SET status = 'closed' WHERE id = 4; UPDATE tickets SET status = 'closed' WHERE id = 5; COMMIT",
              ["Start with `BEGIN;`.", "Two `UPDATE` statements, one per ticket.", "Finish with `COMMIT;`."], after="SELECT id, status FROM tickets WHERE id IN (4, 5) ORDER BY id", diff=2),
          fill("Lock the row you are about to update so no other transaction changes it first (PostgreSQL).", "SELECT * FROM tickets WHERE id = 4 ____ UPDATE;", [["FOR"]], ["It is a two-word clause ending in `UPDATE`.", "The first word is a preposition.", "`FOR`"], lang="sql", ci=True, diff=3),
          mcq("Transaction A reads ticket 4's status twice and gets `open` then `closed`, because transaction B committed in between. Which anomaly is this?", ["Dirty read", "Non-repeatable read", "Phantom read", "Deadlock"], 1,
              ["B's change was committed, so it is not a dirty read.", "The **same row** returned a different value.", "A phantom is about new rows appearing, not changed values."], diff=3, tags=["interview"]),
          mcq("Two transactions each update tickets 4 and 5, but one goes 4 then 5 and the other 5 then 4. They sometimes freeze each other. What is the standard fix?", ["Add more indexes", "Always update rows in the same order in every transaction", "Use `SELECT *`", "Turn off transactions"], 1,
              ["Each holds one lock and waits for the other.", "A consistent order breaks the cycle.", "Databases also abort one transaction when they detect a deadlock, so code should retry."], diff=3, tags=["interview"]),
      ], phases=["serving", "monitor"], minutes=7),

    C("sql.analytics", 5, "Analytics patterns: shares, cohorts, latest-per-group and gaps",
      "A handful of query shapes answer most analytics questions. Learn them as patterns and you can adapt them to any table.",
      [
          CODE("""
              -- share of total
              SELECT category, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
              FROM tickets GROUP BY category;

              -- latest row per group
              WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn
                FROM tickets WHERE customer_id IS NOT NULL)
              SELECT customer_id, id FROM ranked WHERE rn = 1;

              -- gap to the previous event
              SELECT id, julianday(created_at) - julianday(LAG(created_at) OVER (PARTITION BY customer_id ORDER BY created_at, id)) AS gap_days
              FROM tickets WHERE customer_id IS NOT NULL;
          """, "sql"),
          UL("**Share of total**: `SUM(...) OVER ()` with an empty window is the grand total.", "**Latest per group**: rank with `ROW_NUMBER` descending and keep `rn = 1`.", "**Cohort**: find each entity's first event with `MIN(date)`, then group by that date.", "**Gaps**: `LAG` the previous event, subtract."),
          QUICK("Which pattern keeps only the newest row for each customer?", ["`GROUP BY customer_id`", "`ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC)` and keep `rn = 1`", "`SELECT DISTINCT customer_id`", "`LIMIT 1`"], 1, "Rank rows inside each group, newest first, then keep the first."),
      ],
      [
          sql(D, "For each ticket `category` show `pct`: its share of all tickets as a percentage with one decimal place.", "-- SUM(COUNT(*)) OVER ()\n",
              "SELECT category, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct FROM tickets GROUP BY category",
              ["Count tickets per category.", "Divide by the grand total, which a window with an empty `OVER ()` gives you.", "`ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)`"], names=True, diff=3),
          sql(D, "A customer's cohort is the date of their first ticket. Show `first_day` and `new_customers`: how many customers had their first ticket on that date. Ignore tickets with no customer.", "-- MIN(created_at) per customer, then count\n",
              "WITH firsts AS (SELECT customer_id, MIN(created_at) AS first_day FROM tickets WHERE customer_id IS NOT NULL GROUP BY customer_id) SELECT first_day, COUNT(*) AS new_customers FROM firsts GROUP BY first_day",
              ["Find each customer's first date in a CTE.", "Then group those dates and count.", "`GROUP BY first_day`"], names=True, diff=3, tags=["interview"]),
          sql(D, "Show each customer's most recent ticket: `customer_id` and `id` (latest `created_at`, ties broken by the larger `id`). Ignore tickets with no customer.", "-- ROW_NUMBER ... rn = 1\n",
              "WITH ranked AS (SELECT customer_id, id, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn FROM tickets WHERE customer_id IS NOT NULL) SELECT customer_id, id FROM ranked WHERE rn = 1",
              ["Rank each customer's tickets, newest first.", "Then keep only rank 1.", "You need the CTE because you cannot filter on a window function directly."], diff=3, tags=["interview"]),
          sql(D, "For each ticket with a customer, show `id` and `gap_days`: the whole number of days since that **same customer's** previous ticket (NULL for their first). Order the window by `created_at`, then `id`.", "-- LAG within PARTITION BY customer_id\n",
              "SELECT id, CAST(julianday(created_at) - julianday(LAG(created_at) OVER (PARTITION BY customer_id ORDER BY created_at, id)) AS INTEGER) AS gap_days FROM tickets WHERE customer_id IS NOT NULL",
              ["`LAG(created_at)` with a partition by customer gives their previous date.", "Subtract the day numbers with `julianday`.", "Wrap it in `CAST(... AS INTEGER)`."], names=True, diff=3),
          mcq("What is the difference between `COUNT(*)` and `COUNT(DISTINCT customer_id)` on `tickets`?", ["No difference", "`COUNT(*)` counts rows, the other counts different customers (ignoring NULL)", "`COUNT(*)` ignores NULL", "`DISTINCT` makes the query faster"], 1,
              ["Think of a customer with three tickets.", "One counts rows, the other counts unique values.", "NULL values are not counted by `COUNT(column)`."], diff=2, tags=["interview"]),
      ], phases=["monitor", "data"], minutes=7),

    C("sql.alerts", 5, "Alerting queries for model monitoring",
      "A monitoring dashboard is a set of queries plus thresholds. The art is flagging real problems without waking people for noise.",
      [
          CODE("""
              -- accuracy drops of more than 0.3 versus the previous day
              WITH daily AS (
                SELECT day, AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END) AS acc
                FROM predictions GROUP BY day)
              SELECT day, ROUND(LAG(acc) OVER (ORDER BY day) - acc, 2) AS decline
              FROM daily
              WHERE LAG(acc) OVER (ORDER BY day) - acc > 0.3;     -- not allowed: window in WHERE!
          """, "sql"),
          P("That last query is wrong: window functions are not allowed in `WHERE`. Put the window in a CTE first, then filter in the outer query. This is the shape of every alerting query:"),
          UL("1. A CTE computes the metric per time bucket.", "2. A second step compares with the previous bucket or a baseline (`LAG`, rolling average).", "3. The outer query filters by the threshold."),
          TIP("Compare against a **rolling baseline** rather than a fixed number when traffic is seasonal, and require the condition on two days in a row to avoid noisy alerts."),
          QUICK("Why can't you write `WHERE LAG(x) OVER (...) > 5`?", ["`LAG` is slow", "Window functions run after `WHERE`, so they do not exist yet at that point", "`LAG` needs `GROUP BY`", "It is allowed"], 1, "Compute the window in a subquery or CTE, then filter on the result."),
      ],
      [
          sql(M, "Find accuracy drops. Show `day` and `decline` (the previous day's accuracy minus this day's, rounded to 2 decimals) for days where the accuracy fell by **more than 0.3** compared with the previous day.", "-- daily CTE, LAG in a second CTE, filter outside\n",
              "WITH daily AS (SELECT day, AVG(CASE WHEN pred_label = true_label THEN 1.0 ELSE 0.0 END) AS acc FROM predictions GROUP BY day), d AS (SELECT day, LAG(acc) OVER (ORDER BY day) - acc AS decline FROM daily) SELECT day, ROUND(decline, 2) AS decline FROM d WHERE decline > 0.3",
              ["Build daily accuracy, then use `LAG` in a second CTE.", "Window functions cannot be filtered directly.", "Filter `WHERE decline > 0.3` in the final query."], names=True, diff=3, tags=["interview"]),
          sql(M, "Low-confidence share. For each `day` show `low_share`: the fraction of that day's predictions with confidence below 0.6 (2 decimals). Keep only days where it is at least 0.5.", "-- AVG of a flag, then HAVING\n",
              "SELECT day, ROUND(AVG(CASE WHEN confidence < 0.6 THEN 1.0 ELSE 0.0 END), 2) AS low_share FROM predictions GROUP BY day HAVING AVG(CASE WHEN confidence < 0.6 THEN 1.0 ELSE 0.0 END) >= 0.5",
              ["The average of a 1/0 flag is the share.", "Filter groups with `HAVING`.", "Repeat the expression in `HAVING`, or use a CTE."], names=True, diff=3),
          sql(M, "Rolling confidence per model. For each prediction show `id`, `model` and `rolling_conf`: the average confidence of the current and previous prediction **within the same model** (ordered by `id`), rounded to 2 decimals.", "-- frame of 2 rows, partitioned by model\n",
              "SELECT id, model, ROUND(AVG(confidence) OVER (PARTITION BY model ORDER BY id ROWS BETWEEN 1 PRECEDING AND CURRENT ROW), 2) AS rolling_conf FROM predictions",
              ["Partition by model so versions do not mix.", "A frame of the previous row and the current row.", "`ROWS BETWEEN 1 PRECEDING AND CURRENT ROW`"], names=True, diff=3),
          mcq("An alert fires every time daily accuracy drops below a fixed 0.8, but ticket volume is tiny on weekends and accuracy swings a lot. What improves it most?", ["Lower the threshold to 0.1", "Use a rolling baseline and require the drop to persist (for example two days), possibly with a minimum sample size", "Alert on every prediction", "Switch off monitoring"], 1,
              ["Fixed thresholds ignore normal variation.", "Small samples are noisy.", "Persistence and a baseline reduce false alarms."], diff=3, tags=["interview"]),
      ], phases=["monitor"], minutes=7),
]
