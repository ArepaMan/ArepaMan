const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const SH = '/tmp/claude-0/-home-user-ArepaMan/8fc33d1f-50c8-5d6b-b4b1-76904f7b8846/scratchpad/shots/';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await b.newContext({ viewport: { width: 1200, height: 900 } });
  const p = await ctx.newPage();
  const errs = [];
  p.on('console', (m) => { if (['error', 'warning'].includes(m.type())) errs.push(m.type() + ': ' + m.text()); });
  p.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.waitForSelector('.todaycard', { timeout: 15000 }).catch(() => console.log('no todaycard'));
  await p.screenshot({ path: SH + 'dash-desktop.png', fullPage: true });
  console.log('errors:', JSON.stringify(errs, null, 1));
  await b.close();
})();
