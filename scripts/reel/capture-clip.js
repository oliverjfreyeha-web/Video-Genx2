#!/usr/bin/env node
// Capture a short 16:9 clip of one version of the explainer as numbered JPEG frames (30 fps).
//
//   seek mode    — pages with render mode (window.__seek):  --mode seek --start <video seconds>
//   anim mode    — early versions without it: jump to a chapter, pause the page, then set every CSS
//                  animation's currentTime for each frame:  --mode anim --scene <index> [--lead 0.3]
//
//   node scripts/reel/capture-clip.js --html renders/reel/versions/v1.html --mode anim --scene 3 --dur 4.5 --out renders/reel/clips/v1
//   node scripts/reel/capture-clip.js --html google-ads-ecommerce-explainer.html --mode seek --start 19.8 --dur 4.5 --palette ocean --out ...
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.execPath, '../../lib/node_modules/playwright'))); }

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > -1 ? process.argv[i + 1] : d; };
const root = path.join(__dirname, '../..');
const HTML = path.resolve(root, arg('html'));
const MODE = arg('mode', 'seek'), DUR = +arg('dur', 4.5), FPS = 30;
const OUT = path.resolve(root, arg('out'));
const PALETTE = arg('palette');

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const frames = Math.round(DUR * FPS);
  const save = i => path.join(OUT, String(i).padStart(4, '0') + '.jpg');

  if (MODE === 'seek') {
    const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
    page.on('pageerror', e => console.error('page error:', e.message));
    await page.goto('file://' + HTML + '?render' + (PALETTE ? '&palette=' + PALETTE : ''), { waitUntil: 'networkidle' });
    const START = +arg('start');
    // touch every scene once so lazily-loaded font weights are in before frame 0
    for (let t = 0; t < 58; t += 3) await page.evaluate(t => window.__seek(t), t);
    await page.evaluate(() => document.fonts.ready);
    for (let f = 0; f < frames; f++) {
      await page.evaluate(t => window.__seek(t), START + f / FPS);
      await page.screenshot({ path: save(f), type: 'jpeg', quality: 92 });
    }
  } else {
    const page = await browser.newPage({ viewport: { width: 1100, height: 800 }, deviceScaleFactor: 1.6 });
    page.on('pageerror', e => console.error('page error:', e.message));
    await page.goto('file://' + HTML, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    // jump to the chapter, pause the page's own clock, then position every CSS animation for each frame
    const SCENE = +arg('scene'), LEAD = +arg('lead', 0.3);
    await page.evaluate(i => document.querySelectorAll('.ticks button')[i].click(), SCENE);
    await page.evaluate(() => document.getElementById('play').click());
    const stage = page.locator('#stage');
    for (let f = 0; f < frames; f++) {
      await page.evaluate(ms => document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms; }), (LEAD + f / FPS) * 1000);
      await stage.screenshot({ path: save(f), type: 'jpeg', quality: 92 });
    }
  }
  await browser.close();
  console.log(`captured ${frames} frames -> ${path.relative(root, OUT)}`);
})();
