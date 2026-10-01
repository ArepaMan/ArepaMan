#!/usr/bin/env bash
# Fetch the self-hosted engines (Brython, sql.js asm build, CodeMirror 5) into vendor/ via npm.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); cd "$tmp"; npm init -y >/dev/null
npm install brython@3.14.3 sql.js@1.14.2 codemirror@5.65.19 >/dev/null
cd - >/dev/null; mkdir -p vendor
cp "$tmp/node_modules/brython/brython.min.js" "$tmp/node_modules/brython/brython_stdlib.js" "$tmp/node_modules/sql.js/dist/sql-asm.js" vendor/
rm -rf vendor/cm_src; mkdir -p vendor/cm_src; cp -r "$tmp/node_modules/codemirror/lib" "$tmp/node_modules/codemirror/mode" "$tmp/node_modules/codemirror/addon" vendor/cm_src/
echo "vendor ready"
