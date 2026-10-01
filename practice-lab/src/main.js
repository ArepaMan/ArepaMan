'use strict';
/* ---------- boot ---------- */
async function fetchJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }
async function boot() {
  const root = document.getElementById('app'); App.root = root;
  Store.loadLocal(); applyTheme();
  root.appendChild(h('div.boot', h('div.spinner'), h('p', 'Loading your practice lab…')));
  try {
    const cur = await fetchJSON('content/curriculum.json');
    const files = {};
    await Promise.all(cur.tracks.map(async (t) => { files[t.id] = await fetchJSON('content/' + t.id + '.json'); }));
    indexContent(cur, files);
  } catch (e) {
    console.error(e);
    mount(root, h('div.card.page', h('h2', 'Could not load the exercises'), h('p', 'The content files did not load. Reload the page. If it keeps happening, the artifact may need republishing.'), h('pre.small', { text: String(e) }), h('button.btn.primary', { type: 'button', text: 'Reload', onclick: () => location.reload() })));
    return;
  }
  const hash = (location.hash || '').replace('#', ''); if (TABS.some((t) => t[0] === hash)) App.tab = hash;
  Store.onChange(() => App.refreshChrome());
  App.render();
  Store.attachCloud().then(() => { applyTheme(); if (!Session.run) App.render(); else App.refreshChrome(); });
  const flush = () => { if (Store._dirty && Object.keys(Store._dirty).length) Store.flush(); };
  document.addEventListener('visibilitychange', () => { if (document.hidden) flush(); });
  window.addEventListener('pagehide', flush);
  window.addEventListener('hashchange', () => { const t = (location.hash || '').replace('#', ''); if (TABS.some((x) => x[0] === t) && t !== App.tab && !Session.run) App.go(t); });
}
window.addEventListener('DOMContentLoaded', boot);
