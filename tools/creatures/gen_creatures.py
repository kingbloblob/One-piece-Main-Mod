"""Generates the One Piece creatures' models, textures, spawn eggs, drops, spawn biome tags and names.

Run:  python3 gen_creatures.py <path to source/>
Writes only files owned by the creatures feature (package com.onepiecemod.creature and its assets).
The Java entity/registration code is hand-written; this script writes CreatureModels.java (client)
from the same box list it paints the textures from, so model and texture always match.
"""
import json, os, random, struct, sys, zlib

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
RES = os.path.join(SRC, 'src/main/resources')
CLIENT_JAVA = os.path.join(SRC, 'src/client/java/com/onepiecemod/creature/client')


def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# ---------------- model spec ----------------
# box(x, y, z, w, h, d, color, eyes=None, front=[(x, y, color)], pattern=None)
# part(name, pivot, boxes, rot=(0,0,0), parent=None)
# Model space: 16 px = 1 block, y points down, y=24 is the ground, the front is -z, right is -x.

def box(x, y, z, w, h, d, color, eyes=None, front=None, pattern=None):
    return dict(x=x, y=y, z=z, w=w, h=h, d=d, color=color, eyes=eyes, front=front or [], pattern=pattern)


def part(name, pivot, boxes, rot=(0, 0, 0), parent=None):
    return dict(name=name, pivot=pivot, boxes=boxes, rot=rot, parent=parent)


def legs4(xo, y, zf, zb, w, h, color, dz=None):
    d = dz or w
    b = lambda: [box(-w / 2, 0, -d / 2, w, h, d, color)]
    return [part('leg0', (-xo, y, zf), b()), part('leg1', (xo, y, zf), b()),
            part('leg2', (-xo, y, zb), b()), part('leg3', (xo, y, zb), b())]


S = {}

# ---- Passive ----
BR, BR2, BEAK = '#5b3a1e', '#7a5232', '#e0b030'
S['south_bird'] = [
    part('body', (0, 0, 0), [box(-3, 13, -4, 6, 6, 8, BR, pattern='speckle')]),
    part('head', (0, 14, -4), [box(-2.5, -5, -4, 5, 5, 5, BR2, eyes='#111111'),
                               box(-1, -3, -9, 2, 2, 5, BEAK)]),
    part('leg0', (-1.5, 19, 0), [box(-0.5, 0, -0.5, 1, 5, 1, '#c89040')]),
    part('leg1', (1.5, 19, 0), [box(-0.5, 0, -0.5, 1, 5, 1, '#c89040')]),
    part('wing0', (-3, 14, -3), [box(-1, 0, 0, 1, 4, 7, '#3e2612')]),
    part('wing1', (3, 14, -3), [box(0, 0, 0, 1, 4, 7, '#3e2612')]),
    part('tail', (0, 15, 4), [box(-2, 0, 0, 4, 1, 5, '#3e2612')], rot=(-0.3, 0, 0)),
]

DUCK, DUCK2, BILL, HAT = '#f0d878', '#f7e9b0', '#f2a33a', '#3a6fd0'
S['spot_billed_duck'] = [
    part('body', (0, 0, 0), [box(-5, 5, -6, 10, 8, 12, DUCK, pattern='speckle')]),
    part('head', (0, 6, -5), [box(-2, -8, -2, 4, 9, 4, DUCK),
                              box(-3, -13, -5, 6, 6, 7, DUCK2, eyes='#111111'),
                              box(-2.5, -10, -10, 5, 2, 5, BILL, pattern='spots'),
                              box(-3.5, -15, -4.5, 7, 2, 6, HAT, pattern='band')]),
    part('leg0', (-2.5, 13, 1), [box(-1, 0, -1, 2, 10, 2, BILL), box(-2, 10, -3, 4, 1, 4, BILL)]),
    part('leg1', (2.5, 13, 1), [box(-1, 0, -1, 2, 10, 2, BILL), box(-2, 10, -3, 4, 1, 4, BILL)]),
    part('wing0', (-5, 6, -4), [box(-1, 0, 0, 1, 6, 10, '#d9bd55')]),
    part('wing1', (5, 6, -4), [box(0, 0, 0, 1, 6, 10, '#d9bd55')]),
    part('tail', (0, 6, 6), [box(-3, 0, 0, 6, 3, 3, '#d9bd55')], rot=(-0.4, 0, 0)),
]

TUNA, TUNA2, FIN = '#5d7fa3', '#c9d6e3', '#3f5f80'
S['elephant_tuna'] = [
    part('body', (0, 0, 0), [box(-5, 8, -10, 10, 12, 20, TUNA, pattern='belly'),
                             box(-0.5, 3, -4, 1, 5, 8, FIN)]),
    part('head', (0, 14, -10), [box(-4.5, -5, -7, 9, 10, 7, TUNA, eyes='#101820'),
                                box(-1.5, 1, -14, 3, 3, 7, '#6f8fb0', pattern='band'),
                                box(-8, -4, -5, 3, 7, 1, '#7d9cbc'),
                                box(5, -4, -5, 3, 7, 1, '#7d9cbc')]),
    part('tail', (0, 14, 10), [box(-1.5, -2.5, 0, 3, 5, 6, TUNA), box(-0.5, -7, 5, 1, 14, 4, FIN)]),
    part('wing0', (-5, 17, -4), [box(-5, 0, 0, 5, 1, 4, FIN)], rot=(0, 0, 0.3)),
    part('wing1', (5, 17, -4), [box(0, 0, 0, 5, 1, 4, FIN)], rot=(0, 0, -0.3)),
]

FLUFF, SKIN = '#f7a8d0', '#fbe9d7'
S['cotton_candy_lamb'] = [
    part('body', (0, 0, 0), [box(-4, 8, -6, 8, 8, 12, FLUFF, pattern='fluff')]),
    part('head', (0, 10, -6), [box(-2.5, -3, -5, 5, 5, 5, SKIN, eyes='#2a1a1a'),
                               box(-3, -5, -4, 6, 2, 4, '#b8e4f7', pattern='fluff')]),
    *legs4(2, 16, -4, 4, 2, 8, SKIN),
    part('tail', (0, 9, 6), [box(-1.5, 0, 0, 3, 3, 2, '#b8e4f7', pattern='fluff')]),
]

# ---- Neutral ----
DUG, SHELL = '#c9a27a', '#3f7a3a'
S['kung_fu_dugong'] = [
    part('body', (0, 0, 0), [box(-3.5, 8, -3, 7, 10, 6, DUG, pattern='belly'),
                             box(-4, 7, 2, 8, 11, 3, SHELL, pattern='shell')]),
    part('head', (0, 8, 0), [box(-3, -6, -3, 6, 6, 6, DUG, eyes='#111111'),
                             box(-1.5, -3, -4, 3, 2, 1, '#8a6a4a')]),
    part('arm0', (-3.5, 10, 0), [box(-2, 0, -1, 2, 6, 2, '#b08a62')]),
    part('arm1', (3.5, 10, 0), [box(0, 0, -1, 2, 6, 2, '#b08a62')]),
    part('leg0', (-1.5, 18, 0), [box(-1, 0, -2, 2, 6, 4, '#b08a62')]),
    part('leg1', (1.5, 18, 0), [box(-1, 0, -2, 2, 6, 4, '#b08a62')]),
]

YAG = '#e98aa0'
S['yagara_bull'] = [
    part('body', (0, 0, 0), [box(-4, 8, -6, 8, 8, 12, YAG, pattern='belly')]),
    part('head', (0, 9, -6), [box(-3.5, -6, -5, 7, 7, 5, YAG),
                              box(-3.5, -8, -3, 2, 2, 2, '#ffffff', front=[(0, 1, '#111111'), (1, 1, '#111111')]),
                              box(1.5, -8, -3, 2, 2, 2, '#ffffff', front=[(0, 1, '#111111'), (1, 1, '#111111')]),
                              box(-2.5, -3, -8, 5, 3, 3, '#f5b7c4', front=[(1, 1, '#7a3040'), (3, 1, '#7a3040')])]),
    part('tail', (0, 12, 6), [box(-1.5, -1.5, 0, 3, 3, 7, YAG), box(-1.5, -5, 5, 3, 4, 2, YAG)]),
    part('wing0', (-4, 13, -2), [box(-1, 0, 0, 1, 4, 6, '#c96a80')]),
    part('wing1', (4, 13, -2), [box(0, 0, 0, 1, 4, 6, '#c96a80')]),
]

HIDE, HORN = '#5a2a1a', '#efe6cf'
S['fighting_bull'] = [
    part('body', (0, 0, 0), [box(-6, 4, -9, 12, 11, 18, HIDE, pattern='speckle')]),
    part('head', (0, 7, -9), [box(-4, -4, -6, 8, 8, 6, HIDE, eyes='#c02020'),
                              box(-3, 1, -8, 6, 3, 2, '#3a1a10', front=[(1, 1, '#000000'), (4, 1, '#000000')]),
                              box(-9, -4, -4, 5, 2, 2, HORN), box(4, -4, -4, 5, 2, 2, HORN),
                              box(-9, -8, -4, 2, 4, 2, HORN), box(7, -8, -4, 2, 4, 2, HORN)]),
    *legs4(3.5, 15, -6, 6, 4, 9, '#4a2212'),
    part('tail', (0, 5, 9), [box(-0.5, 0, 0, 1, 9, 1, '#3a1a10')], rot=(0.3, 0, 0)),
]

# ---- Hostile ----
FUR = '#f4f4f4'
S['lapahn'] = [
    part('body', (0, 0, 0), [box(-5, 2, -4, 10, 12, 8, FUR, pattern='fluff')]),
    part('head', (0, 2, 0), [box(-4, -8, -4, 8, 8, 8, FUR, eyes='#8a0000'),
                             box(-3.5, -16, -1, 2, 8, 2, FUR, front=[(0, 2, '#f2b8c6'), (1, 2, '#f2b8c6'), (0, 4, '#f2b8c6'), (1, 4, '#f2b8c6')]),
                             box(1.5, -16, -1, 2, 8, 2, FUR, front=[(0, 2, '#f2b8c6'), (1, 2, '#f2b8c6'), (0, 4, '#f2b8c6'), (1, 4, '#f2b8c6')]),
                             box(-2, -4, -5, 4, 3, 1, '#dddddd', front=[(1, 0, '#333333'), (2, 0, '#333333'), (0, 2, '#ffffff'), (3, 2, '#ffffff')])]),
    part('arm0', (-5, 4, 0), [box(-3, 0, -1.5, 3, 10, 3, FUR)]),
    part('arm1', (5, 4, 0), [box(0, 0, -1.5, 3, 10, 3, FUR)]),
    part('leg0', (-2.5, 14, 0), [box(-2, 0, -2, 4, 10, 4, FUR)]),
    part('leg1', (2.5, 14, 0), [box(-2, 0, -2, 4, 10, 4, FUR)]),
    part('tail', (0, 12, 4), [box(-1.5, 0, 0, 3, 3, 2, '#ffffff')]),
]

SAND, SAND2 = '#c9a45a', '#8a6a30'
side = []
for i, z in enumerate((-3, 1, 5)):
    side.append(part('sideleg%d' % (2 * i), (-4, 18, z), [box(-7, -0.5, -0.5, 7, 1, 1, SAND2)], rot=(0, 0, -0.75)))
    side.append(part('sideleg%d' % (2 * i + 1), (4, 18, z), [box(0, -0.5, -0.5, 7, 1, 1, SAND2)], rot=(0, 0, 0.75)))
S['sand_scorpion'] = [
    part('body', (0, 0, 0), [box(-4, 16, -6, 8, 4, 12, SAND, pattern='stripes')]),
    part('head', (0, 18, -6), [box(-3, -2, -3, 6, 3, 3, SAND2, eyes='#111111'),
                               box(-7, -1, -8, 3, 2, 6, SAND2), box(4, -1, -8, 3, 2, 6, SAND2)]),
    *side,
    part('tail', (0, 17, 6), [box(-1.5, -1, 0, 3, 2, 5, SAND), box(-1, -8, 4, 2, 8, 2, SAND, pattern='stripes'),
                              box(-1, -10, 1, 2, 2, 5, SAND), box(-0.5, -9, 0, 1, 2, 1, '#3a2a20')]),
]

PURP = '#8a3fb5'
SMILE = '#2a0a3a'
face = [(3, 3, '#ffffff'), (4, 3, '#ffffff'), (3, 4, '#ffffff'), (4, 4, SMILE),
        (7, 3, '#ffffff'), (8, 3, '#ffffff'), (7, 4, SMILE), (8, 4, '#ffffff'),
        (2, 7, SMILE), (9, 7, SMILE)] + [(x, 8, SMILE) for x in range(3, 9)] + [(x, 9, SMILE) for x in range(4, 8)]
S['smiley'] = [
    part('body', (0, 0, 0), [box(-6, 10, -6, 12, 12, 12, PURP, front=face, pattern='swirl'),
                             box(-4, 6, -4, 8, 4, 8, '#a35ccc', pattern='swirl')]),
    part('puff0', (-7, 8, -5), [box(-1, -1, -1, 2, 2, 2, '#c08ae0')]),
    part('puff1', (7, 8, -5), [box(-1, -1, -1, 2, 2, 2, '#c08ae0')]),
    part('puff2', (-7, 8, 5), [box(-1, -1, -1, 2, 2, 2, '#c08ae0')]),
    part('puff3', (7, 8, 5), [box(-1, -1, -1, 2, 2, 2, '#c08ae0')]),
]

FF, FFIN = '#d4472b', '#8a2a1a'
S['fighting_fish'] = [
    part('body', (0, 0, 0), [box(-4, 8, -8, 8, 9, 16, FF, pattern='scales'),
                             box(-0.5, 4, -6, 1, 4, 10, FFIN)]),
    part('head', (0, 12, -8), [box(-3.5, -4, -6, 7, 8, 6, FF, eyes='#ffd000'),
                               box(-0.5, -5, -10, 1, 1, 5, '#f2e0c0'),
                               box(-3, 2, -6.5, 6, 1, 1, '#ffffff')]),
    part('wing0', (-4, 10, -4), [box(-8, 0, 0, 8, 1, 7, FFIN)], rot=(0, 0, 0.4)),
    part('wing1', (4, 10, -4), [box(0, 0, 0, 8, 1, 7, FFIN)], rot=(0, 0, -0.4)),
    part('tail', (0, 12, 8), [box(-1.5, -2, 0, 3, 4, 5, FF), box(-0.5, -6, 4, 1, 12, 4, FFIN)]),
]

CROC, BAN = '#4f7a2a', '#f2d43a'
S['bananawani'] = [
    part('body', (0, 0, 0), [box(-5, 13, -10, 10, 7, 20, CROC, pattern='scales'),
                             box(-3, 12, -8, 6, 1, 16, '#3a5a1e', pattern='stripes')]),
    part('head', (0, 15, -10), [box(-4, -3, -10, 8, 4, 10, CROC, pattern='scales'),
                                box(-4, -5, -3, 8, 2, 3, CROC, eyes='#ffcc00'),
                                box(-2.5, -9, -4, 5, 6, 4, BAN, pattern='band'),
                                box(-2, -11, -8, 4, 3, 5, BAN)]),
    part('jaw', (0, 1, 0), [box(-4, 0, -10, 8, 2, 10, '#a7b86a', front=[(x, 0, '#ffffff') for x in range(0, 8, 2)])],
         parent='head'),
    *legs4(5, 19, -7, 7, 3, 5, '#3f6420'),
    part('tail', (0, 15, 10), [box(-3, -1.5, 0, 6, 5, 10, CROC, pattern='scales'), box(-2, 0, 10, 4, 3, 8, CROC)]),
]


# ---------------- texture packing + painting ----------------

def foot(b):
    return 2 * (b['d'] + b['w']), b['d'] + b['h']


def pack(spec):
    boxes = [b for p in spec for b in p['boxes']]
    order = sorted(boxes, key=lambda b: -foot(b)[1])
    for W in (64, 128, 256):
        x = y = rowh = 0
        ok = True
        for b in order:
            fw, fh = foot(b)
            if fw > W:
                ok = False
                break
            if x + fw > W:
                x, y, rowh = 0, y + rowh, 0
            b['u'], b['v'] = x, y
            x += fw
            rowh = max(rowh, fh)
        if ok:
            H = y + rowh
            Hp = 32
            while Hp < H:
                Hp *= 2
            if Hp <= W:
                return W, Hp
    raise SystemExit('texture too big')


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def paint(spec, W, H, seed):
    rnd = random.Random(seed)
    img = [[(0, 0, 0, 0)] * W for _ in range(H)]

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            img[y][x] = (c[0], c[1], c[2], 255)

    for p in spec:
        for b in p['boxes']:
            base = hexc(b['color'])
            u, v, w, h, d = b['u'], b['v'], b['w'], b['h'], b['d']
            faces = [  # (x0, y0, fw, fh, light)
                (u + d, v, w, d, 1.12), (u + d + w, v, w, d, 0.72),
                (u, v + d, d, h, 0.9), (u + d, v + d, w, h, 1.0),
                (u + d + w, v + d, d, h, 0.9), (u + 2 * d + w, v + d, w, h, 0.85)]
            for fi, (fx, fy, fw, fh, light) in enumerate(faces):
                for yy in range(fh):
                    for xx in range(fw):
                        f = light * rnd.uniform(0.95, 1.05)
                        if fi >= 2 and fh > 2:
                            # side faces: lit from above, darker towards the ground, soft rim at the edges
                            f *= 1.08 - 0.2 * yy / (fh - 1)
                            if yy == fh - 1 or (fw > 3 and xx in (0, fw - 1)):
                                f *= 0.88
                        pat = b['pattern']
                        if pat == 'speckle' and rnd.random() < 0.12:
                            f *= 0.8
                        elif pat == 'spots' and rnd.random() < 0.15:
                            f *= 0.55
                        elif pat == 'fluff':
                            f *= 1.0 + 0.12 * (((xx // 2) + (yy // 2)) % 2) - 0.06
                        elif pat == 'stripes' and yy % 3 == 0:
                            f *= 0.78
                        elif pat == 'scales' and (xx + 2 * (yy % 2)) % 4 == 0:
                            f *= 0.82
                        elif pat == 'shell' and (xx % 4 == 0 or yy % 4 == 0):
                            f *= 0.7
                        elif pat == 'swirl':
                            f *= 1.0 + 0.1 * ((xx + yy) % 5 == 0)
                        elif pat == 'band' and yy == fh // 2:
                            f *= 1.35
                        elif pat == 'belly' and fi == 1:
                            f *= 1.35
                        put(fx + xx, fy + yy, shade(base, f))
            # front face details
            fx, fy = u + d, v + d
            if b['eyes']:
                ec = hexc(b['eyes'])
                ex = max(1, w // 4)
                ey = 1 if h > 3 else 0
                for k, x in enumerate((ex, w - 1 - ex)):
                    x = int(x)
                    put(fx + x, fy + ey, ec)
                    if w >= 8:
                        put(fx + x, fy + ey + 1, ec)
                    if w >= 6:
                        # white of the eye on the outside, and a glint
                        put(fx + x + (-1 if k == 0 else 1), fy + ey, (236, 236, 228))
                        put(fx + x, fy + ey, shade(ec, 0.6) if sum(ec) > 120 else ec)
                        if w >= 8:
                            put(fx + x, fy + ey, (250, 250, 250))
                # eyes on the sides of the head too, so they show from the side
                if d >= 4 and h >= 3:
                    put(u + d - 2, v + d + ey, ec)
                    put(u + d + w + 1, v + d + ey, ec)
            for (x, y, c) in b['front']:
                put(fx + x, fy + y, hexc(c))
    return img


def write_png(path, img):
    H, W = len(img), len(img[0])
    raw = b''.join(b'\x00' + b''.join(struct.pack('BBBB', *px) for px in row) for row in img)

    def chunk(t, data):
        c = struct.pack('>I', len(data)) + t + data
        return c + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0)) \
        + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)


def egg_png(path, c1, c2, seed):
    rnd = random.Random(seed)
    a, b = hexc(c1), hexc(c2)
    img = [[(0, 0, 0, 0)] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            # egg: wider at the bottom
            cy = y - 8.5
            rx = 5.2 if cy > 0 else 5.2 - (abs(cy) / 7.5) ** 2 * 2.2
            ry = 6.8
            nx, ny = (x - 7.5) / rx, cy / ry
            r = nx * nx + ny * ny
            if r <= 1.0:
                col = a
                if rnd.random() < 0.22 and r < 0.8:
                    col = b
                f = 1.12 - 0.25 * ((x - 5) / 10 + (y - 5) / 12)
                if r > 0.8:
                    f *= 0.75
                img[y][x] = shade(col, f) + (255,)
    write_png(path, img)


# ---------------- Java model code ----------------

def fnum(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    return s + 'f'


def java_layer(name, spec, W, H):
    out = ['\tprivate static LayerDefinition %s() {' % camel(name),
           '\t\tMeshDefinition mesh = new MeshDefinition();',
           '\t\tPartDefinition root = mesh.getRoot();']
    declared = {'root'}
    for p in spec:
        parent = p['parent'] or 'root'
        cubes = ''.join('\n\t\t\t\t\t\t.texOffs(%d, %d).addBox(%s)' % (
            b['u'], b['v'], ', '.join(fnum(v) for v in (b['x'], b['y'], b['z'], b['w'], b['h'], b['d'])))
            for b in p['boxes'])
        px, py, pz = p['pivot']
        rx, ry, rz = p['rot']
        pose = ('PartPose.offset(%s, %s, %s)' % (fnum(px), fnum(py), fnum(pz)) if (rx, ry, rz) == (0, 0, 0) else
                'PartPose.offsetAndRotation(%s, %s, %s, %s, %s, %s)' % tuple(fnum(v) for v in (px, py, pz, rx, ry, rz)))
        children = any(q['parent'] == p['name'] for q in spec)
        prefix = 'PartDefinition %s = ' % p['name'] if children else ''
        out.append('\t\t%s%s.addOrReplaceChild("%s", CubeListBuilder.create()%s,\n\t\t\t\t%s);' % (
            prefix, parent, p['name'], cubes, pose))
    out.append('\t\treturn LayerDefinition.create(mesh, %d, %d);' % (W, H))
    out.append('\t}')
    return '\n'.join(out)


def camel(s):
    a = s.split('_')
    return a[0] + ''.join(x.title() for x in a[1:])


def rig(spec):
    names = [p['name'] for p in spec]
    cnt = lambda pre: len([n for n in names if n.startswith(pre) and n[len(pre):].isdigit()])
    return 'new Rig(%s, %s, %s, %d, %d, %d, %d, %d)' % (
        str('head' in names).lower(), str('jaw' in names).lower(), str('tail' in names).lower(),
        cnt('leg'), cnt('sideleg'), cnt('wing'), cnt('arm'), cnt('puff'))


# ---------------- data: names, spawns, drops, eggs ----------------
# id: (name, egg colors, spawn biomes (vanilla + onepiece), drops)
SMELT = {"type": "minecraft:furnace_smelt", "condition": {"type": "minecraft:any_of", "terms": [
    {"type": "minecraft:entity_properties", "entity": "this", "predicate": {"minecraft:flags": {"is_on_fire": True}}},
    {"type": "minecraft:entity_properties", "entity": "direct_attacker", "predicate": {"minecraft:equipment": {
        "mainhand": {"predicates": {"minecraft:enchantments": [{"enchantments": "#minecraft:smelts_loot"}]}}}}}]}}

D = {
    'south_bird': ('South Bird', '#5b3a1e', '#e0b030',
                   ['jungle', 'sparse_jungle', 'bamboo_jungle', 'onepiece:jaya'],
                   [('feather', 0, 2), ('chicken', 1, 1, 'smelt')]),
    'spot_billed_duck': ('Spot-Billed Duck', '#f0d878', '#3a6fd0',
                         ['desert', 'savanna', 'savanna_plateau', 'onepiece:alabasta'],
                         [('feather', 1, 3), ('chicken', 1, 2, 'smelt')]),
    'elephant_tuna': ('Elephant Tuna', '#5d7fa3', '#c9d6e3',
                      ['ocean', 'deep_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean', 'warm_ocean',
                       'onepiece:east_blue', 'onepiece:fishman_reef'],
                      [('cod', 2, 5, 'smelt'), ('bone_meal', 0, 2)]),
    'cotton_candy_lamb': ('Cotton Candy Lamb', '#f7a8d0', '#b8e4f7',
                          ['meadow', 'cherry_grove', 'flower_forest', 'sunflower_plains', 'onepiece:whole_cake'],
                          [('pink_wool', 1, 1), ('sugar', 1, 3), ('mutton', 1, 2, 'smelt')]),
    'kung_fu_dugong': ('Kung-Fu Dugong', '#c9a27a', '#3f7a3a',
                       ['beach', 'desert', 'onepiece:alabasta'],
                       [('cod', 0, 2, 'smelt'), ('turtle_scute', 0, 1, 'player')]),
    'yagara_bull': ('Yagara Bull', '#e98aa0', '#f5b7c4',
                    ['river', 'ocean', 'lukewarm_ocean', 'warm_ocean', 'onepiece:fishman_reef', 'onepiece:sabaody'],
                    [('salmon', 1, 2, 'smelt'), ('kelp', 0, 3)]),
    'fighting_bull': ('Fighting Bull', '#5a2a1a', '#efe6cf',
                      ['savanna', 'plains', 'windswept_savanna', 'onepiece:dressrosa'],
                      [('beef', 2, 4, 'smelt'), ('leather', 1, 3)]),
    'lapahn': ('Lapahn', '#f4f4f4', '#8a0000',
               ['snowy_plains', 'snowy_taiga', 'snowy_slopes', 'grove', 'ice_spikes', 'frozen_peaks',
                'onepiece:drum_island', 'onepiece:punk_hazard_frozen'],
               [('rabbit', 1, 2, 'smelt'), ('white_wool', 0, 2), ('rabbit_foot', 1, 1, 'rare'), ('onepiece:berry', 2, 6)]),
    'sand_scorpion': ('Sand Scorpion', '#c9a45a', '#3a2a20',
                      ['desert', 'badlands', 'eroded_badlands', 'wooded_badlands', 'onepiece:alabasta'],
                      [('spider_eye', 0, 1), ('bone', 0, 2), ('onepiece:berry', 1, 3)]),
    'smiley': ('Smiley', '#8a3fb5', '#2a0a3a',
               ['swamp', 'mangrove_swamp', 'onepiece:punk_hazard_burning', 'onepiece:punk_hazard_frozen'],
               [('slime_ball', 1, 3), ('purple_dye', 0, 2), ('onepiece:berry', 2, 5)]),
    'fighting_fish': ('Fighting Fish', '#d4472b', '#8a2a1a',
                      ['warm_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean', 'ocean',
                       'onepiece:east_blue', 'onepiece:fishman_reef'],
                      [('salmon', 1, 3, 'smelt'), ('prismarine_shard', 0, 1), ('onepiece:berry', 2, 6)]),
    'bananawani': ('Bananawani', '#4f7a2a', '#f2d43a',
                   ['desert', 'badlands', 'onepiece:alabasta'],
                   [('leather', 2, 4), ('gold_nugget', 1, 5), ('onepiece:berry', 5, 15)]),
}


def drop_pool(entry):
    item, lo, hi = entry[0], entry[1], entry[2]
    flag = entry[3] if len(entry) > 3 else None
    name = item if ':' in item else 'minecraft:' + item
    mods = [{"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    if flag == 'smelt':
        mods.append(SMELT)
    mods.append({"type": "minecraft:enchanted_count_increase",
                 "count": {"type": "minecraft:uniform", "min": 0.0, "max": 1.0}, "enchantment": "minecraft:looting"})
    pool = {"rolls": 1, "entries": [{"type": "minecraft:item", "name": name, "modifier": mods}]}
    if flag == 'player':
        pool["condition"] = {"type": "minecraft:killed_by_player"}
    if flag == 'rare':
        pool["condition"] = {"type": "minecraft:all_of", "terms": [
            {"type": "minecraft:killed_by_player"}, {"type": "minecraft:random_chance", "chance": 0.1}]}
    return pool


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def main():
    import creatures_more  # the second batch of 28 creatures
    creatures_more.add(S, D)
    import creatures_under  # cave creatures (underground thread)
    creatures_under.add(S, D)
    layers, rigs, switch = [], [], []
    for i, (cid, spec) in enumerate(S.items()):
        W, H = pack(spec)
        write_png(os.path.join(RES, 'assets/onepiece/textures/entity/creature/%s.png' % cid), paint(spec, W, H, i * 31 + 7))
        layers.append(java_layer(cid, spec, W, H))
        switch.append('\t\t\tcase "%s" -> %s();' % (cid, camel(cid)))
        rigs.append('\t\t\tcase "%s" -> %s;' % (cid, rig(spec)))

    java = '''package com.onepiecemod.creature.client;

import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * The block shapes of every One Piece creature. GENERATED by tools/creatures/gen_creatures.py, which also
 * paints the matching textures, so change the shapes there and run it again instead of editing this file.
 *
 * Sizes are in pixels (16 = 1 block), y = 24 is the ground, the front is -Z and the right side is -X.
 * Part names tell CreatureModel how to move them: head, jaw, tail, leg0.., sideleg0.., wing0.., arm0.., puff0..
 */
public final class CreatureModels {
	/** Which moving parts a creature has, so the model knows what to animate. */
	public record Rig(boolean head, boolean jaw, boolean tail, int legs, int sideLegs, int wings, int arms, int puffs) {
	}

	private CreatureModels() {
	}

	public static LayerDefinition create(String id) {
		return switch (id) {
%s
			default -> throw new IllegalArgumentException("No model for creature " + id);
		};
	}

	public static Rig rig(String id) {
		return switch (id) {
%s
			default -> throw new IllegalArgumentException("No rig for creature " + id);
		};
	}

%s
}
''' % ('\n'.join(switch), '\n'.join(rigs), '\n\n'.join(layers))
    os.makedirs(CLIENT_JAVA, exist_ok=True)
    with open(os.path.join(CLIENT_JAVA, 'CreatureModels.java'), 'w') as f:
        f.write(java)

    lang = {}
    for i, (cid, (name, c1, c2, biomes, drops)) in enumerate(D.items()):
        lang['entity.onepiece.%s' % cid] = name
        lang['item.onepiece.%s_spawn_egg' % cid] = name + ' Spawn Egg'
        egg_png(os.path.join(RES, 'assets/onepiece/textures/item/%s_spawn_egg.png' % cid), c1, c2, i)
        wjson(os.path.join(RES, 'assets/onepiece/items/%s_spawn_egg.json' % cid),
              {"model": {"type": "minecraft:model", "model": "onepiece:item/%s_spawn_egg" % cid}})
        wjson(os.path.join(RES, 'assets/onepiece/models/item/%s_spawn_egg.json' % cid),
              {"parent": "minecraft:item/generated", "textures": {"layer0": "onepiece:item/%s_spawn_egg" % cid}})
        wjson(os.path.join(RES, 'data/onepiece/tags/worldgen/biome/spawns/%s.json' % cid),
              {"replace": False, "values": [b if ':' in b else 'minecraft:' + b for b in biomes]})
        wjson(os.path.join(RES, 'data/onepiece/loot_table/entities/%s.json' % cid),
              {"type": "minecraft:entity", "pools": [drop_pool(e) for e in drops],
               "random_sequence": "onepiece:entities/%s" % cid})
    wjson(os.path.join(RES, 'assets/onepiece_creatures/lang/en_us.json'), lang)
    print('generated', len(S), 'creatures')


if __name__ == '__main__':
    main()
