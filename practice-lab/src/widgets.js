'use strict';
/* ---------- interactive visual widgets used inside lessons ---------- */
const PAL = ['#3566d3', '#c9741a', '#2a8a57', '#7b54c9', '#c23b4e', '#0b7a87'];
function wbox(kind, title, ...kids) {
  return h('figure.widget.w-' + kind, h('figcaption', h('span.tag', { text: 'Try it' }), h('span', { text: title || '' })), ...kids);
}
function btnrow(opts, cur, on, cls) {
  const row = h('div.seg' + (cls ? '.' + cls : ''), { role: 'group' });
  opts.forEach((o) => {
    const b = h('button', { type: 'button', class: o === cur ? 'on' : '', text: o, onclick: () => { Array.from(row.children).forEach((c) => c.classList.toggle('on', c === b)); on(o); } });
    row.appendChild(b);
  });
  return row;
}
function miniTable(cols, rows, o) {
  o = o || {};
  const t = h('table.mini');
  t.appendChild(h('thead', h('tr', cols.map((c) => h('th', { text: c })))));
  const tb = h('tbody');
  rows.forEach((r, ri) => {
    const tr = h('tr', { class: (o.cls && o.cls[ri]) || '' });
    r.forEach((v) => tr.appendChild(h('td', { text: v === null || v === undefined ? 'NULL' : String(v), class: v === null ? 'null' : '' })));
    tb.appendChild(tr);
  });
  t.appendChild(tb);
  return h('div.tscroll', t);
}

const Widgets = {
  /* ---- step through code ---- */
  trace(d) {
    let i = 0; let timer = null;
    const lines = d.code.replace(/\n$/, '').split('\n');
    const code = h('div.trace-code.cm-s-sr');
    const rows = lines.map((ln, k) => { const r = h('div.tl', h('span.ln', { text: k + 1 }), highlightInto(h('span.lt'), ln || ' ', d.lang || 'python')); code.appendChild(r); return r; });
    const vars = h('div.trace-vars'); const out = h('pre.trace-out'); const note = h('div.trace-note'); const stack = h('div.trace-stack');
    const ids = {}; let nid = 0;
    const slider = h('input', { type: 'range', min: 0, max: d.steps.length - 1, value: 0, 'aria-label': 'Step', oninput: (e) => { i = +e.target.value; draw(); } });
    const count = h('span.muted');
    const draw = () => {
      const st = d.steps[i];
      rows.forEach((r, k) => r.classList.toggle('cur', k + 1 === st.l));
      const cur = rows[st.l - 1]; if (cur && cur.scrollIntoView && false) cur.scrollIntoView({ block: 'nearest' });
      clear(vars);
      const names = Object.keys(st.v || {});
      if (!names.length) vars.appendChild(h('div.muted', { text: 'No variables yet' }));
      names.forEach((n) => {
        const v = st.v[n]; let badge = null;
        if (v.i) { if (!(v.i in ids)) ids[v.i] = ++nid; badge = h('span.idb', { style: { background: PAL[(ids[v.i] - 1) % PAL.length] }, title: 'Same colour = same object in memory', text: '#' + ids[v.i] }); }
        vars.appendChild(h('div.var', h('span.vn', { text: n }), h('span.vv', { text: v.r }), badge));
      });
      out.textContent = st.o || ''; out.hidden = !st.o;
      stack.textContent = st.s && st.s.length ? 'Call stack: ' + st.s.join(' → ') : '';
      note.textContent = st.n || ''; note.hidden = !st.n;
      slider.value = i; count.textContent = 'Step ' + (i + 1) + ' of ' + d.steps.length;
      prev.disabled = i === 0; next.disabled = i === d.steps.length - 1;
    };
    const stop = () => { clearInterval(timer); timer = null; play.textContent = 'Play'; };
    const prev = h('button.btn.ghost.sm', { type: 'button', text: 'Back', onclick: () => { stop(); if (i > 0) { i--; draw(); } } });
    const next = h('button.btn.sm', { type: 'button', text: 'Next line', onclick: () => { stop(); if (i < d.steps.length - 1) { i++; draw(); } } });
    const play = h('button.btn.ghost.sm', { type: 'button', text: 'Play', onclick: () => {
      if (timer) return stop(); play.textContent = 'Pause';
      timer = setInterval(() => { if (i < d.steps.length - 1) { i++; draw(); } else stop(); }, 900);
    } });
    const el = wbox('trace', d.title || 'Step through the code', code, h('div.trace-ctl', prev, next, play, count), slider, stack, vars, out, note);
    draw(); return el;
  },

  /* ---- slicing ---- */
  slice(d) {
    const seq = d.seq || 'MACHINE'; const arr = Array.from(seq); const n = arr.length;
    const a = h('input', { type: 'number', placeholder: 'start', 'aria-label': 'start', value: d.a ?? '' });
    const b = h('input', { type: 'number', placeholder: 'stop', 'aria-label': 'stop', value: d.b ?? '' });
    const c = h('input', { type: 'number', placeholder: 'step', 'aria-label': 'step', value: d.c ?? '' });
    const cells = h('div.cells'); const expr = h('code.expr'); const res = h('code.res');
    const val = (x) => (x.value === '' ? null : parseInt(x.value, 10));
    const idxs = (len, s, e, st) => {
      st = st === null ? 1 : st; if (st === 0) return null;
      const lo = st > 0 ? 0 : -1, hi = st > 0 ? len : len - 1;
      let S = s === null ? (st > 0 ? 0 : len - 1) : s < 0 ? Math.max(s + len, lo) : Math.min(s, hi);
      let E = e === null ? (st > 0 ? len : -1) : e < 0 ? Math.max(e + len, lo) : Math.min(e, hi);
      const out = []; if (st > 0) for (let k = S; k < E; k += st) out.push(k); else for (let k = S; k > E; k += st) out.push(k);
      return out;
    };
    const draw = () => {
      const s = val(a), e = val(b), st = val(c); const ix = idxs(n, s, e, st);
      clear(cells);
      arr.forEach((ch, k) => cells.appendChild(h('div.cell' + (ix && ix.includes(k) ? '.sel' : ''), h('span.pi', { text: k }), h('span.ch', { text: ch }), h('span.ni', { text: k - n }))));
      const parts = [s === null ? '' : s, e === null ? '' : e].join(':') + (st === null ? '' : ':' + st);
      expr.textContent = (d.name || 'word') + '[' + parts + ']';
      res.textContent = ix === null ? 'ValueError: slice step cannot be zero' : '→ ' + JSON.stringify(typeof seq === 'string' ? ix.map((k) => arr[k]).join('') : ix.map((k) => arr[k]));
    };
    [a, b, c].forEach((x) => x.addEventListener('input', draw));
    const el = wbox('slice', d.title || 'Slice explorer', h('div.slice-in', h('span.mono', { text: (d.name || 'word') + '[' }), a, h('span.mono', { text: ':' }), b, h('span.mono', { text: ':' }), c, h('span.mono', { text: ']' })), cells, h('div.slice-out', expr, res), h('p.muted.small', { text: 'Top numbers are indexes from the left, bottom numbers from the right. Leave a box empty to omit it.' }));
    draw(); return el;
  },

  /* ---- NumPy broadcasting ---- */
  broadcast(d) {
    const A = h('input.shape', { value: d.a || '3,1', 'aria-label': 'Shape of A' }), B = h('input.shape', { value: d.b || '1,4', 'aria-label': 'Shape of B' });
    const out = h('div.bc-out'); const grid = h('div.bc-grid');
    const parse = (s) => { const p = s.split(',').map((x) => x.trim()).filter((x) => x !== '').map(Number); return p.every((x) => Number.isInteger(x) && x >= 0 && x < 100) ? p : null; };
    const draw = () => {
      clear(out); clear(grid);
      const a = parse(A.value), b = parse(B.value);
      if (!a || !b) { out.appendChild(h('div.muted', { text: 'Enter shapes like 3,1 or 8,4,2' })); return; }
      const n = Math.max(a.length, b.length); const pa = Array(n - a.length).fill(null).concat(a), pb = Array(n - b.length).fill(null).concat(b);
      const res = []; let bad = -1;
      for (let k = 0; k < n; k++) {
        const x = pa[k] === null ? 1 : pa[k], y = pb[k] === null ? 1 : pb[k];
        if (x === y || x === 1 || y === 1) res.push(x === 1 ? y : x); else { res.push('?'); if (bad < 0) bad = k; }
      }
      const row = (label, p) => h('div.bc-row', h('span.bc-l', { text: label }), p.map((v) => h('span.bc-d' + (v === null ? '.pad' : ''), { text: v === null ? '–' : v })));
      out.appendChild(row('A', pa)); out.appendChild(row('B', pb));
      out.appendChild(h('div.bc-row.res', h('span.bc-l', { text: 'out' }), res.map((v, k) => h('span.bc-d' + (k === bad ? '.bad' : '.ok'), { text: v }))));
      out.appendChild(h('div.bc-msg' + (bad >= 0 ? '.bad' : '.ok'), { text: bad >= 0 ? 'Error: dimension ' + (bad + 1) + ' has ' + pa[bad] + ' vs ' + pb[bad] + '. They must be equal, or one must be 1.' : 'Broadcasts to shape (' + res.join(', ') + (res.length === 1 ? ',' : '') + ')' }));
      if (bad < 0 && res.length <= 2 && sum(res) <= 20) {
        const r = res.length === 1 ? [1, res[0]] : res;
        grid.style.setProperty('--cols', r[1]);
        for (let i = 0; i < r[0]; i++) for (let j = 0; j < r[1]; j++) grid.appendChild(h('span.bc-cell', { style: { background: PAL[(i * 2 + j) % PAL.length] + '33' }, text: i + ',' + j }));
      }
    };
    [A, B].forEach((x) => x.addEventListener('input', draw));
    const presets = h('div.seg', ['3,1 | 1,4', '5,3 | 3', '4,3 | 4', '2,3,4 | 3,4', '8,1,6 | 7,1'].map((p) => h('button', { type: 'button', text: p.replace(' | ', ' + '), onclick: () => { const q = p.split(' | '); A.value = q[0]; B.value = q[1]; draw(); } })));
    const el = wbox('broadcast', d.title || 'Will these shapes broadcast?', h('div.bc-in', h('label', 'A ', A), h('label', 'B ', B)), presets, out, grid, h('p.muted.small', { text: 'Rule: line the shapes up from the right. Each pair of sizes must match, or one of them must be 1.' }));
    draw(); return el;
  },

  /* ---- tensor shape flow (PyTorch) ---- */
  shapeflow(d) {
    const inp = h('input.shape', { value: d.input || '32,3,28,28', 'aria-label': 'Input shape' });
    const list = h('div.sf-list'); const layers = d.layers.slice();
    const parseShape = (s) => { const p = s.split(',').map((x) => x.trim()).filter(Boolean).map(Number); return p.every(Number.isInteger) ? p : null; };
    const prod = (a) => a.reduce((x, y) => x * y, 1);
    const apply = (sh, spec) => {
      const m = /^(\w+)\s*(?:\((.*)\))?$/.exec(spec.trim()); if (!m) return { err: 'Cannot read this layer.' };
      const name = m[1], args = (m[2] || '').split(',').map((x) => x.trim()).filter(Boolean);
      const N = args.map((x) => (/^-?\d+$/.test(x) ? parseInt(x, 10) : x));
      const last = sh[sh.length - 1];
      switch (name) {
        case 'Linear': if (last !== N[0]) return { err: 'Linear expects last dim ' + N[0] + ' but got ' + last + '.' }; return { sh: sh.slice(0, -1).concat([N[1]]) };
        case 'Flatten': { const s = N.length ? N[0] : 1; return { sh: sh.slice(0, s).concat([prod(sh.slice(s))]) }; }
        case 'Conv2d': { if (sh.length !== 4) return { err: 'Conv2d needs a 4D input (N, C, H, W); got ' + sh.length + 'D.' }; if (sh[1] !== N[0]) return { err: 'Conv2d expects ' + N[0] + ' input channels but got ' + sh[1] + '.' };
          const k = N[2], s = N[3] || 1, p = N[4] || 0; const f = (x) => Math.floor((x + 2 * p - k) / s) + 1; return { sh: [sh[0], N[1], f(sh[2]), f(sh[3])] }; }
        case 'MaxPool2d': { if (sh.length !== 4) return { err: 'MaxPool2d needs a 4D input.' }; const k = N[0], s = N[1] || k; const f = (x) => Math.floor((x - k) / s) + 1; return { sh: [sh[0], sh[1], f(sh[2]), f(sh[3])] }; }
        case 'AdaptiveAvgPool2d': return { sh: [sh[0], sh[1], N[0], N[0]] };
        case 'ReLU': case 'Dropout': case 'Sigmoid': case 'Softmax': case 'LayerNorm': case 'BatchNorm2d': return { sh };
        case 'Embedding': return { sh: sh.concat([N[1]]) };
        case 'unsqueeze': { const dd = N[0] < 0 ? sh.length + 1 + N[0] : N[0]; const o = sh.slice(); o.splice(dd, 0, 1); return { sh: o }; }
        case 'squeeze': return { sh: sh.filter((x) => x !== 1) };
        case 'view': case 'reshape': { const tot = prod(sh); const neg = N.indexOf(-1); const known = prod(N.filter((x) => x !== -1)); if (neg >= 0) { if (known === 0 || tot % known) return { err: 'Cannot infer -1: ' + tot + ' elements do not divide by ' + known + '.' }; const o = N.slice(); o[neg] = tot / known; return { sh: o }; } if (known !== tot) return { err: 'view needs ' + tot + ' elements but ' + known + ' were asked for.' }; return { sh: N }; }
        case 'transpose': { const o = sh.slice(); const x = N[0] < 0 ? o.length + N[0] : N[0], y = N[1] < 0 ? o.length + N[1] : N[1]; [o[x], o[y]] = [o[y], o[x]]; return { sh: o }; }
        case 'permute': { if (N.length !== sh.length) return { err: 'permute needs ' + sh.length + ' axes.' }; return { sh: N.map((x) => sh[x < 0 ? sh.length + x : x]) }; }
        case 'mean': case 'sum': { const dd = N[0] < 0 ? sh.length + N[0] : N[0]; const o = sh.slice(); o.splice(dd, 1); return { sh: o }; }
        default: return { err: 'Unknown layer ' + name };
      }
    };
    const draw = () => {
      clear(list); let sh = parseShape(inp.value);
      if (!sh || !sh.length) { list.appendChild(h('div.muted', { text: 'Enter a shape like 32,3,28,28' })); return; }
      list.appendChild(h('div.sf-row', h('span.sf-op', { text: 'input' }), h('span.sf-sh', { text: '(' + sh.join(', ') + ')' })));
      let failed = false;
      layers.forEach((spec) => {
        const row = h('div.sf-row' + (failed ? '.skip' : ''));
        if (failed) { row.appendChild(h('span.sf-op', { text: spec })); row.appendChild(h('span.sf-sh', { text: '' })); }
        else {
          const r = apply(sh, spec);
          if (r.err) { failed = true; row.classList.add('bad'); row.appendChild(h('span.sf-op', { text: spec })); row.appendChild(h('span.sf-sh', { text: 'Error: ' + r.err })); }
          else { sh = r.sh; row.appendChild(h('span.sf-op', { text: spec })); row.appendChild(h('span.sf-sh', { text: '(' + sh.join(', ') + ')' })); }
        }
        list.appendChild(row);
      });
    };
    inp.addEventListener('input', draw);
    const el = wbox('shapeflow', d.title || 'Follow the tensor shape', h('label.sf-in', 'Input shape ', inp), list, h('p.muted.small', { text: d.note || 'Change the input shape. Watch where a layer stops accepting it.' }));
    draw(); return el;
  },

  /* ---- SQL joins ---- */
  join(d) {
    let kind = 'INNER';
    const L = d.left, Rr = d.right; const [lk, rk] = d.on;
    const li = L.cols.indexOf(lk), ri = Rr.cols.indexOf(rk);
    const res = h('div'); const lt = h('div'), rt = h('div');
    const draw = () => {
      const out = []; const lm = new Set(), rm = new Set();
      L.rows.forEach((lr, a) => Rr.rows.forEach((rr, b) => { if (lr[li] !== null && lr[li] === rr[ri]) { out.push(lr.concat(rr)); lm.add(a); rm.add(b); } }));
      if (kind === 'LEFT' || kind === 'FULL') L.rows.forEach((lr, a) => { if (!lm.has(a)) out.push(lr.concat(Rr.cols.map(() => null))); });
      if (kind === 'RIGHT' || kind === 'FULL') Rr.rows.forEach((rr, b) => { if (!rm.has(b)) out.push(L.cols.map(() => null).concat(rr)); });
      mount(lt, h('h4', { text: L.name }), miniTable(L.cols, L.rows, { cls: L.rows.map((_, a) => (lm.has(a) ? 'hit' : (kind === 'LEFT' || kind === 'FULL' ? 'keep' : 'miss'))) }));
      mount(rt, h('h4', { text: Rr.name }), miniTable(Rr.cols, Rr.rows, { cls: Rr.rows.map((_, b) => (rm.has(b) ? 'hit' : (kind === 'RIGHT' || kind === 'FULL' ? 'keep' : 'miss'))) }));
      mount(res, h('h4', { text: 'Result of ' + kind + ' JOIN: ' + out.length + ' rows' }), miniTable(L.cols.map((c) => L.name + '.' + c).concat(Rr.cols.map((c) => Rr.name + '.' + c)), out));
    };
    const el = wbox('join', d.title || 'See how each join treats unmatched rows', h('code.sqlline', { text: 'SELECT * FROM ' + L.name + ' ' + 'JOIN ' + Rr.name + ' ON ' + L.name + '.' + lk + ' = ' + Rr.name + '.' + rk }), btnrow(['INNER', 'LEFT', 'RIGHT', 'FULL'], kind, (k) => { kind = k; draw(); }), h('div.two', lt, rt), res, h('p.muted.small', { text: 'Green rows found a partner. Amber rows are kept with NULLs. Grey rows are dropped.' }));
    draw(); return el;
  },

  /* ---- GROUP BY ---- */
  groupby(d) {
    let agg = 'COUNT'; let grouped = false;
    const t = h('div'), r = h('div');
    const gi = d.cols.indexOf(d.group), vi = d.cols.indexOf(d.value);
    const groups = uniq(d.rows.map((x) => x[gi]));
    const calc = (vals) => agg === 'COUNT' ? vals.length : agg === 'SUM' ? sum(vals) : agg === 'AVG' ? Math.round(avg(vals) * 100) / 100 : agg === 'MAX' ? Math.max(...vals) : Math.min(...vals);
    const draw = () => {
      const rows = grouped ? d.rows.slice().sort((a, b) => groups.indexOf(a[gi]) - groups.indexOf(b[gi])) : d.rows;
      const tb = miniTable(d.cols, rows); Array.from(tb.querySelectorAll('tbody tr')).forEach((tr, k) => { tr.style.borderLeft = '5px solid ' + PAL[groups.indexOf(rows[k][gi]) % PAL.length]; });
      mount(t, tb);
      const out = groups.map((g) => [g, calc(d.rows.filter((x) => x[gi] === g).map((x) => x[vi]))]);
      mount(r, h('code.sqlline', { text: 'SELECT ' + d.group + ', ' + agg + '(' + (agg === 'COUNT' ? '*' : d.value) + ') FROM ' + d.table + ' GROUP BY ' + d.group + ';' }), grouped ? miniTable([d.group, agg + '(' + (agg === 'COUNT' ? '*' : d.value) + ')'], out) : h('p.muted', { text: 'Press "Group the rows" to collapse each colour into one output row.' }));
    };
    const gb = h('button.btn.sm', { type: 'button', text: 'Group the rows', onclick: () => { grouped = !grouped; gb.textContent = grouped ? 'Ungroup' : 'Group the rows'; draw(); } });
    const el = wbox('groupby', d.title || 'Watch GROUP BY collapse rows', h('div.ctlrow', btnrow(['COUNT', 'SUM', 'AVG', 'MAX'], agg, (a) => { agg = a; draw(); }), gb), t, r);
    draw(); return el;
  },

  /* ---- window functions ---- */
  window(d) {
    let fn = 'ROW_NUMBER'; let part = true;
    const box = h('div'); const code = h('code.sqlline');
    const draw = () => {
      const pi = d.cols.indexOf(d.part), oi = d.cols.indexOf(d.order), vi = d.cols.indexOf(d.value);
      const rows = d.rows.slice().sort((a, b) => (part ? (a[pi] < b[pi] ? -1 : a[pi] > b[pi] ? 1 : 0) : 0) || b[oi] - a[oi]);
      const calc = []; const cnt = {}; const run = {}; const prev = {}; const rank = {}; const lastv = {};
      rows.forEach((r, k) => {
        const key = part ? r[pi] : '*'; cnt[key] = (cnt[key] || 0) + 1; run[key] = (run[key] || 0) + r[vi];
        if (lastv[key] !== r[oi]) { rank[key] = cnt[key]; lastv[key] = r[oi]; }
        calc.push(fn === 'ROW_NUMBER' ? cnt[key] : fn === 'RANK' ? rank[key] : fn === 'SUM (running)' ? run[key] : (prev[key] === undefined ? null : prev[key]));
        prev[key] = r[vi];
      });
      const label = fn === 'SUM (running)' ? 'running_total' : fn === 'LAG' ? 'prev_value' : fn.toLowerCase();
      const body = rows.map((r, k) => r.concat([calc[k]]));
      const cls = rows.map((r, k) => (part && k > 0 && rows[k - 1][pi] !== r[pi] ? 'sep' : ''));
      const call = fn === 'ROW_NUMBER' ? 'ROW_NUMBER()' : fn === 'RANK' ? 'RANK()' : fn === 'LAG' ? 'LAG(' + d.value + ')' : 'SUM(' + d.value + ')';
      code.textContent = 'SELECT *, ' + call + ' OVER (' + (part ? 'PARTITION BY ' + d.part + ' ' : '') + 'ORDER BY ' + d.order + ' DESC) AS ' + label + ' FROM ' + d.table + ';';
      mount(box, miniTable(d.cols.concat([label]), body, { cls }));
    };
    const pbtn = h('button.btn.ghost.sm', { type: 'button', text: 'Partition: on', onclick: () => { part = !part; pbtn.textContent = 'Partition: ' + (part ? 'on' : 'off'); draw(); } });
    const el = wbox('window', d.title || 'Windows keep the rows', h('div.ctlrow', btnrow(['ROW_NUMBER', 'RANK', 'SUM (running)', 'LAG'], fn, (f) => { fn = f; draw(); }), pbtn), code, box);
    draw(); return el;
  },

  /* ---- Docker layer cache ---- */
  layers(d) {
    let v = 0; let changed = d.variants[0].lines.length - 1;
    const stack = h('div.layers'); const msg = h('div.lay-msg');
    const draw = () => {
      const lines = d.variants[v].lines; clear(stack);
      if (changed >= lines.length) changed = lines.length - 1;
      let cost = 0;
      lines.forEach((ln, k) => {
        const rebuild = k >= changed; if (rebuild) cost += ln.cost || 1;
        stack.appendChild(h('button.layer' + (rebuild ? '.rebuild' : '.cached') + (k === changed ? '.changed' : ''), { type: 'button', onclick: () => { changed = k; draw(); } },
          h('code', { text: ln.ins }), h('span.lay-st', { text: k === changed ? 'changed' : rebuild ? 'rebuilds' : 'cached' }), h('span.lay-c', { text: rebuild ? '~' + (ln.cost || 1) + 's' : '0s' })));
      });
      msg.textContent = 'Editing line ' + (changed + 1) + ' rebuilds it and everything below it: about ' + cost + ' s.';
    };
    const tabs = btnrow(d.variants.map((x) => x.name), d.variants[0].name, (n) => { v = d.variants.findIndex((x) => x.name === n); changed = d.variants[v].lines.length - 1; draw(); });
    const el = wbox('layers', d.title || 'Which layers rebuild?', tabs, h('p.small', { text: 'Tap the line you edit. Docker reuses every layer above it.' }), stack, msg);
    draw(); return el;
  },

  /* ---- pipeline stepper ---- */
  pipe(d) {
    let i = 0; const stage = h('div.pipe-stages'); const out = h('pre.pipe-out'); const inp = h('pre.pipe-in');
    const draw = () => {
      clear(stage);
      d.stages.forEach((s, k) => stage.appendChild(h('button.pstage' + (k <= i ? '.on' : ''), { type: 'button', onclick: () => { i = k; draw(); } }, h('code', { text: (k ? '| ' : '') + s.cmd }))));
      out.textContent = d.stages[i].out; inp.textContent = d.input || '';
    };
    const el = wbox('pipe', d.title || 'Follow the data through the pipe', d.input ? h('div.pipe-lab', 'Input file') : null, d.input ? inp : null, h('p.small', { text: 'Tap a stage to see what comes out of it.' }), stage, h('div.pipe-lab', 'Output after this stage'), out);
    draw(); return el;
  },

  /* ---- regex tester ---- */
  regex(d) {
    const pat = h('input.mono', { value: d.pattern || '', 'aria-label': 'Pattern', spellcheck: 'false' });
    const txt = h('textarea.mono', { rows: 4, 'aria-label': 'Text', spellcheck: 'false' }); txt.value = d.text || '';
    const view = h('pre.rx-view'); const info = h('div.rx-info');
    const draw = () => {
      clear(view); clear(info);
      let re; try { re = new RegExp(pat.value, d.flags || 'g'); } catch (e) { info.appendChild(h('div.bc-msg.bad', { text: 'Invalid pattern: ' + e.message })); view.textContent = txt.value; return; }
      const t = txt.value; let last = 0, n = 0; let m; const g = new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g'); const groups = [];
      while ((m = g.exec(t)) && n < 200) {
        if (m[0] === '') { g.lastIndex++; continue; }
        view.appendChild(document.createTextNode(t.slice(last, m.index))); view.appendChild(h('mark.m' + (n % 2), { text: m[0] })); last = m.index + m[0].length; n++;
        if (m.length > 1 && groups.length < 6) groups.push(m.slice(1));
      }
      view.appendChild(document.createTextNode(t.slice(last)));
      info.appendChild(h('div', { text: n + ' match' + (n === 1 ? '' : 'es') }));
      groups.forEach((gs, k) => info.appendChild(h('div.muted.small', { text: 'match ' + (k + 1) + ' groups: ' + JSON.stringify(gs) })));
    };
    [pat, txt].forEach((x) => x.addEventListener('input', draw));
    const el = wbox('regex', d.title || 'Test a pattern', h('label', 'Pattern ', pat), h('label', 'Text', txt), view, info, h('p.muted.small', { text: 'This tester uses the browser’s regex engine. Basics match Python’s re module.' }));
    draw(); return el;
  },

  /* ---- search cost ---- */
  search(d) {
    const n = d.n || 16; const keys = Array.from({ length: n }, (_, k) => (k + 1) * 3);
    let target = keys[Math.floor(n * 0.7)];
    const sel = h('input', { type: 'range', min: 0, max: n - 1, value: Math.floor(n * 0.7), 'aria-label': 'Row to look up', oninput: (e) => { target = keys[+e.target.value]; draw(); } });
    const a = h('div.cells.small'), b = h('div.cells.small'), msg = h('div.bc-msg.ok');
    const draw = () => {
      const lin = keys.indexOf(target) + 1; let lo = 0, hi = n - 1, steps = 0; const visited = [];
      while (lo <= hi) { const mid = (lo + hi) >> 1; steps++; visited.push(mid); if (keys[mid] === target) break; if (keys[mid] < target) lo = mid + 1; else hi = mid - 1; }
      mount(a, ...keys.map((k, i) => h('div.cell' + (i < lin ? '.sel' : ''), h('span.ch', { text: k }))));
      mount(b, ...keys.map((k, i) => h('div.cell' + (visited.includes(i) ? '.sel' : ''), h('span.ch', { text: k }))));
      msg.textContent = 'Looking for id ' + target + ': full scan reads ' + lin + ' rows, an index lookup reads ' + steps + '. With a million rows that is up to 1,000,000 vs about 20.';
    };
    const el = wbox('search', d.title || 'Scan vs index', h('label', 'Row to find ', sel), h('div.pipe-lab', 'Full table scan (no index)'), a, h('div.pipe-lab', 'Index lookup (sorted structure)'), b, msg);
    draw(); return el;
  },

  /* ---- k8s label selector ---- */
  selector(d) {
    const sel = Object.assign({}, d.selector); const keys = uniq(d.pods.flatMap((p) => Object.keys(p.labels).map((k) => k + '=' + p.labels[k])));
    const active = new Set(Object.keys(sel).map((k) => k + '=' + sel[k]));
    const pods = h('div.pods'); const code = h('code.sqlline'); const msg = h('div.bc-msg');
    const draw = () => {
      clear(pods); const need = Array.from(active);
      let hits = 0;
      d.pods.forEach((p) => {
        const ok = need.every((k) => { const [a, b] = k.split('='); return p.labels[a] === b; }); if (ok) hits++;
        pods.appendChild(h('div.pod' + (ok ? '.hit' : ''), h('strong', { text: p.name }), h('div.small', Object.keys(p.labels).map((k) => h('span.lab' + (active.has(k + '=' + p.labels[k]) ? '.on' : ''), { text: k + ': ' + p.labels[k] })))));
      });
      code.textContent = 'selector:' + (need.length ? '\n' + need.map((k) => '  ' + k.replace('=', ': ')).join('\n') : ' {}');
      msg.className = 'bc-msg ' + (hits ? 'ok' : 'bad'); msg.textContent = hits + ' of ' + d.pods.length + ' pods receive traffic. A pod matches only if it has ALL the selector labels.';
    };
    const chips = h('div.chips', keys.map((k) => h('button.chip' + (active.has(k) ? '.on' : ''), { type: 'button', text: k, onclick: (e) => { if (active.has(k)) active.delete(k); else active.add(k); e.currentTarget.classList.toggle('on'); draw(); } })));
    const el = wbox('selector', d.title || 'Which pods does the Service select?', h('p.small', { text: 'Toggle selector labels.' }), chips, pods, h('pre.code.cm-s-sr', code), msg);
    draw(); return el;
  },

  /* ---- classification metrics ---- */
  metrics(d) {
    const data = d.data; let th = 0.5;
    const sl = h('input', { type: 'range', min: 0, max: 100, value: 50, 'aria-label': 'Threshold', oninput: (e) => { th = e.target.value / 100; draw(); } });
    const strip = h('div.mstrip'); const cm = h('div.cmat'); const stats = h('div.mstats');
    const draw = () => {
      let tp = 0, fp = 0, fn = 0, tn = 0; clear(strip);
      data.slice().sort((a, b) => a[0] - b[0]).forEach(([s, y]) => {
        const pred = s >= th ? 1 : 0; if (pred && y) tp++; else if (pred && !y) fp++; else if (!pred && y) fn++; else tn++;
        strip.appendChild(h('span.dot' + (y ? '.pos' : '.neg') + (pred ? '.pp' : ''), { title: 'score ' + s + ', true label ' + y }));
      });
      const P = tp + fp ? tp / (tp + fp) : 0, Rr = tp + fn ? tp / (tp + fn) : 0, F = P + Rr ? 2 * P * Rr / (P + Rr) : 0;
      mount(cm, h('div.c.tp', h('b', { text: tp }), 'TP'), h('div.c.fp', h('b', { text: fp }), 'FP'), h('div.c.fn', h('b', { text: fn }), 'FN'), h('div.c.tn', h('b', { text: tn }), 'TN'));
      mount(stats, h('div', h('span.muted', 'precision '), h('b', { text: P.toFixed(2) })), h('div', h('span.muted', 'recall '), h('b', { text: Rr.toFixed(2) })), h('div', h('span.muted', 'F1 '), h('b', { text: F.toFixed(2) })), h('div', h('span.muted', 'threshold '), h('b', { text: th.toFixed(2) })));
    };
    const el = wbox('metrics', d.title || 'Move the threshold', h('p.small', { text: 'Each dot is a model score, sorted left to right. Filled = actually positive. Solid ring = predicted positive.' }), strip, sl, h('div.mrow', cm, stats));
    draw(); return el;
  },
};

function makeWidget(block) {
  const f = Widgets[block.kind];
  if (!f) return h('div.muted', { text: '[missing widget: ' + block.kind + ']' });
  try { return f(block.data || {}); } catch (e) { console.error(e); return h('div.muted', { text: '[widget error]' }); }
}
