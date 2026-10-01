'use strict';
/* ---------- small charts and bits ---------- */
function bar(pct, cls) { return h('span.bar' + (cls ? '.' + cls : ''), { role: 'img', 'aria-label': Math.round(pct) + ' percent' }, h('i', { style: { width: clamp(pct, 0, 100) + '%' } })); }
function ring(pct, size, label, color) {
  const r = (size - 10) / 2, c = 2 * Math.PI * r; const off = c * (1 - clamp(pct, 0, 100) / 100);
  return sv('svg', { width: size, height: size, viewBox: '0 0 ' + size + ' ' + size, role: 'img', 'aria-label': label || pct + '%' },
    sv('circle', { cx: size / 2, cy: size / 2, r, fill: 'none', stroke: 'var(--line)', 'stroke-width': 7 }),
    sv('circle', { cx: size / 2, cy: size / 2, r, fill: 'none', stroke: color || 'var(--accent)', 'stroke-width': 7, 'stroke-linecap': 'round', 'stroke-dasharray': c, 'stroke-dashoffset': off, transform: 'rotate(-90 ' + size / 2 + ' ' + size / 2 + ')' }),
    sv('text', { x: size / 2, y: size / 2 + 5, 'text-anchor': 'middle', 'font-size': size / 4, 'font-weight': 700, fill: 'var(--ink)', 'font-family': 'var(--f-display)' }, Math.round(pct) + '%'));
}
function flameIcon() { return sv('svg', { width: 22, height: 22, viewBox: '0 0 24 24', 'aria-hidden': 'true' }, sv('path', { d: 'M12 2c1 4-3 5.5-3 9.5 0 1.6.9 2.8 2 3.3-.4-2.200.7-3.600 2-4.800.4 2.200 3 3.200 3 6a5 5 0 0 1-10 0c0-6 5-8 6-14z', fill: 'var(--warn)' })); }

function radarChart() {
  const tr = Cx.list; const n = tr.length; const W = 320, C = W / 2, Rr = 112;
  const pt = (i, v) => { const a = -Math.PI / 2 + (2 * Math.PI * i) / n; return [C + Math.cos(a) * Rr * v / 100, C + Math.sin(a) * Rr * v / 100]; };
  const poly = (vals) => vals.map((v, i) => pt(i, Math.max(v, 3)).join(',')).join(' ');
  const svg = sv('svg.radar', { viewBox: '-44 -8 ' + (W + 88) + ' ' + (W + 16), role: 'img', 'aria-label': 'Mastery by track: ' + tr.map((t) => t.name + ' ' + trackAvg(t.id)).join(', ') });
  [25, 50, 75, 100].forEach((g) => svg.appendChild(sv('polygon', { points: tr.map((_, i) => pt(i, g).join(',')).join(' '), fill: 'none', stroke: 'var(--line)', 'stroke-width': 1 })));
  tr.forEach((t, i) => { const p = pt(i, 100); svg.appendChild(sv('line', { x1: C, y1: C, x2: p[0], y2: p[1], stroke: 'var(--line)', 'stroke-width': 1 })); });
  svg.appendChild(sv('polygon', { points: poly(tr.map((t) => trackAvg(t.id, 'learned'))), fill: 'var(--accent)', 'fill-opacity': 0.14, stroke: 'var(--accent)', 'stroke-opacity': 0.45, 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }));
  svg.appendChild(sv('polygon', { points: poly(tr.map((t) => trackAvg(t.id))), fill: 'var(--accent)', 'fill-opacity': 0.32, stroke: 'var(--accent)', 'stroke-width': 2.2 }));
  tr.forEach((t, i) => { const p = pt(i, Math.max(trackAvg(t.id), 3)); svg.appendChild(sv('circle', { cx: p[0], cy: p[1], r: 4, fill: 'var(--c-' + t.id + ')', stroke: 'var(--surface)', 'stroke-width': 1.5 })); });
  tr.forEach((t, i) => {
    const p = pt(i, 128); const lv = trackUnlocked(t.id) ? 'L' + Math.min(trackLevel(t.id), t.maxLevel) : 'locked';
    const anchor = Math.abs(p[0] - C) < 6 ? 'middle' : p[0] > C ? 'start' : 'end';
    svg.appendChild(sv('text', { x: p[0], y: p[1] - 2, 'text-anchor': anchor, 'font-size': 12, 'font-weight': 700, fill: 'var(--ink)', 'font-family': 'var(--f-display)' }, t.short || t.name));
    svg.appendChild(sv('text', { x: p[0], y: p[1] + 12, 'text-anchor': anchor, 'font-size': 10.5, fill: 'var(--ink2)', 'font-family': 'var(--f-mono)' }, trackAvg(t.id) + '% · ' + lv));
  });
  return svg;
}
function heatmap(weeks) {
  const day = today(); const dow = (parseDay(day).getDay() + 6) % 7; // Monday=0
  const start = addDays(day, -(weeks * 7 - 1) - (6 - dow) + (6 - dow));
  const cell = 14, gap = 3; const W = weeks * (cell + gap), H = 7 * (cell + gap);
  const svg = sv('svg.heat', { viewBox: '0 0 ' + (W + 4) + ' ' + (H + 4), role: 'img', 'aria-label': 'Daily activity for the last ' + weeks + ' weeks' });
  const first = addDays(day, -dow - (weeks - 1) * 7);
  for (let w = 0; w < weeks; w++) for (let d = 0; d < 7; d++) {
    const ds = addDays(first, w * 7 + d); if (ds > day) continue;
    const n = (S().days[ds] || { ex: 0 }).ex; const lvl = n === 0 ? 0 : n < 5 ? 1 : n < 10 ? 2 : n < 15 ? 3 : 4;
    svg.appendChild(sv('rect', { x: 2 + w * (cell + gap), y: 2 + d * (cell + gap), width: cell, height: cell, rx: 3, class: 'hm l' + lvl + (ds === day ? ' today' : '') }, sv('title', {}, fmtDay(ds) + ': ' + n + ' exercises')));
  }
  return svg;
}
function forecastChart() {
  const data = dueForecast(14); const max = Math.max(4, ...data.map((d) => d.n)); const W = 336, H = 120, bw = 18, g = 6;
  const svg = sv('svg.fc', { viewBox: '0 0 ' + W + ' ' + (H + 28), role: 'img', 'aria-label': 'Reviews due over the next 14 days' });
  [0, 0.5, 1].forEach((f) => svg.appendChild(sv('line', { x1: 0, x2: W, y1: H - f * (H - 14), y2: H - f * (H - 14), stroke: 'var(--line)', 'stroke-width': 1 })));
  svg.appendChild(sv('text', { x: 0, y: 10, 'font-size': 10, fill: 'var(--ink2)' }, max));
  data.forEach((d, i) => {
    const hh = d.n ? Math.max(3, (d.n / max) * (H - 14)) : 0; const x = 12 + i * (bw + g);
    svg.appendChild(sv('rect', { x, y: H - hh, width: bw, height: hh, rx: 3, fill: i === 0 ? 'var(--accent)' : 'var(--accent2)' }, sv('title', {}, fmtDay(d.day) + ': ' + d.n + ' concept' + (d.n === 1 ? '' : 's') + ' due')));
    if (d.n) svg.appendChild(sv('text', { x: x + bw / 2, y: H - hh - 4, 'text-anchor': 'middle', 'font-size': 10, fill: 'var(--ink)', 'font-family': 'var(--f-mono)' }, d.n));
    if (i % 2 === 0) svg.appendChild(sv('text', { x: x + bw / 2, y: H + 14, 'text-anchor': 'middle', 'font-size': 9.5, fill: 'var(--ink2)', 'font-family': 'var(--f-mono)' }, i === 0 ? 'today' : parseDay(d.day).getDate()));
  });
  return svg;
}
function curveChart() {
  const W = 336, H = 130; const svg = sv('svg.curve', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Illustration: memory fades after learning; each spaced review makes it fade more slowly' });
  const reviews = [0, 1, 4, 11, 25]; const xs = (d) => 8 + (d / 40) * (W - 20); let path = ''; let stab = 1.2;
  const y = (r) => 10 + (1 - r) * (H - 36);
  reviews.forEach((d, k) => {
    const next = reviews[k + 1] === undefined ? 40 : reviews[k + 1];
    for (let t = d; t <= next; t += 0.5) { const r = Math.exp(-(t - d) / stab); path += (path ? 'L' : 'M') + xs(t).toFixed(1) + ',' + y(r).toFixed(1) + ' '; }
    stab *= 2.6;
    svg.appendChild(sv('line', { x1: xs(d), x2: xs(d), y1: 10, y2: H - 26, stroke: 'var(--accent)', 'stroke-opacity': 0.35, 'stroke-dasharray': '3 3' }));
    svg.appendChild(sv('text', { x: xs(d), y: H - 12, 'text-anchor': 'middle', 'font-size': 9.5, fill: 'var(--ink2)', 'font-family': 'var(--f-mono)' }, k === 0 ? 'learn' : 'day ' + d));
  });
  svg.insertBefore(sv('path', { d: path, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2.4, 'stroke-linejoin': 'round' }), svg.firstChild);
  svg.appendChild(sv('text', { x: W - 6, y: 12, 'text-anchor': 'end', 'font-size': 10, fill: 'var(--ink2)' }, 'how much you still remember'));
  return svg;
}

/* ---------- concept chip ---------- */
function conceptChip(c, o) {
  o = o || {}; const i = cinfo(c.id); const open = conceptOpen(c);
  const b = h('button.cc.st-' + i.state + (open ? '' : '.locked'), { type: 'button', title: c.title + ' · ' + STATE_LABEL[i.state] + (i.n ? ' · ' + i.eff + '%' : ''), onclick: () => { if (o.onclick) o.onclick(); else App.openConcept(c.id); } },
    h('span.cn', { text: c.title }), i.n ? h('span.cp', { text: i.eff + '%' }) : h('span.cp', { text: open ? 'new' : 'locked' }),
    i.fresh === 'fading' || i.fresh === 'rusty' ? h('span.fd.' + i.fresh, { title: FRESH_LABEL[i.fresh] }) : null);
  return b;
}

/* ---------- the App shell ---------- */
const TABS = [['today', 'Today'], ['map', 'Map'], ['drills', 'Drills'], ['journal', 'Journal'], ['stats', 'Stats']];
const App = {
  tab: 'today', detail: null, root: null,
  go(t) { this.tab = t; this.detail = null; try { history.replaceState(null, '', '#' + t); } catch (e) { /* ignore */ } this.render(); window.scrollTo(0, 0); },
  openConcept(cid) { this.detail = cid; this.render(); window.scrollTo(0, 0); },
  refreshChrome() {
    const chip = document.getElementById('sync'); if (!chip) return;
    const m = { saving: 'Saving…', error: 'Save problem', loading: 'Loading…' };
    chip.textContent = m[Store.status] || (Store.mode === 'cloud' ? 'Saved to account' : 'Saved in browser');
    chip.className = 'sync ' + (Store.status === 'error' ? 'bad' : Store.mode === 'cloud' ? 'good' : 'warn');
    chip.title = Store.note || '';
    const sv0 = streakView(); const sb = document.getElementById('streakbadge'); if (sb) sb.textContent = sv0.cur;
  },
  render() {
    const root = this.root; clear(root);
    const nav = h('nav.tabs', { role: 'tablist' }, TABS.map(([id, label]) => h('button.tab' + (this.tab === id && !this.detail ? '.on' : ''), { type: 'button', role: 'tab', 'aria-selected': this.tab === id, onclick: () => this.go(id) }, label)));
    const sb = streakView();
    const head = h('header.top', h('div.brand', radarMark(), h('span.bn', { text: 'Skill Radar' })),
      nav,
      h('div.top-r', h('span#streakwrap.streakwrap', { title: 'Day streak' }, flameIcon(), h('span#streakbadge', { text: sb.cur })), h('button.btn.ghost.sm#sync.sync', { type: 'button', onclick: () => this.go('stats') }), h('button.btn.ghost.sm.theme', { type: 'button', 'aria-label': 'Switch theme', onclick: () => cycleTheme(), text: themeLabel() })));
    const main = h('main.page');
    const bottom = h('nav.bottom', TABS.map(([id, label]) => h('button.btab' + (this.tab === id && !this.detail ? '.on' : ''), { type: 'button', onclick: () => this.go(id) }, tabIcon(id), h('span', { text: label }))));
    mount(root, head, main, bottom);
    try {
      if (this.detail) main.appendChild(View.concept(this.detail));
      else main.appendChild(View[this.tab]());
    } catch (e) { console.error(e); main.appendChild(h('div.card', h('h3', 'Something went wrong drawing this page'), h('pre.small', { text: String(e && e.stack || e) }))); }
    this.refreshChrome();
  },
};
function radarMark() { return sv('svg', { width: 26, height: 26, viewBox: '0 0 26 26', 'aria-hidden': 'true' }, sv('circle', { cx: 13, cy: 13, r: 11, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2 }), sv('circle', { cx: 13, cy: 13, r: 6, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 1.5, 'stroke-opacity': 0.6 }), sv('path', { d: 'M13 13 L22 8', stroke: 'var(--accent)', 'stroke-width': 2.2, 'stroke-linecap': 'round' }), sv('circle', { cx: 19, cy: 16, r: 2, fill: 'var(--warn)' })); }
function tabIcon(id) {
  const p = { today: 'M4 12l5 5L20 6', map: 'M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2zM9 4v14M15 6v14', drills: 'M13 2L4 14h7l-1 8 9-12h-7z', stats: 'M4 20V10M10 20V4M16 20v-8M22 20H2', journal: 'M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11' }[id];
  return sv('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' }, sv('path', { d: p }));
}
function themeLabel() { const t = S().cfg.theme; return t === 'dark' ? 'Dark' : t === 'light' ? 'Light' : 'Auto'; }
function applyTheme() { const t = S().cfg.theme; const r = document.documentElement; if (t) r.setAttribute('data-theme', t); else r.removeAttribute('data-theme'); }
function cycleTheme() { const o = ['', 'light', 'dark']; const c = S().cfg; c.theme = o[(o.indexOf(c.theme || '') + 1) % 3]; applyTheme(); Store.touch('state'); const b = document.querySelector('.theme'); if (b) b.textContent = themeLabel(); }

/* ---------- views ---------- */
const View = {
  today() {
    const plan = ensurePlan(); const s = S(); const sb = streakView();
    const wrap = h('div.grid.today');
    const left = h('section.card.todaycard');
    const remain = plan.steps.filter((x) => !x.done); const exLeft = remain.filter((x) => x.e).length;
    const revs = plan.steps.filter((x) => x.k === 'rev'), news = plan.steps.filter((x) => x.k === 'les');
    const first = !s.sess && !Object.keys(s.days).length;
    left.appendChild(h('div.kicker', { text: new Date(NOW()).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }) }));
    left.appendChild(h('h1', { text: first ? 'Welcome. Your first session is ready.' : remain.length ? 'Today’s session' : 'Today’s plan is done' }));
    left.appendChild(h('p.lede', { html: rich(first ? 'About 25 minutes: one new idea per track, then practice where **you write the code**. Hints come in steps; the solution unlocks after you try.' : remain.length ? '**' + revs.length + '** review' + (revs.length === 1 ? '' : 's') + ' · **' + news.length + '** new concept' + (news.length === 1 ? '' : 's') + ' · **' + exLeft + '** exercises · about **' + planEstMinutes(plan) + ' min**' : 'You can keep going with more, or stop here. Reviews are scheduled for you.') }));
    const list = h('ol.plan');
    plan.steps.forEach((st) => {
      const c = Cx.concepts[st.c]; const label = st.k === 'les' ? 'Learn: ' + c.title : st.k === 'int' ? 'Interview: ' + c.title : (st.k === 'rev' ? (st.maint ? 'Keep fresh: ' : 'Review: ') : 'Practise: ') + c.title;
      if (st.k !== 'les' && plan.steps.filter((x) => x.c === st.c && x.k !== 'les').length > 1 && plan.steps.find((x) => x.c === st.c && x.k === st.k && x.e) !== st) return; // collapse repeats
      const n = plan.steps.filter((x) => x.c === st.c && x.k === st.k && x.e).length;
      list.appendChild(h('li' + (st.done ? '.done' : ''), trackChip(c.track), h('span', { text: label + (st.k !== 'les' && n > 1 ? '  ×' + n : '') })));
    });
    left.appendChild(list);
    const act = h('div.actions');
    act.appendChild(h('button.btn.primary.big', { type: 'button', text: first ? 'Start my first session' : remain.length ? (plan.steps.some((x) => x.done) ? 'Resume session' : 'Start session') : 'Keep going', onclick: () => startToday() }));
    act.appendChild(h('button.btn.secondary', { type: 'button', title: 'Three quick exercises keep your streak alive', text: '5-minute minimum', onclick: () => startMinimum() }));
    left.appendChild(act);
    left.appendChild(h('p.muted.small', { text: sb.doneToday ? 'Streak counted for today. Extra sessions never hurt, since reviews stay on their own schedule.' : 'Answer ' + Math.max(0, 3 - sb.exToday) + ' exercise' + (3 - sb.exToday === 1 ? '' : 's') + ' today to extend your streak.' }));
    wrap.appendChild(left);

    const rightcol = h('div.rightcol');
    rightcol.appendChild(h('section.card.radarcard', h('h3', { text: 'Your skill radar' }), radarChart(), h('div.legend', h('span.lg.a', 'now (after fading)'), h('span.lg.b', 'learned peak'))));
    wrap.appendChild(rightcol);

    // streak
    const stc = h('section.card.streakcard', h('div.sline', flameIcon(), h('b.big', { text: sb.cur }), h('span', { text: sb.cur === 1 ? 'day streak' : 'day streak' })), h('div.dotsrow', Array.from({ length: 14 }, (_, k) => { const d = addDays(today(), k - 13); const n = (s.days[d] || { ex: 0 }).ex; return h('i' + (n >= 3 ? '.on' : n > 0 ? '.part' : '') + (k === 13 ? '.today' : ''), { title: fmtDay(d) + ': ' + n + ' exercises' }); })),
      h('p.muted.small', { text: 'Best ' + sb.best + ' · rest tokens left this month: ' + sb.tok + '. A token covers one missed day automatically.' }));
    rightcol.appendChild(stc);

    // tracks
    const tracks = h('section.span2', h('h2', { text: 'Tracks and next unlocks' }));
    const tg = h('div.tgrid'); Cx.list.forEach((t) => tg.appendChild(trackCard(t))); tracks.appendChild(tg); wrap.appendChild(tracks);

    // phases
    const ph = h('section.span2', h('h2', { text: 'Ready for each ReviewRadar phase?' }), h('p.muted', { text: 'Readiness is the average mastery of the concepts tagged for that phase.' }));
    const pg = h('div.pgrid'); Cx.phases.forEach((p) => pg.appendChild(phaseCard(p))); ph.appendChild(pg); wrap.appendChild(ph);

    // weak spots
    const weak = weakSpots(6);
    const wk = h('section.span2', h('div.rowbetween', h('h2', { text: 'Weak spots' }), weak.length ? h('button.btn.secondary.sm', { type: 'button', text: 'Drill them', onclick: () => startWeak() }) : null));
    if (!weak.length) wk.appendChild(h('div.card.empty', { text: 'Nothing is shaky yet. Concepts you miss or let fade will show up here with their next review date.' }));
    else { const wl = h('div.weak'); weak.forEach((w) => { const c = Cx.concepts[w.id]; const i = w.info; wl.appendChild(h('div.wrow', trackChip(c.track), h('button.link', { type: 'button', text: c.title, onclick: () => App.openConcept(c.id) }), h('span.chip.st-' + i.state, { text: STATE_LABEL[i.state] + ' ' + i.eff + '%' }), i.fresh !== 'fresh' ? h('span.chip.fd-' + i.fresh, { text: FRESH_LABEL[i.fresh] }) : null, h('span.muted.small.nx', { text: i.due ? (i.due <= today() ? 'due now' : 'next ' + fmtDay(i.due)) : '' }), h('button.btn.ghost.sm', { type: 'button', text: 'Practise', onclick: () => startPractice(w.id, 3) }))); }); wk.appendChild(h('div.card.weakc', wl)); }
    wrap.appendChild(wk);
    return wrap;
  },

  map() {
    const wrap = h('div.maps', h('h1', { text: 'Concept map' }), h('p.lede', 'Every concept has a short lesson and 2 to 4 exercises. Tap one to read or practise it. Levels unlock when you demonstrate mastery.'));
    Cx.list.forEach((t) => {
      const unlocked = trackUnlocked(t.id); const cur = trackLevel(t.id);
      const sec = h('section.card.tmap', h('div.rowbetween', h('h2', trackChip(t.id), ' ' + t.name), h('span.muted.small', { text: t.blurb })));
      if (!unlocked) sec.appendChild(h('div.lockmsg', { text: 'Locked. ' + t.unlockText }));
      t.levels.forEach((lv) => {
        const ls = levelStats(t.id, lv.n); const open = levelOpen(t.id, lv.n);
        const row = h('div.lvrow' + (open ? '' : '.locked'), h('div.lvhead', h('span.lvn', { text: 'L' + lv.n }), h('strong', { text: lv.name }), ls.cleared ? h('span.chip.st-mastered', { text: 'Cleared' }) : open ? h('span.chip.st-learning', { text: ls.avg + '% / ' + LEVEL_PASS + '%' }) : h('span.chip.muted', { text: 'Locked' }), h('span.muted.small', { text: lv.blurb })));
        const chips = h('div.chips2'); levelConcepts(t.id, lv.n).forEach((c) => chips.appendChild(conceptChip(c)));
        row.appendChild(chips); sec.appendChild(row);
      });
      wrap.appendChild(sec);
    });
    return wrap;
  },

  drills() {
    const wrap = h('div.drills', h('h1', { text: 'Drills' }), h('p.lede', 'Short, focused rounds. Everything here counts toward mastery and spaced review.'));
    const g = h('div.dgrid');
    const dueN = dueConcepts().length; const weakN = weakSpots(5).length;
    const card = (title, text, label, fn, dis) => h('div.card.dcard', h('h3', { text: title }), h('p', { html: rich(text) }), h('button.btn.primary' + (dis ? '[disabled]' : ''), { type: 'button', text: label, disabled: !!dis, onclick: fn }));
    g.appendChild(card('Interview drill', 'Six mixed questions in the style of ML engineering interviews: code, "what does this print", debugging. Uses concepts you have started.', 'Start drill', startInterview));
    g.appendChild(card('Due reviews', '**' + dueN + '** concept' + (dueN === 1 ? ' is' : 's are') + ' due or overdue. One question each.', dueN ? 'Review now' : 'Nothing due', startDue, !dueN));
    g.appendChild(card('Weak-spot drill', weakN ? 'Five questions on what is shakiest or fading.' : 'No weak spots right now.', 'Drill weak spots', startWeak, !weakN));
    wrap.appendChild(g);
    wrap.appendChild(h('h2', { text: 'Level checkpoints' }));
    wrap.appendChild(h('p.muted', { text: 'Five fresh questions with no hints. You need 4 clean answers to clear a level. A checkpoint opens when mastery is at least ' + LEVEL_PASS + '%.' }));
    const cg = h('div.dgrid');
    Cx.list.forEach((t) => {
      if (!trackUnlocked(t.id)) return; const L = trackLevel(t.id); if (L > t.maxLevel) { cg.appendChild(h('div.card.dcard', h('h3', trackChip(t.id), ' ' + t.name), h('p', 'All levels cleared. Keep it fresh with reviews.'))); return; }
      const ls = levelStats(t.id, L); const rec = lvState(t.id).cp[L];
      cg.appendChild(h('div.card.dcard', h('h3', trackChip(t.id), ' ' + t.name + ' · L' + L), reqList(ls), rec ? h('p.muted.small', { text: 'Tries: ' + rec.tries + ' · best ' + rec.best + '/5' }) : null, h('button.btn.primary', { type: 'button', text: ls.eligible ? 'Take the checkpoint' : 'Not unlocked yet', disabled: !ls.eligible, onclick: () => startCheckpoint(t.id, L) })));
    });
    wrap.appendChild(cg);
    wrap.appendChild(h('h2', { text: 'ReviewRadar phase checks' }));
    wrap.appendChild(h('p.muted', { text: 'A mixed round across tracks for one project phase. It works as a capstone and keeps old skills fresh, even after you have cleared every level.' }));
    const pgrid = h('div.dgrid');
    Cx.phases.forEach((ph) => { const r = phaseReadiness(ph.id); pgrid.appendChild(h('div.card.dcard', h('h3', { text: ph.name }), h('p', { text: ph.blurb }), h('div.pline', bar(r.pct), h('b', { text: r.pct + '%' })), h('button.btn.secondary', { type: 'button', text: 'Start phase check', onclick: () => startPhase(ph.id) }))); });
    wrap.appendChild(pgrid);
    return wrap;
  },

  journal() {
    const wrap = h('div.journal', h('h1', { text: 'Journal' }), h('p.lede', { text: 'Every miss carries information. Note why it happened and this page shows the pattern, so you can fix the habit and not only the answer.' }));
    const st = journalStats(60); const loose = missesWithoutReason(6);
    if (!st.items.length && !loose.length) {
      wrap.appendChild(h('div.card.empty', h('h3', { text: 'Nothing here yet' }), h('p', { text: 'When an exercise ends in a miss, or takes a lot of help, you will be asked why. Tap a reason and it is saved here. After a few entries you will see which kind of mistake is yours.' })));
      return wrap;
    }
    const g = h('div.grid');
    const max = Math.max(1, ...CAUSES.map((c) => st.counts[c.id]));
    const chart = h('section.card', h('h3', { text: 'What trips you up' }), h('p.muted.small', { text: 'Last 60 days. ' + st.items.length + ' entr' + (st.items.length === 1 ? 'y' : 'ies') + ', ' + st.fixed + ' since fixed.' }));
    CAUSES.forEach((c) => chart.appendChild(h('div.jbar', h('span.jl', { text: c.label }), h('span.bar', h('i', { style: { width: (st.counts[c.id] / max * 100) + '%' } })), h('b', { text: st.counts[c.id] }))));
    g.appendChild(chart);
    g.appendChild(h('section.card', h('h3', { text: st.top ? 'Your top pattern: ' + st.top.label.toLowerCase() : 'Your patterns' }), st.top ? h('p', { text: st.top.tip }) : h('p.muted', { text: 'Tag a few misses with a reason and a suggestion appears here.' }),
      st.repeat.length ? h('div', h('h4', { text: 'Concepts that keep catching you' }), ...st.repeat.slice(0, 5).map((r) => { const c = Cx.concepts[r.id]; return h('div.wrow', trackChip(c.track), h('button.link', { type: 'button', text: c.title, onclick: () => App.openConcept(c.id) }), h('span.chip.' + (r.fixed ? 'st-mastered' : 'st-shaky'), { text: r.n + ' entries' + (r.fixed ? ', fixed' : '') }), h('button.btn.ghost.sm', { type: 'button', text: 'Practise', onclick: () => startPractice(c.id, 3) })); })) : null));
    wrap.appendChild(g);
    if (loose.length) {
      const sec = h('section.card.looseC', h('h3', { text: 'Recent misses without a reason' }), h('p.muted.small', { text: 'Tap a reason to log it. It takes five seconds and makes the patterns above accurate.' }));
      loose.forEach((l) => {
        const ex = Cx.exercises[l.e]; const row = h('div.jentry');
        const done = () => { clear(row); row.appendChild(h('span.muted', { text: 'Saved.' })); };
        row.appendChild(h('div.jprompt', trackChip(ex.track), h('span', { text: ex.prompt.replace(/[`*]/g, '').slice(0, 100) })));
        row.appendChild(h('div.chips', CAUSES.map((c) => h('button.chip.cause', { type: 'button', text: c.label, onclick: () => { const entry = journalAdd(l.e, 'miss', { attempts: l.a, hints: l.h }); entry.t = l.t; journalSet(entry, [c.id], ''); done(); setTimeout(() => App.render(), 600); } }))));
        sec.appendChild(row);
      });
      wrap.appendChild(h('div.stack', sec));
    }
    const list = h('section.card', h('h3', { text: 'Entries' }));
    st.items.slice().reverse().slice(0, 30).forEach((j) => {
      const ex = Cx.exercises[j.e]; if (!ex) return; const fixed = journalFixed(j);
      list.appendChild(h('div.jentry', h('div.jprompt', trackChip(ex.track), h('strong', { text: Cx.concepts[j.c].title }), h('span.muted.small', { text: new Date(j.t).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }), h('span.chip.' + (fixed ? 'st-mastered' : 'st-shaky'), { text: fixed ? 'Fixed' : 'Open' })),
        h('div.small', { text: ex.prompt.replace(/[`*]/g, '').slice(0, 140) }),
        h('div.chips', j.why.length ? j.why.map((w) => h('span.chip', { text: (CAUSES.find((c) => c.id === w) || { label: w }).label })) : [h('span.chip.muted', { text: 'no reason noted' })]),
        j.x ? h('p.note.small', { text: j.x }) : null,
        h('div.actions', h('button.btn.secondary.sm', { type: 'button', text: 'Try it again', onclick: () => Session.start([{ k: 'rev', c: j.c, e: j.e, done: false }], { title: 'Retry from the journal', kind: 'drill' }) }), h('button.btn.ghost.sm', { type: 'button', text: 'Re-read the lesson', onclick: () => App.openConcept(j.c) }))));
    });
    wrap.appendChild(list);
    return wrap;
  },

  stats() {
    const s = S(); const wrap = h('div.stats', h('h1', { text: 'Stats and settings' }));
    const g = h('div.grid');
    const total = Object.values(s.days).reduce((n, d) => n + d.ex, 0); const mins = Math.round(Object.values(s.days).reduce((n, d) => n + d.sec, 0) / 60);
    const conceptsStarted = Cx.list.reduce((n, t) => n + t.concepts.filter((c) => cinfo(c.id).n).length, 0); const all = Object.keys(Cx.concepts).length;
    g.appendChild(h('section.card', h('h3', 'Totals'), h('div.sum-grid', h('div.sum', h('b', { text: total }), h('span', 'exercises')), h('div.sum', h('b', { text: mins }), h('span', 'minutes')), h('div.sum', h('b', { text: conceptsStarted + '/' + all }), h('span', 'concepts started')))));
    g.appendChild(h('section.card', h('h3', 'Activity'), h('div.heatwrap', heatmap(16)), h('p.muted.small', { text: 'Last 16 weeks. Darker means more exercises.' })));
    g.appendChild(h('section.card', h('h3', 'Reviews due, next 14 days'), forecastChart(), h('p.muted.small', { text: 'Concepts due on each day. Overdue ones count as today.' })));
    g.appendChild(h('section.card', h('h3', 'Why reviews are spaced'), curveChart(), h('p.muted.small', { text: 'Illustration. Each successful review pushes the next one further out (1, 3, 7, 14, 30, 60, 90, 180 days). Skip them and a concept shows as Fading, then Rusty.' })));
    // pace
    const pc = recentPace();
    g.appendChild(h('section.card', h('h3', 'Your pace'), h('p', { html: rich(pc.hasData ? 'Last 14 days: about **' + Math.round(pc.pace) + '** exercises on days you practise, **' + pc.act + '** active days, **' + Math.round(pc.acc * 100) + '%** clean answers.' : 'Not enough data yet. Timelines use a default of about 9 exercises a day until you have two active days.') }), h('p.muted.small', { text: 'Timeline estimates on the Today tab use this pace and become more accurate the longer you use the app.' })));
    // history
    const hist = h('section.card.span2', h('h3', 'Recent answers'));
    const recent = Store.log.slice(-25).reverse();
    if (!recent.length) hist.appendChild(h('div.muted', { text: 'Answers will be listed here.' }));
    else { const tb = h('table.hist'); tb.appendChild(h('thead', h('tr', ['When', 'Concept', 'Result', 'Hints'].map((x) => h('th', { text: x }))))); const body = h('tbody'); recent.forEach((l) => { const c = Cx.concepts[l.c]; if (!c) return; body.appendChild(h('tr', h('td', { text: new Date(l.t).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }), h('td', trackChip(c.track), ' ' + c.title), h('td', h('span.chip.r-' + l.r, { text: l.r === 'ok' ? 'clean' : l.r === 'hint' ? 'with help' : 'missed' })), h('td', { text: l.h || '' }))); }); tb.appendChild(body); hist.appendChild(h('div.tscroll', tb)); }
    g.appendChild(hist);
    // notes
    const nt = h('section.card.span2', h('h3', 'Your explanations'));
    const notes = Store.notes.slice(-8).reverse();
    if (!notes.length) nt.appendChild(h('div.muted', { text: 'When an exercise asks you to explain in your own words, your answer is kept here for review.' }));
    notes.forEach((n) => { const e = Cx.exercises[n.e]; nt.appendChild(h('div.note', h('div.small.muted', { text: (e ? Cx.concepts[e.concept].title : n.e) + ' · ' + new Date(n.t).toLocaleDateString() }), h('p', { text: n.x }))); });
    g.appendChild(nt);
    // settings
    const set = h('section.card.span2', h('h3', 'Storage and backup'));
    const where = Store.mode === 'cloud' ? 'in this artifact\u2019s private account storage (only you can read it), mirrored in this browser.' : 'in this browser only. ' + (Store.note || '');
    set.appendChild(h('p', { html: rich('**Where progress lives:** ' + where) }));
    set.appendChild(h('p.muted.small', { text: 'Engines: Python runner ' + (Engine.py.state === 'idle' ? 'not started yet' : Engine.py.state) + ', SQL engine ' + (Engine.sql.state === 'idle' ? 'not started yet' : Engine.sql.state) + '.' + (Engine.py.state === 'failed' ? ' Python exercises fall back to self-check.' : '') }));
    const bk = h('div.actions');
    bk.appendChild(h('button.btn.secondary', { type: 'button', text: 'Save backup file', onclick: async () => { try { const d = await window.claude.use('downloads'); if (!d) throw new Error('n/a'); await d.save({ filename: 'skill-radar-progress.json', data: Store.exportJSON() }); } catch (e) { toast('Could not start a download here. Use “Copy backup” instead.', 'warn'); } } }));
    bk.appendChild(h('button.btn.ghost', { type: 'button', text: 'Copy backup', onclick: () => { copyText(Store.exportJSON()); toast('Backup copied'); } }));
    set.appendChild(bk);
    const ta = h('textarea.mono', { rows: 3, placeholder: 'Paste a backup here to restore it', 'aria-label': 'Paste backup' });
    set.appendChild(ta); set.appendChild(h('div.actions', h('button.btn.ghost', { type: 'button', text: 'Restore from pasted backup', onclick: () => { try { Store.importJSON(ta.value); toast('Progress restored'); App.render(); } catch (e) { toast(String(e.message || e), 'bad'); } } })));
    let armed = false; const rb = h('button.btn.danger', { type: 'button', text: 'Reset all progress', onclick: () => { if (!armed) { armed = true; rb.textContent = 'Tap again to erase everything'; setTimeout(() => { armed = false; rb.textContent = 'Reset all progress'; }, 4000); } else { Store.reset(); toast('Progress erased'); App.render(); } } });
    set.appendChild(h('div.actions', rb));
    g.appendChild(set);
    wrap.appendChild(g); return wrap;
  },

  concept(cid) {
    const c = Cx.concepts[cid]; const wrap = h('div.cpage');
    wrap.appendChild(h('button.btn.ghost.sm', { type: 'button', text: '← Back to ' + (App.tab === 'map' ? 'the map' : 'dashboard'), onclick: () => { App.detail = null; App.render(); } }));
    wrap.appendChild(lessonCard(c, conceptOpen(c) ? () => startConcept(cid) : null, { cta: 'Learn and practise this concept' }));
    if (!conceptOpen(c)) wrap.appendChild(h('div.lockmsg', { text: 'You can read this lesson now. Exercises unlock when you reach Level ' + c.level + ' in ' + Cx.tracks[c.track].name + '.' }));
    const raw = S().c[cid]; const info = cinfo(cid);
    const ex = h('section.card', h('div.rowbetween', h('h3', 'Exercises'), info.n ? h('span.muted.small', { text: 'Mastery ' + info.eff + '% · ' + STATE_LABEL[info.state] + (info.due ? ' · next review ' + (info.due <= today() ? 'now' : fmtDay(info.due)) : '') }) : null));
    c.exercises.forEach((e) => { const r = raw && raw.ex[e.id]; ex.appendChild(h('div.exrow', h('span.chip.muted', { text: TYPE_LABEL[e.type] }), h('span.exp', { text: e.prompt.replace(/[`*]/g, '').slice(0, 90) + (e.prompt.length > 90 ? '…' : '') }), h('span.dots', [1, 2, 3].map((i) => h('i' + (i <= (e.diff || 1) ? '.on' : ''))), ), r ? h('span.chip.r-' + r.r, { text: r.r === 'ok' ? 'clean' : r.r === 'hint' ? 'with help' : 'missed' }) : h('span.chip.muted', { text: 'not tried' }))); });
    if (conceptOpen(c)) ex.appendChild(h('div.actions', h('button.btn.primary', { type: 'button', text: 'Practise 3', onclick: () => startPractice(cid, 3) })));
    wrap.appendChild(ex);
    return wrap;
  },
};

function reqList(ls) {
  const item = (ok, text) => h('li' + (ok ? '.ok' : ''), h('span.mk', { text: ok ? '✓' : '○' }), h('span', { text }));
  return h('ul.reqs', item(ls.avg >= LEVEL_PASS, 'Mastery ' + ls.avg + '% (need ' + LEVEL_PASS + '%)'), item(ls.solved >= ls.reqEx, Math.min(ls.solved, ls.reqEx) + ' of ' + ls.reqEx + ' exercises solved'), item(ls.nh >= ls.reqNH, Math.min(ls.nh, ls.reqNH) + ' of ' + ls.reqNH + ' solved with no hints'), item(ls.cleared, 'Checkpoint passed'));
}
function trackCard(t) {
  const unlocked = trackUnlocked(t.id); const L = trackLevel(t.id); const done = L > t.maxLevel;
  const card = h('div.card.tcard.t-' + t.id + (unlocked ? '' : '.locked'));
  card.appendChild(h('div.rowbetween', h('h3', t.name), trackFreshness(t.id) !== 'none' ? h('span.chip.fd-' + trackFreshness(t.id), { text: FRESH_LABEL[trackFreshness(t.id)] }) : null));
  if (!unlocked) { card.appendChild(h('p.muted', { text: t.unlockText })); return card; }
  if (done) { card.appendChild(h('p', { text: 'All levels cleared.' })); card.appendChild(h('p.muted.small', { text: trackFreshness(t.id) === 'rusty' ? 'Rusty. A quick review round restores it.' : 'Keep it fresh with reviews.' })); return card; }
  const ls = levelStats(t.id, L); const lv = t.levels[L - 1];
  card.appendChild(h('div.tline', ring(ls.avg, 64, 'Mastery of this level', 'var(--c-' + t.id + ')'), h('div', h('div.lvname', { text: 'Level ' + L + ' of ' + t.maxLevel + ': ' + lv.name }), h('div.muted.small', { text: ls.started + ' of ' + ls.count + ' concepts started · mastery, ' + LEVEL_PASS + '% unlocks the next level' }))));
  card.appendChild(reqList(ls));
  const act = h('div.actions');
  const nxt = nextNew(t.id);
  act.appendChild(h('button.btn.secondary.sm', { type: 'button', text: nxt ? 'Learn next' : 'Practise', onclick: () => { if (nxt) startConcept(nxt); else { const w = levelConcepts(t.id, L).filter((c) => cinfo(c.id).n).sort((a, b) => cinfo(a.id).eff - cinfo(b.id).eff)[0]; if (w) startPractice(w.id, 3); else App.go('map'); } } }));
  if (ls.eligible) act.appendChild(h('button.btn.primary.sm', { type: 'button', text: 'Take checkpoint', onclick: () => startCheckpoint(t.id, L) }));
  card.appendChild(act);
  // timeline
  const sel = h('select', { 'aria-label': 'Target level for ' + t.name, onchange: () => draw() }, Array.from({ length: t.maxLevel - L + 1 }, (_, k) => L + k).map((x) => h('option', { value: x, text: x === t.maxLevel ? 'Expert (clear L' + x + ')' : 'Clear L' + x })));
  const out = h('div.est');
  const draw = () => {
    const e = estimateTo(t.id, +sel.value); clear(out);
    if (e.done) { out.textContent = 'Already cleared.'; return; }
    out.appendChild(h('div', h('b', { text: '~' + e.sessions + ' session' + (e.sessions === 1 ? '' : 's') }), h('span.muted', { text: ' of practising ' + t.short })));
    out.appendChild(h('div.muted.small', { text: 'about ' + fmtDay(e.from) + ' to ' + fmtDay(e.to) + ' at ' + (e.pace.hasData ? 'your pace' : 'a default pace') }));
  };
  card.appendChild(h('div.pathbox', h('label.small.muted', { text: 'Timeline to ' }), sel, out)); draw();
  return card;
}
function phaseCard(p) {
  const r = phaseReadiness(p.id);
  const c = h('div.card.pcard.ps-' + r.status.replace(' ', '-'));
  c.appendChild(h('div.rowbetween', h('h3', p.name), h('span.chip.ps-' + r.status.replace(' ', '-'), { text: r.status === 'ready' ? 'Ready' : r.status === 'almost' ? 'Almost' : 'Not yet' })));
  c.appendChild(h('div.muted.small', { text: p.blurb })); c.appendChild(h('div.pline', bar(r.pct), h('b', { text: r.pct + '%' })));
  c.appendChild(h('div.muted.small', { text: r.solid + ' of ' + r.total + ' skills solid' }));
  const miss = r.missing.slice(0, 3);
  if (miss.length) { c.appendChild(h('div.small.lbl', { text: 'Work on' })); c.appendChild(h('div.chips', miss.map((m) => h('button.chip.link' + (m.open ? '' : '.muted'), { type: 'button', title: m.open ? 'Open' : 'Locked behind Level ' + m.c.level, text: m.c.title + (m.open ? '' : ' (L' + m.c.level + ')'), onclick: () => App.openConcept(m.c.id) })))); }
  return c;
}
function startMinimum() {
  const due = dueConcepts().slice(0, 3); const steps = [];
  due.forEach((d) => steps.push({ k: 'rev', c: d.id, e: pickEx(d.id), done: false }));
  if (steps.length < 3) weakSpots(3).forEach((w) => { if (steps.length < 3 && !steps.some((x) => x.c === w.id)) steps.push({ k: 'rev', c: w.id, e: pickEx(w.id), done: false }); });
  if (steps.length < 3) { const p = ensurePlan(); p.steps.filter((x) => x.e && !x.done).slice(0, 3 - steps.length).forEach((x) => steps.push({ k: x.k, c: x.c, e: x.e, done: false })); }
  if (!steps.length) { toast('Nothing to practise yet. Start the full session.', 'warn'); return; }
  Session.start(steps, { title: '5-minute minimum', kind: 'min' });
}
