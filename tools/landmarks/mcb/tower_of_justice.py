"""Enies Lobby, the World Government's judicial island, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/tower_of_justice.md).

Three rock pillars standing in a foaming abyss, with the sea pouring over the rim all round. South: the Main Gate
with its round towers and guard rooms, the town of the officials (furnished houses on a lamp-lit avenue) and the
Courthouse (colonnade, pediment, clock tower and dome; inside the courtroom with Baskerville's high three-seat bench,
the dock and the gallery, offices in the wings). A drawbridge crosses the chasm to the Tower of Justice: four white
tiers with corner turrets, every floor furnished round a stair core (CP9's rooms: Blueno's bar, Kalifa's bath,
Kumadori's tatami room, a dojo), Spandam's office at the top and the WG flag on the roof. Behind it the Bridge of
Hesitation leads to the colossal Gates of Justice. Site 224 x 224, island tops at y 0, abyss floor y -41. (v2)"""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     table, castle_eave, stair_core, ring_floor, tier, cornice, wg_emblem, wg_flag, set_if_air)
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "tower_of_justice"
TITLE = "Enies Lobby"
CUTS = [3, 10, 40]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")
SOFT_EDGES = False                  # v3: the site is sea round a great round hole, edges are designed
EDGE_REACH = 2

WHITE = "onepiece:marine_bricks"
WHITE_ST = "onepiece:marine_brick_stairs"
WHITE_SL = "onepiece:marine_brick_slab"
WHITE_W = "onepiece:marine_brick_wall"
WALLMIX = ["onepiece:marine_bricks", "minecraft:white_concrete", "minecraft:smooth_quartz"]
TILE = "onepiece:marine_tiles"
TILE_ST = "onepiece:marine_tile_stairs"
PIL = "onepiece:marine_pillar[axis=y]"
ROOF = "minecraft:deepslate_tiles"
ROOF_ST = "minecraft:deepslate_tile_stairs"
GLASS = "minecraft:light_blue_stained_glass_pane"
INNER = "minecraft:white_concrete"
ROCK = ["minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:cobblestone"]
ROCK_W = [0.5, 0.25, 0.15, 0.10]
PAVE = ["minecraft:stone_bricks", "minecraft:polished_andesite", "minecraft:cracked_stone_bricks"]
FALL = "minecraft:light_blue_stained_glass"
FOAM = "minecraft:white_stained_glass"
WATER = "minecraft:water[level=0]"
GATE = "minecraft:polished_deepslate"
GATE2 = "minecraft:deepslate_tiles"
GATE3 = "minecraft:polished_blackstone_bricks"

N = 224
CX = 112
FLOOR_Y = -41
MAIN = (112, 156, 82, 48)           # ellipse cx, cz, rx, rz (v3: smaller, so the abyss shows all round)
HOLE = (112, 116, 106)              # v3: the great hole in the sea (cx, cz, r); the sea pours over its rim
ROCK_T = (112, 60, 36, 26)
ROCK_G = (112, 9, 52, 9)
CH = (76, 114, 148, 140, 14)        # courthouse x1, z1, x2, z2, roof y
TC = (112, 58)                      # tower centre
TT = [(15, 0, 5), (12, 30, 4), (9, 54, 3), (6, 72, 2)]   # tower tiers: half width, base y, storeys (fh 6)
ROOF_Y = 84
CORE = (110, 56)                    # tower stair, size 5


def ell(X, Z, e, wob=0.0):
    cx, cz, rx, rz = e
    r = np.hypot((X - cx) / rx, (Z - cz) / rz)
    return r <= 1 + wob * np.sin(X * 0.37 + Z * 0.21) * np.cos(Z * 0.29 - X * 0.13)


def land(X, Z):
    return ell(X, Z, MAIN, 0.03) | ell(X, Z, ROCK_T, 0.05) | ell(X, Z, ROCK_G, 0.04)


def on_land(x, z):
    return bool(land(np.array([x]), np.array([z]))[0])


# ---------------------------------------------------------------- the abyss, the rock pillars, the falls
def in_hole(X, Z):
    return np.hypot(X - HOLE[0], Z - HOLE[1]) < HOLE[2]


def terrain(bb, rng):
    """y 0 is the sea surface. Outside the round hole: open sea on a rock bed. Inside: a 41-deep abyss with a churning
    pool on its floor and the islands standing on rock pillars. On the rim the sea pours over the edge all round as a
    real waterfall curtain (source water at the lip, falling water down the cliff)."""
    hole = lambda X, Z: in_hole(X, Z)
    bb.mix(0, -48, 0, N - 1, FLOOR_Y - 1, N - 1, ROCK, ROCK_W)
    # the open sea outside the hole: rock to -9, sand bed, water to y 0
    # (only a wobbly band round the rim is written, so no square of sea bed shows at the site corners)
    near = lambda X, Z: ~hole(X, Z) & (np.hypot(X - HOLE[0], Z - HOLE[1]) < HOLE[2] + 7 + 3 * NT.noise(X, Z, 1139, 9))
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -10, N - 1, lambda X, y, Z: near(X, Z), "minecraft:stone")
    bb.fill_where(0, -9, 0, N - 1, -9, N - 1, lambda X, y, Z: near(X, Z), "minecraft:sand")
    bb.fill_where(0, -8, 0, N - 1, 0, N - 1, lambda X, y, Z: near(X, Z), WATER)
    # the cliff wall of the hole: a 3-thick ring of wet dark rock under the lip (behind the falling water)
    lip = lambda X, Z: (np.hypot(X - HOLE[0], Z - HOLE[1]) >= HOLE[2]) & (np.hypot(X - HOLE[0], Z - HOLE[1]) < HOLE[2] + 3)
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -1, N - 1, lambda X, y, Z: lip(X, Z) & (NT.noise(X + y * 3, Z - y, 1131, 3) > 0.45), "minecraft:deepslate")
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -1, N - 1, lambda X, y, Z: lip(X, Z) & (NT.noise(X + y * 3, Z - y, 1131, 3) <= 0.45), "minecraft:tuff")
    bb.fill_where(0, -2, 0, N - 1, -1, N - 1, lambda X, y, Z: lip(X, Z), "minecraft:mossy_cobblestone")
    # inside the hole: air down to the pool, the islands' pillars
    bb.fill(0, FLOOR_Y, 0, N - 1, FLOOR_Y, N - 1, WATER)
    bb.fill_where(0, FLOOR_Y + 1, 0, N - 1, 0, N - 1, lambda X, y, Z: hole(X, Z) & ~land(X, Z), AIR)
    # the curtain: the outermost ring inside the hole is falling water from the lip to the pool
    # (flowing water does not survive structure placement, so the curtain is a sheet of still water held against
    # the rock by a skin of clear glass: it reads as a wall of falling sea from inside and from above)
    rd = lambda X, Z: np.hypot(X - HOLE[0], Z - HOLE[1])
    ring = lambda X, Z: hole(X, Z) & (rd(X, Z) >= HOLE[2] - 1.5) & ~land(X, Z)
    skin = lambda X, Z: hole(X, Z) & (rd(X, Z) >= HOLE[2] - 2.9) & (rd(X, Z) < HOLE[2] - 1.5) & ~land(X, Z)
    bb.fill_where(0, FLOOR_Y + 1, 0, N - 1, 0, N - 1, lambda X, y, Z: ring(X, Z), WATER)
    bb.fill_where(0, FLOOR_Y + 1, 0, N - 1, 0, N - 1, lambda X, y, Z: skin(X, Z), "minecraft:glass")
    # rock pillars: mixed stone in noise patches (no stripes), moss and dripstone near the top
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -1, N - 1, lambda X, y, Z: land(X, Z), "minecraft:stone")
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -1, N - 1, lambda X, y, Z: land(X, Z) & (NT.noise(X + y * 2, Z - y, 1132, 5) > 0.6), "minecraft:andesite")
    bb.fill_where(0, FLOOR_Y, 0, N - 1, -1, N - 1, lambda X, y, Z: land(X, Z) & (NT.noise(X - y, Z + y * 2, 1133, 4) > 0.7), "minecraft:tuff")
    bb.fill_where(0, -3, 0, N - 1, -1, N - 1, lambda X, y, Z: land(X, Z) & (NT.noise(X, Z, 1134, 3) > 0.62), "minecraft:mossy_cobblestone")
    bb.mix(0, 0, 0, N - 1, 0, N - 1, PAVE, [0.6, 0.3, 0.1])
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: ~land(X, Z) & hole(X, Z) & ~ring(X, Z), AIR)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: ~land(X, Z) & ~hole(X, Z), WATER)
    # kerb round every island so nobody walks straight off, posts with lanterns now and then
    edge = lambda X, y, Z: land(X, Z) & ~(land(X + 1, Z) & land(X - 1, Z) & land(X, Z + 1) & land(X, Z - 1))
    bb.fill_where(1, 1, 1, N - 2, 1, N - 2, edge, WHITE_W)


# ---------------------------------------------------------------- main gate and town
def main_gate(bb, tracker, audit):
    z1, z2 = 186, 199
    gx1, gx2 = 98, 126
    # curtain walls either side
    for (a, b) in ((80, gx1 - 1), (gx2 + 1, 144)):
        bb.fill(a, 1, 192, b, 20, 195, WHITE)
        cornice(bb, a, 192, b, 195, 20, WHITE_ST, parapet=WHITE, merlons=WHITE)
        bb.fill(a, 21, 192, b, 21, 195, TILE)
    # gatehouse with the great arch
    top = tier(bb, gx1, z1, gx2, z2, 0, 4, 8, WALLMIX, GLASS, WHITE_ST, pilaster=PIL, band="minecraft:blue_terracotta",
               weights=[0.75, 0.15, 0.1])
    cornice(bb, gx1, z1, gx2, z2, top, WHITE_ST, parapet=WHITE, merlons=WHITE)
    P.arched_opening(bb, "x", CX, 1, z1, 11, 20, depth=z2 - z1 + 1, trim=PIL)
    bb.fill(CX - 5, 0, z1, CX + 5, 0, z2, "minecraft:polished_andesite")
    for y in (8, 16, 24):
        bb.fill(CX - 6, y, z1 + 1, CX + 6, y, z2 - 1, AIR)
    for (a, b) in ((gx1 + 1, CX - 7), (CX + 7, gx2 - 1)):
        for k, y in enumerate((1, 9, 17, 25)):
            wing_floor(bb, a, z1 + 1, b, z2 - 1, y, 7, INNER, seed_of("gate", a, y), tracker,
                       [["storage", "bedroom"][k % 2]], corridor="z", cw=3, audit=audit, max_room=8, min_room=4)
        bb.fill(a + 1, 1, z1 + 1, a + 1, 25, z1 + 1, "minecraft:ladder[facing=south]")
        bb.fill(CX - 7 if a < CX else CX + 7, 1, (z1 + z2) // 2, CX - 7 if a < CX else CX + 7, 2, (z1 + z2) // 2, AIR)
    # portcullis teeth in the arch and the WG emblem over it on both faces
    for x in range(CX - 4, CX + 5, 2):
        bb.fill(x, 17, z1, x, 21, z1, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    wg_emblem(bb, CX, 26, z1 - 1, "minecraft:blue_concrete", k=1.4, axis="x")
    wg_emblem(bb, CX, 26, z2 + 1, "minecraft:blue_concrete", k=1.4, axis="x")
    # two round towers with slate spires
    for tx in (88, 136):
        bb.cylinder(tx, 0, 192, 7, 44, WHITE)
        bb.cylinder(tx, 1, 192, 6, 43, AIR)
        for y in (12, 24, 36):
            bb.cylinder(tx, y, 192, 6, y, "minecraft:smooth_stone")
        P.square_spiral_stair(bb, tx - 3, 1, 189, 7, 44, WHITE_ST, core=WHITE)
        for y in range(6, 42, 6):
            for (dx, dz) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
                bb.fill(tx + dx, y, 192 + dz, tx + dx, y + 1, 192 + dz, GLASS)
        bb.cylinder(tx, 44, 192, 8, 44, TILE)
        for a in range(0, 360, 15):
            t = math.radians(a)
            bb.set(round(tx + 8 * math.cos(t)), 45, round(192 + 8 * math.sin(t)), WHITE_W)
        P.cone_roof(bb, tx, 46, 192, 5, 14, ROOF, hollow=False)
        bb.fill(tx, 60, 192, tx, 63, 192, "minecraft:dark_oak_fence")
        bb.fill(tx, 1, 199 if tx < CX else 185, tx, 2, 199 if tx < CX else 185, AIR)
        bb.fill(tx + (7 if tx < CX else -7), 1, 192, tx + (7 if tx < CX else -7), 2, 192, AIR)
        bb.fill(tx, 57, 192, tx + 1, 57, 192, AIR)
        wg_flag(bb, tx + 1, 63, 192, w=7, h=5)


TOWN = dict(walls=["minecraft:calcite", "minecraft:white_terracotta", "minecraft:smooth_sandstone"],
            frame="minecraft:stripped_dark_oak_log", base=["minecraft:stone_bricks", "minecraft:polished_andesite",
                                                           "minecraft:andesite"],
            floor="minecraft:spruce_planks", wood="dark_oak", chimney="minecraft:stone_bricks")


def town(bb, tracker, audit, rng):
    # the avenue from the gate to the courthouse, and a cross street
    bb.fill(CX - 5, 0, 144, CX + 5, 0, 185, "minecraft:polished_andesite")
    bb.fill(CX - 1, 0, 144, CX + 1, 0, 185, "minecraft:smooth_stone")
    bb.fill(36, 0, 164, 188, 0, 167, "minecraft:polished_andesite")
    for z in range(148, 184, 8):
        for x in (CX - 6, CX + 6):
            lamp_post(bb, x, 1, z, h=4)
    placed = []
    for z0 in (151, 171):
        for x0 in list(range(30, 100, 11)) + list(range(121, 196, 11)):
            w = int(rng.integers(8, 10)); d = int(rng.integers(7, 9)); floors = int(rng.integers(2, 4))
            rot = 3 if x0 < CX else 1
            if z0 + d >= 164 and z0 <= 168:
                continue                                    # keep the cross street clear
            W, D = (w, d) if rot % 2 == 0 else (d, w)
            if x0 + W >= CX - 7 and x0 <= CX + 7:
                continue
            if z0 + D > 185 or not all(on_land(x, z) for x in (x0 - 3, x0 + W + 2) for z in (z0 - 3, z0 + D + 2)):
                continue
            m, top, au = house_module(seed_of("elh", x0, z0), w, d, floors, ROOF_ST, tracker,
                                      [["kitchen", "living"][int(rng.integers(2))], "bedroom", "library"], pal=TOWN,
                                      timber=bool(rng.random() < 0.5), jetty=False)
            audit += au
            place_house(bb, m, w, d, x0, 0, z0, rot)
            placed.append((x0, z0, x0 + W, z0 + D))
    # little squares with a fountain at the crossing
    bb.cylinder(CX, 1, 166, 4, 1, WHITE)
    bb.cylinder(CX, 1, 166, 3, 1, WATER)
    bb.fill(CX, 1, 166, CX, 4, 166, WHITE)
    bb.set(CX, 5, 166, "minecraft:white_stained_glass")
    return placed


# ---------------------------------------------------------------- courthouse
def courthouse(bb, tracker, audit):
    x1, z1, x2, z2, top = CH
    tier(bb, x1, z1, x2, z2, 0, 2, 7, WALLMIX, GLASS, WHITE_ST, pilaster=PIL, band="minecraft:blue_terracotta",
         weights=[0.75, 0.15, 0.1], every=3)
    cornice(bb, x1, z1, x2, z2, top, WHITE_ST, parapet=WHITE_W)
    bb.fill(x1, top, z1, x2, top, z2, TILE)
    # the courtroom: double height in the middle
    c1, c2 = 96, 128
    bb.fill(c1, 7, z1 + 1, c2, 7, z2 - 1, AIR)
    for x in (c1 - 1, c2 + 1):
        bb.fill(x, 1, z1 + 1, x, 13, z2 - 1, WHITE)
        for z in range(z1 + 5, z2 - 3, 7):
            P.arched_opening(bb, "z", z, 1, x, 3, 4, depth=1)
    # Baskerville's bench: a high platform across the north end with three great seats, a tunnel under it to the
    # drawbridge door
    bb.fill(c1 + 4, 1, z1 + 1, c2 - 4, 5, z1 + 4, "minecraft:dark_oak_planks")
    bb.fill(c1 + 4, 6, z1 + 4, c2 - 4, 6, z1 + 4, "minecraft:dark_oak_slab[type=bottom]")
    for x in (CX - 5, CX, CX + 5):
        bb.set(x, 6, z1 + 2, "onepiece:captains_chair[facing=south]")
        bb.set(x, 7, z1 + 1, "minecraft:red_wool")
    P.stair_run(bb, c1 + 1, 1, z1 + 1, 5, 2, "east", "minecraft:dark_oak_stairs", base_y=0,
                support="minecraft:dark_oak_planks")
    bb.fill(CX - 3, 1, z1, CX + 3, 4, z1 + 4, AIR)
    bb.fill(CX - 3, 0, z1, CX + 3, 0, z1 + 4, "minecraft:polished_andesite")
    bb.fill(CX - 4, 1, z1 + 1, CX - 4, 4, z1 + 4, "minecraft:dark_oak_log[axis=y]")
    bb.fill(CX + 4, 1, z1 + 1, CX + 4, 4, z1 + 4, "minecraft:dark_oak_log[axis=y]")
    wg_flag(bb, CX - 6, 13, z1 + 1, w=13, h=5)
    # the dock (iron bars), the witness box, the clerks' desks and the gallery benches
    bb.fill(CX - 2, 1, z1 + 10, CX + 2, 1, z1 + 10, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    bb.fill(CX - 2, 1, z1 + 8, CX - 2, 1, z1 + 10, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    bb.fill(CX + 2, 1, z1 + 8, CX + 2, 1, z1 + 10, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    for x in (c1 + 3, c2 - 3):
        bb.fill(x - 1, 1, z1 + 7, x + 1, 1, z1 + 7, "minecraft:spruce_planks")
        bb.set(x, 1, z1 + 8, "minecraft:spruce_stairs[facing=north,half=bottom]")
        bb.set(x, 2, z1 + 7, "minecraft:lantern[hanging=false]")
    for z in range(z1 + 13, z2 - 2, 2):
        for (a, b) in ((c1 + 1, CX - 3), (CX + 3, c2 - 1)):
            bb.fill(a, 1, z, b, 1, z, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
    bb.fill(CX - 1, 0, z1 + 11, CX + 1, 0, z2 - 1, "minecraft:red_wool")
    for z in range(z1 + 6, z2 - 2, 8):
        bb.set(CX, 12, z, "onepiece:chandelier[facing=north]")
    for z in range(z1 + 3, z2 - 2, 5):
        for x in (c1, c2):
            bb.fill(x, 1, z, x, 12, z, PIL)
    # the wings: offices, archives and the judges' chambers on two floors
    for (a, b) in ((x1 + 1, c1 - 2), (c2 + 2, x2 - 1)):
        for k, y in enumerate((1, 8)):
            wing_floor(bb, a, z1 + 1, b, z2 - 1, y, 6, INNER, seed_of("ch", a, y), tracker,
                       [["library", "living"], ["living", "bedroom", "library"]][k], corridor="z", cw=3, audit=audit,
                       max_room=9)
        bb.fill(a + 1, 1, z2 - 1, a + 1, 7, z2 - 1, "minecraft:ladder[facing=north]")
    # front doors, portico with columns and a pediment
    bb.fill(CX - 3, 1, z2, CX + 3, 5, z2, AIR)
    for x, h in ((CX - 1, "left"), (CX, "right")):
        bb.set(x, 1, z2, f"minecraft:dark_oak_door[facing=south,half=lower,hinge={h},open=false]")
        bb.set(x, 2, z2, f"minecraft:dark_oak_door[facing=south,half=upper,hinge={h},open=false]")
    px1, px2, pz = 90, 134, z2 + 6
    bb.fill(px1 - 1, 0, z2 + 1, px2 + 1, 0, pz + 1, WHITE)
    bb.fill(px1 - 1, 0, pz + 2, px2 + 1, 0, pz + 2, st(WHITE_ST, "north"))
    P.colonnade(bb, "x", px1, px2, pz, 1, 4, 13, PIL, base=WHITE, capital="minecraft:chiseled_quartz_block",
                beam=WHITE)
    bb.fill(px1, top, z2 + 1, px2, top, pz, WHITE)
    for i in range(12):
        a, b = px1 + 2 * i, px2 - 2 * i
        if a > b:
            break
        bb.fill(a, top + 1 + i, pz, b, top + 1 + i, pz, WHITE)
        bb.fill(a, top + 1 + i, z2 + 1, b, top + 1 + i, pz - 1, TILE)
        bb.set(a - 1, top + 1 + i, pz, st(WHITE_ST, "east")); bb.set(b + 1, top + 1 + i, pz, st(WHITE_ST, "west"))
    wg_emblem(bb, CX, top + 6, pz + 1, "minecraft:blue_concrete", k=1.0, axis="x")
    # the clock tower and dome over the middle
    tx1, tz1, tx2, tz2 = CX - 8, 118, CX + 8, 134
    tt = tier(bb, tx1, tz1, tx2, tz2, top, 3, 7, WALLMIX, GLASS, WHITE_ST, pilaster=PIL, weights=[0.75, 0.15, 0.1],
              every=4)
    cornice(bb, tx1, tz1, tx2, tz2, tt, WHITE_ST, parapet=WHITE_W)
    for (cx, cz, ax) in ((CX, tz2 + 1, "x"), (CX, tz1 - 1, "x"), (tx1 - 1, 126, "z"), (tx2 + 1, 126, "z")):
        for a in range(0, 360, 10):
            t = math.radians(a)
            u, v = round(4 * math.cos(t)), round(4 * math.sin(t))
            if ax == "x":
                bb.set(cx + u, tt - 6 + v, cz, "minecraft:gold_block")
            else:
                bb.set(cx, tt - 6 + v, cz + u, "minecraft:gold_block")
        if ax == "x":
            bb.fill(cx, tt - 6, cz, cx, tt - 3, cz, "minecraft:black_concrete"); bb.fill(cx, tt - 6, cz, cx + 2, tt - 6, cz, "minecraft:black_concrete")
        else:
            bb.fill(cx, tt - 6, cz, cx, tt - 3, cz, "minecraft:black_concrete"); bb.fill(cx, tt - 6, cz, cx, tt - 6, cz + 2, "minecraft:black_concrete")
    bb.dome(CX, tt + 1, 126, 8, "minecraft:light_gray_concrete", hollow=True)
    bb.fill(CX, tt + 9, 126, CX, tt + 13, 126, "minecraft:dark_oak_fence")
    bb.set(CX, tt + 14, 126, "minecraft:lantern[hanging=false]")
    bb.fill(tx1 + 2, top + 1, tz1 + 1, tx1 + 2, tt, tz1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(tx1 + 2, top, tz1 + 1, tx1 + 2, top, tz1 + 1, "minecraft:ladder[facing=south]")
    furnish(bb, [(tx1 + 1, tz1 + 1, tx2 - 1, tz2 - 1)], top + 8, 6, ["workshop"], seed_of("clock"), tracker, audit=audit)
    # roof stair from the wing's top floor
    bb.fill(x1 + 2, 8, z1 + 1, x1 + 2, top, z1 + 1, "minecraft:ladder[facing=south]")
    return pz


# ---------------------------------------------------------------- drawbridge, tower, bridge of hesitation, gates
def drawbridge(bb):
    z1, z2 = 84, CH[1] - 1
    bb.fill(CX - 3, 0, z1, CX + 3, 0, z2, "minecraft:spruce_planks")
    bb.fill(CX - 4, 0, z1, CX - 4, 1, z2, "minecraft:dark_oak_log[axis=z]")
    bb.fill(CX + 4, 0, z1, CX + 4, 1, z2, "minecraft:dark_oak_log[axis=z]")
    bb.fill(CX - 3, -1, z1 + 2, CX + 3, -1, z2 - 2, "minecraft:dark_oak_slab[type=top]")
    # the lifting towers on the tower rock and the chains
    for x in (CX - 7, CX + 7):
        bb.fill(x - 1, 1, z1 - 4, x + 1, 18, z1 - 2, WHITE)
        bb.fill(x - 1, 19, z1 - 4, x + 1, 19, z1 - 2, TILE)
        P.cone_roof(bb, x, 20, z1 - 3, 2, 4, ROOF, hollow=False)
        bb.set(x, 15, z1 - 1, "minecraft:lantern[hanging=false]")
        ex = CX - 4 if x < CX else CX + 4                 # chain from the tower top down to the deck edge
        for k in range(17):
            t = k / 16
            bb.set(round(x + (ex - x) * t), round(17 - 15 * t), round(z1 - 1 + 15 * t),
                   "minecraft:iron_chain[axis=y,waterlogged=false]")


def theme_room(bb, room, y, theme):
    """Dress one room for a CP9 member."""
    x1, z1, x2, z2 = room
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    if theme == "bar":                       # Blueno's bar
        bb.fill(x1 + 1, y, cz, x2 - 1, y, cz, "minecraft:dark_oak_planks")
        bb.fill(x1 + 1, y + 1, cz, x2 - 1, y + 1, cz, "minecraft:dark_oak_slab[type=bottom]")
        for x in range(x1 + 1, x2, 2):
            set_if_air(bb, x, y, cz + 1, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
        bb.fill(x1, y, z1, x1, y + 2, z1 + 2, "minecraft:barrel[facing=east]")
        bb.set(x2, y, z1, "minecraft:barrel[facing=up]")
    elif theme == "bath":                    # Kalifa's bath
        bb.fill(cx - 2, y - 1, cz - 1, cx + 2, y - 1, cz + 1, "minecraft:smooth_quartz")
        bb.fill(cx - 2, y, cz - 1, cx + 2, y, cz + 1, "minecraft:smooth_quartz")
        bb.fill(cx - 1, y, cz, cx + 1, y, cz, WATER)
        bb.set(cx - 2, y + 1, cz - 1, "minecraft:potted_white_tulip")
        bb.fill(x1, y - 1, z1, x2, y - 1, z1, "minecraft:white_glazed_terracotta")
    elif theme == "tatami":                  # Kumadori's room
        bb.fill(x1, y - 1, z1, x2, y - 1, z2, "minecraft:bamboo_mosaic")
        bb.set(cx, y, cz, "minecraft:bamboo_slab[type=bottom]")
        bb.set(x1, y, z2, "minecraft:potted_bamboo")
        bb.set(x2, y, z1, "minecraft:lantern[hanging=false]")
    elif theme == "dojo":                    # Jabra's training room
        bb.fill(x1, y - 1, z1, x2, y - 1, z2, "minecraft:stripped_spruce_wood[axis=y]")
        bb.set(x1, y, z1, "onepiece:weapon_rack[facing=east]")
        bb.set(cx, y, cz, "minecraft:target")
        bb.set(x2, y, z2, "minecraft:hay_block[axis=y]")


def tower(bb, tracker, audit):
    cx, cz = TC
    rooms_all = []
    floors = []
    for i, (hw, y0, n) in enumerate(TT):
        x1, x2, z1, z2 = cx - hw, cx + hw, cz - hw, cz + hw
        top = tier(bb, x1, z1, x2, z2, y0, n, 6, WALLMIX, GLASS, WHITE_ST, pilaster=PIL,
                   band="minecraft:light_blue_terracotta", weights=[0.75, 0.15, 0.1], every=2, pil_every=6)
        cornice(bb, x1, z1, x2, z2, top, TILE_ST, parapet=WHITE, merlons=WHITE)
        bb.fill(x1, top, z1, x2, top, z2, TILE)
        # corner turrets with slate spires
        for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            bb.cylinder(tx, top - 8, tz, 2, top + 3, WHITE)
            P.cone_roof(bb, tx, top + 4, tz, 3, 6, ROOF, hollow=False)
            bb.fill(tx, top + 10, tz, tx, top + 11, tz, "minecraft:dark_oak_fence")
        core = (CORE[0] - 1, CORE[1] - 1, CORE[0] + 5, CORE[1] + 5)
        for k in range(n):
            y = y0 + 6 * k + 1
            floors.append(y)
            if hw > 7:
                rs = ring_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 5, core, INNER, seed_of("toj", y), tracker,
                                [["bedroom", "living", "library", "workshop", "storage"][(k + i + j) % 5] for j in range(3)],
                                cw=2, audit=audit, floor="minecraft:polished_andesite", max_room=8)
                rooms_all.append((y, rs))
        floors.append(top + 1)
    # CP9 character rooms: the biggest room on four floors
    for (y, rs), theme in zip([r for r in rooms_all if r[1]][1:5], ("bar", "bath", "tatami", "dojo")):
        big = max(rs, key=lambda r: (r[2] - r[0] + 1) * (r[3] - r[1] + 1))
        theme_room(bb, big, y, theme)
    # top tier: Spandam's office (y 73) and the CP9 lounge (y 79)
    hw, y0, n = TT[3]
    x1, x2, z1, z2 = cx - hw + 1, cx + hw - 1, cz - hw + 1, cz + hw - 1
    oy = y0 + 1
    bb.fill(x1 + 1, oy, z2 - 2, x1 + 5, oy, z2 - 2, "minecraft:dark_oak_planks")
    bb.set(x1 + 3, oy + 1, z2 - 2, "minecraft:gold_block")                 # the golden Den Den Mushi
    bb.set(x1 + 3, oy, z2 - 1, "onepiece:captains_chair[facing=north]")
    bb.fill(x2, oy, z1, x2, oy + 3, z1 + 4, "minecraft:bookshelf")
    bb.fill(x1, oy - 1, z1, x2, oy - 1, z2, "minecraft:red_wool")
    furnish(bb, [(x1, z1, x2, z2)], y0 + 7, 5, ["living"], seed_of("cp9lounge"), tracker, audit=audit)
    # the stair core through every floor up to the roof, a hut on the roof
    stair_core(bb, CORE[0], CORE[1], 5, 1, ROOF_Y, floors, WHITE, WHITE_ST)
    bb.fill(CORE[0] - 1, ROOF_Y + 1, CORE[1] - 1, CORE[0] + 5, ROOF_Y + 4, CORE[1] + 5, WHITE)
    bb.fill(CORE[0], ROOF_Y + 1, CORE[1], CORE[0] + 4, ROOF_Y + 3, CORE[1] + 4, AIR)
    P.square_spiral_stair(bb, CORE[0], ROOF_Y - 4, CORE[1], 5, ROOF_Y, WHITE_ST, core=WHITE)
    bb.fill(CORE[0] + 2, ROOF_Y + 1, CORE[1] + 5, CORE[0] + 2, ROOF_Y + 2, CORE[1] + 5, AIR)
    bb.fill(CORE[0] - 1, ROOF_Y + 5, CORE[1] - 1, CORE[0] + 5, ROOF_Y + 5, CORE[1] + 5, TILE)
    # the WG flag on its pole above the roof
    pole_x, pole_z = cx, cz - 4
    bb.fill(pole_x, ROOF_Y + 1, pole_z, pole_x, ROOF_Y + 26, pole_z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    bb.set(pole_x, ROOF_Y + 27, pole_z, "minecraft:gold_block")
    wg_flag(bb, pole_x + 1, ROOF_Y + 26, pole_z, w=17, h=11)
    # front door and steps on the south side, a terrace round the base
    hw0 = TT[0][0]
    bb.fill(cx - 1, 1, cz + hw0, cx + 1, 4, cz + hw0, AIR)
    for x, h in ((cx - 1, "left"), (cx + 1, "right")):
        bb.set(x, 1, cz + hw0, f"minecraft:iron_door[facing=south,half=lower,hinge={h},open=false,powered=false]")
        bb.set(x, 2, cz + hw0, f"minecraft:iron_door[facing=south,half=upper,hinge={h},open=false,powered=false]")
    bb.fill(cx - 1, 1, cz - hw0, cx + 1, 3, cz - hw0, AIR)          # back door to the Bridge of Hesitation
    wg_emblem(bb, cx, 9, cz + hw0 + 2, "minecraft:blue_concrete", k=1.0, axis="x")
    return ROOF_Y


def bridge_of_hesitation(bb):
    z1, z2 = 15, 37
    bb.fill(CX - 4, 0, z1, CX + 4, 0, z2, "minecraft:stone_bricks")
    bb.fill(CX - 3, 0, z1, CX + 3, 0, z2, "minecraft:polished_andesite")
    for x in (CX - 5, CX + 5):
        bb.fill(x, 0, z1, x, 1, z2, "minecraft:stone_bricks")
        bb.fill(x, 2, z1, x, 2, z2, "minecraft:stone_brick_wall")
    for z in range(z1, z2 + 1, 6):
        for x in (CX - 5, CX + 5):
            bb.fill(x, 2, z, x, 3, z, "minecraft:stone_bricks")
            bb.set(x, 4, z, "minecraft:lantern[hanging=false]")
    # an arch under the span
    for z in range(z1, z2 + 1):
        t = (z - z1) / (z2 - z1)
        drop = int(round(8 * (1 - math.sin(math.pi * t)))) + 1
        bb.fill(CX - 5, -drop, z, CX + 5, -1, z, "minecraft:stone_bricks")


def gates_of_justice(bb):
    """The Gates of Justice: two colossal grey door leaves between thick piers, under a stepped lintel crowned with
    the WG emblem. They face south, towards the tower."""
    x1, x2, z1, z2, H = 79, 145, 5, 12, 104
    bb.fill(x1, 1, z1, x2, H, z2, GATE)
    bb.fill(x1 + 12, 1, z1 + 1, x2 - 12, H - 15, z2 - 1, AIR)          # recess between the piers
    bb.fill(x1 + 12, 1, z1, x2 - 12, H - 15, z1 + 2, GATE2)              # the door leaves (back half)
    bb.fill(x1 + 12, 1, z1 + 3, x2 - 12, H - 15, z1 + 3, GATE2)          # leaf face set back from the piers
    for x in range(x1 + 15, x2 - 11, 6):                                  # vertical ribs
        bb.fill(x, 1, z1 + 4, x, H - 16, z1 + 4, GATE3)
    for y in (24, 48, 72):                                                # cross ribs
        bb.fill(x1 + 12, y, z1 + 4, x2 - 12, y, z1 + 4, GATE3)
    bb.fill(CX, 1, z1 + 3, CX, H - 15, z1 + 4, "minecraft:black_concrete")  # the seam where the leaves meet
    for x in (CX - 4, CX + 4):                                            # ring handles
        for a in range(0, 360, 20):
            t = math.radians(a)
            bb.set(x + round(2 * math.cos(t)), 36 + round(2 * math.sin(t)), z1 + 5, "minecraft:iron_block")
    bb.fill(x1 + 12, 0, z1 + 4, x2 - 12, 0, z2 + 3, "minecraft:polished_andesite")
    # pier faces: tall panels and bands
    for (a, b) in ((x1, x1 + 11), (x2 - 11, x2)):
        for y in range(8, H - 15, 16):
            bb.fill(a + 2, y, z2 + 1, b - 2, y + 10, z2 + 1, GATE3)
            bb.fill(a + 3, y + 1, z2 + 1, b - 3, y + 9, z2 + 1, AIR)
        bb.fill(a, H - 15, z2 + 1, b, H - 14, z2 + 1, GATE3)
    # stepped crown and the emblem
    for i in range(4):
        bb.fill(x1 + 4 * i, H + 1 + 2 * i, z1 + i, x2 - 4 * i, H + 2 + 2 * i, z2 - i, GATE if i % 2 == 0 else GATE3)
    bb.fill(x1 + 12, H - 14, z2 + 1, x2 - 12, H, z2 + 1, GATE3)
    wg_emblem(bb, CX, H - 7, z2 + 2, "minecraft:white_concrete", k=1.6, axis="x")
    for (a, b) in ((x1, x1 + 11), (x2 - 11, x2)):
        for x in (a, b):
            bb.fill(x, 1, z2 + 1, x, H, z2 + 1, GATE3)


# ---------------------------------------------------------------- assembly
def design():
    bb = BigBuild(seed=113, y_min=-48, y_max=128)
    tracker = P.PropTracker(113)
    audit = []
    rng = np.random.default_rng(113)
    terrain(bb, rng)
    main_gate(bb, tracker, audit)
    town(bb, tracker, audit, rng)
    pz = courthouse(bb, tracker, audit)
    drawbridge(bb)
    roof = tower(bb, tracker, audit)
    bridge_of_hesitation(bb)
    gates_of_justice(bb)
    # the courthouse square: planters with trees, benches, WG flag poles
    for (x, z) in ((84, 145), (140, 145), (96, 145), (128, 145)):
        bb.fill(x - 2, 1, z - 2, x + 2, 1, z + 2, WHITE_W)
        bb.fill(x - 1, 1, z - 1, x + 1, 1, z + 1, "minecraft:grass_block[snowy=false]")
        P.tree(bb, x, 2, z, height=6, kind="oak", rng=rng)
    for x in (104, 120):
        bb.fill(x, 1, 146, x, 14, 146, "minecraft:white_concrete")
        wg_flag(bb, x + 1, 14, 146, w=7, h=5)
    # tower rock: lamp posts and a little garden
    for (x, z) in ((92, 66), (132, 66), (92, 50), (132, 50), (100, 40), (124, 40)):
        lamp_post(bb, x, 1, z, h=4)
    return bb, audit, roof


def build():
    bb, audit, roof = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    cx, cz = TC
    hw, y0, n = TT[3]
    b.chest(cx + hw - 2, y0 + 1, cz - hw + 2, "hard", "west")
    b.chest(CH[0] + 4, 1, CH[1] + 4, "marine", "south")
    b.npc(cx, roof + 1, cz + 3, "lucci", True)
    b.guards("cp_agent", ((cx - 8, cz + 20), (cx + 8, cz + 20), (cx - 20, cz), (cx + 20, cz)))
    b.guards("marine_rifle", ((CX - 8, 183), (CX + 8, 183), (CX - 10, 160), (CX + 10, 160)))
    b.guards("marine", ((CX - 20, 148), (CX + 20, 148), (60, 165), (164, 165)))
    return b, 0
