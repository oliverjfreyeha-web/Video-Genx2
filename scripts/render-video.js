#!/usr/bin/env node
// Render google-ads-ecommerce-explainer.html to a 16:9 MP4, frame by frame in headless Chromium.
//
//   node scripts/render-video.js                       -> renders/google-ads-explainer-1080p-silent.mp4
//   scripts/mix-audio.sh                               -> adds voice-over + music -> renders/google-ads-explainer-1080p.mp4
//   node scripts/render-video.js --width 3840 --height 2160 --out renders/explainer-4k.mp4
//   node scripts/render-video.js --stills 3,9.5,16     -> PNG stills at those video times (seconds)
//   add --palette midnight|ocean|berry|citrus to render or preview another colour palette
//   add --page other-explainer.html (and --out / --prefix) to render another explainer built on the same engine
//
// Requires Playwright (with a Chromium) and ffmpeg with libx264 on PATH.
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.execPath, '../../lib/node_modules/playwright'))); }

const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > -1 ? process.argv[i + 1] : def; };
const W = +arg('width', 1920), H = +arg('height', 1080), FPS = +arg('fps', 30);
const root = path.join(__dirname, '..');
const OUT = path.resolve(root, arg('out', 'renders/google-ads-explainer-1080p-silent.mp4'));
const STILLS = arg('stills');
const PALETTE = arg('palette');  // optional: prism (default), midnight, ocean, berry, citrus
const PAGE = arg('page', 'google-ads-ecommerce-explainer.html');  // any explainer page built on this engine
const STILL_PREFIX = arg('prefix', 'still');
const QUERY = arg('query');  // extra page parameters, e.g. --query aspect=16x9
// pages are served over a local HTTP server: module scripts (three.js pages) don't load from file://
const http = require('http');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.mp4': 'video/mp4', '.png': 'image/png', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const page_url = `http://127.0.0.1:${server.address().port}/${PAGE}?render` + (PALETTE ? '&palette=' + PALETTE : '') + (QUERY ? '&' + QUERY : '');
  // SwiftShader WebGL lets three.js pages render headless
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(page_url, { waitUntil: 'networkidle' });
  // fonts load lazily per weight; force every face the page declares in before the first frame
  await page.evaluate(() => Promise.all([...document.fonts].map(f => f.load().catch(() => {}))).then(() => document.fonts.ready));
  await page.waitForFunction(() => window.__duration, null, { timeout: 120000 });  // pages that build asynchronously expose it when ready
  const duration = await page.evaluate(() => window.__duration);

  if (STILLS) {
    fs.mkdirSync(path.join(root, 'renders/stills'), { recursive: true });
    for (const s of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), s);
      const f = path.join(root, `renders/stills/${STILL_PREFIX}-${PALETTE ? PALETTE + '-' : ''}${String(s).replace('.', '_')}.png`);
      await page.screenshot({ path: f });
      console.log(f);
    }
    await browser.close(); return server.close();
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-level:v', '4.0', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.__seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 5) === 0) console.log(`frame ${f}/${frames}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));
  await browser.close(); server.close();
  console.log(`wrote ${OUT}  (${frames} frames, ${duration}s @ ${FPS}fps, ${W}x${H})`);
})();
