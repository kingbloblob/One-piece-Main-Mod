"""Punk Hazard v2, the island split in two, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/punk_hazard_lab.md).

An irregular island whose ground fades out to its beaches: the west half frozen solid (snow fields, ice spikes, snowy
spruces, a frozen lake, and the Marine G-5 warship locked in the ice of a western cove), the east half burning
(black volcanic rock and ash, lava pools in hollows, smoking vents, dead trees, the bones of a dragon and the burnt-out
shell of the old Government lab). A rocky spine runs along the line where the two halves meet. In the middle stands
Caesar Clown's research facility: the main building (an entrance hall and the SAD chamber both two storeys tall,
three floors of labs, stores and quarters in the wings, Caesar's office and the control room under the dome on top),
the Biscuit Room building where the children were kept (west, joined by a glass tube) and the gas works (east, with
its tanks and a big spherical gas reservoir). 176 x 168. y 0 = ground / sea surface. (v2)

v3 (2026-10-30, audit: "the fire half and ice half are hard to tell apart from the sea"): the halves now read from
far off. The west rises into two glaciated snow mountains (white caps, packed-ice cliffs) and the sea round it is
frozen into a sheet of ice and floes; the east rises into a black volcano with a glowing crater, lava pools, magma
streaks down its flanks and smoke, and the sea round it is dark over a seabed of blackstone and magma. The sea fills
only a round patch inside a wobbly rim."""
from mcb import terrain3 as T3
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "punk_hazard_lab"
TITLE = "Punk Hazard Laboratory"
CUTS = [2, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False

NX, NZ = 176, 168
CX, CZ = 88, 84
MIDX = 90
A = (60, 50, 120, 86)                   # main building box (x1, z1, x2, z2)
FH = 6
HALL = (80, 71, 100, 85)                # entrance hall (inside A)
SAD = (80, 51, 100, 65)                 # SAD chamber
B_BOX = (28, 56, 54, 80)                # Biscuit Room building
C_BOX = (126, 56, 150, 80)              # gas works
YARD = (22, 42, 158, 104)               # paved / flat facility ground
LAKE = (40, 30, 15, 10)                 # frozen lake (x, z, rx, rz)
COVE = (10, 124, 28, 16)                # frozen cove with the G-5 ship
SHIP = (21, 124)
RUIN = (124, 106, 148, 124)             # burnt-out old lab
DRAGON = (92, 142)                      # dragon bones (tail end)
SPHERE = (134, 34, 8)
PEAKS = ((34, 18, 30, 44, "cold"), (62, 172, 26, 36, "cold"), (174, 118, 32, 58, "hot"))   # x, z, r, h, half
VOLC = PEAKS[2]

WHITE = "minecraft:white_concrete"
LGRAY = "minecraft:light_gray_concrete"
CYAN = "minecraft:cyan_concrete"
PANEL = "onepiece:lab_panel"
LIGHT = "onepiece:lab_light"
GLASS = "minecraft:light_blue_stained_glass"
QST = "minecraft:quartz_stairs"

_SHORE = NT.outline(CX, CZ, 80, 1531)


def SHORE(X, Z):
    """Distance inland from the coast; the mountains push headlands out past the old outline."""
    d = _SHORE(X, Z)
    for (px, pz, pr, ph, _) in PEAKS:
        d = np.maximum(d, pr * 0.8 - np.hypot(X - px, Z - pz) * (1 + 0.1 * NT.noise(X, Z, 1547, 7)))
    return d

SNOW = [("minecraft:snow_block", 0.56), ("minecraft:grass_block[snowy=true]", 0.12), ("minecraft:packed_ice", 0.08),
        ("minecraft:stone", 0.07), ("minecraft:gravel", 0.07), ("minecraft:podzol[snowy=true]", 0.10)]
SNOW_ROCK = [("minecraft:stone", 0.38), ("minecraft:snow_block", 0.30), ("minecraft:andesite", 0.16),
             ("minecraft:packed_ice", 0.10), ("minecraft:tuff", 0.06)]
ASH = [("minecraft:blackstone", 0.22), ("minecraft:basalt[axis=y]", 0.16), ("onepiece:scorched_stone", 0.18),
       ("onepiece:volcanic_ash", 0.16), ("minecraft:smooth_basalt", 0.10), ("minecraft:magma_block", 0.06),
       ("minecraft:coarse_dirt", 0.12)]
ASH_ROCK = [("minecraft:blackstone", 0.34), ("minecraft:basalt[axis=y]", 0.26), ("minecraft:tuff", 0.16),
            ("onepiece:scorched_stone", 0.16), ("minecraft:magma_block", 0.08)]
SHORE_COLD = [("minecraft:gravel", 0.34), ("minecraft:snow_block", 0.26), ("minecraft:stone", 0.18),
              ("minecraft:andesite", 0.12), ("minecraft:packed_ice", 0.10)]
SHORE_HOT = [("minecraft:blackstone", 0.30), ("minecraft:gravel", 0.26), ("minecraft:tuff", 0.20),
             ("minecraft:basalt[axis=y]", 0.14), ("minecraft:coarse_dirt", 0.10)]
GLACIER = [("minecraft:snow_block", 0.55), ("minecraft:packed_ice", 0.2), ("minecraft:powder_snow", 0.0),
           ("minecraft:blue_ice", 0.07), ("minecraft:snow_block", 0.18)]
SCORCH = [("minecraft:blackstone", 0.3), ("minecraft:basalt[axis=y]", 0.25), ("minecraft:magma_block", 0.17),
          ("onepiece:scorched_stone", 0.18), ("minecraft:netherrack", 0.10)]
PAVE = [("minecraft:polished_andesite", 0.5), ("minecraft:smooth_stone", 0.25), ("minecraft:andesite", 0.15),
        ("minecraft:cracked_stone_bricks", 0.10)]


def border(X, Z):
    """Signed distance-ish to the fire/ice line (negative = frozen west, positive = burning east)."""
    Z0 = np.zeros_like(X) + Z
    return X - (MIDX + 7 * np.sin(Z0 * 0.06) + 10 * (NT.noise(Z0 * 0, Z0, 1532, 17) - 0.5))


def cold(X, Z):
    return border(X, Z) < 0


def ell(X, Z, e):
    x, z, rx, rz = e
    return ((X - x) / rx) ** 2 + ((Z - z) / rz) ** 2


def rect_d(X, Z, r):
    """Distance outside a rectangle (0 inside)."""
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def flatness(X, Z):
    """0 on the facility yard, the lake, the cove and the road to the ship, 1 well away from them."""
    d = rect_d(X, Z, YARD)
    d = np.minimum(d, (np.sqrt(ell(X, Z, LAKE)) - 1) * LAKE[2])
    d = np.minimum(d, (np.sqrt(ell(X, Z, COVE)) - 1) * COVE[3] - 4)
    d = np.minimum(d, rect_d(X, Z, (30, 98, 46, 116)))                 # road down to the cove
    d = np.minimum(d, rect_d(X, Z, RUIN) - 2)
    return np.clip(d / 14.0, 0, 1)


def height(X, Z):
    d = SHORE(X, Z)
    inland = np.clip((d - 3) / 16.0, 0, 1)
    c = cold(X, Z)
    hills = np.where(c, NT.fbm(X, Z, 1541, 30) * 8, NT.fbm(X, Z, 1542, 22) * 10 + NT.noise(X, Z, 1543, 5) * 2.5)
    bd = np.abs(border(X, Z))
    spine = np.clip(1 - bd / 16.0, 0, 1) ** 1.4 * (16 + 16 * NT.fbm(X, Z, 1544, 16))
    for (px, pz, pr, ph, _) in PEAKS:
        r = np.hypot(X - px, Z - pz) * (1 + 0.12 * NT.noise(X, Z, 1545 + px, 9))
        cone = ph * np.clip(1 - r / pr, 0, 1) ** 1.15 + 3 * NT.fbm(X, Z, 1546, 6) * (r < pr)
        if px == VOLC[0]:
            cone = np.where(r < 6, ph - 8 + (r - 6) * -0.0 - (6 - r) * 0.6, cone)     # the crater
        hills = np.maximum(hills, cone * np.clip((d - 2) / 10.0, 0, 1))
    h = np.maximum(hills, spine) * inland * flatness(X, Z)
    h = np.where(d < 2.5, -1, h)
    return np.round(h)


def land(X, Z):
    return (SHORE(X, Z) > 0) & (ell(X, Z, COVE) >= 1)


def hy(x, z):
    return int(height(np.array([[x]]), np.array([[z]]))[0, 0])


def cold_at(x, z):
    return bool(cold(np.array([[x]]), np.array([[z]]))[0, 0])


# ------------------------------------------------------------------ ground
def terrain(bb):
    H = height
    inner = lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (rect_d(X, Z, YARD) > 0)
    NT.cover(bb, -22, -22, 201, 201, H, SHORE_COLD, 1551, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6) & cold(X, Z),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, -22, -22, 201, 201, H, SHORE_HOT, 1552, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6) & ~cold(X, Z),
             under="minecraft:blackstone", core="minecraft:blackstone")
    NT.cover(bb, -22, -22, 201, 201, H, SNOW, 1553, mask=lambda X, Z: inner(X, Z) & cold(X, Z) & (H(X, Z) < 12),
             core="minecraft:stone")
    NT.cover(bb, -22, -22, 201, 201, H, SNOW_ROCK, 1554, mask=lambda X, Z: inner(X, Z) & cold(X, Z) & (H(X, Z) >= 12),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, -22, -22, 201, 201, H, ASH, 1555, mask=lambda X, Z: inner(X, Z) & ~cold(X, Z) & (H(X, Z) < 12),
             under="minecraft:blackstone", core="minecraft:blackstone")
    NT.cover(bb, -22, -22, 201, 201, H, ASH_ROCK, 1556, mask=lambda X, Z: inner(X, Z) & ~cold(X, Z) & (H(X, Z) >= 12),
             under="minecraft:blackstone", core="minecraft:blackstone")
    NT.cover(bb, -22, -22, 201, 201, H, GLACIER, 1564, mask=lambda X, Z: inner(X, Z) & cold(X, Z) & (H(X, Z) >= 22),
             under="minecraft:packed_ice", core="minecraft:stone")
    NT.cover(bb, -22, -22, 201, 201, H, SCORCH, 1565, mask=lambda X, Z: inner(X, Z) & ~cold(X, Z) & (H(X, Z) >= 26),
             under="minecraft:blackstone", core="minecraft:blackstone")
    # the yard: worn paving round the buildings, ground showing through at its ragged edge
    NT.cover(bb, YARD[0], YARD[1], YARD[2], YARD[3], H, PAVE, 1557,
             mask=lambda X, Z: land(X, Z) & (NT.noise(X, Z, 1558, 6) * 6 > rect_d(X, Z, (YARD[0] + 6, YARD[1] + 6, YARD[2] - 6, YARD[3] - 6))),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, YARD[0], YARD[1], YARD[2], YARD[3], H, SNOW, 1559,
             mask=lambda X, Z: land(X, Z) & cold(X, Z) & ~(NT.noise(X, Z, 1558, 6) * 6 > rect_d(X, Z, (YARD[0] + 6, YARD[1] + 6, YARD[2] - 6, YARD[3] - 6))),
             core="minecraft:stone")
    NT.cover(bb, YARD[0], YARD[1], YARD[2], YARD[3], H, ASH, 1560,
             mask=lambda X, Z: land(X, Z) & ~cold(X, Z) & ~(NT.noise(X, Z, 1558, 6) * 6 > rect_d(X, Z, (YARD[0] + 6, YARD[1] + 6, YARD[2] - 6, YARD[3] - 6))),
             under="minecraft:blackstone", core="minecraft:blackstone")
    # the frozen lake: ice over dark water
    x, z, rx, rz = LAKE
    m = lambda X, yy, Z: ell(X, Z, LAKE) < 1
    bb.fill_where(x - rx, -4, z - rz, x + rx, 0, z + rz, m, AIR)
    bb.fill_where(x - rx, -4, z - rz, x + rx, -4, z + rz, m, "minecraft:gravel")
    bb.fill_where(x - rx, -3, z - rz, x + rx, -1, z + rz, lambda X, yy, Z: ell(X, Z, LAKE) < 1 - 0.25 * (yy == -3), "minecraft:water")
    bb.fill_where(x - rx, -3, z - rz, x + rx, -1, z + rz, m, "minecraft:stone", only_empty=True)
    bb.fill_where(x - rx, 0, z - rz, x + rx, 0, z + rz,
                  lambda X, yy, Z: (ell(X, Z, LAKE) < 1) & (NT.noise(X, Z, 1561, 3) > 0.2), "minecraft:ice")
    bb.fill_where(x - rx, 0, z - rz, x + rx, 0, z + rz, m, "minecraft:packed_ice", only_empty=True)
    # the cove: sea ice over water that deepens to the open sea
    x, z, rx, rz = COVE

    def depth(X, Z):
        t = ell(X, Z, COVE)
        return np.where(t < 1, np.round(-2 - 7 * (1 - t) ** 0.5 - 3 * np.clip((x - X) / rx, 0, 1)), 99)
    for y in range(-13, 1):
        sel = lambda X, yy, Z: (depth(X, Z) < yy) & (SHORE(X, Z) > -6)
        bb.fill_where(0, y, z - rz, x + rx, y, z + rz, sel, "minecraft:water")
        bb.fill_where(0, y, z - rz, x + rx, y, z + rz, lambda X, yy, Z: (depth(X, Z) == yy) & (SHORE(X, Z) > -6), "minecraft:gravel")
        bb.fill_where(0, y, z - rz, x + rx, y, z + rz, lambda X, yy, Z: (depth(X, Z) - 1 == yy) & (SHORE(X, Z) > -6), "minecraft:stone")

    # the sea round the island: frozen over on the west, dark over a burning seabed on the east
    n, o = 224, -22
    GX, GZ = T3.grid(n)
    GX, GZ = GX + o, GZ + o
    landm = land(GX, GZ) | (ell(GX, GZ, COVE) < 1.2)
    W, bed, rr = T3.sea(bb, n, landm, CX + 8, CZ + 10, 102, 1566, deep=-13, shelf=12, y_min=-14, x0=o, z0=o)
    coldm = cold(GX, GZ)
    nz = NT.noise(GX, GZ, 1567, 6)
    ice = W & coldm & (nz > 0.22) & (rr < 0.97)
    bb.fill_where(o, 0, o, o + n - 1, 0, o + n - 1, lambda XX, yy, ZZ: ice & (nz > 0.55), "minecraft:packed_ice")
    bb.fill_where(o, 0, o, o + n - 1, 0, o + n - 1, lambda XX, yy, ZZ: ice & (nz <= 0.55), "minecraft:ice")
    hot = W & ~coldm
    for y in range(-14, 0):
        bb.fill_where(o, y, o, o + n - 1, y, o + n - 1, lambda XX, yy, ZZ: hot & (bed == yy), "minecraft:blackstone")
        bb.fill_where(o, y, o, o + n - 1, y, o + n - 1, lambda XX, yy, ZZ: hot & (bed == yy) & (NT.noise(XX, ZZ, 1568, 4) > 0.62),
                      "minecraft:magma_block")


def volcano_top(bb, rng):
    """The crater: a lava lake sealed in basalt, smoke from signal fires on hay round the rim, magma streaks."""
    vx, vz, vr, vh = VOLC[:4]
    top = hy(vx, vz)
    bb.fill_where(vx - 7, top - 2, vz - 7, vx + 7, top, vz + 7, lambda X, Y, Z: np.hypot(X - vx, Z - vz) < 6.5, "minecraft:basalt[axis=y]")
    bb.fill_where(vx - 7, top, vz - 7, vx + 7, top, vz + 7, lambda X, Y, Z: np.hypot(X - vx, Z - vz) < 4.6, "minecraft:lava")
    bb.fill_where(vx - 7, top + 1, vz - 7, vx + 7, top + 1, vz + 7,
                  lambda X, Y, Z: (np.hypot(X - vx, Z - vz) >= 4.6) & (np.hypot(X - vx, Z - vz) < 6.2), "minecraft:magma_block")
    for k in range(6):
        a = k * math.pi / 3 + 0.4
        x, z = round(vx + 7.5 * math.cos(a)), round(vz + 7.5 * math.sin(a))
        y = hy(x, z)
        bb.set(x, y + 1, z, "minecraft:hay_block")
        bb.set(x, y + 2, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        for st_ in range(7, int(vr * 0.9)):
            x = int(round(vx + st_ * math.cos(a) + 1.5 * math.sin(st_ / 3)))
            z = int(round(vz + st_ * math.sin(a)))
            if not land(np.array([[x]]), np.array([[z]]))[0, 0] or cold_at(x, z):
                break
            y = hy(x, z)
            bb.set(x, y, z, "minecraft:magma_block" if st_ % 5 else "minecraft:shroomlight")
            bb.set(x + 1, y, z, "minecraft:magma_block" if st_ < vr * 0.6 else "minecraft:blackstone")


def sea_ice(bb):
    """Freeze the cove's surface (after the ship is in): ice floes and packed ice, a few dark leads of open water."""
    x, z, rx, rz = COVE
    X = np.arange(0, x + rx + 1)[:, None]
    Z = np.arange(z - rz, z + rz + 1)[None, :]
    names = bb.names
    reg = bb.get_region(0, 0, z - rz, x + rx, 0, z + rz)[:, 0, :]
    water = np.vectorize(lambda i: names[i].startswith("minecraft:water"))(reg)
    keep = (ell(X, Z, COVE) < 1.25) & (SHORE(X, Z) > -8)
    n = NT.noise(X, Z, 1562, 5)
    for (lo, hi, blk) in ((0.32, 1.1, "minecraft:ice"), (0.62, 1.1, "minecraft:packed_ice")):
        sel = water & keep & (n > lo) & (n <= hi)
        bb.fill_where(0, 0, z - rz, x + rx, 0, z + rz, lambda XX, yy, ZZ, s=sel: s, blk)


def snow_layers(bb, rng):
    """Snow drifts on the frozen half: layers in patches, thicker in the hollows."""
    X = np.arange(0, NX)[:, None]
    Z = np.arange(0, NZ)[None, :]
    H = height(X, Z).astype(int)
    M = land(X, Z) & cold(X, Z) & (rect_d(X, Z, (A[0] - 3, A[1] - 3, A[2] + 3, A[3] + 3)) > 0) & \
        (rect_d(X, Z, (B_BOX[0] - 3, B_BOX[1] - 3, B_BOX[2] + 3, B_BOX[3] + 3)) > 0) & (ell(X, Z, LAKE) > 1)
    dens = NT.noise(X, Z, 1563, 7)
    hit = M & (rng.random(H.shape) < np.clip(dens * 1.3 - 0.25, 0, 0.9))
    names = bb.names
    for i, j in zip(*np.nonzero(hit)):
        y = H[i, j]
        col = bb.get_region(int(i), y, int(j), int(i), y + 1, int(j))[0, :, 0]
        top = names[col[0]] or ""
        if col[1] not in (0, 1) or not top.split("[")[0].endswith(("snow_block", "grass_block", "podzol", "stone", "gravel", "andesite")):
            continue
        k = 1 + int(dens[i, j] * 3.4)
        bb.set(int(i), y + 1, int(j), f"minecraft:snow[layers={min(k, 4)}]")


# ------------------------------------------------------------------ main building
def main_building(bb, tracker, audit):
    x1, z1, x2, z2 = A
    top = tier(bb, x1, z1, x2, z2, 0, 3, FH, [WHITE, "minecraft:smooth_quartz"], GLASS, QST,
               pilaster=LGRAY, band=CYAN, top_plate=LGRAY, weights=[0.75, 0.25], every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:smooth_quartz_stairs", parapet=LGRAY)
    hx1, hz1, hx2, hz2 = HALL
    sx1, sz1, sx2, sz2 = SAD
    # inner walls: the central block between the wings, the walls either side of the crossing corridor
    for wx in (hx1 - 1, hx2 + 1):
        bb.fill(wx, 1, z1 + 1, wx, top - 1, z2 - 1, PANEL)
    for wz in (hz1 - 1, sz2 + 1):
        bb.fill(hx1, 1, wz, hx2, top - 1, wz, PANEL)
    for k in range(3):
        y = 1 + FH * k
        bb.fill(hx1 - 1, y, 67, hx1 - 1, y + 2, 69, AIR)
        bb.fill(hx2 + 1, y, 67, hx2 + 1, y + 2, 69, AIR)
    # the wings: three floors of rooms off a corridor that lines up with the crossing corridor
    kinds = [("workshop", "storage", "kitchen", "storage"), ("library", "workshop", "living", "library"),
             ("library", "bedroom", "living", "bedroom")]
    for k in range(3):
        y = 1 + FH * k
        for (a1, a2, s) in ((x1 + 1, hx1 - 2, 1), (hx2 + 2, x2 - 1, 2)):
            wing_floor(bb, a1, z1 + 1, a2, z2 - 1, y, FH - 1, PANEL, seed_of("ph", k, s), tracker, kinds[k],
                       corridor="x", cw=3, carpet=(None, "minecraft:cyan_carpet"), wood="birch", audit=audit,
                       lamp=LIGHT)
    # doors out at both corridor ends (west to the Biscuit Room tube, east to the gas works)
    bb.fill(x1, 1, 67, x1, 3, 69, AIR)
    bb.fill(x2, 1, 67, x2, 3, 69, AIR)
    # the crossing corridor through the centre on every floor (a glass-walled bridge on floor 2)
    for k in range(3):
        y = FH * k
        bb.fill(hx1, y, 67, hx2, y, 69, "minecraft:polished_andesite" if k == 0 else "minecraft:smooth_stone")
        bb.fill(hx1, y + 1, 68, hx2, y + 1, 68, "minecraft:cyan_carpet")
        for x in range(hx1 + 2, hx2, 5):
            bb.set(x, y + FH - 1, 68, LIGHT)
    for x in range(hx1 + 1, hx2, 3):                  # windows from the corridor into the two tall rooms
        for wz in (hz1 - 1, sz2 + 1):
            bb.fill(x, 2, wz, x + 1, 3, wz, GLASS)
            bb.fill(x, 8, wz, x + 1, 9, wz, GLASS)
    # floor 2 bridge: plates removed over the two tall rooms, the corridor kept
    bb.fill(hx1, FH, hz1, hx2, FH, hz2, AIR)
    bb.fill(sx1, FH, sz1, sx2, FH, sz2, AIR)
    entrance_hall(bb, tracker, audit)
    sad_chamber(bb)
    top_floor(bb, tracker, audit, top)
    # main doors and canopy (south)
    cx = (hx1 + hx2) // 2
    bb.fill(cx - 2, 1, z2, cx + 2, 4, z2, AIR)
    bb.fill(cx - 3, 5, z2, cx + 3, 5, z2, CYAN)
    bb.fill(cx - 5, 5, z2 + 1, cx + 5, 5, z2 + 5, "minecraft:smooth_quartz_slab[type=bottom]")
    bb.fill(cx - 5, 5, z2 + 5, cx + 5, 5, z2 + 5, "minecraft:light_gray_concrete")
    for x in (cx - 5, cx + 5):
        bb.fill(x, 1, z2 + 5, x, 4, z2 + 5, "minecraft:quartz_pillar[axis=y]")
    for x in (cx - 3, cx + 3):
        bb.set(x, 4, z2 + 3, LIGHT)
    for dx in range(-4, 5):
        bb.fill(cx + dx, 0, z2 + 1, cx + dx, 0, z2 + 9, "minecraft:polished_andesite" if abs(dx) < 3 else "minecraft:smooth_stone")
    # back door (north) to the yard and the reservoir road
    bb.fill(cx - 1, 1, z1, cx + 1, 3, z1, AIR)
    roof(bb, top)


def entrance_hall(bb, tracker, audit):
    hx1, hz1, hx2, hz2 = HALL
    cx = (hx1 + hx2) // 2
    bb.fill(hx1, 0, hz1, hx2, 0, hz2, "minecraft:polished_andesite")
    bb.fill(cx - 1, 0, hz1, cx + 1, 0, hz2, "minecraft:white_concrete")
    bb.fill(cx, 0, hz1, cx, 0, hz2, "minecraft:cyan_concrete")
    for (x, z) in ((hx1 + 6, hz1 + 4), (hx2 - 6, hz1 + 4), (hx1 + 6, hz2 - 4), (hx2 - 6, hz2 - 4)):
        bb.fill(x, 1, z, x, 2 * FH - 1, z, "minecraft:quartz_pillar[axis=y]")
        bb.set(x, 2 * FH - 1, z, "minecraft:chiseled_quartz_block")
    # reception desk and benches
    bb.fill(cx - 4, 1, hz2 - 7, cx + 4, 1, hz2 - 7, "minecraft:white_glazed_terracotta" if False else "minecraft:smooth_quartz")
    bb.fill(cx - 4, 2, hz2 - 7, cx + 4, 2, hz2 - 7, "minecraft:smooth_quartz_slab[type=bottom]")
    bb.set(cx, 1, hz2 - 8, "minecraft:birch_stairs[facing=south]")
    bb.set(cx - 2, 3, hz2 - 7, "minecraft:lectern[facing=south]") if False else bb.set(cx - 2, 3, hz2 - 7, "minecraft:potted_azure_bluet")
    bb.set(cx + 3, 3, hz2 - 7, "minecraft:candle[candles=2,lit=true]")
    for x in (hx1 + 2, hx2 - 2):
        for z in range(hz1 + 6, hz2 - 1, 4):
            bb.set(x, 1, z, st("minecraft:birch_stairs", "east" if x < cx else "west"))
            bb.set(x, 1, z + 1, st("minecraft:birch_stairs", "east" if x < cx else "west"))
    bb.set(hx1 + 1, 1, hz2 - 1, "minecraft:potted_fern")
    bb.set(hx2 - 1, 1, hz2 - 1, "minecraft:potted_fern")
    # a hall of light: lab lights set in the ceiling, two hanging lamps
    for x in range(hx1 + 3, hx2 - 1, 5):
        for z in range(hz1 + 2, hz2, 5):
            bb.set(x, 2 * FH, z, LIGHT)
    for x in (cx - 5, cx + 5):
        bb.fill(x, 2 * FH - 3, (hz1 + hz2) // 2, x, 2 * FH - 1, (hz1 + hz2) // 2, "minecraft:iron_chain[axis=y]")
        bb.set(x, 2 * FH - 4, (hz1 + hz2) // 2, "minecraft:lantern[hanging=true]")
    # the balcony on floor 2 along the north side, reached by the stair, with a door onto the bridge
    bb.fill(hx1 + 1, FH, hz1, hx2, FH, hz1 + 2, "minecraft:smooth_stone")
    bb.fill(hx1 + 6, FH + 1, hz1 + 2, hx2, FH + 1, hz1 + 2, "minecraft:white_concrete")
    bb.fill(hx1 + 6, FH + 2, hz1 + 2, hx2, FH + 2, hz1 + 2, "minecraft:smooth_quartz_slab[type=bottom]")
    bb.fill(cx, FH + 1, hz1 - 1, cx + 1, FH + 2, hz1 - 1, AIR)
    bb.fill(cx, 1, hz1 - 1, cx + 1, 2, hz1 - 1, AIR)
    # spiral stair in the north-west corner from the hall to the top floor
    bb.fill(hx1, 1, hz1, hx1 + 5, 2 * FH, hz1 + 5, AIR)
    P.square_spiral_stair(bb, hx1 + 1, 1, hz1, 5, 2 * FH, QST, core="minecraft:quartz_pillar[axis=y]", headroom=3)
    bb.fill(hx1, 0, hz1, hx1 + 5, 0, hz1 + 5, "minecraft:polished_andesite")


def sad_chamber(bb):
    """The SAD tank: a tall purple glass vat on a steel base, a catwalk ring at floor 2, pipes up to the roof."""
    sx1, sz1, sx2, sz2 = SAD
    cx, cz = (sx1 + sx2) // 2, (sz1 + sz2) // 2
    top = 2 * FH
    bb.fill(sx1, 0, sz1, sx2, 0, sz2, "minecraft:polished_deepslate")
    bb.cylinder(cx, 0, cz, 6, 0, "minecraft:iron_block")
    bb.cylinder(cx, 1, cz, 5, 1, "minecraft:polished_deepslate")
    bb.cylinder(cx, 2, cz, 4, top - 3, "minecraft:purple_stained_glass", hollow=True)
    bb.cylinder(cx, 2, cz, 3, top - 4, "minecraft:amethyst_block")
    bb.cylinder(cx, 2, cz, 2, top - 5, "minecraft:purple_concrete")
    bb.cylinder(cx, top - 2, cz, 4, top - 2, "minecraft:iron_block")
    for y in range(3, top - 3, 3):
        bb.cylinder(cx, y, cz, 4, y, "minecraft:iron_block", hollow=True)
    # catwalk ring at the floor 2 level with a handrail and a way onto the corridor bridge
    bb.ring(cx, FH, cz, 5, 6, FH, "minecraft:iron_block")
    bb.ring(cx, FH + 1, cz, 6, 7, FH + 1, "minecraft:iron_bars")
    bb.fill(cx, FH, cz + 7, cx + 1, FH, sz2, "minecraft:iron_block")
    bb.fill(cx, FH + 1, cz + 6, cx + 1, FH + 2, cz + 7, AIR)
    bb.fill(cx, FH + 1, sz2 + 1, cx + 1, FH + 2, sz2 + 1, AIR)
    bb.fill(cx, 1, sz2 + 1, cx + 1, 2, sz2 + 1, AIR)
    # pipes from the vat to the ceiling and along it to the walls, gauges, control desks
    for (dx, dz) in ((-6, -6), (6, -6), (-6, 5), (6, 5)):
        bb.fill(cx + dx, 1, cz + dz, cx + dx, top - 1, cz + dz, "minecraft:lightning_rod[facing=up]" if False else "minecraft:iron_bars")
        bb.set(cx + dx, top - 1, cz + dz, "minecraft:iron_block")
        bb.set(cx + dx, 4, cz + dz, LIGHT)
    bb.fill(cx, top - 1, cz, cx, top - 1, cz, "minecraft:iron_block")
    bb.fill(sx1 + 1, top - 1, cz, sx2 - 1, top - 1, cz, "minecraft:iron_block")
    bb.fill(cx, top - 1, sz1 + 1, cx, top - 1, sz2 - 1, "minecraft:iron_block")
    for x in (sx1 + 1, sx2 - 1):
        for z in range(sz1 + 2, sz2 - 1, 3):
            bb.set(x, 1, z, "minecraft:polished_deepslate_slab[type=top]" if z % 2 else "minecraft:smoker[facing=%s,lit=false]" % ("east" if x < cx else "west"))
            bb.set(x, 2, z, "minecraft:light_blue_stained_glass_pane" if False else "minecraft:lever[face=floor,facing=north,powered=false]")
    for (x, z) in ((sx1 + 3, sz1 + 1), (sx2 - 3, sz1 + 1)):
        bb.fill(x - 1, 1, z, x + 1, 2, z, "minecraft:barrel[facing=up,open=false]")
    for x in range(sx1 + 2, sx2 - 1, 4):
        for z in (sz1 + 2, sz2 - 2):
            bb.set(x, top, z, LIGHT)


def top_floor(bb, tracker, audit, top):
    """Floor 3 of the centre: Caesar's office over the hall, the control room under the dome over the SAD chamber."""
    hx1, hz1, hx2, hz2 = HALL
    sx1, sz1, sx2, sz2 = SAD
    y = 2 * FH + 1
    cx = (hx1 + hx2) // 2
    # Caesar's office: purple carpet, a big desk before the windows, his chair, gas flasks, a lounge
    bb.fill(hx1, y - 1, hz1, hx2, y - 1, hz2, "minecraft:dark_oak_planks")
    bb.fill(hx1 + 7, y, hz1 + 2, hx2 - 2, y, hz2 - 2, "minecraft:purple_carpet")
    bb.fill(hx1 + 8, y, hz1 + 3, hx2 - 3, y, hz2 - 3, "minecraft:magenta_carpet")
    dz = hz2 - 4
    bb.fill(cx - 3, y, dz, cx + 3, y, dz, "minecraft:dark_oak_planks")
    bb.fill(cx - 3, y + 1, dz, cx + 3, y + 1, dz, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(cx, y, dz + 1, "minecraft:dark_oak_stairs[facing=north]")
    bb.set(cx - 1, y, dz + 1, "minecraft:dark_oak_trapdoor[facing=east,half=bottom,open=true]")
    bb.set(cx + 1, y, dz + 1, "minecraft:dark_oak_trapdoor[facing=west,half=bottom,open=true]")
    for (x, item) in ((cx - 3, "minecraft:brewing_stand"), (cx - 1, "minecraft:candle[candles=3,lit=true]"),
                      (cx + 2, "minecraft:potted_crimson_fungus")):
        bb.set(x, y + 2, dz, item)
    for x in range(hx1 + 8, hx2 - 2, 3):                         # flasks of gas on shelves along the north wall
        bb.set(x, y, hz1, "minecraft:bookshelf")
        bb.set(x + 1, y, hz1, "minecraft:purple_stained_glass")
        bb.set(x + 1, y + 1, hz1, "minecraft:brewing_stand")
    for (x, z) in ((cx - 6, hz1 + 6), (cx - 4, hz1 + 6)):
        bb.set(x, y, z, "minecraft:purple_wool")
    bb.set(cx - 5, y, hz1 + 6, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(cx - 5, y, hz1 + 7, "minecraft:purple_wool")
    furnish(bb, [(hx2 - 7, hz1 + 1, hx2 - 1, hz1 + 8)], y, FH - 1, ["library"], seed_of("caesar"), tracker, audit=audit)
    for x in range(hx1 + 8, hx2 - 1, 6):
        bb.set(x, top - 1, (hz1 + hz2) // 2, "minecraft:pearlescent_froglight[axis=y]")
    bb.fill(cx, y, hz1 - 1, cx + 1, y + 1, hz1 - 1, AIR)
    # the control room: a ring of consoles round the dome's light well, a wall of monitors
    bb.fill(sx1, y - 1, sz1, sx2, y - 1, sz2, "minecraft:polished_deepslate")
    ccx, ccz = (sx1 + sx2) // 2, (sz1 + sz2) // 2
    bb.ring(ccx, y, ccz, 4, 5, y, "minecraft:polished_deepslate_slab[type=top]")
    bb.ring(ccx, y + 1, ccz, 4, 5, y + 1, "minecraft:daylight_detector[inverted=false,power=0]")
    bb.cylinder(ccx, y - 1, ccz, 2, y - 1, "minecraft:glass")
    for x in range(sx1 + 1, sx2):
        bb.set(x, y, sz1, "minecraft:polished_deepslate")
        bb.set(x, y + 1, sz1, "minecraft:black_stained_glass" if x % 3 else "minecraft:verdant_froglight[axis=y]")
        bb.set(x, y + 2, sz1, "minecraft:black_stained_glass" if (x + 1) % 3 else "minecraft:pearlescent_froglight[axis=y]")
        bb.set(x, y, sz1 + 1, "minecraft:polished_deepslate_slab[type=top]" if x % 4 else "minecraft:crafter[crafting=false,orientation=up_north,triggered=false]" if False else "minecraft:polished_deepslate_slab[type=top]")
    for x in range(sx1 + 3, sx2 - 1, 4):
        bb.set(x, y, sz1 + 2, "minecraft:birch_stairs[facing=north]")
        bb.set(x, y + 1, sz1 + 1, "minecraft:lever[face=floor,facing=south,powered=false]")
    furnish(bb, [(sx1 + 1, sz2 - 5, sx1 + 6, sz2 - 1), (sx2 - 6, sz2 - 5, sx2 - 1, sz2 - 1)], y, FH - 1,
            ["workshop", "storage"], seed_of("ctrl"), tracker, audit=audit)
    bb.fill(ccx, y, sz2 + 1, ccx + 1, y + 1, sz2 + 1, AIR)


def roof(bb, top):
    sx1, sz1, sx2, sz2 = SAD
    ccx, ccz = (sx1 + sx2) // 2, (sz1 + sz2) // 2
    # the dome over the control room (white with glass ribs), open into the room below
    bb.cylinder(ccx, top, ccz, 9, top, AIR)
    bb.cylinder(ccx, top, ccz, 10, top, LGRAY, hollow=True)
    bb.dome(ccx, top, ccz, 10, WHITE)
    for k in range(8):
        a = k * math.pi / 4
        for r in range(2, 11):
            yy = top + int(round(math.sqrt(max(0, 100 - r * r))))
            bb.set(round(ccx + r * math.cos(a)), yy, round(ccz + r * math.sin(a)), GLASS)
    bb.set(ccx, top + 11, ccz, LGRAY)
    bb.fill(ccx, top + 12, ccz, ccx, top + 17, ccz, "minecraft:iron_bars")
    bb.set(ccx, top + 18, ccz, "minecraft:end_rod[facing=up]")
    # antennae, vents and the roof lights over the wings
    x1, z1, x2, z2 = A
    for (x, z, h) in ((x1 + 5, z1 + 5, 9), (x2 - 5, z1 + 5, 12), (x2 - 9, z2 - 6, 7)):
        bb.fill(x, top + 1, z, x, top + h, z, "minecraft:iron_bars")
        bb.set(x, top + h + 1, z, "minecraft:lightning_rod[facing=up]")
        bb.fill(x - 1, top + h - 2, z, x + 1, top + h - 2, z, "minecraft:iron_bars")
    for (x, z) in ((x1 + 10, z2 - 8), (x1 + 13, z2 - 8), (x2 - 14, z1 + 7)):
        bb.fill(x, top + 1, z, x + 1, top + 2, z + 1, "minecraft:light_gray_concrete")
        bb.fill(x, top + 3, z, x + 1, top + 3, z + 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    for (x, z) in ((x1 + 4, z2 - 4), (x2 - 4, z2 - 4), (x1 + 4, z1 + 12)):
        bb.cylinder(x, top + 1, z, 2, top + 4, WHITE)
        bb.cylinder(x, top + 5, z, 1, top + 5, LGRAY)


# ------------------------------------------------------------------ Biscuit Room building + glass tube
def biscuit_building(bb, tracker, audit):
    x1, z1, x2, z2 = B_BOX
    top = tier(bb, x1, z1, x2, z2, 0, 2, FH, [WHITE, "minecraft:smooth_quartz"], "minecraft:pink_stained_glass", QST,
               pilaster="minecraft:pink_concrete", band="minecraft:magenta_concrete", top_plate=LGRAY, weights=[0.8, 0.2],
               every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:smooth_quartz_stairs", parapet="minecraft:pink_terracotta")
    for x in range(x1 - 1, x2 + 2, 2):                          # candy-stripe crest on the parapet
        set_if_air(bb, x, top + 2, z1 - 1, "minecraft:white_concrete")
        set_if_air(bb, x, top + 2, z2 + 1, "minecraft:white_concrete")
    # the big glass skylight over the playroom
    bb.fill(x1 + 6, top, z1 + 6, x2 - 6, top, z2 - 6, "minecraft:glass")
    bb.fill(x1 + 6, FH, z1 + 6, x2 - 6, FH, z2 - 6, AIR)
    # ground floor: the Biscuit Room playroom (rows of beds, a ball pit, a slide, candy pillars, the sweets table)
    y = 1
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:pink_terracotta")
    for x in range(x1 + 2, x2 - 1):
        for z in range(z1 + 2, z2 - 1):
            if (x // 2 + z // 2) % 2 == 0 and abs(x - (x1 + x2) / 2) < 7 and abs(z - (z1 + z2) / 2) < 7:
                bb.set(x, 0, z, "minecraft:white_terracotta")
    cols = ["pink", "light_blue", "yellow", "lime", "magenta", "orange", "cyan", "red"]
    for i, x in enumerate(range(x1 + 2, x2 - 1, 3)):
        c = cols[i % len(cols)]
        bb.set(x, y, z1 + 1, f"minecraft:{c}_bed[facing=south,part=head,occupied=false]")
        bb.set(x, y, z1 + 2, f"minecraft:{c}_bed[facing=south,part=foot,occupied=false]")
        bb.set(x + 1, y, z1 + 1, "minecraft:birch_slab[type=bottom]") if x + 1 < x2 - 1 else None
        if x + 1 < x2 - 1:
            bb.set(x + 1, y + 1, z1 + 1, ("minecraft:candle[candles=1,lit=true]", "minecraft:potted_dandelion", "minecraft:cake")[i % 3])
    for (x, z) in ((x1 + 6, z1 + 6), (x2 - 6, z1 + 6), (x1 + 6, z2 - 6), (x2 - 6, z2 - 6)):
        bb.fill(x, y, z, x, FH - 1, z, "onepiece:candy_cane_block")
    pz = z2 - 5                                                    # ball pit
    bb.fill(x1 + 2, y, pz - 2, x1 + 8, y, z2 - 1, "minecraft:white_concrete")
    bb.fill(x1 + 3, y, pz - 1, x1 + 7, y, z2 - 2, AIR)
    for x in range(x1 + 3, x1 + 8):
        for z in range(pz - 1, z2 - 1):
            bb.set(x, y - 1, z, f"minecraft:{cols[(x * 3 + z * 5) % len(cols)]}_wool")
            bb.set(x, y, z, f"minecraft:{cols[(x * 7 + z) % len(cols)]}_carpet")
    sx = x2 - 6                                                   # slide
    for k in range(4):
        bb.set(sx, y + k, z2 - 2 - k, "minecraft:ladder[facing=south]") if False else None
    bb.fill(sx - 1, y, z2 - 6, sx + 1, y + 2, z2 - 6, "minecraft:yellow_concrete")
    bb.fill(sx - 1, y + 3, z2 - 6, sx + 1, y + 3, z2 - 6, "minecraft:yellow_concrete")
    bb.set(sx, y, z2 - 7, "minecraft:ladder[facing=north]")
    bb.set(sx, y + 1, z2 - 7, "minecraft:ladder[facing=north]")
    bb.set(sx, y + 2, z2 - 7, "minecraft:ladder[facing=north]")
    for k in range(3):
        bb.set(sx, y + 2 - k, z2 - 5 + k, "minecraft:smooth_quartz_stairs[facing=north,half=bottom]")
    tz = (z1 + z2) // 2                                          # the sweets table
    tx1, tx2 = x1 + 10, x2 - 10
    bb.fill(tx1, y, tz, tx2, y, tz + 1, "minecraft:birch_fence")
    bb.fill(tx1, y + 1, tz, tx2, y + 1, tz + 1, "minecraft:white_carpet")
    for x in range(tx1, tx2 + 1, 2):
        bb.set(x, y + 1, tz, "minecraft:cake")
        bb.set(x, y, tz - 1, "minecraft:birch_stairs[facing=south]")
        bb.set(x, y, tz + 2, "minecraft:birch_stairs[facing=north]")
    for x in range(x1 + 4, x2 - 3, 6):
        for z in (z1 + 9, z2 - 9):
            bb.set(x, FH - 1, z, "minecraft:pearlescent_froglight[axis=y]")
    # upstairs: the dining room and the classroom, a ladder up through the corner
    furnish(bb, [(x1 + 1, z1 + 1, x2 - 1, z1 + 5), (x1 + 1, z2 - 5, x2 - 1, z2 - 1)], FH + 1, FH - 1,
            ["kitchen", "library"], seed_of("biscuit2"), tracker, audit=audit)
    bb.fill(x1 + 1, FH + 1, z1 + 6, x2 - 1, FH + 1, z1 + 6, "minecraft:pink_stained_glass_pane" if False else "minecraft:white_concrete")
    bb.fill(x1 + 1, FH + 1, z2 - 6, x2 - 1, FH + 1, z2 - 6, "minecraft:white_concrete")
    bb.fill(x1 + 1, FH + 1, z1 + 6, x1 + 5, FH + 1, z2 - 6, "minecraft:white_concrete")
    bb.fill(x2 - 5, FH + 1, z1 + 6, x2 - 1, FH + 1, z2 - 6, "minecraft:white_concrete")
    bb.fill(x1 + 6, FH, z1 + 6, x1 + 6, FH, z2 - 6, "minecraft:smooth_stone")
    bb.fill(x1 + 1, FH, z1 + 6, x1 + 5, FH, z2 - 6, "minecraft:smooth_stone")
    bb.fill(x2 - 5, FH, z1 + 6, x2 - 1, FH, z2 - 6, "minecraft:smooth_stone")
    bb.fill(x1 + 1, 1, z1 + 4, x1 + 1, FH + 1, z1 + 4, "minecraft:ladder[facing=east]")
    bb.set(x1 + 1, FH, z1 + 4, "minecraft:ladder[facing=east]")
    # doors: south to the snow, east to the glass tube
    bb.fill((x1 + x2) // 2, 1, z2, (x1 + x2) // 2 + 1, 3, z2, AIR)
    bb.fill(x2, 1, 67, x2, 3, 69, AIR)
    # the glass tube to the main building
    bb.fill(x2 + 1, 0, 66, A[0] - 1, 0, 70, "minecraft:polished_andesite")
    bb.fill(x2 + 1, 1, 66, A[0] - 1, 4, 66, "minecraft:glass")
    bb.fill(x2 + 1, 1, 70, A[0] - 1, 4, 70, "minecraft:glass")
    bb.fill(x2 + 1, 5, 66, A[0] - 1, 5, 70, "minecraft:glass")
    bb.fill(x2 + 1, 1, 67, A[0] - 1, 4, 69, AIR)
    bb.fill(x2 + 1, 1, 68, A[0] - 1, 1, 68, "minecraft:pink_carpet")
    for x in (x2 + 1, A[0] - 1):
        bb.fill(x, 0, 66, x, 5, 66, LGRAY)
        bb.fill(x, 0, 70, x, 5, 70, LGRAY)
        bb.fill(x, 5, 66, x, 5, 70, LGRAY)


# ------------------------------------------------------------------ gas works, tanks, reservoir
def gas_works(bb, tracker, audit):
    x1, z1, x2, z2 = C_BOX
    fh = 7
    top = tier(bb, x1, z1, x2, z2, 0, 2, fh, [LGRAY, "minecraft:polished_andesite"], "minecraft:gray_stained_glass",
               None, pilaster="minecraft:iron_block", band="minecraft:purple_concrete", top_plate="minecraft:gray_concrete",
               weights=[0.7, 0.3], every=4, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:polished_andesite_stairs", parapet="minecraft:gray_concrete")
    # a workshop hall below (pipes, valves, a vat), storage above
    furnish(bb, [(x1 + 1, z1 + 1, x2 - 1, z2 - 1)], 1, fh - 1, ["workshop"], seed_of("gasworks"), tracker, audit=audit)
    furnish(bb, [(x1 + 1, z1 + 1, x2 - 1, z2 - 1)], fh + 1, fh - 1, ["storage"], seed_of("gasworks2"), tracker, audit=audit)
    bb.fill(x1 + 1, 1, z2 - 2, x1 + 1, fh + 1, z2 - 2, "minecraft:ladder[facing=east]")
    bb.fill(x1, 1, 67, x1, 3, 69, AIR)
    bb.fill(x2, 1, 67, x2, 3, 69, AIR)
    bb.fill((x1 + x2) // 2, 1, z2, (x1 + x2) // 2 + 1, 3, z2, AIR)
    # covered pipe bridge to the main building
    bb.fill(A[2] + 1, 0, 66, x1 - 1, 0, 70, "minecraft:polished_andesite")
    bb.fill(A[2] + 1, 1, 66, x1 - 1, 4, 70, LGRAY)
    bb.fill(A[2] + 1, 2, 66, x1 - 1, 3, 66, "minecraft:gray_stained_glass")
    bb.fill(A[2] + 1, 2, 70, x1 - 1, 3, 70, "minecraft:gray_stained_glass")
    bb.fill(A[2] + 1, 1, 67, x1 - 1, 3, 69, AIR)
    bb.fill(A[2] + 1, 5, 67, x1 - 1, 5, 67, "minecraft:iron_block")
    bb.fill(A[2] + 1, 5, 69, x1 - 1, 5, 69, "minecraft:purple_concrete")
    # three gas tanks south of the works, piped in
    for k, tx in enumerate((x1 + 3, x1 + 13, x2 - 1)):
        tz = z2 + 12
        bb.cylinder(tx, 1, tz, 4, 13, WHITE)
        bb.dome(tx, 14, tz, 4, WHITE, hollow=False)
        for y in (4, 10):
            bb.ring(tx, y, tz, 4, 5, y, "minecraft:purple_concrete")
        bb.cylinder(tx, 0, tz, 5, 0, "minecraft:polished_andesite")
        for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
            bb.fill(tx + dx, 1, tz + dz, tx + dx, 3, tz + dz, "minecraft:iron_bars")
        bb.fill(tx, 9, z2 + 1, tx, 9, tz - 4, "minecraft:iron_block")
        bb.fill(tx, 10, z2, tx, 10, z2, "minecraft:iron_block")
        bb.fill(tx + 4, 15 + k, tz, tx + 4, 15 + k, tz, "minecraft:iron_bars")
        bb.set(tx, 18, tz, "minecraft:lightning_rod[facing=up]")
        bb.fill(tx - 1, 1, tz + 4, tx + 1, 13, tz + 4, "minecraft:ladder[facing=south]") if False else \
            bb.fill(tx, 1, tz + 5, tx, 13, tz + 5, "minecraft:ladder[facing=south]")
    # the big spherical gas reservoir north of the yard, on legs over a walled pad
    sx, sz, r = SPHERE
    gy = max(hy(sx + dx, sz + dz) for dx in (-r, 0, r) for dz in (-r, 0, r))
    bb.cylinder(sx, gy - 3, sz, r + 3, gy, "minecraft:polished_andesite")
    bb.ring(sx, gy + 1, sz, r + 2, r + 3, gy + 1, "minecraft:andesite_wall")
    cy = gy + r + 6
    for k in range(6):
        a = k * math.pi / 3
        lx, lz = round(sx + (r - 1) * math.cos(a)), round(sz + (r - 1) * math.sin(a))
        bb.fill(lx, gy + 1, lz, lx, cy, lz, "minecraft:iron_block")
    bb.fill_where(sx - r - 1, cy - r - 1, sz - r - 1, sx + r + 1, cy + r + 1, sz + r + 1,
                  lambda X, yy, Z: (X - sx) ** 2 + (yy - cy) ** 2 + (Z - sz) ** 2 <= r * r + r, WHITE)
    bb.fill_where(sx - r - 1, cy, sz - r - 1, sx + r + 1, cy, sz + r + 1,
                  lambda X, yy, Z: (X - sx) ** 2 + (Z - sz) ** 2 <= r * r + r, "minecraft:purple_concrete")
    bb.fill_where(sx - r - 1, cy, sz - r - 1, sx + r + 1, cy, sz + r + 1,
                  lambda X, yy, Z: ((X - sx) ** 2 + (Z - sz) ** 2 <= (r - 1) ** 2), WHITE)
    # a caged ladder up one leg and a walkway ring round the equator
    bb.ring(sx, cy, sz, r + 1, r + 2, cy, "minecraft:iron_block")
    bb.ring(sx, cy + 1, sz, r + 2, r + 3, cy + 1, "minecraft:iron_bars")
    bb.fill(sx + r + 2, gy + 1, sz, sx + r + 2, cy, sz, "minecraft:ladder[facing=east]")
    bb.fill(sx + r + 1, gy + 1, sz, sx + r + 1, cy - 1, sz, "minecraft:iron_block")
    # the pipe to the works
    py = gy + 4
    bb.fill(sx, py, sz + r + 1, sx, py, z1 - 1, "minecraft:iron_block")
    for z in range(sz + r + 3, z1 - 1, 5):
        bb.fill(sx, max(1, hy(sx, z) + 1), z, sx, py - 1, z, "minecraft:iron_bars")
    return (sx - r - 4, sz - r - 4, sx + r + 4, sz + r + 4)


# ------------------------------------------------------------------ the frozen half
def disc(bb, x, y, z, r, block, y2=None):
    """A filled disc (or short column to y2) of float radius r."""
    R = int(math.ceil(r))
    bb.fill_where(x - R, y, z - R, x + R, y if y2 is None else y2, z + R,
                  lambda X, yy, Z: (X - x) ** 2 + (Z - z) ** 2 <= r * r + 0.5, block)


def ice_spike(bb, x, y, z, h, r):
    for yy in range(h):
        rr = max(0.6, r * (1 - yy / h) ** 1.3)
        disc(bb, x, y + yy, z, rr, "minecraft:packed_ice" if yy < h - 3 else "minecraft:ice")
    disc(bb, x, y - 2, z, r + 0.5, "minecraft:packed_ice", y - 1)


def frozen_half(bb, rng, taken):
    k, t = 0, 0
    for _ in range(3000):
        x, z = int(rng.integers(4, NX - 4)), int(rng.integers(4, NZ - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not cold(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 7 or ell(X, Z, COVE)[0, 0] < 1.3 or ell(X, Z, LAKE)[0, 0] < 1.4:
            continue
        if flatness(X, Z)[0, 0] < 0.5 or border(X, Z)[0, 0] > -8:
            continue
        if any(a[0] - 2 <= x <= a[2] + 2 and a[1] - 2 <= z <= a[3] + 2 for a in taken):
            continue
        y = hy(x, z)
        if rng.random() < 0.38 and k < 20:
            h = int(rng.integers(6, 20))
            ice_spike(bb, x, y + 1, z, h, rng.uniform(1.2, 2.6))
            taken.append((x - 3, z - 3, x + 3, z + 3))
            k += 1
        elif t < 46:
            P.tree(bb, x, y + 1, z, int(rng.integers(7, 14)), "spruce", rng)
            taken.append((x - 2, z - 2, x + 2, z + 2))
            t += 1
        if k >= 20 and t >= 46:
            break
    for _ in range(14):
        x, z = int(rng.integers(8, MIDX - 10)), int(rng.integers(8, NZ - 8))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or ell(X, Z, COVE)[0, 0] < 1.2 or flatness(X, Z)[0, 0] < 0.5:
            continue
        NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.4, 2.8), rng,
                   blocks=("minecraft:stone", "minecraft:packed_ice", "minecraft:snow_block"))
    # two wrecked G-5 tanks half buried in the snow by the lake
    for (x, z) in ((LAKE[0] + 20, LAKE[1] + 4), (LAKE[0] - 6, LAKE[1] + 16)):
        y = hy(x, z)
        bb.fill(x, y, z, x + 6, y + 2, z + 3, "minecraft:gray_concrete")
        bb.fill(x + 1, y + 3, z + 1, x + 4, y + 3, z + 2, "minecraft:gray_concrete")
        bb.fill(x + 5, y + 3, z + 1, x + 10, y + 3, z + 1, "minecraft:iron_block")
        for xx in range(x, x + 7, 2):
            bb.set(xx, y, z - 1, "minecraft:polished_blackstone_slab[type=bottom]")
            bb.set(xx, y, z + 4, "minecraft:polished_blackstone_slab[type=bottom]")
        bb.fill(x + 2, y + 4, z, x + 4, y + 4, z + 3, "minecraft:snow[layers=2]")
        taken.append((x - 2, z - 2, x + 11, z + 6))


def g5_cove(bb, rng):
    """The G-5 warship frozen into the cove, a gangway of planks over the ice to a snowy landing, a camp fire."""
    sx, sz = SHIP
    fp = stamp_ship(bb, "marine_warship", sx, sz, water_y=0, rot=0)
    sea_ice(bb)
    # landing: a little plank jetty from the shore to the ship's bow, sea-ice around it
    shore_x = next(x for x in range(fp[2], NX) if land(np.array([[x]]), np.array([[sz]]))[0, 0]) if True else fp[2] + 4
    for x in range(fp[2] - 2, shore_x + 1):
        bb.fill(x, 0, sz - 1, x, 0, sz + 1, "minecraft:spruce_planks")
        if (x - fp[2]) % 4 == 0:
            bb.fill(x, -6, sz - 2, x, 1, sz - 2, "minecraft:spruce_log[axis=y]")
            bb.fill(x, -6, sz + 2, x, 1, sz + 2, "minecraft:spruce_log[axis=y]")
    lx, lz = shore_x + 4, sz
    y = hy(lx, lz)
    bb.set(lx, y + 1, lz, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((-2, 0, "east"), (2, 0, "west"), (0, 2, "north")):
        bb.set(lx + dx, y + 1, lz + dz, f"minecraft:spruce_stairs[facing={f}]")
    for (dx, dz) in ((-3, -3), (3, -3)):
        bb.set(lx + dx, y + 1, lz + dz, "minecraft:barrel[facing=up,open=false]")
    return fp


# ------------------------------------------------------------------ the burning half
def lava_pool(bb, x, z, rx, rz, rng):
    """A lava pool sunk in a hollow, rimmed with magma and basalt so it stays put."""
    X = np.arange(x - rx - 3, x + rx + 4)[:, None]
    Z = np.arange(z - rz - 3, z + rz + 4)[None, :]
    H = height(X, Z)
    y = int(H.min())
    t = lambda XX, ZZ: ((XX - x) / rx) ** 2 + ((ZZ - z) / rz) ** 2 * (0.85 + 0.3 * NT.noise(XX, ZZ, x * 7 + z, 3))
    bb.fill_where(x - rx - 3, y - 3, z - rz - 3, x + rx + 3, y + 3, z + rz + 3,
                  lambda XX, yy, ZZ: (t(XX, ZZ) < 1) & (yy > y), AIR)
    bb.fill_where(x - rx - 3, y - 3, z - rz - 3, x + rx + 3, y, z + rz + 3,
                  lambda XX, yy, ZZ: (t(XX, ZZ) < 1.7) & (t(XX, ZZ) >= 1) & (yy >= y - 2), "minecraft:magma_block")
    bb.fill_where(x - rx - 3, y - 3, z - rz - 3, x + rx + 3, y - 3, z + rz + 3,
                  lambda XX, yy, ZZ: t(XX, ZZ) < 1.7, "minecraft:basalt[axis=y]")
    bb.fill_where(x - rx - 3, y - 2, z - rz - 3, x + rx + 3, y, z + rz + 3,
                  lambda XX, yy, ZZ: (t(XX, ZZ) < 1) & ((yy < y) | (t(XX, ZZ) < 0.92)), "minecraft:lava")
    bb.fill_where(x - rx - 3, y - 2, z - rz - 3, x + rx + 3, y, z + rz + 3,
                  lambda XX, yy, ZZ: (t(XX, ZZ) < 1) & (yy == y) & (t(XX, ZZ) >= 0.92), "minecraft:magma_block")
    # walls up to the surrounding ground so nothing leaks over the rim
    bb.fill_where(x - rx - 3, y + 1, z - rz - 3, x + rx + 3, y + 8, z + rz + 3,
                  lambda XX, yy, ZZ: (t(XX, ZZ) < 1.7) & (t(XX, ZZ) >= 1) & (yy <= np.broadcast_to(height(XX, ZZ), np.broadcast_shapes(XX.shape, ZZ.shape))),
                  "minecraft:blackstone", only_empty=True)


def vent(bb, x, z, rng):
    y = hy(x, z)
    disc(bb, x, y, z, 2.2, "minecraft:basalt[axis=y]")
    disc(bb, x, y + 1, z, 1.2, "minecraft:basalt[axis=y]")
    bb.set(x, y + 1, z, "minecraft:magma_block")
    bb.set(x, y + 2, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


def dead_tree(bb, x, z, rng):
    y = hy(x, z)
    h = int(rng.integers(5, 10))
    log = "minecraft:stripped_dark_oak_log" if rng.random() < 0.5 else "minecraft:dark_oak_log"
    bb.fill(x, y + 1, z, x, y + h, z, log + "[axis=y]")
    for _ in range(int(rng.integers(1, 4))):
        a = rng.uniform(0, 6.283)
        by = y + int(rng.integers(h // 2, h))
        for s in range(1, int(rng.integers(2, 4))):
            bx, bz = x + round(math.cos(a) * s), z + round(math.sin(a) * s)
            bb.set(bx, by + s // 2, bz, log + ("[axis=x]" if abs(math.cos(a)) > 0.7 else "[axis=z]" if abs(math.sin(a)) > 0.7 else "[axis=y]"))


def dragon_bones(bb):
    """The bones of the dragon Law cut down: a spine curving over the ash, ribs, a horned skull, claws."""
    x0, z0 = DRAGON
    pts = []
    for i in range(46):
        x = x0 + i
        z = z0 + round(4 * math.sin(i * 0.12))
        pts.append((x, z))
    for i, (x, z) in enumerate(pts):
        g = hy(x, z)
        yb = g + 1 + round(3 * math.sin(min(i, 40) / 40 * math.pi)) + (1 if 12 <= i <= 34 else 0)
        bb.set(x, yb, z, "minecraft:bone_block[axis=x]")
        if i % 3 == 0 and i > 2:
            bb.set(x, yb + 1, z, "minecraft:bone_block[axis=y]")
        if 12 <= i <= 34 and i % 3 == 0:                        # ribs arching down to the ground
            for side in (-1, 1):
                for k in range(1, 6):
                    rz = z + side * (k if k < 4 else 4)
                    ry = yb - (0 if k < 3 else k - 2)
                    if ry > g:
                        bb.set(x, ry, rz, "minecraft:bone_block[axis=z]" if k < 3 else "minecraft:bone_block[axis=y]")
    # the skull at the head end
    hx, hz = pts[-1]
    g = hy(hx, hz)
    bb.fill(hx + 1, g + 1, hz - 2, hx + 5, g + 3, hz + 2, "minecraft:bone_block[axis=x]")
    bb.fill(hx + 6, g + 1, hz - 1, hx + 9, g + 2, hz + 1, "minecraft:bone_block[axis=x]")
    bb.fill(hx + 2, g + 2, hz - 1, hx + 4, g + 2, hz + 1, AIR)
    for dz in (-2, 2):
        bb.set(hx + 3, g + 3, hz + dz, AIR)
        bb.set(hx + 2, g + 2, hz + dz, "minecraft:black_concrete")
        bb.fill(hx + 1, g + 4, hz + dz, hx, g + 6, hz + dz, "minecraft:bone_block[axis=y]")
        bb.set(hx - 1, g + 7, hz + dz, "minecraft:bone_block[axis=y]")
    for x in range(hx + 6, hx + 10):
        if x % 2 == 0:
            bb.set(x, g, hz - 2, "minecraft:bone_block[axis=y]") if False else bb.set(x, g + 1, hz - 2, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
    for i in (14, 30):                                          # claws
        x, z = pts[i]
        g = hy(x, z)
        for side in (-1, 1):
            bb.fill(x, g + 1, z + side * 6, x + 2, g + 1, z + side * 6, "minecraft:bone_block[axis=x]")
            bb.set(x + 3, g + 1, z + side * 6, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
    return (x0 - 2, z0 - 10, hx + 11, z0 + 10)


def old_lab_ruin(bb, rng, tracker, audit):
    """The old Government lab, burnt out in the explosion: broken white walls blackened by fire, a fallen floor."""
    x1, z1, x2, z2 = RUIN
    g = max(0, int(height(np.arange(x1, x2 + 1)[:, None], np.arange(z1, z2 + 1)[None, :]).max()))
    bb.fill(x1, g, z1, x2, g, z2, "minecraft:polished_andesite")
    bb.fill(x1 - 1, g - 3, z1 - 1, x2 + 1, g - 1, z2 + 1, "minecraft:blackstone")
    hgt = lambda X, Z: np.clip((NT.noise(X, Z, 1571, 4) * 13 - 1).astype(int), 0, 12)
    burnt = ["minecraft:white_concrete", "minecraft:light_gray_concrete", "minecraft:gray_concrete",
             "minecraft:black_concrete", "onepiece:scorched_stone"]

    def wall(X, yy, Z):
        edge = (X == x1) | (X == x2) | (Z == z1) | (Z == z2) | (X == (x1 + x2) // 2)
        return edge & (yy > g) & (yy <= g + hgt(X, Z))
    for k, blk in enumerate(burnt):
        bb.fill_where(x1, g + 1, z1, x2, g + 12, z2,
                      lambda X, yy, Z, k=k: wall(X, yy, Z) & ((NT.noise(X * 2 + yy, Z * 2, 1572, 3) * 4.99 + (yy - g) / 6).astype(int) % 5 == k), blk)
    for x in range(x1 + 2, x2 - 1, 3):                         # empty window holes
        for z in (z1, z2):
            bb.fill(x, g + 3, z, x, g + 4, z, AIR)
    # half of the upper floor still hangs, the rest lies as rubble
    bb.fill(x1 + 1, g + 6, z1 + 1, (x1 + x2) // 2 - 1, g + 6, z1 + 8, "minecraft:smooth_stone_slab[type=top]")
    for _ in range(40):
        x, z = int(rng.integers(x1 + 1, x2)), int(rng.integers(z1 + 1, z2))
        bb.set(x, g + 1, z, ("minecraft:blackstone", "minecraft:gravel", "onepiece:scorched_stone",
                              "minecraft:smooth_stone_slab[type=bottom]", "minecraft:iron_bars", "minecraft:coal_block")[int(rng.integers(0, 6))])
    furnish(bb, [((x1 + x2) // 2 + 1, z1 + 1, x2 - 1, z1 + 7)], g + 1, 4, ["library"], seed_of("oldlab"), tracker, audit=audit)
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2), g


def burning_half(bb, rng, taken):
    pools = 0
    for _ in range(600):
        x, z = int(rng.integers(12, NX - 12)), int(rng.integers(12, NZ - 12))
        X, Z = np.array([[x]]), np.array([[z]])
        if cold(X, Z)[0, 0] or border(X, Z)[0, 0] < 8 or SHORE(X, Z)[0, 0] < 10 or flatness(X, Z)[0, 0] < 0.3:
            continue
        rx, rz = int(rng.integers(3, 7)), int(rng.integers(3, 6))
        if any(a[0] - rx - 3 <= x <= a[2] + rx + 3 and a[1] - rz - 3 <= z <= a[3] + rz + 3 for a in taken[1:]) or rect_d(X, Z, YARD)[0, 0] < rx + 2:
            continue
        lava_pool(bb, x, z, rx, rz, rng)
        taken.append((x - rx - 3, z - rz - 3, x + rx + 3, z + rz + 3))
        pools += 1
        if pools >= 6:
            break
    n = 0
    for _ in range(3000):
        x, z = int(rng.integers(6, NX - 6)), int(rng.integers(6, NZ - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if cold(X, Z)[0, 0] or border(X, Z)[0, 0] < 4 or SHORE(X, Z)[0, 0] < 6 or flatness(X, Z)[0, 0] < 0.5:
            continue
        if any(a[0] - 1 <= x <= a[2] + 1 and a[1] - 1 <= z <= a[3] + 1 for a in taken):
            continue
        if n % 3 == 0:
            vent(bb, x, z, rng)
        else:
            dead_tree(bb, x, z, rng)
        taken.append((x - 2, z - 2, x + 2, z + 2))
        n += 1
        if n >= 42:
            break
    for _ in range(14):
        x, z = int(rng.integers(MIDX + 10, NX - 8)), int(rng.integers(8, NZ - 8))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or flatness(X, Z)[0, 0] < 0.5 or cold(X, Z)[0, 0]:
            continue
        if any(a[0] - 2 <= x <= a[2] + 2 and a[1] - 2 <= z <= a[3] + 2 for a in taken):
            continue
        NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.4, 3.0), rng,
                   blocks=("minecraft:blackstone", "minecraft:basalt[axis=y]", "onepiece:scorched_stone"))
    print("lava pools:", pools, "vents/trees:", n)


def steam_line(bb, rng):
    """Where fire meets ice the ground steams: wet mud, puddles, smoke along the line (outside the yard)."""
    for z in range(4, NZ - 4, 2):
        Z = np.array([[z]])
        xs = np.arange(MIDX - 30, MIDX + 30)[:, None]
        b = border(xs, Z)[:, 0]
        x = int(xs[np.argmin(np.abs(b)), 0])
        X = np.array([[x]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or rect_d(X, Z, YARD)[0, 0] < 3:
            continue
        y = hy(x, z)
        for dx in (-1, 0, 1):
            if rng.random() < 0.7:
                bb.set(x + dx, y, z, "minecraft:mud" if rng.random() < 0.7 else "minecraft:packed_mud")
        if rng.random() < 0.08:
            bb.set(x, y + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
            bb.set(x, y, z, "minecraft:magma_block")


# ------------------------------------------------------------------ assembly
def yard_details(bb, rng):
    """Lamp masts round the yard, a road to the cove, fences and crates."""
    for (x, z) in ((A[0] - 6, A[3] + 6), (A[2] + 6, A[3] + 6), (A[0] - 6, A[1] - 6), (A[2] + 6, A[1] - 6),
                   (B_BOX[0] - 4, B_BOX[3] + 6), (C_BOX[2] + 4, C_BOX[3] + 4)):
        y = max(0, hy(x, z))
        bb.fill(x, y + 1, z, x, y + 7, z, "minecraft:iron_bars")
        bb.set(x, y + 1, z, "minecraft:polished_andesite")
        bb.set(x, y + 8, z, LIGHT)
        bb.set(x, y + 9, z, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    # the road from the Biscuit Room down to the cove landing
    for z in range(B_BOX[3] + 1, 118):
        for x in range(36, 41):
            X, Z = np.array([[x]]), np.array([[z]])
            if not land(X, Z)[0, 0]:
                continue
            y = hy(x, z)
            if NT.noise(x, z, 1581, 3) > 0.25:
                bb.set(x, y, z, "minecraft:gravel" if NT.noise(x, z, 1582, 2) > 0.5 else "minecraft:packed_ice")
            bb.set(x, y + 1, z, AIR)
    for (x, z) in ((A[2] + 4, A[3] + 3), (A[2] + 5, A[3] + 3), (A[2] + 4, A[3] + 4), (A[0] - 5, A[1] + 2)):
        bb.set(x, max(0, hy(x, z)) + 1, z, "minecraft:barrel[facing=up,open=false]")


def design():
    bb = BigBuild(seed=1531, y_min=-16, y_max=100)
    tracker = P.PropTracker(1531)
    audit = []
    rng = np.random.default_rng(1531)
    terrain(bb)
    taken = [(YARD[0], YARD[1], YARD[2], YARD[3])]
    main_building(bb, tracker, audit)
    biscuit_building(bb, tracker, audit)
    taken.append(gas_works(bb, tracker, audit))
    taken.append(g5_cove(bb, rng))
    taken.append((30, 96, 46, 120))
    r, _ = old_lab_ruin(bb, rng, tracker, audit)
    taken.append(r)
    taken.append(dragon_bones(bb))
    yard_details(bb, rng)
    frozen_half(bb, rng, taken)
    burning_half(bb, rng, taken)
    steam_line(bb, rng)
    volcano_top(bb, rng)
    snow_layers(bb, rng)
    NT.plants(bb, -22, -22, 201, 201, height, 1590, density=0.22,
              kinds=["onepiece:ash_grass"],
              mask=lambda X, Z: land(X, Z) & ~cold(X, Z) & (rect_d(X, Z, YARD) > 0),
              ground=("blackstone", "volcanic_ash", "coarse_dirt", "scorched_stone"))
    NT.plants(bb, -22, -22, 201, 201, height, 1591, density=0.3, kinds=["minecraft:dead_bush"],
              mask=lambda X, Z: land(X, Z) & ~cold(X, Z), ground=("coarse_dirt",))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    hx1, hz1, hx2, hz2 = HALL
    b.npc(A[0] + 6, 2 * FH + 1, A[1] + 4, "vegapunk", False)
    b.npc((hx1 + hx2) // 2 + 3, 1, hz2 - 3, "law", False)
    b.npc(SHIP[0] + 26, max(0, hy(SHIP[0] + 26, SHIP[1] + 3)) + 1, SHIP[1] + 3, "smoker", False)
    b.chest(A[2] - 4, 1, A[1] + 3, "lab", "west")
    b.chest(A[0] + 4, 2 * FH + 1, A[3] - 3, "lab", "east")
    b.chest((hx1 + hx2) // 2 + 6, 2 * FH + 1, hz2 - 2, "legendary", "north")
    b.chest(RUIN[0] + 4, 1 + max(0, hy(RUIN[0] + 4, RUIN[1] + 4)), RUIN[1] + 4, "treasure", "east")
    for (gx, gz, kind) in ((A[0] - 4, A[3] + 6, "frost_soldier"), (B_BOX[0] - 4, B_BOX[1] + 2, "frost_soldier"),
                           (LAKE[0] + 4, LAKE[1] + 14, "frost_soldier"), (SHIP[0] + 24, SHIP[1] - 5, "marine"),
                           (C_BOX[2] + 5, C_BOX[1] - 4, "flame_guard"), (RUIN[0] - 4, RUIN[3] + 2, "flame_guard"),
                           (DRAGON[0] + 20, DRAGON[1] - 12, "flame_guard")):
        b.guard(gx, max(0, hy(gx, gz)) + 1, gz, kind)
    return b, 0
