from dsl import *

TRACK = "python"

CONCEPTS = [
    C("py.torch1", 5, "PyTorch tensors and shapes",
      "A PyTorch tensor is a NumPy-like array that can live on a GPU and track gradients. Reading shapes fluently is the most valuable deep-learning skill.",
      [
          CODE("""
              import torch
              x = torch.randn(32, 3, 28, 28)   # (batch, channels, height, width)
              x.shape                          # torch.Size([32, 3, 28, 28])
              x.view(32, -1).shape             # (32, 2352)   3*28*28 = 2352
              x.unsqueeze(0).shape             # (1, 32, 3, 28, 28)  add a size-1 axis
              x.permute(0, 2, 3, 1).shape      # (32, 28, 28, 3)     reorder axes
              x.mean(dim=1).shape              # (32, 28, 28)        the dim you name disappears
              logits = torch.randn(8, 4)
              logits.argmax(dim=1).shape       # (8,)  one class index per sample
          """),
          P("Edit the input shape below and see where a layer stops accepting it. Try `32,1,28,28` or `32,3,28,28`."),
          VIZ("shapeflow", title="Follow a batch through a small CNN", input="32,3,28,28", layers=["Conv2d(3,16,3,1,1)", "ReLU", "MaxPool2d(2)", "Flatten", "Linear(3136,10)"], note="Conv2d(in_channels, out_channels, kernel, stride, padding). Try changing the input channels."),
          UL("The first axis is almost always the **batch**.", "Images are `(N, C, H, W)` in PyTorch (channels first); NumPy and TensorFlow often use channels last.", "`view` needs memory laid out contiguously; `reshape` always works. `.item()` turns a one-element tensor into a Python number.", "Default float dtype is `float32`; class labels for classification need `int64` (`long`)."),
          QUICK("A tensor has shape `(32, 3, 28, 28)`. What is `x.view(32, -1).shape`?", ["(32, 2352)", "(32, 84)", "(32, 3, 784)", "(2352, 32)"], 0, "3 x 28 x 28 = 2352 numbers per sample; `-1` is worked out for you."),
      ],
      [
          mcq("`x = torch.randn(32, 3, 224, 224)`. What is `x.view(32, -1).shape`?", ["(32, 150528)", "(32, 672)", "(32, 3, 50176)", "(150528, 32)"], 0,
              ["Multiply the remaining axes: 3 x 224 x 224.", "224 x 224 = 50176.", "3 x 50176 = 150528."], diff=2, tags=["interview"]),
          predict("What does this print? (Think in shapes. `torch.Size` prints like a tuple.)", """
              import torch
              x = torch.arange(24).reshape(2, 3, 4)
              print(x.shape, x.unsqueeze(0).shape, x.permute(2, 0, 1).shape, x.sum(dim=1).shape)
          """, "torch.Size([2, 3, 4]) torch.Size([1, 2, 3, 4]) torch.Size([4, 2, 3]) torch.Size([2, 4])", ["`unsqueeze(0)` adds a new first axis of size 1.", "`permute(2, 0, 1)` puts old axis 2 first, then 0, then 1.", "`sum(dim=1)` removes axis 1 (size 3)."], diff=3, verify=False),
          fill("Add a batch axis to a single image, then multiply two matrices.", "import torch\nimg = torch.randn(3, 224, 224)\nbatch = img.____(0)          # shape (1, 3, 224, 224)\nA, B = torch.randn(4, 3), torch.randn(3, 5)\nout = torch.____(A, B)      # shape (4, 5)", ["unsqueeze", ["matmul", "mm"]], ["The first one inserts a size-1 dimension at position 0.", "The second is matrix multiplication; `A @ B` does the same thing.", "`unsqueeze` and `matmul`."], lang="python"),
      ], phases=["deep"], minutes=6),

    C("py.torch2", 5, "nn.Module, layers and loss shapes",
      "A model is a class whose `forward` method describes how data flows. Shape arithmetic for layers and for the loss decides whether it runs at all.",
      [
          CODE("""
              import torch.nn as nn

              class TextClassifier(nn.Module):
                  def __init__(self, vocab=1000, dim=64, classes=4):
                      super().__init__()
                      self.emb = nn.Embedding(vocab, dim)
                      self.fc = nn.Linear(dim, classes)

                  def forward(self, ids):          # ids: (batch, seq)
                      h = self.emb(ids)            # (batch, seq, dim)
                      h = h.mean(dim=1)            # (batch, dim)
                      return self.fc(h)            # (batch, classes)  raw scores = logits
          """),
          VIZ("shapeflow", title="A tiny text classifier", input="8,20", layers=["Embedding(1000,64)", "mean(1)", "Linear(64,32)", "ReLU", "Linear(32,4)"], note="Input is a batch of 8 token-id sequences of length 20. Try changing 20 to 50: nothing breaks, because the mean removes that axis."),
          P("Conv layers shrink images by a formula you should know by heart: `out = floor((size + 2*pad - kernel) / stride) + 1`."),
          UL("`nn.Linear(in, out)` has `in x out + out` parameters and acts on the **last** axis.", "`nn.CrossEntropyLoss` wants **logits** of shape `(N, C)` and integer class ids of shape `(N,)`. It applies softmax itself.", "`nn.Module` tracks every layer you assign to `self`, so `model.parameters()` just works."),
          WARN("Do not put `softmax` before `CrossEntropyLoss`. The loss already does a log-softmax internally, and doing it twice quietly hurts training."),
          QUICK("`nn.CrossEntropyLoss()(logits, y)`: what shape is `y`?", ["(N, C) probabilities", "(N,) integer class ids", "(C,)", "(N, 1) floats"], 1, "One integer class index per sample, dtype long."),
      ],
      [
          code("Write `conv_out(size, kernel, stride=1, pad=0)` returning the output size of a convolution along one dimension: `(size + 2*pad - kernel) // stride + 1`.",
               "def conv_out(size, kernel, stride=1, pad=0):\n    pass\n", """
              def conv_out(size, kernel, stride=1, pad=0):
                  return (size + 2 * pad - kernel) // stride + 1
          """, """
              t("conv_out(28, 3, 1, 1)", 28)
              t("conv_out(32, 5)", 28)
              t("conv_out(224, 7, 2, 3)", 112)
              t("conv_out(28, 2, 2)", 14)
              t("conv_out(112, 3, 2, 1)", 56)
          """, ["Padding adds `pad` pixels on both sides.", "The kernel needs `kernel` pixels at each position and slides by `stride`.", "`(size + 2 * pad - kernel) // stride + 1`"], diff=2, tags=["interview"]),
          mcq("How many learnable parameters does `nn.Linear(3136, 10)` have (weights and bias)?", ["31,360", "31,370", "3,146", "313,600"], 1,
              ["Weights: one per input-output pair.", "3136 x 10 = 31,360 weights.", "Add the 10 biases."], diff=3, tags=["interview"]),
          spot("This training step runs but the model learns poorly. Which line is the problem?", ["logits = model(x)", "probs = torch.softmax(logits, dim=1)", "loss = nn.CrossEntropyLoss()(probs, y)", "loss.backward()"], 3,
               ["Look at what is passed to the loss.", "`CrossEntropyLoss` already applies log-softmax.", "It should receive raw logits."], lang="python",
               fix=FIX("What is the fix?", ["Pass `logits` to the loss and drop the softmax", "Use `MSELoss`", "Apply softmax twice", "Remove `backward()`"], 0), diff=3, tags=["interview"],
               explain=EXPLAIN("In your own words: why is softmax before CrossEntropyLoss a bug?",
                               ["CrossEntropyLoss already includes log-softmax", "Applying it twice squashes the scores and weakens gradients"],
                               "The loss expects raw scores (logits) and normalises them itself. Feeding it probabilities applies softmax twice, which squeezes the values and makes the gradient signal weaker.")),
      ], phases=["deep"], minutes=6),

    C("py.torch3", 5, "The training loop",
      "The loop has a fixed rhythm: forward, loss, backward, step. Knowing why each step exists lets you debug the usual mistakes.",
      [
          CODE("""
              model.train()
              for x, y in train_loader:
                  optimizer.zero_grad()          # clear old gradients
                  logits = model(x)              # forward pass
                  loss = loss_fn(logits, y)      # how wrong are we?
                  loss.backward()                # compute gradients
                  optimizer.step()               # update the weights

              model.eval()                       # dropout/batch-norm behave for inference
              with torch.no_grad():              # do not build the graph: faster, less memory
                  for x, y in val_loader:
                      preds = model(x).argmax(dim=1)
          """),
          UL("Gradients **accumulate** by default. Without `zero_grad()` each step adds to the last.", "`model.eval()` changes behaviour of dropout and batch norm. `torch.no_grad()` turns off gradient tracking. You usually want both when validating.", "`argmax` is not differentiable: use it for predictions, never before the loss."),
          WARN("Move the model **and** each batch to the same device: `x = x.to(device)`. A CPU/GPU mix is a classic error."),
          QUICK("What happens if you forget `optimizer.zero_grad()`?", ["Nothing, it is optional", "Gradients from earlier batches pile up and the updates are wrong", "The model stops training immediately", "The loss becomes zero"], 1, "`backward()` adds to the existing `.grad`."),
      ],
      [
          order("Put the training step in the correct order.",
                ["for x, y in train_loader:", "    optimizer.zero_grad()", "    logits = model(x)", "    loss = loss_fn(logits, y)", "    loss.backward()", "    optimizer.step()"],
                ["Gradients must be cleared before `backward()` adds new ones.", "You need a loss before you can call `backward()`.", "`step()` uses the gradients, so it comes after `backward()`."],
                lang="python", alts=[["for x, y in train_loader:", "    logits = model(x)", "    loss = loss_fn(logits, y)", "    optimizer.zero_grad()", "    loss.backward()", "    optimizer.step()"]]),
          spot("Training crashes with `element 0 of tensors does not require grad`. Which line is the problem?", ["for x, y in loader:", "    logits = model(x).argmax(dim=1)", "    loss = loss_fn(logits, y)", "    loss.backward()"], 2,
               ["`backward()` needs a computation graph back to the weights.", "What does `argmax` return?", "Integer indexes carry no gradient."], lang="python",
               fix=FIX("What is the fix?", ["Pass the raw `model(x)` output to the loss and use `argmax` only for predictions", "Call `loss.backward(retain_graph=True)`", "Wrap the loop in `torch.no_grad()`", "Convert `y` to float"], 0), diff=3, tags=["interview"]),
          predict("What does this print?", """
              import torch
              w = torch.tensor(2.0, requires_grad=True)
              for _ in range(2):
                  loss = w * 3
                  loss.backward()
              print(w.grad)
          """, "tensor(6.)", ["The gradient of `w * 3` with respect to `w` is 3.", "`backward()` is called twice without clearing.", "Gradients add up: 3 + 3."], diff=3, verify=False, tags=["interview"],
                  explain=EXPLAIN("In your own words: why is the gradient 6 and not 3?",
                                  ["Each backward() adds into w.grad", "Nothing cleared the gradient between the two calls"],
                                  "PyTorch accumulates gradients on purpose (useful for large effective batches). Since `w.grad` was never reset, the second `backward()` added another 3 to the first 3.")),
      ], phases=["deep"], minutes=6),

    C("py.hf", 5, "Hugging Face: tokenizers, models and batches",
      "A tokenizer turns text into numbers, pads batches to equal length and tells the model which positions are real.",
      [
          CODE("""
              from transformers import AutoTokenizer, AutoModelForSequenceClassification

              tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
              model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=4)

              batch = tok(["refund please", "app crashes when I log in on a slow connection"],
                          padding=True, truncation=True, max_length=128, return_tensors="pt")
              batch.keys()          # input_ids, attention_mask
              out = model(**batch)  # out.logits has shape (2, 4)
          """),
          UL("`input_ids` are integer token ids, shape `(batch, seq_len)`.", "`attention_mask` is 1 for real tokens and 0 for padding, same shape.", "`padding=True` pads to the longest text in the batch. `truncation=True, max_length=N` cuts longer texts.", "`pipeline(\"text-classification\")` bundles tokenizer + model for quick inference."),
          P("Padding is simple enough to write yourself, and the first exercise does."),
          WARN("A tokenizer must match the model checkpoint. Mixing a tokenizer from one model with another model's weights gives garbage."),
          QUICK("In `attention_mask`, a padded position is:", ["1", "0", "-1", "the pad token id"], 1, "Zero tells attention to ignore that position."),
      ],
      [
          code("Write `pad_batch(seqs, pad_id=0)` that pads each list of token ids on the right to the length of the longest one, and returns `(input_ids, attention_mask)` as two lists of lists.",
               "def pad_batch(seqs, pad_id=0):\n    pass\n", """
              def pad_batch(seqs, pad_id=0):
                  longest = max(len(s) for s in seqs)
                  ids = [s + [pad_id] * (longest - len(s)) for s in seqs]
                  mask = [[1] * len(s) + [0] * (longest - len(s)) for s in seqs]
                  return ids, mask
          """, """
              t("pad_batch([[5, 6, 7], [8]])", ([[5, 6, 7], [8, 0, 0]], [[1, 1, 1], [1, 0, 0]]))
              t("pad_batch([[1, 2]], pad_id=9)", ([[1, 2]], [[1, 1]]))
              t("pad_batch([[1], [2], [3]])", ([[1], [2], [3]], [[1], [1], [1]]))
          """, ["Find the longest sequence first.", "The mask has a 1 for each real token and a 0 for each pad.", "`s + [pad_id] * (longest - len(s))`"], diff=3, tags=["interview"]),
          fill("Complete the code that prepares a batch and builds a 4-class model.", "tok = AutoTokenizer.from_pretrained(\"distilbert-base-uncased\")\nmodel = AutoModelForSequenceClassification.from_pretrained(\"distilbert-base-uncased\", ____=4)\nbatch = tok(texts, padding=True, ____=True, return_tensors=\"pt\")\nout = model(**batch)", ["num_labels", "truncation"], ["The first is how many output classes the classification head has.", "The second cuts texts that are longer than the model's limit.", "`num_labels` and `truncation`."], lang="python"),
          mcq("A batch has 8 texts and the longest is 40 tokens. What is the shape of `batch[\"input_ids\"]` with `padding=True`?", ["(8, 40)", "(40, 8)", "(8,)", "(8, 128)"], 0,
              ["Rows are texts, columns are token positions.", "Padding goes to the longest text, not to the model maximum.", "Shape is `(batch, longest)`."], diff=2),
      ], phases=["deep"], minutes=6),

    C("py.fastapi", 5, "FastAPI basics",
      "FastAPI turns type-hinted Python functions into a web API with validation and automatic docs. It is how ReviewRadar serves predictions.",
      [
          CODE("""
              from fastapi import FastAPI
              from pydantic import BaseModel

              app = FastAPI()

              class Ticket(BaseModel):
                  text: str

              @app.get("/health")
              def health():
                  return {"status": "ok"}

              @app.get("/tickets/{ticket_id}")          # path parameter
              def get_ticket(ticket_id: int, verbose: bool = False):   # query parameter ?verbose=true
                  return {"id": ticket_id, "verbose": verbose}

              @app.post("/predict")
              def predict(ticket: Ticket):               # JSON body validated against Ticket
                  return {"label": "bug", "confidence": 0.93}
          """),
          UL("Function parameters named in the path are **path** parameters; other simple types are **query** parameters; a Pydantic model is the **JSON body**.", "Invalid input gets an automatic **422** response before your code runs.", "Run with `uvicorn main:app --reload`; the interactive docs live at `/docs`."),
          WARN("Load the model **once** at startup, not inside the request function. Loading weights on every request makes the service painfully slow."),
          QUICK("A client POSTs `{\"txt\": \"hi\"}` to an endpoint expecting `Ticket(text: str)`. FastAPI responds:", ["200 with an empty label", "422 validation error", "500 server error", "It ignores the body"], 1, "The required field `text` is missing, so validation fails with 422."),
      ],
      [
          fill("Complete the endpoint.", "from fastapi import FastAPI\nfrom pydantic import BaseModel\napp = FastAPI()\n\nclass Ticket(BaseModel):\n    text: str\n\n@app.____(\"/predict\")\ndef predict(ticket: ____):\n    return {\"label\": \"bug\"}", ["post", "Ticket"], ["Sending data to the server uses a verb other than GET.", "The body parameter is annotated with the model class.", "`post` and `Ticket`."], lang="python"),
          spot("Requesting `/tickets/7` returns a 422 error. Which line is the problem?", ["@app.get(\"/tickets/{ticket_id}\")", "def get_ticket(id: int):", "    return {\"id\": id}"], 2,
               ["Compare the name in the path with the parameter name.", "FastAPI matches path parameters by **name**.", "`ticket_id` vs `id`."], lang="python",
               fix=FIX("What is the fix?", ["Rename the parameter to `ticket_id`", "Change the return value", "Use `post` instead of `get`", "Add `async`"], 0), diff=2),
          code("Without FastAPI: write `validate_ticket(payload)` that mimics request validation. Return a list of problems (empty if fine): `\"text is required\"` if the key is missing, `\"text must be a string\"` if it is not a str, `\"text must not be empty\"` if it is an empty or blank string. Report only the first problem.",
               "def validate_ticket(payload):\n    pass\n", """
              def validate_ticket(payload):
                  if "text" not in payload:
                      return ["text is required"]
                  if not isinstance(payload["text"], str):
                      return ["text must be a string"]
                  if not payload["text"].strip():
                      return ["text must not be empty"]
                  return []
          """, """
              t("validate_ticket({'text': 'app crashes'})", [])
              t("validate_ticket({})", ["text is required"])
              t("validate_ticket({'text': 5})", ["text must be a string"])
              t("validate_ticket({'text': '   '})", ["text must not be empty"])
          """, ["Check the problems in the order they can occur.", "Missing key first, then wrong type, then empty text.", "Return early with a one-item list."], diff=2),
      ], phases=["serving"], minutes=6),

    C("py.perf", 5, "Performance, profiling and async",
      "Measure before you optimise. Most speed-ups come from choosing a better algorithm, vectorising, caching, or not blocking while you wait.",
      [
          CODE("""
              # 1. measure
              import timeit, cProfile
              timeit.timeit("sum(range(1000))", number=1000)
              cProfile.run("main()")            # which functions eat the time?

              # 2. vectorise instead of looping
              total = sum(x * x for x in xs)    # fine
              total = (arr * arr).sum()         # NumPy: runs in C, much faster for big arrays

              # 3. cache repeated work
              from functools import lru_cache
          """),
          P("**I/O-bound** work (waiting for networks or disks) benefits from `asyncio` or threads. **CPU-bound** work (number crunching) needs vectorisation or multiple processes, because of the GIL."),
          CODE("""
              import asyncio

              async def work(name, delay):
                  await asyncio.sleep(delay)      # yields control while waiting
                  print(name)

              async def main():
                  await asyncio.gather(work("slow", 0.03), work("fast", 0.01))   # run together

              asyncio.run(main())   # prints fast, then slow
          """),
          WARN("Premature optimisation wastes time. Profile first, fix the biggest bottleneck, measure again."),
          QUICK("Calling an external API 1,000 times and waiting on each answer is best sped up with:", ["More CPU cores", "`asyncio` or threads", "A bigger list", "`lru_cache` always"], 1, "The program mostly waits, so overlap the waiting."),
      ],
      [
          predict("What does this print?", """
              import asyncio

              async def work(name, delay):
                  await asyncio.sleep(delay)
                  print(name)

              async def main():
                  await asyncio.gather(work("slow", 0.03), work("fast", 0.01))

              asyncio.run(main())
          """, "fast\nslow", ["Both tasks start together.", "Each waits for its own delay.", "The shorter delay finishes first."], diff=3, tags=["interview"]),
          code("Write `moving_average(xs, k)` returning the average of every window of `k` consecutive values (so `len(xs) - k + 1` numbers). Do it with a running sum rather than re-adding each window.",
               "def moving_average(xs, k):\n    pass\n", """
              def moving_average(xs, k):
                  window = sum(xs[:k])
                  out = [window / k]
                  for i in range(k, len(xs)):
                      window += xs[i] - xs[i - k]
                      out.append(window / k)
                  return out
          """, """
              t("moving_average([1, 2, 3, 4, 5], 2)", [1.5, 2.5, 3.5, 4.5])
              t("moving_average([4, 4, 4], 3)", [4.0])
              t("moving_average([1, 3, 5, 7], 1)", [1.0, 3.0, 5.0, 7.0])
              t("len(moving_average(list(range(20000)), 100))", 19901)
          """, ["Adding `k` numbers for every window repeats a lot of work.", "When the window slides one step, one value leaves and one enters.", "`window += xs[i] - xs[i - k]`"], diff=3, tags=["interview"]),
          mcq("A script spends 90% of its time in a function you did not suspect. What should you do first?", ["Rewrite the whole script in C", "Profile to find the real bottleneck and fix that", "Add threads everywhere", "Cache every function"], 1,
              ["Guessing wastes time.", "Tools like `cProfile` show where time goes.", "Fix the biggest cost and measure again."], diff=2),
      ], phases=["serving", "monitor"], minutes=5),

    C("py.tf", 5, "TensorFlow and Keras: shapes and parameters",
      "TensorFlow follows the same ideas as PyTorch with different defaults. The biggest one: images are **channels last**.",
      [
          CODE("""
              import tensorflow as tf
              from tensorflow import keras

              model = keras.Sequential([
                  keras.layers.Input(shape=(28, 28, 1)),               # (height, width, channels); the batch axis is implicit
                  keras.layers.Conv2D(16, 3, activation="relu"),       # -> (26, 26, 16)   no padding shrinks by kernel-1
                  keras.layers.MaxPooling2D(2),                        # -> (13, 13, 16)
                  keras.layers.Flatten(),                              # -> (2704,)
                  keras.layers.Dense(10),                              # -> (10,)  raw scores (logits)
              ])
              model.compile(optimizer="adam",
                            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                            metrics=["accuracy"])
              model.fit(x_train, y_train, epochs=3, batch_size=32, validation_split=0.1)
          """),
          TABLE(["", "PyTorch", "TensorFlow / Keras"], [["Image batch shape", "`(N, C, H, W)`", "`(N, H, W, C)`"], ["Layer sizes", "you give input and output sizes", "`Dense(10)`: input size is inferred"], ["Training", "you write the loop", "`compile()` then `fit()`"], ["Loss for raw scores", "`CrossEntropyLoss()`", "`SparseCategoricalCrossentropy(from_logits=True)`"]]),
          UL("Parameters in `Dense(units)`: `inputs x units + units`. In `Conv2D(filters, k)`: `k x k x in_channels x filters + filters`.", "`from_logits=True` says the model outputs raw scores. If your last layer already applies softmax, use `False`; mixing them up quietly harms training.", "`model.summary()` prints every layer's output shape and parameter count. Use it constantly."),
          QUICK("A batch of 32 RGB images of 64 x 64 pixels has which default TensorFlow shape?", ["(32, 3, 64, 64)", "(32, 64, 64, 3)", "(64, 64, 3)", "(3, 32, 64, 64)"], 1, "Channels come last: batch, height, width, channels."),
      ],
      [
          mcq("In the model above, `Conv2D(16, 3)` runs on a 1-channel image. How many parameters does that layer have?", ["144", "160", "16", "2704"], 1,
              ["Weights: 3 x 3 kernel x 1 input channel x 16 filters.", "That is 144 weights.", "Add one bias per filter (16)."], diff=3, tags=["interview"]),
          fill("Compile a classifier whose last layer outputs raw scores.", "model.____(optimizer=\"adam\",\n              loss=keras.losses.SparseCategoricalCrossentropy(from_logits=____),\n              metrics=[\"accuracy\"])", ["compile", "True"], ["The first fills in how the model will be trained.", "The last layer has no softmax, so the loss receives logits.", "`compile` and `True`."], lang="python", diff=2),
          code("Without TensorFlow: write `conv_params(k, c_in, c_out)` returning the number of parameters of a square-kernel convolution layer (weights plus one bias per output channel).",
               "def conv_params(k, c_in, c_out):\n    pass\n", """
              def conv_params(k, c_in, c_out):
                  return k * k * c_in * c_out + c_out
          """, """
              t("conv_params(3, 1, 16)", 160)
              t("conv_params(3, 16, 32)", 4640)
              t("conv_params(1, 64, 10)", 650)
          """, ["Each of the `c_out` filters has a `k x k x c_in` block of weights.", "Add one bias for each filter.", "`k * k * c_in * c_out + c_out`"], diff=2, tags=["interview"]),
      ], phases=["deep"], minutes=6),
]
