const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await (await b.newContext({ viewport: { width: 900, height: 900 } })).newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8200/test.html');
  await p.waitForFunction("typeof Cx !== 'undefined' && Cx.loaded");
  const r = await p.evaluate(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    Engine.py.p = Promise.reject(new Error('blocked by CSP')); Engine.py.p.catch(() => {}); Engine.py.state = 'failed'; Engine.py.err = 'blocked by CSP';
    let done = null; const host = document.createElement('div'); document.body.appendChild(host);
    const card = renderExercise(Cx.exercises['py.vars.2'], { mode: 'free', onDone: (c) => { done = c; } }); host.appendChild(card);
    card.querySelector('.CodeMirror').CodeMirror.setValue('tickets_open = 12');
    Array.from(card.querySelectorAll('.btn')).find((x) => x.textContent.trim() === 'Check').click();
    await sleep(300);
    const selfPanel = card.innerText.includes('Self-check') && card.innerText.includes('Did your answer match');
    Array.from(card.querySelectorAll('.btn')).find((x) => /Yes, I got it/.test(x.textContent)).click();
    await sleep(300);
    Array.from(card.querySelectorAll('.cont .btn')).find((x) => /Continue|Finish/.test(x.textContent)).click();
    await sleep(100);
    return { selfPanel, done };
  });
  console.log('fallback:', JSON.stringify(r), 'errors:', JSON.stringify(errs));
  await b.close();
})();
