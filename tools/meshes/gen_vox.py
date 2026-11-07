"""Makes the blocky, Minecraft-style models for the chapter 1191/1198 transformations (drawn by
com.onepiecemod.mesh.client.MeshForms, files in assets/onepiece/meshes/). Built from ryan's chapter images:

  nika_wild      Luffy's feral black Nika: a hunched ape with long knuckle-walking arms, a big white cloud
                 head with a huge black grin of zigzag teeth, an ape nose, black gloved hands with white
                 cloud swirls, a tail.
  imu_beast      Imu, chapter 1198: a tall robe of white and black stripes with a black slit down the front
                 dotted with white, a narrow black head, ring horns with a white flame inside, a ring of eyes
                 behind, a long sword, huge dark wings, black clouds full of eyes on both sides.
  imu_demon      Imu, chapter 1191 devil form: dark muscled body, long pale hair, red ringed eyes, curled
                 horns + a bigger pair, goatee, horned skulls, cloak, tail, black wings, ring of black flames
                 with eyes.
  nidhogg        Loki's Nidhogg hybrid: a dragon head with a jagged-tooth snout and a crown of spikes, huge
                 horns, a curly white mane, glossy black muscles, an ornate chest band, studded cuffs,
                 claws, dragon legs, bat wings, a spiked tail, and Ragnir (a long white-wrapped pole with a
                 block head).
  character/loki Loki himself: magenta hair with two thick braids, wide-rimmed black helmet with long horns
                 (the left one wrapped), bandaged eyes, Viking clothes, Ragnir.

Run: python3 tools/meshes/gen_vox.py [names...] [--preview DIR]   (from anywhere)
"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshkit import hexc, mix, shade, catmull, norm  # noqa: E402
from voxkit import Vox  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'main', 'resources', 'assets', 'onepiece', 'meshes')
V = np.array
SIDES = (1, -1)


def sx(p, s):
    return V([p[0] * s, p[1], p[2]], dtype=float)


def glow(c):
    c = hexc(c)
    return (c[0], c[1], c[2], 1)


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


def loft(v, bone, rings, color, mode='fill'):
    """A solid body from (y, half-width, front depth, back depth[, z centre]) rings, straight between rings."""
    R = [list(r) + [0.0] * (5 - len(r)) for r in rings]
    ys = [r[0] for r in R]
    lo = V([-max(r[1] for r in R), min(ys), min(r[4] - r[2] for r in R)]) - v.px
    hi = V([max(r[1] for r in R), max(ys), max(r[4] + r[3] for r in R)]) + v.px
    idx, cen = v._range(lo, hi)
    y = cen[:, 1]
    w = np.interp(y, ys, [r[1] for r in R])
    df = np.interp(y, ys, [r[2] for r in R])
    db = np.interp(y, ys, [r[3] for r in R])
    cz = np.interp(y, ys, [r[4] for r in R])
    dz = cen[:, 2] - cz
    d = np.where(dz < 0, df, db)
    m = (cen[:, 0] / w) ** 2 + (dz / d) ** 2 <= 1.0
    m &= (y >= min(ys)) & (y <= max(ys))
    v._set(bone, idx[m], cen[m], color, mode=mode)


def grin_paint(cx, cy, cz_max, w, h, mouth, tooth, n, zig=True, lift=0.0, px=1 / 16):
    """Colour function for painting a grin onto a face: black crescent with zigzag (or square) teeth."""
    step = 2 * w / n

    def top(x):
        s = (x - cx) / w
        return cy + h * (0.25 + 0.75 * s * s) + lift * s * s

    def bot(x):
        s = (x - cx) / w
        return cy + h * (-0.75 + 1.75 * s * s) + lift * s * s

    def f(p, u):
        x, y, z = p
        if z > cz_max or abs((x - cx) / w) > 1.0:
            return None
        t, b = top(x), bot(x)
        if not (b <= y <= t):
            return None
        mid = (t + b) / 2
        depth = t - b
        k = ((x - cx + w) / step) % 1.0
        if zig:
            # pixel zigzag: the row by each lip is all teeth, the next row only every other pixel
            col = int(math.floor(x / px))
            rt = (t - y) / px
            rb = (y - b) / px
            if rt < 1.0 or (rt < 2.0 and col % 3 != 0):
                return tooth
            if rb < 1.0 or (rb < 2.0 and col % 3 != 1):
                return tooth
        else:
            if 0.15 < k < 0.85 and (y > mid + depth * 0.06 or y < mid - depth * 0.06):
                return tooth
        return mouth
    return f


def eye_paint(cx, cy, r, rings, zmax=None):
    """Concentric round eye painted on a front face: rings = [(fraction, colour), ...] outermost first."""
    def f(p, u):
        if zmax is not None and p[2] > zmax:
            return None
        d = math.hypot(p[0] - cx, p[1] - cy) / r
        col = None
        for frac, c in rings:
            if d <= frac:
                col = c
        return col
    return f


def feather_wing(v, bone, s, root, span, dark, mid, count=(8, 10, 11), back=0.0):
    """Big bird wing of flat feathers fanned out to side s; the wing lies in the x-y plane."""
    r = V(root, dtype=float)
    lead = [r, r + V([s * span * 0.3, span * 0.3, back]), r + V([s * span * 0.65, span * 0.45, back]), r + V([s * span, span * 0.32, back])]
    edge = catmull(lead, 10)
    v.tube(bone, lead, [span * 0.06, span * 0.05, span * 0.035, span * 0.015], dark, per=5)

    def at(t):
        return edge[min(int(t * (len(edge) - 1)), len(edge) - 1)]
    layers = [(count[0], 0.3, 0.05, -0.0), (count[1], 0.58, 0.065, 0.0), (count[2], 1.0, 0.085, 0.0)]
    for li, (n, lf, wf, _) in enumerate(layers):
        for i in range(n):
            t = (i + 0.5) / n
            if li == 2:
                t = 0.35 + 0.65 * t
            base = at(t) + V([0, 0, back + v.px * (2 - li)])
            ang = math.radians(-90 + 72 * t ** 1.4)
            d = norm(V([s * math.cos(ang), math.sin(ang), 0.0]))
            L = span * lf * (0.55 + 0.6 * t if li == 2 else 0.7 + 0.35 * t)
            wid = span * wf * (0.8 + 0.4 * t)
            side = norm(np.cross(V([0, 0, 1.0]), d))
            col = mid if (i + li) % 2 else dark

            def fn(u, w, base=base, d=d, L=L, wid=wid, side=side):
                prof = math.sin(math.pi * min(1.0, u * 1.15)) ** 0.6 if u < 0.87 else (1 - u) / 0.13 * 0.6
                return base + d * L * u + side * (w * 2 - 1) * wid * max(prof, 0.05)
            v.sheet(bone, fn, col)


def bat_wing(v, bone, s, root, k, bone_col, skin_col, claw_col):
    r = V(root, dtype=float)
    elbow = r + V([s * 1.6 * k, 1.3 * k, 1.1 * k])
    wrist = r + V([s * 3.3 * k, 2.0 * k, 1.0 * k])
    tips = [r + V([s * 6.4 * k, 1.3 * k, 1.4 * k]), r + V([s * 6.0 * k, -1.2 * k, 1.7 * k]),
            r + V([s * 4.6 * k, -3.0 * k, 1.6 * k]), r + V([s * 2.6 * k, -3.6 * k, 1.2 * k])]
    body_edge = r + V([s * 0.2 * k, -3.2 * k, 0.2 * k])
    v.tube(bone, [r, elbow, wrist], [0.34 * k, 0.26 * k, 0.2 * k], bone_col, per=4)
    v.ball(bone, wrist, (0.22 * k, 0.22 * k, 0.22 * k), bone_col)
    v.tube(bone, [wrist + V([0, 0.1 * k, 0]), wrist + V([s * 0.35 * k, 1.0 * k, -0.2 * k])], [0.14 * k, 0.0], claw_col, smooth=False)
    fingers = []
    for t in tips:
        mid = wrist + (t - wrist) * 0.5 + V([0, 0.15 * k, 0.1 * k])
        v.tube(bone, [wrist, mid, t], [0.13 * k, 0.09 * k, 0.04 * k], bone_col, per=4)
        v.tube(bone, [t, t + norm(t - mid) * 0.5 * k], [0.08 * k, 0.0], claw_col, smooth=False)  # a spike at each finger tip
        fingers.append((wrist, mid, t))

    def along(f, q):
        a, b, c = f
        return a + (b - a) * (q * 2) if q < 0.5 else b + (c - b) * (q * 2 - 1)
    for i in range(len(fingers) - 1):
        fa, fb = fingers[i], fingers[i + 1]

        def fn(u, q, fa=fa, fb=fb):
            p = along(fa, q) * (1 - u) + along(fb, q) * u
            return p + (wrist - p) * math.sin(math.pi * u) * q ** 1.5 * 0.35
        v.sheet(bone, fn, skin_col)
    fl = fingers[-1]

    def fn2(u, q):
        p = along(fl, q) * (1 - u) + (r + (body_edge - r) * q) * u
        return p + (r + (wrist - r) * 0.4 - p) * math.sin(math.pi * u) * q ** 1.5 * 0.25
    v.sheet(bone, fn2, skin_col)

    def fn3(u, q):
        pa = r + (wrist - r) * q + V([0, 0.25 * k * math.sin(math.pi * q), 0])
        return pa * (1 - u * 0.25) + along(fingers[0], q) * (u * 0.25)
    v.sheet(bone, fn3, skin_col)


def ragnir(v, bone, x, z, y_head, y_top, k, pole='#3a2a1e', band='#f2f0e8', head='#2c2c32', rim='#c8a860'):
    """Ragnir: a long pole wrapped in white bands, a big block head resting on the ground."""
    hs = 0.7 * k
    v.box(bone, (x - hs, y_head, z - hs), (x + hs, y_head + hs * 2, z + hs), head)
    for yy in (y_head + 0.12 * k, y_head + hs * 2 - 0.22 * k):
        v.box(bone, (x - hs - v.px, yy, z - hs - v.px), (x + hs + v.px, yy + 0.12 * k, z + hs + v.px), rim)
    v.box(bone, (x - hs * 0.4, y_head + hs * 0.6, z - hs - v.px), (x + hs * 0.4, y_head + hs * 1.4, z + hs + v.px), rim)
    top = y_head + hs * 2
    r = max(0.12 * k, v.px)
    L = y_top - top

    def pole_c(p, u):
        q = (p[1] - top) / L
        return hexc(band) if 0.05 < q < 0.85 and int(q * 26) % 2 == 0 else hexc(pole)
    v.box(bone, (x - r, top, z - r), (x + r, y_top, z + r), pole_c)
    v.box(bone, (x - r * 1.6, y_top - r, z - r * 1.6), (x + r * 1.6, y_top + r * 2, z + r * 1.6), rim)


def hand(v, bone, wrist, s, k, skin, claw=None, curl=0.5, fingers=4):
    w = V(wrist, dtype=float)
    pc = w + V([0, -0.07 * k, -0.01 * k])
    v.ball(bone, pc, (0.05 * k, 0.08 * k, 0.07 * k), skin)
    for i in range(fingers):
        zf = (-0.05 + 0.1 * i / max(fingers - 1, 1)) * k
        base = pc + V([0.005 * s * k, -0.06 * k, zf])
        L = (0.09 - 0.012 * abs(i - 1.3)) * k
        mid = base + V([-s * 0.01 * k, -L * 0.6, -0.005 * k])
        tip = mid + V([-s * 0.03 * k * curl, -L * 0.5, -0.01 * k])
        v.tube(bone, [base, mid, tip], [0.02 * k, 0.017 * k, 0.014 * k], skin, per=2)
        if claw:
            d = norm(tip - mid)
            v.tube(bone, [tip, tip + d * 0.05 * k], [0.014 * k, 0.0], claw, smooth=False)
    tb = pc + V([-s * 0.035 * k, -0.01 * k, -0.055 * k])
    v.tube(bone, [tb, tb + V([-s * 0.02 * k, -0.06 * k, -0.025 * k])], [0.02 * k, 0.015 * k], skin, smooth=False)


# ---------------- Luffy: feral black Nika (hunched ape) ----------------

def nika():
    v = Vox(1 / 16, noise=0.05, seed=3)
    BLACK = hexc('#17171c')
    DARK = hexc('#26262e')
    WHITE = hexc('#f6f6f8')
    GREY = hexc('#c9ccd6')
    cloud = lambda p, u: WHITE if p[1] % 0.25 > 0.07 else GREY
    v.bone('body', 'root', (0, 0.9, 0.05))
    v.bone('head', 'body', (0, 1.6, -0.3))
    v.bone('arm_r', 'body', (0.33, 1.52, -0.2))
    v.bone('arm_l', 'body', (-0.33, 1.52, -0.2))
    v.bone('leg_r', 'root', (0.16, 0.85, 0.05))
    v.bone('leg_l', 'root', (-0.16, 0.85, 0.05))
    v.bone('tail', 'body', (0, 0.9, 0.2))
    humanoid_anims(v, walk_leg=30, walk_arm=30, attack=120, roar_arms=60)
    v.anim('tail', 'idle', 'y', 18, 1.6)
    v.anim('body', 'idle', 'up', 0.02, 1.4)
    v.anim('head', 'idle', 'z', 5, 2.2)
    # hunched torso: round back, chest pushed forward
    v.tube('body', [V([0, 0.88, 0.06]), V([0, 1.2, 0.02]), V([0, 1.45, -0.1]), V([0, 1.58, -0.22])], [0.2, 0.23, 0.27, 0.24], BLACK, per=4)
    v.ball('body', V([0, 1.42, 0.02]), (0.3, 0.25, 0.26), BLACK)  # hunched shoulders and back
    v.ball('body', V([0, 1.05, -0.06]), (0.2, 0.17, 0.17), DARK)  # belly
    # cloud scarf round the neck, sash at the waist
    for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
        v.ball('body', V([math.sin(a) * 0.24, 1.6 + 0.03 * math.sin(a * 3), -0.22 - math.cos(a) * 0.16]), (0.09, 0.08, 0.09), cloud)
    for a in np.linspace(0, 2 * math.pi, 10)[:-1]:
        v.ball('body', V([math.sin(a) * 0.22, 0.9, 0.05 - math.cos(a) * 0.17]), (0.07, 0.06, 0.07), cloud)
    # short bent legs
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        v.tube(b, [sx((0.16, 0.85, 0.05), s), sx((0.21, 0.47, -0.12), s), sx((0.19, 0.1, 0.04), s)], [0.12, 0.1, 0.085], BLACK, per=3)
        v.ball(b, sx((0.19, 0.06, -0.06), s), (0.1, 0.07, 0.17), BLACK)
        for a in np.linspace(0, 2 * math.pi, 6)[:-1]:
            v.ball(b, sx((0.19 + 0.1 * math.sin(a), 0.17, 0.02 - 0.1 * math.cos(a)), s), (0.05, 0.045, 0.05), cloud)
    # long ape arms reaching the ground, black with white cloud swirls
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((0.33, 1.52, -0.2), s), sx((0.46, 1.08, -0.3), s), sx((0.44, 0.42, -0.34), s)

        def armc(p, u, sh=sh, wr=wr):
            d = norm(wr - sh)
            q = p - sh
            off = q - d * (q @ d)
            ang = math.atan2(off[2], off[0] * s)
            band = (u * 2.6 + ang / (2 * math.pi)) % 1.0
            return WHITE if band < 0.2 else BLACK
        v.ball(b, sh, (0.13, 0.12, 0.13), BLACK)
        v.tube(b, [sh, el, wr], [0.1, 0.09, 0.08], armc, per=4)
        # big black glove hand, knuckles down
        hc = wr + V([0, -0.1, -0.02])
        v.ball(b, hc, (0.11, 0.1, 0.12), BLACK)
        for i in range(4):
            f0 = hc + V([0, -0.05, -0.08 + 0.055 * i])
            v.tube(b, [f0, f0 + V([0, -0.09, -0.04]), f0 + V([0, -0.12, -0.1])], [0.035, 0.032, 0.03], BLACK, per=2)
        v.tube(b, [hc + V([-s * 0.07, 0, -0.08]), hc + V([-s * 0.1, -0.06, -0.16])], [0.035, 0.03], BLACK, smooth=False)
        # white cloud swirl on the back of the hand
        def swirl(p, u, hc=hc):
            if (p[0] - hc[0]) * s < 0.06:
                return None
            dy, dz = p[1] - hc[1], p[2] - hc[2]
            rr = math.hypot(dy, dz)
            a = math.atan2(dz, dy)
            return WHITE if (rr / 0.09 * 2 * math.pi - a) % (2 * math.pi) < 2.4 and rr < 0.1 else None
        v.ball(b, hc, (0.13, 0.12, 0.14), swirl, mode='paint')
        v.ball(b, wr + V([0, 0.05, 0]), (0.11, 0.06, 0.11), cloud)  # cloud cuff
    # head: big round white cloud; a huge black grin across the lower face
    hc = V([0, 1.85, -0.42])
    v.ball('head', hc, (0.42, 0.42, 0.36), WHITE)
    rnd = random.Random(7)
    for i in range(16):
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(0.0, 1.2)
        d = V([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
        if d[2] < -0.3 and d[1] < 0.6:
            continue
        v.ball('head', hc + d * V([0.42, 0.38, 0.36]), (0.12, 0.11, 0.12), cloud)
    v.ball('head', hc + V([0, -0.08, -0.04]), (0.43, 0.36, 0.37), grin_paint(0, 1.76, -0.5, 0.38, 0.4, BLACK, glow('#ffffff'), 5, zig=True, lift=0.0), mode='paint')
    # eyes: black with glowing white pupils and red rims (Gear 5)
    for s in SIDES:
        v.ball('head', hc + V([0.12 * s, 0.12, -0.05]), (0.08, 0.07, 0.31),
               eye_paint(0.12 * s, hc[1] + 0.12, 0.075, [(1.0, (190, 20, 20)), (0.75, BLACK), (0.4, glow('#ffffff'))], zmax=-0.62), mode='paint')
    # ape nose: a little snout block with two nostrils
    v.box('head', (-0.07, 1.92, -0.79), (0.07, 2.0, -0.7), GREY)
    v.box('head', (-0.05, 1.925, -0.8), (-0.01, 1.95, -0.78), BLACK)
    v.box('head', (0.01, 1.925, -0.8), (0.05, 1.95, -0.78), BLACK)
    # tail curling up behind
    tp = [V([0, 0.9, 0.2]), V([0, 0.75, 0.45]), V([0.05, 0.95, 0.7]), V([0.1, 1.3, 0.72]), V([0.06, 1.5, 0.6])]
    v.tube('tail', tp, [0.06, 0.055, 0.05, 0.04, 0.035], BLACK, per=4)
    v.ball('tail', V([0.06, 1.55, 0.58]), (0.08, 0.07, 0.08), cloud)
    return v


# ---------------- Imu: chapter 1198 form ----------------

def imu_beast():
    v = Vox(0.05, noise=0.04, seed=5)
    BLACK = hexc('#0e0d12')
    DARK = hexc('#1e1c26')
    WHITE = hexc('#efede6')
    LINE = hexc('#2a2a32')
    v.bone('body', 'root', (0, 2.2, 0))
    v.bone('head', 'body', (0, 4.5, 0))
    v.bone('arm_r', 'body', (0.75, 4.2, 0))
    v.bone('arm_l', 'body', (-0.75, 4.2, 0))
    v.bone('wing_r', 'body', (0.4, 4.1, 0.55))
    v.bone('wing_l', 'body', (-0.4, 4.1, 0.55))
    v.bone('halo', 'body', (0, 6.6, 0.45))
    v.bone('flame', 'head', (0, 5.9, 0))
    v.anim('body', 'idle', 'up', 0.08, 4.0)
    v.anim('head', 'look', 'y', 0.6)
    v.anim('head', 'look', 'x', 0.4)
    v.anim('head', 'roar', 'x', 15)
    v.anim('arm_r', 'attack', 'x', 85)
    v.anim('arm_l', 'attack', 'x', 85)
    v.anim('body', 'attack', 'y', -15)
    v.anim('flame', 'idle', 'y', 25, 1.4)
    v.anim('halo', 'idle', 'z', 6, 7.0)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        v.anim(b, 'idle', 'z', 12 * s, 2.8)
        v.anim(b, 'fly', 'z', 12 * s, 1.0)
        v.anim(b, 'roar', 'z', 20 * s)

    # big white cloak with thin dark stripes, sharp wide shoulders, open down the front over a black body
    rings = [(0.0, 1.6, 0.8, 0.85), (1.5, 1.45, 0.72, 0.8), (3.2, 1.45, 0.66, 0.75), (4.3, 1.8, 0.62, 0.7), (4.65, 1.85, 0.55, 0.6), (4.85, 1.0, 0.45, 0.5), (5.0, 0.45, 0.3, 0.35)]

    def open_w(y):
        return 0.9 - min(max(y, 0), 4.6) / 4.6 * 0.5

    def cloak_c(p, u):
        x, y, z = p
        if z < -0.05 and abs(x) < open_w(y):
            return BLACK
        side = abs(x) > 1.3
        coord = z if side else x
        return LINE if int(math.floor(coord / 0.1)) % 3 == 0 else WHITE
    loft(v, 'body', rings, cloak_c)
    # pointed shoulder tips
    for s in SIDES:
        v.box('body', sx((1.75, 4.45, -0.35), s) if s > 0 else (-2.1, 4.45, -0.35), (2.1, 4.65, 0.4) if s > 0 else (-1.75, 4.65, 0.4), WHITE)
    # the column of white dots down the black front
    for i in range(14):
        y = 2.2 + i * 0.2
        v.box('body', (-0.05, y, -2), (0.05, y + 0.08, 0), glow('#ffffff'), mode='paint')
    # a white skull near the hem and a big ringed eye at the waist
    df0 = 0.8
    v.ball('body', (0, 0.65, -df0 + 0.05), (0.24, 0.22, 0.2), WHITE)
    for s in SIDES:
        v.box('body', (0.04 * s, 0.65, -1.2) if s > 0 else (-0.14, 0.65, -1.2), (0.14, 0.75, 0) if s > 0 else (-0.04, 0.75, 0), BLACK, mode='paint')
    v.box('body', (-0.15, 0.45, -1.2), (0.15, 0.52, 0), BLACK, mode='paint')

    def ring_eye(p, u):
        r = math.hypot(p[0] - 0.4, p[1] - 1.7)
        if r < 0.1:
            return BLACK
        if r < 0.32:
            return WHITE if r > 0.2 else BLACK
        return None
    v.box('body', (0.05, 1.35, -2), (0.75, 2.05, 0), ring_eye, mode='paint')
    # long white veil of hair falling from the head over the shoulders, ragged at the bottom
    rnd = random.Random(11)
    for s in SIDES:
        for c in range(4, 10):
            x = s * (c * 0.1 + 0.05)
            bottom = 2.6 + rnd.uniform(0, 0.45) + (c - 4) * 0.05
            col = LINE if c == 6 else WHITE
            z0 = -0.95
            v.box('body', (x - 0.04, bottom, z0), (x + 0.04, 5.6 - (c - 4) * 0.05, z0 + 0.2), col)
        # the veil's outer edge wraps back round the side of the head
        v.box('body', sx((0.85, 3.0, -0.75), s) if s > 0 else (-0.95, 3.0, -0.75), (0.95, 5.2, -0.1) if s > 0 else (-0.85, 5.2, -0.1), WHITE)
    # black sleeves coming out of the cloak, black gloves with a white eye ring at the wrist
    for s, b, wr in ((1, 'arm_r', V([0.25, 3.15, -1.0])), (-1, 'arm_l', V([-0.25, 2.95, -1.0]))):
        sh, el = sx((0.55, 4.3, -0.2), s), sx((0.8, 3.5, -0.7), s)
        v.tube(b, [sh, el, wr], [0.22, 0.2, 0.17], BLACK, per=4)
        v.ball(b, wr + V([-s * 0.05, 0, -0.08]), (0.17, 0.15, 0.17), BLACK)
        v.ball(b, wr + V([s * 0.12, 0.0, -0.05]), (0.1, 0.16, 0.16), WHITE, mode='paint')
    # the long straight sword held across the body, blade up to his left, handle down to his right
    hilt = V([0.05, 3.05, -1.15])
    tip = V([-3.0, 4.2, -1.25])
    d = norm(tip - hilt)
    v.tube('arm_r', [hilt - d * 0.9, hilt + d * 0.2], 0.06, BLACK, smooth=False)
    up = norm(np.cross(d, V([0, 0, 1.0])))

    def blade(u, w):
        return hilt + d * (0.3 + u * (np.linalg.norm(tip - hilt) - 0.3)) + up * (w - 0.5) * 0.14 * (1 - u * 0.5)
    v.sheet('arm_r', blade, lambda p, u: hexc('#f4f6fa') if u < 0.97 else hexc('#b8c0d0'), nv=3)
    # small narrow black head with a neck, a face like the chapter image: almond eyes, a scar down his
    # left eye, a thin smile, a pointed goatee, and the light catching the right side of his face
    v.box('head', (-0.12, 4.8, -0.5), (0.12, 5.2, -0.2), BLACK)
    v.ball('head', (0, 5.3, -0.75), (0.4, 0.6, 0.4), BLACK)
    LIT = hexc('#cfccc4')
    SCAR = glow('#ffffff')

    def face(p, u):
        x, y, z = p
        if z > -0.82:
            return None
        if abs(x - 0.15) < 0.03 and 5.02 < y < 5.85:
            return SCAR
        for ex in (0.15, -0.15):
            dx, dy = (x - ex) / 0.11, (y - 5.36) / 0.055
            if dx * dx + dy * dy <= 1.0:
                return BLACK if abs(x - ex) < 0.03 else glow('#f4f4f4')
        if abs(x) < 0.13 and 4.95 < y < 5.0:
            return glow('#e8e6e0')
        if 0.12 < abs(x) < 0.17 and 5.0 < y < 5.05:
            return glow('#e8e6e0')
        if x < -0.26 and y > 4.9:
            return LIT
        return None
    v.ball('head', (0, 5.3, -0.75), (0.41, 0.61, 0.41), face, mode='paint')
    v.tube('head', [V([0, 4.85, -1.02]), V([0, 4.55, -1.08]), V([0.02, 4.25, -1.05])], [0.11, 0.07, 0.0], hexc('#3a3844'), per=4)
    # white helmet over the top of the head; the horns grow out of its sides
    HELM = hexc('#ecebe6')
    HELM2 = hexc('#c9c6be')
    helm_c = lambda p, u: HELM2 if p[1] < 5.52 else HELM
    v.ball('head', (0, 5.6, -0.72), (0.48, 0.45, 0.46), helm_c, cut=('y', 1, 5.47))
    v.ball('head', (0, 5.9, -0.72), (0.36, 0.22, 0.36), helm_c)  # crown, where the flame rises
    for s in SIDES:
        v.ball('head', (0.38 * s, 5.75, -0.68), (0.2, 0.3, 0.26), helm_c)  # side plates that become the horn roots
        v.ball('head', (0.42 * s, 5.35, -0.7), (0.08, 0.18, 0.2), helm_c)  # cheek guards down the sides of the face
    # huge black crescent horns, open at the top, rising out of the helmet
    for s in SIDES:
        hp = [V([0.38 * s, 5.8, -0.68]), V([0.85 * s, 5.9, -0.5]), V([1.4 * s, 6.25, -0.4]), V([1.7 * s, 6.9, -0.4]), V([1.6 * s, 7.55, -0.4]), V([1.3 * s, 8.0, -0.4])]
        v.tube('head', hp, [0.22, 0.27, 0.26, 0.2, 0.12, 0.04], BLACK, per=5)
        # white collar where each horn leaves the helmet
        v.tube('head', [V([0.5 * s, 5.82, -0.64]), V([0.62 * s, 5.85, -0.58])], 0.3, helm_c, smooth=False)
    # white flame above the head, between the horns
    for k in range(3):
        ph = k * 2.1
        pts = [V([0.3 * math.sin(ph + t * 5) * (1 - t * 0.5), 6.0 + t * 1.6, -0.4 + 0.2 * math.cos(ph + t * 5) * (1 - t * 0.5)]) for t in np.linspace(0, 1, 8)]
        v.tube('flame', pts, [0.22, 0.24, 0.2, 0.16, 0.12, 0.08, 0.05, 0.02], glow('#f8f8ff'), per=2)
    # ring of eyes behind him
    hcen = V([0, 6.6, 0.45])
    ring = [hcen + V([math.sin(a) * 3.0, math.cos(a) * 3.0, 0]) for a in np.linspace(0, 2 * math.pi, 57)]
    v.tube('halo', ring, 0.17, hexc('#2a2733'), per=1, smooth=False)
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        c = hcen + V([math.sin(a) * 3.0, math.cos(a) * 3.0, -0.2])
        v.ball('halo', c, (0.26, 0.2, 0.1), WHITE)
        v.ball('halo', c + V([0, 0, -0.06]), (0.12, 0.12, 0.08), BLACK)
    # huge dark feathered wings
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        feather_wing(v, b, s, sx((0.4, 4.3, 0.75), s), 3.3, DARK, hexc('#2e2b38'), count=(9, 11, 12))
    # black clouds full of eyes on both sides
    for i, (wy, wx) in enumerate([(2.2, 2.6), (3.5, 2.9), (4.8, 2.5)]):
        for s in SIDES:
            b = v.bone('cloud%d%s' % (i, 'r' if s > 0 else 'l'), 'root', (wx * s, wy, 0.2))
            v.anim(b, 'idle', 'up', 0.15, 3.0 + i * 0.6, i + (s > 0))
            rnd = random.Random(40 + i * 3 + s)
            for j in range(6):
                c = V([s * (wx - 1.1 + j * 0.45), wy + rnd.uniform(-0.12, 0.12), 0.2 + rnd.uniform(-0.1, 0.1)])
                v.ball(b, c, (0.32, 0.26, 0.28), BLACK)
            for j in range(4):
                ex = s * (wx - 0.9 + j * 0.6)
                v.ball(b, V([ex, wy, -0.05]), (0.17, 0.12, 0.08), WHITE)
                v.ball(b, V([ex, wy, -0.1]), (0.07, 0.07, 0.06), BLACK)
    # finer detail for the 40-block giant: cloth folds and fine strands in the white, a dark hem
    def cloth(p, c):
        x, y, z = p
        k = math.sin(x * 9.0 + y * 0.6) * 0.5 + math.sin(z * 11.0) * 0.3
        if y < 0.2:
            return LINE
        return hexc('#ffffff') if k > 0.4 else (hexc('#c2beb5') if k < -0.4 else None)
    v.retex(['body'], [WHITE], cloth)
    v.retex(['body'], [hexc('#ffffff')], lambda p, c: hexc('#c4c0b8') if int(p[0] / 0.05) % 5 == 0 and p[2] < -0.8 else None)
    v.box('arm_r', V([0.05, 3.05, -1.15]) + V([-0.06, -0.2, -0.06]), V([0.05, 3.05, -1.15]) + V([0.06, 0.2, 0.06]), hexc('#d8d4cc'))

    return v


# ---------------- Imu: devil form (chapter 1191) ----------------

def imu_demon():
    v = Vox(1 / 12, noise=0.05, seed=9)
    SKIN = hexc('#3a3444')
    SKIN2 = hexc('#4c4558')
    HAIR = hexc('#e4dfee')
    HAIR2 = hexc('#bcb4cc')
    CLOAK = hexc('#1f1a26')
    CLOAK_IN = hexc('#6a1420')
    TROUS = hexc('#2a2232')
    BONE = hexc('#ece4d2')
    BLACK = hexc('#0b090e')
    v.bone('body', 'root', (0, 2.45, 0))
    v.bone('head', 'body', (0, 4.35, -0.05))
    v.bone('arm_r', 'body', (0.85, 4.0, 0))
    v.bone('arm_l', 'body', (-0.85, 4.0, 0))
    v.bone('leg_r', 'root', (0.3, 2.4, 0))
    v.bone('leg_l', 'root', (-0.3, 2.4, 0))
    v.bone('tail', 'body', (0, 2.45, 0.35))
    v.bone('wing_r', 'body', (0.3, 3.95, 0.45))
    v.bone('wing_l', 'body', (-0.3, 3.95, 0.45))
    v.bone('halo', 'head', (0, 4.75, 0.55))
    humanoid_anims(v, walk_leg=22, walk_arm=16, attack=115, roar_arms=50)
    v.anim('tail', 'idle', 'y', 14, 2.4)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        v.anim(b, 'idle', 'z', 6 * s, 3.0)
        v.anim(b, 'roar', 'z', 25 * s)
        v.anim(b, 'fly', 'z', 30 * s, 0.9)
    v.anim('halo', 'idle', 'z', 8, 6.0)
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        v.tube(b, [sx((0.3, 2.4, 0), s), sx((0.34, 1.25, -0.08), s), sx((0.33, 0.2, 0.02), s)], [0.27, 0.22, 0.18], TROUS, per=3)
        v.ball(b, sx((0.33, 0.1, -0.12), s), (0.15, 0.1, 0.28), SKIN)
        for i in range(3):
            base = sx((0.24 + 0.09 * i, 0.06, -0.38), s)
            v.tube(b, [base, base + V([0, -0.03, -0.12])], [0.04, 0.0], BONE, smooth=False)

    def torso_c(p, u):
        if p[2] < -0.3 and 2.9 < p[1] < 3.6 and (abs(p[0]) < 0.04 or abs(p[1] - 3.15) < 0.04 or abs(p[1] - 3.4) < 0.04):
            return SKIN2
        return SKIN
    loft(v, 'body', [(2.3, 0.5, 0.33, 0.35), (2.95, 0.42, 0.32, 0.3), (3.35, 0.5, 0.36, 0.32), (3.75, 0.68, 0.42, 0.36),
                     (4.05, 0.8, 0.36, 0.36), (4.15, 0.3, 0.22, 0.22), (4.4, 0.17, 0.16, 0.16)], torso_c)
    for s in SIDES:
        v.ball('body', sx((0.27, 3.72, -0.3), s), (0.27, 0.2, 0.15), SKIN2)

    # cloak from the shoulders to the calves, open at the front, red inside
    def cloak_fn(u, q):
        a = math.radians(-128 + 256 * u)
        return V([math.sin(a) * (0.9 + q * 0.45), 4.1 - q * 3.3, math.cos(a) * (0.5 + q * 0.4) + 0.05])
    v.sheet('body', cloak_fn, lambda p, u: CLOAK_IN if (u < 0.06 or u > 0.94) else CLOAK, thick=2)
    loft(v, 'body', [(3.95, 0.92, 0.42, 0.45), (4.12, 0.88, 0.4, 0.42), (4.22, 0.5, 0.3, 0.3)], CLOAK)

    def skull(b, c, k):
        c = V(c, dtype=float)
        v.ball(b, c, (0.13 * k, 0.12 * k, 0.1 * k), BONE)
        v.ball(b, c + V([0, -0.1 * k, -0.02 * k]), (0.08 * k, 0.05 * k, 0.07 * k), BONE)
        for s in SIDES:
            v.box(b, c + V([0.03 * s - 0.035, -0.02, -0.12 * k]), c + V([0.03 * s + 0.035, 0.04, -0.07 * k]), BLACK)
            hb = c + V([0.1 * s * k, 0.07 * k, -0.02 * k])
            v.tube(b, [hb, hb + V([0.1 * s * k, 0.08 * k, 0]), hb + V([0.12 * s * k, 0.2 * k, -0.03 * k])], [0.035 * k, 0.025 * k, 0.0], BONE, per=2)
    skull('body', (0.0, 3.25, -0.42), 1.3)
    skull('body', (0.0, 2.55, -0.45), 1.1)
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        skull(b, sx((0.95, 4.22, -0.05), s), 1.2)
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((0.9, 4.0, 0), s), sx((1.25, 3.3, -0.1), s), sx((1.35, 2.6, -0.35), s)
        v.ball(b, sh, (0.28, 0.26, 0.28), SKIN)
        v.tube(b, [sh, el, wr], [0.22, 0.17, 0.13], SKIN, per=3)
        hand(v, b, wr, s, 2.4, SKIN, claw=BONE)
    hc = V([0, 4.62, -0.05])
    v.ball('head', hc, (0.21, 0.26, 0.24), SKIN)
    v.ball('head', hc + V([0, -0.15, -0.08]), (0.15, 0.11, 0.15), SKIN)
    for s in SIDES:
        v.ball('head', hc + V([0.085 * s, 0.03, 0]), (0.07, 0.07, 0.3),
               eye_paint(0.085 * s, hc[1] + 0.03, 0.065, [(1.0, BLACK), (0.85, glow('#ff2a1a')), (0.55, BLACK), (0.3, glow('#ff6a3a'))], zmax=-0.2), mode='paint')
    v.ball('head', hc + V([0, -0.1, 0]), (0.13, 0.06, 0.3), grin_paint(0, 4.52, -0.25, 0.1, 0.05, BLACK, BONE, 5, px=1 / 12), mode='paint')
    v.tube('head', [hc + V([0, -0.26, -0.16]), hc + V([0, -0.4, -0.18]), hc + V([0, -0.52, -0.12])], [0.055, 0.04, 0.0], HAIR, per=2)
    rnd = random.Random(31)
    for i in range(30):
        a = rnd.uniform(-2.3, 2.3)
        root = hc + V([math.sin(a) * 0.2, 0.18, math.cos(a) * 0.2 + 0.03])
        L = rnd.uniform(1.4, 2.3)
        sw = rnd.uniform(-0.12, 0.12)
        pts = [root, root + V([math.sin(a) * 0.12, 0.04, 0.12]), root + V([math.sin(a) * 0.25 + sw, -L * 0.4, 0.3]), root + V([math.sin(a) * 0.4 + sw * 2, -L, 0.45])]
        v.tube('head', pts, [0.07, 0.07, 0.06, 0.03], HAIR if i % 3 else HAIR2, per=3)
    v.ball('head', hc + V([0, 0.07, 0.03]), (0.225, 0.23, 0.235), HAIR, cut=('y', 1, hc[1] + 0.02))
    for s in SIDES:
        base = hc + V([0.17 * s, 0.1, 0.0])
        curl = [base]
        for t in np.linspace(0, 1.6 * math.pi, 7)[1:]:
            rr = 0.17 * (1 - t / (2.2 * math.pi))
            curl.append(base + V([s * (0.08 + rr * (1 - math.cos(t)) * 0.7 + t * 0.02), rr * math.sin(t), -rr * (1 - math.cos(t)) * 0.4 + 0.05]))
        v.tube('head', curl, [0.075, 0.065, 0.055, 0.04, 0.03, 0.02, 0.0], hexc('#2a2420'), per=2)
        b2 = hc + V([0.1 * s, 0.2, 0.02])
        v.tube('head', [b2, b2 + V([0.25 * s, 0.22, 0.05]), b2 + V([0.45 * s, 0.6, 0.0]), b2 + V([0.4 * s, 0.95, -0.1]), b2 + V([0.28 * s, 1.15, -0.12])],
               [0.085, 0.075, 0.06, 0.035, 0.0], BLACK, per=3)
    hcen = V([0, 4.75, 0.55])
    for i in range(16):
        a = 2 * math.pi * i / 16
        d = V([math.sin(a), math.cos(a), 0.0])
        base = hcen + d * 1.1
        v.tube('halo', [base - d * 0.12, base + d * 0.25 + V([math.cos(a), -math.sin(a), 0]) * 0.06, hcen + d * 1.7 + V([math.cos(a), -math.sin(a), 0]) * 0.14],
               [0.15, 0.1, 0.0], BLACK, per=2)
        v.ball('halo', base - V([0, 0, 0.06]), (0.12, 0.12, 0.06), hexc('#f2ece8'))
        v.ball('halo', base - V([0, 0, 0.1]), (0.07, 0.07, 0.05), glow('#e01818'))
    v.tube('halo', [hcen + V([math.sin(a) * 1.05, math.cos(a) * 1.05, 0]) for a in np.linspace(0, 2 * math.pi, 33)], 0.07, BLACK, per=1, smooth=False)
    tp = [V([0, 2.45, 0.35]), V([0, 1.9, 0.85]), V([0.3, 1.0, 1.25]), V([0.7, 0.35, 1.5]), V([1.3, 0.12, 1.6]), V([1.9, 0.25, 1.5])]
    v.tube('tail', tp, [0.13, 0.11, 0.09, 0.07, 0.05, 0.035], SKIN, per=4)
    tip = V([1.9, 0.25, 1.5])
    dd = norm(tip - V([1.3, 0.12, 1.6]))
    v.sheet('tail', lambda u, w: tip + dd * (u * 0.4) + V([0, 1.0, 0]) * (w - 0.5) * 0.34 * (1 - u), SKIN, thick=2)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        feather_wing(v, b, s, sx((0.3, 3.95, 0.5), s), 2.4, hexc('#120f16'), hexc('#262030'))
    return v


# ---------------- Loki: Nidhogg hybrid ----------------

def nidhogg(px=0.0625):
    v = Vox(px, noise=0.05, seed=11)
    OBS = hexc('#121218')
    OBS2 = hexc('#22222c')
    BELLY = hexc('#4a3e38')
    GOLD = hexc('#d8c48e')
    GOLD2 = hexc('#8a6c3a')
    FUR = hexc('#f4f2ec')
    FUR2 = hexc('#c8c4bc')
    CLAW = hexc('#e0d8c8')
    TOOTH = hexc('#f2ead2')
    v.bone('body', 'root', (0, 4.1, 0))
    v.bone('head', 'body', (0, 7.45, -0.3))
    v.bone('arm_r', 'body', (2.0, 6.9, 0))
    v.bone('arm_l', 'body', (-2.0, 6.9, 0))
    v.bone('leg_r', 'root', (0.95, 4.0, 0.1))
    v.bone('leg_l', 'root', (-0.95, 4.0, 0.1))
    v.bone('tail', 'body', (0, 4.0, 0.8))
    v.bone('wing_r', 'body', (0.9, 6.8, 1.0))
    v.bone('wing_l', 'body', (-0.9, 6.8, 1.0))
    humanoid_anims(v, walk_leg=22, walk_arm=14, attack=125, roar_arms=40)
    v.anim('head', 'roar', 'x', 10)
    v.anim('tail', 'idle', 'y', 12, 3.0)
    v.anim('tail', 'walk', 'y', 9, 1.0)
    v.anim('body', 'idle', 'up', 0.06, 3.2)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        v.anim(b, 'idle', 'z', 5 * s, 3.4)
        v.anim(b, 'fly', 'z', 32 * s, 1.1)
        v.anim(b, 'roar', 'z', 22 * s)
        v.anim(b, 'rest', 'y', -30 * s)

    def torso_c(p, u):
        if p[2] < -0.75 and 4.0 < p[1] < 6.0 and abs(p[0]) < 0.9:
            return OBS2 if (p[1] - 4.0) % 0.5 < 0.13 else BELLY
        return OBS
    loft(v, 'body', [(3.7, 1.25, 0.95, 0.95), (4.2, 1.3, 1.0, 1.0), (4.8, 1.22, 1.0, 0.95), (5.5, 1.5, 1.15, 1.0),
                     (6.2, 1.95, 1.3, 1.05), (6.85, 2.15, 1.1, 1.05), (7.15, 1.4, 0.9, 0.9), (7.45, 0.8, 0.7, 0.7)], torso_c)
    for s in SIDES:
        v.ball('body', sx((0.75, 6.25, -0.85), s), (0.85, 0.62, 0.45), OBS)
        v.ball('body', sx((1.65, 7.05, 0.15), s), (0.75, 0.55, 0.8), OBS)
    # spikes down the back
    for i in range(7):
        y = 4.4 + i * 0.45
        v.tube('body', [V([0, y, 0.85 + 0.04 * i]), V([0, y + 0.25, 1.45 + 0.03 * i])], [0.16, 0.0], OBS2, smooth=False)

    # ornate chest band and belt (gold with dark diamonds)
    def band_c(p, u):
        a = math.atan2(p[0], -p[2])
        return GOLD2 if int((a + 4) * 6) % 3 == 0 else GOLD
    for y, rx, rz, w in ((6.05, 2.0, 1.34, 0.18), (4.45, 1.38, 1.08, 0.24)):
        v.box('body', (-rx - 0.2, y - w, -rz - 0.2), (rx + 0.2, y + w, rz + 0.2), band_c, mode='paint')
    v.box('body', (-0.32, 4.15, -1.2), (0.32, 4.75, -1.0), GOLD)
    v.box('body', (-0.16, 4.3, -1.25), (0.16, 4.6, -1.15), GOLD2)
    # white fur trim at the waist
    for a in np.linspace(0, 2 * math.pi, 18)[:-1]:
        v.ball('body', V([math.sin(a) * 1.38, 4.0, -math.cos(a) * 1.08]), (0.3, 0.26, 0.3), FUR if int(a * 3) % 2 else FUR2)
    # legs: round thighs, fur ring, dragon shins, talons
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        hip, knee, ank, ball = sx((0.95, 4.0, 0.1), s), sx((1.05, 2.5, -0.55), s), sx((1.05, 1.05, 0.4), s), sx((1.05, 0.3, -0.15), s)
        v.ball(b, sx((1.0, 3.35, -0.2), s), (0.95, 1.05, 0.95), OBS)
        v.tube(b, [knee, sx((1.06, 1.8, 0.05), s), ank], [0.58, 0.48, 0.32], OBS, per=3)
        v.tube(b, [ank, ball], [0.32, 0.27], OBS, smooth=False)
        for a in np.linspace(0, 2 * math.pi, 10)[:-1]:
            v.ball(b, sx((1.0 + 0.95 * math.sin(a), 3.95, -0.1 - 0.9 * math.cos(a)), s), (0.24, 0.22, 0.24), FUR)
        for ang in (-30, 0, 30):
            d = norm(V([math.sin(math.radians(ang)) * s, -0.1, -math.cos(math.radians(ang))]))
            t1 = ball + d * 0.6 + V([0, -0.1, 0])
            v.tube(b, [ball, t1], [0.2, 0.15], OBS, smooth=False)
            v.tube(b, [t1, t1 + d * 0.35 + V([0, -0.1, 0]), t1 + d * 0.6 + V([0, -0.25, 0])], [0.14, 0.09, 0.0], CLAW, per=2)
        v.tube(b, [ank + V([0, -0.1, 0.1]), ank + V([0, -0.5, 0.55]), ank + V([0, -0.95, 0.7])], [0.15, 0.1, 0.0], CLAW, per=2)
    # arms: massive, spiked studded cuffs, clawed hands, spikes on the forearm
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((2.0, 6.9, 0), s), sx((2.55, 5.3, 0.15), s), sx((2.65, 3.95, -0.35), s)
        v.ball(b, sx((2.15, 6.85, 0.0), s), (0.88, 0.78, 0.82), OBS)
        v.tube(b, [sh, sx((2.4, 6.1, 0.05), s), el], [0.72, 0.78, 0.55], OBS, per=3)
        v.tube(b, [el, sx((2.65, 4.7, -0.05), s), wr], [0.58, 0.62, 0.45], OBS, per=3)
        for i in range(3):
            p0 = el + (wr - el) * (0.2 + 0.25 * i) + V([s * 0.5, 0, 0.1])
            v.tube(b, [p0, p0 + V([s * 0.45, 0.15, 0.1])], [0.13, 0.0], OBS2, smooth=False)
        v.tube(b, [wr + V([0, 0.6, 0.06]), wr + V([0, 0.0, 0])], [0.58, 0.55], GOLD, smooth=False)
        for j in range(8):
            a = 2 * math.pi * j / 8
            for yy in (0.15, 0.45):
                p = wr + V([math.cos(a) * 0.56, yy, math.sin(a) * 0.56])
                v.tube(b, [p, p + V([math.cos(a) * 0.22, 0, math.sin(a) * 0.22])], [0.09, 0.0], OBS2, smooth=False)
        hand(v, b, wr, s, 5.0, OBS, claw=CLAW)
    ragnir(v, 'arm_r', 2.72, -1.15, 0.0, 6.2, 1.35)
    # dragon head: skull, blocky snout and lower jaw full of jagged teeth
    hc = V([0, 8.05, -0.55])
    v.ball('head', hc, (0.62, 0.62, 0.62), OBS)
    v.tube('head', [V([0, 7.3, -0.3]), hc + V([0, -0.3, 0.2])], [0.75, 0.62], OBS, smooth=False)
    v.box('head', hc + V([-0.42, -0.35, -1.35]), hc + V([0.42, 0.15, -0.3]), OBS)            # upper snout
    v.box('head', hc + V([-0.36, -0.68, -1.2]), hc + V([0.36, -0.42, -0.3]), OBS2)           # lower jaw
    v.box('head', hc + V([-0.38, -0.45, -1.3]), hc + V([0.38, -0.33, -0.35]), (40, 14, 14))  # mouth gap

    def teeth(p, u):
        z = p[2] - hc[2]
        if z > -0.32:
            return None
        k = ((p[0] + 0.5) / 0.125) % 2
        y = p[1] - hc[1]
        if y > -0.42 and k < 1:
            return TOOTH      # upper fangs hanging down
        if y < -0.38 and k >= 1:
            return TOOTH      # lower fangs pointing up
        return None
    v.box('head', hc + V([-0.43, -0.52, -1.36]), hc + V([0.43, -0.28, -0.3]), teeth, mode='paint')
    v.box('head', hc + V([-0.25, 0.0, -1.38]), hc + V([-0.1, 0.12, -1.32]), (10, 10, 10))  # nostrils
    v.box('head', hc + V([0.1, 0.0, -1.38]), hc + V([0.25, 0.12, -1.32]), (10, 10, 10))
    for s in SIDES:
        v.box('head', hc + V([0.18 * s - 0.15, 0.15, -0.68]), hc + V([0.18 * s + 0.15, 0.3, -0.55]), glow('#ffd040'))
        v.box('head', hc + V([0.18 * s - 0.2, 0.3, -0.7]), hc + V([0.18 * s + 0.2, 0.42, -0.5]), OBS2)  # heavy brow
    # huge curved horns
    for s in SIDES:
        hb = hc + V([0.42 * s, 0.35, 0.0])
        v.tube('head', [hb, hb + V([0.8 * s, 0.35, 0.25]), hb + V([1.45 * s, 1.05, 0.15]), hb + V([1.55 * s, 1.95, -0.35]), hb + V([1.2 * s, 2.55, -0.85])],
               [0.34, 0.28, 0.2, 0.12, 0.0], OBS, per=5)
    # crown of spikes all round the back of the head
    cc = hc + V([0, 0.2, 0.3])
    for i in range(13):
        a = math.radians(-110 + 220 * i / 12)
        d = norm(V([math.sin(a), math.cos(a) * 0.9 + 0.3, 0.55]))
        L = 1.0 + 0.7 * math.cos(a) ** 2
        v.tube('head', [cc + d * 0.3, cc + d * (0.3 + L)], [0.18, 0.0], OBS2 if i % 2 else OBS, smooth=False)
    # curly white mane over the chest, shoulders and the back of the head
    rnd = random.Random(77)
    curls = []
    for i in range(70):
        zone = rnd.random()
        if zone < 0.3:
            a = rnd.uniform(-2.4, 2.4)
            c = hc + V([math.sin(a) * 0.7, rnd.uniform(0.0, 0.6), math.cos(a) * 0.6 + 0.15])
        elif zone < 0.7:
            a = rnd.uniform(-math.pi, math.pi)
            c = V([math.sin(a) * rnd.uniform(0.6, 1.9), rnd.uniform(6.85, 7.5), math.cos(a) * rnd.uniform(0.5, 1.0)])
        else:
            c = V([rnd.uniform(-1.1, 1.1), rnd.uniform(6.3, 7.0), -rnd.uniform(1.05, 1.3)])
        curls.append(c)
    for i, c in enumerate(curls):
        r = rnd.uniform(0.2, 0.34)
        v.ball('head' if np.linalg.norm(c - hc) < 1.2 else 'body', c, (r, r * 0.9, r), FUR if i % 3 else FUR2)
    # spiked tail
    tp = [V([0, 4.0, 0.8]), V([0, 3.0, 1.9]), V([0.5, 1.4, 3.0]), V([1.4, 0.4, 3.9]), V([2.6, 0.2, 4.4]), V([3.6, 0.6, 4.6])]
    v.tube('tail', tp, [0.75, 0.6, 0.45, 0.32, 0.2, 0.08], OBS, per=4)
    cp = catmull(tp, 8)
    for t in np.linspace(0.05, 0.9, 9):
        p = cp[int(t * (len(cp) - 1))]
        q = cp[min(int(t * (len(cp) - 1)) + 1, len(cp) - 1)]
        d = norm(q - p)
        upv = norm(np.cross(d, np.cross(V([0, 1.0, 0]), d)))
        r = 0.75 * (1 - t) + 0.1
        v.tube('tail', [p + upv * r * 0.7, p + upv * (r + 0.45) - d * 0.15], [0.16, 0.0], OBS2, smooth=False)
    for s, b in ((1, 'wing_r'), (-1, 'wing_l')):
        bat_wing(v, b, s, sx((0.9, 6.8, 1.0), s), 1.05, OBS, hexc('#2a181c'), CLAW)
    # finer detail for the 40-block giant: overlapping dragon scales on the black hide, plates on the belly
    EDGE = hexc('#07070b')
    SHINE = hexc('#2e2e3a')

    def scales(p, c):
        x, y, z = p
        row = math.floor(y / 0.19)
        off = 0.5 if row % 2 else 0.0
        u = (x + z) / 0.24 + off
        fu, fy = u - math.floor(u), y / 0.19 - row
        if fy < 0.2 or abs(fu - 0.5) > 0.5 - 0.12 * (1 - fy):
            return EDGE
        return SHINE if fy > 0.75 else None
    v.retex(['body', 'head', 'arm_r', 'arm_l', 'leg_r', 'leg_l', 'tail'], [OBS, OBS2], scales)
    v.retex(['body'], [BELLY], lambda p, c: hexc('#2c241f') if (p[1] / 0.3) % 1 < 0.2 else (hexc('#5c4e46') if (p[1] / 0.3) % 1 > 0.8 else None))
    v.retex(['body', 'arm_r', 'arm_l', 'head'], [FUR], lambda p, c: FUR2 if int(p[1] / 0.0625 + p[0] / 0.0625 * 0.5) % 4 == 0 else None)

    return v


# ---------------- Loki: his own look ----------------

def loki():
    v = Vox(0.0625, scale=4.44, noise=0.05, seed=13)
    SKIN = hexc('#c99a7a')
    HAIR = hexc('#e294c8')
    HAIR2 = hexc('#b86aa0')
    TUNIC = hexc('#5a2e24')
    LEATHER = hexc('#33261e')
    FUR = hexc('#dedad2')
    FUR2 = hexc('#a8a49c')
    GOLD = hexc('#d4b46a')
    HELM = hexc('#18181e')
    BAND = hexc('#f2eee4')
    v.bone('body', 'root', (0, 3.7, 0))
    v.bone('head', 'body', (0, 6.75, -0.05))
    v.bone('arm_r', 'body', (1.2, 6.25, 0))
    v.bone('arm_l', 'body', (-1.2, 6.25, 0))
    v.bone('leg_r', 'root', (0.5, 3.6, 0))
    v.bone('leg_l', 'root', (-0.5, 3.6, 0))
    v.bone('cape', 'body', (0, 6.4, 0.6))
    humanoid_anims(v, walk_leg=24, walk_arm=18, attack=120, roar_arms=35)
    v.anim('cape', 'walk', 'x', -6, 2.0)
    for s, b in ((1, 'leg_r'), (-1, 'leg_l')):
        v.tube(b, [sx((0.5, 3.6, 0), s), sx((0.53, 2.8, -0.04), s), sx((0.55, 1.95, -0.1), s)], [0.5, 0.45, 0.37], LEATHER, per=3)
        v.tube(b, [sx((0.55, 1.95, -0.1), s), sx((0.55, 0.45, 0.0), s)], [0.37, 0.33], LEATHER, smooth=False)
        v.box(b, sx((0.55, 0, 0), s) + V([-0.36, 0, -0.62]), sx((0.55, 0, 0), s) + V([0.36, 1.2, 0.36]), hexc('#2a1e18'))
        for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
            v.ball(b, sx((0.55 + 0.4 * math.sin(a), 1.25, -0.4 * math.cos(a)), s), (0.15, 0.13, 0.15), FUR if int(a * 2) % 2 else FUR2)
    loft(v, 'body', [(3.3, 0.85, 0.62, 0.6), (3.7, 0.82, 0.6, 0.58), (4.3, 0.75, 0.55, 0.52), (5.0, 0.85, 0.6, 0.55),
                     (5.7, 1.05, 0.68, 0.6), (6.2, 1.15, 0.6, 0.6), (6.45, 0.55, 0.42, 0.42), (6.75, 0.34, 0.32, 0.32)], TUNIC)
    v.box('body', (-1, 3.95, -1), (1, 4.22, 1), LEATHER, mode='paint')
    v.box('body', (-0.22, 3.92, -0.7), (0.22, 4.25, -0.55), GOLD)
    v.sheet('body', lambda u, q: V([math.sin(math.radians(-170 + 340 * u)) * (0.88 + 0.25 * q), 3.95 - q * 1.15,
                                    -math.cos(math.radians(-170 + 340 * u)) * (0.64 + 0.25 * q)]), TUNIC, thick=2)
    for a in np.linspace(0, 2 * math.pi, 16)[:-1]:
        v.ball('body', V([math.sin(a) * 1.0, 6.22, -math.cos(a) * 0.62]), (0.26, 0.22, 0.26), FUR if int(a * 2) % 2 else FUR2)
    v.sheet('cape', lambda u, q: V([(u - 0.5) * (2.1 + 0.7 * q), 6.35 - q * 4.6, 0.64 + 0.35 * q]), hexc('#3e3028'), thick=2)
    for s, b in ((1, 'arm_r'), (-1, 'arm_l')):
        sh, el, wr = sx((1.2, 6.2, 0), s), sx((1.45, 5.0, 0.08), s), sx((1.52, 3.9, -0.18), s)
        v.ball(b, sx((1.22, 6.15, 0.0), s), (0.46, 0.43, 0.46), TUNIC)
        v.tube(b, [sh, sx((1.35, 5.6, 0.05), s), el], [0.38, 0.4, 0.3], SKIN, per=3)
        v.tube(b, [el, sx((1.5, 4.5, -0.04), s), wr], [0.32, 0.33, 0.25], SKIN, per=3)
        v.tube(b, [wr + V([0, 0.75, 0.04]), wr], [0.35, 0.3], lambda p, u: GOLD if int(u * 6) % 3 == 1 else LEATHER, smooth=False)
        hand(v, b, wr, s, 3.6, SKIN)
    ragnir(v, 'arm_r', 1.6, -0.85, 0.0, 5.4, 1.0)
    hc = V([0, 7.3, -0.12])
    v.tube('head', [V([0, 6.5, -0.05]), V([0, 6.95, -0.1])], [0.34, 0.3], SKIN, smooth=False)
    v.ball('head', hc, (0.5, 0.58, 0.53), SKIN)
    v.ball('head', hc + V([0, -0.34, -0.14]), (0.4, 0.26, 0.4), SKIN)
    v.ball('head', hc + V([0, -0.36, -0.14]), (0.42, 0.12, 0.43), grin_paint(0, hc[1] - 0.36, -0.4, 0.26, 0.08, (40, 14, 14), (242, 236, 224), 7, zig=False, lift=0.06), mode='paint')
    v.box('head', (-0.08, hc[1] - 0.18, -0.72), (0.08, hc[1] - 0.02, -0.6), SKIN)  # nose
    # bandage over the eyes
    v.ball('head', hc + V([0, 0.08, 0]), (0.56, 0.16, 0.6), lambda p, u: BAND if int(p[1] / 0.125) % 2 else hexc('#d0c8b8'), cut=('y', 1, hc[1] - 0.06))
    v.box('head', hc + V([-0.12, -0.95, 0.4]), hc + V([0.0, 0.0, 0.58]), BAND)
    rnd = random.Random(11)
    for i in range(36):
        a = rnd.uniform(-2.5, 2.5)
        root = hc + V([math.sin(a) * 0.45, 0.25, math.cos(a) * 0.45])
        if root[2] < hc[2] - 0.1:
            continue
        L = rnd.uniform(1.6, 2.7)
        sw = rnd.uniform(-0.3, 0.3)
        pts = [root, root + V([math.sin(a) * 0.25, 0.05, 0.2]), root + V([math.sin(a) * 0.45 + sw, -L * 0.4, 0.45]), root + V([math.sin(a) * 0.55 + sw * 2, -L, 0.5])]
        v.tube('head', pts, [0.13, 0.13, 0.1, 0.04], HAIR if i % 3 else HAIR2, per=2)
    for s in SIDES:
        top = hc + V([0.4 * s, 0.05, -0.15])
        path = [top, top + V([0.12 * s, -0.4, -0.12]), top + V([0.14 * s, -0.95, -0.42]), top + V([0.1 * s, -1.6, -0.5]), top + V([0.06 * s, -2.3, -0.44])]
        v.tube('head', path, [0.16, 0.15, 0.14, 0.12, 0.1], lambda p, u: HAIR2 if int(u * 14) % 2 else HAIR, per=6)
        end = top + V([0.06 * s, -2.3, -0.44])
        v.box('head', end - V([0.12, 0.05, 0.12]), end + V([0.12, 0.1, 0.12]), GOLD)
    # wide-rimmed black helmet and long black horns, the left one wrapped in white
    v.ball('head', hc + V([0, 0.22, 0]), (0.55, 0.5, 0.58), HELM, cut=('y', 1, hc[1] + 0.22))
    v.ball('head', hc + V([0, 0.24, 0]), (1.05, 0.07, 1.05), HELM)
    for s in SIDES:
        hb = hc + V([0.36 * s, 0.5, 0.0])
        path = [hb, hb + V([0.25 * s, 0.6, 0.02]), hb + V([0.33 * s, 1.3, -0.05]), hb + V([0.22 * s, 1.95, -0.12])]
        col = (lambda p, u: BAND if 0.06 < u < 0.82 and int(u * 18) % 2 == 0 else HELM) if s < 0 else HELM
        v.tube('head', path, [0.18, 0.15, 0.1, 0.0], col, per=6)
    # finer detail for the 33-block giant
    v.retex(['body'], [TUNIC], lambda p, c: hexc('#4a241c') if (int(p[0] / 0.0625) + int(p[1] / 0.0625)) % 4 == 0 else (hexc('#6a3a2e') if abs(abs(p[0]) - 0.45) < 0.04 else None))
    v.retex(['head'], [HAIR, HAIR2], lambda p, c: hexc('#f0b4dc') if int(p[0] / 0.0625 * 3 + p[2] / 0.0625) % 5 == 0 else None)
    v.retex(['leg_r', 'leg_l'], [LEATHER], lambda p, c: hexc('#261c16') if (p[1] / 0.35) % 1 < 0.12 else None)
    for s in SIDES:
        pts = [V([0.95 * s, 6.05, -0.5]), V([0.35 * s, 5.4, -0.74]), V([-0.3 * s, 4.75, -0.72]), V([-0.75 * s, 4.25, -0.6])]
        v.tube('body', pts, 0.09, LEATHER, per=6)
        for t in (0.15, 0.4, 0.65, 0.9):
            q = catmull(pts, 6)[int(t * (len(catmull(pts, 6)) - 1))]
            v.ball('body', q + V([0, 0, -0.06]), (0.06, 0.06, 0.05), GOLD)
    v.ball('body', V([0, 5.05, -0.78]), (0.16, 0.16, 0.08), GOLD)  # where the straps cross
    v.ball('head', hc + V([0, 0.28, 0]), (0.58, 0.06, 0.61), GOLD, cut=('y', 1, hc[1] + 0.22))
    for a in np.linspace(0, 2 * math.pi, 13)[:-1]:
        v.ball('head', hc + V([math.sin(a) * 0.6, 0.29, -math.cos(a) * 0.62]), (0.05, 0.05, 0.05), hexc('#f4e4a8'))
    # brows over the bandage and a scar down the left cheek
    v.box('head', hc + V([-0.36, 0.24, -0.62]), hc + V([0.36, 0.3, -0.45]), hexc('#7a4a5e'), mode='paint')
    v.tube('head', [hc + V([-0.25, 0.0, -0.5]), hc + V([-0.3, -0.35, -0.44])], 0.035, hexc('#8a5a4a'), smooth=False)

    return v


# nidhogg_player: the same dragon with bigger pixels, for players in the fruit's form (drawn small, so far fewer faces)
MODELS = {'nika_wild': nika, 'imu_beast': imu_beast, 'imu_demon': imu_demon, 'nidhogg': nidhogg, 'nidhogg_player': lambda: nidhogg(0.125), 'character/loki': loki}


def main():
    prev = None
    if '--preview' in sys.argv:
        prev = sys.argv[sys.argv.index('--preview') + 1]
        os.makedirs(prev, exist_ok=True)
    only = [a for a in sys.argv[1:] if a in MODELS]
    for name, fn in MODELS.items():
        if only and name not in only:
            continue
        v = fn()
        m = v.to_mesh()
        path = os.path.join(OUT, name + '.bin')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        size = m.write(path)
        print('%-16s %7d pixels %6d faces %5d KB' % (name, v.count(), m.count(), size // 1024))
        if prev:
            from preview import sheet
            sheet(m, os.path.join(prev, name.replace('/', '_') + '.png'))


if __name__ == '__main__':
    main()
