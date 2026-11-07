"""Generates the monster forms only bosses use: King's pteranodon, Magellan's Venom Demon,
Queen's brachiosaurus, Saint Saturn's Gyuki and Imu's two monster forms.

Run:  python3 -I gen_boss_forms.py <path to source/>
Writes src/client/java/com/onepiecemod/character/client/BossFormModels.java and
src/main/resources/assets/onepiece/textures/entity/boss_form/<form>.png.
Kaido's dragon (seiryu) and Lucci's leopard are player Zoan forms from tools/zoan/gen_zoan.py; bosses reuse those.
Same model space and animation rules as gen_zoan.py (16 px = 1 block, y down, y = 24 is the ground, front is -z).
Animation names: idle, walk, fly (optional), attack, roar.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'creatures'))
sys.path.insert(0, os.path.join(HERE, '..', 'zoan'))
from gen_creatures import box, part, pack, paint, write_png, java_layer, camel  # noqa: E402
from gen_zoan import wave, rot, pos, pulse, anim_java  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
OUT_JAVA = os.path.join(SRC, 'src/client/java/com/onepiecemod/character/client/BossFormModels.java')
OUT_TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/boss_form')

F, A = {}, {}

# ---------------- King: Pteranodon (black, with Lunarian flames on the back) ----------------
K1, K2, BEAK, FLAME, FLAME2 = '#262428', '#4a4650', '#c8b890', '#ff8a20', '#ffe060'
F['pteranodon'] = [
    part('body', (0, 12, 0), [box(-4, -4, -8, 8, 7, 16, K1, pattern='scales'),
                              box(-3, -1, -9, 6, 5, 2, K2),
                              box(-2, -7, -4, 4, 3, 8, FLAME, pattern='stripes')]),
    part('head', (0, -2, -8), [box(-3, -5, -6, 6, 6, 6, K1, eyes='#ff3020', pattern='scales'),
                               box(-1.5, -3, -16, 3, 3, 10, BEAK),
                               box(-1, -0.5, -14, 2, 1, 8, BEAK),
                               box(-0.5, -9, 0, 1, 5, 8, K2),
                               box(-2, -8, -2, 4, 3, 3, FLAME)], parent='body'),
    part('wing0', (-4, -3, -4), [box(-14, -0.5, 0, 14, 1, 12, K1, pattern='stripes')], parent='body'),
    part('wingtip0', (-14, 0, 0), [box(-14, -0.5, 0, 14, 1, 9, K2, pattern='stripes'), box(-14, -0.5, 9, 14, 1, 2, FLAME2)],
         parent='wing0'),
    part('wing1', (4, -3, -4), [box(0, -0.5, 0, 14, 1, 12, K1, pattern='stripes')], parent='body'),
    part('wingtip1', (14, 0, 0), [box(0, -0.5, 0, 14, 1, 9, K2, pattern='stripes'), box(0, -0.5, 9, 14, 1, 2, FLAME2)],
         parent='wing1'),
    part('tail', (0, -1, 8), [box(-1.5, -1, 0, 3, 2, 10, K1, pattern='scales'), box(-2, -3, 8, 4, 4, 3, FLAME)],
         rot=(0.1, 0, 0), parent='body'),
    part('leg0', (-2.5, 15, 2), [box(-1, 0, -1, 2, 7, 2, K2), box(-2, 7, -3, 4, 2, 4, BEAK)]),
    part('leg1', (2.5, 15, 2), [box(-1, 0, -1, 2, 7, 2, K2), box(-2, 7, -3, 4, 2, 4, BEAK)]),
]

# ---------------- Magellan: Venom Demon (Hydra's poison shaped into a giant horned demon) ----------------
P1, P2, P3, BONE, EYE = '#6a2a8a', '#9a50c0', '#3a1050', '#e8e0d0', '#ffe030'
F['venom_demon'] = [
    part('base', (0, 24, 0), [box(-7, -6, -6, 14, 6, 12, P3, pattern='fluff'), box(-9, -2, -8, 18, 2, 16, P1, pattern='fluff')]),
    part('body', (0, 18, 0), [box(-8, -18, -5, 16, 18, 10, P1, pattern='fluff'),
                              box(-6, -16, -5.6, 12, 10, 1, P2, pattern='speckle'),
                              box(-10, -19, -4, 20, 4, 8, P2, pattern='fluff')]),
    part('head', (0, -18, -1), [box(-5, -10, -5, 10, 10, 9, P1, eyes=EYE, pattern='speckle'),
                                box(-4, -3, -6, 8, 3, 2, BONE, front=[(1, 0, P3), (3, 0, P3), (5, 0, P3)]),
                                box(-8, -14, -2, 3, 6, 3, BONE), box(5, -14, -2, 3, 6, 3, BONE),
                                box(-9, -17, -1, 2, 4, 2, BONE), box(7, -17, -1, 2, 4, 2, BONE)], parent='body'),
    part('arm0', (-10, -16, 0), [box(-6, -2, -3.5, 6, 18, 7, P1, pattern='fluff'),
                                 box(-7, 16, -4.5, 8, 6, 9, P2, pattern='fluff'),
                                 box(-7, 21, -5, 2, 3, 2, BONE), box(-3, 21, -5, 2, 3, 2, BONE)], parent='body'),
    part('arm1', (10, -16, 0), [box(0, -2, -3.5, 6, 18, 7, P1, pattern='fluff'),
                                box(-1, 16, -4.5, 8, 6, 9, P2, pattern='fluff'),
                                box(5, 21, -5, 2, 3, 2, BONE), box(1, 21, -5, 2, 3, 2, BONE)], parent='body'),
]


# ---------------- Queen: Brachiosaurus (long neck, tan hide, Queen's braids down the neck) ----------------
Q1, Q2, QB, QHAIR, QSHADE = '#a8906a', '#7a6648', '#dccba0', '#2a2a2e', '#40e0e8'
F['brachiosaurus'] = [
    part('body', (0, 10, 0), [box(-6, -5, -9, 12, 10, 18, Q1, pattern='scales'),
                              box(-5, 4, -8, 10, 1, 16, QB)]),
    part('neck', (0, -3, -8), [box(-2, -18, -2, 4, 18, 4, Q1, pattern='scales'),
                               box(-1, -16, 2, 2, 14, 1, QHAIR)], rot=(0.35, 0, 0), parent='body'),
    part('head', (0, -18, 0), [box(-2.5, -3, -6, 5, 4, 7, Q1, eyes='#2a2a2a', pattern='scales'),
                               box(-2.5, -2.5, -6.2, 5, 1, 1, QSHADE),
                               box(-1.5, -1, -8, 3, 2, 2, QB)], rot=(-0.35, 0, 0), parent='neck'),
    part('tail', (0, -2, 9), [box(-2, -2, 0, 4, 4, 14, Q1, pattern='scales'), box(-1, -1, 14, 2, 2, 6, Q2)],
         rot=(-0.25, 0, 0), parent='body'),
    part('leg0', (-4, 14, -6), [box(-2, 0, -2, 4, 10, 4, Q2)]),
    part('leg1', (4, 14, -6), [box(-2, 0, -2, 4, 10, 4, Q2)]),
    part('leg2', (-4, 14, 6), [box(-2, 0, -2, 4, 10, 4, Q2)]),
    part('leg3', (4, 14, 6), [box(-2, 0, -2, 4, 10, 4, Q2)]),
]

# ---------------- Saint Saturn: Gyuki (an ox-skull head with horns on a giant spider's body) ----------------
S1, S2, SBONE, SEYE = '#2a2630', '#4a4452', '#e8e0d0', '#ff2a20'
_gyuki = [
    part('body', (0, 10, 0), [box(-6, -4, -6, 12, 8, 12, S1, pattern='speckle')]),
    part('abdomen', (0, -1, 6), [box(-7, -6, 0, 14, 11, 14, S2, pattern='speckle'),
                                 box(-2, -6.5, 3, 4, 1, 8, '#7a2a3a')], rot=(-0.15, 0, 0), parent='body'),
    part('head', (0, -1, -6), [box(-5, -6, -8, 10, 9, 8, SBONE, eyes=SEYE),
                               box(-3, -1, -10, 6, 4, 3, '#cfc6b4'),
                               box(-11, -8, -5, 6, 2, 2, SBONE), box(5, -8, -5, 6, 2, 2, SBONE),
                               box(-12, -13, -5, 2, 6, 2, SBONE), box(10, -13, -5, 2, 6, 2, SBONE),
                               box(-5, -7, -2, 10, 1, 2, S1)], parent='body'),
]
for i, z in enumerate((-4, -1, 2, 5)):
    for side, sx in (('l', -1), ('r', 1)):
        n = '%s%d' % (side, i)
        upper = box(-12, -1, -1, 12, 2, 2, S2) if sx < 0 else box(0, -1, -1, 12, 2, 2, S2)
        fan = (0.55, 0.18, -0.18, -0.55)[i]   # front legs reach forward, back legs back
        _gyuki.append(part('leg_' + n, (sx * 6, 10, z), [upper], rot=(0, fan * sx, 0.6 * -sx)))
        _gyuki.append(part('foot_' + n, (sx * 12, 0, 0), [box(-1, 0, -1, 2, 22, 2, S1), box(-1.5, 20, -1.5, 3, 2, 3, SBONE)],
                           rot=(0, 0, 0.35 * -sx), parent='leg_' + n))
F['gyuki'] = _gyuki

# ---------------- Imu: the demonic form (chapter 1191 leaks: bigger, four horns, blackened arms, a pendant of horned skulls) ----------------
I1, I2, IARM, IHORN, IHAIR, IEYE, IGOLD, ISKULL = '#16141a', '#2a2630', '#0a0a0c', '#d8d0c0', '#f0f0f0', '#e02020', '#c8a040', '#e8e0d0'
F['imu_demon'] = [
    part('body', (0, 6, 0), [box(-7, -18, -4, 14, 18, 8, I1, pattern='fluff'),
                             box(-1, -18, -4.6, 2, 16, 1, IGOLD),
                             # The pendant: three horned skulls on a gold chain.
                             box(-5, -16, -5, 10, 1, 1, IGOLD),
                             box(-1.5, -15, -6, 3, 3, 1, ISKULL, front=[(0, 1, '#1a1a1a'), (2, 1, '#1a1a1a')]),
                             box(-5, -14, -6, 3, 3, 1, ISKULL, front=[(0, 1, '#1a1a1a'), (2, 1, '#1a1a1a')]),
                             box(2, -14, -6, 3, 3, 1, ISKULL, front=[(0, 1, '#1a1a1a'), (2, 1, '#1a1a1a')]),
                             box(-8, 0, -5, 16, 18, 10, I1, pattern='fluff')]),
    part('head', (0, -18, 0), [box(-4, -8, -4, 8, 8, 8, I2, eyes=IEYE),
                               box(-5, -9, -3, 10, 4, 9, IHAIR, pattern='stripes'),
                               box(-5, -6, 3, 10, 14, 2, IHAIR, pattern='stripes'),
                               # Four horns: two big ones curling up, two smaller ones at the back.
                               box(-7, -11, -2, 3, 4, 3, IHORN), box(-8, -16, -1, 2, 5, 2, IHORN),
                               box(4, -11, -2, 3, 4, 3, IHORN), box(6, -16, -1, 2, 5, 2, IHORN),
                               box(-4, -12, 2, 2, 4, 2, IHORN), box(2, -12, 2, 2, 4, 2, IHORN)], parent='body'),
    part('arm0', (-8, -16, 0), [box(-4, -2, -2.5, 4, 20, 5, IARM, pattern='scales'),
                                box(-5, 17, -3, 6, 4, 6, IARM, front=[(0, 3, IHORN), (2, 3, IHORN), (4, 3, IHORN)])], parent='body'),
    part('arm1', (8, -16, 0), [box(0, -2, -2.5, 4, 20, 5, IARM, pattern='scales'),
                               box(-1, 17, -3, 6, 4, 6, IARM, front=[(1, 3, IHORN), (3, 3, IHORN), (5, 3, IHORN)])], parent='body'),
]

# ---------------- Imu: the third form (chapter 1198 leaks: a huge beast, stretched torso, long neck, massive horns) ----------------
F['imu_beast'] = [
    part('body', (0, 8, 0), [box(-6, -5, -12, 12, 10, 24, I1, pattern='fluff'),
                             box(-1, -5.5, -11, 2, 1, 22, IGOLD),
                             box(-5, 4, -11, 10, 1, 20, IARM)]),
    part('neck', (0, -2, -11), [box(-2.5, -18, -2.5, 5, 18, 5, I2, pattern='scales'),
                                box(-3, -17, 2, 6, 16, 1, IHAIR, pattern='stripes')], rot=(0.45, 0, 0), parent='body'),
    part('head', (0, -18, 0), [box(-4, -6, -7, 8, 7, 8, I2, eyes=IEYE),
                               box(-3, -1, -9, 6, 2, 4, IARM, front=[(0, 0, ISKULL), (2, 0, ISKULL), (3, 0, ISKULL), (5, 0, ISKULL)]),
                               box(-4.5, -7, 0, 9, 4, 4, IHAIR, pattern='stripes'),
                               # Massive horns sweeping out and up.
                               box(-12, -8, -2, 8, 3, 3, IHORN), box(-14, -16, -2, 3, 9, 3, IHORN), box(-15, -20, -1, 2, 4, 2, IHORN),
                               box(4, -8, -2, 8, 3, 3, IHORN), box(11, -16, -2, 3, 9, 3, IHORN), box(13, -20, -1, 2, 4, 2, IHORN),
                               box(-3, -11, -1, 2, 5, 2, IHORN), box(1, -11, -1, 2, 5, 2, IHORN)], rot=(-0.45, 0, 0), parent='neck'),
    part('tail', (0, -2, 12), [box(-2, -2, 0, 4, 4, 14, I1, pattern='fluff'), box(-3, -3, 12, 6, 6, 4, IARM)],
         rot=(-0.2, 0, 0), parent='body'),
    part('leg0', (-5, 12, -9), [box(-2.5, 0, -2.5, 5, 12, 5, IARM, pattern='scales'), box(-3, 10, -4, 6, 2, 6, IARM, front=[(0, 0, IHORN), (5, 0, IHORN)])]),
    part('leg1', (5, 12, -9), [box(-2.5, 0, -2.5, 5, 12, 5, IARM, pattern='scales'), box(-3, 10, -4, 6, 2, 6, IARM, front=[(0, 0, IHORN), (5, 0, IHORN)])]),
    part('leg2', (-5, 12, 9), [box(-2.5, 0, -2.5, 5, 12, 5, I1, pattern='fluff')]),
    part('leg3', (5, 12, 9), [box(-2.5, 0, -2.5, 5, 12, 5, I1, pattern='fluff')]),
]

# ---------------- animations ----------------
# Pteranodon: always on the wing (the boss renderer draws it flying), a dive with the beak to attack.
idle, walk, fly, attack, roar = {}, {}, {}, {}, {}
rot(idle, 'wing0', 2, wave(1.6, 25))
rot(idle, 'wing1', 2, wave(1.6, -25))
rot(idle, 'wingtip0', 2, wave(1.6, 15, -0.9))
rot(idle, 'wingtip1', 2, wave(1.6, -15, -0.9))
rot(idle, 'head', 0, wave(1.6, 5, 1.0))
rot(walk, 'leg0', 0, wave(0.8, 25))
rot(walk, 'leg1', 0, wave(0.8, -25))
rot(fly, 'wing0', 2, wave(1.0, 45))
rot(fly, 'wing1', 2, wave(1.0, -45))
rot(fly, 'wingtip0', 2, wave(1.0, 28, -0.9))
rot(fly, 'wingtip1', 2, wave(1.0, -28, -0.9))
pos(fly, 'body', 1, wave(1.0, 1.5, 3.14159))
rot(fly, 'tail', 0, wave(1.0, 6, 0.5))
rot(fly, 'leg0', 0, wave(1.0, 0, offset=55))
rot(fly, 'leg1', 0, wave(1.0, 0, offset=55))
rot(attack, 'body', 0, pulse([(0, 0), (0.15, 30), (0.4, -10), (0.6, 0)]))
rot(attack, 'head', 0, pulse([(0, 0), (0.15, -25), (0.3, 30), (0.6, 0)]))
rot(attack, 'wing0', 2, pulse([(0, 0), (0.15, -60), (0.6, 0)]))
rot(attack, 'wing1', 2, pulse([(0, 0), (0.15, 60), (0.6, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.3, -45), (1.0, -45), (1.3, 0)]))
rot(roar, 'wing0', 2, pulse([(0, 0), (0.3, -70), (1.0, -70), (1.3, 0)]))
rot(roar, 'wing1', 2, pulse([(0, 0), (0.3, 70), (1.0, 70), (1.3, 0)]))
A['pteranodon'] = {'idle': (1.6, True, idle), 'walk': (0.8, True, walk), 'fly': (1.0, True, fly),
                   'attack': (0.6, False, attack), 'roar': (1.3, False, roar)}

# Venom Demon: a slow, heavy sway; drags itself forward; slams both fists down.
idle, walk, attack, roar = {}, {}, {}, {}
rot(idle, 'body', 2, wave(3.0, 3))
rot(idle, 'body', 0, wave(3.0, 2, 1.5))
rot(idle, 'arm0', 2, wave(3.0, 5, 0.4, offset=4))
rot(idle, 'arm1', 2, wave(3.0, -5, 0.4, offset=-4))
rot(idle, 'head', 1, wave(3.0, 6, 0.8))
pos(idle, 'base', 1, wave(1.5, 0.5))
rot(walk, 'arm0', 0, wave(1.4, -20))
rot(walk, 'arm1', 0, wave(1.4, 20))
rot(walk, 'body', 1, wave(1.4, 8))
pos(walk, 'body', 1, wave(0.7, -1.0, n=6))
rot(attack, 'arm0', 0, pulse([(0, 0), (0.2, -160), (0.4, -20), (0.7, 0)]))
rot(attack, 'arm1', 0, pulse([(0, 0), (0.2, -160), (0.4, -20), (0.7, 0)]))
rot(attack, 'body', 0, pulse([(0, 0), (0.2, -15), (0.4, 25), (0.7, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.4, -35), (1.2, -35), (1.6, 0)]))
rot(roar, 'arm0', 2, pulse([(0, 0), (0.4, 60), (1.2, 60), (1.6, 0)]))
rot(roar, 'arm1', 2, pulse([(0, 0), (0.4, -60), (1.2, -60), (1.6, 0)]))
rot(roar, 'body', 0, pulse([(0, 0), (0.4, -15), (1.2, -15), (1.6, 0)]))
A['venom_demon'] = {'idle': (3.0, True, idle), 'walk': (1.4, True, walk), 'attack': (0.7, False, attack), 'roar': (1.6, False, roar)}


# Brachiosaurus: neck sways, heavy four-legged walk, slams its head down, roars at the sky.
idle, walk, attack, roar = {}, {}, {}, {}
rot(idle, 'neck', 0, wave(3.0, 4))
rot(idle, 'head', 0, wave(3.0, -3, 0.6))
rot(idle, 'tail', 1, wave(3.0, 8))
rot(walk, 'leg0', 0, wave(1.2, 20))
rot(walk, 'leg3', 0, wave(1.2, 20))
rot(walk, 'leg1', 0, wave(1.2, -20))
rot(walk, 'leg2', 0, wave(1.2, -20))
rot(walk, 'neck', 0, wave(0.6, 3))
rot(walk, 'tail', 1, wave(1.2, 10))
rot(attack, 'neck', 0, pulse([(0, 0), (0.2, -25), (0.45, 45), (0.8, 0)]))
rot(attack, 'head', 0, pulse([(0, 0), (0.2, -10), (0.45, 20), (0.8, 0)]))
rot(roar, 'neck', 0, pulse([(0, 0), (0.4, -35), (1.2, -35), (1.6, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.4, -25), (1.2, -25), (1.6, 0)]))
rot(roar, 'tail', 0, pulse([(0, 0), (0.4, -15), (1.2, -15), (1.6, 0)]))
A['brachiosaurus'] = {'idle': (3.0, True, idle), 'walk': (1.2, True, walk), 'attack': (0.8, False, attack), 'roar': (1.6, False, roar)}

# Gyuki: legs twitch, scuttles with the legs in two alternating groups, rams with the horns, rears up to roar.
idle, walk, attack, roar = {}, {}, {}, {}
rot(idle, 'head', 1, wave(2.5, 6))
rot(idle, 'abdomen', 0, wave(2.5, 4, 1.0))
for i in range(4):
    for side, sx in (('l', -1), ('r', 1)):
        n = 'leg_%s%d' % (side, i)
        group = 1 if (i + (sx > 0)) % 2 else -1
        rot(idle, n, 2, wave(2.5, 3 * sx, i * 0.7))
        rot(walk, n, 1, wave(0.7, 18 * group))
        rot(walk, n, 2, wave(0.7, 8 * sx * group, 1.57))
pos(walk, 'body', 1, wave(0.35, -0.6))
rot(attack, 'head', 0, pulse([(0, 0), (0.2, -30), (0.4, 25), (0.7, 0)]))
rot(attack, 'body', 0, pulse([(0, 0), (0.2, -10), (0.4, 12), (0.7, 0)]))
rot(roar, 'body', 0, pulse([(0, 0), (0.4, -25), (1.2, -25), (1.6, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.4, -20), (1.2, -20), (1.6, 0)]))
for side, sx in (('l', -1), ('r', 1)):
    rot(roar, 'leg_%s0' % side, 2, pulse([(0, 0), (0.4, -40 * sx), (1.2, -40 * sx), (1.6, 0)]))
A['gyuki'] = {'idle': (2.5, True, idle), 'walk': (0.7, True, walk), 'attack': (0.7, False, attack), 'roar': (1.6, False, roar)}

# Imu, demonic form: slow menacing sway, horn-first lunge, both black arms crash down.
idle, walk, attack, roar = {}, {}, {}, {}
rot(idle, 'body', 2, wave(3.0, 2))
rot(idle, 'arm0', 2, wave(3.0, 4, offset=6))
rot(idle, 'arm1', 2, wave(3.0, -4, offset=-6))
rot(idle, 'head', 0, wave(3.0, 3, 1.0))
rot(walk, 'arm0', 0, wave(1.4, -18))
rot(walk, 'arm1', 0, wave(1.4, 18))
pos(walk, 'body', 1, wave(0.7, -0.8, n=6))
rot(attack, 'arm0', 0, pulse([(0, 0), (0.2, -170), (0.4, -20), (0.7, 0)]))
rot(attack, 'arm1', 0, pulse([(0, 0), (0.2, -170), (0.4, -20), (0.7, 0)]))
rot(attack, 'body', 0, pulse([(0, 0), (0.2, -12), (0.4, 20), (0.7, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.4, -30), (1.2, -30), (1.6, 0)]))
rot(roar, 'arm0', 2, pulse([(0, 0), (0.4, 70), (1.2, 70), (1.6, 0)]))
rot(roar, 'arm1', 2, pulse([(0, 0), (0.4, -70), (1.2, -70), (1.6, 0)]))
A['imu_demon'] = {'idle': (3.0, True, idle), 'walk': (1.4, True, walk), 'attack': (0.7, False, attack), 'roar': (1.6, False, roar)}

# Imu, third form: the long neck weaves like a snake, heavy four-legged prowl, horns rammed forward.
idle, walk, attack, roar = {}, {}, {}, {}
rot(idle, 'neck', 0, wave(3.0, 5))
rot(idle, 'neck', 1, wave(3.0, 10, 1.2))
rot(idle, 'head', 1, wave(3.0, -8, 1.8))
rot(idle, 'tail', 1, wave(3.0, 12))
for leg, sgn in (('leg0', 1), ('leg3', 1), ('leg1', -1), ('leg2', -1)):
    rot(walk, leg, 0, wave(1.2, 22 * sgn))
rot(walk, 'neck', 1, wave(1.2, 6))
rot(walk, 'tail', 1, wave(1.2, 14))
rot(attack, 'neck', 0, pulse([(0, 0), (0.2, -30), (0.45, 50), (0.8, 0)]))
rot(attack, 'head', 0, pulse([(0, 0), (0.2, -10), (0.45, 25), (0.8, 0)]))
rot(roar, 'neck', 0, pulse([(0, 0), (0.4, -40), (1.2, -40), (1.6, 0)]))
rot(roar, 'head', 0, pulse([(0, 0), (0.4, -30), (1.2, -30), (1.6, 0)]))
rot(roar, 'body', 0, pulse([(0, 0), (0.4, -10), (1.2, -10), (1.6, 0)]))
A['imu_beast'] = {'idle': (3.0, True, idle), 'walk': (1.2, True, walk), 'attack': (0.8, False, attack), 'roar': (1.6, False, roar)}


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
    java = '''package com.onepiecemod.character.client;

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
 * GENERATED by tools/bossforms/gen_boss_forms.py: monster forms only bosses use (King's pteranodon,
 * Magellan's Venom Demon, Queen's brachiosaurus, Saturn's Gyuki, Imu's demon and beast forms). Change the script and run it again instead of editing this file.
 */
public final class BossFormModels {
	public static final String[] FORMS = {%s};

	private BossFormModels() {
	}

	public static LayerDefinition layer(String form) {
		return switch (form) {
%s
			default -> throw new IllegalArgumentException("No boss form " + form);
		};
	}

	/** The form's animations by name: idle, walk, attack, roar, and fly for the pteranodon. */
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
    print('generated', len(F), 'boss forms')


if __name__ == '__main__':
    main()
