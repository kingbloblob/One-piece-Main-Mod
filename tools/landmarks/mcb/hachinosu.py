"""Hachinosu v3, redesigned with the Minecraft Builder skill to match the anime: Beehive Island, the pirate island
that was the Rocks Pirates' base and is now ruled by Blackbeard.

The island's landmark is a gigantic stone skull that stands upright like a wall: a wide, semi-flat face (about 72
wide, 94 high, only ~26 deep), cream bone shading to tan at the rim, a golden-orange domed cap on top, two huge
round eye holes you can see the sky through, a long crack running down from the crown through the right eye, a
small arched window between the eyes and an orange bandana bow knotted on its right side.

Round its foot a massive pirate city piles up a mound in tiers: hundreds of cream, tan and sandstone box houses
stacked on plinths, flat roofs with parapets, roof gardens and add-on rooms, alleys and a stair street climbing
from the harbour to the skull's jaw gate. Palms in the gaps, grey crags at the flanks.

Inside the skull: the jaw hall (the great tavern where the Titanic Captains drink) behind the gate, Koby's cell
beside it, a spiral stair up the core to Blackbeard's throne room behind the arched window, and the treasure vault
in the cap. The harbour on the south shore has piers, a market and two visiting pirate ships.
176 x 176, y 0 = sea surface. (v3)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, st, stair_core, steady, palm, onion_dome, lamp_post
from mcb.kit_interiors import furnish_kit, table_group, bar_counter, wall_lights, Plan, _tables
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "hachinosu"
TITLE = "Hachinosu (Beehive Island)"
CUTS = [3, 14, 30, 45, 60]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
GY = 4                        # coast ground
CX, CZ = 88, 62               # skull mid-plane
CRX, CRY, CRV = 36, 38, 58    # cranium ellipse (half width, half height, centre height above GY)
TOPV = CRV + CRY              # skull top, above GY
MOUND = 21                    # city mound height at the skull's foot (jaw gate floor = GY + MOUND + 1)
HALL_Y = GY + MOUND + 1
THRONE_Y = GY + 37
VAULT_Y = GY + 82
EYES = ((CX - 15, CRV + 2), (CX + 15, CRV + 2))
EYE_R = (10.0, 11.0)
_ISLE = NT.outline(88, 88, 77, 8080, wobble=0.08)
CRAGS = ((22, 70, 12, 36), (33, 48, 8, 24), (154, 72, 11, 32), (142, 50, 8, 22))

GROUND = [("minecraft:coarse_dirt", 0.25), ("minecraft:grass_block", 0.3), ("minecraft:packed_mud", 0.12), ("minecraft:rooted_dirt", 0.1),
          ("minecraft:podzol", 0.1), ("minecraft:sand", 0.0), ("minecraft:dirt_path", 0.13)]
STREET = [("minecraft:sandstone", 0.3), ("minecraft:packed_mud", 0.25), ("minecraft:smooth_sandstone", 0.2), ("minecraft:mud_bricks", 0.15),
          ("minecraft:cut_sandstone", 0.1)]
# house palettes: wall, trim, slab
HOUSE = [("minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:smooth_sandstone_slab"),
         ("minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:sandstone_slab"),
         ("minecraft:birch_planks", "minecraft:stripped_birch_log[axis=y]", "minecraft:birch_slab"),
         ("minecraft:sandstone", "minecraft:smooth_sandstone", "minecraft:sandstone_slab"),
         ("minecraft:end_stone_bricks", "minecraft:sandstone", "minecraft:end_stone_brick_slab"),
         ("minecraft:packed_mud", "minecraft:mud_bricks", "minecraft:mud_brick_slab"),
         ("minecraft:mushroom_stem", "minecraft:birch_planks", "minecraft:birch_slab"),
         ("minecraft:smooth_sandstone", "minecraft:terracotta", "minecraft:smooth_sandstone_slab")]
KINDS = ["tavern", "bedroom", "kitchen", "storeroom", "dining", "workshop", "bedroom", "tavern"]
WOODS = ["spruce", "oak", "birch", "jungle", "dark_oak"]


# ------------------------------------------------------------------ the skull's shape

def jaw_w(v):
    return 24 + 8 * np.clip((np.asarray(v, float) - 10) / 30.0, 0, 1)


def skull_q(u, v):
    """0..1 how far inside the skull outline (1 = middle of the face, 0 = rim, <0 outside)."""
    u = np.asarray(u, float); v = np.asarray(v, float)
    qc = 1 - (u / CRX) ** 2 - ((v - CRV) / CRY) ** 2
    qj = np.where(v <= CRV, 1 - (u / jaw_w(v)) ** 2, -1)
    return np.maximum(qc, qj)


def front_z(q):
    return CZ + 3 + 11 * np.clip(q, 0, 1) ** 0.35


def back_z(q):
    return CZ - 3 - 9 * np.clip(q, 0, 1) ** 0.35


def cap_v(u):
    return 80 - 12 * (np.asarray(u, float) / CRX) ** 2


def eye_e(x, v):
    return min(((x - ex) / EYE_R[0]) ** 2 + ((v - ev) / EYE_R[1]) ** 2 for ex, ev in EYES)


# ------------------------------------------------------------------ terrain: island + the city mound

def _skull_dist(X, Z):
    dx = np.maximum(np.abs(X - CX) - 26, 0)
    dz = np.maximum(np.maximum((CZ - 12) - Z, Z - (CZ + 15)), 0)
    return np.hypot(dx, dz)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    sd = _skull_dist(X, Z)
    k = np.where(Z < CZ, 0.75, 1.0)
    m = MOUND * k * np.clip(1 - sd / 54.0, 0, 1) ** 1.25
    h = GY + m + (NT.fbm(X, Z, 8081, 20) - 0.5) * 3 * (1 - np.clip(1 - sd / 54.0, 0, 1))
    # the plaza in front of the jaw gate is level with the gate
    plaza = (np.abs(X - CX) <= 11) & (Z >= CZ + 10) & (Z <= CZ + 26)
    h = np.where(plaza, GY + MOUND, h)
    h = np.where(d < 12, 1 + (h - 1) * np.clip(d / 12.0, 0, 1), h)
    bay = np.hypot((X - 88) / 30.0, (Z - 160) / 22.0) < 1
    h = np.where(bay, -6, h)
    h = np.where(d < 1.5, -5 - np.clip(-d, 0, 6), h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def street(X, Z):
    """The stair street from the quay up to the plaza, and a ring lane round the mound's middle."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    main = (np.abs(X - CX) <= 2) & (Z > CZ + 25) & (Z < 134)
    return main & land(X, Z) & (_ISLE(X, Z) > 6)


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GROUND, 8082, mask=land, under="minecraft:dirt", core="minecraft:sandstone", base=-8)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:sandstone")
    # sandy beach fringe
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:sand", 0.8), ("minecraft:sandstone", 0.2)], 8084,
             mask=lambda X, Z: land(X, Z) & (_ISLE(X, Z) < 6), under="minecraft:sand", core="minecraft:sandstone", depth=2, base=-4)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 8083, mask=street, under="minecraft:dirt", core="minecraft:sandstone", depth=1, base=-2)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 8085,
             mask=lambda X, Z: (np.abs(X - CX) <= 11) & (Z >= CZ + 10) & (Z <= CZ + 26), under="minecraft:sandstone", core="minecraft:sandstone", depth=1, base=-2)
    # steps on the main street where the ground rises toward the skull
    for z in range(CZ + 26, 134):
        a, b2 = hy(CX, z), hy(CX, z + 1)
        if a > b2:
            for x in range(CX - 2, CX + 3):
                bb.fill(x, b2 + 1, z + 1, x, a - 1, z + 1, "minecraft:sandstone")
                bb.set(x, a, z + 1, st("minecraft:sandstone_stairs", "north"))


def crags(bb, rng):
    """Grey rock crags at the flanks of the skull, as in the anime."""
    for (cx, cz, r, h) in CRAGS:
        base = hy(cx, cz) - 3
        def f(X, y, Z, cx=cx, cz=cz, r=r, h=h, base=base):
            t = np.clip((y - base) / h, 0, 1)
            rr = r * (1 - t ** 1.6) * (0.8 + 0.4 * NT.noise(X * 2 + y, Z * 2 - y, 8100 + cx, 4))
            return np.hypot(X - cx, Z - cz) <= rr
        for blk, s in (("minecraft:stone", 0), ("minecraft:andesite", 1), ("minecraft:tuff", 2), ("minecraft:cobblestone", 3)):
            bb.fill_where(cx - r - 2, base, cz - r - 2, cx + r + 2, base + h, cz + r + 2,
                          lambda X, y, Z, s=s, f=f: f(X, y, Z) & ((NT.noise(X + y * 2, Z - y, 8110 + s, 5) * 4).astype(int) == s), blk)
        bb.fill_where(cx - r - 2, base, cz - r - 2, cx + r + 2, base + h, cz + r + 2, f, "minecraft:stone", only_empty=True)


# ------------------------------------------------------------------ the skull

def _face_block(q, v, u, n):
    if v > cap_v(u):
        if q > 0.3:
            return "minecraft:honeycomb_block" if n < 0.72 else "minecraft:acacia_planks"
        if q > 0.12:
            return "minecraft:acacia_planks" if n < 0.6 else "minecraft:orange_terracotta"
        return "minecraft:orange_terracotta"
    if q > 0.5:
        return "minecraft:smooth_sandstone" if n < 0.55 else ("minecraft:end_stone" if n < 0.8 else "minecraft:birch_planks")
    if q > 0.2:
        return "minecraft:sandstone" if n < 0.6 else "minecraft:smooth_sandstone"
    return "minecraft:packed_mud" if n < 0.6 else "minecraft:mud_bricks"


def skull(bb):
    base = GY - 2
    for x in range(CX - CRX - 1, CX + CRX + 2):
        u = x - CX
        for v in range(base - GY, TOPV + 1):
            q = float(skull_q(u, v))
            if q < 0:
                continue
            zf, zb = int(round(front_z(q))), int(round(back_z(q)))
            capped = v > cap_v(u)
            if capped:
                zf += 1
            y = GY + v
            bb.fill(x, y, zb, x, y, zf, "minecraft:sandstone")
            n = float(NT.noise(np.array(x * 1.0), np.array(y * 1.3), 8090, 5))
            blk = _face_block(q, v, u, n)
            bb.fill(x, y, zf - 1, x, y, zf, blk)
            bb.fill(x, y, zb, x, y, zb + 1, blk if capped else ("minecraft:sandstone" if n < 0.7 else "minecraft:smooth_sandstone" if n < 0.85 else "minecraft:packed_mud"))
            # a faint ridge on the cap, and the cap's lower lip
            if capped and abs(v - cap_v(u)) < 1.0:
                bb.set(x, y, zf + 1, "minecraft:orange_terracotta")
    # eyes: two huge round holes right through, with a bevelled dark rim
    for x in range(CX - CRX, CX + CRX + 1):
        for v in range(CRV - 15, CRV + 18):
            e = eye_e(x, v)
            q = float(skull_q(x - CX, v))
            zf, zb = int(round(front_z(q))), int(round(back_z(q)))
            if e <= 1:
                bb.fill(x, GY + v, zb - 1, x, GY + v, zf + 2, AIR)
            elif e <= 1.3:
                bb.set(x, GY + v, zf, AIR)
                bb.set(x, GY + v, zf - 1, "minecraft:mud_bricks" if e < 1.15 else "minecraft:packed_mud")
                bb.set(x, GY + v, zb, "minecraft:packed_mud")
    # hidden light blocks in the eye tunnels (keeps the light-finisher from hanging lanterns in them)
    for ex, ev in EYES:
        q = float(skull_q(ex - CX, ev))
        for z in range(int(back_z(q)) + 2, int(front_z(q)) - 1, 6):
            for (dx, dv) in ((0, -11), (-6, -8), (6, -8)):          # sitting on the eye's floor
                bb.set(ex + dx, GY + ev + dv, z, "minecraft:light[level=15,waterlogged=false]")
    # the crack from the crown down through the right eye and on down the cheek
    pts = [(1, TOPV), (4, 88), (2, 82), (7, 76), (11, 70), None, (13, 49), (10, 42), (14, 35), (9, 28), (12, 22)]
    segs, cur = [], []
    for p in pts:
        if p is None:
            segs.append(cur); cur = []
        else:
            cur.append(p)
    segs.append(cur)
    for seg in segs:
        for (a, b), (c, d) in zip(seg, seg[1:]):
            n = int(max(abs(c - a), abs(d - b)) * 2) + 1
            for i in range(n + 1):
                u = a + (c - a) * i / n
                v = b + (d - b) * i / n
                x, y = int(round(CX + u)), int(round(GY + v))
                q = float(skull_q(u, v))
                if q < 0 or eye_e(x, v) <= 1:
                    continue
                zf = int(round(front_z(q))) + (1 if v > cap_v(u) else 0)
                bb.fill(x, y, zf - 1, x, y, zf, AIR)
                bb.set(x, y, zf - 2, "minecraft:brown_terracotta")
    # the arched window between and below the eyes (the throne room looks out of it)
    q = float(skull_q(0, 40))
    zf = int(round(front_z(q)))
    for x in range(CX - 3, CX + 4):
        for y in range(THRONE_Y + 1, THRONE_Y + 9):
            top = THRONE_Y + 6 + math.sqrt(max(0.0, 9 - (x - CX) ** 2))
            if y <= top:
                bb.fill(x, y, CZ + 10, x, y, zf, AIR)
            elif y <= top + 1.2:
                bb.set(x, y, zf, "minecraft:cut_sandstone")
        bb.set(x, THRONE_Y, zf + 1, "minecraft:smooth_sandstone_slab[type=top]")
        bb.set(x, THRONE_Y + 1, zf, "minecraft:brown_stained_glass_pane" if False else AIR)
    for x in range(CX - 3, CX + 4):
        for y in range(THRONE_Y + 2, THRONE_Y + 9):
            if y <= THRONE_Y + 6 + math.sqrt(max(0.0, 9 - (x - CX) ** 2)):
                bb.set(x, y, zf - 1, "minecraft:yellow_stained_glass_pane" if (x + y) % 4 else "minecraft:dark_oak_fence")
    bb.fill(CX - 3, THRONE_Y + 1, zf, CX + 3, THRONE_Y + 1, zf, "minecraft:dark_oak_fence")
    # the bandana bow knotted on the right side
    kx, ky, kz = CX + CRX - 1, GY + 66, CZ + 4
    def lobe(cx, cy, cz, rx, ry, rz, X, y, Z):
        return ((X - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2 <= 1
    parts = [(kx, ky, kz, 3.5, 3.5, 4.5), (kx + 8, ky + 5, kz + 1, 7.0, 3.6, 3.6), (kx + 8, ky - 5, kz + 1, 7.0, 3.6, 3.6)]
    for (cx, cy, cz, rx, ry, rz) in parts:
        bb.fill_where(int(cx - rx - 1), int(cy - ry - 1), int(cz - rz - 1), int(cx + rx + 1), int(cy + ry + 1), int(cz + rz + 1),
                      lambda X, y, Z, a=(cx, cy, cz, rx, ry, rz): lobe(*a, X, y, Z), "minecraft:orange_terracotta")
        # highlight on the top-front, a shadow underneath
        bb.fill_where(int(cx - rx - 1), int(cy - ry - 1), int(cz - rz - 1), int(cx + rx + 1), int(cy + ry + 1), int(cz + rz + 1),
                      lambda X, y, Z, a=(cx, cy, cz, rx, ry, rz): lobe(*a, X, y, Z) & ((y - a[1]) + (Z - a[2]) * 0.8 > a[4] * 0.5), "minecraft:honeycomb_block")
        bb.fill_where(int(cx - rx - 1), int(cy - ry - 1), int(cz - rz - 1), int(cx + rx + 1), int(cy + ry + 1), int(cz + rz + 1),
                      lambda X, y, Z, a=(cx, cy, cz, rx, ry, rz): lobe(*a, X, y, Z) & ((y - a[1]) < -a[4] * 0.55), "minecraft:terracotta")
    # the band itself running round the cap's lower lip on the right side up to the knot
    for x in range(CX + 18, kx + 1):
        u = x - CX
        v = int(round(cap_v(u)))
        q = float(skull_q(u, v))
        if q < 0:
            continue
        zf = int(round(front_z(q))) + 1
        for k in range(2):
            bb.set(x, GY + v - k, zf + 1, "minecraft:orange_terracotta")


# ------------------------------------------------------------------ inside the skull

def insides(bb):
    y = HALL_Y
    x1, x2, z1, z2 = CX - 18, CX + 18, CZ - 8, CZ + 9
    # the jaw hall: the tavern of the Titanic Captains, vaulted
    for yy in range(y, y + 12):
        k = max(0, yy - y - 8)
        bb.fill(x1 + k, yy, z1 + k, x2 - k, yy, z2 - k, AIR)
    bb.mix(x1, y - 1, z1, x2, y - 1, z2, ["minecraft:spruce_planks", "minecraft:dark_oak_planks", "minecraft:spruce_planks"], [0.5, 0.3, 0.2])
    cols = [(xx, zz) for xx in range(x1 + 5, x2 - 3, 9) for zz in (z1 + 5, z2 - 5)]
    for (xx, zz) in cols:
        bb.fill(xx, y, zz, xx, y + 9, zz, "minecraft:dark_oak_log[axis=y]")
        bb.set(xx, y + 10, zz, "minecraft:stripped_dark_oak_wood")
    # gate: an arch through the jaw onto the plaza
    q = float(skull_q(0, MOUND + 3))
    zf = int(round(front_z(q)))
    for x in range(CX - 4, CX + 5):
        top = y + 4 + math.sqrt(max(0.0, 16 - (x - CX) ** 2)) * 0.8
        for yy in range(y, int(top) + 1):
            bb.fill(x, yy, z2, x, yy, zf + 1, AIR)
        bb.set(x, int(top) + 1, zf, "minecraft:cut_sandstone")
    bb.fill(CX - 4, y - 1, z2, CX + 4, y - 1, zf + 1, "minecraft:smooth_sandstone")
    for s in (-1, 1):
        bb.fill(CX + s * 5, y, zf, CX + s * 5, y + 6, zf + 1, "minecraft:cut_sandstone")
        bb.set(CX + s * 5, y + 3, zf + 2, "minecraft:wall_torch[facing=south]")
    pl = Plan((x1 + 1, z1 + 1, x2 - 1, z2 - 1), [(CX, z2 + 1)])
    pl.take([c for c in cols if pl.inside(*c)])
    bar_counter(pl, bb, x1 + 3, z1 + 2, y, 20, "north", "dark_oak", "x")
    _tables(pl, bb, y, "spruce", "red", length=3, gap=2)
    for xx in range(x1 + 4, x2 - 3, 7):
        for zz in (z1 + 9, z2 - 2):
            bb.fill(xx, y + 7, zz, xx, y + 10, zz, "minecraft:iron_chain[axis=y]")
            bb.set(xx, y + 6, zz, "minecraft:lantern[hanging=true]")
    wall_lights(pl, bb, y, 8, 10, light="minecraft:lantern[hanging=true]", panel=None)
    # Blackbeard's flag over the bar
    for r in range(7):
        for c in range(9):
            sk = (r in (1, 2) and 2 <= c <= 6) or (r == 3 and c in (3, 5)) or (r == 4 and 3 <= c <= 5) or (r == 5 and c in (1, 7)) or (r == 6 and c in (0, 8))
            bb.set(CX - 4 + c, y + 9 - r, z1, "minecraft:white_wool" if sk else "minecraft:black_wool")
    # Koby's cell off the east end of the hall
    kx, kz = x2 + 3, CZ
    bb.fill(kx - 2, y, kz - 2, kx + 2, y + 3, kz + 2, AIR)
    bb.fill(kx - 2, y - 1, kz - 2, kx + 2, y - 1, kz + 2, "minecraft:cobblestone")
    bb.fill(x2, y, kz - 1, kx - 3, y + 2, kz + 1, "minecraft:iron_bars")
    bb.set(kx + 2, y, kz + 2, "minecraft:iron_chain[axis=y]"); bb.set(kx + 2, y + 1, kz + 2, "minecraft:iron_chain[axis=y]")
    bb.set(kx, y, kz - 2, "minecraft:hay_block[axis=y]"); bb.set(kx - 1, y + 3, kz, "minecraft:lantern[hanging=true]")
    # the spiral core from the hall up to the throne room and the vault
    sx, sz = CX - 3, CZ - 8
    stair_core(bb, sx, sz, 6, y, VAULT_Y, [y, THRONE_Y + 1, VAULT_Y + 1], "minecraft:sandstone", "minecraft:dark_oak_stairs", slit=None)
    bb.fill(sx + 1, y, sz + 6, sx + 4, y + 2, z1, AIR)
    # throne room behind the arched window
    ty = THRONE_Y + 1
    tx1, tx2, tz1, tz2 = CX - 12, CX + 12, CZ - 1, CZ + 9
    bb.fill(tx1, ty - 1, tz1, tx2, ty - 1, tz2, "minecraft:polished_blackstone_bricks")
    bb.fill(tx1, ty, tz1, tx2, ty + 8, tz2, AIR)
    bb.fill(CX - 2, ty - 1, tz1 + 2, CX + 2, ty - 1, tz2, "minecraft:red_terracotta")
    bb.fill(CX - 1, ty, tz1 + 3, CX + 1, ty, tz2 - 1, "minecraft:red_carpet")
    bb.fill(sx + 1, ty, sz + 6, sx + 4, ty + 2, tz1, AIR)
    # Blackbeard's throne on a dais at the back, facing the window
    bb.fill(CX - 3, ty, tz1, CX + 3, ty, tz1 + 1, "minecraft:polished_blackstone")
    bb.set(CX, ty + 1, tz1 + 1, st("minecraft:dark_oak_stairs", "north"))
    bb.fill(CX - 1, ty + 1, tz1, CX + 1, ty + 4, tz1, "minecraft:dark_oak_planks")
    for s in (-1, 1):
        bb.set(CX + s, ty + 1, tz1 + 1, "minecraft:dark_oak_trapdoor[facing=%s,half=bottom,open=true]" % ("east" if s < 0 else "west"))
    pl = Plan((tx1 + 1, tz1 + 2, tx2 - 1, tz2 - 1), [(CX, tz2 + 1), (CX - 1, tz1 + 1)])
    table_group(pl, bb, CX - 10, tz1 + 4, ty, 5, "x", "dark_oak", "black")
    table_group(pl, bb, CX + 5, tz1 + 4, ty, 5, "x", "dark_oak", "black")
    wall_lights(Plan((tx1, tz1, tx2, tz2), [(CX, tz2 + 1)]), bb, ty, 8, 10, panel=None)
    # vault in the cap
    vy = VAULT_Y + 1
    bb.fill(CX - 8, vy - 1, CZ - 6, CX + 8, vy + 5, CZ + 7, AIR)
    bb.fill(CX - 8, vy - 1, CZ - 6, CX + 8, vy - 1, CZ + 7, "minecraft:polished_blackstone_bricks")
    bb.fill_where(CX - 8, vy, CZ - 6, CX + 8, vy + 1, CZ + 7,
                  lambda X, Y, Z: ((np.abs(X - CX) >= 6) | (Z >= CZ + 5)) & (Y - vy <= np.minimum(np.abs(X - CX) - 6, Z - CZ - 5) + 1) & ~((np.abs(X - CX) <= 4) & (Z <= CZ - 2)),
                  "minecraft:gold_block")
    for x in (CX - 7, CX + 7):
        for z in (CZ - 5, CZ + 6):
            bb.set(x, vy, z, "minecraft:barrel[facing=up,open=false]")
    for (lx, lz) in ((CX - 4, CZ), (CX + 4, CZ), (CX, CZ + 4)):
        bb.set(lx, vy + 5, lz, "minecraft:lantern[hanging=true]")


# ------------------------------------------------------------------ the city

def box_house(bb, x0, z0, w, d, y0, floors, rng, face, extra=True, fh=4):
    """A flat-roofed cream/tan box house: trim corners and floor bands, small windows with sills, a door on `face`,
    floors joined by a ladder, every floor furnished. Returns the roof y."""
    wall, trim, slab = HOUSE[int(rng.integers(0, len(HOUSE)))]
    x1, z1 = x0 + w - 1, z0 + d - 1
    top = y0 + floors * fh
    bb.fill(x0, y0, z0, x1, top, z1, wall)
    bb.fill(x0 + 1, y0, z0 + 1, x1 - 1, top - 1, z1 - 1, AIR)
    for (cx, cz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        bb.fill(cx, y0, cz, cx, top, cz, trim)
    wood = WOODS[int(rng.integers(0, len(WOODS)))]
    for f in range(floors):
        yf = y0 + f * fh
        if f:
            bb.fill(x0 + 1, yf - 1, z0 + 1, x1 - 1, yf - 1, z1 - 1, f"minecraft:{wood}_planks")
            for (a, b) in ((x0, z0), (x1, z0)):
                pass
            bb.fill(x0, yf - 1, z0, x1, yf - 1, z0, trim); bb.fill(x0, yf - 1, z1, x1, yf - 1, z1, trim)
            bb.fill(x0, yf - 1, z0, x0, yf - 1, z1, trim); bb.fill(x1, yf - 1, z0, x1, yf - 1, z1, trim)
        else:
            bb.fill(x0 + 1, yf - 1, z0 + 1, x1 - 1, yf - 1, z1 - 1, f"minecraft:{wood}_planks")
        # windows with sills on all four sides
        for side, xs, zs, out in (("south", range(x0 + 2, x1 - 1, 2), [z1], (0, 1)), ("north", range(x0 + 2, x1 - 1, 2), [z0], (0, -1)),
                                  ("east", [x1], range(z0 + 2, z1 - 1, 2), (1, 0)), ("west", [x0], range(z0 + 2, z1 - 1, 2), (-1, 0))):
            for wx in xs:
                for wz in zs:
                    if f == 0 and side == face and abs((wx - (x0 + x1) // 2) if side in ("south", "north") else (wz - (z0 + z1) // 2)) <= 1:
                        continue
                    if rng.random() < 0.25:
                        continue
                    bb.fill(wx, yf + 1, wz, wx, yf + 2, wz, "minecraft:brown_stained_glass_pane" if rng.random() < 0.6 else "minecraft:glass_pane")
                    bb.set(wx + out[0], yf, wz + out[1], slab + "[type=top]")
    # ladder in the north-west inner corner
    if floors > 1:
        bb.fill(x0 + 1, y0, z0 + 1, x0 + 1, top - 1, z0 + 1, "minecraft:ladder[facing=south]")
    # the door
    dx, dz = {"south": ((x0 + x1) // 2, z1), "north": ((x0 + x1) // 2, z0), "east": (x1, (z0 + z1) // 2), "west": (x0, (z0 + z1) // 2)}[face]
    ox, oz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[face]
    bb.set(dx, y0, dz, f"minecraft:{wood}_door[facing={face},half=lower,hinge=left]")
    bb.set(dx, y0 + 1, dz, f"minecraft:{wood}_door[facing={face},half=upper,hinge=left]")
    g = hy(dx + ox, dz + oz)
    if g < y0 - 1:
        bb.fill(dx + ox, g + 1, dz + oz, dx + ox, y0 - 1, dz + oz, trim)
    bb.fill(dx + ox, y0, dz + oz, dx + ox, y0 + 2, dz + oz, AIR)
    side_x, side_z = (dx + 1, dz) if face in ("south", "north") else (dx, dz + 1)
    bb.set(side_x + ox, y0 + 2, side_z + oz, f"minecraft:wall_torch[facing={face}]")
    # furnish every floor
    for f in range(floors):
        yf = y0 + f * fh
        doors = [(x0 + 1, z0)] if floors > 1 else []
        if f == 0:
            doors.append((dx, dz))
        furnish_kit(bb, (x0 + 1, z0 + 1, x1 - 1, z1 - 1), yf, fh - 1, KINDS[int(rng.integers(0, len(KINDS)))], wood=wood,
                    seed=int(rng.integers(0, 1 << 30)), doors=doors, accent=["red", "orange", "yellow", "green", "brown", "blue"][int(rng.integers(0, 6))])
    # roof: parapet, then a garden, an add-on room, a little dome or clutter
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                bb.set(x, top + 1, z, slab + "[type=bottom]")
    if floors > 1:
        bb.set(x0 + 1, top, z0 + 1, "minecraft:ladder[facing=south]") if False else bb.set(x0 + 1, top, z0 + 1, f"minecraft:{wood}_trapdoor[facing=south,half=top,open=false]")
    r = rng.random()
    if r < 0.25 and w >= 5 and d >= 5:
        bb.fill(x0 + 1, top, z0 + 2, x1 - 1, top, z1 - 1, "minecraft:moss_block")
        for _ in range(3):
            px, pz = int(rng.integers(x0 + 1, x1)), int(rng.integers(z0 + 2, z1))
            bb.set(px, top + 1, pz, "minecraft:flowering_azalea" if rng.random() < 0.5 else "minecraft:azalea")
    elif r < 0.45 and extra and w >= 6 and d >= 6:
        aw, ad = w - 2 - int(rng.integers(0, 2)), d - 2 - int(rng.integers(0, 2))
        ax = x0 + (0 if rng.random() < 0.5 else w - aw)
        az = z0 + (0 if rng.random() < 0.5 else d - ad)
        fc = "south" if az == z0 else "north"
        box_house(bb, ax, az, aw, ad, top + 1, 1, rng, fc, extra=False)
    elif r < 0.55 and w >= 5 and d >= 5:
        onion_dome(bb, (x0 + x1) // 2, top + 1, (z0 + z1) // 2, 1.6, "minecraft:green_terracotta" if rng.random() < 0.6 else "minecraft:oxidized_cut_copper",
                   tip="minecraft:lightning_rod")
    elif r < 0.7:
        bb.set(x1 - 1, top + 1, z1 - 1, "minecraft:barrel[facing=up,open=false]")
        bb.fill(x1 - 1, top + 1, z0 + 1, x1 - 1, top + 3, z0 + 1, f"minecraft:{wood}_fence")
        bb.fill(x0 + 1, top + 3, z0 + 1, x1 - 2, top + 3, z0 + 1, "minecraft:white_wool" if False else AIR)
    return top


def city(bb, rng):
    houses = []
    def blocked(x0, z0, x1, z1):
        X = np.arange(x0 - 1, x1 + 2)[:, None]; Z = np.arange(z0 - 1, z1 + 2)[None, :]
        if (~land(X, Z)).any() or (_ISLE(X, Z) < 8).any() or street(X, Z).any():
            return True
        if (_skull_dist(X, Z) < 1).any():
            return True
        if ((np.abs(X - CX) <= 12) & (Z >= CZ + 9) & (Z <= CZ + 27)).any():
            return True
        if ((Z >= 126) & (np.abs(X - 88) < 36)).any():                      # the quay and market
            return True
        return any(x0 - 1 <= b[2] and b[0] <= x1 + 1 and z0 - 1 <= b[3] and b[1] <= z1 + 1 for b in houses)
    cand = [(x, z) for x in range(6, N - 12) for z in range(6, N - 12)]
    key = [float(_skull_dist(np.array(x + 3.0), np.array(z + 3.0))) + rng.random() * 30 for (x, z) in cand]
    order = np.argsort(key)
    for i in order:
            x0, z0 = cand[i]
            if any(np.hypot(x0 + 3 - cx, z0 + 3 - cz) < r + 5 for (cx, cz, r, h) in CRAGS):
                continue
            w, d = int(rng.integers(5, 8)), int(rng.integers(5, 8))
            x1, z1 = x0 + w - 1, z0 + d - 1
            if blocked(x0, z0, x1, z1):
                continue
            X = np.arange(x0, x1 + 1)[:, None]; Z = np.arange(z0, z1 + 1)[None, :]
            hs = height(X, Z)
            g = int(hs.max())
            near = float(np.clip(1 - _skull_dist(np.array(float((x0 + x1) / 2)), np.array(float((z0 + z1) / 2))) / 54.0, 0, 1))
            floors = 1 + int(rng.random() < 0.5 + 0.5 * near) + int(rng.random() < 0.2 + 0.6 * near) + int(rng.random() < 0.7 * near ** 1.5) + int(rng.random() < 0.6 * near ** 2)
            # face downhill / toward the street
            mx, mz = (x0 + x1) / 2 - CX, (z0 + z1) / 2 - (CZ + 4)
            if abs(mz) >= abs(mx):
                face = "south" if mz > 0 else "north"
            else:
                face = "east" if mx > 0 else "west"
            # plinth from the lowest ground up
            bb.fill(x0, int(hs.min()) - 2, z0, x1, g, z1, "minecraft:sandstone" if rng.random() < 0.6 else "minecraft:mud_bricks")
            box_house(bb, x0, z0, w, d, g + 1, floors, rng, face)
            houses.append((x0, z0, x1, z1))
    # lamp posts on the streets
    for z in range(CZ + 28, 132, 6):
        for s in (-3, 3):
            x = CX + s
            if bb.get_region(x, hy(x, z) + 1, z, x, hy(x, z) + 1, z)[0, 0, 0] in (0, 1):
                lamp_post(bb, x, hy(x, z) + 1, z, post="minecraft:dark_oak_fence", h=3)
    print("houses:", len(houses))
    return houses


def plaza(bb):
    """The plaza before the jaw gate: fountain, stalls, flags."""
    y = GY + MOUND + 1
    fx, fz = CX, CZ + 20
    bb.fill_where(fx - 3, y - 1, fz - 3, fx + 3, y, fz + 3, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 3.2, "minecraft:cut_sandstone")
    bb.fill_where(fx - 2, y, fz - 2, fx + 2, y, fz + 2, lambda X, Y, Z: np.hypot(X - fx, Z - fz) <= 2.2, "minecraft:water")
    bb.fill(fx, y, fz, fx, y + 2, fz, "minecraft:cut_sandstone"); bb.set(fx, y + 3, fz, "minecraft:lantern[hanging=false]")
    colors = ["red", "yellow", "orange", "purple"]
    for i, (sx, sz) in enumerate(((CX - 10, CZ + 14), (CX + 7, CZ + 14), (CX - 10, CZ + 21), (CX + 7, CZ + 21))):
        for (a, b) in ((sx, sz), (sx + 3, sz), (sx, sz + 2), (sx + 3, sz + 2)):
            bb.fill(a, y, b, a, y + 2, b, "minecraft:spruce_fence")
        for x in range(sx, sx + 4):
            for z in range(sz, sz + 3):
                bb.set(x, y + 3, z, f"minecraft:{colors[i] if (x - sx) % 2 == 0 else 'white'}_wool")
        bb.set(sx + 1, y, sz + 1, "minecraft:barrel[facing=up,open=false]"); bb.set(sx + 2, y, sz + 1, "minecraft:melon" if i % 2 else "minecraft:pumpkin")
    for s in (-1, 1):
        x = CX + s * 9
        bb.fill(x, y, CZ + 12, x, y + 9, CZ + 12, "minecraft:dark_oak_fence")
        for r in range(3):
            for c in range(4):
                bb.set(x + s * (c + 1), y + 8 - r, CZ + 12, "minecraft:black_wool" if (r, c) != (1, 1) else "minecraft:white_wool")


def harbour(bb, rng):
    """Piers in the bay, a market of stalls on the quay, two visiting pirate ships."""
    qz = 136
    bb.fill(56, -6, qz, 120, GY, qz + 3, "minecraft:cobbled_deepslate")
    bb.mix(56, GY, qz, 120, GY, qz + 3, ["minecraft:spruce_planks", "minecraft:dark_oak_planks"], [0.6, 0.4])
    bb.fill(56, GY + 1, qz, 120, GY + 12, qz + 3, AIR)
    for px in (64, 88, 112):
        bb.fill(px - 1, GY - 1, qz + 4, px + 1, GY - 1, qz + 26, "minecraft:spruce_planks")
        for z in range(qz + 4, qz + 27, 4):
            bb.fill(px - 2, -6, z, px - 2, GY - 1, z, "minecraft:spruce_log[axis=y]")
            bb.fill(px + 2, -6, z, px + 2, GY - 1, z, "minecraft:spruce_log[axis=y]")
            bb.set(px - 2, GY, z, "minecraft:spruce_fence"); bb.set(px + 2, GY, z, "minecraft:spruce_fence")
        bb.set(px - 2, GY + 1, qz + 26, "minecraft:lantern[hanging=false]"); bb.set(px + 2, GY + 1, qz + 26, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "bezan_black", 76, qz + 15, water_y=0, rot=1)
    stamp_ship(bb, "victoria_punk", 100, qz + 16, water_y=0, rot=1)
    # market stalls with striped awnings along the quay
    colors = ["red", "yellow", "green", "blue", "orange", "purple"]
    for i, sx in enumerate(range(58, 118, 7)):
        if abs(sx + 2 - 88) < 4:
            continue
        sz = qz - 6
        c = colors[i % len(colors)]
        for (a, b) in ((sx, sz), (sx + 4, sz), (sx, sz + 3), (sx + 4, sz + 3)):
            bb.fill(a, GY + 1, b, a, GY + 3, b, "minecraft:spruce_fence")
        for x in range(sx, sx + 5):
            for z in range(sz, sz + 4):
                bb.set(x, GY + 4, z, f"minecraft:{c if (x - sx) % 2 == 0 else 'white'}_wool")
        bb.fill(sx + 1, GY + 1, sz + 3, sx + 3, GY + 1, sz + 3, st("minecraft:spruce_stairs", "north", "top"))
        bb.set(sx + 1, GY + 2, sz + 3, "minecraft:barrel[facing=up,open=false]" if i % 2 else "minecraft:melon")
        bb.set(sx + 3, GY + 2, sz + 3, "minecraft:pumpkin" if i % 3 else "minecraft:hay_block[axis=y]")


def scenery(bb, rng, houses):
    """Palms in the gaps and on the beach, a few boulders, grass tufts."""
    for _ in range(1400):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or _ISLE(X, Z)[0, 0] < 3 or _skull_dist(X, Z)[0, 0] < 3 or street(X, Z)[0, 0]:
            continue
        if any(b[0] - 2 <= x <= b[2] + 2 and b[1] - 2 <= z <= b[3] + 2 for b in houses):
            continue
        y = hy(x, z)
        if bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] > 1 or bb.get_region(x, y, z, x, y, z)[0, 0, 0] <= 1:
            continue
        r = rng.random()
        if r < 0.07:
            palm(bb, x, y + 1, z, int(rng.integers(8, 13)), (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))))
        elif r < 0.09:
            NT.boulder(bb, x, y, z, int(rng.integers(1, 3)), rng, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:tuff"))
        elif r < 0.3:
            bb.set(x, y + 1, z, "minecraft:short_grass" if r < 0.25 else "minecraft:fern")


def design():
    bb = BigBuild(seed=8080, y_min=-14, y_max=GY + TOPV + 6)
    rng = np.random.default_rng(8080)
    terrain(bb)
    crags(bb, rng)
    skull(bb)
    insides(bb)
    plaza(bb)
    houses = city(bb, rng)
    harbour(bb, rng)
    scenery(bb, rng, houses)
    return bb, []


def build():
    bb, audit = design()
    b = to_canvas(bb)
    steady(b)
    y = HALL_Y
    b.npc(CX, THRONE_Y + 1, CZ + 5, "blackbeard", True)
    b.chest(CX - 3, VAULT_Y + 1, CZ - 4, "legendary", "south"); b.chest(CX + 3, VAULT_Y + 1, CZ - 4, "legendary", "south")
    b.chest(CX - 16, y, CZ - 6, "treasure", "east")
    b.chest(CX + 22, y, CZ + 1, "medium", "west")
    b.guards("blackbeard_pirate", ((CX - 6, CZ + 6), (CX + 6, CZ + 6), (CX - 6, CZ + 22), (CX + 6, CZ + 22)), y=y)
    b.guards("blackbeard_pirate", ((CX - 8, CZ + 6), (CX + 8, CZ + 6)), y=THRONE_Y + 1)
    b.guards("pirate_gunner", ((70, 132), (106, 132)), y=GY + 1)
    return b, 0
