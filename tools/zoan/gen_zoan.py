"""Generates the full-body Zoan forms: models, textures and keyframe animations.

Run:  python3 -I gen_zoan.py <path to source/>
Writes src/client/java/com/onepiecemod/zoan/client/ZoanModels.java and
src/main/resources/assets/onepiece/textures/entity/zoan/<form>.png. Edit shapes and animations here,
not in ZoanModels.java. Box/part/texture helpers are shared with tools/creatures/gen_creatures.py.

Model space: 16 px = 1 block, y points down, y = 24 is the ground, the front is -z, right is -x.
Animations use Minecraft's own keyframe system (the one the Warden and Camel use): every value is
ADDED to the part's resting pose. Rotations in degrees, positions in pixels.
Animation names the renderer looks for: idle, walk, fly (optional), attack, roar.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'creatures'))
from gen_creatures import box, part, pack, paint, write_png, java_layer, camel  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
OUT_JAVA = os.path.join(SRC, 'src/client/java/com/onepiecemod/zoan/client/ZoanModels.java')
OUT_TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/zoan')

F = {}   # form -> parts
A = {}   # form -> {anim: (length, looping, {bone: {'rot': [(t, (x, y, z))], 'pos': [...]}})}

# ---------------- Lucci: leopard hybrid ----------------
Y, Y2, NOSE, PANTS = '#e0b040', '#f3dca0', '#2a1a10', '#1c1c1c'
F['leopard'] = [
    part('body', (0, 10, 0), [box(-6, -14, -3.5, 12, 14, 7, Y, pattern='spots'),
                              box(-4, -12, -4.5, 8, 10, 1, Y2)]),
    part('head', (0, -14, 0), [box(-4, -8, -4.5, 8, 8, 8, Y, eyes='#2a8a2a', pattern='spots'),
                               box(-2.5, -4, -7.5, 5, 4, 3, Y2, front=[(2, 0, NOSE), (1, 3, NOSE), (3, 3, NOSE)]),
                               box(-4, -10, -2, 2, 2, 1, Y), box(2, -10, -2, 2, 2, 1, Y)], parent='body'),
    part('arm0', (-7, -12, 0), [box(-3, -2, -2.5, 4, 15, 5, Y, pattern='spots'),
                                box(-3, 13, -2.5, 4, 2, 5, Y2, front=[(0, 1, '#ffffff'), (2, 1, '#ffffff')])], parent='body'),
    part('arm1', (7, -12, 0), [box(-1, -2, -2.5, 4, 15, 5, Y, pattern='spots'),
                               box(-1, 13, -2.5, 4, 2, 5, Y2, front=[(1, 1, '#ffffff'), (3, 1, '#ffffff')])], parent='body'),
    part('leg0', (-3, 10, 0), [box(-2.5, 0, -2.5, 5, 10, 5, PANTS), box(-2.5, 10, -3.5, 5, 4, 6, Y, pattern='spots')]),
    part('leg1', (3, 10, 0), [box(-2.5, 0, -2.5, 5, 10, 5, PANTS), box(-2.5, 10, -3.5, 5, 4, 6, Y, pattern='spots')]),
    part('tail0', (0, -2, 3.5), [box(-1, -1, 0, 2, 2, 7, Y, pattern='stripes')], rot=(-0.5, 0, 0), parent='body'),
    part('tail1', (0, 0, 7), [box(-1, -1, 0, 2, 2, 7, Y, pattern='stripes')], rot=(0.3, 0, 0), parent='tail0'),
]

# ---------------- Chopper: Heavy Point ----------------
FUR, FUR2, HOOF, HAT, SHORTS, ANT = '#8a5a3c', '#e8d8c0', '#3a2a20', '#f0a0b0', '#3060c0', '#c8a070'
hat_x = [(2, 0, '#ffffff'), (6, 0, '#ffffff'), (3, 1, '#ffffff'), (5, 1, '#ffffff'), (4, 2, '#ffffff'),
         (3, 3, '#ffffff'), (5, 3, '#ffffff')]
F['heavy_point'] = [
    part('body', (0, 9, 0), [box(-7, -15, -4, 14, 15, 8, FUR, pattern='fluff'),
                             box(-5, -14, -4.6, 10, 7, 1, FUR2)]),
    part('head', (0, -15, 0), [box(-3.5, -7, -4, 7, 7, 7, FUR, eyes='#111111'),
                               box(-2, -3, -6.5, 4, 3, 3, '#c09070', front=[(1, 0, '#3070e0'), (2, 0, '#3070e0')]),
                               box(-4.5, -12, -4.5, 9, 5, 9, HAT, front=hat_x),
                               box(-5.5, -8, -5.5, 11, 1, 11, HAT),
                               box(-11, -14, -1, 6, 2, 2, ANT), box(-11, -18, -1, 2, 4, 2, ANT), box(-8, -17, -1, 2, 3, 2, ANT),
                               box(5, -14, -1, 6, 2, 2, ANT), box(9, -18, -1, 2, 4, 2, ANT), box(6, -17, -1, 2, 3, 2, ANT)],
         parent='body'),
    part('arm0', (-8, -13, 0), [box(-4, -2, -3, 5, 16, 6, FUR, pattern='fluff'), box(-4, 14, -3, 5, 3, 6, HOOF)], parent='body'),
    part('arm1', (8, -13, 0), [box(-1, -2, -3, 5, 16, 6, FUR, pattern='fluff'), box(-1, 14, -3, 5, 3, 6, HOOF)], parent='body'),
    part('leg0', (-3.5, 9, 0), [box(-3, 0, -3, 6, 7, 6, SHORTS), box(-2.5, 7, -2.5, 5, 6, 5, FUR, pattern='fluff'),
                                box(-2.5, 13, -3, 5, 2, 6, HOOF)]),
    part('leg1', (3.5, 9, 0), [box(-3, 0, -3, 6, 7, 6, SHORTS), box(-2.5, 7, -2.5, 5, 6, 5, FUR, pattern='fluff'),
                               box(-2.5, 13, -3, 5, 2, 6, HOOF)]),
]

# ---------------- Marco: blue phoenix ----------------
B1, B2, GOLD = '#30a0f0', '#7ad8ff', '#f8d040'
F['phoenix'] = [
    part('body', (0, 12, 0), [box(-4, -4, -7, 8, 8, 14, B1, pattern='fluff'), box(-3, -2, -8, 6, 6, 2, B2)]),
    part('head', (0, -2, -7), [box(-3, -6, -5, 6, 6, 6, B1, eyes=GOLD, pattern='fluff'),
                               box(-1, -3, -9, 2, 2, 4, GOLD),
                               box(-0.5, -10, -2, 1, 4, 6, GOLD), box(-0.5, -12, 1, 1, 3, 4, B2)], parent='body'),
    part('wing0', (-4, -3, -3), [box(-12, -0.5, 0, 12, 1, 10, B1, pattern='stripes')], parent='body'),
    part('wingtip0', (-12, 0, 0), [box(-12, -0.5, 0, 12, 1, 9, B2, pattern='stripes'), box(-12, -0.5, 9, 12, 1, 3, GOLD)],
         parent='wing0'),
    part('wing1', (4, -3, -3), [box(0, -0.5, 0, 12, 1, 10, B1, pattern='stripes')], parent='body'),
    part('wingtip1', (12, 0, 0), [box(0, -0.5, 0, 12, 1, 9, B2, pattern='stripes'), box(0, -0.5, 9, 12, 1, 3, GOLD)],
         parent='wing1'),
    part('tail', (0, -2, 7), [box(-3, -0.5, 0, 6, 1, 14, GOLD, pattern='stripes'), box(-1, 0, 0, 2, 1, 18, B2)],
         rot=(0.15, 0, 0), parent='body'),
    part('leg0', (-2, 16, 0), [box(-0.5, 0, -0.5, 1, 6, 1, GOLD), box(-1.5, 6, -2, 3, 2, 3, GOLD)]),
    part('leg1', (2, 16, 0), [box(-0.5, 0, -0.5, 1, 6, 1, GOLD), box(-1.5, 6, -2, 3, 2, 3, GOLD)]),
]

# ---------------- Kaido: Seiryu, the azure dragon ----------------
D1, BELLY, MANE, HORN = '#2a70c0', '#e8e0c0', '#60d0e0', '#f0e8d0'
SEG = [8, 8, 8, 7, 7, 6, 6, 5, 4, 3]
F['seiryu'] = [
    part('head', (0, 8, 0), [box(-4, -4, -10, 8, 7, 10, D1, eyes='#ffd000', pattern='scales'),
                             box(-3, -2, -16, 6, 4, 6, D1, pattern='scales'),
                             box(-4, -9, -3, 1, 6, 1, HORN), box(3, -9, -3, 1, 6, 1, HORN),
                             box(-5, -5, -1, 10, 9, 4, MANE, pattern='fluff'),
                             box(-9, -1, -15, 5, 1, 1, HORN), box(4, -1, -15, 5, 1, 1, HORN)]),
    part('jaw', (0, 2, -6), [box(-3, 0, -10, 6, 2, 10, D1, pattern='scales'),
                             box(-2.5, -0.5, -9.5, 5, 1, 1, '#ffffff'), box(-2.5, -0.5, -9.5, 1, 1, 8, '#ffffff'),
                             box(1.5, -0.5, -9.5, 1, 1, 8, '#ffffff')], parent='head'),
]
prev = 'root'
for i, s in enumerate(SEG):
    h = s / 2
    boxes = [box(-h, -h, 0, s, s, 8, D1, pattern='scales'), box(-h + 1, h, 0, s - 2, 1, 8, BELLY)]
    if s >= 5:
        boxes.append(box(-0.5, -h - 3, 1, 1, 3, 6, MANE))
    if i == len(SEG) - 1:
        boxes.append(box(-3, -4, 8, 6, 8, 6, MANE, pattern='fluff'))
    F['seiryu'].append(part('seg%d' % i, (0, 8, 0) if i == 0 else (0, 0, 8), boxes, parent=None if i == 0 else 'seg%d' % (i - 1)))
for seg, n in (('seg1', 0), ('seg6', 2)):
    s = SEG[int(seg[3:])]
    F['seiryu'].append(part('dleg%d' % n, (-s / 2, 2, 4), [box(-2, 0, -1, 2, 5, 2, D1), box(-3, 5, -2, 3, 1, 3, HORN)], parent=seg))
    F['seiryu'].append(part('dleg%d' % (n + 1), (s / 2, 2, 4), [box(0, 0, -1, 2, 5, 2, D1), box(0, 5, -2, 3, 1, 3, HORN)], parent=seg))


# ---------------- animations ----------------

def wave(length, amp, phase=0.0, n=8, offset=0.0):
    """Keyframes for offset + amp * sin(2pi t / length + phase), looping cleanly."""
    return [(length * k / n, offset + amp * math.sin(2 * math.pi * k / n + phase)) for k in range(n + 1)]


def rot(anim, bone, axis, keys):
    ch = anim.setdefault(bone, {}).setdefault('rot', {})
    ch[axis] = keys


def pos(anim, bone, axis, keys):
    ch = anim.setdefault(bone, {}).setdefault('pos', {})
    ch[axis] = keys


def pulse(points):
    """One-shot keyframes from (t, value) pairs."""
    return list(points)


def biped(form, heavy):
    idle, walk, attack, roar = {}, {}, {}, {}
    pos(idle, 'body', 1, wave(2.0, 0.6))
    rot(idle, 'arm0', 2, wave(2.0, 3))
    rot(idle, 'arm1', 2, wave(2.0, -3))
    rot(idle, 'head', 0, wave(2.0, 2, math.pi / 2))
    rot(walk, 'leg0', 0, wave(1.0, 38))
    rot(walk, 'leg1', 0, wave(1.0, -38))
    rot(walk, 'arm0', 0, wave(1.0, -30))
    rot(walk, 'arm1', 0, wave(1.0, 30))
    rot(walk, 'body', 1, wave(1.0, 6))
    pos(walk, 'body', 1, wave(0.5, -0.8, n=6))
    if not heavy:
        rot(idle, 'tail0', 1, wave(2.0, 18))
        rot(idle, 'tail1', 1, wave(2.0, 25, -1.0))
        rot(walk, 'tail0', 1, wave(1.0, 20))
        rot(walk, 'tail1', 1, wave(1.0, 30, -1.2))
        # Leopard claw swipe: right arm rakes down across the body, body twists into it.
        rot(attack, 'arm0', 0, pulse([(0, 0), (0.12, -150), (0.3, -40), (0.5, 0)]))
        rot(attack, 'arm0', 2, pulse([(0, 0), (0.12, -30), (0.3, 25), (0.5, 0)]))
        rot(attack, 'body', 1, pulse([(0, 0), (0.12, 25), (0.3, -20), (0.5, 0)]))
        rot(attack, 'arm1', 0, pulse([(0, 0), (0.2, -60), (0.5, 0)]))
    else:
        # Heavy Point: a one-two of huge hooves.
        rot(attack, 'arm0', 0, pulse([(0, 0), (0.1, -95), (0.22, -20), (0.5, 0)]))
        rot(attack, 'arm1', 0, pulse([(0, 0), (0.2, -10), (0.32, -95), (0.5, 0)]))
        rot(attack, 'body', 1, pulse([(0, 0), (0.1, 20), (0.32, -20), (0.5, 0)]))
    # Roar when the form starts: head thrown back, arms spread wide, chest out.
    rot(roar, 'head', 0, pulse([(0, 0), (0.3, -35), (0.9, -35), (1.2, 0)]))
    rot(roar, 'arm0', 2, pulse([(0, 0), (0.3, 55), (0.9, 55), (1.2, 0)]))
    rot(roar, 'arm1', 2, pulse([(0, 0), (0.3, -55), (0.9, -55), (1.2, 0)]))
    rot(roar, 'body', 0, pulse([(0, 0), (0.3, -12), (0.9, -12), (1.2, 0)]))
    A[form] = {'idle': (2.0, True, idle), 'walk': (1.0, True, walk), 'attack': (0.5, False, attack), 'roar': (1.2, False, roar)}


biped('leopard', False)
biped('heavy_point', True)

# Phoenix
idle, walk, fly, attack, roar = {}, {}, {}, {}, {}
# On the ground the wings fold back along the body (turned about y), drooping a little, tips tucked under.
rot(idle, 'wing0', 1, wave(2.0, 0, offset=80))
rot(idle, 'wing1', 1, wave(2.0, 0, offset=-80))
rot(idle, 'wing0', 2, wave(2.0, 3, offset=-25))
rot(idle, 'wing1', 2, wave(2.0, -3, offset=25))
rot(idle, 'wingtip0', 1, wave(2.0, 0, offset=-160))
rot(idle, 'wingtip1', 1, wave(2.0, 0, offset=160))
rot(idle, 'tail', 1, wave(2.0, 8))
rot(idle, 'head', 0, wave(2.0, 4, 1.0))
rot(walk, 'leg0', 0, wave(0.6, 30))
rot(walk, 'leg1', 0, wave(0.6, -30))
pos(walk, 'body', 1, wave(0.3, -0.7, n=6))
rot(fly, 'wing0', 2, wave(0.8, 50))
rot(fly, 'wing1', 2, wave(0.8, -50))
rot(fly, 'wingtip0', 2, wave(0.8, 30, -0.9))
rot(fly, 'wingtip1', 2, wave(0.8, -30, -0.9))
pos(fly, 'body', 1, wave(0.8, 1.2, math.pi))
rot(fly, 'tail', 0, wave(0.8, 6, 0.5))
rot(fly, 'leg0', 0, wave(0.8, 0, offset=60))
rot(fly, 'leg1', 0, wave(0.8, 0, offset=60))
rot(attack, 'wing0', 1, pulse([(0, 0), (0.15, 45), (0.35, -20), (0.5, 0)]))
rot(attack, 'wing1', 1, pulse([(0, 0), (0.15, -45), (0.35, 20), (0.5, 0)]))
rot(attack, 'body', 0, pulse([(0, 0), (0.15, -15), (0.35, 15), (0.5, 0)]))
rot(attack, 'head', 0, pulse([(0, 0), (0.2, 25), (0.5, 0)]))
rot(roar, 'wing0', 2, pulse([(0, 0), (0.3, -45), (0.6, -30), (0.9, -45), (1.2, 0)]))
rot(roar, 'wing1', 2, pulse([(0, 0), (0.3, 45), (0.6, 30), (0.9, 45), (1.2, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.3, -40), (0.9, -40), (1.2, 0)]))
A['phoenix'] = {'idle': (2.0, True, idle), 'walk': (0.6, True, walk), 'fly': (0.8, True, fly),
                'attack': (0.5, False, attack), 'roar': (1.2, False, roar)}

# Seiryu: a ripple travels from the head down the body, so the dragon "swims" through the air.
idle, walk, attack, roar = {}, {}, {}, {}
for i in range(len(SEG)):
    rot(idle, 'seg%d' % i, 1, wave(3.0, 9 + i * 0.6, -0.7 * i))
    rot(idle, 'seg%d' % i, 0, wave(3.0, 4, -0.7 * i + 1.3))
    rot(walk, 'seg%d' % i, 1, wave(1.2, 6 + i * 0.4, -0.8 * i))
rot(idle, 'head', 1, wave(3.0, -8, 0.6))
rot(idle, 'jaw', 0, wave(3.0, 3, offset=4))
for n in range(4):
    rot(idle, 'dleg%d' % n, 0, wave(1.5, 25, n * 1.6))
rot(attack, 'jaw', 0, pulse([(0, 0), (0.15, 40), (0.45, 40), (0.6, 0)]))
rot(attack, 'head', 0, pulse([(0, 0), (0.15, -20), (0.3, 10), (0.6, 0)]))
pos(attack, 'head', 2, pulse([(0, 0), (0.3, -4), (0.6, 0)]))
rot(roar, 'jaw', 0, pulse([(0, 0), (0.3, 50), (1.0, 50), (1.4, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.3, -35), (1.0, -35), (1.4, 0)]))
for i in range(4):
    rot(roar, 'seg%d' % i, 0, pulse([(0, 0), (0.3 + i * 0.1, -8 + i * 3), (1.4, 0)]))
A['seiryu'] = {'idle': (3.0, True, idle), 'walk': (1.2, True, walk), 'attack': (0.6, False, attack), 'roar': (1.4, False, roar)}


# ---------------- Luffy: Wild Nika (the feral, ape-like form from chapter 1198 leaks) ----------------
# Hunched and long-armed like an ape: wild black hair, fangs, a tail, open red vest, blue shorts, straw hat.
LS, LS2, LHAIR, VEST, SHORTS2, STRAW, BAND, FANG = '#e8b890', '#c8946a', '#1a1a1e', '#d0302a', '#3a5ab0', '#e8c868', '#c02020', '#ffffff'
F['nika_wild'] = [
    part('body', (0, 11, 0), [box(-5, -13, -3, 10, 13, 6, LS, pattern='speckle'),
                              box(-5.5, -13.5, -3.5, 3, 12, 7, VEST), box(2.5, -13.5, -3.5, 3, 12, 7, VEST),
                              box(-4, -15, -3, 8, 3, 6, LHAIR, pattern='fluff')],
         rot=(0.35, 0, 0)),
    part('head', (0, -13, -1), [box(-4, -8, -4.5, 8, 8, 8, LS, eyes='#1a1a1a'),
                                box(-2, -4, -6, 4, 3, 2, LS2, front=[(1, 0, '#2a1a1a'), (2, 0, '#2a1a1a')]),
                                box(-3, -1, -5, 6, 1, 1, FANG, front=[(1, 0, '#3a1010'), (4, 0, '#3a1010')]),
                                box(-5, -10, -3, 10, 4, 9, LHAIR, pattern='fluff'),
                                box(-5.5, -7, 2, 11, 6, 3, LHAIR, pattern='fluff'),
                                box(-6, -9, -5, 12, 1, 12, STRAW, pattern='stripes'),
                                box(-4, -11, -3.5, 8, 2, 8, BAND),
                                box(-4, -13, -3.5, 8, 2, 8, STRAW, pattern='stripes')], rot=(-0.35, 0, 0), parent='body'),
    # Long ape arms that nearly reach the ground.
    part('arm0', (-6.5, -11, 0), [box(-3, -2, -2.5, 4, 18, 5, LS, pattern='speckle'),
                                  box(-3.5, 15, -3, 5, 4, 6, LS2, front=[(0, 2, FANG), (2, 2, FANG), (4, 2, FANG)])],
         rot=(-0.35, 0, 0), parent='body'),
    part('arm1', (6.5, -11, 0), [box(-1, -2, -2.5, 4, 18, 5, LS, pattern='speckle'),
                                 box(-1.5, 15, -3, 5, 4, 6, LS2, front=[(0, 2, FANG), (2, 2, FANG), (4, 2, FANG)])],
         rot=(-0.35, 0, 0), parent='body'),
    part('leg0', (-2.5, 11, 1), [box(-2.5, 0, -2.5, 5, 6, 5, SHORTS2), box(-2, 6, -2, 4, 5, 4, LS), box(-2.5, 11, -3.5, 5, 2, 6, LS2)]),
    part('leg1', (2.5, 11, 1), [box(-2.5, 0, -2.5, 5, 6, 5, SHORTS2), box(-2, 6, -2, 4, 5, 4, LS), box(-2.5, 11, -3.5, 5, 2, 6, LS2)]),
    part('tail0', (0, -1, 3), [box(-1, -1, 0, 2, 2, 7, LHAIR, pattern='fluff')], rot=(-0.9, 0, 0), parent='body'),
    part('tail1', (0, 0, 7), [box(-1, -1, 0, 2, 2, 7, LHAIR, pattern='fluff'), box(-1.5, -1.5, 6, 3, 3, 3, LHAIR, pattern='fluff')],
         rot=(0.6, 0, 0), parent='tail0'),
]
biped('nika_wild', False)
# A wild ape: bounces on its knuckles, and the attack is a two-handed overhead smash.
ni = A['nika_wild']
pos(ni['idle'][2], 'body', 1, wave(1.0, 0.9))
rot(ni['idle'][2], 'arm0', 0, wave(1.0, 6))
rot(ni['idle'][2], 'arm1', 0, wave(1.0, 6))
rot(ni['walk'][2], 'arm0', 0, wave(0.6, -45))
rot(ni['walk'][2], 'arm1', 0, wave(0.6, 45))
ni['attack'] = (0.5, False, {})
rot(ni['attack'][2], 'arm0', 0, pulse([(0, 0), (0.15, -170), (0.3, -10), (0.5, 0)]))
rot(ni['attack'][2], 'arm1', 0, pulse([(0, 0), (0.15, -170), (0.3, -10), (0.5, 0)]))
rot(ni['attack'][2], 'body', 0, pulse([(0, 0), (0.15, -20), (0.3, 25), (0.5, 0)]))

# ---------------- Loki: Ryu Ryu no Mi, Model: Nidhogg (hybrid, chapter 1198) ----------------
# A dragon-man: horned dragon head, scaled body, bat wings and a long tail. Colours are our guess until the
# official colour pages: dark green-black scales, gold horns, lightning-yellow eyes.
N1, N2, NBELLY, NHORN, NEYE, NWING = '#1e3a34', '#2e5a4e', '#8a9a70', '#d8b040', '#ffe040', '#14262a'
F['nidhogg'] = [
    part('body', (0, 10, 0), [box(-6, -15, -3.5, 12, 15, 7, N1, pattern='scales'),
                              box(-4, -13, -4.5, 8, 11, 1, NBELLY, pattern='stripes'),
                              box(-7, -16, -3, 14, 3, 6, N2, pattern='scales')]),
    part('head', (0, -15, 0), [box(-4, -7, -5, 8, 7, 8, N1, eyes=NEYE, pattern='scales'),
                               box(-3, -4, -10, 6, 4, 5, N2, pattern='scales', front=[(1, 0, '#101010'), (4, 0, '#101010')]),
                               box(-2.5, -1, -9.5, 5, 1, 4, '#f0f0e8'),
                               box(-5, -12, -1, 2, 6, 2, NHORN), box(3, -12, -1, 2, 6, 2, NHORN),
                               box(-6, -14, 1, 2, 3, 2, NHORN), box(4, -14, 1, 2, 3, 2, NHORN),
                               box(-1, -9, -2, 2, 2, 7, N2)], parent='body'),
    part('arm0', (-7, -13, 0), [box(-3, -2, -2.5, 4, 15, 5, N1, pattern='scales'),
                                box(-3.5, 12, -3, 5, 3, 6, N2, front=[(0, 2, NHORN), (2, 2, NHORN), (4, 2, NHORN)])], parent='body'),
    part('arm1', (7, -13, 0), [box(-1, -2, -2.5, 4, 15, 5, N1, pattern='scales'),
                               box(-1.5, 12, -3, 5, 3, 6, N2, front=[(0, 2, NHORN), (2, 2, NHORN), (4, 2, NHORN)])], parent='body'),
    part('wing0', (-3, -13, 3.5), [box(-16, -1, 0, 16, 14, 1, NWING, pattern='stripes'), box(-17, -2, -0.5, 2, 2, 2, NHORN)],
         rot=(0, 0.5, 0.2), parent='body'),
    part('wing1', (3, -13, 3.5), [box(0, -1, 0, 16, 14, 1, NWING, pattern='stripes'), box(15, -2, -0.5, 2, 2, 2, NHORN)],
         rot=(0, -0.5, -0.2), parent='body'),
    part('leg0', (-3, 10, 0), [box(-2.5, 0, -2.5, 5, 11, 5, N1, pattern='scales'), box(-3, 11, -4, 6, 3, 7, N2)]),
    part('leg1', (3, 10, 0), [box(-2.5, 0, -2.5, 5, 11, 5, N1, pattern='scales'), box(-3, 11, -4, 6, 3, 7, N2)]),
    part('tail0', (0, -1, 3.5), [box(-2, -2, 0, 4, 4, 9, N1, pattern='scales'), box(-0.5, -3.5, 1, 1, 2, 7, NHORN)],
         rot=(-0.4, 0, 0), parent='body'),
    part('tail1', (0, 0, 9), [box(-1.5, -1.5, 0, 3, 3, 9, N1, pattern='scales'), box(-2.5, -0.5, 7, 5, 1, 4, NHORN)],
         rot=(0.35, 0, 0), parent='tail0'),
]
biped('nidhogg', False)
nd = A['nidhogg']
rot(nd['idle'][2], 'wing0', 1, wave(2.0, 8, offset=0))
rot(nd['idle'][2], 'wing1', 1, wave(2.0, -8, offset=0))
rot(nd['walk'][2], 'wing0', 1, wave(1.0, 10))
rot(nd['walk'][2], 'wing1', 1, wave(1.0, -10))
rot(nd['roar'][2], 'wing0', 1, pulse([(0, 0), (0.3, -45), (0.9, -45), (1.2, 0)]))
rot(nd['roar'][2], 'wing1', 1, pulse([(0, 0), (0.3, 45), (0.9, 45), (1.2, 0)]))


# ---------------- Java ----------------

def fnum(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return ('0' if s in ('-0', '') else s) + 'f'


def channel_java(target, axes, scale):
    times = sorted({round(t, 4) for keys in axes.values() for t, _ in keys})

    def at(keys, t):
        for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return keys[-1][1] if t > keys[-1][0] else keys[0][1]
    frames = []
    for t in times:
        v = [at(axes[a], t) if a in axes else 0.0 for a in range(3)]
        vec = 'KeyframeAnimations.%s(%s, %s, %s)' % ((scale,) + tuple(fnum(x) for x in v))
        frames.append('new Keyframe(%s, %s, AnimationChannel.Interpolations.CATMULLROM)' % (fnum(t), vec))
    return 'new AnimationChannel(AnimationChannel.Targets.%s,\n\t\t\t\t\t\t%s)' % (target, ',\n\t\t\t\t\t\t'.join(frames))


def anim_java(name, length, looping, bones):
    lines = ['\tprivate static AnimationDefinition %s() {' % camel(name),
             '\t\treturn AnimationDefinition.Builder.withLength(%s)%s' % (fnum(length), '.looping()' if looping else '')]
    for bone, chans in bones.items():
        if 'rot' in chans:
            lines.append('\t\t\t\t.addAnimation("%s", %s)' % (bone, channel_java('ROTATION', chans['rot'], 'degreeVec')))
        if 'pos' in chans:
            lines.append('\t\t\t\t.addAnimation("%s", %s)' % (bone, channel_java('POSITION', chans['pos'], 'posVec')))
    lines.append('\t\t\t\t.build();')
    lines.append('\t}')
    return '\n'.join(lines)


def main():
    layers, anims, cases, acases = [], [], [], []
    for form, spec in F.items():
        W, H = pack(spec)
        write_png(os.path.join(OUT_TEX, form + '.png'), paint(spec, W, H, sum(map(ord, form))))
        layers.append(java_layer(form, spec, W, H))
        cases.append('\t\t\tcase "%s" -> %s();' % (form, camel(form)))
        names = []
        for an, (length, looping, bones) in A[form].items():
            fn = form + '_' + an
            anims.append(anim_java(fn, length, looping, bones))
            names.append('"%s", %s()' % (an, camel(fn)))
        acases.append('\t\t\tcase "%s" -> Map.of(%s);' % (form, ', '.join(names)))
    java = '''package com.onepiecemod.zoan.client;

import java.util.Map;

import net.minecraft.client.animation.AnimationChannel;
import net.minecraft.client.animation.AnimationDefinition;
import net.minecraft.client.animation.Keyframe;
import net.minecraft.client.animation.KeyframeAnimations;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * GENERATED by tools/zoan/gen_zoan.py: the shapes and keyframe animations of the full-body Zoan forms.
 * Change the script and run it again instead of editing this file.
 */
public final class ZoanModels {
	public static final String[] FORMS = {%s};

	private ZoanModels() {
	}

	public static LayerDefinition layer(String form) {
		return switch (form) {
%s
			default -> throw new IllegalArgumentException("No Zoan form " + form);
		};
	}

	/** The form's animations by name: idle, walk, attack, roar, and fly for the phoenix. */
	public static Map<String, AnimationDefinition> animations(String form) {
		return switch (form) {
%s
			default -> Map.of();
		};
	}

%s

%s
}
''' % (', '.join('"%s"' % f for f in F), '\n'.join(cases), '\n'.join(acases), '\n\n'.join(layers), '\n\n'.join(anims))
    os.makedirs(os.path.dirname(OUT_JAVA), exist_ok=True)
    with open(OUT_JAVA, 'w') as f:
        f.write(java)
    print('generated', len(F), 'Zoan forms')


if __name__ == '__main__':
    main()
