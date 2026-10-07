#!/usr/bin/env node
// Render google-ads-ecommerce-explainer.html to a 16:9 MP4, frame by frame in headless Chromium.
//
//   node scripts/render-video.js                       -> renders/google-ads-explainer-1080p-silent.mp4
//   scripts/mix-audio.sh                               -> adds voice-over + music -> renders/google-ads-explainer-1080p.mp4
//   node scripts/render-video.js --width 3840 --height 2160 --out renders/explainer-4k.mp4
//   node scripts/render-video.js --stills 3,9.5,16     -> PNG stills at those video times (seconds)
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
const page_url = 'file://' + path.join(root, 'google-ads-ecommerce-explainer.html') + '?render';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto(page_url, { waitUntil: 'networkidle' });
  // fonts load lazily per weight; force them all in before the first frame
  await page.evaluate(() => Promise.all([
    '400 1em Geist', '500 1em Geist', '600 1em Geist', '400 1em "Geist Mono"', '500 1em "Geist Mono"',
    '400 1em "Instrument Serif"', 'italic 400 1em "Instrument Serif"',
  ].map(f => document.fonts.load(f))).then(() => document.fonts.ready));
  const duration = await page.evaluate(() => window.__duration);

  if (STILLS) {
    fs.mkdirSync(path.join(root, 'renders/stills'), { recursive: true });
    for (const s of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), s);
      const f = path.join(root, `renders/stills/still-${String(s).replace('.', '_')}.png`);
      await page.screenshot({ path: f });
      console.log(f);
    }
    return browser.close();
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.__seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 5) === 0) console.log(`frame ${f}/${frames}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));
  await browser.close();
  console.log(`wrote ${OUT}  (${frames} frames, ${duration}s @ ${FPS}fps, ${W}x${H})`);
})();
