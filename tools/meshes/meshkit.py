"""Smooth mesh building blocks for the mod's non-blocky models (tools/meshes/gen_meshes.py uses them).

Everything is in blocks: y is up, the model stands on y = 0 and faces -z (its front).
Shapes are made of many small four-cornered faces with smooth normals, so Minecraft's own entity
lighting shades them like round surfaces. Colours live on the vertices (a plain white texture is used).

Output (MeshFile.write) is the binary format read by com.onepiecemod.mesh.client.MeshModel:
  int magic 0x4F504D31 ('OPM1'), float scale, int boneCount
  per bone: UTF name, int parent (-1 = root), float px py pz (pivot),
            int animCount, per anim: byte state (0 idle, 1 walk, 2 attack, 3 roar, 4 fly), byte axis (0 x, 1 y, 2 z, 3 move y),
                                     float amplitude (degrees, or blocks for axis 3), float period (s; walk: cycles), float phase (radians)
            int quadCount, per quad 4 x (float x y z, byte nx ny nz (x127), int argb)
"""
import math
import struct

import numpy as np


# ---------------- colours ----------------

def hexc(s):
    if not isinstance(s, str):
        return tuple(s[:3])
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, f):
    return tuple(max(0, min(255, int(c[i] * f))) for i in range(3))


def const(c):
    c = hexc(c) if isinstance(c, str) else c
    return lambda p, n, u, v: c


def gloss(base, hi='#9aa4b8', power=6.0, amount=0.45):
    """A glossy black/obsidian look: lighter where the surface faces up and towards the front-left light."""
    base, hi = hexc(base), hexc(hi)
    L = np.array([-0.35, 0.8, -0.5]); L = L / np.linalg.norm(L)

    def f(p, n, u, v):
        s = max(0.0, float(np.dot(n, L))) ** power
        return mix(base, hi, s * amount)
    return f


# ---------------- maths ----------------

def norm(v):
    v = np.asarray(v, dtype=float)
    l = np.linalg.norm(v)
    return v / l if l > 1e-9 else v


def rot_matrix(rx=0.0, ry=0.0, rz=0.0):
    """Rotation by angles in degrees, applied x then y then z."""
    rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Z @ Y @ X


def catmull(points, per=6):
    """A smooth curve through the control points (Catmull-Rom), as a list of points."""
    P = [np.asarray(p, dtype=float) for p in points]
    if len(P) < 3:
        return P
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return out


def lerp_list(values, t):
    """Value at t (0..1) along evenly spaced values."""
    if not isinstance(values, (list, tuple)):
        return values
    x = t * (len(values) - 1)
    i = min(int(x), len(values) - 2)
    f = x - i
    return values[i] * (1 - f) + values[i + 1] * f


# ---------------- the mesh ----------------

class Mesh:
    def __init__(self, scale=1.0):
        self.scale = scale
        self.bones = []          # (name, parent, pivot)
        self.index = {}
        self.anims = {}          # bone -> list of (state, axis, amp, period, phase)
        self.quads = {}          # bone -> list of quads; quad = 4 x (p, n, rgb)
        self.bone('root', None, (0, 0, 0))

    # ---- skeleton ----
    def bone(self, name, parent, pivot):
        self.index[name] = len(self.bones)
        self.bones.append((name, parent, tuple(float(x) for x in pivot)))
        self.anims[name] = []
        self.quads[name] = []
        return name

    def anim(self, bone, state, axis, amp, period=1.0, phase=0.0):
        states = {'idle': 0, 'walk': 1, 'attack': 2, 'roar': 3, 'fly': 4, 'rest': 5, 'look': 6}
        axes = {'x': 0, 'y': 1, 'z': 2, 'up': 3}
        self.anims[bone].append((states[state], axes[axis], float(amp), float(period), float(phase)))

    # ---- raw faces ----
    def quad(self, bone, ps, ns, cs):
        self.quads[bone].append(list(zip(ps, ns, cs)))

    def grid(self, bone, P, N, color, flip=False):
        """P, N: arrays [nu+1][nv+1][3]; color(p, n, u, v) -> rgb."""
        nu, nv = len(P) - 1, len(P[0]) - 1
        C = [[color(P[i][j], N[i][j], i / nu, j / nv) for j in range(nv + 1)] for i in range(nu + 1)]
        for i in range(nu):
            for j in range(nv):
                idx = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                if flip:
                    idx.reverse()
                self.quad(bone, [P[a][b] for a, b in idx], [N[a][b] for a, b in idx], [C[a][b] for a, b in idx])

    # ---- shapes ----
    def ellipsoid(self, bone, center, radii, color, rot=(0, 0, 0), nu=20, nv=14, squash_bottom=1.0):
        """A smooth egg/ball. radii = (rx, ry, rz); rot = degrees. squash_bottom < 1 flattens the lower half."""
        c = np.asarray(center, dtype=float)
        R = rot_matrix(*rot)
        rx, ry, rz = radii
        P, N = [], []
        for i in range(nu + 1):
            th = 2 * math.pi * i / nu
            rowp, rown = [], []
            for j in range(nv + 1):
                ph = math.pi * j / nv - math.pi / 2
                x, y, z = math.cos(ph) * math.sin(th), math.sin(ph), math.cos(ph) * -math.cos(th)
                yy = y * (squash_bottom if y < 0 else 1.0)
                p = np.array([x * rx, yy * ry, z * rz])
                n = norm(np.array([x / rx, yy / ry / (squash_bottom if y < 0 else 1.0), z / rz]))
                rowp.append(c + R @ p)
                rown.append(R @ n)
            P.append(rowp)
            N.append(rown)
        self.grid(bone, P, N, color)

    def sweep(self, bone, path, radius, color, sides=12, per=6, caps=True, flat=1.0, twist=0.0, smooth=True, hint=None):
        """A tube along a curve. radius = number or list (start..end). flat < 1 squashes it into a band
        (for blades and straps). color gets u = along (0..1), v = around (0..1)."""
        pts = catmull(path, per) if smooth and len(path) > 2 else [np.asarray(p, dtype=float) for p in path]
        if len(pts) < 2:
            return
        # parallel-transport frames
        T = [norm(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]) for i in range(len(pts))]
        if hint is not None:
            h = np.asarray(hint, dtype=float)
            Nf = [norm(h - T[0] * np.dot(h, T[0]))]
        else:
            up = np.array([0, 1, 0]) if abs(T[0][1]) < 0.9 else np.array([1, 0, 0])
            Nf = [norm(np.cross(np.cross(T[0], up), T[0]))]
        for i in range(1, len(pts)):
            b = np.cross(T[i - 1], T[i])
            if np.linalg.norm(b) < 1e-8:
                Nf.append(Nf[-1])
            else:
                b = norm(b)
                ang = math.acos(max(-1.0, min(1.0, float(np.dot(T[i - 1], T[i])))))
                n = Nf[-1]
                n = n * math.cos(ang) + np.cross(b, n) * math.sin(ang) + b * np.dot(b, n) * (1 - math.cos(ang))
                Nf.append(norm(n))
        P, N = [], []
        L = len(pts) - 1
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides
            colp, coln = [], []
            for i, p in enumerate(pts):
                t = i / L
                r = lerp_list(radius, t)
                aa = a + twist * t
                n0 = Nf[i]
                b0 = np.cross(T[i], n0)
                off = n0 * math.cos(aa) * r + b0 * math.sin(aa) * r * flat
                nn = norm(n0 * math.cos(aa) * flat + b0 * math.sin(aa))
                colp.append(p + off)
                coln.append(nn)
            P.append(colp)
            N.append(coln)
        # grid wants [u][v]: u around? we want color u=along, v=around
        PP = [[P[k][i] for k in range(sides + 1)] for i in range(len(pts))]
        NN = [[N[k][i] for k in range(sides + 1)] for i in range(len(pts))]
        self.grid(bone, PP, NN, lambda p, n, u, v: color(p, n, u, v), flip=True)
        if caps:
            for end, t, sgn in ((pts[0], 0.0, -1), (pts[-1], 1.0, 1)):
                r = lerp_list(radius, t)
                if r < 1e-4:
                    continue
                idx = 0 if t == 0 else len(pts) - 1
                ring = [PP[idx][k] for k in range(sides + 1)]
                nrm = T[idx] * sgn
                col = color(end, nrm, t, 0)
                for k in range(sides):
                    q = [end, ring[k], ring[k + 1], ring[k + 1]] if sgn > 0 else [end, ring[k + 1], ring[k], ring[k]]
                    self.quad(bone, q, [nrm] * 4, [col] * 4)

    def surface(self, bone, fn, nu, nv, color, thick=0.0):
        """Any surface: fn(u, v) -> point for u, v in 0..1. thick > 0 adds a back sheet offset along the normal."""
        P = [[np.asarray(fn(i / nu, j / nv), dtype=float) for j in range(nv + 1)] for i in range(nu + 1)]
        N = []
        for i in range(nu + 1):
            row = []
            for j in range(nv + 1):
                du = P[min(i + 1, nu)][j] - P[max(i - 1, 0)][j]
                dv = P[i][min(j + 1, nv)] - P[i][max(j - 1, 0)]
                row.append(norm(np.cross(du, dv)))
            N.append(row)
        self.grid(bone, P, N, color)
        if thick > 0:
            P2 = [[P[i][j] - N[i][j] * thick for j in range(nv + 1)] for i in range(nu + 1)]
            N2 = [[-N[i][j] for j in range(nv + 1)] for i in range(nu + 1)]
            self.grid(bone, P2, N2, color, flip=True)

    def loft(self, bone, rings, color, sides=20, per=4, caps=True):
        """A body made of horizontal-ish rings, smoothed between them (torsos, robes, heads).
        rings: list of (y, rx, rz_front, rz_back, cz) or with a 6th value cx. Front is -z."""
        R = [list(r) + [0.0] * (6 - len(r)) for r in rings]
        pts = catmull([np.array(r, dtype=float) for r in R], per)
        P, N = [], []
        for r in pts:
            y, rx, rzf, rzb, cz, cx = r
            row = []
            for k in range(sides + 1):
                a = 2 * math.pi * k / sides
                sx, cz_ = math.sin(a), -math.cos(a)
                rz = rzf if cz_ < 0 else rzb
                row.append(np.array([cx + sx * rx, y, cz + cz_ * rz]))
            P.append(row)
        nu = len(P) - 1
        for i in range(nu + 1):
            row = []
            for k in range(sides + 1):
                du = P[min(i + 1, nu)][k] - P[max(i - 1, 0)][k]
                dv = P[i][(k + 1) % sides] - P[i][(k - 1) % sides]
                n = norm(np.cross(dv, du))
                c = np.array([pts[i][5], pts[i][0], pts[i][4]])
                if np.dot(n, P[i][k] - c) < 0:
                    n = -n
                row.append(n)
            N.append(row)
        self.grid(bone, P, N, color)
        if caps:
            for i, sgn in ((0, -1), (nu, 1)):
                y, rx, rzf, rzb, cz, cx = pts[i]
                c = np.array([cx, y, cz]); n = np.array([0, sgn, 0.0])
                for k in range(sides):
                    col = color(c, n, i / max(nu, 1), 0)
                    self.quad(bone, [c, P[i][k], P[i][k + 1], P[i][k + 1]], [n] * 4, [col] * 4)

    def disc(self, bone, center, normal, r, color, segs=16, r_in=0.0):
        """A flat round disc (or ring when r_in > 0) facing along normal (eyes, rims, brims)."""
        c = np.asarray(center, dtype=float); n = norm(normal)
        a = norm(np.cross(n, [0, 1, 0])) if abs(n[1]) < 0.9 else norm(np.cross(n, [1, 0, 0]))
        b = np.cross(n, a)
        for k in range(segs):
            t0, t1 = 2 * math.pi * k / segs, 2 * math.pi * (k + 1) / segs
            o0, o1 = a * math.cos(t0) + b * math.sin(t0), a * math.cos(t1) + b * math.sin(t1)
            q = [c + o0 * r_in, c + o0 * r, c + o1 * r, c + o1 * r_in]
            col = color(c, n, k / segs, 0)
            self.quad(bone, q, [n] * 4, [col] * 4)

    def cone(self, bone, base, tip, r, color, sides=8):
        self.sweep(bone, [base, tip], [r, 0.0], color, sides=sides, smooth=False)

    # ---- output ----
    def count(self):
        return sum(len(q) for q in self.quads.values())

    def write(self, path):
        out = bytearray()
        out += struct.pack('>ifi', 0x4F504D31, self.scale, len(self.bones))
        for name, parent, pivot in self.bones:
            b = name.encode('utf-8')
            out += struct.pack('>H', len(b)) + b
            out += struct.pack('>i', -1 if parent is None else self.index[parent])
            out += struct.pack('>fff', *pivot)
            out += struct.pack('>i', len(self.anims[name]))
            for st, ax, amp, per, ph in self.anims[name]:
                out += struct.pack('>bbfff', st, ax, amp, per, ph)
            quads = self.quads[name]
            out += struct.pack('>i', len(quads))
            for q in quads:
                for p, n, c in q:
                    nb = [max(-127, min(127, int(round(x * 127)))) for x in norm(n)]
                    a = 0xFE if len(c) > 3 and c[3] else 0xFF
                    argb = (a << 24) | (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])
                    if argb >= 1 << 31:
                        argb -= 1 << 32
                    out += struct.pack('>fffbbbi', float(p[0]), float(p[1]), float(p[2]), nb[0], nb[1], nb[2], argb)
        with open(path, 'wb') as f:
            f.write(out)
        return len(out)
