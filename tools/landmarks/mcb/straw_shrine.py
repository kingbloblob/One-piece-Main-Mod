"""Hawkins' Straw Shrine v2, redesigned with the Minecraft Builder skill: Basil Hawkins the Magician's hideaway in a
misty swamp forest (his Straw Man form, ch 501+ / ep 395+ and Wano: a towering straw figure stuck with nails; tarot
cards, straw dolls, candles everywhere).

Silhouette first: a GIANT Straw Man effigy, 40 blocks tall, standing behind the shrine with its arms spread, a
pointed straw hood over a hollow face, nails and spikes stuck through the straw, straw strands hanging off its arms;
in front of it a dark shrine hall under a curved irimoya roof; a long line of vermilion torii over a boardwalk that
crosses the swamp to it; dead trees hung with straw dolls all around.

Around it: the black swamp (mud, pools, lily pads, roots, moss, dead dark oak and mangrove), the shrine hall inside
(altar with the giant tarot cards, candles in rows, straw dolls on shelves, Hawkins' card table), the fortune
teller's hut on stilts, the crew's camp of tents, stone lanterns, a ring of hanging dolls. 128 x 128, land site,
ground y 0, pools sit below it and never touch the edge. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
import mcasian as A  # noqa: E402

SID = "straw_shrine"
TITLE = "Hawkins' Straw Shrine"
CUTS = [3, 10, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 128
CX = 64                             # the shrine axis (north-south)
HZ0, HZ1 = 30, 50                   # shrine hall
EZ = 20                             # effigy feet
_LAND = NT.outline(64, 64, 60, 6501, wobble=0.12)
SWAMP = [("minecraft:mud", 0.3), ("minecraft:grass_block", 0.25), ("minecraft:moss_block", 0.18), ("minecraft:podzol", 0.12),
         ("minecraft:coarse_dirt", 0.08), ("minecraft:rooted_dirt", 0.07)]
SHRINE = dict(column="minecraft:stripped_dark_oak_log", beam="minecraft:dark_oak_planks", soffit="minecraft:dark_oak_planks",
              panel="minecraft:yellow_terracotta", lattice="minecraft:dark_oak_planks", wall_low="minecraft:brown_terracotta",
              floor="minecraft:dark_oak_planks", ornament="minecraft:dark_oak_planks", bracket="minecraft:stripped_dark_oak_log",
              bracket_stairs="minecraft:dark_oak_stairs")
STRAW = ["minecraft:hay_block", "minecraft:hay_block", "minecraft:yellow_terracotta", "minecraft:bamboo_block[axis=y]"]


def pools(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (NT.noise(X, Z, 6502, 14) > 0.62) & (_LAND(X, Z) > 10) & ~((np.abs(X - CX) < 22) & (Z > 8) & (Z < 60))


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    h = 1 + NT.fbm(X, Z, 6503, 16) * 2
    h = np.where(d < 10, h * np.clip(d / 10.0, 0, 1), h)
    h = np.where(pools(X, Z), -2, h)
    sh = (np.abs(X - CX) < 20) & (Z > 10) & (Z < 56)
    h = np.where(sh, 2, h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def onland(X, Z):
    return _LAND(np.asarray(X, float), np.asarray(Z, float)) > 0


def terrain(bb):
    pl = lambda X, Z: pools(X, Z)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SWAMP, 6504, mask=lambda X, Z: onland(X, Z) & ~pl(X, Z), core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:mud", 0.7), ("minecraft:clay", 0.3)], 6505, mask=pl, under="minecraft:mud",
             core="minecraft:stone", base=-6)
    bb.fill_where(0, -1, 0, N - 1, 0, N - 1, lambda X, y, Z: pl(X, Z), "minecraft:water")
    rng = np.random.default_rng(6506)
    for _ in range(140):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if pools(np.array(float(x)), np.array(float(z))) and rng.random() < 0.5:
            bb.set(x, 1, z, "minecraft:lily_pad")
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 6507, density=0.35, kinds=["minecraft:fern", "minecraft:short_grass", "minecraft:large_fern",
              "minecraft:moss_carpet", "minecraft:brown_mushroom", "minecraft:bush"], flowers=["minecraft:blue_orchid"],
              mask=lambda X, Z: onland(X, Z) & ~pl(X, Z))


def dead_tree(bb, x, z, h, rng, dolls=0):
    """A dead swamp tree: dark trunk with roots, bare crooked branches, hanging moss vines and straw dolls."""
    y = hy(x, z)
    log = "minecraft:dark_oak_log" if rng.random() < 0.6 else "minecraft:mangrove_log"
    bb.fill(x, y - 1, z, x, y + h, z, log + "[axis=y]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if rng.random() < 0.7:
            bb.set(x + dx, y + 1, z + dz, "minecraft:mangrove_roots")
    tips = []
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 6.283)
        by = y + int(h * rng.uniform(0.45, 0.95))
        L = int(rng.integers(3, 7))
        for s in range(1, L + 1):
            bx, bz = x + int(round(math.cos(a) * s)), z + int(round(math.sin(a) * s))
            bb.set(bx, by + s // 2, bz, log + ("[axis=x]" if abs(math.cos(a)) > 0.7 else "[axis=z]" if abs(math.sin(a)) > 0.7 else "[axis=y]"))
        tips.append((x + int(round(math.cos(a) * L)), by + L // 2, z + int(round(math.sin(a) * L))))
    for (tx, ty, tz) in tips:
        if dolls > 0:
            dolls -= 1
            n = int(rng.integers(2, 5))
            bb.fill(tx, ty - n, tz, tx, ty - 1, tz, "minecraft:iron_chain[axis=y]")
            straw_doll(bb, tx, ty - n - 3, tz)
        elif rng.random() < 0.6:
            n = int(rng.integers(2, 6))
            for k in range(1, n):
                bb.set(tx, ty - k, tz, "minecraft:weeping_vines_plant" if k < n - 1 else "minecraft:weeping_vines")


def straw_doll(bb, x, y, z):
    """A hanging straw doll: hay head, a cross of bamboo arms, a straw body with a red tie."""
    bb.set(x, y + 2, z, "minecraft:hay_block")
    bb.set(x, y + 1, z, "minecraft:yellow_terracotta")
    bb.set(x - 1, y + 1, z, "minecraft:bamboo_fence") if False else None
    bb.set(x, y, z, "minecraft:red_wool")


def effigy(bb):
    """The Straw Man: legs like bundled sheaves, a long straw robe, arms spread wide with straw strands hanging, a
    pointed hood with a dark hollow face and two glowing eyes, nails stuck through it."""
    y0 = 2
    straw = lambda X, y, Z: np.where(NT.noise(X * 3 + y, Z * 3, 6508, 2) > 0.55, 1, 0)
    hb = bb.register("minecraft:hay_block"); yt = bb.register("minecraft:yellow_terracotta")

    def fill_shape(x1, y1, z1, x2, y2, z2, f):
        bb.fill_where(x1, y1, z1, x2, y2, z2, lambda X, y, Z: f(X, y, Z) & (straw(X, y, Z) == 0), "minecraft:hay_block")
        bb.fill_where(x1, y1, z1, x2, y2, z2, lambda X, y, Z: f(X, y, Z) & (straw(X, y, Z) == 1), "minecraft:yellow_terracotta")
    # legs (two sheaves) and robe flaring to the ground
    for s in (-1, 1):
        fill_shape(CX + s * 4 - 3, y0, EZ - 3, CX + s * 4 + 3, y0 + 12, EZ + 3,
                   lambda X, y, Z, s=s: ((X - CX - s * 4) ** 2 + (Z - EZ) ** 2) <= (2.6 - (y - y0) * 0.04) ** 2)
    fill_shape(CX - 10, y0 + 8, EZ - 7, CX + 10, y0 + 28, EZ + 7,
               lambda X, y, Z: ((X - CX) / (8.5 - (y - y0 - 8) * 0.22)) ** 2 + ((Z - EZ) / (5.5 - (y - y0 - 8) * 0.13)) ** 2 <= 1)
    # hollow the robe so it reads as a shell (and saves blocks)
    bb.fill_where(CX - 9, y0 + 9, EZ - 6, CX + 9, y0 + 26, EZ + 6,
                  lambda X, y, Z: ((X - CX) / (7.0 - (y - y0 - 8) * 0.22)) ** 2 + ((Z - EZ) / (4.0 - (y - y0 - 8) * 0.13)) ** 2 <= 1, AIR)
    # shoulders and spread arms with the hands drooping, straw strands hanging
    ay = y0 + 26
    for s in (-1, 1):
        for k in range(0, 19):
            x = CX + s * (3 + k)
            yy = ay - (k * k) // 60
            fill_shape(x - 1, yy - 2, EZ - 2, x + 1, yy + 2, EZ + 2, lambda X, y, Z, x=x, yy=yy: (X == x) & ((y - yy) ** 2 + (Z - EZ) ** 2 <= 3.2))
            if k % 3 == 1 and k > 3:
                L = 2 + (k * 7) % 5
                bb.fill(x, yy - 2 - L, EZ + (k % 2), x, yy - 2, EZ + (k % 2), "minecraft:hay_block" if k % 2 else "minecraft:yellow_terracotta")
        hx = CX + s * 22
        fill_shape(hx - 2, ay - 9, EZ - 2, hx + 2, ay - 4, EZ + 2, lambda X, y, Z, hx=hx: ((X - hx) ** 2 + (Z - EZ) ** 2) <= 3.5)
        for f in range(-1, 2):
            bb.fill(hx + s, ay - 13, EZ + f, hx + s, ay - 10, EZ + f, "minecraft:bamboo_block[axis=y]")
    # the hood: a cone of straw with a dark hollow face (facing south, toward the shrine)
    hy0 = y0 + 28
    for k in range(18):
        r = 6.2 - k * 0.33
        fill_shape(CX - 7, hy0 + k, EZ - 7, CX + 7, hy0 + k, EZ + 7, lambda X, y, Z, r=r: ((X - CX) ** 2 + (Z - EZ) ** 2) <= r * r)
    bb.fill_where(CX - 4, hy0 + 2, EZ + 1, CX + 4, hy0 + 9, EZ + 7,
                  lambda X, y, Z: ((X - CX) / 3.6) ** 2 + ((y - hy0 - 5) / 3.6) ** 2 <= 1, "minecraft:black_concrete")
    bb.fill_where(CX - 3, hy0 + 3, EZ, CX + 3, hy0 + 8, EZ + 2,
                  lambda X, y, Z: ((X - CX) / 3) ** 2 + ((y - hy0 - 5) / 3) ** 2 <= 1, "minecraft:black_concrete")
    for s in (-1, 1):
        bb.set(CX + s * 2, hy0 + 6, EZ + 5, "minecraft:shroomlight")
    # nails and spikes stuck through the straw (iron bars poking out)
    rng = np.random.default_rng(6509)
    for _ in range(40):
        yy = int(rng.integers(y0 + 8, hy0 + 10))
        a = rng.uniform(0, 6.283)
        r = 9 if yy < y0 + 26 else 7
        x, z = CX + int(round(r * math.cos(a))), EZ + int(round(r * 0.7 * math.sin(a)))
        bb.set(x, yy, z, "minecraft:iron_bars")
        bb.set(x + int(round(math.cos(a))), yy, z + int(round(math.sin(a))), "minecraft:iron_bars")
    # a rope belt with paper streamers (shide)
    bb.fill_where(CX - 9, y0 + 18, EZ - 7, CX + 9, y0 + 18, EZ + 7,
                  lambda X, y, Z: (((X - CX) / 6.6) ** 2 + ((Z - EZ) / 4.3) ** 2 <= 1.3) & (((X - CX) / 6.6) ** 2 + ((Z - EZ) / 4.3) ** 2 > 0.8),
                  "minecraft:brown_wool")
    for dx in (-4, 0, 4):
        bb.fill(CX + dx, y0 + 15, EZ + 6, CX + dx, y0 + 17, EZ + 6, "minecraft:white_wool")


def shrine_hall(bb):
    """Dark timber hall on a stone platform, curved irimoya roof, veranda, the altar with giant tarot cards."""
    x1, x2, z1, z2 = CX - 12, CX + 12, HZ0, HZ1
    y = 2
    bb.fill(x1 - 2, y - 3, z1 - 2, x2 + 2, y, z2 + 2, "minecraft:stone_bricks")
    bb.fill(x1 - 2, y, z1 - 2, x2 + 2, y, z2 + 2, "minecraft:dark_oak_planks")
    bb.fill(x1, y + 1, z1, x2, y + 8, z2, "minecraft:dark_oak_planks")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 8, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 1, z, x, y + 8, z, "minecraft:stripped_dark_oak_log[axis=y]")
            if x + 2 <= x2:
                bb.fill(x + 1, y + 2, z, x + 3, y + 6, z, "minecraft:yellow_terracotta")
                bb.fill(x + 2, y + 4, z, x + 2, y + 6, z, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=true]" if z == z1 else "minecraft:dark_oak_trapdoor[facing=south,half=bottom,open=true]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 1, z, x, y + 8, z, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(CX - 2, y + 1, z2, CX + 2, y + 5, z2, AIR)
    for x in (x1 - 2, x2 + 2):
        for z in range(z1 - 2, z2 + 3, 4):
            bb.fill(x, y + 1, z, x, y + 7, z, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(x1 + 1, y + 9, z1 + 1, x2 - 1, y + 9, z2 - 1, "minecraft:dark_oak_planks")
    A.curved_roof(bb, x1 - 4, z1 - 4, x2 + 4, z2 + 4, y + 9, 9, style="irimoya", pal=SHRINE)
    # inside: altar dais with giant tarot cards, rows of candles, doll shelves, Hawkins' card table
    bb.fill(CX - 8, y + 1, z1 + 1, CX + 8, y + 1, z1 + 4, "minecraft:dark_oak_planks")
    for k, dx in enumerate((-6, -2, 2, 6)):
        bb.fill(CX + dx - 1, y + 2, z1 + 2, CX + dx + 1, y + 6, z1 + 2, "minecraft:white_concrete")
        bb.fill(CX + dx - 1, y + 2, z1 + 3, CX + dx + 1, y + 2, z1 + 3, "minecraft:dark_oak_slab[type=bottom]")
        sym = ["minecraft:black_concrete", "minecraft:red_concrete", "minecraft:purple_concrete", "minecraft:yellow_concrete"][k]
        bb.set(CX + dx, y + 4, z1 + 3, sym); bb.set(CX + dx, y + 5, z1 + 3, sym if k % 2 else "minecraft:white_concrete")
        bb.set(CX + dx, y + 3, z1 + 3, sym if k % 2 == 0 else "minecraft:white_concrete")
    for x in range(x1 + 2, x2 - 1, 2):
        bb.set(x, y + 2, z1 + 5, "minecraft:candle[candles=3,lit=true]" if x % 4 else "minecraft:white_candle[candles=4,lit=true]")
    for z in range(z1 + 7, z2 - 2, 3):
        for x in (x1 + 1, x2 - 1):
            bb.set(x, y + 3, z, "minecraft:dark_oak_slab[type=top]")
            bb.set(x, y + 4, z, "minecraft:hay_block"); bb.set(x, y + 5, z, "minecraft:candle[candles=2,lit=true]")
    tx, tz = CX, (z1 + z2) // 2 + 2
    bb.fill(tx - 1, y + 1, tz, tx + 1, y + 1, tz, "minecraft:dark_oak_fence")
    bb.fill(tx - 1, y + 2, tz, tx + 1, y + 2, tz, "minecraft:dark_oak_pressure_plate")
    bb.set(tx, y + 1, tz + 2, "minecraft:dark_oak_stairs[facing=north]")
    for (a, b) in ((-1, 0), (1, 0)):
        bb.set(tx + a, y + 3, tz + b, "minecraft:white_carpet")
    for z in range(z1 + 6, z2 - 1, 6):
        bb.set(CX, y + 8, z, "minecraft:lantern[hanging=true]")
    return y


def torii(bb, z, y, w=7, h=8, col="minecraft:red_concrete"):
    for s in (-1, 1):
        bb.fill(CX + s * (w // 2), y, z, CX + s * (w // 2), y + h, z, col)
    bb.fill(CX - w // 2 - 2, y + h + 1, z, CX + w // 2 + 2, y + h + 1, z, "minecraft:black_concrete")
    bb.set(CX - w // 2 - 2, y + h + 2, z, "minecraft:black_concrete"); bb.set(CX + w // 2 + 2, y + h + 2, z, "minecraft:black_concrete")
    bb.fill(CX - w // 2 - 1, y + h - 1, z, CX + w // 2 + 1, y + h - 1, z, col)
    bb.set(CX, y + h, z, col)


def approach(bb):
    """Boardwalk from the south edge over the swamp to the hall, torii every 9 blocks, stone lanterns, a rope with
    paper streamers at the hall end."""
    y = 2
    for z in range(HZ1 + 3, N - 10):
        bb.fill(CX - 2, y, z, CX + 2, y, z, "minecraft:spruce_planks")
        bb.fill(CX - 2, y + 1, z, CX + 2, y + 6, z, AIR)
        if z % 4 == 0:
            for s in (-3, 3):
                bb.fill(CX + s, -3, z, CX + s, y + 1, z, "minecraft:stripped_spruce_log[axis=y]")
    for z in range(HZ1 + 8, N - 14, 9):
        torii(bb, z, y + 1)
    for z in range(HZ1 + 12, N - 14, 18):
        for s in (-6, 6):
            A.stone_lantern(bb, CX + s, hy(CX + s, z) + 1, z)
    # steps down from the boardwalk to the ground at the south end
    bb.fill(CX - 2, 1, N - 10, CX + 2, 1, N - 8, "minecraft:spruce_slab[type=top]")


def hut_and_camp(bb, rng):
    """Fortune teller's hut on stilts (west) and the crew camp (east)."""
    hx, hz = 26, 54
    y = 5
    for (a, b) in ((0, 0), (8, 0), (0, 7), (8, 7)):
        bb.fill(hx + a, hy(hx + a, hz + b) - 1, hz + b, hx + a, y, hz + b, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(hx - 1, y, hz - 1, hx + 9, y, hz + 8, "minecraft:dark_oak_planks")
    bb.fill(hx, y + 1, hz, hx + 8, y + 5, hz + 7, "minecraft:spruce_planks")
    bb.fill(hx + 1, y + 1, hz + 1, hx + 7, y + 4, hz + 6, AIR)
    bb.fill(hx + 4, y + 1, hz + 7, hx + 4, y + 2, hz + 7, AIR)
    for x in (hx + 2, hx + 6):
        bb.set(x, y + 3, hz, "minecraft:purple_stained_glass_pane"); bb.set(x, y + 3, hz + 7, "minecraft:purple_stained_glass_pane")
    P.gable_roof(bb, hx - 1, hz - 1, hx + 9, hz + 8, y + 6, "minecraft:dark_oak_stairs", ridge="minecraft:dark_oak_slab[type=bottom]",
                 ridge_axis="x", gable_fill="minecraft:spruce_planks", overhang=1)
    bb.set(hx + 4, y + 1, hz + 3, "minecraft:dark_oak_fence"); bb.set(hx + 4, y + 2, hz + 3, "minecraft:tinted_glass")
    bb.set(hx + 3, y + 1, hz + 3, "minecraft:dark_oak_stairs[facing=east]"); bb.set(hx + 5, y + 1, hz + 3, "minecraft:dark_oak_stairs[facing=west]")
    bb.set(hx + 1, y + 1, hz + 1, "minecraft:bookshelf"); bb.set(hx + 7, y + 1, hz + 1, "minecraft:candle[candles=4,lit=true]")
    bb.set(hx + 7, y + 1, hz + 6, "minecraft:purple_bed[facing=north,part=foot]") if False else bb.set(hx + 7, y + 1, hz + 6, "minecraft:barrel[facing=up]")
    for k in range(y - 1):
        bb.set(hx + 4, hy(hx + 4, hz + 9 + k) + 1, hz + 9 + k, "minecraft:spruce_stairs[facing=north]") if False else None
    bb.fill(hx + 4, 1, hz + 8, hx + 4, y, hz + 8, "minecraft:ladder[facing=south]")
    # crew camp: three tents round a fire, east of the boardwalk
    cx, cz = 96, 60
    yy = hy(cx, cz)
    bb.set(cx, yy + 1, cz, "minecraft:campfire[lit=true]")
    for k, (dx, dz) in enumerate(((-7, -3), (4, -7), (2, 4))):
        x, z = cx + dx, cz + dz
        ty = hy(x + 2, z + 2)
        for s in range(3):
            bb.fill(x, ty + 1 + s, z + s, x + 5, ty + 1 + s, z + s, "minecraft:brown_wool" if k % 2 else "minecraft:yellow_wool")
            bb.fill(x, ty + 1 + s, z + 4 - s, x + 5, ty + 1 + s, z + 4 - s, "minecraft:brown_wool" if k % 2 else "minecraft:yellow_wool")
        bb.fill(x + 1, ty + 1, z + 1, x + 4, ty + 2, z + 3, AIR)
        bb.set(x + 2, ty + 1, z + 2, "minecraft:brown_bed[facing=east,part=foot]"); bb.set(x + 3, ty + 1, z + 2, "minecraft:brown_bed[facing=east,part=head]")
    for (dx, dz) in ((-3, 3), (3, -2)):
        bb.set(cx + dx, yy + 1, cz + dz, "minecraft:stripped_spruce_log[axis=x]")
    return (hx, hz, y)


def design():
    bb = BigBuild(seed=6500, y_min=-8, y_max=90)
    rng = np.random.default_rng(6510)
    terrain(bb)
    approach(bb)
    y = shrine_hall(bb)
    effigy(bb)
    hut = hut_and_camp(bb, rng)
    trees = []
    for _ in range(600):
        if len(trees) >= 34:
            break
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if _LAND(np.array(float(x)), np.array(float(z))) < 5 or (abs(x - CX) < 26 and z < 62) or abs(x - CX) < 9:
            continue
        if (18 < x < 40 and 46 < z < 66) or (84 < x < 108 and 48 < z < 72) or any(math.hypot(x - a, z - b) < 7 for (a, b) in trees):
            continue
        trees.append((x, z))
        dead_tree(bb, x, z, int(rng.integers(8, 17)), rng, dolls=int(rng.integers(0, 3)))
    # stone lanterns flanking the hall, hanging dolls ring
    for s in (-1, 1):
        A.stone_lantern(bb, CX + s * 16, 3, HZ1 + 4)
    return bb, [], y, hut


def build():
    bb, audit, y, hut = design()
    b = to_canvas(bb)
    steady(b)
    b.npc(CX, y + 1, HZ0 + 8, "hawkins", True)
    b.chest(CX + 8, y + 2, HZ0 + 2, "medium", "south")
    b.chest(hut[0] + 1, hut[2] + 1, hut[1] + 6, "medium", "east")
    return b, 0
