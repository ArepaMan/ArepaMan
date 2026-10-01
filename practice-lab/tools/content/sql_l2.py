from dsl import *

TRACK = "sql"
D = "support"

CONCEPTS = [
    C("sql.agg", 2, "Aggregates: COUNT, SUM, AVG and GROUP BY",
      "Aggregate functions squeeze many rows into one number. `GROUP BY` does it once per group.",
      [
          P("Press the buttons to group the rows by category and change the function."),
          VIZ("groupby", title="Watch GROUP BY collapse rows", table="tickets", cols=["id", "category", "words"], group="category", value="words",
              rows=[[1, "billing", 42], [2, "bug", 118], [3, "account", 20], [4, "bug", 95], [5, "feature", 60], [6, "billing", 38], [7, "bug", 150], [8, "account", 15]]),
          CODE("""
              SELECT COUNT(*) FROM tickets;                              -- how many rows
              SELECT category, COUNT(*) AS n FROM tickets GROUP BY category;
              SELECT category, ROUND(AVG(words), 1) AS avg_words
              FROM tickets
              GROUP BY category
              HAVING COUNT(*) > 3;                                       -- filter groups
          """, "sql"),
          UL("`COUNT(*)` counts rows; `COUNT(col)` skips NULLs.", "`WHERE` filters **rows before** grouping. `HAVING` filters **groups after** aggregating.", "Every selected column must be either in `GROUP BY` or inside an aggregate."),
          WARN("You cannot use an aggregate in `WHERE`. `WHERE COUNT(*) > 3` is an error; use `HAVING COUNT(*) > 3`."),
          QUICK("Which clause removes whole groups, such as categories with fewer than 3 tickets?", ["`WHERE`", "`HAVING`", "`ORDER BY`", "`DISTINCT`"], 1, "`HAVING` runs after grouping, so it can test aggregates."),
      ],
      [
          sql(D, "How many tickets are in each category? Show `category` and the count as `n`.", "-- GROUP BY\n", "SELECT category, COUNT(*) AS n FROM tickets GROUP BY category", ["You need one row per category.", "Count rows with `COUNT(*)`.", "`SELECT category, COUNT(*) AS n FROM tickets GROUP BY category`"], names=True),
          sql(D, "For categories with more than 3 tickets, show `category` and the average `words` rounded to 1 decimal as `avg_words`.", "-- GROUP BY with HAVING\n", "SELECT category, ROUND(AVG(words), 1) AS avg_words FROM tickets GROUP BY category HAVING COUNT(*) > 3", ["Group by category, then keep only big groups.", "Filter groups with `HAVING`, not `WHERE`.", "`... GROUP BY category HAVING COUNT(*) > 3`"], names=True, diff=2, tags=["interview"]),
          sql(D, "How many **open** tickets are there for each priority? Show `priority` and `n`.", "-- filter rows first, then group\n", "SELECT priority, COUNT(*) AS n FROM tickets WHERE status = 'open' GROUP BY priority", ["Filter the rows before grouping.", "`WHERE` comes before `GROUP BY`.", "`WHERE status = 'open' GROUP BY priority`"], names=True, diff=2),
          mcq("You want customers' ticket counts but only for customers with at least 3 tickets. Where does that condition go?", ["`WHERE COUNT(*) >= 3`", "`HAVING COUNT(*) >= 3`", "`GROUP BY COUNT(*) >= 3`", "`LIMIT 3`"], 1,
              ["The count only exists after grouping.", "Aggregates cannot appear in `WHERE`.", "`HAVING` filters groups."], diff=2, tags=["interview"],
              explain=EXPLAIN("In your own words: what is the difference between WHERE and HAVING?",
                              ["WHERE filters individual rows before grouping", "HAVING filters groups after aggregates are computed"],
                              "`WHERE` is applied to rows before they are grouped, so it cannot see aggregate results. `HAVING` runs after `GROUP BY` and can filter on `COUNT`, `SUM` and friends.")),
      ], phases=["data", "monitor"], minutes=5),

    C("sql.joins", 2, "Joins: combining tables",
      "Data lives in separate tables linked by keys. A join lines rows up by a matching column, and the join type decides what happens to rows without a partner.",
      [
          VIZ("join", title="See how each join treats unmatched rows",
              left={"name": "customers", "cols": ["id", "name"], "rows": [[1, "Ana"], [2, "Ben"], [3, "Chika"], [10, "Jorge"]]},
              right={"name": "tickets", "cols": ["id", "customer_id", "category"], "rows": [[1, 1, "billing"], [2, 2, "bug"], [8, 1, "account"], [11, None, "other"]]}, on=["id", "customer_id"]),
          CODE("""
              SELECT t.id, c.name
              FROM tickets AS t
              JOIN customers AS c ON c.id = t.customer_id;           -- INNER JOIN

              SELECT c.name, COUNT(t.id) AS n
              FROM customers AS c
              LEFT JOIN tickets AS t ON t.customer_id = c.id          -- keep customers with no tickets
              GROUP BY c.id;
          """, "sql"),
          UL("`INNER JOIN` (just `JOIN`) keeps only matching rows.", "`LEFT JOIN` keeps every left row; missing partners become NULL.", "Short aliases (`AS t`, `AS c`) keep queries readable."),
          TIP("To find rows **without** a partner (customers with no tickets): `LEFT JOIN`, then `WHERE t.id IS NULL`."),
          QUICK("Which join keeps customers who have no tickets?", ["INNER JOIN", "LEFT JOIN from customers", "LEFT JOIN from tickets", "CROSS JOIN"], 1, "A LEFT JOIN keeps every row from the table on its left, here `customers`."),
      ],
      [
          sql(D, "Show each ticket's `id` together with the customer's `name`. Tickets without a customer can be left out.", "-- JOIN ... ON\n", "SELECT t.id, c.name FROM tickets t JOIN customers c ON c.id = t.customer_id", ["Two tables are needed.", "Match `tickets.customer_id` with `customers.id`.", "`FROM tickets t JOIN customers c ON c.id = t.customer_id`"]),
          sql(D, "List **every** customer's `name` with their number of tickets as `n`, including customers with zero tickets.", "-- LEFT JOIN + GROUP BY\n", "SELECT c.name, COUNT(t.id) AS n FROM customers c LEFT JOIN tickets t ON t.customer_id = c.id GROUP BY c.id", ["Customers with no tickets must survive the join.", "Use `LEFT JOIN` from customers.", "`COUNT(t.id)` counts only real tickets, so it gives 0 for no match."], names=False, diff=3, tags=["interview"]),
          sql(D, "Which customers have never opened a ticket? Show their `name`.", "-- anti-join\n", "SELECT c.name FROM customers c LEFT JOIN tickets t ON t.customer_id = c.id WHERE t.id IS NULL", ["Start from a LEFT JOIN.", "A customer with no tickets gets NULLs on the ticket side.", "`WHERE t.id IS NULL`"], diff=3, tags=["interview"],
              explain=EXPLAIN("In your own words: why does `t.id IS NULL` find customers with no tickets?",
                              ["LEFT JOIN fills the ticket columns with NULL when nothing matches", "A real ticket always has a non-NULL id"],
                              "A left join keeps every customer. If none of their tickets match, all ticket columns come back as NULL. A real ticket has a non-null `id`, so `IS NULL` isolates the unmatched customers.")),
      ], phases=["data", "monitor"], minutes=6),

    C("sql.dml", 2, "Changing data: INSERT, UPDATE, DELETE",
      "Besides reading, SQL writes. The golden rule: always check your `WHERE` before you run an `UPDATE` or `DELETE`.",
      [
          CODE("""
              INSERT INTO customers (id, name, plan, country) VALUES (11, 'Kai Nowak', 'pro', 'PL');

              UPDATE tickets SET status = 'closed', resolved_at = '2026-09-19' WHERE id = 4;

              DELETE FROM tickets WHERE status = 'closed' AND priority = 1;
          """, "sql"),
          WARN("`UPDATE tickets SET status = 'closed'` **without** `WHERE` changes every row. Run the same condition as a `SELECT` first to see what will be touched."),
          UL("Constraints such as `PRIMARY KEY`, `NOT NULL` and `UNIQUE` make the database reject bad data.", "A **transaction** (`BEGIN` ... `COMMIT`) makes several changes succeed or fail together.", "In these exercises changes affect a throwaway copy of the data. A check query then reads the result."),
          QUICK("What happens with `DELETE FROM tickets;` (no `WHERE`)?", ["Nothing", "It deletes every row", "It deletes the table", "It deletes the first row"], 1, "All rows go. The table itself stays."),
      ],
      [
          sql(D, "Add a new customer: id `11`, name `Kai Nowak`, plan `pro`, country `PL`.", "-- INSERT INTO ... VALUES\n", "INSERT INTO customers (id, name, plan, country) VALUES (11, 'Kai Nowak', 'pro', 'PL')", ["Name the table and the columns.", "Then `VALUES (...)` in the same order.", "`INSERT INTO customers (id, name, plan, country) VALUES (11, 'Kai Nowak', 'pro', 'PL');`"],
              after="SELECT id, name, plan, country FROM customers WHERE id = 11"),
          sql(D, "Close ticket 4: set `status` to `closed` and `resolved_at` to `2026-09-19`.", "-- UPDATE ... SET ... WHERE\n", "UPDATE tickets SET status = 'closed', resolved_at = '2026-09-19' WHERE id = 4", ["Only one ticket should change.", "Set both columns separated by a comma.", "`UPDATE tickets SET status = 'closed', resolved_at = '2026-09-19' WHERE id = 4;`"],
              after="SELECT id, status, resolved_at FROM tickets WHERE id = 4", diff=2),
          sql(D, "Delete all tickets that are `closed` and have priority 1.", "-- DELETE ... WHERE\n", "DELETE FROM tickets WHERE status = 'closed' AND priority = 1", ["Both conditions must hold.", "A `DELETE` takes a `WHERE` just like a `SELECT`.", "`DELETE FROM tickets WHERE status = 'closed' AND priority = 1;`"],
              after="SELECT COUNT(*) FROM tickets", diff=2),
          spot("A teammate wants to close ticket 9 only, but this deletes the wrong data. Which line is the problem?", ["UPDATE tickets", "SET status = 'closed'", ";"], 2,
               ["Read what the statement actually targets.", "Which rows will it change?", "There is no `WHERE`, so every ticket changes."], lang="sql",
               fix=FIX("What is the fix?", ["Add `WHERE id = 9` before the semicolon", "Add `LIMIT 1` before the semicolon", "Replace `UPDATE` with `INSERT`", "Nothing, the statement is fine"], 0,
                       whys=[None, "`LIMIT` is not allowed in a standard `UPDATE` and does not say which row.", "`INSERT` adds rows; it cannot change existing ones.", "It would close every ticket."]), diff=2, tags=["interview"]),
      ], phases=["data", "serving"], minutes=5),
]
