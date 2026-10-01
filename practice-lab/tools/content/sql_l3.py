from dsl import *

TRACK = "sql"
D = "support"

CONCEPTS = [
    C("sql.subq", 3, "Subqueries",
      "A query can sit inside another. A subquery computes a value or a list of values that the outer query then uses.",
      [
          CODE("""
              -- scalar subquery: one value
              SELECT id, words FROM tickets
              WHERE words > (SELECT AVG(words) FROM tickets);

              -- IN: a list of values
              SELECT name FROM customers
              WHERE id IN (SELECT customer_id FROM tickets WHERE status = 'open');

              -- EXISTS: is there at least one matching row?
              SELECT name FROM customers c
              WHERE NOT EXISTS (SELECT 1 FROM tickets t WHERE t.customer_id = c.id);
          """, "sql"),
          UL("A subquery in parentheses can return **one value**, **a column** (for `IN`) or **a table** (in `FROM`).", "A **correlated** subquery refers to the outer row (`c.id` above) and is re-evaluated per row.", "`EXISTS` stops at the first match, so it is often faster than `IN` for big tables."),
          WARN("`x NOT IN (subquery)` returns **no rows at all** if the subquery produces even one `NULL`. Prefer `NOT EXISTS`."),
          QUICK("Which keyword asks whether a subquery returns at least one row?", ["`ANY`", "`EXISTS`", "`HAVING`", "`DISTINCT`"], 1, "`EXISTS (subquery)` is true when the subquery finds a row."),
      ],
      [
          sql(D, "Show the `id` and `words` of every ticket longer than the average ticket.", "-- WHERE words > (subquery)\n", "SELECT id, words FROM tickets WHERE words > (SELECT AVG(words) FROM tickets)", ["First you need the average length as a single number.", "Put that query in parentheses inside the `WHERE`.", "`WHERE words > (SELECT AVG(words) FROM tickets)`"]),
          sql(D, "Show the `name` of every customer who has at least one **open** ticket.", "-- IN or EXISTS\n", "SELECT name FROM customers WHERE id IN (SELECT customer_id FROM tickets WHERE status = 'open')", ["Find the customer ids of open tickets first.", "Then keep customers whose id is in that list.", "`WHERE id IN (SELECT customer_id FROM tickets WHERE status = 'open')`"], diff=2),
          sql(D, "Using `NOT EXISTS`, show the `name` of customers who have never opened a ticket.", "-- correlated subquery\n", "SELECT name FROM customers c WHERE NOT EXISTS (SELECT 1 FROM tickets t WHERE t.customer_id = c.id)", ["The subquery must look at the current customer.", "Compare `t.customer_id` with `c.id` inside it.", "`WHERE NOT EXISTS (SELECT 1 FROM tickets t WHERE t.customer_id = c.id)`"], diff=3),
          mcq("`SELECT name FROM customers WHERE id NOT IN (SELECT customer_id FROM tickets);` What does it return here? (One ticket has no customer, so its `customer_id` is NULL.)", ["Customers with no tickets", "No rows at all", "All customers", "An error"], 1,
              ["`id NOT IN (1, 2, NULL)` can never be true.", "Comparing with NULL gives unknown.", "The `NULL` in the list poisons the whole test."], diff=3, tags=["interview"],
              why="`NOT IN` with a NULL in the list evaluates to unknown for every row, so nothing passes the filter. `NOT EXISTS` (or filtering the NULL out of the subquery) avoids it.",
              explain=EXPLAIN("In your own words: why does the NULL break NOT IN?",
                              ["NOT IN means not equal to any value in the list", "Comparing with NULL is unknown, so the test is never true"],
                              "`id NOT IN (a, b, NULL)` expands to `id <> a AND id <> b AND id <> NULL`. The last part is unknown, so the whole condition can never be true.")),
      ], phases=["data", "monitor"], minutes=6),

    C("sql.cte", 3, "CTEs: WITH clauses",
      "A common table expression gives a subquery a name so the query reads top to bottom, one idea per step.",
      [
          CODE("""
              WITH open_t AS (
                  SELECT * FROM tickets WHERE status = 'open'
              ),
              per_cat AS (
                  SELECT category, COUNT(*) AS n FROM open_t GROUP BY category
              )
              SELECT category, n FROM per_cat WHERE n >= 2;
          """, "sql"),
          UL("`WITH name AS (...)` defines a temporary table that exists only for this statement.", "Chain several CTEs with commas. A later CTE can use an earlier one.", "CTEs are for **readability**. The planner treats them much like subqueries."),
          TIP("Write complicated queries as a series of small named steps and test each step by selecting from it."),
          QUICK("A CTE lives:", ["Forever, like a table", "For the one statement that defines it", "Until the connection closes", "Only inside `HAVING`"], 1, "It is a named subquery for a single statement."),
      ],
      [
          sql(D, "Use a CTE named `open_t` holding the open tickets. Then count them per category: show `category` and `n`.", "-- WITH open_t AS (...)\n", "WITH open_t AS (SELECT * FROM tickets WHERE status = 'open') SELECT category, COUNT(*) AS n FROM open_t GROUP BY category", ["Define the CTE first, then select from it.", "Filter inside the CTE, group outside.", "`WITH open_t AS (SELECT * FROM tickets WHERE status = 'open') SELECT category, COUNT(*) AS n FROM open_t GROUP BY category`"], names=True),
          sql(D, "Show the `category` of every category whose average `words` is above the average of all tickets. Use two CTEs.", "-- per_cat and overall\n", "WITH per_cat AS (SELECT category, AVG(words) AS a FROM tickets GROUP BY category), overall AS (SELECT AVG(words) AS a FROM tickets) SELECT per_cat.category FROM per_cat, overall WHERE per_cat.a > overall.a", ["One CTE for each category's average, one for the overall average.", "The overall CTE has a single row, so you can join it to every category.", "`FROM per_cat, overall WHERE per_cat.a > overall.a`"], diff=3, tags=["interview"]),
          sql(D, "Show the `name` and ticket count `n` of customers who have **more tickets than the average customer** (average over customers who have at least one ticket). Ignore tickets with no customer.", "-- count per customer in a CTE\n", "WITH per_c AS (SELECT customer_id, COUNT(*) AS n FROM tickets WHERE customer_id IS NOT NULL GROUP BY customer_id) SELECT c.name, p.n FROM per_c p JOIN customers c ON c.id = p.customer_id WHERE p.n > (SELECT AVG(n) FROM per_c)", ["Count tickets per customer id first.", "Then compare each count to `(SELECT AVG(n) FROM per_c)`.", "Join to `customers` at the end to get the names."], diff=3, tags=["interview"]),
          order("Put the lines in order to build a query that lists the categories having at least 3 open tickets.",
                ["WITH open_t AS (", "    SELECT * FROM tickets WHERE status = 'open'", ")", "SELECT category, COUNT(*) AS n", "FROM open_t", "GROUP BY category", "HAVING COUNT(*) >= 3;"],
                ["A `WITH` block must come before the main `SELECT`.", "The CTE body is inside the brackets.", "`HAVING` comes after `GROUP BY`."], lang="sql", diff=2),
      ], phases=["data", "monitor"], minutes=6),

    C("sql.case", 3, "CASE, COALESCE, NULLs and dates",
      "`CASE` is SQL's if/else. `COALESCE` replaces missing values. Both appear in nearly every real query.",
      [
          CODE("""
              SELECT id,
                     CASE WHEN words < 20 THEN 'short'
                          WHEN words < 100 THEN 'medium'
                          ELSE 'long' END AS size
              FROM tickets;

              SELECT t.id, COALESCE(a.name, 'unassigned') AS agent
              FROM tickets t LEFT JOIN agents a ON a.id = t.agent_id;

              -- days between two dates (SQLite). In PostgreSQL: resolved_at - created_at
              SELECT id, CAST(julianday(resolved_at) - julianday(created_at) AS INTEGER) AS days
              FROM tickets WHERE resolved_at IS NOT NULL;
          """, "sql"),
          UL("`CASE` checks `WHEN` branches top to bottom and uses the first that is true.", "`COALESCE(a, b, c)` returns the first value that is not NULL.", "Aggregates such as `AVG` and `SUM` **ignore NULLs**. `COUNT(*)` counts rows, `COUNT(col)` counts non-NULLs.", "Anything + NULL is NULL. Any comparison with NULL is unknown."),
          WARN("Date functions differ between databases: `julianday`/`strftime` in SQLite, `date_trunc` and date subtraction in PostgreSQL. The ideas carry over; the function names do not."),
          QUICK("What is `COALESCE(NULL, NULL, 3, 4)`?", ["NULL", "3", "4", "7"], 1, "It returns the first non-NULL argument."),
      ],
      [
          sql(D, "Label each ticket by length: show `id` and `size`, where `size` is `short` (under 20 words), `medium` (under 100) or `long`.", "-- CASE WHEN\n", "SELECT id, CASE WHEN words < 20 THEN 'short' WHEN words < 100 THEN 'medium' ELSE 'long' END AS size FROM tickets", ["`CASE` goes in the select list.", "Check the smallest range first.", "`CASE WHEN words < 20 THEN 'short' WHEN words < 100 THEN 'medium' ELSE 'long' END AS size`"], names=True, diff=2),
          sql(D, "For resolved tickets show `id` and the whole number of days between `created_at` and `resolved_at`, named `days`. (In SQLite use `julianday(...)`.)", "-- julianday(date) gives a day number\n", "SELECT id, CAST(julianday(resolved_at) - julianday(created_at) AS INTEGER) AS days FROM tickets WHERE resolved_at IS NOT NULL", ["Subtract the two day numbers.", "Only tickets with a `resolved_at` qualify.", "`CAST(julianday(resolved_at) - julianday(created_at) AS INTEGER) AS days`"], names=True, diff=3),
          sql(D, "Show every ticket `id` and its agent's name as `agent`. Use `unassigned` when there is no agent.", "-- LEFT JOIN + COALESCE\n", "SELECT t.id, COALESCE(a.name, 'unassigned') AS agent FROM tickets t LEFT JOIN agents a ON a.id = t.agent_id", ["Unassigned tickets must not disappear.", "A LEFT JOIN gives NULL when there is no agent.", "`COALESCE(a.name, 'unassigned') AS agent`"], names=True, diff=3),
          mcq("A column holds the values 2, NULL, 4. What does `AVG(col)` return?", ["2", "3", "NULL", "1.5"], 1,
              ["Do aggregates count the NULL?", "`AVG` ignores NULLs: (2 + 4) / 2.", "If NULL counted as 0 it would be 2, but it is skipped."], diff=2, tags=["interview"]),
      ], phases=["data", "monitor"], minutes=6),

    C("sql.setops", 3, "Set operations and self-joins",
      "Stack results with `UNION`, compare them with `INTERSECT` and `EXCEPT`, or join a table to itself to compare its own rows.",
      [
          CODE("""
              -- customers with BOTH an open and a closed ticket
              SELECT customer_id FROM tickets WHERE status = 'open'
              INTERSECT
              SELECT customer_id FROM tickets WHERE status = 'closed';

              -- combos in open tickets that never appear in closed ones
              SELECT category, priority FROM tickets WHERE status = 'open'
              EXCEPT
              SELECT category, priority FROM tickets WHERE status = 'closed';

              -- self-join: pairs of tickets from the same customer
              SELECT a.id AS a_id, b.id AS b_id
              FROM tickets a JOIN tickets b ON a.customer_id = b.customer_id AND a.id < b.id;
          """, "sql"),
          UL("`UNION` removes duplicates; `UNION ALL` keeps them and is faster.", "Both queries must return the same number of columns with compatible types.", "A self-join needs two **aliases** for the same table. `a.id < b.id` stops each pair appearing twice and a row pairing with itself."),
          QUICK("Which keeps duplicate rows?", ["`UNION`", "`UNION ALL`", "`INTERSECT`", "`EXCEPT`"], 1, "`UNION` de-duplicates; `UNION ALL` does not."),
      ],
      [
          sql(D, "Show the `name` of customers who have both an open ticket and a closed ticket.", "-- INTERSECT or two IN tests\n", "SELECT name FROM customers WHERE id IN (SELECT customer_id FROM tickets WHERE status = 'open') AND id IN (SELECT customer_id FROM tickets WHERE status = 'closed')", ["You need the customers who appear in both groups.", "Two `IN` tests joined with `AND` work, or `INTERSECT` on ids.", "`WHERE id IN (open ids) AND id IN (closed ids)`"], diff=3),
          sql(D, "Which `category` and `priority` combinations occur in open tickets but never in closed tickets?", "-- EXCEPT\n", "SELECT category, priority FROM tickets WHERE status = 'open' EXCEPT SELECT category, priority FROM tickets WHERE status = 'closed'", ["Take the open combinations, then remove the closed ones.", "`EXCEPT` subtracts the second result from the first.", "`SELECT ... WHERE status = 'open' EXCEPT SELECT ... WHERE status = 'closed'`"], diff=3),
          sql(D, "List every pair of tickets raised by the same customer. Show `a_id` and `b_id` with `a_id` smaller than `b_id`, so each pair appears once.", "-- join tickets to tickets\n", "SELECT a.id AS a_id, b.id AS b_id FROM tickets a JOIN tickets b ON a.customer_id = b.customer_id AND a.id < b.id", ["Use the `tickets` table twice with different aliases.", "Match on `customer_id`.", "`a.id < b.id` removes duplicates."], names=True, diff=3, tags=["interview"]),
          mcq("You combine two result sets that overlap and want to keep every row, including duplicates. Which should you use?", ["`UNION`", "`UNION ALL`", "`INTERSECT`", "`JOIN`"], 1,
              ["One of them removes duplicates by sorting or hashing.", "The other just appends.", "`UNION ALL`."], diff=2),
      ], phases=["data", "monitor"], minutes=6),
]
