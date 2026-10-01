from dsl import *

TRACK = "bash"

MAKEFILE = "\n".join([
    "GREETING = hello",
    "",
    "all: build",
    "\t@echo done",
    "",
    "build:",
    "\t@echo \"$(GREETING) from build\"",
])

GREET_SH = """#!/bin/bash
name=${1:-world}
for i in 1 2; do
  echo "hello $name $i"
done"""

CONCEPTS = [
    C("sh.script", 4, "Writing shell scripts",
      "A script is a text file of commands. Add a shebang, a few variables and a loop, and repetitive work becomes one command.",
      [
          CODE("""
              #!/bin/bash                       # which program runs this file
              name=${1:-world}                  # first argument, default "world"
              for f in *.csv; do                # loop over files
                  echo "processing $f"
              done
              if [ -f "$name" ]; then           # test: is it a regular file?
                  echo "exists"
              fi
              count=$(wc -l < data.txt)         # capture a command's output
              echo "$count lines"
          """, "bash"),
          UL("Make it runnable once with `chmod +x script.sh`, then start it with `./script.sh arg1 arg2`.", "`$1`, `$2` are arguments, `$@` is all of them, `$#` is how many. `$(cmd)` captures output.", "Tests live in `[ ... ]`: `-f` file, `-d` folder, `-z` empty string, `-eq` numbers equal, `==` strings equal. **Spaces inside the brackets are required.**"),
          WARN("Unquoted variables break on spaces. If `file=\"my report.txt\"`, then `rm $file` runs `rm my report.txt` and tries to delete two files. Write `rm \"$file\"`."),
          QUICK("Inside a script, what is `$1`?", ["The script's name", "The first argument", "The exit code", "The number of arguments"], 1, "`$0` is the name, `$1` the first argument, `$#` the count."),
      ],
      [
          predict("The file `greet.sh` below is run as `bash greet.sh ana` and then as `bash greet.sh`. What is printed in total?", GREET_SH, "hello ana 1\nhello ana 2\nhello world 1\nhello world 2",
                  ["`${1:-world}` means: the first argument, or `world` if there is none.", "The loop runs twice for each run.", "First run uses `ana`, the second uses `world`."], lang="bash", diff=3,
                  verify={"bash": "cat > greet.sh <<'EOF'\n" + GREET_SH + "\nEOF\nbash greet.sh ana\nbash greet.sh"}),
          order("Put the lines in order to back up every CSV into a `backup` folder and then print `done`.",
                ["#!/bin/bash", "mkdir -p backup", "for f in *.csv; do", "  cp \"$f\" \"backup/$f\"", "done", "echo \"done\""],
                ["The shebang is always the first line.", "Create the folder before copying into it.", "The loop body sits between `do` and `done`."], lang="bash", diff=2),
          spot("This script should delete `my report.txt`, but it fails with two errors. Which line is the problem?", ["file=\"my report.txt\"", "touch \"$file\"", "rm $file"], 3,
               ["Compare how line 2 and line 3 use the variable.", "Unquoted variables are split at spaces.", "Line 3 runs `rm my report.txt`."], lang="bash",
               fix=FIX("What is the fix?", ["`rm \"$file\"`", "`rm -f $file`", "`rm '$file'`", "`rm file`"], 0, whys=[None, "`-f` hides the error but still tries to delete two wrong files.", "Single quotes pass the literal text `$file`.", "That deletes a file literally called `file`."]), diff=2, tags=["interview"]),
          fill("Complete the test.", "if [ -f \"$1\" ]; ____\n  echo \"exists\"\nfi", ["then"], ["An `if` in bash is closed by `fi`. What keyword opens its body?", "It comes after the semicolon.", "`then`"], lang="bash"),
      ], phases=["monitor", "cloud"], minutes=5),

    C("sh.exit", 4, "Exit codes and safe scripts",
      "Every command ends with a number: 0 means success, anything else means failure. Safe scripts check it, and stop when something goes wrong.",
      [
          CODE("""
              true;  echo $?          # 0   ($? is the last exit code)
              false; echo $?          # 1

              mkdir build && cd build        # && : run the next only if the first succeeded
              cmd1 || echo "cmd1 failed"     # || : run the next only if the first failed

              #!/bin/bash
              set -euo pipefail              # e: stop on error, u: error on unset variables, pipefail: a failing pipe step fails the whole pipe
              trap 'rm -f "$tmp"' EXIT       # always clean up, even on error
              cd "$BUILD_DIR" || exit 1      # never carry on in the wrong folder
          """, "bash"),
          UL("CI systems judge a job by its exit code. Exit 0 means pass, so a script that swallows errors makes CI lie.", "`set -e` stops at the first failing command. `set -u` catches typos in variable names.", "`exit 3` ends the script with your own code."),
          WARN("`cd \"$DIR\"` followed by `rm -rf ./*` is a famous disaster: if `cd` fails, the `rm` runs in the wrong folder. Guard with `cd \"$DIR\" || exit 1`."),
          QUICK("What does `set -e` do?", ["Echoes each command", "Stops the script when a command fails", "Makes variables read-only", "Exports variables"], 1, "The script exits as soon as a command returns non-zero."),
      ],
      [
          predict("What does this print?", """
              true && echo A
              false && echo B
              false || echo C
              test -f nofile; echo $?
          """, "A\nC\n1", ["`&&` runs the right side only after success.", "`||` runs the right side only after failure.", "`test -f nofile` fails, so `$?` is 1."], lang="bash", diff=2,
                  verify={"bash": "true && echo A\nfalse && echo B\nfalse || echo C\ntest -f nofile; echo $?"}),
          mcq("A CI step runs `./deploy.sh`. The script's last command fails but the script ends with `echo finished`. What exit code does the script return, and what does CI show?", ["Non-zero, CI fails", "0, CI passes even though something failed", "It depends on the OS", "CI ignores exit codes"], 1,
              ["A script's exit code is the exit code of its last command.", "`echo` succeeds.", "Use `set -e` so the failure stops the script."], diff=3, tags=["interview"]),
          spot("This cleanup script deletes the wrong files when `$BUILD_DIR` does not exist. Which line is the problem?", ["#!/bin/bash", "cd \"$BUILD_DIR\"", "rm -rf ./*"], 2,
               ["What happens to line 3 if line 2 fails?", "Without protection the script keeps going.", "It would delete everything in the current folder."], lang="bash",
               fix=FIX("What is the best fix?", ["`cd \"$BUILD_DIR\" || exit 1`", "Add `ls` before `rm`", "Use `rm -r` instead of `rm -rf`", "Wrap the path in single quotes"], 0), diff=3, tags=["interview"]),
          fill("Make the script always remove the temp file when it ends, even after an error.", "tmp=$(mktemp)\ntrap 'rm -f \"$tmp\"' ____", ["EXIT"], ["`trap` runs a command when a signal or event happens.", "There is a pseudo-signal for \"the script is ending\".", "`EXIT`"], lang="bash", diff=2),
      ], phases=["monitor", "cloud"], minutes=5),

    C("sh.make", 5, "Makefile basics",
      "A Makefile names the commands you run all the time (`make test`, `make lint`, `make docker`) so everyone, and CI, runs them the same way.",
      [
          CODE("""
              GREETING = hello                     # a variable

              .PHONY: test lint all                # these names are tasks, not files

              all: lint test                       # default target: runs these first

              test:                                # target:
              	pytest -q                          #   recipe (must start with a TAB)

              lint:
              	ruff check .

              docker:
              	docker build -t reviewradar:$(TAG) .
          """, "bash"),
          UL("`target: prerequisites` followed by recipe lines indented with a **TAB**, not spaces.", "`make` with no argument runs the first target. `make test` runs `test`.", "`.PHONY` says the target is a task. Without it, a file called `test` would make `make test` think the work is already done.", "Inside recipes `$@` is the target name and `$<` the first prerequisite. Variables are read with `$(NAME)`."),
          WARN("Recipes indented with spaces fail with `missing separator`. Configure your editor to insert a real tab in Makefiles."),
          QUICK("What does `.PHONY: test` protect you from?", ["Typos in recipes", "A file named `test` making `make test` do nothing", "Running tests twice", "Missing variables"], 1, "Make skips a target whose file already exists and is up to date; `.PHONY` forces the recipe to run."),
      ],
      [
          predict("Given this Makefile, what does `make` (no arguments) print? (Recipe lines start with a tab.)", MAKEFILE, "hello from build\ndone",
                  ["`make` runs the first target, `all`.", "`all` depends on `build`, so `build` runs first.", "`$(GREETING)` expands to `hello`. `@` hides the command itself."], lang="bash", diff=3,
                  verify={"bash": "make", "files": {"Makefile": MAKEFILE}}),
          fill("Declare the targets that are tasks rather than files.", ".____: test lint\ntest:\n\tpytest -q\nlint:\n\truff check .", ["PHONY"], ["The name is spelled in capitals, after a dot.", "It means \"these targets are not files\".", "`.PHONY`"], lang="bash"),
          mcq("In a recipe, what does `$@` stand for?", ["The first prerequisite", "The name of the target being built", "All prerequisites", "The current directory"], 1,
              ["It is an automatic variable.", "Think of it as \"at the target\".", "`$<` is the first prerequisite."], diff=2),
      ], phases=["cloud", "serving"], minutes=5),

    C("sh.ci", 5, "Shell in CI and automation",
      "CI pipelines are mostly shell. A few patterns (`xargs`, loops, strict flags, `curl --fail`) cover most automation you will write.",
      [
          CODE("""
              printf 'a.txt\\nb.txt\\n' | xargs -I{} echo "file: {}"     # run a command once per input line
              find . -name "*.pyc" -delete                             # find and delete
              for f in a b; do echo "run $f"; done | wc -l             # 2

              curl -sf https://api.example.com/health || exit 1        # -s quiet, -f fail on HTTP errors
              docker build -t app . && docker push app                 # push only if build succeeded
              set -x                                                   # echo every command (do NOT use with secrets)
          """, "bash"),
          UL("`&&` chains steps that depend on each other. `;` runs the next step regardless, which is rarely what CI wants.", "Never print secrets. CI masks known secrets, but `set -x` or `echo \"$TOKEN\"` can still leak derived values.", "Use `jq` to read JSON from APIs: `curl -s url | jq -r .status`."),
          QUICK("You want to push a Docker image only if the build worked. Which is right?", ["`docker build -t app . ; docker push app`", "`docker build -t app . && docker push app`", "`docker push app || docker build -t app .`", "`docker build -t app . | docker push app`"], 1, "`&&` stops the chain when the build fails."),
      ],
      [
          predict("What does this print?", """
              printf 'a.txt\\nb.txt\\n' | xargs -I{} echo "file: {}"
              for f in a b c; do echo "run $f"; done | wc -l
          """, "file: a.txt\nfile: b.txt\n3", ["`xargs -I{}` runs the command once per input line.", "The loop prints three lines.", "`wc -l` counts them."], lang="bash", diff=2,
                  verify={"bash": "printf 'a.txt\\nb.txt\\n' | xargs -I{} echo \"file: {}\"\nfor f in a b c; do echo \"run $f\"; done | wc -l"}),
          spot("This CI script pushes an image even when the build fails. Which line is the problem?", ["#!/bin/bash", "docker build -t app . ; docker push app"], 2,
               ["Look at how the two commands are joined.", "A semicolon ignores the result of the first command.", "Use `&&`, or add `set -e` at the top."], lang="bash",
               fix=FIX("What is the fix?", ["Join with `&&` (or add `set -e`)", "Add `sudo`", "Swap the order of the commands", "Add `-q` to `docker build`"], 0), diff=2, tags=["interview"]),
          fill("Make `curl` quiet and make it fail on HTTP errors, so a failed health check fails the job.", "curl ____ https://api.example.com/health || exit 1", [["-sf", "-fs", "-s -f", "-f -s"]], ["`-s` silences the progress meter.", "`-f` makes HTTP errors (like 500) return a non-zero exit code.", "`-sf`"], lang="bash", diff=2),
      ], phases=["cloud", "monitor"], minutes=5),
]
