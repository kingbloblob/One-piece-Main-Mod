"""Den Den Mushi Relay Outpost v2, redesigned with the Minecraft Builder skill: a lonely Marine signal station on a
rocky headland that passes the Navy's calls across the sea (Den Den Mushi are snails; relay stations keep big ones
and whole pens of baby snails, and the Navy's "Black" and "White" Den Den Mushi tap and jam calls).

Silhouette first: a tall white stone signal tower with blue bands on the headland's crag, a glass lantern room on
top holding a GIANT Den Den Mushi (green snail body, striped shell with a dial, eye stalks, a receiver on its back),
next to a lattice antenna mast with crossbars; a Marine sloop at the jetty below.

Below the tower: the radio room (rows of snails on desks, receivers, maps), the operators' barracks and mess, the
officer's quarters, a supply shed, the snail nursery (glass pens with lettuce beds and baby snails), a vegetable
garden, a helipad-like flag square with the Marine flag, a jetty with the sloop. 128 x 104, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, tier, cornice, lamp_post, steady
from mcb.kit_interiors import furnish_kit, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship
from mcb.lotpack import pack_houses

SID = "den_den_outpost"
TITLE = "Den Den Mushi Relay Outpost"
CUTS = [3, 10, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 128, 104
TX, TZ = 46, 44                    # signal tower centre (on the crag)
_ISLE = NT.outline(50, 52, 42, 3301, wobble=0.1)
_CRAG = NT.outline(44, 42, 18, 3302, wobble=0.15)
MEADOW = NT.MEADOW
ROCK = [("minecraft:stone", 0.35), ("minecraft:andesite", 0.25), ("minecraft:diorite", 0.1), ("minecraft:cobblestone", 0.1),
        ("minecraft:grass_block", 0.2)]
WHITE = ["minecraft:white_concrete", "minecraft:smooth_quartz", "minecraft:calcite"]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    c = np.clip(_CRAG(X, Z) / 10.0, 0, 1)
    h = 3 + NT.fbm(X, Z, 3303, 18) * 3 + c ** 0.8 * 13
    h = np.where(d < 9, -5 + (h + 5) * np.clip(d / 9.0, 0, 1) ** 1.3, h)
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
    steep = lambda X, Z: (_CRAG(X, Z) > 0) & (height(X, Z) > 8)
    beach = lambda X, Z: land(X, Z) & (_ISLE(X, Z) < 11)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, MEADOW, 3304, mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ~beach(X, Z),
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, ROCK, 3305, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:sand", 0.6), ("minecraft:gravel", 0.0), ("minecraft:stone", 0.25),
                                                 ("minecraft:andesite", 0.15)], 3306, mask=beach, under="minecraft:sandstone",
             core="minecraft:stone", base=-6)
    wet = lambda X, Z: ~land(X, Z) & (_ISLE(X, Z) > -10)          # seabed only near the shore, never a square plate
    bed = lambda X, Z: np.minimum(height(X, Z), -1) - np.clip(-_ISLE(X, Z) / 5.0, 0, 6).astype(int)
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:gravel")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:stone")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 3307, density=0.2, kinds=["minecraft:short_grass", "minecraft:short_grass", "minecraft:fern"],
              flowers=["minecraft:cornflower", "minecraft:oxeye_daisy"], mask=lambda X, Z: land(X, Z) & ~steep(X, Z))


def snail(bb, x, y, z, s=1.0, axis="x"):
    """A Den Den Mushi facing +x (axis x) or +z: green body slab, a big round striped shell with a dial, two eye
    stalks with eyes, a receiver handset on the shell."""
    L = int(round(14 * s))
    for k in range(L):
        t = k / max(L - 1, 1)
        hw = max(1, int(round((2.4 - 0.9 * t) * s)))
        hh = max(1, int(round((2 + (1.5 if t > 0.75 else 0)) * s)))
        for dz in range(-hw, hw + 1):
            for dy in range(hh):
                px, pz = (x + k, z + dz) if axis == "x" else (x + dz, z + k)
                bb.set(px, y + dy, pz, "minecraft:lime_concrete" if dy else "minecraft:green_concrete")
    # head with eyes on stalks
    hx = L - 2
    for st_ in (-1, 1):
        for dy in range(int(4 * s)):
            px, pz = (x + hx, z + st_ * int(round(1.2 * s))) if axis == "x" else (x + st_ * int(round(1.2 * s)), z + hx)
            bb.set(px, y + int(3 * s) + dy, pz, "minecraft:lime_concrete")
        px, pz = (x + hx, z + st_ * int(round(1.2 * s))) if axis == "x" else (x + st_ * int(round(1.2 * s)), z + hx)
        bb.set(px, y + int(3 * s) + int(4 * s), pz, "minecraft:white_concrete")
        bb.set(px + (1 if axis == "x" else 0), y + int(3 * s) + int(4 * s), pz + (0 if axis == "x" else 1), "minecraft:black_concrete")
    # the shell: a disc standing on the back, rings of orange / white, the dial (a gold button) on the side
    cx = int(round(L * 0.38))
    r = 5.2 * s
    for u in range(-int(r) - 1, int(r) + 2):
        for v in range(0, int(2 * r) + 2):
            d = math.hypot(u, v - r)
            if d > r:
                continue
            for w in range(-int(2.4 * s), int(2.4 * s) + 1):
                if d ** 2 + (w * 1.7) ** 2 > r * r * 1.05:
                    continue
                ring = int(d / (1.3 * s)) % 2
                blk = "minecraft:orange_terracotta" if ring else "minecraft:white_terracotta"
                px, pz = (x + cx + u, z + w) if axis == "x" else (x + w, z + cx + u)
                bb.set(px, y + 1 + v, pz, blk)
    for side in (-1, 1):
        px, pz = (x + cx, z + side * int(2.6 * s)) if axis == "x" else (x + side * int(2.6 * s), z + cx)
        bb.set(px, y + 1 + int(r), pz, "minecraft:gold_block")
    # receiver on top
    px, pz = (x + cx, z) if axis == "x" else (x, z + cx)
    bb.fill(px - (2 if axis == "x" else 0), y + int(2 * r) + 2, pz - (0 if axis == "x" else 2),
            px + (2 if axis == "x" else 0), y + int(2 * r) + 2, pz + (0 if axis == "x" else 2), "minecraft:black_concrete")


def tower(bb):
    """The signal tower on the crag: white shaft with blue bands, stair core, radio room floors, the glass lantern
    room with the giant snail, a gallery and a beacon roof."""
    y0 = max(hy(TX + a, TZ + b) for a in range(-7, 8, 2) for b in range(-7, 8, 2))
    y0 = min(y0, 16)
    bb.cylinder(TX, y0 - 12, TZ, 8, y0, "minecraft:stone_bricks")
    bb.cylinder(TX, y0 + 1, TZ, 7, y0 + 30, "minecraft:white_concrete", hollow=True)
    for yy in range(y0 + 1, y0 + 31):
        if yy % 8 == 0:
            bb.ring(TX, yy, TZ, 6, 7, yy, "minecraft:blue_concrete")
    for f in range(4):
        fy = y0 + 1 + 7 * f
        bb.cylinder(TX, fy - 1, TZ, 6, fy - 1, "minecraft:spruce_planks")
        for a in range(0, 360, 45):
            t = math.radians(a + 22)
            bb.fill(TX + int(round(7 * math.cos(t))), fy + 2, TZ + int(round(7 * math.sin(t))),
                    TX + int(round(7 * math.cos(t))), fy + 3, TZ + int(round(7 * math.sin(t))), "minecraft:glass_pane")
        kind = ["radio", "radio", "office", "storeroom"][f]
        furnish_kit(bb, (TX - 3, TZ - 3, TX + 3, TZ + 3), fy, 5, kind, wood="spruce", seed=3310 + f, doors=[(TX - 4, TZ)], accent="blue")
        bb.fill(TX - 5, fy - 1, TZ - 1, TX - 4, fy - 1, TZ + 1, AIR)
        bb.fill(TX - 5, fy - 1, TZ, TX - 5, fy + 6, TZ, "minecraft:ladder[facing=east]")
    bb.fill(TX, y0 + 1, TZ + 7, TX, y0 + 3, TZ + 7, AIR)
    # gallery and lantern room
    top = y0 + 30
    bb.cylinder(TX, top, TZ, 10, top, "minecraft:smooth_stone")
    bb.ring(TX, top + 1, TZ, 9, 10, top + 1, "minecraft:white_concrete")
    for a in range(0, 360, 12):
        t = math.radians(a)
        bb.set(TX + int(round(10 * math.cos(t))), top + 2, TZ + int(round(10 * math.sin(t))), "minecraft:iron_bars")
    bb.ring(TX, top + 1, TZ, 6, 7, top + 12, "minecraft:light_blue_stained_glass")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.fill(TX + int(round(7 * math.cos(t))), top + 1, TZ + int(round(7 * math.sin(t))),
                TX + int(round(7 * math.cos(t))), top + 12, TZ + int(round(7 * math.sin(t))), "minecraft:blue_concrete")
    snail(bb, TX - 5, top + 1, TZ, s=0.75, axis="x")
    P.cone_roof(bb, TX, top + 13, TZ, 8, 6, "minecraft:blue_concrete")
    bb.fill(TX, top + 19, TZ, TX, top + 24, TZ, "minecraft:iron_bars")
    bb.set(TX, top + 25, TZ, "minecraft:lightning_rod")
    bb.fill(TX + 1, top + 21, TZ, TX + 6, top + 24, TZ, "minecraft:white_wool")
    bb.fill(TX + 3, top + 22, TZ, TX + 4, top + 23, TZ, "minecraft:blue_wool")
    bb.fill(TX - 5, top - 6, TZ, TX - 5, top, TZ, "minecraft:ladder[facing=east]")
    bb.fill(TX - 6, top, TZ, TX - 5, top, TZ, AIR)
    # the antenna mast beside it: lattice of iron bars with crossbars, cables to the tower
    ax, az = TX + 14, TZ - 6
    ay = hy(ax, az)
    for yy in range(ay + 1, ay + 46):
        w = max(0, 2 - (yy - ay) // 18)
        for (a, b) in ((ax - w, az - w), (ax + w, az - w), (ax - w, az + w), (ax + w, az + w)):
            bb.set(a, yy, b, "minecraft:iron_bars" if (yy - ay) % 6 else "minecraft:iron_block")
        if (yy - ay) % 9 == 0:
            bb.fill(ax - 5, yy, az, ax + 5, yy, az, "minecraft:iron_bars")
    bb.set(ax, ay + 46, az, "minecraft:redstone_lamp[lit=true]")
    bb.fill(ax - 2, ay, az - 2, ax + 2, ay, az + 2, "minecraft:stone_bricks")
    return y0, top


def compound(bb, tracker):
    """Barracks, mess, officer's house, supply shed, snail nursery, flag square, paths."""
    marine = [dict(walls=WHITE, frame="minecraft:stripped_birch_log", base=["minecraft:stone_bricks", "minecraft:andesite",
              "minecraft:polished_andesite"], floor="minecraft:birch_planks", wood="birch", chimney="minecraft:bricks")]
    roofs = ["minecraft:blue_terracotta" if False else "minecraft:deepslate_tile_stairs", "minecraft:dark_prismarine_stairs"]
    reserved = [(TX - 12, TZ - 12, TX + 20, TZ + 12), (60, 60, 82, 76), (70, 30, 90, 46)]
    ok = lambda x, z: bool(land(x, z)) and 1 <= hy(x, z) <= 10 and _ISLE(np.array(float(x)), np.array(float(z))) > 8
    pack_houses(bb, hy, ok, (14, 14, 96, 92), 9, 3320, tracker, marine, roofs, focus=(TX, TZ), reserved=reserved,
                sizes=(8, 11), floors=(1, 2), gap=2, max_step=4, kinds=("barracks", "mess", "office"))
    # snail nursery: a long glass greenhouse with lettuce beds (moss + leaves) and baby snails
    x1, z1, x2, z2 = 62, 62, 80, 74
    y = max(hy(x, z) for x in range(x1, x2 + 1, 3) for z in range(z1, z2 + 1, 3))
    bb.fill(x1, y - 3, z1, x2, y, z2, "minecraft:stone_bricks")
    bb.fill(x1, y + 1, z1, x2, y + 5, z2, "minecraft:glass")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 5, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 3):
        bb.fill(x, y + 1, z1, x, y + 5, z1, "minecraft:white_concrete"); bb.fill(x, y + 1, z2, x, y + 5, z2, "minecraft:white_concrete")
    P.gable_roof(bb, x1, z1, x2, z2, y + 6, "minecraft:glass_pane" if False else "minecraft:white_concrete_powder" if False else "minecraft:quartz_stairs",
                 ridge="minecraft:quartz_slab[type=bottom]", ridge_axis="x", overhang=0)
    for x in range(x1 + 2, x2 - 1, 4):
        bb.fill(x, y + 1, z1 + 2, x + 1, y + 1, z2 - 2, "minecraft:moss_block")
        for z in range(z1 + 2, z2 - 1, 2):
            bb.set(x, y + 2, z, "minecraft:azalea_leaves[persistent=true]" if (x + z) % 3 else "minecraft:moss_carpet")
        bb.set(x + 1, y + 2, z1 + 3, "minecraft:lime_carpet")
    bb.fill((x1 + x2) // 2, y + 1, z2, (x1 + x2) // 2, y + 2, z2, AIR)
    for x in range(x1 + 3, x2 - 2, 5):
        bb.set(x, y + 5, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    # flag square with the Marine flag
    fx, fz, fy = 80, 38, hy(80, 38)
    bb.fill(fx - 6, fy, fz - 6, fx + 6, fy, fz + 6, "minecraft:smooth_stone")
    bb.fill(fx - 6, fy + 1, fz - 6, fx + 6, fy + 8, fz + 6, AIR)
    bb.fill(fx - 6, fy, fz - 6, fx + 6, fy, fz - 6, "minecraft:blue_concrete")
    bb.fill(fx, fy + 1, fz, fx, fy + 16, fz, "minecraft:birch_fence")
    for u in range(8):
        for v in range(5):
            gull = (v == 2 and 2 <= u <= 5) or (v == 1 and u in (1, 6)) or (v == 3 and u in (3, 4))
            bb.set(fx + 1 + u, fy + 16 - v, fz, "minecraft:blue_wool" if gull else "minecraft:white_wool")
    for (a, b) in ((fx - 6, fz - 6), (fx + 6, fz - 6), (fx - 6, fz + 6), (fx + 6, fz + 6)):
        lamp_post(bb, a, fy + 1, b, post="minecraft:birch_fence")


def jetty(bb):
    """A jetty off the east shore with the Marine sloop tied up."""
    z = 58
    x0 = max(x for x in range(NX) if land(x, z)) - 3
    bb.fill(x0, 1, z - 2, x0 + 20, 1, z + 2, "minecraft:spruce_planks")
    for x in range(x0 + 2, x0 + 21, 4):
        for dz in (-3, 3):
            bb.fill(x, -8, z + dz, x, 1, z + dz, "minecraft:stripped_spruce_log[axis=y]")
            bb.set(x, 2, z + dz, "minecraft:spruce_fence")
    lamp_post(bb, x0 + 20, 2, z + 2, post="minecraft:birch_fence")
    stamp_ship(bb, "marine_warship", x0 + 26, z + 16, water_y=0, rot=0)


def design():
    bb = BigBuild(seed=3300, y_min=-14, y_max=100)
    tracker = P.PropTracker(3300)
    terrain(bb)
    y0, top = tower(bb)
    compound(bb, tracker)
    jetty(bb)
    # stairs/path from the compound up the crag to the tower door
    for k in range(18):
        x, z = TX, TZ + 8 + k
        y = hy(x, z)
        bb.fill(x - 1, y, z, x + 1, y, z, "minecraft:stone_bricks")
        bb.fill(x - 1, y + 1, z, x + 1, y + 3, z, AIR)
    return bb, [], y0, top


def build():
    bb, audit, y0, top = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(TX + 2, y0 + 1, TZ - 2, "easy", "west")
    b.chest(TX + 3, top + 1, TZ + 3, "marine", "west")
    for (x, z) in ((80, 34), (70, 50), (TX, TZ + 12)):
        b.guard(x, hy(x, z) + 1, z, "marine")
    b.guard(TX + 2, top + 1, TZ - 4, "marine_rifle")
    return b, 0
