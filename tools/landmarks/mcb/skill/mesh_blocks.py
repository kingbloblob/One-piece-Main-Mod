"""mesh_blocks: read a Minecraft build exported as glTF/GLB (or a zip of one) whose
materials are NAMED BY BLOCK (Mineways and similar exporters: 'Block_of_Quartz',
'Stained_Glass', 'Wool', ...). Gives exact block types instead of colour guesses.

    python mesh_blocks.py model.zip --out analysis [--block 0.00390625]

Outputs in --out: grid.npz (label grid, x/y/z with z UP as in Mineways), names.json
(label -> readable name, coloured variants resolved from the texture atlas, e.g.
'magenta Wool'; glass colours are approximate, marked '~' with the measured hex colour:
look at the hex, not just the dye name), palette.txt (block counts), top.png, side_*.png.
Then study grid.npz with small ad-hoc numpy scripts (radial profiles, height bands,
connected components for repeated creatures) as described in references/mesh-analysis.md.

Memory: the binary buffer is memory-mapped and meshes are processed one at a time, so
models of several hundred MB work in ~3 GB RAM. If materials are NOT block names
(e.g. 'Material.001'), use mesh_analyze.py instead.
"""
import argparse
import json
import os
import struct
import tempfile
import zipfile
from collections import Counter

import numpy as np
from PIL import Image

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
DYES = {"white": (234, 236, 237), "orange": (241, 118, 20), "magenta": (189, 68, 179),
        "light_blue": (58, 175, 217), "yellow": (248, 198, 40), "lime": (112, 185, 26),
        "pink": (237, 141, 172), "gray": (63, 68, 72), "light_gray": (142, 142, 135),
        "cyan": (21, 138, 145), "purple": (122, 42, 173), "blue": (53, 57, 157),
        "brown": (114, 72, 41), "green": (85, 110, 28), "red": (161, 39, 35), "black": (21, 21, 26)}
TERRA = {"white": (210, 178, 161), "orange": (162, 84, 38), "magenta": (150, 88, 109),
         "light_blue": (113, 109, 138), "yellow": (186, 133, 35), "lime": (104, 118, 53),
         "pink": (162, 78, 79), "gray": (58, 42, 36), "light_gray": (135, 107, 98),
         "cyan": (87, 92, 92), "purple": (118, 70, 86), "blue": (74, 60, 91),
         "brown": (77, 51, 36), "green": (76, 83, 42), "red": (143, 61, 47), "black": (37, 23, 16)}
DYED = ("wool", "carpet", "stained_glass", "concrete", "shulker", "bed", "banner")


def open_model(path):
    if path.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        found = [os.path.join(r, f) for r, _, fs in os.walk(tmp) for f in fs
                 if f.lower().endswith((".gltf", ".glb"))]
        if not found:
            raise SystemExit("zip contains no .gltf or .glb")
        path = sorted(found, key=len)[0]
    base = os.path.dirname(path)
    if path.lower().endswith(".glb"):
        mm = np.memmap(path, dtype=np.uint8, mode="r")
        ln = struct.unpack("<I", bytes(mm[12:16]))[0]
        g = json.loads(bytes(mm[20:20 + ln]).decode())
        bin_off = 20 + ln + 8
        bufs = [mm[bin_off:]]
    else:
        g = json.load(open(path))
        bufs = [np.memmap(os.path.join(base, b["uri"]), dtype=np.uint8, mode="r") for b in g["buffers"]]
    return g, bufs, base


def accessor(g, bufs, i):
    a = g["accessors"][i]
    bv = g["bufferViews"][a["bufferView"]]
    buf = bufs[bv.get("buffer", 0)]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    dt, n = COMP[a["componentType"]], NC[a["type"]]
    isz = np.dtype(dt).itemsize * n
    stride = bv.get("byteStride", 0)
    if stride and stride != isz:
        raw = np.lib.stride_tricks.as_strided(buf[off:], shape=(a["count"], isz), strides=(stride, 1))
        return np.ascontiguousarray(raw).view(dt).reshape(a["count"], n)
    return np.frombuffer(buf[off:off + a["count"] * isz], dtype=dt).reshape(a["count"], n)


def load_image(g, bufs, base, tex_index):
    src = g["textures"][tex_index]["source"]
    im = g["images"][src]
    if "uri" in im:
        return np.array(Image.open(os.path.join(base, im["uri"])).convert("RGBA")).astype(float)
    bv = g["bufferViews"][im["bufferView"]]
    import io
    data = bytes(bufs[bv.get("buffer", 0)][bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])
    return np.array(Image.open(io.BytesIO(data)).convert("RGBA")).astype(float)


def estimate_block(g, bufs, sample=60):
    """Most common spacing between distinct vertex coordinates over many meshes. Full
    blocks dominate most builds, so the mode is the block size (sub-block detail such as
    stairs and buttons gives rarer, smaller spacings)."""
    c = Counter()
    seen = 0
    for m in g["meshes"]:
        for p in m["primitives"]:
            P = accessor(g, bufs, p["attributes"]["POSITION"]).astype(np.float64)
            for ax in range(3):
                d = np.diff(np.unique(np.round(P[:, ax], 6)))
                c.update(np.round(d[d > 1e-6], 6).tolist())
            seen += 1
            if seen >= sample:
                break
        if seen >= sample:
            break
    if not c:
        raise SystemExit("could not estimate block size; pass --block")
    return float(c.most_common(1)[0][0])


def run(path, out, block=None, tiles_per_row=None):
    os.makedirs(out, exist_ok=True)
    g, bufs, base = open_model(path)
    mats = [m.get("name", f"mat{i}") for i, m in enumerate(g["materials"])]
    bs = block or estimate_block(g, bufs)
    keys = []
    texinfo = {}
    for m in g["meshes"]:
        for p in m["primitives"]:
            mat = p.get("material", 0)
            P = accessor(g, bufs, p["attributes"]["POSITION"]).astype(np.float64) / bs
            I = (accessor(g, bufs, p["indices"]).reshape(-1, 3).astype(np.int64)
                 if "indices" in p else np.arange(len(P)).reshape(-1, 3))
            a, b_, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
            n = np.cross(b_ - a, c - a)
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
            ok = np.abs(n).max(1) > 0.999
            if "NORMAL" in p.get("attributes", {}):
                nn = accessor(g, bufs, p["attributes"]["NORMAL"])[I[ok, 0]]
            else:
                nn = n[ok]
            cen = ((a + b_ + c) / 3)[ok]
            cell = np.floor(cen - nn * 0.05).astype(np.int64)
            if "TEXCOORD_0" in p["attributes"]:
                UV = accessor(g, bufs, p["attributes"]["TEXCOORD_0"])
                uvc = (UV[I[ok, 0]] + UV[I[ok, 1]] + UV[I[ok, 2]]) / 3
                k = tiles_per_row or 32
                tile = np.clip((uvc[:, 1] * k).astype(int), 0, k - 1) * k + np.clip((uvc[:, 0] * k).astype(int), 0, k - 1)
            else:
                tile = np.zeros(len(cell), int)
            keys.append(np.c_[cell, mat * 4096 + tile])
            pbr = g["materials"][mat].get("pbrMetallicRoughness", {})
            if "baseColorTexture" in pbr:
                texinfo[mat] = pbr["baseColorTexture"]["index"]
    K = np.concatenate(keys)
    mn = K[:, :3].min(0)
    K[:, :3] -= mn
    dims = K[:, :3].max(0) + 1
    if dims.prod() > 4e8:
        raise SystemExit(f"grid {tuple(dims)} is too large: block size {bs:.6g} is probably wrong; pass --block")
    flat = (K[:, 0] * dims[1] + K[:, 1]) * dims[2] + K[:, 2]
    u, cnt = np.unique(flat * (1 << 20) + K[:, 3], return_counts=True)
    cu, lu = u >> 20, u & ((1 << 20) - 1)
    o = np.lexsort((-cnt, cu))
    cu, lu = cu[o], lu[o]
    first = np.r_[True, cu[1:] != cu[:-1]]
    labs, inv = np.unique(lu[first], return_inverse=True)
    grid = np.zeros(int(dims.prod()), np.uint16)
    grid[cu[first]] = inv + 1
    grid = grid.reshape(dims)
    # names and colours
    imgs = {t: load_image(g, bufs, base, t) for t in set(texinfo.values())}
    names, colors = {0: "air"}, np.zeros((len(labs) + 1, 3))
    k = tiles_per_row or 32
    for i, lab in enumerate(labs, 1):
        mat, tile = int(lab // 4096), int(lab % 4096)
        nm = mats[mat]
        col = np.array([200.0, 200, 200])
        if mat in texinfo:
            im = imgs[texinfo[mat]]
            ts = im.shape[0] // k
            ty, tx = tile // k, tile % k
            px = im[ty * ts:(ty + 1) * ts, tx * ts:(tx + 1) * ts]
            w = px[..., 3:4] / 255 + 1e-6
            col = (px[..., :3] * w).reshape(-1, 3).sum(0) / w.sum()
        low = nm.lower()
        tab = TERRA if ("stained_clay" in low or "terracotta" in low) else DYES if any(d in low for d in DYED) else None
        if tab:
            nm = min(tab, key=lambda d: np.sum((np.array(tab[d]) - col) ** 2)) + " " + nm
            if "glass" in low:   # translucent tiles blend with alpha: name is approximate
                nm = "~" + nm + " #%02x%02x%02x" % tuple(int(v) for v in col)
        names[i] = nm
        colors[i] = col
    np.savez_compressed(os.path.join(out, "grid.npz"), grid=grid, colors=colors, block=bs, origin=mn)
    json.dump(names, open(os.path.join(out, "names.json"), "w"), indent=0)
    c = Counter()
    lab_counts = np.bincount(grid.ravel(), minlength=len(names))
    for i, v in enumerate(lab_counts[1:], 1):
        c[names[i]] += int(v)
    tot = sum(c.values())
    with open(os.path.join(out, "palette.txt"), "w") as f:
        f.write(f"grid (x, y, z-up) = {tuple(int(d) for d in dims)}  block size {bs:.6g}  surface blocks {tot}\n")
        for nm, v in c.most_common():
            f.write(f"{v:9d}  {100 * v / tot:5.1f}%  {nm}\n")
    # renders: top (looking down z) and four sides
    def proj(axis, rev):
        G = np.flip(grid, axis) if rev else grid
        occ = G > 0
        idx = np.argmax(occ, axis)
        lab = np.take_along_axis(G, np.expand_dims(idx, axis), axis).squeeze(axis)
        im = colors[lab] * (1 - 0.6 * idx / G.shape[axis])[..., None]
        im[~occ.any(axis)] = (15, 15, 25)
        return np.transpose(im, (1, 0, 2))
    Image.fromarray(proj(2, True).astype(np.uint8)).save(os.path.join(out, "top.png"))
    for ax, rev, nm in [(1, False, "a"), (1, True, "b"), (0, False, "c"), (0, True, "d")]:
        im = proj(ax, rev)[::-1]
        Image.fromarray((im[:, ::-1] if rev else im).astype(np.uint8)).save(os.path.join(out, f"side_{nm}.png"))
    print(open(os.path.join(out, "palette.txt")).read()[:1500])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--block", type=float)
    ap.add_argument("--tiles-per-row", type=int, help="atlas tiles per row (default 32)")
    a = ap.parse_args()
    run(a.model, a.out, a.block, a.tiles_per_row)
