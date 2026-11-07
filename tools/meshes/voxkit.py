"""Blocky (Minecraft-style) models: shapes are filled into a grid of small cubes ("pixels"), and only the
outside faces are kept, merged into big flat rectangles where neighbours share a colour.

Same skeleton/animation/output as meshkit.Mesh (the game's MeshForms draws both), so a model written with
Vox.ball/tube/box/sheet becomes a .bin with Vox.to_mesh().write(path).

Coordinates are blocks: y up, front -z, +x = the model's right. px = the size of one pixel cube in blocks
(1/16 is a normal Minecraft pixel; big bosses use bigger pixels, like scaled-up mobs).
Colours: an (r, g, b) tuple, '#hex', (r, g, b, 1) for a glowing pixel, or a function f(p, u) -> colour,
where p is the pixel centre and u runs 0..1 along a tube.
"""
import math

import numpy as np

from meshkit import Mesh, catmull, hexc, rot_matrix, norm


def _col(c):
    if c is None:
        return None
    if isinstance(c, str):
        return hexc(c)
    return tuple(c)


class Vox:
    def __init__(self, px, scale=1.0, noise=0.0, seed=1):
        self.px = px
        self.mesh = Mesh(scale)
        self.cells = {'root': {}}
        self.noise = noise
        self.seed = seed

    # ---- skeleton (same as Mesh) ----
    def bone(self, name, parent, pivot):
        self.mesh.bone(name, parent, pivot)
        self.cells[name] = {}
        return name

    def anim(self, *a, **k):
        self.mesh.anim(*a, **k)

    # ---- grid helpers ----
    def _range(self, lo, hi):
        p = self.px
        i0 = np.floor(np.asarray(lo) / p).astype(int)
        i1 = np.ceil(np.asarray(hi) / p).astype(int)
        ii, jj, kk = np.meshgrid(np.arange(i0[0], i1[0] + 1), np.arange(i0[1], i1[1] + 1), np.arange(i0[2], i1[2] + 1), indexing='ij')
        idx = np.stack([ii.ravel(), jj.ravel(), kk.ravel()], 1)
        return idx, (idx + 0.5) * p

    def _set(self, bone, idx, centers, color, us=None, mode='fill'):
        cells = self.cells[bone]
        fn = color if callable(color) else None
        c0 = None if fn else _col(color)
        for n in range(len(idx)):
            key = (int(idx[n][0]), int(idx[n][1]), int(idx[n][2]))
            if mode == 'paint' and key not in cells:
                continue
            if mode == 'carve':
                cells.pop(key, None)
                continue
            c = _col(fn(centers[n], 0.0 if us is None else float(us[n]))) if fn else c0
            if c is None:
                continue
            cells[key] = c

    # ---- shapes ----
    def ball(self, bone, center, radii, color, rot=(0, 0, 0), mode='fill', cut=None):
        """A solid egg. cut = (axis, sign, value): keep only one side of a plane (e.g. ('y', 1, 2.0) keeps y > 2)."""
        c = np.asarray(center, dtype=float)
        r = np.asarray(radii, dtype=float)
        R = rot_matrix(*rot)
        ext = np.abs(R) @ r
        idx, cen = self._range(c - ext - self.px, c + ext + self.px)
        local = (cen - c) @ R  # into the egg's own axes
        m = ((local / r) ** 2).sum(1) <= 1.0
        if cut:
            ax, sg, val = cut
            a = 'xyz'.index(ax)
            m &= (cen[:, a] - val) * sg >= 0
        self._set(bone, idx[m], cen[m], color, mode=mode)

    def box(self, bone, lo, hi, color, mode='fill'):
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        idx, cen = self._range(lo, hi)
        m = np.all((cen >= lo) & (cen <= hi), 1)
        self._set(bone, idx[m], cen[m], color, mode=mode)

    def tube(self, bone, path, radius, color, per=6, smooth=True, mode='fill', square=False):
        """A solid tube along a curve; radius = number or list (start..end). square: box cross-section."""
        pts = catmull(path, per) if smooth and len(path) > 2 else [np.asarray(p, dtype=float) for p in path]
        n = len(pts) - 1
        if n < 1:
            return
        rads = [_lerp(radius, i / n) for i in range(n + 1)]
        done = {}
        for s in range(n):
            a, b = pts[s], pts[s + 1]
            ra, rb = max(rads[s], self.px * 0.55), max(rads[s + 1], self.px * 0.55)
            rr = max(ra, rb)
            idx, cen = self._range(np.minimum(a, b) - rr - self.px, np.maximum(a, b) + rr + self.px)
            d = b - a
            L2 = max(float(d @ d), 1e-12)
            t = np.clip(((cen - a) @ d) / L2, 0, 1)
            near = a + t[:, None] * d
            off = cen - near
            r = ra + (rb - ra) * t
            if square:
                m = np.all(np.abs(off) <= r[:, None], 1)
            else:
                m = (off ** 2).sum(1) <= r ** 2
            for q in np.nonzero(m)[0]:
                key = tuple(idx[q])
                u = (s + t[q]) / n
                if key not in done or u > done[key][0]:
                    done[key] = (u, cen[q])
        keys = list(done.keys())
        if not keys:
            return
        self._set(bone, np.array(keys), np.array([done[k][1] for k in keys]), color, us=np.array([done[k][0] for k in keys]), mode=mode)

    def sheet(self, bone, fn, color, nu=None, nv=None, thick=1, mode='fill'):
        """A thin sheet: fn(u, v) -> point. Every pixel the sheet passes through is filled (thick = layers)."""
        # sample densely enough to never skip a pixel
        probe = [np.asarray(fn(u, v)) for u in (0, 0.5, 1) for v in (0, 0.5, 1)]
        span = max(np.linalg.norm(probe[0] - probe[2]), np.linalg.norm(probe[0] - probe[6]), np.linalg.norm(probe[2] - probe[8]), 1e-3)
        nu = nu or int(span / self.px * 2.5) + 2
        nv = nv or int(span / self.px * 2.5) + 2
        done = {}
        for i in range(nu + 1):
            for j in range(nv + 1):
                p = np.asarray(fn(i / nu, j / nv), dtype=float)
                key = tuple(np.floor(p / self.px).astype(int))
                done[key] = (i / nu, p)
                if thick > 1:
                    for dx in range(-(thick // 2), thick - thick // 2):
                        for ax in range(3):
                            k2 = list(key); k2[ax] += dx
                            done.setdefault(tuple(k2), (i / nu, p))
        keys = list(done.keys())
        cen = (np.array(keys) + 0.5) * self.px
        self._set(bone, np.array(keys), cen, color, us=np.array([done[k][0] for k in keys]), mode=mode)

    def mirror(self, bone_from, bone_to=None):
        """Copy a bone's pixels to the other side (x -> -x). Pixel i maps to -i-1."""
        src = self.cells[bone_from]
        dst = self.cells[bone_to or bone_from]
        for (i, j, k), c in list(src.items()):
            dst[(-i - 1, j, k)] = c

    def retex(self, bones, match, fn):
        """Repaint pixels whose colour is in match: fn(centre, colour) -> new colour (or None to keep)."""
        match = {tuple(_col(m)) for m in match}
        for b in bones:
            cells = self.cells.get(b, {})
            for key, c in cells.items():
                if tuple(c) in match:
                    n = fn((np.asarray(key) + 0.5) * self.px, c)
                    if n is not None:
                        cells[key] = _col(n)

    def count(self):
        return sum(len(c) for c in self.cells.values())

    # ---- to faces ----
    def to_mesh(self):
        p = self.px
        rng = np.random.RandomState(self.seed)
        for bone, cells in self.cells.items():
            if not cells:
                continue
            if self.noise > 0:
                # a little Minecraft-texture speckle, in steps so faces still merge into rectangles
                noisy = {}
                for key, c in cells.items():
                    h = (key[0] * 73856093 ^ key[1] * 19349663 ^ key[2] * 83492791) & 0xFFFF
                    f = 1.0 + self.noise * (((h % 3) - 1))
                    noisy[key] = tuple(max(0, min(255, int(c[q] * f))) for q in range(3)) + tuple(c[3:])
                cells = noisy
            for axis in range(3):
                for sgn in (1, -1):
                    nrm = [0.0, 0.0, 0.0]
                    nrm[axis] = float(sgn)
                    # group exposed faces by slice
                    slices = {}
                    for key, c in cells.items():
                        nb = list(key); nb[axis] += sgn
                        if tuple(nb) in cells:
                            continue
                        a1, a2 = [a for a in range(3) if a != axis]
                        slices.setdefault(key[axis], {})[(key[a1], key[a2])] = c
                    for layer, faces in slices.items():
                        a1, a2 = [a for a in range(3) if a != axis]
                        used = set()
                        for (x, y) in sorted(faces.keys()):
                            if (x, y) in used:
                                continue
                            c = faces[(x, y)]
                            w = 1
                            while (x + w, y) in faces and (x + w, y) not in used and faces[(x + w, y)] == c:
                                w += 1
                            h = 1
                            while all((x + q, y + h) in faces and (x + q, y + h) not in used and faces[(x + q, y + h)] == c for q in range(w)):
                                h += 1
                            for q in range(w):
                                for r in range(h):
                                    used.add((x + q, y + r))
                            plane = (layer + (1 if sgn > 0 else 0)) * p
                            corners = []
                            for (u, v) in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
                                pt = [0.0, 0.0, 0.0]
                                pt[axis] = plane
                                pt[a1] = u * p
                                pt[a2] = v * p
                                corners.append(np.array(pt))
                            # wind so the face points along the normal
                            e1, e2 = corners[1] - corners[0], corners[3] - corners[0]
                            if np.dot(np.cross(e1, e2), nrm) < 0:
                                corners = [corners[0], corners[3], corners[2], corners[1]]
                            self.mesh.quad(bone, corners, [np.array(nrm)] * 4, [c] * 4)
        return self.mesh


def _lerp(values, t):
    if not isinstance(values, (list, tuple)):
        return values
    x = t * (len(values) - 1)
    i = min(int(x), len(values) - 2)
    f = x - i
    return values[i] * (1 - f) + values[i + 1] * f
