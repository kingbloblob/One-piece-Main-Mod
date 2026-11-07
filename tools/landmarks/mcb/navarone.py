"""Navarone v2, redesigned with the Minecraft Builder skill: G-8, the Marines' "impregnable fortress".

A ring of sheer grey cliffs rising 30 blocks out of the sea, grass and scrub on the rim. Hidden inside the ring is the
inner harbour, reached only through a rock tunnel on the south side that is shut by a huge two-leaf sea gate. Round
the harbour runs the stone quay with cranes, bollards and lamps; the Going Merry lies in the repair dock with
scaffolding along her side and a Marine warship is moored on the east quay. Two white stair towers climb the inner
cliff from the quay to the rim.

On the north rim stands the fortress: a white, blue-trimmed headquarters of three storeys (Jessica's kitchen and the
long mess hall, barracks, infirmary, armory, stores), a two-storey officers' tier on top (radio room, records,
officers' rooms) and Commodore Jonathan's office tower with its windows over the harbour, a radar dome and the flag.
A barracks block on the east rim, the supply depot on the west rim, four searchlight towers and gun batteries all
round the outer cliffs. 176 x 176, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, tier, cornice, lamp_post, stair_core, steady, furnish
from mcb.kit_interiors import furnish_kit, table_group, bar_counter, chair, bench, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "navarone"
TITLE = "Navarone (G-8 Fortress)"
CUTS = [2, 12, 31, 40]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
C = 88
RIM = 30                              # rim plateau height
HX, HZ, HRX, HRZ = 88, 104, 38, 27    # inner harbour ellipse
CH = 9                                # half width of the channel
TUN = (134, 152)                      # z range where the rock roofs the channel (the tunnel)
GATE_Z = 150                          # the sea gate
QY = 2                                # quay top
_ISLE = NT.outline(C, C, 74, 6910, wobble=0.05)
WHITE = ["minecraft:white_concrete", "minecraft:calcite", "minecraft:smooth_quartz"]
BLUE = "minecraft:light_blue_concrete"
DBLUE = "minecraft:blue_concrete"
ROCK = [("minecraft:stone", 0.42), ("minecraft:andesite", 0.22), ("minecraft:tuff", 0.12), ("minecraft:cobblestone", 0.08),
        ("minecraft:diorite", 0.06), ("minecraft:mossy_cobblestone", 0.04), ("minecraft:gravel", 0.0), ("minecraft:deepslate", 0.06)]
TOP = [("minecraft:grass_block", 0.62), ("minecraft:coarse_dirt", 0.1), ("minecraft:moss_block", 0.08), ("minecraft:podzol", 0.06),
       ("minecraft:rooted_dirt", 0.06), ("minecraft:stone", 0.08)]
PAVE = [("minecraft:stone_bricks", 0.4), ("minecraft:polished_andesite", 0.25), ("minecraft:cracked_stone_bricks", 0.1),
        ("minecraft:andesite", 0.15), ("minecraft:smooth_stone", 0.1)]

HQ = (54, 29, 122, 59)                # main headquarters block (3 storeys)
HQ2 = (66, 34, 110, 54)               # officers' tier (2 storeys)
OFF = (80, 36, 96, 52)                # Jonathan's office tower
STRATA = ["minecraft:stone", "minecraft:andesite", "minecraft:stone", "minecraft:tuff", "minecraft:stone", "minecraft:cobbled_deepslate",
          "minecraft:andesite", "minecraft:stone", "minecraft:diorite", "minecraft:stone"]
FH = 6


def harbour_e(X, Z):
    """Ellipse distance: < 1 inside the harbour."""
    return np.hypot((np.asarray(X, float) - HX) / HRX, (np.asarray(Z, float) - HZ) / HRZ)


def channel(X, Z):
    return (np.abs(np.asarray(X, float) - HX) <= CH) & (np.asarray(Z, float) > HZ)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    rim = RIM + (NT.fbm(X, Z, 6911, 22) - 0.5) * 6
    out = np.clip((d - 3) / 6.0, 0, 1) ** 0.4           # outer cliff: beach then a steep wall
    h = 1 + (rim - 1) * out
    e = harbour_e(X, Z)
    en = e * (1 + (NT.fbm(X, Z, 6916, 9) - 0.5) * 0.10)    # wobbly cliff foot, not a perfect ellipse
    ledge = (NT.fbm(X * 1.3, Z * 1.3, 6917, 7) - 0.5) * 6   # ledges and bulges on the face
    inner = np.clip((en - 1.04) * 5.0, 0, 1) ** 0.45        # inner cliff above the quay
    q = np.where(e < 1.0, -8, QY + np.clip((rim - QY) * inner + ledge * (inner > 0.15) * (inner < 0.9), 0, rim))
    h = np.minimum(h, np.where(e < 1.16, q, h))
    ch = channel(X, Z)
    sides = np.clip((np.abs(X - HX) - CH) / 4.0, 0, 1) ** 0.5
    h = np.where(ch, -8, np.where((np.abs(X - HX) < CH + 4) & (Z > HZ), np.minimum(h, QY + (h - QY) * sides), h))
    # the tunnel keeps the rock over the channel: handled in terrain() as a roof, the heightmap says "water"
    h = np.where(d < 1.5, -6 - np.clip(-d, 0, 8), h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)
SHORE = _ISLE(X_, Z_)
E = harbour_e(X_, Z_)
G = np.zeros_like(HMAP)
for _a, _b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))), ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
    _d = np.abs(HMAP[_a] - HMAP[_b]); G[_a] = np.maximum(G[_a], _d); G[_b] = np.maximum(G[_b], _d)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def steep(X, Z):
    return G[_ix(X, Z)] >= 3


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


# ------------------------------------------------------------------ terrain
def terrain(bb):
    top_ok = lambda X, Z: land(X, Z) & ~steep(X, Z) & (height(X, Z) > 4)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, TOP, 6912, mask=top_ok, under="minecraft:dirt", core="minecraft:stone", base=-10)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 6913, mask=lambda X, Z: land(X, Z) & ~top_ok(X, Z), under="minecraft:stone",
             core="minecraft:stone", base=-10)
    # rock strata on the cliff faces: wavy horizontal bands under the top layers
    off = lambda X, Z: (NT.fbm(X, Z, 6915, 18) * 7).astype(int)
    for i, blk in enumerate(STRATA):
        if blk == "minecraft:stone":
            continue
        # each band is broken up by smooth noise so it reads as rock layers, not painted stripes
        bb.fill_where(0, -10, 0, N - 1, RIM + 6, N - 1,
                      lambda X, y, Z, i=i: land(X, Z) & (y <= height(X, Z) - 1) & (((y + off(X, Z)) // 3) % len(STRATA) == i)
                      & (NT.noise(X + y * 7, Z - y * 5, 6918 + i, 4) > 0.3), blk)
    # sea and harbour water, sea bed
    bed = lambda X, Z: np.minimum(height(X, Z), -2)
    wet = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:gravel")
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:stone")
    # the quay round the harbour: a 3-wide stone brick edge at QY on the dry side of the ellipse
    qmask = lambda X, Z: (harbour_e(X, Z) >= 1.0) & (harbour_e(X, Z) < 1.1) & ~channel(X, Z)
    bb.fill_where(0, -6, 0, N - 1, QY, N - 1, lambda X, y, Z: qmask(X, Z) & (y < QY), "minecraft:stone_bricks")
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.full(np.broadcast(X, Z).shape, QY), PAVE, 6914, mask=qmask,
             under="minecraft:stone_bricks", core="minecraft:stone_bricks", depth=1, base=QY)
    bb.fill_where(0, QY + 1, 0, N - 1, QY + 30, N - 1, lambda X, y, Z: qmask(X, Z), AIR)
    # quay edge kerb: polished andesite slabs along the water
    kerb = lambda X, Z: (harbour_e(X, Z) >= 1.0) & (harbour_e(X, Z) < 1.03) & ~channel(X, Z)
    bb.fill_where(0, QY, 0, N - 1, QY, N - 1, lambda X, y, Z: kerb(X, Z), "minecraft:polished_andesite")
    # channel walls: dressed stone where the channel cuts the rock
    for z in range(HZ + HRZ - 4, N):
        for x in (HX - CH - 1, HX + CH + 1):
            top = hy(x, z)
            if top > 1:
                bb.fill(x, -8, z, x, min(top, 4), z, "minecraft:stone_bricks")
    # channel towpaths from the quay to the tunnel mouth
    for x in (HX - CH - 3, HX - CH - 2, HX + CH + 2, HX + CH + 3):
        for z in range(HZ + HRZ - 2, TUN[0]):
            if hy(x, z) <= QY + 1:
                bb.fill(x, -4, z, x, QY, z, "minecraft:stone_bricks")
                bb.fill(x, QY + 1, z, x, QY + 12, z, AIR)


def tunnel(bb):
    """Rock roof over the channel (the tunnel) with a dressed stone arch at each end and the great sea gate."""
    z1, z2 = TUN
    w = CH + 4
    for z in range(z1, z2 + 1):
        for x in range(HX - w, HX + w + 1):
            dx = abs(x - HX)
            arch = 9 + int(round(math.sqrt(max(0.0, w * w - dx * dx)) * 0.55))       # round vault, crown ~y 16
            top = int(round(RIM - 3 + (NT.fbm(np.array([[float(x)]]), np.array([[float(z)]]), 6911, 22)[0, 0] - 0.5) * 6))
            if top > arch:
                bb.mix(x, arch, z, x, top, z, [r for r, _ in ROCK[:4]], [0.5, 0.25, 0.15, 0.1])
                if dx > CH:
                    bb.fill(x, QY + 1, z, x, arch - 1, z, AIR) if dx <= CH + 3 else None
    # towpaths through the tunnel
    for x in (HX - CH - 3, HX - CH - 2, HX + CH + 2, HX + CH + 3):
        bb.fill(x, -4, z1, x, QY, z2, "minecraft:stone_bricks")
        bb.fill(x, QY + 1, z1, x, QY + 6, z2, AIR)
    for z in range(z1 + 3, z2, 6):
        for x in (HX - CH - 4, HX + CH + 4):
            bb.set(x, QY + 4, z, "minecraft:lantern[hanging=false]") if False else None
            bb.set(x, QY + 5, z, "minecraft:sea_lantern")
    # arches of dressed stone at both ends
    for z in (z1, z2):
        for x in range(HX - w, HX + w + 1):
            dx = abs(x - HX)
            arch = 9 + int(round(math.sqrt(max(0.0, w * w - dx * dx)) * 0.55))
            bb.fill(x, arch, z, x, arch + 2, z, "minecraft:stone_bricks" if dx % 3 else "minecraft:chiseled_stone_bricks")
    # the sea gate: two huge leaves, the west one shut, the east one swung half open
    gz = GATE_Z
    for x in range(HX - CH, HX + 1):
        dx = abs(x - HX)
        arch = 9 + int(round(math.sqrt(max(0.0, w * w - dx * dx)) * 0.55))
        bb.fill(x, -7, gz, x, arch - 1, gz, "minecraft:iron_block" if (x + 1) % 4 else "minecraft:polished_deepslate")
        bb.fill(x, 4, gz, x, 4, gz, DBLUE)
        bb.fill(x, 10, gz, x, 10, gz, DBLUE)
    for i in range(CH):
        x, z = HX + 1 + i // 2, gz - 1 - i
        dx = abs(x - HX)
        bb.fill(x, -7, z, x, 13, z, "minecraft:iron_block" if i % 4 else "minecraft:polished_deepslate")
        bb.set(x, 4, z, DBLUE); bb.set(x, 10, z, DBLUE)
    # the big gull mark painted over the gate
    for x in range(HX - 7, HX + 8):
        for y in range(19, 24):
            u, v = (x - HX) / 7.0, (y - 21.5) / 2.5
            if abs(v + 0.7 * abs(u) - 0.3) < 0.4 and abs(u) < 0.95:
                if bb.get_region(x, y, z2, x, y, z2)[0, 0, 0] > 1:
                    bb.set(x, y, z2 + 1, DBLUE)


# ------------------------------------------------------------------ the headquarters
def hq(bb, audit, tracker):
    x1, z1, x2, z2 = HQ
    y0 = hy(88, 36)
    y0 = max(y0, RIM - 1)
    # level the plateau under the fortress and a parade ground in front (harbour side)
    # a masonry terrace only where the rock is lower than the parade ground (a retaining wall, not a plain slab)
    bb.fill_where(x1 - 6, y0 - 14, z1 - 6, x2 + 6, y0, z2 + 8, lambda X, y, Z: y > height(X, Z) - 1, "minecraft:stone_bricks")
    bb.fill_where(x1 - 6, y0 - 14, z1 - 6, x2 + 6, y0, z2 + 8, lambda X, y, Z: (y > height(X, Z) - 1) & ((y + X + Z) % 7 == 0), "minecraft:cracked_stone_bricks")
    bb.fill(x1 - 6, y0 + 1, z1 - 6, x2 + 6, y0 + 40, z2 + 8, AIR)
    for (a, b, c, d) in ((x1 - 6, z1 - 6, x2 + 6, z1 - 6), (x1 - 6, z2 + 8, x2 + 6, z2 + 8), (x1 - 6, z1 - 6, x1 - 6, z2 + 8), (x2 + 6, z1 - 6, x2 + 6, z2 + 8)):
        bb.fill(a, y0 + 1, b, c, y0 + 1, d, "minecraft:stone_brick_wall")
    mx, mz = (x1 + x2) // 2, (z1 + z2) // 2
    for (a, b, c, d) in ((mx - 3, z2 + 8, mx + 3, z2 + 8), (x1 - 6, mz - 2, x1 - 6, mz + 2), (x2 + 6, mz - 2, x2 + 6, mz + 2),
                         (x1 + 4, z2 + 8, x1 + 7, z2 + 8), (x2 - 7, z2 + 8, x2 - 4, z2 + 8)):
        bb.fill(a, y0 + 1, b, c, y0 + 1, d, AIR)
    NT.cover(bb, x1 - 6, z1 - 6, x2 + 6, z2 + 8, lambda X, Z: np.full(np.broadcast(X, Z).shape, y0), PAVE, 6920,
             under="minecraft:stone", core="minecraft:stone", depth=1, base=y0)
    top = tier(bb, x1, z1, x2, z2, y0, 3, FH, WHITE, "minecraft:light_blue_stained_glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band=BLUE, plate="minecraft:smooth_stone", top_plate="minecraft:smooth_quartz",
               weights=[0.6, 0.25, 0.15], every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:light_blue_concrete")
    # ground floor: Jessica's kitchen + the long mess hall (west), the entrance hall (middle), offices/stores (east)
    fy = y0 + 1
    h = FH - 1
    mid = (x1 + x2) // 2
    bb.fill(mid - 6, fy, z1 + 1, mid - 6, fy + h - 1, z2 - 1, "minecraft:calcite")
    bb.fill(mid + 6, fy, z1 + 1, mid + 6, fy + h - 1, z2 - 1, "minecraft:calcite")
    for zz in (z2 - 4, z1 + 6):
        bb.fill(mid - 6, fy, zz, mid - 6, fy + 1, zz, AIR)
        bb.fill(mid + 6, fy, zz, mid + 6, fy + 1, zz, AIR)
    # kitchen strip along the north wall of the west half, a serving counter, then the mess hall tables
    kx1, kx2 = x1 + 1, mid - 7
    bb.fill(kx1, fy, z1 + 8, kx2, fy + h - 1, z1 + 8, "minecraft:calcite")
    for xx in range(kx1 + 3, kx2 - 2, 7):
        bb.fill(xx, fy, z1 + 8, xx + 1, fy + 1, z1 + 8, AIR)
    furnish_kit(bb, (kx1, z1 + 1, kx2, z1 + 7), fy, h, "kitchen", wood="birch", seed=691, doors=[(xx, z1 + 8) for xx in range(kx1 + 3, kx2 - 2, 7)])
    furnish_kit(bb, (kx1, z1 + 9, kx2, z2 - 1), fy, h, "mess", wood="birch", seed=692,
                doors=[(xx, z1 + 8) for xx in range(kx1 + 3, kx2 - 2, 7)] + [(mid - 6, z2 - 4), (mid - 6, z1 + 6)])
    # entrance hall: open, with a grand stair up to the 2nd floor, notice boards and benches
    bb.fill(mid - 1, fy, z2, mid + 1, fy + 3, z2, AIR)
    for i in range(FH):
        bb.fill(mid - 2, fy + i, z1 + 3 + i, mid + 2, fy + i, z1 + 3 + i, st("minecraft:quartz_stairs", "south"))
        bb.fill(mid - 2, fy, z1 + 3 + i, mid + 2, fy + i - 1, z1 + 3 + i, "minecraft:calcite") if i else None
    bb.fill(mid - 2, fy + FH - 1, z1 + 3, mid + 2, fy + FH - 1, z1 + 3 + FH - 1, AIR)
    bb.fill(mid - 2, fy + FH - 1, z1 + 3, mid + 2, fy + FH - 1, z1 + 3 + FH - 1, AIR)
    for i in range(FH):
        bb.set(mid - 2, fy + FH - 1, z1 + 3 + i, AIR)
    bb.fill(mid - 2, y0 + FH, z1 + 3, mid + 2, y0 + FH, z1 + 3 + FH - 1, AIR)
    bench(bb, mid - 4, fy, z2 - 6, 1, "west", "birch", axis="z")
    bench(bb, mid + 4, fy, z2 - 6, 1, "east", "birch", axis="z")
    bb.fill(mid - 1, fy - 1, z1 + 10, mid + 1, fy - 1, z2 - 1, DBLUE)
    wall_lights(type("p", (), {"x1": mid - 5, "z1": z1 + 1, "x2": mid + 5, "z2": z2 - 1})(), bb, fy, h, 10)
    wing_floor(bb, mid + 7, z1 + 1, x2 - 1, z2 - 1, fy, h, "minecraft:calcite", seed_of("nv", 0), tracker,
               ["storeroom", "office", "storeroom", "workshop", "office"], corridor="z", cw=3, wood="birch",
               carpet=(None, "minecraft:light_blue_carpet"), audit=audit, kit=True)
    # floors 2 and 3: barracks, infirmary, armory, stores, records
    for f, kinds in ((1, ["barracks", "barracks", "infirmary", "barracks", "armory", "barracks", "storeroom"]),
                     (2, ["barracks", "office", "library", "barracks", "armory", "bedroom", "radio"])):
        y = y0 + 1 + FH * f
        keep = [(mid - 3, z1 + 1, mid + 3, z1 + 10), (x1 + 1, z1 + 1, x1 + 5, z1 + 5)]
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, h, "minecraft:calcite", seed_of("nv", f), tracker, kinds, corridor="x", cw=3,
                   wood="birch", carpet=(None, "minecraft:light_blue_carpet"), audit=audit, keep=keep, kit=True, max_room=12, min_room=6)
    # the stair well in the north-west corner (ground to roof)
    stair_core(bb, x1 + 2, z1 + 2, 4, y0 + 1, top, [y0 + 1 + FH, y0 + 1 + 2 * FH, top + 1], "minecraft:calcite", "minecraft:quartz_stairs", slit=None)
    # main door: a porch with columns, the MARINE sign above
    bb.fill(mid - 4, y0 + 1, z2 + 1, mid + 4, y0 + 1, z2 + 4, "minecraft:smooth_quartz_slab[type=bottom]")
    for xx in (mid - 4, mid + 4):
        bb.fill(xx, y0 + 1, z2 + 4, xx, y0 + 5, z2 + 4, "minecraft:quartz_pillar[axis=y]")
    bb.fill(mid - 5, y0 + 6, z2 + 1, mid + 5, y0 + 6, z2 + 5, "minecraft:smooth_quartz")
    bb.fill(mid - 5, y0 + 7, z2 + 5, mid + 5, y0 + 7, z2 + 5, BLUE)
    bb.fill(mid - 1, y0 + 1, z2, mid + 1, y0 + 3, z2, AIR)
    return y0, top


def officers(bb, audit, tracker, top0):
    x1, z1, x2, z2 = HQ2
    top = tier(bb, x1, z1, x2, z2, top0, 2, FH, WHITE, "minecraft:light_blue_stained_glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band=BLUE, top_plate="minecraft:smooth_quartz", weights=[0.6, 0.25, 0.15], every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:light_blue_concrete")
    for f, kinds in ((0, ["captain", "radio", "office", "bedroom", "library"]), (1, ["bedroom", "office", "bedroom", "captain"])):
        y = top0 + 1 + FH * f
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, FH - 1, "minecraft:calcite", seed_of("nvo", f), tracker, kinds, corridor="x", cw=3,
                   wood="dark_oak", carpet=(None, "minecraft:blue_carpet"), audit=audit, kit=True,
                   keep=[(OFF[0], OFF[1], OFF[2], OFF[3])], min_room=6)
    stair_core(bb, x1 + 2, z2 - 6, 4, top0 + 1, top, [top0 + 1 + FH, top + 1], "minecraft:calcite", "minecraft:quartz_stairs", slit=None)
    # the roof terrace round the office tower: benches and lamps
    for xx in range(x1 + 2, x2 - 1, 8):
        lamp_post(bb, xx, top + 1, z2 - 1, post="minecraft:white_concrete_wall" if False else "minecraft:diorite_wall")
    return top


def office_tower(bb, base):
    """Jonathan's office: a square tower, tall windows on the harbour side, the radar dome and flag on top."""
    x1, z1, x2, z2 = OFF
    top = tier(bb, x1, z1, x2, z2, base, 2, FH, WHITE, "minecraft:light_blue_stained_glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band=BLUE, top_plate="minecraft:smooth_quartz", weights=[0.6, 0.25, 0.15], every=2, pil_every=4)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:light_blue_concrete")
    # the office: big desk facing the harbour windows, map table, bookcases, the commodore's chair
    fy = base + 1
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), fy, FH - 1, "captain", wood="dark_oak", seed=6930, doors=[((x1 + x2) // 2, z2)], accent="blue")
    for xx in range(x1 + 2, x2 - 1, 2):
        bb.fill(xx, fy + 1, z2, xx, fy + 3, z2, "minecraft:light_blue_stained_glass_pane")
    bb.fill((x1 + x2) // 2, fy, z2, (x1 + x2) // 2, fy + 1, z2, AIR)
    # upper floor: radar/plotting room
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), fy + FH, FH - 1, "radio", wood="birch", seed=6931, doors=[(x1 + 2, z1 + 2)])
    bb.fill(x1 + 1, fy, z1 + 1, x1 + 1, top, z1 + 1, "minecraft:ladder[facing=south]")
    bb.set(x1 + 1, fy + FH - 1, z1 + 1, "minecraft:ladder[facing=south]")
    # radar dome + mast + flag
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    bb.dome(cx, top + 1, cz, 6, "minecraft:white_concrete", hollow=True)
    bb.fill(cx, top + 7, cz, cx, top + 9, cz, "minecraft:iron_bars")
    bb.fill(cx - 3, top + 9, cz, cx + 3, top + 9, cz, "minecraft:iron_bars")
    bb.fill(x2 - 1, top + 1, z1 + 1, x2 - 1, top + 20, z1 + 1, "minecraft:iron_bars")
    for r in range(5):
        for c in range(8):
            gull = 1 <= r <= 3 and abs(c - 3.5) - r < 0 if False else (r == 2 and 2 <= c <= 5) or (r == 1 and c in (1, 6)) or (r == 3 and c in (3, 4))
            bb.set(x2 - 2 - c, top + 19 - r, z1 + 1, "minecraft:blue_wool" if gull else "minecraft:white_wool")
    return top


# ------------------------------------------------------------------ rim buildings, towers, guns
def barracks_east(bb, audit, tracker):
    x1, z1, x2, z2 = 136, 66, 154, 106
    y0 = RIM - 1
    bb.fill(x1 - 3, y0 - 10, z1 - 3, x2 + 3, y0, z2 + 3, "minecraft:stone")
    bb.fill(x1 - 3, y0 + 1, z1 - 3, x2 + 3, y0 + 30, z2 + 3, AIR)
    NT.cover(bb, x1 - 3, z1 - 3, x2 + 3, z2 + 3, lambda X, Z: np.full(np.broadcast(X, Z).shape, y0), PAVE, 6940, under="minecraft:stone",
             core="minecraft:stone", depth=1, base=y0)
    top = tier(bb, x1, z1, x2, z2, y0, 2, FH, WHITE, "minecraft:glass_pane", "minecraft:quartz_stairs", band=BLUE,
               top_plate="minecraft:smooth_quartz", weights=[0.6, 0.25, 0.15], every=3)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:light_blue_concrete")
    for f in range(2):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + 1 + FH * f, FH - 1, "minecraft:calcite", seed_of("nvb", f), tracker,
                   ["barracks", "barracks", "mess", "barracks", "storeroom"] if f == 0 else ["barracks", "infirmary", "barracks", "bedroom"],
                   corridor="z", cw=3, wood="birch", audit=audit, keep=[(x1 + 1, z1 + 1, x1 + 4, z1 + 4)], kit=True, min_room=6)
    bb.fill(x1 + 2, y0 + 1, z1 + 2, x1 + 2, top, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, y0 + FH, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, top, z1 + 2, AIR)
    bb.fill(x1, y0 + 1, (z1 + z2) // 2 - 1, x1, y0 + 3, (z1 + z2) // 2 + 1, AIR)


def depot_west(bb, audit, tracker):
    """Supply depot on the west rim: a big shed with racks of crates and barrels, a fuel store, a crane over the
    cliff to the quay below."""
    x1, z1, x2, z2 = 20, 72, 40, 100
    y0 = RIM - 1
    bb.fill(x1 - 3, y0 - 10, z1 - 3, x2 + 6, y0, z2 + 3, "minecraft:stone")
    bb.fill(x1 - 3, y0 + 1, z1 - 3, x2 + 6, y0 + 25, z2 + 3, AIR)
    NT.cover(bb, x1 - 3, z1 - 3, x2 + 6, z2 + 3, lambda X, Z: np.full(np.broadcast(X, Z).shape, y0), PAVE, 6950, under="minecraft:stone",
             core="minecraft:stone", depth=1, base=y0)
    bb.walls(x1, y0 + 1, z1, x2, y0 + 7, z2, "minecraft:white_concrete")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:smooth_stone")
    for zz in range(z1 + 2, z2 - 1, 4):
        bb.fill(x1, y0 + 4, zz, x1, y0 + 5, zz, "minecraft:glass_pane"); bb.fill(x2, y0 + 4, zz, x2, y0 + 5, zz, "minecraft:glass_pane")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + 8, "minecraft:cyan_terracotta" if False else "minecraft:prismarine_brick_stairs",
                 ridge="minecraft:dark_prismarine", ridge_axis="z", gable_fill="minecraft:white_concrete", overhang=0)
    bb.fill(x2, y0 + 1, (z1 + z2) // 2 - 2, x2, y0 + 4, (z1 + z2) // 2 + 2, AIR)
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), y0 + 1, 6, "storeroom", wood="spruce", seed=6951, doors=[(x2, (z1 + z2) // 2)])
    # racks down the middle
    for zz in range(z1 + 4, z2 - 3, 6):
        for xx in range(x1 + 6, x2 - 5, 3):
            if bb.get_region(xx, y0 + 1, zz, xx, y0 + 1, zz)[0, 0, 0] in (0, 1):
                bb.fill(xx, y0 + 1, zz, xx, y0 + 3, zz, "minecraft:barrel[facing=up,open=false]")
    # crane on the cliff edge
    cx, cz = x2 + 4, z2 - 4
    bb.fill(cx, y0 + 1, cz, cx, y0 + 14, cz, "minecraft:white_concrete")
    bb.fill(cx, y0 + 14, cz, cx + 12, y0 + 14, cz, "minecraft:white_concrete")
    bb.fill(cx + 12, y0 + 2, cz, cx + 12, y0 + 13, cz, "minecraft:iron_chain[axis=y]")
    bb.set(cx - 1, y0 + 14, cz, "minecraft:iron_block")
    bb.fill(cx - 1, y0 + 1, cz - 1, cx + 1, y0 + 1, cz + 1, "minecraft:polished_andesite")


def searchlight(bb, x, z):
    y0 = hy(x, z)
    bb.fill(x - 2, y0 - 6, z - 2, x + 2, y0, z + 2, "minecraft:stone_bricks")
    bb.fill(x - 1, y0 + 1, z - 1, x + 1, y0 + 12, z + 1, "minecraft:white_concrete")
    bb.fill(x - 1, y0 + 4, z - 1, x + 1, y0 + 4, z + 1, BLUE)
    bb.fill(x - 1, y0 + 9, z - 1, x + 1, y0 + 9, z + 1, BLUE)
    bb.fill(x - 2, y0 + 13, z - 2, x + 2, y0 + 13, z + 2, "minecraft:smooth_quartz_slab[type=bottom]")
    bb.fill(x - 1, y0 + 13, z - 1, x + 1, y0 + 13, z + 1, "minecraft:smooth_quartz")
    for (a, b) in ((x - 2, z - 2), (x + 2, z - 2), (x - 2, z + 2), (x + 2, z + 2)):
        bb.set(a, y0 + 14, b, "minecraft:iron_bars")
    bb.set(x, y0 + 14, z, "minecraft:sea_lantern")
    bb.set(x, y0 + 15, z, "minecraft:iron_trapdoor[facing=north,half=bottom,open=true]")
    bb.fill(x, y0 + 1, z + 2, x, y0 + 13, z + 2, "minecraft:ladder[facing=south]")
    bb.fill(x, y0 + 1, z + 1, x, y0 + 12, z + 1, AIR)
    bb.fill(x, y0 + 1, z + 2, x, y0 + 2, z + 2, "minecraft:ladder[facing=south]")


def battery(bb, x, z, facing):
    """A gun emplacement on the rim edge: stone pad, a parapet with an embrasure, the cannon, shot and a hut."""
    y0 = hy(x, z)
    if y0 < RIM - 6:
        return False
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
    px, pz = (1, 0) if dx == 0 else (0, 1)
    bb.fill(x - 3, y0, z - 3, x + 3, y0, z + 3, "minecraft:polished_andesite")
    bb.fill(x - 3, y0 + 1, z - 3, x + 3, y0 + 4, z + 3, AIR)
    for k in range(-3, 4):
        bb.set(x + dx * 3 + px * k, y0 + 1, z + dz * 3 + pz * k, "minecraft:stone_bricks")
        if abs(k) > 1:
            bb.set(x + dx * 3 + px * k, y0 + 2, z + dz * 3 + pz * k, "minecraft:stone_brick_wall")
    bb.set(x + dx, y0 + 1, z + dz, f"onepiece:cannon[facing={facing}]")
    bb.set(x - dx * 2 + px * 2, y0 + 1, z - dz * 2 + pz * 2, "minecraft:barrel[facing=up,open=false]")
    bb.set(x - dx * 2 - px * 2, y0 + 1, z - dz * 2 - pz * 2, "minecraft:coal_block")
    return True


def stair_tower(bb, x, z, rim_side):
    """A white stair tower from the quay up to the rim, with a little bridge to the rim at the top."""
    top = RIM + 2
    bb.fill(x - 1, -6, z - 1, x + 6, QY, z + 6, "minecraft:stone_bricks")
    stair_core(bb, x, z, 6, QY + 1, top, [QY + 1, top + 1], "minecraft:white_concrete", "minecraft:quartz_stairs", slit="minecraft:light_blue_stained_glass")
    for yy in range(QY + 6, top, 6):
        bb.fill(x - 1, yy, z - 1, x + 6, yy, z - 1, BLUE); bb.fill(x - 1, yy, z + 6, x + 6, yy, z + 6, BLUE)
        bb.fill(x - 1, yy, z - 1, x - 1, yy, z + 6, BLUE); bb.fill(x + 6, yy, z - 1, x + 6, yy, z + 6, BLUE)
    bb.fill(x - 2, top + 4, z - 2, x + 7, top + 4, z + 7, "minecraft:smooth_quartz")
    bb.fill(x - 1, top + 5, z - 1, x + 6, top + 5, z + 6, "minecraft:smooth_quartz_slab[type=bottom]")
    # quay door
    bb.fill(x + 2, QY + 1, z + 6, x + 3, QY + 3, z + 6, AIR)
    bb.fill(x + 2, QY + 1, z - 1, x + 3, QY + 3, z - 1, AIR)
    # bridge to the rim
    bx = (x - 1, -1) if rim_side == "west" else (x + 6, 1) if rim_side == "east" else None
    if rim_side == "north":
        for k in range(1, 12):
            bb.fill(x + 1, top, z - 1 - k, x + 4, top, z - 1 - k, "minecraft:smooth_stone")
            bb.fill(x + 1, top + 1, z - 1 - k, x + 4, top + 3, z - 1 - k, AIR)
            bb.set(x + 1, top + 1, z - 1 - k, "minecraft:diorite_wall"); bb.set(x + 4, top + 1, z - 1 - k, "minecraft:diorite_wall")
        bb.fill(x + 2, top + 1, z - 1, x + 3, top + 3, z - 1, AIR)
    else:
        sgn = bx[1]
        edge = x + 6 if sgn > 0 else x - 1
        for k in range(1, 12):
            xx = edge + sgn * k
            bb.fill(xx, top, z + 1, xx, top, z + 4, "minecraft:smooth_stone")
            bb.fill(xx, top + 1, z + 1, xx, top + 3, z + 4, AIR)
            bb.set(xx, top + 1, z + 1, "minecraft:diorite_wall"); bb.set(xx, top + 1, z + 4, "minecraft:diorite_wall")
        bb.fill(edge, top + 1, z + 2, edge, top + 3, z + 3, AIR)


def quay_props(bb, rng):
    """Bollards, lamps, crates and cranes round the quay; the repair dock scaffolding."""
    pts = []
    for a in range(0, 360, 6):
        t = math.radians(a)
        x, z = int(round(HX + (HRX + 1.2) * math.cos(t))), int(round(HZ + (HRZ + 1.2) * math.sin(t)))
        if channel(np.array([[x]]), np.array([[z]]))[0, 0] or abs(x - HX) < CH + 5 and z > HZ:
            continue
        pts.append((a, x, z))
    for i, (a, x, z) in enumerate(pts):
        if i % 3 == 0:
            bb.set(x, QY + 1, z, "minecraft:polished_andesite_slab[type=bottom]" if False else "minecraft:stone_brick_wall")
        t = math.radians(a)
        lx, lz = int(round(HX + (HRX + 3) * math.cos(t))), int(round(HZ + (HRZ + 3) * math.sin(t)))
        if i % 5 == 2 and hy(lx, lz) == QY:
            lamp_post(bb, lx, QY + 1, lz, post="minecraft:iron_bars", h=3)
        elif i % 7 == 4 and hy(lx, lz) == QY:
            bb.set(lx, QY + 1, lz, "minecraft:barrel[facing=up,open=false]")
            if rng.random() < 0.5:
                bb.set(lx, QY + 2, lz, "minecraft:barrel[facing=up,open=false]")
    # two gantry cranes on the north quay
    for gx in (HX - 14, HX + 16):
        gz = HZ - HRZ - 1
        for (a, b) in ((gx - 3, gz - 2), (gx + 3, gz - 2), (gx - 3, gz + 1), (gx + 3, gz + 1)):
            bb.fill(a, QY + 1, b, a, QY + 13, b, "minecraft:white_concrete" if (a + b) % 2 else BLUE)
        bb.fill(gx - 3, QY + 14, gz - 2, gx + 3, QY + 14, gz + 1, "minecraft:white_concrete")
        bb.fill(gx - 1, QY + 14, gz + 2, gx + 1, QY + 14, gz + 12, "minecraft:white_concrete")
        bb.fill(gx - 1, QY + 15, gz - 1, gx + 1, QY + 17, gz, "minecraft:light_blue_concrete")
        bb.fill(gx, QY + 7, gz + 11, gx, QY + 13, gz + 11, "minecraft:iron_chain[axis=y]")
        bb.set(gx, QY + 6, gz + 11, "minecraft:iron_block")


def design():
    bb = BigBuild(seed=6910, y_min=-16, y_max=100)
    tracker = P.PropTracker(6910)
    audit = []
    rng = np.random.default_rng(6910)
    terrain(bb)
    tunnel(bb)
    y0, top0 = hq(bb, audit, tracker)
    top1 = officers(bb, audit, tracker, top0)
    office_tower(bb, top1)
    barracks_east(bb, audit, tracker)
    depot_west(bb, audit, tracker)
    lights = []
    for ang in (225, 315, 135, 45):
        t = math.radians(ang)
        for r in range(72, 40, -1):
            x, z = int(round(C + r * math.cos(t))), int(round(C + r * math.sin(t)))
            if hy(x, z) >= RIM - 3 and hy(x + 2, z + 2) >= RIM - 3 and hy(x - 2, z - 2) >= RIM - 3:
                searchlight(bb, x - int(3 * math.cos(t)), z - int(3 * math.sin(t)))
                lights.append((x - int(3 * math.cos(t)), z - int(3 * math.sin(t))))
                break
    n = 0
    for a in range(0, 360, 15):
        t = math.radians(a)
        for r in range(74, 50, -1):
            x, z = int(round(C + r * math.cos(t))), int(round(C + 2 + r * math.sin(t)))
            if 0 < x < N and 0 < z < N and hy(x, z) >= RIM - 4 and not (HQ[0] - 8 < x < HQ[2] + 8 and HQ[1] - 8 < z < HQ[3] + 12):
                face = "east" if abs(math.cos(t)) > abs(math.sin(t)) and math.cos(t) > 0 else "west" if abs(math.cos(t)) > abs(math.sin(t)) else \
                    "south" if math.sin(t) > 0 else "north"
                n += battery(bb, x, z, face)
                break
    stair_tower(bb, HX - HRX + 4, HZ - 12, "west")
    stair_tower(bb, HX + HRX - 10, HZ - 12, "east")
    quay_props(bb, rng)
    # the Going Merry in the repair dock (west), scaffold towers along her side; the warship moored east
    stamp_ship(bb, "going_merry", HX - 14, HZ + 4, water_y=0, rot=0)
    for xx in range(HX - 28, HX + 1, 6):
        bb.fill(xx, -8, HZ + 15, xx, 9, HZ + 15, "minecraft:spruce_fence")
        bb.fill(xx - 1, 4, HZ + 14, xx + 1, 4, HZ + 15, "minecraft:spruce_slab[type=top]")
        bb.fill(xx - 1, 9, HZ + 14, xx + 1, 9, HZ + 15, "minecraft:spruce_slab[type=top]")
    stamp_ship(bb, "marine_warship", HX + 18, HZ + 6, water_y=0, rot=1)
    # trees and scrub on the rim
    for _ in range(140):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if hy(x, z) >= RIM - 3 and not steep(np.array([[x]]), np.array([[z]]))[0, 0] and is_free(bb, x, hy(x, z) + 1, z, 2) \
                and not (HQ[0] - 8 < x < HQ[2] + 8 and HQ[1] - 8 < z < HQ[3] + 12):
            if rng.random() < 0.35:
                P.tree(bb, x, hy(x, z) + 1, z, height=int(rng.integers(5, 8)), kind="spruce" if rng.random() < 0.6 else "oak", rng=rng)
            else:
                bb.set(x, hy(x, z) + 1, z, "minecraft:sweet_berry_bush[age=1]" if rng.random() < 0.3 else "minecraft:short_grass")
    # vines on the inner cliff
    for _ in range(260):
        x, z = int(rng.integers(40, 136)), int(rng.integers(70, 136))
        e = E[x, z]
        if 1.12 < e < 1.5 and steep(np.array([[x]]), np.array([[z]]))[0, 0]:
            ytop = hy(x, z)
            for (ox, oz, f) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
                if hy(x + ox, z + oz) < ytop - 3:
                    L = int(rng.integers(2, 12))
                    for k in range(L):
                        yy = ytop - k
                        if yy <= hy(x + ox, z + oz) + 1:
                            break
                        set_if_air(bb, x + ox, yy, z + oz, f"minecraft:vine[{f}=true]")
                    break
    return bb, audit, y0, top0, top1, lights


def is_free(bb, x, y, z, r):
    return (bb.get_region(x - r, y, z - r, x + r, y + 3, z + r) <= 1).all()


def build():
    bb, audit, y0, top0, top1, lights = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    mid = (HQ[0] + HQ[2]) // 2
    b.text(mid - 15, y0 + 3 * FH - 1, HQ[3] + 1, "MARINE", DBLUE, scale=1) if False else None
    b.chest(OFF[0] + 2, top1 + 1, OFF[1] + 2, "marine", "south")
    b.chest(HQ[0] + 8, y0 + 1 + FH, HQ[1] + 2, "marine", "south")
    b.chest(24, RIM, 76, "medium", "east")
    b.chest(HX - 4, QY + 1, HZ - HRZ - 1, "easy", "south")
    for (x, z) in ((mid - 4, HQ[3] + 6), (mid + 4, HQ[3] + 6), (HX - 10, HZ - HRZ - 1), (HX + 10, HZ - HRZ - 1), (HX - CH - 3, TUN[0] - 2)):
        b.guard(x, hy(x, z) + 1 if hy(x, z) > QY else QY + 1, z, "marine")
    for (x, z) in lights[:2]:
        b.guard(x, hy(x, z) + 14, z, "marine_rifle")
    b.guards("elite_marine", ((mid, HQ[3] - 4),), y=y0 + 1)
    return b, 0
