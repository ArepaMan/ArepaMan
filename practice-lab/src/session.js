'use strict';
/* ---------- session runner (full-screen flow) ---------- */
const Session = {
  run: null,
  start(steps, o) {
    o = o || {};
    this.run = { steps: steps.slice(), i: 0, results: [], title: o.title || 'Practice', kind: o.kind || 'plan', cp: o.cp || null, onExit: o.onExit, planMode: !!o.planMode, deltas: {}, started: NOW(), missed: [] };
    if (this.run.planMode) this.run.i = Math.max(0, this.run.steps.findIndex((s) => !s.done));
    if (this.run.i < 0) this.run.i = 0;
    document.body.classList.add('in-session');
    this.render();
  },
  exit() {
    document.body.classList.remove('in-session');
    const r = this.run; this.run = null;
    const view = document.getElementById('session'); if (view) view.remove();
    if (r && r.onExit) r.onExit(); else App.go(App.tab);
  },
  render() {
    const r = this.run; let host = document.getElementById('session');
    if (!host) { host = h('section#session', { role: 'dialog', 'aria-label': r.title }); document.body.appendChild(host); }
    clear(host);
    const total = r.steps.length;
    const segs = h('div.segs', r.steps.map((s, k) => h('i' + (s.done || k < r.i ? '.done' : '') + (k === r.i ? '.cur' : ''))));
    const top = h('header.s-top', h('button.btn.ghost.sm', { type: 'button', text: 'Save and exit', onclick: () => this.exit() }), h('div.s-title', { text: r.title }), h('span.muted.small', { text: Math.min(r.i + 1, total) + ' / ' + total }));
    host.appendChild(top); host.appendChild(segs);
    const body = h('main.s-body'); host.appendChild(body);
    if (r.i >= total) return this.summary(body);
    const s = r.steps[r.i]; const c = Cx.concepts[s.c];
    if (s.k === 'les') {
      body.appendChild(lessonCard(c, () => { s.done = true; if (S().c[s.c] && S().c[s.c].relearn) S().c[s.c].relearn = false; Store.touch('state'); r.i++; this.render(); }, { cta: s.relearn ? 'I have re-read it. Practise' : 'Start practising' }));
    } else {
      const ex = Cx.exercises[s.e]; const mode = s.k === 'rev' ? 'rev' : s.k === 'new' ? 'new' : s.k === 'int' ? 'int' : s.k === 'cp' ? 'cp' : 'free';
      const last = r.i === total - 1;
      const card = renderExercise(ex, {
        mode, last, noHints: r.kind === 'cp', noSolution: false, noExplain: r.kind === 'cp', maxTries: r.kind === 'cp' ? (ex.type === 'code' || ex.type === 'sql' ? 3 : 2) : 0,
        onDone: (cls, meta) => {
          const d = record(ex.id, cls, meta); s.done = true; s.res = cls;
          if (d) { const k = ex.concept; r.deltas[k] = r.deltas[k] || { before: d.before, after: d.after }; r.deltas[k].after = d.after; }
          r.results.push({ eid: ex.id, cid: ex.concept, res: cls, mode });
          if (cls === 'miss') r.missed.push(ex.id);
          Store.touch('state'); App.refreshChrome();
          r.i++; this.render();
        },
      });
      body.appendChild(card);
    }
    host.scrollTop = 0;
  },
  summary(body) {
    const r = this.run; const res = r.results;
    const ok = res.filter((x) => x.res === 'ok').length, hint = res.filter((x) => x.res === 'hint').length, miss = res.filter((x) => x.res === 'miss').length;
    if (r.planMode) {
      const plan = S().plan;
      if (plan && plan.steps.every((x) => x.done) && !plan.counted) { plan.counted = true; S().sess++; Store.touch('state'); }
    }
    let cpMsg = null;
    if (r.cp) {
      const passed = passCheckpoint(r.cp.track, r.cp.level, ok + (hint ? 0 : 0), res.length);
      cpMsg = passed
        ? h('div.feedback.good', h('strong', { text: 'Checkpoint passed' }), R('You cleared **Level ' + r.cp.level + '** of ' + Cx.tracks[r.cp.track].name + (r.cp.level < Cx.tracks[r.cp.track].maxLevel ? '. Level ' + (r.cp.level + 1) + ' is open.' : '. That is the whole track.')))
        : h('div.feedback.bad', h('strong', { text: 'Not yet' }), R('You need 4 of 5 clean answers. Review the weak spots below and try again; the questions rotate.'));
    }
    const sv = streakView();
    const wrap = h('div.summary',
      h('h2', { text: res.length ? 'Session complete' : 'Nothing was answered' }),
      cpMsg,
      h('div.sum-grid', h('div.sum', h('b.good', { text: ok }), h('span', 'clean')), h('div.sum', h('b.warn', { text: hint }), h('span', 'with help')), h('div.sum', h('b.bad', { text: miss }), h('span', 'to revisit'))),
      h('div.sum-streak', h('strong', { text: sv.cur + '-day streak' }), h('span.muted', { text: sv.doneToday ? ' Today counts.' : ' Answer ' + Math.max(0, 3 - sv.exToday) + ' more to count today.' })));
    const ids = Object.keys(r.deltas);
    if (ids.length) {
      const list = h('div.deltas');
      ids.forEach((cid) => { const d = r.deltas[cid]; const cc = Cx.concepts[cid]; const up = d.after - d.before; list.appendChild(h('div.delta', trackChip(cc.track), h('span.dn', { text: cc.title }), h('span.bar', h('i', { style: { width: Math.max(2, d.after) + '%' } })), h('span.dv' + (up > 0 ? '.up' : up < 0 ? '.dn' : ''), { text: d.before + ' → ' + d.after }))); });
      wrap.appendChild(h('h4', { text: 'Mastery changes' })); wrap.appendChild(list);
    }
    const act = h('div.actions');
    if (r.missed.length) act.appendChild(h('button.btn.secondary', { type: 'button', text: 'Retry what I missed (' + r.missed.length + ')', onclick: () => {
      const steps = []; r.missed.forEach((eid) => { const cid = Cx.exercises[eid].concept; const e2 = pickEx(cid, { exclude: Cx.concepts[cid].exercises.length > 1 ? [eid] : [] }); steps.push({ k: 'rev', c: cid, e: e2 }); });
      this.start(steps, { title: 'Retry missed', kind: 'retry', onExit: r.onExit });
    } }));
    if (r.planMode) act.appendChild(h('button.btn.secondary', { type: 'button', text: 'Keep going', onclick: () => {
      const x = extendPlan();
      if (x.added <= 0) { toast('Nothing more to add today. Try an interview drill.', 'warn'); return; }
      if (x.capped) toast('You have started plenty of new concepts today. Added reviews instead.', 'warn');
      this.start(S().plan.steps, { title: 'Today', planMode: true, onExit: r.onExit });
    } }));
    act.appendChild(h('button.btn.primary', { type: 'button', text: 'Back to dashboard', onclick: () => this.exit() }));
    wrap.appendChild(act);
    body.appendChild(wrap);
  },
};

/* entry points */
function startToday() {
  const plan = ensurePlan();
  if (!plan.steps.length) { toast('Nothing to do yet. Check the Map tab.', 'warn'); return; }
  if (plan.steps.every((x) => x.done)) { const x = extendPlan(); if (x.added <= 0) { toast('You finished today’s plan. Nice. Try an interview drill.'); return; } }
  Session.start(plan.steps, { title: 'Today’s session', planMode: true });
}
function startConcept(cid) {
  const c = Cx.concepts[cid];
  const steps = [{ k: 'les', c: cid, done: false }];
  pickMany(cid, c.exercises.length).forEach((eid) => steps.push({ k: 'free', c: cid, e: eid, done: false }));
  Session.start(steps, { title: c.title, kind: 'concept' });
}
function startPractice(cid, n) {
  const steps = []; const used = [];
  for (let k = 0; k < (n || 3); k++) { const e = pickEx(cid, { exclude: used }); if (e && !used.includes(e)) { used.push(e); steps.push({ k: 'free', c: cid, e, done: false }); } }
  Session.start(steps, { title: Cx.concepts[cid].title, kind: 'practice' });
}
function startInterview() {
  const ids = interviewPool(6);
  if (!ids.length) { toast('Unlock a few concepts first. Interview drills use what you have seen.', 'warn'); return; }
  Session.start(ids.map((e) => ({ k: 'int', c: Cx.exercises[e].concept, e, done: false })), { title: 'Interview drill', kind: 'drill' });
}
function startWeak() {
  const w = weakSpots(5);
  if (!w.length) { toast('No weak spots right now. Good.'); return; }
  Session.start(w.map((x) => ({ k: 'rev', c: x.id, e: pickEx(x.id), done: false })), { title: 'Weak-spot drill', kind: 'drill' });
}
function startDue() {
  const d = dueConcepts().slice(0, 10);
  if (!d.length) { toast('No reviews are due.'); return; }
  Session.start(d.map((x) => ({ k: 'rev', c: x.id, e: pickEx(x.id), done: false })), { title: 'Due reviews', kind: 'drill' });
}
function startCheckpoint(tid, L) {
  const ids = checkpointExercises(tid, L);
  if (ids.length < 3) { toast('This level has too few exercises for a checkpoint yet.', 'warn'); return; }
  Session.start(ids.map((e) => ({ k: 'cp', c: Cx.exercises[e].concept, e, done: false })), { title: Cx.tracks[tid].name + ' · Level ' + L + ' checkpoint', kind: 'cp', cp: { track: tid, level: L } });
}

function startPhase(pid) {
  const ph = Cx.phases.find((p) => p.id === pid); const pool = [];
  Cx.list.forEach((t) => t.concepts.forEach((c) => { if ((c.phases || []).includes(pid) && conceptOpen(c) && cinfo(c.id).n > 0) c.exercises.forEach((e) => pool.push(e)); }));
  if (pool.length < 3) { toast('Learn a few concepts for this phase first, then come back.', 'warn'); return; }
  const sorted = shuffle(pool).sort((a, b) => { const sa = exSeen(a.id), sb = exSeen(b.id); return ((sa ? sa.t : 0) - (sb ? sb.t : 0)) || ((b.diff || 1) - (a.diff || 1)); });
  const out = []; const per = {};
  sorted.forEach((e) => { if (out.length < 6 && (per[e.track] || 0) < 3 && !out.some((x) => x.concept === e.concept)) { out.push(e); per[e.track] = (per[e.track] || 0) + 1; } });
  sorted.forEach((e) => { if (out.length < 6 && !out.includes(e)) out.push(e); });
  Session.start(out.map((e) => ({ k: 'free', c: e.concept, e: e.id, done: false })), { title: 'Phase check: ' + ph.name, kind: 'drill' });
}
