'use strict';
/* ---------- lesson rendering ---------- */
function trackChip(tid) { const t = Cx.tracks[tid]; return h('span.chip.tr-' + tid, { text: t.short || t.name }); }
function phaseTags(arr) { return (arr || []).map((p) => { const ph = Cx.phases.find((x) => x.id === p); return h('span.chip.phase', { title: 'Prepares you for: ' + (ph ? ph.name : p), text: ph ? ph.short : p }); }); }

function quickCheck(b) {
  const order = shuffle(b.choices.map((c, i) => i)); const fb = h('div.quick-fb', { 'aria-live': 'polite' }); let done = false;
  const box = h('div.quick', h('div.quick-q', { html: rich(b.q) }));
  const list = h('div.choices');
  order.forEach((i) => {
    const btn = h('button.choice', { type: 'button', html: rich(b.choices[i]), onclick: () => {
      if (done) return;
      if (i === b.a) { done = true; btn.classList.add('right'); fb.className = 'quick-fb good'; fb.innerHTML = rich('Yes. ' + (b.why || '')); }
      else { btn.classList.add('wrong'); btn.disabled = true; fb.className = 'quick-fb bad'; fb.innerHTML = rich('Not that one. Look again.'); }
    } });
    list.appendChild(btn);
  });
  box.appendChild(list); box.appendChild(fb);
  return h('div.quickwrap', h('span.tag', { text: 'Quick check' }), box);
}
function renderBlocks(blocks) {
  const f = document.createDocumentFragment();
  (blocks || []).forEach((b) => {
    let n = null;
    switch (b.t) {
      case 'p': n = R(b.x); break;
      case 'h': n = h('h4.lh', { text: b.x }); break;
      case 'code': n = codeBlock(b.x, b.lang || 'python', { label: b.label }); break;
      case 'viz': n = makeWidget(b); break;
      case 'tip': n = h('div.callout.tip', h('strong', 'Tip'), R(b.x)); break;
      case 'warn': n = h('div.callout.warn', h('strong', 'Watch out'), R(b.x)); break;
      case 'ul': n = h('ul.lul', b.x.map((i) => h('li', { html: rich(i) }))); break;
      case 'table': n = miniTable(b.cols, b.rows); break;
      case 'quick': n = quickCheck(b); break;
      default: break;
    }
    if (n) f.appendChild(n);
  });
  return f;
}
function lessonCard(c, onDone, o) {
  o = o || {};
  const body = h('div.lesson-body'); body.appendChild(renderBlocks(c.lesson.blocks));
  const info = cinfo(c.id);
  return h('article.lesson',
    h('div.chips', trackChip(c.track), h('span.chip', { text: 'Level ' + c.level + ' · ' + Cx.tracks[c.track].levels[c.level - 1].name }), phaseTags(c.phases), h('span.chip.muted', { text: (c.minutes || 3) + ' min' }), info.n ? h('span.chip.st-' + info.state, { text: STATE_LABEL[info.state] }) : h('span.chip.st-new', { text: 'New concept' })),
    h('h2', { text: c.title }), c.lede ? h('p.lede', { html: rich(c.lede) }) : null, body,
    onDone ? h('div.actions', h('button.btn.primary', { type: 'button', text: o.cta || 'Start practising', onclick: onDone })) : null);
}

/* ---------- exercise helpers ---------- */
const TYPE_LABEL = { code: 'Write code', sql: 'Write SQL', predict: 'Predict the output', mcq: 'Choose', fill: 'Fill the blanks', spot: 'Find the bug', order: 'Put in order' };
const MODE_LABEL = { new: 'New', rev: 'Review', int: 'Interview', cp: 'Checkpoint', free: 'Practice' };
const normText = (s) => String(s).replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+$/, '')).join('\n').replace(/^\n+|\n+$/g, '');
const normBlank = (s) => String(s).trim().replace(/\s+/g, ' ');

function renderCases(r) {
  return h('ul.cases', r.cases.map((c) => h('li' + (c.ok ? '.ok' : '.bad'), h('span.mk', { text: c.ok ? '✓' : '✗' }), h('code', { text: c.label }), c.ok ? null : h('div.small', { text: c.err ? 'Error: ' + c.err : 'got ' + c.got + ', expected ' + c.want }))));
}
function resultTable(res, max) {
  if (!res) return h('div.muted', { text: 'No result table.' });
  const rows = res.values.slice(0, max || 30);
  const t = miniTable(res.columns, rows);
  return h('div', t, res.values.length > rows.length ? h('div.muted.small', { text: 'Showing the first ' + rows.length + ' of ' + res.values.length + ' rows.' }) : null);
}

/* ---------- type builders ---------- */
const TYPES = {
  code(ex, X) {
    const host = h('div.editor'); const out = h('div.out', { 'aria-live': 'polite' });
    const ed = makeEditor(host, { lang: 'python', value: ex.starter || '', minLines: ex.lines || 8, onRun: () => X.primary() });
    const busy = h('div.engine', { text: '' }); let ready = Engine.py.state === 'ready';
    const warm = () => { if (Engine.py.state === 'idle') { busy.textContent = 'Starting the Python runner (first time takes a few seconds)…'; } Engine.py.load().then(() => { busy.textContent = ''; ready = true; }).catch(() => { busy.textContent = ''; }); };
    warm();
    const show = (r, withCases) => {
      clear(out);
      if (r.error) out.appendChild(h('div.errbox', h('strong', { text: 'Error' }), h('pre', { text: r.error })));
      if (r.stdout) out.appendChild(h('div.stdout', h('div.small.muted', { text: 'Printed' }), h('pre', { text: r.stdout })));
      if (withCases && r.cases.length) out.appendChild(renderCases(r));
      if (!r.error && !r.stdout && !(withCases && r.cases.length)) out.appendChild(h('div.muted', { text: 'Ran with no output. Use print(...) to see values, or press Check.' }));
    };
    const failedEngine = () => Engine.py.state === 'failed';
    const el = h('div', host, busy, out);
    return {
      node: el, runLabel: 'Run',
      async run() { try { await Engine.py.load(); } catch (e) { return this.selfCheck(); } const r = await Engine.py.run(ed.get(), ''); show(r, false); return null; },
      async check() {
        try { await Engine.py.load(); } catch (e) { return this.selfCheck(); }
        const r = await Engine.py.run(ed.get(), ex.tests); show(r, true);
        if (r.error) return { ok: false, msg: 'Your code raised an error before the tests could finish.' };
        const bad = r.cases.filter((c) => !c.ok).length;
        if (!r.cases.length) return { ok: false, msg: 'No tests ran.' };
        return bad ? { ok: false, msg: bad + ' of ' + r.cases.length + ' checks failed. Read the red lines above.' } : { ok: true };
      },
      selfCheck() { return { self: true, why: 'The in-browser Python runner could not start in this view (' + Engine.py.err + '). Compare your code with the reference and grade yourself honestly.' }; },
      solution: () => h('div', codeBlock(ex.solution, 'python', { label: 'One solution' })),
      retype() { ed.set(ex.starter || ''); clear(out); },
      lock() { ed.setReadOnly(true); }, focus: () => ed.focus(), refresh: () => ed.refresh(),
      hasWork: () => ed.get().trim() !== (ex.starter || '').trim(),
      reset: () => { ed.set(ex.starter || ''); clear(out); },
    };
  },

  sql(ex, X) {
    const host = h('div.editor'); const out = h('div.out', { 'aria-live': 'polite' }); const schema = h('details.schema', { open: window.innerWidth > 720 }, h('summary', 'Tables you can query')); const sbody = h('div.schema-body'); schema.appendChild(sbody);
    const ed = makeEditor(host, { lang: 'sql', value: ex.starter || '', minLines: ex.lines || 6, onRun: () => X.primary() });
    const busy = h('div.engine', { text: 'Loading the SQL engine…' });
    Engine.sql.load().then(async () => { busy.textContent = ''; const d = await Engine.sql.describe(ex.dataset); mount(sbody, ...d.map((t) => h('div.tbl', h('div.tname', h('strong', { text: t.name }), h('span.muted.small', { text: ' ' + t.count + ' rows' })), h('div.small.cols', t.cols.map((c) => h('span.col', { text: c.n + ' ' + (c.t || '').toLowerCase() + (c.pk ? ' (key)' : '') }))), miniTable(t.cols.map((c) => c.n), t.rows)))); }).catch(() => { busy.textContent = ''; mount(sbody, h('div.muted', { text: 'Table preview unavailable.' })); });
    let fails = 0; let expectedBox = null;
    const showRes = (r) => { clear(out); if (r.error) out.appendChild(h('div.errbox', h('strong', 'SQL error'), h('pre', { text: r.error }))); else out.appendChild(h('div', h('div.small.muted', { text: 'Your result' }), resultTable(r.res))); };
    return {
      node: h('div', schema, host, busy, out), runLabel: 'Run query',
      async run() { try { await Engine.sql.load(); } catch (e) { return this.selfCheck(); } const r = await Engine.sql.runUser(ex, ed.get()); showRes(r); return null; },
      async check() {
        try { await Engine.sql.load(); } catch (e) { return this.selfCheck(); }
        const r = await Engine.sql.runUser(ex, ed.get()); showRes(r);
        if (r.error) return { ok: false, msg: 'The query failed. Fix the error above and run it again.' };
        const exp = await Engine.sql.expected(ex);
        const cmp = sqlCompare(exp.res, r.res, ex);
        if (cmp.ok) return { ok: true };
        fails++;
        if (fails >= 2 && !expectedBox) { expectedBox = h('div.expected', h('div.small.muted', { text: 'Expected result (the shape your query should produce)' }), resultTable(exp.res, 12)); out.appendChild(expectedBox); }
        return { ok: false, msg: cmp.msg };
      },
      selfCheck() { return { self: true, why: 'The in-browser SQL engine could not start in this view. Compare with the reference query and grade yourself honestly.' }; },
      solution: () => h('div', codeBlock(ex.solution, 'sql', { label: 'One solution' })),
      retype() { ed.set(ex.starter || ''); clear(out); },
      lock() { ed.setReadOnly(true); }, focus: () => ed.focus(), refresh: () => ed.refresh(),
      hasWork: () => ed.get().trim() !== (ex.starter || '').trim(),
      reset: () => { ed.set(ex.starter || ''); clear(out); },
    };
  },

  predict(ex, X) {
    const ta = h('textarea.answer.mono', { rows: Math.min(8, Math.max(2, (ex.answer.match(/\n/g) || []).length + 2)), placeholder: ex.placeholder || 'Type exactly what is printed (one line per line)', 'aria-label': 'Your predicted output', spellcheck: 'false' });
    const traceHost = h('div');
    const node = h('div', ex.code ? codeBlock(ex.code, ex.lang || 'python') : null, h('label.lbl', { for: 'ans-' + ex.id, text: 'Output' }), ta, traceHost);
    ta.id = 'ans-' + ex.id;
    return {
      node, runLabel: null,
      check() {
        const u = normText(ta.value); const all = [ex.answer].concat(ex.accept || []);
        if (!u) return { ok: false, msg: 'Type your prediction first.' };
        const ok = all.some((a) => normText(a) === u || normBlank(a) === normBlank(u) && !/\n/.test(a));
        return ok ? { ok: true } : { ok: false, msg: (ex.nearMiss && ex.nearMiss(u)) || 'That is not what this code prints. Go through it line by line, writing down each variable as it changes.' };
      },
      solution: () => h('div', h('div.small.muted', { text: 'It prints' }), h('pre.code.plain', { text: ex.answer })),
      lock() { ta.readOnly = true; }, focus: () => ta.focus(),
      hasWork: () => ta.value.trim() !== '',
      extraHint: ex.trace ? { label: 'Step through the code', run: () => { traceHost.appendChild(makeWidget({ kind: 'trace', data: Object.assign({ code: ex.code }, ex.trace) })); } } : null,
    };
  },

  mcq(ex, X) {
    const multi = Array.isArray(ex.answer); const correct = multi ? ex.answer : [ex.answer];
    const order = shuffle(ex.choices.map((c, i) => i)); const picked = new Set(); let locked = false;
    const list = h('div.choices'); const fbs = h('div');
    const btns = {};
    const colorize = (i, good) => { btns[i].classList.add(good ? 'right' : 'wrong'); };
    order.forEach((i) => {
      const b = h('button.choice' + (multi ? '.multi' : ''), { type: 'button', html: rich(ex.choices[i]), 'aria-pressed': 'false', onclick: () => {
        if (locked) return;
        if (multi) { if (picked.has(i)) picked.delete(i); else picked.add(i); b.classList.toggle('on', picked.has(i)); b.setAttribute('aria-pressed', picked.has(i)); }
        else X.primary(i);
      } });
      btns[i] = b; list.appendChild(b);
    });
    return {
      node: h('div', ex.code ? codeBlock(ex.code, ex.lang || 'python') : null, multi ? h('p.muted.small', { text: 'Select all that apply.' }) : null, list, fbs), runLabel: null, primaryLabel: multi ? 'Check' : null, hidePrimary: !multi,
      check(i) {
        const sel = multi ? Array.from(picked) : [i];
        if (!sel.length) return { ok: false, msg: 'Select at least one answer.' };
        const ok = sel.length === correct.length && sel.every((x) => correct.includes(x));
        if (ok) { sel.forEach((x) => colorize(x, true)); return { ok: true }; }
        if (!multi) { colorize(i, false); btns[i].disabled = true; }
        const why = !multi && ex.whys && ex.whys[i] ? ex.whys[i] : '';
        return { ok: false, msg: why || (multi ? 'Not quite. Some of your picks are wrong or one is missing.' : 'Not that one. Think again.') };
      },
      solution: () => { correct.forEach((i) => colorize(i, true)); return h('div', h('div.small.muted', { text: 'Correct answer' }), h('ul.lul', correct.map((i) => h('li', { html: rich(ex.choices[i]) })))); },
      lock() { locked = true; Object.values(btns).forEach((b) => { b.disabled = true; }); },
      hasWork: () => true,
    };
  },

  fill(ex, X) {
    const parts = ex.template.split('____'); const inputs = []; const pre = h('pre.code.fill.cm-s-sr');
    parts.forEach((p, i) => {
      pre.appendChild(document.createTextNode(p));
      if (i < parts.length - 1) { const inp = h('input.blank', { type: 'text', 'aria-label': 'Blank ' + (i + 1), size: Math.max(5, (ex.blanks[i][0] || '').length + 1), autocomplete: 'off', autocapitalize: 'off', spellcheck: 'false' }); inputs.push(inp); pre.appendChild(inp); }
    });
    return {
      node: h('div.codewrap', pre), runLabel: null,
      check() {
        let all = true;
        inputs.forEach((inp, i) => {
          const v = normBlank(inp.value); const ok = v && ex.blanks[i].some((a) => (ex.ci ? normBlank(a).toLowerCase() === v.toLowerCase() : normBlank(a) === v));
          inp.classList.toggle('ok', !!ok); inp.classList.toggle('no', !ok); if (!ok) all = false;
        });
        return all ? { ok: true } : { ok: false, msg: 'Some blanks are not right yet (marked red). Read the surrounding lines for clues.' };
      },
      solution: () => { let k = 0; const filled = ex.template.replace(/____/g, () => ex.blanks[k++][0]); return h('div', codeBlock(filled, ex.lang || 'text', { label: 'Completed' })); },
      lock() { inputs.forEach((i) => { i.readOnly = true; }); }, focus: () => inputs[0] && inputs[0].focus(),
      hasWork: () => inputs.some((i) => i.value.trim()),
    };
  },

  spot(ex, X) {
    const sel = new Set(); let stage = 1; const box = h('div.spot'); const fixHost = h('div'); let locked = false;
    ex.lines.forEach((ln, i) => {
      const row = h('button.sl', { type: 'button', 'aria-pressed': 'false', onclick: () => { if (locked || stage !== 1) return; if (sel.has(i + 1)) sel.delete(i + 1); else sel.add(i + 1); row.classList.toggle('on', sel.has(i + 1)); row.setAttribute('aria-pressed', sel.has(i + 1)); } },
        h('span.ln', { text: i + 1 }), highlightInto(h('span.lt'), ln || ' ', ex.lang || 'text'));
      box.appendChild(row);
    });
    const rows = Array.from(box.children);
    let fixChosen = false; let fixOrder = null; let fixBtns = {};
    const buildFix = () => {
      stage = 2; clear(fixHost);
      fixHost.appendChild(h('p.lbl', { text: ex.fix.q || 'How should it be fixed?' }));
      const list = h('div.choices'); fixOrder = shuffle(ex.fix.choices.map((c, i) => i)); fixBtns = {};
      fixOrder.forEach((i) => { const b = h('button.choice', { type: 'button', html: rich(ex.fix.choices[i]), onclick: () => { if (locked) return; X.primary(i); } }); fixBtns[i] = b; list.appendChild(b); });
      fixHost.appendChild(list);
    };
    return {
      node: h('div', h('div.codewrap.cm-s-sr', box), h('p.muted.small', { text: 'Tap the line or lines that contain the problem, then press Check.' }), fixHost), runLabel: null,
      check(i) {
        if (stage === 1) {
          if (!sel.size) return { ok: false, msg: 'Tap at least one line first.' };
          const bad = ex.bad; const ok = sel.size === bad.length && bad.every((b) => sel.has(b));
          if (!ok) return { ok: false, msg: 'Not quite. ' + (sel.size > bad.length ? 'Some lines you marked are fine.' : 'There is more wrong than you marked, or you picked the wrong line.') };
          rows.forEach((r, k) => r.classList.toggle('bad', bad.includes(k + 1)));
          if (ex.fix) { buildFix(); return { ok: false, progress: true, msg: 'Right line. Now choose the fix.' }; }
          return { ok: true };
        }
        const good = i === ex.fix.answer; fixBtns[i].classList.add(good ? 'right' : 'wrong');
        if (!good) { fixBtns[i].disabled = true; return { ok: false, msg: (ex.fix.why && ex.fix.why[i]) || 'That would not fix it.' }; }
        return { ok: true };
      },
      solution: () => { rows.forEach((r, k) => r.classList.toggle('bad', ex.bad.includes(k + 1))); return h('div', h('div.small.muted', { text: 'The problem is on line' + (ex.bad.length > 1 ? 's ' : ' ') + ex.bad.join(', ') }), ex.fix ? h('div', h('div.small.muted', { text: 'Fix' }), R(ex.fix.choices[ex.fix.answer])) : null); },
      lock() { locked = true; }, hasWork: () => sel.size > 0,
    };
  },

  order(ex, X) {
    const items = ex.lines.map((l, i) => ({ l, i })); const pool = (ex.extra || []).map((l, i) => ({ l, i: 1000 + i })); const all = shuffle(items.concat(pool));
    const mine = []; const poolEl = h('div.o-pool'); const ansEl = h('div.o-ans'); let locked = false;
    const draw = () => {
      clear(poolEl); clear(ansEl);
      all.filter((x) => !mine.includes(x)).forEach((x) => poolEl.appendChild(h('button.o-chip', { type: 'button', onclick: () => { if (locked) return; mine.push(x); draw(); } }, h('code', { text: x.l }))));
      if (!mine.length) ansEl.appendChild(h('div.muted.small', { text: 'Tap lines below in the order they should run.' }));
      mine.forEach((x, k) => ansEl.appendChild(h('button.o-chip.in', { type: 'button', onclick: () => { if (locked) return; mine.splice(k, 1); draw(); } }, h('span.ln', { text: k + 1 }), h('code', { text: x.l }))));
    };
    draw();
    const valid = (arr) => [ex.lines].concat(ex.alts || []).some((o) => o.length === arr.length && o.every((l, k) => l === arr[k]));
    return {
      node: h('div', h('div.o-box', ansEl), poolEl, h('button.btn.ghost.sm', { type: 'button', text: 'Clear', onclick: () => { if (!locked) { mine.length = 0; draw(); } } })), runLabel: null,
      check() {
        const arr = mine.map((x) => x.l);
        if (!arr.length) return { ok: false, msg: 'Build your answer first.' };
        if (valid(arr)) return { ok: true };
        const right = arr.filter((l, k) => ex.lines[k] === l).length;
        return { ok: false, msg: right ? right + ' line(s) are already in the right place. Rearrange the rest.' : 'None of the lines are in the right place yet.' };
      },
      solution: () => h('div', codeBlock(ex.lines.join('\n'), ex.lang || 'text', { label: 'Correct order' })),
      lock() { locked = true; }, hasWork: () => mine.length > 0,
    };
  },
};

/* ---------- exercise card ---------- */
function renderExercise(ex, ctx) {
  ctx = ctx || {};
  const c = Cx.concepts[ex.concept];
  const st = { attempts: 0, hints: 0, solved: false, shown: false, t0: NOW(), finished: false, self: false };
  const maxTries = ctx.maxTries || 0;
  const feedback = h('div.feedback', { 'aria-live': 'polite' }); const hintBox = h('div.hints'); const after = h('div.after'); const actions = h('div.actions');
  const X = { primary: (arg) => primary(arg) };
  const T = TYPES[ex.type](ex, X);
  const diff = ex.diff || 1;
  const head = h('div.chips', trackChip(ex.track), h('span.chip.' + (ctx.mode || 'free'), { text: MODE_LABEL[ctx.mode || 'free'] }), h('span.chip.muted', { text: TYPE_LABEL[ex.type] }), phaseTags(ex.phases).slice(0, 2), h('span.dots', { title: 'Difficulty ' + diff + ' of 3' }, [1, 2, 3].map((i) => h('i' + (i <= diff ? '.on' : '')))), (ex.tags || []).includes('interview') ? h('span.chip.int', { text: 'Interview style' }) : null);
  const prompt = h('div.prompt', { html: '' }); prompt.appendChild(R(ex.prompt));
  const root = h('article.xcard', head, h('div.ctitle', { text: c.title }), prompt, T.node);

  const hintBtn = h('button.btn.ghost', { type: 'button', text: 'Hint', onclick: () => revealHint() });
  const solBtn = h('button.btn.ghost', { type: 'button', text: 'Show solution', onclick: () => showSolution() });
  const runBtn = T.runLabel ? h('button.btn.secondary', { type: 'button', text: T.runLabel, onclick: async () => { runBtn.disabled = true; try { const r = await T.run(); if (r && r.self) selfGrade(r); } finally { runBtn.disabled = false; } } }) : null;
  const primBtn = h('button.btn.primary', { type: 'button', text: T.primaryLabel || 'Check', onclick: () => primary() });
  if (T.hidePrimary) primBtn.hidden = true;
  const nHints = (ex.hints || []).length;
  const updateButtons = () => {
    hintBtn.textContent = nHints ? 'Hint (' + st.hints + '/' + nHints + ')' : 'Hint';
    hintBtn.hidden = !!ctx.noHints || (!nHints && !T.extraHint) || st.solved || st.shown;
    hintBtn.disabled = st.hints >= nHints + (T.extraHint ? 1 : 0) || (T.extraHint && st.hints >= nHints + 1);
    const canSol = st.attempts >= 1 && !ctx.noSolution;
    solBtn.hidden = !!ctx.noSolution || st.solved || st.shown; solBtn.disabled = !canSol;
    solBtn.title = canSol ? '' : 'Make an attempt first. The solution unlocks after your first try.';
    solBtn.textContent = canSol ? 'Show solution' : 'Solution unlocks after your first try';
    primBtn.hidden = T.hidePrimary || st.solved || st.shown || st.self; if (runBtn) runBtn.hidden = st.solved || st.shown || st.self;
  };
  actions.append(...[primBtn, runBtn, hintBtn, solBtn].filter(Boolean));
  root.append(actions, hintBox, feedback, after);
  updateButtons();

  function revealHint() {
    if (st.solved || st.shown) return;
    const hints = ex.hints || [];
    if (st.hints < hints.length) { hintBox.appendChild(h('div.hint', h('span.hl', { text: 'Hint ' + (st.hints + 1) }), R(hints[st.hints]))); st.hints++; }
    else if (T.extraHint && st.hints < hints.length + 1) { T.extraHint.run(); st.hints++; }
    updateButtons();
  }
  function say(kind, title, bodyNode) {
    clear(feedback); feedback.className = 'feedback ' + kind;
    feedback.appendChild(h('strong', { text: title })); if (bodyNode) feedback.appendChild(bodyNode);
    feedback.scrollIntoView && feedback.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
  async function primary(arg) {
    if (st.solved || st.shown || st.finished) return;
    primBtn.disabled = true;
    let r;
    try { r = await T.check(arg); } catch (e) { console.error(e); r = { ok: false, msg: 'Something went wrong while checking. Try again.' }; }
    primBtn.disabled = false;
    if (!r) return;
    if (r.self) return selfGrade(r);
    if (!r.progress) st.attempts++;
    updateButtons();
    if (r.ok) return solved();
    say(r.progress ? 'info' : 'bad', r.progress ? 'On track' : 'Not quite', R(r.msg || ''));
    if (maxTries && st.attempts >= maxTries) { say('bad', 'Out of tries', R('This checkpoint question is done. Here is the solution so you learn from it.')); revealSolution(true); }
  }
  function selfGrade(r) {
    st.self = true; st.attempts = Math.max(1, st.attempts); updateButtons();
    say('info', 'Self-check', R(r.why));
    clear(after); after.appendChild(T.solution());
    after.appendChild(h('div.actions', h('span.muted', { text: 'Did your answer match?' }), h('button.btn.primary', { type: 'button', text: 'Yes, I got it', onclick: () => { st.solved = true; st.selfOk = true; finishAfter(); } }), h('button.btn.ghost', { type: 'button', text: 'No', onclick: () => { st.shown = true; finishAfter(); } })));
  }
  function solved() {
    st.solved = true; T.lock(); updateButtons();
    const note = ex.why ? R(ex.why) : null;
    say('good', st.attempts === 1 && !st.hints ? 'Correct' : 'Correct. It took ' + st.attempts + ' tr' + (st.attempts === 1 ? 'y' : 'ies') + (st.hints ? ' and ' + st.hints + ' hint' + (st.hints > 1 ? 's' : '') : '') + '.', note);
    if (ex.explain && !ctx.noExplain) return explainStep();
    finishAfter();
  }
  function explainStep() {
    const ta = h('textarea.answer', { rows: 3, placeholder: 'Write 1–3 sentences. Say why it works, not just what you did.', 'aria-label': 'Explain in your own words' });
    const go = h('button.btn.primary', { type: 'button', text: 'Compare with the model answer', disabled: true });
    ta.addEventListener('input', () => { go.disabled = ta.value.trim().length < 15; });
    const box = h('div.explain', h('h4', { text: 'Explain it in your own words' }), R(ex.explain.ask || 'In your own words: why does your answer work?'), ta, h('div.actions', go));
    after.appendChild(box);
    go.onclick = () => {
      const pts = ex.explain.points || []; const checks = [];
      const list = h('div.pts', pts.map((p, i) => { const cb = h('input', { type: 'checkbox', id: 'pt-' + ex.id + i }); checks.push(cb); return h('label.pt', { for: 'pt-' + ex.id + i }, cb, h('span', { html: rich(p) })); }));
      const fin = h('button.btn.primary', { type: 'button', text: 'Done', onclick: () => { st.explainScore = pts.length ? checks.filter((x) => x.checked).length / pts.length : 1; note(ex.id, ta.value, checks.filter((x) => x.checked).length); finishAfter(); box.remove(); } });
      mount(box, h('h4', { text: 'Model answer' }), R(ex.explain.model), h('p.small', { text: 'Which of these did your explanation include? Be honest.' }), list, h('div.actions', fin));
    };
    ta.focus && ta.focus();
  }
  function showSolution() {
    if (st.attempts < 1) return;
    revealSolution(false);
  }
  function revealSolution(forced) {
    st.shown = true; T.lock && T.lock(); updateButtons();
    clear(after); after.appendChild(T.solution());
    if (ex.why) after.appendChild(R(ex.why));
    if (!forced) say('info', 'Solution shown', R('This one counts as a miss and comes back tomorrow. For code, try retyping it from memory below.'));
    if (T.retype) after.appendChild(h('div.actions', h('button.btn.ghost', { type: 'button', text: 'Retype it from memory', onclick: () => { T.retype && T.retype(); st.retyping = true; T.lock = () => {}; } })));
    finishAfter();
  }
  function classify() {
    if (st.shown) return 'miss';
    if (st.self) return st.selfOk ? 'hint' : 'miss';
    let r = st.hints > 0 || st.attempts > 2 ? 'hint' : 'ok';
    if (r === 'ok' && st.explainScore !== undefined && st.explainScore < 0.5) r = 'hint';
    return r;
  }
  function finishAfter() {
    if (st.finished) return;
    const wait = !!root.querySelector('.explain');
    const go = () => {
      st.finished = true;
      const cls = classify(); const meta = { hints: st.hints, attempts: st.attempts, ms: NOW() - st.t0, mode: ctx.mode };
      if ((cls === 'miss' || (cls === 'hint' && (st.hints >= 2 || st.attempts >= 3))) && !ctx.noJournal) after.appendChild(journalPrompt(ex, cls, st));
      const btn = h('button.btn.primary.big', { type: 'button', text: ctx.last ? 'Finish' : 'Continue', onclick: () => { if (st.saveJournal) st.saveJournal(); ctx.onDone && ctx.onDone(cls, meta); } });
      const bar = h('div.actions.cont', btn); after.appendChild(bar); btn.focus && btn.focus(); bar.scrollIntoView && bar.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    };
    if (wait) { const iv = setInterval(() => { if (!root.querySelector('.explain')) { clearInterval(iv); go(); } }, 150); } else go();
  }
  setTimeout(() => { T.refresh && T.refresh(); }, 50);
  return root;
}

/* "Why did this one go wrong?" prompt shown after a miss or a struggle */
function journalPrompt(ex, cls, st) {
  let entry = null; const chosen = new Set();
  const note = h('textarea.answer', { rows: 2, placeholder: 'Optional: what will you do differently next time?', 'aria-label': 'What will you do differently', hidden: true });
  const tip = h('div.jtip', { 'aria-live': 'polite' });
  const save = () => { if (!chosen.size && !note.value.trim()) return; if (!entry) entry = journalAdd(ex.id, cls, { attempts: st.attempts, hints: st.hints }); journalSet(entry, Array.from(chosen), note.value); };
  st.saveJournal = save;
  const chips = CAUSES.map((c) => {
    const b = h('button.chip.cause', { type: 'button', 'aria-pressed': 'false', text: c.label, onclick: () => {
      if (chosen.has(c.id)) chosen.delete(c.id); else chosen.add(c.id);
      b.classList.toggle('on', chosen.has(c.id)); b.setAttribute('aria-pressed', chosen.has(c.id));
      note.hidden = false; const last = CAUSES.find((x) => chosen.has(x.id) && x.id === c.id) || CAUSES.find((x) => chosen.has(x.id));
      tip.textContent = last ? last.tip : ''; save();
    } });
    return b;
  });
  note.addEventListener('blur', save);
  return h('div.journal-prompt', h('h4', { text: cls === 'miss' ? 'Why did this one go wrong?' : 'This one took a lot of help. Why?' }), h('p.muted.small', { text: 'Tap what fits. Your answers build the Journal tab, which shows your patterns.' }), h('div.chips', chips), tip, note);
}
