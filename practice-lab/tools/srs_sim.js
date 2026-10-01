const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext()).newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  const out = await p.evaluate(() => {
    const log = [];
    const DAY = 864e5;
    // a diligent learner: clean answers every day, does the full plan, takes checkpoints when offered
    let unlockedAt = {};
    for (let d = 0; d < 60; d++) {
      window.__skew = d * DAY;
      const plan = ensurePlan();
      plan.steps.forEach((st) => { st.done = true; if (st.e) record(st.e, 'ok', { hints: 0, attempts: 1, ms: 30000 }); });
      plan.counted = true; S().sess++;
      Cx.list.forEach((t) => {
        if (!trackUnlocked(t.id)) return;
        const L = trackLevel(t.id); if (L > t.maxLevel) return;
        const ls = levelStats(t.id, L);
        if (ls.eligible) { passCheckpoint(t.id, L, 5, 5); unlockedAt[t.id + ' L' + L] = d + 1; }
      });
      if (d % 10 === 9) log.push('day ' + (d + 1) + ': ' + Cx.list.map((t) => t.id + ' L' + trackLevel(t.id) + ' ' + trackAvg(t.id) + '%').join(' | '));
    }
    // timeline estimate sanity for python right now
    const est = estimateTo('python', 5);
    // forgetting: jump 90 days ahead without practice
    window.__skew = (60 + 90) * DAY;
    const fresh = Cx.list.map((t) => t.id + ':' + trackFreshness(t.id) + ' avg ' + trackAvg(t.id) + '% learned ' + trackAvg(t.id, 'learned') + '%').join(' | ');
    const sample = cinfo('py.vars');
    return { log, unlockedAt, est, fresh, sample, due: dueConcepts().length, planAfterBreak: ensurePlan().steps.length };
  });
  out.log.forEach((l) => console.log(l));
  console.log('unlocked (day):', JSON.stringify(out.unlockedAt));
  console.log('estimate python->L5 (state at day 60):', JSON.stringify(out.est));
  console.log('after 90 idle days:', out.fresh);
  console.log('py.vars after idle:', JSON.stringify(out.sample), 'due:', out.due, 'plan steps:', out.planAfterBreak);
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
