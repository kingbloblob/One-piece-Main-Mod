"""Drum Castle v3 (2026-10-30 redo at true scale): Drum Island and the Drum Rockies (dossier: mcb/dossiers/drum_castle.md).

Silhouette first: the Drum Rockies are enormous sheer cylinders of grey rock, flat-topped and snow-capped, and the
castle is tiny on the top of the tallest one. Here the main drum is 54 across and 150 high, with four lower drums
(70-110 high) round it, all rising out of a snowy island in a cold sea. On the summit: Dr. Kureha's three-storey
snow-brick castle with four blue-capped corner towers and the keep's pale blue onion dome, Hiluluk's Jolly Roger,
the cannons on the rim and the pink snow. Inside: the clinic and lab, great hall, library, kitchen, Chopper's and
Kureha's rooms, the old king's armory. A hidden stair winds up inside the rock; the ropeway runs all the way down to
Bighorn, an organic snowed-in town of timber houses packed round a plaza and along curving lanes, in spruce woods.
200 x 200, summit at 150, flag near 215. y 0 = sea level. (v3)"""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     tier, cornice, stair_core, set_if_air, onion_dome)
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import terrain3 as T3
from mcb.lotpack import pack_houses

SID = "drum_castle"
TITLE = "Drum Castle"
CUTS = [3, 76, 83]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False

N = 200
MX, MZ, MR, TOP = 112, 78, 27, 150
PEAKS = ((44, 66, 17, 110), (168, 50, 15, 96), (160, 132, 13, 80), (62, 22, 11, 70))
ISLE = NT.outline(100, 100, 86, 2810, wobble=0.10)
TOWN = (28, 104, 120, 176)                      # Bighorn's area (x1, z1, x2, z2)
PLAZA = (70, 140)
SNOWB = "onepiece:snow_bricks"
STONE = "minecraft:stone_bricks"
STONE_ST = "minecraft:stone_brick_stairs"
ROOF_ST = "minecraft:deepslate_tile_stairs"
PINK = "minecraft:pink_concrete_powder"
LEAF = "minecraft:spruce_leaves[distance=7,persistent=true,waterlogged=false]"
COLD = dict(walls=["minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks"],
            frame="minecraft:stripped_dark_oak_log", base=["minecraft:cobblestone", "minecraft:stone_bricks",
                                                           "minecraft:mossy_cobblestone"],
            floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks")

HILULUK = ("##...p...p...##",
           ".##...###...##.",
           ".p.#.#####.#.p.",
           "....#######....",
           "p...#..#..#...p",
           ".p..#######..p.",
           ".....##.##.....",
           "p..#.#####.#..p",
           ".##..#.#.#..##.",
           "##...........##",
           "...p...p...p...")

CAS = (MX - 19, MZ - 14, MX + 19, MZ + 10)       # castle footprint
G = TOP + 1
FH = 7


def _hmap():
    X, Z = T3.grid(N)
    d = ISLE(X, Z)
    hill = 2 + 9 * NT.fbm(X, Z, 2811, 22) * np.clip((d - 4) / 18.0, 0, 1)
    flat = (X >= TOWN[0] - 4) & (X <= TOWN[2] + 4) & (Z >= TOWN[1] - 4) & (Z <= TOWN[3] + 4)
    hill = np.where(flat, np.minimum(hill, 2 + 2 * NT.noise(X, Z, 2812, 15)), hill)
    hill = np.where(np.hypot(X - MX, Z - MZ) < MR + 14, 1, hill)
    h = np.where(d >= 1, np.maximum(1, hill), -99)
    return np.round(h).astype(int), d >= 1


HMAP, LAND = _hmap()


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


SNOWY = [("minecraft:snow_block", 0.55), ("minecraft:powder_snow", 0.0), ("minecraft:grass_block[snowy=true]", 0.15),
         ("minecraft:podzol[snowy=true]", 0.1), ("minecraft:packed_ice", 0.05), ("minecraft:stone", 0.07), ("minecraft:gravel", 0.08)]


def ground(bb, rng):
    hf = lambda XX, ZZ: HMAP[XX.astype(int), ZZ.astype(int)]
    NT.cover(bb, 0, 0, N - 1, N - 1, hf, [r for r in SNOWY if r[1] > 0], 2813,
             mask=lambda XX, ZZ: LAND[XX.astype(int), ZZ.astype(int)], core="minecraft:stone", base=-14)
    T3.sea(bb, N, LAND, 100, 100, 98, 2814, deep=-18, shelf=12, floor="minecraft:gravel", y_min=-24)
    # ice floes on the cold sea
    for _ in range(60):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if not LAND[x, z] and (bb.get_region(x, 0, z, x, 0, z)[0, 0, 0] > 1):
            r = rng.uniform(1.0, 2.8)
            bb.fill_where(x - 3, 0, z - 3, x + 3, 0, z + 3, lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) &
                          ~LAND[np.clip(X, 0, N - 1), np.clip(Z, 0, N - 1)], "minecraft:packed_ice")
    for _ in range(700):
        x, z = int(rng.integers(N)), int(rng.integers(N))
        if LAND[x, z]:
            set_if_air(bb, x, hy(x, z) + 1, z, "minecraft:snow[layers=%d]" % int(rng.integers(1, 3)))


def drum(bb, cx, cz, R, top, seed):
    """A sheer drum-shaped rock column: banded strata, snow ledges every few layers, icicles, a snowy cap."""
    for y in range(-8, top + 1):
        rr = R * (1.16 - 0.16 * max(y, 0) / top) + 0.8 * math.sin(y * 0.5 + seed) + (3.5 * max(0, 6 - y) / 6.0)
        blk = "minecraft:stone" if (y // 4 + seed) % 3 else "minecraft:andesite"
        if y % 13 == 7:
            blk = "minecraft:diorite"
        bb.fill_where(cx - R - 9, y, cz - R - 9, cx + R + 9, y, cz + R + 9,
                      lambda X, yy, Z, rr=rr: (X - cx) ** 2 + (Z - cz) ** 2 <= rr * rr, blk)
        if y % 6 == 3:
            bb.fill_where(cx - R - 9, y, cz - R - 9, cx + R + 9, y, cz + R + 9,
                          lambda X, yy, Z, rr=rr: np.abs(np.sqrt((X - cx) ** 2 + (Z - cz) ** 2) - rr - 0.4) < 0.7,
                          "minecraft:snow_block")
    for a in range(0, 360, 7):
        t = math.radians(a + seed * 17)
        k = (a * 7 + seed) % 5
        for y in range(9 + k * 6, top - 4, 24):
            rr = R * (1.16 - 0.16 * y / top) + 0.8 * math.sin(y * 0.5 + seed)
            ix, iz = round(cx + (rr + 0.6) * math.cos(t)), round(cz + (rr + 0.6) * math.sin(t))
            for yy in range(y - 3, y + 1):
                set_if_air(bb, ix, yy, iz, "minecraft:packed_ice")
    bb.fill_where(cx - R - 3, top, cz - R - 3, cx + R + 3, top, cz + R + 3,
                  lambda X, yy, Z: (X - cx) ** 2 + (Z - cz) ** 2 <= (R + 0.5) ** 2, "minecraft:snow_block")


def hidden_stair(bb):
    """A stair winding up inside the main column, from a door at its foot to the summit courtyard behind the castle."""
    sx, sz = MX + 6, MZ + 12
    bb.fill(sx - 1, 1, sz - 1, sx + 7, TOP, sz + 7, AIR)
    P.square_spiral_stair(bb, sx, 1, sz, 7, TOP, "minecraft:stone_brick_stairs", core="minecraft:stone_bricks")
    # the tunnel from the cliff foot to the shaft (south face)
    for z in range(sz + 7, MZ + MR + 4):
        bb.fill(sx + 2, 1, z, sx + 4, 4, z, AIR)
        bb.set(sx + 3, 5, z, "minecraft:stone_bricks")
    for z in range(sz + 8, MZ + MR + 3, 5):
        bb.set(sx + 3, 4, z, "minecraft:lantern[hanging=true]")
    bb.fill(sx + 1, 1, MZ + MR + 2, sx + 5, 6, MZ + MR + 2, STONE)
    bb.fill(sx + 2, 1, MZ + MR + 2, sx + 4, 4, MZ + MR + 2, AIR)
    # the exit on the summit, a little stone hut with a door
    bb.fill(sx - 1, G, sz - 1, sx + 7, G + 4, sz + 7, SNOWB)
    bb.fill(sx, G, sz, sx + 6, G + 3, sz + 6, AIR)
    bb.fill(sx - 1, G + 5, sz - 1, sx + 7, G + 5, sz + 7, "minecraft:spruce_slab[type=bottom]")
    bb.fill(sx + 3, G, sz - 1, sx + 3, G + 1, sz - 1, AIR)


def castle(bb, tracker, audit):
    x1, z1, x2, z2 = CAS
    bb.fill(x1 - 2, G - 1, z1 - 2, x2 + 2, G - 1, z2 + 2, STONE)
    top = tier(bb, x1, z1, x2, z2, G - 1, 3, FH, SNOWB, "minecraft:light_blue_stained_glass_pane", STONE_ST,
               pilaster=STONE, band="minecraft:stone_bricks", plate="minecraft:spruce_planks", top_plate=SNOWB,
               every=3, pil_every=4, win_h=3)
    cornice(bb, x1, z1, x2, z2, top, STONE_ST)
    core = (x2 - 7, z1 + 2)
    stair_core(bb, core[0], core[1], 5, G, top, [G - 1 + FH * k for k in range(4)], SNOWB, STONE_ST)
    keep = [(core[0] - 1, core[1] - 1, core[0] + 5, core[1] + 5)]
    kinds = [["bedroom", "workshop", "kitchen", "storage"], ["library", "living", "bedroom"], ["bedroom", "library", "workshop"]]
    for k in range(3):
        y = G + FH * k
        if k == 0:
            # the great hall in the middle of the ground floor, rooms either end
            hx1, hx2 = x1 + 12, x2 - 12
            wing_floor(bb, x1 + 1, z1 + 1, hx1 - 2, z2 - 1, y, FH - 1, SNOWB, seed_of("drum", k, 0), tracker,
                       ["bedroom", "workshop"], corridor="z", cw=3, audit=audit, max_room=10, wood="spruce")
            wing_floor(bb, hx2 + 2, z1 + 1, x2 - 1, z2 - 1, y, FH - 1, SNOWB, seed_of("drum", k, 1), tracker,
                       ["kitchen", "storage"], corridor="z", cw=3, audit=audit, max_room=10, wood="spruce", keep=keep)
            bb.fill(hx1 - 1, y, z1 + 1, hx1 - 1, y + FH - 2, z2 - 1, SNOWB)
            bb.fill(hx2 + 1, y, z1 + 1, hx2 + 1, y + FH - 2, z2 - 1, SNOWB)
            for zz in (MZ - 2, MZ - 1):
                bb.fill(hx1 - 1, y, zz, hx1 - 1, y + 2, zz, AIR)
                bb.fill(hx2 + 1, y, zz, hx2 + 1, y + 2, zz, AIR)
            bb.fill(hx1, y - 1, z1 + 1, hx2, y - 1, z2 - 1, "minecraft:polished_andesite")
            bb.fill(hx1 + 2, y - 1, MZ - 3, hx2 - 2, y - 1, MZ, "minecraft:red_wool")
            bb.set((hx1 + hx2) // 2, y + FH - 2, MZ - 2, "onepiece:chandelier[facing=north]")
            for x in (hx1 + 1, hx2 - 1):
                for z in (z1 + 2, z2 - 2):
                    bb.fill(x, y, z, x, y + FH - 2, z, STONE)
            bb.fill(hx1 + 2, y, z1 + 1, hx2 - 2, y + 1, z1 + 1, "minecraft:bookshelf")
        else:
            wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, FH - 1, SNOWB, seed_of("drum", k), tracker, kinds[k],
                       corridor="x", cw=3, audit=audit, max_room=11, wood="spruce", keep=keep,
                       carpet=(None, "minecraft:red_carpet"))
    # the gate (south) onto the summit courtyard
    gx = MX
    bb.fill(gx - 2, G, z2, gx + 2, G + 4, z2, AIR)
    P.arched_opening(bb, "x", gx, G, z2, 5, 6, depth=1, trim=STONE)
    for x in (gx - 4, gx + 4):
        bb.fill(x, G, z2 + 1, x, G + 3, z2 + 1, "minecraft:spruce_fence")
        bb.set(x, G + 4, z2 + 1, "minecraft:lantern[hanging=false]")
    # roof, corner towers, the keep with the onion dome
    P.hip_roof(bb, x1 - 2, z1 - 2, x2 + 2, z2 + 2, top + 1, ROOF_ST, overhang=0)
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(tx, G - 1, tz, 5, top + 14, SNOWB)
        bb.cylinder(tx, G, tz, 4, top + 13, AIR)
        for fy in [G - 1 + FH * k for k in range(1, 4)] + [top + 7]:
            bb.cylinder(tx, fy, tz, 4, fy, "minecraft:spruce_planks")
        bb.fill(tx, G, tz - 3 if tz == z2 else tz + 3, tx, top + 7, tz - 3 if tz == z2 else tz + 3,
                "minecraft:ladder[facing=%s]" % ("south" if tz == z2 else "north"))
        for fy in [G - 1 + FH * k for k in range(1, 4)] + [top + 7]:
            bb.set(tx, fy, tz - 3 if tz == z2 else tz + 3, "minecraft:ladder[facing=%s]" % ("south" if tz == z2 else "north"))
        dz = 1 if tz == z1 else -1
        dx = 1 if tx == x1 else -1
        for fy in [G + FH * k for k in range(3)]:
            bb.fill(tx + dx * 4, fy, tz + dz * 4, tx + dx * 5, fy + 1, tz + dz * 5, AIR)
        for y in range(G + 3, top + 12, 5):
            for (ox, oz) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
                bb.fill(tx + ox, y, tz + oz, tx + ox, y + 1, tz + oz, "minecraft:light_blue_stained_glass_pane")
        for a in range(0, 360, 15):
            t = math.radians(a)
            set_if_air(bb, round(tx + 5 * math.cos(t)), top + 15, round(tz + 5 * math.sin(t)), "minecraft:stone_brick_wall")
        P.cone_roof(bb, tx, top + 15, tz, 6, 14, "minecraft:blue_terracotta", hollow=False)
        bb.set(tx, top + 29, tz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    kx, kz = MX, MZ - 2
    bb.cylinder(kx, top, kz, 7, top + 20, SNOWB)
    bb.cylinder(kx, top + 1, kz, 6, top + 19, AIR)
    bb.cylinder(kx, top + 10, kz, 6, top + 10, "minecraft:spruce_planks")
    for y in range(top + 3, top + 19, 4):
        for (ox, oz) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
            bb.fill(kx + ox, y, kz + oz, kx + ox, y + 2, kz + oz, "minecraft:light_blue_stained_glass_pane")
    bb.cylinder(kx, top + 20, kz, 8, top + 20, STONE)
    dome_top = onion_dome(bb, kx, top + 21, kz, 8, "minecraft:light_blue_terracotta")
    bb.fill(kx, dome_top + 1, kz, kx, dome_top + 12, kz, "minecraft:dark_oak_fence")
    bb.set(kx, dome_top + 13, kz, "minecraft:gold_block")
    for r, row in enumerate(HILULUK):
        for c, ch in enumerate(row):
            bb.set(kx, dome_top + 12 - r, kz + 1 + c,
                   {"#": "minecraft:white_wool", "p": "minecraft:pink_wool"}.get(ch, "minecraft:black_wool"))
    # a ladder from the top floor up into the keep
    bb.fill(kx + 5, G + FH * 2, kz, kx + 5, top + 10, kz, "minecraft:ladder[facing=west]")
    bb.fill(kx + 5, top, kz, kx + 5, top + 10, kz, "minecraft:ladder[facing=west]")
    return top


def summit(bb, rng):
    """Parapet round the rim, the cannons, pink snow where Hiluluk's powder fell, the courtyard."""
    def ring(X, y, Z):
        d = np.sqrt((X - MX) ** 2 + (Z - MZ) ** 2)
        return (d >= MR - 1.2) & (d <= MR + 0.4)
    bb.fill_where(MX - MR - 2, G, MZ - MR - 2, MX + MR + 2, G, MZ + MR + 2, ring, SNOWB)
    bb.fill_where(MX - MR - 2, G + 1, MZ - MR - 2, MX + MR + 2, G + 1, MZ + MR + 2,
                  lambda X, y, Z: ring(X, y, Z) & ((X + Z) % 2 == 0), "minecraft:stone_brick_wall")
    for a in list(range(55, 130, 15)) + list(range(235, 310, 15)):
        t = math.radians(a)
        cx, cz = round(MX + (MR - 3) * math.cos(t)), round(MZ + (MR - 3) * math.sin(t))
        out = "south" if 45 <= a <= 135 else "north"
        dz = 1 if out == "south" else -1
        bb.set(cx, G, cz, "minecraft:spruce_planks")
        bb.set(cx, G, cz - dz, "minecraft:spruce_slab[type=bottom]")
        bb.fill(cx, G + 1, cz, cx, G + 1, cz + dz, "minecraft:polished_basalt[axis=z]")
        for s in (-1, 1):
            bb.set(cx + s, G, cz, "minecraft:dark_oak_trapdoor[facing=%s,half=bottom,open=true,powered=false,waterlogged=false]" % ("east" if s > 0 else "west"))
        for k in (2, 3):
            bb.set(cx, G + 1, cz + dz * k, AIR)
    for x in range(MX - MR, MX + MR + 1):
        for z in range(MZ - MR, MZ + MR + 1):
            if (x - MX) ** 2 + (z - MZ) ** 2 > (MR - 1.5) ** 2:
                continue
            if (bb.get_region(x, G, z, x, G + 30, z) > 1).any():
                continue
            n = math.sin(x * 0.7) + math.cos(z * 0.6) + rng.random()
            if n > 0.4:
                bb.set(x, TOP, z, PINK)
            if rng.random() < 0.1:
                bb.set(x, G, z, "minecraft:pink_petals[facing=north,flower_amount=4]")


def ropeway(bb):
    """The ropeway cable from the summit down to Bighorn's plaza: a summit tower, a valley tower and a gondola."""
    sx, sz = MX - 18, MZ + 16
    ex, ez = PLAZA[0] + 14, PLAZA[1] - 16
    ey = hy(ex, ez)
    bb.fill(sx, G, sz, sx, G + 6, sz, "minecraft:dark_oak_log[axis=y]")
    bb.fill(ex, ey + 1, ez, ex, ey + 14, ez, "minecraft:dark_oak_log[axis=y]")
    bb.fill(ex - 3, ey + 1, ez - 3, ex + 3, ey + 1, ez + 3, "minecraft:spruce_planks")
    bb.fill(ex - 3, ey + 2, ez - 3, ex + 3, ey + 2, ez + 3, "minecraft:spruce_fence")
    bb.fill(ex - 2, ey + 2, ez - 2, ex + 2, ey + 2, ez + 2, AIR)
    bb.set(ex - 3, ey + 2, ez, AIR)
    n = 400
    pts = []
    for i in range(n + 1):
        t = i / n
        x = sx + (ex - sx) * t
        z = sz + (ez - sz) * t
        y = (G + 6) + (ey + 14 - (G + 6)) * t - 16 * math.sin(t * math.pi)
        pts.append((round(x), round(y), round(z)))
        set_if_air(bb, round(x), round(y), round(z), "minecraft:dark_oak_fence")
    for frac in (0.35, 0.7):
        gx, gy, gz = pts[int(n * frac)]
        bb.fill(gx - 2, gy - 6, gz - 2, gx + 2, gy - 2, gz + 2, "minecraft:red_terracotta")
        bb.fill(gx - 2, gy - 4, gz - 1, gx + 2, gy - 3, gz + 1, "minecraft:glass_pane")
        bb.fill(gx - 1, gy - 4, gz - 2, gx + 1, gy - 3, gz + 2, "minecraft:glass_pane")
        bb.fill(gx - 1, gy - 5, gz - 1, gx + 1, gy - 3, gz + 1, AIR)
        bb.fill(gx, gy - 1, gz, gx, gy - 1, gz, "minecraft:iron_chain[axis=y]")


LANES = [((70, 140), (40, 112)), ((70, 140), (104, 112)), ((70, 140), (34, 170)), ((70, 140), (112, 172)),
         ((70, 140), (70, 186)), ((104, 112), (MX - 14, MZ + MR + 8))]


def lane_d(X, Z):
    """Distance to the nearest (gently curving) lane of Bighorn."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    best = np.full(np.broadcast(X, Z).shape, 99.0)
    for (a, b) in LANES:
        ax, az = a; bx, bz = b
        vx, vz = bx - ax, bz - az
        t = np.clip(((X - ax) * vx + (Z - az) * vz) / float(vx * vx + vz * vz), 0, 1)
        px = ax + vx * t + 5 * np.sin(t * math.pi) * (-vz) / math.hypot(vx, vz)
        pz = az + vz * t + 5 * np.sin(t * math.pi) * (vx) / math.hypot(vx, vz)
        best = np.minimum(best, np.hypot(X - px, Z - pz))
    return best


def bighorn(bb, rng, tracker, audit):
    """Bighorn: snowy timber houses packed round a plaza and along curving lanes (no grid), the well, lamp posts."""
    px, pz = PLAZA
    py = hy(px, pz)
    X, Z = T3.grid(N)
    LD = lane_d(X, Z)
    lane = LAND & (LD <= 1.6) & (np.hypot(X - MX, Z - MZ) > MR + 4)
    plaza = np.hypot(X - px, Z - pz) <= 11
    for y in range(int(HMAP.min()), int(HMAP.max()) + 1):
        m = lane & (HMAP == y) & ~plaza
        if m.any():
            bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda XX, yy, ZZ, m=m: m & ((XX * 7 + ZZ * 3) % 5 != 0), "minecraft:packed_ice")
            bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda XX, yy, ZZ, m=m: m & ((XX * 7 + ZZ * 3) % 5 == 0), "minecraft:snow_block")
    bb.fill_where(px - 12, py, pz - 12, px + 12, py, pz + 12, lambda XX, yy, ZZ: np.hypot(XX - px, ZZ - pz) <= 11, "minecraft:polished_andesite")
    bb.fill_where(px - 12, py - 3, pz - 12, px + 12, py - 1, pz + 12, lambda XX, yy, ZZ: np.hypot(XX - px, ZZ - pz) <= 11, "minecraft:stone")
    bb.fill_where(px - 12, py + 1, pz - 12, px + 12, py + 8, pz + 12, lambda XX, yy, ZZ: np.hypot(XX - px, ZZ - pz) <= 11, AIR)
    bb.fill(px - 2, py, pz - 2, px + 2, py + 1, pz + 2, "minecraft:cobblestone")
    bb.fill(px - 1, py - 3, pz - 1, px + 1, py + 1, pz + 1, "minecraft:water[level=0]")
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bb.fill(px + dx, py + 2, pz + dz, px + dx, py + 4, pz + dz, "minecraft:spruce_fence")
    bb.fill(px - 2, py + 5, pz - 2, px + 2, py + 5, pz + 2, "minecraft:spruce_slab[type=bottom]")
    for a in range(0, 360, 45):
        t = math.radians(a)
        lamp_post(bb, round(px + 10 * math.cos(t)), py + 1, round(pz + 10 * math.sin(t)))
    ok = lambda x, z: (0 <= x < N and 0 <= z < N and LAND[x, z] and LD[x, z] > 2.2 and not plaza[x, z]
                       and math.hypot(x - MX, z - MZ) > MR + 8 and ISLE(np.array([x]), np.array([z]))[0] > 9
                       and all(math.hypot(x - a, z - b) > r + 6 for (a, b, r, h) in PEAKS))
    roofs = ["minecraft:spruce_stairs", "minecraft:dark_oak_stairs", "minecraft:deepslate_tile_stairs"]
    pals = [COLD, dict(COLD, walls=["minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:white_terracotta"]),
            dict(COLD, walls=["minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:stripped_dark_oak_log[axis=y]"])]
    face = lambda cx, cz: 0 if cz < pz - 4 else 2 if cz > pz + 4 else (1 if cx < px else 3)
    placed = pack_houses(bb, hy, ok, (14, 92, 132, 190), 46, seed_of("bighorn"), tracker, pals, roofs, focus=PLAZA,
                         sizes=(7, 11), floors=(1, 3), kinds=("kitchen", "bedroom", "dining", "storeroom"), max_step=4)
    # snow on the roofs' flat bits and lanterns by doors come from the house kit; a few market stalls round the plaza
    for k, a in enumerate(range(20, 360, 70)):
        t = math.radians(a)
        sx, sz = round(px + 7 * math.cos(t)), round(pz + 7 * math.sin(t))
        bb.set(sx, py + 1, sz, "minecraft:barrel[facing=up,open=false]")
        bb.set(sx + 1, py + 1, sz, "minecraft:spruce_fence"); bb.set(sx + 1, py + 2, sz, "minecraft:white_carpet")
    return placed


def forest(bb, rng):
    """Spruce woods in noise patches round the town and the drums."""
    dens = NT.fbm(np.arange(N)[:, None], np.arange(N)[None, :], 2815, 26)
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if not LAND[x, z] or dens[x, z] < 0.45 or ISLE(np.array([x]), np.array([z]))[0] < 4:
            continue
        if (x - MX) ** 2 + (z - MZ) ** 2 < (MR + 8) ** 2 or any((x - a) ** 2 + (z - b) ** 2 < (r + 6) ** 2 for (a, b, r, h) in PEAKS):
            continue
        y0 = hy(x, z)
        if (bb.get_region(x - 2, y0 + 1, z - 2, x + 2, y0 + 10, z + 2) > 1).any():
            continue
        h = int(rng.integers(8, 15))
        bb.fill(x, y0 + 1, z, x, y0 + h, z, "minecraft:spruce_log[axis=y]")
        for kk in range(h - 7, h + 1):
            r = max(0.6, (h - kk) * 0.45 + 0.5)
            bb.fill_where(x - 4, y0 + kk, z - 4, x + 4, y0 + kk, z + 4,
                          lambda X, y, Z, r=r: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) & ~((X == x) & (Z == z)), LEAF, only_empty=True)
        bb.set(x, y0 + h + 1, z, "minecraft:snow_block")
        k += 1
        if k >= 240:
            break


def design():
    bb = BigBuild(seed=281, y_min=-26, y_max=TOP + 75)
    tracker = P.PropTracker(281)
    audit = []
    rng = np.random.default_rng(281)
    ground(bb, rng)
    drum(bb, MX, MZ, MR, TOP, 0)
    for i, (px, pz, pr, ph) in enumerate(PEAKS):
        drum(bb, px, pz, pr, ph, i + 1)
    hidden_stair(bb)
    castle(bb, tracker, audit)
    summit(bb, rng)
    ropeway(bb)
    bighorn(bb, rng, tracker, audit)
    forest(bb, rng)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    x1, z1, x2, z2 = CAS
    b.npc(MX, G, MZ - 2, "chopper", False)
    b.chest(x1 + 3, G, z1 + 3, "medicine", "east")
    b.chest(x2 - 3, G + FH, z2 - 3, "medicine", "west")
    return b, 0
