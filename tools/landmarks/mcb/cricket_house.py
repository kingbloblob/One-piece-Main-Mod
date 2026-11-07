"""Montblanc Cricket's house on Jaya v2, redesigned with the Minecraft Builder skill.

The famous sight: a grand castle front on the beach, cream stone with blue roofs, a round tower on the west, the
gate keep with its stepped gable and rose window in the middle, more wall and a second tower to the east... and then
nothing: the castle stops in a ragged cut, because the other half of Noland's old house was blown into the sky with
Skypiea. From the side the front is only three blocks thick, propped up by timber braces, and the little wooden house
Cricket actually lives in hides behind it (kitchen with the feast table, his study of maps and Noland's log, a bedroom
and the diving workshop upstairs) with the cellar of Noland's gold underneath. South of the gate the beach and the
long pier with Cricket's diving winch, his boat and the Going Merry being refitted by the Saruyama Alliance; to the
east the Alliance camp (Masira and Shoujou's tents, monkey banners, the feast fire, salvage junk); north the South
Bird jungle of Jaya with giant trees and a South Bird nest. 160 x 160. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, glyph, table, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import shipstamp as SS

SID = "cricket_house"
TITLE = "Montblanc Cricket's House (Jaya)"
CUTS = [3, 9, -3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
TY = 2
FZ = 82                       # the castle front's south face
FX1, FX2 = 46, 104            # the front's full width before the cut
CUT = 98                      # roughly where the castle stops
GX = 74                       # gate centre
HOUSE = (64, 62, 16, 12)      # x0, z0, w, d of Cricket's real house
PX = 92                       # the pier's x
CAMP = (116, 98)
WALL = ["minecraft:smooth_sandstone", "minecraft:sandstone", "onepiece:alabasta_sandstone_bricks"]
TRIM = "minecraft:cut_sandstone"
ROOF = "minecraft:blue_terracotta"
ROOF_ST = "minecraft:deepslate_tile_stairs"
_ISLE = NT.outline(80, 74, 58, 7310, wobble=0.08)
_COVE = NT.outline(92, 152, 40, 7311, wobble=0.1)
GRASS = [("minecraft:grass_block", 0.6), ("minecraft:podzol", 0.14), ("minecraft:moss_block", 0.08), ("minecraft:coarse_dirt", 0.08),
         ("minecraft:rooted_dirt", 0.1)]
SAND = [("minecraft:sand", 0.8), ("minecraft:sandstone", 0.06), ("minecraft:gravel", 0.04), ("minecraft:clay", 0.1)]
YARD = [("minecraft:grass_block", 0.55), ("minecraft:coarse_dirt", 0.2), ("minecraft:dirt_path", 0.15), ("minecraft:sand", 0.1)]
STONE = ("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone")


def shore(X, Z):
    return np.minimum(_ISLE(X, Z), -_COVE(X, Z))


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    hill = 9 * np.clip((58 - Z) / 40.0, 0, 1) ** 1.3 * np.clip(d / 20.0, 0, 1)
    roll = TY + NT.fbm(X, Z, 7312, 22) * 3 - 0.8 + hill
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, roll)
    # the castle grounds, the house yard and the camp are level
    flat = np.zeros_like(X)
    for (x1, z1, x2, z2) in ((FX1 - 6, 52, FX2 + 2, FZ + 14), (CAMP[0] - 16, CAMP[1] - 16, CAMP[0] + 16, CAMP[1] + 16)):
        dx = np.maximum(np.maximum(x1 - X, X - x2), 0)
        dz = np.maximum(np.maximum(z1 - Z, Z - z2), 0)
        flat = np.maximum(flat, np.clip(1 - np.hypot(dx, dz) / 8.0, 0, 1))
    h = np.where(d >= 10, h * (1 - flat) + TY * flat, h)
    return np.where(d < 1.5, -1, np.round(h))


def build_maps():
    X = np.arange(N)[:, None].astype(float)
    Z = np.arange(N)[None, :].astype(float)
    return _height(X, Z).astype(int), shore(X, Z)


HMAP, SHORE = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def yard(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (X >= FX1 - 4) & (X <= FX2) & (Z >= 54) & (Z <= FZ + 10)
    m |= (np.abs(X - GX) <= 2) & (Z > FZ) & (Z < FZ + 40)
    m |= (np.hypot(X - CAMP[0], Z - CAMP[1]) < 15)
    m |= (np.abs(Z - (FZ + 6 + 2 * np.sin(X * 0.1))) <= 1.5) & (X > FX2) & (X < CAMP[0])
    return m


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 7320, mask=lambda X, Z: land(X, Z) & (sh(X, Z) < 9),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRASS, 7321, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 9) & ~yard(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, YARD, 7322, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 9) & yard(X, Z),
             core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the castle front
def cut_x(y):
    """The ragged line where the castle stops (x of the last block at height y)."""
    return int(CUT + 3 * math.sin(y * 0.7) + 2 * math.sin(y * 1.9 + 1) - (y - TY) * 0.12)


def front(bb):
    z0, z1 = FZ - 2, FZ
    top = TY + 20
    # plinth and wall body
    bb.fill(FX1, TY - 3, z0, FX2, TY + 1, z1 + 1, "minecraft:stone_bricks")
    bb.mix(FX1, TY + 2, z0, FX2, top, z1, WALL, [0.6, 0.25, 0.15])
    bb.fill(FX1, TY + 2, z1 + 1, FX2, TY + 2, z1 + 1, "minecraft:stone_brick_stairs[facing=south,half=bottom]")
    # string courses
    for y in (TY + 9, TY + 16):
        bb.fill(FX1, y, z1 + 1, FX2, y, z1 + 1, "minecraft:sandstone_stairs[facing=south,half=top]")
    # crenellated parapet
    bb.fill(FX1, top + 1, z1, FX2, top + 1, z1, TRIM)
    for x in range(FX1, FX2 + 1, 2):
        bb.set(x, top + 2, z1, TRIM)
    # pilasters every 6 blocks
    for x in range(FX1 + 2, FX2, 6):
        bb.fill(x, TY + 2, z1 + 1, x, top, z1 + 1, "minecraft:smooth_quartz")
    # windows: two rows of round-topped windows
    for x in list(range(FX1 + 5, GX - 6, 6)) + list(range(GX + 8, FX2, 6)):
        for y0 in (TY + 4, TY + 11):
            P.arched_opening(bb, "x", x, y0, z0, 3, 4, depth=3, fill="minecraft:light_blue_stained_glass_pane")
            bb.fill(x - 1, y0 - 1, z1 + 1, x + 1, y0 - 1, z1 + 1, "minecraft:smooth_sandstone_slab[type=top]")
    # the gate keep in the middle: taller, stepped gable, rose window
    kx1, kx2 = GX - 9, GX + 9
    bb.mix(kx1, top, z0, kx2, top + 8, z1, WALL, [0.6, 0.25, 0.15])
    for i in range(7):
        bb.fill(kx1 + i, top + 9 + i, z0, kx2 - i, top + 9 + i, z1, WALL[0])
        bb.set(kx1 + i, top + 10 + i, z1, TRIM)
        bb.set(kx2 - i, top + 10 + i, z1, TRIM)
    bb.fill(GX, top + 16, z1, GX, top + 19, z1, "minecraft:iron_bars")
    bb.set(GX, top + 20, z1, "minecraft:lightning_rod")
    bb.fill_where(GX - 4, top + 3, z1, GX + 4, top + 11, z1,
                  lambda X, Y, Z: np.hypot(X - GX, Y - (top + 7)) <= 3.6, "minecraft:blue_stained_glass")
    bb.fill_where(GX - 4, top + 3, z1, GX + 4, top + 11, z1,
                  lambda X, Y, Z: (np.abs(np.hypot(X - GX, Y - (top + 7)) - 3.9) < 0.6), TRIM)
    bb.fill_where(GX - 4, top + 3, z1, GX + 4, top + 11, z1,
                  lambda X, Y, Z: (np.hypot(X - GX, Y - (top + 7)) <= 3.6) & ((X == GX) | (Y == top + 7)), "minecraft:gold_block")
    # the gate: big arch with a raised portcullis and studded doors swung open
    P.arched_opening(bb, "x", GX, TY + 1, z0 - 1, 7, 10, depth=5, trim="minecraft:chiseled_sandstone")
    bb.fill(GX - 3, TY + 9, z0, GX + 3, TY + 10, z0, "minecraft:iron_bars")
    for sx in (-4, 4):
        bb.fill(GX + sx, TY + 1, z1 + 1, GX + sx, TY + 11, z1 + 2, "minecraft:smooth_quartz")
        bb.set(GX + sx, TY + 12, z1 + 2, "minecraft:lantern[hanging=false]")
    # west tower: a half-round tower (front half only, of course) with a blue cone roof
    tower(bb, FX1 + 4, 7, top + 10)
    # east tower, smaller, just before the cut
    tower(bb, CUT - 7, 5, top + 6)
    # banners hanging off the parapet
    for x in (GX - 14, GX - 7, GX + 7, GX + 14):
        bb.fill(x, top - 7, z1 + 1, x, top, z1 + 1, "minecraft:blue_wool")
        bb.set(x, top - 8, z1 + 1, "minecraft:white_wool")
        bb.fill(x, top - 4, z1 + 1, x, top - 3, z1 + 1, "minecraft:yellow_wool")
    # ---- the cut: everything east of the ragged line is gone; the cut face shows broken masonry
    for y in range(TY - 3, top + 30):
        cx = cut_x(y)
        bb.fill(cx + 1, y, z0 - 9, FX2 + 12, y, z1 + 3, AIR)
        for z in range(z0, z1 + 2):
            if (bb.get_region(cx, y, z, cx, y, z) > 1).any():
                bb.set(cx, y, z, ("minecraft:cracked_stone_bricks", "minecraft:cobblestone", "minecraft:mossy_cobblestone")[(y + z) % 3])
    # rubble at the foot of the cut
    rng = np.random.default_rng(7330)
    for _ in range(26):
        x = CUT + int(rng.integers(0, 9)); z = FZ - 4 + int(rng.integers(0, 10))
        set_if_air(bb, x, hy(x, z) + 1, z, ("minecraft:cobblestone", "minecraft:cracked_stone_bricks", "minecraft:smooth_sandstone_slab[type=bottom]")[int(rng.integers(0, 3))])
    # the back: plain, propped up by timber braces (it really is only a front)
    for x in range(FX1 + 3, CUT - 2, 7):
        for k in range(10):
            y = TY + 1 + k
            zz = z0 - 1 - (9 - k) // 2 - 1
            bb.set(x, y, zz, "minecraft:stripped_spruce_log[axis=y]")
        bb.fill(x, TY + 1, z0 - 7, x, TY + 1, z0 - 1, "minecraft:spruce_planks")
        bb.fill(x, TY + 11, z0 - 1, x, TY + 12, z0 - 1, "minecraft:spruce_planks")
    return top


def tower(bb, cx, r, roof_y):
    """Half-round tower against the front, flat back (z < FZ - 2 cut away)."""
    z0 = FZ - 2
    half = lambda X, Y, Z: Z >= z0
    bb.fill_where(cx - r, TY - 2, z0, cx + r, roof_y, z0 + r,
                  lambda X, Y, Z: half(X, Y, Z) & (np.hypot(X - cx, Z - z0) <= r + 0.4), WALL[0])
    bb.fill_where(cx - r, TY - 2, z0, cx + r, roof_y, z0 + r,
                  lambda X, Y, Z: half(X, Y, Z) & (np.hypot(X - cx, Z - z0) <= r + 0.4) & (NT.noise(X + Y, Z - Y, 7331, 3) < 0.3), WALL[1])
    # slit windows round the front
    for k, a in enumerate((-60, 0, 60)):
        x = cx + int(round((r) * math.sin(math.radians(a))))
        z = z0 + int(round((r) * math.cos(math.radians(a))))
        for y0 in range(TY + 5, roof_y - 3, 6):
            bb.fill(x, y0, z, x, y0 + 2, z, "minecraft:light_blue_stained_glass_pane")
    # machicolation ring and cone roof (front half)
    bb.fill_where(cx - r - 1, roof_y - 1, z0, cx + r + 1, roof_y, z0 + r + 1,
                  lambda X, Y, Z: (Z >= z0) & (np.abs(np.hypot(X - cx, Z - z0) - (r + 0.6)) < 0.8), TRIM)
    for i in range(r + 2):
        rr = r + 1 - i * (r + 1) / (r + 1.5)
        yy = roof_y + 1 + int(i * 1.6)
        bb.fill_where(cx - r - 1, yy, z0, cx + r + 1, yy + 1, z0 + r + 1,
                      lambda X, Y, Z, rr=rr: (Z >= z0) & (np.hypot(X - cx, Z - z0) <= rr + 0.3), ROOF)
    tip = roof_y + 2 + int((r + 2) * 1.6)
    bb.fill(cx, tip, z0, cx, tip + 4, z0, "minecraft:dark_oak_fence")
    bb.fill(cx + 1, tip + 2, z0, cx + 3, tip + 3, z0, "minecraft:blue_wool")


# ------------------------------------------------------------------ Cricket's real house behind it
def house(bb, tracker, audit):
    x0, z0, w, d = HOUSE
    pal = dict(walls=["minecraft:spruce_planks", "minecraft:stripped_spruce_wood", "minecraft:oak_planks"],
               frame="minecraft:stripped_dark_oak_log", base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone"],
               floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:cobblestone", parapet="minecraft:spruce_planks")
    m, top, au = house_module(seed_of("cricket"), w, d, 2, "minecraft:spruce_stairs", tracker, ["kitchen", "library", "bedroom", "workshop"],
                              pal=pal, fh=5, timber=True, jetty=False)
    audit += au
    place_house(bb, m, w, d, x0, TY, z0, 0)     # door south, out to the gate
    # the cellar: Noland's gold
    cx1, cz1, cx2, cz2 = x0 + 2, z0 + 2, x0 + w - 3, z0 + d - 3
    bb.fill(cx1 - 1, TY - 7, cz1 - 1, cx2 + 1, TY - 1, cz2 + 1, "minecraft:stone_bricks")
    bb.fill(cx1, TY - 6, cz1, cx2, TY - 2, cz2, AIR)
    bb.fill(cx1, TY - 7, cz1, cx2, TY - 7, cz2, "minecraft:cobblestone")
    bb.fill(cx1, TY - 1, cz1, cx1, TY - 1, cz1, AIR)
    bb.fill(cx1, TY - 6, cz1, cx1, TY, cz1, "minecraft:ladder[facing=south]")
    bb.set(cx1, TY + 1, cz1, AIR)
    bb.set(cx1, TY, cz1, "minecraft:spruce_trapdoor[facing=south,half=top,open=false]")
    gx, gz = cx2 - 2, cz2 - 1
    bb.fill_where(gx - 3, TY - 6, gz - 3, gx + 2, TY - 3, gz + 1,
                  lambda X, Y, Z: (X - gx) ** 2 + ((Y - (TY - 7)) * 1.6) ** 2 + (Z - gz) ** 2 <= 9, "minecraft:gold_block")
    bb.set(gx - 3, TY - 6, gz, "minecraft:raw_gold_block")
    for x in range(cx1 + 2, cx2 - 4, 3):
        bb.set(x, TY - 6, cz1, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, TY - 3, cz1 - 1, "minecraft:wall_torch[facing=south]") if False else None
    bb.set(cx1 + 3, TY - 3, cz2, "minecraft:lantern[hanging=true]") if False else None
    bb.set((cx1 + cx2) // 2, TY - 2, (cz1 + cz2) // 2, "minecraft:lantern[hanging=true]")
    bb.set(cx1 + 1, TY - 2, cz2 - 1, "minecraft:lantern[hanging=true]")
    # porch with Cricket's deck chair and the old log of Noland on a lectern
    px = x0 + w // 2
    bb.fill(px - 3, TY, z0 + d, px + 3, TY, z0 + d + 1, "minecraft:spruce_planks")
    for x in (px - 3, px + 3):
        bb.fill(x, TY + 1, z0 + d + 1, x, TY + 3, z0 + d + 1, "minecraft:spruce_fence")
        bb.set(x, TY + 4, z0 + d + 1, "minecraft:spruce_slab[type=bottom]")
    bb.fill(px - 3, TY + 4, z0 + d, px + 3, TY + 4, z0 + d + 1, "minecraft:spruce_slab[type=bottom]")
    bb.set(px - 2, TY + 1, z0 + d, "minecraft:spruce_stairs[facing=north,half=bottom]")
    bb.set(px + 2, TY + 1, z0 + d, "minecraft:lectern[facing=south]")
    return (x0 - 2, z0 - 2, x0 + w + 2, z0 + d + 2)


def garden(bb, rng):
    """Between house and the front: laundry line, a vegetable bed, the outdoor feast table."""
    x0, z0, w, d = HOUSE
    # feast table west of the house (the night the Straw Hats ate with Cricket and the monkeys)
    tx, tz = x0 - 12, z0 + 4
    bb.fill(tx, TY + 1, tz, tx + 2, TY + 1, tz + 9, "minecraft:spruce_slab[type=top]")
    for z in range(tz, tz + 10, 2):
        set_if_air(bb, tx - 1, TY + 1, z, "minecraft:spruce_stairs[facing=east,half=bottom]")
        set_if_air(bb, tx + 3, TY + 1, z, "minecraft:spruce_stairs[facing=west,half=bottom]")
    for z, s in ((tz + 1, "minecraft:decorated_pot"), (tz + 4, "minecraft:barrel[facing=up,open=false]"), (tz + 8, "minecraft:candle[candles=3,lit=true]")):
        bb.set(tx + 1, TY + 2, z, s)
    # cooking fire
    bb.set(tx + 6, TY + 1, tz + 4, "minecraft:campfire[lit=true]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        set_if_air(bb, tx + 6 + dx * 2, TY + 1, tz + 4 + dz * 2, "minecraft:stripped_oak_log[axis=x]" if dz == 0 else "minecraft:stripped_oak_log[axis=z]")
    # vegetable bed east of the house
    vx, vz = x0 + w + 3, z0 + 2
    bb.fill(vx - 1, TY, vz - 1, vx + 7, TY, vz + 6, "minecraft:spruce_planks")
    bb.fill(vx, TY, vz, vx + 6, TY, vz + 5, "minecraft:farmland[moisture=7]")
    bb.fill(vx + 3, TY, vz, vx + 3, TY, vz + 5, "minecraft:water")
    for x in range(vx, vx + 7):
        if x != vx + 3:
            bb.fill(x, TY + 1, vz, x, TY + 1, vz + 5, ("minecraft:carrots[age=7]", "minecraft:potatoes[age=7]", "minecraft:wheat[age=7]")[x % 3])
    # laundry line
    lx, lz = x0 + 2, z0 - 6
    for x in (lx, lx + 12):
        bb.fill(x, TY + 1, lz, x, TY + 4, lz, "minecraft:spruce_fence")
    bb.fill(lx + 1, TY + 4, lz, lx + 11, TY + 4, lz, "minecraft:tripwire[attached=true]")
    for x, c in ((lx + 3, "white"), (lx + 5, "light_blue"), (lx + 8, "orange")):
        bb.set(x, TY + 3, lz, f"minecraft:{c}_wool")
    return (x0 - 16, z0 - 8, x0 + w + 12, z0 + d + 2)


# ------------------------------------------------------------------ pier, diving gear, the Merry
def pier(bb, rng):
    z_sea = next(z for z in range(FZ + 2, N) if not land(np.array([PX]), np.array([z]))[0])
    z_end = min(N - 30, z_sea + 22)
    bb.fill(PX - 2, 0, FZ + 6, PX + 2, 0, z_end, "minecraft:spruce_planks")
    for z in range(FZ + 6, z_end + 1):
        y = max(1, hy(PX, z) + 1) if z < z_sea else 1
        bb.fill(PX - 2, 1, z, PX + 2, max(1, y - 1), z, AIR) if False else None
    for z in range(z_sea - 4, z_end + 1, 4):
        for x in (PX - 2, PX + 2):
            bb.fill(x, -8, z, x, -1, z, "minecraft:stripped_spruce_log[axis=y]")
            bb.fill(x, 1, z, x, 1, z, "minecraft:spruce_fence")
    # walkway on land from the gate down to the pier
    for z in range(FZ + 2, z_sea):
        y = hy(PX, z)
        for x in range(PX - 2, PX + 3):
            bb.set(x, y, z, "minecraft:spruce_planks")
            bb.fill(x, y + 1, z, x, y + 3, z, AIR)
    # the diving winch at the end: A-frame, chain, the round diving bell on a hook, the air pump
    ez = z_end - 2
    for x in (PX - 2, PX + 2):
        bb.fill(x, 1, ez, x, 7, ez, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(PX - 2, 8, ez, PX + 2, 8, ez, "minecraft:stripped_spruce_log[axis=x]")
    bb.fill(PX, 8, ez + 1, PX, 8, ez + 5, "minecraft:stripped_spruce_log[axis=z]")
    bb.fill(PX, 4, ez + 5, PX, 7, ez + 5, "minecraft:iron_chain[axis=y]")
    bb.fill_where(PX - 2, -1, ez + 3, PX + 2, 3, ez + 7, lambda X, Y, Z: (X - PX) ** 2 + (Y - 1) ** 2 + (Z - (ez + 5)) ** 2 <= 4.5,
                  "minecraft:waxed_copper_block")
    bb.set(PX, 1, ez + 7, "minecraft:glass")
    bb.set(PX - 1, 1, ez + 4, "minecraft:glass") if False else None
    bb.set(PX + 1, 1, ez - 1, "minecraft:grindstone[face=floor,facing=east]")
    bb.set(PX - 1, 1, ez - 1, "minecraft:barrel[facing=up,open=false]")
    bb.set(PX - 1, 1, ez - 3, "minecraft:lever[face=floor,facing=north,powered=false]")
    bb.set(PX + 1, 1, ez - 3, "minecraft:lantern[hanging=false]")
    # Cricket's boat, moored west of the pier
    bx, bz = PX - 7, z_sea + 6
    bb.fill_where(bx - 3, -1, bz - 6, bx + 3, 1, bz + 6,
                  lambda X, Y, Z: ((X - bx) / 2.6) ** 2 + ((Z - bz) / 6.2) ** 2 <= 1 - (Y < 0) * 0.35, "minecraft:spruce_planks")
    bb.fill_where(bx - 3, 1, bz - 6, bx + 3, 1, bz + 6,
                  lambda X, Y, Z: ((X - bx) / 1.7) ** 2 + ((Z - bz) / 5.2) ** 2 <= 1, AIR)
    bb.fill_where(bx - 3, 0, bz - 6, bx + 3, 0, bz + 6,
                  lambda X, Y, Z: ((X - bx) / 1.7) ** 2 + ((Z - bz) / 5.2) ** 2 <= 1, "minecraft:spruce_slab[type=top]")
    bb.fill(bx, 1, bz - 1, bx, 7, bz - 1, "minecraft:spruce_fence")
    bb.fill(bx, 4, bz, bx, 6, bz + 3, "minecraft:white_wool")
    bb.set(bx, 1, bz + 3, "minecraft:barrel[facing=up,open=false]")
    # the Going Merry, refitted here by the Saruyama Alliance (bow out to sea)
    fp = SS.stamp_ship(bb, "going_merry", PX + 14, z_sea + 14, 0, 1)
    return (PX - 12, FZ + 4, fp[2] + 2, N), z_end


# ------------------------------------------------------------------ the Saruyama Alliance camp
MONKEY = ["..####..",
          ".#....#.",
          "#.#..#.#",
          "#......#",
          ".#.##.#.",
          "..####.."]


def camp(bb, rng):
    cx, cz = CAMP
    # big fire with log seats
    bb.set(cx, TY + 1, cz, "minecraft:campfire[lit=true]")
    bb.fill_where(cx - 2, TY, cz - 2, cx + 2, TY, cz + 2, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 2.3, "minecraft:cobblestone")
    bb.set(cx, TY, cz, "minecraft:cobblestone")
    for a in range(0, 360, 60):
        x = cx + int(round(5 * math.cos(math.radians(a)))); z = cz + int(round(5 * math.sin(math.radians(a))))
        bb.set(x, TY + 1, z, "minecraft:stripped_oak_log[axis=x]" if abs(math.cos(math.radians(a))) < 0.5 else "minecraft:stripped_oak_log[axis=z]")
    # three tents (Masira's, Shoujou's, the crew's)
    for i, (tx, tz, col) in enumerate(((cx - 11, cz - 6, "brown"), (cx + 7, cz - 9, "orange"), (cx - 2, cz + 8, "green"))):
        for k in range(4):
            bb.fill(tx - 3 + k, TY + 1 + k, tz, tx - 3 + k, TY + 1 + k, tz + 6, f"minecraft:{col}_wool")
            bb.fill(tx + 3 - k, TY + 1 + k, tz, tx + 3 - k, TY + 1 + k, tz + 6, f"minecraft:{col}_wool")
        bb.fill(tx - 2, TY + 1, tz + 6, tx + 2, TY + 3, tz + 6, "minecraft:spruce_planks")
        bb.fill(tx, TY + 1, tz + 6, tx, TY + 2, tz + 6, AIR)
        bb.set(tx - 1, TY + 1, tz + 2, "minecraft:white_bed[facing=north,part=foot]")
        bb.set(tx - 1, TY + 1, tz + 1, "minecraft:white_bed[facing=north,part=head]")
        bb.set(tx + 1, TY + 1, tz + 1, "minecraft:barrel[facing=up,open=false]")
        bb.set(tx + 1, TY + 1, tz + 4, "minecraft:lantern[hanging=false]")
    # monkey banners on tall poles
    for (fx, fz) in ((cx - 14, cz + 4), (cx + 12, cz + 3)):
        bb.fill(fx, TY + 1, fz, fx, TY + 14, fz, "minecraft:spruce_fence")
        bb.fill(fx + 1, TY + 8, fz, fx + 9, TY + 14, fz, "minecraft:yellow_wool")
        glyph(bb, MONKEY, fx + 1, TY + 14, fz, "minecraft:brown_wool")
    # salvage heap: anchors, chains, an old cannon, broken planks, a treasure-hunter's sieve
    sx, sz = cx + 4, cz - 1
    bb.fill_where(sx + 6, TY + 1, sz - 4, sx + 12, TY + 3, sz + 4,
                  lambda X, Y, Z: (X - (sx + 9)) ** 2 + ((Y - TY) * 2) ** 2 + (Z - sz) ** 2 <= 14, "minecraft:coarse_dirt")
    for (x, y, z, s) in ((sx + 8, TY + 3, sz, "minecraft:anvil[facing=north]"), (sx + 10, TY + 3, sz - 1, "minecraft:iron_chain[axis=x]"),
                         (sx + 9, TY + 4, sz + 1, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]"),
                         (sx + 7, TY + 2, sz + 3, "minecraft:cauldron"), (sx + 11, TY + 2, sz - 3, "minecraft:dark_oak_fence")):
        set_if_air(bb, x, y, z, s)
    for x in range(cx - 6, cx - 1):
        set_if_air(bb, x, TY + 1, cz - 12, "minecraft:barrel[facing=up,open=false]")
    return (cx - 18, cz - 18, cx + 18, cz + 18)


# ------------------------------------------------------------------ the South Bird jungle
def jungle(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 12 or z > FZ - 8:
            continue
        if any(t[0] - 4 <= x <= t[2] + 4 and t[1] - 4 <= z <= t[3] + 4 for t in taken):
            continue
        h = int(rng.integers(22, 36))
        NT.giant_tree(bb, x, hy(x, z) + 1, z, h, rng, kind="jungle" if k % 3 else "dark_oak")
        taken.append((x - 7, z - 7, x + 7, z + 7))
        k += 1
        if k == 3:
            # a South Bird nest in this one
            ny = hy(x, z) + h - 6
            bb.fill_where(x - 4, ny, z - 4, x + 4, ny + 2, z + 4,
                          lambda X_, Y, Z_: (np.hypot(X_ - x, Z_ - z) <= 3.8) & ((Y == ny) | (np.hypot(X_ - x, Z_ - z) >= 2.8)), "minecraft:hay_block")
            bb.fill(x - 3, ny + 3, z - 3, x + 3, ny + 3, z + 3, AIR) if False else None
            bb.set(x, ny + 1, z, "minecraft:turtle_egg[eggs=3,hatch=0]")
        if k >= 16:
            break
    # small jungle trees and bushes in between
    for _ in range(140):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 10 or yard(X, Z)[0]:
            continue
        if any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
            continue
        y = hy(x, z) + 1
        if rng.random() < 0.6:
            P.tree(bb, x, y, z, height=int(rng.integers(6, 11)), kind=("jungle", "oak", "jungle")[int(rng.integers(0, 3))], rng=rng)
        else:
            bb.fill_where(x - 2, y, z - 2, x + 2, y + 2, z + 2, lambda X_, Y, Z_: (X_ - x) ** 2 + ((Y - y) * 1.5) ** 2 + (Z_ - z) ** 2 <= 5,
                          "minecraft:jungle_leaves[persistent=true]", only_empty=True)
    print("giant trees:", k)


def rocks(bb, rng):
    for _ in range(14):
        a = rng.uniform(0, 2 * math.pi)
        x, z = int(80 + 56 * math.cos(a)), int(74 + 56 * math.sin(a))
        X, Z = np.array([x]), np.array([z])
        if 0 < sh(X, Z)[0] < 8 and z < FZ + 4:
            NT.boulder(bb, x, hy(x, z), z, float(rng.uniform(1.6, 3.2)), rng, blocks=STONE)


def design():
    bb = BigBuild(seed=7310, y_min=-14, y_max=80)
    tracker = P.PropTracker(7310)
    audit = []
    rng = np.random.default_rng(7310)
    terrain(bb)
    front(bb)
    taken = [(FX1 - 4, FZ - 12, CUT + 10, FZ + 4)]
    taken.append(house(bb, tracker, audit))
    taken.append(garden(bb, rng))
    fp, z_end = pier(bb, rng)
    taken.append(fp)
    taken.append(camp(bb, rng))
    rocks(bb, rng)
    jungle(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 7390, density=0.34,
              kinds=["minecraft:fern", "minecraft:large_fern", "minecraft:short_grass", "minecraft:tall_grass"], flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 9) & ~yard(X, Z))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates."""
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
    x0, z0, w, d = HOUSE
    b.chest(x0 + 6, TY - 6, z0 + 3, "treasure", "south")
    b.chest(x0 + w + 2, TY + 1, z0 + d - 1, "medium", "west")
    b.chest(CAMP[0] - 9, TY + 1, CAMP[1] - 4, "easy", "east")
    return b, 0
