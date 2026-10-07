#!/usr/bin/env node
// Render scripts/reel/reel.html (1080×1920) frame by frame, then mix narration + music into the final reel.
//
//   node scripts/reel/render-reel.js                 -> renders/google-ads-explainer-reel-9x16.mp4
//   node scripts/reel/render-reel.js --stills 1,5,26  -> renders/reel/stills/*.png
//
// Needs the clips (capture-clip.js), renders/reel/reel-vo.wav + reel-data.js (make_reel_audio.py)
// and renders/reel/music.wav (make_music.py --length 61.1 --outro 57.5 --out renders/reel/music.wav).
const path = require('path');
const fs = require('fs');
const { spawn, execFileSync } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.execPath, '../../lib/node_modules/playwright'))); }

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > -1 ? process.argv[i + 1] : d; };
const root = path.join(__dirname, '../..');
const FPS = 30, STILLS = arg('stills');
const SILENT = path.join(root, 'renders/reel/reel-silent.mp4');
const OUT = path.join(root, arg('out', 'renders/google-ads-explainer-reel-9x16.mp4'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto('file://' + path.join(__dirname, 'reel.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => Promise.all(['600 1em Unbounded', '700 1em Figtree', '800 1em Figtree', '600 1em Figtree', '400 1em "Martian Mono"']
    .map(f => document.fonts.load(f))).then(() => document.fonts.ready));
  const duration = await page.evaluate(() => window.__duration);

  if (STILLS) {
    const dir = path.join(root, 'renders/reel/stills'); fs.mkdirSync(dir, { recursive: true });
    for (const s of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), s);
      await page.screenshot({ path: path.join(dir, `reel-${String(s).replace('.', '_')}.png`) });
    }
    return browser.close();
  }

  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high', '-level:v', '4.0', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', SILENT],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.__seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 5) === 0) console.log(`frame ${f}/${frames}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
  await browser.close();

  // same mix as scripts/mix-audio.sh: narration up front, music ducked underneath
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', SILENT, '-i', path.join(root, 'renders/reel/reel-vo.wav'), '-i', path.join(root, 'renders/reel/music.wav'),
    '-filter_complex',
    '[1:a]aformat=sample_rates=44100:channel_layouts=stereo,highpass=f=80,volume=4.8dB,asplit=2[vo][key];' +
    '[2:a]highpass=f=35,equalizer=f=2200:width_type=o:width=1.6:g=-3,volume=-12dB[bed];' +
    '[bed][key]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=450:makeup=1[ducked];' +
    '[vo][ducked]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.89:level=false[a]',
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
  console.log(`wrote ${path.relative(root, OUT)}  (${frames} frames, ${duration}s, 1080x1920)`);
})();
