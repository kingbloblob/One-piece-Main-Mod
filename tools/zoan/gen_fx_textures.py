"""Textures for the Logia element body (element_0..3.png) and first-person Zoan arms (arm_<form>.png).

Run:  python3 -I gen_fx_textures.py <path to source/>
element_N: soft white flame noise (tinted in game with the fruit's color), with more holes each frame
so the shell crumbles away. arm_<form>: a 64x64 skin-layout texture filled with the form's fur/scales.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'creatures'))
from gen_creatures import write_png, hexc  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
FX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/fx')
ZOAN = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/zoan')


def element(frame):
    rnd = random.Random(40 + frame)
    holes = [0.05, 0.25, 0.5, 0.75][frame]
    img = []
    for y in range(64):
        row = []
        for x in range(64):
            # flame-like streaks rising up each body part (v grows downward in a skin texture)
            f = 0.75 + 0.25 * math.sin(x * 0.9 + y * 0.35 + frame) * math.sin(y * 0.55 - x * 0.2)
            f *= rnd.uniform(0.85, 1.1)
            if rnd.random() < holes:
                row.append((0, 0, 0, 0))
            else:
                v = max(0, min(255, int(255 * f)))
                row.append((v, v, v, 255))
        img.append(row)
    return img


def fur(base, spots=None, stripes=None, seed=1):
    rnd = random.Random(seed)
    c = hexc(base)
    img = []
    for y in range(64):
        row = []
        for x in range(64):
            f = rnd.uniform(0.88, 1.08)
            col = c
            if spots and ((x * 7 + y * 13) % 23 == 0 or (x * 5 + y * 3) % 29 == 0):
                col = hexc(spots)
            if stripes and y % 4 == 0:
                col = hexc(stripes)
            row.append(tuple(max(0, min(255, int(v * f))) for v in col) + (255,))
        img.append(row)
    return img


def main():
    for frame in range(4):
        write_png(os.path.join(FX, 'element_%d.png' % frame), element(frame))
    write_png(os.path.join(ZOAN, 'arm_leopard.png'), fur('#e0b040', spots='#3a2410', seed=2))
    write_png(os.path.join(ZOAN, 'arm_heavy_point.png'), fur('#8a5a3c', seed=3))
    write_png(os.path.join(ZOAN, 'arm_phoenix.png'), fur('#30a0f0', stripes='#7ad8ff', seed=4))
    write_png(os.path.join(ZOAN, 'arm_seiryu.png'), fur('#2a70c0', stripes='#60d0e0', seed=5))
    write_png(os.path.join(ZOAN, 'arm_nidhogg.png'), fur('#1e3a34', stripes='#2e5a4e', seed=6))
    write_png(os.path.join(ZOAN, 'arm_nika_wild.png'), fur('#e8b890', spots='#c8946a', seed=7))
    print('written element + arm textures')


if __name__ == '__main__':
    main()
