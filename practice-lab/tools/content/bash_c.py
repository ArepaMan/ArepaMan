from dsl import *
from tracegen import pipe_steps

TRACK = "bash"

ACCESS = """
10.0.0.1 GET /predict 200 120
10.0.0.2 POST /predict 500 340
10.0.0.1 GET /health 200 3
10.0.0.3 POST /predict 200 150
10.0.0.2 POST /predict 500 360
10.0.0.1 GET /predict 404 8
"""

CONCEPTS = [
    C("sh.logs", 4, "Log forensics with one-liners",
      "When a service misbehaves at 3 a.m., the answer is in the logs. A few pipelines answer almost every question: how many, which, how slow, from whom.",
      [
          P("A web log with the fields `ip method path status milliseconds`. Tap through a typical investigation: how often does each status code appear?"),
          VIZ("pipe", title="Count requests by status", **pipe_steps(ACCESS, ["cat access.log", "awk '{print $4}'", "sort", "uniq -c", "sort -rn"], filename="access.log")),
          CODE("""
              awk '$4 == 500 {s += $5; n++} END {print s / n}' access.log     # average ms of the 500s
              awk '$3 == "/predict" && $4 >= 500 {print $1}' access.log | sort -u   # who hit errors
              sort -k5 -nr access.log | head -3                                # 3 slowest requests
              grep -c " 500 " access.log                                       # how many errors
              tail -f app.log | grep --line-buffered ERROR                     # watch live
          """, "bash"),
          UL("Think in three steps: **select** the lines (`grep`, `awk` condition), **extract** the field (`awk '{print $n}'`, `cut`), **summarise** (`sort | uniq -c`, `awk` sums, `wc -l`).", "`sort -k5 -n` sorts by the 5th field numerically. `-r` reverses.", "`sort -u` is `sort | uniq`."),
          QUICK("Which pipeline lists each distinct IP once?", ["`awk '{print $1}' log | uniq`", "`awk '{print $1}' log | sort -u`", "`cut -d' ' -f4 log | sort`", "`grep ip log`"], 1, "`uniq` only removes adjacent duplicates, so sort first. `sort -u` does both."),
      ],
      [
          predict("What does this print?", """
              awk '{print $4}' access.log | sort | uniq -c | sort -rn
          """, "3 200\n2 500\n1 404", ["Column 4 is the status code.", "`uniq -c` counts each distinct code after sorting.", "`sort -rn` puts the most common first."], lang="bash", diff=2, tags=["interview"],
                  verify={"bash": "awk '{print $4}' access.log | sort | uniq -c | sort -rn", "files": {"access.log": ACCESS}}),
          predict("What does this print?", """
              awk '$4 == 500 {s += $5; n++} END {print s / n}' access.log
          """, "350", ["Only lines whose status is 500 are summed.", "Their times are 340 and 360.", "Divide the total by the count."], lang="bash", diff=3,
                  verify={"bash": "awk '$4 == 500 {s += $5; n++} END {print s / n}' access.log", "files": {"access.log": ACCESS}}),
          predict("What does this print?", """
              awk '$3 == "/predict" && $4 >= 500 {print $1}' access.log | sort -u
          """, "10.0.0.2", ["Two conditions must both hold on a line.", "Which lines are `/predict` with status 500 or more?", "Both come from the same IP, and `sort -u` keeps one."], lang="bash", diff=3,
                  verify={"bash": "awk '$3 == \"/predict\" && $4 >= 500 {print $1}' access.log | sort -u", "files": {"access.log": ACCESS}}),
          fill("Show the two slowest requests (the fifth column is the time in ms).", "sort -k5 ____ access.log | head -2", [["-nr", "-rn", "-n -r", "-r -n"]], ["Sort by the fifth field.", "It must be numeric, and largest first.", "`-nr`"], lang="bash", diff=2),
      ], phases=["monitor"], minutes=6),

    C("sh.cron", 5, "Scheduling and background jobs",
      "Batch scoring, backups and drift reports run on a schedule. Cron is simple and unforgiving: know its syntax and its quirks.",
      [
          CODE("""
              # minute hour day-of-month month day-of-week   command
              */15 * * * *   /srv/reviewradar/score.sh        # every 15 minutes
              30 2 * * *     /srv/reviewradar/backup.sh       # every day at 02:30
              0 3 * * 1      /srv/reviewradar/drift.sh        # Mondays at 03:00 (0 or 7 = Sunday)
              0 */6 * * *    /srv/reviewradar/report.sh       # every 6 hours, on the hour

              crontab -e          # edit your schedule
              crontab -l          # list it
          """, "bash"),
          UL("Cron runs jobs with a **minimal environment**: a short `PATH`, no virtualenv, and your home as the working directory. Use absolute paths and `cd` in the command.", "Capture output, or it vanishes: `>> /var/log/job.log 2>&1`.", "A long job can overlap with its next run. Guard with `flock -n /tmp/job.lock command`.", "In the shell: `cmd &` runs in the background, `jobs` lists, `wait` pauses until they finish, `nohup cmd &` survives closing the terminal, `kill PID` stops one."),
          WARN("\"It works in my terminal but not in cron\" is almost always the environment: the PATH, the working directory or a missing activated virtualenv."),
          QUICK("Which schedule runs a job every day at 02:30?", ["`2 30 * * *`", "`30 2 * * *`", "`* 2:30 * * *`", "`30 2 1 * *`"], 1, "Minute comes first (30), then hour (2)."),
      ],
      [
          fill("Complete the cron expression for \"every day at 02:30\".", "____ ____ * * *   /srv/reviewradar/backup.sh", ["30", "2"], ["The first field is the minute, the second is the hour.", "02:30 means minute 30, hour 2.", "`30` and `2`."], lang="bash"),
          predict("What does this print?", """
              sleep 0.1 &
              echo "started"
              wait
              echo "finished"
          """, "started\nfinished", ["`&` starts `sleep` in the background and the script moves on.", "`wait` blocks until background jobs end.", "So the order of the two echo lines is fixed."], lang="bash", diff=2,
                  verify={"bash": "sleep 0.1 &\necho \"started\"\nwait\necho \"finished\""}),
          spot("This cron job works when typed in a terminal but never produces output when scheduled. Which line is the problem?", "*/5 * * * * python score.py", 1,
               ["What is the working directory and `PATH` under cron?", "The script path and interpreter are relative.", "Cron also throws away output unless you redirect it."], lang="bash",
               fix=FIX("What is the best fix?", ["`*/5 * * * * cd /srv/reviewradar && /usr/bin/python3 score.py >> /var/log/score.log 2>&1`", "`*/5 * * * * python score.py &`", "`*/5 * * * * sudo python score.py`", "`5 * * * * python score.py`"], 0, whys=[None, "`&` does nothing about the environment.", "`sudo` does not fix paths and adds risk.", "That changes the schedule, not the problem."]), diff=3, tags=["interview"]),
          mcq("Your hourly cron job sometimes takes 70 minutes, so two copies overlap and corrupt a file. What is the standard fix?", ["Run it every two minutes", "Wrap it in a lock, for example `flock -n /tmp/job.lock ./job.sh`", "Add `sleep 60` at the start", "Run it as root"], 1,
              ["The second copy should not start while the first still runs.", "A file lock enforces that.", "`flock -n` exits immediately when the lock is taken."], diff=3, tags=["interview"]),
      ], phases=["monitor", "cloud"], minutes=6),
]
