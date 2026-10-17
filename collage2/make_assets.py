"""Cutouts for collage spot #2 ("First Reply Wins"): the cat-headed homeowner split into puppet pieces
(lid / face / jaw), plus single coins. Same print treatment as collage/make_assets.py: halftone + rough white edge.

    python -I collage2/make_assets.py <source-photo-dir>

Sources (see CREDITS.md): skimage.data.chelsea (CC0), skimage.data.coins (Brooklyn Museum, no known restrictions).
"""
import sys, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent / 'assets'
OUT.mkdir(exist_ok=True)
PAPER = np.array([243, 236, 220]) / 255
INK = np.array([40, 26, 18]) / 255          # warm sepia ink for the portrait


def lum(a): return a[..., :3] @ np.array([.299, .587, .114])


def halftone(L, cell=6.0, angle=45, gain=1.15, blur=1.0):
    L = ndi.gaussian_filter(L, blur); h, w = L.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32); a = np.deg2rad(angle)
    u = (x * np.cos(a) + y * np.sin(a)) / cell; v = (-x * np.sin(a) + y * np.cos(a)) / cell
    d = np.sqrt((u - np.round(u)) ** 2 + (v - np.round(v)) ** 2) * cell
    r = cell * .5 * np.sqrt(np.clip(1 - L, 0, 1)) * gain * 1.25
    return np.clip(r - d + .5, 0, 1)


def rough(mask, amp=3.0, freq=.035, seed=1):
    r = np.random.default_rng(seed)
    dist = ndi.distance_transform_edt(mask) - ndi.distance_transform_edt(~mask)
    n = ndi.gaussian_filter(r.standard_normal(mask.shape), 1 / freq); n /= np.abs(n).max() + 1e-6
    return dist + n * amp > 0


def save(rgb, alpha, edge, name, crop_box=None):
    cut = alpha > .5
    outer = rough(ndi.binary_dilation(cut, iterations=edge), amp=edge * .45, seed=sum(map(ord, name)))
    h, w = cut.shape
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = PAPER; out[..., 3] = outer
    a = alpha[..., None]; out[..., :3] = out[..., :3] * (1 - a) + rgb * a
    img = Image.fromarray((out * 255).astype(np.uint8), 'RGBA')
    if crop_box: img = img.crop(crop_box)
    else: img = img.crop(img.getbbox())
    img.save(OUT / f'{name}.png', optimize=True); print('wrote', name, img.size)
    return img


# ---------- the cat-headed homeowner: one rembg cut, split into lid / face / jaw on rough scissor lines ----------
from rembg import remove
cat = Image.open(SRC / 'chelsea.png').convert('RGB').crop((0, 0, 420, 300))
cat = cat.resize((cat.width * 2, cat.height * 2), Image.LANCZOS)
rgba = np.asarray(remove(cat), np.float32) / 255
P = 40
rgba = np.pad(rgba, ((P, P), (P, P), (0, 0)))
alpha = ndi.binary_fill_holes(ndi.binary_opening(rgba[..., 3] > .5, iterations=3)).astype(np.float32)
lab, n = ndi.label(alpha > .5)
if n > 1: alpha = (lab == np.argmax(ndi.sum(alpha > .5, lab, range(1, n + 1))) + 1).astype(np.float32)
L = np.clip((lum(rgba) - .5) * 1.25 + .56, 0, 1)
cov = halftone(L, cell=6.5)
tint = np.array([238, 214, 178]) / 255
rgb = np.ones(cov.shape + (3,)) * tint * (1 - cov[..., None]) + INK * cov[..., None]
H, Wd = alpha.shape
yy, xx = np.mgrid[0:H, 0:Wd]
lid_line = P + 175 + (xx - P) * .06 + 6 * np.sin(xx / 23.0)          # forehead cut (slightly tilted, wobbly)
jaw_line = P + 505 + 5 * np.sin(xx / 17.0)                            # below the nose: the jaw flaps
pieces = {'cat_lid': yy < lid_line, 'cat_face': (yy >= lid_line) & (yy < jaw_line), 'cat_jaw': yy >= jaw_line}
H_box = (0, 0, Wd, H)                                                  # keep a shared canvas so the pieces re-assemble 1:1
for name, m in pieces.items():
    save(rgb, alpha * m, 7, name, crop_box=H_box)
# mouth interior shown behind the jaw when it opens
mouth = np.zeros((H, Wd)); mouth[(yy > jaw_line - 40) & (yy < jaw_line + 25) & ((xx - P - 520) ** 2 / 120 ** 2 + (yy - jaw_line) ** 2 / 50 ** 2 < 1)] = 1
save(np.ones((H, Wd, 3)) * np.array([70, 14, 20]) / 255, mouth, 4, 'cat_mouth', crop_box=H_box)

# ---------- coins (Brooklyn Museum photo): pick six and cut each on its rim ----------
co = np.asarray(Image.open(SRC / 'coins.png').convert('L'), np.float32) / 255
mask = ndi.binary_fill_holes(ndi.binary_opening(co > .45, iterations=2))
lab, n = ndi.label(mask)
objs = ndi.find_objects(lab)
sizes = ndi.sum(mask, lab, range(1, n + 1))
keep = [i for i in np.argsort(-sizes)[:10]][:6]
for k, i in enumerate(keep):
    sl = objs[i]; y0, y1, x0, x1 = sl[0].start - 6, sl[0].stop + 6, sl[1].start - 6, sl[1].stop + 6
    crop = co[max(0, y0):y1, max(0, x0):x1]; m = (lab[max(0, y0):y1, max(0, x0):x1] == i + 1).astype(np.float32)
    big = lambda a: np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((a.shape[1] * 3, a.shape[0] * 3), Image.LANCZOS), np.float32) / 255
    cb, mb = big(crop), big(m) > .5
    cb = np.pad(cb, 30, constant_values=.5); mb = np.pad(mb, 30)
    cv = halftone(np.clip((cb - .5) * 1.4 + .5, 0, 1), cell=4.5, angle=30)
    gold = np.array([226, 186, 92]) / 255
    rgbc = gold * (1 - cv[..., None]) + np.array([60, 40, 10]) / 255 * cv[..., None]
    save(rgbc, mb.astype(np.float32), 6, f'coin{k}')
print('done')
