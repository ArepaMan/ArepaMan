from dsl import *

TRACK = "python"

CONCEPTS = [
    C("py.torch4", 5, "Datasets, DataLoaders and batching",
      "A DataLoader turns a pile of examples into shuffled batches of equal shape. Getting batching and padding right avoids both bugs and slow training.",
      [
          CODE("""
              from torch.utils.data import Dataset, DataLoader

              class TicketDataset(Dataset):
                  def __init__(self, texts, labels):
                      self.texts, self.labels = texts, labels
                  def __len__(self):                 # how many examples
                      return len(self.texts)
                  def __getitem__(self, i):          # one example by index
                      return self.texts[i], self.labels[i]

              train_loader = DataLoader(TicketDataset(X_train, y_train),
                                        batch_size=32, shuffle=True, collate_fn=collate)
              val_loader = DataLoader(TicketDataset(X_val, y_val), batch_size=64)   # no shuffle needed
          """),
          UL("A `Dataset` needs `__len__` and `__getitem__`. A `DataLoader` handles batching, shuffling and parallel loading.", "`shuffle=True` for training only. `drop_last=True` discards a final smaller batch (useful with batch norm).", "`collate_fn` builds one batch from a list of examples. For text it pads sequences to the longest in the batch and builds the attention mask.", "Sorting by length into buckets (**length bucketing**) cuts wasted padding and speeds up training."),
          WARN("Do not shuffle the validation set for any reason other than convenience, and never fit preprocessing (tokenizer vocabulary, scalers) on validation or test data."),
          QUICK("10 examples, `batch_size=4`, `drop_last=False`. How many batches does the loader produce?", ["2", "3", "4", "10"], 1, "4 + 4 + 2: three batches, the last one smaller."),
      ],
      [
          code("Write a generator `batches(items, size, drop_last=False)` that yields consecutive lists of `size` items. When `drop_last` is true, skip a final shorter batch.",
               "def batches(items, size, drop_last=False):\n    pass\n", """
              def batches(items, size, drop_last=False):
                  for i in range(0, len(items), size):
                      b = items[i:i + size]
                      if drop_last and len(b) < size:
                          return
                      yield b
          """, """
              t("list(batches(list(range(1, 11)), 4))", [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]])
              t("list(batches(list(range(1, 11)), 4, drop_last=True))", [[1, 2, 3, 4], [5, 6, 7, 8]])
              t("list(batches([1, 2], 5))", [[1, 2]])
              t("list(batches([], 3))", [])
          """, ["Step through the list in jumps of `size`.", "Slice `items[i:i + size]` for each batch.", "If `drop_last` and the slice is short, stop."], diff=2),
          code("Write `collate(batch, pad_id=0)` for a batch of `(token_ids, label)` pairs. Return a dict with `input_ids` (each list padded on the right to the longest), `attention_mask` (1 for real tokens, 0 for padding) and `labels`.",
               "def collate(batch, pad_id=0):\n    pass\n", """
              def collate(batch, pad_id=0):
                  longest = max(len(ids) for ids, _ in batch)
                  return {
                      "input_ids": [ids + [pad_id] * (longest - len(ids)) for ids, _ in batch],
                      "attention_mask": [[1] * len(ids) + [0] * (longest - len(ids)) for ids, _ in batch],
                      "labels": [label for _, label in batch],
                  }
          """, """
              t("collate([([5, 6, 7], 1), ([8], 0)])", {"input_ids": [[5, 6, 7], [8, 0, 0]], "attention_mask": [[1, 1, 1], [1, 0, 0]], "labels": [1, 0]})
              t("collate([([1, 2], 3)], pad_id=9)", {"input_ids": [[1, 2]], "attention_mask": [[1, 1]], "labels": [3]})
          """, ["Find the longest sequence in the batch.", "Pad each list and build a matching mask.", "Collect the labels in a separate list."], diff=3, tags=["interview"]),
          predict("What does this print? (How many batches, and how many items are in the last one?)", """
              import math
              n, bs = 10, 4
              print(math.ceil(n / bs), n % bs or bs)
          """, "3 2", ["10 items in groups of 4.", "Two full batches, then what is left.", "`10 % 4` is 2."], diff=2),
          spot("Training accuracy oscillates strangely. The training data is stored sorted by label. Which line is the problem?", ["train_loader = DataLoader(train_ds, batch_size=32)", "val_loader = DataLoader(val_ds, batch_size=64)"], 1,
               ["What order do the training batches arrive in?", "Sorted data gives batches full of a single class.", "The training loader is missing an argument."], lang="python",
               fix=FIX("What is the fix?", ["Add `shuffle=True` to the training loader", "Add `shuffle=True` to the validation loader", "Use `batch_size=1`", "Set `drop_last=True` on both"], 0), diff=2, tags=["interview"]),
      ], phases=["deep"], minutes=6),

    C("py.torch5", 5, "Fine-tuning: schedules, early stopping and overfitting",
      "Most fine-tuning skill is knowing what the curves mean and which two or three knobs to turn.",
      [
          CODE("""
              # freeze the pretrained body, train only the new head
              for p in model.base.parameters():
                  p.requires_grad = False

              # keep gradients from exploding
              torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

              # learning rate: warm up, then decay
              #   lr rises linearly to base_lr over `warmup` steps, then falls linearly to 0 at `total`
          """),
          TABLE(["Curves", "Diagnosis", "Try"], [["train loss and val loss both high", "underfitting", "train longer, bigger model, higher learning rate"], ["train loss falling, val loss rising", "overfitting", "more data, augmentation, dropout or weight decay, early stopping"], ["loss jumps to NaN", "exploding gradients or learning rate too high", "lower the learning rate, clip gradients"], ["val loss noisy", "small validation set or high learning rate", "bigger validation set, lower learning rate"]]),
          UL("**Early stopping** stops when validation loss has not improved for `patience` epochs and keeps the best checkpoint.", "**Warmup** avoids huge early updates on pretrained weights. Transformers are usually fine-tuned with a small learning rate (about 2e-5) and a warmup.", "Freeze layers when you have little data. Unfreeze later with a smaller learning rate."),
          QUICK("Training loss keeps dropping but validation loss started rising after epoch 3. This is:", ["Underfitting", "Overfitting", "A bug in the loader", "Normal at any point"], 1, "The model memorises the training set and generalises worse."),
      ],
      [
          code("Write `early_stop_epoch(val_losses, patience)` returning the index of the epoch at which training would stop: the first epoch where `patience` epochs in a row have failed to beat the best validation loss so far. Return `None` if it never stops.",
               "def early_stop_epoch(val_losses, patience):\n    pass\n", """
              def early_stop_epoch(val_losses, patience):
                  best = float("inf")
                  since = 0
                  for i, v in enumerate(val_losses):
                      if v < best:
                          best = v
                          since = 0
                      else:
                          since += 1
                          if since >= patience:
                              return i
                  return None
          """, """
              t("early_stop_epoch([1.0, 0.8, 0.7, 0.71, 0.72, 0.73], 3)", 5)
              t("early_stop_epoch([1.0, 0.9, 0.8], 3)", None)
              t("early_stop_epoch([1.0, 1.1, 1.2, 0.5, 0.6], 2)", 2)
              t("early_stop_epoch([1.0, 1.1, 0.9, 1.0, 1.1], 2)", 4)
          """, ["Track the best loss so far and how many epochs since it improved.", "A new best resets the counter to zero.", "Return the current index when the counter reaches `patience`."], diff=3, tags=["interview"]),
          code("Write `warmup_linear(step, warmup, total, base_lr)`: the learning rate rises linearly from 0 to `base_lr` over `warmup` steps, then falls linearly to 0 at step `total` (and stays 0 after).",
               "def warmup_linear(step, warmup, total, base_lr):\n    pass\n", """
              def warmup_linear(step, warmup, total, base_lr):
                  if step < warmup:
                      return base_lr * step / warmup
                  return base_lr * max(0.0, (total - step) / (total - warmup))
          """, """
              t("warmup_linear(0, 10, 100, 1.0)", 0.0)
              t("warmup_linear(5, 10, 100, 1.0)", 0.5)
              t("warmup_linear(10, 10, 100, 1.0)", 1.0)
              t("warmup_linear(55, 10, 100, 1.0)", 0.5)
              t("warmup_linear(100, 10, 100, 1.0)", 0.0)
              t("warmup_linear(150, 10, 100, 1.0)", 0.0)
          """, ["Two phases: before and after `warmup`.", "Phase 1 is a straight line up: `base_lr * step / warmup`.", "Phase 2 is a straight line down to zero at `total`."], diff=3),
          fill("Freeze the pretrained layers and clip gradients to a maximum norm of 1.0.", "for p in model.base.parameters():\n    p.requires_grad = ____\ntorch.nn.utils.clip_grad_norm_(model.parameters(), ____)", [["False"], ["1.0", "1"]], ["Freezing means gradients are not computed.", "The second value is the maximum allowed gradient norm.", "`False` and `1.0`."], lang="python", diff=2),
          mcq("Training loss: 0.9, 0.5, 0.3, 0.15, 0.08. Validation loss: 0.95, 0.6, 0.55, 0.62, 0.7. What do you do?", ["Train much longer", "Stop around epoch 3 (early stopping) and consider regularisation or more data", "Raise the learning rate", "Delete the validation set"], 1,
              ["Compare the two curves after epoch 3.", "Validation got worse while training got better.", "That is overfitting."], diff=2, tags=["interview"]),
      ], phases=["deep"], minutes=6),

    C("py.rag", 5, "RAG building blocks: chunking, retrieval and evaluation",
      "Retrieval-augmented generation answers from your documents: split them, embed the pieces, retrieve the closest, and give them to the model. Each step can be measured.",
      [
          CODE("""
              chunks = chunk_text(doc, size=200, overlap=40)        # 1. split into overlapping pieces
              vectors = embed(chunks)                                # 2. embeddings, stored in pgvector
              hits = nearest(embed(question), vectors, k=5)          # 3. retrieve the closest pieces
              prompt = "Answer using only this context:\\n" + "\\n".join(hits) + "\\n\\nQuestion: " + question
              answer = llm(prompt)                                   # 4. generate
          """),
          UL("**Chunk size**: small chunks are precise but lose context; big chunks carry context but dilute the match. **Overlap** keeps sentences from being cut off.", "Evaluate retrieval separately from generation: if the right passage was never retrieved, no prompt can fix the answer.", "**recall@k**: the share of relevant passages that appear in the top k. **MRR**: the average of 1 / (rank of the first correct result)."),
          WARN("A fluent answer is not a correct answer. Check that the cited chunk really contains the claim, and test questions the documents cannot answer."),
          QUICK("The right passage is retrieved at rank 4, but the model's answer is wrong. Where do you look first?", ["The embedding model", "The prompt and generation step (retrieval worked)", "The chunk size", "The database index"], 1, "Retrieval found the passage, so the problem is how it is used."),
      ],
      [
          code("Write `chunk_text(text, size, overlap)` that splits `text` into word chunks of `size` words, each starting `size - overlap` words after the previous one. The last chunk may be shorter. Return a list of strings joined by single spaces.",
               "def chunk_text(text, size, overlap):\n    pass\n", """
              def chunk_text(text, size, overlap):
                  words = text.split()
                  step = size - overlap
                  chunks = []
                  for start in range(0, len(words), step):
                      chunks.append(" ".join(words[start:start + size]))
                      if start + size >= len(words):
                          break
                  return chunks
          """, """
              t("chunk_text('a b c d e f g', 3, 1)", ["a b c", "c d e", "e f g"])
              t("chunk_text('a b c d e f', 3, 1)", ["a b c", "c d e", "e f"])
              t("chunk_text('a b c', 3, 1)", ["a b c"])
              t("chunk_text('x y', 5, 1)", ["x y"])
          """, ["Work with words, not characters.", "Each chunk starts `size - overlap` words after the previous start.", "Stop once a chunk reaches the end of the text."], diff=3, tags=["interview"]),
          code("Write `recall_at_k(retrieved, relevant, k)`: the fraction of the `relevant` ids that appear in the first `k` of `retrieved`. If `relevant` is empty, return 0.0.",
               "def recall_at_k(retrieved, relevant, k):\n    pass\n", """
              def recall_at_k(retrieved, relevant, k):
                  if not relevant:
                      return 0.0
                  return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))
          """, """
              t("recall_at_k(['a', 'b', 'c'], ['b', 'z'], 2)", 0.5)
              t("recall_at_k(['a', 'b', 'c'], ['b', 'z'], 1)", 0.0)
              t("recall_at_k(['a'], [], 3)", 0.0)
              t("recall_at_k(['a', 'b'], ['a', 'b'], 5)", 1.0)
          """, ["Only the first `k` results count.", "Count how many relevant ids are among them.", "Divide by the number of relevant ids."], diff=2),
          code("Write `mrr(results)` where `results` is a list of `(retrieved_ids, correct_id)` pairs. For each pair the score is `1 / rank` of the correct id in the list (rank starts at 1), or 0 if it is missing. Return the average. An empty list gives 0.0.",
               "def mrr(results):\n    pass\n", """
              def mrr(results):
                  if not results:
                      return 0.0
                  total = 0.0
                  for retrieved, correct in results:
                      if correct in retrieved:
                          total += 1 / (retrieved.index(correct) + 1)
                  return total / len(results)
          """, """
              t("mrr([(['a', 'b', 'c'], 'b'), (['x', 'y'], 'z')])", 0.25)
              t("mrr([(['a'], 'a')])", 1.0)
              t("mrr([])", 0.0)
              t("round(mrr([(['a', 'b', 'c'], 'c'), (['q'], 'q')]), 6)", 0.666667)
          """, ["The rank is the list position plus one.", "A missing answer scores 0.", "Add up the scores and divide by the number of queries."], diff=3, tags=["interview"]),
      ], phases=["deep", "serving"], minutes=7),

    C("py.serve2", 5, "Serving ML: startup, testing and resilience",
      "A model endpoint fails in boring ways: slow loads, blocked event loops, flaky dependencies and untested routes. Cheap habits prevent most of them.",
      [
          CODE("""
              from contextlib import asynccontextmanager
              from fastapi import FastAPI
              from fastapi.testclient import TestClient

              @asynccontextmanager
              async def lifespan(app):
                  app.state.model = load_model()     # once, at startup
                  yield                               # the app serves requests here
                  # cleanup goes after yield

              app = FastAPI(lifespan=lifespan)

              @app.post("/predict")
              def predict(ticket: Ticket):            # plain def: FastAPI runs it in a worker thread
                  return {"label": app.state.model.predict(ticket.text)}

              def test_predict():
                  with TestClient(app) as client:
                      r = client.post("/predict", json={"text": "refund please"})
                      assert r.status_code == 200
          """),
          UL("Load the model **once** in `lifespan`, never inside the request function.", "`async def` endpoints must not run slow blocking code (model inference, `requests.get`), or they freeze every other request. Use plain `def` for CPU-bound work, or an executor.", "Add `/health` (process is up) and readiness (model loaded) endpoints. Return **503** while loading, **422** for invalid input.", "Retry flaky outbound calls with a small limit and a delay, and set timeouts."),
          QUICK("A heavy model prediction runs inside an `async def` endpoint. What happens under load?", ["Requests run in parallel threads", "The event loop is blocked and other requests wait", "FastAPI moves it to the GPU", "Nothing, async is always faster"], 1, "Blocking work inside async code stops the whole event loop."),
      ],
      [
          fill("Finish the startup hook and the test.", "@asynccontextmanager\nasync def lifespan(app):\n    app.state.model = load_model()\n    ____\n\ndef test_predict():\n    r = client.post(\"/predict\", json={\"text\": \"hi\"})\n    assert r.status_code == ____", [["yield"], ["200"]], ["The hook has to hand control back to the app while it serves.", "A successful request returns this status code.", "`yield` and `200`."], lang="python", diff=2),
          spot("Under load the whole service freezes during predictions. Which line is the problem?", ["@app.post(\"/predict\")", "async def predict(ticket: Ticket):", "    return {\"label\": model.predict(ticket.text)}   # slow CPU-bound call"], 2,
               ["Which keyword makes the function run on the event loop?", "CPU-bound code blocks that loop.", "A plain `def` lets FastAPI use a worker thread."], lang="python",
               fix=FIX("What is the best fix?", ["Make it a plain `def` (or run the call in an executor)", "Add `await` in front of `model.predict`", "Add a second `async def` endpoint", "Increase the timeout"], 0, whys=[None, "`await` only works on awaitables; `model.predict` is a normal blocking function.", "That does not stop the first one blocking.", "A longer timeout hides the freeze but does not fix it."]), diff=3, tags=["interview"]),
          code("Write `retry(fn, attempts)` that calls `fn()` and returns its result. If it raises, try again, up to `attempts` calls in total. If every attempt fails, re-raise the last error.",
               "def retry(fn, attempts):\n    pass\n", """
              def retry(fn, attempts):
                  last = None
                  for _ in range(attempts):
                      try:
                          return fn()
                      except Exception as e:
                          last = e
                  raise last
          """, """
              tx("calls = []\\ndef flaky():\\n    calls.append(1)\\n    if len(calls) < 3:\\n        raise ValueError('x')\\n    return 'ok'", "retry(flaky, 3)", "ok")
              tx("calls2 = []\\ndef flaky2():\\n    calls2.append(1)\\n    raise KeyError('k')", "1", 1)
              texc("retry(flaky2, 2)", KeyError)
              t("len(calls2)", 2)
              t("retry(lambda: 7, 1)", 7)
          """, ["Loop up to `attempts` times.", "Return as soon as a call succeeds; remember the last error.", "After the loop, `raise` the remembered error."], diff=3, tags=["interview"]),
          mcq("A request arrives while the model is still loading at startup. Which response is most appropriate?", ["200 with an empty label", "503 Service Unavailable (and a readiness check that stays failing)", "422 Unprocessable Entity", "404 Not Found"], 1,
              ["The request itself is fine. The service is not ready.", "422 means the request body was invalid.", "503 tells clients and load balancers to retry later."], diff=2, tags=["interview"]),
      ], phases=["serving"], minutes=7),
]
