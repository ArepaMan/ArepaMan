// Renders EVERY exercise through the real UI component and solves it with the real controls.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext({ viewport: { width: 900, height: 900 } })).newPage();
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  const only = process.argv[2] || '';
  const res = await p.evaluate(async (only) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const host = document.createElement('div'); host.id = 'qa'; document.body.appendChild(host);
    const fails = []; let n = 0; const byType = {};
    const textOf = (ch) => rich(ch);
    const norm = (h) => { const d = document.createElement('div'); d.innerHTML = h; return d.innerHTML; };
    const clickByHtml = (root, sel, html) => { const want = norm(html); const el = Array.from(root.querySelectorAll(sel)).find((e) => e.innerHTML === want); if (!el) throw new Error('no element for ' + html.slice(0, 40)); el.click(); };
    for (const id in Cx.exercises) {
      if (only && !id.startsWith(only)) continue;
      const ex = Cx.exercises[id]; let done = null;
      host.innerHTML = '';
      const card = renderExercise(ex, { mode: 'free', onDone: (c) => { done = c; } });
      host.appendChild(card);
      try {
        const primary = () => Array.from(card.querySelectorAll('.actions .btn')).find((x) => /^(Check)$/.test(x.textContent.trim()));
        if (ex.type === 'mcq') {
          const ans = Array.isArray(ex.answer) ? ex.answer : [ex.answer];
          ans.forEach((a) => clickByHtml(card, '.choice', textOf(ex.choices[a])));
          if (Array.isArray(ex.answer)) primary().click();
        } else if (ex.type === 'fill') {
          card.querySelectorAll('input.blank').forEach((inp, i) => { inp.value = ex.blanks[i][0]; });
          primary().click();
        } else if (ex.type === 'spot') {
          const rows = card.querySelectorAll('.sl'); ex.bad.forEach((b) => rows[b - 1].click()); primary().click();
          if (ex.fix) { await sleep(60); clickByHtml(card, '.choice', textOf(ex.fix.choices[ex.fix.answer])); }
        } else if (ex.type === 'order') {
          for (const line of ex.lines) { const chip = Array.from(card.querySelectorAll('.o-pool .o-chip')).find((c) => c.querySelector('code').textContent === line); if (!chip) throw new Error('no chip ' + line); chip.click(); }
          primary().click();
        } else if (ex.type === 'predict') {
          card.querySelector('textarea.answer').value = ex.answer; primary().click();
        } else if (ex.type === 'code' || ex.type === 'sql') {
          card.querySelector('.CodeMirror').CodeMirror.setValue(ex.solution); primary().click();
        }
        let t = 0; while (!card.querySelector('.feedback.good') && t < 120) { await sleep(50); t++; }
        if (!card.querySelector('.feedback.good')) throw new Error('not accepted: ' + (card.querySelector('.feedback') || {}).innerText);
        // explanation step
        const ta = card.querySelector('.explain textarea');
        if (ta) {
          ta.value = 'my own explanation of the idea in a few words'; ta.dispatchEvent(new Event('input'));
          Array.from(card.querySelectorAll('.explain .btn')).find((x) => /Compare/.test(x.textContent)).click();
          card.querySelectorAll('.pt input').forEach((c) => { c.checked = true; });
          card.querySelector('.explain .btn.primary').click();
        }
        t = 0; while (!done && t < 40) { const cont = Array.from(card.querySelectorAll('.cont .btn')).find((x) => /Continue|Finish/.test(x.textContent)); if (cont) { cont.click(); break; } await sleep(50); t++; }
        t = 0; while (!done && t < 20) { await sleep(25); t++; }
        if (done !== 'ok') throw new Error('classified as ' + done);
        n++; byType[ex.type] = (byType[ex.type] || 0) + 1;
      } catch (e) { fails.push([id, ex.type, String(e.message || e).slice(0, 160)]); }
    }
    return { n, byType, fails };
  }, only);
  console.log('solved via UI:', res.n, JSON.stringify(res.byType));
  console.log('failures:', res.fails.length); res.fails.forEach((f) => console.log(' -', f.join(' | ')));
  console.log('page errors:', JSON.stringify(errs));
  await b.close();
  process.exit(res.fails.length || errs.length ? 1 : 0);
})();
