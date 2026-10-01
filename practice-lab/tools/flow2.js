// checkpoint + phase check + drills through the real session runner
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext({ viewport: { width: 900, height: 900 } })).newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html'); await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  const res = await p.evaluate(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const DAY = 864e5; const out = {};
    for (let d = 0; d < 12; d++) { window.__skew = d * DAY; const plan = ensurePlan(); plan.steps.forEach((st) => { st.done = true; if (st.e) record(st.e, 'ok', { hints: 0, attempts: 1 }); }); plan.counted = true; S().sess++; }
    window.__skew = 12 * DAY;
    const ls = levelStats('python', 1); out.eligible = ls.eligible; out.avg = ls.avg;
    // run a checkpoint by solving each exercise through the UI
    async function solveCurrent() {
      const card = document.querySelector('#session .xcard'); const id = Session.run.steps[Session.run.i].e; const ex = Cx.exercises[id];
      const norm = (h) => { const d = document.createElement('div'); d.innerHTML = h; return d.innerHTML; };
      const click = (sel, html) => Array.from(card.querySelectorAll(sel)).find((e) => e.innerHTML === norm(html)).click();
      const primary = () => Array.from(card.querySelectorAll('.actions .btn')).find((x) => x.textContent.trim() === 'Check');
      if (ex.type === 'predict') { card.querySelector('textarea.answer').value = ex.answer; primary().click(); }
      else if (ex.type === 'code') { card.querySelector('.CodeMirror').CodeMirror.setValue(ex.solution); primary().click(); }
      else if (ex.type === 'mcq') click('.choice', rich(ex.choices[ex.answer]));
      else if (ex.type === 'spot') { const rows = card.querySelectorAll('.sl'); ex.bad.forEach((x) => rows[x - 1].click()); primary().click(); await sleep(80); if (ex.fix) click('.choice', rich(ex.fix.choices[ex.fix.answer])); }
      else if (ex.type === 'order') { ex.lines.forEach((l) => Array.from(card.querySelectorAll('.o-pool .o-chip')).find((c) => c.querySelector('code').textContent === l).click()); primary().click(); }
      else if (ex.type === 'fill') { card.querySelectorAll('input.blank').forEach((i, k) => { i.value = ex.blanks[k][0]; }); primary().click(); }
      let t = 0; while (!card.querySelector('.feedback.good') && t < 100) { await sleep(50); t++; }
      const cont = () => Array.from(card.querySelectorAll('.cont .btn')).find((x) => /Continue|Finish/.test(x.textContent));
      t = 0; while (!cont() && t < 60) { await sleep(50); t++; } cont().click(); await sleep(60);
    }
    startCheckpoint('python', 1); await sleep(100);
    out.cpSteps = Session.run.steps.length; out.noHintBtn = !Array.from(document.querySelectorAll('#session .actions .btn')).some((x) => /^Hint/.test(x.textContent) && !x.hidden);
    for (let k = 0; k < out.cpSteps; k++) await solveCurrent();
    out.summary = document.querySelector('#session .summary') ? document.querySelector('#session .summary').innerText.slice(0, 160) : 'NO SUMMARY';
    out.cleared = lvState('python').cleared.slice(); out.levelNow = trackLevel('python');
    Session.exit();
    // phase check
    startPhase('data'); await sleep(100); out.phaseSteps = Session.run.steps.length; Session.exit();
    startInterview(); await sleep(100); out.intSteps = Session.run ? Session.run.steps.length : 0; if (Session.run) Session.exit();
    startWeak(); await sleep(50); out.weak = Session.run ? Session.run.steps.length : 0; if (Session.run) Session.exit();
    // rest token / streak gap logic
    window.__skew = 15 * DAY; out.streakAfterGap3 = streakView();
    window.__skew = 30 * DAY; out.streakAfterGap18 = streakView();
    return out;
  });
  console.log(JSON.stringify(res, null, 1)); console.log('errors', JSON.stringify(errs));
  await b.close();
})();
