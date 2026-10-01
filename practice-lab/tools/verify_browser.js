// Runs every code/sql exercise through the REAL in-page engines (Brython / sql.js): solution must pass, starter must not.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext()).newPage();
  p.on('pageerror', (e) => console.log('PAGEERROR', e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded", { timeout: 20000 });
  const only = process.argv[2] || '';
  const res = await p.evaluate(async (only) => {
    const bad = []; let n = 0, py = 0, sq = 0;
    for (const id in Cx.exercises) {
      const ex = Cx.exercises[id]; if (only && !id.startsWith(only)) continue;
      try {
        if (ex.type === 'code') {
          py++; const r = await Engine.py.run(ex.solution, ex.tests);
          if (r.error || !r.cases.length || r.cases.some((c) => !c.ok)) bad.push([id, 'solution', r.error || JSON.stringify(r.cases.filter((c) => !c.ok).slice(0, 2))]);
          const s = await Engine.py.run(ex.starter, ex.tests);
          if (!s.error && s.cases.length && s.cases.every((c) => c.ok)) bad.push([id, 'starter passes']);
        } else if (ex.type === 'sql') {
          sq++; const exp = await Engine.sql.expected(ex);
          if (exp.error) { bad.push([id, 'solution sql error', exp.error]); continue; }
          const sol = await Engine.sql.runUser(ex, ex.solution);
          const c1 = sqlCompare(exp.res, sol.res, ex); if (!c1.ok) bad.push([id, 'solution != expected', c1.msg]);
          const st = await Engine.sql.runUser(ex, ex.starter);
          if (!st.error) { const c2 = sqlCompare(exp.res, st.res, ex); if (c2.ok) bad.push([id, 'starter passes']); }
        }
        n++;
      } catch (e) { bad.push([id, 'exception', String(e && e.message || e)]); }
    }
    return { n, py, sq, bad };
  }, only);
  console.log(`checked ${res.n} (python ${res.py}, sql ${res.sq}); failures: ${res.bad.length}`);
  res.bad.forEach((x) => console.log(' -', x.join(' | ')));
  await b.close();
  process.exit(res.bad.length ? 1 : 0);
})();
