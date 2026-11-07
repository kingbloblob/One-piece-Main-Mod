"""Extra 3D shapes for the big characters (bulky bodies, horns, beards, capes, afros, skirts).

Used by gen_skins.py. For every character listed in GIANTS it:
  * paints the extra boxes into the skin, which then becomes 128x128 (the normal 64x64 skin
    stays in the top left corner, the extra boxes go in the free space around it), and
  * writes src/client/java/com/onepiecemod/character/client/GiantModels.java, the matching model.
So shape and texture always match: change a box here and run gen_skins.py again.

Box: dict(part, x, y, z, w, h, d, pivot=(px,py,pz) offset from the part, rot=(rx,ry,rz),
          mirror=True to also add a mirrored copy on the left limb / other side,
          paint=('sample', part, r0, r1)  copy the outfit from that part's rows r0..r1
                ('color', '#hex', pattern))  plain colour; pattern: None, 'hair', 'fur', 'curls', 'dots'
Model space is Minecraft's: 16 px = 1 block, y points down, the front is -z, the right side is -x.
Parts: head (pivot 0,0,0), body (0,0,0), right_arm (-5,2,0), right_leg (-1.9,12,0).
"""
import os
import random

from PIL import Image
from skinkit import PARTS, FRONT, BACK, hexc, shade, mix

TEX = 128   # giant skins are 128x128 (256x256 if the boxes don't fit)
WB_COAT = '#f2f0e8'
MARINE = '#f2f2f0'

# ---------------- shared body plans ----------------

def brute(arm_rows=12, chest=None, legs=True):
    """A huge, broad body: deep chest, thick arms and legs. Covers the normal body with bigger boxes."""
    b = [
        dict(part='body', x=-6, y=-1, z=-3.5, w=12, h=9, d=7, paint=('sample', 'body', 0, 9)),
        dict(part='body', x=-5, y=8, z=-3, w=10, h=5, d=6, paint=('sample', 'body', 8, 12)),
        # arms sit further out so they clear the wide chest
        dict(part='right_arm', x=-6, y=-3, z=-3, w=6, h=7, d=6, mirror=True, paint=('sample', 'arm', 0, 6)),
        dict(part='right_arm', x=-5.5, y=4, z=-2.5, w=5, h=7, d=5, mirror=True, paint=('sample', 'arm', 6, 11)),
        dict(part='right_arm', x=-5.5, y=10.5, z=-2.5, w=5, h=2, d=5, mirror=True, paint=('sample', 'arm', 10, 12)),
    ]
    if legs:
        b.append(dict(part='right_leg', x=-2.6, y=0, z=-2.6, w=5, h=12, d=5, mirror=True, paint=('sample', 'leg', 0, 12)))
    return b


def cape(outer, lining=None, trim=None, collar=None, length=None, wide=False, kanji=False,
         pattern='cloth', ragged=False, width=None, flare=1, sleeves=False, mantle=True):
    """A real 3D cape in three hinged pieces (cape0-2) that GiantModel swings as the character walks.
    lining = inside colour, trim = edge colour, kanji = the Marines' "Justice" on the back,
    ragged = feathery bottom edge, sleeves = empty coat sleeves hanging behind the arms."""
    lining = lining or '#%02x%02x%02x' % shade(outer, 0.7)[:3]
    zp, top = (3.6, -1.5) if wide else (2.2, -0.5)
    w0 = width or (15 if wide else 10)
    total = length or (25 if wide else 23)
    lens = [round(total * 0.36), round(total * 0.32)]
    lens.append(total - sum(lens))
    b, y0, parent, piv = [], 0, 'body', (0, top, zp)
    for k, ln in enumerate(lens):
        w = w0 + 2 * flare * k
        b.append(dict(name='cape%d' % k, part=parent, x=-w / 2, y=0, z=0, w=w, h=ln, d=1, pivot=piv,
                      paint=('cape', outer, lining, trim, pattern, y0, total, kanji, ragged and k == 2)))
        parent, piv, y0 = 'cape%d' % k, (0, ln, 0), y0 + ln
    if mantle:   # the part resting on the shoulders
        if wide:
            b.append(dict(part='right_arm', x=-6.6, y=-3.8, z=-3.8, w=8, h=3, d=8, mirror=True, paint=('color', outer, pattern)))
        else:
            b.append(dict(part='right_arm', x=-3.6, y=-2.6, z=-2.6, w=5, h=2, d=5, mirror=True, paint=('color', outer, pattern)))
    if collar:
        b.append(dict(part='body', x=-6.5 if wide else -5, y=-3 if wide else -1.5, z=-3.8 if wide else -2.8,
                      w=13 if wide else 10, h=3, d=9 if wide else 7, paint=('color', collar, 'fur')))
    if sleeves:
        b.append(dict(part='cape0', x=-w0 / 2 - 1, y=1, z=0.2, w=3, h=10, d=3, mirror=True, rot=(0.05, 0, 0.08),
                      paint=('color', outer, 'cloth')))
    return b


def horns(color, spread=0.4, length=5, at=(3.0, -8.0, -1.5)):
    x, y, z = at
    return [dict(part='head', x=-0.5, y=-length, z=-0.5, w=1, h=length, d=1, pivot=(-x, y, z),
                 rot=(-0.25, 0, -spread), mirror=True, paint=('color', color, None)),
            dict(part='head', x=-1, y=-1.5, z=-1, w=2, h=2, d=2, pivot=(-x, y, z),
                 rot=(-0.25, 0, -spread), mirror=True, paint=('color', color, None))]


def hair_back(color, length=12, width=9):
    return [dict(part='head', x=-width / 2, y=-8.5, z=3, w=width, h=length, d=2, paint=('color', color, 'hair'))]


def beard(color, w=8, h=4):
    return [dict(part='head', x=-w / 2, y=-2.5, z=-4.8, w=w, h=h, d=2, paint=('color', color, 'hair'))]


def afro(color, w=12, h=8, d=11, y=-13):
    return [dict(part='head', x=-w / 2, y=y, z=-5, w=w, h=h, d=d, paint=('color', color, 'curls'))]


def marine_cape():
    return cape(MARINE, '#d8d8e0', kanji=True)


def shades(lens, frame='#202020'):
    return [dict(part='head', x=-4.5, y=-4.6, z=-4.7, w=9, h=2, d=1, paint=('color', frame, 'shades:' + lens))]


def top_hat(color, band=None, brim=11, crown=8, tall=7, top=-8.5, pattern=None):
    """A real top hat: flat brim, tall crown. top = where the brim sits (y, -8.5 = on the head)."""
    b = [dict(part='head', x=-brim / 2, y=top, z=-brim / 2, w=brim, h=1, d=brim, paint=('color', color, None)),
         dict(part='head', x=-crown / 2, y=top - tall, z=-crown / 2, w=crown, h=tall, d=crown, paint=('color', color, pattern))]
    if band:
        b.append(dict(part='head', x=-crown / 2 - 0.2, y=top - 2, z=-crown / 2 - 0.2, w=crown + 0.4, h=1, d=crown + 0.4,
                      paint=('color', band, None)))
    return b


def antlers(color, at=(4.0, -7.0, -1.0)):
    """Chopper's antlers: a thick branch out of each side of the hat with two prongs."""
    return [dict(part='head', x=-1, y=-7, z=-1, w=2, h=7, d=2, pivot=(-at[0], at[1], at[2]), rot=(-0.2, 0, -0.95),
                 mirror=True, paint=('color', color, 'hair')),
            dict(part='head', x=-1, y=-5.5, z=-0.5, w=4, h=1.5, d=1.5, pivot=(-at[0], at[1], at[2]), rot=(-0.2, 0, -0.95),
                 mirror=True, paint=('color', color, None)),
            dict(part='head', x=-1, y=-3, z=-0.5, w=3, h=1.5, d=1.5, pivot=(-at[0], at[1], at[2]), rot=(-0.2, 0, -0.95),
                 mirror=True, paint=('color', color, None))]


def drum_ring(gold='#d8a830', skin='#e8e0d0'):
    """Enel's ring of drums (the Tomoe drums) floating behind his back."""
    ring = [dict(part='body', x=-9, y=-10, z=4, w=18, h=1, d=1, paint=('color', gold, None)),
            dict(part='body', x=-9, y=8, z=4, w=18, h=1, d=1, paint=('color', gold, None)),
            dict(part='body', x=-9, y=-10, z=4, w=1, h=19, d=1, paint=('color', gold, None)),
            dict(part='body', x=8, y=-10, z=4, w=1, h=19, d=1, paint=('color', gold, None))]
    drums = []
    for (x, y) in ((-11, -3), (7, -3), (-2, -12), (-2, 6)):
        drums.append(dict(part='body', x=x, y=y, z=3, w=4, h=4, d=3, paint=('color', gold, 'drum')))
    return ring + drums


def katana(handle='#2a2a34', sheath='#141416', at=(6.4, 9.0, 0.0), tilt=1.15, spread=0.12):
    """A katana worn through the sash on the left hip: handle forward and up, scabbard back and down."""
    x, y, z = at
    return [dict(part='body', x=-0.5, y=-6, z=-0.5, w=1, h=4, d=1, pivot=(x, y, z), rot=(tilt, 0, spread),
                 paint=('color', handle, 'scabbard')),
            dict(part='body', x=-1, y=-2.2, z=-1, w=2, h=1, d=2, pivot=(x, y, z), rot=(tilt, 0, spread),
                 paint=('color', '#c8a040', 'metal')),
            dict(part='body', x=-0.5, y=-1.2, z=-0.6, w=1, h=11, d=1.2, pivot=(x, y, z), rot=(tilt, 0, spread),
                 paint=('color', sheath, None))]


def s_horn(color, at=(3.2, -7.5, -1.0), size=1.0):
    """A horn that curls like an S (Imu): three segments, each starting at the end of the one before."""
    import math
    out, (x, y, z), ang = [], at, 0.0
    for ln, th, turn in ((4.5, 2, 0.75), (4, 1.6, -0.55), (3.5, 1.2, 0.95)):
        ln, th = ln * size, th * size
        ang += turn
        out.append(dict(part='head', x=-th / 2, y=-ln, z=-th / 2, w=th, h=ln, d=th, pivot=(-x, y, z),
                        rot=(-0.15, 0, -ang), mirror=True, paint=('color', color, None)))
        x, y = x + ln * math.sin(ang), y - ln * math.cos(ang)
    return out


def spikes(color, pat='hair', n=7, at_y=-8.0, ln=6, tilt=-0.55, fan=0.75, r=4.2):
    """Wild spiky hair: spikes fanning out round the top and back of the head."""
    import math
    out = []
    for k in range(n):
        a = -1.25 + 2.5 * k / (n - 1)
        out.append(dict(part='head', x=-1.5, y=-ln, z=-1.5, w=3, h=ln, d=3, pivot=(r * math.sin(a), at_y + 1.5, 1.5 + 1.5 * math.cos(a)),
                        rot=(tilt, 0, a * fan), paint=('color', color, pat)))
    return out


def nio_dasuki(wide=False):
    """The nio-dasuki (Oden, Yamato): a thick purple-and-white twisted rope over the shoulders, tied in a huge bow on
    the back."""
    sx, z = (6.5, 3.5) if wide else (4.5, 2)
    c = ('color', '#7a3aa8', 'twist:#f4f0f8')
    return [dict(part='body', x=-sx - 0.5, y=-1.6, z=-z - 0.6, w=3, h=2, d=2 * z + 1.2, mirror=True, paint=c),   # over the shoulders
            dict(part='body', x=-sx, y=0.5, z=z - 0.4, w=2 * sx, h=2, d=2, paint=c),                               # across the back
            dict(part='body', x=-2, y=-0.5, z=z + 0.5, w=4, h=4, d=3, paint=c),                                    # the knot
            dict(part='body', x=-9 if wide else -7, y=-3, z=z + 1, w=7 if wide else 5.5, h=5, d=2, pivot=(0, 1.5, 0),
                 rot=(0, 0, 0.35), mirror=True, paint=c),                                                          # bow loops
            dict(part='body', x=-4, y=0, z=z + 1, w=2, h=7, d=1.5, pivot=(-1, 2, 0), rot=(0, 0, -0.25), mirror=True, paint=c)]   # ends


def wing(color, pat='wing', at=(-2.0, 1.0, 2.6), spread=0.45, lift=0.3, size=1.0, back=0.25):
    """A bat/pteranodon wing on the back: a bony top edge and a membrane hanging from it. Mirrored."""
    w, h = 16 * size, 15 * size
    return [dict(part='body', x=-w, y=-1, z=0, w=w, h=h, d=1, pivot=at, rot=(back, spread, lift), mirror=True,
                 paint=('color', color, pat)),
            dict(part='body', x=-w - 1, y=-2.5, z=-0.5, w=w + 1, h=2, d=2, pivot=at, rot=(back, spread, lift), mirror=True,
                 paint=('color', color, 'leather'))]


# Parts of the normal player model that a character does not have (Shanks lost his left arm).
HIDDEN = {'shanks': ['left_arm']}

# Parts whose normal player-shaped box is NOT drawn (its extra boxes still are). Used to give a character a
# different body shape: Brook's thin skeleton limbs, Chopper's big head and stubby legs, Ivankov's huge head.
STRIP = {
    'hancock': ['body', 'right_arm', 'left_arm'],
    'big_mom': ['head', 'hat'],
    'brook': ['body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'],
    'chopper': ['head', 'hat', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'],
    'vegapunk': ['head', 'hat'],
    'ivankov': ['head', 'hat'],
    'moria': ['head', 'hat', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'],
    'franky': ['right_arm', 'left_arm'],
    'imu': ['right_leg', 'left_leg'],
}

# Arm/leg swing multiplier for short-limbed characters (their limbs hang far below the joint).
SWING = {'chopper': 0.4}

# Extra leg length in px for famously long-legged characters: GiantModel raises the hips (and everything above
# them) by this much and long_legs() draws longer legs, so they still reach the ground.
# Wide bodies: the shoulders sit this many px further out, so the arms (and what they hold) clear the body
ARMS_OUT = {'big_mom': 8}
LEGS = {'doflamingo': 4, 'aokiji': 4, 'katakuri': 4, 'kizaru': 3, 'hancock': 5}
for _cid in LEGS:
    STRIP.setdefault(_cid, []).extend(['right_leg', 'left_leg'])


def long_legs(cid, w=4):
    n = LEGS[cid]
    return [dict(part='right_leg', x=-w / 2, y=0, z=-2, w=w, h=12 + n, d=4, mirror=True, paint=('sample', 'leg', 0, 12))]


# ---------------- reshaped bodies (with STRIP) ----------------

def skeleton():
    """Brook: a skeleton in a suit. Narrow chest, stick-thin arms and legs (2 px), skull kept full size."""
    return [
        dict(part='body', x=-3, y=0, z=-1.5, w=6, h=12, d=3, paint=('sample', 'body', 0, 12)),
        dict(part='body', x=-4, y=0, z=-2, w=8, h=2, d=4, paint=('sample', 'body', 0, 2)),       # shoulders of the jacket
        dict(part='right_arm', x=-0.5, y=-2, z=-1, w=2, h=13, d=2, mirror=True, paint=('sample', 'arm', 0, 12)),
        dict(part='right_leg', x=-1, y=0, z=-1, w=2, h=12, d=2, mirror=True, paint=('sample', 'leg', 0, 12)),
        dict(part='right_leg', x=-1.5, y=10, z=-2.5, w=3, h=2, d=4, mirror=True, paint=('sample', 'leg', 10, 12)),   # shoes
    ]


def chibi_reindeer():
    """Chopper's Brain Point: head about as big as his body, round little torso, stubby arms and legs.
    Head pivot stays at the neck (y 0) so the head box hangs below it; feet still end at the ground (y 24)."""
    return [
        dict(part='head', x=-6, y=-3, z=-5.5, w=12, h=11, d=11, paint=('sample', 'head', 0, 8)),
        dict(part='body', x=-4, y=8, z=-3, w=8, h=11, d=6, paint=('sample', 'body', 0, 12)),
        dict(part='right_arm', x=-2, y=7, z=-1.5, w=3, h=7, d=3, mirror=True, paint=('sample', 'arm', 0, 12)),
        dict(part='right_leg', x=-1.5, y=6, z=-1.5, w=3, h=6, d=3, mirror=True, paint=('sample', 'leg', 0, 12)),
        dict(part='head', x=-1, y=3, z=-6.5, w=2, h=2, d=1, paint=('color', '#3a6ad0', None)),     # blue nose
    ]


# ---------------- the giants ----------------


GIANTS = {
    'whitebeard': brute() + cape(WB_COAT, '#c8c0d8', wide=True, sleeves=True) + [
        # the crescent mustache, sticking out past the face
        dict(part='head', x=-3, y=-3.2, z=-4.9, w=6, h=1, d=1, paint=('color', '#f4f4f0', None)),
        dict(part='head', x=3, y=-4.2, z=-4.9, w=2, h=1, d=1, mirror=True, paint=('color', '#f4f4f0', None)),
        dict(part='head', x=5, y=-7.2, z=-4.9, w=1, h=3, d=1, mirror=True, paint=('color', '#f4f4f0', None)),
        # bandana knot tails
        dict(part='head', x=-1, y=-7, z=4, w=2, h=4, d=1, rot=(0.3, 0, 0), paint=('color', '#18181a', None)),
    ],
    'blackbeard': brute() + cape('#18181a', '#5a1a1a', wide=True, sleeves=True) + beard('#141414', 9, 5) + [
        dict(part='body', x=-5.5, y=3.5, z=-5.5, w=11, h=7, d=3, paint=('sample', 'body', 3, 10)),   # the big belly
    ],
    # Big Mom: very wide and round, a big grinning head with pink curls flaring out to both sides,
    # her pink bicorne pirate hat (skull and crossbones, white plume) and the pink polka-dot dress with a white hem
    'big_mom': [
        dict(part='head', x=-6.5, y=-12, z=-6, w=13, h=12, d=12, paint=('sample', 'head', 0, 8)),
        dict(part='body', x=-11, y=-1, z=-5, w=22, h=6, d=10, paint=('sample', 'body', 0, 6)),
        dict(part='body', x=-11.5, y=3, z=-5.5, w=23, h=1, d=11, paint=('color', '#e0b040', 'metal')),   # gold neckline
        dict(part='body', x=-12.5, y=4, z=-7.5, w=25, h=16, d=15, paint=('color', '#f6aac0', 'polka')),  # the dress
        dict(part='body', x=-13, y=19.5, z=-8, w=26, h=2, d=16, paint=('color', '#f6f2f4', 'cloth')),     # white hem
        dict(part='right_arm', x=-5, y=-3, z=-3.5, w=7, h=14, d=7, mirror=True, paint=('sample', 'arm', 0, 12)),   # shoulders moved out by ARMS_OUT
        # pink curls: a cap under the hat, a mass down the back and big puffs flaring out to the sides
        dict(part='head', x=-8, y=-15, z=-7, w=16, h=4, d=14, paint=('color', '#f07aa8', 'curls')),
        dict(part='head', x=-9, y=-14, z=4, w=18, h=16, d=5, paint=('color', '#ec70a2', 'curls')),
        dict(part='head', x=-17, y=-16, z=-5, w=10, h=10, d=11, mirror=True, paint=('color', '#f584b0', 'curls')),
        dict(part='head', x=-22, y=-14, z=-3, w=6, h=7, d=8, mirror=True, paint=('color', '#f07aa8', 'curls')),
        dict(part='head', x=-15, y=-7, z=-3, w=7, h=8, d=9, mirror=True, paint=('color', '#ec70a2', 'curls')),
        # the bicorne: crown, gold band, a tall front flap with the Jolly Roger, a back flap and a white plume
        dict(part='head', x=-7, y=-20, z=-5, w=14, h=5, d=10, paint=('color', '#f08cb4', 'cloth')),
        dict(part='head', x=-7.5, y=-16.5, z=-5.5, w=15, h=1.5, d=11, paint=('color', '#e0b040', 'metal')),
        dict(part='head', x=-11, y=-23, z=-7, w=22, h=8, d=2, paint=('color', '#f08cb4', 'jolly')),
        dict(part='head', x=-10, y=-22, z=4, w=20, h=6, d=2, paint=('color', '#e07aa4', 'cloth')),
        dict(part='head', x=5, y=-26, z=-3, w=9, h=9, d=10, paint=('color', '#f8f6f8', 'curls')),
    ],
    'kaido': brute() + cape('#3a3048', '#2c2438', trim='#d8b040', wide=True, sleeves=True, flare=0) + hair_back('#1a1a20', 14, 10) + beard('#1a1a20', 8, 4)
             + horns('#e8e0d0', 0.35, 6) + [
        dict(part='body', x=-7, y=7.5, z=-4.5, w=14, h=2, d=9, paint=('color', '#ece4c8', 'fur')),    # rope belt
        dict(part='right_arm', x=-4.5, y=4, z=-3, w=6, h=2, d=6, mirror=True, paint=('color', '#5a5a64', 'dots')),
    ],
    'kuma': brute() + [
        # round bear ears on his cap, cream like the cap (same look as the Pacifista)
        dict(part='head', x=-1, y=-1.5, z=-0.5, w=3, h=3, d=1, pivot=(-3.5, -9, 0), mirror=True, paint=('color', '#ece6d6', None)),
        # his Bible, always in his left hand
        dict(part='left_arm', x=1, y=8, z=-5.5, w=4, h=6, d=2, paint=('color', '#4a2018', 'band')),
    ],
    # Moria: pear-shaped giant: small head held high on a long thick neck, narrow shoulders, enormous round
    # belly, short thin legs; black coat with the big orange fur collar, little horns.
    'moria': [
        dict(part='head', x=-4, y=-14, z=-4, w=8, h=8, d=8, paint=('sample', 'head', 0, 8)),            # head up on the neck
        dict(part='head', x=-3, y=-6, z=-3, w=6, h=7, d=6, paint=('color', '#9aa8c0', None)),             # long neck
        dict(part='body', x=-6, y=-1, z=-3.5, w=12, h=6, d=7, paint=('sample', 'body', 0, 5)),          # chest
        dict(part='body', x=-9, y=3, z=-7, w=18, h=10, d=14, paint=('sample', 'body', 3, 12)),         # the huge belly
        dict(part='right_arm', x=-9, y=-1, z=-2.5, w=5, h=14, d=5, mirror=True, paint=('sample', 'arm', 0, 12)),
        dict(part='right_leg', x=-1.5, y=1, z=-1.5, w=3, h=11, d=3, mirror=True, paint=('sample', 'leg', 1, 12)),
    ] + cape('#1a1420', '#6a2a8a', collar='#e08030', wide=True) + horns('#e8e0d0', 0.5, 3, at=(3.0, -14.0, -1.5)),
    'katakuri': brute(legs=False) + long_legs('katakuri') + [
        dict(part='head', x=-5, y=-3.5, z=-5, w=10, h=4, d=10, paint=('color', '#7a7060', 'fur')),   # big scarf
    ],
    # King (One Piece Wiki): a towering Lunarian: brown skin, black feathered wings, a flame rising from his upper back,
    # a full-face black leather mask with goggle lenses and horn-like spikes, white hair long on top and bound at the
    # back, a dark-blue double-breasted leather jacket with gold buttons, black high-heeled boots
    'king': brute() + wing('#141416', 'feather', size=1.45, spread=0.2, lift=0.55, back=0.2) + [
        dict(part='head', x=-4.6, y=-8.6, z=-4.6, w=9.2, h=1, d=9.2, paint=('color', '#1a1a1e', 'leather')),  # mask top
        dict(part='head', x=-2, y=-11, z=-1, w=4, h=3, d=5, paint=('color', '#ececec', 'hair')),            # hair bound on top
        dict(name='tail0', part='head', x=-2.5, y=0, z=0, w=5, h=10, d=2, pivot=(0, -9, 3.5), rot=(0.35, 0, 0), paint=('color', '#eeeeee', 'hair')),
        dict(part='tail0', x=-3, y=9.5, z=-0.5, w=6, h=10, d=2, rot=(-0.2, 0, 0), paint=('color', '#e4e4e4', 'hair')),
        dict(part='body', x=-6, y=-8, z=3.4, w=12, h=8, d=4, paint=('color', '#ff7a20', 'flame')),            # Lunarian flame
        dict(part='body', x=-4, y=-13, z=4, w=8, h=5, d=3, paint=('color', '#ff7a20', 'flame')),
        dict(part='body', x=-2, y=-16, z=4.5, w=4, h=3, d=2, paint=('color', '#ff7a20', 'flame')),
        dict(part='right_leg', x=-1, y=11, z=1.5, w=2, h=2, d=2, mirror=True, paint=('color', '#0e0e10', None)),   # boot heels
    ] + horns('#1a1a1e', 0.75, 4, at=(3.2, -7.0, -2.0)) + horns('#1a1a1e', 0.45, 3, at=(2.2, -8.0, 1.5)),
    # Oden (One Piece Wiki): huge and muscular, long wild black hair with a flat circular top, red eyeliner, short goatee,
    # an orange kimono with two yellow crescent moons that leaves his legs bare, a big purple-and-white nio-dasuki tied
    # round his shoulders, and two swords (Enma, and Ame no Habakiri with its golden guard) at his hip
    'oden': brute() + hair_back('#141414', 14, 11) + [
        dict(part='head', x=-7, y=-13, z=-5, w=14, h=5, d=10, paint=('color', '#141414', 'hair')),           # flat round top
        dict(part='head', x=-5, y=-13, z=-7, w=10, h=5, d=14, paint=('color', '#161616', 'hair')),
        dict(part='head', x=-6, y=-9, z=-2, w=2, h=11, d=7, mirror=True, paint=('color', '#141414', 'hair')),   # wild sides
        dict(part='head', x=-1.5, y=0, z=-4.7, w=3, h=1.5, d=1, paint=('color', '#141414', 'hair')),         # goatee
    ] + spikes('#141414', n=7, at_y=-11, ln=5, tilt=-0.9, fan=1.1, r=6.5) + spikes('#141414', n=5, at_y=-6, ln=6, tilt=-0.4, fan=1.3, r=5.5) + nio_dasuki(wide=True)
      + katana('#141414', '#141414', at=(6.6, 8.6, -1.0)) + katana('#3a2a20', '#2a1a14', at=(6.9, 9.6, 0.5), tilt=1.3, spread=0.2),
    'jinbe': brute() + hair_back('#141418', 6, 6) + [
        dict(part='head', x=-1.5, y=-11, z=-1.5, w=3, h=3, d=3, paint=('color', '#141418', 'hair')),   # top knot
        dict(part='head', x=-5, y=-4, z=-4.5, w=1, h=5, d=4, mirror=True, paint=('color', '#141418', 'hair')),   # sideburns
        dict(part='head', x=-4.5, y=-2, z=-5, w=9, h=3, d=1, paint=('color', '#5a7aa0', None)),   # the big jaw
        dict(part='body', x=-6.5, y=4, z=-5, w=13, h=6, d=9, paint=('sample', 'body', 4, 10)),     # round belly
    ],
    # the Straw Hats' own shapes
    'usopp': [dict(part='head', x=-1, y=-4, z=-10, w=2, h=2, d=6, paint=('color', '#b07a50', 'nose'))],   # the long nose
    'chopper': chibi_reindeer() + antlers('#6a4a2a', at=(5.0, -3.5, -0.5))
               + top_hat('#f07aa8', brim=15, crown=11, tall=8, top=-3.5, pattern='xcross'),
    'brook': skeleton() + afro('#141414', 12, 7, 11, -13) + top_hat('#141414', band='#e8c040', brim=13, crown=8, tall=8, top=-13.5),
    'crocodile': cape('#1e2a24', '#3a5a4a', collar='#6a5a3a') + [
        # the golden hook in place of his left hand
        dict(part='left_arm', x=-1.5, y=9.5, z=-2.5, w=5, h=3, d=5, paint=('color', '#d8a830', None)),
        dict(part='left_arm', x=0.5, y=12, z=-0.5, w=1, h=4, d=1, paint=('color', '#e8c040', None)),
        dict(part='left_arm', x=0.5, y=15.5, z=-4, w=1, h=1, d=4, paint=('color', '#e8c040', None)),
        dict(part='left_arm', x=0.5, y=12.5, z=-4, w=1, h=3, d=1, paint=('color', '#e8c040', None)),
    ],
    'kid': cape('#a02020', '#5a1010', collar='#e8e4d8', pattern='fur') + [
        # his mechanical left arm
        dict(part='left_arm', x=-1.5, y=-2.5, z=-2.5, w=5, h=13, d=5, paint=('color', '#8a3a2a', 'metal')),
        dict(part='left_arm', x=-2, y=3, z=-3, w=6, h=2, d=6, paint=('color', '#5a5a64', None)),
        dict(part='left_arm', x=-2, y=8, z=-3, w=6, h=2, d=6, paint=('color', '#5a5a64', None)),
    ],
    'lucci': top_hat('#141414', band='#f0f0f0', brim=11, crown=8, tall=6) + [
        # Hattori the pigeon on his shoulder
        dict(part='body', x=-8.5, y=-3, z=-1.5, w=3, h=3, d=4, paint=('color', '#f4f4f4', 'pigeon')),
        dict(part='body', x=-8, y=-5, z=-2.5, w=2, h=2, d=2, paint=('color', '#f4f4f4', None)),
        dict(part='body', x=-7.5, y=-4, z=-3.5, w=1, h=1, d=1, paint=('color', '#e8a030', None)),
    ],
    'enel': drum_ring() + [
        dict(part='head', x=4, y=-3, z=-1, w=1, h=6, d=2, mirror=True, paint=('color', '#dca478', None)),   # long earlobes
    ],
    'magellan': brute() + horns('#3a2a4a', 0.2, 3),
    # Ivankov: a head nearly as big as his chest, under an even bigger round purple afro, and a dark cape
    'ivankov': [
        dict(part='head', x=-7, y=-13, z=-6.5, w=14, h=13, d=13, paint=('sample', 'head', 0, 8)),
        dict(part='head', x=-9, y=-21, z=-8, w=18, h=8, d=16, paint=('color', '#6a3a8a', 'curls')),   # afro: wide middle
        dict(part='head', x=-7, y=-25, z=-6.5, w=14, h=4, d=13, paint=('color', '#72408f', 'curls')),  # rounded top
        dict(part='head', x=-8, y=-15, z=3.5, w=16, h=9, d=5, paint=('color', '#5e3280', 'curls')),    # down the back
        dict(part='head', x=-8.5, y=-14, z=-6, w=2, h=5, d=9, mirror=True, paint=('color', '#6a3a8a', 'curls')),  # over the ears
    ] + cape('#2a2240', '#5a2a6a', collar='#2a2240', length=22),
    # Imu (as finally revealed): tanned skin, long white hair, S-curled horns, red ringed eyes, a black robe
    # down to the ground, folded dark wings and a devil's tail
    'imu': s_horn('#3a2a30', at=(3.0, -8.0, -0.5), size=1.5) + wing('#2a2232', size=1.1, spread=0.2, lift=0.45, back=0.3) + [
        dict(part='head', x=-4.6, y=-8.6, z=-3.6, w=9.2, h=1.6, d=8.2, paint=('color', '#f0f0f0', 'hair')),   # hair cap
        dict(part='head', x=-4.6, y=-6.5, z=3, w=9.2, h=20, d=2, paint=('color', '#f0f0f0', 'hair')),         # down the back
        dict(part='head', x=-5, y=-7, z=-3.5, w=1.2, h=13, d=2.5, mirror=True, paint=('color', '#ececec', 'hair')),  # locks in front
        dict(part='body', x=-4.5, y=-0.5, z=-2.5, w=9, h=11, d=5, paint=('sample', 'body', 0, 11)),            # robe
        dict(part='body', x=-5.5, y=10, z=-3.5, w=11, h=14, d=7, paint=('color', '#16141a', 'cloth')),          # robe to the ground
        dict(part='body', x=-5.6, y=22.5, z=-3.6, w=11.2, h=1.5, d=7.2, paint=('color', '#c8a040', 'metal')),    # gold hem
        dict(part='body', x=-0.5, y=-1.5, z=-2.7, w=1, h=24, d=0.5, paint=('color', '#c8a040', 'metal')),       # gold front seam
        dict(part='right_arm', x=-3.5, y=3, z=-3, w=5, h=9, d=6, mirror=True, paint=('color', '#16141a', 'cloth')),  # wide sleeves
        dict(name='tail0', part='body', x=-1, y=0, z=-1, w=2, h=12, d=2, pivot=(0, 11, 3.5), rot=(0.85, 0, 0), paint=('color', '#1e1a24', 'leather')),
        dict(part='tail0', x=-2, y=11, z=-1.5, w=4, h=4, d=1, rot=(0, 0, 0.785), paint=('color', '#1e1a24', None)),   # spade tip
    ],
    'doflamingo': long_legs('doflamingo') + cape('#f070b8', '#c84890', pattern='fur', ragged=True, width=13, flare=2, mantle=False) + shades('#d02060', '#f4f4f4') + [
        dict(part='body', x=-7.5, y=-3, z=-4.5, w=15, h=4, d=10, paint=('color', '#ff90c8', 'fur')),     # big feather collar
        dict(part='right_arm', x=-4.5, y=-3.5, z=-3.5, w=6, h=5, d=7, mirror=True, paint=('color', '#f584c0', 'fur')),
    ],
    # Franky: barrel chest, thin upper arms, his famous giant forearms with the blue stars, metal nose
    'franky': [
        dict(part='body', x=-5.5, y=-0.5, z=-3, w=11, h=8, d=6, paint=('sample', 'body', 0, 8)),
        dict(part='right_arm', x=-4, y=-2, z=-1.5, w=3, h=6, d=3, mirror=True, paint=('sample', 'arm', 0, 5)),
        dict(part='right_arm', x=-6, y=3, z=-3, w=6, h=8, d=6, mirror=True, paint=('sample', 'arm', 4, 11)),
        dict(part='right_arm', x=-5.5, y=10.5, z=-2.5, w=5, h=2.5, d=5, mirror=True, paint=('sample', 'arm', 10, 12)),
        dict(part='head', x=-1, y=-4, z=-5.5, w=2, h=2, d=2, paint=('color', '#a8b0b8', 'metal')),
    ],
    # Vegapunk (Stella): the Nomi Nomi fruit grew his brain, so his bald head is enormous and tall
    'vegapunk': [
        dict(part='head', x=-5, y=-9, z=-5, w=10, h=9, d=10, paint=('sample', 'head', 0, 8)),
        dict(part='head', x=-8, y=-21, z=-8, w=16, h=13, d=16, paint=('color', '#f2c9a0', None)),      # the huge bald cranium
        dict(part='head', x=-6.5, y=-25, z=-6.5, w=13, h=4, d=13, paint=('color', '#f4cea6', None)),
        dict(part='head', x=-8.5, y=-12, z=1, w=17, h=5, d=8, paint=('color', '#9a8ab0', 'hair')),     # hair round the back
        dict(part='head', x=-8.5, y=-12, z=-6, w=1, h=5, d=7, mirror=True, paint=('color', '#9a8ab0', 'hair')),
    ],
    # Boa Hancock: tall and statuesque: very long legs, slim waist and arms, full chest, long black hair to her waist
    'hancock': long_legs('hancock', w=3.5) + hair_back('#141418', 15, 8)
               + cape('#f4f2ea', '#d8d4e4', length=27, width=12, flare=1, mantle=False) + [
        dict(part='right_arm', x=-1.5, y=-2.6, z=-2, w=4, h=1.5, d=4, mirror=True, paint=('color', '#e8c040', None)),   # gold epaulettes
        dict(part='right_arm', x=-1.5, y=-1.1, z=-2, w=4, h=1, d=4, mirror=True, paint=('color', '#d8a830', None)),
        dict(part='body', x=-3.5, y=0, z=-2, w=7, h=12, d=4, paint=('sample', 'body', 0, 12)),
        dict(part='body', x=-3, y=2, z=-3.5, w=6, h=3, d=2, paint=('sample', 'body', 2, 5)),           # chest
        dict(part='body', x=-4, y=8, z=-2.5, w=8, h=4, d=5, paint=('sample', 'body', 8, 12)),          # hips
        dict(part='right_arm', x=-1, y=-2, z=-1.5, w=3, h=12, d=3, mirror=True, paint=('sample', 'arm', 0, 12)),
    ],
    # Yamato (One Piece Wiki): long white hair bound between orange rods into a ponytail whose ends fade from aqua green
    # to blue, red horns turning flesh-coloured at the base, orange eyes, gold hoop earrings, a sleeveless white top
    # with diamond designs and an indigo wisp-patterned bottom half, red hakama, sandals, and the big purple-and-white
    # nio-dasuki (rope tied in a bow) on the back
    'yamato': [dict(b, paint=('color', '#e8a890', None)) if b['h'] == 2 else b for b in horns('#d82828', 0.3, 4)] + [
        dict(part='head', x=-4.6, y=-8.6, z=-4.6, w=9.2, h=2, d=9.2, paint=('color', '#f4f4f4', 'hair')),
        dict(part='head', x=-4.6, y=-7, z=-4.7, w=3, h=2, d=1, paint=('color', '#f4f4f4', 'hair')),            # fringe
        dict(part='head', x=1.6, y=-7, z=-4.7, w=3, h=2, d=1, paint=('color', '#f4f4f4', 'hair')),
        dict(part='head', x=-5, y=-7, z=-3.5, w=1.2, h=9, d=1.5, mirror=True, paint=('color', '#f4f4f4', 'tips:#3ab8b0')),
        dict(part='head', x=-4.7, y=-3, z=-0.6, w=0.6, h=2.5, d=1.2, mirror=True, paint=('color', '#e8c040', 'metal')),   # hoops
        dict(part='head', x=-2.5, y=-11, z=1, w=5, h=4, d=4, paint=('color', '#f4f4f4', 'hair')),             # ponytail root
        dict(part='head', x=-3.5, y=-10, z=1.5, w=7, h=1, d=1, paint=('color', '#e8902a', None)),            # orange rods
        dict(part='head', x=-3.5, y=-8.5, z=1.5, w=7, h=1, d=1, paint=('color', '#e8902a', None)),
        dict(name='tail0', part='head', x=-3, y=0, z=0, w=6, h=11, d=3, pivot=(0, -9, 4), rot=(0.2, 0, 0), paint=('color', '#f4f4f4', 'hair')),
        dict(part='tail0', x=-3.5, y=10.5, z=-0.5, w=7, h=9, d=3, rot=(-0.15, 0, 0), paint=('color', '#f4f4f4', 'tips:#3ab8b0')),
        dict(part='tail0', x=-3, y=19, z=0, w=6, h=3, d=2.5, rot=(-0.2, 0, 0), paint=('color', '#3a6ad0', 'hair')),   # blue ends
        dict(part='right_leg', x=-2.6, y=0, z=-2.6, w=5.2, h=11, d=5.2, mirror=True, paint=('sample', 'leg', 0, 11)),   # hakama
    ] + nio_dasuki(),
    # Garp: built like a wall, so the brute body with a Marine coat over his shoulders
    'garp': brute() + cape(MARINE, '#d8d8e0', kanji=True, wide=True),
    'sengoku': brute() + cape(MARINE, '#d8d8e0', kanji=True, wide=True) + [dict(part='head', x=-3, y=-11, z=-1.5, w=6, h=2, d=4, paint=('color', '#f8f8f8', None)),
                                                     dict(part='head', x=-1, y=-10.5, z=-3.5, w=2, h=1, d=2, paint=('color', '#e8b030', None))],
    'akainu': brute() + cape(MARINE, '#d8d8e0', kanji=True, wide=True) + [dict(part='head', x=-4.6, y=-9.4, z=-4.6, w=9, h=2, d=9, paint=('color', '#2a2a4a', None)),
                               dict(part='head', x=-4.6, y=-7.6, z=-7, w=9, h=1, d=3, paint=('color', '#1a1a2a', None))],
    'kizaru': long_legs('kizaru') + marine_cape() + shades('#c08020'),
    'fujitora': marine_cape(), 'ryokugyu': marine_cape() + hair_back('#2a4a2a', 10, 8), 'aokiji': long_legs('aokiji') + marine_cape(),
    'shanks': cape('#1a1a1c', '#5a1a1a') + [
        # the left arm is hidden (HIDDEN), so the cape rests on a shoulder piece on the body instead
        dict(part='body', x=3.5, y=-1.5, z=-2.6, w=5, h=3, d=5, paint=('color', '#1a1a1c', 'cloth')),
    ],
    # Roger: the huge black mustache that curls up at both ends
    'roger': cape('#b02424', '#e8e0c0', trim='#e8c040') + [
        dict(part='head', x=-3.5, y=-3.4, z=-5, w=7, h=1.5, d=1.5, paint=('color', '#141414', 'hair')),
        dict(part='head', x=3.5, y=-4.2, z=-5, w=2, h=1.5, d=1.5, mirror=True, paint=('color', '#141414', 'hair')),
        dict(part='head', x=5.5, y=-6.4, z=-5, w=1.5, h=3, d=1.5, mirror=True, paint=('color', '#141414', 'hair')),
    ],
    'dragon': cape('#2a5a2e', '#1a3a1e', length=24) + [dict(part='head', x=-4.6, y=-6.5, z=3.4, w=9, h=6, d=2, paint=('color', '#2a5a2e', 'cloth'))],
    # Sabo: black top hat with his goggles on the band
    'sabo': cape('#2a46a0', '#1a2a6a', length=18, mantle=False) + top_hat('#1a1a22', band='#3a6ad0', brim=11, crown=8, tall=6) + [
        dict(part='head', x=-3.5, y=-11, z=-4.6, w=3, h=2, d=1, paint=('color', '#80c0f0', None)),
        dict(part='head', x=0.5, y=-11, z=-4.6, w=3, h=2, d=1, paint=('color', '#80c0f0', None)),
    ],
    # Buggy: his big round red clown nose
    'buggy': [dict(part='head', x=-1.5, y=-4.5, z=-6, w=3, h=3, d=2, paint=('color', '#e02020', None))],
    # Law: the fluffy white hat with brown spots
    'law': [dict(part='head', x=-4.8, y=-10.5, z=-4.8, w=10, h=3, d=10, paint=('color', '#f4f2ea', 'spots')),
            dict(part='head', x=-4.6, y=-8, z=-4.6, w=9, h=1, d=9, paint=('color', '#e8e4d8', 'fur'))],
    'rayleigh': cape('#c8c0b0'),
    'hawkins': cape('#4a2a5a', trim='#e8c040'),
    'drake': cape('#3a3a4a', '#2a2a2a'),
    'mihawk': cape('#1e1e22', '#8a1a1a', length=22) + [dict(part='head', x=-7, y=-9.5, z=-7, w=14, h=1, d=14, paint=('color', '#1a1a1a', None)),
               dict(part='head', x=4, y=-13, z=0, w=1, h=4, d=3, rot=(0, 0, 0.3), paint=('color', '#f4f4f4', 'fur'))],
    'luffy': [dict(part='head', x=-6.5, y=-6.5, z=-6.5, w=13, h=1, d=13, paint=('color', '#e8c860', 'straw')),
              dict(part='head', x=-4.5, y=-6.5 - 2, z=-4.5, w=9, h=2, d=9, paint=('color', '#c82020', None)),
              dict(part='head', x=-4.5, y=-6.5 - 4, z=-4.5, w=9, h=2, d=9, paint=('color', '#e8c860', 'straw'))],
    'ace': [dict(part='head', x=-6.5, y=-7, z=-6.5, w=13, h=1, d=13, paint=('color', '#e08030', None)),
            dict(part='head', x=-4.5, y=-11, z=-4.5, w=9, h=4, d=9, paint=('color', '#e08030', 'band'))],
    # Rocks D. Xebec (One Piece Wiki): tall and muscular, unruly blue-and-white spiky hair, a purple lightning tattoo by
    # his left eye, gold earrings, shirtless under a black feathery coat worn on his back, red wrist cuffs, a red
    # fur-trimmed belt, black trousers with a gold chain, black boots, and his saber Eclipse in a light sheath on the right
    'xebec': brute() + cape('#141416', '#26262c', collar='#1c1c20', wide=True, pattern='fur', ragged=True, flare=2)
             + spikes('#eef0f6', n=7, ln=9, tilt=-0.35, fan=0.6) + spikes('#3a64c8', n=6, at_y=-7.5, ln=7, tilt=-0.6, fan=0.9) + hair_back('#eef0f6', 12, 10) + [
        dict(part='head', x=-4.6, y=-8.8, z=-4.6, w=9.2, h=2, d=9.2, paint=('color', '#eef0f6', 'hair')),
        dict(part='head', x=-4.7, y=-3.2, z=-0.6, w=0.6, h=2, d=1.2, mirror=True, paint=('color', '#e8c040', 'metal')),   # earrings
        dict(part='body', x=-6.5, y=8, z=-4, w=13, h=2.5, d=8, paint=('color', '#c02020', 'fur')),                       # red belt
        dict(part='body', x=-6.7, y=7.6, z=-4.2, w=13.4, h=0.8, d=8.4, paint=('color', '#f0ece4', 'fur')),              # its fur trim
        dict(part='right_arm', x=-6, y=8, z=-3, w=6, h=2, d=6, mirror=True, paint=('color', '#c02020', None)),          # wrist cuffs
        dict(part='right_leg', x=2.4, y=1, z=-1, w=0.6, h=4, d=0.6, rot=(0, 0, -0.3), paint=('color', '#e8c040', 'metal')),   # chain
    ] + katana('#2a2a30', '#e8e0c8', at=(-6.6, 8.6, -1.0), spread=-0.12),
    # Kin'emon (One Piece Wiki): black top-knot and goatee, samurai gi split down the middle (black-and-white stripes
    # on his left, orange on his right), two katana with flame-patterned sheaths on his left side, geta
    'kinemon': [
        dict(part='head', x=-1.2, y=-10, z=-3.5, w=2.4, h=2, d=7, paint=('color', '#141414', 'hair')),       # top-knot
        dict(part='head', x=-1.6, y=-10.4, z=1.5, w=3.2, h=2.4, d=1.5, paint=('color', '#f4f0e0', None)),     # its tie
        dict(part='head', x=-4.6, y=-6, z=-1, w=1.2, h=4, d=5, mirror=True, paint=('color', '#141414', 'hair')),   # sideburns
        dict(part='head', x=-4.2, y=-6.5, z=3.4, w=8.4, h=5, d=1.2, paint=('color', '#141414', 'hair')),       # back of the head
        dict(part='head', x=-1, y=-1, z=-4.6, w=2, h=1.5, d=0.8, paint=('color', '#141414', 'hair')),         # goatee
        dict(part='right_leg', x=-2.5, y=0, z=-2.5, w=5, h=10, d=5, mirror=True, paint=('sample', 'leg', 0, 10)),   # hakama
        dict(part='body', x=-4.6, y=7.5, z=-2.6, w=9.2, h=2, d=5.2, paint=('color', '#e8e0c8', 'rope')),       # sash
    ] + katana('#1a1a1a', '#1a1414', at=(4.6, 8.6, -1.0)) + katana('#1a1a1a', '#1a1414', at=(4.9, 9.4, 0.4), tilt=1.3, spread=0.2),
    # Loki (chapter 1198 era): a giant brute, dark fur mantle, wild golden mane, iron cuffs and broken chain links.
    'loki': brute() + cape('#2a2420', '#3a3028', collar='#4a3a2a', wide=True, pattern='fur', ragged=True, flare=2)
            + spikes('#e0b848', n=7, ln=9, tilt=-0.35, fan=0.7) + hair_back('#e0b848', 14, 10) + [
        dict(part='right_arm', x=-6.2, y=8, z=-3.2, w=6.4, h=2.5, d=6.4, mirror=True, paint=('color', '#5a5a62', 'metal')),   # iron cuffs
        dict(part='right_arm', x=-4, y=10.5, z=-0.5, w=1, h=4, d=1, mirror=True, rot=(0.3, 0, 0), paint=('color', '#7a7a84', 'metal')),  # chain
        dict(part='body', x=-6.5, y=8, z=-4, w=13, h=2, d=8, paint=('color', '#5a3a22', 'rope')),                            # belt
    ],
}

# ---------------- UV packing ----------------

def free_areas(tex):
    """Areas not used by the normal 64x64 skin, for a tex x tex texture."""
    return [(64, 0, tex - 64, 64), (0, 64, tex, tex - 64)]


def net_size(b):
    w, h, d = int(round(b['w'])), int(round(b['h'])), int(round(b['d']))
    return 2 * (w + d), h + d


def pack(boxes):
    """Shelf packing into the free areas. Mirrored boxes share one texture. Returns the texture size."""
    order = sorted(range(len(boxes)), key=lambda i: -net_size(boxes[i])[1])
    for tex in (TEX, 256):
        areas = [dict(x=a[0], y=a[1], w=a[2], h=a[3], cx=a[0], cy=a[1], row=0) for a in free_areas(tex)]
        ok = True
        for i in order:
            fw, fh = net_size(boxes[i])
            for a in areas:
                if a['cx'] + fw > a['x'] + a['w']:
                    a['cx'], a['cy'], a['row'] = a['x'], a['cy'] + a['row'], 0
                if a['cy'] + fh <= a['y'] + a['h'] and fw <= a['w']:
                    boxes[i]['u'], boxes[i]['v'] = a['cx'], a['cy']
                    a['cx'] += fw
                    a['row'] = max(a['row'], fh)
                    break
            else:
                ok = False
                break
        if ok:
            return tex
    raise SystemExit('giant texture too full')


# ---------------- painting ----------------

KANJI = ['.##.##.', '#..#..#', '.#####.', '#.#.#.#', '.##.##.', '#.#.#.#']   # "Justice", roughly


def face_cols(part):
    ww = PARTS[part][2]
    fw = len(FRONT[part])
    sw = (ww - 2 * fw) // 2
    return [(0, sw), (sw, fw), (sw + fw, sw), (2 * sw + fw, fw)]


def sample(img, part, face, fx, fy, r0, r1):
    ox, oy, ww, hh, top, bot, tw, th = PARTS[part]
    if face in (4, 5):
        x0, y0 = top if face == 4 else bot
        return img.getpixel((x0 + min(tw - 1, int(fx * tw)), y0 + min(th - 1, int(fy * th))))
    c0, cw = face_cols(part)[face]
    col = c0 + min(cw - 1, int(fx * cw))
    row = r0 + min(r1 - r0 - 1, int(fy * (r1 - r0)))
    return img.getpixel((ox + col, oy + row))


JOLLY = [
    '#......#',
    '.#.##.#.',
    '..####..',
    '..#..#..',
    '..####..',
    '...##...',
    '.#....#.',
    '#......#',
]


def paint_box(img, base, b, rnd):
    u, v = b['u'], b['v']
    w, h, d = int(round(b['w'])), int(round(b['h'])), int(round(b['d']))
    faces = [  # (face id, x0, y0, fw, fh, light)
        (4, u + d, v, w, d, 1.1), (5, u + d + w, v, w, d, 0.7),
        (0, u, v + d, d, h, 0.9), (1, u + d, v + d, w, h, 1.0),
        (2, u + d + w, v + d, d, h, 0.9), (3, u + 2 * d + w, v + d, w, h, 0.85)]
    kind = b['paint'][0]
    for (fid, x0, y0_face, fw, fh, light) in faces:
        for yy in range(fh):
            for xx in range(fw):
                fx, fy = (xx + 0.5) / fw, (yy + 0.5) / fh
                if kind == 'cape':
                    _, outer, lining, trim, pat, y0, total, kanji, ragged = b['paint']
                    gy = y0 + yy if fid in (0, 1, 2, 3) else y0
                    c = hexc(lining) if fid == 1 else hexc(outer)
                    f = (1.0 if fid != 1 else 0.85) * rnd.uniform(0.95, 1.05) * (1.03 - 0.12 * gy / total)
                    if pat == 'fur' and (xx * 3 + yy * 5) % 4 == 0:
                        f *= 1.15
                    elif pat == 'cloth' and fid == 3 and xx % 4 == 1:
                        f *= 0.93          # folds
                    if trim and (fid in (0, 2, 4, 5) or (fid == 3 and xx in (0, fw - 1))
                                 or (y0 + fh >= total and yy == fh - 1)):
                        c, f = hexc(trim), 1.0
                    if kanji and fid == 3:
                        sc = 2 if fw >= 14 else 1
                        gx = (xx - (fw - 7 * sc) // 2) // sc
                        ky = (gy - 3) // sc
                        if 0 <= gx < 7 and 0 <= ky < 6 and KANJI[ky][gx] == '#':
                            c, f = hexc('#1a1a1a'), 1.0
                    if ragged and fid in (0, 1, 2, 3) and yy >= fh - 2 and (xx + yy) % 2 == 0:
                        img.putpixel((x0 + xx, yy + y0_face), (0, 0, 0, 0))
                        continue
                    img.putpixel((x0 + xx, yy + y0_face), shade(c, f))
                    continue
                if kind == 'sample':
                    _, part, r0, r1 = b['paint']
                    c = sample(base, part, fid, fx, fy, r0, r1)
                    if c[3] == 0:
                        c = sample(base, part, 1, fx, fy, r0, r1)
                    f = 1.0
                else:
                    _, col, pat = b['paint']
                    c = hexc(col)
                    f = light * rnd.uniform(0.94, 1.06)
                    if pat == 'hair' and (xx + yy * 2) % 5 == 0:
                        f *= 0.82
                    elif pat == 'fur' and (xx * 3 + yy * 5) % 4 == 0:
                        f *= 1.15
                    elif pat == 'curls' and ((xx // 2) + (yy // 2)) % 2 == 0:
                        f *= 0.86
                    elif pat == 'polka' and yy % 5 in (1, 2) and (xx + 3 * ((yy // 5) % 2)) % 6 in (1, 2):
                        c = hexc('#d8344e')              # Big Mom's red polka dots
                    elif pat == 'jolly' and fid == 1 and 0 <= xx - (fw - 8) // 2 < 8 and JOLLY[yy * 8 // fh][xx - (fw - 8) // 2] == '#':
                        c, f = hexc('#f6f4ee'), 1.0      # skull and crossbones on Big Mom's hat
                    elif pat == 'dots' and (xx + yy) % 3 == 0:
                        c = hexc('#c8c8d0')
                    elif pat == 'straw' and (xx + 2 * yy) % 3 == 0:
                        f *= 0.85
                    elif pat == 'band' and fid in (0, 1, 2, 3) and yy == fh - 1:
                        c = hexc('#c02a2a')
                    elif pat == 'xcross' and fid == 1 and (xx * (fh - 1) == yy * (fw - 1) or (fw - 1 - xx) * (fh - 1) == yy * (fw - 1)):
                        c, f = hexc('#f8f8f8'), 1.0      # Chopper's white X
                    elif pat == 'spots' and (xx * 7 + yy * 3 + fid) % 9 == 0:
                        c = hexc('#6a4a2a')              # Law's hat spots
                    elif pat == 'metal':
                        f *= 1.2 if (xx + yy) % 4 == 0 else (0.8 if (xx * 2 + yy) % 5 == 0 else 1.0)
                    elif pat == 'drum' and fid in (4, 5):
                        c = hexc('#f0e8d0')              # drum skins on the ends
                    elif pat == 'pigeon' and fid == 1 and xx == fw // 2 and yy >= 1:
                        c = hexc('#d02020')              # Hattori's tie
                    elif pat == 'nose' and fid in (0, 1, 2, 3):
                        f *= 1.05 - 0.1 * (fx if fid in (0, 2) else 0.5)
                    elif pat and pat.startswith('shades:') and fid == 1 and 0 < yy and (1 <= xx <= 3 or 5 <= xx <= 7):
                        c, f = hexc(pat[7:]), 1.0
                    elif pat and pat.startswith('tips:') and ((fid in (0, 1, 2, 3) and fy > 0.72) or fid == 5):
                        c = hexc(pat[5:])                # hair ends in another colour (Yamato's green tips)
                    elif pat and pat.startswith('twist:') and (xx + yy) % 4 < 2:
                        c = hexc(pat[6:])                # two-colour twisted rope (nio-dasuki)
                    elif pat == 'feather' and fid in (0, 1, 2, 3, 5):
                        f *= 1.3 if yy % 4 == 3 else (0.85 if (xx + yy // 4) % 3 == 0 else 1.0)   # rows of black feathers
                    elif pat == 'rope' and (xx + yy) % 3 == 0:
                        f *= 0.8                         # twisted rope
                    elif pat == 'flame':
                        c = mix(hexc('#ffe060'), hexc('#ff4a10'), min(1.0, max(0.0, 1.0 - fy if fid in (0, 1, 2, 3) else 0.6)))
                        f = 1.15 if (xx * 5 + yy * 3) % 7 == 0 else 1.0
                    elif pat == 'leather' and fid in (0, 1, 2, 3) and (yy % 4 == 0 or xx % 5 == 2):
                        f *= 1.18                        # seams and creases
                    elif pat == 'wing' and fid in (2, 3, 1, 0) and (xx + yy) % 6 == 0:
                        f *= 1.35                        # the bones in a wing membrane
                    elif pat == 'scabbard' and fid in (0, 1, 2, 3) and yy % 3 == 0:
                        c = hexc('#c8a040')              # cord wrapping on a sword handle
                    elif pat == 'cloth' and fid in (0, 1, 2, 3):
                        f *= 1.05 - 0.15 * fy
                    if fid in (0, 1, 2, 3) and fh > 3:
                        f *= 1.04 - 0.1 * fy
                img.putpixel((x0 + xx, y0_face + yy), shade(c, f))


def paint_giant(cid, img):
    """img: the finished 64x64 skin. Returns the bigger giant skin (128 or 256 square)."""
    boxes = GIANTS[cid]
    tex = pack(boxes)
    big = Image.new('RGBA', (tex, tex), (0, 0, 0, 0))
    big.paste(img, (0, 0))
    rnd = random.Random(cid)
    for b in boxes:
        paint_box(big, img, b, rnd)
    return big


# ---------------- Java model ----------------

PART_NAMES = {'head': 'head', 'body': 'body', 'right_arm': 'right_arm', 'right_leg': 'right_leg'}
MIRROR_PART = {'right_arm': 'left_arm', 'right_leg': 'left_leg', 'head': 'head', 'body': 'body',
               'cape0': 'cape0', 'cape1': 'cape1', 'cape2': 'cape2'}


def f(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return (s if s not in ('-0', '') else '0') + 'F'


def java_boxes(cid):
    lines = []
    for i, b in enumerate(GIANTS[cid]):
        copies = [(b['part'], False)]
        if b.get('mirror'):
            copies.append((MIRROR_PART[b['part']], True))
        for (part, mir) in copies:
            px, py, pz = b.get('pivot', (0, 0, 0))
            rx, ry, rz = b.get('rot', (0, 0, 0))
            x, w = b['x'], b['w']
            if mir:
                # same box on the other side: flip across x
                x = -(b['x'] + b['w'])
                px = -px
                ry, rz = -ry, -rz
            cube = 'CubeListBuilder.create().texOffs(%d, %d)%s.addBox(%s, %s, %s, %s, %s, %s)' % (
                b['u'], b['v'], '.mirror()' if mir else '', f(x), f(b['y']), f(b['z']),
                f(round(b['w'])), f(round(b['h'])), f(round(b['d'])))
            var = part.replace('right_arm', 'rightArm').replace('left_arm', 'leftArm').replace('right_leg', 'rightLeg').replace('left_leg', 'leftLeg')
            if part == 'left_arm' and not mir:
                x, w = b['x'], b['w']    # a box only on the left limb: given in that limb's own space
            pose = 'PartPose.offsetAndRotation(%s, %s, %s, %s, %s, %s)' % (f(px), f(py), f(pz), f(rx), f(ry), f(rz))
            if b.get('name') and not mir:
                lines.append('\t\tPartDefinition %s = %s.addOrReplaceChild("%s", %s,\n\t\t\t\t%s);' % (b['name'], var, b['name'], cube, pose))
            else:
                lines.append('\t\t%s.addOrReplaceChild("giant%d%s", %s,\n\t\t\t\t%s);' % (var, i, 'm' if mir else '', cube, pose))
    return lines


def write_java(src):
    out = os.path.join(src, 'src/client/java/com/onepiecemod/character/client/GiantModels.java')
    ids = sorted(GIANTS)
    sizes = '\n'.join('\t\t\tcase "%s" -> %d;' % (c, pack(GIANTS[c])) for c in ids if pack(GIANTS[c]) != TEX)
    cases = '\n'.join('\t\t\tcase "%s" -> %s(mesh);' % (c, camel(c)) for c in ids)
    hidden = '\n'.join('\t\t\tcase "%s" -> Set.of(%s);' % (c, ', '.join('"%s"' % p for p in HIDDEN[c])) for c in ids if c in HIDDEN)
    methods = []
    for c in ids:
        methods.append('\tprivate static void %s(MeshDefinition mesh) {\n%s\n%s\n\t}' % (
            camel(c), PARTS_DECL, '\n'.join(java_boxes(c))))
    stripped = '\n'.join('\t\t\tcase "%s" -> Set.of(%s);' % (c, ', '.join('"%s"' % p for p in STRIP[c])) for c in ids if c in STRIP)
    legs = '\n'.join('\t\t\tcase "%s" -> %s;' % (c, f(LEGS[c])) for c in ids if c in LEGS)
    arms_out = '\n'.join('\t\t\tcase "%s" -> %s;' % (c, f(ARMS_OUT[c])) for c in ids if c in ARMS_OUT)
    swing = '\n'.join('\t\t\tcase "%s" -> %s;' % (c, f(SWING[c])) for c in ids if c in SWING)
    java = JAVA % dict(ids=', '.join('"%s"' % c for c in ids), cases=cases, sizes=sizes, hidden=hidden,
                       stripped=stripped, swing=swing, legs=legs, arms_out=arms_out,
                       methods='\n\n'.join(methods))
    with open(out, 'w') as fh:
        fh.write(java)


def camel(s):
    p = s.split('_')
    return p[0] + ''.join(x.title() for x in p[1:])


PARTS_DECL = '''\t\tPartDefinition root = mesh.getRoot();
\t\tPartDefinition head = root.getChild("head");
\t\tPartDefinition body = root.getChild("body");
\t\tPartDefinition rightArm = root.getChild("right_arm");
\t\tPartDefinition leftArm = root.getChild("left_arm");
\t\tPartDefinition rightLeg = root.getChild("right_leg");
\t\tPartDefinition leftLeg = root.getChild("left_leg");'''

JAVA = '''package com.onepiecemod.character.client;

import java.util.Set;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Bigger, bulkier models for the giant characters (Whitebeard, Kaido, Big Mom...): the normal player shape
 * plus extra boxes for muscles, bellies, capes, horns, beards and hair. Their skins are 128x128.
 * GENERATED by tools/skins/gen_skins.py (shapes in tools/skins/giants.py), which also paints the matching
 * skins, so change the shapes there and run it again instead of editing this file.
 */
public final class GiantModels {
	public static final Set<String> IDS = Set.of(%(ids)s);

	private GiantModels() {
	}

	public static ModelLayerLocation layer(String id) {
		return new ModelLayerLocation(OnePieceMod.id("character_" + id), "main");
	}

	/** Registers one model layer per giant. CharacterClient calls this. */
	public static void register() {
		for (String id : IDS) {
			ModelLayerRegistry.registerModelLayer(layer(id), () -> create(id));
		}
	}

	public static LayerDefinition create(String id) {
		MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
		switch (id) {
%(cases)s
			default -> {
			}
		}
		return LayerDefinition.create(mesh, size(id), size(id));
	}

	/** Texture size of each giant's skin. */
	private static int size(String id) {
		return switch (id) {
%(sizes)s
			default -> 128;
		};
	}

	/** Parts whose normal box is not drawn (their extra boxes are): a reshaped body, e.g. Brook's thin limbs. */
	public static Set<String> stripped(String id) {
		return switch (id) {
%(stripped)s
			default -> Set.of();
		};
	}

	/** How far the arms and legs swing (1 = normal). Short limbs hanging far below the joint swing less. */
	public static float swing(String id) {
		return switch (id) {
%(swing)s
			default -> 1.0F;
		};
	}

	/** Extra leg length in px (long-legged characters): GiantModel raises everything above the hips this much. */
	public static float legs(String id) {
		return switch (id) {
%(legs)s
			default -> 0.0F;
		};
	}

	/** How many px further out the shoulders sit (very wide bodies), so the arms and held items clear the body. */
	public static float armsOut(String id) {
		return switch (id) {
%(arms_out)s
			default -> 0.0F;
		};
	}

	/** Body parts this character does not have (Shanks has no left arm). GiantModel keeps them hidden. */
	public static Set<String> hidden(String id) {
		return switch (id) {
%(hidden)s
			default -> Set.of();
		};
	}

%(methods)s
}
'''
