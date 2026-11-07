"""Shift Station v2, redesigned with the Minecraft Builder skill: the Puffing Tom's switching station on a little
island in the open sea between Water 7, San Faldo, St. Poplar and Pucci (Kokoro's station, episode 229 / ch. 322).

A small grassy island with a rocky hill to the west and a sand beach on the east, where the sea-train rails run out
into the water just under the surface. The line comes in from the east, splits at the switch tower (the "shift")
into three tracks that fan out over the sea on trestles, and ends at a buffer on the island.

On the island: the station house (two storeys of timber and brick: waiting room, ticket office, luggage room and
Kokoro's office, with a tall clock tower and a "SHIFT STATION" board over the platform); the long island platform
between the two tracks under a striped canopy with benches and lamps; the Puffing Tom itself standing at the
platform (paddle-wheel steam engine, tender and three carriages); Kokoro and Chimney's house-bar with Kokoro's
drinks counter, a stack of crates and Gonbe's hutch; the engine shed with a work pit; the coal stage, water tower
and a few staff cottages on the hill; a jetty with rowboats. 144 x 112, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, tier, cornice, lamp_post, steady, house_module, place_house
from mcb.kit_interiors import furnish_kit, bench, bar_counter, table_group, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.lotpack import pack_houses

SID = "sea_train_station"
TITLE = "Shift Station (Puffing Tom)"
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 144, 112
T1, T2 = 54, 66                     # the two station tracks (z)
PZ1, PZ2 = 57, 63                   # island platform between them
SHORE = 84                          # rails leave the land here (x)
FORK = 104                          # the switch tower
_MAIN = NT.outline(52, 58, 46, 7701, wobble=0.08)
_LOBES = [NT.outline(28, 26, 20, 7708, wobble=0.1), NT.outline(27, 92, 19, 7709, wobble=0.1)]


def _ISLE(X, Z):
    d = _MAIN(X, Z)
    for f in _LOBES:
        d = np.maximum(d, f(X, Z))
    return d
MEADOW = NT.MEADOW
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.25), ("minecraft:mossy_cobblestone", 0.15),
        ("minecraft:cobblestone", 0.1), ("minecraft:grass_block", 0.1)]
BRICK = ["minecraft:bricks", "minecraft:bricks", "minecraft:granite"]
YARD = [("minecraft:gravel", 0.0), ("minecraft:coarse_dirt", 0.25), ("minecraft:packed_mud", 0.2), ("minecraft:dirt_path", 0.25),
        ("minecraft:grass_block", 0.3)]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)                                   # >0 inside the island outline, grows inwards
    hill = 2 + np.clip((44 - X) / 30.0, 0, 1) ** 1.2 * (6 + 8 * NT.fbm(X, Z, 7702, 20)) + np.clip((34 - Z) / 16.0, 0, 1) * 5 + np.clip((Z - 92) / 12.0, 0, 1) * 3
    h = np.where(d < 9, -4 + (hill + 4) * np.clip(d / 9.0, 0, 1) ** 1.2, hill)
    yard = (X > 12) & (X < SHORE - 6) & (Z > 34) & (Z < 90)
    h = np.where(yard & (d > 6), np.minimum(h, 1) * 0 + 1, h)  # the station yard is level at y 1
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def terrain(bb):
    steep = lambda X, Z: height(X, Z) > 6
    yard = lambda X, Z: (X > 12) & (X < SHORE - 4) & (Z > 34) & (Z < 90) & (height(X, Z) == 1)
    beach = lambda X, Z: land(X, Z) & (height(X, Z) <= 2) & (_ISLE(X, Z) < 9)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, MEADOW, 7703, mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ~yard(X, Z) & ~beach(X, Z),
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, ROCK, 7704, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, YARD, 7705, mask=lambda X, Z: yard(X, Z) & ~beach(X, Z), core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:sand", 0.8), ("minecraft:gravel", 0.0), ("minecraft:sandstone", 0.1),
                                                 ("minecraft:suspicious_sand", 0.0), ("minecraft:clay", 0.1)], 7706,
             mask=beach, under="minecraft:sandstone", core="minecraft:stone", base=-6)
    wet = lambda X, Z: ~land(X, Z) & (_ISLE(X, Z) > -10)          # seabed only near the shore, never a square plate
    bed = lambda X, Z: np.minimum(height(X, Z), -1) - np.clip(-_ISLE(X, Z) / 6.0, 0, 6).astype(int)
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:sandstone")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 7707, density=0.22, kinds=["minecraft:short_grass", "minecraft:short_grass",
              "minecraft:fern", "minecraft:tall_grass"], flowers=["minecraft:poppy", "minecraft:cornflower", "minecraft:oxeye_daisy"],
              mask=lambda X, Z: land(X, Z) & ~yard(X, Z))


# ------------------------------------------------------------------ the line
RAIL_EW = "minecraft:rail[shape=east_west]"


def rail_at(bb, x, z, shape="east_west"):
    """One rail cell: on land on a gravel bed at y 1 (rail y 2), over the sea on a plank deck just under the surface."""
    if land(x, z) and hy(x, z) >= 1:
        bb.set(x, 1, z, "minecraft:gravel" if (x + z) % 3 else "minecraft:andesite")
        bb.set(x, 0, z, "minecraft:stone")
        bb.set(x, 2, z, f"minecraft:rail[shape={shape}]")
        bb.fill(x, 3, z, x, 8, z, AIR)
    else:
        bb.set(x, -1, z, "minecraft:spruce_planks")
        bb.set(x, 0, z, f"minecraft:rail[shape={shape},waterlogged=true]")


def track(bb, pts):
    """Rails along a polyline of (x, z) points; diagonals become zig-zags. Trestle legs every 6 over water."""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0))
        prev = None
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); z = round(z0 + (z1 - z0) * i / n)
            if prev and prev[0] != x and prev[1] != z:       # keep the rails connected: add the corner cell
                rail_at(bb, x, prev[1], "east_west")
            rail_at(bb, x, z, "east_west" if z1 == z0 else ("east_west" if abs(x1 - x0) >= abs(z1 - z0) else "north_south"))
            if not land(x, z) and x % 6 == 0:
                for dz in (-1, 1):
                    bb.fill(x, -9, z + dz, x, -1, z + dz, "minecraft:spruce_log[axis=y]")
            prev = (x, z)


def line(bb):
    # main line from the east, the switch, three tracks fanning out to Water 7 / San Faldo / St. Poplar
    track(bb, [(14, T1), (FORK, T1), (NX - 1, T1)])
    track(bb, [(14, T2), (SHORE + 8, T2), (FORK - 6, T1 + 2), (FORK, T1)])
    track(bb, [(FORK, T1), (FORK + 14, T1 - 10), (NX - 1, 8)])
    track(bb, [(FORK, T1), (FORK + 14, T1 + 10), (NX - 1, NZ - 8)])
    # ramps where the rails meet the shore: the land rails step down into the sea
    for z in (T1, T2):
        for x in range(SHORE - 6, SHORE + 2):
            if land(x, z) and hy(x, z) >= 1:
                continue
            bb.set(x, 1, z, AIR)
    # buffer stops at the land end
    for z in (T1, T2):
        bb.fill(12, 2, z - 1, 13, 3, z + 1, "minecraft:spruce_planks")
        bb.set(13, 4, z - 1, "minecraft:red_concrete"); bb.set(13, 4, z + 1, "minecraft:red_concrete")
        bb.set(14, 3, z, "minecraft:redstone_lamp[lit=true]")
    # the switch tower out at the fork: a white signal cabin on stilts with a lever frame and signal arms
    sx, sz = FORK - 4, T1 - 8
    for (a, b) in ((sx, sz), (sx + 6, sz), (sx, sz + 5), (sx + 6, sz + 5)):
        bb.fill(a, -9, b, a, 6, b, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(sx - 1, 6, sz - 1, sx + 7, 6, sz + 6, "minecraft:spruce_planks")
    bb.fill(sx, 7, sz, sx + 6, 11, sz + 5, "minecraft:white_terracotta")
    bb.fill(sx + 1, 7, sz + 1, sx + 5, 11, sz + 4, AIR)
    for x in range(sx + 1, sx + 6):
        bb.fill(x, 9, sz, x, 10, sz, "minecraft:glass_pane"); bb.fill(x, 9, sz + 5, x, 10, sz + 5, "minecraft:glass_pane")
        bb.set(x, 7, sz + 1, "minecraft:lever[face=floor,facing=south]")
    for z in range(sz + 1, sz + 5):
        bb.fill(sx + 6, 9, z, sx + 6, 10, z, "minecraft:glass_pane")
    bb.set(sx + 3, 8, sz + 6, AIR); bb.set(sx + 3, 7, sz + 5, AIR); bb.set(sx + 3, 8, sz + 5, AIR)
    bb.fill(sx + 3, 0, sz + 6, sx + 3, 6, sz + 6, "minecraft:ladder[facing=south]")
    bb.set(sx + 1, 7, sz + 4, "minecraft:spruce_stairs[facing=north]"); bb.set(sx + 5, 7, sz + 4, "minecraft:barrel[facing=up]")
    bb.set(sx + 3, 10, sz + 3, "minecraft:lantern[hanging=true]") if False else bb.set(sx + 3, 11, sz + 3, "minecraft:lantern[hanging=true]")
    P.hip_roof(bb, sx - 1, sz - 1, sx + 7, sz + 6, 12, "minecraft:dark_oak_stairs", ridge="minecraft:dark_oak_slab[type=bottom]", overhang=0)
    for (gx, gz) in ((FORK + 8, T1 - 5), (FORK + 8, T1 + 5), (SHORE + 4, T1 - 2)):
        bb.fill(gx, -9, gz, gx, 9, gz, "minecraft:iron_bars" if gx > SHORE + 4 else "minecraft:dark_oak_fence")
        bb.fill(gx, -1, gz, gx, 0, gz, "minecraft:stripped_spruce_log[axis=y]")
        bb.set(gx, 10, gz, "minecraft:redstone_lamp[lit=true]")
        bb.fill(gx + 1, 8, gz, gx + 3, 8, gz, "minecraft:red_concrete")
        bb.set(gx + 3, 8, gz, "minecraft:white_concrete")


# ------------------------------------------------------------------ the Puffing Tom
def puffing_tom(bb, xh, z):
    """Engine facing +x with its nose at xh, rails at y 2 (floor y 3). Big red paddle wheels each side, a tall flared
    stack, a round smokebox face with a lamp eye, a tender and three carriages behind."""
    # engine: boiler barrel x xh-14..xh-2, radius 2.5 round the axis y 6
    for x in range(xh - 14, xh - 1):
        for y in range(3, 10):
            for dz in range(-3, 4):
                if (y - 6) ** 2 + dz * dz <= 7.3:
                    bb.set(x, y, z + dz, "minecraft:black_concrete" if (x - xh) % 4 else "minecraft:gold_block")
    for y in range(3, 10):
        for dz in range(-3, 4):
            r2 = (y - 6) ** 2 + dz * dz
            if r2 <= 7.3:
                bb.set(xh - 1, y, z + dz, "minecraft:polished_blackstone" if r2 > 3 else "minecraft:iron_block")
    bb.set(xh, 6, z, "minecraft:redstone_lamp[lit=true]"); bb.set(xh, 7, z, "minecraft:iron_trapdoor[facing=east,half=bottom,open=true]")
    for dz in (-2, -1, 0, 1, 2):                                    # cow-catcher
        bb.set(xh, 3, z + dz, "minecraft:iron_bars"); bb.set(xh + 1, 3, z + dz, "minecraft:iron_bars" if abs(dz) < 2 else AIR)
    # the stack (flared top) and the steam dome
    sx = xh - 5
    bb.fill(sx, 10, z, sx, 14, z, "minecraft:black_concrete")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bb.set(sx + dx, 15, z + dz, "minecraft:polished_blackstone")
    bb.set(sx, 15, z, "minecraft:campfire[lit=true,signal_fire=true]")
    bb.set(xh - 9, 10, z, "minecraft:gold_block"); bb.set(xh - 9, 11, z, "minecraft:bell[attachment=floor,facing=east]")
    # cab
    cx0, cx1 = xh - 20, xh - 15
    bb.fill(cx0, 3, z - 3, cx1, 9, z + 3, "minecraft:red_terracotta")
    bb.fill(cx0 + 1, 4, z - 2, cx1 - 1, 8, z + 2, AIR)
    bb.fill(cx0 - 1, 10, z - 4, cx1 + 1, 10, z + 4, "minecraft:dark_oak_slab[type=bottom]")
    for x in (cx0 + 1, cx0 + 3):
        bb.fill(x, 6, z - 3, x + 1, 7, z - 3, "minecraft:glass_pane"); bb.fill(x, 6, z + 3, x + 1, 7, z + 3, "minecraft:glass_pane")
    bb.fill(cx0 + 2, 4, z - 3, cx0 + 2, 5, z - 3, AIR); bb.fill(cx0 + 2, 4, z + 3, cx0 + 2, 5, z + 3, AIR)
    bb.set(cx1 - 1, 4, z, "minecraft:blast_furnace[facing=west,lit=true]"); bb.set(cx1 - 1, 5, z - 1, "minecraft:lever[face=wall,facing=west]")
    bb.set(cx0 + 1, 4, z + 1, "minecraft:spruce_stairs[facing=east]"); bb.set(cx0 + 2, 8, z, "minecraft:lantern[hanging=true]")
    bb.fill(cx0, 3, z - 3, cx1 + 1, 3, z + 3, "minecraft:black_concrete")
    # the paddle wheels: three each side, red rims with iron spokes and hubs, half hidden by a wheel box
    for wx in (xh - 12, xh - 7):
        for side in (-1, 1):
            zz = z + side * 4
            for a in range(0, 360, 15):
                t = math.radians(a)
                bb.set(wx + round(3 * math.cos(t)), 5 + round(3 * math.sin(t)), zz, "minecraft:red_concrete")
            for a in range(0, 180, 45):
                t = math.radians(a)
                for r in (1, 2):
                    bb.set(wx + round(r * math.cos(t)), 5 + round(r * math.sin(t)), zz, "minecraft:iron_bars")
                    bb.set(wx - round(r * math.cos(t)), 5 - round(r * math.sin(t)), zz, "minecraft:iron_bars")
            bb.set(wx, 5, zz, "minecraft:iron_block")
            bb.fill(wx - 3, 9, zz, wx + 3, 9, zz, "minecraft:red_terracotta")
            bb.set(wx - 3, 8, zz, "minecraft:red_terracotta"); bb.set(wx + 3, 8, zz, "minecraft:red_terracotta")
    bb.fill(xh - 14, 3, z - 3, xh - 2, 3, z + 3, "minecraft:black_concrete")
    # tender (coal) and three carriages
    t0 = cx0 - 9
    bb.fill(t0, 3, z - 3, t0 + 7, 6, z + 3, "minecraft:black_concrete"); bb.fill(t0 + 1, 6, z - 2, t0 + 6, 7, z + 2, "minecraft:coal_block")
    for i in range(2):
        c1 = t0 - 2 - i * 17
        c0 = c1 - 14
        bb.fill(c0, 3, z - 3, c1, 3, z + 3, "minecraft:dark_oak_planks")
        bb.fill(c0, 4, z - 3, c1, 8, z + 3, "minecraft:white_terracotta")
        bb.fill(c0, 4, z - 3, c1, 4, z + 3, "minecraft:green_terracotta")
        bb.fill(c0 + 1, 4, z - 2, c1 - 1, 8, z + 2, AIR)
        bb.fill(c0, 9, z - 3, c1, 9, z + 3, "minecraft:green_terracotta")
        bb.fill(c0 + 1, 10, z - 2, c1 - 1, 10, z + 2, "minecraft:dark_oak_slab[type=bottom]")
        bb.fill(c0 - 1, 9, z - 4, c1 + 1, 9, z - 4, "minecraft:dark_oak_slab[type=top]"); bb.fill(c0 - 1, 9, z + 4, c1 + 1, 9, z + 4, "minecraft:dark_oak_slab[type=top]")
        for x in range(c0 + 2, c1 - 1, 3):
            bb.fill(x, 6, z - 3, x + 1, 7, z - 3, "minecraft:glass_pane"); bb.fill(x, 6, z + 3, x + 1, 7, z + 3, "minecraft:glass_pane")
        for x in range(c0 + 2, c1 - 1, 3):          # facing seat pairs either side of the aisle
            for dz in (-2, 2):
                bb.set(x, 4, z + dz, "minecraft:spruce_stairs[facing=east]")
                bb.set(x + 1, 4, z + dz, "minecraft:spruce_stairs[facing=west]")
        for x in range(c0 + 3, c1 - 1, 5):
            bb.set(x, 8, z, "minecraft:lantern[hanging=true]")
        bb.fill(c0 + 7, 4, z + 3, c0 + 7, 5, z + 3, AIR)          # platform-side door
        bb.fill(c0 + 7, 4, z + 3, c0 + 7, 4, z + 3, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]") if False else None
        for wx in (c0 + 3, c1 - 3):
            for side in (-1, 1):
                bb.set(wx, 2, z + side * 3, "minecraft:iron_block"); bb.set(wx + 1, 2, z + side * 3, "minecraft:iron_block")
        bb.fill(c1 + 1, 4, z, c1 + 1, 4, z, "minecraft:chain[axis=x]") if False else bb.set(c1 + 1, 4, z, "minecraft:iron_chain[axis=x]")


# ------------------------------------------------------------------ the platform and the station house
def platform(bb):
    x1, x2 = 18, SHORE - 2
    bb.fill(x1, 1, PZ1, x2, 2, PZ2, "minecraft:stone_bricks")
    bb.mix(x1, 2, PZ1, x2, 2, PZ2, ["minecraft:polished_andesite", "minecraft:smooth_stone", "minecraft:andesite"], [0.5, 0.35, 0.15])
    bb.fill(x1, 2, PZ1, x2, 2, PZ1, "minecraft:yellow_concrete"); bb.fill(x1, 2, PZ2, x2, 2, PZ2, "minecraft:yellow_concrete")
    bb.fill(x1, 3, PZ1, x2, 14, PZ2, AIR)
    # canopy: iron posts every 6 with a striped roof
    for x in range(x1 + 2, x2, 6):
        for z in (PZ1 + 1, PZ2 - 1):
            bb.fill(x, 3, z, x, 7, z, "minecraft:dark_oak_fence")
            bb.set(x, 8, z, "minecraft:stripped_dark_oak_log[axis=y]")
        bb.fill(x, 8, PZ1 + 1, x, 8, PZ2 - 1, "minecraft:stripped_dark_oak_log[axis=z]")
        bb.set(x, 7, (PZ1 + PZ2) // 2, "minecraft:lantern[hanging=true]")
    for x in range(x1, x2 + 1):
        for z in range(PZ1 - 1, PZ2 + 2):
            bb.set(x, 9, z, "minecraft:green_terracotta" if (x // 3) % 2 else "minecraft:white_terracotta")
        bb.set(x, 10, (PZ1 + PZ2) // 2, "minecraft:green_terracotta")
        bb.set(x, 8, PZ1 - 1, "minecraft:dark_oak_trapdoor[facing=north,half=top,open=false]")
        bb.set(x, 8, PZ2 + 1, "minecraft:dark_oak_trapdoor[facing=south,half=top,open=false]")
    # benches back to back down the middle, flower tubs, a clock and the name board
    for x in range(x1 + 4, x2 - 4, 6):
        bench(bb, x, 3, PZ1 + 2, 3, "north", wood="dark_oak")
        bench(bb, x, 3, PZ2 - 2, 3, "south", wood="dark_oak")
        bb.set(x + 4, 3, PZ1 + 3, "minecraft:potted_azure_bluet") if (x // 6) % 2 else bb.set(x + 4, 3, PZ1 + 3, "minecraft:barrel[facing=up]")
    mid = (x1 + x2) // 2
    bb.fill(mid - 1, 3, (PZ1 + PZ2) // 2, mid - 1, 7, (PZ1 + PZ2) // 2, "minecraft:dark_oak_fence")
    bb.set(mid - 1, 7, (PZ1 + PZ2) // 2 - 1, "minecraft:white_concrete"); bb.set(mid - 1, 7, (PZ1 + PZ2) // 2 + 1, "minecraft:white_concrete")
    # ramp off the platform's west end onto the yard
    for k in range(2):
        bb.fill(x1 - 1 - k, 2 - k, PZ1 + 1, x1 - 1 - k, 2 - k, PZ2 - 1, "minecraft:stone_brick_stairs[facing=east]")


def station_house(bb, tracker):
    x1, z1, x2, z2 = 20, 28, 62, T1 - 4
    y = 1
    top = tier(bb, x1, z1, x2, z2, y, 2, 6, BRICK, "minecraft:glass_pane", "minecraft:stone_brick_stairs",
               pilaster="minecraft:stripped_spruce_log[axis=y]", band="minecraft:white_terracotta", plate="minecraft:spruce_planks",
               top_plate="minecraft:spruce_planks", weights=[0.7, 0.2, 0.1], every=3, pil_every=6)
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:deepslate_tile_stairs", ridge="minecraft:deepslate_tile_slab[type=bottom]",
                 ridge_axis="x", gable_fill="minecraft:bricks", overhang=1)
    # rooms: ground floor = waiting room | ticket hall | luggage; upstairs = Kokoro's office | records | staff room
    for f, kinds in enumerate((["tavern", "office", "storeroom"], ["office", "library", "bedroom"])):
        fy = y + 1 + 6 * f
        xs = [x1 + 1, x1 + 17, x1 + 29, x2 - 1]
        for k in range(3):
            if k:
                bb.fill(xs[k] - 1, fy, z1 + 1, xs[k] - 1, fy + 4, z2 - 1, "minecraft:stripped_spruce_log[axis=y]")
                bb.fill(xs[k] - 1, fy, (z1 + z2) // 2, xs[k] - 1, fy + 1, (z1 + z2) // 2 + 1, AIR)
            furnish_kit(bb, (xs[k], z1 + 1, xs[k + 1] - (2 if k < 2 else 0), z2 - 1), fy, 5, kinds[k], wood="spruce", seed=7710 + f * 3 + k,
                        doors=[(xs[k], (z1 + z2) // 2), (xs[k + 1] - 1, (z1 + z2) // 2)], accent="green")
    # stair up in the north-west corner of the ticket hall
    P.stair_run(bb, x1 + 18, y + 1, z1 + 2, 6, 2, "east", "minecraft:spruce_stairs") if hasattr(P, "stair_run") else None
    bb.fill(x1 + 18, y + 6, z1 + 2, x1 + 24, y + 6, z1 + 3, AIR)
    # doors onto the platform side and the yard, a deep porch with a lamp over the platform door
    for dx in (8, 23, 36):
        bb.fill(x1 + dx, y + 1, z2, x1 + dx + 1, y + 3, z2, AIR)
        bb.set(x1 + dx, y + 4, z2 + 1, "minecraft:lantern[hanging=true]") if False else bb.set(x1 + dx, y + 4, z2 + 1, "minecraft:wall_torch[facing=south]")
    bb.fill(x1 + 22, y + 1, z1, x1 + 25, y + 4, z1, AIR)
    # ticket window from the platform side
    bb.fill(x1 + 20, y + 2, z2, x1 + 21, y + 2, z2, "minecraft:spruce_slab[type=top]")
    bb.fill(x1 + 20, y + 3, z2, x1 + 21, y + 3, z2, "minecraft:iron_bars")
    # the clock tower at the east end: brick shaft, white clock faces on four sides, copper-green spire
    tx1, tz1 = x2 - 8, z1 + 2
    tx2, tz2 = tx1 + 8, tz1 + 8
    bb.fill(tx1, top, tz1, tx2, top + 16, tz2, "minecraft:bricks")
    bb.fill(tx1 + 1, top, tz1 + 1, tx2 - 1, top + 16, tz2 - 1, AIR)
    for (a, b) in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
        bb.fill(a, top, b, a, top + 16, b, "minecraft:stone_bricks")
    cx, cz, cy = (tx1 + tx2) // 2, (tz1 + tz2) // 2, top + 11
    for (fx, fz, axis) in ((cx, tz1, "x"), (cx, tz2, "x"), (tx1, cz, "z"), (tx2, cz, "z")):
        for u in range(-3, 4):
            for v in range(-3, 4):
                if u * u + v * v <= 10:
                    px, pz = (fx + u, fz) if axis == "x" else (fx, fz + u)
                    bb.set(px, cy + v, pz, "minecraft:white_concrete" if u * u + v * v <= 5 else "minecraft:gold_block")
        px, pz = (fx, fz) if axis == "x" else (fx, fz)
        bb.set(px, cy, pz, "minecraft:black_concrete"); bb.set(px, cy + 1, pz, "minecraft:black_concrete")
        hx, hz = (fx + 1, fz) if axis == "x" else (fx, fz + 1)
        bb.set(hx, cy, hz, "minecraft:black_concrete")
    bb.fill(tx1 - 1, top + 17, tz1 - 1, tx2 + 1, top + 17, tz2 + 1, "minecraft:stone_brick_slab[type=bottom]")
    P.hip_roof(bb, tx1, tz1, tx2, tz2, top + 18, "minecraft:oxidized_cut_copper_stairs", ridge="minecraft:oxidized_cut_copper_slab[type=bottom]")
    bb.fill(cx, top + 22, cz, cx, top + 26, cz, "minecraft:iron_bars"); bb.set(cx, top + 27, cz, "minecraft:lightning_rod")
    bb.set(cx, top + 15, cz, "minecraft:bell[attachment=ceiling,facing=north]")
    bb.fill(cx, top - 5, tz1 + 1, cx, top + 14, tz1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(cx, top, tz1 + 1, cx, top, tz1 + 1, "minecraft:ladder[facing=south]")
    return top


def board(b):
    """The station name board over the platform (white letters on green), painted after to_canvas."""
    x0, y0, z = 22, 12, PZ1 - 1
    b.box(x0 - 1, y0 - 1, z, x0 + 55, y0 + 7, z, "minecraft:green_concrete")
    b.text(x0 + 1, y0 + 5, z, "SHIFT STATION", "minecraft:white_concrete", axis="x")
    for x in (x0 + 2, x0 + 52):
        b.column(x, z, 10, y0 - 2, "minecraft:dark_oak_fence")


# ------------------------------------------------------------------ Kokoro's house, shed, coal stage, cottages
def kokoro_house(bb):
    """Kokoro and Chimney's two-storey house-bar south of the tracks: a bar counter downstairs (Kokoro's gin),
    the kitchen behind, bedrooms upstairs, Gonbe's hutch and a washing line in the yard."""
    x1, z1, x2, z2 = 18, 74, 38, 88
    y = 1
    top = tier(bb, x1, z1, x2, z2, y, 2, 5, ["minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_concrete_powder"],
               "minecraft:glass_pane", "minecraft:spruce_stairs", pilaster="minecraft:stripped_spruce_log[axis=y]",
               band="minecraft:spruce_planks", plate="minecraft:spruce_planks", top_plate="minecraft:spruce_planks",
               weights=[0.6, 0.25, 0.15], every=3, pil_every=5)
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:red_nether_brick_stairs", ridge="minecraft:red_nether_brick_slab[type=bottom]",
                 ridge_axis="x", gable_fill="minecraft:white_terracotta", overhang=1)
    bar_counter(None, bb, x1 + 3, z1 + 6, y + 1, 9, "south", wood="spruce") if False else None
    furnish_kit(bb, (x1 + 1, z1 + 1, x1 + 12, z2 - 1), y + 1, 4, "tavern", wood="spruce", seed=7720, doors=[(x1 + 6, z1)], accent="red")
    furnish_kit(bb, (x1 + 14, z1 + 1, x2 - 1, z2 - 1), y + 1, 4, "kitchen", wood="spruce", seed=7721, doors=[(x1 + 13, z1 + 5)], accent="red")
    bb.fill(x1 + 13, y + 1, z1 + 1, x1 + 13, y + 4, z2 - 1, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(x1 + 13, y + 1, z1 + 5, x1 + 13, y + 2, z1 + 5, AIR)
    furnish_kit(bb, (x1 + 1, z1 + 1, x1 + 10, z2 - 1), y + 6, 4, "bedroom", wood="spruce", seed=7722, doors=[(x1 + 11, z1 + 4)], accent="pink")
    furnish_kit(bb, (x1 + 12, z1 + 1, x2 - 1, z2 - 1), y + 6, 4, "bedroom", wood="spruce", seed=7723, doors=[(x1 + 11, z1 + 4)], accent="blue")
    bb.fill(x1 + 11, y + 6, z1 + 1, x1 + 11, y + 9, z2 - 1, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(x1 + 11, y + 6, z1 + 4, x1 + 11, y + 7, z1 + 4, AIR)
    bb.fill(x2 - 1, y + 1, z2 - 1, x2 - 1, y + 6, z2 - 1, "minecraft:ladder[facing=north]")
    bb.fill(x1 + 6, y + 1, z1, x1 + 7, y + 3, z1, AIR)
    # porch facing the tracks with a bench and Kokoro's sign
    bb.fill(x1 + 3, y, z1 - 3, x1 + 10, y, z1 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 3, y + 4, z1 - 3, x1 + 10, y + 4, z1 - 1, "minecraft:spruce_slab[type=bottom]")
    for xx in (x1 + 3, x1 + 10):
        bb.fill(xx, y + 1, z1 - 3, xx, y + 3, z1 - 3, "minecraft:spruce_fence")
    bench(bb, x1 + 8, y + 1, z1 - 2, 2, "south", wood="spruce")
    bb.set(x1 + 4, y + 1, z1 - 2, "minecraft:barrel[facing=up]"); bb.set(x1 + 4, y + 2, z1 - 2, "minecraft:potted_poppy")
    # Gonbe's hutch and the washing line
    bb.fill(x2 + 3, y + 1, z1 + 2, x2 + 5, y + 2, z1 + 4, "minecraft:spruce_planks"); bb.set(x2 + 4, y + 1, z1 + 1, AIR)
    bb.fill(x2 + 3, y + 3, z1 + 2, x2 + 5, y + 3, z1 + 4, "minecraft:spruce_slab[type=bottom]")
    bb.set(x2 + 4, y + 1, z1 + 2, "minecraft:white_carpet") if False else bb.set(x2 + 4, y + 1, z1 + 3, "minecraft:hay_block")
    for xx in (x2 + 3, x2 + 12):
        bb.fill(xx, y + 1, z1 + 9, xx, y + 4, z1 + 9, "minecraft:spruce_fence")
    for xx in range(x2 + 4, x2 + 12):
        bb.set(xx, y + 4, z1 + 9, "minecraft:tripwire")
        if xx % 2:
            bb.set(xx, y + 3, z1 + 9, ["minecraft:white_banner", "minecraft:pink_banner", "minecraft:light_blue_banner"][xx % 3]) if False else None
    return top


def engine_shed(bb):
    """A long brick shed over the end of track T2 west of the platform... placed north-west on its own siding."""
    x1, z1, x2, z2 = 14, 18, 36, 30
    y = max(hy(x, z) for x in range(x1, x2 + 1) for z in range(z1, z2 + 1))
    bb.fill(x1, y - 3, z1, x2, y, z2, "minecraft:stone_bricks")
    bb.fill(x1, y + 1, z1, x2, y + 8, z2, "minecraft:bricks")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 8, z2 - 1, AIR)
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, "minecraft:spruce_planks")
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, y + 1, z1, x, y + 8, z1, "minecraft:stone_bricks"); bb.fill(x, y + 1, z2, x, y + 8, z2, "minecraft:stone_bricks")
        if x + 2 <= x2:
            bb.fill(x + 1, y + 4, z1, x + 2, y + 6, z1, "minecraft:glass_pane"); bb.fill(x + 1, y + 4, z2, x + 2, y + 6, z2, "minecraft:glass_pane")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y + 9, "minecraft:deepslate_tile_stairs", ridge="minecraft:deepslate_tile_slab[type=bottom]",
                 ridge_axis="x", gable_fill="minecraft:bricks", overhang=1)
    bb.fill(x2, y + 1, z1 + 4, x2, y + 7, z2 - 4, AIR)
    # work pit with rails over it, benches and tools
    bb.fill(x1 + 4, y - 2, (z1 + z2) // 2 - 1, x2 - 3, y, (z1 + z2) // 2 + 1, AIR)
    bb.fill(x1 + 4, y - 3, (z1 + z2) // 2 - 1, x2 - 3, y - 3, (z1 + z2) // 2 + 1, "minecraft:stone_bricks")
    for x in range(x1 + 2, x2):
        bb.set(x, y + 1, (z1 + z2) // 2 - 1, "minecraft:rail[shape=east_west]") if not (x1 + 4 <= x <= x2 - 3) else bb.set(x, y + 1, (z1 + z2) // 2 - 1, AIR)
    for x in range(x1 + 4, x2 - 2):
        bb.set(x, y, (z1 + z2) // 2 - 1, "minecraft:iron_bars"); bb.set(x, y + 1, (z1 + z2) // 2 - 1, "minecraft:rail[shape=east_west]")
    for x in range(x1 + 2, x2 - 1, 3):
        bb.set(x, y + 1, z1 + 1, ["minecraft:anvil[facing=east]", "minecraft:smithing_table", "minecraft:grindstone[face=floor,facing=east]",
                                  "minecraft:barrel[facing=up]", "minecraft:blast_furnace[facing=south]"][x % 5])
        bb.set(x, y + 1, z2 - 1, ["minecraft:chest[facing=north]", "minecraft:barrel[facing=up]", "minecraft:crafting_table"][x % 3])
    for x in range(x1 + 4, x2, 6):
        bb.set(x, y + 8, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
        bb.set(x, y + 4, z1 + 1, "minecraft:wall_torch[facing=south]"); bb.set(x, y + 4, z2 - 1, "minecraft:wall_torch[facing=north]")


def coal_and_water(bb):
    # water tower on the yard south-east of Kokoro's house
    wx, wz = 50, 80
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        bb.fill(wx + dx, 2, wz + dz, wx + dx, 12, wz + dz, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.cylinder(wx, 13, wz, 4, 13, "minecraft:spruce_planks")
    bb.cylinder(wx, 14, wz, 4, 19, "minecraft:spruce_planks", hollow=True)
    bb.cylinder(wx, 14, wz, 3, 18, "minecraft:water")
    for y in (15, 18):
        bb.ring(wx, y, wz, 3, 4, y, "minecraft:dark_oak_planks")
    P.cone_roof(bb, wx, 20, wz, 5, 4, "minecraft:dark_oak_planks")
    bb.fill(wx + 4, 13, wz, wx + 9, 13, wz, "minecraft:dark_oak_trapdoor[facing=east,half=top]") if False else bb.fill(wx + 5, 11, wz, wx + 8, 11, wz, "minecraft:dark_oak_fence")
    bb.fill(wx + 8, 4, wz, wx + 8, 10, wz, "minecraft:iron_chain[axis=y]")
    bb.fill(wx - 3, 2, wz + 4, wx - 3, 12, wz + 4, "minecraft:ladder[facing=south]")
    # coal stage: a raised timber staging with coal heaps and a chute, by track T2
    cx1, cz1, cx2, cz2 = 58, 70, 72, 78
    bb.fill(cx1, 1, cz1, cx2, 4, cz2, "minecraft:stone_bricks")
    bb.fill(cx1, 5, cz1, cx2, 5, cz2, "minecraft:spruce_planks")
    for x in range(cx1 + 1, cx2, 2):
        for z in range(cz1 + 1, cz2):
            h = 1 + int(2.2 * NT.noise(np.array(x), np.array(z), 7730, 3))
            bb.fill(x, 6, z, x, 5 + h, z, "minecraft:coal_block")
    for x in range(cx1, cx2 + 1, 3):
        bb.set(x, 6, cz1, "minecraft:spruce_fence")
    bb.fill(cx1 + 3, 5, cz1 - 1, cx1 + 3, 5, cz1 - 2, "minecraft:spruce_trapdoor[facing=north,half=top]")
    bb.set(cx1 + 1, 2, cz1 - 1, "minecraft:ladder[facing=north]") if False else None
    for y in range(2, 6):
        bb.set(cx2 + 1, y, cz2 - 1, "minecraft:ladder[facing=east]")
    for x in (cx1 + 2, cx1 + 7, cx1 + 12):
        bb.set(x, 2, cz1 - 1, "minecraft:barrel[facing=up]")
    bb.fill(cx1 + 5, 2, cz1 - 2, cx1 + 6, 2, cz1 - 2, "minecraft:minecart") if False else None


def cottages(bb, tracker):
    """Staff and fishermen's cottages packed on the hill lobes west of the yard, each furnished."""
    walls = [["minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_concrete_powder"],
             ["minecraft:yellow_terracotta", "minecraft:smooth_sandstone", "minecraft:sandstone"],
             ["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:calcite"]]
    pal = [dict(walls=w, frame="minecraft:stripped_spruce_log", base=["minecraft:cobblestone", "minecraft:stone_bricks",
           "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks") for w in walls]
    roofs = ["minecraft:red_nether_brick_stairs", "minecraft:dark_oak_stairs", "minecraft:deepslate_tile_stairs", "minecraft:spruce_stairs"]
    reserved = [(12, 26, 66, 54), (14, 17, 37, 31), (10, T1 - 3, SHORE + 2, T2 + 3), (16, 70, 46, 92), (44, 74, 56, 86),
                (56, 66, 76, 80), (20, 52, 30, 76)]
    ok = lambda x, z: bool(land(x, z)) and hy(x, z) >= 1 and _ISLE(np.array(float(x)), np.array(float(z))) > 5
    face = lambda cx, cz: 0 if cz < T1 else 2
    return pack_houses(bb, hy, ok, (6, 8, 86, 104), 16, 7740, tracker, pal, roofs, focus=(40, 60), reserved=reserved,
                       sizes=(7, 9), floors=(1, 2), gap=2, face=face, max_step=6)


def jetty(bb):
    """A plank jetty off the beach south of the tracks with two rowboats and a lamp at the end."""
    z = 84
    x0 = max(x for x in range(NX) if land(x, z) and hy(x, z) >= 1) - 2
    bb.fill(x0, 1, z - 1, x0 + 18, 1, z + 1, "minecraft:spruce_planks")
    for x in range(x0 + 2, x0 + 19, 4):
        bb.fill(x, -6, z - 2, x, 1, z - 2, "minecraft:stripped_spruce_log[axis=y]"); bb.fill(x, -6, z + 2, x, 1, z + 2, "minecraft:stripped_spruce_log[axis=y]")
        bb.set(x, 2, z - 2, "minecraft:spruce_fence"); bb.set(x, 2, z + 2, "minecraft:spruce_fence")
    lamp_post(bb, x0 + 18, 2, z + 1)
    for (bx, bz) in ((x0 + 6, z + 4), (x0 + 12, z - 6)):
        for dx in range(7):
            half = 1 if 1 <= dx <= 5 else 0
            for dz in range(-half, half + 1):
                bb.set(bx + dx, 0, bz + dz, "minecraft:spruce_planks")
            bb.set(bx + dx, 1, bz - half - 0, "minecraft:spruce_slab[type=bottom]") if half else None
            bb.set(bx + dx, 1, bz + half, "minecraft:spruce_slab[type=bottom]") if half else None
        bb.set(bx + 3, 1, bz, "minecraft:spruce_trapdoor[facing=north,half=bottom]")


def scenery(bb, rng):
    # a few palms and oaks on the hill, rocks on the shore, lamp posts along the yard paths
    for (x, z) in ((10, 26), (14, 98), (30, 100), (48, 22), (60, 18), (26, 16)):
        if land(x, z):
            P.tree(bb, x, hy(x, z) + 1, z, height=int(rng.integers(6, 9)), kind="oak", rng=rng)
    for (x, z) in ((70, 30), (66, 96), (74, 90), (12, 104)):
        if land(x, z) or hy(x, z) > -3:
            NT.boulder(bb, x, max(hy(x, z), -2), z, 2, rng)
    for x in range(16, 70, 10):
        lamp_post(bb, x, 2, T2 + 4)
        lamp_post(bb, x, 2, T1 - 3) if x > 64 else None
    # yard paths: station door -> Kokoro's porch, platform ramp -> shed
    for z in range(T2 + 2, 74):
        for x in (24, 25, 26):
            bb.set(x, 1, z, "minecraft:dirt_path")


def design():
    bb = BigBuild(seed=7700, y_min=-14, y_max=64)
    tracker = P.PropTracker(7700)
    rng = np.random.default_rng(7700)
    terrain(bb)
    line(bb)
    platform(bb)
    top = station_house(bb, tracker)
    kokoro_house(bb)
    engine_shed(bb)
    coal_and_water(bb)
    cottages(bb, tracker)
    jetty(bb)
    scenery(bb, rng)
    puffing_tom(bb, 76, T1)
    return bb, [], top


def build():
    bb, audit, top = design()
    b = to_canvas(bb)
    steady(b)
    board(b)
    b.chest(60, 2, 30, "easy", "south")
    b.chest(22, 8, 30, "galley", "south")
    b.chest(20, 2, 76, "easy", "east")
    return b, 0
