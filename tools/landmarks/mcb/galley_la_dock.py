"""Water 7 and the Galley-La docks, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/galley_la_dock.md).

The Water Capital: a round city rising in three terraces to the Great Fountain, ring canals with bridges, grand
stairs up every terrace, tall narrow stucco and brick houses (all furnished) all the way round. On the east shore
Galley-La Company's Dock 1: two slipways open to the sea, a galleon on the ways and a new hull still in its ribs,
red gantry cranes, workshops, timber stacks and the DOCK 1 gate; south of it the Galley-La headquarters (Iceburg's
office, meeting hall, offices) with its clock tower, and a yagara boat landing. ~224 x 224, fountain ~80 tall.
Ground (outer ring) = y 0. (v2, 2026-10-29)"""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     table, tier, cornice, set_if_air)
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import terrain3 as T3

SID = "galley_la_dock"
TITLE = "Water 7 and the Galley-La docks"
CUTS = [3, 15, 27]
TILER = dict(terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False
LOBE = (150, 8, 222, 206, 16)                            # rounded east lobe: x1, z1, x2, z2, corner radius
LX = 204                                                 # east end of the yagara landing

STONE = "onepiece:canal_bricks"
STONE_ST = "onepiece:canal_brick_stairs"
STONE_SL = "onepiece:canal_brick_slab"
STONE_W = "onepiece:canal_brick_wall"
COBBLE = ["onepiece:water7_cobbles", "minecraft:stone_bricks", "onepiece:water7_cobbles"]
COBBLE_ST = "onepiece:water7_cobble_stairs"
COBBLE_W = "onepiece:water7_cobble_wall"
STUCCO = "onepiece:dressrosa_stucco"
TILES = "onepiece:dressrosa_tiles"
TILES_ST = "onepiece:dressrosa_tile_stairs"
WATER = "minecraft:water[level=0]"
JET = "minecraft:light_blue_stained_glass"
FOAM = "minecraft:white_stained_glass"
RED = "minecraft:red_concrete"
GLASS = "minecraft:glass_pane"

N = 224
CX, CZ = 100, 112
R = 96
TIERS = ((R, 0), (70, 12), (46, 24), (24, 36))          # radius -> street top y
CANALS = ((72, 77, 0), (48, 51, 12))                     # (r1, r2, street y): water 4 below the street
AXES = ("n", "s", "w")
DOCK = (156, 16, 218, 120)                              # x1, z1, x2, z2
HQ = (158, 132, 204, 166)
SLIPS = ((30, 50), (74, 94))                            # z ranges of the slipways

PALS = [
    dict(walls=[STUCCO, "minecraft:white_terracotta", STUCCO], frame=STONE,
         base=COBBLE, floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:smooth_sandstone"], frame=STONE,
         base=COBBLE, floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:bricks", "minecraft:bricks", "minecraft:granite"], frame="minecraft:smooth_quartz",
         base=COBBLE, floor="minecraft:dark_oak_planks", wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:calcite", "minecraft:white_concrete_powder", "minecraft:calcite"], frame=STONE,
         base=COBBLE, floor="minecraft:spruce_planks", wood="mangrove", chimney="minecraft:bricks"),
    dict(walls=["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:light_blue_terracotta"],
         frame="minecraft:smooth_quartz", base=COBBLE, floor="minecraft:spruce_planks", wood="spruce",
         chimney="minecraft:bricks"),
]
ROOFS = [TILES_ST, TILES_ST, "minecraft:brick_stairs", "minecraft:mangrove_stairs", "minecraft:prismarine_brick_stairs"]


def street_y(r):
    y = None
    for (rr, yy) in TIERS:
        if r <= rr:
            y = yy
    return y


def in_dock(x, z, pad=0):
    return DOCK[0] - pad <= x <= DOCK[2] + pad and DOCK[1] - pad <= z <= DOCK[3] + pad


def in_hq(x, z, pad=0):
    return HQ[0] - pad <= x <= HQ[2] + pad and HQ[1] - pad <= z <= HQ[3] + pad


def axis_of(x, z, width=6):
    """Which stair axis (if any) a point is on."""
    if abs(x - CX) <= width and z > CZ:
        return "s"
    if abs(x - CX) <= width and z < CZ:
        return "n"
    if abs(z - CZ) <= width and x < CX:
        return "w"
    return None


# ---------------------------------------------------------------- terrain: terraces, canals, quays
def lobe_mask():
    """The dock and HQ quarter: a rounded slab of land east of the city with a gently wobbling quay line (v3: was a
    square plot cut off by the build's edge)."""
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    x1, z1, x2, z2, rc = LOBE
    qx = np.clip(X, x1 + rc, x2 - rc); qz = np.clip(Z, z1 + rc, z2 - rc)
    wob = 1.5 * NT.noise(X, Z, 707, 13)
    return (np.hypot(X - qx, Z - qz) <= rc + wob) & (X >= x1 - 30)


def quay_and_sea(bb):
    """A canal-brick quay wall round the whole island and a round patch of sea round it, so the city stands in the sea."""
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    land = (np.hypot(X - CX, Z - CZ) <= R) | lobe_mask()
    edge = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1))
    edge &= np.hypot(X - CX, Z - CZ) > R - 1.5
    bb.fill_where(0, -7, 0, N - 1, 0, N - 1, lambda XX, y, ZZ: edge[XX, ZZ], STONE)
    bb.fill_where(0, 1, 0, N - 1, 1, N - 1, lambda XX, y, ZZ: edge[XX, ZZ], COBBLE_W)
    T3.sea(bb, N, land, N / 2, N / 2, N / 2 - 1, 717, top=-1, deep=-12, shelf=10, y_min=-12)


def terrain(bb):
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    r = np.hypot(X - CX, Z - CZ)
    city = r <= R
    land = city | lobe_mask()
    # base: the sea floor everywhere, water up to y -1 off the island (the sea around Water 7)
    # only the island itself: around it the world's own coast and sea stay as they are
    bb.fill_where(0, -10, 0, N - 1, -1, N - 1, lambda XX, y, ZZ: land[XX, ZZ], "minecraft:stone")
    for (rr, yy) in TIERS:
        bb.fill_where(0, 0, 0, N - 1, yy, N - 1,
                      lambda XX, y, ZZ, rr=rr, yy=yy: (np.hypot(XX - CX, ZZ - CZ) <= rr) & (y < yy), "minecraft:stone")
        bb.fill_where(0, yy, 0, N - 1, yy, N - 1,
                      lambda XX, y, ZZ, rr=rr: (np.hypot(XX - CX, ZZ - CZ) <= rr), COBBLE[0])
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda XX, y, ZZ: land[XX, ZZ] & ~city[XX, ZZ], COBBLE[0])
    # paving pattern rings
    for (rr, yy) in TIERS:
        bb.fill_where(0, yy, 0, N - 1, yy, N - 1,
                      lambda XX, y, ZZ, rr=rr: (np.abs(np.hypot(XX - CX, ZZ - CZ) - (rr - 2)) < 0.8), "minecraft:polished_andesite")
    # terrace walls (canal bricks) with a balustrade on top
    for (rr, yy) in TIERS[1:]:
        ring = lambda XX, y, ZZ, rr=rr: (np.hypot(XX - CX, ZZ - CZ) <= rr) & (np.hypot(XX - CX, ZZ - CZ) > rr - 1.6)
        bb.fill_where(0, 0, 0, N - 1, yy, N - 1, ring, STONE)
        bb.fill_where(0, yy + 1, 0, N - 1, yy + 1, N - 1, ring, STONE_W)
    # ring canals, water 4 deep below the street, stone banks
    for (r1, r2, yy) in CANALS:
        ch = lambda XX, y, ZZ, r1=r1, r2=r2: (np.hypot(XX - CX, ZZ - CZ) >= r1) & (np.hypot(XX - CX, ZZ - CZ) <= r2)
        bb.fill_where(0, yy - 5, 0, N - 1, yy - 5, N - 1, ch, "minecraft:sand")
        bb.fill_where(0, yy - 4, 0, N - 1, yy - 1, N - 1, ch, WATER)
        bb.fill_where(0, yy, 0, N - 1, yy, N - 1, ch, AIR)
        for rb in (r1 - 1, r2 + 1):
            edge = lambda XX, y, ZZ, rb=rb: np.abs(np.hypot(XX - CX, ZZ - CZ) - rb) < 0.7
            bb.fill_where(0, yy - 4, 0, N - 1, yy, N - 1, edge, STONE)
            bb.fill_where(0, yy + 1, 0, N - 1, yy + 1, N - 1, edge, COBBLE_W)
    # the outer quay round the city at sea level
    quay_and_sea(bb)


def grand_stairs(bb):
    """A stair up each terrace on the north, south and west axes, with a bridge over each canal and lamps."""
    for (rr, yy) in TIERS[1:]:
        lo = [y for (r2, y) in TIERS if r2 > rr][-1]           # street height below this terrace
        h = yy - lo
        for ax in AXES:
            d = {"s": (0, 1), "n": (0, -1), "w": (-1, 0)}[ax]
            # top of the flight sits inside the terrace edge; it descends outwards to the wall line
            for i in range(h):
                y = lo + 1 + i                                   # step height
                dist = rr - (h - 1 - i)                          # radius of this step
                if ax in ("s", "n"):
                    z = CZ + d[1] * dist
                    bb.fill(CX - 4, y, z, CX + 4, y, z, st(COBBLE_ST, "north" if ax == "s" else "south"))
                    bb.fill(CX - 4, y + 1, z, CX + 4, y + 4, z, AIR)
                    bb.fill(CX - 5, y, z, CX - 5, y + 1, z, STONE); bb.fill(CX + 5, y, z, CX + 5, y + 1, z, STONE)
                else:
                    x = CX + d[0] * dist
                    bb.fill(x, y, CZ - 4, x, y, CZ + 4, st(COBBLE_ST, "east"))
                    bb.fill(x, y + 1, CZ - 4, x, y + 4, CZ + 4, AIR)
                    bb.fill(x, y, CZ - 5, x, y + 1, CZ - 5, STONE); bb.fill(x, y, CZ + 5, x, y + 1, CZ + 5, STONE)
    # bridges over the canals on the axes and on the diagonals
    for (r1, r2, yy) in CANALS:
        for a in (90, 270, 180, 135, 225, 45, 315, 0):
            t = math.radians(a)
            for k in range(r1 - 2, r2 + 3):
                x, z = round(CX + k * math.cos(t)), round(CZ + k * math.sin(t))
                if in_dock(x, z, 2):
                    continue
                for w in range(-2, 3):
                    px, pz = round(x - w * math.sin(t)), round(z + w * math.cos(t))
                    hump = 1 if r1 + 1 <= k <= r2 - 1 else 0
                    bb.set(px, yy + hump, pz, "minecraft:stone_bricks")
                for w in (-3, 3):
                    px, pz = round(x - w * math.sin(t)), round(z + w * math.cos(t))
                    bb.set(px, yy + 1 + (1 if r1 + 1 <= k <= r2 - 1 else 0), pz, STONE_W)


def rings_of_houses(bb, tracker, audit, rng):
    placed = []
    bands = [(87, 0, 3), (61, 12, 3), (36, 24, 3)]               # (radius, street y, max floors)
    for (rad, yy, mf) in bands:
        a = 0.0
        i = 0
        while a < 2 * math.pi:
            i += 1
            w = int(rng.integers(9, 12)); d = int(rng.integers(9, 13))
            hx, hz = CX + rad * math.cos(a), CZ + rad * math.sin(a)
            dxc, dzc = CX - hx, CZ - hz
            rot = (0 if dzc > 0 else 2) if abs(dzc) >= abs(dxc) else (3 if dxc > 0 else 1)
            W, D = (w, d) if rot % 2 == 0 else (d, w)
            tang = abs(math.sin(a)) * W + abs(math.cos(a)) * D          # footprint along the ring
            x0, z0 = int(round(hx - W / 2)), int(round(hz - D / 2))
            box = (x0 - 1, z0 - 1, x0 + W, z0 + D)
            corners = [(box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])]
            ok = all(street_y(math.hypot(x - CX, z - CZ)) == yy for (x, z) in corners)
            ok = ok and not any(axis_of(x, z, 7) for (x, z) in corners + [(int(hx), int(hz))])
            ok = ok and not any(in_dock(x, z, 3) or in_hq(x, z, 3) for (x, z) in corners)
            ok = ok and not any(box[0] <= p[2] and p[0] <= box[2] and box[1] <= p[3] and p[1] <= box[3] for p in placed)
            if not ok:
                a += 2.0 / rad
                continue
            k = int(rng.integers(len(PALS)))
            floors = int(rng.integers(2, mf + 2))
            m, top, au = house_module(seed_of("w7", rad, i), w, d, floors, ROOFS[int(rng.integers(len(ROOFS)))], tracker,
                                      [["kitchen", "living", "workshop"][int(rng.integers(3))], "bedroom", "library", "bedroom"],
                                      pal=PALS[k], timber=False, jetty=False)
            audit += au
            place_house(bb, m, w, d, x0, yy, z0, rot)
            placed.append(box)
            a += (tang + 2.5) / rad
    return placed


def fountain(bb):
    """The Great Fountain on the top terrace: three basins of real water stepping up round a column, glass jets and
    foam pouring from rim to rim, and the tall jet at the top."""
    y0 = TIERS[3][1]
    bb.cylinder(CX, y0 + 1, CZ, 18, y0 + 2, STONE)
    bb.cylinder(CX, y0 + 2, CZ, 17, y0 + 2, WATER)
    bb.cylinder(CX, y0 + 1, CZ, 10, y0 + 14, STONE)
    bb.cylinder(CX, y0 + 15, CZ, 12, y0 + 15, STONE)
    bb.cylinder(CX, y0 + 16, CZ, 12, y0 + 16, STONE_W)
    bb.cylinder(CX, y0 + 16, CZ, 11, y0 + 16, WATER)
    bb.cylinder(CX, y0 + 16, CZ, 5, y0 + 30, STONE)
    bb.cylinder(CX, y0 + 31, CZ, 7, y0 + 31, STONE)
    bb.cylinder(CX, y0 + 32, CZ, 7, y0 + 32, STONE_W)
    bb.cylinder(CX, y0 + 32, CZ, 6, y0 + 32, WATER)
    bb.cylinder(CX, y0 + 32, CZ, 2, y0 + 52, JET)
    bb.cylinder(CX, y0 + 49, CZ, 4, y0 + 53, FOAM, hollow=True)
    bb.cylinder(CX, y0 + 53, CZ, 3, y0 + 53, FOAM)
    # falling curtains from each basin rim to the one below
    for (r_, ytop, ybot) in ((12, y0 + 15, y0 + 3), (7, y0 + 31, y0 + 17), (4, y0 + 48, y0 + 33)):
        for a in range(0, 360, 4):
            if a % 24 in (0, 4):
                continue
            t = math.radians(a)
            x, z = round(CX + (r_ + 1) * math.cos(t)), round(CZ + (r_ + 1) * math.sin(t))
            for y in range(ybot, ytop):
                bb.set(x, y, z, FOAM if (y + a) % 5 == 0 else JET)
    # decorative arches round the pedestal
    for a in range(0, 360, 45):
        t = math.radians(a)
        x, z = round(CX + 10 * math.cos(t)), round(CZ + 10 * math.sin(t))
        bb.fill(x, y0 + 3, z, x, y0 + 13, z, "minecraft:smooth_quartz")
    # benches and lamps round the fountain plaza
    for a in range(0, 360, 30):
        t = math.radians(a)
        x, z = round(CX + 21 * math.cos(t)), round(CZ + 21 * math.sin(t))
        if axis_of(x, z, 5):
            continue
        lamp_post(bb, x, y0 + 1, z, h=4)


# ---------------------------------------------------------------- Dock 1
def ship_frame(bb, x0, z0, L, beam):
    """A hull still in its ribs on the slipway: keel, stem and sternpost, ribs every 3, a few strakes planked."""
    cz = z0
    hw = beam // 2
    bb.fill(x0, -2, cz, x0 + L, -2, cz, "minecraft:stripped_spruce_log[axis=x]")
    for i in range(0, L + 1, 3):
        t = i / L
        p = math.sqrt(max(0.0, 1 - abs(2 * t - 1) ** 3)) if t > 0.4 else 1.0
        h = max(1, int(round(hw * p)))
        for y in range(-1, 9):
            frac = 0.45 + 0.55 * min(1.0, (y + 1) / 6)
            w = max(1, int(round(h * frac)))
            bb.set(x0 + i, y, cz - w, "minecraft:stripped_oak_log[axis=y]")
            bb.set(x0 + i, y, cz + w, "minecraft:stripped_oak_log[axis=y]")
        bb.fill(x0 + i, 8, cz - h, x0 + i, 8, cz + h, "minecraft:stripped_oak_log[axis=z]")
    for i in range(0, L - 6):                                              # lower strakes planked
        t = i / L
        p = math.sqrt(max(0.0, 1 - abs(2 * t - 1) ** 3)) if t > 0.4 else 1.0
        h = max(1, int(round(hw * p)))
        for y in (-1, 0, 1, 2):
            frac = 0.45 + 0.55 * min(1.0, (y + 1) / 6)
            w = max(1, int(round(h * frac)))
            bb.set(x0 + i, y, cz - w, "minecraft:oak_planks"); bb.set(x0 + i, y, cz + w, "minecraft:oak_planks")
    bb.fill(x0 + L, -1, cz, x0 + L + 2, 10, cz, "minecraft:stripped_oak_log[axis=y]")
    bb.fill(x0 - 1, -1, cz, x0 - 1, 9, cz, "minecraft:stripped_oak_log[axis=y]")
    # scaffolding along both sides
    for i in range(2, L, 5):
        for s in (-1, 1):
            zz = cz + s * (hw + 2)
            bb.fill(x0 + i, -8, zz, x0 + i, -1, zz, "minecraft:stripped_spruce_log[axis=y]")   # a pile under it, or it drops
            bb.fill(x0 + i, 0, zz, x0 + i, 9, zz, "minecraft:scaffolding[bottom=false,distance=0,waterlogged=false]")


def gantry(bb, x, z1, z2, h=30):
    for z in (z1, z2):
        bb.fill(x, 1, z, x + 1, h, z + 1, RED)
    bb.fill(x, h + 1, z1, x + 1, h + 2, z2 + 1, RED)
    bb.fill(x - 1, h + 3, z1, x + 2, h + 3, z2 + 1, "minecraft:red_terracotta")
    for z in range(z1 + 3, z2, 4):
        bb.set(x, h, z, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    mid = (z1 + z2) // 2
    bb.fill(x - 1, h, mid - 1, x + 2, h, mid + 1, "minecraft:yellow_concrete")
    bb.fill(x, h - 12, mid, x, h - 1, mid, "minecraft:iron_chain[axis=y,waterlogged=false]")
    bb.set(x, h - 13, mid, "onepiece:anchor[facing=east]")
    bb.fill(x + 2, 1, z1, x + 2, h, z1, "minecraft:ladder[facing=east]")


def dock_one(bb, tracker, audit, rng):
    x1, z1, x2, z2 = DOCK
    # the yard: cobbles, a brick wall round the land side, the gate
    bb.fill(x1, 0, z1, x2, 0, z2, COBBLE[0])
    bb.mix(x1, 0, z1, x2, 0, z2, COBBLE, [0.6, 0.3, 0.1])
    for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2)):
        bb.fill(a, 1, b, c, 4, d, "minecraft:bricks")
        bb.fill(a, 5, b, c, 5, d, STONE_W)
    gz = (z1 + z2) // 2 + 4
    bb.fill(x1 - 1, 1, gz - 13, x1 + 1, 21, gz + 13, "minecraft:bricks")
    P.arched_opening(bb, "z", gz, 1, x1 - 1, 9, 11, depth=3, trim=STONE)
    bb.fill(x1 - 1, 0, gz - 4, x1 + 1, 0, gz + 4, "minecraft:polished_andesite")
    bb.fill(x1 - 2, 13, gz - 12, x1 - 2, 20, gz + 12, "minecraft:white_concrete")
    cornice(bb, x1 - 1, gz - 13, x1 + 1, gz + 13, 21, STONE_ST, parapet=STONE_W)
    # slipways: water channels open to the sea at the east edge, a ramp at the land end
    for (a, b) in SLIPS:
        bb.fill(x1 + 22, -7, a, x2, -1, b, WATER)
        bb.fill(x1 + 22, 0, a, x2, 0, b, AIR)
        bb.fill(x2, -8, a - 1, x2, 1, b + 1, STONE)                       # the sea gate (closed) at the end
        bb.fill(x2, 2, a - 1, x2, 2, b + 1, STONE_W)
        for i in range(8):                                                # the ways sloping into the water
            bb.fill(x1 + 18 + i, -1 - i // 2, a + 2, x1 + 18 + i, -i // 2, b - 2, "minecraft:spruce_planks")
            bb.fill(x1 + 18 + i, 1 - i // 2, a + 2, x1 + 18 + i, 2, b - 2, AIR)
        for (zz, f) in ((a - 1, "south"), (b + 1, "north")):
            bb.fill(x1 + 18, -7, zz, x2, 0, zz, STONE)
            for x in range(x1 + 20, x2, 6):
                bb.set(x, 1, zz, "minecraft:spruce_fence")
    # a galleon on the ways in the north slip, a new hull in its ribs in the south one
    P.ship(bb, x1 + 26, -5, (SLIPS[0][0] + SLIPS[0][1]) // 2, length=38, beam=13, depth=7, masts=2,
           hull="minecraft:spruce_planks", deck="minecraft:oak_planks", sail="minecraft:white_wool")
    ship_frame(bb, x1 + 24, (SLIPS[1][0] + SLIPS[1][1]) // 2, 34, 13)
    gantry(bb, x1 + 34, SLIPS[0][0] - 3, SLIPS[0][1] + 2)
    gantry(bb, x1 + 50, SLIPS[0][0] - 3, SLIPS[0][1] + 2)
    gantry(bb, x1 + 34, SLIPS[1][0] - 3, SLIPS[1][1] + 2)
    gantry(bb, x1 + 50, SLIPS[1][0] - 3, SLIPS[1][1] + 2)
    # workshops: the saw shed and the rigging loft between and beside the slips, furnished
    for (a, b, c, d) in ((x1 + 2, 54, x1 + 20, 70), (x1 + 2, 98, x1 + 20, 116), (x1 + 26, 98, x1 + 46, 116)):
        bb.fill(a, 0, b, c, 0, d, "minecraft:spruce_planks")
        bb.walls(a, 1, b, c, 8, d, "minecraft:spruce_planks")
        for x in range(a, c + 1, 4):
            bb.fill(x, 1, b, x, 8, b, "minecraft:stripped_spruce_log[axis=y]")
            bb.fill(x, 1, d, x, 8, d, "minecraft:stripped_spruce_log[axis=y]")
        for x in range(a + 2, c - 1, 4):
            bb.fill(x, 3, b, x, 5, b, GLASS); bb.fill(x, 3, d, x, 5, d, GLASS)
        bb.fill(c, 1, (b + d) // 2 - 2, c, 6, (b + d) // 2 + 2, AIR)
        P.gable_roof(bb, a - 1, b - 1, c + 1, d + 1, 9, "minecraft:spruce_stairs", gable_fill="minecraft:spruce_planks",
                     overhang=0, ridge_axis="x")
        furnish(bb, [(a + 1, b + 1, c - 1, d - 1)], 1, 6, ["workshop"], seed_of("shed", a, b), tracker, audit=audit)
    # timber stacks, crates, barrels, anchors, cannons waiting to be fitted
    for i, (x, z) in enumerate(((x1 + 6, 22), (x1 + 12, 22), (x1 + 6, 26), (x1 + 26, 58), (x1 + 34, 58), (x1 + 42, 62))):
        bb.fill(x, 1, z, x + 5, 1 + i % 2, z + 2, "minecraft:stripped_spruce_log[axis=x]")
    for (x, z) in ((x1 + 4, 76), (x1 + 6, 78), (x1 + 4, 80), (x1 + 58, 56), (x1 + 60, 58)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up]")
    for (x, z) in ((x1 + 10, 84), (x1 + 14, 86), (x1 + 52, 66)):
        bb.set(x, 1, z, "onepiece:crate_stack[facing=east]")
    bb.set(x1 + 8, 1, 90, "onepiece:anchor[facing=east]")
    bb.set(x1 + 16, 1, 92, "onepiece:cannon[facing=east]")
    bb.set(x1 + 18, 1, 92, "onepiece:cannonball_pile[facing=east]")
    for z in range(z1 + 4, z2 - 3, 10):
        lamp_post(bb, x1 + 3, 1, z, h=4)
    return gz


def headquarters(bb, tracker, audit):
    """Galley-La Company HQ: a three-storey palazzo with a clock tower, Iceburg's office at the top."""
    x1, z1, x2, z2 = HQ
    bb.fill(x1 - 4, 0, z1 - 4, x2 + 4, 0, z2 + 4, "minecraft:polished_andesite")
    top = tier(bb, x1, z1, x2, z2, 0, 3, 6, [STUCCO, "minecraft:white_terracotta"], GLASS, STONE_ST, pilaster=STONE,
               band=STONE, weights=[0.8, 0.2], every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top - 1, STONE_ST)
    P.hip_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, TILES_ST, overhang=1)
    for k, y in enumerate((1, 7, 13)):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 5, "minecraft:white_concrete", seed_of("glhq", y), tracker,
                   [["living", "storage"], ["library", "living"], ["library", "bedroom"]][k], corridor="x", cw=3,
                   carpet=(None, "minecraft:red_carpet"), audit=audit, max_room=10)
    # ladders between floors at the west end of the corridor
    mz = (z1 + z2) // 2
    bb.fill(x1 + 1, 1, mz, x1 + 1, 13, mz, "minecraft:ladder[facing=east]")
    # front door on the west (towards the city), with a portico
    bb.fill(x1, 1, mz - 1, x1, 4, mz + 1, AIR)
    for zz, h in ((mz - 1, "left"), (mz, "right")):
        bb.set(x1, 1, zz, f"minecraft:spruce_door[facing=west,half=lower,hinge={h},open=false]")
        bb.set(x1, 2, zz, f"minecraft:spruce_door[facing=west,half=upper,hinge={h},open=false]")
    for zz in (mz - 4, mz + 4):
        bb.fill(x1 - 3, 1, zz, x1 - 3, 6, zz, "minecraft:smooth_quartz")
    bb.fill(x1 - 4, 7, mz - 5, x1, 7, mz + 5, STONE_SL + "[type=bottom]")
    # the clock tower over the middle
    tx1, tz1 = (x1 + x2) // 2 - 5, mz - 5
    tt = tier(bb, tx1, tz1, tx1 + 10, tz1 + 10, top, 3, 6, STUCCO, GLASS, STONE_ST, pilaster=STONE, every=3)
    cornice(bb, tx1, tz1, tx1 + 10, tz1 + 10, tt, STONE_ST, parapet=STONE_W)
    for (cx, cz, ax) in ((tx1 + 5, tz1 - 1, "x"), (tx1 - 1, tz1 + 5, "z")):
        for a in range(0, 360, 15):
            t = math.radians(a)
            u, v = round(3 * math.cos(t)), round(3 * math.sin(t))
            if ax == "x":
                bb.set(cx + u, tt - 5 + v, cz, "minecraft:gold_block")
            else:
                bb.set(cx, tt - 5 + v, cz + u, "minecraft:gold_block")
    P.hip_roof(bb, tx1 - 1, tz1 - 1, tx1 + 11, tz1 + 11, tt + 2, TILES_ST, overhang=0)
    # Iceburg's office on the top floor of the tower
    furnish(bb, [(tx1 + 1, tz1 + 1, tx1 + 9, tz1 + 9)], top + 1, 5, ["library"], seed_of("iceburg"), tracker,
            audit=audit)
    bb.set(tx1 + 5, top + 1, tz1 + 2, "onepiece:navigators_desk[facing=south]")
    bb.fill(tx1 + 2, top - 5, tz1 + 1, tx1 + 2, top + 12, tz1 + 1, "minecraft:ladder[facing=south]")
    bb.set(tx1 + 2, top, tz1 + 1, "minecraft:ladder[facing=south]")
    # garden and the yagara landing south of it
    for x in range(x1, x2 + 1, 8):
        bb.set(x, 1, z2 + 3, "minecraft:potted_azalea_bush")
    bb.fill(x1 - 4, -1, 172, LX, 0, 200, COBBLE[0])
    bb.fill(x1 + 10, -6, 186, LX, -1, 212, WATER)                      # the basin opens south into the sea
    bb.fill(x1 + 10, 0, 186, LX, 1, 212, AIR)
    bb.fill(LX, -7, 185, LX, 1, 200, STONE)
    bb.fill(x1 + 9, -7, 185, x1 + 9, 0, 200, STONE)
    for x in range(x1 + 14, LX - 6, 9):                                  # little pontoons with yagara boats
        bb.fill(x, 0, 190, x + 1, 0, 206, "minecraft:spruce_planks")
        bb.fill(x + 3, -1, 196, x + 6, -1, 200, "minecraft:oak_planks")
        bb.set(x + 4, 0, 197, "minecraft:oak_stairs[facing=south,half=bottom]")
        bb.set(x + 5, 0, 198, "minecraft:white_wool")
    return top


# ---------------------------------------------------------------- assembly
def design():
    bb = BigBuild(seed=77, y_min=-12, y_max=110)
    tracker = P.PropTracker(77)
    audit = []
    rng = np.random.default_rng(77)
    terrain(bb)
    grand_stairs(bb)
    gz = dock_one(bb, tracker, audit, rng)
    headquarters(bb, tracker, audit)
    rings_of_houses(bb, tracker, audit, rng)
    fountain(bb)
    # lamps along the canals, little trees in planters
    for (r1, r2, yy) in CANALS:
        for a in range(0, 360, 12):
            t = math.radians(a)
            x, z = round(CX + (r1 - 2) * math.cos(t)), round(CZ + (r1 - 2) * math.sin(t))
            if not in_dock(x, z, 2) and not axis_of(x, z, 4):
                lamp_post(bb, x, yy + 1, z, h=3)
    # gondola-style yagara boats moored in the canals
    for (r1, r2, yy) in CANALS:
        for a in range(20, 360, 55):
            t = math.radians(a)
            x, z = round(CX + (r1 + r2) / 2 * math.cos(t)), round(CZ + (r1 + r2) / 2 * math.sin(t))
            if in_dock(x, z, 4):
                continue
            bb.fill(x - 1, yy - 1, z, x + 1, yy - 1, z, "minecraft:oak_slab[type=top]")
            bb.set(x, yy, z, "minecraft:oak_stairs[facing=east,half=bottom]")
    return bb, audit, gz


def build():
    bb, audit, gz = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    x1 = DOCK[0]
    b.text(x1 - 3, 14, gz - 11, "DOCK 1", "minecraft:red_concrete", axis="z", step=1)    # ~23 wide, reads from the west
    hx1, hz1, hx2, hz2 = HQ
    b.chest(hx1 + 3, 1, hz1 + 3, "easy", "south")
    b.npc(210, 1, 96, "franky")
    b.flag((hx1 + hx2) // 2, 40, (hz1 + hz2) // 2, h=8, colors=("minecraft:white_wool", "minecraft:red_wool"), skull=False)
    return b, 0
