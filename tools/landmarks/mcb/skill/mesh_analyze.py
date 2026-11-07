"""mesh_analyze: study a Minecraft build exported as a 3D mesh (glTF / GLB / zip).

    python mesh_analyze.py model.zip --out analysis            # auto block size
    python mesh_analyze.py model.glb --out analysis --block 0.25   # force block size

Pipeline: read the mesh (no external libraries) -> keep the axis-aligned faces -> find the
block size and grid origin -> each face marks the block behind it as occupied -> flood fill
decides which unseen cells are hidden solid -> face colours are matched to approximate
block colours -> compact numeric report (+ one contact-sheet PNG).

Block identities are GUESSES from colours (see photo_tools.BLOCKS); partial geometry
(stairs, slabs, fences) is detected only as 'partial faces'. glTF files using Draco or
meshopt compression are not supported (the script says so); use an uncompressed glTF/GLB.
"""
import argparse
import base64
import io
import json
import os
import struct
import sys
import tempfile
import urllib.parse
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ------------------------------------------------------------------ reading
def load_container(path):
    """Return (gltf_json, buffers, base_dir). Accepts .gltf, .glb or .zip containing one."""
    tmp = None
    if path.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        found = [os.path.join(r, f) for r, _, fs in os.walk(tmp) for f in fs
                 if f.lower().endswith((".gltf", ".glb"))]
        if not found:
            raise ValueError("zip contains no .gltf or .glb")
        path = sorted(found, key=lambda p: (p.lower().endswith(".glb"), len(p)))[0]
    base = os.path.dirname(path)
    glb_bin = None
    if path.lower().endswith(".glb"):
        data = open(path, "rb").read()
        magic, ver, total = struct.unpack_from("<4sII", data, 0)
        if magic != b"glTF":
            raise ValueError("not a GLB file")
        off, g = 12, None
        while off < len(data):
            ln, typ = struct.unpack_from("<II", data, off)
            chunk = data[off + 8: off + 8 + ln]
            if typ == 0x4E4F534A:
                g = json.loads(chunk.decode("utf-8"))
            elif typ == 0x004E4942 and glb_bin is None:
                glb_bin = chunk
            off += 8 + ln
    else:
        g = json.load(open(path, encoding="utf-8"))
    bad = [e for e in (g.get("extensionsRequired", []) + g.get("extensionsUsed", []))
           if e in ("KHR_draco_mesh_compression", "EXT_meshopt_compression")]
    if bad:
        raise ValueError(f"mesh uses {bad}: compressed geometry is not supported; export an uncompressed glTF/GLB")
    bufs = []
    for b in g.get("buffers", []):
        uri = b.get("uri")
        if uri is None:
            bufs.append(glb_bin)
        elif uri.startswith("data:"):
            bufs.append(base64.b64decode(uri.split(",", 1)[1]))
        else:
            bufs.append(open(os.path.join(base, urllib.parse.unquote(uri)), "rb").read())
    return g, bufs, base


def read_accessor(g, bufs, ai):
    acc = g["accessors"][ai]
    dt = np.dtype(COMP[acc["componentType"]])
    n = NCOMP[acc["type"]]
    if "bufferView" not in acc:
        return np.zeros((acc["count"], n), dtype=np.float32)
    bv = g["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or dt.itemsize * n
    buf = bufs[bv["buffer"]]
    if stride == dt.itemsize * n:
        arr = np.frombuffer(buf, dtype=dt, count=acc["count"] * n, offset=off).reshape(acc["count"], n)
    else:
        arr = np.ndarray(shape=(acc["count"], n), dtype=dt, buffer=buf, offset=off, strides=(stride, dt.itemsize))
    if acc.get("normalized") and dt.kind in "iu":
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


def _local_matrix(n):
    if "matrix" in n:
        return np.array(n["matrix"], float).reshape(4, 4).T
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R * np.array(n.get("scale", [1, 1, 1]), float)[None, :]
    M[:3, 3] = n.get("translation", [0, 0, 0])
    return M


def load_images(g, bufs, base):
    out = {}
    for i, im in enumerate(g.get("images", [])):
        try:
            if "uri" in im:
                u = im["uri"]
                data = base64.b64decode(u.split(",", 1)[1]) if u.startswith("data:") else \
                    open(os.path.join(base, urllib.parse.unquote(u)), "rb").read()
            else:
                bv = g["bufferViews"][im["bufferView"]]
                o = bv.get("byteOffset", 0)
                data = bufs[bv["buffer"]][o:o + bv["byteLength"]]
            out[i] = np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))
        except Exception as e:  # noqa: BLE001
            print("warning: could not read image", i, e)
    return out


def resolve_model(path, depth=0):
    """Unpack (nested) zips; return (model_path, extra_search_dirs). Prefers glb/gltf over fbx."""
    dirs = []
    while path.lower().endswith(".zip") and depth < 4:
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        dirs.append(tmp)
        files = [os.path.join(r, f) for r, _, fs in os.walk(tmp) for f in fs]
        pick = None
        for ext in (".glb", ".gltf", ".fbx"):
            c = [f for f in files if f.lower().endswith(ext)]
            if c:
                pick = max(c, key=os.path.getsize)
                break
        if pick is None:
            zips = [f for f in files if f.lower().endswith(".zip")]
            if not zips:
                raise ValueError("no .glb/.gltf/.fbx (or nested zip) found in archive")
            pick = max(zips, key=os.path.getsize)
        path = pick
        depth += 1
    return path, dirs


def read_mesh(path):
    """Return dict: tri (T,3,3) world positions, uv (T,3,2) or None, mat (T,) int, vcol (T,3) or None,
    nrm (T,3) vertex-normal hint, materials list, images dict."""
    path, dirs = resolve_model(path)
    if path.lower().endswith(".fbx"):
        from fbx_reader import read_fbx
        return read_fbx(path, dirs)
    g, bufs, base = load_container(path)
    images = load_images(g, bufs, base)
    mats = []
    for m in g.get("materials", [{}]):
        pbr = m.get("pbrMetallicRoughness", {})
        tex = pbr.get("baseColorTexture", {}).get("index")
        img = g["textures"][tex].get("source") if tex is not None and "textures" in g else None
        mats.append({"factor": np.array(pbr.get("baseColorFactor", [1, 1, 1, 1])[:3], float), "image": img})
    if not mats:
        mats = [{"factor": np.ones(3), "image": None}]
    tris, uvs, matid, nrm_hint = [], [], [], []
    skipped = 0
    scene = g["scenes"][g.get("scene", 0)] if "scenes" in g else {"nodes": list(range(len(g["nodes"])))}
    stack = [(n, np.eye(4)) for n in scene["nodes"]]
    while stack:
        ni, parent = stack.pop()
        node = g["nodes"][ni]
        M = parent @ _local_matrix(node)
        for c in node.get("children", []):
            stack.append((c, M))
        if "mesh" not in node:
            continue
        for prim in g["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode", 4) != 4:
                skipped += 1
                continue
            P = read_accessor(g, bufs, prim["attributes"]["POSITION"]).astype(np.float64)
            P = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
            idx = read_accessor(g, bufs, prim["indices"]).ravel().astype(np.int64) if "indices" in prim \
                else np.arange(len(P))
            idx = idx[: len(idx) // 3 * 3].reshape(-1, 3)
            tris.append(P[idx])
            if "TEXCOORD_0" in prim["attributes"]:
                uvs.append(read_accessor(g, bufs, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)[idx])
            else:
                uvs.append(np.full((len(idx), 3, 2), np.nan, np.float32))
            if "NORMAL" in prim["attributes"]:
                N = read_accessor(g, bufs, prim["attributes"]["NORMAL"]).astype(np.float64)
                N = N @ M[:3, :3].T
                nrm_hint.append(N[idx].mean(axis=1))
            else:
                nrm_hint.append(np.full((len(idx), 3), np.nan))
            matid.append(np.full(len(idx), prim.get("material", 0), np.int32))
    if not tris:
        raise ValueError("no triangle meshes found")
    if skipped:
        print(f"note: skipped {skipped} non-triangle primitives")
    return {"tri": np.concatenate(tris), "uv": np.concatenate(uvs), "mat": np.concatenate(matid),
            "nrm": np.concatenate(nrm_hint), "materials": mats, "images": images}


# ------------------------------------------------------------ voxelisation
def face_colors(mesh, sel, chunk=200000):
    """Mean base colour (0-255) for selected triangles by sampling their texture at 7 points."""
    bary = np.array([[1 / 3, 1 / 3, 1 / 3], [2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3],
                     [.4, .4, .2], [.4, .2, .4], [.2, .4, .4]])
    out = np.zeros((len(sel), 3), np.float32)
    mat = mesh["mat"][sel]
    for mi, m in enumerate(mesh["materials"]):
        which = np.nonzero(mat == mi)[0]
        if not len(which):
            continue
        img = mesh["images"].get(m["image"]) if m["image"] is not None else None
        for s in range(0, len(which), chunk):
            w = which[s:s + chunk]
            if img is None or np.isnan(mesh["uv"][sel[w]]).any():
                out[w] = m["factor"] * 255
                continue
            uv = mesh["uv"][sel[w]]                                  # (n,3,2)
            pts = np.einsum("sk,nkc->nsc", bary, uv) % 1.0           # (n,7,2)
            h, wd = img.shape[:2]
            px = np.clip((pts[..., 0] * wd).astype(np.int64), 0, wd - 1)
            py = np.clip((pts[..., 1] * h).astype(np.int64), 0, h - 1)
            samp = img[py, px].astype(np.float32)                    # (n,7,C)
            if samp.shape[2] == 4:                                   # ignore transparent texels
                al = samp[..., 3:4] / 255.0
                wsum = al.sum(axis=1)
                col = (samp[..., :3] * al).sum(axis=1) / np.maximum(wsum, 1e-6)
                col[wsum[:, 0] < 1e-3] = 128
            else:
                col = samp.mean(axis=1)
            out[w] = col * m["factor"]
    return out


def estimate_block(ext, forced=None):
    """Block size from the tangent extents of axis-aligned triangles; returns (size, top candidates)."""
    e = ext[ext > 1e-9]
    bins = np.round(np.log2(e) * 40).astype(np.int64)
    vals, counts = np.unique(bins, return_counts=True)
    order = np.argsort(-counts)[:5]
    cands = []
    for o in order:
        sel = bins == vals[o]
        cands.append((float(e[sel].mean()), int(counts[o])))
    return (forced or cands[0][0]), cands


def pick_atlas(mesh):
    """Index of the image used by most triangles (the block texture atlas), or None."""
    counts = {}
    for mi, m in enumerate(mesh["materials"]):
        if m["image"] is not None:
            counts[m["image"]] = counts.get(m["image"], 0) + int((mesh["mat"] == mi).sum())
    return max(counts, key=counts.get) if counts else None


def voxelize(mesh, block=None, tile_px=None):
    tri = mesh["tri"]
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] /= ln[ok, None]
    hint = mesh["nrm"]
    flip = np.nan_to_num((n * hint).sum(axis=1)) < 0
    n[flip] *= -1
    ax = np.abs(n).argmax(axis=1)
    aligned = ok & (np.abs(n[np.arange(len(n)), ax]) > 0.98)
    sel = np.nonzero(aligned)[0]
    stats = {"triangles": int(len(tri)), "aligned": int(len(sel))}
    T = tri[sel]
    axs = ax[sel]
    sg = np.sign(n[sel, axs]).astype(int)
    span = T.max(axis=1) - T.min(axis=1)                                  # (m,3)
    mask = np.ones_like(span, bool)
    mask[np.arange(len(sel)), axs] = False
    ext = span[mask]
    s, cands = estimate_block(ext, block)
    stats["block_size"] = s
    stats["block_candidates"] = cands
    verts = T.reshape(-1, 3)
    phase = np.zeros(3)
    for a in range(3):
        ph = (verts[:, a] / s) % 1.0
        bins = np.bincount((ph * 50).astype(int) % 50, minlength=50)
        pk = bins.argmax()
        center = (pk + 0.5) / 50
        delta = ((ph - center + 0.5) % 1.0) - 0.5
        near = delta[np.abs(delta) < 0.05]
        phase[a] = float((center + (near.mean() if len(near) else 0.0)) % 1.0)
        if phase[a] > 0.98:
            phase[a] = 0.0
    cen = T.mean(axis=1) / s - phase[None, :]
    owner = np.floor(cen.copy()).astype(np.int64)
    air = owner.copy()
    shift = 0.01
    for a in range(3):
        m = axs == a
        owner[m, a] = np.floor(cen[m, a] - sg[m] * shift).astype(np.int64)
        air[m, a] = np.floor(cen[m, a] + sg[m] * shift).astype(np.int64)
    # partial geometry: face plane not on the integer grid or face smaller than a block
    plane = cen[np.arange(len(sel)), axs]
    off_grid = np.abs(plane - np.round(plane)) > 0.03
    small = (ext.reshape(-1, 2).max(axis=1) / s) < 0.9
    stats["partial_face_share"] = round(float((off_grid | small).mean()), 3)
    cols = face_colors(mesh, sel)
    atlas_i = pick_atlas(mesh)
    face_tile = np.full(len(sel), -1, np.int64)
    tile_origins, tile_size = np.zeros((0, 2), int), 0
    if atlas_i is not None:
        img = mesh["images"][atlas_i]
        ah, aw = img.shape[:2]
        uvA = mesh["uv"][sel] * np.array([aw, ah], np.float32)               # pixel coords (top-left origin)
        mimg = np.array([m["image"] if m["image"] is not None else -1 for m in mesh["materials"]])[mesh["mat"][sel]]
        okuv = ~np.isnan(uvA).any(axis=(1, 2)) & (mimg == atlas_i)
        mn, mx = np.nanmin(uvA, axis=1), np.nanmax(uvA, axis=1)
        ext2 = mx - mn
        e_round = np.round(ext2.max(axis=1)).astype(int)
        e_mode = int(np.bincount(e_round[okuv & (e_round > 1)]).argmax()) if (okuv & (e_round > 1)).any() else 0
        if e_mode >= 2:
            full = okuv & (np.abs(ext2[:, 0] - e_mode) < 0.6) & (np.abs(ext2[:, 1] - e_mode) < 0.6)
            org = np.unique(np.round(mn[full]).astype(int), axis=0)
            tmap = np.full((ah, aw), -1, np.int32)
            for ti, (ox, oy) in enumerate(org):
                tmap[oy:oy + e_mode, ox:ox + e_mode] = ti
            cpx = np.clip(np.round(uvA.mean(axis=1)).astype(int), 0, [aw - 1, ah - 1])
            ft = tmap[cpx[:, 1], cpx[:, 0]]
            face_tile[okuv] = ft[okuv]
            tile_origins, tile_size = org, e_mode
    S = len(tile_origins)
    lo = np.minimum(owner.min(axis=0), air.min(axis=0)) - 1
    hi = np.maximum(owner.max(axis=0), air.max(axis=0)) + 1
    dims = tuple(int(v) for v in hi - lo + 1)
    stats["grid"] = dims
    if np.prod(dims, dtype=np.float64) > 4e8:
        raise ValueError(f"grid {dims} too large; check --block (estimated {s:.5f})")
    o = owner - lo
    a_ = air - lo
    occ = np.zeros(dims, bool)
    occ[o[:, 0], o[:, 1], o[:, 2]] = True
    airmark = np.zeros(dims, bool)
    airmark[a_[:, 0], a_[:, 1], a_[:, 2]] = True
    # colour per owner voxel (mean of its faces)
    flat = np.ravel_multi_index((o[:, 0], o[:, 1], o[:, 2]), dims)
    uniq, inv = np.unique(flat, return_inverse=True)
    sums = np.zeros((len(uniq), 3), np.float64)
    np.add.at(sums, inv, cols)
    cnt = np.bincount(inv).astype(np.float64)
    vcol = (sums / cnt[:, None]).astype(np.uint8)
    vtile = np.full(len(uniq), -1, np.int64)
    if atlas_i is not None and (face_tile >= 0).any():
        v_ = face_tile >= 0
        key = inv[v_] * (S + 1) + face_tile[v_]
        uk, cn2 = np.unique(key, return_counts=True)
        vi_, ti_ = uk // (S + 1), uk % (S + 1)
        order = np.lexsort((-cn2, vi_))
        first = np.r_[True, vi_[order][1:] != vi_[order][:-1]]
        vtile[vi_[order][first]] = ti_[order][first]
    # hidden solid: empty regions never touched by an air-facing face
    from scipy import ndimage
    lab, nlab = ndimage.label(~occ)
    air_labels = np.unique(lab[airmark & ~occ])
    border = np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                       lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
    is_air = np.isin(lab, np.union1d(air_labels, border)) | occ
    hidden = ~is_air
    stats["owner_voxels"] = int(len(uniq))
    stats["hidden_solid_voxels"] = int(hidden.sum())
    stats["atlas_tiles_found"] = int(S)
    stats["atlas_tile_px"] = int(tile_size)
    return {"occ": occ, "hidden": hidden, "flat_idx": uniq, "vcol": vcol, "vtile": vtile, "dims": dims,
            "stats": stats, "atlas": mesh["images"].get(atlas_i) if atlas_i is not None else None,
            "tile_origins": tile_origins, "tile_size": tile_size, "S": S}


# ------------------------------------------------------------ blocks & build
def match_blocks(vcol, k=14):
    """Quantise voxel colours to k clusters and map each to its nearest block name."""
    from photo_tools import BLOCKS, nearest_blocks
    im = Image.fromarray(vcol.reshape(-1, 1, 3))
    q = im.quantize(colors=k, method=Image.MEDIANCUT)
    idx = np.asarray(q).reshape(-1)
    pal = np.array(q.getpalette()[:3 * k]).reshape(-1, 3)
    names = [f"minecraft:{nearest_blocks(tuple(int(v) for v in c), 1)[0]}" for c in pal]
    return idx, pal, names


def tile_color(atlas, origin, size):
    ox, oy = int(origin[0]), int(origin[1])
    blk = atlas[oy:oy + size, ox:ox + size].astype(np.float32)
    if blk.shape[2] == 4:
        a = blk[..., 3:4] / 255.0
        if a.sum() < 1e-3:
            return (128, 128, 128)
        return tuple(int(v) for v in (blk[..., :3] * a).sum(axis=(0, 1)) / a.sum())
    return tuple(int(v) for v in blk.mean(axis=(0, 1)))


def match_tiles(vox):
    """Cluster id = atlas tile used by each surface block. Names are provisional (nearest by colour)."""
    from photo_tools import nearest_blocks
    vt = vox["vtile"]
    valid = vt >= 0
    tiles = np.unique(vt[valid])
    pos = {int(t): i for i, t in enumerate(tiles)}
    idx = np.array([pos.get(int(t), -1) for t in vt])
    names = [f"minecraft:{nearest_blocks(tile_color(vox['atlas'], vox['tile_origins'][t], vox['tile_size']), 1)[0]}" for t in tiles]
    if (~valid).any():
        names.append("minecraft:stone")
        idx[~valid] = len(names) - 1
    return idx, None, names, tiles


def save_tile_sheet(path, vox, idx, names, tiles, top=16, zoom=6):
    from PIL import ImageDraw
    cnt = np.bincount(idx, minlength=len(names))
    order = [i for i in np.argsort(-cnt) if i < len(tiles)][:top]
    size = vox["tile_size"]
    cell = size * zoom
    cols = 8
    rows = (len(order) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 14)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    out = []
    for n, i in enumerate(order):
        ox, oy = [int(v) for v in vox["tile_origins"][tiles[i]]]
        t = Image.fromarray(vox["atlas"][oy:oy + size, ox:ox + size]).convert("RGBA")
        bg = Image.new("RGBA", t.size, (60, 60, 60, 255)); bg.alpha_composite(t)
        bg = bg.convert("RGB").resize((cell, cell), Image.NEAREST)
        x, y = (n % cols) * cell, (n // cols) * (cell + 14)
        sheet.paste(bg, (x, y + 14))
        d.text((x + 2, y + 1), f"#{n + 1} {100 * cnt[i] / max(len(idx), 1):.0f}%", fill=(230, 230, 230))
        out.append((n + 1, (ox, oy), round(100 * cnt[i] / max(len(idx), 1), 1), names[i]))
    sheet.save(path)
    return out


def to_bigbuild(vox, idx, names, hidden_block="minecraft:stone"):
    from mcbig import BigBuild, T
    nx, ny, nz = vox["dims"]
    b = BigBuild(y_min=0, y_max=ny - 1)
    ox, oy, oz = np.unravel_index(vox["flat_idx"], vox["dims"])
    ids = np.array([b.register(n) for n in names], dtype=np.uint16)[idx]
    hx, hy, hz = np.nonzero(vox["hidden"])
    X = np.concatenate([ox, hx]); Y = np.concatenate([oy, hy]); Z = np.concatenate([oz, hz])
    V = np.concatenate([ids, np.full(len(hx), b.register(hidden_block), np.uint16)])
    keys = np.stack([X // T, Z // T], axis=1)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.ravel()
    for g_, (tx, tz) in enumerate(uniq):
        s = inv == g_
        b._tile(int(tx), int(tz))[X[s] - tx * T, Y[s], Z[s] - tz * T] = V[s]
    return b


# ----------------------------------------------------------------- analysis
def periodicity(depth, hit, vmin=3):
    """Dominant spacing (blocks) of facade relief along the horizontal axis (bays, buttresses,
    windows). Each wall row is high-pass filtered, its ends are trimmed (corner towers), rows with
    no relief are ignored, and the per-row autocorrelations are averaged; only genuine peaks count."""
    from scipy.ndimage import uniform_filter1d
    d = np.where(hit, np.minimum(depth, 6), 6).astype(float)
    nh = d.shape[0]
    if nh < 16:
        return None
    d = d - uniform_filter1d(d, size=9, axis=0, mode="nearest")
    trim = max(3, int(nh * 0.2))
    d = d[trim:nh - trim]
    n = d.shape[0]
    energy = (d ** 2).sum(axis=0)
    rows = energy > max(0.05 * energy.max(), 1e-6) if energy.max() > 0 else None
    if rows is None or rows.sum() < 3:
        return None
    f = np.fft.rfft(d[:, rows], n=2 * n, axis=0)
    ac = np.fft.irfft(f * np.conj(f), axis=0)[:n]
    ac = (ac / np.maximum(ac[0], 1e-9)).mean(axis=1)
    hi = min(n // 2, 40)
    peaks = [l for l in range(vmin, hi) if ac[l] > ac[l - 1] and ac[l] >= ac[l + 1] and ac[l] > 0.15]
    if not peaks:
        return None
    lag = max(peaks, key=lambda l: ac[l] - 0.002 * l)
    return {"period": int(lag), "strength": round(float(ac[lag]), 2)}


def analyze(b, vox, idx, pal, names):
    from verify import measure, silhouette, flatness
    out = {"stats": vox["stats"], "measure": measure(b), "silhouette": silhouette(b, 10)}
    out["flat_wall_percent"] = flatness(b)
    # palette share overall and by height third
    ox, oy, oz = np.unravel_index(vox["flat_idx"], vox["dims"])
    k = len(names)
    tot = np.bincount(idx, minlength=k) / max(len(idx), 1)
    out["palette"] = [(names[i], round(float(tot[i]) * 100, 1)) for i in np.argsort(-tot)[:10]]
    ny = vox["dims"][1]
    bands = {}
    for nm, (a, c) in {"low": (0, ny / 3), "mid": (ny / 3, 2 * ny / 3), "high": (2 * ny / 3, ny + 1)}.items():
        m = (oy >= a) & (oy < c)
        if m.any():
            sh = np.bincount(idx[m], minlength=k) / m.sum()
            bands[nm] = [(names[i], round(float(sh[i]) * 100, 1)) for i in np.argsort(-sh)[:4]]
    out["palette_by_height"] = bands
    # facade rhythm (bay spacing) per side, and symmetry
    maps = b.elevation_maps()
    out["facade_rhythm"] = {s: periodicity(dp, ht) for s, (_, ht, dp) in maps.items()}
    solid = vox["occ"] | vox["hidden"]
    H = np.where(solid.any(axis=1), solid.shape[1] - 1 - solid[:, ::-1, :].argmax(axis=1), -1)
    def sym(Hm, Hf):
        both = (Hm >= 0) | (Hf >= 0)
        return round(float(1 - np.abs(Hm - Hf)[both].mean() / max(Hm.max(), 1)), 2) if both.any() else 0.0
    out["symmetry"] = {"mirror_x": sym(H, H[::-1]), "mirror_z": sym(H, H[:, ::-1])}
    # roof/height steps: gradient of the height map
    gx = np.abs(np.diff(H, axis=0))[(H[1:] >= 0) & (H[:-1] >= 0)]
    gz = np.abs(np.diff(H, axis=1))[(H[:, 1:] >= 0) & (H[:, :-1] >= 0)]
    g = np.concatenate([gx, gz])
    if len(g):
        out["height_steps_percent"] = {str(s): round(100 * float((g == s).mean()), 1) for s in (0, 1, 2)}
        out["height_steps_percent"]["3+"] = round(100 * float((g >= 3).mean()), 1)
    return out


def report_text(a):
    L = []
    s = a["stats"]; m = a["measure"]
    L.append(f"size (x,y,z) = {m['size_x']} x {m['size_y']} x {m['size_z']} blocks   height/width {m['height_to_width']}")
    L.append(f"block size in model units: {s['block_size']:.5f}   triangles {s['triangles']:,} (axis-aligned {s['aligned']:,})")
    L.append(f"surface blocks {s['owner_voxels']:,}   hidden solid {s['hidden_solid_voxels']:,}   partial-geometry faces {100 * s['partial_face_share']:.0f}%")
    L.append("silhouette (y_from-y_to: width_x x width_z):  " + "; ".join(f"{r[0]}-{r[1]}: {r[2]}x{r[3]}" for r in a["silhouette"]))
    L.append("palette: " + ", ".join(f"{n.split(':')[1]} {p}%" for n, p in a["palette"][:8]))
    for k, v in a["palette_by_height"].items():
        L.append(f"  {k}: " + ", ".join(f"{n.split(':')[1]} {p}%" for n, p in v))
    if a.get("top_tiles"):
        L.append("top atlas tiles (row/col, share, provisional block): " + "; ".join(
            f"#{t[0]}@{t[1][0]},{t[1][1]} {t[2]}% {t[3].split(':')[1]}" for t in a["top_tiles"][:12]))
    L.append(f"flat wall % by side: {a['flat_wall_percent']}")
    L.append(f"facade rhythm (bay spacing): {a['facade_rhythm']}")
    L.append(f"symmetry (1.0 = mirror image): {a['symmetry']}")
    L.append(f"height steps between neighbouring columns %: {a.get('height_steps_percent')}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--block", type=float, help="force block size in model units")
    ap.add_argument("--colors", type=int, default=14)
    ap.add_argument("--tile", type=int, default=None, help="(unused; tiles are detected from UVs)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mesh = read_mesh(a.model)
    vox = voxelize(mesh, a.block, a.tile)
    tiles = None
    if vox["atlas"] is not None and (vox["vtile"] >= 0).mean() > 0.5:
        idx, pal, names, tiles = match_tiles(vox)
        print(f"palette from {vox['S']} atlas tiles of {vox['tile_size']} px")
    else:
        idx, pal, names = match_blocks(vox["vcol"], a.colors)
    b = to_bigbuild(vox, idx, names)
    res = analyze(b, vox, idx, pal, names)
    if tiles is not None:
        res["top_tiles"] = save_tile_sheet(os.path.join(a.out, "tiles_top.png"), vox, idx, names, tiles)
    txt = report_text(res)
    print(txt)
    with open(os.path.join(a.out, "report.txt"), "w") as f:
        f.write(txt + "\n")
    with open(os.path.join(a.out, "analysis.json"), "w") as f:
        json.dump(res, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    b.render_elevations(os.path.join(a.out, "elevations.png"), max_side=900)
    np.savez_compressed(os.path.join(a.out, "voxels.npz"), occ=vox["occ"], hidden=vox["hidden"],
                        flat_idx=vox["flat_idx"], cluster=idx, palette=np.array(names),
                        vtile=vox["vtile"], tiles=(tiles if tiles is not None else np.array([])), S=vox["S"],
                        tile_origins=vox["tile_origins"], tile_size=vox["tile_size"])
    print("wrote", a.out)


if __name__ == "__main__":
    main()
