const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const SH = '/tmp/claude-0/-home-user-ArepaMan/8fc33d1f-50c8-5d6b-b4b1-76904f7b8846/scratchpad/shots/';
const mobile = process.argv[2] !== 'desktop';
const theme = process.argv[3] || '';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await b.newContext({ viewport: mobile ? { width: 390, height: 844 } : { width: 1100, height: 900 }, colorScheme: theme === 'dark' ? 'dark' : 'light' });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  const tag = (mobile ? 'm' : 'd') + (theme ? '-' + theme : '') + '-ex-';
  const list = ['sql.joins.2', 'sh.files.3', 'py.pandas2.2', 'sql.index.2', 'py.pytest.1', 'k8s.pods.2', 'py.classes.3'];
  for (const id of list) {
    await p.evaluate((id) => { const ex = Cx.exercises[id]; Session.start([{ k: 'new', c: ex.concept, e: id, done: false }], { title: 'Preview', kind: 'free' }); }, id);
    await p.waitForSelector('#session .xcard');
    await p.waitForTimeout(500);
    await p.screenshot({ path: SH + tag + id + '.png', fullPage: false });
    await p.evaluate(() => Session.exit());
  }
  // dashboard top on this viewport
  await p.evaluate(() => App.go('today'));
  await p.screenshot({ path: SH + tag + 'today.png', fullPage: false });
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
