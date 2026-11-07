"""Alubarna, capital of Alabasta, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/alubarna_palace.md).

The royal palace on its sandstone mesa: walled grounds with domed corner towers and a gatehouse, gardens with pools
and palms, the palace with an arcaded front, four minarets and the great white dome over the throne room (Cobra's
throne, pillars, banners), royal apartments, library, kitchens and guard rooms on three floors, barracks and a guest
house in the side courts, and under it all the royal tomb with the Poneglyph, reached by a hidden stair behind the
throne. Below the mesa a grand stairway comes down to the city: the plaza with the clock tower (where Pell carried
the bomb), market stalls, and flat-roofed houses with striped awnings, all furnished. 224 x 224, plateau top y 24,
great dome ~84. Ground (city) = y 0. (v2, 2026-10-29)

v3 (2026-10-30, audit: "the city is identical box houses in a grid"): the city is replanned as an organic desert
town: nine winding sandstone streets wander out from the plaza, two wobbly ring streets cross them, and ~90 flat-roofed
houses of one to three storeys in three wall mixes are packed between them, doors to the nearest street, palms in the
gaps (mcb/organic_town.py)."""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     table, tier, cornice, stair_core, palm, onion_dome, set_if_air)
from mcb.bridge import to_canvas
from mcb.organic_town import organic_town

SID = "alubarna_palace"
TITLE = "Alubarna Palace (Alabasta)"
CUTS = [4, 12, 27]
TILER = dict(terrain="beard_thin")
EDGE_REACH = 2

SAND = "onepiece:alabasta_sandstone_bricks"
SAND_ST = "onepiece:alabasta_sandstone_brick_stairs"
SAND_SL = "onepiece:alabasta_sandstone_brick_slab"
SAND_W = "onepiece:alabasta_sandstone_brick_wall"
TILE = "onepiece:alabasta_tiles"
TILE_ST = "onepiece:alabasta_tile_stairs"
PILLAR = "onepiece:alubarna_pillar[axis=y]"
CUT = "minecraft:cut_sandstone"
SMOOTH = "minecraft:smooth_sandstone"
DOME = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
CLIFF = ["minecraft:sandstone", "minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:terracotta"]
GLASS = "minecraft:orange_stained_glass_pane"
WATER = "minecraft:water[level=0]"
WALLMIX = [SAND, SMOOTH, CUT]

N = 224
CX = 112
PLAT = 24
MESA = (14, 4, 210, 118)                 # x1, z1, x2, z2 of the plateau top
WALLS = (22, 10, 202, 112)               # palace grounds wall
PAL = (64, 22, 160, 78)                  # palace block
HALL = (96, 30, 128, 70)                 # throne room
TOMB = (98, 36, 126, 64, 6)              # x1, z1, x2, z2, floor y
PLAZA = (88, 148, 136, 188)
CLOCK = (112, 172)

TOWN = dict(walls=[SMOOTH, "minecraft:sandstone", CUT], frame=CUT, base=["minecraft:sandstone", CUT, SMOOTH],
            floor="minecraft:birch_planks", wood="jungle", chimney=SAND, parapet=SMOOTH)


def mesa_h(X, Z):
    """Plateau height: PLAT on top, eroded cliffs falling to 0 within ~8 blocks of its edge."""
    x1, z1, x2, z2 = MESA
    ex = np.maximum.reduce([x1 - X, X - x2, z1 - Z, Z - z2, np.zeros_like(X)])
    n = np.sin(X * 0.37) * 2 + np.cos(Z * 0.29) * 2 + np.sin((X + Z) * 0.11) * 1.5
    h = np.where(ex == 0, PLAT, PLAT - ex * (3.0 + n * 0.3) + n)
    return np.clip(np.floor(h), 0, PLAT)


# ---------------------------------------------------------------- ground, mesa, tomb
def ground(bb):
    bb.fill(0, -4, 0, N - 1, -1, N - 1, "minecraft:sandstone")
    bb.fill(0, 0, 0, N - 1, 0, N - 1, "minecraft:sand")
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    H = mesa_h(X, Z)
    for y in range(1, PLAT + 1):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda XX, yy, ZZ: H[XX, ZZ] >= yy, "minecraft:sandstone")
        bb.fill_where(0, y, 0, N - 1, y, N - 1,
                      lambda XX, yy, ZZ: (H[XX, ZZ] >= yy) & (np.sin(XX * 0.21 + yy * 0.9) > 0.55), "minecraft:smooth_sandstone")
        bb.fill_where(0, y, 0, N - 1, y, N - 1,
                      lambda XX, yy, ZZ: (H[XX, ZZ] >= yy) & ((yy % 6) == 0) & (np.cos(ZZ * 0.17 + XX * 0.05) > 0.2), "minecraft:terracotta")
    # palace grounds paving
    x1, z1, x2, z2 = WALLS
    bb.fill(x1, PLAT, z1, x2, PLAT, z2, "minecraft:smooth_sandstone")
    bb.fill_where(x1, PLAT, z1, x2, PLAT, z2, lambda XX, y, ZZ: (XX // 3 + ZZ // 3) % 2 == 0, CUT)
    # city paving: checker in the plaza, sandstone streets elsewhere
    bb.fill_where(0, 0, 120, N - 1, 0, N - 1, lambda XX, y, ZZ: (XX + ZZ) % 7 == 0, "minecraft:smooth_sandstone")
    px1, pz1, px2, pz2 = PLAZA
    bb.fill_where(px1, 0, pz1, px2, 0, pz2, lambda XX, y, ZZ: (XX // 3 + ZZ // 3) % 2 == 0, SMOOTH)
    bb.fill_where(px1, 0, pz1, px2, 0, pz2, lambda XX, y, ZZ: (XX // 3 + ZZ // 3) % 2 == 1, CUT)


def royal_tomb(bb, tracker):
    x1, z1, x2, z2, fy = TOMB
    bb.fill(x1 - 1, fy, z1 - 1, x2 + 1, fy + 12, z2 + 1, SAND)
    bb.fill(x1, fy + 1, z1, x2, fy + 11, z2, AIR)
    bb.fill(x1, fy, z1, x2, fy, z2, TILE)
    bb.fill(CX - 1, fy, z1 + 3, CX + 1, fy, z2, "minecraft:red_terracotta")
    for z in range(z1 + 3, z2, 5):
        for x in (x1 + 4, x2 - 4):
            bb.fill(x, fy + 1, z, x, fy + 10, z, PILLAR)
            bb.set(x + (1 if x < CX else -1), fy + 1, z, "minecraft:soul_lantern[hanging=false]")
    # sarcophagi of the Nefertari kings along the walls
    for z in range(z1 + 5, z2 - 2, 6):
        for x in (x1 + 1, x2 - 3):
            bb.fill(x, fy + 1, z, x + 2, fy + 1, z + 1, "minecraft:chiseled_sandstone")
            bb.fill(x, fy + 2, z, x + 2, fy + 2, z + 1, SAND_SL + "[type=bottom]")
            bb.set(x + 1, fy + 3, z, "minecraft:candle[candles=3,lit=true,waterlogged=false]")
    # the Poneglyph at the far end on a dais
    bb.fill(CX - 3, fy + 1, z1, CX + 3, fy + 1, z1 + 2, TILE)
    bb.fill(CX - 1, fy + 2, z1 + 1, CX + 1, fy + 4, z1 + 1, "onepiece:poneglyph")
    for x in (CX - 3, CX + 3):
        bb.set(x, fy + 2, z1 + 2, "minecraft:soul_lantern[hanging=false]")
    for x in range(x1 + 3, x2 - 2, 6):
        bb.set(x, fy + 11, (z1 + z2) // 2, "minecraft:soul_lantern[hanging=true]")


# ---------------------------------------------------------------- palace
def corner_tower(bb, cx, cz, base, h, r=5, dome_r=6):
    bb.cylinder(cx, base, cz, r, base + h, SAND)
    bb.cylinder(cx, base + 1, cz, r - 1, base + h - 1, AIR)
    for y in range(base + 6, base + h - 2, 6):
        bb.cylinder(cx, y, cz, r - 1, y, "minecraft:smooth_sandstone")
        for a in range(0, 360, 45):
            t = math.radians(a)
            bb.fill(round(cx + r * math.cos(t)), y + 2, round(cz + r * math.sin(t)),
                    round(cx + r * math.cos(t)), y + 3, round(cz + r * math.sin(t)), GLASS)
    bb.cylinder(cx, base + h - 3, cz, r + 1, base + h - 3, CUT)
    bb.cylinder(cx, base + h, cz, r + 1, base + h, CUT)
    bb.cylinder(cx, base + h, cz, r, base + h, TILE)
    for a in range(0, 360, 20):
        t = math.radians(a)
        bb.set(round(cx + (r + 1) * math.cos(t)), base + h + 1, round(cz + (r + 1) * math.sin(t)), SAND_W)
    bb.cylinder(cx, base + h + 1, cz, dome_r - 2, base + h + 3, SAND)
    onion_dome(bb, cx, base + h + 4, cz, dome_r, DOME)
    bb.fill(cx, base + 1, cz - r + 1, cx, base + h - 1, cz - r + 1, "minecraft:ladder[facing=south]")
    for y in range(base + 6, base + h - 2, 6):
        bb.set(cx, y, cz - r + 1, "minecraft:ladder[facing=south]")


def pointed_arcade(bb, x1, x2, z, y, h, every=4):
    """Pillars with pointed arches between them along x on plane z."""
    for x in range(x1, x2 + 1, every):
        bb.fill(x, y, z, x, y + h - 1, z, PILLAR)
    for x in range(x1, x2):
        k = (x - x1) % every
        if k == 0:
            continue
        drop = 1 if k in (1, every - 1) else 0
        bb.fill(x, y + h - 1 - drop, z, x, y + h, z, CUT)
    bb.fill(x1, y + h + 1, z, x2, y + h + 1, z, SAND)


def palace(bb, tracker, audit):
    x1, z1, x2, z2 = PAL
    base = PLAT
    top = tier(bb, x1, z1, x2, z2, base, 3, 7, WALLMIX, GLASS, SAND_ST, pilaster=PILLAR, band=CUT, every=3, pil_every=8,
               weights=[0.7, 0.2, 0.1], top_plate=TILE)
    cornice(bb, x1, z1, x2, z2, top, SAND_ST, parapet=SAND, merlons=SAND)
    # the throne room: two storeys tall under the great dome
    h1, hz1, h2, hz2 = HALL
    bb.fill(h1, base + 7, hz1, h2, base + 7, hz2, AIR)
    for x in (h1 - 1, h2 + 1):
        bb.fill(x, base + 1, hz1, x, base + 13, hz2, SAND)
        for z in range(hz1 + 6, hz2 - 3, 8):
            P.arched_opening(bb, "z", z, base + 1, x, 3, 5, depth=1)
            P.arched_opening(bb, "z", z, base + 8, x, 3, 4, depth=1)
    bb.fill(h1, base + 14, hz1, h2, base + 14, hz2, AIR)                    # open up into the dome
    for z in range(hz1 + 2, hz2 - 1, 5):
        for x in (h1 + 3, h2 - 3):
            bb.fill(x, base + 1, z, x, base + 14, z, PILLAR)
    bb.fill(CX - 2, base, hz1 + 4, CX + 2, base, hz2, "minecraft:red_terracotta")
    bb.fill(CX - 1, base + 1, hz1 + 6, CX + 1, base + 1, hz2, "minecraft:red_carpet")
    bb.fill(CX - 5, base + 1, hz1 + 1, CX + 5, base + 2, hz1 + 4, TILE)       # the dais
    bb.fill(CX - 3, base + 1, hz1 + 5, CX + 3, base + 1, hz1 + 5, st(TILE_ST, "north"))
    bb.set(CX, base + 3, hz1 + 2, "onepiece:throne[facing=south]")
    for x in (CX - 3, CX + 3):
        bb.set(x, base + 3, hz1 + 2, "onepiece:red_floor_cushion[facing=south]")
        bb.fill(x, base + 3, hz1 + 4, x, base + 4, hz1 + 4, "minecraft:jungle_fence")
        bb.set(x, base + 5, hz1 + 4, "minecraft:lantern[hanging=false]")
    for x in range(h1 + 2, h2 - 1, 4):                                        # banners of the royal house
        bb.fill(x, base + 6, hz1, x, base + 11, hz1, "minecraft:red_wool")
        bb.set(x, base + 10, hz1, "minecraft:yellow_wool")
    for z in range(hz1 + 8, hz2 - 2, 8):
        bb.set(CX, base + 13, z, "onepiece:chandelier[facing=north]")
    # the great dome on a drum
    dcx, dcz = CX, (hz1 + hz2) // 2
    bb.cylinder(dcx, top + 1, dcz, 15, top + 6, SAND)
    bb.cylinder(dcx, top + 1, dcz, 14, top + 6, AIR)
    for a in range(0, 360, 15):
        t = math.radians(a)
        bb.fill(round(dcx + 15 * math.cos(t)), top + 2, round(dcz + 15 * math.sin(t)),
                round(dcx + 15 * math.cos(t)), top + 4, round(dcz + 15 * math.sin(t)), GLASS)
    bb.cylinder(dcx, top + 6, dcz, 16, top + 6, CUT)
    bb.cylinder(dcx, top, dcz, 14, top, AIR)
    bb.dome(dcx, top + 7, dcz, 15, DOME, hollow=True)
    bb.fill_where(dcx - 16, top + 7, dcz - 16, dcx + 16, top + 22, dcz + 16,
                  lambda X, y, Z: (np.abs(np.hypot(np.hypot(X - dcx, Z - dcz), y - top - 7) - 15) < 0.8) & ((y - top) % 5 == 0),
                  "minecraft:yellow_concrete")
    onion_dome(bb, dcx, top + 22, dcz, 3, DOME)
    bb.fill(h1, top, hz1, h2, top, hz2, AIR)
    bb.fill_where(h1, top, hz1, h2, top, hz2, lambda X, y, Z: np.hypot(X - dcx, Z - dcz) > 14.5, TILE)
    # wings: three floors of rooms
    for (a, b) in ((x1 + 1, h1 - 2), (h2 + 2, x2 - 1)):
        for k in range(3):
            y = base + 7 * k + 1
            kinds = [["kitchen", "storage", "living"], ["bedroom", "living", "library"], ["bedroom", "library"]][k]
            wing_floor(bb, a, z1 + 1, b, z2 - 1, y, 6, "minecraft:smooth_sandstone", seed_of("alu", a, k), tracker,
                       kinds, corridor="z", cw=3, carpet=(None, "minecraft:red_carpet"), audit=audit, max_room=10,
                       wood="jungle")
        bb.fill(a + 1, base + 1, z1 + 1, a + 1, base + 14, z1 + 1, "minecraft:ladder[facing=south]")
    # the arcaded front gallery and the main doors
    pointed_arcade(bb, x1, x2, z2 + 4, base + 1, 9)
    bb.fill(x1, base + 11, z2 + 1, x2, base + 11, z2 + 4, TILE)
    bb.fill(x1, base + 12, z2 + 4, x2, base + 12, z2 + 4, SAND_W)
    bb.fill(CX - 3, base + 1, z2, CX + 3, base + 6, z2, AIR)
    P.arched_opening(bb, "x", CX, base + 1, z2, 7, 7, depth=1, trim=GOLD)
    # four minarets at the corners
    for (mx, mz) in ((x1 - 2, z1 - 2), (x2 + 2, z1 - 2), (x1 - 2, z2 + 2), (x2 + 2, z2 + 2)):
        corner_tower(bb, mx, mz, base, 40, r=4, dome_r=5)
    # small domes on the wing roofs, on drums with windows
    for dx in (x1 + 15, x2 - 15):
        for dz in (z1 + 14, z2 - 14):
            bb.cylinder(dx, top + 1, dz, 5, top + 5, SAND)
            for a in range(0, 360, 45):
                t = math.radians(a)
                bb.fill(round(dx + 5 * math.cos(t)), top + 2, round(dz + 5 * math.sin(t)),
                        round(dx + 5 * math.cos(t)), top + 3, round(dz + 5 * math.sin(t)), GLASS)
            bb.cylinder(dx, top + 5, dz, 6, top + 5, CUT)
            onion_dome(bb, dx, top + 6, dz, 6, DOME)
    # the hidden stair behind the throne down to the tomb
    stair_core(bb, h2 - 6, hz1 + 1, 5, TOMB[4] + 1, base, [base + 1], SAND, SAND_ST)
    return top


def grounds(bb, tracker, audit, rng):
    x1, z1, x2, z2 = WALLS
    base = PLAT
    # the wall: 3 thick, crenellated, walkway on top
    for (a, b, c, d) in ((x1, z1, x2, z1 + 2), (x1, z2 - 2, x2, z2), (x1, z1, x1 + 2, z2), (x2 - 2, z1, x2, z2)):
        bb.fill(a, base + 1, b, c, base + 10, d, SAND)
        bb.fill(a, base + 10, b, c, base + 10, d, TILE)
    for x in range(x1, x2 + 1, 2):
        bb.set(x, base + 11, z1, SAND); bb.set(x, base + 11, z2, SAND)
    for z in range(z1, z2 + 1, 2):
        bb.set(x1, base + 11, z, SAND); bb.set(x2, base + 11, z, SAND)
    for (cx, cz) in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1)):
        corner_tower(bb, cx, cz, base, 26, r=6, dome_r=7)
    # the gatehouse on the south wall
    bb.fill(CX - 12, base + 1, z2 - 4, CX + 12, base + 18, z2 + 2, SAND)
    P.arched_opening(bb, "x", CX, base + 1, z2 - 4, 9, 12, depth=7, trim=CUT)
    cornice(bb, CX - 12, z2 - 4, CX + 12, z2 + 2, base + 18, SAND_ST, parapet=SAND, merlons=SAND)
    for gx in (CX - 13, CX + 13):
        corner_tower(bb, gx, z2 - 1, base, 30, r=4, dome_r=5)
    for x in (CX - 9, CX + 9):
        bb.fill(x, base + 6, z2 + 3, x, base + 15, z2 + 3, "minecraft:red_wool")
        bb.set(x, base + 12, z2 + 3, "minecraft:yellow_wool")
    # gardens: two pools with fountains, palms, flower beds, paths from the gate to the palace
    bb.fill(CX - 3, base, PAL[3] + 5, CX + 3, base, z2 - 4, "minecraft:red_terracotta")
    for px in (CX - 40, CX + 40):
        pz = 96
        bb.fill(px - 14, base, pz - 7, px + 14, base, pz + 7, CUT)
        bb.fill(px - 13, base - 2, pz - 6, px + 13, base, pz + 6, WATER)
        bb.fill(px - 13, base - 3, pz - 6, px + 13, base - 3, pz + 6, "minecraft:prismarine")
        bb.fill(px, base - 2, pz, px, base + 3, pz, CUT)
        bb.set(px, base + 4, pz, "minecraft:light_blue_stained_glass")
        for (dx, dz) in ((-16, -9), (16, -9), (-16, 9), (16, 9), (0, -9), (0, 9)):
            palm(bb, px + dx, base + 1, pz + dz, 9 + int(rng.integers(0, 4)), ((1 if dx < 0 else -1), 0))
    for (fx, fz1, fx2, fz2) in ((x1 + 6, 84, x1 + 30, 106), (x2 - 30, 84, x2 - 6, 106)):
        bb.fill(fx, base, fz1, fx2, base, fz2, "minecraft:grass_block[snowy=false]")
        bb.fill_where(fx, base + 1, fz1, fx2, base + 1, fz2,
                      lambda X, y, Z: ((X + Z) % 3 == 0), "minecraft:orange_tulip")
        bb.fill_where(fx, base + 1, fz1, fx2, base + 1, fz2,
                      lambda X, y, Z: ((X * 2 + Z) % 5 == 0), "minecraft:dandelion")
    # side courts: barracks (west) and the royal guest house (east), flat roofs, furnished
    for (a, b, kinds) in ((x1 + 6, x1 + 36, ["bedroom", "storage"]), (x2 - 36, x2 - 6, ["living", "bedroom", "library"])):
        tt = tier(bb, a, z1 + 8, b, z1 + 60, base, 2, 6, WALLMIX, GLASS, SAND_ST, band=CUT, weights=[0.7, 0.2, 0.1],
                  top_plate=TILE)
        cornice(bb, a, z1 + 8, b, z1 + 60, tt, SAND_ST, parapet=SAND, merlons=SAND)
        for k in range(2):
            wing_floor(bb, a + 1, z1 + 9, b - 1, z1 + 59, base + 6 * k + 1, 5, "minecraft:smooth_sandstone",
                       seed_of("side", a, k), tracker, kinds, corridor="z", cw=3, audit=audit, max_room=10, wood="jungle")
        bb.fill(a + 1, base + 1, z1 + 9, a + 1, base + 7, z1 + 9, "minecraft:ladder[facing=south]")
        dx = (a + b) // 2
        bb.fill(dx, base + 1, z1 + 60, dx + 1, base + 3, z1 + 60, AIR)


def grand_stair(bb):
    z2 = WALLS[3]
    zt = z2 + 3                      # top of the flight, outside the gatehouse
    for i in range(PLAT):
        y = PLAT - i
        z = zt + i
        bb.fill(CX - 8, y, z, CX + 8, y, z, st(SAND_ST, "north"))
        bb.fill(CX - 8, 0, z, CX + 8, y - 1, z, SAND)
        bb.fill(CX - 8, y + 1, z, CX + 8, y + 5, z, AIR)
        for x in (CX - 9, CX + 9):
            bb.fill(x, 0, z, x, y + 1, z, SAND)
            bb.set(x, y + 2, z, SAND_W)
            if i % 6 == 0:
                bb.set(x, y + 3, z, "minecraft:lantern[hanging=false]")
    bb.fill(CX - 8, PLAT, z2 + 3, CX + 8, PLAT, z2 + 3, TILE)
    return zt + PLAT


def clock_tower(bb, tracker):
    cx, cz = CLOCK
    x1, z1, x2, z2 = cx - 5, cz - 5, cx + 5, cz + 5
    bb.fill(x1 - 3, 0, z1 - 3, x2 + 3, 1, z2 + 3, CUT)
    top = tier(bb, x1, z1, x2, z2, 1, 6, 6, [SAND, SMOOTH], GLASS, SAND_ST, pilaster=PILLAR, every=5, pil_every=5)
    cornice(bb, x1, z1, x2, z2, top, SAND_ST)
    # the clock faces (gold rings, black hands) and the open bell room above
    for (fx, fz, ax) in ((cx, z2 + 1, "x"), (cx, z1 - 1, "x"), (x1 - 1, cz, "z"), (x2 + 1, cz, "z")):
        for a in range(0, 360, 12):
            t = math.radians(a)
            u, v = round(4 * math.cos(t)), round(4 * math.sin(t))
            if ax == "x":
                bb.set(fx + u, top - 5 + v, fz, GOLD)
            else:
                bb.set(fx, top - 5 + v, fz + u, GOLD)
        if ax == "x":
            bb.fill(fx, top - 5, fz, fx, top - 2, fz, "minecraft:black_concrete")
            bb.fill(fx, top - 5, fz, fx + 2, top - 5, fz, "minecraft:black_concrete")
        else:
            bb.fill(fx, top - 5, fz, fx, top - 2, fz, "minecraft:black_concrete")
            bb.fill(fx, top - 5, fz, fx, top - 5, fz + 2, "minecraft:black_concrete")
    bb.fill(x1, top + 1, z1, x2, top + 8, z2, SAND)
    bb.fill(x1 + 1, top + 1, z1 + 1, x2 - 1, top + 7, z2 - 1, AIR)
    bb.fill(cx - 2, top + 2, z1, cx + 2, top + 6, z2, AIR)
    bb.fill(x1, top + 2, cz - 2, x2, top + 6, cz + 2, AIR)
    bb.fill(cx, top + 6, cz, cx, top + 7, cz, "minecraft:iron_chain[axis=y,waterlogged=false]")
    bb.set(cx, top + 5, cz, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    bb.fill(x1, top + 8, z1, x2, top + 8, z2, TILE)
    onion_dome(bb, cx, top + 9, cz, 5, DOME)
    P.square_spiral_stair(bb, x1 + 1, 2, z1 + 1, 9, top + 1, SAND_ST, core=SAND)
    bb.fill(cx, 2, z2, cx, 4, z2, AIR)
    bb.set(cx, 2, z2, "minecraft:jungle_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(cx, 3, z2, "minecraft:jungle_door[facing=south,half=upper,hinge=left,open=false]")


def market(bb, rng):
    colors = ["red", "orange", "yellow", "light_blue", "white", "lime"]
    px1, pz1, px2, pz2 = PLAZA
    spots = [(x, pz1 + 4) for x in range(px1 + 4, px2 - 4, 9) if abs(x - CX) > 12] + \
            [(x, pz2 - 4) for x in range(px1 + 4, px2 - 4, 9) if abs(x - CX) > 8]
    for i, (x, z) in enumerate(spots):
        c = colors[i % len(colors)]
        for (dx, dz) in ((-2, -1), (2, -1), (-2, 1), (2, 1)):
            bb.fill(x + dx, 1, z + dz, x + dx, 3, z + dz, "minecraft:jungle_fence")
        for dx in range(-2, 3):
            for dz in range(-1, 2):
                bb.set(x + dx, 4, z + dz, f"minecraft:{c if (dx + 2) % 2 == 0 else 'white'}_wool")
        bb.fill(x - 1, 1, z, x + 1, 1, z, "minecraft:jungle_planks")
        goods = ["minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up]",
                 "onepiece:crate_stack[facing=south]", "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]"]
        bb.set(x - 1, 2, z, goods[int(rng.integers(len(goods)))])
        bb.set(x + 1, 2, z, goods[int(rng.integers(len(goods)))])


def town(bb, tracker, audit, rng, stair_end):
    """v3: an organic desert city round the market plaza, winding sandstone streets wandering out from it (and up to
    the grand stair), flat-roofed houses of one to three storeys packed between them, palms in the gaps."""
    colors = ["red", "orange", "yellow", "light_blue", "white", "lime", "cyan"]
    reserved = [(PLAZA[0] - 2, PLAZA[1] - 2, PLAZA[2] + 2, PLAZA[3] + 2), (CX - 11, 112, CX + 11, stair_end + 2)]

    def ok(x, z):
        if not (3 <= x <= N - 4 and 120 <= z <= N - 4):
            return False
        if mesa_h(np.array([x]), np.array([z]))[0] > 0:
            return False
        return not any(r[0] <= x <= r[2] and r[1] <= z <= r[3] for r in reserved)
    pals = [TOWN, dict(TOWN, walls=["minecraft:sandstone", SMOOTH, "minecraft:terracotta"]),
            dict(TOWN, walls=[CUT, "minecraft:white_terracotta", SMOOTH])]
    roofs = ["flat:" + c for c in colors]
    cx, cz = (PLAZA[0] + PLAZA[2]) // 2, (PLAZA[1] + PLAZA[3]) // 2
    S, placed = organic_town(bb, (3, 120, N - 4, N - 4), (cx, cz), ok, seed_of("alu_town"), tracker, pals, roofs,
                             ["minecraft:white_terracotta", "minecraft:smooth_sandstone", "minecraft:white_terracotta", CUT],
                             90, spokes=9, rings=((50, 2.2), (78, 2.0)), sizes=(7, 11), floors=(1, 3),
                             kinds=("kitchen", "bedroom", "living", "storeroom"), plinth="minecraft:sandstone",
                             timber=False, reserved=reserved)
    print("alubarna houses:", len(placed))
    taken = [(x - 1, z - 1, x + w, z + d) for (x, z, w, d, y, rot) in placed] + reserved
    for _ in range(90):                              # palms in the gaps
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(122, N - 4))
        if any(r[0] - 2 <= x <= r[2] + 2 and r[1] - 2 <= z <= r[3] + 2 for r in taken):
            continue
        if (bb.get_region(x - 3, 1, z - 3, x + 3, 12, z + 3) > 1).any() or S[x - 3, z - 120]:
            continue
        palm(bb, x, 1, z, 8 + int(rng.integers(0, 5)), (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))))
        taken.append((x - 3, z - 3, x + 3, z + 3))


# ---------------------------------------------------------------- assembly
def design():
    bb = BigBuild(seed=131, y_min=-6, y_max=110)
    tracker = P.PropTracker(131)
    audit = []
    rng = np.random.default_rng(131)
    ground(bb)
    royal_tomb(bb, tracker)
    grounds(bb, tracker, audit, rng)
    top = palace(bb, tracker, audit)
    end = grand_stair(bb)
    clock_tower(bb, tracker)
    market(bb, rng)
    town(bb, tracker, audit, rng, end)
    for x in range(PLAZA[0], PLAZA[2] + 1, 12):
        lamp_post(bb, x, 1, PLAZA[1] - 3, post="minecraft:jungle_fence", h=4)
    return bb, audit, top


def build():
    bb, audit, top = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    h1, hz1, h2, hz2 = HALL
    b.chest(CX + 4, PLAT + 1, hz1 + 7, "treasure", "west")
    b.guards("baroque_agent", ((CX - 6, 108), (CX + 6, 108), (CX - 4, 84), (CX + 4, 84)), y=PLAT + 1)
    b.guards("baroque_agent", ((CX - 14, 150), (CX + 14, 190)), y=1)
    return b, 0
