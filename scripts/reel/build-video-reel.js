#!/usr/bin/env node
// Turn a finished 16:9 explainer into a 9:16 reel (1080×1920) with a step tracker, big titles and word-by-word captions.
//
//   node scripts/reel/build-video-reel.js --config scripts/reel/booked-jobs-reel.json
//
// The config names the silent render (frames), the final MP4 (its soundtrack is reused as-is), the caption timings
// written by make_voiceover.py, the tracker chips and one title per segment. See booked-jobs-reel.json.
const path = require('path');
const fs = require('fs');
const { spawn, execFileSync } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.execPath, '../../lib/node_modules/playwright'))); }

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > -1 ? process.argv[i + 1] : d; };
const root = path.join(__dirname, '../..');
const cfg = JSON.parse(fs.readFileSync(path.resolve(root, arg('config')), 'utf8'));
const work = path.join(root, 'renders/reel', cfg.name);
const frameDir = path.join(work, 'frames');
const FPS = 30, STILLS = arg('stills');

(async () => {
  // 1. frames from the silent 16:9 render
  if (!fs.existsSync(path.join(frameDir, '0001.jpg'))) {
    fs.mkdirSync(frameDir, { recursive: true });
    execFileSync('ffmpeg', ['-v', 'error', '-i', path.resolve(root, cfg.video), '-vf', 'scale=1600:-1', '-q:v', '3', path.join(frameDir, '%04d.jpg')], { stdio: 'inherit' });
  }
  const frames = fs.readdirSync(frameDir).filter(f => f.endsWith('.jpg')).length;
  // 2. data file for the compositor
  const captions = JSON.parse(fs.readFileSync(path.resolve(root, cfg.captions), 'utf8'));
  const data = { duration: cfg.duration, bar: cfg.bar, chips: cfg.chips, segments: cfg.segments, captions, frames,
    frameDir: path.relative(__dirname, frameDir) };
  fs.writeFileSync(path.join(work, 'reel-data.js'), 'window.REEL = ' + JSON.stringify(data) + ';\n');

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto('file://' + path.join(__dirname, 'reel-video.html') + '?data=' + encodeURIComponent(path.relative(__dirname, path.join(work, 'reel-data.js'))), { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready);
  await page.evaluate(() => Promise.all(['600 1em Unbounded', '800 1em Figtree', '400 1em "Martian Mono"'].map(f => document.fonts.load(f))).then(() => document.fonts.ready));

  if (STILLS) {
    for (const s of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), s);
      await page.screenshot({ path: path.join(work, `still-${String(s).replace('.', '_')}.png`) });
    }
    return browser.close();
  }
  // 3. render, then 4. reuse the explainer's finished soundtrack
  const silent = path.join(work, 'reel-silent.mp4');
  const total = Math.round(cfg.duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high', '-level:v', '4.0', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < total; f++) {
    await page.evaluate(t => window.__seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 10) === 0) console.log(`frame ${f}/${total}`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
  await browser.close();
  const out = path.resolve(root, cfg.out);
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', path.resolve(root, cfg.audioFrom), '-map', '0:v', '-map', '1:a', '-c', 'copy', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
  console.log(`wrote ${cfg.out}`);
})();
