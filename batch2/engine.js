// Shared engine for the batch-2 ads. A page calls Engine({ dur, fonts, seek(t), captions }) after defining its stage.
// - 9:16 by default (1080×1920); ?aspect=16x9 → 1920×1080. The page reads E.W / E.H / E.WIDE to lay itself out.
// - One clock: seek(t) must set every visual from t alone. ?render exposes window.__seek / __duration for capture.
// - Captions: word-by-word chunks from the <script id="captions"> JSON (t0/t1/text), drawn into #caps .capbox.
(function () {
  const Q = new URLSearchParams(location.search);
  const E = window.E = {};
  E.RENDER = Q.has('render'); E.WIDE = Q.get('aspect') === '16x9';
  E.W = E.WIDE ? 1920 : 1080; E.H = E.WIDE ? 1080 : 1920;
  if (E.WIDE) document.documentElement.classList.add('wide');
  E.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  E.prog = (t, a, d) => E.clamp((t - a) / d);
  E.eOut = x => 1 - Math.pow(1 - E.clamp(x), 3);                                        // entrances
  E.eIO = x => { x = E.clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };   // moves
  E.back = (x, c = 1.7) => { x = E.clamp(x); return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  E.lerp = (a, b, p) => a + (b - a) * p;
  E.hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  E.step = (t, fps) => Math.floor(t * fps + 1e-6) / fps;
  E.$ = id => document.getElementById(id);
  // entrance helper: fade + rise + scale from .94, never from 0
  E.show = (el, p, dy = 24, s0 = .94) => { p = E.clamp(p); el.style.opacity = p; el.style.visibility = p > 0 ? 'visible' : 'hidden';
    el.style.transform = `translateY(${(1 - E.eOut(p)) * dy}px) scale(${s0 + (1 - s0) * E.eOut(p)})`; };

  window.Engine = function (cfg) {
    const stage = E.$('stage'), frame = E.$('frame');
    stage.style.width = E.W + 'px'; stage.style.height = E.H + 'px';
    const fit = () => { stage.style.transform = `scale(${frame.clientWidth / E.W})`; };
    new ResizeObserver(fit).observe(frame); fit();
    // captions
    const capEl = E.$('caps'), box = capEl && capEl.querySelector('.capbox');
    const chunks = [];
    if (box && E.$('captions')) JSON.parse(E.$('captions').textContent).forEach(c => {
      const ws = c.text.split(' '), tot = c.text.length; let acc = 0;
      const tw = ws.map(w => { const t = c.t0 + acc / tot * (c.t1 - c.t0); acc += w.length + 1; return { w, t }; });
      const per = cfg.capWords || 4;
      for (let i = 0; i < tw.length; i += per) chunks.push({ ws: tw.slice(i, i + per), end: i + per < tw.length ? tw[i + per].t : c.t1 + .3 });
    });
    let lastK = -2;
    const captions = t => {
      if (!box) return;
      const k = chunks.findIndex(ch => t >= ch.ws[0].t - .05 && t < ch.end);
      if (k !== lastK) { box.innerHTML = k < 0 ? '' : chunks[k].ws.map(x => `<span>${x.w}</span>`).join(' '); lastK = k; }
      capEl.style.opacity = k < 0 || (cfg.capsOff && cfg.capsOff(t)) ? 0 : 1;
      if (k >= 0) [...box.children].forEach((s, j) => { const w = chunks[k].ws[j], nx = chunks[k].ws[j + 1];
        s.className = t >= w.t ? (nx && t >= nx.t ? 'on' : 'now') : ''; });
    };
    const seek = t => { t = E.clamp(t, 0, cfg.dur - 1e-4); cfg.seek(t); captions(t); };
    // player
    let T = 0, playing = false, last = 0;
    const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    const ui = () => { if (E.$('fill')) E.$('fill').style.transform = `scaleX(${T / cfg.dur})`; if (E.$('time')) E.$('time').textContent = `${fmt(T)} / ${fmt(cfg.dur)}`; };
    const tick = now => { if (!playing) return; T += (now - last) / 1000; last = now; if (T >= cfg.dur) { T = cfg.dur; playing = false; E.$('play').textContent = '▶'; } seek(T); ui(); if (playing) requestAnimationFrame(tick); };
    if (E.$('play')) E.$('play').onclick = () => { playing = !playing; E.$('play').textContent = playing ? '❚❚' : '▶'; if (T >= cfg.dur) T = 0; last = performance.now(); if (playing) requestAnimationFrame(tick); };
    if (E.$('trk')) E.$('trk').onclick = e => { const r = e.currentTarget.getBoundingClientRect(); T = E.clamp((e.clientX - r.left) / r.width) * cfg.dur; seek(T); ui(); };
    document.addEventListener('keydown', e => { if (e.code === 'Space' && E.$('play')) { e.preventDefault(); E.$('play').click(); } });
    (async () => {
      await Promise.all((cfg.fonts || []).map(f => document.fonts.load(f)));
      await document.fonts.ready;
      await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
      seek(E.RENDER ? 0 : (cfg.preview || 0)); ui();
      if (E.RENDER) { document.body.classList.add('render'); window.__duration = cfg.dur; window.__seek = t => seek(t); }
    })();
  };
})();
