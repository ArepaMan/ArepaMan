'use strict';
/* ---------- helpers ---------- */
const NOW = () => Date.now() + (window.__skew || 0);
const p2 = (n) => String(n).padStart(2, '0');
const dayOf = (ts) => { const d = new Date(ts); return d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate()); };
const today = () => dayOf(NOW());
const parseDay = (s) => { const a = s.split('-').map(Number); return new Date(a[0], a[1] - 1, a[2], 12); };
const addDays = (s, n) => { const d = parseDay(s); d.setDate(d.getDate() + n); return dayOf(d.getTime()); };
const diffDays = (a, b) => Math.round((parseDay(a) - parseDay(b)) / 864e5);
const fmtDay = (s) => parseDay(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const sum = (a) => a.reduce((x, y) => x + y, 0);
const avg = (a) => (a.length ? sum(a) / a.length : 0);
const uniq = (a) => Array.from(new Set(a));
const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* hyperscript: h('div.card#id', {onclick, class, text, html, style:{}}, ...kids) */
function h(tag, props, ...kids) {
  const m = /^([a-z0-9]*)((?:[.#][\w-]+)*)$/i.exec(tag) || [];
  const el = document.createElement(m[1] || 'div');
  (m[2] || '').replace(/([.#])([\w-]+)/g, (_, k, v) => { if (k === '.') el.classList.add(v); else el.id = v; });
  if (props && (typeof props !== 'object' || props instanceof Node || Array.isArray(props))) { kids.unshift(props); props = null; }
  for (const k in props || {}) {
    const v = props[k];
    if (v == null || v === false) continue;
    if (k === 'class') v.split(' ').forEach((c) => c && el.classList.add(c));
    else if (k === 'text') el.textContent = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k.slice(0, 2) === 'on' && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'data') for (const d in v) el.dataset[d] = v[d];
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, v);
  }
  const add = (k) => {
    if (k == null || k === false) return;
    if (Array.isArray(k)) k.forEach(add);
    else el.appendChild(k instanceof Node ? k : document.createTextNode(String(k)));
  };
  kids.forEach(add);
  return el;
}
const SVGNS = 'http://www.w3.org/2000/svg';
function sv(tag, attrs, ...kids) {
  const parts = tag.split('.');
  const el = document.createElementNS(SVGNS, parts[0]);
  if (parts.length > 1) el.setAttribute('class', parts.slice(1).join(' '));
  for (const k in attrs || {}) if (attrs[k] != null) el.setAttribute(k, attrs[k]);
  const add = (c) => { if (c == null || c === false) return; if (Array.isArray(c)) c.forEach(add); else el.appendChild(c instanceof Node ? c : document.createTextNode(String(c))); };
  kids.forEach(add);
  return el;
}
const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };
const mount = (el, ...kids) => { clear(el); kids.forEach((k) => el.appendChild(k)); return el; };

/* inline rich text: `code`, **bold**, *em*, [label](https://...) */
function rich(s) {
  let t = esc(s);
  t = t.replace(/`([^`]+)`/g, (_, c) => '<code>' + c + '</code>');
  t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[^*\w])\*([^*\n]+)\*(?!\w)/g, '$1<em>$2</em>');
  t = t.replace(/\[([^\]]+)\]\((https:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return t.replace(/\n/g, '<br>');
}
const R = (s, tag) => h(tag || 'p', { html: rich(s) });

function toast(msg, kind) {
  let box = document.getElementById('toasts');
  if (!box) { box = h('div#toasts', { 'aria-live': 'polite' }); document.body.appendChild(box); }
  const t = h('div.toast' + (kind ? '.' + kind : ''), { text: msg });
  box.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 2600);
}

function copyText(text) {
  const fb = () => {
    const ta = h('textarea', { style: { position: 'fixed', opacity: 0 } }); ta.value = text; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) { /* ignore */ }
    ta.remove();
  };
  try { navigator.clipboard.writeText(text).catch(fb); } catch (e) { fb(); }
}

function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = () => rej(new Error('Could not load ' + src)); document.head.appendChild(s);
  });
}
const withTimeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms))]);

/* ---------- persistence ---------- */
const LS_KEY = 'skillradar.v1';
const freshState = () => ({
  v: 1, created: today(), updated: 0, sess: 0, rot: 0,
  streak: { cur: 0, best: 0, last: '', tok: 2, tokMonth: '' },
  days: {}, c: {}, lv: {}, plan: null, cfg: { theme: '' }, iv: { n: 0, last: '' }, hints: {},
});
const Store = {
  s: freshState(), log: [], notes: [], journal: [],
  mode: 'local', status: 'loading', // mode: cloud | local ; status: ok | saving | error | loading
  note: '', _t: null, _busy: false, _dirty: {}, db: null, listeners: [],
  onChange(fn) { this.listeners.push(fn); },
  emit() { this.listeners.forEach((f) => { try { f(); } catch (e) { console.error(e); } }); },
  loadLocal() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) { const o = JSON.parse(raw); if (o && o.s) { this.s = Object.assign(freshState(), o.s); this.log = o.log || []; this.notes = o.notes || []; this.journal = o.journal || []; } }
    } catch (e) { /* storage unavailable */ }
  },
  writeLocal() {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ s: this.s, log: this.log, notes: this.notes, journal: this.journal })); } catch (e) { /* ignore */ }
  },
  touch(kind) {
    this.s.updated = NOW();
    this._dirty[kind || 'state'] = true;
    if (kind === 'log' || kind === 'notes' || kind === 'journal') this._dirty.state = true;
    this.writeLocal();
    clearTimeout(this._t);
    this._t = setTimeout(() => this.flush(), 1800);
  },
  async attachCloud() {
    try {
      if (!window.claude || !window.claude.use) { this.status = 'ok'; this.note = 'Saved in this browser only.'; this.emit(); return; }
      const [db, user] = await Promise.all([withTimeout(window.claude.use('db'), 12000).catch(() => null), withTimeout(window.claude.use('user'), 12000).catch(() => null)]);
      let owner = false;
      try { owner = user ? await user.isOwner() : false; } catch (e) { owner = false; }
      if (!db || !owner) {
        this.mode = 'local'; this.status = 'ok';
        this.note = !db ? 'Saved in this browser only (account storage is unavailable here).' : 'Saved in this browser only (only the artifact owner can save to the account).';
        this.emit(); return;
      }
      this.db = db;
      const [a, b, c, j] = await Promise.all([db.doc('practice/state').get(), db.doc('practice/log').get(), db.doc('practice/notes').get(), db.doc('practice/journal').get()]);
      const cloud = a.exists ? a.data() : null;
      if (cloud && (cloud.updated || 0) > (this.s.updated || 0)) {
        this.s = Object.assign(freshState(), JSON.parse(JSON.stringify(cloud)));
        this.log = b.exists ? (b.data().items || []).slice() : [];
        this.notes = c.exists ? (c.data().items || []).slice() : [];
        this.journal = j.exists ? (j.data().items || []).slice() : [];
        this.writeLocal();
      } else if (this.s.updated) {
        this._dirty = { state: true, log: true, notes: true, journal: true };
      } else if (!j.exists && this.journal.length) { this._dirty.journal = true; }
      this.mode = 'cloud'; this.status = 'ok'; this.note = 'Saved to your account.';
      this.emit();
      if (Object.keys(this._dirty).length) this.flush();
    } catch (e) {
      console.warn('cloud attach failed', e);
      this.mode = 'local'; this.status = 'ok'; this.note = 'Saved in this browser only (account storage did not respond).'; this.emit();
    }
  },
  async flush() {
    if (this._busy) { clearTimeout(this._t); this._t = setTimeout(() => this.flush(), 1200); return; }
    if (this.mode !== 'cloud' || !this.db) { this._dirty = {}; return; }
    const d = this._dirty; this._dirty = {};
    this._busy = true; this.status = 'saving'; this.emit();
    try {
      if (d.state) await this.db.doc('practice/state').set(JSON.parse(JSON.stringify(this.s)));
      if (d.log) await this.db.doc('practice/log').set({ items: this.log.slice(-450) });
      if (d.notes) await this.db.doc('practice/notes').set({ items: this.notes.slice(-80) });
      if (d.journal) await this.db.doc('practice/journal').set({ items: this.journal.slice(-300) });
      this.status = 'ok'; this.note = 'Saved to your account.';
    } catch (e) {
      console.warn('save failed', e);
      this._dirty = Object.assign(this._dirty, d);
      this.status = 'error'; this.note = 'Could not reach account storage. Progress is kept in this browser and will retry.';
      setTimeout(() => this.flush(), 15000);
    }
    this._busy = false; this.emit();
  },
  exportJSON() { return JSON.stringify({ app: 'skill-radar', exportedAt: new Date(NOW()).toISOString(), state: this.s, log: this.log, notes: this.notes, journal: this.journal }, null, 1); },
  importJSON(txt) {
    const o = JSON.parse(txt);
    if (!o || !o.state || o.app !== 'skill-radar') throw new Error('This is not a Skill Radar backup.');
    this.s = Object.assign(freshState(), o.state); this.log = o.log || []; this.notes = o.notes || []; this.journal = o.journal || [];
    this._dirty = { state: true, log: true, notes: true, journal: true }; this.touch('state'); this.emit();
  },
  reset() { this.s = Object.assign(freshState(), { cfg: this.s.cfg }); this.log = []; this.notes = []; this.journal = []; this._dirty = { state: true, log: true, notes: true, journal: true }; this.touch('state'); this.emit(); },
};
