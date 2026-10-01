"""Test harness shared by the browser (Brython) and the CPython verifier.

run(code, tests) executes a learner's code, then the exercise's test code.
Test code can call: t(expr, want), tx(setup, expr, want), texc(expr, ExcName),
tprint(want) / stdout(), check(label, got, want).
Returns a JSON string: {error, stdout, cases:[{label, ok, got, want, err}]}.
"""
import sys
import json
import re

_LIMIT = 1000000
_ticks = [0]
_MSG = "Your code ran more than 1,000,000 loop steps or calls. Is there an infinite loop, or a very slow approach?"


def _t_():
    _ticks[0] += 1
    if _ticks[0] > _LIMIT:
        raise TimeoutError(_MSG)
    return True


def _g_(it):
    for x in it:
        _ticks[0] += 1
        if _ticks[0] > _LIMIT:
            raise TimeoutError(_MSG)
        yield x


_DEF = re.compile(r"^(\s*)(async\s+)?def\s.*:\s*(#.*)?$")


def guard(code):
    """Make runaway loops and runaway recursion raise TimeoutError instead of freezing the page."""
    lines = code.split("\n")
    out = []
    for k, line in enumerate(lines):
        s = line.lstrip()
        ind = line[: len(line) - len(s)]
        body = s.rstrip()
        if body.startswith("while ") and body.endswith(":"):
            line = ind + "while _t_() and (" + body[6:-1] + "):"
        elif body.startswith("for ") and body.endswith(":") and " in " in body:
            i = body.index(" in ")
            line = ind + body[: i + 4] + "_g_(" + body[i + 4 : -1] + "):"
        out.append(line)
        if _DEF.match(line):
            j = k + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
                j += 1
            if j < len(lines):
                nxt = lines[j]
                nind = nxt[: len(nxt) - len(nxt.lstrip())]
                first = nxt.lstrip()[:3]
                if len(nind) > len(ind) and first not in ('"""', "'''"):
                    out.append(nind + "_t_()")
    return "\n".join(out)


class _Cap:
    def __init__(self):
        self.parts = []

    def write(self, s):
        self.parts.append(str(s))
        return len(s)

    def flush(self):
        pass

    def getvalue(self):
        return "".join(self.parts)


def _eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) == type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-6 * max(1.0, abs(b))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return type(a) == type(b) and len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    return type(a) == type(b) and a == b


def _short(v):
    r = repr(v)
    return r if len(r) <= 200 else r[:197] + "..."


def _err(e):
    return type(e).__name__ + ": " + str(e)


def run(code, tests="", stop_after_user=False):
    res = {"error": None, "stdout": "", "cases": []}
    ns = {"__name__": "__main__", "_t_": _t_, "_g_": _g_}
    cap = _Cap()
    old = sys.stdout
    _ticks[0] = 0
    try:
        sys.stdout = cap
        try:
            compile(code, "<your code>", "exec")
            compiled = compile(guard(code), "<your code>", "exec")
        except SyntaxError as e:
            ln = getattr(e, "lineno", None)
            res["error"] = "SyntaxError: " + str(getattr(e, "msg", e)) + (" (line %s)" % ln if ln else "")
            return json.dumps(res)
        try:
            exec(compiled, ns)
        except BaseException as e:
            res["error"] = _err(e)
        finally:
            sys.stdout = old
        res["stdout"] = cap.getvalue()
        if res["error"] or not tests:
            return json.dumps(res)
        user_out = res["stdout"]

        def add(label, ok, got=None, want=None, err=None):
            res["cases"].append({"label": label, "ok": bool(ok), "got": got, "want": want, "err": err})

        def t(expr, want):
            _ticks[0] = 0
            sys.stdout = _Cap()
            try:
                got = eval(guard(expr), ns)
            except BaseException as e:
                add(expr, False, None, _short(want), _err(e))
                return
            finally:
                sys.stdout = old
            add(expr, _eq(got, want), _short(got), _short(want))

        def tx(setup, expr, want):
            _ticks[0] = 0
            sys.stdout = _Cap()
            try:
                exec(guard(setup), ns)
                got = eval(expr, ns)
            except BaseException as e:
                add(expr, False, None, _short(want), _err(e))
                return
            finally:
                sys.stdout = old
            add(expr, _eq(got, want), _short(got), _short(want))

        def texc(expr, exc):
            _ticks[0] = 0
            sys.stdout = _Cap()
            try:
                eval(guard(expr), ns)
            except BaseException as e:
                ok = isinstance(e, exc)
                add(expr + " raises " + exc.__name__, ok, type(e).__name__, exc.__name__)
                return
            finally:
                sys.stdout = old
            add(expr + " raises " + exc.__name__, False, "no error", exc.__name__)

        def tprint(want, label="printed output"):
            add(label, user_out == want, _short(user_out), _short(want))

        def tcall_out(expr, want):
            """Run expr and compare what it prints."""
            _ticks[0] = 0
            c = _Cap()
            sys.stdout = c
            try:
                eval(guard(expr), ns)
            except BaseException as e:
                sys.stdout = old
                add(expr + " prints", False, None, _short(want), _err(e))
                return
            finally:
                sys.stdout = old
            add(expr + " prints", c.getvalue() == want, _short(c.getvalue()), _short(want))

        def check(label, got, want):
            add(label, _eq(got, want), _short(got), _short(want))

        def _rerun(over):
            src = code
            for k, v in over.items():
                src, n = re.subn(r"(?m)^%s[ \t]*=.*$" % re.escape(k), "%s = %r" % (k, v), src)
                if n == 0:
                    src = "%s = %r\n" % (k, v) + src
            ns2 = {"__name__": "__main__", "_t_": _t_, "_g_": _g_}
            c2 = _Cap()
            _ticks[0] = 0
            sys.stdout = c2
            try:
                exec(compile(guard(src), "<your code>", "exec"), ns2)
            finally:
                sys.stdout = old
            return ns2, c2.getvalue()

        def _lab(over, what):
            return "with " + ", ".join("%s = %r" % (k, v) for k, v in over.items()) + ": " + what

        def tvar(over, expr, want):
            """Re-run the learner's script with new values for top-level variables, then evaluate expr."""
            try:
                ns2, _ = _rerun(over)
                got = eval(expr, ns2)
            except BaseException as e:
                add(_lab(over, expr), False, None, _short(want), _err(e))
                return
            add(_lab(over, expr), _eq(got, want), _short(got), _short(want))

        def tvout(over, want):
            """Re-run with new top-level values and compare the printed output."""
            try:
                _, out = _rerun(over)
            except BaseException as e:
                add(_lab(over, "printed output"), False, None, _short(want), _err(e))
                return
            add(_lab(over, "printed output"), out == want, _short(out), _short(want))

        helpers = {
            "tvar": tvar, "tvout": tvout,
            "t": t, "tx": tx, "texc": texc, "tprint": tprint, "tcall_out": tcall_out,
            "check": check, "stdout": lambda: user_out,
        }
        tns = dict(ns)
        tns.update(helpers)
        ns.update(helpers)
        try:
            exec(tests, ns)
        except BaseException as e:
            res["error"] = "Test runner problem: " + _err(e)
        return json.dumps(res)
    finally:
        sys.stdout = old
