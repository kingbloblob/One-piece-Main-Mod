"""Race features and the character customizer's hair, scars and outfits for PLAYERS.

Run:  python3 appearance.py [path to source/]
Writes:
  src/client/java/com/onepiecemod/body/client/AppearanceModels.java   (the 3D boxes, GENERATED)
  assets/onepiece/textures/entity/appearance/features.png             (race bits, scars, outfits)
  assets/onepiece/textures/entity/appearance/hair.png                 (grey hair, tinted in game)

Every box belongs to a "group". The game shows a group when it applies to that player:
  race:<race id>   from the race picker (Mink ears and tail, Oni horns, Skypiean wings ...)
  hair:<style>     scar:<name>     outfit:<name>     from the body screen (/body)
The names and order of HAIR, SCARS and OUTFITS must match com.onepiecemod.body.Look.

Model space is the player model's: x = the player's left, -y = up, -z = forward (the face).
Head boxes are relative to the neck (the head is -4..4, -8..0, -4..4), body boxes to the neck too
(the body is -4..4, 0..12, -2..2).
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skinkit import hexc, shade

SRC = next((a for a in sys.argv[1:] if not a.startswith('--')), '/mnt/project-files/one-piece-mod/source')


def box(group, name, parent, origin, size, color, pivot=(0, 0, 0), rot=(0, 0, 0), inflate=0.0, faces=None,
        pattern=None):
    return dict(group=group, name=name, parent=parent, origin=origin, size=size, color=color, pivot=pivot,
                rot=rot, inflate=inflate, faces=faces or {}, pattern=pattern)


# ---------------- races ----------------
MINK_FUR, MINK_IN = '#d89a4a', '#f2c8a0'
RACE = [
    box('race:mink', 'mink_ear_r', 'head', (-4.5, -11, -1), (2, 3, 1), MINK_FUR, faces={'front': MINK_IN}),
    box('race:mink', 'mink_ear_l', 'head', (2.5, -11, -1), (2, 3, 1), MINK_FUR, faces={'front': MINK_IN}),
    box('race:mink', 'mink_tail', 'body', (-1, -1, 0), (2, 2, 6), MINK_FUR, pivot=(0, 10, 2), rot=(-35, 0, 0),
        pattern='tail_tip'),
    box('race:oni', 'oni_horn_r', 'head', (-0.5, -4, -0.5), (1, 4, 1), '#ece4cc', pivot=(-2.5, -8, -2.5),
        rot=(-10, 0, -15), pattern='horn'),
    box('race:oni', 'oni_horn_l', 'head', (-0.5, -4, -0.5), (1, 4, 1), '#ece4cc', pivot=(2.5, -8, -2.5),
        rot=(-10, 0, 15), pattern='horn'),
    box('race:fishman', 'fish_fin', 'body', (-0.5, 0, 0), (1, 7, 3), '#3e78b0', pivot=(0, 1, 2), rot=(-8, 0, 0),
        pattern='fin'),
    box('race:fishman', 'fish_fin_head', 'head', (-0.5, -2, 0), (1, 2, 4), '#3e78b0', pivot=(0, -8, -2),
        pattern='fin'),
    box('race:tontatta', 'tontatta_tail', 'body', (-1.5, -1.5, 0), (3, 3, 5), '#b8784a', pivot=(0, 10, 2),
        rot=(-50, 0, 0), pattern='tail_tip'),
]


# ---------------- wings ----------------
# Anime-style feathered wings: a covert "arm" along the top, rows of long flight feathers hanging below it,
# and an outer tip section that angles up. Built for the right wing (the player's right is -x) and mirrored.
# AppearanceModel flaps the parts named <prefix>_r / _l and <prefix>_r_tip / _l_tip.

def mirror(b):
    ox, oy, oz = b['origin']
    w = b['size'][0]
    px, py, pz = b['pivot']
    rx, ry, rz = b['rot']
    m = dict(b)
    m['name'] = b['name'].replace('_r', '_l', 1) if '_r' in b['name'] else b['name']
    m['parent'] = b['parent'].replace('_r', '_l', 1) if b['parent'] not in ('head', 'body') else b['parent']
    m['origin'] = (-(ox + w), oy, oz)
    m['pivot'] = (-px, py, pz)
    m['rot'] = (rx, -ry, -rz)
    m['faces'] = {{'left': 'right', 'right': 'left'}.get(k, k): v for k, v in b['faces'].items()}
    m['share'] = b['name']  # Same texture as the right-hand part.
    return m


def feather(group, name, parent, at, width, length, angle, color, z, tilt=0.0):
    """One flight feather or covert: a flat plane hanging down (+y) from a point on the wing bone,
    turned outward by `angle` degrees and tipped back by `tilt` so the rows fan and overlap."""
    return box(group, name, parent, (-width / 2, 0, 0), (width, length, 0), color, pivot=(at, 0, z),
               rot=(tilt, 0, angle), pattern='feather')


def wing(group, prefix, k, color, pivot, rot):
    """A bird wing for the player's right side (mirrored for the left), k = size (1 = small).

    Bones: shoulder (<prefix>_r) > forearm (_arm, bent up at the elbow) > hand (_tip, bent up at the wrist).
    Feathers, from the body out: tertials and scapulars on the shoulder, secondaries along the forearm,
    primaries fanning out from the hand (longest near the tip, the outermost almost level). Two rows of coverts
    lie over the bases of the flight feathers, on the side that faces back (+z), the way a real wing is layered.
    """
    def n(v):
        return max(1, round(v * k))
    w = max(2, round(2 * k))  # Feather width in pixels.
    root, arm, hand = prefix + '_r', prefix + '_r_arm', prefix + '_r_tip'
    l1, l2, l3 = n(3), n(6), n(4)
    parts = [
        box(group, root, 'body', (-l1, -0.7, -0.5), (l1, 1.4, 1), color, pivot=pivot, rot=rot, pattern='bone'),
        box(group, arm, root, (-l2, -0.6, -0.4), (l2, 1.2, 0.8), color, pivot=(-l1 + 0.3, 0, 0), rot=(0, 0, 14),
            pattern='bone'),
        box(group, hand, arm, (-l3, -0.5, -0.35), (l3, 1, 0.7), color, pivot=(-l2 + 0.3, 0, 0), rot=(0, 0, 22),
            pattern='bone'),
    ]
    # Tertials and scapulars (shoulder).
    for i in range(3):
        x = -l1 * (i + 0.5) / 3
        parts.append(feather(group, '%s_t%d' % (root, i), root, x, w, n(6 + i), -8 + 4 * i, color, 0.05 * i, 4))
        parts.append(feather(group, '%s_s%d' % (root, i), root, x, w, n(3.5), -4 + 3 * i, color, 0.45, 8))
    # Secondaries (forearm) and their two covert rows.
    for i in range(8):
        x = -l2 * (i + 0.5) / 8
        parts.append(feather(group, '%s_f%d' % (arm, i), arm, x, w, n(9 + 0.25 * i), -6 + 3 * i, color, 0.03 * i, 3))
        parts.append(feather(group, '%s_g%d' % (arm, i), arm, x, w, n(4.5), -4 + 3 * i, color, 0.38, 6))
        parts.append(feather(group, '%s_m%d' % (arm, i), arm, x, w, n(2.2), -2 + 2 * i, color, 0.55, 10))
    # Primaries (hand): fanned wide, longest second from the tip.
    lengths = [10.5, 11, 11.5, 12, 12.5, 13, 13.5, 13.5, 12.5]
    for i, length in enumerate(lengths):
        x = -l3 * min(1.0, (i + 0.5) / 7)
        parts.append(feather(group, '%s_p%d' % (hand, i), hand, x, w + 1, n(length), 14 + 7.5 * i, color,
                             0.03 * (len(lengths) - i), 2))
    # Primary coverts.
    for i in range(5):
        x = -l3 * (i + 0.5) / 5
        parts.append(feather(group, '%s_c%d' % (hand, i), hand, x, w, n(4), 14 + 11 * i, color, 0.4, 6))
    right = parts
    return right + [mirror(b) for b in right]


WINGS = (
    # Skypieans (Conis, Pagaya, Enel): small white angel wings high on the back.
    wing('race:skypiean', 'sky_wing', 1.2, '#ffffff', pivot=(-1.5, 2.5, 2.2), rot=(10, 28, 22))
    # Lunarians (King): huge black wings, plus the flame burning on their back.
    + wing('race:lunarian', 'luna_wing', 1.7, '#18181f', pivot=(-1.5, 2, 2.2), rot=(12, 26, 16))
    + [
        box('glow:lunarian', 'luna_flame', 'body', (-3, -12, -1), (6, 12, 2), '#ff8a1a', pivot=(0, 5, 4),
            rot=(-12, 0, 0), pattern='flame'),
        box('glow:lunarian', 'luna_flame_r', 'luna_flame', (-1.5, -8, -0.5), (3, 8, 1), '#ff9a2a',
            pivot=(-3, -1, 0), rot=(0, 0, -25), pattern='flame'),
        box('glow:lunarian', 'luna_flame_l', 'luna_flame', (-1.5, -8, -0.5), (3, 8, 1), '#ff9a2a',
            pivot=(3, -1, 0), rot=(0, 0, 25), pattern='flame'),
    ]
)


# ---------------- hair (painted grey, tinted in game) ----------------
HAIR_CAP = dict(origin=(-4, -8.6, -4), size=(8, 3, 8), inflate=0.3)


def hair_cap(style):
    return box('hair:' + style, style + '_cap', 'head', HAIR_CAP['origin'], HAIR_CAP['size'], '#d8d8d8',
               inflate=HAIR_CAP['inflate'], pattern='hair')


HAIR = [
    hair_cap('spiky'),
    box('hair:spiky', 'spiky_1', 'head', (-3.5, -11, -3), (2, 3, 2), '#d8d8d8', rot=(0, 0, -12), pattern='hair'),
    box('hair:spiky', 'spiky_2', 'head', (0.5, -11.5, -2.5), (2, 3, 2), '#d8d8d8', rot=(0, 0, 10), pattern='hair'),
    box('hair:spiky', 'spiky_3', 'head', (-1.5, -11, 0.5), (2, 3, 2), '#d8d8d8', pattern='hair'),
    box('hair:spiky', 'spiky_4', 'head', (1.5, -10.5, 1.5), (2, 2, 2), '#d8d8d8', pattern='hair'),
    hair_cap('long'),
    box('hair:long', 'long_back', 'head', (-4, -8, 3.6), (8, 12, 1), '#d8d8d8', inflate=0.3, pattern='hair'),
    box('hair:long', 'long_side_r', 'head', (-4.6, -8, -3), (1, 9, 5), '#d8d8d8', inflate=0.2, pattern='hair'),
    box('hair:long', 'long_side_l', 'head', (3.6, -8, -3), (1, 9, 5), '#d8d8d8', inflate=0.2, pattern='hair'),
    box('hair:afro', 'afro', 'head', (-5.5, -12, -5), (11, 8, 11), '#d8d8d8', pattern='curls'),
    hair_cap('topknot'),
    box('hair:topknot', 'topknot', 'head', (-1, -11, -0.5), (2, 3, 3), '#d8d8d8', pattern='hair'),
    hair_cap('pompadour'),
    box('hair:pompadour', 'pompadour', 'head', (-4, -11, -6), (8, 3, 6), '#d8d8d8', inflate=0.2, pattern='hair'),
    hair_cap('ponytail'),
    box('hair:ponytail', 'ponytail', 'head', (-1, 0, 0), (2, 7, 2), '#d8d8d8', pivot=(0, -6, 4.2), rot=(20, 0, 0),
        pattern='hair'),
]

# ---------------- scars (thin decals on the face and chest) ----------------
SCAR = '#a84848'
SCARS = [
    box('scar:eye', 'scar_eye', 'head', (1.5, -7, -4.06), (1, 4, 0), SCAR, pattern='stitch_v'),
    box('scar:cheek', 'scar_cheek', 'head', (0.5, -3.5, -4.06), (3, 1, 0), SCAR, pattern='stitch_h'),
    box('scar:chest_x', 'scar_chest', 'body', (-2.5, 1, -2.06), (5, 5, 0), SCAR, pattern='x'),
    box('scar:burn', 'scar_burn', 'head', (0.5, -7, -4.06), (3, 3, 0), '#c06050', pattern='burn'),
    box('scar:forehead', 'scar_forehead', 'head', (-0.5, -8, -4.06), (1, 2, 0), SCAR),
]

# ---------------- outfits ----------------
STRAW, STRAW_BAND = '#e8c860', '#c82020'
OUTFITS = [
    box('outfit:straw_hat', 'straw_brim', 'head', (-6.5, -8.6, -6.5), (13, 1, 13), STRAW, pattern='straw'),
    box('outfit:straw_hat', 'straw_crown', 'head', (-4.5, -11.6, -4.5), (9, 3, 9), STRAW, pattern='straw_band'),
    box('outfit:marine_coat', 'marine_coat', 'body', (-5, 0, 0), (10, 16, 1), '#f2f2ee', pivot=(0, -0.2, 2.4),
        rot=(6, 0, 0), pattern='justice'),
    box('outfit:marine_coat', 'marine_shoulders', 'body', (-5.5, -0.6, -2.6), (11, 2, 5), '#f2f2ee', inflate=0.1),
    box('outfit:captain_cape', 'captain_cape', 'body', (-5, 0, 0), (10, 16, 1), '#1a1a1e', pivot=(0, -0.2, 2.4),
        rot=(6, 0, 0), faces={'front': '#a01818'}, pattern='cape_trim'),
    box('outfit:captain_cape', 'captain_shoulders', 'body', (-5.5, -0.6, -2.6), (11, 2, 5), '#1a1a1e',
        inflate=0.1, pattern='gold_trim'),
    box('outfit:bandana', 'bandana', 'head', (-4, -8.4, -4), (8, 3, 8), '#2a4ab0', inflate=0.4, pattern='dots'),
    box('outfit:bandana', 'bandana_knot', 'head', (-1, -7, 4.2), (2, 2, 2), '#2a4ab0', pattern='dots'),
    box('outfit:headband', 'headband', 'head', (-4, -6.6, -4), (8, 1, 8), '#f2f2ee', inflate=0.45),
    box('outfit:headband', 'headband_tails', 'head', (-1, -6.6, 4.3), (2, 4, 1), '#f2f2ee', rot=(15, 0, 0)),
    box('outfit:tricorn', 'tricorn_brim', 'head', (-6, -8.8, -6), (12, 1, 12), '#1e1e22', pattern='gold_edge'),
    box('outfit:tricorn', 'tricorn_crown', 'head', (-4.2, -11.6, -4.2), (8.4, 3, 8.4), '#1e1e22', pattern='skull'),
    box('outfit:haramaki', 'haramaki', 'body', (-4, 7, -2), (8, 3, 4), '#3a8a3a', inflate=0.35, pattern='knit'),
]

FEATURES = RACE + WINGS + SCARS + OUTFITS
TEX_FEATURES = 256
TEX_HAIR = 128


# ---------------- texture painting ----------------

def face_regions(u, v, size):
    w, h, d = (int(math.ceil(s)) for s in size)
    return {
        'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h),
    }


def pattern_color(p, base, face, x, y, fw, fh):
    c = hexc(base)
    if p == 'hair':
        f = 1.0 + (0.12 if (x * 3 + y) % 5 == 0 else 0) - (0.14 if (x + y * 2) % 7 == 0 else 0)
        return shade(c, f)
    if p == 'curls':
        return shade(c, 0.85 if (x + y) % 3 == 0 else 1.05 if (x * y) % 4 == 1 else 1.0)
    if p == 'tail_tip':
        return hexc('#f4ead8') if face == 'back' or (face in ('left', 'right', 'top', 'bottom') and x >= fw - 2) else c
    if p == 'horn':
        return shade(c, 1.1) if y == 0 else shade(c, 0.9 + 0.05 * (y % 2))
    if p == 'feathers':
        return shade(c, 0.82) if (y % 3 == 2) or (face in ('left', 'right') and x == fw - 1) else c
    if p == 'feather':
        # A real feather: a shaft down the middle, vanes with fine barb lines, a rounded, slightly darker tip.
        dark = sum(c[:3]) < 200
        if y == fh - 1 and fw >= 3 and (x == 0 or x == fw - 1):
            return None
        if y == fh - 1 and fw == 2 and x == 1:
            return None
        shaft = fw // 2 if fw >= 3 else 0
        f = 1.0
        if x == shaft and y < fh - 1:
            f = 1.45 if dark else 0.93
        elif (x + y) % 3 == 0:
            f = 1.15 if dark else 0.98
        if y >= fh - 2:
            f *= 1.3 if dark else 0.95
        if y < 2:
            f *= 0.92
        return shade(c, f)
    if p == 'bone':
        return shade(c, 1.1 if face == 'top' else 0.95)
    if p == 'coverts':
        # Small rounded covert feathers in rows.
        return shade(c, 0.9) if (x + (y // 2) * 2) % 3 == 0 or y == fh - 1 else shade(c, 1.04) if y == 0 else c
    if p == 'plume':
        # Long flight feathers: a darker shaft line every 2 columns, ragged pointed ends at the bottom.
        if face in ('front', 'back'):
            if y >= fh - 2 and (x % 2 == 1) == (y == fh - 1 or x % 4 == 1):
                return None
            if x % 2 == 1:
                return shade(c, 0.86)
            return shade(c, 1.0 + 0.06 * (y < 2))
        return shade(c, 0.9)
    if p == 'flame':
        # A tongue of fire: pointed at the top, widest low down, yellow core and red-orange rim.
        mid = (fw - 1) / 2
        rel = y / max(1, fh - 1)
        half = fw / 2 * (rel ** 0.8 if rel < 0.75 else 1 - (rel - 0.75) * 1.6)
        if face in ('front', 'back'):
            if abs(x - mid) + 0.5 > half + 0.35:
                return None
            if abs(x - mid) + 0.5 < half * 0.5 and rel > 0.3:
                return hexc('#fff0a0')
            return hexc('#ff4a10') if abs(x - mid) + 1.5 > half else c
        return None if rel < 0.3 else hexc('#ffb030')
    if p == 'fin':
        return shade(c, 0.8) if x % 2 == 0 else shade(c, 1.1)
    if p == 'stitch_v':
        return c if y % 2 == 0 else shade(c, 0.7)
    if p == 'stitch_h':
        return c if x % 2 == 0 else shade(c, 0.7)
    if p == 'x':
        if face != 'front':
            return None
        return c if x == y or x == fw - 1 - y else None
    if p == 'burn':
        return shade(c, 0.85 + 0.1 * ((x + y) % 2)) if (x + y) < 5 else None
    if p == 'straw':
        return shade(c, 0.88) if (x + y) % 2 == 0 else c
    if p == 'straw_band':
        if face in ('front', 'back', 'left', 'right') and y == fh - 1:
            return hexc(STRAW_BAND)
        return shade(c, 0.88) if (x + y) % 2 == 0 else c
    if p == 'justice':
        # The black "JUSTICE" kanji on the back of the coat, and blue cuffs at the bottom.
        if face == 'back' and 2 <= y <= 6 and 1 <= x <= fw - 2 and (x + y) % 2 == 0:
            return hexc('#1a1a1a')
        return hexc('#2a4a9a') if face in ('front', 'back') and y == fh - 1 else c
    if p == 'cape_trim':
        return hexc('#d8b040') if face in ('front', 'back') and (x == 0 or x == fw - 1) else None
    if p == 'gold_trim':
        return hexc('#d8b040') if face in ('left', 'right') or (face == 'top' and (x == 0 or x == fw - 1)) else c
    if p == 'gold_edge':
        return hexc('#d8b040') if face in ('front', 'back', 'left', 'right') else c
    if p == 'skull':
        if face == 'front' and fw // 2 - 1 <= x <= fw // 2 and 1 <= y <= 2:
            return hexc('#f2f2ee')
        return c
    if p == 'dots':
        return hexc('#f2f2ee') if (x * 2 + y * 3) % 5 == 0 else c
    if p == 'knit':
        return shade(c, 0.85) if x % 2 == 0 else c
    return c


def paint(boxes, size, path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    u = v = row_h = 0
    by_name = {b['name']: b for b in boxes}
    for b in boxes:
        if b.get('share'):
            b['uv'] = by_name[b['share']]['uv']
            continue
        w, h, d = (int(math.ceil(s)) for s in b['size'])
        bw, bh = 2 * (w + d), d + h
        if u + bw > size:
            u, v, row_h = 0, v + row_h, 0
        if v + bh > size:
            raise SystemExit('texture %s is full at %s' % (path, b['name']))
        b['uv'] = (u, v)
        for face, (fx, fy, fw, fh) in face_regions(u, v, b['size']).items():
            base = b['faces'].get(face, b['color'])
            for y in range(fh):
                for x in range(fw):
                    col = pattern_color(b['pattern'], base, face, x, y, fw, fh) if b['pattern'] else hexc(base)
                    if col is None:
                        if b['pattern'] in ('cape_trim',):
                            col = hexc(base)
                        else:
                            continue
                    # Simple light: tops bright, bottoms and backs darker.
                    lf = {'top': 1.08, 'bottom': 0.8, 'back': 0.9, 'left': 0.95, 'right': 0.95}.get(face, 1.0)
                    img.putpixel((fx + x, fy + y), shade(col, lf))
        u += bw
        row_h = max(row_h, bh)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# ---------------- java ----------------

def num(f):
    s = ('%.3f' % f).rstrip('0').rstrip('.')
    return (s if s not in ('-0', '') else '0') + 'F'


def java_part(b):
    ox, oy, oz = b['origin']
    w, h, d = b['size']
    infl = ', new CubeDeformation(%s)' % num(b['inflate']) if b['inflate'] else ''
    px, py, pz = b['pivot']
    rx, ry, rz = (math.radians(a) for a in b['rot'])
    return ('\t\tPartDefinition %s = %s.addOrReplaceChild("%s", CubeListBuilder.create().texOffs(%d, %d).addBox(%s, %s, %s, %s, %s, %s%s),\n'
            '\t\t\t\tPartPose.offsetAndRotation(%s, %s, %s, %s, %s, %s));') % (
        b['name'], b['parent'], b['name'], b['uv'][0], b['uv'][1], num(ox), num(oy), num(oz), num(w), num(h), num(d), infl,
        num(px), num(py), num(pz), num(rx), num(ry), num(rz))


def groups_java(boxes):
    groups = {}
    for b in boxes:
        groups.setdefault(b['group'], []).append(b)
    paths = {}
    for b in boxes:
        paths[b['name']] = paths.get(b['parent'], b['parent']) + '/' + b['name']
    return ',\n'.join('\t\t\tMap.entry("%s", List.of(%s))' % (g, ', '.join('"%s"' % paths[b['name']] for b in bs))
                      for g, bs in groups.items())


JAVA = '''package com.onepiecemod.body.client;

import java.util.List;
import java.util.Map;

import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.model.player.PlayerModel;

import com.onepiecemod.OnePieceMod;

/**
 * The 3D race features (Mink ears, Oni horns, wings...) and the body screen's hair, scars and outfits.
 * GENERATED by tools/skins/appearance.py, which also paints the textures: change the boxes there and run it again.
 */
public final class AppearanceModels {
	public static final ModelLayerLocation FEATURES = new ModelLayerLocation(OnePieceMod.id("appearance"), "features");
	public static final ModelLayerLocation HAIR = new ModelLayerLocation(OnePieceMod.id("appearance"), "hair");

	/** Which boxes ("parent/name") belong to each group, like "race:mink" or "outfit:straw_hat". */
	public static final Map<String, List<String>> FEATURE_GROUPS = Map.ofEntries(
%(feature_groups)s
	);
	public static final Map<String, List<String>> HAIR_GROUPS = Map.ofEntries(
%(hair_groups)s
	);

	private AppearanceModels() {
	}

	public static LayerDefinition features() {
		MeshDefinition mesh = PlayerModel.createMesh(CubeDeformation.NONE, false);
		PartDefinition head = mesh.getRoot().getChild("head");
		PartDefinition body = mesh.getRoot().getChild("body");
%(features)s
		return LayerDefinition.create(mesh, %(tf)d, %(tf)d);
	}

	public static LayerDefinition hair() {
		MeshDefinition mesh = PlayerModel.createMesh(CubeDeformation.NONE, false);
		PartDefinition head = mesh.getRoot().getChild("head");
		PartDefinition body = mesh.getRoot().getChild("body");
%(hair)s
		return LayerDefinition.create(mesh, %(th)d, %(th)d);
	}
}
'''


def main():
    tex = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/appearance')
    paint(FEATURES, TEX_FEATURES, os.path.join(tex, 'features.png'))
    paint(HAIR, TEX_HAIR, os.path.join(tex, 'hair.png'))
    out = os.path.join(SRC, 'src/client/java/com/onepiecemod/body/client/AppearanceModels.java')
    with open(out, 'w') as f:
        f.write(JAVA % dict(feature_groups=groups_java(FEATURES), hair_groups=groups_java(HAIR),
                            features='\n'.join(java_part(b) for b in FEATURES),
                            hair='\n'.join(java_part(b) for b in HAIR), tf=TEX_FEATURES, th=TEX_HAIR))
    print('appearance: %d feature boxes, %d hair boxes' % (len(FEATURES), len(HAIR)))


if __name__ == '__main__':
    main()
