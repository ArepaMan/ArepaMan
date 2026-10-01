const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const SH = '/tmp/claude-0/-home-user-ArepaMan/8fc33d1f-50c8-5d6b-b4b1-76904f7b8846/scratchpad/shots/';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext({ viewport: { width: 1000, height: 1000 } })).newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html'); await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  // 1. a miss through the UI: attempt, reveal solution, tag reasons, continue
  await p.evaluate(() => { Session.start([{ k: 'new', c: 'py.vars', e: 'py.vars.1', done: false }, { k: 'new', c: 'py.arith', e: 'py.arith.3', done: false }], { title: 'T', kind: 'free' }); });
  await p.waitForSelector('#session .xcard');
  await p.fill('#session textarea.answer', '1 1'); await p.click('#session .btn.primary >> text=Check');
  await p.waitForSelector('.feedback.bad');
  await p.click('#session >> text=Show solution'); await p.waitForSelector('.journal-prompt');
  await p.click('.chip.cause >> text=Did not understand the idea'); await p.click('.chip.cause >> text=Misread the question');
  await p.fill('.journal-prompt textarea', 'I assumed b followed a'); await p.click('.journal-prompt .chip.cause >> nth=0'); await p.click('.journal-prompt .chip.cause >> nth=0');
  await p.screenshot({ path: SH + 'journal-prompt.png' });
  await p.click('#session >> text=Continue');
  const r1 = await p.evaluate(() => ({ journal: Store.journal, relearn: S().c['py.vars'].relearn, local: JSON.parse(localStorage.getItem('skillradar.v1')).journal.length }));
  console.log('after miss:', JSON.stringify(r1));
  // 2. second exercise: correct with 1 hint -> no prompt
  await p.evaluate(() => Session.exit());
  // 3. a miss without a reason in the log, then the journal view
  const r2 = await p.evaluate(() => {
    record('py.arith.3', 'miss', { attempts: 2 }); record('py.arith.1', 'miss', { attempts: 1 });
    window.__skew = 864e5; const plan = ensurePlan();
    return { loose: missesWithoutReason(5).length, planHasRelearn: plan.steps.some((x) => x.relearn && x.c === 'py.vars'), firstStep: plan.steps[0] };
  });
  console.log('journal state:', JSON.stringify(r2));
  await p.evaluate(() => { window.__skew = 0; App.go('journal'); });
  await p.screenshot({ path: SH + 'journal-tab.png', fullPage: true });
  // retro tag one
  await p.click('.looseC .chip.cause >> nth=2'); await p.waitForTimeout(900);
  console.log('entries now:', await p.evaluate(() => Store.journal.length), 'stats', JSON.stringify(await p.evaluate(() => { const s = journalStats(60); return { n: s.items.length, top: s.top && s.top.id, counts: s.counts }; })));
  // backup round trip keeps journal
  const rt = await p.evaluate(() => { const j = Store.exportJSON(); const n = Store.journal.length; Store.journal = []; Store.importJSON(j); return [n, Store.journal.length]; });
  console.log('export/import journal:', JSON.stringify(rt), 'errors', JSON.stringify(errs));
  // mobile nav shows 5 tabs
  await p.setViewportSize({ width: 390, height: 800 }); await p.evaluate(() => App.go('journal'));
  await p.screenshot({ path: SH + 'journal-mobile.png' });
  await b.close();
})().catch((e) => { console.error('FAIL', e.message); process.exit(1); });
