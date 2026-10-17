"""Build the collage cutouts: halftone print look + rough white scissor edge, as transparent PNGs.

    python -I collage/make_assets.py <source-photo-dir>

Sources (see CREDITS.md): scikit-image sample photos — eagle (CC0), rocket launch (public domain), Hubble Ultra Deep
Field (NASA, public domain), brick and gravel textures (CC0). Everything else (house head shapes, door frames, flowers,
hands) is drawn here or in the page.
"""
import sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent / 'assets'
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)

PAPER = np.array([243, 236, 220]) / 255      # newsprint white of the cut paper
INK = np.array([22, 20, 18]) / 255
RED = np.array([200, 38, 30]) / 255


def lum(img):
    a = np.asarray(img.convert('RGB'), dtype=np.float32) / 255
    return a @ np.array([.299, .587, .114])


def halftone(L, cell=7.0, angle=45, gain=1.15, blur=1.2):
    """Amplitude-modulated dot screen: returns ink coverage 0..1 (antialiased)."""
    L = ndi.gaussian_filter(L, blur)
    h, w = L.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angle)
    u = (x * np.cos(a) + y * np.sin(a)) / cell
    v = (-x * np.sin(a) + y * np.cos(a)) / cell
    du, dv = u - np.round(u), v - np.round(v)
    d = np.sqrt(du * du + dv * dv) * cell                      # distance to the cell centre in px
    r = cell * .5 * np.sqrt(np.clip(1 - L, 0, 1)) * gain * 1.25  # dot radius from darkness
    return np.clip(r - d + .5, 0, 1)


def rough(mask, amp=3.0, freq=0.035, seed=1):
    """Perturb a mask's edge so it looks scissor-cut (straight-ish runs with small wobbles)."""
    r = np.random.default_rng(seed)
    h, w = mask.shape
    dist = ndi.distance_transform_edt(mask) - ndi.distance_transform_edt(~mask)
    n = ndi.gaussian_filter(r.standard_normal((h, w)), 1 / freq)
    n = n / (np.abs(n).max() + 1e-6)
    return dist + n * amp > 0


def finish(rgb, alpha, edge=7, name='x', shadowless=True):
    """Add the white paper edge around the cut (alpha dilated by `edge` px, roughened) and save."""
    cut = alpha > .5
    outer = ndi.binary_dilation(cut, iterations=edge)
    outer = rough(outer, amp=edge * .45, seed=hash(name) % 999)
    h, w = cut.shape
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = PAPER
    out[..., 3] = outer
    a = alpha[..., None]
    out[..., :3] = out[..., :3] * (1 - a) + rgb * a
    img = Image.fromarray((out * 255).astype(np.uint8), 'RGBA')
    bb = img.getbbox(); img = img.crop(bb)
    img.save(OUT / f'{name}.png', optimize=True)
    print('wrote', name, img.size)


def ink_on_paper(cov, ink=INK, paper=PAPER, tint=None):
    rgb = np.ones(cov.shape + (3,)) * (tint if tint is not None else paper)
    return rgb * (1 - cov[..., None]) + ink * cov[..., None]


def pad(img, p):
    w, h = img.size
    c = Image.new(img.mode, (w + 2 * p, h + 2 * p), (0, 0, 0, 0) if img.mode == 'RGBA' else 0)
    c.paste(img, (p, p)); return c


def cutout(path, crop=None, scale=1.0, name='x', cell=6.5, edge=8, tint=None, ink=INK, contrast=1.15):
    from rembg import remove
    im = Image.open(path).convert('RGB')
    if crop: im = im.crop(crop)
    if scale != 1: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    rgba = remove(im)
    rgba = pad(rgba, edge * 3)
    a = np.asarray(rgba, np.float32)[..., 3] / 255
    a = ndi.binary_opening(a > .5, iterations=2).astype(np.float32)
    a = ndi.binary_fill_holes(a > .5).astype(np.float32)
    lab, n = ndi.label(a > .5)
    if n > 1:                                                 # keep the biggest piece only
        sizes = ndi.sum(a > .5, lab, range(1, n + 1)); a = (lab == (np.argmax(sizes) + 1)).astype(np.float32)
    L = lum(rgba)
    L = np.clip((L - .5) * contrast + .55, 0, 1)
    cov = halftone(L, cell=cell)
    rgb = ink_on_paper(cov, ink=ink, tint=tint)
    finish(rgb, a, edge=edge, name=name)


def shape_piece(size, draw_fn, texture=None, cell=7, ink=INK, tint=None, edge=8, name='x', tex_contrast=1.0, tex_bias=0.0):
    """A drawn silhouette filled with a halftoned photo texture."""
    w, h = size
    m = Image.new('L', (w, h), 0); draw_fn(ImageDraw.Draw(m)); a = np.asarray(m, np.float32) / 255
    a = np.pad(a, edge * 3)
    if texture is not None:
        t = Image.open(texture).convert('L').resize((a.shape[1], a.shape[0]), Image.LANCZOS)
        L = np.clip((np.asarray(t, np.float32) / 255 - .5) * tex_contrast + .5 + tex_bias, 0, 1)
    else:
        L = np.ones_like(a) * .85
    cov = halftone(L, cell=cell)
    rgb = ink_on_paper(cov, ink=ink, tint=tint)
    finish(rgb, a, edge=edge, name=name)


# ---------- photo cutouts ----------
cutout(SRC / 'eagle.png', crop=(80, 300, 1450, 1500), scale=.55, name='eagle', cell=5.5, edge=7)
cutout(SRC / 'rocket.png', crop=(268, 70, 372, 427), scale=2.2, name='rocket', cell=4.5, edge=6, contrast=1.3)

# deep space: keep the colour (it's the reveal), add a fine colour halftone so it reads printed
sp = Image.open(SRC / 'hubble_deep_field.png').convert('RGB').resize((1000, 872))
arr = np.asarray(sp, np.float32) / 255
boost = np.clip(arr * 1.35, 0, 1)
cov = halftone(1 - lum(sp) * 1.6, cell=4, angle=15, gain=.9)
spc = boost * (1 - .25 * cov[..., None]) + boost * .25 * cov[..., None] * 1.8
Image.fromarray((np.clip(spc, 0, 1) * 255).astype(np.uint8)).save(OUT / 'space.jpg', quality=92)
print('wrote space')

# ---------- the house head (cut from the brick + gravel photos) ----------
BRICK_RED = np.array([196, 66, 48]) / 255
PAPER_PINK = np.array([246, 226, 210]) / 255
shape_piece((640, 470), lambda d: d.rectangle([0, 0, 640, 470], fill=255), texture=SRC / 'brick.png', cell=6,
            ink=BRICK_RED * .55, tint=np.array([226, 120, 92]) / 255, edge=9, name='walls', tex_contrast=1.6)
shape_piece((800, 330), lambda d: d.polygon([(0, 330), (400, 0), (800, 330)], fill=255), texture=SRC / 'gravel.png', cell=6,
            ink=INK, tint=np.array([70, 74, 82]) / 255, edge=9, name='roof', tex_contrast=1.8, tex_bias=-.1)
shape_piece((110, 210), lambda d: d.rectangle([0, 0, 110, 210], fill=255), texture=SRC / 'brick.png', cell=5,
            ink=BRICK_RED * .5, tint=np.array([214, 104, 80]) / 255, edge=7, name='chimney', tex_contrast=1.6)


def window(d):
    d.rectangle([0, 0, 150, 170], fill=255)
shape_piece((150, 170), window, cell=5, ink=INK, tint=np.array([250, 244, 228]) / 255, edge=7, name='window')

# door = mouth: three replacement frames (closed / ajar / wide open)
def door_closed(d): d.rectangle([0, 0, 160, 230], fill=255)
shape_piece((160, 230), door_closed, texture=SRC / 'grass.png', cell=5, ink=np.array([20, 40, 70]) / 255,
            tint=np.array([40, 92, 160]) / 255, edge=7, name='door0', tex_contrast=.6)
for k, (wd, name) in enumerate([(110, 'door1'), (40, 'door2')]):
    def dd(d, wd=wd):
        d.rectangle([0, 0, 160, 230], fill=255)
    m = Image.new('RGB', (160, 230), (18, 14, 14))
    dr = ImageDraw.Draw(m)
    tongue_h = 46 if k == 0 else 80
    dr.ellipse([30, 230 - tongue_h, 130, 230 + tongue_h], fill=(214, 70, 82))     # tongue
    dr.rectangle([0, 0, wd, 230], fill=(40, 92, 160))                              # door leaf swinging in
    dr.line([(wd, 0), (wd, 230)], fill=(250, 244, 228), width=5)
    rgb = np.asarray(m, np.float32) / 255
    a = np.ones((230, 160), np.float32)
    finish(np.pad(rgb, ((21, 21), (21, 21), (0, 0)), constant_values=0), np.pad(a, 21), edge=7, name=name)
print('done')
