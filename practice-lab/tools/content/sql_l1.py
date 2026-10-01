from dsl import *

TRACK = "sql"
D = "support"

CONCEPTS = [
    C("sql.select", 1, "SELECT: choosing columns",
      "A table is a grid of rows and named columns. `SELECT` picks which columns you want to see, and `FROM` says which table.",
      [
          P("The tables below are a small support-desk database, like the tickets ReviewRadar classifies. Open the **Tables you can query** box in any exercise to see them."),
          CODE("""
              SELECT name, country FROM customers;          -- two columns, every row

              SELECT id, words AS length FROM tickets;      -- AS gives a column a new name

              SELECT id, words / 200.0 AS minutes FROM tickets;   -- compute a value
          """, "sql"),
          UL("`SELECT *` means every column. Handy for a quick look, but name your columns in real code.", "Keywords are case-insensitive, but writing them in capitals makes queries easier to read.", "`--` starts a comment. End a statement with `;`."),
          WARN("`/` between two whole numbers does integer division in SQLite and Postgres: `7 / 2` is 3. Use `7 / 2.0` to get 3.5."),
          QUICK("Which query returns only the `plan` column of `customers`?", ["`SELECT plan FROM customers;`", "`SELECT customers FROM plan;`", "`FROM customers SELECT plan;`", "`SELECT * plan;`"], 0, "The pattern is `SELECT columns FROM table`."),
      ],
      [
          sql(D, "Show every customer's `name` and `country`.", "-- write your query\n", "SELECT name, country FROM customers", ["You need two columns from one table.", "List the columns after SELECT, separated by a comma.", "`SELECT name, country FROM customers;`"]),
          sql(D, "Show each ticket's `id` and its `words` renamed to `length`.", "-- use AS to rename\n", "SELECT id, words AS length FROM tickets", ["Two columns: `id` and `words`.", "`AS` renames a column in the result.", "`SELECT id, words AS length FROM tickets;`"], names=True, diff=2),
          sql(D, "For each ticket show its `id` and the reading time in minutes, named `minutes`, rounded to 2 decimals. Assume 200 words per minute.", "-- ROUND(value, 2)\n", "SELECT id, ROUND(words / 200.0, 2) AS minutes FROM tickets", ["Divide `words` by 200.", "Use `200.0` so the division keeps decimals.", "`SELECT id, ROUND(words / 200.0, 2) AS minutes FROM tickets;`"], names=True, diff=2),
      ], phases=["data", "monitor"], minutes=4),

    C("sql.where", 1, "WHERE: filtering rows",
      "`WHERE` keeps only the rows that satisfy a condition. Combine conditions with `AND`, `OR` and `NOT`.",
      [
          CODE("""
              SELECT id FROM tickets WHERE status = 'open' AND priority = 3;
              SELECT name FROM customers WHERE plan IN ('pro', 'enterprise');
              SELECT id FROM tickets WHERE words BETWEEN 20 AND 100;
              SELECT name FROM customers WHERE name LIKE 'A%';        -- starts with A
              SELECT id FROM tickets WHERE agent_id IS NULL;          -- no agent yet
          """, "sql"),
          TABLE(["Pattern", "Means"], [["`=` `<>` `<` `>=`", "compare (`<>` is not equal)"], ["`IN (a, b)`", "one of several values"], ["`LIKE 'x%'`", "`%` any text, `_` one character"], ["`IS NULL`", "the value is missing"]]),
          WARN("`NULL` means \"unknown\", so `x = NULL` is never true, even for NULL rows. Always write `IS NULL` or `IS NOT NULL`."),
          QUICK("Which clause correctly finds tickets that have not been resolved (`resolved_at` is missing)?", ["`WHERE resolved_at = NULL`", "`WHERE resolved_at IS NULL`", "`WHERE resolved_at = ''`", "`WHERE NOT resolved_at`"], 1, "Only `IS NULL` tests for a missing value."),
      ],
      [
          sql(D, "Find the `id` of every ticket that is `open` and has priority 3.", "-- WHERE with AND\n", "SELECT id FROM tickets WHERE status = 'open' AND priority = 3", ["Two conditions must both be true.", "Text values go in single quotes: `'open'`.", "`WHERE status = 'open' AND priority = 3`"]),
          sql(D, "List the `name` of every customer who is not on the `free` plan.", "-- not free\n", "SELECT name FROM customers WHERE plan <> 'free'", ["Use a comparison that means \"not equal\".", "`<>` or `!=`, or `IN ('pro', 'enterprise')`.", "`WHERE plan <> 'free'`"]),
          sql(D, "Which tickets have no agent assigned? Show their `id`.", "-- careful with NULL\n", "SELECT id FROM tickets WHERE agent_id IS NULL", ["The `agent_id` is missing (NULL) for these tickets.", "`= NULL` never matches.", "`WHERE agent_id IS NULL`"], diff=2, tags=["interview"]),
          mcq("What does `SELECT id FROM tickets WHERE resolved_at = NULL;` return?", ["The unresolved tickets", "All tickets", "No rows at all", "An error"], 2,
              ["Compare anything with NULL using `=`.", "The result is not true, it is unknown.", "`WHERE` keeps only rows where the condition is true."], diff=2, tags=["interview"],
              why="`resolved_at = NULL` evaluates to NULL (unknown) for every row, and `WHERE` keeps only rows that are true. Use `IS NULL`."),
      ], phases=["data"], minutes=4),

    C("sql.order", 1, "ORDER BY, LIMIT and DISTINCT",
      "Rows come back in no guaranteed order unless you ask. `ORDER BY` sorts, `LIMIT` trims, and `DISTINCT` removes repeats.",
      [
          CODE("""
              SELECT id, words FROM tickets ORDER BY words DESC LIMIT 3;     -- 3 longest
              SELECT DISTINCT category FROM tickets ORDER BY category;       -- unique values
              SELECT id FROM tickets ORDER BY priority DESC, created_at ASC; -- tie-breaker after the comma
          """, "sql"),
          UL("`ASC` is the default (smallest first); `DESC` is largest first.", "Sort by several columns: later ones only matter when earlier ones tie.", "`LIMIT n` keeps the first `n` rows, so it only makes sense after an `ORDER BY`."),
          WARN("Without `ORDER BY`, the database may return rows in any order and that order can change. Never rely on it."),
          QUICK("Which gives the 5 most recent tickets?", ["`ORDER BY created_at LIMIT 5`", "`ORDER BY created_at DESC LIMIT 5`", "`LIMIT 5 ORDER BY created_at`", "`SELECT DISTINCT 5`"], 1, "Newest first means descending date, then take 5."),
      ],
      [
          sql(D, "Show the `id` and `words` of the 3 longest tickets, longest first.", "-- ORDER BY ... DESC LIMIT\n", "SELECT id, words FROM tickets ORDER BY words DESC LIMIT 3", ["Sort by length first.", "`DESC` puts the biggest at the top.", "`ORDER BY words DESC LIMIT 3`"], ordered=True),
          sql(D, "List the distinct ticket categories in alphabetical order.", "-- DISTINCT + ORDER BY\n", "SELECT DISTINCT category FROM tickets ORDER BY category", ["You want each category once.", "`DISTINCT` removes duplicates.", "`SELECT DISTINCT category FROM tickets ORDER BY category`"], ordered=True),
          sql(D, "List every ticket `id`, highest priority first. For tickets with the same priority, oldest `created_at` first.", "-- two sort keys\n", "SELECT id FROM tickets ORDER BY priority DESC, created_at ASC", ["Sort by priority, then break ties.", "Separate the sort keys with a comma.", "`ORDER BY priority DESC, created_at ASC`"], ordered=True, diff=2),
      ], phases=["data", "monitor"], minutes=4),
]
