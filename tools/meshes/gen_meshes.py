"""Makes the smooth (non-blocky) models for the chapter 1191/1198 transformations, drawn by
com.onepiecemod.mesh.client.MeshForms:

  imu_demon      Imu's devil form (boss phase 2): dark muscled body, long pale hair, red ringed eyes,
                 curled horns + a bigger upper pair, goatee, horned skulls, tail, black feathered wings,
                 a ring of black flames with 16 eyes behind the head.
  imu_beast      Imu's chapter 1198 form (boss phase 3): very tall, black neck column with white dots,
                 huge crescent horns with a white flame between, a robe of long white strands open at the
                 front over a black body with a skull and an eye, a long straight blade, dark feathered
                 wings, black smoke wisps with ringed eyes floating round.
  nika_wild      Luffy's black cloud Nika (player, Gear 5 again in Gear 5): black body, white cloud swirls on
                 the arms, a head of white cloud puffs with a huge black grin of zigzag teeth, black gloved
                 hands, a tail.
  nidhogg        Loki's Nidhogg hybrid (boss form; players with the fruit get it smaller): huge glossy black
                 muscles, lighter belly, big curved horns, a crown of spikes, a wild white mane, a grid-tooth
                 grin, an ornate chest band and belt, white fur trim, studded cuffs, claws, dragon legs with
                 talons, bat wings, a tail, and the hammer Ragnir.
  character/loki Loki's own look: a giant with light magenta hair (two thick braids in front), a wide-rimmed
                 black helmet with long black horns (the left one wrapped), bandaged eyes, Viking clothes,
                 Ragnir.

Run: python3 tools/meshes/gen_meshes.py [--preview DIR]   (from the repo root)
"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshkit import Mesh, hexc, mix, shade, const, gloss, norm, rot_matrix  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'main', 'resources', 'assets', 'onepiece', 'meshes')

V = np.array
SIDES = (1, -1)  # +1 = the model's right (+x), -1 = its left


def glow(c):
    c = hexc(c) if isinstance(c, str) else c
    return lambda p, n, u, v: (c[0], c[1], c[2], 1)


def sx(p, s):
    """Mirror a point to side s (points are written for the right side, +x)."""
    return V([p[0] * s, p[1], p[2]], dtype=float)


# ---------------- shared parts ----------------

def ring_eye(m, bone, center, normal, r, rings, lit=True):
    """Concentric discs, outermost first: rings = list of (fraction of r, colour)."""
    n = norm(normal)
    for k, (f, c) in enumerate(rings):
        col = glow(c) if lit else const(c)
        m.disc(bone, V(center) + n * (0.004 + 0.004 * k) * max(r * 6, 1), n, r * f, col, segs=18)


def head_z(hc, r):
    """Front surface of a round head: z for (x, y)."""
    def f(x, y):
        d = r * r - (x - hc[0]) ** 2 - (y - hc[1]) ** 2
        return hc[2] - math.sqrt(max(d, r * r * 0.05))
    return f


def grin(m, bone, cx, cy, w, h, zf, mouth='#120a0c', tooth='#f4f2ea', n=9, zig=True, grid=False, lift=0.0):
    """A wide grin on a curved face: top/bottom lips meet at the corners, which curl up.
    zig: sharp interlocking teeth. grid: square teeth in two rows with dark gaps (Loki)."""
    def top(x):
        s = (x - cx) / w
        return cy + h * (0.25 + 0.75 * s * s) + lift * s * s

    def bot(x):
        s = (x - cx) / w
        return cy + h * (-0.75 + 1.75 * s * s) + lift * s * s
    e = 0.004 + w * 0.01
    m.surface(bone, lambda u, v: V([cx + (u * 2 - 1) * w, bot(cx + (u * 2 - 1) * w) * (1 - v) + top(cx + (u * 2 - 1) * w) * v,
                                     zf(cx + (u * 2 - 1) * w, cy) - e]), 16, 3, const(mouth))
    tcol = const(tooth)
    if zig:
        step = 2 * w / n
        for i in range(n):
            x = cx - w + step * (i + 0.5)
            s = abs((x - cx) / w)
            if s > 0.93:
                continue
            mid = (top(x) + bot(x)) / 2
            depth = (top(x) - bot(x))
            z = zf(x, cy) - e * 2
            # upper tooth: base on the top lip, tip just past the middle
            m.surface(bone, (lambda x=x, z=z, mid=mid, depth=depth: lambda u, v: V([
                x + (u - 0.5) * step * (1 - v), top(x) * (1 - v) + (mid - depth * 0.12) * v, z]))(), 2, 2, tcol)
            x2 = x + step / 2
            if abs((x2 - cx) / w) < 0.9:
                mid2 = (top(x2) + bot(x2)) / 2
                depth2 = top(x2) - bot(x2)
                m.surface(bone, (lambda x2=x2, z=z, mid2=mid2, depth2=depth2: lambda u, v: V([
                    x2 + (u - 0.5) * step * (1 - v), bot(x2) * (1 - v) + (mid2 + depth2 * 0.12) * v, z - e]))(), 2, 2, tcol)
    if grid:
        step = 2 * w / n
        for row in (0, 1):
            for i in range(n):
                x0, x1 = cx - w + step * (i + 0.12), cx - w + step * (i + 0.88)
                xm = (x0 + x1) / 2
                if abs((xm - cx) / w) > 0.9:
                    continue
                mid = (top(xm) + bot(xm)) / 2
                y0, y1 = (mid + 0.02 * h, top(xm) - 0.05 * h) if row == 0 else (bot(xm) + 0.05 * h, mid - 0.02 * h)
                z = zf(xm, cy) - e * 2
                m.surface(bone, (lambda x0=x0, x1=x1, y0=y0, y1=y1, z=z: lambda u, v: V([x0 + (x1 - x0) * u, y0 + (y1 - y0) * v, z]))(),
                          1, 1, tcol)


def hand(m, bone, wrist, s, k, skin, claw=None, fingers=4, curl=0.6, nail=None, thumb=True):
    """A hand hanging down from the wrist, palm facing the body. k = size (1 = about a person's hand)."""
    w = V(wrist, dtype=float)
    pc = w + V([0, -0.07 * k, -0.01 * k])
    m.ellipsoid(bone, pc, (0.045 * k, 0.075 * k, 0.065 * k), skin, nu=14, nv=10)
    for i in range(fingers):
        zf = (-0.045 + 0.09 * i / max(fingers - 1, 1)) * k
        base = pc + V([0.005 * s * k, -0.06 * k, zf])
        L = (0.085 - 0.012 * abs(i - 1.3)) * k
        mid = base + V([-s * 0.01 * k, -L * 0.6, -0.005 * k])
        tip = mid + V([-s * 0.03 * k * curl, -L * 0.55 * (1 - curl * 0.4), -0.01 * k])
        m.sweep(bone, [base, mid, tip], [0.016 * k, 0.014 * k, 0.011 * k], skin, sides=8, per=3)
        if claw:
            d = norm(tip - mid)
            m.sweep(bone, [tip, tip + d * 0.045 * k + V([-s * 0.012 * k, -0.01 * k, 0])], [0.011 * k, 0.0], claw, sides=6, smooth=False)
    if thumb:
        tb = pc + V([-s * 0.03 * k, -0.01 * k, -0.05 * k])
        tt = tb + V([-s * 0.02 * k, -0.06 * k, -0.025 * k])
        m.sweep(bone, [tb, tt], [0.018 * k, 0.013 * k], skin, sides=8, smooth=False)
        if claw:
            m.sweep(bone, [tt, tt + V([-s * 0.01 * k, -0.04 * k, -0.01 * k])], [0.012 * k, 0.0], claw, sides=6, smooth=False)


def feather_wing(m, bone, s, root, span, dark, sheen, count=(9, 11, 12), droop=0.25, back=0.0):
    """A big bird wing made of overlapping flat feathers, spreading out to side s and up.
    The feathers lie roughly in the x-y plane (the wing's flat face points backwards)."""
    r = V(root, dtype=float)
    lead = [r, r + V([s * span * 0.3, span * 0.28, back + 0.05]), r + V([s * span * 0.65, span * 0.42, back + 0.1]),
            r + V([s * span * 1.0, span * 0.30, back + 0.12])]
    from meshkit import catmull
    edge = catmull(lead, 10)
    m.sweep(bone, lead, [span * 0.05, span * 0.04, span * 0.03, span * 0.012], gloss(dark, sheen, 4, 0.5), sides=8, per=5)

    def at(t):
        return edge[min(int(t * (len(edge) - 1)), len(edge) - 1)]
    layers = [(count[0], 0.28, 0.035, 0.06), (count[1], 0.55, 0.05, 0.03), (count[2], 0.95, 0.07, 0.0)]
    for li, (n, lf, wf, dz) in enumerate(layers):
        for i in range(n):
            t = (i + 0.5) / n
            if li == 2:
                t = 0.35 + 0.65 * t  # primaries sit on the outer half
            base = at(t) + V([0, 0, dz + back * 0.0 + 0.01 * li])
            ang = math.radians(-90 + 70 * t ** 1.4)  # straight down at the body, out-and-down at the tip
            d = norm(V([s * math.cos(ang) * -1 * -1 if False else s * math.cos(ang + math.pi / 2 - math.pi / 2), math.sin(ang), 0.0]))
            d = norm(V([s * (math.cos(ang)), math.sin(ang), 0.02]))
            L = span * lf * (0.55 + 0.6 * t if li == 2 else 0.7 + 0.35 * t) * (1.0 - droop * (1 - t) * 0.5)
            wid = span * wf * (0.8 + 0.4 * t)
            tip = base + d * L
            mid = base + d * L * 0.55 + V([0, 0, 0.02 * span])
            hint = np.cross(V([0, 0, 1.0]), d)
            c = gloss(mix(hexc(dark), hexc(sheen), 0.12 * li) if isinstance(dark, str) else dark, sheen, 5, 0.35 + 0.1 * li)
            m.sweep(bone, [base, mid, tip], [wid * 0.55, wid, wid * 0.45], c, sides=6, per=3, flat=0.12, hint=hint)


def bat_wing(m, bone, s, root, scale, bone_col, skin_col):
    """A dragon/bat wing: an arm with long fingers and a thin skin stretched between them."""
    k = scale
    r = V(root, dtype=float)
    elbow = r + V([s * 1.6 * k, 1.3 * k, 1.1 * k])
    wrist = r + V([s * 3.3 * k, 2.0 * k, 1.0 * k])
    tips = [r + V([s * 6.4 * k, 1.3 * k, 1.4 * k]), r + V([s * 6.0 * k, -1.2 * k, 1.7 * k]),
            r + V([s * 4.6 * k, -3.0 * k, 1.6 * k]), r + V([s * 2.6 * k, -3.6 * k, 1.2 * k])]
    body_edge = r + V([s * 0.2 * k, -3.2 * k, 0.2 * k])
    bc = gloss(bone_col, '#8890a0', 5, 0.5)
    m.sweep(bone, [r, elbow, wrist], [0.32 * k, 0.24 * k, 0.18 * k], bc, sides=10, per=4)
    m.ellipsoid(bone, wrist, (0.2 * k, 0.2 * k, 0.2 * k), bc, nu=10, nv=8)
    m.cone(bone, wrist + V([0, 0.1 * k, 0]), wrist + V([s * 0.3 * k, 0.9 * k, -0.2 * k]), 0.12 * k, const('#d8d0c0'))
    fingers = []
    for t in tips:
        mid = wrist + (t - wrist) * 0.5 + V([0, 0.15 * k, 0.1 * k])
        m.sweep(bone, [wrist, mid, t], [0.12 * k, 0.08 * k, 0.03 * k], bc, sides=8, per=4)
        fingers.append((wrist, mid, t))

    def along(f, v):
        a, b, c = f
        return a + (b - a) * (v * 2) if v < 0.5 else b + (c - b) * (v * 2 - 1)
    skin = lambda p, n, u, v: mix(hexc(skin_col), hexc('#4a1e22'), 0.35 * (1 - v))
    edges = [[r, elbow, wrist]] + []
    # skin between neighbouring fingers, scalloped at the trailing edge
    for i in range(len(fingers) - 1):
        fa, fb = fingers[i], fingers[i + 1]

        def fn(u, v, fa=fa, fb=fb):
            pa, pb = along(fa, v), along(fb, v)
            p = pa * (1 - u) + pb * u
            pull = math.sin(math.pi * u) * v ** 1.5 * 0.35
            p = p + (wrist - p) * pull
            return p + V([0, 0, 0.04 * k * math.sin(math.pi * u)])
        m.surface(bone, fn, 8, 10, skin)
    # skin from the last finger back to the body
    fl = fingers[-1]

    def fn2(u, v):
        pa = along(fl, v)
        pb = r + (body_edge - r) * v
        p = pa * (1 - u) + pb * u
        pull = math.sin(math.pi * u) * v ** 1.5 * 0.25
        return p + (r + (wrist - r) * 0.4 - p) * pull
    m.surface(bone, fn2, 8, 10, skin)
    # and the front skin from the arm to the first finger
    fa = fingers[0]

    def fn3(u, v):
        pa = r + (wrist - r) * v + V([0, 0.25 * k * math.sin(math.pi * v), 0])
        pb = along(fa, v)
        return pa * (1 - u * 0.25) + pb * (u * 0.25)
    m.surface(bone, fn3, 3, 8, skin)


def hammer(m, bone, top, bottom, k, handle='#3a2a1e', band='#f0eee6', head='#2a2a30', rim='#c8a860'):
    """Ragnir: a long handle wrapped in white bands and a big rounded hammer head at the bottom end."""
    top, bottom = V(top, dtype=float), V(bottom, dtype=float)
    d = norm(bottom - top)
    L = np.linalg.norm(bottom - top)
    m.sweep(bone, [top, bottom], [0.09 * k, 0.1 * k], const(handle), sides=10, smooth=False)
    nb = 9
    for i in range(nb):
        c = top + d * L * (0.08 + 0.75 * i / nb)
        m.sweep(bone, [c, c + d * L * 0.05], [0.12 * k, 0.12 * k], const(band), sides=10, smooth=False)
    m.ellipsoid(bone, top - d * 0.1 * k, (0.15 * k, 0.15 * k, 0.15 * k), const(rim), nu=10, nv=8)
    hc = bottom + d * 0.35 * k
    side = norm(np.cross(d, V([0, 0, 1.0])))
    a, b = hc - side * 0.75 * k, hc + side * 0.75 * k
    m.sweep(bone, [a, a + side * 0.12 * k, hc, b - side * 0.12 * k, b], [0.42 * k, 0.5 * k, 0.55 * k, 0.5 * k, 0.42 * k],
            gloss(head, '#a0a8b8', 5, 0.5), sides=16, per=3)
    for e, sg in ((a, -1), (b, 1)):
        m.disc(bone, e + side * sg * 0.005, side * sg, 0.44 * k, const(rim), segs=16)
        m.disc(bone, e + side * sg * 0.01, side * sg, 0.25 * k, const(head), segs=16)
    for t in (0.3, 0.7):
        c = a + (b - a) * t
        m.sweep(bone, [c, c + side * 0.08 * k], [0.57 * k, 0.57 * k], const(rim), sides=16, smooth=False)


def puffs(m, bone, centers, rmin, rmax, color, seed, nu=12, nv=9):
    rnd = random.Random(seed)
    for c in centers:
        r = rnd.uniform(rmin, rmax)
        m.ellipsoid(bone, c, (r, r * rnd.uniform(0.8, 1.0), r * rnd.uniform(0.85, 1.0)), color, nu=nu, nv=nv)


def humanoid_anims(m, arms=('arm_r', 'arm_l'), legs=('leg_r', 'leg_l'), body='body', head='head', walk_leg=28, walk_arm=22,
                   attack=110, roar_arms=45):
    m.anim(legs[0], 'walk', 'x', walk_leg, 1.0, 0.0)
    m.anim(legs[1], 'walk', 'x', walk_leg, 1.0, math.pi)
    m.anim(arms[0], 'walk', 'x', walk_arm, 1.0, math.pi)
    m.anim(arms[1], 'walk', 'x', walk_arm, 1.0, 0.0)
    m.anim(arms[0], 'idle', 'z', 2.5, 3.2, 0.0)
    m.anim(arms[1], 'idle', 'z', -2.5, 3.2, 0.0)
    m.anim(body, 'idle', 'x', 1.2, 3.2, 0.0)
    m.anim(head, 'look', 'y', 0.8)
    m.anim(head, 'look', 'x', 0.7)
    m.anim(arms[0], 'attack', 'x', attack)
    m.anim(body, 'attack', 'y', -18)
    m.anim(arms[0], 'roar', 'z', roar_arms)
    m.anim(arms[1], 'roar', 'z', -roar_arms)
    m.anim(head, 'roar', 'x', 25)


# ---------------- Luffy: black cloud Nika ----------------

def nika():
    m = Mesh(1.0)
    BLACK = '#141418'
    body_c = gloss(BLACK, '#7c8496', 6, 0.35)
    cloud = lambda p, n, u, v: mix(hexc('#ffffff'), hexc('#c9ccd6'), max(0.0, -n[1]) * 0.8 + 0.05)
    m.bone('body', 'root', (0, 1.05, 0))
    m.bone('head', 'body', (0, 1.86, 0))
    m.bone('arm_r', 'body', (0.29, 1.72, 0))
    m.bone('arm_l', 'body', (-0.29, 1.72, 0))
    m.bone('leg_r', 'root', (0.13, 1.02, 0))
    m.bone('leg_l', 'root', (-0.13, 1.02, 0))
    m.bone('tail', 'body', (0, 1.02, 0.12))
    humanoid_anims(m, attack=120, roar_arms=60)
    m.anim('tail', 'idle', 'y', 18, 1.6)
    m.anim('tail', 'walk', 'z', 10, 1.0)
    m.anim('body', 'idle', 'up', 0.02, 1.6)
    m.anim('head', 'idle', 'z', 4, 2.2)
    # torso: lanky
    m.loft('body', [(0.92, 0.19, 0.12, 0.13), (1.05, 0.2, 0.12, 0.13), (1.22, 0.165, 0.1, 0.11), (1.4, 0.19, 0.12, 0.11),
                    (1.58, 0.25, 0.14, 0.12), (1.72, 0.27, 0.11, 0.11), (1.8, 0.11, 0.08, 0.08), (1.9, 0.065, 0.06, 0.06)], body_c, sides=20)
    # a cloud scarf round the neck and shoulders, and a cloud sash at the waist
    sc = [V([math.sin(a) * 0.2, 1.8 + 0.03 * math.sin(a * 3), -math.cos(a) * 0.13]) for a in np.linspace(0, 2 * math.pi, 11)[:-1]]
    puffs(m, 'body', sc, 0.07, 0.1, cloud, 1)
    sash = [V([math.sin(a) * 0.21, 1.02, -math.cos(a) * 0.14]) for a in np.linspace(0, 2 * math.pi, 13)[:-1]]
    puffs(m, 'body', sash, 0.05, 0.075, cloud, 2)
    # legs
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        hip, knee, ank = sx((0.13, 1.0, 0), s), sx((0.14, 0.55, -0.03), s), sx((0.14, 0.1, 0.01), s)
        m.sweep(b, [hip, knee, ank], [0.1, 0.085, 0.07], body_c, sides=14, per=5)
        m.ellipsoid(b, sx((0.14, 0.05, -0.06), s), (0.065, 0.05, 0.13), body_c, nu=14, nv=8)
        # cloud swirls round the ankles
        puffs(m, b, [sx((0.14 + 0.07 * math.sin(a), 0.16, -0.07 * math.cos(a)), s) for a in np.linspace(0, 6.28, 6)[:-1]], 0.035, 0.05, cloud, 3 + s)
    # arms with white cloud-swirl markings (spiralling bands, puffy at the edges)
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((0.29, 1.72, 0), s), sx((0.36, 1.38, 0.02), s), sx((0.38, 1.06, -0.02), s)
        def armcol(p, n, u, v):
            band = math.sin(2 * math.pi * (u * 3.2 + v * 1.0 + 0.15))
            return (245, 245, 248) if band > 0.55 else hexc(BLACK) if band < 0.35 else (150, 152, 160)
        m.ellipsoid(b, sx((0.3, 1.69, 0), s), (0.1, 0.09, 0.1), body_c, nu=14, nv=10)
        m.sweep(b, [sh, el, wr], [0.075, 0.07, 0.06, 0.05], armcol, sides=16, per=8)
        for t in (0.2, 0.5, 0.8):
            c = sh + (wr - sh) * t
            m.ellipsoid(b, c + V([s * 0.06, 0.02, -0.04]), (0.035, 0.03, 0.035), cloud, nu=10, nv=7)
        # black glove hands, big and cartoony
        hand(m, b, wr + V([0, 0.01, 0]), s, 1.35, gloss('#0c0c10', '#6c7488', 5, 0.4))
        m.sweep(b, [wr + V([0, 0.03, 0]), wr + V([0, -0.04, 0])], [0.07, 0.068], const('#0c0c10'), sides=14, smooth=False)
    # head: a mass of white cloud puffs, with eyes and a huge black zigzag grin in front
    hc = V([0, 2.08, 0])
    m.ellipsoid('head', hc, (0.2, 0.22, 0.2), cloud, nu=20, nv=14)
    rnd = random.Random(7)
    pts = []
    for i in range(34):
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(-0.3, 1.0)
        d = V([math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)])
        if d[2] < -0.55 and d[1] < 0.5:
            continue  # keep the face clear
        pts.append(hc + d * 0.2 * V([1.15, 1.05, 1.1]) + V([0, 0.03, 0]))
    puffs(m, 'head', pts, 0.08, 0.13, cloud, 8)
    # the big ponytail-like cloud plume at the back
    puffs(m, 'head', [hc + V([0.12 * math.sin(t * 3), 0.1 + t * 0.12, 0.2 + t * 0.22]) for t in np.linspace(0, 1, 6)], 0.07, 0.11, cloud, 9)
    zf = head_z(hc, 0.205)
    grin(m, 'head', 0, 2.0, 0.16, 0.06, zf, mouth='#050506', tooth='#ffffff', n=8, zig=True, lift=0.03)
    # eyes: black almonds with white glowing ringed pupils, and red rims like Gear 5
    for s in SIDES:
        ex, ey = 0.075 * s, 2.13
        nrm = norm(V([ex, ey - hc[1], zf(ex, ey) - hc[2]]))
        m.ellipsoid('head', V([ex, ey, zf(ex, ey) + 0.01]), (0.045, 0.03, 0.015), const('#050506'), nu=10, nv=6)
        ring_eye(m, 'head', V([ex, ey, zf(ex, ey) - 0.005]), nrm, 0.024, [(1.0, '#ff3a3a'), (0.7, '#ffffff'), (0.25, '#101010')])
    # ape nose: a small rounded snout bump
    m.ellipsoid('head', V([0, 2.075, zf(0, 2.075) + 0.01]), (0.045, 0.03, 0.035), cloud, nu=10, nv=7)
    m.ellipsoid('head', V([0.016, 2.07, zf(0, 2.07) - 0.018]), (0.008, 0.006, 0.006), const('#202024'), nu=6, nv=4)
    m.ellipsoid('head', V([-0.016, 2.07, zf(0, 2.07) - 0.018]), (0.008, 0.006, 0.006), const('#202024'), nu=6, nv=4)
    # tail: curls up behind, cloud puff at the tip
    tp = [V([0, 1.0, 0.12]), V([0, 0.85, 0.35]), V([0.05, 1.0, 0.6]), V([0.1, 1.35, 0.62]), V([0.06, 1.55, 0.5])]
    m.sweep('tail', tp, [0.05, 0.045, 0.04, 0.03, 0.02], body_c, sides=10, per=5)
    puffs(m, 'tail', [V([0.06, 1.58, 0.48]), V([0.0, 1.62, 0.52]), V([0.1, 1.62, 0.45])], 0.05, 0.07, cloud, 10)
    return m


# ---------------- Imu: devil form (phase 2) ----------------

def imu_demon():
    m = Mesh(1.0)
    SKIN = '#3a3444'
    skin = gloss(SKIN, '#8a80a0', 4, 0.45)
    HAIR = '#e4dfee'
    hair = lambda p, n, u, v: mix(hexc(HAIR), hexc('#9a92b0'), 0.15 + 0.5 * u)
    cloak = lambda p, n, u, v: mix(hexc('#1c1822'), hexc('#3a3046'), max(0.0, n[1]) * 0.6 + 0.2)
    trousers = lambda p, n, u, v: mix(hexc('#241c2a'), hexc('#44384e'), max(0.0, n[1]) * 0.5 + 0.15)
    bone_c = lambda p, n, u, v: mix(hexc('#efe8d8'), hexc('#a89c88'), max(0.0, -n[1]) * 0.7)
    m.bone('body', 'root', (0, 2.45, 0))
    m.bone('head', 'body', (0, 4.35, -0.05))
    m.bone('arm_r', 'body', (0.78, 4.05, 0))
    m.bone('arm_l', 'body', (-0.78, 4.05, 0))
    m.bone('leg_r', 'root', (0.3, 2.4, 0))
    m.bone('leg_l', 'root', (-0.3, 2.4, 0))
    m.bone('tail', 'body', (0, 2.45, 0.35))
    m.bone('wing_r', 'body', (0.3, 3.95, 0.45))
    m.bone('wing_l', 'body', (-0.3, 3.95, 0.45))
    m.bone('halo', 'head', (0, 4.75, 0.55))
    humanoid_anims(m, walk_leg=22, walk_arm=16, attack=115, roar_arms=50)
    m.anim('tail', 'idle', 'y', 14, 2.4)
    m.anim('tail', 'walk', 'y', 10, 1.0)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        m.anim(b, 'idle', 'z', 6 * s, 3.0)
        m.anim(b, 'roar', 'z', 25 * s)
        m.anim(b, 'fly', 'z', 30 * s, 0.9)
    m.anim('halo', 'idle', 'z', 8, 6.0)
    # legs in dark trousers, clawed bare feet
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        hip, knee, ank = sx((0.3, 2.4, 0), s), sx((0.34, 1.25, -0.08), s), sx((0.33, 0.2, 0.02), s)
        m.sweep(b, [hip, knee, ank], [0.27, 0.22, 0.2, 0.15], trousers, sides=16, per=5)
        m.ellipsoid(b, sx((0.33, 0.1, -0.12), s), (0.14, 0.1, 0.28), skin, nu=14, nv=8)
        for i in range(3):
            base = sx((0.24 + 0.09 * i, 0.06, -0.36), s)
            m.cone(b, base, base + V([0, -0.04, -0.12]), 0.035, const('#d8d0c8'), sides=6)
    # muscled torso
    def torso_c(p, n, u, v):
        c = mix(hexc(SKIN), hexc('#6c6480'), max(0.0, float(np.dot(n, norm(V([-0.3, 0.7, -0.6]))))) ** 4 * 0.6)
        # abdominal lines
        if p[2] < -0.3 and 2.9 < p[1] < 3.6 and (abs(p[0]) < 0.02 or abs(p[1] - 3.15) < 0.015 or abs(p[1] - 3.4) < 0.015):
            c = shade(c, 0.55)
        return c
    m.loft('body', [(2.3, 0.5, 0.33, 0.35), (2.6, 0.48, 0.32, 0.34), (2.95, 0.42, 0.32, 0.3), (3.35, 0.5, 0.36, 0.32),
                    (3.75, 0.68, 0.42, 0.36), (4.0, 0.78, 0.36, 0.36), (4.12, 0.3, 0.22, 0.22), (4.35, 0.17, 0.16, 0.16)], torso_c, sides=24)
    for s in SIDES:
        m.ellipsoid('body', sx((0.26, 3.72, -0.3), s), (0.26, 0.2, 0.14), skin, nu=14, nv=10)  # pecs
    # cloak: hangs from the shoulders to the calves, open at the front
    def cloak_fn(u, v):
        a = math.radians(-125 + 250 * u)  # 0 = back
        y = 4.1 - v * 3.3
        rx = 0.85 + v * 0.45
        rz = 0.45 + v * 0.4
        wave = 0.04 * math.sin(u * 30) * v
        return V([math.sin(a) * (rx + wave), y, math.cos(a) * (rz + wave) + 0.05])
    m.surface('body', cloak_fn, 30, 12, cloak, thick=0.02)
    m.loft('body', [(3.95, 0.86, 0.4, 0.42), (4.1, 0.82, 0.38, 0.4), (4.2, 0.5, 0.3, 0.3)], cloak, sides=24)  # shoulder mantle
    # horned skulls: two on the chest, one on each shoulder
    def skull(b, c, k, nrm):
        c = V(c, dtype=float)
        m.ellipsoid(b, c, (0.12 * k, 0.12 * k, 0.1 * k), bone_c, nu=12, nv=9)
        m.ellipsoid(b, c + V([0, -0.09 * k, -0.02 * k]), (0.075 * k, 0.05 * k, 0.07 * k), bone_c, nu=10, nv=6)
        for s in SIDES:
            m.disc(b, c + V([0.045 * s * k, 0.0, -0.095 * k]), nrm, 0.032 * k, const('#120c10'), segs=10)
            hb = c + V([0.09 * s * k, 0.07 * k, -0.02 * k])
            m.sweep(b, [hb, hb + V([0.1 * s * k, 0.08 * k, 0]), hb + V([0.12 * s * k, 0.2 * k, -0.03 * k])], [0.03 * k, 0.02 * k, 0.0],
                    bone_c, sides=6, per=3)
    skull('body', (0.0, 3.25, -0.4), 1.2, V([0, 0, -1.0]))
    skull('body', (0.0, 2.55, -0.43), 1.0, V([0, 0, -1.0]))
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        skull(b, sx((0.88, 4.2, -0.05), s), 1.1, V([0, 0.3, -1.0]))
    # arms: thick and muscled, clawed hands
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((0.9, 4.0, 0), s), sx((1.25, 3.3, -0.1), s), sx((1.35, 2.6, -0.35), s)
        m.ellipsoid(b, sx((0.9, 4.0, 0.0), s), (0.27, 0.25, 0.27), skin, nu=14, nv=10)
        m.sweep(b, [sh, sx((1.08, 3.65, -0.04), s), el, sx((1.32, 2.95, -0.22), s), wr], [0.22, 0.22, 0.16, 0.17, 0.12], skin, sides=16, per=4)
        hand(m, b, wr, s, 2.4, skin, claw=const('#e8e0d8'))
    # head, face, hair, horns
    hc = V([0, 4.62, -0.05])
    m.ellipsoid('head', hc, (0.2, 0.25, 0.23), skin, nu=20, nv=14)
    m.ellipsoid('head', hc + V([0, -0.15, -0.08]), (0.14, 0.1, 0.14), skin, nu=14, nv=8)  # jaw
    zf = head_z(hc, 0.225)
    for s in SIDES:
        ex = 0.08 * s
        nrm = norm(V([ex * 0.6, 0.1, -1]))
        ring_eye(m, 'head', V([ex, 4.66, zf(ex, 4.66) - 0.012]), nrm, 0.045, [(1.0, '#120808'), (0.82, '#ff2a1a'), (0.55, '#1a0606'),
                                                                               (0.4, '#ff5a3a'), (0.16, '#000000')])
        m.sweep('head', [V([ex * 1.5, 4.72, zf(ex, 4.72) - 0.01]), V([ex * 0.4, 4.7, zf(ex * 0.4, 4.7) - 0.02])], [0.012, 0.008],
                const('#0c0a10'), sides=5, smooth=False)  # brows
    grin(m, 'head', 0, 4.5, 0.09, 0.025, zf, mouth='#0c0608', tooth='#e8e4dc', n=7, zig=True, lift=0.02)
    # goatee
    m.sweep('head', [hc + V([0, -0.26, -0.15]), hc + V([0, -0.38, -0.17]), hc + V([0, -0.5, -0.12])], [0.05, 0.035, 0.0], hair, sides=8, per=4)
    # long pale hair flowing down the back
    rnd = random.Random(31)
    for i in range(46):
        a = rnd.uniform(-2.3, 2.3)  # around the back of the head
        e = rnd.uniform(-0.1, 0.9)
        root = hc + V([math.sin(a) * 0.2 * math.cos(e), 0.12 + 0.12 * math.sin(e), math.cos(a) * 0.2 * math.cos(e) + 0.02])
        if root[2] < hc[2] - 0.12:
            continue
        L = rnd.uniform(1.4, 2.4)
        sw = rnd.uniform(-0.15, 0.15)
        pts = [root, root + V([math.sin(a) * 0.12, 0.05, 0.12]), root + V([math.sin(a) * 0.25 + sw, -L * 0.35, 0.3]),
               root + V([math.sin(a) * 0.35 + sw * 2, -L * 0.7, 0.42]), root + V([math.sin(a) * 0.42 + sw * 3, -L, 0.48])]
        m.sweep('head', pts, [0.06, 0.06, 0.05, 0.035, 0.0], hair, sides=6, per=3)
    m.ellipsoid('head', hc + V([0, 0.06, 0.03]), (0.215, 0.22, 0.225), hair, nu=18, nv=12, squash_bottom=0.3)  # scalp
    for s in SIDES:
        # curled ram horns at the temples
        base = hc + V([0.16 * s, 0.1, 0.0])
        curl = [base]
        for t in np.linspace(0, 1.6 * math.pi, 9)[1:]:
            rr = 0.16 * (1 - t / (2.2 * math.pi))
            curl.append(base + V([s * (0.08 + rr * (1 - math.cos(t)) * 0.7 + t * 0.02), rr * math.sin(t), -rr * (1 - math.cos(t)) * 0.4 + 0.05]))
        m.sweep('head', curl, [0.07, 0.065, 0.055, 0.045, 0.035, 0.025, 0.015, 0.008, 0.0], gloss('#2a2420', '#8a8070', 4, 0.5), sides=10, per=3)
        # the bigger pair, sweeping up and out
        b2 = hc + V([0.1 * s, 0.2, 0.02])
        m.sweep('head', [b2, b2 + V([0.25 * s, 0.22, 0.05]), b2 + V([0.45 * s, 0.6, 0.0]), b2 + V([0.4 * s, 0.95, -0.1]),
                         b2 + V([0.28 * s, 1.15, -0.12])], [0.08, 0.07, 0.055, 0.03, 0.0], gloss('#18141a', '#787080', 4, 0.5), sides=10, per=4)
    # ring of black flames with 16 eyes behind the head
    hcen = V([0, 4.75, 0.55])
    for i in range(16):
        a = 2 * math.pi * i / 16
        d = V([math.sin(a), math.cos(a), 0.0])
        base = hcen + d * 1.1
        tip = hcen + d * 1.65 + V([0, 0, 0.05]) + V([math.cos(a), -math.sin(a), 0]) * 0.15
        m.sweep('halo', [base - d * 0.15, base + d * 0.15 + V([math.cos(a), -math.sin(a), 0]) * 0.06, tip],
                [0.16, 0.12, 0.0], gloss('#0a0810', '#4a3860', 3, 0.6), sides=8, per=3, flat=0.35, hint=V([0, 0, 1.0]))
        ring_eye(m, 'halo', base - V([0, 0, 0.03]), V([0, 0, -1.0]), 0.15, [(1.0, '#f2ece8'), (0.72, '#e01818'), (0.42, '#200404'), (0.18, '#ff6040')])
    m.sweep('halo', [hcen + V([math.sin(a) * 1.0, math.cos(a) * 1.0, 0]) for a in np.linspace(0, 2 * math.pi, 25)], 0.07,
            gloss('#0a0810', '#4a3860', 3, 0.6), sides=8, per=2, caps=False)
    # long dark tail with an arrow tip
    tp = [V([0, 2.45, 0.35]), V([0, 1.9, 0.85]), V([0.3, 1.0, 1.25]), V([0.7, 0.35, 1.5]), V([1.3, 0.12, 1.6]), V([1.9, 0.25, 1.5])]
    m.sweep('tail', tp, [0.13, 0.11, 0.09, 0.07, 0.05, 0.035], skin, sides=10, per=5)
    tip = V([1.9, 0.25, 1.5]); d = norm(tip - V([1.3, 0.12, 1.6]))
    m.sweep('tail', [tip - d * 0.05, tip + d * 0.2, tip + d * 0.42], [0.04, 0.17, 0.0], skin, sides=6, smooth=False, flat=0.3,
            hint=V([0, 1.0, 0]))
    # black feathered wings
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        feather_wing(m, b, s, sx((0.3, 3.95, 0.45), s), 2.3, '#0e0c12', '#5a5070', back=0.1)
    return m


# ---------------- Imu: chapter 1198 form (phase 3) ----------------

def imu_beast():
    m = Mesh(1.0)
    BLACK = '#0b0a0e'
    blk = gloss(BLACK, '#5a5668', 4, 0.45)
    WHITE = '#efede6'
    m.bone('body', 'root', (0, 2.2, 0))
    m.bone('head', 'body', (0, 4.35, 0))
    m.bone('arm_r', 'body', (0.75, 4.1, 0))
    m.bone('arm_l', 'body', (-0.75, 4.1, 0))
    m.bone('robe', 'body', (0, 4.3, 0))
    m.bone('wing_r', 'body', (0.35, 4.05, 0.45))
    m.bone('wing_l', 'body', (-0.35, 4.05, 0.45))
    m.bone('flame', 'head', (0, 5.7, 0))
    m.anim('body', 'idle', 'up', 0.08, 4.0)
    m.anim('body', 'idle', 'x', 1.0, 4.0)
    m.anim('robe', 'walk', 'x', 4, 1.0)
    m.anim('robe', 'idle', 'z', 1.5, 3.0)
    m.anim('head', 'look', 'y', 0.6)
    m.anim('head', 'look', 'x', 0.4)
    m.anim('head', 'roar', 'x', 18)
    m.anim('arm_r', 'attack', 'x', 95)
    m.anim('arm_r', 'attack', 'z', -25)
    m.anim('body', 'attack', 'y', -15)
    m.anim('arm_r', 'roar', 'z', 30)
    m.anim('arm_l', 'roar', 'z', -45)
    m.anim('arm_l', 'idle', 'x', 4, 3.5)
    m.anim('flame', 'idle', 'y', 25, 1.4)
    m.anim('flame', 'idle', 'z', 5, 0.9)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        m.anim(b, 'idle', 'z', 18 * s, 2.6)
        m.anim(b, 'fly', 'z', 14 * s, 1.0)
        m.anim(b, 'roar', 'z', 22 * s)
    # black body under the robe
    m.loft('body', [(0.05, 0.75, 0.55, 0.6), (0.8, 0.7, 0.55, 0.55), (1.8, 0.6, 0.5, 0.48), (2.8, 0.58, 0.48, 0.45),
                    (3.6, 0.7, 0.5, 0.45), (4.15, 0.78, 0.42, 0.42), (4.3, 0.3, 0.25, 0.25)], blk, sides=24)
    # the big eye and the skull on the lower front
    ring_eye(m, 'body', V([0, 2.55, -0.52]), V([0, 0.05, -1.0]), 0.36, [(1.0, '#f4f2ec'), (0.62, '#c81818'), (0.42, '#0a0204'), (0.2, '#e84030')])
    m.ellipsoid('body', V([0, 1.45, -0.5]), (0.3, 0.32, 0.16), const('#e8e4da'), nu=16, nv=12)
    m.ellipsoid('body', V([0, 1.18, -0.52]), (0.2, 0.12, 0.13), const('#e0dcd0'), nu=12, nv=8)
    for s in SIDES:
        m.ellipsoid('body', V([0.12 * s, 1.5, -0.64]), (0.085, 0.09, 0.03), const('#060506'), nu=10, nv=8)
    m.ellipsoid('body', V([0, 1.36, -0.665]), (0.035, 0.05, 0.02), const('#060506'), nu=8, nv=6)
    for i in range(6):
        m.ellipsoid('body', V([-0.125 + 0.05 * i, 1.12, -0.64]), (0.02, 0.04, 0.02), const('#060506'), nu=6, nv=4)
    # robe: long white strands from the shoulders to the floor, open at the front
    rnd = random.Random(5)
    strand = lambda p, n, u, v: mix(hexc(WHITE), hexc('#9c9a94'), 0.12 + u * 0.35 + max(0.0, -n[1]) * 0.2)
    for i in range(54):
        a = math.radians(-155 + 310 * (i + 0.5) / 54) + rnd.uniform(-0.03, 0.03)  # 0 = straight back
        top = V([math.sin(a) * 0.82, 4.22, math.cos(a) * 0.48])
        bot = V([math.sin(a) * (1.35 + rnd.uniform(-0.1, 0.12)), 0.03, math.cos(a) * 1.05])
        ph = rnd.uniform(0, 6.28)
        pts = [top + (bot - top) * t + V([math.cos(a) * 0.05 * math.sin(ph + t * 7), 0, -math.sin(a) * 0.05 * math.sin(ph + t * 7)])
               for t in np.linspace(0, 1, 6)]
        out = V([math.sin(a), 0, math.cos(a)])
        hint = np.cross(V([0, 1.0, 0]), out)
        m.sweep('robe', pts, [0.1, 0.12, 0.14, 0.15, 0.14, 0.09], strand, sides=6, per=4, flat=0.3, hint=hint)
    m.loft('robe', [(3.9, 0.92, 0.52, 0.55), (4.15, 0.88, 0.5, 0.52), (4.3, 0.55, 0.36, 0.38), (4.38, 0.28, 0.26, 0.26)],
           lambda p, n, u, v: mix(hexc(WHITE), hexc('#b8b6ae'), 0.2), sides=24)
    # arms: thin and black inside wide strand sleeves; the right one holds the long blade
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh = sx((0.75, 4.1, 0), s)
        el = sx((1.05, 3.25, -0.25), s)
        wr = sx((0.85, 2.85, -0.85), s) if s > 0 else sx((0.95, 2.75, -0.45), s)
        m.sweep(b, [sh, el, wr], [0.13, 0.11, 0.08], blk, sides=12, per=4)
        hand(m, b, wr, s, 2.2, blk, claw=const('#d8d4cc'))
        for j in range(9):
            a = 2 * math.pi * j / 9
            off = V([math.cos(a) * 0.22, 0, math.sin(a) * 0.22])
            p0 = sh + off * 0.8 + V([0, 0.05, 0])
            p1 = el + off * 1.4 + V([0, -0.1, 0])
            p2 = el + off * 1.8 + V([0, -0.85, 0.2])
            m.sweep(b, [p0, p1, p2], [0.06, 0.08, 0.05], strand, sides=5, per=3, flat=0.35)
    hand_r = V([0.85, 2.7, -0.92])
    d = norm(V([0.45, 1.0, -0.12]))
    bottom = hand_r - d * 0.55
    top = hand_r + d * 4.2
    m.sweep('arm_r', [bottom, hand_r + d * 0.25], [0.06, 0.06], const('#1e1a22'), sides=8, smooth=False)  # grip
    m.ellipsoid('arm_r', hand_r + d * 0.3, (0.14, 0.04, 0.14), const('#c8c4bc'), nu=12, nv=6)  # guard
    edge = norm(np.cross(d, V([0, 0, 1.0])))
    blade = lambda p, n, u, v: mix(hexc('#f6f8fc'), hexc('#8a94a8'), abs(v - 0.5) * 1.6)
    m.sweep('arm_r', [hand_r + d * 0.3, hand_r + d * 2.0, top], [0.095, 0.09, 0.0], blade, sides=8, per=2, flat=0.18, hint=edge, smooth=False)
    # neck column with a row of white dots down the front, and the head
    m.sweep('head', [V([0, 4.25, 0]), V([0, 4.9, -0.02]), V([0, 5.6, 0])], [0.22, 0.2, 0.19], blk, sides=16, per=4)
    m.ellipsoid('head', V([0, 5.6, 0]), (0.2, 0.18, 0.2), blk, nu=14, nv=10)
    for i in range(9):
        y = 4.45 + i * 0.13
        m.ellipsoid('head', V([0, y, -0.2]), (0.04, 0.04, 0.02), glow('#ffffff'), nu=8, nv=6)
    # huge black crescent horns making a U above the head
    for s in SIDES:
        hp = [V([0.15 * s, 5.55, 0]), V([0.7 * s, 5.75, 0.02]), V([1.25 * s, 6.3, 0.0]), V([1.45 * s, 7.05, -0.05]),
              V([1.25 * s, 7.7, -0.1]), V([0.85 * s, 8.0, -0.12])]
        m.sweep('head', hp, [0.2, 0.2, 0.17, 0.12, 0.06, 0.0], gloss('#09080c', '#6a6478', 4, 0.6), sides=12, per=5)
    # white swirling flame between the horns
    for k in range(4):
        ph = k * math.pi / 2
        pts = [V([0.32 * math.sin(ph + t * 5) * (1 - t * 0.6), 5.72 + t * 1.6, 0.25 * math.cos(ph + t * 5) * (1 - t * 0.6)])
               for t in np.linspace(0, 1, 9)]
        m.sweep('flame', pts, [0.17, 0.2, 0.16, 0.13, 0.1, 0.07, 0.05, 0.02, 0.0], glow('#f8f8ff'), sides=8, per=3)
    m.ellipsoid('flame', V([0, 6.05, 0]), (0.32, 0.36, 0.3), glow('#e8ecff'), nu=12, nv=10)
    # dark feathered wings
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        feather_wing(m, b, s, sx((0.35, 4.05, 0.45), s), 3.6, '#0c0b10', '#4c4658', count=(10, 12, 13), back=0.15)
    # black smoke wisps with ringed eyes floating round
    wisps = [(2.2, 2.0, 40), (-2.4, 3.0, -30), (1.9, 4.6, 150), (-1.8, 5.2, -160), (2.6, 3.6, 95), (-2.7, 1.5, -90)]
    for i, (wx, wy, face) in enumerate(wisps):
        b = m.bone('wisp%d' % i, 'root', (wx, wy, 0.3))
        m.anim(b, 'idle', 'up', 0.25, 3.0 + i * 0.4, i * 1.3)
        m.anim(b, 'idle', 'y', 10, 5.0 + i * 0.5, i)
        c = V([wx, wy, 0.3 - 0.6 * (i % 2)])
        rnd2 = random.Random(100 + i)
        for j in range(5):
            m.ellipsoid(b, c + V([rnd2.uniform(-0.25, 0.25), rnd2.uniform(-0.2, 0.25), rnd2.uniform(-0.15, 0.15)]),
                        (rnd2.uniform(0.2, 0.3), rnd2.uniform(0.18, 0.26), rnd2.uniform(0.18, 0.26)), gloss('#08070a', '#3a3640', 3, 0.5), nu=12, nv=8)
        tail = [c + V([0, 0, 0.1]), c + V([math.copysign(0.4, wx), -0.5, 0.3]), c + V([math.copysign(0.2, wx), -1.1, 0.5]),
                c + V([math.copysign(0.6, wx), -1.5, 0.5])]
        m.sweep(b, tail, [0.22, 0.15, 0.08, 0.0], gloss('#08070a', '#3a3640', 3, 0.5), sides=8, per=4)
        ring_eye(m, b, c + V([0, 0.05, -0.3]), V([0, 0.0, -1.0]), 0.17, [(1.0, '#f4f0ea'), (0.75, '#101010'), (0.58, '#d02020'),
                                                                         (0.38, '#101010'), (0.18, '#f4f0ea')])
    return m


# ---------------- Loki: Nidhogg hybrid ----------------

def nidhogg():
    m = Mesh(1.0)
    OBS = '#0c0c10'
    obs = gloss(OBS, '#9aa2b8', 5, 0.55)
    belly = '#5a4c44'
    GOLD = '#dccb98'
    fur = lambda p, n, u, v: mix(hexc('#fbfaf6'), hexc('#bdbab2'), max(0.0, -n[1]) * 0.7)
    mane = lambda p, n, u, v: mix(hexc('#ffffff'), hexc('#b8b8c0'), 0.1 + u * 0.4 + max(0.0, -n[1]) * 0.25)
    m.bone('body', 'root', (0, 4.1, 0))
    m.bone('head', 'body', (0, 7.45, -0.3))
    m.bone('arm_r', 'body', (2.0, 6.9, 0))
    m.bone('arm_l', 'body', (-2.0, 6.9, 0))
    m.bone('leg_r', 'root', (0.95, 4.0, 0.1))
    m.bone('leg_l', 'root', (-0.95, 4.0, 0.1))
    m.bone('tail', 'body', (0, 4.0, 0.8))
    m.bone('wing_r', 'body', (0.9, 6.8, 1.0))
    m.bone('wing_l', 'body', (-0.9, 6.8, 1.0))
    humanoid_anims(m, walk_leg=22, walk_arm=14, attack=125, roar_arms=40)
    m.anim('head', 'roar', 'x', 10)  # plus the humanoid roar tilt: head thrown back to breathe lightning
    m.anim('tail', 'idle', 'y', 12, 3.0)
    m.anim('tail', 'walk', 'y', 9, 1.0)
    m.anim('body', 'idle', 'up', 0.06, 3.2)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        m.anim(b, 'idle', 'z', 5 * s, 3.4)
        m.anim(b, 'fly', 'z', 32 * s, 1.1)
        m.anim(b, 'roar', 'z', 22 * s)
        m.anim(b, 'rest', 'y', -38 * s)
        m.anim(b, 'rest', 'z', -10 * s)
    # torso: massive, glossy black with a lighter belly
    def torso_c(p, n, u, v):
        c = obs(p, n, u, v)
        front = -n[2]
        if front > 0.45 and 4.0 < p[1] < 6.4 and abs(p[0]) < 1.0:
            c = mix(c, hexc(belly), min(1.0, (front - 0.45) * 2.5))
            # belly plates
            if (p[1] - 4.0) % 0.42 < 0.05:
                c = shade(c, 0.6)
        return c
    m.loft('body', [(3.7, 1.25, 0.95, 0.95), (4.2, 1.3, 1.0, 1.0), (4.8, 1.22, 1.0, 0.95), (5.5, 1.5, 1.15, 1.0),
                    (6.2, 1.95, 1.3, 1.05), (6.85, 2.15, 1.1, 1.05), (7.15, 1.4, 0.9, 0.9), (7.45, 0.75, 0.65, 0.7)], torso_c, sides=28)
    for s in SIDES:
        m.ellipsoid('body', sx((0.75, 6.25, -0.85), s), (0.85, 0.62, 0.45), obs, nu=16, nv=12)   # pecs
        m.ellipsoid('body', sx((1.65, 7.05, 0.15), s), (0.75, 0.55, 0.8), obs, nu=16, nv=12)    # traps / shoulder mass
    # ornate chest band and belt
    def band_c(p, n, u, v):
        k = int(u * 40) % 4
        return hexc(GOLD) if k != 0 else hexc('#8a6c3a')
    for y, rx, rz, w in ((6.0, 1.98, 1.32, 0.16), (4.45, 1.36, 1.06, 0.22)):
        ring = [V([math.sin(a) * rx, y, -math.cos(a) * rz]) for a in np.linspace(0, 2 * math.pi, 33)]
        m.sweep('body', ring, w, band_c, sides=8, per=2, caps=False, flat=0.35)
    m.disc('body', V([0, 4.45, -1.16]), V([0, 0, -1.0]), 0.32, const(GOLD), segs=16)
    m.disc('body', V([0, 4.45, -1.17]), V([0, 0, -1.0]), 0.18, const('#8a6c3a'), segs=16)
    for s in SIDES:  # diagonal straps over the chest to the band
        m.sweep('body', [sx((0.3, 6.05, -1.32), s), sx((1.0, 6.8, -0.95), s), sx((1.5, 7.25, -0.2), s)], 0.12, band_c, sides=6, per=4, flat=0.35)
    # white fur trim round the waist
    puffs(m, 'body', [V([math.sin(a) * 1.35, 4.0 + 0.06 * math.sin(a * 5), -math.cos(a) * 1.05]) for a in np.linspace(0, 2 * math.pi, 23)[:-1]],
          0.25, 0.34, fur, 21)
    # legs: huge round thighs, dragon shins, long talons
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        hip, knee, ank, ball = sx((0.95, 4.0, 0.1), s), sx((1.05, 2.5, -0.55), s), sx((1.05, 1.05, 0.4), s), sx((1.05, 0.3, -0.15), s)
        m.ellipsoid(b, sx((1.0, 3.35, -0.2), s), (0.95, 1.05, 0.95), obs, nu=18, nv=12)
        m.sweep(b, [hip, sx((1.02, 3.2, -0.25), s), knee], [0.85, 0.9, 0.6], obs, sides=18, per=4)
        m.sweep(b, [knee, sx((1.06, 1.8, 0.05), s), ank], [0.58, 0.48, 0.32], obs, sides=16, per=4)
        m.sweep(b, [ank, ball], [0.32, 0.27], obs, sides=14, smooth=False)
        puffs(m, b, [sx((1.0 + 0.92 * math.sin(a), 3.95, -0.1 - 0.85 * math.cos(a)), s) for a in np.linspace(0, 2 * math.pi, 12)[:-1]],
              0.2, 0.28, fur, 30 + s)
        for i, ang in enumerate((-30, 0, 30)):
            d = norm(V([math.sin(math.radians(ang)) * s, -0.1, -math.cos(math.radians(ang))]))
            b0 = ball + V([0, 0, 0])
            t1 = b0 + d * 0.6 + V([0, -0.1, 0])
            t2 = t1 + d * 0.35 + V([0, -0.15, 0])
            m.sweep(b, [b0, t1], [0.2, 0.14], obs, sides=10, smooth=False)
            m.sweep(b, [t1, t2 + V([0, 0.05, 0]), t2 + d * 0.25 + V([0, -0.08, 0])], [0.13, 0.08, 0.0], gloss('#1a1816', '#d8d0c0', 3, 0.6),
                    sides=8, per=3)
        m.sweep(b, [ank + V([0, -0.1, 0.1]), ank + V([0, -0.5, 0.55]), ank + V([0, -0.95, 0.7])], [0.14, 0.09, 0.0],
                gloss('#1a1816', '#d8d0c0', 3, 0.6), sides=8, per=3)  # back talon / spur
    # arms: enormous, studded cuffs, clawed hands
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((2.0, 6.9, 0), s), sx((2.55, 5.3, 0.15), s), sx((2.65, 3.95, -0.35), s)
        m.ellipsoid(b, sx((2.15, 6.85, 0.0), s), (0.85, 0.75, 0.8), obs, nu=18, nv=12)  # deltoid
        m.sweep(b, [sh, sx((2.4, 6.1, 0.05), s), el], [0.72, 0.78, 0.55], obs, sides=18, per=4)
        m.sweep(b, [el, sx((2.65, 4.7, -0.05), s), wr], [0.58, 0.62, 0.45], obs, sides=18, per=4)
        cuff_c = lambda p, n, u, v: hexc(GOLD)
        m.sweep(b, [wr + V([0, 0.55, 0.06]), wr + V([0, 0.05, 0])], [0.55, 0.52], cuff_c, sides=18, smooth=False)
        for j in range(10):
            a = 2 * math.pi * j / 10
            for yy in (0.15, 0.42):
                p = wr + V([math.cos(a) * 0.54, yy, math.sin(a) * 0.54])
                m.cone(b, p, p + V([math.cos(a) * 0.14, 0, math.sin(a) * 0.14]), 0.07, gloss('#0c0c10', '#9aa2b8', 4, 0.6), sides=6)
        hand(m, b, wr, s, 5.0, obs, claw=gloss('#1a1816', '#e8e0d0', 3, 0.6))
    # Ragnir in the right hand, head down by the feet
    hammer(m, 'arm_r', V([2.72, 4.6, -0.95]), V([2.72, 0.9, -1.15]), 1.6)
    # head
    hc = V([0, 8.05, -0.75])
    m.ellipsoid('head', hc, (0.68, 0.74, 0.7), obs, nu=22, nv=16)
    m.ellipsoid('head', hc + V([0, -0.42, -0.22]), (0.6, 0.38, 0.52), obs, nu=18, nv=10)  # big jaw
    m.sweep('head', [V([0, 7.3, -0.3]), hc + V([0, -0.3, 0.2])], [0.75, 0.6], obs, sides=16, smooth=False)  # neck
    zf = head_z(hc + V([0, 0, -0.08]), 0.74)
    grin(m, 'head', 0, 7.72, 0.52, 0.16, zf, mouth='#1a0c0a', tooth='#efe6cc', n=10, zig=False, grid=True, lift=0.1)
    for s in SIDES:
        ex = 0.25 * s
        nrm = norm(V([ex, 0.1, -0.9]))
        m.ellipsoid('head', V([ex, 8.08, zf(ex, 8.08) + 0.02]), (0.13, 0.06, 0.04), const('#050505'), rot=(0, 0, -14 * s), nu=12, nv=6)
        ring_eye(m, 'head', V([ex, 8.08, zf(ex, 8.08) - 0.02]), nrm, 0.07, [(1.0, '#fff8d0'), (0.4, '#ffb020')])
        m.sweep('head', [V([ex * 1.6, 8.26, zf(ex * 1.6, 8.26) - 0.01]), V([ex * 0.3, 8.14, zf(ex * 0.3, 8.14) - 0.04])], [0.05, 0.03],
                obs, sides=6, smooth=False)  # heavy brow
    # big curved black horns
    for s in SIDES:
        hb = hc + V([0.42 * s, 0.35, 0.0])
        m.sweep('head', [hb, hb + V([0.8 * s, 0.35, 0.25]), hb + V([1.45 * s, 1.05, 0.15]), hb + V([1.55 * s, 1.95, -0.35]),
                         hb + V([1.2 * s, 2.55, -0.85])], [0.32, 0.27, 0.2, 0.12, 0.0], gloss('#060608', '#a0a8c0', 5, 0.6), sides=14, per=6)
    # crown of black spikes behind the head
    cc = hc + V([0, 0.15, 0.35])
    for i in range(11):
        a = math.radians(-100 + 200 * i / 10)
        d = norm(V([math.sin(a), math.cos(a) * 0.9 + 0.25, 0.55]))
        L = 1.2 + 0.7 * math.cos(a) ** 2
        m.sweep('head', [cc + d * 0.3, cc + d * (0.3 + L * 0.6) + V([0, 0, 0.1]), cc + d * (0.3 + L)], [0.17, 0.1, 0.0],
                gloss('#060608', '#a0a8c0', 5, 0.6), sides=8, per=3)
    # wild white swirling mane over the head, shoulders and chest
    rnd = random.Random(77)
    for i in range(90):
        zone = rnd.random()
        if zone < 0.35:   # top/back of head
            a, e = rnd.uniform(-2.6, 2.6), rnd.uniform(0.1, 1.1)
            root = hc + V([math.sin(a) * 0.55 * math.cos(e), 0.6 * math.sin(e) + 0.1, math.cos(a) * 0.55 * math.cos(e)])
            out = norm(root - hc + V([0, 0.3, 0.3]))
        elif zone < 0.75:  # shoulders / neck ruff
            a = rnd.uniform(-math.pi, math.pi)
            root = V([math.sin(a) * rnd.uniform(0.8, 1.8), rnd.uniform(6.95, 7.35), math.cos(a) * rnd.uniform(0.6, 1.0)])
            out = norm(V([math.sin(a), 0.05, math.cos(a) * (0.6 if math.cos(a) < 0 else 1.0)]))
        else:             # chest
            root = V([rnd.uniform(-1.1, 1.1), rnd.uniform(6.3, 6.9), -rnd.uniform(1.0, 1.25)])
            out = norm(V([root[0] * 0.4, -0.6, -0.8]))
        L = rnd.uniform(0.7, 1.5)
        sp = rnd.uniform(0, 6.28)
        cr = rnd.uniform(0.15, 0.3)
        side = norm(np.cross(out, V([0, 1.0, 0])) + V([1e-3, 0, 0]))
        up = np.cross(side, out)
        pts = [root]
        for t in np.linspace(0.25, 1.0, 5):
            ang = sp + t * 5.5
            pts.append(root + out * L * t + (side * math.cos(ang) + up * math.sin(ang)) * cr * t)
        m.sweep('body' if zone >= 0.35 else 'head', pts, [0.16, 0.15, 0.12, 0.09, 0.05, 0.0], mane, sides=7, per=3)
    puffs(m, 'head', [hc + V([rnd.uniform(-0.4, 0.4), 0.45 + rnd.uniform(0, 0.25), rnd.uniform(-0.1, 0.45)]) for _ in range(10)], 0.22, 0.32, mane, 78)
    # tail
    tp = [V([0, 4.0, 0.8]), V([0, 3.0, 1.9]), V([0.5, 1.4, 3.0]), V([1.4, 0.4, 3.9]), V([2.6, 0.2, 4.4]), V([3.6, 0.6, 4.6])]
    m.sweep('tail', tp, [0.75, 0.6, 0.45, 0.32, 0.2, 0.08], obs, sides=14, per=5)
    for i, t in enumerate(np.linspace(0.05, 0.9, 9)):
        from meshkit import catmull
        cp = catmull(tp, 8)
        p = cp[int(t * (len(cp) - 1))]
        q = cp[min(int(t * (len(cp) - 1)) + 1, len(cp) - 1)]
        d = norm(q - p)
        upv = norm(np.cross(d, np.cross(V([0, 1.0, 0]), d)))
        r = 0.75 * (1 - t) + 0.1
        m.cone('tail', p + upv * r * 0.8, p + upv * (r + 0.45) - d * 0.15, 0.15, gloss('#060608', '#a0a8c0', 5, 0.6), sides=6)
    # bat wings
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        bat_wing(m, b, s, sx((0.9, 6.8, 1.0), s), 1.05, '#0c0c10', '#241418')
    return m


# ---------------- Loki: his own look ----------------

def loki():
    m = Mesh(4.44)   # modelled at Loki's character scale (8 blocks tall)
    SKIN = '#c99a7a'
    skin = gloss(SKIN, '#f0d0b8', 4, 0.35)
    HAIR = '#e294c8'
    hair = lambda p, n, u, v: mix(hexc(HAIR), hexc('#a85890'), 0.1 + 0.45 * u + max(0.0, -n[1]) * 0.2)
    tunic = lambda p, n, u, v: mix(hexc('#4a2a22'), hexc('#7a4a3a'), max(0.0, n[1]) * 0.4 + max(0.0, -n[2]) * 0.15)
    leather = lambda p, n, u, v: mix(hexc('#2a201a'), hexc('#5a4838'), max(0.0, n[1]) * 0.4)
    fur = lambda p, n, u, v: mix(hexc('#dedad2'), hexc('#8e8a82'), max(0.0, -n[1]) * 0.6 + 0.1)
    GOLD = '#d4b46a'
    m.bone('body', 'root', (0, 3.7, 0))
    m.bone('head', 'body', (0, 6.75, -0.05))
    m.bone('arm_r', 'body', (1.2, 6.25, 0))
    m.bone('arm_l', 'body', (-1.2, 6.25, 0))
    m.bone('leg_r', 'root', (0.5, 3.6, 0))
    m.bone('leg_l', 'root', (-0.5, 3.6, 0))
    m.bone('cape', 'body', (0, 6.4, 0.6))
    humanoid_anims(m, walk_leg=24, walk_arm=18, attack=120, roar_arms=35)
    m.anim('cape', 'walk', 'x', -6, 2.0)
    m.anim('cape', 'idle', 'x', -2, 3.0)
    # legs: leather trousers, fur-topped boots
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        hip, knee, ank = sx((0.5, 3.6, 0), s), sx((0.55, 1.95, -0.1), s), sx((0.55, 0.45, 0.0), s)
        m.sweep(b, [hip, sx((0.53, 2.8, -0.04), s), knee], [0.5, 0.45, 0.37], leather, sides=16, per=4)
        m.sweep(b, [knee, ank], [0.37, 0.3], leather, sides=16, smooth=False)
        m.loft(b, [(0.0, 0.34, 0.55, 0.36, -0.1, 0.55 * s), (0.25, 0.36, 0.52, 0.36, -0.08, 0.55 * s), (0.6, 0.34, 0.36, 0.34, 0.0, 0.55 * s),
                   (1.25, 0.36, 0.36, 0.36, 0.0, 0.55 * s)], leather, sides=18)
        puffs(m, b, [sx((0.55 + 0.38 * math.sin(a), 1.3, -0.38 * math.cos(a)), s) for a in np.linspace(0, 2 * math.pi, 11)[:-1]], 0.11, 0.15, fur, 40 + s)
        m.sweep(b, [sx((0.55, 1.85, -0.38), s), sx((0.55, 1.6, -0.39), s)], 0.06, const(GOLD), sides=6, smooth=False)
    # torso: tunic with a belt, fur collar
    m.loft('body', [(3.3, 0.85, 0.62, 0.6), (3.7, 0.82, 0.6, 0.58), (4.3, 0.75, 0.55, 0.52), (5.0, 0.85, 0.6, 0.55),
                    (5.7, 1.05, 0.68, 0.6), (6.2, 1.15, 0.6, 0.6), (6.45, 0.55, 0.42, 0.42), (6.7, 0.32, 0.32, 0.32)], tunic, sides=26)
    m.loft('body', [(3.95, 0.82, 0.6, 0.58), (4.2, 0.8, 0.58, 0.56)], leather, sides=26)  # belt
    m.ellipsoid('body', V([0, 4.08, -0.6]), (0.22, 0.17, 0.06), const(GOLD), nu=12, nv=8)
    m.ellipsoid('body', V([0, 4.08, -0.64]), (0.12, 0.09, 0.04), const('#8a6c3a'), nu=10, nv=6)
    # tunic skirt panels over the hips
    m.surface('body', lambda u, v: V([math.sin(math.radians(-170 + 340 * u)) * (0.86 + 0.25 * v), 3.95 - v * 1.15,
                                       -math.cos(math.radians(-170 + 340 * u)) * (0.62 + 0.25 * v)]), 28, 4, tunic, thick=0.03)
    puffs(m, 'body', [V([math.sin(a) * 1.0, 6.22 + 0.05 * math.sin(a * 4), -math.cos(a) * 0.62]) for a in np.linspace(0, 2 * math.pi, 18)[:-1]],
          0.2, 0.27, fur, 50)
    # fur cape down the back
    m.surface('cape', lambda u, v: V([(u - 0.5) * (2.1 + 0.7 * v), 6.35 - v * 4.6, 0.62 + 0.35 * v + 0.06 * math.sin(u * 18) * v]),
              14, 10, lambda p, n, u, v: mix(hexc('#3a2e26'), hexc('#5c4a3c'), 0.4 * u), thick=0.05)
    # arms: bare, muscled, leather bracers
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((1.2, 6.2, 0), s), sx((1.45, 5.0, 0.08), s), sx((1.52, 3.9, -0.18), s)
        m.ellipsoid(b, sx((1.22, 6.15, 0.0), s), (0.45, 0.42, 0.45), tunic, nu=16, nv=10)
        m.sweep(b, [sh, sx((1.35, 5.6, 0.05), s), el], [0.38, 0.4, 0.3], skin, sides=16, per=4)
        m.sweep(b, [el, sx((1.5, 4.5, -0.04), s), wr], [0.32, 0.33, 0.25], skin, sides=16, per=4)
        m.sweep(b, [wr + V([0, 0.75, 0.04]), wr + V([0, 0.05, 0])], [0.34, 0.29], leather, sides=16, smooth=False)
        for yy in (0.25, 0.55):
            m.sweep(b, [wr + V([0, yy, 0.02]), wr + V([0, yy + 0.07, 0.02])], 0.345, const(GOLD), sides=16, smooth=False)
        hand(m, b, wr, s, 3.6, skin)
    hammer(m, 'arm_r', V([1.6, 4.4, -0.75]), V([1.6, 0.85, -0.85]), 1.55)
    # head
    hc = V([0, 7.3, -0.12])
    m.sweep('head', [V([0, 6.5, -0.05]), V([0, 6.95, -0.1])], [0.34, 0.3], skin, sides=14, smooth=False)  # neck
    m.ellipsoid('head', hc, (0.5, 0.58, 0.53), skin, nu=22, nv=16)
    m.ellipsoid('head', hc + V([0, -0.34, -0.14]), (0.4, 0.26, 0.4), skin, nu=16, nv=10)
    zf = head_z(hc, 0.54)
    zj = head_z(hc + V([0, -0.34, -0.14]), 0.4)
    grin(m, 'head', 0, hc[1] - 0.36, 0.24, 0.055, lambda x, y: min(zj(x, y), zf(x, y)), mouth='#2a0e0e', tooth='#f2ece0', n=9, zig=False, grid=True, lift=0.06)
    m.ellipsoid('head', V([0, hc[1] - 0.1, zf(0, hc[1] - 0.1) + 0.02]), (0.08, 0.12, 0.08), skin, nu=10, nv=8)  # nose
    # bandages over the eyes
    band = lambda p, n, u, v: mix(hexc('#f4f0e6'), hexc('#c8c0b0'), 0.5 + 0.5 * math.sin(u * 60))
    ring = [hc + V([math.sin(a) * 0.52, 0.08 + 0.04 * math.sin(a * 2), -math.cos(a) * 0.56]) for a in np.linspace(0, 2 * math.pi, 25)]
    m.sweep('head', ring, 0.16, band, sides=8, per=2, caps=False, flat=0.25)
    m.sweep('head', [hc + V([-0.05, -0.05, 0.45]), hc + V([-0.15, -0.5, 0.55]), hc + V([-0.1, -0.95, 0.5])], 0.07, band, sides=6, per=3, flat=0.3)
    # hair: messy at the back, two thick braids in front
    rnd = random.Random(11)
    for i in range(55):
        a = rnd.uniform(-2.5, 2.5)
        e = rnd.uniform(-0.2, 0.7)
        root = hc + V([math.sin(a) * 0.42 * math.cos(e), 0.1 + 0.4 * math.sin(e), math.cos(a) * 0.44 * math.cos(e)])
        if root[2] < hc[2] - 0.15:
            continue
        L = rnd.uniform(1.6, 2.8)
        sw = rnd.uniform(-0.3, 0.3)
        pts = [root, root + V([math.sin(a) * 0.25, 0.08, 0.2]), root + V([math.sin(a) * 0.4 + sw, -L * 0.35, 0.4 + rnd.uniform(-0.1, 0.2)]),
               root + V([math.sin(a) * 0.5 + sw * 1.6, -L * 0.7, 0.5]), root + V([math.sin(a) * 0.55 + sw * 2.4, -L, 0.48 + rnd.uniform(-0.1, 0.2)])]
        m.sweep('head', pts, [0.11, 0.12, 0.1, 0.07, 0.0], hair, sides=6, per=3)
    for s in SIDES:
        top = hc + V([0.36 * s, 0.05, -0.12])
        path = [top, top + V([0.12 * s, -0.4, -0.12]), top + V([0.14 * s, -0.95, -0.4]), top + V([0.1 * s, -1.6, -0.48]),
                top + V([0.06 * s, -2.3, -0.42])]
        from meshkit import catmull
        cp = catmull(path, 12)
        radii = [0.13 * (1 - 0.35 * t) * (0.82 + 0.18 * abs(math.sin(t * 30))) for t in np.linspace(0, 1, len(cp))]
        m.sweep('head', cp, radii, hair, sides=10, smooth=False)
        end = cp[-1]
        m.sweep('head', [end + V([0, 0.12, 0]), end + V([0, -0.02, 0])], 0.1, const(GOLD), sides=10, smooth=False)
        m.sweep('head', [end, end + V([0.04 * s, -0.25, 0.02]), end + V([0.06 * s, -0.45, 0.04])], [0.1, 0.12, 0.0], hair, sides=8, per=3)
    # wide-rimmed black helmet with long black horns, the left one wrapped
    helm = gloss('#141418', '#8890a0', 5, 0.5)
    m.ellipsoid('head', hc + V([0, 0.22, 0.0]), (0.55, 0.5, 0.58), helm, nu=22, nv=14, squash_bottom=0.05)
    m.disc('head', hc + V([0, 0.25, 0]), V([0, 1.0, 0]), 1.1, helm, segs=28, r_in=0.5)
    m.disc('head', hc + V([0, 0.23, 0]), V([0, -1.0, 0]), 1.1, helm, segs=28, r_in=0.5)
    m.sweep('head', [hc + V([math.sin(a) * 1.1, 0.24, -math.cos(a) * 1.1]) for a in np.linspace(0, 2 * math.pi, 29)], 0.035, helm,
            sides=6, per=1, caps=False)
    for s in SIDES:
        hb = hc + V([0.36 * s, 0.5, 0.0])
        path = [hb, hb + V([0.25 * s, 0.6, 0.02]), hb + V([0.33 * s, 1.3, -0.05]), hb + V([0.22 * s, 1.95, -0.12])]
        wrap = s < 0
        col = (lambda p, n, u, v: (232, 226, 214) if (u * 40) % 2 < 1.2 and 0.08 < u < 0.82 else hexc('#0e0e12')) if wrap else \
            gloss('#0e0e12', '#8890a0', 5, 0.5)
        m.sweep('head', path, [0.17, 0.14, 0.09, 0.0], col, sides=12, per=8)
    return m


MODELS = {'nika_wild': nika, 'imu_demon': imu_demon, 'imu_beast': imu_beast, 'nidhogg': nidhogg, 'character/loki': loki}


def main():
    prev = None
    if '--preview' in sys.argv:
        prev = sys.argv[sys.argv.index('--preview') + 1]
        os.makedirs(prev, exist_ok=True)
    only = [a for a in sys.argv[1:] if a in MODELS]
    for name, fn in MODELS.items():
        if only and name not in only:
            continue
        m = fn()
        path = os.path.join(OUT, name + '.bin')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        size = m.write(path)
        print('%-16s %6d faces  %5d KB' % (name, m.count(), size // 1024))
        if prev:
            from preview import sheet
            sheet(m, os.path.join(prev, name.replace('/', '_') + '.png'))


if __name__ == '__main__':
    main()
