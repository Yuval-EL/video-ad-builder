// Captures review stills for one deliverable in one format.
// Usage: node tools/stills.js <player.html> <outDir> <deliverable> <16x9|9x16|1x1> [auto | t1,t2,...]
// "auto" takes one still near the end of every scene, when all its elements have landed.

const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path'); const fs = require('fs');
const DIMS = { '16x9': [1920, 1080], '9x16': [1080, 1920], '1x1': [1080, 1080] };

(async () => {
  const [,, html, outDir, deliverable, fmt = '16x9', times = 'auto'] = process.argv;
  fs.mkdirSync(outDir, { recursive: true });
  const [width, height] = DIMS[fmt];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width, height } });
  const errors = []; p.on('pageerror', (e) => errors.push(e.message));
  await p.goto(pathToFileURL(path.resolve(html)).href + `#d=${encodeURIComponent(deliverable)}&fmt=${fmt}&render`);
  await p.waitForFunction(() => typeof window.seek === 'function', null, { timeout: 15000 }).catch(() => {});
  if (errors.length) { console.error('page errors:', errors); process.exit(1); }
  await p.evaluate(() => document.fonts.ready);
  const S = await p.evaluate(() => window.SCHEDULE);
  const list = times === 'auto'
    ? S.scenes.map((s, i) => ({ id: s.id, t: (i < S.scenes.length - 1 ? S.scenes[i + 1].t : S.duration) - 0.25 }))
    : times.split(',').map(Number).map((t) => ({ id: 't' + t.toFixed(1), t }));
  let n = 0;
  for (const { id, t } of list) {
    await p.evaluate((t) => window.seek(t), t);
    await p.screenshot({ path: path.join(outDir, `${deliverable}-${fmt}-${String(++n).padStart(2, '0')}-${id}.jpg`), type: 'jpeg', quality: 80 });
  }
  // Overflow check: anything inside the safe area that spills outside the frame.
  const spills = await p.evaluate(() => {
    const out = []; const W = window.DIMS[0], H = window.DIMS[1];
    document.querySelectorAll('.scene').forEach((sc) => {
      const prev = sc.style.display; sc.style.display = 'block';
      sc.querySelectorAll('.safe > *').forEach((el) => { const r = el.getBoundingClientRect(); if (r.left < -2 || r.top < -2 || r.right > W + 2 || r.bottom > H + 2) out.push(sc.dataset.sid + ': ' + el.className); });
      sc.style.display = prev;
    });
    return out;
  });
  await b.close();
  console.log(`${list.length} stills for ${deliverable} ${fmt}` + (spills.length ? ` | OVERFLOW: ${spills.join('; ')}` : ' | no overflow'));
})();
