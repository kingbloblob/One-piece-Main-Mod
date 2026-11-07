"""The Human Auctioning House v2 in Grove 1 of Sabaody, redesigned with the Minecraft Builder skill.

Sabaody is a ring of giant Yarukiman mangroves standing in the sea; bubbles float up from their roots all day. Grove 1
is the lawless grove of the auction: the hall stands under the great numbered mangrove "1", a blood-red theatre with
a curved front of black columns, a gilt sign and a big red dome over the auditorium. Inside, from the street: the
lobby with chandeliers, the ticket counter and the grand stairs to the balcony boxes; the auditorium of tiered seats
rising to the back, the Celestial Dragons' gilded box down at the front, side balconies; the stage with its red
curtain, the auctioneer's podium, the display cage and the mermaid's fishbowl; backstage the corridor of cells and
holding pens (and the giant's cell), the auctioneer's office and the vault. Outside: the plaza with a fountain and
Marine guards, souvenir shops and a bar on the street, a bubble-coating stall, and the mangrove roots arching over the
paths. 160 x 160. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, glyph, table, lamp_post
from mcb.bridge import to_canvas
from mcb.mangrove import yarukiman as shared_yarukiman
from mcb import nature as NT

SID = "auction_house"
TITLE = "Human Auctioning House (Sabaody Grove 1)"
CUTS = [3, 11, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
TY = 2
X1, X2 = 54, 106            # the hall
Z1, Z2 = 34, 100            # north (backstage) .. south (front)
LOBBY_Z = 88                # lobby z LOBBY_Z..Z2
STAGE_Z = (44, 56)          # stage z range
BACK_Z = 43                 # backstage z1..BACK_Z
H = 18                      # wall height above TY
MX = (X1 + X2) // 2         # centre line
RED = ["minecraft:red_nether_bricks", "minecraft:red_terracotta", "minecraft:nether_bricks"]
BLACK = "minecraft:polished_blackstone_bricks"
GOLD = "minecraft:gold_block"
YLOG = "onepiece:yarukiman_log[axis=y]"
YWOOD = "onepiece:yarukiman_wood"
YLEAF = "onepiece:yarukiman_leaves[distance=7,persistent=true,waterlogged=false]"
BUB = "onepiece:bubble_glass"
_ISLE = NT.outline(84, 88, 74, 4710, wobble=0.06)
SOIL = [("minecraft:grass_block", 0.5), ("minecraft:moss_block", 0.12), ("minecraft:rooted_dirt", 0.12), ("minecraft:mud", 0.08),
        ("minecraft:coarse_dirt", 0.1), ("minecraft:podzol", 0.08)]
PAVE = [("minecraft:stone_bricks", 0.45), ("minecraft:polished_andesite", 0.25), ("minecraft:cracked_stone_bricks", 0.12),
        ("minecraft:andesite", 0.1), ("minecraft:mossy_stone_bricks", 0.08)]
SAND = [("minecraft:sand", 0.7), ("minecraft:mud", 0.15), ("minecraft:clay", 0.15)]
TREES = [(30, 42, 8.0, 64), (140, 36, 6.5, 54), (26, 136, 6.0, 50), (146, 134, 6.5, 56)]   # x, z, trunk r, height
FONT = {"H": ["#.#", "#.#", "###", "#.#", "#.#"], "U": ["#.#", "#.#", "#.#", "#.#", "###"], "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
        "A": [".#.", "#.#", "###", "#.#", "#.#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"], "C": ["###", "#..", "#..", "#..", "###"],
        "T": ["###", ".#.", ".#.", ".#.", ".#."], "I": ["###", ".#.", ".#.", ".#.", "###"], "O": ["###", "#.#", "#.#", "#.#", "###"],
        "1": [".#.", "##.", ".#.", ".#.", "###"], " ": ["..", "..", "..", "..", ".."]}


def text(bb, s, x, y, z, block, axis="x", scale=1, sign=1):
    """Pixel letters along +x (sign 1) or -x (sign -1) on plane z (axis x), or along z."""
    for ch in s:
        rows = FONT[ch]
        for r, bits in enumerate(rows):
            for c, b_ in enumerate(bits):
                if b_ == "#":
                    for i in range(scale):
                        for j in range(scale):
                            if axis == "x":
                                bb.set(x + sign * (c * scale + i), y - r * scale - j, z, block)
                            else:
                                bb.set(x, y - r * scale - j, z + sign * (c * scale + i), block)
        x += sign * (len(rows[0]) + 1) * scale if axis == "x" else 0
        z += sign * (len(rows[0]) + 1) * scale if axis != "x" else 0


def shore(X, Z):
    return _ISLE(X, Z)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    roll = TY + NT.fbm(X, Z, 4711, 20) * 3 - 1
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, roll)
    dx = np.maximum(np.maximum(X1 - 14 - X, X - X2 - 14), 0)
    dz = np.maximum(np.maximum(Z1 - 8 - Z, Z - Z2 - 26), 0)
    flat = np.clip(1 - np.hypot(dx, dz) / 10.0, 0, 1)
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
    """The plaza in front, the street east-west past it and the lanes to the trees."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (X >= X1 - 10) & (X <= X2 + 10) & (Z >= Z2) & (Z <= Z2 + 22)
    m |= (np.abs(Z - (Z2 + 14 + 2 * np.sin(X * 0.07))) <= 2.5)
    m |= (X >= X1 - 4) & (X <= X2 + 4) & (Z >= Z1 - 4) & (Z <= Z2)
    m |= (np.abs(X - (MX + 3 * np.sin(Z * 0.1))) <= 1.5) & (Z < Z1)
    return m


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 4720, mask=lambda X, Z: land(X, Z) & (sh(X, Z) < 8), under="minecraft:mud",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SOIL, 4721, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~paved(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 4722, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & paved(X, Z), core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:mud")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the giant mangroves
def yarukiman(bb, x, z, r, h, rng, number=None, skip=None):
    """A giant Yarukiman (v3, shared with the other Sabaody builds: mcb/mangrove.py): a lumpy trunk standing on a
    tent of arching prop roots, a broken crown high up, bubbles welling from the roots, the grove number on a board."""
    return shared_yarukiman(bb, x, hy(x, z), z, r, h, rng, number=number, skip=skip)


def bubbles(bb, rng, taken, n=40):
    k = 0
    for _ in range(600):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        y = int(rng.integers(TY + 6, TY + 40))
        if X1 - 2 <= x <= X2 + 2 and Z1 - 2 <= z <= Z2 + 2 and y < TY + H + 14:
            continue
        r = float(rng.uniform(1.0, 2.4))
        reg = bb.get_region(x - 3, y - 3, z - 3, x + 3, y + 3, z + 3)
        if (reg > 0).any():
            continue
        bb.fill_where(x - 3, y - 3, z - 3, x + 3, y + 3, z + 3,
                      lambda X, Y, Z: np.abs(np.sqrt((X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2) - r) < 0.55, BUB)
        k += 1
        if k >= n:
            break


# ------------------------------------------------------------------ the hall
def shell(bb):
    top = TY + H
    bb.fill(X1 - 1, TY - 3, Z1 - 1, X2 + 1, TY, Z2 + 1, BLACK)
    bb.fill(X1, TY, Z1, X2, TY, Z2, "minecraft:dark_oak_planks")
    bb.mix(X1, TY + 1, Z1, X2, top, Z2, RED, [0.65, 0.2, 0.15])
    bb.fill(X1 + 1, TY + 1, Z1 + 1, X2 - 1, top, Z2 - 1, AIR)
    # black pilasters and a cornice
    for x in range(X1, X2 + 1, 6):
        for z in (Z1, Z2):
            bb.fill(x, TY + 1, z, x, top, z, BLACK)
    for z in range(Z1, Z2 + 1, 6):
        for x in (X1, X2):
            bb.fill(x, TY + 1, z, x, top, z, BLACK)
    for (x, z, f) in [(x, Z2 + 1, "south") for x in range(X1 - 1, X2 + 2)] + [(x, Z1 - 1, "north") for x in range(X1 - 1, X2 + 2)] + \
                     [(X1 - 1, z, "west") for z in range(Z1, Z2 + 1)] + [(X2 + 1, z, "east") for z in range(Z1, Z2 + 1)]:
        bb.set(x, top, z, f"minecraft:polished_blackstone_brick_stairs[facing={'north' if f == 'south' else 'south' if f == 'north' else 'east' if f == 'west' else 'west'},half=top]")
    bb.fill(X1 - 1, top + 1, Z1 - 1, X2 + 1, top + 1, Z2 + 1, "minecraft:polished_blackstone_brick_wall")
    bb.fill(X1, top + 1, Z1, X2, top + 1, Z2, "minecraft:polished_blackstone")
    bb.fill(X1 + 1, top + 1, Z1 + 1, X2 - 1, top + 1, Z2 - 1, "minecraft:dark_oak_planks")
    # tall arched windows on the long sides
    for z in range(Z1 + 3, Z2 - 2, 6):
        for x in (X1, X2):
            P.arched_opening(bb, "z", z, TY + 6, x, 3, 8, depth=1, fill="minecraft:red_stained_glass_pane")
    # the dome over the auditorium
    cz = (STAGE_Z[1] + LOBBY_Z) // 2
    R = 22
    bb.fill_where(MX - R, top + 1, cz - R, MX + R, top + 16, cz + R,
                  lambda X, Y, Z: (((X - MX) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - top) / 15.0) ** 2 <= 1) &
                                  (((X - MX) ** 2 + (Z - cz) ** 2) / (R - 1.3) ** 2 + ((Y - top) / 13.8) ** 2 > 1), "minecraft:red_terracotta")
    bb.fill_where(MX - R, top + 1, cz - R, MX + R, top + 16, cz + R,
                  lambda X, Y, Z: (((X - MX) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - top) / 15.0) ** 2 <= 1) &
                                  (((X - MX) ** 2 + (Z - cz) ** 2) / (R - 1.3) ** 2 + ((Y - top) / 13.8) ** 2 > 1) &
                                  ((np.round(np.degrees(np.arctan2(Z - cz, X - MX))) % 30) < 4), "minecraft:gold_block")
    bb.fill_where(MX - R, top + 1, cz - R, MX + R, top + 16, cz + R,
                  lambda X, Y, Z: (((X - MX) ** 2 + (Z - cz) ** 2) / (R - 1.3) ** 2 + ((Y - top) / 13.8) ** 2 <= 1) & (Y > top), AIR)
    bb.fill(MX - R + 1, top + 1, cz - R + 1, MX + R - 1, top + 1, cz + R - 1, AIR) if False else None
    # open the ceiling under the dome
    bb.fill_where(MX - R, top, cz - R, MX + R, top + 1, cz + R, lambda X, Y, Z: (X > X1) & (X < X2) & ((X - MX) ** 2 + (Z - cz) ** 2 < (R - 1.3) ** 2), AIR)
    bb.fill(MX - 1, top + 16, cz - 1, MX + 1, top + 16, cz + 1, GOLD)
    bb.fill(MX, top + 17, cz, MX, top + 19, cz, "minecraft:end_rod[facing=up]")
    # chandelier hanging from the dome
    bb.fill(MX, top + 4, cz, MX, top + 14, cz, "minecraft:iron_chain[axis=y]")
    bb.fill_where(MX - 3, top + 3, cz - 3, MX + 3, top + 3, cz + 3, lambda X, Y, Z: np.abs(np.hypot(X - MX, Z - cz) - 2.6) < 0.6, GOLD)
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        bb.set(MX + dx, top + 2, cz + dz, "minecraft:lantern[hanging=true]")
    return top


def front(bb):
    """The curved front: a porch of black columns, steps, the gilt sign and the doors."""
    top = TY + H
    z0 = Z2 + 1
    bb.fill_where(X1 + 6, TY - 1, z0, X2 - 6, TY, z0 + 8,
                  lambda X, Y, Z: ((X - MX) / 26.0) ** 2 + ((Z - z0) / 8.5) ** 2 <= 1, "minecraft:polished_blackstone")
    for i in range(3):
        bb.fill_where(X1 + 6, TY - 1 + i, z0, X2 - 6, TY - 1 + i, z0 + 10,
                      lambda X, Y, Z, i=i: (((X - MX) / (27.0 - i)) ** 2 + ((Z - z0) / (9.5 - i * 1.2)) ** 2 <= 1) &
                                           (((X - MX) / (26.0 - i)) ** 2 + ((Z - z0) / (8.5 - i * 1.2)) ** 2 > 1), "minecraft:polished_blackstone_slab[type=top]")
    for a in range(-70, 71, 14):
        x = MX + int(round(24 * math.sin(math.radians(a))))
        z = z0 + int(round(7.4 * math.cos(math.radians(a))))
        bb.fill(x, TY + 1, z, x, top - 2, z, "minecraft:polished_basalt[axis=y]")
        bb.set(x, top - 1, z, "minecraft:chiseled_polished_blackstone")
    bb.fill_where(X1 + 6, top, z0, X2 - 6, top + 1, z0 + 9,
                  lambda X, Y, Z: ((X - MX) / 25.5) ** 2 + ((Z - z0) / 8.2) ** 2 <= 1, "minecraft:polished_blackstone")
    bb.fill_where(X1 + 6, top + 1, z0, X2 - 6, top + 1, z0 + 9,
                  lambda X, Y, Z: (((X - MX) / 25.5) ** 2 + ((Z - z0) / 8.2) ** 2 <= 1) & (((X - MX) / 24.5) ** 2 + ((Z - z0) / 7.2) ** 2 > 1),
                  "minecraft:gold_block")
    # the gilt sign above the doors: HUMAN AUCTION
    bb.fill(MX - 28, top + 2, Z2 + 1, MX + 28, top + 10, Z2 + 1, "minecraft:black_concrete")
    bb.fill(MX - 29, top + 2, Z2 + 1, MX - 29, top + 10, Z2 + 1, GOLD)
    bb.fill(MX + 29, top + 2, Z2 + 1, MX + 29, top + 10, Z2 + 1, GOLD)
    bb.fill(MX - 29, top + 11, Z2 + 1, MX + 29, top + 11, Z2 + 1, GOLD)
    text(bb, "HUMAN AUCTION", MX - 27, top + 8, Z2 + 2, GOLD)
    # triple doors
    for dx in (-8, 0, 8):
        P.arched_opening(bb, "x", MX + dx, TY + 1, Z2, 3 if dx else 5, 6 if dx else 8, depth=1, trim="minecraft:gold_block")
    for x in (MX - 1, MX + 1):
        bb.set(x, TY + 1, Z2, f"minecraft:dark_oak_door[facing=south,half=lower,hinge={'left' if x < MX else 'right'}]")
        bb.set(x, TY + 2, Z2, f"minecraft:dark_oak_door[facing=south,half=upper,hinge={'left' if x < MX else 'right'}]")
    bb.set(MX, TY + 1, Z2, AIR)
    # red carpet down the steps
    bb.fill(MX - 1, TY, Z2 + 1, MX + 1, TY, Z2 + 8, "minecraft:red_wool")


def lobby(bb, tracker, audit):
    z1, z2 = LOBBY_Z, Z2 - 1
    bb.fill(X1 + 1, TY + 6, z1, X2 - 1, TY + 6, z2, "minecraft:dark_oak_planks")       # mezzanine floor
    bb.fill(X1 + 1, TY + 1, z1 - 1, X2 - 1, TY + 14, z1 - 1, RED[0])                     # wall to the auditorium
    for dx in (-10, 10):
        P.arched_opening(bb, "x", MX + dx, TY + 1, z1 - 1, 3, 4, depth=1, trim=GOLD)
    P.arched_opening(bb, "x", MX, TY + 7, z1 - 1, 7, 6, depth=1)
    bb.fill(MX - 4, TY + 6, z1, MX + 4, TY + 6, z1 + 5, AIR)          # well over the lobby centre
    bb.fill(MX - 5, TY + 7, z1, MX + 5, TY + 7, z1 + 6, AIR) if False else None
    for x in (MX - 5, MX + 5):
        bb.fill(x, TY + 7, z1, x, TY + 7, z1 + 6, "minecraft:dark_oak_fence")
    bb.fill(MX - 5, TY + 7, z1 + 6, MX + 5, TY + 7, z1 + 6, "minecraft:dark_oak_fence")
    # grand stairs both sides up to the mezzanine
    for side in (-1, 1):
        x = MX + side * 16
        for i in range(5):
            bb.fill(x - 1, TY + 1 + i, z2 - 1 - i, x + 1, TY + 1 + i, z2 - 1 - i, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
            bb.fill(x - 1, TY + 2 + i, z2 - 1 - i, x + 1, TY + 6, z2 - 1 - i, AIR)
        bb.fill(x - 1, TY + 6, z2 - 6, x + 1, TY + 6, z2 - 6, AIR)
    bb.fill(X1 + 1, TY, z1, X2 - 1, TY, z2, "minecraft:polished_blackstone")
    bb.fill(MX - 2, TY, z1, MX + 2, TY, z2, "minecraft:red_wool")
    # ticket counter (west) and coat check (east)
    bb.fill(X1 + 3, TY + 1, z1 + 2, X1 + 3, TY + 1, z1 + 8, "minecraft:dark_oak_planks")
    bb.fill(X1 + 3, TY + 2, z1 + 2, X1 + 3, TY + 2, z1 + 8, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(X1 + 3, TY + 3, z1 + 5, "minecraft:candle[candles=2,lit=true]")
    bb.set(X1 + 2, TY + 1, z1 + 4, "minecraft:lectern[facing=east]")
    for z in range(z1 + 2, z1 + 9, 2):
        bb.set(X2 - 2, TY + 1, z, "minecraft:dark_oak_fence")
        bb.set(X2 - 2, TY + 2, z, "minecraft:black_carpet")
    for (x, z) in ((MX - 10, z1 + 4), (MX + 10, z1 + 4)):
        bb.fill(x, TY + 1, z, x, TY + 4, z, "minecraft:polished_basalt[axis=y]")
        bb.set(x, TY + 5, z, "minecraft:potted_dead_bush") if False else None
        bb.set(x, TY + 5, z, GOLD)
    for (x, z) in ((MX - 10, z2 - 3), (MX + 10, z2 - 3)):
        bb.fill(x, TY + 10, z, x, TY + 13, z, "minecraft:iron_chain[axis=y]")
        bb.set(x, TY + 9, z, "minecraft:lantern[hanging=true]")
    # mezzanine: the VIP lounge rooms
    rooms, doors = P.bsp_rooms(bb, X1 + 1, z1 + 1, MX - 7, z2, TY + 7, 5, RED[0], seed=4740, min_room=5)
    rooms2, doors2 = P.bsp_rooms(bb, MX + 7, z1 + 1, X2 - 1, z2, TY + 7, 5, RED[0], seed=4741, min_room=5)
    for i, r in enumerate(rooms + rooms2):
        P.furnish_room(bb, r, TY + 7, kind=("living", "library", "storage", "living")[i % 4], height=5, seed=4742 + i, wood="dark_oak",
                       tracker=tracker, doors=doors + doors2)
        txt, ok = P.audit_props(bb, [r], TY + 7, 5)
        if not ok:
            audit.append(txt)
    bb.fill(X1 + 1, TY + 12, z1, X2 - 1, TY + 12, z2, "minecraft:dark_oak_planks")


def auditorium(bb):
    z1, z2 = STAGE_Z[1] + 1, LOBBY_Z - 2
    # tiered seats: rows of red seats rising toward the lobby, an aisle in the middle and at both sides
    floor_y = TY
    for k, z in enumerate(range(z1 + 4, z2 + 1, 2)):
        y = TY + k // 2
        bb.fill(X1 + 1, TY, z, X2 - 1, y, z + 1, "minecraft:dark_oak_planks")
        for x in range(X1 + 4, X2 - 3):
            if abs(x - MX) <= 1:
                continue
            bb.set(x, y + 1, z + 1, "minecraft:red_nether_brick_stairs[facing=north,half=bottom]") if False else None
            bb.set(x, y + 1, z + 1, "minecraft:crimson_stairs[facing=north,half=bottom]")
        floor_y = y
    bb.fill(MX - 1, TY, z1, MX + 1, TY, z2, "minecraft:dark_oak_planks")
    for k, z in enumerate(range(z1 + 4, z2 + 1, 2)):
        y = TY + k // 2
        bb.fill(MX - 1, TY + 1, z, MX + 1, y + 1, z + 1, AIR) if y > TY else None
        bb.fill(MX - 1, TY, z, MX + 1, y, z + 1, "minecraft:red_wool") if False else None
    # lanterns on the row ends (side aisles and the centre aisle) so the hall is lit without hanging lights
    for k, z in enumerate(range(z1 + 4, z2 + 1, 2)):
        y = TY + k // 2
        if k % 2 == 0:
            for x in (X1 + 4, X2 - 4, MX - 2, MX + 2):
                bb.set(x, y + 1, z + 1, "minecraft:lantern[hanging=false]")
    # aisle as a ramp of carpet steps
    for k, z in enumerate(range(z1 + 4, z2 + 1, 2)):
        y = TY + k // 2
        bb.fill(MX - 1, y, z, MX + 1, y, z + 1, "minecraft:dark_oak_planks")
        bb.fill(MX - 1, y + 1, z, MX + 1, y + 1, z + 1, "minecraft:red_carpet")
    # the Celestial Dragons' box: a gilded dais at the front left with white throne seats
    cx1, cz1 = X1 + 3, z1 + 1
    bb.fill(cx1, TY, cz1, cx1 + 12, TY + 1, cz1 + 6, "minecraft:quartz_block")
    bb.fill(cx1, TY + 2, cz1, cx1 + 12, TY + 2, cz1 + 6, "minecraft:white_carpet")
    for x in range(cx1, cx1 + 13):
        bb.set(x, TY + 2, cz1 + 6, "minecraft:gold_block") if x % 3 == 0 else bb.set(x, TY + 2, cz1 + 6, "minecraft:quartz_slab[type=bottom]")
    for x in range(cx1 + 2, cx1 + 11, 3):
        bb.set(x, TY + 2, cz1 + 3, "minecraft:quartz_stairs[facing=south,half=bottom]")
        bb.set(x, TY + 3, cz1 + 4, "minecraft:white_banner[rotation=8]") if False else None
    for x in (cx1, cx1 + 12):
        bb.fill(x, TY + 3, cz1, x, TY + 6, cz1, "minecraft:gold_block")
    bb.fill(cx1, TY + 7, cz1, cx1 + 12, TY + 7, cz1 + 2, "minecraft:white_wool")
    # side balconies on the walls
    for (x1, x2) in ((X1 + 1, X1 + 4), (X2 - 4, X2 - 1)):
        bb.fill(x1, TY + 8, z1 + 2, x2, TY + 8, z2, "minecraft:dark_oak_planks")
        xr = x2 if x1 == X1 + 1 else x1
        for z in range(z1 + 2, z2 + 1):
            bb.set(xr, TY + 9, z, GOLD if z % 4 == 0 else "minecraft:dark_oak_fence")
        for z in range(z1 + 4, z2, 4):
            bb.set(x1 + 1 if x1 == X1 + 1 else x2 - 1, TY + 9, z, "minecraft:crimson_stairs[facing=" + ("east" if x1 == X1 + 1 else "west") + ",half=bottom]")
    for z in range(z1 + 6, z2, 8):
        for x in (X1 + 1, X2 - 1):
            bb.set(x, TY + 12, z, "minecraft:lantern[hanging=false]")
    return floor_y


def stage(bb):
    z1, z2 = STAGE_Z
    sy = TY + 3
    bb.fill(X1 + 1, TY, z1, X2 - 1, sy, z2, "minecraft:dark_oak_planks")
    bb.fill(X1 + 6, sy, z2 + 1, X2 - 6, sy, z2 + 1, "minecraft:dark_oak_slab[type=bottom]") if False else None
    for i in range(3):
        bb.fill(MX - 4, TY + 1 + i, z2 + 3 - i, MX + 4, TY + 1 + i, z2 + 3 - i, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
    # proscenium arch and the red curtain (drawn to the sides) and a valance
    bb.fill(X1 + 1, sy + 1, z2, X1 + 8, TY + H - 1, z2, RED[0])
    bb.fill(X2 - 8, sy + 1, z2, X2 - 1, TY + H - 1, z2, RED[0])
    bb.fill(X1 + 9, TY + H - 4, z2, X2 - 9, TY + H - 1, z2, RED[0])
    bb.fill(X1 + 9, TY + H - 5, z2, X2 - 9, TY + H - 5, z2, GOLD)
    for x in list(range(X1 + 9, X1 + 14)) + list(range(X2 - 13, X2 - 8)):
        bb.fill(x, sy + 1, z2 - 1, x, TY + H - 6, z2 - 1, "minecraft:red_wool")
    bb.fill(X1 + 14, TY + H - 7, z2 - 1, X2 - 14, TY + H - 6, z2 - 1, "minecraft:red_wool")
    # the auctioneer's podium, the display cage and the mermaid's fishbowl
    bb.set(MX + 9, sy + 1, z2 - 3, "minecraft:lectern[facing=south]")
    bb.set(MX + 9, sy + 1, z2 - 4, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
    cx, cz = MX - 8, z1 + 6
    bb.fill(cx - 2, sy + 1, cz - 2, cx + 2, sy + 4, cz + 2, "minecraft:iron_bars")
    bb.fill(cx - 1, sy + 1, cz - 1, cx + 1, sy + 3, cz + 1, AIR)
    bb.fill(cx - 2, sy + 5, cz - 2, cx + 2, sy + 5, cz + 2, "minecraft:dark_oak_slab[type=bottom]")
    fx, fz = MX, z1 + 5
    bb.fill_where(fx - 3, sy + 1, fz - 3, fx + 3, sy + 6, fz + 3, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 2.6, "minecraft:glass")
    bb.fill_where(fx - 3, sy + 1, fz - 3, fx + 3, sy + 5, fz + 3, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 1.7, "minecraft:water")
    bb.fill_where(fx - 3, sy + 6, fz - 3, fx + 3, sy + 6, fz + 3, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 1.7, AIR)
    bb.set(fx, sy + 1, fz, "minecraft:tube_coral_block")
    bb.set(fx, sy + 2, fz, "minecraft:sea_pickle[pickles=3,waterlogged=true]")
    for x in range(X1 + 10, X2 - 9, 6):
        bb.set(x, sy + 1, z2, "minecraft:lantern[hanging=false]")
    return sy


def backstage(bb, tracker, audit):
    """Cells along a corridor, the giant's cell, the office and the vault."""
    z1, z2 = Z1 + 1, BACK_Z
    bb.fill(X1 + 1, TY + 1, z2, X2 - 1, TY + H - 1, z2, RED[0])
    for dx in (-14, 14):
        bb.fill(MX + dx, TY + 4, z2, MX + dx, TY + 5, z2, AIR)
        bb.set(MX + dx, TY + 4, z2, AIR)
    bb.fill(MX - 14, TY + 4, z2 + 1, MX - 14, TY + 3, z2 + 1, AIR)
    # steps from the stage level down to backstage floor at TY
    for dx in (-14, 14):
        bb.fill(MX + dx, TY + 1, z2 - 1, MX + dx, TY + 3, z2 - 1, AIR)
        for i in range(3):
            bb.set(MX + dx, TY + 1 + i, z2 - 3 + i, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
            bb.fill(MX + dx, TY + 2 + i, z2 - 3 + i, MX + dx, TY + 5, z2 - 3 + i, AIR)
    bb.fill(MX - 14, TY + 4, z2, MX - 14, TY + 5, z2, AIR)
    bb.fill(MX + 14, TY + 4, z2, MX + 14, TY + 5, z2, AIR)
    # corridor at z2-3..z2-1 is the steps; cells along the north wall
    cz1, cz2 = z1, z2 - 5
    bb.fill(X1 + 1, TY + 1, cz2 + 1, X2 - 1, TY + 5, cz2 + 1, "minecraft:iron_bars")
    bb.fill(X1 + 1, TY + 6, cz1, X2 - 1, TY + 6, cz2 + 1, "minecraft:polished_blackstone")
    x = X1 + 1
    k = 0
    while x < X2 - 6:
        w = 9 if k == 2 else 5                      # the giant's cell is the big one
        bb.fill(x + w, TY + 1, cz1, x + w, TY + 5, cz2, BLACK)
        cell_x2 = x + w - 1
        if k in (0, 4):
            # the office and the vault are rooms, not cells
            bb.fill(x, TY + 1, cz2 + 1, cell_x2, TY + 5, cz2 + 1, RED[0])
            bb.set(x + 2, TY + 1, cz2 + 1, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left]")
            bb.set(x + 2, TY + 2, cz2 + 1, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left]")
            if k == 0:
                P.furnish_room(bb, (x, cz1, cell_x2, cz2), TY + 1, kind="library", height=5, seed=4750, wood="dark_oak", tracker=tracker,
                               doors=[(x + 2, cz2 + 1)])
                txt, ok = P.audit_props(bb, [(x, cz1, cell_x2, cz2)], TY + 1, 5)
                if not ok:
                    audit.append(txt)
            else:
                bb.fill(x, TY + 1, cz1, cell_x2, TY + 1, cz1 + 1, GOLD)
                bb.set(x + 1, TY + 2, cz1, "minecraft:gold_block")
        else:
            bb.set(x + 2, TY + 1, cz2 + 1, "minecraft:iron_door[facing=south,half=lower,hinge=left,open=false]")
            bb.set(x + 2, TY + 2, cz2 + 1, "minecraft:iron_door[facing=south,half=upper,hinge=left,open=false]")
            bb.set(x + 1, TY + 1, cz1, "minecraft:hay_block")
            bb.set(cell_x2, TY + 1, cz1, "minecraft:cauldron")
            bb.set(x + w // 2, TY + 5, cz1 + 1, "minecraft:iron_chain[axis=y]")
            bb.set(x + w // 2, TY + 4, cz1 + 1, "minecraft:lantern[hanging=true]")
            if k == 2:
                bb.fill(x + 1, TY + 1, cz1 + 2, x + 7, TY + 1, cz1 + 3, "minecraft:white_wool")
                bb.fill(x + 3, TY + 1, cz1, x + 4, TY + 5, cz1, "minecraft:iron_chain[axis=y]")
        x += w + 1
        k += 1
    for xx in range(X1 + 6, X2 - 4, 10):
        bb.set(xx, TY + 5, cz2 + 3, "minecraft:lantern[hanging=true]")


def street(bb, tracker, audit, rng, taken0):
    """Shops and a bar along the street in front of the plaza, a bubble-coating stall, lamps, the fountain."""
    taken = []
    zz = Z2 + 18
    k = 0
    PALS = [dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:light_gray_terracotta"], frame="minecraft:stripped_spruce_log",
                 base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:spruce_planks", wood="spruce",
                 chimney="minecraft:bricks", parapet="minecraft:stone_bricks"),
            dict(walls=["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:cyan_terracotta"], frame="minecraft:stripped_dark_oak_log",
                 base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:oak_planks", wood="oak",
                 chimney="minecraft:bricks", parapet="minecraft:stone_bricks")]
    KINDS = [["living", "bedroom"], ["kitchen", "storage"], ["storage", "bedroom"], ["living", "kitchen"]]
    ROOFS = ["minecraft:dark_oak_stairs", "minecraft:prismarine_brick_stairs", "minecraft:spruce_stairs"]
    for (x0, z0, rot) in ((14, Z2 + 3, 0), (29, Z2 + 3, 0), (14, Z2 + 21, 2), (29, Z2 + 21, 2), (44, Z2 + 23, 2),
                          (120, Z2 + 3, 0), (135, Z2 + 3, 0), (120, Z2 + 21, 2), (135, Z2 + 21, 2), (105, Z2 + 23, 2),
                          (36, 70, 1), (124, 66, 3)):
        w, d = (11, 9) if rot % 2 == 0 else (9, 11)
        xs, zs = np.array([x0, x0 + w, x0, x0 + w]), np.array([z0, z0, z0 + d, z0 + d])
        if not land(xs, zs).all() or sh(xs, zs).min() < 9:
            continue
        if any(t[0] <= x0 + w and x0 <= t[2] and t[1] <= z0 + d and z0 <= t[3] for t in taken0 + taken):
            continue
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        m, top, au = house_module(seed_of("ah", x0, z0), mw, md, 2, ROOFS[k % 3], tracker, KINDS[k % 4], pal=PALS[k % 2])
        audit += au
        place_house(bb, m, mw, md, x0, hy(x0 + w // 2, z0 + d // 2), z0, rot)
        taken.append((x0 - 1, z0 - 1, x0 + w + 1, z0 + d + 1))
        k += 1
    print("houses:", k)
    # fountain in the plaza
    fx, fz = MX, Z2 + 15
    bb.fill_where(fx - 5, TY, fz - 5, fx + 5, TY + 1, fz + 5, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 4.6, "minecraft:polished_andesite")
    bb.fill_where(fx - 5, TY + 1, fz - 5, fx + 5, TY + 1, fz + 5, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 3.6, "minecraft:water")
    bb.fill(fx, TY + 1, fz, fx, TY + 4, fz, "minecraft:polished_andesite")
    bb.set(fx, TY + 5, fz, "minecraft:water")
    # bubble-coating stall (the coating that lets ships dive to Fish-Man Island)
    sx, sz = X2 + 4, Z2 + 6
    for (x, z) in ((sx, sz), (sx + 5, sz), (sx, sz + 4), (sx + 5, sz + 4)):
        bb.fill(x, TY + 1, z, x, TY + 3, z, "minecraft:spruce_fence")
    bb.fill(sx, TY + 4, sz, sx + 5, TY + 4, sz + 4, "minecraft:light_blue_wool")
    bb.fill(sx + 1, TY + 1, sz + 2, sx + 4, TY + 1, sz + 2, "minecraft:spruce_slab[type=top]")
    bb.set(sx + 2, TY + 2, sz + 2, "minecraft:brewing_stand")
    bb.set(sx + 3, TY + 2, sz + 2, "minecraft:cauldron")
    for i, x in enumerate(range(X1 - 8, X2 + 10, 8)):
        if abs(x - MX) > 6:
            lamp_post(bb, x, TY + 1, Z2 + 21, h=4)
    return taken


def roots_over_paths(bb, rng):
    """Mangrove roots arching over the street, as in all the groves."""
    for (x, z) in ((20, Z2 + 14), (N - 22, Z2 + 12), (MX + 2, 18)):
        if not land(np.array([x]), np.array([z]))[0]:
            continue
        yb = hy(x, z)
        for i in range(40):
            t = i / 39
            rx, rz = x + (t - 0.5) * 2, z + (t - 0.5) * 26
            ry = yb + int(round(11 * math.sin(t * math.pi))) - 1
            bb.fill_where(int(rx) - 2, ry - 1, int(rz) - 2, int(rx) + 2, ry + 1, int(rz) + 2,
                          lambda X, Y, Z, rx=rx, rz=rz, ry=ry: (X - rx) ** 2 + (Z - rz) ** 2 + ((Y - ry) * 1.2) ** 2 <= 2.4, YWOOD)


def design():
    bb = BigBuild(seed=4710, y_min=-14, y_max=112)
    tracker = P.PropTracker(4710)
    audit = []
    rng = np.random.default_rng(4710)
    terrain(bb)
    taken = []
    for i, (x, z, r, h) in enumerate(TREES):
        taken.append(yarukiman(bb, x, z, r, h, rng, number="1" if i == 0 else None))
    shell(bb)
    front(bb)
    lobby(bb, tracker, audit)
    auditorium(bb)
    stage(bb)
    backstage(bb, tracker, audit)
    taken += street(bb, tracker, audit, rng, [(t[0] + 6, t[1] + 6, t[2] - 6, t[3] - 6) for t in taken])
    roots_over_paths(bb, rng)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 4790, density=0.3,
              kinds=["minecraft:short_grass", "minecraft:fern", "minecraft:tall_grass", "minecraft:large_fern"], flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~paved(X, Z))
    bubbles(bb, rng, taken)
    return bb, audit


def steady(b):
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(X1 + 2, TY + 2, Z1 + 3, "treasure", "east") if False else None
    b.chest(X1 + 31, TY + 1, Z1 + 3, "treasure", "south")
    b.chest(X1 + 6, TY + 2, STAGE_Z[1] + 3, "celestial", "south")
    b.guards("marine", ((MX - 6, Z2 + 11), (MX + 6, Z2 + 11), (MX - 20, Z2 + 18), (MX + 20, Z2 + 18)), y=TY + 1)
    b.guards("cp_agent", ((MX, BACK_Z - 2),), y=TY + 1)
    return b, 0
