'use strict';
/* ---------- in-browser runners ---------- */
const Engine = {
  py: {
    state: 'idle', p: null, fn: null, err: '',
    load() {
      if (this.p) return this.p;
      this.state = 'loading';
      this.p = (async () => {
        try {
          await loadScript('vendor/brython.min.js');
          await loadScript('vendor/brython_stdlib.js');
          window.brython({ indexedDB: false });
          const src = await (await fetch('vendor/harness.txt')).text();
          window.__BRYTHON__.runPythonSource(src, 'harness');
          this.fn = window.__BRYTHON__.$getattr(window.__BRYTHON__.imported.harness, 'run');
          const smoke = JSON.parse(this.fn('x = 1', 't("x", 1)'));
          if (smoke.error || !smoke.cases.length || !smoke.cases[0].ok) throw new Error(smoke.error || 'smoke test failed');
          this.state = 'ready';
        } catch (e) {
          this.state = 'failed'; this.err = String((e && e.message) || e);
          throw e;
        }
      })();
      this.p.catch(() => {});
      return this.p;
    },
    async run(code, tests) {
      await this.load();
      try { return JSON.parse(this.fn(code, tests || '')); }
      catch (e) { return { error: 'The Python runner stopped: ' + ((e && e.args && e.args[0]) || e), stdout: '', cases: [] }; }
    },
  },
  sql: {
    state: 'idle', p: null, SQL: null, err: '', cache: {},
    load() {
      if (this.p) return this.p;
      this.state = 'loading';
      this.p = (async () => {
        try {
          await loadScript('vendor/sql-asm.js');
          this.SQL = await window.initSqlJs();
          const db = new this.SQL.Database(); db.exec('select 1'); db.close();
          this.state = 'ready';
        } catch (e) { this.state = 'failed'; this.err = String((e && e.message) || e); throw e; }
      })();
      this.p.catch(() => {});
      return this.p;
    },
    open(dataset) {
      const db = new this.SQL.Database();
      db.exec(Cx.datasets[dataset].setup);
      return db;
    },
    exec(db, text) {
      try {
        const res = db.exec(text);
        return { res: res.length ? res[res.length - 1] : null, all: res };
      } catch (e) { return { error: String((e && e.message) || e) }; }
    },
    async describe(dataset) {
      if (this.cache[dataset]) return this.cache[dataset];
      await this.load();
      const db = this.open(dataset); const out = [];
      const names = db.exec("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by rowid");
      (names.length ? names[0].values : []).forEach(([name]) => {
        const info = db.exec('pragma table_info(' + name + ')')[0];
        const rows = db.exec('select * from ' + name + ' limit 4')[0];
        const cnt = db.exec('select count(*) from ' + name)[0].values[0][0];
        out.push({ name, cols: info.values.map((r) => ({ n: r[1], t: r[2], pk: r[5] })), rows: rows ? rows.values : [], count: cnt });
      });
      db.close(); this.cache[dataset] = out; return out;
    },
    /* run learner SQL against a dataset; mode 'dml' runs `after` query to read results */
    async runUser(ex, text) {
      await this.load();
      const db = this.open(ex.dataset);
      try {
        const r = this.exec(db, text);
        if (r.error) return { error: r.error };
        if (ex.after) { const a = this.exec(db, ex.after); return a.error ? { error: a.error } : { res: a.res }; }
        return { res: r.res };
      } finally { db.close(); }
    },
    async expected(ex) {
      await this.load();
      const db = this.open(ex.dataset);
      try {
        const r = this.exec(db, ex.solution);
        if (r.error) return { error: r.error };
        if (ex.after) { const a = this.exec(db, ex.after); return a.error ? { error: a.error } : { res: a.res }; }
        return { res: r.res };
      } finally { db.close(); }
    },
  },
};

const normCell = (v) => (v === null ? null : typeof v === 'number' ? Math.round(v * 1e6) / 1e6 : String(v));
function sqlCompare(exp, got, ex) {
  if (!got) return { ok: false, msg: 'Your query did not return a result table. Make sure the last statement is a SELECT.' };
  if (got.columns.length !== exp.columns.length) return { ok: false, msg: 'Your result has ' + got.columns.length + ' column(s); the expected result has ' + exp.columns.length + '.' };
  if (ex.names && got.columns.map((c) => c.toLowerCase()).join() !== exp.columns.map((c) => c.toLowerCase()).join()) return { ok: false, msg: 'Column names should be: ' + exp.columns.join(', ') + '. You returned: ' + got.columns.join(', ') + '.' };
  if (got.values.length !== exp.values.length) return { ok: false, msg: 'Your result has ' + got.values.length + ' row(s); the expected result has ' + exp.values.length + '.' };
  const a = got.values.map((r) => JSON.stringify(r.map(normCell))), b = exp.values.map((r) => JSON.stringify(r.map(normCell)));
  const aa = ex.ordered ? a : a.slice().sort(), bb = ex.ordered ? b : b.slice().sort();
  for (let i = 0; i < aa.length; i++) {
    if (aa[i] !== bb[i]) return { ok: false, msg: ex.ordered ? 'The rows are not in the expected order or have different values (first difference at row ' + (i + 1) + ').' : 'Same shape, but some values differ from the expected result.' };
  }
  return { ok: true };
}

/* ---------- editor ---------- */
const CM_MODE = { python: 'python', sql: 'text/x-pgsql', bash: 'shell', sh: 'shell', yaml: 'yaml', dockerfile: 'dockerfile', json: { name: 'javascript', json: true }, toml: 'toml', markdown: 'markdown', hcl: 'hcl', regex: null, text: null, output: null };
function defineHcl() {
  if (!window.CodeMirror || CodeMirror.modes.hcl) return;
  const kw = /^(resource|variable|output|provider|module|data|locals|terraform|required_providers|required_version|backend|lifecycle|depends_on|for_each|count|dynamic|content|provisioner|moved|import)\b/;
  CodeMirror.defineMode('hcl', () => ({
    startState: () => ({ blk: false }),
    token(stream, st) {
      if (st.blk) { if (stream.skipTo('*/')) { stream.next(); stream.next(); st.blk = false; } else stream.skipToEnd(); return 'comment'; }
      if (stream.eatSpace()) return null;
      if (stream.match('/*')) { st.blk = true; return 'comment'; }
      if (stream.match('#') || stream.match('//')) { stream.skipToEnd(); return 'comment'; }
      if (stream.match(/^"(?:[^"\\]|\\.)*"/)) return 'string';
      if (stream.match(/^<<-?\w+/)) return 'string';
      if (stream.match(/^-?\d+(\.\d+)?\b/)) return 'number';
      if (stream.match(/^(true|false|null)\b/)) return 'atom';
      if (stream.match(kw)) return 'keyword';
      if (stream.match(/^[A-Za-z_][\w-]*(?=\s*=)/)) return 'property';
      if (stream.match(/^(var|local|each|self|module|data|aws_\w+)\.[\w.[\]*-]+/)) return 'variable-2';
      stream.next(); return null;
    },
  }));
}
function highlightInto(el, code, lang) {
  el.textContent = '';
  const mode = CM_MODE[lang];
  if (window.CodeMirror && CodeMirror.runMode && mode) {
    try {
      CodeMirror.runMode(code, mode, (text, style) => {
        if (text === '\n') { el.appendChild(document.createTextNode('\n')); return; }
        if (style) { const s = document.createElement('span'); s.className = 'cm-' + style.replace(/ +/g, ' cm-'); s.textContent = text; el.appendChild(s); } else el.appendChild(document.createTextNode(text));
      });
      return el;
    } catch (e) { /* fall through */ }
  }
  el.textContent = code; return el;
}
function codeBlock(code, lang, opts) {
  opts = opts || {};
  const pre = h('pre.code.cm-s-sr');
  const c = h('code'); pre.appendChild(c);
  highlightInto(c, code.replace(/\n$/, ''), lang);
  const wrap = h('div.codewrap', pre);
  if (opts.label) wrap.insertBefore(h('div.codelabel', { text: opts.label }), pre);
  return wrap;
}
function makeEditor(parent, o) {
  defineHcl();
  o = o || {};
  if (window.CodeMirror) {
    const run = () => { if (o.onRun) o.onRun(); return false; };
    const cm = CodeMirror(parent, {
      value: o.value || '', mode: CM_MODE[o.lang] === undefined ? null : CM_MODE[o.lang], theme: 'sr', lineNumbers: o.lineNumbers !== false,
      indentUnit: o.lang === 'yaml' || o.lang === 'hcl' ? 2 : 4, tabSize: o.lang === 'yaml' || o.lang === 'hcl' ? 2 : 4, indentWithTabs: false, smartIndent: true, matchBrackets: true, autoCloseBrackets: o.lang !== 'markdown',
      lineWrapping: !!o.wrap, readOnly: !!o.readOnly, viewportMargin: Infinity, inputStyle: 'contenteditable',
      extraKeys: {
        Tab: (c) => { if (c.somethingSelected()) c.indentSelection('add'); else c.replaceSelection(Array(c.getOption('indentUnit') + 1).join(' '), 'end'); },
        'Shift-Tab': (c) => c.indentSelection('subtract'), 'Ctrl-Enter': run, 'Cmd-Enter': run,
      },
    });
    cm.getWrapperElement().style.setProperty('--minlines', o.minLines || 6);
    if (o.onChange) cm.on('change', () => o.onChange());
    return { get: () => cm.getValue(), set: (v) => cm.setValue(v), focus: () => cm.focus(), refresh: () => cm.refresh(), el: cm.getWrapperElement(), setReadOnly: (b) => cm.setOption('readOnly', b) };
  }
  const ta = h('textarea.fallback-editor', { spellcheck: 'false', rows: o.minLines || 6 }); ta.value = o.value || '';
  ta.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') { e.preventDefault(); const s = ta.selectionStart; ta.value = ta.value.slice(0, s) + '    ' + ta.value.slice(ta.selectionEnd); ta.selectionStart = ta.selectionEnd = s + 4; }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && o.onRun) { e.preventDefault(); o.onRun(); }
  });
  if (o.onChange) ta.addEventListener('input', () => o.onChange());
  parent.appendChild(ta);
  return { get: () => ta.value, set: (v) => { ta.value = v; }, focus: () => ta.focus(), refresh: () => {}, el: ta, setReadOnly: (b) => { ta.readOnly = b; } };
}
