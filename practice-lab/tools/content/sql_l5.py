from dsl import *

TRACK = "sql"
D = "support"

CONCEPTS = [
    C("sql.index", 5, "Indexes and reading query plans",
      "An index is a sorted lookup structure. It turns a scan of every row into a few steps, at the cost of extra storage and slower writes.",
      [
          VIZ("search", title="Scan vs index", n=16),
          CODE("""
              CREATE INDEX idx_tickets_customer ON tickets(customer_id);

              EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE customer_id = 3;
              -- SQLite:  SEARCH tickets USING INDEX idx_tickets_customer (customer_id=?)   <- index used
              --          SCAN tickets                                                       <- every row read
              -- PostgreSQL: EXPLAIN ANALYZE ...   shows "Index Scan" or "Seq Scan" with real timings
          """, "sql"),
          UL("Index the columns you filter, join and sort on, mainly foreign keys such as `customer_id`.", "A **composite** index `(a, b)` helps queries on `a` or on `a` and `b`, but not on `b` alone (leftmost prefix rule).", "Every index slows `INSERT`/`UPDATE`/`DELETE` and uses disk. Do not index everything."),
          WARN("The planner may ignore an index on a tiny table or a column where most rows match. Always read the plan instead of guessing."),
          QUICK("Which plan line means the database used an index?", ["`SCAN tickets`", "`SEARCH tickets USING INDEX ...`", "`USE TEMP B-TREE`", "`SCAN CONSTANT ROW`"], 1, "SCAN reads every row; SEARCH ... USING INDEX jumps straight to matches."),
      ],
      [
          sql(D, "Create an index named `idx_tickets_customer` on the `customer_id` column of `tickets`.", "-- CREATE INDEX name ON table(column)\n", "CREATE INDEX idx_tickets_customer ON tickets(customer_id)", ["Name the index, then the table and column.", "`CREATE INDEX <name> ON <table>(<column>)`", "`CREATE INDEX idx_tickets_customer ON tickets(customer_id);`"], after="SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'idx_tickets_customer'"),
          mcq("There is a composite index on `tickets(customer_id, created_at)`. Which queries can use it efficiently? (Select all that apply.)", ["`WHERE customer_id = 3`", "`WHERE created_at = '2026-09-01'`", "`WHERE customer_id = 3 AND created_at > '2026-09-05'`", "`WHERE status = 'open'`"], [0, 2],
              ["An index is sorted by the first column, then the second within it.", "You must be able to use the **leftmost** column.", "Queries 1 and 3 start with `customer_id`."], diff=3, tags=["interview"],
              explain=EXPLAIN("In your own words: why can't a query on only `created_at` use that index well?",
                              ["The index is sorted by customer_id first", "Matching created_at values are scattered across the whole index"],
                              "The index is ordered by `customer_id` and only then by `created_at`. Rows with the same date are spread out through the index, so it cannot jump to them; it would have to scan everything.")),
          mcq("What is the main cost of adding many indexes to a table?", ["Reads become slower", "Writes become slower and storage grows", "Queries return wrong results", "The primary key changes"], 1,
              ["Think about what must happen on every `INSERT`.", "Each index also has to be updated.", "More structures to maintain."], diff=2),
      ], phases=["monitor", "serving"], minutes=6),

    C("sql.plans", 5, "Slow-query patterns",
      "Most slow queries come from a handful of patterns. Spotting them is a core skill for anyone who owns a database behind an API.",
      [
          CODE("""
              -- 1. A function on the column hides it from the index
              SELECT * FROM customers WHERE LOWER(name) = 'ana ruiz';       -- cannot use an index on name
              -- fix: store normalised data, or create an index ON customers(LOWER(name)) in PostgreSQL

              -- 2. Leading wildcard
              SELECT * FROM customers WHERE name LIKE 'Ana%';    -- can use an index
              SELECT * FROM customers WHERE name LIKE '%Ruiz';   -- must scan everything

              -- 3. N+1 queries: one query for tickets, then one per ticket for its customer.
              --    Fix: one JOIN.
          """, "sql"),
          UL("**SELECT \\*** pulls columns you do not need and defeats covering indexes.", "**OFFSET pagination** gets slower on later pages. Use keyset pagination: `WHERE id > :last_id ORDER BY id LIMIT 20`.", "In PostgreSQL, `EXPLAIN ANALYZE` actually runs the query and shows real timings."),
          QUICK("Which `LIKE` can use an ordinary index on `name`?", ["`LIKE '%son'`", "`LIKE '%son%'`", "`LIKE 'Joh%'`", "None of them"], 2, "A fixed prefix lets the database jump into the sorted index."),
      ],
      [
          spot("This query is slow even though `customers.name` is indexed. Which line is the problem?", ["SELECT id", "FROM customers", "WHERE LOWER(name) = 'ana ruiz';"], 3,
               ["Look at what the `WHERE` does to the indexed column.", "The index stores `name`, not `LOWER(name)`.", "Wrapping the column in a function hides it from the index."], lang="sql",
               fix=FIX("What is the best fix?", ["Compare the raw column, or create an expression index on `LOWER(name)`", "Add `LIMIT 1`", "Replace `FROM` with `JOIN`", "Use `SELECT *`"], 0), diff=3, tags=["interview"]),
          mcq("A page loads 50 tickets with one query, then runs 50 more queries to fetch each ticket's customer. What is this called and how do you fix it?", ["N+1; fetch customers with a single JOIN", "Deadlock; add an index", "Dirty read; use a transaction", "Normalisation; split the table"], 0,
              ["One query plus N more queries.", "Databases are good at combining tables.", "A JOIN (or `IN`) fetches everything at once."], diff=3, tags=["interview"]),
          fill("Ask PostgreSQL to run the query and report real timings.", "EXPLAIN ____ SELECT * FROM tickets WHERE customer_id = 3;", ["ANALYZE"], ["Plain `EXPLAIN` only estimates.", "A keyword makes it execute the query as well.", "`ANALYZE`"], lang="sql", ci=True),
      ], phases=["serving", "monitor"], minutes=6),

    C("sql.pgvector", 5, "pgvector: similarity search in Postgres",
      "An embedding turns text into a list of numbers so that similar meanings sit close together. pgvector stores those vectors in Postgres and finds the nearest ones.",
      [
          CODE("""
              CREATE EXTENSION IF NOT EXISTS vector;

              CREATE TABLE docs (
                  id bigserial PRIMARY KEY,
                  body text,
                  embedding vector(384)          -- one 384-number embedding per row
              );

              -- the 5 most similar documents to a query vector
              SELECT id, body
              FROM docs
              ORDER BY embedding <=> '[0.12, 0.03, ...]'
              LIMIT 5;

              CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops);   -- approximate, fast
          """, "sql"),
          TABLE(["Operator", "Distance"], [["`<->`", "Euclidean (L2)"], ["`<=>`", "cosine distance"], ["`<#>`", "negative inner product"]]),
          UL("Smaller distance means more similar. Sort ascending and take `LIMIT k`.", "Without an index this is an **exact** scan of every row. `HNSW` and `IVFFlat` indexes are **approximate**: much faster, with a small chance of missing the true nearest neighbour.", "You can combine vector search with normal filters (`WHERE customer_id = 3`) and joins. That is the retrieval step of RAG."),
          P("Cosine distance is `1 - (a . b) / (|a| |b|)`. It ignores the length of the vectors and compares only direction. You can write the exact search yourself in a few lines, and the exercises do."),
          QUICK("A vector index of type HNSW gives you:", ["Exact results, slower", "Faster approximate nearest neighbours", "Compression of the text", "Automatic embeddings"], 1, "It trades a little recall for a big speed-up."),
      ],
      [
          fill("Complete the vector search.", "CREATE TABLE docs (id bigserial PRIMARY KEY, body text, embedding ____(384));\n\nSELECT id, body FROM docs\nORDER BY embedding ____ '[0.12, 0.03, 0.88]'\nLIMIT 5;", ["vector", ["<=>", "<->"]], ["The column type comes from the extension and takes the dimension in brackets.", "For cosine distance the operator is a symbol with `=` in the middle.", "`vector` and `<=>`."], lang="sql", diff=2),
          code("Write `cosine_distance(a, b)` for two equal-length lists of numbers: `1 - dot(a, b) / (|a| * |b|)`.",
               "def cosine_distance(a, b):\n    pass\n", """
              def cosine_distance(a, b):
                  dot = sum(x * y for x, y in zip(a, b))
                  na = sum(x * x for x in a) ** 0.5
                  nb = sum(y * y for y in b) ** 0.5
                  return 1 - dot / (na * nb)
          """, """
              t("cosine_distance([1, 0], [1, 0])", 0.0)
              t("cosine_distance([1, 0], [0, 1])", 1.0)
              t("cosine_distance([1, 0], [-1, 0])", 2.0)
              t("round(cosine_distance([1, 2, 3], [2, 4, 6]), 9)", 0.0)
          """, ["The dot product is the sum of pairwise products.", "A vector's length is the square root of the sum of its squares.", "`1 - dot / (na * nb)`"], diff=3, tags=["interview"]),
          code("Write `nearest(query, items, k)` where `items` is a dict from id to vector. Return the ids of the `k` items closest to `query` by cosine distance, closest first. (This is what `ORDER BY embedding <=> query LIMIT k` does.)",
               "def nearest(query, items, k):\n    pass\n", """
              def cosine_distance(a, b):
                  dot = sum(x * y for x, y in zip(a, b))
                  na = sum(x * x for x in a) ** 0.5
                  nb = sum(y * y for y in b) ** 0.5
                  return 1 - dot / (na * nb)

              def nearest(query, items, k):
                  return sorted(items, key=lambda i: cosine_distance(query, items[i]))[:k]
          """, """
              docs = {"refund": [1.0, 0.1], "login": [0.0, 1.0], "billing": [0.9, 0.3], "crash": [0.1, 0.9]}
              t("nearest([1, 0], docs, 2)", ["refund", "billing"])
              t("nearest([0, 1], docs, 1)", ["login"])
              t("nearest([0.5, 0.5], docs, 4)[0] in ('billing', 'crash')", True)
          """, ["Compute a distance from the query to every item.", "Sort the ids by that distance and slice the first `k`.", "`sorted(items, key=lambda i: cosine_distance(query, items[i]))[:k]`"], diff=3, tags=["interview"]),
      ], phases=["deep", "serving"], minutes=7),
]
