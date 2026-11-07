"""Dressrosa Royal Palace on the King's Plateau, under Doflamingo's Birdcage, redesigned with the Minecraft Builder
skill (dossier: mcb/dossiers/dressrosa_palace.md).

The King's Plateau, a sheer banded rock mesa with buttresses and ivy, rises out of the flower town; a grand quartz
stair climbs its south face to a garden courtyard with a fountain; on top the pink-and-white palace: three furnished
floors (the throne hall, the banquet hall, the royal rooms, Doflamingo's pink suite), four round corner towers and the
tall central keep with cone roofs, flying the Donquixote Jolly Roger. All round, the flower town: pastel stucco houses
with tiled roofs on mosaic streets, cafe awnings, sunflower beds and fountains, and over everything Doflamingo's
Birdcage of strings. ~172 x 172, keep ~104, cage ~140. Ground = y 0. (v2)

v3 (2026-10-30, audit: "the town is a grid of identical houses"): the flower town is replanned: eight winding mosaic
streets wander out from the plateau, a wobbly ring street loops round it, and ~70 pastel houses (four wall mixes,
tile, spruce and nether-brick roofs, two to three storeys) are packed between them with doors to the nearest street,
cafe awnings, flower beds, fountains and lamps in the gaps (mcb/organic_town.py)."""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     tier, cornice, stair_core, set_if_air, table)
from mcb.bridge import to_canvas
from mcb.organic_town import organic_town

SID = "dressrosa_palace"
TITLE = "Dressrosa Royal Palace"
CUTS = [34, 42, 50]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 172
CX, CZ = 86, 78
STUCCO = "onepiece:dressrosa_stucco"
TILE = "onepiece:dressrosa_tiles"
TILE_ST = "onepiece:dressrosa_tile_stairs"
MOSAIC = "onepiece:dressrosa_mosaic"
PINK = "minecraft:pink_terracotta"
WHITE = "minecraft:white_terracotta"
QUARTZ_ST = "minecraft:quartz_stairs"
PLAT = 32
PLATEAU = (48, 40, 124, 112)
PAL = (58, 48, 114, 88)
FH = 8
KEEP = (CX, 56)
DRESS = dict(walls=[STUCCO, "minecraft:white_concrete", "minecraft:yellow_terracotta"], frame="minecraft:smooth_sandstone",
             base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"],
             floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks", parapet=STUCCO)
DRESS2 = dict(DRESS, walls=[PINK, STUCCO, "minecraft:white_terracotta"])


STREETS = None                           # bool [x, z] over the site, filled by town()


def street(x, z):
    return STREETS is not None and 0 <= x < N and 0 <= z < N and bool(STREETS[x, z])


def town_ground(bb, rng):
    bb.fill(0, -4, 0, N - 1, -1, N - 1, "minecraft:dirt")
    bb.fill(0, 0, 0, N - 1, 0, N - 1, "minecraft:grass_block")


def plateau(bb, rng):
    x1, z1, x2, z2 = PLATEAU

    def noise(X, Z):
        return 1.6 * np.sin(X * 0.31) * np.cos(Z * 0.27) + 1.2 * np.sin((X + Z) * 0.13)

    for y in range(0, PLAT + 1):
        grow = max(0, 3 - y // 4)                       # buttresses spread toward the foot
        def inside(X, yy, Z, grow=grow, y=y):
            d = np.minimum(np.minimum(X - x1, x2 - X), np.minimum(Z - z1, z2 - Z))
            return d >= -grow - np.clip(noise(X, Z) + 0.5 * np.sin(y * 0.7 + X * 0.2), -1, 2)
        band = ["minecraft:stone", "minecraft:stone", "minecraft:andesite", "minecraft:stone", "minecraft:tuff",
                "minecraft:stone", "minecraft:andesite"][(y // 3) % 7]
        bb.fill_where(x1 - 8, y, z1 - 8, x2 + 8, y, z2 + 8, inside, band)
    bb.fill(x1, PLAT, z1, x2, PLAT, z2, "minecraft:grass_block")
    # ivy and azalea spilling over the rim
    for x in range(x1, x2 + 1, 2):
        for z in (z1 - 1, z2 + 1):
            for k in range(1, int(rng.integers(3, 10))):
                set_if_air(bb, x, PLAT - k, z, "minecraft:vine[north=%s,south=%s,east=false,west=false,up=false]" % (
                    "true" if z == z2 + 1 else "false", "true" if z == z1 - 1 else "false"))
    for z in range(z1, z2 + 1, 3):
        for x in (x1, x2):
            set_if_air(bb, x, PLAT + 1, z, "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    # the grand stair up the south face, quartz parapets, lamps
    for i in range(PLAT):
        z = z2 + PLAT - i
        bb.fill(CX - 6, 1, z, CX + 6, i, z, "minecraft:smooth_quartz")
        bb.fill(CX - 6, i + 1, z, CX + 6, i + 1, z, st(QUARTZ_ST, "north"))
        bb.fill(CX - 6, i + 2, z, CX + 6, i + 5, z, AIR)
        for x in (CX - 7, CX + 7):
            bb.fill(x, 1, z, x, i + 2, z, "minecraft:quartz_bricks")
            if i % 6 == 0:
                bb.set(x, i + 3, z, "minecraft:lantern[hanging=false]")


def courtyard(bb):
    x1, z1, x2, z2 = PLATEAU
    gz1, gz2 = PAL[3] + 2, z2 - 1
    for x in range(x1 + 2, x2 - 1):
        for z in range(gz1, gz2 + 1):
            if abs(x - CX) <= 3 or (z - gz1) % 9 == 0:
                bb.set(x, PLAT, z, "minecraft:smooth_quartz" if (x + z) % 2 else MOSAIC)
            elif (x + z) % 5 == 0:
                bb.set(x, PLAT + 1, z, ["minecraft:poppy", "minecraft:allium", "minecraft:pink_tulip",
                                        "minecraft:oxeye_daisy", "minecraft:cornflower"][(x * 7 + z) % 5])
    for x in range(x1 + 3, x2 - 2):
        for z in (gz1 + 1, gz2 - 1):
            if abs(x - CX) > 4 and (x % 12) not in (0, 1):
                bb.set(x, PLAT + 1, z, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")
    fz = (gz1 + gz2) // 2
    bb.cylinder(CX, PLAT + 1, fz, 5, PLAT + 1, "minecraft:quartz_bricks")
    bb.cylinder(CX, PLAT + 1, fz, 4, PLAT + 1, "minecraft:water[level=0]")
    bb.fill(CX, PLAT + 1, fz, CX, PLAT + 4, fz, "minecraft:quartz_pillar[axis=y]")
    bb.cylinder(CX, PLAT + 4, fz, 2, PLAT + 4, "minecraft:quartz_slab[type=bottom]")
    bb.set(CX, PLAT + 5, fz, "minecraft:sea_lantern")
    for x in (CX - 9, CX + 9):
        for z in range(gz1 + 2, gz2, 6):
            lamp_post(bb, x, PLAT + 1, z, post="minecraft:quartz_pillar[axis=y]")


def palace(bb, tracker, audit):
    x1, z1, x2, z2 = PAL
    y0 = PLAT
    top = tier(bb, x1, z1, x2, z2, y0, 3, FH, [STUCCO, PINK], "minecraft:glass_pane", "minecraft:smooth_quartz_stairs",
               pilaster=WHITE, band=WHITE, plate="minecraft:dark_oak_planks", top_plate=WHITE, weights=[0.8, 0.2],
               every=3, pil_every=4, win_h=4)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:smooth_quartz_stairs", parapet=WHITE, merlons=PINK)
    core = (x2 - 8, z1 + 3)
    stair_core(bb, core[0], core[1], 5, y0 + 1, top, [y0 + FH * k for k in range(4)], STUCCO, "minecraft:dark_oak_stairs")
    keep_box = [(core[0] - 1, core[1] - 1, core[0] + 5, core[1] + 5)]
    hx1, hx2 = CX - 13, CX + 13
    # ground floor: the throne hall through the middle (two storeys), wings either side
    y = y0 + 1
    for (a, b_, nm, kinds) in ((x1 + 1, hx1 - 2, "w", ["living", "library"]), (hx2 + 2, x2 - 1, "e", ["kitchen", "storage"])):
        wing_floor(bb, a, z1 + 1, b_, z2 - 1, y, FH - 1, STUCCO, seed_of("dr1", nm), tracker, kinds, corridor="z",
                   cw=3, audit=audit, max_room=11, wood="dark_oak", keep=keep_box, carpet=(None, "minecraft:red_carpet"))
    bb.fill(hx1, y, z1 + 1, hx2, y0 + 2 * FH - 1, z2 - 1, AIR)
    for x in (hx1 - 1, hx2 + 1):
        bb.fill(x, y, z1 + 1, x, y0 + 2 * FH - 1, z2 - 1, STUCCO)
        bb.fill(x, y, CZ - 3, x, y + 2, CZ - 1, AIR)
    bb.fill(hx1, y0, z1 + 1, hx2, y0, z2 - 1, "minecraft:polished_diorite")
    bb.fill(CX - 2, y0, z1 + 4, CX + 2, y0, z2 - 1, "minecraft:red_wool")
    for x in range(hx1 + 2, hx2 - 1, 5):
        for z in (z1 + 3, z2 - 3):
            bb.fill(x, y, z, x, y0 + 2 * FH - 1, z, "minecraft:quartz_pillar[axis=y]")
        bb.set(x, y0 + 2 * FH - 2, CZ - 2, "onepiece:chandelier[facing=north]")
    # the throne on a dais at the north end
    bb.fill(CX - 4, y, z1 + 1, CX + 4, y, z1 + 4, "minecraft:quartz_bricks")
    bb.fill(CX - 1, y + 1, z1 + 1, CX + 1, y + 1, z1 + 2, "minecraft:gold_block")
    bb.set(CX, y + 2, z1 + 2, "minecraft:red_nether_brick_stairs[facing=south,half=bottom]")
    bb.fill(CX - 1, y + 2, z1 + 1, CX + 1, y + 6, z1 + 1, "minecraft:red_wool")
    bb.set(CX, y + 7, z1 + 1, "minecraft:gold_block")
    for x in (CX - 6, CX + 6):
        bb.fill(x, y, z1 + 1, x, y + 8, z1 + 1, "minecraft:pink_wool")
    # front door onto the courtyard
    bb.fill(CX - 2, y, z2, CX + 2, y + 4, z2, AIR)
    P.arched_opening(bb, "x", CX, y, z2, 5, 6, depth=1, trim=WHITE)
    # second floor (the wings over the side rooms) and third floor
    y = y0 + FH + 1
    for (a, b_, nm, kinds) in ((x1 + 1, hx1 - 2, "w2", ["bedroom", "library"]), (hx2 + 2, x2 - 1, "e2", ["living", "bedroom"])):
        wing_floor(bb, a, z1 + 1, b_, z2 - 1, y, FH - 1, STUCCO, seed_of("dr2", nm), tracker, kinds, corridor="z",
                   cw=3, audit=audit, max_room=11, wood="dark_oak", keep=keep_box)
    y = y0 + 2 * FH + 1
    wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, FH - 1, STUCCO, seed_of("dr3"), tracker,
               ["bedroom", "living", "library", "bedroom"], corridor="x", cw=4, audit=audit, max_room=12,
               wood="dark_oak", keep=keep_box, carpet=(None, "minecraft:pink_carpet"))
    # Doflamingo's suite: the west end of the top floor goes pink, with a feather-coat stand and his chair
    sx = x1 + 2
    bb.fill(sx, y - 1, z1 + 2, sx + 10, y - 1, z1 + 14, "minecraft:pink_wool")
    bb.fill(sx + 2, y, z1 + 4, sx + 3, y, z1 + 5, "minecraft:pink_wool")
    bb.set(sx + 2, y + 1, z1 + 4, "minecraft:magenta_wool")
    bb.set(sx + 6, y, z1 + 3, "minecraft:pink_bed[facing=south,part=head,occupied=false]")
    bb.set(sx + 6, y, z1 + 4, "minecraft:pink_bed[facing=south,part=foot,occupied=false]")
    # roof
    P.hip_roof(bb, x1 + 2, z1 + 2, x2 - 2, z2 - 2, top + 1, TILE_ST, overhang=0)
    # corner towers
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(tx, y0, tz, 6, top + 12, WHITE)
        bb.cylinder(tx, y0 + 1, tz, 5, top + 11, AIR)
        for fy in [y0 + FH * k for k in range(1, 4)]:
            bb.cylinder(tx, fy, tz, 5, fy, "minecraft:dark_oak_planks")
        lz = tz + 4 if tz == z1 else tz - 4
        bb.fill(tx, y0 + 1, lz, tx, top + 4, lz, "minecraft:ladder[facing=%s]" % ("north" if tz == z1 else "south"))
        for fy in [y0 + FH * k for k in range(1, 4)]:
            bb.set(tx, fy, lz, "minecraft:ladder[facing=%s]" % ("north" if tz == z1 else "south"))
        dx = 1 if tx == x1 else -1
        dz = 1 if tz == z1 else -1
        for fy in [y0 + 1 + FH * k for k in range(3)]:
            bb.fill(tx + dx * 5, fy, tz + dz * 5, tx + dx * 6, fy + 1, tz + dz * 6, AIR)
        for yy in range(y0 + 4, top + 10, 5):
            for (ox, oz) in ((6, 0), (-6, 0), (0, 6), (0, -6)):
                bb.fill(tx + ox, yy, tz + oz, tx + ox, yy + 1, tz + oz, "minecraft:glass_pane")
        bb.cylinder(tx, top + 12, tz, 7, top + 12, PINK)
        for a in range(0, 360, 15):
            t = math.radians(a)
            bb.set(round(tx + 7 * math.cos(t)), top + 13, round(tz + 7 * math.sin(t)), PINK)
        P.cone_roof(bb, tx, top + 13, tz, 7, 18, TILE, hollow=False)
        bb.set(tx, top + 31, tz, "minecraft:gold_block")
    # the central keep
    kx, kz = KEEP
    bb.cylinder(kx, top, kz, 8, top + 30, WHITE)
    bb.cylinder(kx, top + 1, kz, 7, top + 29, AIR)
    for fy in (top + 10, top + 20):
        bb.cylinder(kx, fy, kz, 7, fy, "minecraft:dark_oak_planks")
    P.square_spiral_stair(bb, kx - 3, top + 1, kz - 3, 7, top + 20, "minecraft:dark_oak_stairs", core=WHITE)
    for yy in range(top + 4, top + 28, 5):
        for (ox, oz) in ((8, 0), (-8, 0), (0, 8), (0, -8)):
            bb.fill(kx + ox, yy, kz + oz, kx + ox, yy + 2, kz + oz, "minecraft:glass_pane")
    bb.cylinder(kx, top + 30, kz, 9, top + 30, PINK)
    for a in range(0, 360, 12):
        t = math.radians(a)
        bb.set(round(kx + 9 * math.cos(t)), top + 31, round(kz + 9 * math.sin(t)), PINK)
    P.cone_roof(bb, kx, top + 31, kz, 9, 24, TILE, hollow=False)
    tip = top + 55
    bb.fill(kx, tip, kz, kx, tip + 14, kz, "minecraft:dark_oak_fence")
    FW, FHt = 13, 11
    for c in range(FW):
        for r in range(FHt):
            dx, dy = c - 6, r - 5
            ring = 4.5 <= math.hypot(dx, dy) <= 5.5
            eye = c in (4, 8) and r in (3, 4)
            smile = (r == 6 and c in (3, 9)) or (r == 7 and 4 <= c <= 8)
            slash = r == round(c * (FHt - 1) / (FW - 1))
            fg = ring or eye or smile or slash
            bb.set(kx + 1 + c, tip + 13 - r, kz, "minecraft:black_wool" if fg else "minecraft:pink_wool")
    # a hatch from the top floor into the keep
    bb.fill(kx + 4, top - FH + 1, kz, kx + 4, top + 1, kz, "minecraft:ladder[facing=west]")
    return top


def town(bb, rng, tracker, audit):
    x1, z1, x2, z2 = PLATEAU
    stair = (CX - 8, z2, CX + 8, z2 + PLAT + 2)
    roofs = [TILE_ST, TILE_ST, "minecraft:spruce_stairs", "minecraft:red_nether_brick_stairs"]
    taken = []

    def free(a, b, w, d):
        if a < 1 or b < 1 or a + w > N - 2 or b + d > N - 2:
            return False
        for (p, q, r, s) in [(x1 - 9, z1 - 9, x2 + 9, z2 + 9), stair] + taken:
            if a - 1 <= r and p <= a + w and b - 1 <= s and q <= b + d:
                return False
        X = np.arange(a - 1, a + w + 1)[:, None]
        Z = np.arange(b - 1, b + d + 1)[None, :]
        return not ((X % 24 <= 2) | (Z % 24 <= 2) | (np.abs(X - CX) <= 4)).any()

    global STREETS
    reserved = [(x1 - 9, z1 - 9, x2 + 9, z2 + 9), stair]
    ok = lambda x, z: 1 <= x < N - 2 and 1 <= z < N - 2 and not any(p <= x <= r and q <= z <= t for (p, q, r, t) in reserved)
    pals = [DRESS, DRESS2, dict(DRESS, walls=["minecraft:white_terracotta", STUCCO, "minecraft:light_blue_terracotta"]),
            dict(DRESS, walls=["minecraft:yellow_terracotta", STUCCO, "minecraft:white_concrete"])]
    roofs = [TILE_ST, TILE_ST, "minecraft:spruce_stairs", "minecraft:red_nether_brick_stairs", "flat:orange"]
    S, placed = organic_town(bb, (0, 0, N - 1, N - 1), (CX, CZ), ok, seed_of("dress_town"), tracker, pals, roofs,
                             [MOSAIC, MOSAIC, TILE], 80, spokes=8, rings=((64, 1.8),), width=1.8, sizes=(6, 9),
                             floors=(2, 3), kinds=("kitchen", "living", "bedroom", "library"),
                             plinth="minecraft:stone_bricks", fh=4, timber=False, reserved=reserved)
    STREETS = S
    # the stair foot opens onto a mosaic forecourt
    bb.fill(CX - 9, 0, z2 + PLAT + 1, CX + 9, 0, min(N - 1, z2 + PLAT + 8), MOSAIC)
    for i, (x0, z0, w, d, y, rot) in enumerate(placed):
        if i % 3 == 0:                                           # a striped cafe awning on the door side
            col = ["red", "yellow", "orange", "lime"][i % 4]
            if rot in (0, 2):
                zf = z0 + d if rot == 0 else z0 - 1
                for x in range(x0, x0 + w):
                    set_if_air(bb, x, 4, zf, f"minecraft:{col}_wool" if x % 2 else "minecraft:white_wool")
            else:
                xf = x0 + w if rot == 1 else x0 - 1
                for z in range(z0, z0 + d):
                    set_if_air(bb, xf, 4, z, f"minecraft:{col}_wool" if z % 2 else "minecraft:white_wool")
    print("dressrosa houses:", len(placed))
    # flower beds, sunflowers and fountains in the green gaps, lamp posts on the streets
    for _ in range(1400):
        x, z = int(rng.integers(1, N - 1)), int(rng.integers(1, N - 1))
        if street(x, z) or bb.get_region(x, 1, z, x, 1, z)[0, 0, 0] > 1 or bb.get_region(x, 0, z, x, 0, z)[0, 0, 0] <= 1:
            continue
        if x1 - 9 <= x <= x2 + 9 and z1 - 9 <= z <= z2 + 9:
            continue
        r = rng.random()
        if r < 0.7:
            bb.set(x, 1, z, ["minecraft:poppy", "minecraft:allium", "minecraft:pink_tulip", "minecraft:oxeye_daisy",
                             "minecraft:cornflower", "minecraft:rose_bush[half=lower]"][int(rng.integers(5))])
        else:
            bb.set(x, 1, z, "minecraft:sunflower[half=lower]")
            bb.set(x, 2, z, "minecraft:sunflower[half=upper]")
    for (fx, fz) in ((12, 12), (156, 12), (12, 156), (156, 156), (CX, 160)):
        if (bb.get_region(fx - 3, 1, fz - 3, fx + 3, 3, fz + 3) > 1).any():
            continue
        bb.cylinder(fx, 0, fz, 3, 1, "minecraft:quartz_bricks")
        bb.cylinder(fx, 1, fz, 2, 1, "minecraft:water[level=0]")
        bb.fill(fx, 1, fz, fx, 3, fz, "minecraft:quartz_pillar[axis=y]")
        bb.set(fx, 4, fz, "minecraft:sea_lantern")
    for x in range(3, N - 3, 3):
        for z in range(3, N - 3, 3):
            if (x * 7 + z * 13) % 11 or not street(x, z) or street(x + 2, z) and street(x - 2, z) and street(x, z + 2) and street(x, z - 2):
                continue
            if not (x1 - 9 <= x <= x2 + 9 and z1 - 9 <= z <= z2 + 9) and (bb.get_region(x - 1, 1, z - 1, x + 1, 4, z + 1) <= 1).all():
                lamp_post(bb, x, 1, z)


def birdcage(bb):
    """Doflamingo's strings: 24 white lines from the sky curving down like the bars of a birdcage."""
    AY, R = 140, 82
    for k in range(24):
        t = 2 * math.pi * k / 24
        prev = None
        for s in range(0, 1601):
            ph = (math.pi / 2) * s / 1600
            r = R * math.sin(ph)
            c = (round(CX + r * math.cos(t)), round(AY * math.cos(ph)), round(CZ + r * math.sin(t)))
            if prev is not None and c != prev:
                x, y, z = prev
                while (x, y, z) != c:
                    if x != c[0]:
                        x += 1 if c[0] > x else -1
                    elif z != c[2]:
                        z += 1 if c[2] > z else -1
                    else:
                        y += 1 if c[1] > y else -1
                    if 0 <= x < N and 0 <= z < N and y >= 1:
                        set_if_air(bb, x, y, z, "minecraft:white_stained_glass_pane")
            prev = c


def design():
    bb = BigBuild(seed=7, y_min=-6, y_max=150)
    tracker = P.PropTracker(7)
    audit = []
    rng = np.random.default_rng(7)
    town_ground(bb, rng)
    plateau(bb, rng)
    courtyard(bb)
    palace(bb, tracker, audit)
    town(bb, rng, tracker, audit)
    birdcage(bb)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    x1, z1, x2, z2 = PAL
    F1, F3 = PLAT + 1, PLAT + 2 * FH + 1
    b.npc(CX, F1 + 2, z1 + 2, "doflamingo", True)
    b.chest(CX + 6, F1, z1 + 2, "legendary", "south")
    b.chest(x1 + 4, F3, z1 + 8, "legendary", "east")
    b.chest(x1 + 3, F1, z2 - 3, "treasure", "east")
    b.guards("donquixote", ((CX - 3, z2 + 4), (CX + 3, z2 + 4), (CX - 8, CZ), (CX + 8, CZ)), y=F1)
    b.guards("gladiator", ((CX - 10, z2 + 12), (CX + 10, z2 + 12), (CX - 4, PLATEAU[3] - 2)), y=PLAT + 1)
    b.guards("donquixote", ((CX - 14, CZ), (CX + 14, CZ)), y=F3)
    return b, 0
