"""Kuraigana Castle v2, Dracule Mihawk's home on the ruined island where Zoro trained, redesigned with the Minecraft
Builder skill.

A gloomy island of dark moss and mud under its strange curled hills (steep peaks whose summits curl over into
spirals). On a crag in the middle, over a still black lake on its north side, the castle: a tall gothic main block of
deepslate with steep tiled roofs, pointed corner towers with red-glass windows, flying buttresses down its long
sides, the tall gate tower with its spire on the south front, and an arcaded terrace over the lake. Inside: the
great hall (double height, Mihawk's tall chair on a dais before the fireplace, chandeliers, the sword gallery along
its walls), wings of rooms on three floors (library, dining hall, guest rooms, Perona's pink ghost room), the wine
cellar cut into the rock. South of the castle the training yard where Zoro learned; the road winds down the crag
through the ruins of the old kingdom's town (roofless shells, rubble, a broken church), past the graveyard, through
the dead forest where the Humandrills lurk, to the jetty with Mihawk's coffin boat. 176 x 176. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor, stair_core, \
    house_module, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "kuraigana_castle"
TITLE = "Kuraigana Castle (Mihawk)"
CUTS = [5, 16, 24, 32]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
SHORE = NT.outline(88, 90, 80, 1820, wobble=0.08)
CX, CZ = 88, 70
CROWN = 14                                  # the crag top: the castle floor
K = (62, 54, 114, 84)                       # main block (walls)
FH = 8
TOP = CROWN + 3 * FH
LAKE = (88, 30, 30, 13)                     # cx, cz, rx, rz (north of the castle)
PLAT = (54, 44, 122, 112)                   # the levelled crag top
YARD = (66, 90, 110, 110)                   # the training yard in front of the castle
TOWN = (34, 120, 132, 158)
GRAVES = (132, 96, 160, 122)
JETTY = (88, 168)
HILLS = ((154, 64, 13, 30, (0, 1)), (22, 74, 12, 26, (1, 0)), (34, 30, 10, 22, (1, 0)))

DS = "minecraft:deepslate_bricks"
DST = "minecraft:deepslate_tiles"
DST_ST = "minecraft:deepslate_tile_stairs"
WALLS = ["minecraft:deepslate_bricks", "minecraft:deepslate_tiles", "minecraft:cracked_deepslate_bricks", "minecraft:polished_deepslate"]
GLOOM = [("minecraft:podzol", 0.24), ("minecraft:moss_block", 0.18), ("minecraft:coarse_dirt", 0.16), ("minecraft:mud", 0.1),
         ("minecraft:grass_block", 0.16), ("minecraft:rooted_dirt", 0.08), ("minecraft:podzol", 0.08)]
ROCK = [("minecraft:deepslate", 0.3), ("minecraft:tuff", 0.22), ("minecraft:cobbled_deepslate", 0.16), ("minecraft:stone", 0.12),
        ("minecraft:andesite", 0.1), ("minecraft:mossy_cobblestone", 0.1)]
SHORE_MIX = [("minecraft:gravel", 0.5), ("minecraft:coarse_dirt", 0.2), ("minecraft:mud", 0.15), ("minecraft:tuff", 0.15)]
ROAD = [("minecraft:cobbled_deepslate", 0.3), ("minecraft:gravel", 0.25), ("minecraft:coarse_dirt", 0.2),
        ("minecraft:mossy_cobblestone", 0.15), ("minecraft:packed_mud", 0.1)]
ROAD_PTS = [(88, 112), (88, 118), (70, 126), (62, 140), (84, 150), (88, 166)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def seg_d(X, Z, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / float(vx * vx + vz * vz), 0, 1)
    return np.hypot(X - ax - t * vx, Z - az - t * vz), t


def road_d(X, Z):
    d = np.full(np.broadcast(X, Z).shape, 1e9)
    for a, b in zip(ROAD_PTS, ROAD_PTS[1:]):
        d = np.minimum(d, seg_d(X, Z, a, b)[0])
    return d


def in_lake(X, Z, m=0.0):
    lx, lz, rx, rz = LAKE
    return ((X - lx) / (rx + m)) ** 2 + ((Z - lz) / (rz + m)) ** 2 < 1


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 3 + NT.fbm(X, Z, 1821, 24) * 4
    crag = np.clip(1 - rect_d(X, Z, PLAT) / 16.0, 0, 1)
    crag = crag ** 1.3 * (0.85 + 0.3 * NT.noise(X, Z, 1822, 6))
    h = h * (1 - crag) + CROWN * crag
    h = np.where(rect_d(X, Z, PLAT) == 0, CROWN, h)
    # the road ramps down the crag
    acc, L = 0.0, [math.dist(a, b) for a, b in zip(ROAD_PTS, ROAD_PTS[1:])]
    t = np.zeros(np.broadcast(X, Z).shape); best = np.full(t.shape, 1e9)
    for (a, b), l in zip(zip(ROAD_PTS, ROAD_PTS[1:]), L):
        dd, tt = seg_d(X, Z, a, b)
        m = dd < best
        t = np.where(m, (acc + tt * l) / sum(L), t)
        best = np.minimum(best, dd)
        acc += l
    ry = CROWN - np.clip(t * 3.2, 0, 1) * (CROWN - 3) - np.clip(t - 0.7, 0, 1) / 0.3 * 2.4
    rw = np.clip((best - 2.5) / 4.0, 0, 1)
    h = np.where(best < 9, np.minimum(h, ry * (1 - rw) + h * rw) if False else ry * (1 - rw) + h * rw, h)
    # the lake bowl
    lk = in_lake(X, Z, 3)
    h = np.where(lk, np.minimum(h, 1), h)
    h = h * np.clip((d - 1.5) / 7.0, 0, 1)
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
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SHORE_MIX, 1831,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z), under="minecraft:gravel", core="minecraft:tuff")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 1832, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:deepslate",
             core="minecraft:deepslate")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GLOOM, 1833,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z), core="minecraft:tuff")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROAD, 1834,
             mask=lambda X, Z: land(X, Z) & (road_d(X, Z) <= 2 + NT.noise(X, Z, 1835, 3)), core="minecraft:tuff")
    # the lake: black still water with mud banks
    lx, lz, rx, rz = LAKE
    bb.fill_where(lx - rx - 1, 1, lz - rz - 1, lx + rx + 1, 6, lz + rz + 1, lambda X, yy, Z: in_lake(X, Z), AIR)
    bb.fill_where(lx - rx - 1, -5, lz - rz - 1, lx + rx + 1, -5, lz + rz + 1, lambda X, yy, Z: in_lake(X, Z), "minecraft:mud")
    for y in range(-4, 1):
        bb.fill_where(lx - rx - 1, y, lz - rz - 1, lx + rx + 1, y, lz + rz + 1, lambda X, yy, Z: in_lake(X, Z), "minecraft:mud")
        bb.fill_where(lx - rx - 1, y, lz - rz - 1, lx + rx + 1, y, lz + rz + 1,
                      lambda X, yy, Z: in_lake(X, Z) & (yy > -1 - 3 * (1 - ((X - lx) / rx) ** 2 - ((Z - lz) / rz) ** 2)),
                      "minecraft:water")
    bb.fill_where(lx - rx - 1, -5, lz - rz - 1, lx + rx + 1, 0, lz + rz + 1,
                  lambda X, yy, Z: in_lake(X, Z, 1.2) & ~in_lake(X, Z) & (yy == 0), "minecraft:mud")
    for y in range(-12, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy > -2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))), "minecraft:gravel")


def curl_hill(bb, hc, rng):
    """A steep hill narrowing to a neck whose summit curls over into a spiral."""
    cx, cz, R, H, (ux, uz) = hc
    base = hy(cx, cz)
    rho0, pts, th, end = 7.0, [], 0.0, 1.8 * math.pi
    while th <= end:
        rho = rho0 * (1 - 0.22 * th / math.pi)
        u, v = rho0 - rho * math.cos(th), H + rho * math.sin(th)
        pts.append((cx + ux * u, base + v, cz + uz * u, 2.9 - 1.7 * th / end))
        th += 0.05
    span = R + 18
    x1, z1, x2, z2 = cx - span, cz - span, cx + span, cz + span

    def body(X, yy, Z):
        r = np.maximum(2.6, R * np.clip(1 - (yy - base) / H, 0, 1) ** 1.4)
        return (yy >= base - 3) & (yy <= base + H) & (np.hypot(X - cx, Z - cz) <= r)
    bb.fill_where(x1, base - 3, z1, x2, base + H, z2, body, "minecraft:tuff")
    for (px, py, pz, tr) in pts:
        R2 = int(tr) + 2
        bb.fill_where(int(px) - R2, int(py) - R2, int(pz) - R2, int(px) + R2, int(py) + R2, int(pz) + R2,
                      lambda X, yy, Z: (X - px) ** 2 + (yy - py) ** 2 + (Z - pz) ** 2 <= tr * tr, "minecraft:tuff")
    # skin it: moss on top surfaces, podzol/dirt on the sides
    y2 = base + H + 12
    reg = bb.get_region(x1, base - 3, z1, x2, y2, z2)
    names = bb.names
    tuff = [i for i, n in enumerate(names) if n == "minecraft:tuff"]
    if not tuff:
        return
    t = tuff[0]
    solid = reg == t
    above = np.zeros_like(solid)
    above[:, :-1, :] = solid[:, 1:, :]
    skin = solid & ~above
    xs, ys, zs = np.nonzero(skin)
    for i, j, k in zip(xs, ys, zs):
        r = rng.random()
        bb.set(x1 + int(i), base - 3 + int(j), z1 + int(k),
               "minecraft:moss_block" if r < 0.6 else "minecraft:podzol" if r < 0.85 else "minecraft:coarse_dirt")
    side = solid & above
    side[1:-1, :, 1:-1] &= ~(solid[2:, :, 1:-1] & solid[:-2, :, 1:-1] & solid[1:-1, :, 2:] & solid[1:-1, :, :-2])
    xs, ys, zs = np.nonzero(side)
    for i, j, k in zip(xs, ys, zs):
        if rng.random() < 0.5:
            bb.set(x1 + int(i), base - 3 + int(j), z1 + int(k), "minecraft:moss_block" if rng.random() < 0.5 else "minecraft:rooted_dirt")


# ------------------------------------------------------------------ the castle
def spire(bb, cx, cz, r, y0, y1, roof_h):
    bb.fill_where(cx - r, y0, cz - r, cx + r, y1, cz + r, lambda X, yy, Z: np.hypot(X - cx, Z - cz) <= r + 0.3, DS)
    bb.fill_where(cx - r, y0 + 1, cz - r, cx + r, y1, cz + r, lambda X, yy, Z: np.hypot(X - cx, Z - cz) <= r - 0.7, AIR)
    for y in range(y0 + 4, y1 - 2, 6):
        for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
            bb.fill(cx + dx, y, cz + dz, cx + dx, y + 2, cz + dz, "minecraft:red_stained_glass_pane")
    for k in range(roof_h):
        rr = (r + 1.2) * (1 - k / roof_h) + 0.3
        bb.fill_where(cx - r - 2, y1 + 1 + k, cz - r - 2, cx + r + 2, y1 + 1 + k, cz + r + 2,
                      lambda X, yy, Z, rr=rr: np.hypot(X - cx, Z - cz) <= rr, DST)
    bb.set(cx, y1 + roof_h + 1, cz, "minecraft:lightning_rod")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.set(round(cx + (r + 1) * math.cos(t)), y1 + 1, round(cz + (r + 1) * math.sin(t)), "minecraft:deepslate_brick_wall")


def gothic_window(bb, x, z, y, h, axis):
    """A tall pointed window: glass h high with a pointed head."""
    if axis == "x":
        bb.fill(x, y, z, x + 1, y + h - 1, z, "minecraft:gray_stained_glass_pane")
        bb.set(x, y + h, z, st("minecraft:deepslate_brick_stairs", "east", "top"))
        bb.set(x + 1, y + h, z, st("minecraft:deepslate_brick_stairs", "west", "top"))
    else:
        bb.fill(x, y, z, x, y + h - 1, z + 1, "minecraft:gray_stained_glass_pane")
        bb.set(x, y + h, z, st("minecraft:deepslate_brick_stairs", "south", "top"))
        bb.set(x, y + h, z + 1, st("minecraft:deepslate_brick_stairs", "north", "top"))


def castle(bb, tracker, audit, rng):
    x1, z1, x2, z2 = K
    y0 = CROWN
    bb.fill(x1 - 2, y0 - 6, z1 - 2, x2 + 2, y0, z2 + 2, "minecraft:cobbled_deepslate")
    bb.fill(x1 - 2, y0, z1 - 2, x2 + 2, y0, z2 + 2, "minecraft:polished_deepslate")
    bb.mix(x1, y0 + 1, z1, x2, TOP - 1, z2, WALLS, [0.5, 0.25, 0.1, 0.15])
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, TOP - 1, z2 - 1, AIR)
    for k in range(1, 4):
        bb.fill(x1 + 1, y0 + FH * k, z1 + 1, x2 - 1, y0 + FH * k, z2 - 1, "minecraft:dark_oak_planks")
        yb = y0 + FH * k
        for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
            bb.fill(a, yb, b, c, yb, d, "minecraft:polished_deepslate")
    bb.fill(x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, "minecraft:polished_deepslate")
    # tall pointed windows on every storey, buttress piers between them
    for k in range(3):
        wy = y0 + FH * k + 2
        for x in range(x1 + 3, x2 - 3, 5):
            for z in (z1, z2):
                gothic_window(bb, x, z, wy, 4, "x")
        for z in range(z1 + 3, z2 - 3, 5):
            for x in (x1, x2):
                gothic_window(bb, x, z, wy, 4, "z")
    for x in range(x1, x2 + 1, 5):
        for z, o in ((z1, -1), (z2, 1)):
            bb.fill(x, y0 + 1, z + o, x, TOP - 2, z + o, "minecraft:deepslate_brick_wall")
    cornice(bb, x1, z1, x2, z2, TOP, "minecraft:deepslate_brick_stairs", parapet=None)
    # the steep roof with dormers and a ridge of iron spikes
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, TOP + 1, DST_ST, ridge_axis="x", gable_fill=DS, overhang=0, ends_overhang=0)
    W = z2 - z1 + 3
    ridge_y = TOP + 1 + W // 2
    for x in range(x1, x2 + 1, 3):
        bb.set(x, ridge_y + 1, (z1 + z2) // 2, "minecraft:iron_bars")
    for x in range(x1 + 6, x2 - 5, 10):                                 # dormers on the south slope
        for (zz, f) in ((z1 + 3, "north"), (z2 - 3, "south")):
            bb.fill(x - 1, TOP + 4, zz, x + 1, TOP + 6, zz, DS)
            bb.fill(x, TOP + 4, zz, x, TOP + 5, zz, "minecraft:red_stained_glass_pane")
            bb.set(x - 1, TOP + 7, zz, st(DST_ST, "east")); bb.set(x + 1, TOP + 7, zz, st(DST_ST, "west"))
            bb.set(x, TOP + 7, zz, DST); bb.set(x, TOP + 8, zz, "minecraft:deepslate_tile_slab[type=bottom]")
    # corner towers with spires
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        spire(bb, tx, tz, 5, y0 - 4, TOP + 10, 16)
        for k in range(1, 4):
            bb.fill_where(tx - 4, y0 + FH * k, tz - 4, tx + 4, y0 + FH * k, tz + 4, lambda X, yy, Z: np.hypot(X - tx, Z - tz) <= 4.4,
                          "minecraft:dark_oak_planks")
    # flying buttresses: piers out from the long walls, arched struts back to the wall
    for x in range(x1 + 8, x2 - 6, 10):
        for (z, o) in ((z1, -1), (z2, 1)):
            pz = z + o * 7
            if o < 0 and in_lake(np.array([[x]]), np.array([[pz]]), 2)[0, 0]:
                pass
            bb.fill(x - 1, y0 - 6, pz - 1, x + 1, y0 + 2 * FH + 2, pz + 1, DS)
            bb.fill(x, y0 + 2 * FH + 3, pz, x, y0 + 2 * FH + 6, pz, "minecraft:deepslate_brick_wall")
            bb.set(x, y0 + 2 * FH + 7, pz, "minecraft:lightning_rod")
            for i in range(1, 7):
                yy = y0 + 2 * FH + 2 + int(round(3 * math.sin(math.pi * i / 14)))
                bb.set(x, yy, pz - o * i, DS)
                bb.set(x, yy - 1, pz - o * i, st("minecraft:deepslate_brick_stairs", "south" if o > 0 else "north", "top"))
    # the gate tower on the south front, with the door and the tall spire
    gx = CX
    G = (gx - 6, z2 - 2, gx + 6, z2 + 8)
    bb.mix(G[0], y0 + 1, G[1], G[2], TOP + 14, G[3], WALLS, [0.5, 0.25, 0.1, 0.15])
    bb.fill(G[0] + 1, y0 + 1, G[1] + 1, G[2] - 1, TOP + 13, G[3] - 1, AIR)
    for k in range(1, 4):
        bb.fill(G[0] + 1, y0 + FH * k, G[1] + 1, G[2] - 1, y0 + FH * k, G[3] - 1, "minecraft:dark_oak_planks")
    bb.fill(G[0] + 1, TOP + 14, G[1] + 1, G[2] - 1, TOP + 14, G[3] - 1, "minecraft:dark_oak_planks")
    for k in range(4):
        wy = y0 + FH * k + 2
        gothic_window(bb, gx - 1 + (0 if k else 0), G[3], wy, 4 if k else 0, "x") if k else None
    bb.fill(gx - 2, y0 + 1, G[3], gx + 2, y0 + 5, G[3], AIR)                        # the great door
    bb.fill(gx - 2, y0 + 6, G[3], gx + 2, y0 + 6, G[3], "minecraft:polished_deepslate")
    bb.set(gx - 2, y0 + 5, G[3], st("minecraft:deepslate_brick_stairs", "east", "top"))
    bb.set(gx + 2, y0 + 5, G[3], st("minecraft:deepslate_brick_stairs", "west", "top"))
    bb.fill(gx - 1, y0 + 1, G[1], gx + 1, y0 + 4, G[1], AIR)
    bb.fill(gx - 2, y0 + 1, G[3] - 1, gx + 2, y0 + 1, G[3] - 1, "minecraft:red_carpet")
    for (a, f) in ((G[0], "east"), (G[2], "west")):                                # pinnacles on the gate tower
        for c in (G[1], G[3]):
            bb.fill(a, TOP + 15, c, a, TOP + 19, c, "minecraft:deepslate_brick_wall")
    bb.fill(G[0], TOP + 15, G[1], G[2], TOP + 15, G[3], DS)
    bb.fill(G[0] + 1, TOP + 15, G[1] + 1, G[2] - 1, TOP + 15, G[3] - 1, "minecraft:dark_oak_planks")
    for k in range(20):
        rr = 6.3 * (1 - k / 20) + 0.3
        bb.fill_where(gx - 7, TOP + 16 + k, (G[1] + G[3]) // 2 - 7, gx + 7, TOP + 16 + k, (G[1] + G[3]) // 2 + 7,
                      lambda X, yy, Z, rr=rr: (np.abs(X - gx) <= rr) & (np.abs(Z - (G[1] + G[3]) / 2) <= rr), DST)
    bb.set(gx, TOP + 36, (G[1] + G[3]) // 2, "minecraft:lightning_rod")
    # clock-like rose window on the gate tower
    rz = G[3]
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                bb.set(gx + dx, TOP + 6 + dy, rz, "minecraft:red_stained_glass" if (dx + dy) % 2 else "minecraft:black_stained_glass")
    bb.fill(G[0] + 1, y0 + 1, G[1] + 1, G[0] + 1, TOP + 14, G[1] + 1, "minecraft:ladder[facing=east]")
    # inside the main block: the great hall in the middle (two storeys high), wings either side
    hx1, hx2 = CX - 12, CX + 12
    bb.fill(hx1, y0 + FH, z1 + 1, hx2, y0 + FH, z2 - 1, AIR)
    bb.fill(hx1 - 1, y0 + 1, z1 + 1, hx1 - 1, y0 + 2 * FH - 1, z2 - 1, DS)
    bb.fill(hx2 + 1, y0 + 1, z1 + 1, hx2 + 1, y0 + 2 * FH - 1, z2 - 1, DS)
    for z in range(z1 + 4, z2 - 2, 6):
        for x in (hx1 - 1, hx2 + 1):
            bb.fill(x, y0 + 1, z, x, y0 + 3, z + 1, AIR)
    for z in range(z1 + 1, z2):
        for x in range(hx1, hx2 + 1):
            bb.set(x, y0, z, "minecraft:polished_deepslate" if (x + z) % 2 else "minecraft:deepslate_tiles")
    bb.fill(CX - 1, y0 + 1, z1 + 4, CX + 1, y0 + 1, z2 - 1, "minecraft:red_carpet")
    for x in (hx1 + 2, hx2 - 2):                                      # columns
        for z in range(z1 + 4, z2 - 2, 6):
            bb.fill(x, y0 + 1, z, x, y0 + 2 * FH - 1, z, "minecraft:polished_deepslate")
            bb.set(x, y0 + 2 * FH - 1, z, "minecraft:chiseled_deepslate")
    # the dais, Mihawk's tall chair and the fireplace behind it on the north wall
    bb.fill(CX - 4, y0 + 1, z1 + 1, CX + 4, y0 + 1, z1 + 4, "minecraft:polished_blackstone")
    bb.fill(CX - 4, y0 + 1, z1 + 5, CX + 4, y0 + 1, z1 + 5, st("minecraft:polished_blackstone_stairs", "south"))
    bb.set(CX, y0 + 2, z1 + 3, st("minecraft:dark_oak_stairs", "south"))
    bb.fill(CX, y0 + 3, z1 + 2, CX, y0 + 6, z1 + 2, "minecraft:red_wool")
    bb.set(CX - 1, y0 + 2, z1 + 3, st("minecraft:dark_oak_stairs", "east") if False else "minecraft:dark_oak_fence")
    bb.set(CX + 1, y0 + 2, z1 + 3, "minecraft:dark_oak_fence")
    bb.fill(CX - 1, y0 + 3, z1 + 2, CX - 1, y0 + 7, z1 + 2, "minecraft:dark_oak_log[axis=y]")
    bb.fill(CX + 1, y0 + 3, z1 + 2, CX + 1, y0 + 7, z1 + 2, "minecraft:dark_oak_log[axis=y]")
    bb.set(CX, y0 + 7, z1 + 2, "minecraft:dark_oak_log[axis=x]")
    for fx in (CX - 8, CX + 8):
        bb.fill(fx - 2, y0 + 1, z1 + 1, fx + 2, y0 + 5, z1 + 2, "minecraft:polished_blackstone_bricks")
        bb.fill(fx - 1, y0 + 1, z1 + 1, fx + 1, y0 + 3, z1 + 2, AIR)
        bb.fill(fx - 1, y0, z1 + 1, fx + 1, y0, z1 + 1, "minecraft:netherrack")
        bb.fill(fx - 1, y0 + 1, z1 + 1, fx + 1, y0 + 1, z1 + 1, "minecraft:fire") if False else bb.set(fx, y0 + 1, z1 + 1, "minecraft:campfire[lit=true]")
        bb.fill(fx - 1, y0 + 6, z1 + 1, fx + 1, TOP + 12, z1 + 1, "minecraft:polished_blackstone_bricks") if False else \
            bb.fill(fx - 1, y0 + 6, z1 + 1, fx + 1, y0 + 2 * FH - 1, z1 + 1, "minecraft:polished_blackstone_bricks")
        bb.set(fx - 2, y0 + 6, z1 + 2, "minecraft:candle[candles=3,lit=true]")
        bb.set(fx + 2, y0 + 6, z1 + 2, "minecraft:candle[candles=3,lit=true]")
    # chandeliers
    for z in range(z1 + 8, z2 - 3, 9):
        for x in (CX - 5, CX + 5):
            bb.fill(x, y0 + 2 * FH - 4, z, x, y0 + 2 * FH - 1, z, "minecraft:chain")
            bb.set(x, y0 + 2 * FH - 5, z, "minecraft:soul_lantern[hanging=true]")
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bb.set(x + dx, y0 + 2 * FH - 4, z + dz, "minecraft:polished_blackstone_wall")
                bb.set(x + dx, y0 + 2 * FH - 3, z + dz, "minecraft:candle[candles=1,lit=true]")
    # the sword gallery: racks of blades along the hall walls (swords = lightning rods on grindstone stands)
    for z in range(z1 + 6, z2 - 2, 6):
        for (x, f) in ((hx1, "east"), (hx2, "west")):
            bb.set(x, y0 + 1, z + 2, "minecraft:grindstone[face=floor,facing=north]")
            bb.set(x, y0 + 2, z + 2, "minecraft:lightning_rod")
            bb.set(x, y0 + 3, z + 2, "minecraft:lightning_rod")
            bb.set(x, y0 + 5, z + 2, f"minecraft:black_wall_banner[facing={f}]")
    # wings: three floors of rooms each side, a stair core in each
    kinds = [[("kitchen", "storage", "living"), ("library", "library", "living"), ("bedroom", "bedroom", "storage")],
             [("living", "kitchen", "storage"), ("library", "bedroom", "living"), ("bedroom", "bedroom", "living")]]
    for side, (wx1, wx2) in enumerate(((x1 + 1, hx1 - 2), (hx2 + 2, x2 - 1))):
        sx = wx1 + 1 if side == 0 else wx2 - 5
        sz = z2 - 6
        stair_core(bb, sx, sz, 4, y0 + 1, y0 + 2 * FH, (y0 + 1, y0 + FH + 1, y0 + 2 * FH + 1), DS, "minecraft:dark_oak_stairs")
        for k in range(3):
            y = y0 + 1 + FH * k
            wing_floor(bb, wx1, z1 + 1, wx2, z2 - 1, y, FH - 1, DS, seed_of("kg", side, k), tracker, kinds[side][k],
                       corridor="z", cw=3, carpet=(None, "minecraft:red_carpet"), keep=[(sx - 1, sz - 1, sx + 4, sz + 4)],
                       wood="dark_oak", audit=audit, lamp="minecraft:soul_lantern[hanging=true]")
    # top floor over the hall: Perona's pink ghost room (the west half) and the guest rooms (east)
    y = y0 + 2 * FH + 1
    wing_floor(bb, hx1, z1 + 1, hx2, z2 - 1, y, FH - 1, DS, seed_of("kgtop"), tracker, ("bedroom", "living", "bedroom"),
               corridor="x", cw=3, carpet=(None, "minecraft:black_carpet"), wood="dark_oak", audit=audit,
               lamp="minecraft:soul_lantern[hanging=true]")
    pr = (hx1, z1 + 1, CX - 2, (z1 + z2) // 2 - 2)
    reg = bb.get_region(pr[0], y, pr[1], pr[2], y, pr[3])
    names = bb.names
    for i in range(reg.shape[0]):
        for k in range(reg.shape[2]):
            n = names[reg[i, 0, k]] or ""
            if n in ("", "minecraft:air") or "carpet" in n:
                bb.set(pr[0] + i, y, pr[1] + k, "minecraft:pink_carpet" if (i + k) % 5 else "minecraft:magenta_carpet")
    bb.fill(pr[0], y + 3, pr[1], pr[2], y + 3, pr[1], "minecraft:pink_wool")
    for x in range(pr[0] + 2, pr[2] - 1, 4):
        bb.set(x, y + FH - 3, (pr[1] + pr[3]) // 2, "minecraft:pink_stained_glass")
    # stairs from the hall gallery level up: a stair core in the hall's south-west corner
    stair_core(bb, hx1, z2 - 6, 4, y0 + 1, y0 + 2 * FH, (y0 + 1, y0 + 2 * FH + 1), DS, "minecraft:dark_oak_stairs")
    # the wine cellar under the east wing, cut into the rock, a ladder down from the wing's ground floor
    cx1, cz1, cx2, cz2 = hx2 + 4, z1 + 4, x2 - 4, z1 + 16
    bb.fill(cx1, y0 - 5, cz1, cx2, y0 - 1, cz2, AIR)
    bb.fill(cx1 - 1, y0 - 6, cz1 - 1, cx2 + 1, y0 - 6, cz2 + 1, "minecraft:polished_deepslate")
    for x in range(cx1, cx2 + 1):
        for z in (cz1, cz2):
            for yy in range(y0 - 5, y0 - 2):
                bb.set(x, yy, z, "minecraft:barrel[facing=" + ("south" if z == cz1 else "north") + ",open=false]")
    for x in range(cx1 + 3, cx2 - 2, 5):
        bb.set(x, y0 - 2, (cz1 + cz2) // 2, "minecraft:soul_lantern[hanging=true]")
        bb.set(x, y0 - 5, (cz1 + cz2) // 2, "minecraft:barrel[facing=up,open=false]")
    bb.fill(cx1, y0 - 5, cz1 + 1, cx1, y0, cz1 + 1, "minecraft:ladder[facing=east]")
    bb.set(cx1, y0, cz1 + 1, "minecraft:ladder[facing=east]")
    # the terrace over the lake: an arcade along the north face
    for x in range(x1 - 2, x2 + 3):
        bb.fill(x, y0 - 1, z1 - 8, x, y0, z1 - 2, "minecraft:polished_deepslate")
        bb.set(x, y0 + 1, z1 - 8, "minecraft:deepslate_brick_wall")
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, 0, z1 - 8, x, y0 - 2, z1 - 8, DS)
        bb.fill(x + 1, y0 - 2, z1 - 8, x + 3, y0 - 2, z1 - 8, DS)
        bb.set(x + 1, y0 - 3, z1 - 8, st("minecraft:deepslate_brick_stairs", "west", "top"))
        bb.set(x + 3, y0 - 3, z1 - 8, st("minecraft:deepslate_brick_stairs", "east", "top"))
    for x in range(CX - 2, CX + 3):
        bb.set(x, y0 + 1, z1, AIR); bb.set(x, y0 + 2, z1, AIR)
    return (x1 - 9, z1 - 10, x2 + 9, G[3] + 2)


def yard(bb):
    x1, z1, x2, z2 = YARD
    NT.cover(bb, x1, z1, x2, z2, lambda X, Z: X * 0 + CROWN, [("minecraft:packed_mud", 0.3), ("minecraft:coarse_dirt", 0.3),
                                                             ("minecraft:gravel", 0.2), ("minecraft:podzol", 0.2)], 1841)
    for x in range(x1, x2 + 1):
        if abs(x - CX) > 3:
            bb.set(x, CROWN + 1, z2, "minecraft:deepslate_brick_wall")
    for z in range(z1, z2 + 1):
        bb.set(x1, CROWN + 1, z, "minecraft:deepslate_brick_wall"); bb.set(x2, CROWN + 1, z, "minecraft:deepslate_brick_wall")
    for (x, z) in ((x1, z2), (x2, z2), (CX - 4, z2), (CX + 4, z2)):
        bb.fill(x, CROWN + 1, z, x, CROWN + 3, z, DS)
        bb.set(x, CROWN + 4, z, "minecraft:soul_lantern[hanging=false]")
    # training dummies and the sword racks
    for (x, z) in ((x1 + 6, z1 + 6), (x1 + 12, z1 + 9), (x2 - 6, z1 + 6), (x2 - 12, z1 + 9), (x1 + 8, z2 - 5), (x2 - 8, z2 - 5)):
        bb.set(x, CROWN + 1, z, "minecraft:dark_oak_fence")
        bb.set(x, CROWN + 2, z, "minecraft:hay_block[axis=y]")
        bb.set(x, CROWN + 3, z, "minecraft:carved_pumpkin[facing=south]")
    for x in range(x1 + 2, x1 + 6):
        bb.set(x, CROWN + 1, z2 - 2, "minecraft:grindstone[face=floor,facing=north]")
        bb.set(x, CROWN + 2, z2 - 2, "minecraft:lightning_rod")
    bb.set(x2 - 3, CROWN + 1, z2 - 2, "minecraft:anvil[facing=north]")
    bb.set(x2 - 4, CROWN + 1, z2 - 2, "minecraft:smithing_table")


# ------------------------------------------------------------------ the ruins, graveyard, forest, jetty
def ruin(bb, x0, z0, w, d, rng, h=7):
    y = min(hy(x0, z0), hy(x0 + w, z0 + d), hy(x0, z0 + d), hy(x0 + w, z0))
    stones = ["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks", "minecraft:mossy_stone_bricks",
              "minecraft:cracked_stone_bricks"]
    bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:cobblestone")
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            edge = x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1)
            if not edge:
                bb.set(x, y, z, "minecraft:coarse_dirt" if rng.random() < 0.4 else "minecraft:spruce_planks" if rng.random() < 0.5 else "minecraft:moss_block")
                continue
            top = int(h * (0.35 + 0.65 * NT.noise(np.array([[x]]), np.array([[z]]), int(x0 * 7 + z0), 3)[0, 0]))
            for yy in range(y + 1, y + 1 + top):
                bb.set(x, yy, z, stones[int(rng.integers(0, len(stones)))])
            if (x + z) % 3 == 0 and top > 3 and not (x in (x0, x0 + w - 1) and z in (z0, z0 + d - 1)):
                bb.set(x, y + 3, z, AIR)
    bb.fill(x0 + w // 2, y + 1, z0 + d - 1, x0 + w // 2, y + 2, z0 + d - 1, AIR)
    for _ in range(int(w * d * 0.06)):                     # rubble and a fallen beam
        rx, rz = int(rng.integers(x0 + 1, x0 + w - 1)), int(rng.integers(z0 + 1, z0 + d - 1))
        bb.set(rx, y + 1, rz, ("minecraft:cobblestone_slab[type=bottom]", "minecraft:mossy_cobblestone", "minecraft:cobblestone_stairs[facing=north]")[int(rng.integers(0, 3))])
    bb.fill(x0 + 1, y + 1, z0 + 1, x0 + w - 2, y + 1, z0 + 1, "minecraft:stripped_dark_oak_log[axis=x]")


def town(bb, rng):
    taken = []
    spots = [(38, 124, 10, 8), (52, 128, 9, 9), (40, 140, 11, 9), (72, 134, 9, 8), (100, 126, 10, 9), (114, 132, 9, 8),
             (98, 142, 12, 10), (114, 146, 9, 8), (44, 152, 9, 7), (66, 150, 10, 7)]
    for (x, z, w, d) in spots:
        if SHORE(np.array([[x + w]]), np.array([[z + d]]))[0, 0] < 4:
            continue
        ruin(bb, x, z, w, d, rng, h=int(rng.integers(5, 9)))
        taken.append((x - 1, z - 1, x + w, z + d))
    return taken


def graveyard(bb, rng):
    x1, z1, x2, z2 = GRAVES
    y = hy((x1 + x2) // 2, (z1 + z2) // 2)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if abs(x - (x1 + x2) // 2) > 1:
                bb.set(x, hy(x, z) + 1, z, "minecraft:iron_bars")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            bb.set(x, hy(x, z) + 1, z, "minecraft:iron_bars")
    for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.fill(x, hy(x, z) + 1, z, x, hy(x, z) + 3, z, "minecraft:mossy_stone_bricks")
        bb.set(x, hy(x, z) + 4, z, "minecraft:soul_lantern[hanging=false]")
    k = 0
    for x in range(x1 + 3, x2 - 1, 4):
        for z in range(z1 + 3, z2 - 1, 4):
            if rng.random() < 0.15:
                continue
            g = hy(x, z)
            kind = k % 3
            if kind == 0:
                bb.set(x, g + 1, z, "minecraft:mossy_stone_brick_wall"); bb.set(x, g + 2, z, "minecraft:mossy_stone_brick_wall")
                bb.set(x - 1, g + 2, z, "minecraft:stone_button[face=wall,facing=west]") if False else None
            elif kind == 1:
                bb.set(x, g + 1, z, "minecraft:cobblestone_wall")
                bb.set(x, g + 2, z, "minecraft:stone_brick_slab[type=bottom]")
            else:
                bb.set(x, g + 1, z, "minecraft:chiseled_stone_bricks")
            bb.set(x, g, z + 1, "minecraft:coarse_dirt"); bb.set(x, g, z + 2, "minecraft:coarse_dirt")
            k += 1
    # a crypt
    cx, cz = x2 - 7, z1 + 3
    g = hy(cx, cz)
    bb.fill(cx - 3, g - 1, cz - 2, cx + 3, g + 4, cz + 3, "minecraft:mossy_stone_bricks")
    bb.fill(cx - 2, g + 1, cz - 1, cx + 2, g + 3, cz + 2, AIR)
    bb.fill(cx - 1, g + 1, cz + 3, cx + 1, g + 3, cz + 3, "minecraft:iron_bars")
    bb.fill(cx - 3, g + 5, cz - 2, cx + 3, g + 5, cz + 3, "minecraft:stone_brick_slab[type=bottom]")
    bb.set(cx, g + 1, cz, "minecraft:soul_lantern[hanging=false]")
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


def dead_tree(bb, x, y, z, h, rng):
    log = ("minecraft:dark_oak_log", "minecraft:spruce_log", "minecraft:stripped_dark_oak_log")[int(rng.integers(0, 3))]
    bb.fill(x, y - 1, z, x, y + h, z, log + "[axis=y]")
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 6.283)
        by = y + int(h * rng.uniform(0.45, 0.95))
        L = int(rng.integers(2, 5))
        for i in range(1, L + 1):
            bx, bz = x + int(round(math.cos(a) * i)), z + int(round(math.sin(a) * i))
            ax = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            bb.set(bx, by + i // 2, bz, log + f"[axis={ax}]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if rng.random() < 0.6:
            bb.set(x + dx, y, z + dz, log + "[axis=y]")


def forest(bb, rng, taken):
    k = 0
    for _ in range(6000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 2 or road_d(X, Z)[0, 0] < 4 or in_lake(X, Z, 3)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if y < 1:
            continue
        if NT.noise(X, Z, 1871, 18)[0, 0] < 0.35 and rng.random() < 0.7:
            continue
        if rng.random() < 0.7:
            dead_tree(bb, x, y + 1, z, int(rng.integers(5, 11)), rng)
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(8, 13)), "spruce", rng)
        taken.append((x - 2, z - 2, x + 2, z + 2))
        k += 1
        if k >= 130:
            break
    print("trees:", k)


def jetty(bb):
    x, z = JETTY
    zs = z
    while zs > 100 and hy(x, zs) < 1:
        zs -= 1
    for zz in range(zs - 1, min(N - 1, zs + 14)):
        bb.fill(x - 1, 0, zz, x + 1, 0, zz, "minecraft:dark_oak_planks")
        if zz % 4 == 0:
            bb.fill(x - 2, -8, zz, x - 2, 1, zz, "minecraft:dark_oak_log[axis=y]")
            bb.fill(x + 2, -8, zz, x + 2, 1, zz, "minecraft:dark_oak_log[axis=y]")
            bb.set(x + 2, 2, zz, "minecraft:soul_lantern[hanging=false]")
    # the coffin boat beside the jetty: black, coffin-shaped, a tall-backed seat and two green candles
    HALF = (1, 1, 1, 2, 2, 2, 2, 1, 1)
    hull = "minecraft:polished_blackstone"
    bx, bz0 = x + 5, zs + 3
    for i, hw in enumerate(HALF):
        zz = bz0 + i
        for xx in range(bx - hw, bx + hw + 1):
            bb.set(xx, -1, zz, hull); bb.set(xx, 0, zz, "minecraft:black_concrete")
            edge = abs(xx - bx) == hw or i in (0, len(HALF) - 1)
            bb.set(xx, 1, zz, hull if edge else AIR)
    zh = bz0 + len(HALF) - 1
    bb.set(bx, 1, zh - 1, st("minecraft:dark_oak_stairs", "north"))
    for yy in (2, 3):
        bb.set(bx, yy, zh, hull)
    bb.set(bx, 4, zh, "minecraft:polished_blackstone_wall")
    for xx in (bx - 1, bx + 1):
        bb.set(xx, 2, bz0 + 1, "minecraft:polished_blackstone_wall")
        bb.set(xx, 3, bz0 + 1, "minecraft:green_candle[candles=3,lit=true]")
    return (x - 4, zs - 4, x + 9, zs + 14)


def design():
    bb = BigBuild(seed=1820, y_min=-14, y_max=100)
    tracker = P.PropTracker(1820)
    audit = []
    rng = np.random.default_rng(1820)
    terrain(bb)
    for hc in HILLS:
        curl_hill(bb, hc, rng)
    taken = [(hc[0] - hc[2] - 2, hc[1] - hc[2] - 2, hc[0] + hc[2] + 2, hc[1] + hc[2] + 2) for hc in HILLS]
    taken.append(castle(bb, tracker, audit, rng))
    yard(bb)
    taken.append(YARD)
    taken += town(bb, rng)
    taken.append(graveyard(bb, rng))
    taken.append(jetty(bb))
    forest(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1890, density=0.18,
              kinds=["minecraft:short_grass", "minecraft:fern", "minecraft:dead_bush", "minecraft:short_grass", "minecraft:large_fern",
                     "minecraft:brown_mushroom", "minecraft:red_mushroom"],
              flowers=["minecraft:wither_rose", "minecraft:lily_of_the_valley"],
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, PLAT) > 2) & (road_d(X, Z) > 2.5))
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
    b.npc(CX, CROWN + 1, K[1] + 7, "mihawk", True)
    b.chest(K[2] - 4, CROWN + 2 * FH + 1, K[1] + 2, "legendary", "west")
    b.chest(K[2] - 6, CROWN - 5, K[1] + 6, "legendary", "south")
    for (gx, gz) in ((CX - 10, YARD[1] + 6), (CX + 12, YARD[1] + 5)):
        b.guard(gx, CROWN + 1, gz, "humandrill")
    for (gx, gz) in ((40, 100), (130, 140), (60, 160), (150, 120), (30, 120)):
        if land(np.array([[gx]]), np.array([[gz]]))[0, 0]:
            b.guard(gx, hy(gx, gz) + 1, gz, "humandrill")
    return b, 0
