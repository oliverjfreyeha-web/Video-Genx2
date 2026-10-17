# Credits — "Mind the Leads" (10 s collage spot for Elevate Home Ads)

All photos come from the scikit-image sample-data catalogue (fetched with `skimage.data`); licences as stated there.
They were cut out with rembg, halftoned and given a white scissor edge by `collage/make_assets.py`.

| Asset | Source | Licence |
|---|---|---|
| Eagle cutout (`assets/eagle.png`) | `skimage.data.eagle` | CC0 |
| Rocket cutout (`assets/rocket.png`) | `skimage.data.rocket` (launch photo) | Public domain |
| Deep space (`assets/space.jpg`) | `skimage.data.hubble_deep_field` — Hubble Ultra Deep Field, NASA | Public domain (NASA) |
| House walls + chimney (`walls.png`, `chimney.png`) | `skimage.data.brick` texture | CC0 |
| Roof (`roof.png`) | `skimage.data.gravel` texture | CC0 |
| Door-mouth frames (`door0–2.png`) | `skimage.data.grass` texture (door 0) + drawn | CC0 / original |

Everything else (the house-head character, hands, scissors, flowers, planets, stars, tickets, POP burst, newsprint
ground, typography layout) is original artwork drawn in `collage/collage.html` and `collage/make_assets.py`.
The house-head character is an original design; no existing characters, brands or trademarks are used.
"Elevate Home Ads" is the client's own business name.

## Fonts (Google Fonts, SIL Open Font License 1.1)
- Anton — Vernon Adams
- Playfair Display — Claus Eggers Sørensen
- Special Elite — Astigmatic

## Sound
All music and sound design is synthesised in `collage/make_audio.py` (numpy): boom-bap drums, Rhodes-style FM chords,
bass, vinyl crackle, slaps, paper rustles, scissor snips, the comic pop, whooshes.
Voice: Kokoro-82M via kokoro-onnx (Apache-2.0), voices `am_michael` and `af_heart`.

## Tools
rembg (MIT), scikit-image (BSD-3), NumPy/SciPy (BSD), Pillow (HPND), Playwright (Apache-2.0), FFmpeg (LGPL/GPL).
