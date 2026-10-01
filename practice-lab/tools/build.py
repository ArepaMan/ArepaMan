#!/usr/bin/env python3
"""Assemble dist/: index.html (page fragment for publishing), test.html (full doc for local tests),
content/*.json, vendor/ engines. Run after tools/make_content.py."""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")
V = os.path.join(ROOT, "vendor")

JS = ["core.js", "srs.js", "engines.js", "widgets.js", "exercise.js", "session.js", "views.js", "main.js"]
CM_FILES = [
    "lib/codemirror.js", "addon/mode/simple.js", "addon/runmode/runmode.js", "addon/edit/closebrackets.js", "addon/edit/matchbrackets.js",
    "mode/meta.js", "mode/xml/xml.js", "mode/javascript/javascript.js", "mode/python/python.js", "mode/sql/sql.js",
    "mode/shell/shell.js", "mode/yaml/yaml.js", "mode/dockerfile/dockerfile.js", "mode/toml/toml.js",
    "mode/markdown/markdown.js",
]


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "vendor"))
    os.makedirs(os.path.join(DIST, "content"))
    # CodeMirror bundle (concatenated UMD files fall back to the global)
    parts = []
    for f in CM_FILES:
        p = os.path.join(V, "cm_src", f)
        if os.path.exists(p):
            parts.append("/* " + f + " */\n" + rd(p))
    with open(os.path.join(DIST, "vendor", "cm.js"), "w", encoding="utf-8") as o:
        o.write("\n;\n".join(parts))
    for f in ["brython.min.js", "brython_stdlib.js", "sql-asm.js"]:
        shutil.copy(os.path.join(V, f), os.path.join(DIST, "vendor", f))
    shutil.copy(os.path.join(SRC, "harness.py"), os.path.join(DIST, "vendor", "harness.txt"))
    for f in sorted(os.listdir(os.path.join(ROOT, "content"))):
        shutil.copy(os.path.join(ROOT, "content", f), os.path.join(DIST, "content", f))
    css = rd(os.path.join(V, "cm_src", "lib", "codemirror.css")) + "\n" + rd(os.path.join(SRC, "style.css"))
    js = "\n".join(rd(os.path.join(SRC, f)) for f in JS)
    fonts = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700'
             '&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">')
    frag = ("<title>Skill Radar</title>\n" + fonts + "\n<style>\n" + css + "\n</style>\n<div id=\"app\"></div>\n"
            "<script src=\"vendor/cm.js\"></script>\n<script>\n" + js + "\n</script>\n")
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as o:
        o.write(frag)
    full = ("<!doctype html><html><head><meta charset=utf8><meta name=viewport content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
            "<style>:root{color-scheme:light}body{margin:0;font:14px system-ui;background:#fff}[hidden]{display:none!important}</style></head><body>"
            + frag + "</body></html>")
    with open(os.path.join(DIST, "test.html"), "w", encoding="utf-8") as o:
        o.write(full)
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST) for f in fs)
    print("built dist/ (%.1f MB). index.html %.0f KB" % (total / 1e6, os.path.getsize(os.path.join(DIST, "index.html")) / 1e3))


if __name__ == "__main__":
    main()
