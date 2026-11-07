"""Twin Capes v3 (2026-10-30 redo): the way into the Grand Line at the foot of Reverse Mountain, at true scale.

Silhouette first: the Red Line is a colossal red wall across the whole north of the site (~130 above the sea), with
Reverse Mountain bulging out of it in the middle and rising to ~170. The canal comes over the summit from a lake and
falls down the mountain's spine as a stair of pools, spilling into the bay between the two capes. Laboon, the island
whale (about 100 long, as big as a cape), lies in the bay with his scarred forehead pressed toward the Red Line and
the Straw Hat jolly roger Luffy painted on it. On the west cape: Crocus' lighthouse (white with red bands), the
keeper's house, his garden with deck chair and parasol, a jetty. On the east cape: a lookout, rocks and palms. Inside
Laboon: Crocus' painted sky, the stomach sea, an islet with the sickbay. 224 x 224, y 0 = sea surface. (v3)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, palm
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import terrain3 as T3

SID = "twin_capes_lighthouse"
TITLE = "Twin Capes Lighthouse"
CUTS = [3, 10, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False

N = 224
GX = 112                 # Reverse Mountain spine / canal centre line (x)
GW = 5                   # canal half width
SPUR_Z = (40, 116)       # spur runs from the wall face (z 40, ~150 high) down to the sea (z 116)
SUMMIT = (112, 22, 172)  # summit lake centre and top
WHALE_X, HEAD_Z, TAIL_Z = 112, 124, 212
WR = 25                  # Laboon's body radius
WY = 3                   # body centre height
LH = (68, 140)           # lighthouse
LR = 6
_WC1 = NT.outline(46, 128, 33, 7710, wobble=0.10)
_WC2 = NT.outline(40, 84, 26, 7712, wobble=0.12)
_EC1 = NT.outline(184, 120, 29, 7711, wobble=0.10)
_EC2 = NT.outline(186, 82, 24, 7713, wobble=0.12)
_WC = lambda X, Z: np.maximum(_WC1(X, Z), _WC2(X, Z))
_EC = lambda X, Z: np.maximum(_EC1(X, Z), _EC2(X, Z))
GRASS = [("minecraft:grass_block", 0.78), ("minecraft:moss_block", 0.06), ("minecraft:coarse_dirt", 0.08), ("minecraft:podzol", 0.08)]
SAND = [("minecraft:sand", 0.75), ("minecraft:sandstone", 0.1), ("minecraft:clay", 0.15)]
RED_TOP = [("minecraft:red_terracotta", 0.4), ("minecraft:coarse_dirt", 0.2), ("minecraft:red_sand", 0.25), ("minecraft:grass_block", 0.15)]


def _maps():
    X, Z = T3.grid(N)
    edge = np.minimum(X, N - 1 - X)
    taper = np.clip((edge - 8) / 34.0, 0, 1)
    taper = np.floor(taper * 6) / 6.0 * 0.85 + 0.15 * taper           # terraced ends
    face = 42 + 4 * NT.noise(X, 0 * Z, 7701, 13) + 1.6 * np.sin(X * 0.55) + 1.2 * NT.noise(X, 0 * Z, 7702, 3)
    back = 7 + 3 * NT.noise(X, 0 * Z, 7703, 11)
    face = face - (1 - taper) * 18
    plateau = 126 + 10 * NT.fbm(X, Z, 7704, 26)
    wall = (Z >= back) & (Z <= face)
    Hw = np.where(wall, plateau * taper, -99)
    # ledges in front of the face at about a third and two thirds of the height
    for (dz, frac) in ((5, 0.62), (10, 0.3), (15, 0.08)):
        led = (Z > face) & (Z <= face + dz + 2 * NT.noise(X, Z, 7705 + dz, 6))
        Hw = np.where(led, np.maximum(Hw, plateau * taper * frac + 3 * NT.noise(X, Z, 7706, 5)), Hw)
    # Reverse Mountain: a summit cone and a spur falling to the sea
    sx, sz, sy = SUMMIT
    cone = sy - 2.4 * np.hypot(X - sx, (Z - sz) * 1.2)
    t = np.clip((Z - SPUR_Z[0]) / (SPUR_Z[1] - SPUR_Z[0]), 0, 1)
    ridge = np.where(Z < SPUR_Z[0], 150, 150 * (1 - t) ** 0.85)
    spur = ridge - 3.2 * np.maximum(np.abs(X - GX) - 9, 0) ** 1.1 - 6 * NT.noise(X, Z, 7707, 9)
    spur = np.where(Z > SPUR_Z[1] + 4, -99, spur)
    H = np.maximum(np.maximum(Hw, cone), spur)
    red = H > 0
    # the two capes
    dw, de = _WC(X, Z), _EC(X, Z)
    dc = np.maximum(dw, de)
    hill = (2 + 8 * NT.fbm(X, Z, 7708, 18)) * np.clip((dc - 3) / 14.0, 0, 1)
    cape = dc >= 1.5
    Hc = np.where(cape, np.maximum(1, hill), -99)
    lg = np.hypot(X - LH[0], Z - LH[1]) < 17
    Hc = np.where(lg & cape, 3, Hc)
    H = np.where(red, H, Hc)
    land = red | cape
    return np.round(H).astype(int), land, red, face


HMAP, LAND, RED, FACE = _maps()


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def canal_y(z):
    """Pool surface along the canal: the spur's ridge stepped every 3 down to the sea."""
    t = min(max((z - SPUR_Z[0]) / (SPUR_Z[1] - SPUR_Z[0]), 0.0), 1.0)
    r = 150 * (1 - t) ** 0.85 if z >= SPUR_Z[0] else 150
    return max(0, int(3 * math.floor((r - 5) / 3.0)))


def terrain(bb):
    X, Z = T3.grid(N)
    red = RED & (HMAP >= 1)
    T3.strata(bb, HMAP, red, -24, 7720, band=4)
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda XX, ZZ: HMAP[XX.astype(int), ZZ.astype(int)], RED_TOP, 7721,
             mask=lambda XX, ZZ: red[XX.astype(int), ZZ.astype(int)] & (HMAP[XX.astype(int), ZZ.astype(int)] > 100),
             under="minecraft:red_terracotta", depth=1)
    cape = LAND & ~RED
    hfn = lambda XX, ZZ: HMAP[XX.astype(int), ZZ.astype(int)]
    NT.cover(bb, 0, 0, N - 1, N - 1, hfn, SAND, 7722, mask=lambda XX, ZZ: cape[XX.astype(int), ZZ.astype(int)] & (hfn(XX, ZZ) <= 1),
             under="minecraft:sandstone", core="minecraft:stone", base=-16)
    NT.cover(bb, 0, 0, N - 1, N - 1, hfn, GRASS, 7723, mask=lambda XX, ZZ: cape[XX.astype(int), ZZ.astype(int)] & (hfn(XX, ZZ) > 1),
             core="minecraft:stone", base=-16)
    # deep bay for Laboon
    deep = np.where((np.abs(X - WHALE_X) < WR + 6) & (Z > HEAD_Z - 8) & (Z < TAIL_Z + 4), -26, 0)
    T3.sea(bb, N, LAND, 112, 112, 108, 7724, deep=-20, shelf=16, extra_deep=deep)


def canal(bb):
    """Summit lake, then a stair of pools down the spine. Every water block is a source held by stone on all sides
    but the downhill lip, so each pool spills into the next one as a short fall."""
    sx, sz, sy = SUMMIT
    ly = sy - 7
    # summit lake
    bb.fill_where(sx - 16, ly - 3, sz - 14, sx + 16, sy + 4, sz + 14,
                  lambda X, y, Z: (np.hypot(X - sx, (Z - sz) * 1.2) <= 13) & (y > ly), AIR)
    bb.fill_where(sx - 16, ly - 3, sz - 14, sx + 16, ly, sz + 14,
                  lambda X, y, Z: (np.hypot(X - sx, (Z - sz) * 1.2) <= 13) & (y >= ly - 1), "minecraft:water")
    bb.fill_where(sx - 16, ly - 4, sz - 14, sx + 16, ly - 2, sz + 14,
                  lambda X, y, Z: (np.hypot(X - sx, (Z - sz) * 1.2) <= 13) & (y == ly - 2), "minecraft:stone")
    for z in range(sz + 8, SPUR_Z[1] + 8):
        wy = canal_y(z) if z >= SPUR_Z[0] else ly
        for x in range(GX - GW - 2, GX + GW + 3):
            side = abs(x - GX) > GW
            if side:
                top = max(hy(x, z), wy + 2)
                bb.fill(x, max(wy - 6, -6), z, x, top, z, "minecraft:red_terracotta" if (x * 7 + z) % 5 else "minecraft:granite")
            else:
                bb.fill(x, max(wy - 6, -6), z, x, wy - 1, z, "minecraft:stone" if wy > 0 else "minecraft:sand")
                bb.set(x, wy, z, "minecraft:water")
                bb.fill(x, wy + 1, z, x, min(wy + 40, 199), z, AIR)
    # little stepping stones / mossy lips where pools spill
    for z in range(SPUR_Z[0], SPUR_Z[1]):
        if canal_y(z) != canal_y(z + 1):
            for x in (GX - GW - 1, GX + GW + 1):
                bb.set(x, canal_y(z) + 2, z, "minecraft:mossy_cobblestone")


def path_up(bb):
    """A rock-cut stair along the canal's west wall from the bay to the summit lake (a walk for players)."""
    x = GX - GW - 2
    for z in range(SPUR_Z[1] + 6, SUMMIT[1] + 6, -1):
        y = max(canal_y(z) + 2, 1)
        bb.fill(x - 1, y - 2, z, x, y - 1, z, "minecraft:polished_granite")
        bb.fill(x - 1, y, z, x, y + 3, z, AIR)
        bb.set(x - 2, y, z, "minecraft:red_sandstone_wall")
        if z % 9 == 0:
            bb.set(x - 2, y + 1, z, "minecraft:lantern[hanging=false]")


# ------------------------------------------------------------------ Crocus' lighthouse and garden
def lighthouse(bb, tracker, audit):
    cx, cz = LH
    y0 = hy(cx, cz)
    HT = 44
    top = y0 + HT
    bb.cylinder(cx, y0 - 6, cz, LR + 3, y0, "minecraft:stone_bricks")
    bb.cylinder(cx, y0, cz, LR + 3, y0, "minecraft:polished_andesite")
    for y in range(y0 + 1, top + 1):
        k = (y - y0) / HT
        r = LR - 1.8 * k
        band = ((y - y0) // 7) % 2 == 1
        blk = "minecraft:red_concrete" if band else "minecraft:white_concrete"
        bb.fill_where(cx - LR - 1, y, cz - LR - 1, cx + LR + 1, y, cz + LR + 1,
                      lambda X, yy, Z, r=r: (np.hypot(X - cx, Z - cz) <= r + 0.5) & (np.hypot(X - cx, Z - cz) > r - 0.9), blk)
        bb.fill_where(cx - LR, y, cz - LR, cx + LR, y, cz + LR, lambda X, yy, Z, r=r: np.hypot(X - cx, Z - cz) <= r - 0.9, AIR)
    for i in range(HT - 1):
        a = i * 0.55
        for rr in (1.2, 2.2, 3.0):
            bb.set(cx + int(round(rr * math.cos(a))), y0 + 1 + i, cz + int(round(rr * math.sin(a))), "minecraft:smooth_stone_slab[type=top]")
    bb.fill(cx, y0 + 1, cz, cx, top, cz, "minecraft:stripped_spruce_log[axis=y]")
    for y in range(y0 + 5, top - 2, 6):
        for (dx, dz) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            r = int(LR - 1.8 * (y - y0) / HT)
            bb.fill(cx + dx * r, y, cz + dz * r, cx + dx * r, y + 1, cz + dz * r, "minecraft:glass_pane")
            set_if_air(bb, cx + dx * (r - 1), y - 1, cz + dz * (r - 1), "minecraft:lantern[hanging=false]") if y % 12 == 5 else None
    bb.fill(cx - LR, y0 + 1, cz, cx - LR + 1, y0 + 3, cz, AIR)
    bb.set(cx - LR, y0 + 1, cz, "minecraft:spruce_door[facing=west,half=lower,hinge=left]")
    bb.set(cx - LR, y0 + 2, cz, "minecraft:spruce_door[facing=west,half=upper,hinge=left]")
    bb.set(cx - LR - 1, y0 + 3, cz - 1, "minecraft:lantern[hanging=false]") if False else None
    g = top + 1
    bb.cylinder(cx, g, cz, LR + 1, g, "minecraft:smooth_stone")
    bb.fill_where(cx - LR - 2, g + 1, cz - LR - 2, cx + LR + 2, g + 1, cz + LR + 2,
                  lambda X, yy, Z: (np.hypot(X - cx, Z - cz) <= LR + 1.5) & (np.hypot(X - cx, Z - cz) > LR + 0.5), "minecraft:iron_bars")
    bb.fill(cx - 1, g, cz - 1, cx + 1, g, cz + 1, "minecraft:spruce_trapdoor[facing=north,half=top,open=false]")
    bb.fill_where(cx - 3, g + 1, cz - 3, cx + 3, g + 6, cz + 3,
                  lambda X, yy, Z: (np.hypot(X - cx, Z - cz) <= 3.2) & (np.hypot(X - cx, Z - cz) > 2.2), "minecraft:glass")
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        bb.fill(cx + dx, g + 1, cz + dz, cx + dx, g + 6, cz + dz, "minecraft:red_concrete")
    bb.set(cx, g + 1, cz, "minecraft:polished_andesite")
    bb.set(cx, g + 2, cz, "minecraft:sea_lantern"); bb.set(cx, g + 3, cz, "minecraft:glowstone"); bb.set(cx, g + 4, cz, "minecraft:sea_lantern")
    bb.dome(cx, g + 7, cz, 4, "minecraft:red_concrete", hollow=True)
    bb.fill(cx, g + 11, cz, cx, g + 13, cz, "minecraft:lightning_rod[facing=up]")
    # keeper's house: two rooms + a loft, stone base, timber posts, red roof
    hx1, hz1, hx2, hz2 = cx - 22, cz + 3, cx - 8, cz + 14
    y = y0
    bb.fill(hx1 - 1, y - 3, hz1 - 1, hx2 + 1, y, hz2 + 1, "minecraft:cobblestone")
    bb.fill(hx1, y + 1, hz1, hx2, y + 5, hz2, "minecraft:white_terracotta")
    bb.fill(hx1 + 1, y + 1, hz1 + 1, hx2 - 1, y + 5, hz2 - 1, AIR)
    bb.fill(hx1 + 1, y, hz1 + 1, hx2 - 1, y, hz2 - 1, "minecraft:spruce_planks")
    for x in range(hx1, hx2 + 1, 4):
        for z in (hz1, hz2):
            bb.fill(x, y + 1, z, x, y + 5, z, "minecraft:stripped_spruce_log[axis=y]")
    for (x, z) in ((hx2, hz1), (hx2, hz2)):
        bb.fill(x, y + 1, z, x, y + 5, z, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(hx1, y + 5, hz1, hx2, y + 5, hz2, "minecraft:stripped_spruce_log[axis=x]")
    bb.fill(hx1 + 1, y + 5, hz1 + 1, hx2 - 1, y + 5, hz2 - 1, AIR)
    for x in range(hx1 + 2, hx2 - 1, 4):
        for z in (hz1, hz2):
            bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:glass_pane")
            bb.set(x, y + 1, z + (-1 if z == hz1 else 1), "minecraft:spruce_trapdoor[facing=%s,half=top,open=false]" % ("north" if z == hz1 else "south"))
    for z in range(hz1 + 2, hz2 - 1, 4):
        bb.fill(hx1, y + 2, z, hx1, y + 3, z, "minecraft:glass_pane")
    dx = (hx1 + hx2) // 2
    bb.fill(dx, y + 1, hz1, dx, y + 2, hz1, AIR)
    bb.set(dx, y + 1, hz1, "minecraft:spruce_door[facing=north,half=lower,hinge=left]")
    bb.set(dx, y + 2, hz1, "minecraft:spruce_door[facing=north,half=upper,hinge=left]")
    bb.set(dx - 1, y + 3, hz1 - 1, "minecraft:lantern[hanging=false]") if False else None
    bb.fill(dx - 1, y + 4, hz1 - 1, dx + 1, y + 4, hz1 - 1, "minecraft:spruce_slab[type=top]")
    bb.set(dx + 1, y + 3, hz1 - 1, "minecraft:lantern[hanging=true]")
    wx = hx1 + 7
    bb.fill(wx, y + 1, hz1 + 1, wx, y + 4, hz2 - 1, "minecraft:white_terracotta")
    bb.fill(wx, y + 1, hz1 + 5, wx, y + 2, hz1 + 5, AIR)
    rooms = [(hx1 + 1, hz1 + 1, wx - 1, hz2 - 1), (wx + 1, hz1 + 1, hx2 - 1, hz2 - 1)]
    P.furnish_room(bb, rooms[0], y + 1, "bedroom", height=4, seed=seed_of("tc3", 1), doors=[(wx, hz1 + 5)], wood="spruce", tracker=tracker)
    P.furnish_room(bb, rooms[1], y + 1, "study", height=4, seed=seed_of("tc3", 2), doors=[(wx, hz1 + 5), (dx, hz1)], wood="spruce", tracker=tracker)
    for r in rooms:
        txt, ok = P.audit_props(bb, [r], y + 1, 4)
        if not ok:
            audit.append(txt)
    P.gable_roof(bb, hx1 - 1, hz1 - 1, hx2 + 1, hz2 + 1, y + 6, "minecraft:red_nether_brick_stairs", ridge_axis="x",
                 gable_fill="minecraft:white_terracotta", overhang=1)
    bb.fill(hx1 + 2, y + 6, hz2 - 2, hx1 + 2, y + 12, hz2 - 2, "minecraft:bricks")
    # the garden: deck chair under a parasol, reading table, flower beds, picket fence
    gx, gz = cx - 13, cz - 9
    bb.set(gx, y + 1, gz, "minecraft:spruce_stairs[facing=west,half=bottom]")
    bb.set(gx + 1, y + 1, gz, "minecraft:spruce_slab[type=bottom]")
    bb.set(gx + 2, y + 1, gz, "minecraft:spruce_slab[type=bottom]")
    px, pz = gx + 1, gz - 2
    bb.fill(px, y + 1, pz, px, y + 4, pz, "minecraft:birch_fence")
    for ddx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(ddx) + abs(dz) <= 3:
                bb.set(px + ddx, y + 5, pz + dz, "minecraft:white_wool" if (ddx + dz) % 2 else "minecraft:red_wool")
    bb.set(gx + 3, y + 1, gz - 1, "minecraft:spruce_fence"); bb.set(gx + 3, y + 2, gz - 1, "minecraft:spruce_pressure_plate")
    for k, f in enumerate(("poppy", "dandelion", "poppy", "azure_bluet", "oxeye_daisy", "allium", "cornflower", "poppy")):
        x, z = cx - 22 + (k % 4), cz - 13 + 8 * (k // 4)
        bb.set(x, y, z, "minecraft:grass_block"); bb.set(x, y + 1, z, "minecraft:" + f)
    for a in range(0, 360, 4):
        t = math.radians(a)
        x = cx + int(round(16 * math.cos(t))); z = cz + int(round(16 * math.sin(t)))
        if LAND[x, z] and not (40 < a < 140) and not (330 < a or a < 20):
            set_if_air(bb, x, hy(x, z) + 1, z, "minecraft:birch_fence")
    palm(bb, cx - 26, hy(cx - 26, cz - 2) + 1, cz - 2, 12, lean=(-1, 0))
    palm(bb, cx - 4, hy(cx - 4, cz - 14) + 1, cz - 14, 10, lean=(0, -1))
    # jetty out into the bay
    for x in range(cx + LR + 2, cx + LR + 16):
        bb.fill(x, 1, cz - 1, x, 1, cz + 1, "minecraft:spruce_planks")
        if x % 4 == 0:
            for z in (cz - 2, cz + 2):
                bb.fill(x, -8, z, x, 2, z, "minecraft:spruce_log[axis=y]")
            bb.set(x, 3, cz + 2, "minecraft:lantern[hanging=false]")
    bb.set(cx + LR + 15, 2, cz, "minecraft:barrel[facing=up,open=false]")
    return (hx1 - 3, cz - 18, cx + LR + 16, cz + 18)


# ------------------------------------------------------------------ Laboon
L = TAIL_Z - HEAD_Z


def whale_r(t):
    """Body radius along the whale (t 0 = forehead, 1 = tail stock): a blunt, huge head and a long taper."""
    if t < 0.06:
        return WR * (0.72 + 0.28 * math.sqrt(t / 0.06))
    if t < 0.5:
        return WR
    return WR * max(0.12, 1 - ((t - 0.5) / 0.5) ** 1.3 * 0.88)


RS = np.array([whale_r(min(max((z - HEAD_Z) / L, 0.0), 1.0)) for z in range(N)])


def _shape(X, Y, Z, shrink=0.0):
    t = (Z - HEAD_Z) / L
    r = RS[np.clip(Z.astype(int), 0, N - 1)] - shrink
    rx, ry = r * 0.82, r * 0.92
    return (t >= 0) & (t <= 1) & (((X - WHALE_X) / np.maximum(rx, 0.5)) ** 2 + ((Y - WY) / np.maximum(ry, 0.5)) ** 2 <= 1)


def front(bb, x, y, z0=HEAD_Z, z1=HEAD_Z + 12):
    """First solid z on Laboon's forehead along the column (x, y), or None."""
    reg = bb.get_region(x, y, z0, x, y, z1)[0, 0, :]
    for k, v in enumerate(reg):
        if v > 1:
            return z0 + k
    return None


def laboon(bb):
    TOPC = ["minecraft:light_blue_terracotta", "minecraft:cyan_terracotta", "minecraft:gray_terracotta"]
    BELLY = "minecraft:calcite"
    xa, xb, ya, yb = WHALE_X - WR - 2, WHALE_X + WR + 2, -26, WY + WR + 2
    outer = lambda X, Y, Z: _shape(X, Y, Z)
    inner = lambda X, Y, Z: _shape(X, Y, Z, 2.5) & (Z > HEAD_Z + 4) & (Z < TAIL_Z - 26)
    n = lambda X, Y, Z: NT.noise(X + Y * 3, Z, 7730, 6)
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: outer(X, Y, Z) & (Y < WY - 9), BELLY)
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: outer(X, Y, Z) & (Y >= WY - 9) & (Y < WY - 7), "minecraft:light_gray_concrete")
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: outer(X, Y, Z) & (Y >= WY - 7) & (n(X, Y, Z) < 0.55), TOPC[0])
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: outer(X, Y, Z) & (Y >= WY - 7) & (n(X, Y, Z) >= 0.55) & (n(X, Y, Z) < 0.8), TOPC[1])
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: outer(X, Y, Z) & (Y >= WY - 7) & (n(X, Y, Z) >= 0.8), TOPC[2])
    # hollow: Crocus' painted sky above, the stomach sea below
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, inner, AIR)
    sky = lambda X, Y, Z: _shape(X, Y, Z, 1.5) & ~_shape(X, Y, Z, 2.5) & (Z > HEAD_Z + 3) & (Z < TAIL_Z - 25) & (Y > -1)
    cl = lambda X, Y, Z: NT.fbm(X + Y * 2, Z - Y, 7731, 6)
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: sky(X, Y, Z) & (cl(X, Y, Z) < 0.6), "minecraft:light_blue_concrete")
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: sky(X, Y, Z) & (cl(X, Y, Z) >= 0.6), "minecraft:white_concrete")
    bb.fill_where(xa, ya, HEAD_Z, xb, yb, TAIL_Z, lambda X, Y, Z: inner(X, Y, Z) & (Y <= -2), "minecraft:water")
    # glow in the painted sky (sea lanterns behind the clouds)
    for z in range(HEAD_Z + 10, TAIL_Z - 28, 8):
        for xo in (-12, 0, 12):
            for yy in range(WY + WR, WY, -1):
                if _shape(np.array([WHALE_X + xo]), np.array([yy]), np.array([z]), 1.5)[0]:
                    bb.set(WHALE_X + xo, yy, z, "minecraft:sea_lantern")
                    break
    stomach(bb)
    # flukes flat at the surface, fins, blowhole
    for k in range(0, 22):
        for side in (-1, 1):
            for w in range(-3 + k // 8, 4 - k // 8):
                bb.set(WHALE_X + side * (2 + k), 1 + k // 8, TAIL_Z - 8 + w + k // 3, TOPC[0])
    for z in range(TAIL_Z - 10, TAIL_Z + 1):
        bb.fill(WHALE_X - 2, -2, z, WHALE_X + 2, 2, z, TOPC[0])
    for side in (-1, 1):
        fz = HEAD_Z + 44
        for k in range(18):
            for w in range(-4 + k // 5, 5 - k // 5):
                bb.set(WHALE_X + side * (19 + k), WY - 8 - k // 4, fz + k // 2 + w, TOPC[1])
    t0 = 20
    topy = WY + int(RS[HEAD_Z + t0] * 0.92)
    bb.fill(WHALE_X - 1, topy - 1, HEAD_Z + t0, WHALE_X + 1, topy, HEAD_Z + t0 + 1, "minecraft:black_concrete")
    face(bb)


def face(bb):
    # eyes on the sides of the head, low, with a white ring and a highlight
    ez = HEAD_Z + 16
    for side in (-1, 1):
        r = RS[ez] * 0.82
        ex = int(round(WHALE_X + side * r * math.sqrt(max(0.0, 1 - ((-4) / (RS[ez] * 0.92)) ** 2))))
        for dy in range(-3, 4):
            for dz in range(-3, 4):
                d = math.hypot(dy, dz)
                if d <= 3.4:
                    bb.set(ex, WY - 4 + dy, ez + dz, "minecraft:black_concrete" if d <= 1.9 else "minecraft:white_concrete")
                    bb.set(ex - side, WY - 4 + dy, ez + dz, "minecraft:black_concrete")
        bb.set(ex, WY - 3, ez - 1, "minecraft:white_concrete")
        # mouth: a long dark line from the snout back past the eye
        for z in range(HEAD_Z, HEAD_Z + 40):
            rr = RS[z]
            yy = WY - 10
            dxm = (rr * 0.82) * math.sqrt(max(0.0, 1 - ((yy - WY) / (rr * 0.92)) ** 2))
            for k in (0, 1):
                bb.set(int(round(WHALE_X + side * (dxm - k))), yy, z, "minecraft:gray_concrete")
    # the mouth line also crosses the front, low
    for x in range(WHALE_X - 16, WHALE_X + 17):
        z = front(bb, x, WY - 10)
        if z is not None:
            bb.set(x, WY - 10, z, "minecraft:gray_concrete")
    scars()
    jolly_roger(bb)


SCARS = []


def scars():
    pass


JR = [
    "........YYYYYYYYY........",
    "......YYYYYYYYYYYYY......",
    ".....YYYYYYYYYYYYYYY.....",
    ".....RRRRRRRRRRRRRRR.....",
    "..YYYYYYYYYYYYYYYYYYYYY..",
    ".YYYYYYYYYYYYYYYYYYYYYYY.",
    "......WWWWWWWWWWWWW......",
    ".....WWWWWWWWWWWWWWW.....",
    ".....WWKKKWWWWWKKKWW.....",
    ".....WWKKKWWWWWKKKWW.....",
    ".....WWKKKWWWWWKKKWW.....",
    "......WWWWWWKWWWWWW......",
    ".......WWWWWWWWWWW.......",
    "........WKWKWKWKW........",
    "........WWWWWWWWW........",
    "KKK...................KKK",
    ".KKK.................KKK.",
    "...KKK.............KKK...",
    "....KKK...........KKK....",
    "......KKK.......KKK......",
    ".......KKK.....KKK.......",
    "........KKK...KKK........",
    "..........KKKKK..........",
    "...........KKK...........",
]


def jolly_roger(bb):
    """The Straw Hat jolly roger Luffy painted on Laboon's forehead (front face, facing north), plus the old scars."""
    cols = {"Y": "minecraft:yellow_concrete", "R": "minecraft:red_concrete", "W": "minecraft:white_concrete",
            "K": "minecraft:black_concrete"}
    w = 25
    for r, row in enumerate(JR):
        row = (row + "." * w)[:w]
        y = WY + 15 - r
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            x = WHALE_X - w // 2 + c
            z = front(bb, x, y)
            if z is not None:
                bb.set(x, y, z, cols[ch])
    # scars: pale pink stitched gashes round the painting (Laboon kept ramming the Red Line)
    rng = np.random.default_rng(7740)
    for _ in range(22):
        x = WHALE_X + int(rng.choice([-1, 1])) * int(rng.integers(8, 19))
        y = WY + int(rng.integers(-8, 19))
        ln = int(rng.integers(5, 11)); sl = rng.choice([-1, 1])
        for k in range(ln):
            xx, yy = x + k, y + int(sl * k * 0.6)
            z = front(bb, xx, yy, HEAD_Z, HEAD_Z + 16)
            if z is not None:
                bb.set(xx, yy, z, "minecraft:pink_terracotta" if k % 3 else "minecraft:red_terracotta")
                if k % 2 == 0:
                    z2 = front(bb, xx, yy + 1, HEAD_Z, HEAD_Z + 16)
                    if z2 is not None:
                        bb.set(xx, yy + 1, z2, "minecraft:white_terracotta")


def stomach(bb):
    ix, iz = WHALE_X, HEAD_Z + 40
    bb.fill_where(ix - 10, -10, iz - 10, ix + 10, -1, iz + 10,
                  lambda X, Y, Z: ((X - ix) ** 2 + (Z - iz) ** 2) * (1 + 0.3 * NT.noise(X, Z, 7732, 3)) <= (9 + Y * 0.6) ** 2, "minecraft:sand")
    bb.fill_where(ix - 8, -1, iz - 8, ix + 8, -1, iz + 8, lambda X, Y, Z: (X - ix) ** 2 + (Z - iz) ** 2 <= 36, "minecraft:grass_block")
    hx1, hz1, hx2, hz2 = ix - 3, iz - 2, ix + 3, iz + 3
    bb.fill(hx1, 0, hz1, hx2, 3, hz2, "minecraft:white_terracotta")
    bb.fill(hx1 + 1, 0, hz1 + 1, hx2 - 1, 3, hz2 - 1, AIR)
    bb.fill(hx1 + 1, -1, hz1 + 1, hx2 - 1, -1, hz2 - 1, "minecraft:spruce_planks")
    bb.fill(ix, 0, hz1, ix, 1, hz1, AIR)
    bb.set(ix, 0, hz1, "minecraft:spruce_door[facing=north,half=lower,hinge=left]")
    bb.set(ix, 1, hz1, "minecraft:spruce_door[facing=north,half=upper,hinge=left]")
    bb.set(hx1, 1, iz, "minecraft:glass_pane"); bb.set(hx2, 1, iz, "minecraft:glass_pane")
    P.gable_roof(bb, hx1 - 1, hz1 - 1, hx2 + 1, hz2 + 1, 4, "minecraft:spruce_stairs", ridge_axis="z",
                 gable_fill="minecraft:white_terracotta", overhang=0)
    bb.set(hx1 + 1, 0, hz2 - 1, "minecraft:white_bed[facing=south,part=head]")
    bb.set(hx1 + 1, 0, hz2 - 2, "minecraft:white_bed[facing=south,part=foot]")
    bb.set(hx2 - 1, 0, hz2 - 1, "minecraft:brewing_stand")
    bb.set(hx2 - 1, 0, hz1 + 1, "minecraft:barrel[facing=up,open=false]")
    bb.set(ix, 3, iz, "minecraft:lantern[hanging=true]")
    bb.set(ix - 5, 0, iz - 4, "minecraft:spruce_stairs[facing=south,half=bottom]")
    bb.set(ix - 5, 0, iz - 3, "minecraft:spruce_slab[type=bottom]")
    bb.fill(ix - 3, 0, iz - 6, ix - 3, 3, iz - 6, "minecraft:birch_fence")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3:
                bb.set(ix - 3 + dx, 4, iz - 6 + dz, "minecraft:yellow_wool" if (dx + dz) % 2 else "minecraft:white_wool")
    bb.set(ix - 2, 0, iz - 3, "minecraft:birch_fence"); bb.set(ix - 2, 1, iz - 3, "minecraft:birch_pressure_plate")
    palm(bb, ix + 6, 0, iz + 6, 9, lean=(1, 1))
    # iron hatch in the east flank, corridor in, floating dock outside
    hz = iz
    ex = int(WHALE_X + RS[hz] * 0.82)
    bb.fill(WHALE_X + 7, 0, hz - 1, ex + 1, 3, hz + 1, AIR)
    bb.fill(WHALE_X + 7, -1, hz - 1, ex + 1, -1, hz + 1, "minecraft:spruce_planks")
    for yy in range(0, 5):
        for z in (hz - 2, hz + 2):
            bb.set(ex, yy, z, "minecraft:iron_block")
    bb.fill(ex, 4, hz - 2, ex, 4, hz + 2, "minecraft:iron_block")
    bb.set(ex, 0, hz, "minecraft:iron_door[facing=west,half=lower,hinge=left]")
    bb.set(ex, 1, hz, "minecraft:iron_door[facing=west,half=upper,hinge=left]")
    bb.set(ex + 1, 1, hz + 1, "minecraft:stone_button[face=wall,facing=east]")
    bb.set(ex - 1, 1, hz - 1, "minecraft:stone_button[face=wall,facing=west]")
    bb.fill(ex - 1, 0, hz - 1, ex - 1, 1, hz + 1, AIR)
    bb.fill(ex + 1, 0, hz - 3, ex + 6, 0, hz + 3, "minecraft:spruce_planks")
    for (x, z) in ((ex + 1, hz - 3), (ex + 6, hz - 3), (ex + 1, hz + 3), (ex + 6, hz + 3)):
        bb.set(x, 1, z, "minecraft:spruce_fence")
    bb.set(ex + 6, 2, hz + 3, "minecraft:lantern[hanging=false]")


# ------------------------------------------------------------------ east cape lookout, rocks, plants
def east_cape(bb, taken):
    cx, cz = 190, 118
    y = hy(cx, cz)
    bb.fill(cx - 4, y - 2, cz - 4, cx + 4, y, cz + 4, "minecraft:cobblestone")
    for (x, z) in ((cx - 4, cz - 4), (cx + 4, cz - 4), (cx - 4, cz + 4), (cx + 4, cz + 4)):
        bb.fill(x, y + 1, z, x, y + 12, z, "minecraft:spruce_log[axis=y]")
    for yy in (y + 6, y + 11):
        bb.fill(cx - 4, yy, cz - 4, cx + 4, yy, cz + 4, "minecraft:spruce_planks")
        for x in range(cx - 4, cx + 5):
            for z in (cz - 4, cz + 4):
                bb.set(x, yy + 1, z, "minecraft:spruce_fence")
        for z in range(cz - 4, cz + 5):
            for x in (cx - 4, cx + 4):
                bb.set(x, yy + 1, z, "minecraft:spruce_fence")
    for i in range(11):
        bb.set(cx, y + 1 + i, cz + 3, "minecraft:ladder[facing=north]")
    bb.fill(cx, y + 6, cz + 3, cx, y + 6, cz + 3, AIR); bb.fill(cx, y + 11, cz + 3, cx, y + 11, cz + 3, AIR)
    bb.set(cx, y + 7, cz + 3, AIR); bb.set(cx, y + 12, cz + 3, AIR)
    P.hip_roof(bb, cx - 5, cz - 5, cx + 5, cz + 5, y + 15, "minecraft:spruce_stairs")
    bb.set(cx, y + 14, cz, "minecraft:lantern[hanging=true]")
    bb.set(cx - 2, y + 12, cz - 2, "minecraft:spyglass") if False else None
    bb.set(cx - 2, y + 12, cz - 3, "minecraft:barrel[facing=up,open=false]")
    taken.append((cx - 6, cz - 6, cx + 6, cz + 6))


def plants(bb, rng, taken):
    k = 0
    cape = LAND & ~RED
    for _ in range(4000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if not cape[x, z] or hy(x, z) < 2:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if k % 3 == 0:
            NT.boulder(bb, x, hy(x, z), z, float(rng.uniform(1.5, 3.2)), rng)
            taken.append((x - 3, z - 3, x + 3, z + 3))
        else:
            palm(bb, x, hy(x, z) + 1, z, int(rng.integers(9, 15)), lean=((1, 0), (0, 1), (-1, 0), (0, -1))[k % 4])
            taken.append((x - 2, z - 2, x + 2, z + 2))
        k += 1
        if k >= 34:
            break
    hfn = lambda XX, ZZ: HMAP[XX.astype(int), ZZ.astype(int)]
    NT.plants(bb, 0, 0, N - 1, N - 1, hfn, 7750, density=0.3, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda XX, ZZ: cape[XX.astype(int), ZZ.astype(int)] & (hfn(XX, ZZ) > 1))
    # tufts of grass and dead bushes on the Red Line ledges
    NT.plants(bb, 0, 0, N - 1, N - 1, hfn, 7751, density=0.08, kinds=["minecraft:short_grass", "minecraft:dead_bush"],
              mask=lambda XX, ZZ: RED[XX.astype(int), ZZ.astype(int)], ground=("grass_block", "coarse_dirt"))


def design():
    bb = BigBuild(seed=7710, y_min=-30, y_max=200)
    tracker = P.PropTracker(7710)
    audit = []
    rng = np.random.default_rng(7710)
    terrain(bb)
    canal(bb)
    path_up(bb)
    taken = [lighthouse(bb, tracker, audit), (WHALE_X - WR - 4, HEAD_Z - 2, WHALE_X + WR + 4, TAIL_Z + 4)]
    laboon(bb)
    east_cape(bb, taken)
    plants(bb, rng, taken)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    cx, cz = LH
    b.chest(cx - 20, hy(cx, cz) + 1, cz + 5, "easy", "south")
    b.chest(WHALE_X + 2, 0, HEAD_Z + 42, "medium", "west")
    return b, 0
