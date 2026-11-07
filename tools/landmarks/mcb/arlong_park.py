"""Arlong Park, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/arlong_park.md).

The Arlong Pirates' walled compound on the Conomi coast: cream walls capped with teal tiles and red pilasters, square
three-floor corner towers, a gatehouse with the big ARLONG PARK board over a timber gate, a seawater pool in the paved
courtyard (Arlong's deck chair and parasol on its rim), a canal that brings the sea in through tall iron sea gates with
a little landing stage, a training yard, and at the back the main hall with a red-columned veranda and the seven-storey
pagoda tower (Nami's map room at the top, the Arlong flag on the spire). Ground = y 0; the gate faces +z (south); the
sea is to the north (-z). ~180 x 177, tower ~90 tall.
(v3, 2026-10-30: the sea wraps the north and east sides and the pool opens straight to it through a sea-gate tower
in the east wall; buttressed outer walls with a teal wave frieze.)
(v2, 2026-10-29: ryan asked for builds ~50% bigger with more rooms and decor, not just magnified.)"""
import math, zlib
import numpy as np
from mcb.bridge import BigBuild, P, to_canvas

SID = "arlong_park"
TITLE = "Arlong Park"
CUTS = [5, 12, 30, 60]
TILER = dict(terrain="beard_thin")

WALL = ["onepiece:dressrosa_stucco", "minecraft:smooth_sandstone", "minecraft:sandstone"]
WALL_W = [0.6, 0.3, 0.1]
BASE = ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks"]
RED = "minecraft:stripped_mangrove_log[axis=y]"
RED_BEAM = "minecraft:stripped_mangrove_log"
TILE_ST = "minecraft:waxed_oxidized_cut_copper_stairs"
TILE_SL = "minecraft:waxed_oxidized_cut_copper_slab"
TILE = "minecraft:waxed_oxidized_cut_copper"
PAVE = ["minecraft:smooth_stone", "minecraft:stone_bricks", "minecraft:polished_andesite"]
WATER = "minecraft:water[level=0]"
AIR = "minecraft:air"

NX, NZ = 180, 177
WX1, WX2, WZ1, WZ2 = 15, 164, 21, 164       # outer wall line
WT = 4                                       # wall thickness
WALL_H = 16
GX = 90                                      # gate centre x (south wall)
POOL = (81, 105, 33, 22)                     # cx, cz, rx, rz
CHAN = (98, 112)                             # z range of the sea channel from the pool east to the open sea (v3)
HALL = (40, 140, 33, 63)                     # main hall x1, x2, z1, z2
TOWER = (74, 106, 35, 61)                    # tower base x1, x2, z1, z2 (on top of the hall)
HF = 8                                       # hall storey (7 clear + floor)
LEVEL = 7                                    # tower storey height
LEVELS = 7


def flared_eave(bb, x1, z1, x2, z2, y, out=2):
    """A Chinese eave: a skirt of tile stairs `out` blocks wide round a rectangle, the corners swept up by one."""
    for i in range(out):
        yy = y - i + out - 1
        a1, b1, a2, b2 = x1 - out + i, z1 - out + i, x2 + out - i, z2 + out - i
        bb.fill(a1, yy, b1, a2, yy, b1, f"{TILE_ST}[facing=south,half=bottom]")
        bb.fill(a1, yy, b2, a2, yy, b2, f"{TILE_ST}[facing=north,half=bottom]")
        bb.fill(a1, yy, b1, a1, yy, b2, f"{TILE_ST}[facing=east,half=bottom]")
        bb.fill(a2, yy, b1, a2, yy, b2, f"{TILE_ST}[facing=west,half=bottom]")
    for (cx, cz) in ((x1 - out, z1 - out), (x2 + out, z1 - out), (x1 - out, z2 + out), (x2 + out, z2 + out)):
        bb.set(cx, y + out - 1, cz, TILE)
        bb.set(cx, y + out, cz, f"{TILE_SL}[type=bottom]")


def pagoda_roof(bb, x1, z1, x2, z2, y, out=2):
    """Hip roof with a flared skirt and a ridge cap. Returns the top y."""
    flared_eave(bb, x1, z1, x2, z2, y, out=out)
    top = P.hip_roof(bb, x1, z1, x2, z2, y + 1, TILE_ST, ridge=f"{TILE_SL}[type=bottom]")
    i = 0
    while x1 + i <= x2 - i and z1 + i <= z2 - i and y + 1 + i < top:
        if x1 + i + 1 <= x2 - i - 1 and z1 + i + 1 <= z2 - i - 1:
            bb.fill(x1 + i + 1, y + 1 + i, z1 + i + 1, x2 - i - 1, y + 1 + i, z2 - i - 1, TILE)
        i += 1
    return top


def framed_walls(bb, x1, y1, z1, x2, y2, z2, post_every=4, windows=True, win_h=2):
    """Cream walls with red posts, a red beam on top and lattice windows between posts."""
    bb.walls(x1, y1, z1, x2, y2, z2, WALL[0])
    bb.mix(x1, y1, z1, x2, y2, z1, WALL, WALL_W); bb.mix(x1, y1, z2, x2, y2, z2, WALL, WALL_W)
    bb.mix(x1, y1, z1, x1, y2, z2, WALL, WALL_W); bb.mix(x2, y1, z1, x2, y2, z2, WALL, WALL_W)
    bb.fill(x1 + 1, y1, z1 + 1, x2 - 1, y2, z2 - 1, AIR)
    for x in list(range(x1, x2, post_every)) + [x2]:
        bb.fill(x, y1, z1, x, y2, z1, RED); bb.fill(x, y1, z2, x, y2, z2, RED)
    for z in list(range(z1, z2, post_every)) + [z2]:
        bb.fill(x1, y1, z, x1, y2, z, RED); bb.fill(x2, y1, z, x2, y2, z, RED)
    bb.fill(x1, y2 + 1, z1, x2, y2 + 1, z1, f"{RED_BEAM}[axis=x]"); bb.fill(x1, y2 + 1, z2, x2, y2 + 1, z2, f"{RED_BEAM}[axis=x]")
    bb.fill(x1, y2 + 1, z1, x1, y2 + 1, z2, f"{RED_BEAM}[axis=z]"); bb.fill(x2, y2 + 1, z1, x2, y2 + 1, z2, f"{RED_BEAM}[axis=z]")
    if windows:
        wy = y1 + 2
        for x in range(x1 + post_every // 2, x2 - 1, post_every):
            for z in (z1, z2):
                bb.fill(x, wy, z, x, wy + win_h - 1, z, "minecraft:iron_bars")
        for z in range(z1 + post_every // 2, z2 - 1, post_every):
            for x in (x1, x2):
                bb.fill(x, wy, z, x, wy + win_h - 1, z, "minecraft:iron_bars")


def outer_wall(bb):
    for y in range(-3, WALL_H + 1):
        ring = lambda X, yy, Z: (((X >= WX1) & (X <= WX2) & (Z >= WZ1) & (Z <= WZ2)) &
                                 ~((X >= WX1 + WT) & (X <= WX2 - WT) & (Z >= WZ1 + WT) & (Z <= WZ2 - WT)))
        bb.fill_where(WX1, y, WZ1, WX2, y, WZ2, ring, BASE[0] if y <= 2 else WALL[0])
    t = WT - 1
    bb.mix(WX1, 3, WZ1, WX2, WALL_H, WZ1 + t, WALL, WALL_W); bb.mix(WX1, 3, WZ2 - t, WX2, WALL_H, WZ2, WALL, WALL_W)
    bb.mix(WX1, 3, WZ1, WX1 + t, WALL_H, WZ2, WALL, WALL_W); bb.mix(WX2 - t, 3, WZ1, WX2, WALL_H, WZ2, WALL, WALL_W)
    bb.mix(WX1 + WT, 0, WZ1 + WT, WX2 - WT, 0, WZ2 - WT, PAVE, [0.55, 0.3, 0.15])
    # stone plinth course one proud outside
    bb.fill_where(WX1 - 1, 0, WZ1 - 1, WX2 + 1, 2, WZ2 + 1,
                  lambda X, y, Z: ((X == WX1 - 1) | (X == WX2 + 1) | (Z == WZ1 - 1) | (Z == WZ2 + 1)), BASE[0])
    # stone buttresses every 12 (2 out, stepped back near the top) with a red pilaster up the face (v3: walls had no
    # depth), and a teal wave frieze of scallops between them
    for x in range(WX1 + 6, WX2 - 3, 12):
        for (zf, out, f) in ((WZ1, -1, "north"), (WZ2, 1, "south")):
            bb.mix(x - 1, -2, zf + out, x + 1, WALL_H - 5, zf + 2 * out, BASE, [0.7, 0.2, 0.1])
            bb.fill(x - 1, WALL_H - 4, zf + out, x + 1, WALL_H - 4, zf + out, BASE[0])
            bb.fill(x - 1, WALL_H - 4, zf + 2 * out, x + 1, WALL_H - 4, zf + 2 * out, f"minecraft:stone_brick_stairs[facing={'south' if out < 0 else 'north'},half=bottom]")
            bb.fill(x, 3, zf + 3 * out, x, WALL_H - 5, zf + 3 * out, RED)
            bb.fill(x, 3, zf + out, x, WALL_H, zf + out, RED)
    for z in range(WZ1 + 6, WZ2 - 3, 12):
        for (xf, out, f) in ((WX1, -1, "west"), (WX2, 1, "east")):
            bb.mix(xf + out, -2, z - 1, xf + 2 * out, WALL_H - 5, z + 1, BASE, [0.7, 0.2, 0.1])
            bb.fill(xf + out, WALL_H - 4, z - 1, xf + out, WALL_H - 4, z + 1, BASE[0])
            bb.fill(xf + 2 * out, WALL_H - 4, z - 1, xf + 2 * out, WALL_H - 4, z + 1, f"minecraft:stone_brick_stairs[facing={'east' if out < 0 else 'west'},half=bottom]")
            bb.fill(xf + 3 * out, 3, z, xf + 3 * out, WALL_H - 5, z, RED)
            bb.fill(xf + out, 3, z, xf + out, WALL_H, z, RED)
    yf = WALL_H - 3
    for x in range(WX1, WX2 + 1):
        for (zf, f) in ((WZ1 - 1, "north"), (WZ2 + 1, "south")):
            if (x - WX1 - 6) % 12:
                bb.set(x, yf, zf, f"{TILE_ST}[facing={'south' if f == 'north' else 'north'},half=top]" if x % 4 else TILE)
                if x % 4 == 2:
                    bb.set(x, yf - 1, zf, TILE)
    for z in range(WZ1, WZ2 + 1):
        for (xf, f) in ((WX1 - 1, "west"), (WX2 + 1, "east")):
            if (z - WZ1 - 6) % 12 == 0:
                continue
            bb.set(xf, yf, z, f"{TILE_ST}[facing={'east' if f == 'west' else 'west'},half=top]" if z % 4 else TILE)
            if z % 4 == 2:
                bb.set(xf, yf - 1, z, TILE)
    # a red beam band under the coping
    for (a, b_) in ((WZ1 - 1, WZ1 - 1), (WZ2 + 1, WZ2 + 1)):
        bb.fill(WX1 - 1, WALL_H - 1, a, WX2 + 1, WALL_H - 1, b_, f"{RED_BEAM}[axis=x]")
    for a in (WX1 - 1, WX2 + 1):
        bb.fill(a, WALL_H - 1, WZ1 - 1, a, WALL_H - 1, WZ2 + 1, f"{RED_BEAM}[axis=z]")
    # teal tile coping: a little gable roof along the wall top (stairs out on both faces, ridge slab)
    y = WALL_H + 1
    for (a, c) in ((WZ1, WZ1 + t), (WZ2 - t, WZ2)):
        bb.fill(WX1 - 1, y, a - 1, WX2 + 1, y, a - 1, f"{TILE_ST}[facing=south,half=bottom]")
        bb.fill(WX1 - 1, y, c + 1, WX2 + 1, y, c + 1, f"{TILE_ST}[facing=north,half=bottom]")
        bb.fill(WX1 - 1, y, a, WX2 + 1, y, c, TILE)
        bb.fill(WX1 - 1, y + 1, a + 1, WX2 + 1, y + 1, c - 1, f"{TILE_SL}[type=bottom]")
    for (a, c) in ((WX1, WX1 + t), (WX2 - t, WX2)):
        bb.fill(a - 1, y, WZ1 + t, a - 1, y, WZ2 - t, f"{TILE_ST}[facing=east,half=bottom]")
        bb.fill(c + 1, y, WZ1 + t, c + 1, y, WZ2 - t, f"{TILE_ST}[facing=west,half=bottom]")
        bb.fill(a, y, WZ1 + t, c, y, WZ2 - t, TILE)
        bb.fill(a + 1, y + 1, WZ1 + t, c - 1, y + 1, WZ2 - t, f"{TILE_SL}[type=bottom]")
    # small barred windows high in the wall every 24
    for x in range(WX1 + 18, WX2 - 6, 24):
        for z in (WZ1, WZ2):
            bb.fill(x, 10, z, x, 11, z + t if z == WZ1 else z - t, "minecraft:iron_bars")


def corner_tower(bb, cx, cz, tracker, rooms):
    """Square three-floor tower across a wall corner: ladder in the outer corner, a door on the courtyard side,
    rooms on every floor, a flared eave at the wall top and a pagoda roof."""
    s = 7
    x1, x2, z1, z2 = cx - s, cx + s, cz - s, cz + s
    bb.fill(x1 - 1, -3, z1 - 1, x2 + 1, 1, z2 + 1, BASE[0])
    framed_walls(bb, x1, 2, z1, x2, 15, z2, post_every=7, win_h=3)
    framed_walls(bb, x1, 17, z1, x2, 26, z2, post_every=7, win_h=3)
    for fy in (1, 9, 17):
        bb.fill(x1 + 1, fy, z1 + 1, x2 - 1, fy, z2 - 1, "minecraft:spruce_planks")
    flared_eave(bb, x1, z1, x2, z2, WALL_H + 1, out=3)
    pagoda_roof(bb, x1, z1, x2, z2, 28, out=3)
    # ladder in the corner on the sea/outside side
    lx = x1 + 1 if cx < GX else x2 - 1
    lz = z1 + 1 if cz < 90 else z2 - 1
    face = "south" if cz < 90 else "north"
    bb.fill(lx, 2, lz, lx, 26, lz, f"minecraft:ladder[facing={face}]")
    # door from the courtyard
    dx = x2 if cx < GX else x1
    dz = cz + (5 if cz < 90 else -5)
    f = "east" if cx < GX else "west"
    bb.set(dx, 2, dz, f"minecraft:spruce_door[facing={f},half=lower,hinge=left,open=false]")
    bb.set(dx, 3, dz, f"minecraft:spruce_door[facing={f},half=upper,hinge=left,open=false]")
    # rooms: guard room, armory, lookout with a cannon at each window
    for i, (fy, h, kind) in enumerate(((2, 7, "storage"), (10, 7, "workshop"), (18, 8, "bedroom"))):
        rm = (x1 + 2, z1 + 2, x2 - 2, z2 - 2)
        P.furnish_room(bb, rm, fy, kind=kind, height=h, seed=cx * 7 + cz + i, wood="spruce", tracker=tracker,
                       doors=[(lx, lz), (dx, dz)])
        rooms.append((rm, fy, h))
    # cannons on the top floor looking out to sea / over the land
    oz, fz = (z1 + 2, "north") if cz < 90 else (z2 - 2, "south")
    ox, fx = (x1 + 2, "west") if cx < GX else (x2 - 2, "east")
    bb.set(cx, 18, oz, f"onepiece:cannon[facing={fz}]")
    bb.set(ox, 18, cz, f"onepiece:cannon[facing={fx}]")


def gatehouse(bb):
    x1, x2, z1, z2 = GX - 25, GX + 25, WZ2 - 9, WZ2 + 4
    bb.fill(x1 - 1, -3, z1 - 1, x2 + 1, 1, z2 + 1, BASE[0])
    framed_walls(bb, x1, 2, z1, x2, 22, z2, post_every=5, windows=False)
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, PAVE[1])
    bb.fill(x1 + 1, 18, z1 + 1, x2 - 1, 18, z2 - 1, "minecraft:spruce_planks")
    # the gate passage: a tall round-topped arch through the whole depth, timber leaves standing open inside
    P.arched_opening(bb, "x", GX, 2, z1, 13, 15, depth=z2 - z1 + 1, trim=None, fill=AIR)
    for zz in (z1, z2):
        P.arched_opening(bb, "x", GX, 2, zz, 13, 15, depth=1, trim="minecraft:stripped_dark_oak_log[axis=y]", fill=AIR)
    for z in range(z1 + 1, z2):
        bb.fill(GX - 6, 1, z, GX + 6, 1, z, PAVE[1])
    for side in (-1, 1):
        for k in range(1, 7):   # gate leaves swung back against the passage walls
            bb.fill(GX + side * 7, 2, z1 + k, GX + side * 7, 14, z1 + k, "minecraft:dark_oak_planks")
        for yy in (4, 11):
            bb.fill(GX + side * 7, yy, z1 + 1, GX + side * 7, yy, z1 + 6, "minecraft:iron_block")
    # guard rooms either side of the passage, upstairs barracks
    for (a, c) in ((x1 + 1, GX - 9), (GX + 9, x2 - 1)):
        bb.fill(GX - 8 if a < GX else GX + 8, 2, z1 + 1, GX - 8 if a < GX else GX + 8, 17, z2 - 1, WALL[0])
        bb.set(GX - 8 if a < GX else GX + 8, 2, z1 + 4, "minecraft:spruce_door[facing=" + ("west" if a < GX else "east") + ",half=lower,hinge=left,open=false]")
        bb.set(GX - 8 if a < GX else GX + 8, 3, z1 + 4, "minecraft:spruce_door[facing=" + ("west" if a < GX else "east") + ",half=upper,hinge=left,open=false]")
    # sign board over the arch on the outer face: two lines (text added on the canvas)
    bz = z2 + 4          # in front of the eave skirt, hung from the beam ends
    bb.fill(x1 + 1, 18, bz, x2 - 1, 42, bz, "minecraft:dark_oak_planks")
    for y in (18, 42):
        bb.fill(x1 + 1, y, bz, x2 - 1, y, bz, f"{RED_BEAM}[axis=x]")
    for x in (x1 + 1, x2 - 1):
        bb.fill(x, 18, bz, x, 43, bz, RED)
        bb.set(x, 44, bz, f"{TILE_SL}[type=bottom]")
    bb.fill(x1 + 2, 43, bz, x2 - 2, 43, bz, f"{TILE_ST}[facing=north,half=bottom]")
    for x in (x1 + 4, x2 - 4, GX - 10, GX + 10):
        bb.fill(x, 18, z2 + 1, x, 18, bz - 1, f"{RED_BEAM}[axis=z]")
    framed_walls(bb, x1 + 3, 23, z1 + 1, x2 - 3, 32, z2 - 1, post_every=5, win_h=3)
    bb.fill(x1 + 4, 23, z1 + 2, x2 - 4, 23, z2 - 2, "minecraft:spruce_planks")
    pagoda_roof(bb, x1 + 3, z1 + 1, x2 - 3, z2 - 1, 34, out=3)
    flared_eave(bb, x1, z1, x2, z2, 23, out=3)
    # red lanterns either side of the arch, on brackets
    for side in (-1, 1):
        bb.set(GX + side * 10, 13, z2 + 1, f"{RED_BEAM}[axis=z]")
        bb.set(GX + side * 10, 13, z2 + 2, f"{RED_BEAM}[axis=z]")
        bb.set(GX + side * 10, 12, z2 + 2, "minecraft:iron_chain[axis=y]")
        bb.set(GX + side * 10, 11, z2 + 2, "minecraft:lantern[hanging=true]")
    # stairs inside the west guard room up to the gate's upper floor
    P.stair_run(bb, x1 + 2, 2, z1 + 2, 17, 1, "east", "minecraft:spruce_stairs")
    bb.fill(x1 + 13, 18, z1 + 2, x1 + 18, 18, z1 + 2, AIR)
    return (x1, x2, z2)


def sea_x(z):
    """x where the east sea starts at row z: right outside the wall along the north half, curving away to a beach in
    the south-east (v3: the compound now stands on the coast with the sea round two sides)."""
    return WX2 + 3 + max(0.0, z - 118) ** 2 / 30 + 2 * math.sin(z * 0.13)


def sea_and_canal(bb):
    """The sea along the north and east of the compound, and Arlong's channel: straight from the pool east through a
    big sea gate in the east wall, so the pool opens to the open sea (v3)."""
    for x in range(0, NX):
        sz = 12 + int(round(3 * math.sin(x * 0.09)))
        for z in range(0, NZ):
            inside = WX1 - 1 <= x <= WX2 + 1 and WZ1 - 1 <= z <= WZ2 + 1
            if inside:
                continue
            e = max(sz - z, x - sea_x(z))                       # how far into the sea (>0) this cell is
            if e > 0:
                d = min(9, 2 + int(e) // 2)
                bb.fill(x, -d - 1, z, x, -d - 1, z, "minecraft:sand")
                bb.fill(x, -d, z, x, 0, z, WATER)
                bb.fill(x, 1, z, x, 8, z, AIR)
            elif e > -5:
                bb.set(x, 0, z, "minecraft:sand"); bb.set(x, -1, z, "minecraft:sandstone")
    # the channel
    z1, z2 = CHAN
    x0 = POOL[0] + POOL[2] - 8
    bb.fill(x0, -8, z1 - 1, NX - 1, 0, z2 + 1, BASE[1])
    bb.fill(x0, -7, z1, NX - 1, 0, z2, WATER)
    bb.fill(x0, 1, z1, WX2 + 1, 12, z2, AIR)
    bb.fill(x0, 1, z1 - 1, WX2 - WT - 1, 1, z1 - 1, "minecraft:stone_brick_wall")
    bb.fill(x0, 1, z2 + 1, WX2 - WT - 1, 1, z2 + 1, "minecraft:stone_brick_wall")
    # the sea gate: a tall stone gate tower over the channel with a pointed arch and a raised iron portcullis
    gx1, gx2 = WX2 - WT - 2, WX2 + 3
    bb.fill(gx1, 1, z1 - 5, gx2, 26, z2 + 5, BASE[0])
    bb.mix(gx1, 1, z1 - 5, gx2, 26, z2 + 5, BASE, [0.7, 0.2, 0.1])
    P.arched_opening(bb, "z", (z1 + z2) // 2, 1, gx1, z2 - z1 + 1, 19, depth=gx2 - gx1 + 1, fill=AIR)
    bb.fill(gx1, -7, z1, gx2, 0, z2, WATER)
    for z in range(z1, z2 + 1):
        bb.fill(gx2 - 1, 15, z, gx2 - 1, 18, z, "minecraft:iron_bars")     # the portcullis, raised
    for z in (z1 - 5, z2 + 5):
        bb.fill(gx2 + 1, 1, z, gx2 + 1, 25, z, RED)
    flared_eave(bb, gx1, z1 - 5, gx2, z2 + 5, 27, out=2)
    P.hip_roof(bb, gx1, z1 - 5, gx2, z2 + 5, 28, TILE_ST)
    for z in range(z1 + 2, z2 - 1, 4):
        bb.set(gx2 + 1, 21, z, "onepiece:wall_lamp[facing=east]")


def pool(bb):
    cx, cz, rx, rz = POOL
    rim = lambda X, y, Z: ((X - cx) / (rx + 2)) ** 2 + ((Z - cz) / (rz + 2)) ** 2 <= 1
    water = lambda X, y, Z: ((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2 <= 1
    reg = (cx - rx - 3, 0, cz - rz - 3, cx + rx + 3, 0, cz + rz + 3)
    bb.fill_where(reg[0], -8, reg[2], reg[3], 0, reg[5], rim, BASE[0])
    bb.fill_where(reg[0], 0, reg[2], reg[3], 0, reg[5], lambda X, y, Z: rim(X, y, Z) & ~water(X, y, Z), "minecraft:smooth_stone_slab[type=double]")
    bb.fill_where(reg[0], -7, reg[2], reg[3], 0, reg[5], water, WATER)
    bb.fill_where(reg[0], 1, reg[2], reg[3], 1, reg[5],
                  lambda X, y, Z: rim(X, y, Z) & ~(((X - cx) / (rx + 1)) ** 2 + ((Z - cz) / (rz + 1)) ** 2 <= 1),
                  "minecraft:stone_brick_wall")
    # sea-glass lights in the pool floor
    for (dx, dz) in ((-18, 0), (0, -10), (18, 0), (0, 10), (-9, 6), (9, -6)):
        bb.set(cx + dx, -7, cz + dz, "minecraft:sea_lantern")
    # a stone landing on the pool's south rim: Arlong's deck chair under a parasol, a barrel of sake
    lx, lz = cx - 8, cz + rz + 2
    bb.fill(lx - 2, 1, lz - 1, lx + 6, 1, lz, AIR)
    bb.fill(lx - 2, 0, lz + 1, lx + 6, 0, lz + 6, "minecraft:smooth_stone")
    bb.set(lx, 1, lz + 2, "minecraft:spruce_stairs[facing=south,half=bottom]")
    bb.set(lx, 1, lz + 3, "minecraft:spruce_slab[type=bottom]")
    bb.set(lx, 1, lz + 4, "minecraft:spruce_slab[type=bottom]")
    bb.fill(lx + 2, 1, lz + 3, lx + 2, 6, lz + 3, "minecraft:spruce_fence")
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if abs(dx) + abs(dz) <= 4:
                bb.set(lx + 2 + dx, 7, lz + 3 + dz, "minecraft:white_wool" if (dx + dz) % 2 else "minecraft:light_blue_wool")
    bb.set(lx + 5, 1, lz + 2, "minecraft:barrel[facing=up]")
    bb.set(lx + 5, 1, lz + 4, "minecraft:spruce_fence"); bb.set(lx + 5, 2, lz + 4, "minecraft:white_carpet")


def palm(bb, x, z, h, lean):
    """Curving palm: onepiece palm log trunk leaning one way, a crown of drooping fronds."""
    px, pz = x, z
    for y in range(1, h + 1):
        if y > h // 3 and y % 3 == 0:
            px += lean[0]; pz += lean[1]
        bb.set(px, y, pz, "onepiece:palm_log[axis=y]")
    top = h + 1
    leaf = "onepiece:palm_leaves[distance=1,persistent=true,waterlogged=false]"
    bb.set(px, top, pz, leaf)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        for k in range(1, 6):
            yy = top - (1 if k >= 3 else 0) - (1 if k >= 5 else 0)
            bb.set(px + dx * k, yy, pz + dz * k, leaf)


def main_hall(bb, tracker):
    x1, x2, z1, z2 = HALL
    tx1, tx2, tz1, tz2 = TOWER
    bb.fill(x1 - 1, -3, z1 - 1, x2 + 1, 0, z2 + 1, BASE[0])
    framed_walls(bb, x1, 1, z1, x2, HF - 1, z2, post_every=5, win_h=3)
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:dark_oak_planks")
    bb.fill(x1 + 1, HF, z1 + 1, x2 - 1, HF, z2 - 1, "minecraft:spruce_planks")
    framed_walls(bb, x1, HF + 1, z1, x2, 2 * HF - 1, z2, post_every=5, win_h=3)
    flared_eave(bb, x1, z1, x2, z2, HF + 1, out=3)
    # roof over the wings (the tower rises out of the middle)
    bb.fill(x1 + 1, 2 * HF, z1 + 1, x2 - 1, 2 * HF, z2 - 1, "minecraft:spruce_planks")
    for (a, c) in ((x1, tx1 - 1), (tx2 + 1, x2)):
        pagoda_roof(bb, a, z1, c, z2, 2 * HF + 1, out=3)
    # veranda: red columns along the courtyard face under a lean-to of tiles
    vz = z2 + 6
    bb.fill(x1, 0, z2 + 1, x2, 0, vz, PAVE[1])
    for x in range(x1, x2 + 1, 5):
        bb.fill(x, 1, vz, x, HF - 1, vz, RED)
        bb.set(x, 0, vz, "minecraft:chiseled_stone_bricks")
    bb.fill(x1 - 1, HF, z2 + 1, x2 + 1, HF, vz + 1, TILE)
    bb.fill(x1 - 1, HF, vz + 1, x2 + 1, HF, vz + 1, f"{TILE_ST}[facing=north,half=bottom]")
    bb.fill(x1, HF - 1, vz, x2, HF - 1, vz, f"{RED_BEAM}[axis=x]")
    for x in range(x1 + 7, x2, 10):
        bb.set(x, HF - 2, vz - 1, "minecraft:lantern[hanging=true]")
    # doors from the veranda: a grand opening in the middle, side doors
    bb.fill(GX - 2, 1, z2, GX + 2, 5, z2, AIR)
    for x in (55, 125):
        bb.set(x, 1, z2, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left,open=false]")
        bb.set(x, 2, z2, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left,open=false]")
    # inside: Arlong's great room in the middle (throne on a dais, long feast table, banners), barracks in the wings
    rooms = []
    bb.fill(tx1 - 1, 1, z1 + 1, tx1 - 1, HF - 1, z2 - 1, WALL[0]); bb.fill(tx2 + 1, 1, z1 + 1, tx2 + 1, HF - 1, z2 - 1, WALL[0])
    for x in (tx1 - 1, tx2 + 1):
        bb.fill(x, 1, z2 - 6, x, 3, z2 - 5, AIR)
    bb.fill(GX - 5, 1, z1 + 1, GX + 5, 1, z1 + 4, "minecraft:dark_oak_planks")        # dais
    bb.fill(GX - 6, 1, z1 + 5, GX + 6, 1, z1 + 5, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
    bb.set(GX, 2, z1 + 3, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
    bb.set(GX - 1, 2, z1 + 3, "minecraft:dark_oak_slab[type=top]"); bb.set(GX + 1, 2, z1 + 3, "minecraft:dark_oak_slab[type=top]")
    bb.fill(GX - 1, 3, z1 + 2, GX + 1, 4, z1 + 2, "minecraft:dark_oak_planks")
    bb.fill(GX - 7, 2, z1 + 1, GX + 7, 6, z1 + 1, "minecraft:light_blue_wool")
    bb.fill(GX - 3, 3, z1 + 1, GX + 3, 5, z1 + 1, "minecraft:black_wool")
    for x in range(GX - 8, GX + 9):
        bb.set(x, 1, z1 + 12, "minecraft:dark_oak_fence")
        bb.set(x, 2, z1 + 12, "minecraft:white_carpet")
    for x in range(GX - 8, GX + 9, 2):
        bb.set(x, 1, z1 + 11, "minecraft:spruce_stairs[facing=south,half=bottom]")
        bb.set(x, 1, z1 + 13, "minecraft:spruce_stairs[facing=north,half=bottom]")
    bb.fill(GX - 2, 1, z1 + 17, GX + 2, 1, z2 - 2, "minecraft:red_carpet")
    for (a, c, kind) in ((x1 + 1, tx1 - 2, "bedroom"), (tx2 + 2, x2 - 1, "storage")):
        for fl, fy in enumerate((1, HF + 1)):
            rms, doors = P.bsp_rooms(bb, a, z1 + 1, c, z2 - 1, fy, HF - 1, WALL[0], min_room=7, seed=a + fl, max_room=14)
            for i, rm in enumerate(rms):
                k = (kind if i % 2 == 0 else "living") if fl == 0 else ("bedroom" if i % 2 == 0 else "workshop")
                P.furnish_room(bb, rm, fy, kind=k, height=HF - 1, seed=a + 50 * fl + i, doors=doors,
                               wood="spruce", tracker=tracker)
                rooms.append((rm, fy, HF - 1))
    # wing stairs up to the upper floor, along the tower wall
    for sx in (tx1 - 3, tx2 + 2):
        bb.fill(sx, 1, z2 - 9, sx + 1, HF - 1, z2 - 1, AIR)
        P.stair_run(bb, sx, 1, z2 - 2, HF, 2, "north", "minecraft:spruce_stairs")
        bb.fill(sx, HF, z2 - 8, sx + 1, HF, z2 - 5, AIR)
        bb.fill(sx, HF + 1, z2 - 10, sx + 1, HF + 2, z2 - 9, AIR)
    return rooms


def tower(bb, tracker):
    """Pagoda tower on the hall: seven storeys above the hall's two, each a little narrower, each with a flared eave;
    a square stair core in the north-west corner climbs all of it. Top = Nami's map room."""
    tx1, tx2, tz1, tz2 = TOWER
    rooms = []
    x1, x2, z1, z2 = tx1, tx2, tz1, tz2
    framed_walls(bb, x1, HF + 1, z1, x2, 2 * HF - 1, z2, post_every=5, win_h=3)
    kinds = ["workshop", "storage", "living", "library", "bedroom", "bedroom", "library"]
    y = 2 * HF
    for lv in range(LEVELS):
        inset = lv
        a1, a2, b1, b2 = x1 + inset, x2 - inset, z1 + inset, z2 - inset
        bb.fill(a1, y, b1, a2, y, b2, "minecraft:spruce_planks")
        framed_walls(bb, a1, y + 1, b1, a2, y + LEVEL - 1, b2, post_every=5, win_h=3)
        flared_eave(bb, a1, b1, a2, b2, y, out=2)
        if lv < LEVELS - 1:
            P.square_spiral_stair(bb, a1 + 1, y + 1, b1 + 1, 5, y + LEVEL, "minecraft:spruce_stairs", headroom=3)
        room = (a1 + 7, b1 + 1, a2 - 1, b2 - 1)
        if lv < 3:                                   # the wide lower storeys are split into several rooms
            rms, doors = P.bsp_rooms(bb, *room, y + 1, LEVEL - 1, WALL[0], min_room=7, seed=900 + lv, max_room=13)
            doors = list(doors) + [(a1 + 6, b1 + 2)]
        else:
            rms, doors = [room], [(a1 + 6, b1 + 2)]
        for i, rm in enumerate(rms):
            k = kinds[lv] if i == 0 else ["storage", "bedroom", "living"][i % 3]
            P.furnish_room(bb, rm, y + 1, kind=k, height=LEVEL - 1, seed=900 + 10 * lv + i, wood="spruce",
                           tracker=tracker, doors=doors)
            rooms.append((rm, y + 1, LEVEL - 1))
        y += LEVEL
    # the spirals below the first tower floor: great room -> hall upper floor -> tower
    P.square_spiral_stair(bb, x1 + 1, HF + 1, z1 + 1, 5, 2 * HF, "minecraft:spruce_stairs", headroom=3)
    bb.fill(x1 + 1, HF, z1 + 1, x1 + 5, HF, z1 + 5, AIR)
    P.square_spiral_stair(bb, x1 + 1, 1, z1 + 1, 5, HF, "minecraft:spruce_stairs", headroom=3)
    # roof and spire
    a1, a2, b1, b2 = x1 + LEVELS, x2 - LEVELS, z1 + LEVELS, z2 - LEVELS
    top = pagoda_roof(bb, a1, b1, a2, b2, y, out=2)
    sx, sz = int((a1 + a2) / 2), int((b1 + b2) / 2)
    bb.fill(sx, top, sz, sx, top + 8, sz, "minecraft:gold_block")
    for dy in (2, 5):
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(sx + dx, top + dy, sz + dz, "minecraft:gold_block") if dy == 2 else bb.set(sx + dx, top + dy, sz + dz, f"{TILE_SL}[type=bottom]")
    # Nami's map room at the top storey: drafting tables, charts on the walls, a globe
    ty = y - LEVEL + 1
    t1, t2, u1, u2 = x1 + LEVELS - 1, x2 - LEVELS + 1, z1 + LEVELS - 1, z2 - LEVELS + 1
    bb.set(t1 + 8, ty, u1 + 3, "minecraft:cartography_table")
    bb.set(t1 + 11, ty, u1 + 2, "minecraft:chiseled_bookshelf[facing=south]")
    bb.set(t1 + 12, ty, u1 + 3, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    bb.fill(t2 - 1, ty, u1 + 2, t2 - 1, ty + 2, u2 - 2, "minecraft:bookshelf")
    bb.set(t1 + 9, ty, u2 - 2, "minecraft:spruce_fence"); bb.set(t1 + 9, ty + 1, u2 - 2, "minecraft:light_blue_stained_glass")
    return rooms, top, (sx, sz), ty, (t1, u1)


def side_barracks(bb, tracker):
    rooms = []
    for (x1, x2) in ((WX1 + WT + 2, WX1 + WT + 18), (WX2 - WT - 18, WX2 - WT - 2)):
        z1, z2 = 114, 150
        bb.fill(x1 - 1, -3, z1 - 1, x2 + 1, 0, z2 + 1, BASE[0])
        framed_walls(bb, x1, 1, z1, x2, 7, z2, post_every=5, win_h=3)
        bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:spruce_planks")
        bb.fill(x1 + 1, 8, z1 + 1, x2 - 1, 8, z2 - 1, "minecraft:spruce_planks")
        pagoda_roof(bb, x1, z1, x2, z2, 9, out=3)
        face = x2 if x1 < GX else x1
        f = "east" if x1 < GX else "west"
        for z in (120, 132, 144):
            bb.set(face, 1, z, f"minecraft:spruce_door[facing={f},half=lower,hinge=left,open=false]")
            bb.set(face, 2, z, f"minecraft:spruce_door[facing={f},half=upper,hinge=left,open=false]")
            bb.set(face + (1 if x1 < GX else -1), 3, z + 1, f"onepiece:wall_lamp[facing={f}]")
        rms, doors = P.bsp_rooms(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, 1, 7, WALL[0], min_room=6, seed=x1, max_room=12)
        doors = list(doors) + [(face, z) for z in (120, 132, 144)]
        for i, rm in enumerate(rms):
            P.furnish_room(bb, rm, 1, kind=["bedroom", "storage", "kitchen", "bedroom"][i % 4], height=7, seed=x1 + i,
                           doors=doors, wood="spruce", tracker=tracker)
            rooms.append((rm, 1, 7))
    return rooms


def courtyard_decor(bb, rng):
    """Training yard with straw dummies and targets, crate stacks, a landing stage on the canal with a boat, palms,
    barrels and cannons."""
    # training yard in front of the west barracks
    tx, tz = 42, 125
    bb.fill(tx, 0, tz, tx + 14, 0, tz + 18, "minecraft:coarse_dirt")
    for (x, z) in ((tx + 3, tz + 3), (tx + 8, tz + 3), (tx + 3, tz + 9), (tx + 8, tz + 9)):
        bb.set(x, 1, z, "minecraft:spruce_fence"); bb.set(x, 2, z, "minecraft:hay_block[axis=y]")
        bb.set(x, 3, z, "minecraft:carved_pumpkin[facing=south]")
    for z in (tz + 14, tz + 16):
        bb.set(tx + 12, 1, z, "minecraft:target"); bb.set(tx + 12, 2, z, "minecraft:target")
    for x in range(tx, tx + 15):
        for z in (tz - 1, tz + 19):
            if x % 3 == 0:
                bb.set(x, 1, z, "minecraft:spruce_fence")
    # crate stacks by the east barracks and the canal
    for (x, z, h) in ((132, 118, 2), (133, 118, 1), (132, 119, 1), (140, 130, 2), (141, 130, 2), (140, 131, 1)):
        bb.fill(x, 1, z, x, h, z, "minecraft:barrel[facing=up]" if (x + z) % 2 else "minecraft:spruce_planks")
    # landing stage on the canal with a little boat
    z1, z2 = CHAN
    bb.fill(132, 0, z1 - 5, 142, 0, z1 - 2, "minecraft:spruce_planks")
    bb.fill(132, 0, z1, 142, 0, z1 + 1, "minecraft:spruce_planks")            # the jetty out over the water
    for x in range(132, 143, 5):
        bb.set(x, 1, z1 + 1, "minecraft:spruce_fence"); bb.fill(x, -6, z1 + 1, x, -1, z1 + 1, "minecraft:spruce_log")
    bz = z1 + 7
    for dx in range(-5, 6):                                                  # a little boat moored at the jetty
        w = 1 if abs(dx) < 5 else 0
        bb.fill(136 + dx, 0, bz - w - 1, 136 + dx, 0, bz + w + 1, "minecraft:dark_oak_planks")
        if abs(dx) < 5:
            bb.fill(136 + dx, 0, bz - w, 136 + dx, 0, bz + w, WATER)
        bb.fill(136 + dx, -1, bz - w, 136 + dx, -1, bz + w, "minecraft:dark_oak_planks")
    # palms
    for (px, pz, lean) in ((50, 152, (1, 0)), (66, 150, (0, -1)), (114, 150, (-1, 0)), (130, 152, (0, -1)),
                           (30, 92, (1, 1)), (138, 90, (-1, 1)), (30, 74, (1, 0)), (124, 80, (-1, 0))):
        palm(bb, px, pz, int(rng.integers(11, 16)), lean)
    for (x, z) in ((45, 96), (46, 96), (132, 120), (60, 144), (117, 144), (56, 78), (57, 78)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up]")
    for (x, z) in ((66, 152), (114, 152), (40, 80), (140, 80)):
        bb.set(x, 1, z, "onepiece:cannon[facing=south]")


def design():
    bb = BigBuild(seed=31, y_min=-12, y_max=120)
    tracker = P.PropTracker(31)
    rng = np.random.default_rng(31)
    # ground: grass outside, paved courtyard inside
    bb.fill(0, -4, 0, NX - 1, -1, NZ - 1, "minecraft:dirt")
    bb.fill(0, 0, 0, NX - 1, 0, NZ - 1, "minecraft:grass_block[snowy=false]")
    bb.fill(WX1 + WT, 0, WZ1 + WT, WX2 - WT, 0, WZ2 - WT, PAVE[0])
    # gate road out to the south
    for z in range(WZ2, NZ):
        for x in range(GX - 6, GX + 7):
            bb.set(x, 0, z, "minecraft:dirt_path" if (x + z) % 4 else "minecraft:coarse_dirt")
    sea_and_canal(bb)
    outer_wall(bb)
    rooms = []
    rooms += main_hall(bb, tracker)
    trooms, top, (sx, sz), ty, (t1, u1) = tower(bb, tracker)
    rooms += trooms
    rooms += side_barracks(bb, tracker)
    for (cx, cz) in ((WX1 + 1, WZ1 + 1), (WX2 - 1, WZ1 + 1), (WX1 + 1, WZ2 - 1), (WX2 - 1, WZ2 - 1)):
        corner_tower(bb, cx, cz, tracker, rooms)
    gx1, gx2, gz = gatehouse(bb)
    pool(bb)
    # the canal runs through the paving; re-carve so nothing paved over it
    z1, z2 = CHAN
    bb.fill(POOL[0] + POOL[2] - 6, -7, z1, WX2 - WT - 3, 0, z2, WATER)
    bb.fill(POOL[0] + POOL[2] - 6, 1, z1, WX2 - WT - 3, 1, z2, AIR)
    # two humped bridges over the channel
    for bx in (126, 146):
        for z in range(z1 - 1, z2 + 2):
            up = 1 + min(z - z1 + 1, z2 + 1 - z, 3) // 2
            bb.fill(bx - 2, up, z, bx + 2, up, z, "minecraft:stone_bricks")
            bb.set(bx - 3, up + 1, z, "minecraft:stone_brick_wall"); bb.set(bx + 3, up + 1, z, "minecraft:stone_brick_wall")
    courtyard_decor(bb, rng)
    audit = []
    for rm, yy, hh in rooms:
        txt, ok = P.audit_props(bb, [rm], yy, hh)
        if not ok:
            audit.append(txt)
    return bb, audit, (gx1, gx2, gz), (sx, top + 9, sz), ty, (t1, u1)


def build():
    bb, audit, (gx1, gx2, gz), (fx, fy, fz), ty, (t1, u1) = design()
    for a in audit:
        print("audit:", a)
    b = to_canvas(bb)
    # ARLONG / PARK on the gate board, double-size letters, reading from the south
    bz = gz + 5
    b.text(GX - 23, 31, bz, "ARLONG", "minecraft:white_concrete", axis="x", step=1, scale=2)
    b.text(GX - 15, 20, bz, "PARK", "minecraft:white_concrete", axis="x", step=1, scale=2)
    b.flag(fx, fy, fz, h=10, colors=("minecraft:black_wool", "minecraft:light_blue_wool"))
    b.chest(t1 + 14, ty, u1 + 3, "pirate", "south")
    b.guards("fishman", ((GX - 12, WZ2 - 14), (GX + 12, WZ2 - 14), (90, 75), (45, 105), (135, 108), (84, 138)))
    return b, 0
