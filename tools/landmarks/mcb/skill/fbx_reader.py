"""fbx_reader: minimal binary-FBX geometry reader (no external libraries).

read_fbx(path, search_dirs=()) -> mesh dict compatible with mesh_analyze.voxelize:
  tri (T,3,3) world-space triangle positions, uv (T,3,2) (NaN if none), mat (T,) material
  index, nrm (T,3) normal hints (NaN if none), materials [{factor, image}], images {i: RGB array}.
Supports FBX 7.x binary (32-bit and 64-bit record headers), zlib arrays, Model TRS transforms
(translation, rotation order XYZ, pre-rotation, scaling), per-polygon materials and UVs.
Not supported: ASCII FBX, skinning/animation, rotation pivots/offsets.
"""
import os
import struct
import zlib

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ARR = {"f": ("<f4", 4), "d": ("<f8", 8), "l": ("<i8", 8), "i": ("<i4", 4), "b": ("u1", 1)}


class N:
    __slots__ = ("name", "props", "kids")

    def __init__(self, name, props, kids):
        self.name, self.props, self.kids = name, props, kids

    def child(self, name):
        for k in self.kids:
            if k.name == name:
                return k
        return None

    def children(self, name):
        return [k for k in self.kids if k.name == name]


def parse(data):
    if not data.startswith(b"Kaydara FBX Binary"):
        raise ValueError("not a binary FBX (ASCII FBX is not supported; re-export as binary)")
    ver = struct.unpack_from("<I", data, 23)[0]
    wide = ver >= 7500
    hdr = 25 if wide else 13
    fmt = "<QQQB" if wide else "<IIIB"

    def prop(p):
        t = chr(data[p])
        p += 1
        if t == "Y":
            return struct.unpack_from("<h", data, p)[0], p + 2
        if t == "C":
            return bool(data[p]), p + 1
        if t == "I":
            return struct.unpack_from("<i", data, p)[0], p + 4
        if t == "F":
            return struct.unpack_from("<f", data, p)[0], p + 4
        if t == "D":
            return struct.unpack_from("<d", data, p)[0], p + 8
        if t == "L":
            return struct.unpack_from("<q", data, p)[0], p + 8
        if t in ARR:
            n, enc, clen = struct.unpack_from("<III", data, p)
            p += 12
            raw = data[p:p + clen]
            if enc == 1:
                raw = zlib.decompress(raw)
            dt, _ = ARR[t]
            return np.frombuffer(raw, dtype=dt, count=n), p + clen
        if t in "SR":
            ln = struct.unpack_from("<I", data, p)[0]
            raw = data[p + 4:p + 4 + ln]
            return (raw.decode("utf-8", "replace") if t == "S" else raw), p + 4 + ln
        raise ValueError(f"unknown property type {t!r}")

    def node(p):
        end, nprop, plen, nlen = struct.unpack_from(fmt, data, p)
        if end == 0:
            return None, p + hdr
        name = data[p + hdr:p + hdr + nlen].decode("utf-8", "replace")
        q = p + hdr + nlen
        props = []
        for _ in range(nprop):
            v, q = prop(q)
            props.append(v)
        kids = []
        while q < end:
            ch, q = node(q)
            if ch is not None:
                kids.append(ch)
        return N(name, props, kids), end

    top, p = [], 27
    while p < len(data) - hdr:
        nd, p = node(p)
        if nd is None:
            break
        top.append(nd)
    return top


def _rot(rx, ry, rz):
    a, b, c = np.radians([rx, ry, rz])
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def _props70(n):
    out = {}
    p70 = n.child("Properties70")
    if p70:
        for pr in p70.children("P"):
            out[pr.props[0]] = pr.props[4:]
    return out


def _local(model):
    pr = _props70(model)
    t = np.array(pr.get("Lcl Translation", [0, 0, 0]), float)
    r = np.array(pr.get("Lcl Rotation", [0, 0, 0]), float)
    pre = np.array(pr.get("PreRotation", [0, 0, 0]), float)
    s = np.array(pr.get("Lcl Scaling", [1, 1, 1]), float)
    M = np.eye(4)
    M[:3, :3] = _rot(*pre) @ _rot(*r) @ np.diag(s)
    M[:3, 3] = t
    return M


def read_fbx(path, search_dirs=()):
    data = open(path, "rb").read()
    top = parse(data)
    objs = next(n for n in top if n.name == "Objects")
    conns = next((n for n in top if n.name == "Connections"), None)
    by_id = {}
    for o in objs.kids:
        if o.props and isinstance(o.props[0], (int, np.integer)):
            by_id[int(o.props[0])] = o
    parent_of, children_of, mats_of, tex_of = {}, {}, {}, {}
    geom_of = {}
    for c in (conns.kids if conns else []):
        if c.name != "C":
            continue
        kind, child, par = c.props[0], int(c.props[1]), int(c.props[2])
        co, po = by_id.get(child), by_id.get(par)
        if co is None or po is None:
            continue
        if co.name == "Model" and po.name == "Model":
            parent_of[child] = par
        elif co.name == "Geometry" and po.name == "Model":
            geom_of.setdefault(par, []).append(child)
        elif co.name == "Material" and po.name == "Model":
            mats_of.setdefault(par, []).append(child)
        elif co.name == "Texture" and po.name == "Material":
            tex_of.setdefault(par, []).append((child, c.props[3] if len(c.props) > 3 else ""))
    # ---- world matrices
    memo = {}

    def world(mid):
        if mid in memo:
            return memo[mid]
        M = _local(by_id[mid])
        if mid in parent_of:
            M = world(parent_of[mid]) @ M
        memo[mid] = M
        return M

    # ---- textures / materials
    dirs = list(search_dirs) + [os.path.dirname(path)]
    file_index = {}
    for d in dirs:
        for r, _, fs in os.walk(d):
            for f in fs:
                file_index.setdefault(f.lower(), os.path.join(r, f))

    def tex_path(tid):
        t = by_id[tid]
        for key in ("FileName", "RelativeFilename"):
            k = t.child(key)
            if k and k.props:
                base = str(k.props[0]).replace("\\", "/").split("/")[-1].lower()
                if base in file_index:
                    return file_index[base]
        return None

    images, image_ids, materials, mat_index = {}, {}, [], {}

    def material_for(mid):
        if mid in mat_index:
            return mat_index[mid]
        m = by_id[mid]
        pr = _props70(m)
        col = pr.get("DiffuseColor") or pr.get("Diffuse") or [1, 1, 1]
        factor = np.array(col[:3], float) if len(col) >= 3 else np.ones(3)
        best = None
        for tid, prop in tex_of.get(mid, []):
            pth = tex_path(tid)
            if not pth:
                continue
            nm = os.path.basename(pth).lower()
            score = (2 if "diffuse" in str(prop).lower() or "color" in str(prop).lower() else 0) \
                + (1 if any(k in nm for k in ("rgba", "albedo", "diffuse", "base", "color")) else 0) \
                - (2 if any(k in nm for k in ("glow", "emis", "norm", "spec", "rough", "metal", "ao")) else 0)
            if best is None or score > best[0]:
                best = (score, pth)
        if best is None:                       # FBX has no texture links: guess by file name
            base = str(m.props[1]).split("\x00")[0].lower() if len(m.props) > 1 else ""
            cand = None
            for fn, pth in file_index.items():
                if not fn.endswith((".png", ".jpg", ".jpeg", ".tga")):
                    continue
                sc = (4 if base and base in fn else 0) \
                    + (1 if any(k in fn for k in ("rgba", "albedo", "diffuse", "base", "color", "atlas")) else 0) \
                    - (2 if any(k in fn for k in ("glow", "emis", "norm", "spec", "rough", "metal")) else 0)
                if cand is None or sc > cand[0]:
                    cand = (sc, pth)
            if cand and cand[0] > -2:
                best = cand
                print(f"note: no texture link for material {base!r}; using {os.path.basename(cand[1])}")
        img_i = None
        if best:
            pth = best[1]
            if pth not in image_ids:
                im = Image.open(pth)
                if max(im.size) > 4096:
                    im.thumbnail((4096, 4096))
                images[len(images)] = np.asarray(im.convert("RGBA"))
                image_ids[pth] = len(images) - 1
            img_i = image_ids[pth]
        materials.append({"factor": factor if img_i is None else np.ones(3), "image": img_i,
                          "name": str(m.props[1]) if len(m.props) > 1 else ""})
        mat_index[mid] = len(materials) - 1
        return mat_index[mid]

    tris, uvs, mats, nrms = [], [], [], []
    for mid, gids in geom_of.items():
        M = world(mid)
        mlist = mats_of.get(mid, [])
        for gid in gids:
            g = by_id[gid]
            V = g.child("Vertices"); PI = g.child("PolygonVertexIndex")
            if V is None or PI is None:
                continue
            P = np.asarray(V.props[0], float).reshape(-1, 3)
            P = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
            idx = np.asarray(PI.props[0], np.int64)
            ends = np.nonzero(idx < 0)[0]
            starts = np.r_[0, ends[:-1] + 1]
            sizes = ends - starts + 1
            vi = np.where(idx < 0, ~idx, idx)
            ntri = np.maximum(sizes - 2, 0)
            tot = int(ntri.sum())
            poly = np.repeat(np.arange(len(sizes)), ntri)
            k = np.arange(tot) - np.repeat(np.cumsum(ntri) - ntri, ntri)
            a = starts[poly]; b_ = a + k + 1; c_ = a + k + 2
            tri = np.stack([P[vi[a]], P[vi[b_]], P[vi[c_]]], axis=1)
            # UVs
            uv = np.full((tot, 3, 2), np.nan, np.float32)
            le = g.child("LayerElementUV")
            if le is not None and le.child("UV") is not None:
                UV = np.asarray(le.child("UV").props[0], float).reshape(-1, 2)
                ui = le.child("UVIndex")
                mapping = (le.child("MappingInformationType").props[0] if le.child("MappingInformationType") else "ByPolygonVertex")
                src = (np.asarray(ui.props[0], np.int64) if ui is not None else None)
                def pick(pos):
                    key = pos if mapping == "ByPolygonVertex" else vi[pos]
                    return UV[src[key]] if src is not None else UV[key]
                uv = np.stack([pick(a), pick(b_), pick(c_)], axis=1).astype(np.float32)
                uv[..., 1] = 1.0 - uv[..., 1]        # FBX v origin is bottom-left
            # per-polygon materials
            mi = np.zeros(tot, np.int32)
            lm = g.child("LayerElementMaterial")
            if lm is not None and lm.child("Materials") is not None and mlist:
                ms = np.asarray(lm.child("Materials").props[0], np.int64)
                mp = lm.child("MappingInformationType").props[0] if lm.child("MappingInformationType") else "AllSame"
                local = ms[poly] if mp == "ByPolygon" and len(ms) > 1 else np.full(tot, ms[0] if len(ms) else 0)
                ids = np.array([material_for(m_) for m_ in mlist])
                mi = ids[np.clip(local, 0, len(ids) - 1)].astype(np.int32)
            elif mlist:
                mi[:] = material_for(mlist[0])
            else:
                materials.append({"factor": np.ones(3), "image": None, "name": ""})
                mi[:] = len(materials) - 1
            # normals hint
            nh = np.full((tot, 3), np.nan)
            ln = g.child("LayerElementNormal")
            if ln is not None and ln.child("Normals") is not None:
                Nn = np.asarray(ln.child("Normals").props[0], float).reshape(-1, 3)
                mapping = ln.child("MappingInformationType").props[0] if ln.child("MappingInformationType") else ""
                if mapping == "ByPolygonVertex" and len(Nn) == len(idx):
                    nh = (Nn[a] + Nn[b_] + Nn[c_]) / 3.0 @ M[:3, :3].T
                elif mapping == "ByVertice" and len(Nn) == len(P):
                    nh = (Nn[vi[a]] + Nn[vi[b_]] + Nn[vi[c_]]) / 3.0 @ M[:3, :3].T
            tris.append(tri); uvs.append(uv); mats.append(mi); nrms.append(nh)
    if not tris:
        raise ValueError("no mesh geometry found in FBX")
    return {"tri": np.concatenate(tris), "uv": np.concatenate(uvs), "mat": np.concatenate(mats),
            "nrm": np.concatenate(nrms), "materials": materials, "images": images}
