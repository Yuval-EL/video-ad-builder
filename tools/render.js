// Renders one deliverable of an ad, in one format, to a silent MP4. Frame by frame, so timing is exact.
// Usage: node tools/render.js <player.html> <out.mp4> <deliverable> <16x9|9x16|1x1> [fps]

const { chromium } = require('playwright');
const { spawn } = require('child_process');
const { pathToFileURL } = require('url');
const path = require('path');
const fs = require('fs');

if (process.env.LOCALAPPDATA) {
  process.env.PATH = path.join(process.env.LOCALAPPDATA, 'Microsoft', 'WinGet', 'Links') + path.delimiter + process.env.PATH;
}
const DIMS = { '16x9': [1920, 1080], '9x16': [1080, 1920], '1x1': [1080, 1080] };

async function main() {
  const [,, html, outPath, deliverable, fmt = '16x9', fpsArg] = process.argv;
  if (!html || !outPath || !deliverable || !DIMS[fmt]) {
    console.error('usage: node tools/render.js <player.html> <out.mp4> <deliverable> <16x9|9x16|1x1> [fps]'); process.exit(1);
  }
  const [width, height] = DIMS[fmt];
  const fps = Number(fpsArg || 30);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.resolve(html)).href + `#d=${encodeURIComponent(deliverable)}&fmt=${fmt}&render`);
  await page.waitForFunction(() => typeof window.seek === 'function');
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.SCHEDULE.duration);
  const frames = Math.round(duration * fps);

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'png', '-r', String(fps), '-i', '-',
    '-c:v', 'libx264', '-profile:v', 'high', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(fps), '-movflags', '+faststart', outPath],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const started = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate((t) => window.seek(t), i / fps);
    const png = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise((resolve, reject) => ff.on('close', (c) => (c === 0 ? resolve() : reject(new Error('ffmpeg exit ' + c)))));
  await browser.close();
  console.log(`rendered ${path.basename(outPath)} | ${deliverable} ${fmt} | ${duration}s at ${fps} fps | ${(fs.statSync(outPath).size / 1e6).toFixed(1)} MB | ${Math.round((Date.now() - started) / 1000)}s`);
}
main().catch((e) => { console.error(e); process.exit(1); });
