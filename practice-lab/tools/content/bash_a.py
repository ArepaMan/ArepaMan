from dsl import *
from tracegen import pipe_steps

TRACK = "bash"

LOG = """
INFO start
ERROR disk full
WARN slow
ERROR timeout
INFO done
"""

SALES = """
ana 10
ben 5
ana 7
ben 8
"""

CONCEPTS = [
    C("sh.nav", 1, "Finding your way around",
      "The shell is a text conversation with your computer. You always stand in one directory, and a few commands let you look around and move.",
      [
          CODE("""
              $ pwd                  # print working directory: where am I?
              /home/ana/projects
              $ ls                   # list files here
              reviewradar  notes.txt
              $ ls -la               # long format, including hidden files (names starting with .)
              $ cd reviewradar       # move into a folder
              $ cd ..                # up one level
              $ cd ~                 # your home folder (also just: cd)
              $ cd /                 # the very top
          """, "bash"),
          TABLE(["Symbol", "Means"], [["`.`", "the current folder"], ["`..`", "the parent folder"], ["`~`", "your home folder"], ["`/` at the start", "an **absolute** path, from the top"]]),
          P("A path that starts with `/` is **absolute**: it works from anywhere. Anything else is **relative** to where you are standing."),
          TIP("Press **Tab** to auto-complete names and the up arrow to bring back earlier commands. `command --help` and `man command` explain flags."),
          QUICK("You are in `/home/ana/projects`. Where does `cd ../..` take you?", ["/home/ana", "/home", "/", "stays where it is"], 1, "Each `..` goes up one level: projects, then ana, landing in /home."),
      ],
      [
          predict("What does this print? (`basename` shows only the last part of the path.)", """
              mkdir -p proj/data proj/src
              cd proj/data
              cd ../src
              basename "$PWD"
              cd ..
              basename "$PWD"
          """, "src\nproj", ["Track which folder you are in after each `cd`.", "`..` goes to the parent folder.", "First `proj/data`, then up and into `src`, then up to `proj`."], lang="bash",
                  verify={"bash": 'mkdir -p proj/data proj/src\ncd proj/data\ncd ../src\nbasename "$PWD"\ncd ..\nbasename "$PWD"'}),
          mcq("You are in `/home/ana/projects/reviewradar/src`. Which command returns you to `/home/ana`?", ["`cd ../..`", "`cd ~`", "`cd ../../..`", "`cd .`"], 1,
              ["`~` is a shortcut.", "Count the folders if you use `..`: src, reviewradar, projects.", "`cd ~` goes to your home, and `cd ../../..` also works here."],
              whys=["That only reaches /home/ana/projects.", None, "That reaches /home/ana only because the path is exactly three levels deep.", "`.` is the folder you are already in."], diff=2),
          fill("List all files, including hidden ones, in long format.", "ls ____", [["-la", "-al", "-l -a", "-a -l"]], ["`-l` means long format.", "`-a` means all, including names that start with a dot.", "`-la`"], lang="bash"),
      ], phases=["data", "serving"], minutes=4),

    C("sh.files", 1, "Working with files and globs",
      "Create, copy, move and delete from the command line, and use wildcards (globs) to act on many files at once.",
      [
          CODE("""
              $ mkdir logs                 # new folder
              $ touch notes.txt            # new empty file
              $ cp notes.txt backup.txt    # copy
              $ mv backup.txt logs/        # move (also renames: mv old new)
              $ rm notes.txt               # delete a file (no recycle bin!)
              $ rm -r old_folder           # delete a folder and everything in it
              $ ls *.csv                   # * matches any text
              $ ls report?.csv             # ? matches exactly one character
              $ cat notes.txt              # print a file; less notes.txt to page through it
          """, "bash"),
          WARN("`rm` has no undo. Be careful with `rm -r`, and never run `rm -rf` with a path you have not double-checked. A stray space in `rm * .log` deletes **everything** and then looks for a file called `.log`."),
          UL("The **shell** expands `*.csv` into a list of file names before the command runs.", "Quote names with spaces: `cp \"my file.txt\" backup/`.", "`mv` renames when the target is a new name in the same folder."),
          QUICK("Which pattern matches `report1.csv` and `report2.csv` but not `report10.csv`?", ["`report*.csv`", "`report?.csv`", "`report.csv`", "`*.csv`"], 1, "`?` matches exactly one character."),
      ],
      [
          predict("What does this print?", """
              touch b.txt a.txt c.log
              mkdir logs
              mv c.log logs/
              ls
              ls logs
          """, "a.txt\nb.txt\nlogs\nc.log", ["`ls` lists names in alphabetical order.", "`mv c.log logs/` moves the file into the folder.", "After the move `c.log` is no longer in the current folder."], lang="bash",
                  verify={"bash": "touch b.txt a.txt c.log\nmkdir logs\nmv c.log logs/\nls\nls logs"}),
          predict("What does this print?", """
              touch report1.csv report2.csv report10.csv notes.txt
              ls report?.csv
              ls *.txt
          """, "report1.csv\nreport2.csv\nnotes.txt", ["`?` matches exactly one character.", "`report10.csv` has two characters between `report` and `.csv`.", "`*.txt` matches only `notes.txt`."], lang="bash", diff=2,
                  verify={"bash": "touch report1.csv report2.csv report10.csv notes.txt\nls report?.csv\nls *.txt"}),
          spot("You want to delete all `.log` files in the current folder. This command is dangerous. Which line is the problem?", ["cd logs", "rm * .log"], 2,
               ["Look closely at the space in the second line.", "The shell sees two arguments: `*` and `.log`.", "`*` matches every file."], lang="bash",
               fix=FIX("What is the correct command?", ["`rm *.log`", "`rm -rf *`", "`rm .log*`", "`rm * -log`"], 0), diff=2, tags=["interview"]),
      ], phases=["data", "serving"], minutes=4),

    C("sh.pipes", 2, "Pipes and redirection",
      "Small tools that each do one thing become powerful when you connect them. A pipe `|` feeds one command's output into the next.",
      [
          P("Tap the stages to see exactly what comes out of each step. The output below is from really running these commands."),
          VIZ("pipe", title="Follow the data through the pipe", **pipe_steps("""
              bug login
              billing refund
              bug crash
              feature dark-mode
              bug slow
              billing invoice
          """, ["cat data.txt", "cut -d' ' -f1", "sort", "uniq -c", "sort -rn"])),
          CODE("""
              cat access.log | grep 404 | wc -l       # how many 404s?
              echo "first" > out.txt                  # > overwrite a file
              echo "second" >> out.txt                # >> append to a file
              wc -l < out.txt                         # < read a file as input
              command 2> errors.txt                   # 2> sends error messages to a file
              command > all.txt 2>&1                  # stdout and stderr to the same place
          """, "bash"),
          UL("`sort`, `uniq -c` (count adjacent duplicates), `head`, `tail`, `wc -l`, `cut -d, -f2` are the everyday toolbox.", "`uniq` only collapses **adjacent** duplicates, so sort first.", "`>` truncates the file first. Use `>>` to add to the end."),
          QUICK("What does `2>&1` do?", ["Runs the command twice", "Sends error output to the same place as normal output", "Renames file 2", "Discards errors"], 1, "File descriptor 2 is stderr and 1 is stdout."),
      ],
      [
          predict("What does this print?", """
              printf 'bug\\nbilling\\nbug\\nfeature\\nbug\\n' | sort | uniq -c | sort -rn | head -1
          """, "3 bug", ["`sort` puts equal lines next to each other.", "`uniq -c` prefixes each line with its count.", "`sort -rn` puts the largest count first and `head -1` keeps one line."], lang="bash", diff=2, tags=["interview"],
                  verify={"bash": "printf 'bug\\nbilling\\nbug\\nfeature\\nbug\\n' | sort | uniq -c | sort -rn | head -1"}),
          predict("What does this print?", """
              echo "first" > out.txt
              echo "second" >> out.txt
              echo "third" > out.txt
              cat out.txt
              wc -l < out.txt
          """, "third\n1", ["`>` replaces the file's contents.", "Only the last write survives.", "So the file has one line."], lang="bash", diff=2,
                  verify={"bash": 'echo "first" > out.txt\necho "second" >> out.txt\necho "third" > out.txt\ncat out.txt\nwc -l < out.txt'},
                  explain=EXPLAIN("In your own words: why is `first` gone from the file?",
                                  ["`>` truncates (empties) the file before writing", "`>>` would have appended instead"],
                                  "A single `>` opens the file for writing from scratch, wiping what was there. Only `>>` adds to the end. The final `echo \"third\" > out.txt` therefore left a one-line file.")),
          fill("Show the top 3 numbers, largest first.", "sort ____ numbers.txt | head ____", [["-rn", "-nr", "-r -n", "-n -r"], ["-3", "-n 3", "-n3"]], ["`sort -n` sorts numerically.", "`-r` reverses the order.", "`head -3` keeps the first three lines."], lang="bash", diff=2),
          mcq("Which command appends the word `done` to `log.txt` without erasing its contents?", ["`echo done > log.txt`", "`echo done >> log.txt`", "`echo done | log.txt`", "`echo done < log.txt`"], 1,
              ["One redirection overwrites, another adds.", "A pipe sends output to another command, not a file.", "`>>` appends."], diff=1),
      ], phases=["data", "monitor"], minutes=5),

    C("sh.grep", 2, "Searching with grep and find",
      "`grep` finds lines that match a pattern. `find` finds files by name, type or age. Together they answer most \"where is it?\" questions.",
      [
          CODE("""
              grep ERROR app.log                  # lines containing ERROR
              grep -c ERROR app.log               # just the count
              grep -n timeout app.log             # show line numbers
              grep -v INFO app.log                # lines that do NOT match
              grep -i "error" app.log             # ignore case
              grep -r "TODO" src/                 # search every file under src/
              grep -E 'ERROR|WARN' app.log        # extended regex: either word

              find . -name "*.py"                 # files by name
              find . -type f -mtime -1            # files changed in the last day
          """, "bash"),
          UL("`-i` ignore case, `-v` invert, `-n` line numbers, `-c` count, `-r` recursive, `-l` just file names.", "Quote patterns so the shell does not expand them first.", "Pipe into `grep` to filter any command's output: `ps aux | grep python`."),
          QUICK("Which command counts the lines that contain `ERROR`?", ["`grep ERROR file | head`", "`grep -c ERROR file`", "`grep -v ERROR file`", "`find ERROR file`"], 1, "`-c` prints the number of matching lines."),
      ],
      [
          predict("What does this print?", """
              grep -c ERROR app.log
              grep -v INFO app.log | head -2
              grep -n timeout app.log
          """, "2\nERROR disk full\nWARN slow\n4:ERROR timeout", ["The log has 5 lines; two contain ERROR.", "`-v` keeps lines without INFO.", "`-n` prefixes the line number and a colon."], lang="bash", diff=2,
                  verify={"bash": "grep -c ERROR app.log\ngrep -v INFO app.log | head -2\ngrep -n timeout app.log", "files": {"app.log": LOG}}),
          fill("Search for `error`, ignoring case, in every file under `logs/`.", "grep ____ \"error\" logs/", [["-ri", "-ir", "-r -i", "-i -r"]], ["You need two flags: recursive and case-insensitive.", "`-r` recurses, `-i` ignores case.", "`-ri`"], lang="bash"),
          predict("What does this print?", """
              mkdir -p a/b
              touch a/x.py a/b/y.py a/z.txt
              find a -name "*.py" | sort
          """, "a/b/y.py\na/x.py", ["`find` walks the whole folder tree.", "Only names ending in `.py` match.", "`sort` puts `a/b/y.py` before `a/x.py`."], lang="bash", diff=2,
                  verify={"bash": 'mkdir -p a/b\ntouch a/x.py a/b/y.py a/z.txt\nfind a -name "*.py" | sort'}),
      ], phases=["monitor", "data"], minutes=4),

    C("sh.sed", 3, "sed: edit streams of text",
      "`sed` rewrites text as it flows past. Its most useful trick is substitution: `s/old/new/`.",
      [
          CODE("""
              echo "bug in bug fix" | sed 's/bug/issue/'     # issue in bug fix    (first match per line)
              echo "bug in bug fix" | sed 's/bug/issue/g'    # issue in issue fix  (g = every match)
              sed -n '2,3p' file.txt                         # print only lines 2 to 3
              sed '/^#/d' config.txt                         # delete comment lines
              sed -i.bak 's/localhost/prod-db/g' config.txt  # edit the file in place, keep a backup
          """, "bash"),
          UL("The form is `s/pattern/replacement/flags`. Use another separator when the text has slashes: `s#/old/path#/new/path#`.", "`-n` plus `p` prints only the lines you select.", "`-i` edits the file **in place**. Adding `.bak` keeps the original."),
          WARN("`sed -i` changes the file directly. Try the command without `-i` first, or keep a `.bak` copy."),
          QUICK("What does the `g` in `s/a/b/g` do?", ["Greedy matching", "Replaces every match on a line, not just the first", "Global search across files", "Case-insensitive match"], 1, "Without `g`, only the first match in each line is replaced."),
      ],
      [
          predict("What does this print?", """
              echo "bug in bug fix" | sed 's/bug/issue/'
              echo "bug in bug fix" | sed 's/bug/issue/g'
          """, "issue in bug fix\nissue in issue fix", ["Without `g` only the first match per line changes.", "With `g` every match changes.", "The input is the same for both."], lang="bash",
                  verify={"bash": "echo \"bug in bug fix\" | sed 's/bug/issue/'\necho \"bug in bug fix\" | sed 's/bug/issue/g'"}),
          fill("Replace every `localhost` with `prod-db` in `config.txt`, editing the file in place.", "sed -i 's/____/____/g' config.txt", ["localhost", "prod-db"], ["The pattern goes first, the replacement second.", "Fields are separated by slashes.", "`localhost` then `prod-db`."], lang="bash", diff=2),
          predict("What does this print?", """
              sed -n '2,3p' notes.txt
          """, "second\nthird", ["`-n` suppresses normal output.", "`2,3p` prints lines 2 to 3.", "Count lines starting from 1."], lang="bash", diff=2,
                  verify={"bash": "sed -n '2,3p' notes.txt", "files": {"notes.txt": "first\nsecond\nthird\nfourth"}}),
      ], phases=["monitor", "cloud"], minutes=4),

    C("sh.awk", 3, "awk: work with columns",
      "`awk` splits each line into fields (`$1`, `$2`, ...) and runs a small program on each. It is perfect for logs and tables.",
      [
          CODE("""
              awk '{print $1}' sales.txt                      # first column
              awk '$2 > 6 {print $1}' sales.txt               # only rows where column 2 is above 6
              awk -F, '{print $2}' data.csv                   # -F sets the field separator
              awk 'NR == 2 {print $1}' sales.txt              # NR = current line number
              awk '{sum[$1] += $2} END {for (k in sum) print k, sum[k]}' sales.txt   # total per name
          """, "bash"),
          UL("`$0` is the whole line, `$NF` the last field, `NR` the line number, `NF` the number of fields.", "`BEGIN { }` runs before the first line, `END { }` after the last.", "Associative arrays (`sum[$1]`) are awk's dictionaries."),
          QUICK("What does `-F,` do in `awk -F, '{print $2}'`?", ["Prints a file", "Makes the comma the field separator", "Forces output", "Filters by comma"], 1, "`-F` chooses the separator, so lines split at commas."),
      ],
      [
          predict("What does this print? (the output is sorted)", """
              awk '{s[$1] += $2} END {for (k in s) print k, s[k]}' sales.txt | sort
          """, "ana 17\nben 13", ["`s[$1] += $2` adds column 2 into a bucket named by column 1.", "ana: 10 + 7, ben: 5 + 8.", "The `END` block prints each total."], lang="bash", diff=3, tags=["interview"],
                  verify={"bash": "awk '{s[$1] += $2} END {for (k in s) print k, s[k]}' sales.txt | sort", "files": {"sales.txt": SALES}}),
          fill("Print the first column of rows whose second column is greater than 6.", "awk '$2 > 6 {print ____}' sales.txt", ["$1"], ["Fields are numbered from 1.", "The name is in the first column.", "`$1`"], lang="bash", diff=2),
          predict("What does this print?", """
              awk 'NR == 2 {print $1}' sales.txt
              awk '{n += $2} END {print n}' sales.txt
          """, "ben\n30", ["`NR == 2` selects the second line.", "The second line is `ben 5`.", "The total of column 2 is 10 + 5 + 7 + 8."], lang="bash", diff=2,
                  verify={"bash": "awk 'NR == 2 {print $1}' sales.txt\nawk '{n += $2} END {print n}' sales.txt", "files": {"sales.txt": SALES}}),
      ], phases=["monitor"], minutes=4),

    C("sh.env", 3, "Environment variables and quoting",
      "Variables carry configuration into programs. Quotes decide whether the shell expands them. Both matter for secrets and for ReviewRadar's config.",
      [
          CODE("""
              NAME=ana                          # no spaces around =
              echo "hi $NAME"                   # hi ana        (double quotes expand variables)
              echo 'hi $NAME'                   # hi $NAME      (single quotes do not)
              export STAGE=prod                 # make it visible to programs you start
              bash -c 'echo $STAGE'             # prod
              DB_HOST=localhost python app.py   # set a variable for one command only
              echo $PATH                        # folders searched for commands
          """, "bash"),
          UL("A plain variable lives only in the current shell. `export` passes it on to child processes.", "`$PATH` lists where the shell looks for commands. `which python` shows which one it found.", "Secrets such as API keys belong in environment variables or a secret store, **never** in code or git."),
          WARN("Always quote variables that may contain spaces: `\"$file\"`, not `$file`. Unquoted values get split into several words."),
          QUICK("Which prints the literal text `$HOME`?", ["`echo $HOME`", "`echo \"$HOME\"`", "`echo '$HOME'`", "`echo ~`"], 2, "Single quotes switch off expansion."),
      ],
      [
          predict("What does this print?", """
              NAME=ana
              echo "hi $NAME" 'hi $NAME'
              export STAGE=prod
              bash -c 'echo $STAGE'
              OTHER=x
              bash -c 'echo "[$OTHER]"'
          """, "hi ana hi $NAME\nprod\n[]", ["Double quotes expand, single quotes do not.", "A child `bash` only sees exported variables.", "`OTHER` was never exported."], lang="bash", diff=3, tags=["interview"],
                  verify={"bash": "NAME=ana\necho \"hi $NAME\" 'hi $NAME'\nexport STAGE=prod\nbash -c 'echo $STAGE'\nOTHER=x\nbash -c 'echo \"[$OTHER]\"'"},
                  explain=EXPLAIN("In your own words: why is `OTHER` empty in the child shell?",
                                  ["Only exported variables are passed to child processes", "OTHER was set without export so it stays in the parent shell"],
                                  "A plain assignment creates a shell variable that only the current shell can see. `export` marks it for inheritance, so child processes receive a copy.")),
          spot("This should print `Price is 5`, but it prints the text `Price is $price`. Which line is the problem?", ["price=5", "echo 'Price is $price'"], 2,
               ["Look at the type of quotes.", "Single quotes stop the shell from expanding variables.", "Switch to double quotes."], lang="bash",
               fix=FIX("How do you fix it?", ["Use double quotes: `echo \"Price is $price\"`", "Remove the quotes: `echo Price is $price` is the only option", "Use `export price`", "Write `echo 'Price is' + $price`"], 0), diff=2),
          mcq("A teammate hard-codes an API key in `train.py` and pushes to GitHub. What is the right approach?", ["Delete the file next week", "Rotate the key now and load it from an environment variable or secret store", "Make the repository private and leave it", "Encode the key in base64"], 1,
              ["Anything pushed to git history can be copied.", "The old key must be treated as leaked.", "New key, read from the environment."], diff=2, tags=["interview"]),
      ], phases=["serving", "cloud"], minutes=5),
]
