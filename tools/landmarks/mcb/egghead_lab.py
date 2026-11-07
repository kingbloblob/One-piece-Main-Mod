"""Egghead v2, Dr. Vegapunk's island of the future, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/egghead_lab.md).

An irregular green island whose ground fades out to its beaches. The lower town (Faustphase / Fabriophase) rings a
rocky central plateau: round white pod labs with cyan bands and domes, glowing paths, the Pacifista factory with its
assembly line, the Seraphim capsule hall, a robot cafe, round future trees, and a harbour where the Thousand Sunny
(the real ship template) is moored. A glass escalator tube climbs the plateau's cliff. On top (Labophase) stands the
giant egg on a flared stalk: an elevator up the middle into three lab floors (research lab, Vegapunk's library of
knowledge, the Frontier Dome control room), a viewing ring at the cracked top, and Punk Records, the great brain,
floating above the crack on its stem. 176 x 176. y 0 = ground / sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "egghead_lab"
TITLE = "Egghead Labophase"
CUTS = [4, 30, 60]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
CX, CZ = 88, 84                        # island centre
EX, EZ = 90, 74                        # egg / plateau centre
PLAT_R = 30                            # plateau radius (irregular)
PLAT_H = 20                            # plateau top
STALK = 12                             # stalk height above the plateau
ERX, ERY = 24, 34                      # egg radii (lower half squashed)
EY = PLAT_H + STALK + int(ERY * 0.85)  # egg centre
FLOORS = (EY - 16, EY - 4, EY + 8)     # lab floors inside the egg (first air layer)
CRACK = EY + ERY - 12                  # the top is broken open above here
HARBOUR = (88, 160, 30, 14)            # harbour basin (x, z, rx, rz)
SUNNY = (86, 160)

WHITE = "minecraft:white_concrete"
QUARTZ = "minecraft:smooth_quartz"
CYAN = "minecraft:cyan_concrete"
PINK = "minecraft:pink_concrete"
YELLOW = "minecraft:yellow_concrete"
PANEL = "onepiece:lab_panel"
LIGHT = "onepiece:lab_light"
GLASS = "minecraft:light_blue_stained_glass"
WGLASS = "minecraft:white_stained_glass"
QST = "minecraft:quartz_stairs"

SHORE = NT.outline(CX, CZ, 80, 1061)
PLAT = NT.outline(EX, EZ, PLAT_R, 1062, wobble=0.3, lobes=((2, 0.08), (3, 0.07), (5, 0.05), (7, 0.04), (11, 0.03)))

ROCK = [("minecraft:stone", 0.40), ("minecraft:andesite", 0.18), ("minecraft:calcite", 0.14),
        ("minecraft:tuff", 0.12), ("minecraft:diorite", 0.10), ("minecraft:mossy_cobblestone", 0.06)]
SAND = [("minecraft:sand", 0.78), ("minecraft:sandstone", 0.08), ("minecraft:gravel", 0.06), ("minecraft:clay", 0.08)]
PATH = [("minecraft:smooth_quartz", 0.62), ("minecraft:white_concrete", 0.22), ("minecraft:quartz_bricks", 0.16)]
PATHS = {b for b, _ in PATH} | {"minecraft:sea_lantern"}


def ell(X, Z, e):
    x, z, rx, rz = e
    return ((X - x) / rx) ** 2 + ((Z - z) / rz) ** 2


def height(X, Z):
    """Low rolling town ground, a cliff-sided plateau in the middle (rounded top, terraced foot), beach at the shore."""
    d = SHORE(X, Z)
    inland = np.clip((d - 3) / 14.0, 0, 1)
    town = NT.fbm(X, Z, 1071, 34) * 3 * inland
    p = PLAT(X, Z)                                                  # > 0 inside the plateau
    t = np.clip((p + 11) / 11.0, 0, 1)
    raw = t ** 1.5 * PLAT_H
    step = 4 + 2 * NT.noise(X, Z, 1073, 9)                        # rocky ledges with grassy shelves
    ledge = np.floor(raw / step) * step + (raw % step) ** 2 / step * 0.35
    terr = np.where(p > -11, np.minimum(raw, ledge + NT.noise(X, Z, 1072, 4) * 1.5), 0)
    h = np.maximum(town, np.minimum(terr, PLAT_H))
    h = np.where(p > 0, PLAT_H, h)
    h = np.where(d < 2.5, -1, h)
    return np.round(h)


def land(X, Z):
    return (SHORE(X, Z) > 0) & (ell(X, Z, HARBOUR) >= 1)


def hy(x, z):
    return int(height(np.array([[x]]), np.array([[z]]))[0, 0])


def steep(X, Z):
    h = height(X, Z)
    return np.maximum.reduce([np.abs(height(X + dx, Z + dz) - h) for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1))])


# ------------------------------------------------------------------ ground
def terrain(bb):
    H = height
    NT.cover(bb, 0, 0, N - 1, N - 1, H, SAND, 1081, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6),
             under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, ROCK, 1082,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (PLAT(X, Z) <= 1) & (steep(X, Z) >= 2),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, NT.MEADOW, 1083,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & ((PLAT(X, Z) > 1) | (steep(X, Z) < 2)), core="minecraft:stone")
    # the harbour basin
    x, z, rx, rz = HARBOUR

    def depth(X, Z):
        t = ell(X, Z, HARBOUR)
        return np.where(t < 1, np.round(-2 - 7 * (1 - t) ** 0.5 - 3 * np.clip((Z - z) / rz, 0, 1)), 99)
    for y in range(-12, 1):
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz), lambda X, yy, Z: (depth(X, Z) < yy) & (SHORE(X, Z) > -6), "minecraft:water")
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz), lambda X, yy, Z: (depth(X, Z) == yy) & (SHORE(X, Z) > -6), "minecraft:sand")
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz), lambda X, yy, Z: (depth(X, Z) - 1 == yy) & (SHORE(X, Z) > -6), "minecraft:sandstone")


def paths(bb, rng):
    """Glowing white roads: a ring road round the plateau foot, spokes out to the shore. Lights at uneven spacing."""
    def road(x0, z0, x1, z1, w=2):
        L = int(max(abs(x1 - x0), abs(z1 - z0)))
        nxt = int(rng.integers(4, 8))
        for i in range(L + 1):
            t = i / max(L, 1)
            x, z = round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)
            for dx in range(-w, w + 1):
                for dz in range(-w, w + 1):
                    xx, zz = x + dx, z + dz
                    if not (0 <= xx < N and 0 <= zz < N):
                        continue
                    X, Z = np.array([[xx]]), np.array([[zz]])
                    if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 4:
                        continue
                    y = hy(xx, zz)
                    if y > 3:
                        continue
                    edge = max(abs(dx), abs(dz)) == w
                    cur = bb.names[bb.get_region(xx, y, zz, xx, y, zz)[0, 0, 0]] or ""
                    if edge and cur in PATHS:
                        continue
                    bb.set(xx, y, zz, "minecraft:cyan_terracotta" if edge else PATH[int(NT.noise(xx, zz, 1091, 3) * 2.99)][0])
                    bb.fill(xx, y + 1, zz, xx, y + 3, zz, AIR)
            if i == nxt:
                X, Z = np.array([[x]]), np.array([[z]])
                if land(X, Z)[0, 0] and hy(x, z) <= 3:
                    bb.set(x, hy(x, z), z, "minecraft:sea_lantern")
                nxt += int(rng.integers(4, 8))
    R = PLAT_R + 12
    pts = [(EX + round(R * math.cos(a)), EZ + round(R * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 41)]
    for (a, b) in zip(pts, pts[1:]):
        road(a[0], a[1], b[0], b[1])
    for ang in (0.35, 1.57, 2.8, 3.9, 5.2):
        road(EX + round(R * math.cos(ang)), EZ + round(R * math.sin(ang)),
             EX + round((R + 34) * math.cos(ang)), EZ + round((R + 34) * math.sin(ang)), w=1)


# ------------------------------------------------------------------ the town
def pod_lab(bb, cx, cz, r, floors, tracker, audit, kinds, accent=CYAN):
    """A round white lab: drum walls with a ribbon window, an accent band, a dome, floors furnished inside."""
    y0 = max(0, hy(cx, cz))
    fh = 5
    top = y0 + fh * floors
    bb.cylinder(cx, y0 - 3, cz, r + 1, y0, "minecraft:smooth_stone")
    bb.cylinder(cx, y0 + 1, cz, r, top, WHITE, hollow=True)
    bb.cylinder(cx, y0 + 1, cz, r - 1, top, AIR)
    for k in range(floors):
        fy = y0 + fh * k
        if k:
            bb.cylinder(cx, fy, cz, r - 1, fy, PANEL)
        bb.fill_where(cx - r, fy + 2, cz - r, cx + r, fy + 3, cz + r,
                      lambda X, yy, Z: (np.abs(((X - cx) ** 2 + (Z - cz) ** 2) - r * r) <= r) & ((np.arctan2(Z - cz, X - cx) * 4).astype(int) % 3 != 0),
                      GLASS)
    bb.ring(cx, top, cz, r - 1, r + 1, top, accent)
    bb.ring(cx, y0 + 1, cz, r - 1, r + 1, y0 + 1, accent) if False else None
    bb.dome(cx, top, cz, r, QUARTZ)
    bb.cylinder(cx, top, cz, r - 1, top, AIR)
    bb.set(cx, top + r, cz, LIGHT)
    # door (south) with a little canopy
    bb.fill(cx - 1, y0 + 1, cz + r, cx + 1, y0 + 3, cz + r, AIR)
    bb.fill(cx - 2, y0 + 4, cz + r + 1, cx + 2, y0 + 4, cz + r + 2, "minecraft:smooth_quartz_slab[type=bottom]")
    # inside: a square of rooms per floor, a ladder in the core
    s = int(r * 0.7)
    for k in range(floors):
        fy = y0 + fh * k + 1
        furnish(bb, [(cx - s, cz - s, cx + s, cz + s - 2)], fy, fh - 1, [kinds[k % len(kinds)]], seed_of("pod", cx, cz, k),
                tracker, wood="birch", audit=audit)
    if floors > 1:
        bb.fill(cx - r + 1, y0 + 1, cz, cx - r + 1, top - 1, cz, "minecraft:ladder[facing=east]")
        bb.fill(cx - r + 1, y0 + fh, cz, cx - r + 1, y0 + fh * (floors - 1), cz, "minecraft:ladder[facing=east]")
    return (cx - r - 3, cz - r - 3, cx + r + 3, cz + r + 4)


def pacifista_factory(bb, tracker, audit):
    """The Fabriophase factory (east): a long white hall with a sawtooth glass roof, the assembly line inside."""
    x1, z1, x2, z2 = 132, 54, 168, 74
    y0 = max(0, max(hy(x, z) for x in (x1, x2) for z in (z1, z2)))
    bb.fill(x1 - 2, y0 - 3, z1 - 2, x2 + 2, y0, z2 + 2, "minecraft:smooth_stone")
    top = tier(bb, x1, z1, x2, z2, y0, 1, 12, [WHITE, QUARTZ], GLASS, None, pilaster=CYAN, band=None,
               top_plate="minecraft:light_gray_concrete", weights=[0.8, 0.2], every=4, pil_every=6, win_h=4)
    for x in range(x1, x2 + 1, 6):                               # sawtooth roof lights
        for k in range(4):
            bb.fill(x + k, top + 1 + (3 - k), z1, x + k, top + 1 + (3 - k), z2, WHITE)
            bb.fill(x + k, top + 1, z1, x + k, top + (3 - k), z2, AIR)
        bb.fill(x + 4, top + 1, z1, x + 4, top + 4, z2, GLASS)
        bb.fill(x + 5, top + 1, z1, x + 5, top + 1, z2, WHITE)
    bb.fill(x1 + 1, top, z1 + 1, x2 - 1, top, z2 - 1, AIR)
    y = y0 + 1
    zc = (z1 + z2) // 2
    bb.fill(x1 + 2, y0, zc - 1, x2 - 2, y0, zc + 1, "minecraft:black_concrete")
    bb.fill(x1 + 2, y, zc - 1, x2 - 2, y, zc + 1, "minecraft:gray_carpet")
    for x in range(x1 + 4, x2 - 3, 5):                            # Pacifistas half built on the line
        bb.fill(x, y, zc, x, y + 1, zc, "minecraft:iron_block")
        bb.fill(x - 1, y + 2, zc, x + 1, y + 4, zc, "minecraft:iron_block")
        bb.set(x, y + 5, zc, "minecraft:white_concrete")
        bb.set(x, y + 5, zc - 1, "minecraft:red_stained_glass")
        bb.set(x - 2, y + 4, zc, "minecraft:iron_block" if x % 2 else AIR)
        bb.set(x + 2, y + 4, zc, "minecraft:iron_block")
        for side in (-3, 3):                                      # robot arms over the line
            bb.fill(x, y, zc + side, x, y + 7, zc + side, "minecraft:iron_bars")
            bb.set(x, y + 8, zc + side, "minecraft:iron_block")
            bb.set(x, y + 8, zc + side // 3 * 2, "minecraft:iron_block")
            bb.set(x, y + 7, zc + side // 3, "minecraft:lightning_rod[facing=down]")
    for x in range(x1 + 3, x2 - 2, 6):
        bb.set(x, top - 1, z1 + 3, LIGHT)
        bb.set(x, top - 1, z2 - 3, LIGHT)
    furnish(bb, [(x1 + 1, z1 + 1, x1 + 9, zc - 4), (x2 - 9, zc + 4, x2 - 1, z2 - 1)], y, 5, ["workshop", "storage"],
            seed_of("factory"), tracker, wood="birch", audit=audit)
    bb.fill(x1, y, zc - 1, x1, y + 3, zc + 1, AIR)
    bb.fill(x2, y, zc - 1, x2, y + 3, zc + 1, AIR)
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


def seraphim_hall(bb, tracker, audit):
    """A round glass-fronted hall (north-west) with the Seraphim in their capsules in a ring."""
    cx, cz, r = 40, 40, 11
    y0 = max(0, hy(cx, cz))
    bb.cylinder(cx, y0 - 3, cz, r + 1, y0, "minecraft:polished_diorite")
    bb.cylinder(cx, y0 + 1, cz, r, y0 + 9, WHITE, hollow=True)
    bb.cylinder(cx, y0 + 1, cz, r - 1, y0 + 9, AIR)
    bb.fill_where(cx - r, y0 + 2, cz - r, cx + r, y0 + 7, cz + r,
                  lambda X, yy, Z: (np.abs(((X - cx) ** 2 + (Z - cz) ** 2) - r * r) <= r) & (Z > cz), GLASS)
    bb.ring(cx, y0 + 10, cz, r - 1, r + 1, y0 + 10, PINK)
    bb.dome(cx, y0 + 10, cz, r, QUARTZ)
    bb.cylinder(cx, y0 + 10, cz, r - 1, y0 + 10, AIR)
    bb.cylinder(cx, y0 + 10 + r - 2, cz, 2, y0 + 10 + r - 2, GLASS)
    for k in range(7):                                             # capsules round the wall
        a = math.radians(200 + k * 24 - 180)
        x, z = round(cx + (r - 3) * math.cos(a)), round(cz - (r - 3) * math.sin(a))
        bb.set(x, y0 + 1, z, PANEL)
        bb.fill(x, y0 + 2, z, x, y0 + 5, z, GLASS)
        bb.set(x, y0 + 3, z, "minecraft:black_concrete")
        bb.set(x, y0 + 4, z, "minecraft:white_concrete")
        bb.set(x, y0 + 6, z, LIGHT)
    bb.cylinder(cx, y0, cz, 3, y0, "minecraft:cyan_glazed_terracotta" if False else CYAN)
    bb.set(cx, y0 + 1, cz, "minecraft:enchanting_table")
    bb.fill(cx - 1, y0 + 1, cz + r, cx + 1, y0 + 3, cz + r, AIR)
    return (cx - r - 3, cz - r - 3, cx + r + 3, cz + r + 4)


def robot_cafe(bb, tracker, audit):
    """A pastel cafe with a striped awning, tables outside, a big cake sign."""
    x1, z1, x2, z2 = 20, 108, 38, 122
    y0 = max(0, max(hy(x, z) for x in (x1, x2) for z in (z1, z2)))
    bb.fill(x1 - 1, y0 - 3, z1 - 1, x2 + 6, y0, z2 + 1, "minecraft:smooth_quartz")
    top = tier(bb, x1, z1, x2, z2, y0, 1, 6, ["minecraft:pink_terracotta", WHITE], "minecraft:pink_stained_glass", None,
               pilaster=WHITE, top_plate=WHITE, weights=[0.5, 0.5], every=3, pil_every=6, win_h=3)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:smooth_quartz_stairs", parapet="minecraft:pink_concrete")
    furnish(bb, [(x1 + 1, z1 + 1, x2 - 1, z2 - 1)], y0 + 1, 5, ["kitchen"], seed_of("cafe"), tracker, wood="cherry", audit=audit)
    bb.fill(x2, y0 + 1, (z1 + z2) // 2, x2, y0 + 3, (z1 + z2) // 2 + 1, AIR)
    for z in range(z1, z2 + 1):                                    # awning
        bb.set(x2 + 1, y0 + 4, z, "minecraft:pink_wool" if (z // 2) % 2 else "minecraft:white_wool")
        bb.set(x2 + 2, y0 + 4, z, "minecraft:pink_carpet" if (z // 2) % 2 else "minecraft:white_carpet")
    for z in (z1 + 2, z2 - 2):
        bb.set(x2 + 4, y0 + 1, z, "minecraft:cherry_fence")
        bb.set(x2 + 4, y0 + 2, z, "minecraft:pink_carpet")
        bb.set(x2 + 3, y0 + 1, z, st("minecraft:cherry_stairs", "east"))
        bb.set(x2 + 5, y0 + 1, z, st("minecraft:cherry_stairs", "west"))
    bb.fill(x1 + 6, top + 2, z1 - 1, x1 + 12, top + 6, z1 - 1, "minecraft:white_concrete")
    bb.fill(x1 + 7, top + 3, z1 - 1, x1 + 11, top + 3, z1 - 1, PINK)
    bb.fill(x1 + 7, top + 5, z1 - 1, x1 + 11, top + 5, z1 - 1, YELLOW)
    bb.set(x1 + 9, top + 7, z1 - 1, "minecraft:red_concrete")
    return (x1 - 2, z1 - 2, x2 + 7, z2 + 2)


def future_tree(bb, x, z, rng):
    y = hy(x, z)
    h = int(rng.integers(4, 7))
    bb.fill(x, y + 1, z, x, y + h, z, "minecraft:birch_log[axis=y]")
    r = rng.uniform(2.2, 3.2)
    leaf = ("minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]",
            "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]",
            "minecraft:cherry_leaves[distance=7,persistent=true,waterlogged=false]")[int(rng.integers(0, 3))]
    R = int(math.ceil(r))
    bb.fill_where(x - R, y + h - R + 1, z - R, x + R, y + h + R + 1, z + R,
                  lambda X, yy, Z: (X - x) ** 2 + ((yy - y - h - 1) * 1.1) ** 2 + (Z - z) ** 2 <= r * r, leaf, only_empty=True)


def town(bb, rng, tracker, audit):
    taken = []
    pods = [(60, 128, 8, 2, ("living", "kitchen")), (122, 124, 7, 2, ("library", "workshop")),
            (138, 100, 6, 1, ("storage",)), (36, 76, 7, 2, ("workshop", "library")), (58, 26, 6, 1, ("bedroom",)),
            (124, 28, 7, 2, ("library", "living")), (146, 40, 5, 1, ("storage",)), (24, 54, 5, 1, ("kitchen",))]
    accents = [CYAN, PINK, YELLOW, CYAN, PINK, YELLOW, CYAN, PINK]
    for (x, z, r, f, k), ac in zip(pods, accents):
        taken.append(pod_lab(bb, x, z, r, f, tracker, audit, k, accent=ac))
    taken.append(pacifista_factory(bb, tracker, audit))
    taken.append(seraphim_hall(bb, tracker, audit))
    taken.append(robot_cafe(bb, tracker, audit))
    n = 0
    for _ in range(3000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 7 or PLAT(X, Z)[0, 0] > -8 and PLAT(X, Z)[0, 0] < 3:
            continue
        if hy(x, z) > 3 and PLAT(X, Z)[0, 0] <= 3:
            continue
        if PLAT(X, Z)[0, 0] > 3 and np.hypot(x - EX, z - EZ) < ERX + 2:
            continue
        if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
            continue
        name = bb.names[bb.get_region(x, hy(x, z), z, x, hy(x, z), z)[0, 0, 0]] or ""
        if "grass" not in name and "moss" not in name and "podzol" not in name and "dirt" not in name:
            continue
        future_tree(bb, x, z, rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        n += 1
        if n >= 46:
            break
    print("trees:", n)
    return taken


def harbour(bb, rng):
    """A white quay along the north side of the basin with the Thousand Sunny moored, bollards and lights."""
    x, z, rx, rz = HARBOUR
    qz = z - rz + 3
    for xx in range(x - rx + 4, x + rx - 3):
        for zz in range(qz - 3, qz + 1):
            bb.set(xx, 0, zz, "minecraft:smooth_quartz" if zz < qz else "minecraft:cyan_terracotta")
            bb.fill(xx, -6, zz, xx, -1, zz, "minecraft:quartz_bricks")
            bb.fill(xx, 1, zz, xx, 3, zz, AIR)
    for xx in range(x - rx + 6, x + rx - 4, 7):
        bb.set(xx, 1, qz, "minecraft:quartz_pillar[axis=y]" if False else "minecraft:polished_diorite_slab[type=bottom]" if False else "minecraft:diorite_wall")
        bb.set(xx, 1, qz - 3, LIGHT)
    fp = stamp_ship(bb, "thousand_sunny", SUNNY[0], SUNNY[1], water_y=0, rot=0)
    return fp


# ------------------------------------------------------------------ the plateau and the egg
def escalator(bb):
    """A glass tube escalator up the south cliff from the ring road to the plateau top."""
    x = EX - 1
    z_top = EZ + int(PLAT_R * 0.9)
    while PLAT(np.array([[x]]), np.array([[z_top]]))[0, 0] > 1:
        z_top += 1
    z_top -= 2
    for k in range(PLAT_H + 2):
        z = z_top + k
        y = PLAT_H - k
        bb.fill(x - 2, y - 1, z, x + 2, y + 3, z, GLASS)
        bb.fill(x - 1, y, z, x + 1, y + 2, z, AIR)
        bb.fill(x - 1, y - 1, z, x + 1, y - 1, z, st("minecraft:quartz_stairs", "north"))
        bb.set(x - 2, y - 1, z, WHITE)
        bb.set(x + 2, y - 1, z, WHITE)
        if k % 4 == 0:
            bb.set(x, y + 3, z, LIGHT)
        if y - 2 >= 0:
            bb.fill(x - 2, max(0, hy(x, z)), z, x - 2, y - 2, z, WHITE) if k % 6 == 0 else None
            bb.fill(x + 2, max(0, hy(x, z)), z, x + 2, y - 2, z, WHITE) if k % 6 == 0 else None
    bb.fill(x - 1, PLAT_H + 1, z_top - 1, x + 1, PLAT_H + 3, z_top, AIR)
    zb = z_top + PLAT_H + 2
    bb.fill(x - 1, 0, zb, x + 1, 2, zb + 1, AIR)
    bb.fill(x - 2, -1, zb, x + 2, -1, zb + 2, "minecraft:smooth_quartz")


def in_egg(X, Y, Z, grow=0.0):
    dy = Y - EY
    ry = np.where(dy > 0, ERY, ERY * 0.85) + grow
    rx = ERX * (1 - 0.18 * dy / ERY) + grow
    return ((X - EX) ** 2 + (Z - EZ) ** 2) / rx ** 2 + (dy / ry) ** 2 <= 1


def egg(bb, tracker, audit):
    y_lo = EY - int(ERY * 0.85) - 1
    # the flared stalk with an entrance at the foot
    for y in range(PLAT_H + 1, y_lo + 3):
        k = y - PLAT_H
        rr = 6 + 5 * math.exp(-k / 2.5)
        bb.cylinder(EX, y, EZ, int(round(rr)), y, WHITE, hollow=True, thickness=2)
        bb.cylinder(EX, y, EZ, int(round(rr)) - 2, y, AIR)
        if k % 4 == 2:
            bb.ring(EX, y, EZ, int(round(rr)) - 1, int(round(rr)) + 1, y, CYAN)
    bb.cylinder(EX, PLAT_H, EZ, 10, PLAT_H, "minecraft:polished_diorite")
    for k in range(8):                                             # light posts in the egg's shade
        a = k * math.pi / 4 + 0.2
        for rr in (14, 20):
            x, z = round(EX + rr * math.cos(a)), round(EZ + rr * math.sin(a))
            if PLAT(np.array([[x]]), np.array([[z]]))[0, 0] > 1:
                bb.fill(x, PLAT_H + 1, z, x, PLAT_H + 2, z, QUARTZ)
                bb.set(x, PLAT_H + 3, z, LIGHT)
    for gx in range(EX - ERX - 2, EX + ERX + 3, 5):                 # lights set in the ground in the egg's shadow
        for gz in range(EZ - ERX - 2, EZ + ERX + 3, 5):
            x = gx + int(NT.noise(gx, gz, 1131, 1) * 3) - 1
            z = gz + int(NT.noise(gz, gx, 1132, 1) * 3) - 1
            if 11 < math.hypot(x - EX, z - EZ) < ERX + 2 and PLAT(np.array([[x]]), np.array([[z]]))[0, 0] > 1:
                bb.set(x, PLAT_H, z, "minecraft:sea_lantern")
    bb.fill(EX - 1, PLAT_H + 1, EZ + 4, EX + 1, PLAT_H + 3, EZ + 12, AIR)
    # the shell: white below, quartz above the cyan band, window ribbons at every floor, the jagged crack on top
    def shell(X, yy, Z):
        return in_egg(X, yy, Z) & ~in_egg(X, yy, Z, grow=-2)
    x1, x2 = EX - ERX - 3, EX + ERX + 3
    z1, z2 = EZ - ERX - 3, EZ + ERX + 3
    bb.fill_where(x1, y_lo, z1, x2, EY + ERY + 1, z2, lambda X, yy, Z: shell(X, yy, Z) & (yy < EY + 8), WHITE)
    bb.fill_where(x1, y_lo, z1, x2, EY + ERY + 1, z2, lambda X, yy, Z: shell(X, yy, Z) & (yy >= EY + 8), QUARTZ)
    bb.fill_where(x1, EY + 6, z1, x2, EY + 7, z2, lambda X, yy, Z: shell(X, yy, Z), CYAN)
    bb.fill_where(x1, y_lo, z1, x2, EY + ERY + 1, z2, lambda X, yy, Z: in_egg(X, yy, Z, grow=-2), AIR)
    for f in FLOORS:
        bb.fill_where(x1, f + 1, z1, x2, f + 3, z2,
                      lambda X, yy, Z: shell(X, yy, Z) & ((np.arctan2(Z - EZ, X - EX) * 9).astype(int) % 4 != 0), GLASS)
    # jagged crack
    def crack(X, yy, Z):
        a = np.arctan2(Z - EZ, X - EX)
        jag = 3 * np.abs(((a * 7 / math.pi) % 2) - 1) * 2 + 2 * NT.noise((a * 20).astype(int), 0 * X, 1101, 2)
        return yy > CRACK + jag
    bb.fill_where(x1, CRACK, z1, x2, EY + ERY + 2, z2, crack, AIR)
    # floors
    for i, f in enumerate(FLOORS):
        fy = f - 1
        bb.fill_where(x1, fy, z1, x2, fy, z2, lambda X, yy, Z: in_egg(X, yy, Z, grow=-2), PANEL if i else "minecraft:polished_diorite")
    lab_floors(bb, tracker, audit)
    # viewing ring on top at the crack, with a rail
    yv = CRACK
    rr = None
    for k in range(ERX, 0, -1):
        if in_egg(np.array([[EX + k]]), yv, np.array([[EZ]]), grow=-2)[0, 0]:
            rr = k
            break
    bb.fill_where(x1, yv, z1, x2, yv, z2, lambda X, yy, Z: in_egg(X, yy, Z, grow=-2) & ((X - EX) ** 2 + (Z - EZ) ** 2 > (rr - 6) ** 2), PANEL)
    bb.ring(EX, yv + 1, EZ, rr - 7, rr - 6, yv + 1, "minecraft:white_stained_glass")
    for k in range(12):
        t = k * math.pi / 6
        bb.set(round(EX + (rr - 4) * math.cos(t)), yv, round(EZ + (rr - 4) * math.sin(t)), LIGHT)
    # a glass floor over the top lab inside the ring, lit from below the brain
    bb.fill_where(x1, yv, z1, x2, yv, z2, lambda X, yy, Z: (X - EX) ** 2 + (Z - EZ) ** 2 <= (rr - 6) ** 2, "minecraft:white_stained_glass")
    for gx in range(EX - rr, EX + rr + 1, 4):
        for gz in range(EZ - rr, EZ + rr + 1, 4):
            if 2 < math.hypot(gx - EX, gz - EZ) < rr - 6:
                bb.set(gx, yv, gz, LIGHT)
    # elevator: a glass tube with a ladder up the middle from the stalk foot to the viewing deck
    bb.fill(EX - 1, PLAT_H + 1, EZ - 1, EX + 1, yv + 3, EZ + 1, GLASS)
    bb.fill(EX, PLAT_H + 1, EZ, EX, yv + 3, EZ, AIR)
    bb.fill(EX, PLAT_H + 1, EZ, EX, yv + 1, EZ, "minecraft:ladder[facing=south]")
    bb.fill(EX, PLAT_H + 1, EZ - 1, EX, yv + 3, EZ - 1, PANEL)
    for f in FLOORS + (yv + 1,):
        bb.fill(EX, f, EZ + 1, EX, f + 1, EZ + 1, AIR)
    bb.fill(EX, PLAT_H + 1, EZ + 1, EX, PLAT_H + 2, EZ + 1, AIR)
    punk_records(bb, yv)


def lab_floors(bb, tracker, audit):
    kinds = (("workshop", "storage", "workshop", "library"), ("library", "library", "living", "library"),
             ("workshop", "living", "bedroom", "library"))
    for i, f in enumerate(FLOORS):
        rr = None
        for k in range(ERX, 0, -1):
            if in_egg(np.array([[EX + k]]), f + 4, np.array([[EZ]]), grow=-2)[0, 0]:
                rr = k
                break
        hw = int(rr * 0.66)
        wing_floor(bb, EX - hw, EZ - hw, EX + hw, EZ + hw, f, 6, WGLASS if i != 1 else "minecraft:bookshelf",
                   seed_of("egg", i), tracker, kinds[i], corridor="x", cw=3, carpet=(None, "minecraft:cyan_carpet"),
                   keep=((EX - 2, EZ - 2, EX + 2, EZ + 2),), wood="birch", audit=audit, lamp=LIGHT)
        bb.fill(EX - 1, f, EZ - 2, EX + 1, f + 2, EZ + 2, AIR)
        bb.fill(EX - 1, f - 1, EZ - 1, EX + 1, f - 1, EZ + 1, PANEL)
        # consoles round the rim between the rooms and the windows
        for a in range(0, 360, 24):
            t = math.radians(a)
            x, z = round(EX + (rr - 2) * math.cos(t)), round(EZ + (rr - 2) * math.sin(t))
            if bb.get_region(x, f, z, x, f, z)[0, 0, 0] in (0, 1):
                bb.set(x, f, z, PANEL)
                bb.set(x, f + 1, z, LIGHT if a % 48 else "minecraft:white_stained_glass_pane")
        # a ring of light in the ceiling
        bb.ring(EX, f + 6, EZ, hw + 2, hw + 3, f + 6, LIGHT) if i < 2 else None


def punk_records(bb, yv):
    """The great brain over the crack: a lumpy pink mass with folds, on a stem from the viewing deck."""
    cy = yv + 18
    bb.fill(EX, yv + 4, EZ, EX, cy - 5, EZ, "minecraft:iron_bars")
    bb.cylinder(EX, cy - 6, EZ, 1, cy - 6, PINK)
    for side in (-1, 1):
        cx = EX + side * 4
        bb.fill_where(cx - 9, cy - 7, EZ - 10, cx + 9, cy + 9, EZ + 10,
                      lambda X, yy, Z, cx=cx: ((X - cx) / 6.5) ** 2 + ((yy - cy) / 6) ** 2 + ((Z - EZ) / 9) ** 2
                      * (1 - 0.1 * NT.noise(X * 3, Z * 3 + yy, 1111, 2)) <= 1, PINK)
        bb.fill_where(cx - 9, cy - 7, EZ - 10, cx + 9, cy + 9, EZ + 10,
                      lambda X, yy, Z, cx=cx: (((X - cx) / 6.5) ** 2 + ((yy - cy) / 6) ** 2 + ((Z - EZ) / 9) ** 2 <= 1)
                      & (((X - cx) / 6.5) ** 2 + ((yy - cy) / 6) ** 2 + ((Z - EZ) / 9) ** 2 > 0.8)
                      & (np.sin(Z * 0.9 + yy * 0.7) > 0.55), "minecraft:magenta_concrete")
    bb.fill(EX, cy - 6, EZ - 9, EX, cy + 6, EZ + 9, AIR)
    bb.fill(EX, cy - 3, EZ - 6, EX, cy + 2, EZ + 6, "minecraft:magenta_terracotta")
    bb.fill(EX, cy - 2, EZ - 5, EX, cy + 1, EZ + 5, "minecraft:pearlescent_froglight[axis=y]")


def plateau_garden(bb, rng):
    """Flower drifts and round trees on the plateau top round the egg's foot, benches, a path from the escalator."""
    for z in range(EZ + 10, EZ + PLAT_R + 2):
        for x in range(EX - 2, EX + 1):
            if PLAT(np.array([[x]]), np.array([[z]]))[0, 0] > 0:
                bb.set(x, PLAT_H, z, PATH[int(NT.noise(x, z, 1121, 3) * 2.99)][0])
                bb.fill(x, PLAT_H + 1, z, x, PLAT_H + 3, z, AIR)


def design():
    bb = BigBuild(seed=1061, y_min=-14, y_max=EY + ERY + 30)
    tracker = P.PropTracker(1061)
    audit = []
    rng = np.random.default_rng(1061)
    terrain(bb)
    paths(bb, rng)
    taken = town(bb, rng, tracker, audit)
    harbour(bb, rng)
    escalator(bb)
    egg(bb, tracker, audit)
    plateau_garden(bb, rng)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1130, density=0.3, kinds=NT.PLANTS_MEADOW,
              flowers=["minecraft:cornflower", "minecraft:allium", "minecraft:pink_tulip", "minecraft:oxeye_daisy",
                       "minecraft:azure_bluet", "minecraft:lily_of_the_valley"],
              mask=lambda X, Z: land(X, Z) & (np.hypot(X - EX, Z - EZ) > 13))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.npc(EX + 5, FLOORS[-1], EZ + 3, "kizaru", True)
    b.npc(EX - 5, FLOORS[1], EZ + 3, "vegapunk", False)
    b.chest(EX - 5, FLOORS[-1], EZ - 4, "legendary", "south")
    b.chest(EX + 5, FLOORS[0], EZ - 4, "lab", "south")
    b.chest(136, max(0, hy(136, 60)) + 1, 60, "lab", "east")
    for (gx, gz) in ((EX - 8, EZ + 4), (EX + 8, EZ - 4)):
        b.guard(gx, FLOORS[1], gz, "seraphim")
    for (gx, gz) in ((128, 64), (150, 80), (EX, EZ + PLAT_R + 16), (40, 58)):
        b.guard(gx, max(0, hy(gx, gz)) + 1, gz, "pacifista")
    return b, 0
