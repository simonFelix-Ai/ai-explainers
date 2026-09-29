// Capture the three.js scene frame by frame in headless Chromium (software WebGL).
// Usage:
//   node render.mjs --frames out_dir [--fps 30] [--start 0] [--end 45]
//   node render.mjs --still 20.5 --out frame.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return acc;
}, []));
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: CHROME,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.error('page error:', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
await page.goto(`http://127.0.0.1:${port}/web/index.html`);
await page.waitForFunction('window.ready === true', null, { timeout: 120000 });

async function grab(t) {
  const b64 = await page.evaluate((t) => {
    window.renderAt(t);
    return document.querySelector('canvas').toDataURL(window.__fmt || 'image/png', 0.95).split(',')[1];
  }, t);
  return Buffer.from(b64, 'base64');
}

if (args.still !== undefined) {
  fs.writeFileSync(args.out || 'still.png', await grab(parseFloat(args.still)));
  console.log('wrote', args.out || 'still.png');
} else {
  const fps = parseFloat(args.fps || 30), start = parseFloat(args.start || 0), end = parseFloat(args.end || 45);
  const dir = args.frames || 'frames';
  fs.mkdirSync(dir, { recursive: true });
  await page.evaluate(() => { window.__fmt = 'image/jpeg'; });
  const f0 = Math.round(start * fps), f1 = Math.round(end * fps);
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const out = path.join(dir, `f_${String(f).padStart(5, '0')}.jpg`);
    if (fs.existsSync(out) && fs.statSync(out).size > 0) continue;  // resumable
    const tmp = out + '.part';
    fs.writeFileSync(tmp, await grab(f / fps));
    fs.renameSync(tmp, out);
    if ((f - f0) % (fps * 2) === 0) {
      console.log(`t=${(f / fps).toFixed(1)}s  ${((Date.now() - t0) / 1000 / Math.max(1, f - f0 + 1)).toFixed(2)}s/frame`);
    }
  }
}
await browser.close();
server.close();
