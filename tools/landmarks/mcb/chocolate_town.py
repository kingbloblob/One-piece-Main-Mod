"""Chocolate Town v2 (Chocolat Town on Cacao Island, Totto Land), redesigned with the Minecraft Builder skill.

A town where nearly everything is chocolate: the houses are chocolate with white frosting trim and cookie-brick
plinths, the streets are paved with cookie and chocolate, a canal of melted chocolate runs through the town under
arched cookie bridges, and you may eat the buildings (not the roofs: they keep the rain off). In the middle the town
square with a three-tier chocolate fountain and candy-striped lamp posts. On the square Café Caramel, Charlotte
Pudding's café of chocolate, marshmallow, jelly beans and almonds, with a patio of striped parasols; her house next
door. North the Sweets Factory with its candy-cane chimneys, where the wedding cake was baked. South the harbour with
candy-cane bollards and the Thousand Sunny moored. Lollipop trees, gumdrop bushes and candy-cane sprouts in the
gardens. ~176 x 176. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, house_module, place_house, lamp_post, table, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import shipstamp as SS

SID = "chocolate_town"
TITLE = "Chocolate Town (Cacao Island)"
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
TY = 2
CHOC = "onepiece:chocolate_block"
FROST = "onepiece:frosting_block"
COOK = "onepiece:cookie_bricks"
CANE = "onepiece:candy_cane_block"
MELT = "minecraft:brown_concrete"          # the melted chocolate in the canal and the fountain
PL = (88, 72, 14)                          # the town square
CANAL_Z = 102
CAFE = (52, 62, 66, 76)                     # x1, z1, x2, z2
FAC = (96, 24, 136, 46)
_ISLE = NT.outline(88, 88, 70, 15010, wobble=0.07)
GRASS = [("minecraft:grass_block", 0.62), ("onepiece:sugar_sand", 0.16), ("minecraft:moss_block", 0.08), ("minecraft:rooted_dirt", 0.06),
         ("minecraft:podzol", 0.08)]
SAND = [("onepiece:sugar_sand", 0.55), ("minecraft:sand", 0.35), ("minecraft:white_concrete_powder", 0.1)]
PAVE = [(COOK, 0.42), (CHOC, 0.22), ("minecraft:brown_terracotta", 0.14), ("minecraft:smooth_sandstone", 0.12), (FROST, 0.1)]
HOUSE_PALS = [
    dict(walls=[CHOC, CHOC, "minecraft:brown_terracotta"], frame=FROST, base=[COOK, COOK, "minecraft:smooth_sandstone"],
         floor="minecraft:dark_oak_planks", wood="dark_oak", chimney=CANE, parapet=FROST),
    dict(walls=["minecraft:brown_terracotta", CHOC, "minecraft:brown_concrete"], frame="minecraft:pink_concrete", base=[COOK, CHOC, COOK],
         floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks", parapet=FROST),
    dict(walls=["minecraft:white_terracotta", FROST, "minecraft:white_terracotta"], frame=CHOC, base=[COOK, COOK, CHOC],
         floor="minecraft:cherry_planks", wood="cherry", chimney=CANE, parapet=CHOC),
]
ROOFS = ["onepiece:chocolate_stairs", "onepiece:frosting_stairs", "onepiece:cookie_brick_stairs", "minecraft:red_nether_brick_stairs",
         "minecraft:pink_terracotta" if False else "minecraft:cherry_stairs"]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    roll = TY + NT.fbm(X, Z, 15011, 22) * 4 - 1.2
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, roll)
    town = np.clip((d - 10) / 10.0, 0, 1) * np.clip(1 - (np.hypot(X - 88, Z - 80) - 52) / 10.0, 0, 1)
    h = np.where(d >= 10, h * (1 - town) + TY * town, h)
    return np.where(d < 1.5, -1, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SHORE = _height(X_, Z_).astype(int), _ISLE(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def canal(X, Z):
    Z = np.asarray(Z, float); X = np.asarray(X, float)
    return np.abs(Z - (CANAL_Z + 3 * np.sin(X / 14.0))) <= 3.5


def street(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    r = np.hypot(X - PL[0], Z - PL[1])
    m = r <= PL[2]
    m |= np.abs(r - 30) <= 1.6                                        # ring street
    m |= (np.abs(X - PL[0]) <= 2) & (Z > PL[1]) & land(X, Z)           # the avenue to the harbour
    m |= (np.abs(X - PL[0]) <= 2) & (Z < PL[1]) & (Z > FAC[3])         # to the factory
    m |= (np.abs(Z - PL[1]) <= 1.6) & (r < 56)                         # east-west street
    cz = CANAL_Z + 3 * np.sin(X / 14.0)
    m |= ((np.abs(Z - cz) > 3.5) & (np.abs(Z - cz) <= 6.5)) & (sh(X, Z) > 9)   # canal quays
    return m


def terrain(bb):
    beach = lambda X, Z: land(X, Z) & (sh(X, Z) < 9)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 15020, mask=lambda X, Z: beach(X, Z), under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRASS, 15021, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & ~street(X, Z) & ~canal(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 15022, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & street(X, Z) & ~canal(X, Z),
             under="minecraft:sandstone", core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")
    # the chocolate canal: cookie-brick walls, a melted-chocolate surface two below the quay, opening to the sea at both ends
    cm = lambda X, Z: land(X, Z) & canal(X, Z)
    bb.fill_where(0, -4, 0, N - 1, TY + 8, N - 1, lambda X, Y, Z: cm(X, Z) & (Y >= 0), AIR)
    bb.fill_where(0, -4, 0, N - 1, -1, N - 1, lambda X, Y, Z: cm(X, Z), CHOC)
    bb.fill_where(0, -4, 0, N - 1, 0, N - 1, lambda X, Y, Z: cm(X, Z) & (Y == 0), MELT)
    wall = lambda X, Z: land(X, Z) & ~canal(X, Z) & (np.abs(Z - (CANAL_Z + 3 * np.sin(np.asarray(X, float) / 14.0))) <= 4.6)
    bb.fill_where(0, -2, 0, N - 1, TY, N - 1, lambda X, Y, Z: wall(X, Z) & (Y <= height(X, Z)), COOK)
    bb.fill_where(0, TY, 0, N - 1, TY, N - 1, lambda X, Y, Z: wall(X, Z) & (height(X, Z) == TY), FROST)


def cookie_bridge(bb, x):
    cz = int(round(CANAL_Z + 3 * math.sin(x / 14.0)))
    for dz in range(-6, 7):
        y = TY + int(round(2.2 * math.cos(dz / 6.5 * math.pi / 2)))
        bb.fill(x - 2, max(1, y - 1), cz + dz, x + 2, y, cz + dz, COOK)
        bb.fill(x - 2, y + 1, cz + dz, x + 2, y + 3, cz + dz, AIR)
        for s in (-3, 3):
            bb.set(x + s, y + 1, cz + dz, "onepiece:cookie_brick_wall")
            bb.set(x + s, y, cz + dz, COOK)
    for s in (-3, 3):
        for dz in (-6, 6):
            bb.set(x + s, TY + 2, cz + dz, "minecraft:lantern[hanging=false]")


def candy_lamp(bb, x, z):
    y = hy(x, z) + 1
    bb.fill(x, y, z, x, y + 3, z, f"{CANE}[axis=y]")
    bb.set(x, y + 4, z, "minecraft:lantern[hanging=false]")


def lollipop_tree(bb, x, z, col, rng):
    y = hy(x, z) + 1
    h = int(rng.integers(6, 9))
    bb.fill(x, y, z, x, y + h, z, "minecraft:white_concrete")
    cy = y + h + 3
    axis_x = rng.random() < 0.5
    R = 3.4
    def f(X, Y, Z):
        u = (X - x) if axis_x else (Z - z)
        v = Y - cy
        r = np.hypot(u, v)
        return r <= R
    if axis_x:
        bb.fill_where(x - 4, cy - 4, z, x + 4, cy + 4, z, lambda X, Y, Z: f(X, Y, Z), f"minecraft:{col}_concrete")
        bb.fill_where(x - 4, cy - 4, z, x + 4, cy + 4, z,
                      lambda X, Y, Z: f(X, Y, Z) & (((np.arctan2(Y - cy, X - x) + np.hypot(X - x, Y - cy) * 0.9) % 2.1) < 0.8), "minecraft:white_concrete")
    else:
        bb.fill_where(x, cy - 4, z - 4, x, cy + 4, z + 4, lambda X, Y, Z: f(X, Y, Z), f"minecraft:{col}_concrete")
        bb.fill_where(x, cy - 4, z - 4, x, cy + 4, z + 4,
                      lambda X, Y, Z: f(X, Y, Z) & (((np.arctan2(Y - cy, Z - z) + np.hypot(Z - z, Y - cy) * 0.9) % 2.1) < 0.8), "minecraft:white_concrete")


def fountain(bb):
    cx, cz, _ = PL
    y = TY
    for k, (r, h) in enumerate(((7, 2), (4, 4), (2, 6))):
        bb.fill_where(cx - r - 1, y + 1, cz - r - 1, cx + r + 1, y + h, cz + r + 1, lambda X, Y, Z, r=r: np.hypot(X - cx, Z - cz) <= r + 0.4,
                      COOK if k == 0 else CHOC)
        bb.fill_where(cx - r - 1, y + h, cz - r - 1, cx + r + 1, y + h, cz + r + 1, lambda X, Y, Z, r=r: np.hypot(X - cx, Z - cz) <= r - 0.6, MELT)
        bb.fill_where(cx - r - 1, y + h, cz - r - 1, cx + r + 1, y + h, cz + r + 1, lambda X, Y, Z, r=r: np.abs(np.hypot(X - cx, Z - cz) - r) < 0.6, FROST)
        # chocolate dripping over the rims
        for a in range(0, 360, 30 + 15 * k):
            dx, dz = int(round((r + 1) * math.cos(math.radians(a)))), int(round((r + 1) * math.sin(math.radians(a))))
            bb.fill(cx + dx, y + h - 1 - (a // 30) % 2, cz + dz, cx + dx, y + h, cz + dz, CHOC) if k > 0 else None
    bb.fill(cx, y + 7, cz, cx, y + 9, cz, CHOC)
    bb.set(cx, y + 10, cz, "onepiece:chocolate_slab[type=bottom]")
    for a in range(0, 360, 45):
        x, z = int(round(cx + 11 * math.cos(math.radians(a)))), int(round(cz + 11 * math.sin(math.radians(a))))
        candy_lamp(bb, x, z)


# ------------------------------------------------------------------ Café Caramel + Pudding's house
def cafe(bb, tracker, audit):
    x1, z1, x2, z2 = CAFE
    y = TY + 1
    fh = 5
    bb.fill(x1 - 1, y - 4, z1 - 1, x2 + 1, y - 1, z2 + 1, COOK)
    bb.fill(x1, y, z1, x2, y + 2 * fh, z2, CHOC)
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y + 2 * fh, z2 - 1, AIR)
    bb.fill(x1 + 1, y + fh, z1 + 1, x2 - 1, y + fh, z2 - 1, "minecraft:dark_oak_planks")
    # frosting trim at the corners and floor bands, scalloped frosting under the eaves
    for (cx, cz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.fill(cx, y, cz, cx, y + 2 * fh, cz, FROST)
    bb.fill_where(x1, y + fh, z1, x2, y + fh, z2, lambda X, Y, Z: (X == x1) | (X == x2) | (Z == z1) | (Z == z2), FROST)
    bb.fill_where(x1 - 1, y + 2 * fh, z1 - 1, x2 + 1, y + 2 * fh, z2 + 1, lambda X, Y, Z: (X == x1 - 1) | (X == x2 + 1) | (Z == z1 - 1) | (Z == z2 + 1), FROST)
    bb.fill_where(x1 - 1, y + 2 * fh - 1, z1 - 1, x2 + 1, y + 2 * fh - 1, z2 + 1,
                  lambda X, Y, Z: ((X == x1 - 1) | (X == x2 + 1) | (Z == z1 - 1) | (Z == z2 + 1)) & ((X + Z) % 2 == 0), "onepiece:frosting_slab[type=top]")
    # big arched windows on the square side (east) and jelly beans set in the walls
    for z in range(z1 + 2, z2 - 1, 4):
        for f in range(2):
            bb.fill(x2, y + f * fh + 1, z, x2, y + f * fh + 3, z + 1, "minecraft:orange_stained_glass_pane")
            bb.set(x2 + 1, y + f * fh, z, "onepiece:frosting_slab[type=top]"); bb.set(x2 + 1, y + f * fh, z + 1, "onepiece:frosting_slab[type=top]")
    beans = ["minecraft:red_concrete", "minecraft:lime_concrete", "minecraft:yellow_concrete", "minecraft:magenta_concrete", "minecraft:orange_concrete",
             "minecraft:light_blue_concrete"]
    k = 0
    for x in range(x1 + 1, x2):
        for z in (z1, z2):
            for yy in (y + 4, y + fh + 4):
                if (x * 7 + yy) % 3 == 0:
                    bb.set(x, yy, z, beans[k % 6]); k += 1
    # marshmallow roof: soft white and pink pillows, almonds on the ridge
    rt = y + 2 * fh + 1
    bb.fill(x1, rt - 1, z1, x2, rt - 1, z2, CHOC)
    for i, x in enumerate(range(x1 + 1, x2, 3)):
        for j, z in enumerate(range(z1 + 1, z2, 3)):
            col = "minecraft:white_wool" if (i + j) % 3 else "minecraft:pink_wool"
            bb.fill(x, rt, z, x + 1, rt + 1, z + 1, col)
    for x in range(x1 + 2, x2 - 1, 3):
        bb.set(x, rt + 2, (z1 + z2) // 2, "minecraft:brown_terracotta")
    # door to the square + sign board
    dz = (z1 + z2) // 2
    bb.fill(x2, y, dz - 1, x2, y + 2, dz + 1, AIR)
    bb.set(x2, y, dz, "minecraft:dark_oak_door[facing=east,half=lower,hinge=left]"); bb.set(x2, y + 1, dz, "minecraft:dark_oak_door[facing=east,half=upper,hinge=left]")
    bb.set(x2, y, dz + 1, "minecraft:dark_oak_door[facing=east,half=lower,hinge=right]"); bb.set(x2, y + 1, dz + 1, "minecraft:dark_oak_door[facing=east,half=upper,hinge=right]")
    bb.set(x2, y, dz - 1, CHOC); bb.set(x2, y + 1, dz - 1, CHOC)
    bb.fill(x2 + 1, y + 3, dz - 3, x2 + 1, y + 4, dz + 4, "minecraft:orange_concrete")
    bb.fill(x2 + 1, y + 3, dz - 2, x2 + 1, y + 3, dz + 3, "minecraft:yellow_concrete")
    # inside: the counter and tables downstairs, Pudding's kitchen and storeroom upstairs
    bb.fill(x1 + 1, y, z1 + 1, x1 + 2, y, z2 - 1, "minecraft:dark_oak_planks")
    bb.fill(x1 + 3, y, z1 + 1, x1 + 3, y, z2 - 1, "onepiece:chocolate_slab[type=top]")
    for z in range(z1 + 2, z2 - 1, 3):
        bb.set(x1 + 1, y + 1, z, "minecraft:cake") if False else bb.set(x1 + 1, y + 1, z, "minecraft:decorated_pot[facing=east]")
    for (tx, tz) in ((x1 + 7, z1 + 3), (x1 + 7, z2 - 3), (x2 - 4, z1 + 3), (x2 - 4, z2 - 3)):
        table(bb, tx, y, tz, cloth="minecraft:pink_carpet", wood="dark_oak")
    for i in range(fh):
        bb.set(x1 + 5 + i, y + i, z1 + 1, "minecraft:dark_oak_stairs[facing=east,half=bottom]")
        bb.set(x1 + 5 + i, y + fh, z1 + 1, AIR)
    rooms = [(x1 + 1, z1 + 3, (x1 + x2) // 2, z2 - 1), ((x1 + x2) // 2 + 2, z1 + 1, x2 - 1, z2 - 1)]
    for room, kind in zip(rooms, ("kitchen", "storage")):
        P.furnish_room(bb, room, y + fh + 1, kind=kind, height=fh - 1, seed=seed_of("cafe", *room), wood="dark_oak", tracker=tracker)
    bb.fill((x1 + x2) // 2 + 1, y + fh + 1, z1 + 1, (x1 + x2) // 2 + 1, y + 2 * fh - 1, z2 - 1, CHOC)
    bb.fill((x1 + x2) // 2 + 1, y + fh + 1, dz, (x1 + x2) // 2 + 1, y + fh + 2, dz, AIR)
    txt, ok = P.audit_props(bb, rooms, y + fh + 1, fh - 1)
    if not ok:
        audit.append(txt)
    # the patio: a cookie terrace with candy-striped parasols and chocolate chairs
    px1, px2 = x2 + 2, x2 + 12
    bb.fill(px1, TY, z1, px2, TY, z2, COOK)
    for (tx, tz) in ((px1 + 3, z1 + 2), (px1 + 3, z2 - 2), (px1 + 8, (z1 + z2) // 2)):
        bb.set(tx, TY + 1, tz, "minecraft:dark_oak_fence"); bb.set(tx, TY + 2, tz, "minecraft:white_carpet")
        bb.fill(tx, TY + 3, tz, tx, TY + 3, tz, "minecraft:dark_oak_fence")
        for (dx, dz2) in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            bb.set(tx + dx, TY + 4, tz + dz2, "minecraft:red_wool" if (dx + dz2) % 2 else "minecraft:white_wool")
        for dx in (-2, 2):
            bb.set(tx + dx, TY + 1, tz, f"onepiece:chocolate_stairs[facing={'east' if dx < 0 else 'west'},half=bottom]")
    for x in range(px1, px2 + 1, 2):
        bb.set(x, TY + 1, z1, "minecraft:dark_oak_fence") if x != px1 + 3 else None
    # Pudding's house next door (north)
    w, d = 12, 9
    m, top, au = house_module(seed_of("pudding", x1), w, d, 2, "onepiece:frosting_stairs", tracker, ["living", "bedroom"], pal=HOUSE_PALS[2], fh=4)
    audit += au
    place_house(bb, m, w, d, x1 + 1, TY, z1 - d - 4, 3)
    return (x1 - 3, z1 - d - 8, px2 + 2, z2 + 3)


# ------------------------------------------------------------------ the Sweets Factory
def factory(bb, tracker, audit):
    x1, z1, x2, z2 = FAC
    y = TY + 1
    H = 13
    bb.fill(x1 - 1, y - 4, z1 - 1, x2 + 1, y - 1, z2 + 1, COOK)
    bb.fill(x1, y, z1, x2, y + H, z2, "minecraft:brown_terracotta")
    bb.fill_where(x1, y, z1, x2, y + H, z2, lambda X, Y, Z: ((X - x1) % 6 == 0) | (Y == y + H) | (Y == y), COOK)
    bb.fill_where(x1, y, z1, x2, y + H, z2, lambda X, Y, Z: ((Z - z1) % 6 == 0) & ((X == x1) | (X == x2)), COOK)
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y + H - 1, z2 - 1, AIR)
    bb.fill(x1 + 1, y - 1, z1 + 1, x2 - 1, y - 1, z2 - 1, "minecraft:smooth_stone")
    # tall windows between the piers, frosting sills
    for x in range(x1 + 2, x2 - 1, 6):
        for z in (z1, z2):
            bb.fill(x, y + 3, z, x + 2, y + 9, z, "minecraft:glass_pane")
            bb.fill(x, y + 2, z + (-1 if z == z1 else 1), x + 2, y + 2, z + (-1 if z == z1 else 1), "onepiece:frosting_slab[type=top]")
    # saw-tooth roof in chocolate with glass north lights
    for x in range(x1, x2 + 1, 8):
        for i in range(6):
            bb.fill(x + i, y + H + 1 + i, z1, x + i, y + H + 1 + i, z2, "onepiece:chocolate_stairs[facing=west,half=bottom]")
            bb.fill(x + i, y + H + 1, z1, x + i, y + H + i, z2, AIR) if False else None
        bb.fill(x + 6, y + H + 1, z1, x + 6, y + H + 6, z2, "minecraft:light_gray_stained_glass")
        bb.fill(x + 7, y + H + 1, z1, x + 7, y + H + 1, z2, CHOC)
    bb.fill_where(x1, y + H + 1, z1, x2, y + H + 7, z2, lambda X, Y, Z: ((Z == z1) | (Z == z2)) & (Y <= y + H + 1 + (X - x1) % 8) & ((X - x1) % 8 < 7), CHOC)
    # three candy-cane chimneys
    for k, cx in enumerate((x1 + 6, (x1 + x2) // 2, x2 - 6)):
        cz = z1 + 3
        top = y + H + 16 + k * 2
        bb.fill_where(cx - 2, y, cz - 2, cx + 2, top, cz + 2, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 1.8, "minecraft:white_concrete")
        bb.fill_where(cx - 2, y, cz - 2, cx + 2, top, cz + 2,
                      lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= 1.8) & (((Y + np.round(np.arctan2(Z - cz, X - cx) * 2)) % 4) < 2), "minecraft:red_concrete")
        bb.fill(cx, y + H, cz, cx, top, cz, AIR)
        bb.set(cx, top - 1, cz, "minecraft:campfire[lit=true,signal_fire=true,facing=north]")
        bb.set(cx, top - 2, cz, "minecraft:hay_block")
    # inside: the production hall: mixing vats (cauldrons on cookie plinths), ovens, a long cooling belt, the wedding-cake stand
    for x in range(x1 + 4, x2 - 3, 6):
        bb.fill(x, y, z1 + 4, x + 1, y, z1 + 5, COOK)
        bb.set(x, y + 1, z1 + 4, "minecraft:cauldron"); bb.set(x + 1, y + 1, z1 + 5, "minecraft:cauldron")
        bb.set(x, y, z2 - 2, "minecraft:smoker[facing=north]"); bb.set(x + 1, y, z2 - 2, "minecraft:blast_furnace[facing=north]")
        bb.set(x + 2, y, z2 - 2, "minecraft:furnace[facing=north]")
    bb.fill(x1 + 3, y, (z1 + z2) // 2, x2 - 3, y, (z1 + z2) // 2, "minecraft:polished_blackstone_slab[type=bottom]")
    for x in range(x1 + 4, x2 - 3, 3):
        bb.set(x, y + 1, (z1 + z2) // 2, "onepiece:chocolate_slab[type=bottom]") if x % 2 else None
    cx, cz = x2 - 8, (z1 + z2) // 2 + 4
    for k, r in enumerate((3, 2, 1)):
        bb.fill_where(cx - 4, y + k * 2, cz - 4, cx + 4, y + k * 2 + 1, cz + 4, lambda X, Y, Z, r=r: np.hypot(X - cx, Z - cz) <= r + 0.4, FROST)
    for x in range(x1 + 4, x2 - 2, 7):
        bb.fill(x, y + 7, (z1 + z2) // 2 - 3, x, y + H - 1, (z1 + z2) // 2 - 3, "minecraft:iron_chain[axis=y]")
        bb.set(x, y + 6, (z1 + z2) // 2 - 3, "minecraft:lantern[hanging=true]")
    # the gate, south side, to the factory street
    gx = PL[0]
    bb.fill(gx - 2, y, z2, gx + 2, y + 4, z2, AIR)
    bb.fill(gx - 3, y + 5, z2 + 1, gx + 3, y + 5, z2 + 1, FROST)
    for gx2 in (gx - 3, gx + 3):
        bb.fill(gx2, y, z2 + 1, gx2, y + 4, z2 + 1, f"{CANE}[axis=y]")
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 3)


def harbour(bb):
    z_sea = next(z for z in range(PL[1], N) if not land(np.array([PL[0]]), np.array([z]))[0])
    z_end = min(N - 30, z_sea + 10)
    bb.fill(PL[0] - 10, 0, z_sea - 3, PL[0] + 10, 0, z_end, COOK)
    bb.fill(PL[0] - 10, -6, z_end, PL[0] + 10, -1, z_end, COOK)
    for x in range(PL[0] - 10, PL[0] + 11, 4):
        bb.fill(x, 1, z_end, x, 2, z_end, f"{CANE}[axis=y]")
    SS.stamp_ship(bb, "thousand_sunny", PL[0] + 4, z_end + 12, 0, 0)
    return (PL[0] - 28, z_sea - 4, PL[0] + 32, N)


def design():
    bb = BigBuild(seed=15010, y_min=-14, y_max=70)
    tracker = P.PropTracker(15010)
    audit = []
    rng = np.random.default_rng(15010)
    terrain(bb)
    fountain(bb)
    taken = [(PL[0] - PL[2], PL[1] - PL[2], PL[0] + PL[2], PL[1] + PL[2])]
    taken.append(cafe(bb, tracker, audit))
    taken.append(factory(bb, tracker, audit))
    taken.append(harbour(bb))
    for x in (40, 88, 128):
        cookie_bridge(bb, x)
        taken.append((x - 4, CANAL_Z - 10, x + 4, CANAL_Z + 10))
    # chocolate houses along the streets: rings round the square and both canal banks, doors to the street
    cands = []
    for ring, step, face in ((22, 30, "out"), (40, 17, "in"), (54, 14, "in")):
        for a in range(0, 360, step):
            cx, cz = PL[0] + ring * math.cos(math.radians(a + 5)), PL[1] + ring * math.sin(math.radians(a + 5))
            vx, vz = (PL[0] - cx, PL[1] - cz) if face == "in" else (cx - PL[0], cz - PL[1])
            cands.append((cx, cz, vx, vz))
    for x in range(20, N - 20, 13):
        cc = CANAL_Z + 3 * math.sin(x / 14.0)
        cands.append((x, cc - 13, 0, 1))
        cands.append((x, cc + 13, 0, -1))
    for gz in range(20, N - 20, 12):                       # then fill the gaps on a loose grid, facing the square
        for gx in range(20, N - 20, 12):
            cands.append((gx + 3 * math.sin(gz), gz + 3 * math.cos(gx), PL[0] - gx, PL[1] - gz))
    k = 0
    for (cx, cz, vx, vz) in cands:
        rot = (0 if vz > 0 else 2) if abs(vz) >= abs(vx) else (3 if vx > 0 else 1)
        w, d = int(rng.integers(8, 11)), int(rng.integers(7, 9))
        mw, md = w, d
        fw, fd = (w, d) if rot % 2 == 0 else (d, w)
        x0, z0 = int(round(cx - fw / 2)), int(round(cz - fd / 2))
        xs = np.array([x0, x0 + fw, x0, x0 + fw, x0 + fw // 2, x0 + fw // 2, x0, x0 + fw, x0 + fw // 2])
        zs = np.array([z0, z0, z0 + fd, z0 + fd, z0, z0 + fd, z0 + fd // 2, z0 + fd // 2, z0 + fd // 2])
        if not land(xs, zs).all() or sh(xs, zs).min() < 11 or street(xs, zs).any() or canal(xs, zs).any():
            continue
        if any(t[0] <= x0 + fw and x0 <= t[2] and t[1] <= z0 + fd and z0 <= t[3] for t in taken):
            continue
        m, top, au = house_module(seed_of("choco", x0, z0), mw, md, 2 if rng.random() < 0.6 else 1, ROOFS[k % len(ROOFS)], tracker,
                                  [["living", "bedroom"], ["kitchen", "bedroom"], ["living", "library"]][k % 3], pal=HOUSE_PALS[k % 3], fh=4)
        audit += au
        place_house(bb, m, mw, md, x0, hy(x0 + fw // 2, z0 + fd // 2), z0, rot)
        taken.append((x0 - 1, z0 - 1, x0 + fw + 1, z0 + fd + 1))
        k += 1
    print("houses:", k)
    # candy lamps on the ring street, lollipop trees in the gardens
    for a in range(0, 360, 20):
        x, z = int(round(PL[0] + 32.5 * math.cos(math.radians(a)))), int(round(PL[1] + 32.5 * math.sin(math.radians(a))))
        if land(np.array([x]), np.array([z]))[0] and (bb.get_region(x, hy(x, z) + 1, z, x, hy(x, z) + 5, z) <= 1).all() and not canal(x, z):
            candy_lamp(bb, x, z)
    cols = ["pink", "red", "lime", "orange", "magenta", "light_blue", "yellow", "purple"]
    t = 0
    for _ in range(3000):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 10 or street(X, Z)[0] or canal(X, Z)[0]:
            continue
        if any(tt[0] - 4 <= x <= tt[2] + 4 and tt[1] - 4 <= z <= tt[3] + 4 for tt in taken):
            continue
        lollipop_tree(bb, x, z, cols[t % len(cols)], rng)
        taken.append((x - 4, z - 4, x + 4, z + 4))
        t += 1
        if t >= 24:
            break
    print("lollipop trees:", t)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 15090, density=0.42,
              kinds=["onepiece:gumdrop_bush", "onepiece:candy_shrub", "onepiece:wafer_grass", "onepiece:candy_cane_sprout", "minecraft:short_grass",
                     "onepiece:wafer_grass"],
              flowers=["onepiece:lollipop_flower", "minecraft:pink_tulip", "minecraft:allium"],
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 9) & ~street(X, Z) & ~canal(X, Z),
              ground=("grass_block", "moss_block", "podzol", "rooted_dirt", "sugar_sand"))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    x1, z1, x2, z2 = CAFE
    b.chest(x1 + 1, TY + 1, z2 - 2, "candy", "east")
    b.chest(FAC[0] + 3, TY + 1, FAC[3] - 3, "candy", "east")
    b.chest(PL[0] + 3, TY + 1, PL[1] - 9, "easy", "south")
    b.guards("homie", ((PL[0] - 6, PL[1] + 16), (PL[0] + 6, PL[1] + 16), (FAC[0] + 20, FAC[3] + 4), (x2 + 8, z1 - 2)), y=TY + 1)
    return b, 0
