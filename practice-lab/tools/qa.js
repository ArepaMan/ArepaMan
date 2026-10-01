// Seeds ~10 days of fake practice (moving the clock), then screenshots every tab, concept pages with widgets and each exercise type.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const SH = '/tmp/claude-0/-home-user-ArepaMan/8fc33d1f-50c8-5d6b-b4b1-76904f7b8846/scratchpad/shots/';
const mobile = process.argv[2] === 'mobile';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await b.newContext({ viewport: mobile ? { width: 390, height: 844 } : { width: 1180, height: 900 } });
  const p = await ctx.newPage();
  const errs = [];
  p.on('console', (m) => { if (m.type() === 'error' && !/CERT|404/.test(m.text())) errs.push(m.text()); });
  p.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message));
  const tag = mobile ? 'm' : 'd';
  await p.goto('http://localhost:8200/test.html');
  await p.evaluate(() => localStorage.clear());
  await p.reload();
  await p.waitForSelector('.todaycard');
  const seeded = await p.evaluate(() => {
    const out = [];
    for (let i = 0; i < 10; i++) {
      window.__skew = (i - 9) * 864e5;
      const plan = ensurePlan();
      let n = 0;
      plan.steps.forEach((st) => {
        st.done = true;
        if (st.e) { const r = Math.random(); record(st.e, r < 0.65 ? 'ok' : r < 0.85 ? 'hint' : 'miss', { hints: r < 0.85 && r >= 0.65 ? 1 : 0, attempts: 1, ms: 40000 }); n++; }
      });
      plan.counted = true; S().sess++;
      out.push(n);
    }
    window.__skew = 0; Store.touch('state');
    return { perDay: out, concepts: Object.keys(S().c).length, streak: S().streak, due: dueConcepts().length };
  });
  console.log('seeded', JSON.stringify(seeded));
  await p.evaluate(() => { App.render(); });
  await p.screenshot({ path: SH + tag + '-qa-today.png', fullPage: true });
  for (const t of ['map', 'drills', 'stats']) {
    await p.evaluate((t) => App.go(t), t);
    await p.screenshot({ path: SH + tag + '-qa-' + t + '.png', fullPage: true });
  }
  // concept pages with widgets
  for (const cid of ['py.numpy2', 'sql.joins', 'docker.layers', 'py.torch1', 'sql.window1', 'py.metrics', 'k8s.pods', 'sh.pipes']) {
    await p.evaluate((c) => App.openConcept(c), cid);
    await p.screenshot({ path: SH + tag + '-qa-concept-' + cid + '.png', fullPage: true });
  }
  // widget/lesson integrity across ALL concepts
  const bad = await p.evaluate(() => {
    const bad = [];
    for (const cid in Cx.concepts) { App.openConcept(cid); const t = document.querySelector('main.page').innerText; if (/\[widget error\]|\[missing widget/.test(t)) bad.push(cid); }
    return bad;
  });
  console.log('concepts with widget problems:', JSON.stringify(bad));
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})().catch((e) => { console.error('QA FAIL', e); process.exit(1); });
