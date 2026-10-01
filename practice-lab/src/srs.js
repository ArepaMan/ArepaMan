'use strict';
/* ---------- content index ---------- */
const INT = [1, 3, 7, 14, 30, 60, 90, 180, 180]; // days until next review after the k-th spaced success
const LEVEL_PASS = 80;       // average mastery needed to unlock the next level
const NEW_PER_DAY_SOFT = 4;  // soft cap on new concepts a day
const Cx = { tracks: {}, list: [], concepts: {}, exercises: {}, phases: [], datasets: {}, rotation: [], loaded: false };

function indexContent(cur, files) {
  Cx.phases = cur.phases; Cx.rotation = cur.rotation; Cx.datasets = cur.datasets || {};
  cur.tracks.forEach((t, ti) => {
    const f = files[t.id] || { concepts: [] };
    const tr = Object.assign({}, t, { concepts: [], order: ti });
    f.concepts.forEach((c, ci) => {
      c.track = t.id; c.idx = ci; c.exercises = c.exercises || [];
      c.exercises.forEach((e) => { e.concept = c.id; e.track = t.id; e.phases = e.phases || c.phases || []; Cx.exercises[e.id] = e; });
      Cx.concepts[c.id] = c; tr.concepts.push(c);
    });
    tr.maxLevel = t.levels.length;
    Cx.tracks[t.id] = tr; Cx.list.push(tr);
  });
  Cx.loaded = true;
}

/* ---------- concept state ---------- */
const S = () => Store.s;
function cget(cid) {
  const s = S();
  return s.c[cid] || (s.c[cid] = { s: 0, b: 0, d: '', n: 0, ok: 0, nh: 0, ld: '', hd: '', md: '', last: '', w: 0, ex: {} });
}
function intervalFor(b) { return b <= 0 ? 1 : INT[Math.min(b, INT.length) - 1]; }
function cinfo(cid) {
  const raw = S().c[cid];
  if (!raw || !raw.n) return { n: 0, score: 0, eff: 0, state: 'new', fresh: 'none', overdue: 0, due: '', b: 0, w: 0 };
  const day = today();
  const overdue = raw.d ? Math.max(0, diffDays(day, raw.d)) : 0;
  const ratio = overdue / intervalFor(raw.b);
  const f = ratio <= 0 ? 1 : Math.max(0.6, 1 - 0.2 * ratio);
  const eff = Math.round(raw.s * f);
  const fresh = ratio <= 0 ? 'fresh' : ratio <= 1 ? 'fading' : 'rusty';
  let state = eff < 35 ? 'learning' : eff < 65 ? 'shaky' : eff < 85 ? 'solid' : 'mastered';
  if (raw.w > 0 && (state === 'solid' || state === 'mastered')) state = 'shaky';
  return { n: raw.n, score: raw.s, eff, state, fresh, overdue, ratio, due: raw.d, b: raw.b, w: raw.w, nh: raw.nh };
}
const STATE_LABEL = { new: 'New', learning: 'Learning', shaky: 'Shaky', solid: 'Solid', mastered: 'Mastered' };
const FRESH_LABEL = { none: '', fresh: 'Fresh', fading: 'Fading', rusty: 'Rusty' };

/* ---------- levels ---------- */
function lvState(tid) { const s = S(); return s.lv[tid] || (s.lv[tid] = { cleared: [], cp: {} }); }
function trackLevel(tid) { // current working level, or max+1 when all cleared
  const t = Cx.tracks[tid]; const cl = lvState(tid).cleared;
  for (let L = 1; L <= t.maxLevel; L++) if (!cl.includes(L)) return L;
  return t.maxLevel + 1;
}
function trackUnlocked(tid) {
  const t = Cx.tracks[tid];
  return (t.requires || []).every((r) => lvState(r.track).cleared.includes(r.cleared));
}
function levelConcepts(tid, L) { return Cx.tracks[tid].concepts.filter((c) => c.level === L); }
function levelStats(tid, L) {
  const cs = levelConcepts(tid, L);
  const infos = cs.map((c) => cinfo(c.id));
  const exTotal = sum(cs.map((c) => c.exercises.length));
  let solved = 0, nh = 0;
  cs.forEach((c) => { const raw = S().c[c.id]; if (!raw) return; for (const k in raw.ex) { const e = raw.ex[k]; if (e.ok + e.hint > 0) solved++; if (e.ok > 0) nh++; } });
  const reqEx = Math.min(8, Math.max(3, Math.floor(exTotal * 0.5)));
  const avgEff = Math.round(avg(infos.map((i) => i.eff)));
  const cleared = lvState(tid).cleared.includes(L);
  const eligible = avgEff >= LEVEL_PASS && solved >= reqEx && nh >= 2;
  return { cs, count: cs.length, avg: avgEff, solved, nh, reqEx, reqNH: 2, eligible, cleared, started: infos.filter((i) => i.n > 0).length };
}
function levelOpen(tid, L) { return trackUnlocked(tid) && L <= trackLevel(tid); }
function conceptOpen(c) { return levelOpen(c.track, c.level); }
function trackAvg(tid, field) {
  const cs = Cx.tracks[tid].concepts; if (!cs.length) return 0;
  return Math.round(avg(cs.map((c) => (field === 'learned' ? cinfo(c.id).score : cinfo(c.id).eff))));
}
function trackFreshness(tid) {
  const seen = Cx.tracks[tid].concepts.map((c) => cinfo(c.id)).filter((i) => i.n > 0);
  if (!seen.length) return 'none';
  const rusty = seen.filter((i) => i.fresh === 'rusty').length / seen.length;
  const fading = seen.filter((i) => i.fresh !== 'fresh').length / seen.length;
  return rusty >= 0.3 ? 'rusty' : fading >= 0.4 ? 'fading' : 'fresh';
}

/* ---------- recording an answer ---------- */
function record(eid, res, meta) {
  meta = meta || {};
  const ex = Cx.exercises[eid]; if (!ex) return;
  const c = cget(ex.concept); const day = today(); const s = S();
  const e = c.ex[eid] || (c.ex[eid] = { n: 0, ok: 0, hint: 0, miss: 0, t: 0, r: '' });
  e.n++; e[res]++; e.t = NOW(); e.r = res; c.n++; c.last = day;
  const before = cinfo(ex.concept).eff;
  if (res === 'ok') {
    c.ok++; if (!meta.hints) c.nh++;
    if (c.ld !== day) { c.s = clamp(c.s + (c.hd === day ? 15 : 25), 0, 100); c.b = Math.min(9, c.b + 1); c.ld = day; } else c.s = clamp(c.s + 5, 0, 100);
    c.w = 0; c.d = addDays(day, intervalFor(c.b));
  } else if (res === 'hint') {
    if (c.hd !== day && c.ld !== day) c.s = clamp(c.s + 12, 0, 100); else c.s = clamp(c.s + 3, 0, 100);
    c.hd = day; c.d = addDays(day, 1);
  } else {
    c.s = clamp(c.s - (c.md === day ? 6 : 15), 0, 100); c.md = day; c.b = Math.max(0, c.b - 2); c.w++; c.d = addDays(day, 1);
  }
  const d = s.days[day] || (s.days[day] = { ex: 0, ok: 0, hint: 0, miss: 0, sec: 0 });
  d.ex++; d[res]++; d.sec += Math.round((meta.ms || 0) / 1000);
  if (d.ex === 3) bumpStreak(day);
  Store.log.push({ t: NOW(), e: eid, c: ex.concept, r: res, h: meta.hints || 0, a: meta.attempts || 0, ms: meta.ms || 0, m: meta.mode || '' });
  if (Store.log.length > 450) Store.log.splice(0, Store.log.length - 450);
  Store.touch('log');
  return { before, after: cinfo(ex.concept).eff };
}
function bumpStreak(day) {
  const st = S().streak; const month = day.slice(0, 7);
  if (st.tokMonth !== month) { st.tokMonth = month; st.tok = 2; }
  if (st.last === day) return;
  if (!st.last) st.cur = 1;
  else {
    const gap = diffDays(day, st.last);
    if (gap === 1) st.cur++;
    else if (gap > 1) { const missed = gap - 1; if (st.tok >= missed) { st.tok -= missed; st.cur++; st.saved = missed; } else st.cur = 1; }
  }
  st.last = day; st.best = Math.max(st.best, st.cur);
}
function streakView() {
  const st = S().streak; const day = today();
  let cur = st.cur; let alive = true;
  if (st.last) {
    const gap = diffDays(day, st.last);
    if (gap > 1 && st.tok < gap - 1) { cur = 0; alive = false; }
  }
  const doneToday = (S().days[day] || { ex: 0 }).ex >= 3;
  return { cur, best: st.best, tok: st.tok, doneToday, alive, exToday: (S().days[day] || { ex: 0 }).ex };
}
function note(eid, text, pts) {
  Store.notes.push({ t: NOW(), e: eid, x: text.slice(0, 600), p: pts || 0 });
  if (Store.notes.length > 80) Store.notes.shift();
  Store.touch('notes');
}

/* ---------- picking exercises ---------- */
function exSeen(eid) { const ex = Cx.exercises[eid]; const raw = S().c[ex.concept]; return raw && raw.ex[eid] ? raw.ex[eid] : null; }
function pickEx(cid, opts) {
  opts = opts || {};
  const c = Cx.concepts[cid]; const exclude = opts.exclude || [];
  let pool = c.exercises.filter((e) => !exclude.includes(e.id));
  if (opts.tag) { const t = pool.filter((e) => (e.tags || []).includes(opts.tag)); if (t.length) pool = t; }
  if (opts.runnable) { const t = pool.filter((e) => e.type === 'code' || e.type === 'sql'); if (t.length) pool = t; }
  if (!pool.length) pool = c.exercises.slice();
  pool.sort((a, b) => {
    const sa = exSeen(a.id), sb = exSeen(b.id);
    const ta = sa ? sa.t : 0, tb = sb ? sb.t : 0;
    if (opts.byDiff && (!sa || !sb)) return (a.diff || 1) - (b.diff || 1);
    if (!!sa !== !!sb) return sa ? 1 : -1;      // unseen first
    if (ta !== tb) return ta - tb;              // least recently seen
    return (a.diff || 1) - (b.diff || 1);
  });
  return pool[0] ? pool[0].id : null;
}
function pickMany(cid, n, exclude) {
  const out = []; const c = Cx.concepts[cid];
  const sorted = c.exercises.slice().sort((a, b) => (a.diff || 1) - (b.diff || 1));
  sorted.forEach((e) => { if (out.length < n && !(exclude || []).includes(e.id)) out.push(e.id); });
  return out;
}

/* ---------- plan building ---------- */
function dueConcepts() {
  const day = today(); const out = [];
  Cx.list.forEach((t) => t.concepts.forEach((c) => {
    const raw = S().c[c.id]; if (!raw || !raw.n || !raw.d) return;
    if (raw.d <= day) out.push({ id: c.id, over: diffDays(day, raw.d), ratio: diffDays(day, raw.d) / intervalFor(raw.b), s: raw.s, b: raw.b });
  }));
  out.sort((a, b) => (b.ratio - a.ratio) || (a.s - b.s));
  return out;
}
function youngCount(tid) {
  return Cx.tracks[tid].concepts.filter((c) => { const i = cinfo(c.id); return i.n > 0 && i.score < 40; }).length;
}
function nextNew(tid, skip) {
  if (!trackUnlocked(tid)) return null;
  const t = Cx.tracks[tid]; skip = skip || [];
  if (youngCount(tid) >= 3) return null;
  const L = trackLevel(tid);
  for (let i = 0; i < t.concepts.length; i++) {
    const c = t.concepts[i];
    if (c.level > L || skip.includes(c.id)) continue;
    if (cinfo(c.id).n > 0) continue;
    const prev = i > 0 ? t.concepts[i - 1] : null;
    if (prev && prev.level <= L && cinfo(prev.id).n === 0 && !skip.includes(prev.id)) return null; // keep order
    return c.id;
  }
  return null;
}
function newCandidates() {
  const seq = Cx.rotation.length ? Cx.rotation : Cx.list.map((t) => t.id);
  const out = []; const n = S().rot || 0;
  for (let i = 0; i < seq.length; i++) out.push(seq[(n + i) % seq.length]);
  return out;
}
function buildPlan(extra) {
  const day = today(); const s = S(); const steps = [];
  const used = new Set();
  const addEx = (kind, cid, eid, extraProps) => { if (eid) { steps.push(Object.assign({ k: kind, c: cid, e: eid, done: false }, extraProps || {})); used.add(eid); } };
  const due = dueConcepts().filter((d) => cinfo(d.id).n > 0);
  const maint = due.filter((d) => d.b >= 5);
  const normal = due.filter((d) => d.b < 5);
  normal.slice(0, 3).forEach((d) => addEx('rev', d.id, pickEx(d.id, { exclude: [] })));
  if (maint.length) addEx('rev', maint[0].id, pickEx(maint[0].id), { maint: true });
  // new material: python first when available, then one concept from the rotation
  const skip = []; const intro = [];
  const py = nextNew('python'); if (py) { intro.push(py); skip.push(py); }
  for (const tid of newCandidates()) { if (tid === 'python') continue; const c = nextNew(tid, skip); if (c) { intro.push(c); skip.push(c); } if (intro.length >= 2) break; }
  const exPer = [3, 2];
  intro.forEach((cid, i) => {
    steps.push({ k: 'les', c: cid, done: false });
    const n = intro.length === 1 ? 4 : exPer[i] || 2;
    pickMany(cid, n).forEach((eid) => addEx('new', cid, eid));
  });
  // top up with weak concepts if the plan is thin
  if (steps.filter((x) => x.e).length < 7) {
    weakSpots(6).forEach((w) => { if (steps.filter((x) => x.e).length < 8) addEx('rev', w.id, pickEx(w.id, { exclude: [...used] })); });
  }
  if (steps.filter((x) => x.e).length < 4) {
    // everything is quiet: pull forward upcoming reviews
    const soon = []; Cx.list.forEach((t) => t.concepts.forEach((c) => { const raw = s.c[c.id]; if (raw && raw.n && raw.d > day) soon.push({ id: c.id, d: raw.d }); }));
    soon.sort((a, b) => (a.d < b.d ? -1 : 1)).slice(0, 4).forEach((x) => addEx('rev', x.id, pickEx(x.id)));
  }
  // interview drill every 7th session
  const drillDue = (s.sess + 1) % 7 === 0;
  if (drillDue) { const dr = interviewPool(5); dr.forEach((eid) => addEx('int', Cx.exercises[eid].concept, eid)); }
  s.rot = (s.rot || 0) + 1;
  return { day, steps, drill: drillDue, extra: extra || 0 };
}
function ensurePlan() {
  const s = S(); const day = today();
  if (!s.plan || s.plan.day !== day) { s.plan = buildPlan(); Store.touch('state'); }
  return s.plan;
}
function planEstMinutes(plan) {
  return Math.round(sum(plan.steps.filter((x) => !x.done).map((x) => (x.k === 'les' ? 1.5 : 2.2))));
}
function extendPlan() {
  const s = S(); const plan = ensurePlan(); const before = plan.steps.length;
  const day = today();
  const introducedToday = Cx.list.reduce((n, t) => n + t.concepts.filter((c) => { const raw = s.c[c.id]; return raw && raw.n && raw.ld === day && raw.ex && Object.keys(raw.ex).length <= 4; }).length, 0);
  const used = new Set(plan.steps.map((x) => x.e));
  const stepsAdd = [];
  const lessonsToday = plan.steps.filter((x) => x.k === 'les').length;
  let capped = false;
  if (lessonsToday < NEW_PER_DAY_SOFT) {
    const cand = newCandidates(); const skip = plan.steps.filter((x) => x.k === 'les').map((x) => x.c);
    for (const tid of cand) {
      const c = nextNew(tid, skip);
      if (c) { stepsAdd.push({ k: 'les', c, done: false }); pickMany(c, 3, [...used]).forEach((eid) => { used.add(eid); stepsAdd.push({ k: 'new', c, e: eid, done: false }); }); break; }
    }
  } else capped = true;
  // plus pulled-forward reviews of concepts due soonest
  const soon = [];
  Cx.list.forEach((t) => t.concepts.forEach((c) => { const raw = s.c[c.id]; if (raw && raw.n && raw.d > day) soon.push({ id: c.id, d: raw.d }); }));
  soon.sort((a, b) => (a.d < b.d ? -1 : 1));
  const have = new Set(plan.steps.concat(stepsAdd).map((x) => x.c));
  soon.filter((x) => !have.has(x.id)).slice(0, 2).forEach((x) => { const eid = pickEx(x.id, { exclude: [...used] }); if (eid) { used.add(eid); stepsAdd.push({ k: 'rev', c: x.id, e: eid, done: false, early: true }); } });
  plan.steps.push(...stepsAdd); plan.extra = (plan.extra || 0) + 1;
  Store.touch('state');
  return { added: plan.steps.length - before, capped, introducedToday };
}
function interviewPool(n) {
  const pool = [];
  Cx.list.forEach((t) => t.concepts.forEach((c) => {
    if (cinfo(c.id).n === 0 && !(c.level === 1 && conceptOpen(c))) return;
    if (!conceptOpen(c)) return;
    c.exercises.forEach((e) => { if ((e.tags || []).includes('interview')) pool.push(e); });
  }));
  let list = shuffle(pool).sort((a, b) => { const sa = exSeen(a.id), sb = exSeen(b.id); return (sa ? sa.t : 0) - (sb ? sb.t : 0); });
  // mix of types and tracks
  const out = []; const types = new Set(); const tracks = {};
  list.forEach((e) => { if (out.length < n && !types.has(e.type + e.track) && (tracks[e.track] || 0) < 3) { out.push(e.id); types.add(e.type + e.track); tracks[e.track] = (tracks[e.track] || 0) + 1; } });
  list.forEach((e) => { if (out.length < n && !out.includes(e.id)) out.push(e.id); });
  return out.slice(0, n);
}
function weakSpots(limit) {
  const out = [];
  Cx.list.forEach((t) => t.concepts.forEach((c) => {
    const i = cinfo(c.id); if (!i.n) return;
    const urgency = (100 - i.eff) + (i.w ? 20 : 0) + (i.fresh === 'rusty' ? 25 : i.fresh === 'fading' ? 8 : 0);
    if (i.state === 'learning' || i.state === 'shaky' || i.fresh === 'rusty' || i.w > 0) out.push({ id: c.id, info: i, urgency });
  }));
  out.sort((a, b) => b.urgency - a.urgency);
  return out.slice(0, limit || 8);
}

/* ---------- checkpoint ---------- */
function checkpointExercises(tid, L) {
  const cs = shuffle(levelConcepts(tid, L).filter((c) => c.exercises.length));
  const picked = []; const used = [];
  const rounds = Math.ceil(5 / Math.max(1, cs.length));
  for (let r = 0; r < rounds + 1 && picked.length < 5; r++) {
    cs.forEach((c) => { if (picked.length >= 5) return; const e = pickEx(c.id, { exclude: used.concat(picked) }); if (e && !picked.includes(e)) picked.push(e); });
  }
  return picked.slice(0, 5);
}
function passCheckpoint(tid, L, ok, total) {
  const l = lvState(tid); const rec = l.cp[L] || (l.cp[L] = { tries: 0, best: 0 });
  rec.tries++; rec.best = Math.max(rec.best, ok); rec.last = today();
  const passed = ok >= 4 && ok / total >= 0.8;
  if (passed && !l.cleared.includes(L)) { l.cleared.push(L); l.cleared.sort(); }
  Store.touch('state');
  return passed;
}

/* ---------- phases ---------- */
function phaseReadiness(pid) {
  const cs = []; Cx.list.forEach((t) => t.concepts.forEach((c) => { if ((c.phases || []).includes(pid)) cs.push(c); }));
  const rows = cs.map((c) => ({ c, info: cinfo(c.id), open: conceptOpen(c) }));
  const pct = rows.length ? Math.round(avg(rows.map((r) => r.info.eff))) : 0;
  const solid = rows.filter((r) => r.info.eff >= 65).length;
  const missing = rows.filter((r) => r.info.eff < 65).sort((a, b) => a.info.eff - b.info.eff);
  const status = pct >= 75 && solid >= Math.ceil(rows.length * 0.8) ? 'ready' : pct >= 45 ? 'almost' : 'not yet';
  return { rows, pct, solid, total: rows.length, missing, status };
}

/* ---------- forecast / timeline ---------- */
function recentPace() {
  const s = S(); const day = today(); let ex = 0, act = 0;
  for (let i = 0; i < 14; i++) { const d = s.days[addDays(day, -i)]; if (d && d.ex) { ex += d.ex; act++; } }
  const since = Math.max(1, Math.min(14, diffDays(day, s.created) + 1));
  const pace = act >= 2 ? ex / act : 9;
  const activeFrac = act >= 2 ? clamp(act / since, 0.3, 1) : 5 / 7;
  const hist = Store.log.slice(-60); const acc = hist.length >= 10 ? clamp(hist.filter((h) => h.r === 'ok').length / hist.length, 0.35, 0.95) : 0.7;
  return { pace: Math.max(4, pace), activeFrac, acc, act, hasData: act >= 2 };
}
function estimateTo(tid, target) { // clear all levels up to `target`
  const t = Cx.tracks[tid]; const pc = recentPace();
  let exNeeded = 0, maxSteps = 0, levels = 0;
  for (let L = 1; L <= target; L++) {
    if (lvState(tid).cleared.includes(L)) continue;
    levels++;
    levelConcepts(tid, L).forEach((c) => {
      const need = Math.max(0, 85 - cinfo(c.id).eff); const steps = Math.ceil(need / 25);
      exNeeded += steps * 1.3; maxSteps = Math.max(maxSteps, steps);
    });
    exNeeded += 6; // checkpoint
  }
  if (!levels) return { done: true };
  exNeeded *= 0.75 / pc.acc; // 1.3 retries per step assumes ~75% clean answers
  const share = tid === 'python' ? 0.5 : 0.25; // share of a session's exercises this track gets
  const activeDays = exNeeded / (pc.pace * share);
  const cal = activeDays / pc.activeFrac;
  let floor = 0; for (let k = 0; k < Math.max(0, maxSteps - 1); k++) floor += intervalFor(k + 0);
  const low = Math.max(cal * 0.8, floor), high = Math.max(cal * 1.45, floor * 1.25 + 2);
  const day = today();
  return { done: false, levels, sessions: Math.max(1, Math.ceil(activeDays)), lowDays: Math.ceil(low), highDays: Math.ceil(high), from: addDays(day, Math.ceil(low)), to: addDays(day, Math.ceil(high)), pace: pc };
}
function dueForecast(days) {
  const day = today(); const out = [];
  for (let i = 0; i < days; i++) out.push({ day: addDays(day, i), n: 0 });
  Cx.list.forEach((t) => t.concepts.forEach((c) => {
    const raw = S().c[c.id]; if (!raw || !raw.n || !raw.d) return;
    let i = diffDays(raw.d, day); if (i < 0) i = 0; if (i < days) out[i].n++;
  }));
  return out;
}
