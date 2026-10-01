"""Generate step-through traces and pipeline stages from REAL execution at build time."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import types


def make_trace(code, max_steps=48, title=None):
    code = textwrap.dedent(code).strip("\n") + "\n"
    steps = []
    buf = io.StringIO()

    def fmt(v):
        r = repr(v)
        return r if len(r) <= 70 else r[:67] + "..."

    def snap(loc):
        v = {}
        for k, val in loc.items():
            if k.startswith("__") or isinstance(val, (types.FunctionType, types.ModuleType, type)):
                continue
            ent = {"r": fmt(val)}
            if isinstance(val, (list, dict, set)) or (hasattr(val, "__dict__") and not isinstance(val, (int, float, str, bool, tuple, type(None)))):
                ent["i"] = id(val)
            v[k] = ent
        return v

    def stack_of(frame):
        names = []
        f = frame
        while f is not None and f.f_code.co_filename == "<trace>":
            names.append("main" if f.f_code.co_name == "<module>" else f.f_code.co_name + "()")
            f = f.f_back
        names.reverse()
        return names if len(names) > 1 else []

    def local_tracer(frame, event, arg):
        if len(steps) >= max_steps:
            return local_tracer
        if event == "line":
            steps.append({"l": frame.f_lineno, "v": snap(frame.f_locals), "o": buf.getvalue(), "s": stack_of(frame)})
        elif event == "return" and frame.f_code.co_name != "<module>":
            steps.append({"l": frame.f_lineno, "v": snap(frame.f_locals), "o": buf.getvalue(), "s": stack_of(frame), "n": "returns " + fmt(arg)})
        return local_tracer

    def global_tracer(frame, event, arg):
        return local_tracer if frame.f_code.co_filename == "<trace>" else None

    ns = {"__name__": "__main__"}
    compiled = compile(code, "<trace>", "exec")
    with contextlib.redirect_stdout(buf):
        sys.settrace(global_tracer)
        try:
            exec(compiled, ns)
        finally:
            sys.settrace(None)
    steps.append({"l": 0, "v": snap(ns), "o": buf.getvalue(), "s": [], "n": "Done"})
    # drop the id of objects that appear only once across the whole trace (no aliasing to show)
    counts = {}
    for st in steps:
        for ent in st["v"].values():
            if "i" in ent:
                counts.setdefault(ent["i"], set()).add(id(ent))
    d = {"code": code, "steps": steps}
    if title:
        d["title"] = title
    return d


def pipe_steps(input_text, stages, filename="data.txt", extra_files=None):
    """stages: list of shell commands joined with ' | '. Returns widget data with real output per prefix."""
    out = []
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, filename), "w") as f:
            f.write(textwrap.dedent(input_text).strip("\n") + "\n")
        for name, content in (extra_files or {}).items():
            with open(os.path.join(td, name), "w") as f:
                f.write(textwrap.dedent(content).strip("\n") + "\n")
        for k, cmd in enumerate(stages):
            line = " | ".join(stages[: k + 1])
            r = subprocess.run(["bash", "-c", line], cwd=td, capture_output=True, text=True, timeout=10)
            out.append({"cmd": cmd, "out": (r.stdout or r.stderr).rstrip("\n")})
    return {"input": textwrap.dedent(input_text).strip("\n"), "stages": out}


def run_bash(script, files=None):
    with tempfile.TemporaryDirectory() as td:
        for name, content in (files or {}).items():
            p = os.path.join(td, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(textwrap.dedent(content).strip("\n") + "\n")
        r = subprocess.run(["bash", "-c", textwrap.dedent(script)], cwd=td, capture_output=True, text=True, timeout=10, env={"PATH": os.environ["PATH"], "HOME": td, "LC_ALL": "C"})
        return (r.stdout + r.stderr).rstrip("\n")
