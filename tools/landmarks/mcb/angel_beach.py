"""Angel Beach v2 on Angel Island, Skypiea, redesigned with the Minecraft Builder skill: 10,000 m up, where the Straw
Hats first landed in the sky.

Angel Island is a white island of Island Cloud lying in the White-White Sea, the milky Sea Cloud the sky people sail
on like water (here a wide ring of white sea cloud held in a thin cloud dish, faintly blue in the shallows, with puffs
hanging under the rim). The soft cloud beach with tall thin palms rises to grassy cloud slopes. Lovely Street curls
round the island: round white Skypiean houses with domed roofs, sky-blue bands, round windows and little side domes,
with market stalls and a plaza fountain on the hilltop. On the west slope Conis and Pagaya's house (a big and a small
dome joined, a terrace, Pagaya's Waver shed with three Wavers on the slipway); by the plaza Pagaya's dial shop. The
Milky Road, a ribbon of sea cloud, spirals up into the sky off the east shore. On the south shore a cloud pier where the
Going Merry lies at anchor. ~160 x 160, floats at a fixed height (canvas y 0 = world y 168). (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, lamp_post, palm, table, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import shipstamp as SS

SID = "angel_beach"
TITLE = "Angel Beach (Angel Island, Skypiea)"
CUTS = [2, 9, 20]
TILER = dict(terrain="none", sky_y=168)

N = 160
CLOUD = "onepiece:island_cloud"
PUFF = "onepiece:cloud_puff"
CBR = "onepiece:cloud_bricks"
MOSS = "onepiece:cloud_moss"
SHRUB = "onepiece:cloud_shrub"
# The White-White Sea: opaque Sea Cloud on a solid cloud body. It was white stained glass on a 1-3 block dish, which you
# saw straight through to the ocean far below: the island looked hollow and its clouds see-through (ryan 2026-11-02).
SEA = "onepiece:sea_cloud"
SEA_Y = -2
WALL = ["minecraft:white_concrete", "minecraft:white_terracotta", "minecraft:calcite"]
BAND = "minecraft:light_blue_terracotta"
GLASS = "minecraft:light_blue_stained_glass_pane"
HC = (80, 74)                                   # hilltop / plaza centre
_ISLE = NT.outline(80, 74, 56, 12010, wobble=0.07)
_SEA = NT.outline(80, 80, 69, 12011, wobble=0.04, lobes=((3, 0.03), (5, 0.02)))
CONIS = (36, 70)
SHOP = (80, 50)
STREET_R = 31
PIER_X = 80


def sh(X, Z):
    return _ISLE(np.asarray(X, float), np.asarray(Z, float))


def sea(X, Z):
    return (_SEA(np.asarray(X, float), np.asarray(Z, float)) > 0) & (sh(X, Z) <= 1.5)


def _height(X, Z):
    d = sh(X, Z)
    r = np.hypot(X - HC[0], Z - HC[1])
    hill = 9 * np.clip(1 - r / 46, 0, 1) ** 1.4 + NT.fbm(X, Z, 12012, 18) * 2.2
    beach = np.clip(d / 9.0, 0, 1)
    h = np.where(d < 9, beach * 1.2, 1 + hill * np.clip((d - 9) / 10, 0, 1))
    plaza = np.clip(1 - (r - 12) / 6, 0, 1)
    h = h * (1 - plaza) + 9.0 * plaza
    return np.where(d <= 1.5, SEA_Y, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SH = _height(X_, Z_).astype(int), sh(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def land(X, Z):
    return SH[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] > 1.5


def dist_in(X, Z):
    return SH[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def street(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    r = np.hypot(X - HC[0], Z - HC[1])
    m = np.abs(r - STREET_R) <= 1.6                                         # Lovely Street ring
    m |= (np.abs(X - PIER_X) <= 1.5) & (Z > HC[1]) & (dist_in(X, Z) > 1.5)  # down to the pier
    m |= (np.abs(Z - CONIS[1]) <= 1.2) & (X > CONIS[0]) & (X < HC[0])      # to Conis's house
    m |= r <= 16                                                             # the plaza
    return m


# ------------------------------------------------------------------ island + sea
def terrain(bb, rng):
    H = HMAP
    # the cloud body: deep in the middle, a soft rounded underside
    depth = lambda X, Z: np.round(-4 - np.sqrt(np.maximum(dist_in(X, Z), 0)) * 2.6 - NT.noise(X, Z, 12013, 6) * 3)
    bb.fill_where(0, -34, 0, N - 1, 12, N - 1, lambda X, Y, Z: land(X, Z) & (Y <= height(X, Z)) & (Y >= depth(X, Z)), CLOUD)
    GR = [("minecraft:grass_block", 0.56), (CLOUD, 0.22), ("minecraft:moss_block", 0.1), ("minecraft:rooted_dirt", 0.06),
          ("minecraft:coarse_dirt", 0.06)]
    BEACH = [(CLOUD, 0.86), ("minecraft:white_concrete_powder", 0.08), ("minecraft:snow_block", 0.06)]
    PAVE = [(CBR, 0.45), ("minecraft:smooth_quartz", 0.25), ("minecraft:white_terracotta", 0.18), ("minecraft:calcite", 0.12)]
    NT.cover(bb, 0, 0, N - 1, N - 1, height, BEACH, 12014, mask=lambda X, Z: land(X, Z) & (dist_in(X, Z) < 11) & ~street(X, Z), under=CLOUD)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GR, 12015, mask=lambda X, Z: land(X, Z) & (dist_in(X, Z) >= 11) & ~street(X, Z), under=CLOUD)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 12016, mask=lambda X, Z: land(X, Z) & street(X, Z), under=CLOUD)
    # the White-White Sea: sea cloud on a solid cloud body that thickens towards the island and rounds off at the rim,
    # with a ragged line of island-cloud surf along the beach
    bb.fill_where(0, SEA_Y, 0, N - 1, SEA_Y, N - 1, lambda X, Y, Z: sea(X, Z), SEA)
    bb.fill_where(0, SEA_Y, 0, N - 1, SEA_Y, N - 1,
                  lambda X, Y, Z: sea(X, Z) & (dist_in(X, Z) > -1.5 - 2 * NT.noise(X, Z, 12017, 5)), CLOUD)
    rim = lambda X, Z: np.clip(_SEA(np.asarray(X, float), np.asarray(Z, float)), 0, 9)   # 0 at the outer rim, grows inwards
    sea_floor = lambda X, Z: np.round(SEA_Y - 2 - np.sqrt(rim(X, Z)) - np.clip(dist_in(X, Z) + 12, 0, 12) * 0.25
                                      - 1.5 * NT.noise(X, Z, 12018, 7))
    bb.fill_where(0, -34, 0, N - 1, SEA_Y - 1, N - 1, lambda X, Y, Z: sea(X, Z) & (Y >= sea_floor(X, Z)), CLOUD)
    # puffs round the outer rim of the dish and under the island
    for _ in range(70):
        a = rng.uniform(0, 2 * math.pi)
        px, pz = 80 + 67 * math.cos(a), 80 + 67 * math.sin(a)
        if _SEA(np.array([px]), np.array([pz]))[0] < -1 or _SEA(np.array([px]), np.array([pz]))[0] > 3:
            continue
        px, pz, py, pr = int(px), int(pz), SEA_Y - int(rng.integers(1, 4)), float(rng.uniform(1.6, 3.0))
        bb.fill_where(px - 4, py - 3, pz - 4, px + 4, py + 3, pz + 4,
                      lambda X, Y, Z, px=px, py=py, pz=pz, pr=pr: ((X - px) ** 2 + ((Y - py) * 1.6) ** 2 + (Z - pz) ** 2) <= pr * pr, CLOUD,
                      only_empty=True)
    for _ in range(26):
        px, pz = int(rng.integers(40, 120)), int(rng.integers(32, 112))
        if not land(np.array([px]), np.array([pz]))[0]:
            continue
        py = int(-4 - math.sqrt(max(dist_in(px, pz), 0)) * 2.6) - 2
        pr = float(rng.uniform(2.5, 4.5))
        bb.fill_where(px - 5, py - 4, pz - 5, px + 5, py + 4, pz + 5,
                      lambda X, Y, Z, px=px, py=py, pz=pz, pr=pr: ((X - px) ** 2 + ((Y - py) * 1.4) ** 2 + (Z - pz) ** 2) <= pr * pr, CLOUD,
                      only_empty=True)


# ------------------------------------------------------------------ Skypiean houses
def dome(bb, cx, y, cz, r, block, rib=None, k=0.8):
    R = r + 0.4
    shell = lambda X, Y, Z: ((((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - y) / (R * k)) ** 2) <= 1) & \
                            ((((X - cx) ** 2 + (Z - cz) ** 2) / (R - 1.2) ** 2 + ((Y - y) / (R * k - 1.2)) ** 2) > 1)
    bb.fill_where(cx - r - 1, y, cz - r - 1, cx + r + 1, y + r + 1, cz + r + 1, shell, block)
    if rib:
        bb.fill_where(cx - r - 1, y, cz - r - 1, cx + r + 1, y + r + 1, cz + r + 1,
                      lambda X, Y, Z: shell(X, Y, Z) & ((X == cx) | (Z == cz)), rib)
    return y + int(R * k)


def sky_house(bb, cx, cz, r, floors, door, tracker, audit, kinds, seed, side=True):
    """A round Skypiean house: white drum walls with a sky-blue band, round-ish windows framed in cloud brick, a base
    course of cloud brick, a white dome with a little lantern cap, and often a smaller side dome (a porch room)."""
    y = hy(cx, cz) + 1
    fh = 4
    H = floors * (fh + 1)
    disc = lambda rr: (lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= rr)
    bb.fill_where(cx - r - 1, y - 4, cz - r - 1, cx + r + 1, y - 1, cz + r + 1, disc(r + 1.3), CBR)
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H - 1, cz + r, disc(r + 0.4), WALL[0])
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H - 1, cz + r,
                  lambda X, Y, Z: disc(r + 0.4)(X, Y, Z) & (NT.noise(X + 3 * Y, Z, seed, 3) > 0.72), WALL[1])
    bb.fill_where(cx - r, y, cz - r, cx + r, y, cz + r, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - r) < 0.7, CBR)
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r, disc(r - 0.8), AIR)
    for f in range(floors):
        fy = y + f * (fh + 1)
        bb.fill_where(cx - r, fy - 1, cz - r, cx + r, fy - 1, cz + r, disc(r - 0.8), "minecraft:birch_planks")
        bb.fill_where(cx - r, fy + fh, cz - r, cx + r, fy + fh, cz + r, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - r) < 0.7, BAND)
        n = max(4, int(r * 1.1))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            wx, wz = cx + int(round(r * math.cos(a))), cz + int(round(r * math.sin(a)))
            bb.set(wx, fy + 1, wz, GLASS); bb.set(wx, fy + 2, wz, GLASS)
    for f in range(1, floors):
        fy = y + f * (fh + 1)
        bb.fill(cx - r + 2, y + (f - 1) * (fh + 1), cz, cx - r + 2, fy - 1, cz, "minecraft:ladder[facing=east]")
        bb.set(cx - r + 2, fy - 1, cz, AIR)
    dx, dz = {"south": (0, r), "north": (0, -r), "east": (r, 0), "west": (-r, 0)}[door]
    ox, oz = (np.sign(dx), np.sign(dz))
    bb.fill(cx + dx, y, cz + dz, cx + dx, y + 2, cz + dz, AIR)
    bb.set(cx + dx, y, cz + dz, f"minecraft:birch_door[facing={door},half=lower,hinge=left]")
    bb.set(cx + dx, y + 1, cz + dz, f"minecraft:birch_door[facing={door},half=upper,hinge=left]")
    bb.set(cx + dx, y + 2, cz + dz, CBR)
    bb.set(cx + dx + ox, y - 1, cz + dz + oz, "minecraft:smooth_quartz_slab[type=top]")
    sx, sz = (oz, ox)
    for s in (-1, 1):
        set_if_air(bb, cx + dx + ox + sx * s * 2, y, cz + dz + oz + sz * s * 2, "minecraft:potted_azure_bluet")
    q = int((r - 1) / 1.42)
    for f in range(floors):
        fy = y + f * (fh + 1)
        room = (cx - q, cz - q, cx + q, cz + q)
        drs = [(cx + dx - ox, cz + dz - oz)] if f == 0 else [(cx - r + 2, cz)]
        P.furnish_room(bb, room, fy, kind=kinds[f % len(kinds)], height=fh, seed=seed + f, wood="birch", tracker=tracker, doors=drs)
        txt, ok = P.audit_props(bb, [room], fy, fh)
        if not ok:
            audit.append(txt)
    top = dome(bb, cx, y + H, cz, r, "minecraft:white_concrete", rib=CBR)
    bb.fill_where(cx - r - 1, y + H, cz - r - 1, cx + r + 1, y + H, cz + r + 1,
                  lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - (r + 1.1)) < 0.55, "minecraft:smooth_quartz_slab[type=bottom]")
    bb.set(cx, top + 1, cz, "minecraft:light_blue_concrete")
    bb.set(cx, top + 2, cz, "minecraft:end_rod[facing=up]")
    if side and r >= 5:
        # a smaller side dome room opposite the door (a pantry / porch)
        sxx, szz = cx - ox * (r + 2), cz - oz * (r + 2)
        sr = 3
        bb.fill_where(sxx - sr, y - 3, szz - sr, sxx + sr, y - 1, szz + sr, lambda X, Y, Z: np.hypot(X - sxx, Z - szz) <= sr + 0.4, CBR)
        bb.fill_where(sxx - sr, y, szz - sr, sxx + sr, y + 2, szz + sr, lambda X, Y, Z: np.hypot(X - sxx, Z - szz) <= sr + 0.4, WALL[2])
        bb.fill_where(sxx - sr, y, szz - sr, sxx + sr, y + 3, szz + sr,
                      lambda X, Y, Z: (np.hypot(X - sxx, Z - szz) <= sr - 0.8) | (np.hypot(X - cx, Z - cz) <= r - 0.8), AIR)
        dome(bb, sxx, y + 3, szz, sr, "minecraft:white_concrete")
        bb.fill(min(sxx, cx - ox * r), y, min(szz, cz - oz * r), max(sxx, cx - ox * r), y + 1, max(szz, cz - oz * r), AIR)
        bb.set(sxx, y, szz, "minecraft:barrel[facing=up]")
        bb.set(sxx + sx, y + 2, szz + sz, "minecraft:lantern[hanging=true]")
    return (cx - r - 2, cz - r - 2, cx + r + 2, cz + r + 2)


def waver(bb, x, y, z, axis="x", col="light_blue"):
    """A Waver: a slim one-man board-boat with a raised seat and the Breath Dial engine at the stern."""
    if axis == "x":
        bb.fill(x - 3, y, z, x + 2, y, z, f"minecraft:{col}_concrete")
        bb.set(x + 3, y, z, "minecraft:birch_slab[type=bottom]")
        bb.set(x - 1, y + 1, z, "minecraft:birch_stairs[facing=west,half=bottom]")
        bb.set(x - 3, y + 1, z, "minecraft:white_concrete")
        bb.set(x + 1, y + 1, z, "minecraft:birch_trapdoor[facing=east,half=bottom,open=true]")
    else:
        bb.fill(x, y, z - 3, x, y, z + 2, f"minecraft:{col}_concrete")
        bb.set(x, y, z + 3, "minecraft:birch_slab[type=bottom]")
        bb.set(x, y + 1, z - 1, "minecraft:birch_stairs[facing=north,half=bottom]")
        bb.set(x, y + 1, z - 3, "minecraft:white_concrete")


def conis_house(bb, tracker, audit):
    cx, cz = CONIS
    box = sky_house(bb, cx, cz, 7, 2, "east", tracker, audit, ["kitchen", "bedroom"], 12030, side=False)
    # the second, smaller dome joined on the north: Pagaya's workroom
    box2 = sky_house(bb, cx + 2, cz - 13, 5, 1, "east", tracker, audit, ["workshop"], 12031, side=False)
    y = hy(cx, cz) + 1
    bb.fill(cx - 1, y, cz - 8, cx + 1, y + 2, cz - 6, AIR)
    bb.fill(cx - 2, y - 1, cz - 9, cx + 2, y - 1, cz - 6, "minecraft:birch_planks")
    bb.fill(cx - 2, y, cz - 9, cx - 2, y + 3, cz - 6, WALL[0]); bb.fill(cx + 2, y, cz - 9, cx + 2, y + 3, cz - 6, WALL[0])
    bb.fill(cx - 2, y + 3, cz - 9, cx + 2, y + 3, cz - 6, "minecraft:white_concrete")
    # terrace on the sea side (west), birch deck, rail, a table and chairs, a cloud fox's basket
    ty = y - 1
    bb.fill(cx - 15, ty - 4, cz - 6, cx - 8, ty, cz + 6, CBR)
    bb.fill(cx - 15, ty, cz - 6, cx - 8, ty, cz + 6, "minecraft:birch_planks")
    bb.fill(cx - 15, ty + 1, cz - 6, cx - 8, ty + 3, cz + 6, AIR)
    for z in range(cz - 6, cz + 7):
        bb.set(cx - 15, ty + 1, z, "minecraft:birch_fence")
    for x in range(cx - 15, cx - 7):
        bb.set(x, ty + 1, cz - 6, "minecraft:birch_fence"); bb.set(x, ty + 1, cz + 6, "minecraft:birch_fence")
    table(bb, cx - 11, ty + 1, cz, cloth="minecraft:light_blue_carpet", wood="birch")
    bb.set(cx - 12, ty + 1, cz + 3, "minecraft:white_bed[facing=south,part=foot]") if False else None
    bb.set(cx - 9, ty + 1, cz - 4, "minecraft:composter")
    bb.set(cx - 9, ty + 2, cz - 4, "minecraft:white_carpet")
    # Pagaya's Waver shed on the south side: open front to the beach, slipway, three Wavers
    sx1, sz1, sx2, sz2 = cx - 8, cz + 10, cx + 6, cz + 20
    sy = hy(cx, cz + 15) + 1
    bb.fill(sx1, sy - 4, sz1, sx2, sy - 1, sz2, CBR)
    bb.fill(sx1, sy - 1, sz1, sx2, sy - 1, sz2, "minecraft:birch_planks")
    for (px, pz) in ((sx1, sz1), (sx2, sz1), (sx1, sz2), (sx2, sz2), (sx1, (sz1 + sz2) // 2), (sx2, (sz1 + sz2) // 2)):
        bb.fill(px, sy, pz, px, sy + 4, pz, "minecraft:stripped_birch_log[axis=y]")
    bb.fill(sx1 + 1, sy, sz2, sx2 - 1, sy + 4, sz2, WALL[2])
    bb.fill(sx2, sy, sz1 + 1, sx2, sy + 4, sz2 - 1, WALL[2])
    P.gable_roof(bb, sx1 - 1, sz1 - 1, sx2 + 1, sz2 + 1, sy + 5, "minecraft:light_blue_terracotta" if False else "minecraft:birch_stairs",
                 ridge_axis="x", gable_fill="minecraft:white_concrete", overhang=1)
    for k, col in enumerate(("light_blue", "white", "cyan")):
        waver(bb, cx - 2, sy, sz1 + 2 + k * 3, "x", col)
    bb.set(sx2 - 1, sy, sz1 + 1, "minecraft:crafting_table"); bb.set(sx2 - 1, sy, sz1 + 2, "minecraft:smithing_table")
    bb.set(sx2 - 1, sy, sz2 - 1, "minecraft:barrel[facing=up]"); bb.set(sx2 - 2, sy, sz2 - 1, "minecraft:grindstone[face=floor,facing=north]")
    for z in (sz1 + 3, sz2 - 3):
        bb.set(sx1 + 4, sy + 4, z, "minecraft:lantern[hanging=true]")
    # the slipway down to the sea cloud
    for i in range(0, 30):
        x = sx1 - 1 - i
        if not land(np.array([x]), np.array([cz + 15]))[0] and i > 2:
            bb.fill(x, SEA_Y, cz + 13, x, SEA_Y, cz + 17, "minecraft:birch_slab[type=top]")
            break
        yy = hy(x, cz + 15)
        bb.fill(x, yy, cz + 13, x, yy, cz + 17, "minecraft:birch_planks")
    return (box[0] - 12, box2[1], sx2 + 4, sz2 + 4)


def dial_shop(bb, tracker, audit):
    cx, cz = SHOP
    box = sky_house(bb, cx, cz, 6, 1, "south", tracker, audit, ["storage"], 12040, side=True)
    y = hy(cx, cz) + 1
    # an awning over the door and a display counter with dials (shells and pots) on it
    for x in range(cx - 3, cx + 4):
        bb.set(x, y + 3, cz + 7, f"minecraft:{'light_blue' if x % 2 else 'white'}_wool")
    for x in (cx - 3, cx + 3):
        bb.fill(x, y, cz + 8, x, y + 2, cz + 8, "minecraft:birch_fence")
    bb.fill(cx - 3, y + 3, cz + 8, cx + 3, y + 3, cz + 8, "minecraft:birch_slab[type=bottom]")
    bb.fill(cx - 2, y, cz + 9, cx + 2, y, cz + 9, "minecraft:birch_planks") if False else None
    for x, s in ((cx - 2, "minecraft:decorated_pot[facing=south]"), (cx + 2, "minecraft:flower_pot")):
        bb.set(x, y, cz + 8 - 0, "minecraft:birch_fence") if False else None
    return box


def stall(bb, x, z, col, facing):
    y = hy(x, z) + 1
    bb.fill(x - 2, y, z - 1, x + 2, y, z - 1, "minecraft:birch_planks")
    for dx in (-2, 2):
        bb.fill(x + dx, y, z + 1, x + dx, y + 2, z + 1, "minecraft:birch_fence")
        bb.fill(x + dx, y + 1, z - 1, x + dx, y + 2, z - 1, "minecraft:birch_fence")
    for dx in range(-2, 3):
        bb.set(x + dx, y + 3, z - 1, f"minecraft:{col}_wool")
        bb.set(x + dx, y + 3, z, f"minecraft:{col if dx % 2 else 'white'}_wool")
        bb.set(x + dx, y + 3, z + 1, f"minecraft:{col}_carpet") if False else None
    bb.set(x - 1, y + 1, z - 1, "minecraft:melon"); bb.set(x + 1, y + 1, z - 1, "minecraft:barrel[facing=up]")
    bb.set(x, y + 1, z - 1, "minecraft:flower_pot")


def fountain(bb, cx, cz):
    y = hy(cx, cz)
    bb.fill_where(cx - 6, y, cz - 6, cx + 6, y + 1, cz + 6, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 5.6, CBR)
    bb.fill_where(cx - 6, y + 1, cz - 6, cx + 6, y + 1, cz + 6, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 4.6, "minecraft:water")
    bb.fill(cx, y + 1, cz, cx, y + 4, cz, "minecraft:quartz_pillar[axis=y]")
    dome(bb, cx, y + 5, cz, 2, "minecraft:white_concrete", k=0.6)
    bb.set(cx, y + 5, cz, "minecraft:water")
    for (dx, dz) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
        lamp_post(bb, cx + dx, y + 1, cz + dz, post="minecraft:birch_fence", h=3)


def milky_road(bb):
    """A ribbon of sea cloud spiralling up into the sky off the east shore, rimmed with island cloud and puffs."""
    c = (133, 42)
    R = 15
    pts = []
    for i in range(0, 520):
        t = i / 520
        a = math.radians(150 - 360 * t)
        x, z = c[0] + R * math.cos(a), c[1] + R * math.sin(a)
        y = SEA_Y + 34 * t
        pts.append((x, y, z))
    done = set()
    for (x, y, z) in pts:
        a = math.atan2(z - c[1], x - c[0])
        for w in np.arange(-3.0, 3.1, 0.5):
            px, pz = int(round(x + w * math.cos(a))), int(round(z + w * math.sin(a)))
            py = int(round(y))
            if (px, py, pz) in done:
                continue
            done.add((px, py, pz))
            if abs(w) > 2.5:
                bb.set(px, py, pz, CLOUD)
                bb.set(px, py + 1, pz, PUFF) if NT.noise(np.array([px]), np.array([pz]), 12019, 2)[0] > 0.75 else None
            else:
                bb.set(px, py, pz, SEA)
            bb.set(px, py - 1, pz, CLOUD) if abs(w) <= 1.5 and (px + pz) % 3 else None
    return (c[0] - R - 3, c[1] - R - 3, c[0] + R + 3, c[1] + R + 3)


def pier(bb):
    z_sea = next(z for z in range(HC[1], N) if not land(np.array([PIER_X]), np.array([z]))[0])
    z_end = min(N - 22, z_sea + 12)
    bb.fill(PIER_X - 2, SEA_Y + 1, z_sea - 3, PIER_X + 2, SEA_Y + 1, z_end, CBR)
    bb.fill(PIER_X - 1, SEA_Y + 1, z_sea - 3, PIER_X + 1, SEA_Y + 1, z_end, "minecraft:birch_planks")
    for z in range(z_sea, z_end + 1, 4):
        for x in (PIER_X - 2, PIER_X + 2):
            bb.set(x, SEA_Y + 2, z, "minecraft:birch_fence")
            bb.set(x, SEA_Y + 3, z, "minecraft:lantern[hanging=false]") if z % 8 == z_sea % 8 else None
    for x in range(PIER_X - 2, PIER_X + 3):
        bb.set(x, SEA_Y + 2, z_end, "minecraft:birch_fence")
    for k in range(3):
        waver(bb, PIER_X - 5, SEA_Y, z_sea + 2 + k * 4, "x", ("light_blue", "white", "lime")[k])
    SS.stamp_ship(bb, "going_merry", PIER_X + 22, z_end - 2, SEA_Y, 0)
    return (PIER_X - 8, z_sea - 4, PIER_X + 42, N)


def design():
    bb = BigBuild(seed=12010, y_min=-36, y_max=72)
    tracker = P.PropTracker(12010)
    audit = []
    rng = np.random.default_rng(12010)
    terrain(bb, rng)
    fountain(bb, *HC)
    taken = [(HC[0] - 16, HC[1] - 16, HC[0] + 16, HC[1] + 16)]
    taken.append(conis_house(bb, tracker, audit))
    taken.append(dial_shop(bb, tracker, audit))
    taken.append(pier(bb))
    taken.append(milky_road(bb))
    # market stalls round the plaza
    for k, a in enumerate(range(20, 360, 45)):
        x, z = int(HC[0] + 12 * math.cos(math.radians(a))), int(HC[1] + 12 * math.sin(math.radians(a)))
        if abs(x - PIER_X) > 3:
            stall(bb, x, z, ("light_blue", "yellow", "pink", "lime", "cyan", "orange", "magenta", "white")[k % 8], "south")
    # houses along both sides of Lovely Street, doors to the street
    KINDS = [["living", "bedroom"], ["kitchen", "bedroom"], ["living"], ["bedroom", "storage"], ["kitchen"], ["library", "bedroom"]]
    n = 0
    for ring, step in ((STREET_R - 8, 36), (STREET_R + 9, 15)):
        for a in range(0, 360, step):
            r = 4 if ring < STREET_R else (4 if (a // step) % 2 else 5)
            cx, cz = int(HC[0] + ring * math.cos(math.radians(a + 7))), int(HC[1] + ring * math.sin(math.radians(a + 7)))
            if not land(np.array([cx]), np.array([cz]))[0] or dist_in(cx, cz) < r + 3:
                continue
            if any(t[0] <= cx + r and cx - r <= t[2] and t[1] <= cz + r and cz - r <= t[3] for t in taken):
                continue
            vx, vz = HC[0] - cx, HC[1] - cz
            if ring > STREET_R:
                pass
            else:
                vx, vz = -vx, -vz
            door = ("east" if vx > 0 else "west") if abs(vx) > abs(vz) else ("south" if vz > 0 else "north")
            floors = 2 if (n % 3 == 1) else 1
            taken.append(sky_house(bb, cx, cz, r, floors, door, tracker, audit, KINDS[n % len(KINDS)], seed_of("ab", cx, cz)))
            n += 1
    print("houses:", n)
    # palms on the beach and slopes, cloud shrubs, lamp posts
    p = 0
    for _ in range(2000):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        d = dist_in(x, z)
        if not (3 < d < 22) or street(np.array([x]), np.array([z]))[0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        lx, lz = x - HC[0], z - HC[1]
        ll = math.hypot(lx, lz) or 1
        palm(bb, x, hy(x, z) + 1, z, int(rng.integers(11, 17)), (int(round(lx / ll)), int(round(lz / ll))))
        taken.append((x - 3, z - 3, x + 3, z + 3))
        p += 1
        if p >= 34:
            break
    print("palms:", p)
    for a in range(0, 360, 24):
        x, z = int(HC[0] + (STREET_R + 2.5) * math.cos(math.radians(a))), int(HC[1] + (STREET_R + 2.5) * math.sin(math.radians(a)))
        if (bb.get_region(x, hy(x, z) + 1, z, x, hy(x, z) + 4, z) == 0).all():
            lamp_post(bb, x, hy(x, z) + 1, z, post="minecraft:birch_fence", h=3)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 12090, density=0.3,
              kinds=[SHRUB, "minecraft:short_grass", PUFF, "minecraft:short_grass", "minecraft:fern"],
              flowers=["minecraft:azure_bluet", "minecraft:oxeye_daisy", "minecraft:cornflower", "minecraft:lily_of_the_valley"],
              mask=lambda X, Z: land(X, Z) & (dist_in(X, Z) >= 11) & ~street(X, Z),
              ground=("grass_block", "moss_block", "rooted_dirt", "coarse_dirt", "island_cloud"))
    # (no cloud moss on the beach: its petals read as little wire brackets all over the sand, ryan 2026-11-02)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    cx, cz = CONIS
    b.chest(cx + 3, hy(cx, cz) + 1, cz - 3, "sky_treasure", "west")
    b.chest(SHOP[0] - 2, hy(*SHOP) + 1, SHOP[1] - 2, "sky_treasure", "south")
    b.chest(HC[0] + 3, hy(*HC) + 1, HC[1] - 8, "easy", "north")
    return b, 0
