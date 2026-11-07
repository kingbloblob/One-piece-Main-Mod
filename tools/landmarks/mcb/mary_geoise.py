"""Mary Geoise v3 (2026-10-30 redo: the Red Line now towers 130 blocks over the Red Port), the Holy Land on top of
the Red Line (dossier: mcb/dossiers/mary_geoise.md).

The Red Line is a colossal wall of banded red rock running east-west across the site: sheer faces on the south (over
the Red Port) and the north (straight into the sea), its east and west ends stepping down in eroded terraces before
the site edge, the whole thing ringed by sea. Up the south face climb the
Bondola lift (a glass bubble cabin in a white-and-gold frame) and a switchback stair tunnel with windows. On top,
behind the Holy Gate, lawns, white avenues and fountains lead to Pangaea Castle: a Chambord-like white palace with
round corner towers, slate cones, chimney spires and a central lantern tower with a gold dome; inside, the hall of
the Empty Throne ringed by the twenty swords, the Five Elders' chamber, libraries, state rooms, Im's flower room in the
lantern tower, and under the castle the freezer room with the giant straw hat. Six Celestial Dragon mansions with
porticos and gardens; the slave quarters hidden in the rock beneath them. Below: the Red Port with warehouses, the
customs house, the Bondola station and a walled harbour where a Marine warship (the real ship template) is moored.
200 x 200. y 0 = the Red Port and the sea; the Holy Land is at y 130. (v3)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, lamp_post, cornice, tier, wing_floor, \
    house_module, place_house, wg_emblem
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import terrain3 as T3
from mcb.shipstamp import stamp_ship
from mcb.lotpack import pack_houses

SID = "mary_geoise"
TITLE = "Mary Geoise (the Holy Land on the Red Line)"
CUTS = [3, 49, 57, 66]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False

N = 200
TOP = 130
CXC, CZC = 100, 64                         # Pangaea Castle centre
GATE_Z = 112
LIFT_X = 110
Q = "minecraft:smooth_quartz"
QB = "minecraft:quartz_bricks"
QP = "minecraft:quartz_pillar[axis=y]"
QST = "minecraft:smooth_quartz_stairs"
GOLD = "minecraft:gold_block"
SLATE_ST = "minecraft:deepslate_tile_stairs"
SLATE = "minecraft:deepslate_tiles"
WIN = "minecraft:light_blue_stained_glass_pane"
STRATA = T3.RED_STRATA
LAWN = [("minecraft:grass_block", 0.86), ("minecraft:moss_block", 0.05), ("minecraft:rooted_dirt", 0.04),
        ("minecraft:coarse_dirt", 0.05)]
PORT = [("minecraft:stone_bricks", 0.3), ("minecraft:polished_andesite", 0.16), ("minecraft:cobblestone", 0.14),
        ("minecraft:mossy_cobblestone", 0.06), ("minecraft:gravel", 0.08), ("minecraft:grass_block", 0.14),
        ("minecraft:coarse_dirt", 0.12)]


# ------------------------------------------------------------------ the Red Line
def cliff_z(X):
    return 126 + 2 * np.sin(X * 0.13) + np.sin(X * 0.31 + 1)


def back_z(X):
    return 13 + 3 * NT.noise(np.asarray(X, float), np.zeros_like(np.asarray(X, float)), 706, 11) + np.sin(np.asarray(X, float) * 0.21)


def height(X, Z):
    """The Red Line: TOP between a sheer north face (back_z) and a sheer south face (cliff_z) with a few ledges, its
    ends terraced down to the sea before the site edge. South of the face: the Red Port at 0 inside a rough
    half-oval; everywhere else -1 (sea)."""
    X = np.asarray(X, float)
    Z = np.asarray(Z, float)
    X, Z = np.broadcast_arrays(X, Z)
    e = np.clip((np.minimum(X, N - 1 - X) - 8) / 30.0, 0, 1)
    tops = TOP * (np.floor(e * 8) / 8.0) + np.round(3 * NT.noise(X, Z, 705, 5)) * (e < 1)
    zb, zc = back_z(X), cliff_z(X)
    wall = (Z >= zb) & (Z <= zc)
    h = np.where(wall, np.clip(tops, 0, TOP), -1.0)
    # ledges at the foot of both faces (a third and a tenth of the height)
    for (dz, frac, sd) in ((3, 0.34, 707), (6, 0.1, 708)):
        n = 2 * NT.noise(X, Z, sd, 6)
        ls = (Z > zc) & (Z <= zc + dz + n) & (np.abs(X - LIFT_X) > 7)
        ln = (Z < zb) & (Z >= zb - dz - n)
        h = np.where(ls | ln, np.maximum(h, np.round(tops * frac)), h)
    h = np.where(wall & (e >= 1), TOP, h)
    port = (Z > zc) & (np.abs(X - 100) < 76 - 8 * NT.noise(X, Z, 709, 13)) & (Z < 186 - 5 * NT.noise(X, Z, 711, 9))
    h = np.where(port & (h <= 0), 0, h)
    return np.round(h)


def terrain(bb):
    H = height(np.arange(N)[:, None], np.arange(N)[None, :])
    off = np.round(3 * NT.noise(np.arange(N)[:, None], np.arange(N)[None, :], 710, 17)).astype(int)
    for y in range(-4, 1):                                           # the port's ground is soil, not rock
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: H[X[:, 0]][:, Z[0, :]] == 0, "minecraft:dirt")
    for y in range(-14, TOP + 1):
        band = ((y + off) // 3) % len(STRATA)
        for k in set(np.unique(band).tolist()):
            m = (H >= y) & (band == k) & (H > 0)
            if m.any():
                bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z, m=m: m, STRATA[k])
    hf = lambda X, Z: H[X[:, 0]][:, Z[0, :]] if np.ndim(X) == 2 else H[X, Z]
    plateau = lambda X, Z: hf(X, Z) == TOP
    slopes = lambda X, Z: (hf(X, Z) > 0) & (hf(X, Z) < TOP)
    port = lambda X, Z: hf(X, Z) == 0
    NT.cover(bb, 0, 0, N - 1, N - 1, hf, LAWN, 711, mask=plateau, under="minecraft:dirt", depth=2)
    NT.cover(bb, 0, 0, N - 1, N - 1, hf, NT.BADLANDS, 712, mask=slopes, under="minecraft:red_terracotta", depth=1)
    NT.cover(bb, 0, 0, N - 1, N - 1, hf, NT.MEADOW, 713, mask=port,
             under="minecraft:dirt")
    basin = np.zeros((N, N), bool); basin[72:151, 158:185] = True
    T3.sea(bb, N, (H >= 0) | basin, 100, 100, 104, 715, deep=-18, shelf=14, y_min=-24)
    return H, hf


# ------------------------------------------------------------------ Pangaea Castle
def castle(bb, tracker, audit):
    y0 = TOP
    x1, x2, z1, z2 = CXC - 26, CXC + 26, CZC - 16, CZC + 16
    fh = 7
    top = tier(bb, x1, z1, x2, z2, y0, 3, fh, [Q, QB, Q], WIN, QST, pilaster=QP, band=GOLD, plate=QB,
               top_plate=Q, weights=[0.6, 0.3, 0.1], every=3, pil_every=4, win_h=3)
    bb.fill(x1 - 3, y0 - 2, z1 - 3, x2 + 3, y0, z2 + 3, QB)               # terrace the palace stands on
    bb.fill(x1 - 3, y0, z1 - 3, x2 + 3, y0, z2 + 3, Q)
    cornice(bb, x1, z1, x2, z2, top, QST, parapet="minecraft:quartz_slab[type=bottom]")
    P.hip_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, SLATE_ST)
    for x in range(x1 + 6, x2 - 4, 8):                                  # Chambord chimney spires on the roof
        for z in (z1 + 4, z2 - 4):
            bb.fill(x, top + 1, z, x + 1, top + 13, z + 1, QB)
            bb.fill(x - 1, top + 13, z - 1, x + 2, top + 13, z + 2, Q)
            bb.set(x, top + 14, z, GOLD)
            bb.set(x + 1, top + 14, z + 1, GOLD)
    # the four round corner towers with slate cones and gold finials
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(tx, y0 + 1, tz, 6, top + 6, Q)
        bb.cylinder(tx, y0 + 1, tz, 5, top + 6, AIR)
        for k in range(1, 5):
            bb.fill(tx, y0 + k * fh, tz, tx, y0 + k * fh, tz, QB)
            bb.cylinder(tx, y0 + k * fh if k < 4 else top + 6, tz, 5, y0 + k * fh if k < 4 else top + 6, QB)
        for k in range(4):                                           # tower windows on every storey, four sides
            for (dx, dz) in ((6, 0), (-6, 0), (0, 6), (0, -6)):
                bb.fill(tx + dx, y0 + 3 + k * fh, tz + dz, tx + dx, y0 + 5 + k * fh, tz + dz, WIN)
        bb.ring(tx, top + 6, tz, 6, 7, top + 6, GOLD)
        P.cone_roof(bb, tx, top + 7, tz, 7, 16, SLATE)
        bb.fill(tx, top + 23, tz, tx, top + 26, tz, GOLD)
    # inside: towers open into the palace on every floor
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        sx = 1 if tx == x1 else -1
        sz = 1 if tz == z1 else -1
        for k in range(3):
            fy = y0 + 1 + k * fh
            bb.fill(tx + sx * 5, fy, tz + sz * 2, tx + sx * 6, fy + 2, tz + sz * 3, AIR)
    # the central lantern tower: rises from the roof, gold dome, lantern and spire; Im's flower room inside
    lx, lz, lr = CXC, CZC, 8
    ly0 = top + 1
    bb.cylinder(lx, ly0, lz, lr, ly0 + 18, Q)
    bb.cylinder(lx, ly0, lz, lr - 1, ly0 + 18, AIR)
    for a in range(0, 360, 30):
        t = math.radians(a)
        px, pz = round(lx + lr * math.cos(t)), round(lz + lr * math.sin(t))
        bb.fill(px, ly0, pz, px, ly0 + 18, pz, QP)
        wx, wz = round(lx + lr * math.cos(t + 0.26)), round(lz + lr * math.sin(t + 0.26))
        bb.fill(wx, ly0 + 4, wz, wx, ly0 + 13, wz, WIN)
    bb.ring(lx, ly0 + 18, lz, lr - 1, lr + 1, ly0 + 18, GOLD)
    bb.dome(lx, ly0 + 19, lz, lr, GOLD)
    bb.cylinder(lx, ly0 + 19 + lr, lz, 2, ly0 + 25 + lr, Q)
    bb.cylinder(lx, ly0 + 26 + lr, lz, 2, ly0 + 26 + lr, GOLD)
    bb.fill(lx, ly0 + 27 + lr, lz, lx, ly0 + 31 + lr, lz, GOLD)
    flower_room(bb, lx, ly0, lz, lr)
    # ground floor: the hall of the Empty Throne (two storeys), libraries, the Five Elders' chamber
    gy = y0 + 1
    hx1, hx2, hz1, hz2 = CXC - 9, CXC + 9, z1 + 1, z2 - 1
    bb.fill(hx1, gy, hz1, hx2, y0 + 2 * fh - 1, hz2, AIR)
    bb.fill(hx1 - 1, gy, hz1, hx1 - 1, y0 + 2 * fh - 1, hz2, QB)
    bb.fill(hx2 + 1, gy, hz1, hx2 + 1, y0 + 2 * fh - 1, hz2, QB)
    bb.fill(CXC - 2, gy, z2, CXC + 2, gy + 4, z2 + 1, AIR)              # the great door (south), sills cleared
    bb.fill(CXC - 3, gy + 5, z2 + 1, CXC + 3, gy + 5, z2 + 1, GOLD)
    for x in (CXC - 3, CXC + 3):
        bb.fill(x, gy, z2 + 1, x, gy + 4, z2 + 1, QP)
    for k in range(4):
        bb.fill(CXC - 4, y0 - k, z2 + 4 + k, CXC + 4, y0 - k, z2 + 4 + k, st(QST, "north"))
    bb.fill(CXC - 1, y0, hz1, CXC + 1, y0, hz2, "minecraft:red_wool")        # the red carpet... as a floor stripe
    bb.fill(CXC - 1, gy, hz1 + 6, CXC + 1, gy, hz2, "minecraft:red_carpet")
    # the Empty Throne on its dais, the twenty swords of the founding kings round it
    tz = hz1 + 3
    bb.fill(CXC - 4, gy, hz1, CXC + 4, gy, tz + 2, QB)
    bb.fill(CXC - 2, gy + 1, hz1, CXC + 2, gy + 1, tz, QB)
    bb.set(CXC, gy + 2, tz - 1, st("minecraft:quartz_stairs", "north"))
    bb.fill(CXC - 1, gy + 2, tz - 2, CXC + 1, gy + 5, tz - 2, GOLD)
    bb.set(CXC, gy + 6, tz - 2, GOLD)
    bb.set(CXC - 1, gy + 2, tz - 1, "minecraft:quartz_slab[type=bottom]")
    bb.set(CXC + 1, gy + 2, tz - 1, "minecraft:quartz_slab[type=bottom]")
    for k in range(20):
        a = math.radians(k * 18)
        sx, sz = round(CXC + 7 * math.cos(a)), round(tz + 2 + 6 * math.sin(a))
        if hz1 < sz < hz2 and hx1 <= sx <= hx2 and abs(sx - CXC) + abs(sz - tz) > 3:
            g = bb.get_region(sx, gy, sz, sx, gy, sz)[0, 0, 0]
            yy = gy if g in (0, 1) else gy + 1
            bb.set(sx, yy, sz, "minecraft:end_rod[facing=up]")
    for z in range(hz1 + 7, hz2, 5):                                     # hall columns, gold capitals, chandeliers
        for x in (hx1 + 1, hx2 - 1):
            bb.fill(x, gy, z, x, y0 + 2 * fh - 1, z, QP)
            bb.set(x, y0 + 2 * fh - 1, z, GOLD)
        bb.fill(CXC, gy + 6, z, CXC, y0 + 2 * fh - 1, z, "minecraft:iron_chain[axis=y]")
        bb.set(CXC, gy + 5, z, "onepiece:chandelier[facing=north]")
        for x in (hx1 + 2, hx2 - 2):
            bb.set(x, gy, z + 2, "onepiece:candelabra[facing=north]")
    wg_emblem(bb, CXC, y0 + 2 * fh - 3, hz1, GOLD, k=0.5, axis="x")
    # the wings: ground floor offices and libraries, the Five Elders' chamber, upper floors of state rooms
    for (a1, a2, kinds) in ((x1 + 2, hx1 - 2, ["library", "living", "storage", "library"]),
                            (hx2 + 2, x2 - 2, ["living", "library", "kitchen", "storage"])):
        for k in range(3):
            fy = y0 + 1 + k * fh
            wing_floor(bb, a1, z1 + 1, a2, z2 - 1, fy, fh - 1, QB, seed_of("pc", a1, k), tracker, kinds if k < 2 else
                       ["bedroom", "living", "bedroom", "kitchen"], corridor="z", cw=3,
                       carpet=(None, "minecraft:red_carpet"), wood="birch", audit=audit, max_room=10)
            bb.fill(a2 + 1, fy, CZC + 6, a2 + 1, fy + 2, CZC + 7, AIR) if a1 < CXC else bb.fill(a1 - 1, fy, CZC + 6, a1 - 1, fy + 2, CZC + 7, AIR)
    # third floor over the throne hall: the Five Elders' chamber (round table of five) and the gallery
    ey = y0 + 2 * fh + 1
    bb.fill(hx1, ey, hz1, hx2, ey + fh - 2, hz2, AIR)
    bb.cylinder(CXC, ey, CZC + 4, 2, ey, "minecraft:dark_oak_planks")
    for k in range(5):
        a = math.radians(k * 72 - 90)
        bb.set(round(CXC + 4 * math.cos(a)), ey, round(CZC + 4 + 4 * math.sin(a)),
               f"minecraft:dark_oak_stairs[facing={('south', 'west', 'north', 'north', 'east')[k]},half=bottom]")
    bb.set(CXC, ey + 1, CZC + 4, "minecraft:candle[candles=3,lit=true]")
    for z in range(hz1 + 2, hz2 - 1, 6):
        bb.set(CXC - 6, ey + fh - 3, z, "minecraft:lantern[hanging=true]")
        bb.set(CXC + 6, ey + fh - 3, z, "minecraft:lantern[hanging=true]")
    furnish(bb, [(hx1 + 1, hz1 + 1, hx2 - 1, CZC - 4)], ey, fh - 2, ["library"], seed_of("elders"), tracker, audit=audit)
    # stairs between the floors: a walled spiral in each wing beside the throne hall
    for sx in (hx1 - 6, hx2 + 2):
        bb.fill(sx - 1, y0 + 1, z1 + 2, sx + 4, y0 + 3 * fh, z1 + 7, AIR)
        P.square_spiral_stair(bb, sx, y0 + 1, z1 + 3, 4, y0 + 2 * fh, QST, core=QB, headroom=3)
    # a ladder from the third floor up into the lantern tower
    bb.fill(CXC - 7, ey, CZC - 1, CXC - 7, top, CZC - 1, AIR)
    bb.fill(CXC - 7, ey, CZC - 1, CXC - 7, top + 1, CZC - 1, "minecraft:ladder[facing=east]")
    freezer(bb)
    return (x1 - 8, z1 - 8, x2 + 8, z2 + 10)


def flower_room(bb, lx, ly0, lz, lr):
    """Im's flower room in the lantern tower: a carpet of white and blue flowers on moss round a black dais."""
    rng = np.random.default_rng(708)
    bb.cylinder(lx, ly0, lz, lr - 1, ly0, "minecraft:moss_block")
    for _ in range(90):
        a, rr = rng.uniform(0, 6.283), rng.uniform(1.5, lr - 1.5)
        x, z = round(lx + rr * math.cos(a)), round(lz + rr * math.sin(a))
        if abs(x - (lx - 7)) <= 1 and abs(z - (lz - 1)) <= 1:
            continue
        set_if_air(bb, x, ly0 + 1, z, ("minecraft:white_tulip", "minecraft:lily_of_the_valley", "minecraft:azure_bluet",
                                       "minecraft:blue_orchid", "minecraft:oxeye_daisy")[int(NT.noise(x // 3, z // 3, 709, 1) * 4.99)])
    bb.fill(lx - 1, ly0 + 1, lz - 1, lx + 1, ly0 + 1, lz + 1, "minecraft:obsidian")
    bb.set(lx, ly0 + 2, lz, "minecraft:crying_obsidian")
    for (dx, dz) in ((-2, -2), (2, 2)):
        bb.set(lx + dx, ly0 + 1, lz + dz, "minecraft:candle[candles=2,lit=true]")
    bb.fill(lx, ly0 + 14, lz, lx, ly0 + 17, lz, "minecraft:iron_chain[axis=y]")
    bb.set(lx, ly0 + 13, lz, "onepiece:chandelier[facing=north]")


def freezer(bb):
    """Under the castle: the freezer room with the giant straw hat, reached by a stair from the throne hall's west."""
    fx1, fx2, fz1, fz2 = CXC - 12, CXC + 12, CZC - 10, CZC + 8
    fy = TOP - 13
    bb.fill(fx1 - 1, fy - 1, fz1 - 1, fx2 + 1, fy + 10, fz2 + 1, "minecraft:packed_ice")
    bb.fill(fx1, fy, fz1, fx2, fy + 9, fz2, AIR)
    bb.fill(fx1, fy - 1, fz1, fx2, fy - 1, fz2, "minecraft:blue_ice")
    bb.mix(fx1, fy, fz1, fx2, fy, fz2, ["minecraft:snow[layers=1]", "minecraft:air", "minecraft:snow[layers=2]"], [0.4, 0.45, 0.15])
    hx, hz = CXC, CZC - 1
    bb.cylinder(hx, fy, hz, 2, fy + 1, "minecraft:packed_ice")
    bb.cylinder(hx, fy + 2, hz, 7, fy + 2, "minecraft:yellow_terracotta")     # the brim of the giant straw hat
    bb.cylinder(hx, fy + 3, hz, 4, fy + 3, "minecraft:red_terracotta")        # the red band
    bb.cylinder(hx, fy + 4, hz, 4, fy + 6, "minecraft:yellow_terracotta")     # the crown
    bb.cylinder(hx, fy + 7, hz, 3, fy + 7, "minecraft:yellow_terracotta")
    for (x, z) in ((fx1 + 2, fz1 + 2), (fx2 - 2, fz1 + 2), (fx1 + 2, fz2 - 2), (fx2 - 2, fz2 - 2)):
        bb.fill(x, fy, z, x, fy + 9, z, "minecraft:blue_ice")
    for x in range(fx1 + 3, fx2 - 1, 5):                               # sea lanterns set in the ice walls
        for z in (fz1 - 1, fz2 + 1):
            bb.set(x, fy + 3, z, "minecraft:sea_lantern")
    for z in range(fz1 + 3, fz2 - 1, 5):
        for x in (fx1 - 1, fx2 + 1):
            bb.set(x, fy + 3, z, "minecraft:sea_lantern")
    # the stair down from the castle's ground floor (west wing corridor) to the freezer
    sx = CXC - 13
    for i in range(14):
        z = CZC + 15 - i
        y = TOP - i
        bb.fill(sx - 1, y, z, sx + 1, y, z, st("minecraft:quartz_stairs", "south"))
        bb.fill(sx - 1, y + 1, z, sx + 1, y + 3, z, AIR)
        bb.fill(sx - 2, y - 1, z, sx - 2, y + 4, z, "minecraft:packed_ice")
        bb.fill(sx + 2, y - 1, z, sx + 2, y + 4, z, "minecraft:packed_ice")
    bb.fill(sx - 1, fy, CZC + 1, sx + 1, fy + 3, CZC + 2, AIR)


# ------------------------------------------------------------------ the Holy Land
def mansion(seed, w, d, tracker, audit):
    """A Celestial Dragon mansion, door south: two white storeys with quartz pilasters and gold bands, light-blue
    windows with sills, a columned portico with a pediment, a slate hip roof with a gold ridge and a small gold dome,
    rooms on both floors (bsp, furnished) and a ladder up."""
    m = BigBuild(seed=seed, y_min=-3, y_max=40)
    fh = 6
    top = tier(m, 0, 0, w - 1, d - 1, 0, 2, fh, [Q, QB], WIN, QST, pilaster=QP, band=GOLD, plate=QB,
               top_plate=Q, weights=[0.7, 0.3], every=3, pil_every=4, win_h=2)
    m.fill(-2, -3, -2, w + 1, 0, d + 4, QB)
    m.fill(-2, 0, -2, w + 1, 0, d + 4, Q)
    cornice(m, 0, 0, w - 1, d - 1, top, QST)
    P.hip_roof(m, -1, -1, w, d, top + 1, SLATE_ST)
    dx = w // 2
    for x in (dx - 4, dx - 1, dx + 1, dx + 4):                         # the portico
        m.fill(x, 1, d + 2, x, fh * 2 - 2, d + 2, QP)
    m.fill(dx - 5, fh * 2 - 1, d, dx + 5, fh * 2 - 1, d + 3, Q)
    for k in range(4):
        m.fill(dx - 5 + k, fh * 2 + k, d + 3, dx + 5 - k, fh * 2 + k, d + 3, QB)
    m.set(dx, fh * 2 + 1, d + 3, GOLD)
    m.fill(dx - 1, 1, d - 1, dx + 1, 3, d - 1, AIR)
    rooms_all = []
    for f in range(2):
        fy = 1 + f * fh
        rms, doors = P.bsp_rooms(m, 1, 1, w - 2, d - 2, fy, fh - 1, QB, min_room=5, seed=seed + f, max_room=10)
        doors = list(doors) + ([(dx, d - 1)] if f == 0 else []) + [(1, 1)]
        furnish(m, rms, fy, fh - 1, ["living", "kitchen", "library"] if f == 0 else ["bedroom", "living", "bedroom"],
                seed + 10 * f, tracker, doors=doors, wood="birch", audit=audit)
        rooms_all += rms
    m.fill(1, 1, 1, 1, fh + 1, 1, "minecraft:ladder[facing=east]")
    m.set(1, fh, 1, "minecraft:ladder[facing=east]")
    m.cylinder(dx, top + 1, d // 2, 2, top + 1, GOLD)
    m.dome(dx, top + 2, d // 2, 2, GOLD)
    return m


def fountain(bb, x, y, z, r=5):
    bb.cylinder(x, y, z, r, y, QB)
    bb.cylinder(x, y, z, r - 1, y, "minecraft:water")
    bb.cylinder(x, y - 1, z, r, y - 1, QB)
    bb.fill(x, y, z, x, y + 3, z, QP)
    bb.cylinder(x, y + 4, z, 1, y + 4, "minecraft:quartz_slab[type=bottom]")
    bb.set(x, y + 4, z, GOLD)
    bb.set(x, y + 5, z, "minecraft:water")


def holy_land(bb, tracker, audit, rng):
    y = TOP
    # white avenues: the boulevard gate -> castle, a cross avenue; worn edges blend into the lawn
    pav = [(Q, 0.5), (QB, 0.3), ("minecraft:quartz_block", 0.2)]
    NT.cover(bb, CXC - 5, CZC + 20, CXC + 5, GATE_Z + 6, lambda X, Z: np.full(np.broadcast(X, Z).shape, y), pav, 720)
    NT.cover(bb, 50, 96, 150, 102, lambda X, Z: np.full(np.broadcast(X, Z).shape, y), pav, 721)
    for z in range(CZC + 22, GATE_Z, 6):
        for x in (CXC - 7, CXC + 7):
            lamp_post(bb, x, y + 1, z, post="minecraft:diorite_wall",
                      h=3, light="minecraft:lantern[hanging=false]")
    fountain(bb, CXC, y, 99, 6)
    for (sx, sz) in ((CXC - 14, 92), (CXC + 14, 92)):                      # statues of the founding kings
        bb.fill(sx - 1, y + 1, sz - 1, sx + 1, y + 2, sz + 1, QB)
        bb.fill(sx, y + 3, sz, sx, y + 7, sz, Q)
        bb.set(sx - 1, y + 6, sz, Q); bb.set(sx + 1, y + 6, sz, Q)
        bb.set(sx, y + 8, sz, "minecraft:quartz_block"); bb.set(sx, y + 9, sz, GOLD)
    # the six mansions with hedged gardens
    spots = [(46, 52, 22, 15, 0), (134, 52, 22, 15, 0), (46, 76, 20, 13, 0), (134, 76, 20, 13, 0),
             (52, 104, 20, 13, 0), (128, 104, 20, 13, 0)]
    for i, (x0, z0, w, d, rot) in enumerate(spots):
        m = mansion(seed_of("mansion", i), w, d, tracker, audit)
        bb.stamp(m, x0, y, z0, rot=0, include_air=True)
        # hedge round its garden, a gap at the portico
        gx1, gz1, gx2, gz2 = x0 - 4, z0 - 3, x0 + w + 3, z0 + d + 7
        for x in range(gx1, gx2 + 1):
            for z in (gz1, gz2):
                if not (z == gz2 and abs(x - (x0 + w // 2)) <= 2):
                    set_if_air(bb, x, y + 1, z, "minecraft:azalea_leaves[persistent=true]")
        for z in range(gz1, gz2 + 1):
            for x in (gx1, gx2):
                set_if_air(bb, x, y + 1, z, "minecraft:azalea_leaves[persistent=true]")
        for k in range(6):
            fx, fz = int(rng.integers(gx1 + 1, gx2)), int(rng.integers(z0 + d + 5, gz2))
            if (bb.get_region(fx, y + 1, fz, fx, y + 2, fz) > 1).any():
                continue
            kind = ("rose_bush", "peony", "flowering_azalea", "lilac")[k % 4]
            if kind == "flowering_azalea":
                bb.set(fx, y + 1, fz, "minecraft:flowering_azalea")
            else:
                bb.set(fx, y + 1, fz, f"minecraft:{kind}[half=lower]")
                bb.set(fx, y + 2, fz, f"minecraft:{kind}[half=upper]")
    # garden trees on the lawns
    for _ in range(40):
        x, z = int(rng.integers(44, 156)), int(rng.integers(46, 120))
        g = bb.get_region(x - 2, y + 1, z - 2, x + 2, y + 3, z + 2)
        if (g > 1).any() or abs(x - CXC) < 12:
            continue
        P.tree(bb, x, y + 1, z, int(rng.integers(5, 8)), ("cherry", "birch", "oak")[int(rng.integers(3))], rng)
    # the slave quarters in the rock under the west lawn, a hatch and ladder down
    sx1, sx2, sz1, sz2 = 48, 72, 88, 100
    sy = TOP - 9
    bb.fill(sx1 - 1, sy - 1, sz1 - 1, sx2 + 1, sy + 6, sz2 + 1, "minecraft:polished_deepslate")
    bb.fill(sx1, sy, sz1, sx2, sy + 5, sz2, AIR)
    rms, doors = P.bsp_rooms(bb, sx1, sz1, sx2, sz2, sy, 5, "minecraft:polished_deepslate", min_room=5, seed=seed_of("slaves"), max_room=8)
    furnish(bb, rms, sy, 5, ["storage", "workshop", "bedroom", "storage"], seed_of("slavesf"), tracker, doors=list(doors) + [(sx2 - 1, sz2 - 1)],
            wood="spruce", audit=audit)
    bb.fill(sx2 - 1, sy, sz2 - 1, sx2 - 1, TOP, sz2 - 1, "minecraft:ladder[facing=north]")
    bb.set(sx2 - 1, TOP + 1, sz2 - 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")


def holy_gate(bb):
    """The Holy Gate at the head of the Bondola: a white wall-block with a great arch, two towers with gold domes,
    the World Government emblem over the arch."""
    y = TOP
    gz = GATE_Z
    bb.fill(CXC - 16, y + 1, gz, CXC + 16, y + 20, gz + 5, Q)
    P.arched_opening(bb, "x", CXC, y + 1, gz, 11, 15, depth=6, trim=GOLD)
    for x in range(CXC - 16, CXC + 17, 4):
        bb.set(x, y + 20, gz - 1, st(QST, "south", "top"))
        bb.set(x, y + 21, gz, "minecraft:quartz_slab[type=bottom]")
    for tx in (CXC - 19, CXC + 19):
        bb.fill(tx - 3, y + 1, gz - 1, tx + 3, y + 28, gz + 6, QB)
        bb.fill(tx - 2, y + 1, gz, tx + 2, y + 27, gz + 5, AIR)
        for yy in range(y + 5, y + 26, 6):
            bb.fill(tx, yy, gz - 1, tx, yy + 2, gz - 1, WIN)
            bb.fill(tx, yy, gz + 6, tx, yy + 2, gz + 6, WIN)
        bb.fill(tx - 3, y + 28, gz - 1, tx + 3, y + 28, gz + 6, GOLD)
        bb.dome(tx, y + 29, gz + 2, 3, GOLD)
        bb.fill(tx, y + 32, gz + 2, tx, y + 35, gz + 2, GOLD)
    wg_emblem(bb, CXC, y + 19, gz - 1, GOLD, k=0.45, axis="x")


# ------------------------------------------------------------------ up the cliff
def bondola(bb):
    """The Bondola lift on the cliff face: a white frame with gold bands, cables, the glass bubble cabin halfway up,
    stations at the top (by the Holy Gate) and at the Red Port."""
    x = LIFT_X
    zc = int(cliff_z(np.array([x]))[0])
    z1, z2 = zc + 1, zc + 7
    for (px, pz) in ((x - 4, z1), (x + 4, z1), (x - 4, z2), (x + 4, z2)):
        bb.fill(px, 0, pz, px, TOP + 8, pz, "minecraft:white_concrete")
    for yy in range(0, TOP + 9, 8):
        bb.fill(x - 4, yy, z1, x + 4, yy, z1, GOLD if yy % 16 == 0 else "minecraft:white_concrete")
        bb.fill(x - 4, yy, z2, x + 4, yy, z2, GOLD if yy % 16 == 0 else "minecraft:white_concrete")
        bb.fill(x - 4, yy, z1, x - 4, yy, z2, "minecraft:white_concrete")
        bb.fill(x + 4, yy, z1, x + 4, yy, z2, "minecraft:white_concrete")
    bb.fill(x - 4, TOP + 8, z1, x + 4, TOP + 8, z2, "minecraft:white_concrete")
    for cx in (x - 1, x + 1):
        bb.fill(cx, 2, (z1 + z2) // 2, cx, TOP + 7, (z1 + z2) // 2, "minecraft:iron_chain[axis=y]")
    # three bubble cabins on the way up (the anime shows several gondolas on the cables)
    for cy in (TOP // 4, TOP // 2 + 3, 3 * TOP // 4):
        cabin(bb, x, cy, (z1 + z2) // 2)
    for yy in range(12, TOP, 24):                                   # gold lamps on the frame
        bb.set(x - 4, yy, z2 + 1, "minecraft:sea_lantern")
        bb.set(x + 4, yy, z2 + 1, "minecraft:sea_lantern")
    station(bb, x, z1, z2)


def cabin(bb, x, cy, cz):
    if True:
        bb.fill_where(x - 3, cy - 3, cz - 3, x + 3, cy + 3, cz + 3,
                      lambda X, yy, Z: ((X - x) ** 2 + (yy - cy) ** 2 + (Z - cz) ** 2 <= 9.5) & ((X - x) ** 2 + (yy - cy) ** 2 + (Z - cz) ** 2 > 4.5),
                      "minecraft:light_blue_stained_glass")
        bb.fill(x - 2, cy - 2, cz - 2, x + 2, cy - 2, cz + 2, GOLD)
        bb.fill(x - 1, cy - 1, cz - 1, x + 1, cy - 1, cz + 1, "minecraft:white_carpet")
        bb.set(x, cy + 3, cz, GOLD)


def station(bb, x, z1, z2):
    # bottom station: a small white hall with a gold roof band
    bb.fill(x - 7, 0, z2 + 1, x + 7, 0, z2 + 10, Q)
    for (a, b) in ((x - 7, z2 + 10), (x + 7, z2 + 10)):
        bb.fill(a, 1, b, a, 6, b, QP)
    bb.fill(x - 7, 7, z1, x + 7, 7, z2 + 10, Q)
    bb.fill(x - 7, 8, z1, x + 7, 8, z2 + 10, "minecraft:quartz_slab[type=bottom]")
    bb.fill(x - 7, 7, z2 + 10, x + 7, 7, z2 + 10, GOLD)
    bb.set(x, 6, z2 + 5, "minecraft:lantern[hanging=true]")
    # top station: a gold-railed platform on the cliff edge, opening onto the gate square
    bb.fill(x - 5, TOP, z1 - 6, x + 5, TOP, z1, Q)
    for xx in range(x - 5, x + 6):
        bb.set(xx, TOP + 1, z1 - 6, AIR)


def cliff_stair(bb):
    """A switchback stair tunnelled into the cliff face with arched windows, from the Red Port to the Holy Land."""
    runs = [(52, 1, 1, 121, 34), (86, 35, -1, 118, 34), (52, 69, 1, 121, 34), (86, 103, -1, 118, 28)]
    for (xs, ys, dr, z, n) in runs:
        for i in range(n):
            x, y = xs + dr * i, ys + i
            facing = "east" if dr > 0 else "west"
            bb.fill(x, y, z, x, y, z + 1, f"minecraft:red_sandstone_stairs[facing={facing},half=bottom]")
            bb.fill(x, y + 1, z, x, y + 4, z + 1, AIR)
            bb.fill(x, y - 1, z, x, y - 1, z + 1, "minecraft:red_sandstone")
            if i % 6 == 3:                                          # windows out through the face
                zc = int(cliff_z(np.array([x]))[0])
                bb.fill(x, y + 1, z + 2, x, y + 3, zc + 1, AIR)
                bb.set(x, y, zc + 1, "minecraft:red_sandstone_slab[type=bottom]")
            if i % 8 == 5:
                bb.set(x, y + 4, z, "minecraft:lantern[hanging=true]")
    for (lx, ly) in ((86, 35), (49, 69), (86, 103)):                # landings between the runs
        bb.fill(lx, ly, 118, lx + 2, ly + 4, 122, AIR)
        bb.fill(lx, ly - 1, 118, lx + 2, ly - 1, 122, "minecraft:red_sandstone")
        bb.set(lx + 1, ly + 3, 118, "minecraft:lantern[hanging=true]")
    zc = int(cliff_z(np.array([52]))[0])
    bb.fill(49, 1, 121, 52, 4, zc + 1, AIR)                          # the way in from the port
    bb.fill(49, 0, 121, 52, 0, zc + 1, "minecraft:red_sandstone")
    bb.fill(48, 5, zc + 1, 53, 5, zc + 1, "minecraft:cut_red_sandstone")
    bb.fill(58, TOP + 1, 117, 60, TOP + 4, 119, AIR)                 # out onto the Holy Land
    bb.fill(58, TOP, 117, 60, TOP, 117, "minecraft:red_sandstone")


# ------------------------------------------------------------------ the Red Port
def red_port(bb, tracker, audit, rng):
    zc_max = int(cliff_z(np.arange(N)).max()) + 2
    pz1, pz2 = zc_max, 158
    NT.cover(bb, 30, pz1, 170, pz2, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), PORT, 730,
             mask=lambda X, Z: (np.abs(X - 100) < 70 - 6 * NT.noise(X, Z, 731, 9)))
    # the walled harbour basin, a real Marine warship at the quay
    bx1, bx2, bz1, bz2 = 72, 150, 158, 184
    bb.fill(bx1 - 4, -9, bz1 - 4, bx2 + 4, 0, bz2 + 4, "minecraft:stone_bricks")
    bb.fill(bx1, -8, bz1, bx2, -8, bz2, "minecraft:sand")
    bb.fill(bx1, -7, bz1, bx2, 0, bz2, "minecraft:water")
    bb.mix(bx1 - 4, 0, bz1 - 4, bx2 + 4, 0, bz1 - 1, ["minecraft:stone_bricks", "minecraft:polished_andesite", "minecraft:cracked_stone_bricks"], [0.6, 0.3, 0.1])
    for x in range(bx1, bx2 + 1, 8):
        bb.set(x, 1, bz1 - 1, "minecraft:andesite_wall")
        bb.fill(x, -7, bz1, x, -1, bz1, "minecraft:spruce_log[axis=y]")
    for z in range(bz1, bz2 + 5, 6):
        bb.set(bx1 - 2, 1, z, "minecraft:andesite_wall")
        bb.set(bx2 + 2, 1, z, "minecraft:andesite_wall")
    stamp_ship(bb, "marine_warship", 108, 171, water_y=0, rot=0)
    # warehouses and the customs house along the quay
    kinds = (["storage", "living"], ["storage", "kitchen"], ["workshop", "storage"], ["living", "bedroom"])
    houses = [(36, 134, 14, 10, 2), (36, 146, 12, 9, 1), (152, 134, 14, 10, 2), (156, 146, 11, 9, 1),
              (68, 140, 12, 9, 2), (128, 140, 12, 9, 2)]
    for i, (x0, z0, w, d, fl) in enumerate(houses):
        pal = dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"],
                   frame="minecraft:stripped_dark_oak_log", base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:mossy_cobblestone"],
                   floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks")
        mod, ty, au = house_module(seed_of("rp", i), w, d, fl, "minecraft:dark_oak_stairs", tracker, list(kinds[i % 4]), pal=pal)
        audit += au
        place_house(bb, mod, w, d, x0, 0, z0, 0)
    # customs house: a two-storey white block with a flag of the World Government
    cx1, cz1 = 86, 138
    top = tier(bb, cx1, cz1, cx1 + 14, cz1 + 10, 0, 2, 6, [Q, QB], WIN, QST, pilaster=QP, band=GOLD, plate=QB, top_plate=Q)
    cornice(bb, cx1, cz1, cx1 + 14, cz1 + 10, top, QST, parapet="minecraft:quartz_slab[type=bottom]")
    bb.fill(cx1 + 6, 1, cz1 + 10, cx1 + 8, 3, cz1 + 10, AIR)
    for f in range(2):
        rms, doors = P.bsp_rooms(bb, cx1 + 1, cz1 + 1, cx1 + 13, cz1 + 9, 1 + 6 * f, 5, QB, min_room=5, seed=seed_of("cust", f), max_room=8)
        furnish(bb, rms, 1 + 6 * f, 5, ["library", "storage", "living"], seed_of("custf", f), tracker,
                doors=list(doors) + [(cx1 + 7, cz1 + 10), (cx1 + 1, cz1 + 1)], wood="birch", audit=audit)
    bb.fill(cx1 + 1, 1, cz1 + 1, cx1 + 1, 7, cz1 + 1, "minecraft:ladder[facing=east]")
    # the packed port town round them: white and cream houses climbing nowhere (the port is flat), 1-block alleys
    H = height(np.arange(N)[:, None], np.arange(N)[None, :])
    street = lambda x, z: (abs(x - LIFT_X) <= 3) or (150 <= z <= 153) or (abs(x - 100) <= 2)
    ok = lambda x, z: 0 <= x < N and 0 <= z < N and H[x, z] == 0 and not street(x, z)
    reserved = [(x0 - 1, z0 - 1, x0 + w, z0 + d) for (x0, z0, w, d, fl) in houses] + [(cx1 - 1, cz1 - 1, cx1 + 15, cz1 + 11),
                (LIFT_X - 9, 126, LIFT_X + 9, 146), (bx1 - 5, bz1 - 5, bx2 + 5, bz2 + 5)]
    pal = dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"],
               frame="minecraft:stripped_dark_oak_log", base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:mossy_cobblestone"],
               floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks")
    pack_houses(bb, lambda x, z: 0, ok, (26, 128, 174, 186), 40, seed_of("rp-town"), tracker, pal,
                ["minecraft:dark_oak_stairs", "minecraft:spruce_stairs", "minecraft:brick_stairs"], focus=(LIFT_X, 132),
                reserved=reserved, sizes=(7, 11), floors=(1, 3), kinds=("storeroom", "kitchen", "bedroom", "dining"))
    # crates and barrels on the quay, lamp posts
    for _ in range(26):
        x, z = int(rng.integers(bx1, bx2)), int(rng.integers(bz1 - 4, bz1 - 1))
        set_if_air(bb, x, 1, z, ("minecraft:barrel[facing=up,open=false]", "onepiece:sack_pile[facing=north]",
                                 "minecraft:barrel[facing=north,open=false]", "onepiece:cannonball_pile[facing=north]")[int(rng.integers(4))])
    for x in range(40, 162, 12):
        if not (LIFT_X - 9 <= x <= LIFT_X + 9):
            lamp_post(bb, x, 1, pz2 - 2, post="minecraft:dark_oak_fence")


def design():
    bb = BigBuild(seed=611, y_min=-24, y_max=TOP + 70)
    tracker = P.PropTracker(611)
    audit = []
    rng = np.random.default_rng(611)
    H, hf = terrain(bb)
    holy_gate(bb)
    castle(bb, tracker, audit)
    holy_land(bb, tracker, audit, rng)
    bondola(bb)
    cliff_stair(bb)
    red_port(bb, tracker, audit, rng)
    # plants: drifts on the slopes' lower terraces and the port's grass
    NT.plants(bb, 0, 0, N - 1, N - 1, hf, 740, density=0.18, kinds=NT.PLANTS_MEADOW,
              flowers=["minecraft:poppy", "minecraft:dandelion"], mask=lambda X, Z: (hf(X, Z) < TOP) & (hf(X, Z) < 30))
    NT.plants(bb, 0, 0, N - 1, N - 1, hf, 741, density=0.08, kinds=["minecraft:short_grass"],
              flowers=["minecraft:white_tulip", "minecraft:oxeye_daisy", "minecraft:allium"], mask=lambda X, Z: hf(X, Z) == TOP)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    y = TOP + 1
    b.chest(CXC - 3, y + 1, CZC - 13, "legendary", "south")
    b.chest(CXC + 3, y + 1, CZC - 13, "celestial", "south")
    b.chest(CXC + 3, TOP - 13, CZC - 8, "treasure", "west")
    b.chest(50, y, 60, "celestial", "east")
    b.guards("cp0_agent", ((CXC - 4, CZC + 22), (CXC + 4, CZC + 22), (CXC, CZC + 8)), y=y)
    b.guards("vice_admiral", ((CXC, GATE_Z - 4),), y=y)
    b.guards("pacifista", ((CXC - 12, GATE_Z - 3), (CXC + 12, GATE_Z - 3)), y=y)
    b.guards("marine", ((LIFT_X - 6, 150), (LIFT_X + 6, 150), (90, 156), (130, 156)), y=1)
    return b, 0
