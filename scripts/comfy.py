"""ComfyUI workflows for the video pipeline: backgrounds, textures, props, thumbnails and short clips.

ComfyUI runs on the laptop (RX 7600S, 8 GB). This script builds the workflow graph for each job, sends it to
ComfyUI's API, waits, and saves the result into this repo with a provenance file next to it:

    python scripts/comfy.py background "a quiet thrift store aisle at golden hour" --style papercraft
    python scripts/comfy.py texture "kraft paper with soft folds" --style papercraft
    python scripts/comfy.py prop "a cardboard shipping box, slightly open" --style papercraft --cutout
    python scripts/comfy.py thumbnail "stacks of folded clothes on a shop table" --style papercraft --aspect 16x9
    python scripts/comfy.py clip "slow push-in across a papercraft market street" --style papercraft --frames 49
    python scripts/comfy.py check                  # is ComfyUI up, and which models are missing?
    python scripts/comfy.py models --download image --comfy-dir "C:/Users/you/Documents/ComfyUI"
    python scripts/comfy.py export                 # writes comfy/workflows/*.json (drag into ComfyUI to tweak)

Images use SDXL (CreativeML Open RAIL++-M: commercial use allowed); clips use Wan 2.1 T2V 1.3B (Apache-2.0).
Every model here allows commercial use of what it makes. Text never comes from the model: thumbnails get their
title from scripts/make_thumbnail.js, and every prompt carries a negative prompt against text, logos, brands
and real people. Write prompts as original scenes: no brand names, real people or "in the style of <artist>".

Settings: COMFYUI_URL (default http://127.0.0.1:8188) and COMFYUI_DIR (the ComfyUI folder, for `models`),
from the environment or founder-os/.env.
"""
import argparse
import hashlib
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMFY = ROOT / "comfy"
OUT = ROOT / "assets" / "comfy"
HF = "https://huggingface.co"

# file -> (ComfyUI models subfolder, download URL, licence, size in GB, set)
MODELS = {
    "sd_xl_base_1.0.safetensors": ("checkpoints", f"{HF}/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                                   "CreativeML Open RAIL++-M", 6.9, "image"),
    # the fp16-fix VAE avoids black/NaN images on AMD cards running SDXL in half precision
    "sdxl_vae_fp16_fix.safetensors": ("vae", f"{HF}/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors", "MIT", 0.33, "image"),
    "sdxl_lightning_8step_lora.safetensors": ("loras", f"{HF}/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_8step_lora.safetensors",
                                              "CreativeML Open RAIL++-M", 0.39, "image"),
    "wan2.1_t2v_1.3B_fp16.safetensors": ("diffusion_models", f"{HF}/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors",
                                         "Apache-2.0", 2.8, "clip"),
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors": ("text_encoders", f"{HF}/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                                               "Apache-2.0", 6.7, "clip"),
    "wan_2.1_vae.safetensors": ("vae", f"{HF}/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
                                "Apache-2.0", 0.25, "clip"),
}
SDXL, SDXL_VAE, LIGHTNING = "sd_xl_base_1.0.safetensors", "sdxl_vae_fp16_fix.safetensors", "sdxl_lightning_8step_lora.safetensors"
WAN, WAN_TE, WAN_VAE = "wan2.1_t2v_1.3B_fp16.safetensors", "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan_2.1_vae.safetensors"

NEGATIVE = ("text, letters, words, caption, watermark, signature, logo, brand name, trademark, label with writing, "
            "celebrity, real person, photo of a real person, deformed hands, extra fingers, blurry, lowres, jpeg artifacts")

# kind -> what the image is for. size: aspect -> (generate w, h, final w, h)
KINDS = {
    "background": {"model": "sdxl", "hint": "wide establishing shot, calm uncluttered centre, no people, no text",
                   "size": {"16x9": (1344, 768, 1920, 1080), "9x16": (768, 1344, 1080, 1920), "1x1": (1024, 1024, 1024, 1024)}},
    "texture":    {"model": "sdxl", "hint": "flat top-down material texture filling the whole frame, even soft lighting, no objects, no text",
                   "size": {"1x1": (1024, 1024, 1024, 1024), "16x9": (1344, 768, 1920, 1080)}},
    "prop":       {"model": "sdxl", "hint": "a single object, centred, whole object in view, isolated on a plain light grey background, soft contact shadow, no text",
                   "size": {"1x1": (1024, 1024, 1024, 1024), "9x16": (768, 1344, 768, 1344)}},
    "thumbnail":  {"model": "sdxl", "hint": "bold simple composition, one strong subject on the right third, clean empty space on the left for a title, no text",
                   "size": {"16x9": (1344, 768, 1280, 720), "9x16": (768, 1344, 1080, 1920)}},
    "clip":       {"model": "wan", "hint": "smooth slow camera motion, steady, coherent, no text",
                   "size": {"16x9": (832, 480, 832, 480), "9x16": (480, 832, 480, 832)}},
}
QUALITY = {  # SDXL sampler settings. draft = SDXL-Lightning 8-step LoRA (about 4x faster, ignores the negative prompt)
    "final": {"steps": 30, "cfg": 6.0, "sampler": "dpmpp_2m", "scheduler": "karras", "lora": None},
    "draft": {"steps": 8, "cfg": 1.0, "sampler": "euler", "scheduler": "sgm_uniform", "lora": LIGHTNING},
}
WAN_FPS = 16


class ComfyError(RuntimeError):
    pass


def env(key, default=""):
    """os.environ first, then founder-os/.env (FOUNDER_OS_ROOT, else the sibling checkout)."""
    if os.environ.get(key):
        return os.environ[key].strip()
    env_file = pathlib.Path(os.environ.get("FOUNDER_OS_ROOT") or ROOT.parent / "founder-os") / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            k, sep, v = line.partition("=")
            if sep and k.strip() == key and v.strip():
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return default


def styles():
    return json.loads((COMFY / "styles.json").read_text(encoding="utf-8"))


def compose_prompt(kind, prompt, style):
    st = styles()
    if style not in st:
        raise ComfyError(f"unknown style {style!r}; choose from: {', '.join(st)}")
    parts = [prompt.strip().rstrip("."), st[style]["prompt"], KINDS[kind]["hint"]]
    neg = ", ".join(x for x in (NEGATIVE, st[style].get("negative", "")) if x)
    return ", ".join(p for p in parts if p), neg


# ---------------------------------------------------------------- graphs (ComfyUI API format)
def sdxl_graph(prompt, negative, w, h, out_w, out_h, seed, quality="final", prefix="genx"):
    q = QUALITY[quality]
    g = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": SDXL}, "_meta": {"title": "SDXL base"}},
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": SDXL_VAE}, "_meta": {"title": "SDXL VAE (fp16 fix)"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}, "_meta": {"title": "Prompt"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}, "_meta": {"title": "Negative"}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "seed": seed, "steps": q["steps"], "cfg": q["cfg"], "sampler_name": q["sampler"],
            "scheduler": q["scheduler"], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["2", 0]}},
    }
    if q["lora"]:
        g["3"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": q["lora"], "strength_model": 1.0},
                  "_meta": {"title": "SDXL-Lightning 8-step"}}
        g["7"]["inputs"]["model"] = ["3", 0]
    last = ["8", 0]
    if (out_w, out_h) != (w, h):
        g["9"] = {"class_type": "ImageScale", "inputs": {"image": last, "upscale_method": "lanczos", "width": out_w, "height": out_h, "crop": "center"}}
        last = ["9", 0]
    g["10"] = {"class_type": "SaveImage", "inputs": {"images": last, "filename_prefix": prefix}}
    return g


def wan_graph(prompt, negative, w, h, frames, seed, steps=30, prefix="genx-clip"):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": WAN, "weight_dtype": "default"}, "_meta": {"title": "Wan 2.1 T2V 1.3B"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": WAN_TE, "type": "wan"}, "_meta": {"title": "umT5 text encoder"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": WAN_VAE}},
        "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}, "_meta": {"title": "Prompt"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}, "_meta": {"title": "Negative"}},
        "7": {"class_type": "EmptyHunyuanLatentVideo", "inputs": {"width": w, "height": h, "length": frames, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "seed": seed, "steps": steps, "cfg": 6.0, "sampler_name": "uni_pc", "scheduler": "simple",
            "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        # frames come back as numbered PNGs; ffmpeg turns them into the MP4 here (no video nodes needed)
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": prefix}},
    }


def models_for(graph):
    return sorted({v for n in graph.values() for k, v in n["inputs"].items()
                   if k in ("ckpt_name", "vae_name", "lora_name", "unet_name", "clip_name")})


# ---------------------------------------------------------------- client
class Client:
    def __init__(self, url=None):
        self.url = (url or env("COMFYUI_URL", "http://127.0.0.1:8188")).rstrip("/")
        host = urllib.parse.urlparse(self.url).hostname or ""
        # a local server must not go through an HTTP(S)_PROXY that may be set for the internet
        handlers = [urllib.request.ProxyHandler({})] if host in ("127.0.0.1", "localhost", "::1") else []
        self._open = urllib.request.build_opener(*handlers).open
        self.client_id = uuid.uuid4().hex

    def _req(self, path, body=None, timeout=30, raw=False):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers={"Content-Type": "application/json"},
                                     method="POST" if data else "GET")
        try:
            with self._open(req, timeout=timeout) as r:
                b = r.read()
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                j = json.loads(b)
            except ValueError:
                raise ComfyError(f"{path} returned {e.code}") from None
            raise ComfyError(_describe_error(j) or f"{path} returned {e.code}") from None
        except (urllib.error.URLError, OSError) as e:
            raise ComfyError(f"ComfyUI isn't answering at {self.url} ({getattr(e, 'reason', e)}). Start ComfyUI, "
                             "or set COMFYUI_URL (ComfyUI Desktop uses port 8000, the portable build 8188).") from None
        return b if raw else json.loads(b)

    def system(self):
        return self._req("/system_stats")

    def available(self, folder):
        """Model files ComfyUI can see in a models folder (None if this ComfyUI can't list them)."""
        try:
            return set(self._req(f"/models/{folder}"))
        except ComfyError:
            return None

    def missing(self, files):
        out = []
        for f in files:
            have = self.available(MODELS[f][0])
            if have is not None and f not in have:
                out.append(f)
        return out

    def run(self, graph, timeout):
        """Queue a graph, wait for it, and return (prompt_id, [output file refs])."""
        r = self._req("/prompt", {"prompt": graph, "client_id": self.client_id})
        if r.get("node_errors"):
            raise ComfyError(_describe_error(r))
        pid = r["prompt_id"]
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            h = self._req(f"/history/{pid}").get(pid)
            if h:
                st = h.get("status", {})
                if st.get("status_str") == "error":
                    for name, msg in st.get("messages", []):
                        if name == "execution_error":
                            raise ComfyError(f"{msg.get('node_type')} failed: {msg.get('exception_message', '').strip()}")
                    raise ComfyError("the workflow failed (see the ComfyUI console)")
                if st.get("completed", True):
                    files = [img for o in h.get("outputs", {}).values() for img in o.get("images", [])]
                    return pid, sorted(files, key=lambda f: f["filename"])
            time.sleep(1.0)
        self._req("/interrupt", {})
        raise ComfyError(f"timed out after {timeout // 60} min (interrupted it)")

    def fetch(self, ref):
        q = urllib.parse.urlencode({"filename": ref["filename"], "subfolder": ref.get("subfolder", ""), "type": ref.get("type", "output")})
        return self._req(f"/view?{q}", timeout=120, raw=True)


def _describe_error(j):
    err = j.get("error")
    lines = [err.get("message", "") if isinstance(err, dict) else str(err or "")]
    for nid, ne in (j.get("node_errors") or {}).items():
        for e in ne.get("errors", []):
            lines.append(f"node {nid} ({ne.get('class_type')}): {e.get('message')} {e.get('details', '')}".strip())
    return "; ".join(x for x in lines if x)


# ---------------------------------------------------------------- jobs
def make(kind, prompt, style, aspect, seed, quality, frames, steps, out, cutout, client, dry):
    spec = KINDS[kind]
    if aspect not in spec["size"]:
        raise ComfyError(f"{kind} supports aspect {', '.join(spec['size'])}")
    w, h, ow, oh = spec["size"][aspect]
    full, neg = compose_prompt(kind, prompt, style)
    seed = seed if seed is not None else random.randrange(2 ** 32)
    slug = "-".join("".join(c if c.isalnum() else " " for c in prompt.lower()).split()[:6]) or kind
    tag = f"{slug}-{seed}"
    if spec["model"] == "wan":
        if (frames - 1) % 4:
            raise ComfyError("--frames must be 4n+1 (e.g. 33, 49, 81)")
        graph = wan_graph(full, neg, w, h, frames, seed, steps or 30, prefix=f"genx/{kind}/{tag}")
        target = pathlib.Path(out) if out else OUT / kind / f"{tag}.mp4"
    else:
        graph = sdxl_graph(full, neg, w, h, ow, oh, seed, quality, prefix=f"genx/{kind}/{tag}")
        if steps:
            graph["7"]["inputs"]["steps"] = steps
        target = pathlib.Path(out) if out else OUT / kind / f"{tag}.png"
    if dry:
        print(json.dumps(graph, indent=1))
        return None
    if cutout:
        try:
            import rembg  # noqa: F401  (checked before the GPU time is spent)
        except ImportError:
            raise ComfyError("--cutout needs rembg: pip install rembg (into .venv-tts)") from None

    missing = client.missing(models_for(graph))
    if missing:
        sets = sorted({MODELS[m][4] for m in missing})
        raise ComfyError(f"ComfyUI is missing {', '.join(missing)}. Download with: python scripts/comfy.py models "
                         f"--download {' --download '.join(sets)} --comfy-dir <your ComfyUI folder>")
    t0 = time.monotonic()
    pid, refs = client.run(graph, timeout=2 * 3600 if kind == "clip" else 20 * 60)
    if not refs:
        raise ComfyError("the workflow finished but saved no images")
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "clip":
        with tempfile.TemporaryDirectory() as d:
            for i, ref in enumerate(refs):
                (pathlib.Path(d) / f"f{i:05d}.png").write_bytes(client.fetch(ref))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(WAN_FPS), "-i", str(pathlib.Path(d) / "f%05d.png"),
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-movflags", "+faststart", str(target)], check=True)
    else:
        target.write_bytes(client.fetch(refs[0]))
        if cutout:
            cut_out(target)
    meta = {
        "kind": kind, "prompt": prompt, "style": style, "aspect": aspect, "full_prompt": full, "negative": neg,
        "seed": seed, "quality": None if kind == "clip" else quality, "frames": frames if kind == "clip" else None,
        "models": {m: MODELS[m][2] for m in models_for(graph)}, "comfy_prompt_id": pid,
        "seconds": round(time.monotonic() - t0, 1), "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "workflow_sha": hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()[:16],
    }
    target.with_suffix(target.suffix + ".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return target, meta


def cut_out(path):
    """Remove the plain background from a prop (rembg, optional). Writes a transparent PNG in place."""
    from rembg import remove
    path.write_bytes(remove(path.read_bytes()))


# ---------------------------------------------------------------- models
def models_cmd(a, client):
    root = pathlib.Path(a.comfy_dir or env("COMFYUI_DIR")) if (a.comfy_dir or env("COMFYUI_DIR")) else None
    if root and (root / "models").is_dir():
        root = root / "models"
    for name, (sub, url, lic, gb, kit) in MODELS.items():
        have = client.available(sub) if not a.offline else None
        on_disk = root and (root / sub / name).exists()
        state = "ok" if (have and name in have) or on_disk else ("missing" if have is not None or root else "?")
        print(f"  {state:8} {kit:5} {gb:4.1f} GB  {sub}/{name}  ({lic})")
    if not a.download:
        return
    if not root:
        raise ComfyError("--download needs --comfy-dir (or COMFYUI_DIR): the ComfyUI folder that holds models/")
    want = [n for n, m in MODELS.items() if m[4] in a.download or "all" in a.download]
    todo = [n for n in want if not (root / MODELS[n][0] / n).exists()]
    need = sum(MODELS[n][3] for n in todo)
    free = shutil.disk_usage(root).free / 1e9
    if need + 5 > free:
        raise ComfyError(f"needs {need:.1f} GB plus 5 GB headroom, but only {free:.1f} GB is free on that drive")
    for n in todo:
        sub, url = MODELS[n][0], MODELS[n][1]
        dest = root / sub / n
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_suffix(".part")
        have = part.stat().st_size if part.exists() else 0
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        print(f"downloading {n} ({MODELS[n][3]} GB){f', resuming at {have / 1e9:.2f} GB' if have else ''} ...", flush=True)
        with urllib.request.urlopen(req, timeout=60) as r:
            resumed = have and r.status == 206  # a server that ignores Range sends the whole file again
            f = open(part, "ab" if resumed else "wb")
            done = have if resumed else 0
            total, last = done + int(r.headers.get("Content-Length") or 0), done
            with f:
                while chunk := r.read(1 << 22):
                    f.write(chunk)
                    done += len(chunk)
                    if total and done - last > total / 20:
                        last = done
                        print(f"  {100 * done / total:3.0f}%", flush=True)
        part.replace(dest)
    print("models ready" if todo else "nothing to download")


def export_cmd():
    d = COMFY / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    examples = {
        "background-16x9": ("background", "a quiet thrift store aisle at golden hour", "papercraft", "16x9"),
        "texture": ("texture", "kraft paper with soft folds", "papercraft", "1x1"),
        "prop": ("prop", "a cardboard shipping box, slightly open", "papercraft", "1x1"),
        "thumbnail-16x9": ("thumbnail", "stacks of folded clothes on a shop table", "papercraft", "16x9"),
        "clip-16x9": ("clip", "slow push-in across a papercraft market street", "papercraft", "16x9"),
    }
    for name, (kind, prompt, style, aspect) in examples.items():
        full, neg = compose_prompt(kind, prompt, style)
        w, h, ow, oh = KINDS[kind]["size"][aspect]
        g = wan_graph(full, neg, w, h, 33, 1) if kind == "clip" else sdxl_graph(full, neg, w, h, ow, oh, 1)
        (d / f"{name}.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
        print("wrote", (d / f"{name}.json").relative_to(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for kind in KINDS:
        p = sub.add_parser(kind, help=f"make a {kind}")
        p.add_argument("prompt")
        p.add_argument("--style", default="papercraft")
        p.add_argument("--aspect", default=next(iter(KINDS[kind]["size"])))
        p.add_argument("--seed", type=int)
        p.add_argument("--count", type=int, default=1, help="variations (new seed each)")
        p.add_argument("--steps", type=int, help="override the sampler steps")
        p.add_argument("--out", help="output file (default assets/comfy/<kind>/<slug>-<seed>.png|mp4)")
        p.add_argument("--dry-run", action="store_true", help="print the workflow graph and stop")
        if kind == "clip":
            p.add_argument("--frames", type=int, default=33, help="4n+1 frames at 16 fps: 33 = 2 s, 49 = 3 s, 81 = 5 s")
        else:
            p.add_argument("--quality", choices=list(QUALITY), default="final")
        if kind == "prop":
            p.add_argument("--cutout", action="store_true", help="remove the background (needs rembg)")
    sub.add_parser("check", help="is ComfyUI up, which GPU, which models are missing")
    m = sub.add_parser("models", help="list (and download) the models these workflows use")
    m.add_argument("--download", action="append", choices=["image", "clip", "all"], default=[])
    m.add_argument("--comfy-dir")
    m.add_argument("--offline", action="store_true", help="don't ask ComfyUI, only look on disk")
    sub.add_parser("export", help="write example workflows to comfy/workflows/ for the ComfyUI editor")
    sub.add_parser("styles", help="list the style presets")
    a = ap.parse_args(argv)

    client = Client()
    try:
        if a.cmd == "export":
            return export_cmd()
        if a.cmd == "styles":
            for k, v in styles().items():
                print(f"  {k:12} {v['prompt']}")
            return
        if a.cmd == "models":
            return models_cmd(a, client)
        if a.cmd == "check":
            s = client.system()
            dev = (s.get("devices") or [{}])[0]
            print(f"ComfyUI {s.get('system', {}).get('comfyui_version', '?')} at {client.url} on {dev.get('name', '?')} "
                  f"({dev.get('vram_total', 0) / 2**30:.1f} GB VRAM)")
            missing = client.missing(list(MODELS))
            print("all models present" if not missing else "missing: " + ", ".join(missing))
            return
        if a.out and a.count > 1:
            raise ComfyError("--out names one file; drop it to make several variations")
        for i in range(a.count):
            seed = a.seed + i if a.seed is not None else None
            res = make(a.cmd, a.prompt, a.style, a.aspect, seed, getattr(a, "quality", "final"), getattr(a, "frames", 33),
                       a.steps, a.out, getattr(a, "cutout", False), client, a.dry_run)
            if res:
                path, meta = res
                print(f"wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}  (seed {meta['seed']}, {meta['seconds']} s)")
    except ComfyError as e:
        sys.exit(f"ComfyUI: {e}")


if __name__ == "__main__":
    main()
