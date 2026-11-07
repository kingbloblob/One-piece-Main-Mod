"""The Kozuki samurai manor of Wano v2 (Oden's family estate in Kuri), redesigned with the Minecraft Builder skill.

Green Kuri hills with pine and bamboo, rice paddies in the lowland to the west, rocky shores fading to the sea. On a
stone-faced terrace the estate: a white plastered wall under a tiled coping, a two-storey tiled gatehouse on the south.
Inside, the great main house: dark posts and white plaster, a veranda (engawa) running all round under deep tiled
eaves, a smaller upper storey and a big tiled gable roof; tatami rooms on both floors (audience hall with Oden's
seat, sword room, study, bedrooms, kitchen). East of the garden the dojo with training posts and weapon racks; west the
white storehouse (kura) and a little shrine with a red torii; the bell tower in the north-east corner; and the garden
of sakura, stone lanterns, raked gravel paths and a koi pond crossed by a red bridge. 160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, castle_eave, wing_floor, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "wano_house"
TITLE = "Wano Samurai House"
CUTS = [11, 18]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
SHORE = NT.outline(88, 84, 80, 2320, wobble=0.07)
EY = 8                                     # estate terrace level
EST = (40, 34, 132, 124)                   # inside the wall
TILE = "minecraft:deepslate_tile_stairs"
TILEF = "minecraft:deepslate_tiles"
PADDY = (8, 36, 32, 120)
HOUSE = (58, 42, 114, 72)
GATE_X = 86

MEADOW = [("minecraft:grass_block", 0.62), ("minecraft:podzol", 0.08), ("minecraft:moss_block", 0.1), ("minecraft:coarse_dirt", 0.08),
          ("minecraft:rooted_dirt", 0.06), ("minecraft:dirt", 0.06)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.1), ("minecraft:cobblestone", 0.15),
        ("minecraft:mossy_cobblestone", 0.15)]
SAND = [("minecraft:sand", 0.6), ("minecraft:clay", 0.2), ("minecraft:sandstone", 0.2)]
YARD = [("minecraft:packed_mud", 0.25), ("minecraft:dirt_path", 0.3), ("minecraft:coarse_dirt", 0.15), ("minecraft:mud_bricks", 0.1),
        ("minecraft:rooted_dirt", 0.2)]
WALLS = ["minecraft:white_concrete", "minecraft:white_terracotta", "minecraft:calcite"]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 5 + NT.fbm(X, Z, 2322, 26) * 16 - 4
    h = h * np.clip((d - 1.5) / 10.0, 0, 1)
    e = rect_d(X, Z, (EST[0] - 3, EST[1] - 3, EST[2] + 3, EST[3] + 3))
    h = np.where(e <= 0, EY, np.where(e < 14, EY * (1 - e / 14) + h * (e / 14), h))
    p = rect_d(X, Z, PADDY)
    h = np.where(p <= 0, 2, np.where(p < 6, 2 * (1 - p / 6) + h * (p / 6), h))
    road = (np.abs(X - GATE_X) <= 2) & (Z > EST[3])
    h = np.where(road & (d > 3), np.maximum(np.minimum(h, EY - (Z - EST[3] - 3) / 3.0), 1), h)
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None]
    Z = np.arange(N)[None, :]
    H = _height(X, Z).astype(int)
    g = np.zeros_like(H)
    for a, b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))),
                 ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
        dd = np.abs(H[a] - H[b])
        g[a] = np.maximum(g[a], dd); g[b] = np.maximum(g[b], dd)
    return H, g


HMAP, GRAD = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def steep(X, Z):
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 2


def land(X, Z):
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2331, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2332, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, MEADOW, 2333, mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z),
             core="minecraft:stone")
    for y in range(-12, 1):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > -2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)),
                      "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                      "minecraft:sand" if y < -3 else "minecraft:gravel")
    # stone-faced terrace edge round the estate
    x1, z1, x2, z2 = EST[0] - 3, EST[1] - 3, EST[2] + 3, EST[3] + 3
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                bb.fill(x, -2, z, x, EY, z, ("minecraft:stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:cobblestone")[(x * 3 + z) % 3])
    bb.fill(EST[0] - 2, EY, EST[1] - 2, EST[2] + 2, EY, EST[3] + 2, "minecraft:grass_block")
    NT.cover(bb, EST[0] - 2, EST[1] - 2, EST[2] + 2, EST[3] + 2, lambda X, Z: X * 0 + EY,
             [("minecraft:grass_block", 0.8), ("minecraft:moss_block", 0.12), ("minecraft:podzol", 0.08)], 2334)


def paddies(bb):
    """Terraced rice paddies: shallow water squares between grassy bunds, rice (wheat) on farmland strips."""
    x1, z1, x2, z2 = PADDY
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not land(np.array([[x]]), np.array([[z]]))[0, 0] or SHORE(np.array([[x]]), np.array([[z]]))[0, 0] < 4:
                continue
            bund = (x - x1) % 8 == 0 or (z - z1) % 9 == 0
            if bund:
                bb.set(x, 2, z, "minecraft:grass_block")
                bb.set(x, 3, z, AIR)
            elif (x - x1) % 8 == 4:
                bb.set(x, 2, z, "minecraft:water")
                bb.set(x, 1, z, "minecraft:mud")
                bb.set(x, 3, z, AIR)
            else:
                bb.set(x, 2, z, "minecraft:farmland[moisture=7]")
                bb.set(x, 3, z, "minecraft:wheat[age=%d]" % (5 + (x * 7 + z) % 3))
    # a farmer's hut on the edge
    x, z = x2 + 3, z1 + 30
    y = hy(x, z)
    bb.fill(x, y, z, x + 5, y, z + 5, "minecraft:spruce_planks")
    bb.fill(x, y + 1, z, x + 5, y + 3, z + 5, "minecraft:stripped_spruce_wood")
    bb.fill(x + 1, y + 1, z + 1, x + 4, y + 3, z + 4, AIR)
    bb.fill(x + 2, y + 1, z, x + 2, y + 2, z, AIR)
    P.gable_roof(bb, x - 1, z - 1, x + 6, z + 6, y + 4, "minecraft:spruce_stairs", gable_fill="minecraft:hay_block", overhang=0)
    bb.set(x + 4, y + 1, z + 4, "minecraft:composter"); bb.set(x + 1, y + 1, z + 4, "minecraft:barrel[facing=up,open=false]")
    return (x - 2, z - 2, x + 8, z + 8)


def estate_wall(bb):
    """White plaster wall with a tiled coping round the estate, a two-storey gatehouse on the south, a back gate."""
    x1, z1, x2, z2 = EST[0] - 1, EST[1] - 1, EST[2] + 1, EST[3] + 1
    y = EY
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                bb.fill(x, y + 1, z, x, y + 1, z, "minecraft:stone_bricks")
                bb.fill(x, y + 2, z, x, y + 4, z, WALLS[(x * 5 + z * 3) % 3] if (x + z) % 9 else "minecraft:dark_oak_log[axis=y]")
                bb.set(x, y + 5, z, TILEF)
    for x in range(x1, x2 + 1):
        bb.set(x, y + 5, z1 - 1, st(TILE, "south")); bb.set(x, y + 5, z2 + 1, st(TILE, "north"))
    for z in range(z1, z2 + 1):
        bb.set(x1 - 1, y + 5, z, st(TILE, "east")); bb.set(x2 + 1, y + 5, z, st(TILE, "west"))
    # gatehouse
    gx = GATE_X
    gz = z2
    bb.fill(gx - 7, y + 1, gz - 3, gx + 7, y + 7, gz + 3, "minecraft:white_concrete")
    bb.fill(gx - 6, y + 1, gz - 2, gx + 6, y + 6, gz + 2, AIR)
    bb.fill(gx - 7, y, gz - 3, gx + 7, y, gz + 3, "minecraft:stone_bricks")
    for (a, b) in ((gx - 7, gz - 3), (gx + 7, gz - 3), (gx - 7, gz + 3), (gx + 7, gz + 3), (gx - 3, gz + 3), (gx + 3, gz + 3),
                   (gx - 3, gz - 3), (gx + 3, gz - 3)):
        bb.fill(a, y + 1, b, a, y + 7, b, "minecraft:dark_oak_log[axis=y]")
    bb.fill(gx - 2, y + 1, gz - 3, gx + 2, y + 5, gz + 3, AIR)
    bb.fill(gx - 2, y + 1, gz - 2, gx + 2, y + 5, gz + 2, AIR)
    bb.fill(gx - 3, y + 6, gz - 3, gx + 3, y + 6, gz + 3, "minecraft:dark_oak_planks")
    for x in range(gx - 2, gx + 3):
        bb.set(x, y + 1, gz, "minecraft:dark_oak_planks") if False else None
    bb.set(gx - 2, y + 1, gz + 2, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left,open=true]")
    bb.set(gx - 2, y + 2, gz + 2, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left,open=true]")
    bb.set(gx + 2, y + 1, gz + 2, "minecraft:dark_oak_door[facing=south,half=lower,hinge=right,open=true]")
    bb.set(gx + 2, y + 2, gz + 2, "minecraft:dark_oak_door[facing=south,half=upper,hinge=right,open=true]")
    # upper storey: a watch room with lattice windows
    bb.fill(gx - 6, y + 7, gz - 2, gx + 6, y + 10, gz + 2, "minecraft:white_concrete")
    bb.fill(gx - 5, y + 7, gz - 1, gx + 5, y + 10, gz + 1, AIR)
    bb.fill(gx - 6, y + 6, gz - 2, gx + 6, y + 6, gz + 2, "minecraft:dark_oak_planks")
    for x in range(gx - 5, gx + 6):
        if x % 2:
            bb.set(x, y + 8, gz + 2, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]")
            bb.set(x, y + 8, gz - 2, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=true]")
    for (a, b) in ((gx - 6, gz - 2), (gx + 6, gz - 2), (gx - 6, gz + 2), (gx + 6, gz + 2)):
        bb.fill(a, y + 7, b, a, y + 10, b, "minecraft:dark_oak_log[axis=y]")
    castle_eave(bb, gx - 7, gz - 3, gx + 7, gz + 3, y + 6, TILE, TILEF, depth=1, bracket="minecraft:dark_oak_stairs")
    P.gable_roof(bb, gx - 7, gz - 3, gx + 7, gz + 3, y + 11, TILE, gable_fill="minecraft:white_concrete", overhang=1)
    bb.fill(gx - 6, y + 1, gz - 2, gx - 6, y + 7, gz - 2, AIR) if False else None
    bb.fill(gx + 5, y + 1, gz - 1, gx + 5, y + 7, gz - 1, "minecraft:ladder[facing=west]")
    bb.fill(gx + 5, y + 6, gz - 1, gx + 5, y + 6, gz - 1, "minecraft:ladder[facing=west]")
    for x in (gx - 5, gx + 5):
        bb.set(x, y + 5, gz + 4, "minecraft:lantern[hanging=true]") if False else None
    for x in (gx - 4, gx + 4):
        bb.set(x, y + 4, gz + 4, "minecraft:lantern[hanging=false]") if False else None
    # Kozuki crest banners either side of the gate
    for x in (gx - 4, gx + 4):
        bb.set(x, y + 4, gz + 4, "minecraft:black_wall_banner[facing=south]")
    # the back gate on the north
    bb.fill(GATE_X - 1, y + 1, z1, GATE_X + 1, y + 3, z1, AIR)
    return (gx - 9, gz - 5, gx + 9, gz + 5)


def main_house(bb, tracker, audit):
    """The great house: stone plinth, engawa round it under deep eaves, two storeys of posts and white plaster with
    paper-screen windows, rooms on both floors, a big tiled gable roof."""
    x1, z1, x2, z2 = HOUSE
    y0 = EY + 1
    FH = 6
    bb.fill(x1 - 3, EY, z1 - 3, x2 + 3, y0, z2 + 3, "minecraft:stone_bricks")
    bb.fill(x1 - 2, y0, z1 - 2, x2 + 2, y0, z2 + 2, "minecraft:dark_oak_planks")      # the engawa
    for x in range(x1 - 3, x2 + 4, 4):
        bb.set(x, y0, z2 + 4, st("minecraft:stone_brick_stairs", "south")) if False else None
    for x in range(GATE_X - 2, GATE_X + 3):
        bb.set(x, y0, z2 + 3, st("minecraft:stone_brick_stairs", "south"))
    # ground floor
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:spruce_planks")
    bb.mix(x1, y0 + 1, z1, x2, y0 + FH - 1, z2, WALLS, [0.75, 0.15, 0.1])
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + FH - 1, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, y0 + FH, z, "minecraft:dark_oak_log[axis=y]")
            bb.fill(x, y0 + 1, z + (2 if z == z2 else -2), x, y0 + FH - 1, z + (2 if z == z2 else -2), "minecraft:dark_oak_fence")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, y0 + FH, z, "minecraft:dark_oak_log[axis=y]")
            bb.fill(x + (2 if x == x2 else -2), y0 + 1, z, x + (2 if x == x2 else -2), y0 + FH - 1, z, "minecraft:dark_oak_fence")
    bb.fill(x1, y0 + FH - 1, z1, x2, y0 + FH - 1, z1, "minecraft:dark_oak_planks"); bb.fill(x1, y0 + FH - 1, z2, x2, y0 + FH - 1, z2, "minecraft:dark_oak_planks")
    bb.fill(x1, y0 + FH - 1, z1, x1, y0 + FH - 1, z2, "minecraft:dark_oak_planks"); bb.fill(x2, y0 + FH - 1, z1, x2, y0 + FH - 1, z2, "minecraft:dark_oak_planks")
    # shoji windows (white panes, sliding-screen look) all round
    for x in range(x1 + 1, x2):
        if (x - x1) % 4:
            for z in (z1, z2):
                bb.fill(x, y0 + 2, z, x, y0 + 3, z, "minecraft:white_stained_glass_pane")
    for z in range(z1 + 1, z2):
        if (z - z1) % 4:
            for x in (x1, x2):
                bb.fill(x, y0 + 2, z, x, y0 + 3, z, "minecraft:white_stained_glass_pane")
    # entrance (genkan) in the middle of the south front
    cx = GATE_X
    bb.fill(cx - 1, y0 + 1, z2, cx + 1, y0 + 3, z2, AIR)
    bb.set(cx - 2, y0 + 3, z2 + 1, "minecraft:lantern[hanging=false]") if False else None
    # the deep eave over the engawa
    castle_eave(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + FH - 1, TILE, TILEF, depth=2, bracket="minecraft:dark_oak_stairs")
    bb.fill(x1 - 1, y0 + FH, z1 - 1, x2 + 1, y0 + FH, z2 + 1, "minecraft:dark_oak_planks")
    # interior: the audience hall in the middle (open to the entrance), wings either side
    hall = (cx - 9, z1 + 1, cx + 9, z2 - 1)
    keep = [hall, (x1 + 1, z1 + 1, x1 + 3, z1 + 3)]
    wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + 1, FH - 2, "minecraft:white_concrete", 2341, tracker,
               ["kitchen", "bedroom", "storage", "dining", "library", "bedroom"], corridor="x", cw=3, keep=keep, wood="spruce",
               audit=audit, lamp="minecraft:lantern[hanging=true]")
    hx1, hz1, hx2, hz2 = hall
    for x in (hx1 - 1, hx2 + 1):
        bb.fill(x, y0 + 1, hz1, x, y0 + FH - 2, hz2, "minecraft:white_concrete")
        for z in range(hz1, hz2 + 1, 4):
            bb.fill(x, y0 + 1, z, x, y0 + FH - 2, z, "minecraft:dark_oak_log[axis=y]")
        bb.fill(x, y0 + 1, (hz1 + hz2) // 2, x, y0 + 2, (hz1 + hz2) // 2 + 1, AIR)
    bb.fill(hx1, y0, hz1, hx2, y0, hz2, "minecraft:spruce_planks")
    bb.fill_where(hx1 + 1, y0 + 1, hz1 + 1, hx2 - 1, y0 + 1, hz2 - 3, lambda X, yy, Z: ((X - hx1) // 2 + (Z - hz1) // 2) % 2 == 0,
                  "minecraft:lime_carpet")
    bb.fill_where(hx1 + 1, y0 + 1, hz1 + 1, hx2 - 1, y0 + 1, hz2 - 3, lambda X, yy, Z: ((X - hx1) // 2 + (Z - hz1) // 2) % 2 == 1,
                  "minecraft:green_carpet")
    # Oden's seat on a dais at the back, a folding screen behind, the Kozuki crest
    bb.fill(cx - 3, y0 + 1, hz1, cx + 3, y0 + 1, hz1 + 2, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(cx, y0 + 2, hz1 + 1, st("minecraft:dark_oak_stairs", "south"))
    bb.set(cx - 1, y0 + 2, hz1 + 1, "minecraft:red_carpet"); bb.set(cx + 1, y0 + 2, hz1 + 1, "minecraft:red_carpet")
    bb.fill(cx - 4, y0 + 1, z1 + 1, cx + 4, y0 + 4, z1 + 1, "minecraft:yellow_terracotta")
    bb.set(cx, y0 + 3, z1 + 2, "minecraft:item_frame[facing=south]") if False else None
    for x in (cx - 2, cx + 2):
        bb.set(x, y0 + 3, z1 + 2, "minecraft:black_wall_banner[facing=south]")
    for x in (hx1 + 1, hx2 - 1):
        for z in range(hz1 + 4, hz2 - 2, 3):
            bb.set(x, y0 + 1, z, "minecraft:lantern[hanging=false]") if False else bb.set(x, y0 + 1, z, "minecraft:red_carpet")
    for z in range(hz1 + 3, hz2 - 1, 4):
        bb.set(cx, y0 + FH - 2, z, "minecraft:lantern[hanging=true]")
    # sword racks (armor-like rows of tripwire hooks) on the hall side walls
    for z in range(hz1 + 3, hz2 - 2, 2):
        bb.set(hx1, y0 + 3, z, "minecraft:tripwire_hook[attached=false,facing=east,powered=false]")
        bb.set(hx2, y0 + 3, z, "minecraft:tripwire_hook[attached=false,facing=west,powered=false]")
    # upper storey: smaller, set back on the ground-floor roof
    u1, w1, u2, w2 = x1 + 6, z1 + 4, x2 - 6, z2 - 4
    ya = y0 + FH
    bb.fill(u1, ya, w1, u2, ya, w2, "minecraft:spruce_planks")
    bb.mix(u1, ya + 1, w1, u2, ya + FH - 1, w2, WALLS, [0.75, 0.15, 0.1])
    bb.fill(u1 + 1, ya + 1, w1 + 1, u2 - 1, ya + FH - 1, w2 - 1, AIR)
    for x in range(u1, u2 + 1, 4):
        for z in (w1, w2):
            bb.fill(x, ya + 1, z, x, ya + FH - 1, z, "minecraft:dark_oak_log[axis=y]")
    for z in range(w1, w2 + 1, 4):
        for x in (u1, u2):
            bb.fill(x, ya + 1, z, x, ya + FH - 1, z, "minecraft:dark_oak_log[axis=y]")
    for x in range(u1 + 1, u2):
        if (x - u1) % 4:
            bb.fill(x, ya + 2, w1, x, ya + 3, w1, "minecraft:white_stained_glass_pane")
            bb.fill(x, ya + 2, w2, x, ya + 3, w2, "minecraft:white_stained_glass_pane")
    for z in range(w1 + 1, w2):
        if (z - w1) % 4:
            bb.fill(u1, ya + 2, z, u1, ya + 3, z, "minecraft:white_stained_glass_pane")
            bb.fill(u2, ya + 2, z, u2, ya + 3, z, "minecraft:white_stained_glass_pane")
    wing_floor(bb, u1 + 1, w1 + 1, u2 - 1, w2 - 1, ya + 1, FH - 2, "minecraft:white_concrete", 2342, tracker,
               ["bedroom", "library", "bedroom", "living", "storage"], corridor="x", cw=3, keep=[(u1 + 1, w1 + 1, u1 + 3, w1 + 3)],
               wood="dark_oak", audit=audit)
    # stairs: a ladder in the north-west corner of each floor
    bb.fill(x1 + 2, y0 + 1, z1 + 1, x1 + 2, ya, z1 + 1, AIR)
    bb.fill(u1 + 1, y0 + 1, w1 + 1, u1 + 1, ya + 1, w1 + 1, AIR)
    bb.fill(u1 + 1, y0 + 1, w1 + 1, u1 + 1, ya, w1 + 1, "minecraft:ladder[facing=south]")
    P.gable_roof(bb, u1 - 1, w1 - 1, u2 + 1, w2 + 1, ya + FH, TILE, gable_fill="minecraft:white_concrete", overhang=1)
    # roof ridge ends: little onigawara (blackstone) and a gold crest
    for (a) in (u1 - 1, u2 + 1):
        bb.set(a, ya + FH + (w2 - w1 + 2) // 2 + 1, (w1 + w2) // 2, "minecraft:polished_blackstone") if False else None
    # lanterns hung under the eave along the engawa
    for x in range(x1, x2 + 1, 8):
        bb.set(x, y0 + FH - 1, z2 + 2, "minecraft:lantern[hanging=true]") if bb.names[bb.get_region(x, y0 + FH - 1, z2 + 2, x, y0 + FH - 1, z2 + 2)[0, 0, 0]] in ("minecraft:air", "", None) else None
    return (x1 - 4, z1 - 4, x2 + 4, z2 + 5)


def dojo(bb, tracker, audit):
    x1, z1, x2, z2 = 98, 82, 126, 106
    y0 = EY + 1
    bb.fill(x1 - 1, EY, z1 - 1, x2 + 1, y0, z2 + 1, "minecraft:stone_bricks")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:stripped_oak_wood")
    bb.fill(x1, y0 + 1, z1, x2, y0 + 7, z2, "minecraft:stripped_spruce_wood")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + 7, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, y0 + 7, z, "minecraft:dark_oak_log[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, y0 + 7, z, "minecraft:dark_oak_log[axis=y]")
    for x in range(x1 + 1, x2):
        if (x - x1) % 4:
            bb.fill(x, y0 + 4, z1, x, y0 + 5, z1, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=true]")
            bb.fill(x, y0 + 4, z2, x, y0 + 5, z2, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]")
    # sliding doors open on the west to the garden
    bb.fill(x1, y0 + 1, (z1 + z2) // 2 - 2, x1, y0 + 3, (z1 + z2) // 2 + 2, AIR)
    castle_eave(bb, x1, z1, x2, z2, y0 + 7, TILE, TILEF, depth=1, bracket="minecraft:dark_oak_stairs")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + 8, TILE, gable_fill="minecraft:stripped_spruce_wood", overhang=1)
    # training posts (logs wrapped in hay), the master's seat, weapon racks, a calligraphy scroll wall
    for x in range(x1 + 5, x2 - 3, 5):
        for z in (z1 + 4, z2 - 4):
            bb.fill(x, y0 + 1, z, x, y0 + 3, z, "minecraft:oak_log[axis=y]")
            bb.set(x, y0 + 2, z, "minecraft:hay_block[axis=y]")
    bb.fill(x2 - 1, y0 + 1, z1 + 2, x2 - 1, y0 + 1, z2 - 2, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(x2 - 2, y0 + 1, (z1 + z2) // 2, st("minecraft:dark_oak_stairs", "west"))
    for z in range(z1 + 2, z2 - 1):
        bb.set(x2 - 1, y0 + 3, z, "minecraft:tripwire_hook[attached=false,facing=west,powered=false]") if z % 2 else \
            bb.set(x2 - 1, y0 + 4, z, "minecraft:white_wall_banner[facing=west]")
    for x in range(x1 + 2, x2 - 1, 2):
        bb.set(x, y0 + 3, z1 + 1, "minecraft:tripwire_hook[attached=false,facing=south,powered=false]")
    for (x, z) in ((x1 + 2, z1 + 2), (x1 + 2, z2 - 2)):
        bb.set(x, y0 + 1, z, "minecraft:barrel[facing=up,open=false]")
    for z in range(z1 + 4, z2 - 2, 6):
        bb.set((x1 + x2) // 2, y0 + 6, z, "minecraft:lantern[hanging=true]")
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


def kura(bb):
    """The white storehouse: thick plaster walls on a black stone base, a heavy door, a tiled roof, goods inside."""
    x1, z1, x2, z2 = 44, 82, 58, 96
    y0 = EY + 1
    bb.fill(x1, EY, z1, x2, y0 + 1, z2, "minecraft:polished_blackstone_bricks")
    bb.fill(x1, y0 + 2, z1, x2, y0 + 9, z2, "minecraft:white_concrete")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + 8, z2 - 1, AIR)
    bb.fill(x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 1, y0 + 5, z1 + 1, x2 - 1, y0 + 5, z2 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 2, y0 + 5, z1 + 2, x1 + 2, y0 + 5, z1 + 2, AIR)
    bb.fill(x1 + 2, y0 + 1, z1 + 2, x1 + 2, y0 + 5, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, y0 + 1, z1 + 1, "minecraft:spruce_planks")
    for z in (z1 + 4, z2 - 4):
        bb.set(x1, y0 + 7, z, "minecraft:iron_bars"); bb.set(x2, y0 + 7, z, "minecraft:iron_bars")
    cz = (z1 + z2) // 2
    bb.fill(x2, y0 + 1, cz, x2, y0 + 2, cz, AIR)
    bb.set(x2, y0 + 1, cz, "minecraft:iron_door[facing=east,half=lower,hinge=left,open=false,powered=false]")
    bb.set(x2, y0 + 2, cz, "minecraft:iron_door[facing=east,half=upper,hinge=left,open=false,powered=false]")
    bb.set(x2 + 1, y0, cz, "minecraft:stone_bricks"); bb.set(x2 + 1, y0 + 1, cz + 1, "minecraft:stone_button[face=floor,facing=east,powered=false]") if False else None
    bb.set(x2 + 1, y0 + 1, cz - 1, "minecraft:stone_button[face=wall,facing=east,powered=false]") if False else None
    bb.fill(x2 - 1, y0 + 1, cz - 1, x2 - 1, y0 + 1, cz + 1, AIR)
    bb.set(x2 - 1, y0 + 2, cz + 1, "minecraft:stone_button[face=wall,facing=west,powered=false]")
    bb.set(x2 + 1, y0 + 2, cz + 1, "minecraft:stone_button[face=wall,facing=east,powered=false]")
    for z in range(z1 + 1, z2):
        for (x, yy) in ((x1 + 1, y0 + 1), (x1 + 1, y0 + 2), (x1 + 1, y0 + 6)):
            if z not in (z1 + 2,) and (z + yy) % 3:
                bb.set(x, yy, z, ("minecraft:barrel[facing=up,open=false]", "minecraft:hay_block[axis=y]", "onepiece:keg[facing=east]")[(z + yy) % 3])
    for x in range(x1 + 3, x2 - 1):
        bb.set(x, y0 + 1, z2 - 1, "minecraft:barrel[facing=north,open=false]") if x % 2 else bb.set(x, y0 + 1, z2 - 1, "minecraft:chiseled_bookshelf[facing=north]")
        bb.set(x, y0 + 6, z1 + 1, "minecraft:bookshelf") if x % 3 else None
    bb.set((x1 + x2) // 2, y0 + 4, cz, "minecraft:lantern[hanging=true]") if False else bb.set((x1 + x2) // 2, y0 + 4, cz, "minecraft:lantern[hanging=true]")
    bb.set((x1 + x2) // 2, y0 + 8, cz, "minecraft:lantern[hanging=true]")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + 10, TILE, gable_fill="minecraft:white_concrete", overhang=1)
    return (x1 - 2, z1 - 2, x2 + 3, z2 + 2)


def shrine(bb, x, z):
    y = EY
    bb.fill(x - 4, y, z - 4, x + 4, y + 1, z + 3, "minecraft:stone_bricks")
    bb.fill(x - 3, y + 2, z - 3, x + 3, y + 5, z + 1, "minecraft:stripped_spruce_wood")
    bb.fill(x - 2, y + 2, z - 2, x + 2, y + 5, z + 1, AIR)
    bb.fill(x - 3, y + 2, z + 1, x + 3, y + 2, z + 1, "minecraft:dark_oak_fence")
    bb.fill(x - 1, y + 2, z + 1, x + 1, y + 2, z + 1, AIR)
    for (a, b) in ((x - 3, z - 3), (x + 3, z - 3), (x - 3, z + 1), (x + 3, z + 1)):
        bb.fill(a, y + 2, b, a, y + 5, b, "minecraft:red_concrete")
    P.gable_roof(bb, x - 4, z - 4, x + 4, z + 2, y + 6, TILE, gable_fill="minecraft:red_concrete", overhang=1)
    bb.set(x, y + 2, z - 2, "minecraft:candle[candles=3,lit=true]")
    bb.set(x - 1, y + 2, z - 2, "minecraft:flower_pot") if False else None
    bb.set(x, y + 4, z + 2, "minecraft:bell[attachment=ceiling,facing=south]")
    for k, tz in enumerate((z + 6, z + 11)):
        h = 6 - k
        for dx in (-3, 3):
            bb.fill(x + dx, y + 1, tz, x + dx, y + h, tz, "minecraft:red_concrete")
        bb.fill(x - 4, y + h + 1, tz, x + 4, y + h + 1, tz, "minecraft:red_concrete")
        bb.fill(x - 5, y + h + 2, tz, x + 5, y + h + 2, tz, "minecraft:black_concrete")
        bb.fill(x - 3, y + h - 1, tz, x + 3, y + h - 1, tz, "minecraft:red_concrete")
    for zz in range(z + 4, z + 14):
        bb.set(x, y, zz, "minecraft:stone_bricks"); bb.set(x - 1, y, zz, "minecraft:polished_andesite"); bb.set(x + 1, y, zz, "minecraft:polished_andesite")
    for (a, b) in ((x - 3, z + 3), (x + 3, z + 3)):
        stone_lantern(bb, a, EY, b)
    return (x - 6, z - 6, x + 6, z + 14)


def bell_tower(bb, x, z):
    y = EY
    bb.fill(x - 3, y, z - 3, x + 3, y + 1, z + 3, "minecraft:stone_bricks")
    for (a, b) in ((x - 2, z - 2), (x + 2, z - 2), (x - 2, z + 2), (x + 2, z + 2)):
        bb.fill(a, y + 2, b, a, y + 10, b, "minecraft:dark_oak_log[axis=y]")
    for yy in (y + 5, y + 10):
        bb.fill(x - 2, yy, z - 2, x + 2, yy, z + 2, "minecraft:dark_oak_planks")
    bb.fill(x - 1, y + 5, z - 1, x + 1, y + 5, z + 1, AIR)
    bb.fill(x - 2, y + 2, z - 2, x - 2, y + 4, z + 2, "minecraft:dark_oak_fence") if False else None
    for zz in range(z - 2, z + 3):
        bb.fill(x - 2, y + 6, zz, x - 2, y + 6, zz, "minecraft:dark_oak_fence"); bb.fill(x + 2, y + 6, zz, x + 2, y + 6, zz, "minecraft:dark_oak_fence")
    bb.fill(x - 1, y + 6, z - 2, x + 1, y + 6, z - 2, "minecraft:dark_oak_fence"); bb.fill(x - 1, y + 6, z + 2, x + 1, y + 6, z + 2, "minecraft:dark_oak_fence")
    bb.fill(x - 1, y + 2, z + 2, x - 1, y + 6, z + 2, "minecraft:ladder[facing=north]") if False else None
    bb.set(x, y + 9, z, "minecraft:bell[attachment=ceiling,facing=south]")
    bb.fill(x + 1, y + 2, z - 1, x + 1, y + 5, z - 1, "minecraft:ladder[facing=west]") if False else None
    bb.set(x, y + 10, z, "minecraft:dark_oak_planks")
    castle_eave(bb, x - 2, z - 2, x + 2, z + 2, y + 10, TILE, TILEF, depth=2, bracket="minecraft:dark_oak_stairs")
    bb.fill(x - 1, y + 11, z - 1, x + 1, y + 11, z + 1, TILEF)
    bb.set(x, y + 12, z, "minecraft:lightning_rod")
    bb.fill(x - 1, y + 2, z - 1, x - 1, y + 5, z - 1, "minecraft:ladder[facing=south]") if False else None
    for yy in range(y + 2, y + 6):
        bb.set(x, yy, z - 1, "minecraft:ladder[facing=south]") if False else None
    bb.fill(x, y + 2, z - 1, x, y + 2, z - 1, AIR)
    bb.set(x, y + 2, z - 2, "minecraft:dark_oak_planks") if False else None
    # ladder up the inside of the south face
    bb.fill(x, y + 2, z + 1, x, y + 5, z + 1, "minecraft:dark_oak_planks") if False else None
    bb.fill(x + 1, y + 2, z + 1, x + 1, y + 5, z + 1, "minecraft:ladder[facing=north]")
    bb.fill(x + 1, y + 2, z + 2, x + 1, y + 5, z + 2, "minecraft:dark_oak_planks")
    bb.fill(x + 1, y + 5, z + 1, x + 1, y + 5, z + 1, "minecraft:ladder[facing=north]")
    return (x - 5, z - 5, x + 5, z + 5)


def stone_lantern(bb, x, y, z):
    bb.set(x, y + 1, z, "minecraft:stone_brick_wall")
    bb.set(x, y + 2, z, "minecraft:stone_brick_wall")
    bb.set(x, y + 3, z, "minecraft:lantern[hanging=false]") if False else bb.set(x, y + 3, z, "minecraft:soul_lantern[hanging=false]") if False else None
    bb.set(x, y + 3, z, "minecraft:chiseled_stone_bricks") if False else None
    bb.set(x, y + 3, z, "minecraft:lantern[hanging=false]")
    bb.set(x, y + 4, z, "minecraft:stone_brick_slab[type=bottom]")


def sakura(bb, x, y, z, rng, h=6):
    for yy in range(y, y + h):
        bb.set(x, yy, z, "minecraft:cherry_log[axis=y]")
    r = rng.uniform(3, 4.2)
    bb.fill_where(x - 5, y + h - 2, z - 5, x + 5, y + h + 3, z + 5,
                  lambda X, yy, Z: ((X - x) ** 2 + ((yy - y - h) * 1.6) ** 2 + (Z - z) ** 2 <= r * r)
                  & (NT.noise(X + yy, Z, 2399, 2) > 0.18), "minecraft:cherry_leaves[distance=7,persistent=true,waterlogged=false]")
    for _ in range(7):
        px, pz = x + int(rng.integers(-4, 5)), z + int(rng.integers(-4, 5))
        set_if_air(bb, px, y, pz, "minecraft:pink_petals[facing=north,flower_amount=%d]" % int(rng.integers(1, 5)))


def garden(bb, rng):
    """Koi pond with a red bridge, raked gravel paths, stone lanterns, sakura and pines, a little tea house."""
    y = EY
    px, pz = 74, 96
    bb.fill_where(px - 14, y - 3, pz - 9, px + 14, y, pz + 9,
                  lambda X, yy, Z: ((X - px) / 13.0) ** 2 + ((Z - pz) / 8.0) ** 2 + 0.25 * NT.noise(X, Z, 2381, 4) <= 1.0, AIR)
    bb.fill_where(px - 14, y - 3, pz - 9, px + 14, y, pz + 9,
                  lambda X, yy, Z: (((X - px) / 13.0) ** 2 + ((Z - pz) / 8.0) ** 2 + 0.25 * NT.noise(X, Z, 2381, 4) <= 1.0) & (yy <= y - 1)
                  & (yy >= y - 2), "minecraft:water")
    bb.fill_where(px - 14, y - 3, pz - 9, px + 14, y - 3, pz + 9,
                  lambda X, yy, Z: ((X - px) / 13.0) ** 2 + ((Z - pz) / 8.0) ** 2 + 0.25 * NT.noise(X, Z, 2381, 4) <= 1.0, "minecraft:mud")
    bb.fill_where(px - 15, y, pz - 10, px + 15, y, pz + 10,
                  lambda X, yy, Z: (np.abs(((X - px) / 13.0) ** 2 + ((Z - pz) / 8.0) ** 2 + 0.25 * NT.noise(X, Z, 2381, 4) - 1.12) < 0.12)
                  & (NT.noise(X, Z, 2382, 2) > 0.45), "minecraft:mossy_cobblestone")
    for (a, b) in ((px - 6, pz - 2), (px + 3, pz + 3), (px + 8, pz - 3)):
        bb.set(a, y - 1, b, "minecraft:lily_pad") if False else bb.set(a, y, b, "minecraft:lily_pad")
    bb.set(px - 3, y - 1, pz + 4, "minecraft:mossy_cobblestone"); bb.set(px - 3, y, pz + 4, "minecraft:moss_carpet")
    # the red arched bridge across the middle (north-south)
    for k, zz in enumerate(range(pz - 10, pz + 11)):
        yy = y + 1 + int(round(2.2 * math.sin(math.pi * k / 20)))
        bb.fill(px - 1, yy, zz, px + 1, yy, zz, "minecraft:dark_oak_slab[type=bottom]" if k in (0, 20) else "minecraft:dark_oak_planks")
        bb.fill(px - 1, y + 1, zz, px + 1, yy - 1, zz, AIR) if 0 < k < 20 else None
        for xx in (px - 2, px + 2):
            bb.set(xx, yy, zz, "minecraft:red_concrete")
            bb.set(xx, yy + 1, zz, "minecraft:red_stained_glass_pane" if k % 4 else "minecraft:red_concrete")
    # gravel-look paths (light stone, no gravel: it would fall) from the gate to the house, the dojo, the kura
    for (x1, z1, x2, z2) in ((GATE_X - 2, HOUSE[3] + 4, GATE_X + 2, EST[3]), (56, 104, 60, 113), (GATE_X, 92, 96, 94),
                             (59, 88, 64, 90), (px - 1, pz - 13, px + 1, pz - 11), (px - 1, pz + 11, px + 1, 112), (60, 112, GATE_X - 3, 113)):
        NT.cover(bb, x1, z1, x2, z2, lambda X, Z: X * 0 + y,
                 [("minecraft:smooth_stone", 0.3), ("minecraft:polished_diorite", 0.25), ("minecraft:diorite", 0.25),
                  ("minecraft:white_concrete_powder", 0.0), ("minecraft:calcite", 0.2)], 2383)
    for z in range(HOUSE[3] + 6, EST[3] - 2, 6):
        for x in (GATE_X - 4, GATE_X + 4):
            stone_lantern(bb, x, y, z)
    for (x, z) in ((px - 16, pz - 6), (px + 16, pz + 6), (px - 10, pz + 10), (px + 12, pz - 9)):
        stone_lantern(bb, x, y, z)
    # sakura round the pond, pines along the wall
    for (x, z) in ((px - 18, pz + 2), (px + 18, pz - 2), (px - 8, pz - 12), (px + 9, pz + 12), (GATE_X + 10, 112), (GATE_X - 10, 112),
                   (60, 110), (112, 116), (124, 74), (46, 72)):
        sakura(bb, x, y + 1, z, rng, h=int(rng.integers(5, 8)))
    for (x, z) in ((44, 40), (54, 40), (124, 46), (120, 112), (44, 116), (128, 60)):
        P.tree(bb, x, y + 1, z, int(rng.integers(7, 10)), "spruce", rng)
    # hedges of azalea along the house front
    for x in range(HOUSE[0], HOUSE[2] + 1):
        if abs(x - GATE_X) > 4 and x % 7:
            bb.set(x, y + 1, HOUSE[3] + 4, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]" if x % 3 else
                   "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    # a little tea house by the pond
    tx, tz = px - 20, pz - 10
    bb.fill(tx, y + 1, tz, tx + 5, y + 1, tz + 5, "minecraft:dark_oak_planks")
    for (a, b) in ((tx, tz), (tx + 5, tz), (tx, tz + 5), (tx + 5, tz + 5)):
        bb.fill(a, y + 2, b, a, y + 4, b, "minecraft:dark_oak_fence")
    bb.fill(tx + 1, y + 2, tz + 1, tx + 4, y + 2, tz + 4, "minecraft:lime_carpet")
    bb.set(tx + 2, y + 2, tz + 2, "minecraft:dark_oak_trapdoor[facing=north,half=top,open=false]")
    bb.set(tx + 3, y + 3, tz + 2, "minecraft:flower_pot") if False else None
    castle_eave(bb, tx, tz, tx + 5, tz + 5, y + 4, TILE, TILEF, depth=1)
    bb.fill(tx + 1, y + 6, tz + 1, tx + 4, y + 6, tz + 4, TILEF)
    bb.fill(tx + 2, y + 7, tz + 2, tx + 3, y + 7, tz + 3, TILEF)
    return [(px - 22, pz - 13, px + 16, pz + 12)]


def hills(bb, rng, taken):
    k = 0
    for _ in range(6000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 3 or rect_d(X, Z, (EST[0] - 5, EST[1] - 5, EST[2] + 5, EST[3] + 5))[0, 0] == 0:
            continue
        if rect_d(X, Z, PADDY)[0, 0] < 2 or abs(x - GATE_X) < 5 and z > EST[3]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if y < 1:
            continue
        if NT.noise(X, Z, 2371, 16)[0, 0] > 0.68:
            for _ in range(12):
                bx, bz = x + int(rng.integers(-3, 4)), z + int(rng.integers(-3, 4))
                by = hy(bx, bz)
                if GRAD[min(bx, N - 1), min(bz, N - 1)] < 2:
                    bb.fill(bx, by + 1, bz, bx, by + int(rng.integers(6, 12)), bz, "minecraft:bamboo[age=1,leaves=large,stage=0]")
        elif k % 6 == 5:
            sakura(bb, x, y + 1, z, rng)
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(6, 11)), ("spruce", "spruce", "oak", "dark_oak")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 90:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=2320, y_min=-14, y_max=70)
    tracker = P.PropTracker(2320)
    audit = []
    rng = np.random.default_rng(2320)
    terrain(bb)
    taken = [paddies(bb), estate_wall(bb)]
    taken.append(main_house(bb, tracker, audit))
    taken.append(dojo(bb, tracker, audit))
    taken.append(kura(bb))
    taken.append(shrine(bb, 48, 104))
    taken.append(bell_tower(bb, 124, 40))
    taken += garden(bb, rng)
    hills(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2390, density=0.22, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, (EST[0] - 4, EST[1] - 4, EST[2] + 4, EST[3] + 4)) > 0)
              & (rect_d(X, Z, PADDY) > 0) & ~((np.abs(X - GATE_X) <= 2) & (Z > EST[3])))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates (at sea the world's water
    fills in under it): turn those into blocks that stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if (below is None and y >= 0) or (below is not None and render.shape_of(below) != "full"):
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.npc(GATE_X, EY + 2, HOUSE[1] + 4, "oden", False)
    b.npc(112, EY + 2, 94, "yamato", False)
    b.chest(HOUSE[2] - 3, EY + 2, HOUSE[1] + 3, "wano", "west")
    b.chest(50, EY + 2, 84, "easy", "south")
    b.guards("samurai", ((GATE_X - 5, HOUSE[3] + 6), (GATE_X + 5, HOUSE[3] + 6)), y=EY + 1)
    b.guards("samurai", ((GATE_X - 4, EST[3] - 3), (GATE_X + 4, EST[3] - 3)), y=EY + 1)
    return b, 0
