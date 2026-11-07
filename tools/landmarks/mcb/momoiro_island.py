"""Momoiro Island v2 in the Kamabakka Kingdom, redesigned with the Minecraft Builder skill: the lurid pink island where
Sanji was flung during the separation and spent two years learning the Attack Cuisine of the okama.

Everything is pink: cherry trees in full bloom, pink petals on the lawns, hydrangea-like flower beds, heart topiaries,
giant pink flowers taller than a house. In the middle the Queen's palace (Ivankov's): a pink keep of three storeys
with the ballroom on the first floor, the throne room above and the Queen's rooms on top, a gabled roof, four round
corner towers with heart-shaped crowns, a heart window over the entrance, a grand stair and a heart fountain in the
forecourt. East of it the Okama Academy of Attack Cuisine: the training kitchen and the dance hall (a checkered floor,
mirrors, the music corner); round them pink cottages with frilly interiors, a heart pond with a little bridge, and a
landing pier on the south shore. 160 x 160. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, glyph, table, lamp_post, tier, wing_floor
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "momoiro_island"
TITLE = "Momoiro Island (Kamabakka Kingdom)"
CUTS = [3, 9, 15, 21]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
TY = 2
PAL = (62, 40, 98, 66)           # the palace keep x1, z1, x2, z2
ACAD = (108, 56, 132, 80)        # academy
POND = (52, 100)
PINK = ["minecraft:pink_terracotta", "minecraft:pink_concrete", "minecraft:magenta_terracotta"]
WHITE = "minecraft:white_concrete"
TRIM = "minecraft:quartz_block"
HEART = [".##.##.",
         "#######",
         "#######",
         ".#####.",
         "..###..",
         "...#..."]
_ISLE = NT.outline(80, 78, 64, 6610, wobble=0.08)
GRASS = [("minecraft:grass_block", 0.72), ("minecraft:moss_block", 0.08), ("minecraft:rooted_dirt", 0.08), ("minecraft:podzol", 0.06),
         ("minecraft:coarse_dirt", 0.06)]
SAND = [("minecraft:sand", 0.75), ("minecraft:white_concrete_powder", 0.1), ("minecraft:clay", 0.15)]
PAVE = [("minecraft:pink_terracotta", 0.35), ("minecraft:white_terracotta", 0.3), ("minecraft:smooth_quartz", 0.2),
        ("minecraft:cherry_planks", 0.15)]


def shore(X, Z):
    return _ISLE(X, Z)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    roll = TY + NT.fbm(X, Z, 6611, 22) * 4 - 1.2
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, roll)
    flat = np.zeros_like(X)
    for (x1, z1, x2, z2) in ((PAL[0] - 12, PAL[1] - 10, PAL[2] + 12, PAL[3] + 22), (ACAD[0] - 4, ACAD[1] - 4, ACAD[2] + 4, ACAD[3] + 4)):
        dx = np.maximum(np.maximum(x1 - X, X - x2), 0)
        dz = np.maximum(np.maximum(z1 - Z, Z - z2), 0)
        flat = np.maximum(flat, np.clip(1 - np.hypot(dx, dz) / 8.0, 0, 1))
    h = np.where(d >= 10, h * (1 - flat) + TY * flat, h)
    return np.where(d < 1.5, -1, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SHORE = _height(X_, Z_).astype(int), shore(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def paved(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (X >= PAL[0] - 8) & (X <= PAL[2] + 8) & (Z >= PAL[3]) & (Z <= PAL[3] + 18)          # forecourt
    m |= (np.abs(X - 80) <= 2) & (Z > PAL[3]) & (Z < N)                                      # avenue to the pier
    m |= (np.abs(Z - (PAL[3] + 9)) <= 1.5) & (X > PAL[2]) & (X < ACAD[0] + 12)              # to the academy
    m |= (np.abs(np.hypot(X - 80, Z - 78) - 44) <= 1.3)                                       # ring lane
    return m


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 6620, mask=lambda X, Z: land(X, Z) & (sh(X, Z) < 8), under="minecraft:sandstone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRASS, 6621, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~paved(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 6622, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & paved(X, Z), core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


def heart(bb, x, y, z, block, axis="x"):
    glyph(bb, HEART, x - 3, y, z, block, axis=axis) if axis == "x" else glyph(bb, HEART, x, y, z - 3, block, axis="z")


# ------------------------------------------------------------------ the Queen's palace
def palace(bb, tracker, audit):
    x1, z1, x2, z2 = PAL
    fh = 7
    top = tier(bb, x1, z1, x2, z2, TY, 3, fh, PINK, "minecraft:pink_stained_glass_pane", "minecraft:quartz_stairs",
               pilaster=TRIM, band=WHITE, plate="minecraft:cherry_planks", weights=[0.6, 0.25, 0.15], every=3, pil_every=6, win_h=3)
    bb.fill(x1 - 1, TY - 3, z1 - 1, x2 + 1, TY, z2 + 1, "minecraft:polished_diorite") if False else None
    bb.fill(x1 - 2, TY - 3, z1 - 2, x2 + 2, TY, z2 + 2, "minecraft:smooth_quartz")
    bb.fill(x1, TY, z1, x2, TY, z2, "minecraft:cherry_planks")
    # gabled pink-and-white roof with a ridge of quartz
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:cherry_stairs", ridge_axis="x", gable_fill=PINK[0], overhang=1)
    # ground floor: the ballroom (one big hall with a checker floor), stairs up on the west
    by = TY + 1
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            bb.set(x, TY, z, "minecraft:pink_concrete" if (x // 2 + z // 2) % 2 else "minecraft:white_concrete")
    P.furnish_room(bb, (x1 + 5, z1 + 1, x2 - 1, z2 - 1), by, kind="living", height=fh - 1, seed=6630, wood="cherry", tracker=tracker,
                   doors=[(80, z2 - 1), (x1 + 2, z1 + 2)])
    txt, ok = P.audit_props(bb, [(x1 + 5, z1 + 1, x2 - 1, z2 - 1)], by, fh - 1)
    if not ok:
        audit.append(txt)
    for (cx, cz) in ((72, 53), (88, 53)):
        bb.fill(cx, by + 3, cz, cx, TY + fh - 1, cz, "minecraft:iron_chain[axis=y]")
        bb.fill_where(cx - 2, by + 2, cz - 2, cx + 2, by + 2, cz + 2, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - 1.6) < 0.6, "minecraft:gold_block")
        for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            bb.set(cx + dx, by + 1, cz + dz, "minecraft:lantern[hanging=true]")
    # stairs between floors in the west bay
    for f in range(2):
        y0 = TY + f * fh
        for i in range(fh):
            bb.fill(x1 + 1, y0 + 1 + i, z1 + 2 + i, x1 + 3, y0 + 1 + i, z1 + 2 + i, "minecraft:cherry_stairs[facing=south,half=bottom]")
            bb.fill(x1 + 1, y0 + 2 + i, z1 + 2 + i, x1 + 3, y0 + fh + 1, z1 + 2 + i, AIR)
    # first floor: the throne room (Queen Ivankov's) with corridor rooms behind
    ty1 = TY + fh + 1
    bb.fill(x1 + 5, ty1 - 1, z1 + 1, x2 - 1, ty1 - 1, z2 - 1, "minecraft:cherry_planks")
    bb.fill(x1 + 22, ty1 - 1, z1 + 4, x2 - 4, ty1 - 1, z2 - 4, "minecraft:red_wool") if False else None
    rooms = wing_floor(bb, x1 + 5, z1 + 1, x2 - 1, z1 + 10, ty1, fh - 1, PINK[0], 6631, tracker, ["bedroom", "living", "storage"],
                       corridor="x", cw=3, wood="cherry", audit=audit)
    # the throne at the south end of the hall
    tx, tz = 80, z2 - 4
    bb.fill(tx - 3, ty1, tz - 1, tx + 3, ty1, tz + 2, "minecraft:quartz_block")
    bb.set(tx, ty1 + 1, tz + 1, "minecraft:quartz_stairs[facing=north,half=bottom]")
    bb.fill(tx - 1, ty1 + 1, tz + 2, tx + 1, ty1 + 4, tz + 2, "minecraft:pink_wool")
    heart(bb, tx, ty1 + 6, tz + 2, "minecraft:red_concrete")
    bb.fill(tx, ty1, z1 + 12, tx, ty1, tz - 2, "minecraft:pink_carpet") if False else None
    bb.fill(tx - 1, ty1, z1 + 13, tx + 1, ty1, tz - 2, "minecraft:magenta_carpet")
    # second floor: the Queen's rooms
    ty2 = TY + 2 * fh + 1
    rooms2 = wing_floor(bb, x1 + 5, z1 + 1, x2 - 1, z2 - 1, ty2, fh - 1, PINK[0], 6632, tracker, ["bedroom", "living", "library", "bedroom"],
                        corridor="x", cw=3, wood="cherry", audit=audit)
    # the entrance: a porch with a heart window, a grand stair
    ex = 80
    bb.fill(ex - 3, TY + 1, z2, ex + 3, TY + 5, z2, AIR)
    for x in (ex - 1, ex + 1):
        bb.set(x, TY + 1, z2, f"minecraft:cherry_door[facing=south,half=lower,hinge={'left' if x < ex else 'right'}]")
        bb.set(x, TY + 2, z2, f"minecraft:cherry_door[facing=south,half=upper,hinge={'left' if x < ex else 'right'}]")
    bb.set(ex, TY + 1, z2, "minecraft:cherry_door[facing=south,half=lower,hinge=left]")
    bb.set(ex, TY + 2, z2, "minecraft:cherry_door[facing=south,half=upper,hinge=left]")
    bb.fill(ex - 3, TY + 3, z2, ex + 3, TY + 5, z2, PINK[1])
    for x in (ex - 4, ex + 4):
        bb.fill(x, TY + 1, z2 + 1, x, TY + 8, z2 + 4, TRIM) if False else None
        bb.fill(x, TY + 1, z2 + 4, x, TY + 8, z2 + 4, "minecraft:quartz_pillar[axis=y]")
    bb.fill(ex - 5, TY + 9, z2 + 1, ex + 5, TY + 9, z2 + 5, TRIM)
    bb.fill(ex - 5, TY + 10, z2 + 5, ex + 5, TY + 10, z2 + 5, "minecraft:quartz_slab[type=bottom]")
    heart(bb, ex, TY + 20, z2 + 1, "minecraft:red_stained_glass")
    for i in range(3):
        bb.fill(ex - 4 + i, TY - i, z2 + 5 + i, ex + 4 - i, TY - i, z2 + 5 + i, "minecraft:quartz_stairs[facing=south,half=bottom]") if False else None
    bb.fill(ex - 5, TY, z2 + 1, ex + 5, TY, z2 + 6, "minecraft:smooth_quartz")
    bb.fill(ex - 1, TY, z2 + 1, ex + 1, TY, z2 + 6, "minecraft:magenta_wool")
    # four round corner towers with heart crowns
    for (cx, cz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        r = 4
        th = top + 10
        bb.fill_where(cx - r, TY - 2, cz - r, cx + r, th, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 0.4, PINK[1])
        bb.fill_where(cx - r, TY + 1, cz - r, cx + r, th - 1, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.8, AIR)
        bb.fill_where(cx - r, TY + 1, cz - r, cx + r, th, cz + r, lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 0.4) & ((Y - TY) % 7 == 0), WHITE)
        for yy in range(TY + 3, th - 2, 7):
            for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
                bb.fill(cx + dx, yy, cz + dz, cx + dx, yy + 2, cz + dz, "minecraft:pink_stained_glass_pane")
        for f in range(1, 3):
            bb.fill_where(cx - r, TY + f * fh, cz - r, cx + r, TY + f * fh, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.8,
                          "minecraft:cherry_planks")
        bb.fill_where(cx - r - 1, th, cz - r - 1, cx + r + 1, th, cz + r + 1, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 1.3, TRIM)
        bb.fill_where(cx - r - 1, th + 1, cz - r - 1, cx + r + 1, th + 1, cz + r + 1,
                      lambda X, Y, Z: (np.abs(np.hypot(X - cx, Z - cz) - (r + 0.8)) < 0.6) & ((X + Z) % 2 == 0), TRIM)
        heart(bb, cx, th + 7, cz, "minecraft:red_concrete")
        heart(bb, cx, th + 7, cz, "minecraft:red_concrete", axis="z")
    return top


def heart_fountain(bb, cx, cz):
    for r, (block, y) in enumerate((("minecraft:smooth_quartz", TY), )):
        pass
    mask = lambda X, Z, s: ((((X - cx) / s) ** 2 + ((Z - cz) / s) ** 2 - 1) ** 3 - ((X - cx) / s) ** 2 * (-(Z - cz) / s) ** 3) <= 0
    bb.fill_where(cx - 9, TY, cz - 9, cx + 9, TY + 1, cz + 9, lambda X, Y, Z: mask(X, Z, 8.0), "minecraft:smooth_quartz")
    bb.fill_where(cx - 9, TY + 1, cz - 9, cx + 9, TY + 1, cz + 9, lambda X, Y, Z: mask(X, Z, 7.0), "minecraft:water")
    bb.fill(cx, TY + 1, cz, cx, TY + 4, cz, "minecraft:quartz_pillar[axis=y]")
    bb.set(cx, TY + 5, cz, "minecraft:water")


def heart_pond(bb, cx, cz):
    mask = lambda X, Z, s: ((((X - cx) / s) ** 2 + ((Z - cz) / s) ** 2 - 1) ** 3 - ((X - cx) / s) ** 2 * (-(Z - cz) / s) ** 3) <= 0
    yb = hy(cx, cz)
    bb.fill_where(cx - 16, yb - 3, cz - 16, cx + 16, yb, cz + 16, lambda X, Y, Z: mask(X, Z, 13.0) & (Y == yb - 3), "minecraft:clay")
    bb.fill_where(cx - 16, yb - 2, cz - 16, cx + 16, yb, cz + 16, lambda X, Y, Z: mask(X, Z, 13.0), "minecraft:water")
    bb.fill_where(cx - 16, yb + 1, cz - 16, cx + 16, yb + 3, cz + 16, lambda X, Y, Z: mask(X, Z, 13.0), AIR)
    for (dx, dz) in ((-5, -2), (4, 1), (-2, 5), (6, -4)):
        bb.set(cx + dx, yb + 1, cz + dz, "minecraft:lily_pad")
    # a little arched bridge across
    for i in range(-11, 12):
        y = yb + 1 + int(round(2 * math.cos(i / 11 * math.pi / 2)))
        bb.fill(cx + i, y, cz - 1, cx + i, y, cz + 1, "minecraft:cherry_slab[type=top]")
        bb.set(cx + i, y + 1, cz - 2, "minecraft:cherry_fence") if i % 2 == 0 else None
        bb.set(cx + i, y + 1, cz + 2, "minecraft:cherry_fence") if i % 2 == 0 else None
    return (cx - 16, cz - 16, cx + 16, cz + 16)


# ------------------------------------------------------------------ the Okama Academy
def academy(bb, tracker, audit):
    x1, z1, x2, z2 = ACAD
    fh = 6
    top = tier(bb, x1, z1, x2, z2, TY, 2, fh, ["minecraft:white_terracotta", "minecraft:pink_terracotta", "minecraft:calcite"],
               "minecraft:magenta_stained_glass_pane", "minecraft:cherry_stairs", pilaster="minecraft:stripped_cherry_log",
               band="minecraft:magenta_concrete", plate="minecraft:cherry_planks", weights=[0.6, 0.25, 0.15], every=3, pil_every=6)
    P.hip_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:cherry_stairs")
    bb.fill(x1 - 1, TY - 3, z1 - 1, x2 + 1, TY, z2 + 1, "minecraft:smooth_quartz")
    # ground: the training kitchen (two long counters, stoves, the Attack Cuisine drill floor)
    ky = TY + 1
    bb.fill(x1 + 1, TY, z1 + 1, x2 - 1, TY, z2 - 1, "minecraft:white_terracotta")
    for z in (z1 + 4, z1 + 10):
        for x in range(x1 + 3, x2 - 2):
            bb.set(x, ky, z, ("minecraft:smoker[facing=south]", "minecraft:furnace[facing=south]", "minecraft:cherry_planks",
                              "minecraft:cauldron", "minecraft:cherry_planks")[(x - x1) % 5])
        bb.fill(x1 + 3, ky + 1, z, x2 - 3, ky + 1, z, "minecraft:cherry_slab[type=bottom]") if False else None
    for x in range(x1 + 4, x2 - 3, 4):
        bb.set(x, ky + 4, z1 + 7, "minecraft:lantern[hanging=true]")
    P.furnish_room(bb, (x1 + 1, z1 + 13, x2 - 1, z2 - 1), ky, kind="kitchen", height=fh - 1, seed=6640, wood="cherry", tracker=tracker,
                   doors=[(x1 + 2, z2 - 1), ((x1 + x2) // 2, z2 - 1)])
    txt, ok = P.audit_props(bb, [(x1 + 1, z1 + 13, x2 - 1, z2 - 1)], ky, fh - 1)
    if not ok:
        audit.append(txt)
    # door on the west, toward the palace
    bb.fill(x1, TY + 1, (z1 + z2) // 2, x1, TY + 2, (z1 + z2) // 2 + 1, AIR)
    bb.set(x1, TY + 1, (z1 + z2) // 2, "minecraft:cherry_door[facing=west,half=lower,hinge=left]")
    bb.set(x1, TY + 2, (z1 + z2) // 2, "minecraft:cherry_door[facing=west,half=upper,hinge=left]")
    bb.set(x1, TY + 1, (z1 + z2) // 2 + 1, "minecraft:cherry_door[facing=west,half=lower,hinge=right]")
    bb.set(x1, TY + 2, (z1 + z2) // 2 + 1, "minecraft:cherry_door[facing=west,half=upper,hinge=right]")
    # ladder up
    bb.fill(x2 - 1, TY + 1, z1 + 1, x2 - 1, TY + fh, z1 + 1, "minecraft:ladder[facing=west]")
    bb.set(x2 - 1, TY + fh, z1 + 1, "minecraft:ladder[facing=west]")
    # upper: the dance hall (checker floor, mirrors = glass walls with quartz, the music corner)
    dy = TY + fh + 1
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            bb.set(x, dy - 1, z, "minecraft:magenta_concrete" if (x + z) % 2 else "minecraft:white_concrete")
    bb.set(x2 - 1, dy - 1, z1 + 1, AIR)
    bb.fill(x1 + 1, dy, z2 - 1, x2 - 1, dy + 3, z2 - 1, "minecraft:glass_pane") if False else None
    bb.set(x1 + 2, dy, z1 + 2, "minecraft:jukebox")
    bb.set(x1 + 3, dy, z1 + 2, "minecraft:note_block")
    bb.set(x1 + 2, dy, z1 + 3, "minecraft:note_block")
    for x in range(x1 + 4, x2 - 2, 5):
        bb.set(x, dy + 3, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    bb.fill((x1 + x2) // 2, dy + 3, (z1 + z2) // 2 - 2, (x1 + x2) // 2, dy + 3, (z1 + z2) // 2 + 2, "minecraft:amethyst_block")
    heart(bb, (x1 + x2) // 2, top + 9, z2 + 1, "minecraft:magenta_concrete")
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


# ------------------------------------------------------------------ gardens
def giant_flower(bb, x, z, h, petal, rng):
    y = hy(x, z) + 1
    bb.fill(x, y, z, x, y + h, z, "minecraft:green_concrete")
    for k in range(3):
        ly = y + 3 + k * 4
        if ly < y + h - 3:
            dx, dz = ((1, 0), (0, 1), (-1, 0))[k]
            bb.set(x + dx, ly, z + dz, "minecraft:lime_concrete")
            bb.set(x + 2 * dx, ly + 1, z + 2 * dz, "minecraft:lime_concrete")
    cy = y + h
    bb.fill_where(x - 4, cy, z - 4, x + 4, cy + 1, z + 4,
                  lambda X, Y, Z: (np.hypot(X - x, Z - z) <= 4.2) & (np.hypot(X - x, Z - z) > 1.2) &
                                  ((np.round(np.degrees(np.arctan2(Z - z, X - x))) % 72) < 54) & ((Y == cy) | (np.hypot(X - x, Z - z) > 2.8)),
                  petal)
    bb.fill(x - 1, cy, z - 1, x + 1, cy, z + 1, "minecraft:yellow_concrete")
    bb.set(x, cy + 1, z, "minecraft:yellow_concrete")


def topiary(bb, x, z):
    y = hy(x, z) + 1
    bb.fill(x, y, z, x, y + 1, z, "minecraft:cherry_log[axis=y]")
    glyph(bb, HEART, x - 3, y + 8, z, "minecraft:flowering_azalea_leaves[persistent=true]")
    glyph(bb, HEART, x - 3, y + 8, z + 1, "minecraft:azalea_leaves[persistent=true]")


def cottages(bb, tracker, audit, taken):
    PALS = [dict(walls=["minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:pink_concrete"], frame="minecraft:stripped_cherry_log",
                 base=["minecraft:smooth_quartz", "minecraft:calcite", "minecraft:diorite"], floor="minecraft:cherry_planks", wood="cherry",
                 chimney="minecraft:bricks", parapet="minecraft:smooth_quartz"),
            dict(walls=["minecraft:white_terracotta", "minecraft:magenta_terracotta", "minecraft:calcite"], frame="minecraft:stripped_birch_log",
                 base=["minecraft:smooth_quartz", "minecraft:calcite", "minecraft:diorite"], floor="minecraft:birch_planks", wood="birch",
                 chimney="minecraft:bricks", parapet="minecraft:smooth_quartz")]
    ROOFS = ["minecraft:cherry_stairs", "minecraft:red_nether_brick_stairs", "minecraft:purpur_stairs"]
    KINDS = [["living", "bedroom"], ["kitchen", "bedroom"], ["living", "storage"], ["bedroom", "library"]]
    k = 0
    for (ring, a) in [(r, a) for r in (37, 52) for a in range(0, 360, 14 if r > 40 else 20)]:
        cx, cz = 80 + ring * math.cos(math.radians(a)), 78 + ring * math.sin(math.radians(a))
        w, d = 9, 8
        sgn = 1 if ring < 44 else -1                  # doors face the ring lane
        vx, vz = sgn * math.cos(math.radians(a)), sgn * math.sin(math.radians(a))
        rot = (0 if vz > 0 else 2) if abs(vz) >= abs(vx) else (3 if vx > 0 else 1)
        mw, md = (w, d)
        fw, fd = (w, d) if rot % 2 == 0 else (d, w)
        x0, z0 = int(cx - fw / 2), int(cz - fd / 2)
        xs, zs = np.array([x0, x0 + fw, x0, x0 + fw]), np.array([z0, z0, z0 + fd, z0 + fd])
        if not land(xs, zs).all() or sh(xs, zs).min() < 9:
            continue
        if any(t[0] <= x0 + fw and x0 <= t[2] and t[1] <= z0 + fd and z0 <= t[3] for t in taken):
            continue
        m, top, au = house_module(seed_of("momo", x0, z0), mw, md, 2, ROOFS[k % 3], tracker, KINDS[k % 4], pal=PALS[k % 2], fh=4)
        audit += au
        place_house(bb, m, mw, md, x0, hy(x0 + fw // 2, z0 + fd // 2), z0, rot)
        taken.append((x0 - 2, z0 - 2, x0 + fw + 2, z0 + fd + 2))
        k += 1
    print("cottages:", k)


def cherry_tree(bb, x, z, rng):
    y = hy(x, z) + 1
    h = int(rng.integers(5, 9))
    bb.fill(x, y, z, x, y + h, z, "minecraft:cherry_log[axis=y]")
    for k in range(2):
        a = rng.uniform(0, 2 * math.pi)
        bx, bz = x + int(round(2 * math.cos(a))), z + int(round(2 * math.sin(a)))
        bb.set(bx, y + h - 1, bz, "minecraft:cherry_wood")
    r = float(rng.uniform(3, 4.5))
    bb.fill_where(x - 5, y + h - 2, z - 5, x + 5, y + h + 4, z + 5,
                  lambda X, Y, Z: (X - x) ** 2 + ((Y - (y + h + 1)) * 1.5) ** 2 + (Z - z) ** 2 + 2 * NT.noise(X + Y, Z, 6650, 2) <= r * r,
                  "minecraft:cherry_leaves[persistent=true]", only_empty=True)


def pier(bb):
    z_sea = next(z for z in range(PAL[3] + 10, N) if not land(np.array([80]), np.array([z]))[0])
    z_end = min(N - 14, z_sea + 16)
    bb.fill(78, 0, z_sea - 4, 82, 0, z_end, "minecraft:cherry_planks")
    for z in range(z_sea - 2, z_end + 1, 4):
        for x in (78, 82):
            bb.fill(x, -8, z, x, -1, z, "minecraft:stripped_cherry_log[axis=y]")
            bb.set(x, 1, z, "minecraft:cherry_fence")
    bb.fill(77, 1, z_end, 83, 1, z_end, "minecraft:cherry_fence")
    for x in (78, 82):
        bb.fill(x, 2, z_end, x, 3, z_end, "minecraft:cherry_fence")
        bb.set(x, 4, z_end, "minecraft:lantern[hanging=false]")
    heart(bb, 80, 9, z_end, "minecraft:pink_concrete")
    return (74, z_sea - 6, 86, N)


def design():
    bb = BigBuild(seed=6610, y_min=-14, y_max=72)
    tracker = P.PropTracker(6610)
    audit = []
    rng = np.random.default_rng(6610)
    terrain(bb)
    palace(bb, tracker, audit)
    heart_fountain(bb, 80, PAL[3] + 12)
    taken = [(PAL[0] - 8, PAL[1] - 8, PAL[2] + 8, PAL[3] + 18)]
    taken.append(academy(bb, tracker, audit))
    taken.append(heart_pond(bb, *POND))
    taken.append(pier(bb))
    cottages(bb, tracker, audit, taken)
    # heart topiaries along the forecourt
    for x in range(PAL[0] - 6, PAL[2] + 8, 8):
        if abs(x - 80) > 10:
            topiary(bb, x, PAL[3] + 17)
    # giant pink flowers and cherry trees over the lawns
    k = f = 0
    for _ in range(3000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 9 or paved(X, Z)[0]:
            continue
        if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
            continue
        if f < 12 and rng.random() < 0.25:
            giant_flower(bb, x, z, int(rng.integers(9, 16)), ("minecraft:pink_concrete", "minecraft:magenta_concrete", "minecraft:pink_wool")[f % 3], rng)
            taken.append((x - 5, z - 5, x + 5, z + 5))
            f += 1
        elif k < 46:
            cherry_tree(bb, x, z, rng)
            taken.append((x - 4, z - 4, x + 4, z + 4))
            k += 1
        if k >= 46 and f >= 12:
            break
    print("cherry trees:", k, "giant flowers:", f)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 6690, density=0.4,
              kinds=["minecraft:pink_petals[facing=north,flower_amount=4]", "minecraft:short_grass", "minecraft:pink_petals[facing=east,flower_amount=3]",
                     "minecraft:peony", "minecraft:allium", "minecraft:pink_tulip"],
              flowers=["minecraft:pink_tulip", "minecraft:allium", "minecraft:peony", "minecraft:lilac", "minecraft:azure_bluet"],
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~paved(X, Z))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.chest(PAL[2] - 3, TY + 2 * 7 + 1, PAL[1] + 2, "easy", "west")
    b.chest(ACAD[0] + 2, TY + 1, ACAD[1] + 2, "easy", "east")
    b.chest(POND[0] + 15, hy(POND[0] + 15, POND[1]) + 1, POND[1], "easy", "west")
    b.npc(80, TY + 7 + 2, PAL[3] - 5, "ivankov", False)
    return b, 0
