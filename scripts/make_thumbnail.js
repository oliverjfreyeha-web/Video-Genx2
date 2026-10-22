// Thumbnail / cover from ComfyUI artwork: real-type title over the image (the model never draws text).
//   node scripts/make_thumbnail.js --art assets/comfy/thumbnail/x.png --title "Where to source inventory" \
//        --kicker "Module 1 · Lesson 2" --aspect 16x9 --out renders/ascentra/reselling/m01-l02-thumb.png
// 16x9 -> 1280x720 (course player / YouTube), 9x16 -> 1080x1920 (reel cover). --accent sets the kicker colour.
const path = require('path');
const fs = require('fs');

let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.execPath, '../../lib/node_modules/playwright'))); }

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const need = ['art', 'title', 'out'].filter(k => !args[k]);
if (need.length) { console.error(`make_thumbnail: missing --${need.join(', --')}`); process.exit(2); }
const SIZES = { '16x9': [1280, 720], '9x16': [1080, 1920] };
const aspect = args.aspect || '16x9';
if (!SIZES[aspect]) { console.error('make_thumbnail: --aspect is 16x9 or 9x16'); process.exit(2); }
const [w, h] = SIZES[aspect];
const ROOT = path.resolve(__dirname, '..');
const artPath = path.resolve(args.art);
if (!fs.existsSync(artPath)) { console.error(`make_thumbnail: no such image ${args.art}`); process.exit(2); }
const mime = artPath.endsWith('.jpg') || artPath.endsWith('.jpeg') ? 'image/jpeg' : 'image/png';
const art = `data:${mime};base64,${fs.readFileSync(artPath).toString('base64')}`;

(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto('file://' + path.join(ROOT, 'comfy', 'thumbnail.html'), { waitUntil: 'load', timeout: 20000 }).catch(() => {});
    const size = await page.evaluate(o => window.compose(o),
      { art, title: args.title, kicker: args.kicker || '', wide: aspect === '16x9', w, h, accent: args.accent });
    const out = path.resolve(args.out);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await page.screenshot({ path: out, type: out.endsWith('.jpg') ? 'jpeg' : 'png', quality: out.endsWith('.jpg') ? 90 : undefined });
    console.log(`wrote ${path.relative(process.cwd(), out)} (${w}x${h}, title ${size}px)`);
  } finally { await browser.close(); }
})().catch(e => { console.error('make_thumbnail:', e.message); process.exit(1); });
