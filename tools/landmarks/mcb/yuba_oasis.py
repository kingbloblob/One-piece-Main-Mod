"""Yuba v2, redesigned with the Minecraft Builder skill: the dying oasis of Alabasta, the Rebel Army's old headquarters.

Crocodile's sandstorms have buried half of the town: round clay-walled houses with domed roofs, the west side swallowed
by dunes up to the roofs (some only show their domes, others have a trench dug down to the door), dead palms, a
half-buried town wall. In the middle the dry lake bed, cracked and empty, where old Toto keeps digging: his pit goes
down deep with a ladder, and at its bottom water is bubbling up again (the spring Luffy and Toto struck). Toto's tent,
his tools and the old well beside it; Toto's inn (the Straw Hats' night's rest) on the east bank with rooms upstairs; and
east of town the abandoned Rebel Army camp with torn tents, weapon racks, crates, the watchtower and the rebels' flag.
160 x 160. Ground = y 1; the dunes fade out before the site edge. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, palm
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "yuba_oasis"
TITLE = "Yuba Oasis"
CUTS = [3, 8, -4]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
C = 80
TY = 1
LAKE = (78, 82, 22)                 # dry lake bed: centre and radius
PIT = (84, 88)                      # Toto's pit
INN = (108, 70, 124, 84)
CAMP = (118, 102)                   # the rebels' camp centre
ADOBE = ["minecraft:smooth_sandstone", "minecraft:sandstone", "onepiece:alabasta_sandstone_bricks"]
ROOF = ["minecraft:smooth_sandstone", "minecraft:cut_sandstone"]
DUNE = [("minecraft:sand", 0.72), ("minecraft:sandstone", 0.08), ("minecraft:smooth_sandstone", 0.06), ("minecraft:red_sand", 0.03),
        ("minecraft:terracotta", 0.03), ("minecraft:sandstone", 0.08)]
CRACK = [("minecraft:terracotta", 0.3), ("minecraft:packed_mud", 0.25), ("minecraft:brown_terracotta", 0.15), ("minecraft:coarse_dirt", 0.2),
         ("minecraft:mud_bricks", 0.1)]
INN_PAL = dict(walls=["minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:cut_sandstone"], frame="minecraft:cut_sandstone",
               base=["minecraft:sandstone", "minecraft:cut_sandstone", "minecraft:smooth_sandstone"], floor="minecraft:jungle_planks",
               wood="jungle", chimney="minecraft:sandstone", parapet="minecraft:smooth_sandstone")


_OUT = NT.outline(C, C, 67, 8820, wobble=0.08)


def edge_d(X, Z):
    """Distance inside the site's irregular outline (negative outside): the build ends in a round, ragged edge."""
    return _OUT(np.asarray(X, float), np.asarray(Z, float))


def lake_d(X, Z):
    return np.hypot(np.asarray(X, float) - LAKE[0], np.asarray(Z, float) - LAKE[1])


def dune_h(X, Z):
    """Dune sand above the ground: big crescents blown in from the west, light ripples elsewhere, none in the lake bed or
    the camp; capped near the edge so everything rolls down to the site border."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    west = np.clip((96 - X) / 50.0, 0, 1) ** 1.2
    waves = 0.5 + 0.5 * np.sin(X * 0.11 + 2.0 * np.sin(Z * 0.05)) * np.cos(Z * 0.06 + X * 0.02)
    h = 14 * west * (0.45 + 0.55 * waves) + NT.fbm(X, Z, 8810, 20) * 3
    h = h * np.clip((lake_d(X, Z) - LAKE[2] - 2) / 8.0, 0, 1)
    h = h * np.clip((np.hypot(X - CAMP[0], Z - CAMP[1]) - 18) / 10.0, 0, 1) ** 0.5 + 0.0
    cap = 1.6 * (edge_d(X, Z) - 6 - 2 * NT.noise(X, Z, 8811, 9))
    return np.maximum(0, np.minimum(h, cap))


def lake_floor(X, Z):
    d = lake_d(X, Z)
    return np.where(d < LAKE[2], TY - np.round(6 * np.clip(1 - (d / LAKE[2]) ** 2, 0, 1) ** 0.6), TY)


def build_maps():
    X = np.arange(N)[:, None].astype(float)
    Z = np.arange(N)[None, :].astype(float)
    ground = np.where(edge_d(X, Z) < 6, TY - 1, lake_floor(X, Z))
    return ground.astype(int), np.round(dune_h(X, Z)).astype(int)


GROUND, DUNEH = build_maps()


def gy(x, z):
    return int(GROUND[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def top(x, z):
    x, z = min(max(x, 0), N - 1), min(max(z, 0), N - 1)
    return int(GROUND[x, z] + DUNEH[x, z])


def terrain(bb):
    g = lambda X, Z: GROUND[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]
    t = lambda X, Z: g(X, Z) + DUNEH[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]
    inside = lambda X, Z: edge_d(X, Z) > 0
    NT.cover(bb, 0, 0, N - 1, N - 1, g, CRACK, 8813, mask=lambda X, Z: lake_d(X, Z) < LAKE[2], under="minecraft:packed_mud",
             core="minecraft:sandstone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, g, DUNE, 8814, mask=lambda X, Z: (lake_d(X, Z) >= LAKE[2]) & inside(X, Z), under="minecraft:sandstone",
             core="minecraft:sandstone", base=-8)
    # the dry lake bed sits below the build's base level: write air into it, or the sea under a placement stays there
    bb.fill_where(0, TY - 8, 0, N - 1, TY, N - 1, lambda X, Y, Z: (Y > g(X, Z)) & (lake_d(X, Z) < LAKE[2] + 1), AIR, only_empty=True)
    bb.fill_where(0, TY, 0, N - 1, TY + 16, N - 1, lambda X, Y, Z: (Y > g(X, Z)) & (Y < t(X, Z)), "minecraft:sand")
    bb.fill_where(0, TY, 0, N - 1, TY + 16, N - 1, lambda X, Y, Z: (Y > g(X, Z)) & (Y == t(X, Z)) & (NT.noise(X, Z, 8815, 6) < 0.95),
                  "minecraft:sand")
    bb.fill_where(0, TY, 0, N - 1, TY + 16, N - 1, lambda X, Y, Z: (Y > g(X, Z)) & (Y == t(X, Z)) & (NT.noise(X, Z, 8815, 6) >= 0.95),
                  "minecraft:red_sand")


# ------------------------------------------------------------------ round clay houses
def adobe_house(bb, cx, cz, r, h, tracker, audit, k, door_dir, buried):
    """A round clay house: thick walls, a dome roof with a vent, deep window holes with wooden shutters, a door with an
    awning. buried: sand already stands round it; the inside is dug out and a trench leads down to the door, unless the
    house is fully buried (then only the dome shows)."""
    y = TY
    wall = ADOBE[k % len(ADOBE)]
    bb.fill_where(cx - r - 1, y - 3, cz - r - 1, cx + r + 1, y, cz + r + 1, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 0.5,
                  "minecraft:sandstone")
    bb.fill_where(cx - r, y + 1, cz - r, cx + r, y + h, cz + r,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 0.5) & (np.hypot(X - cx, Z - cz) > r - 1.2), wall)
    bb.fill_where(cx - r, y + 1, cz - r, cx + r, y + h + r, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 1.2, AIR)
    bb.fill_where(cx - r - 1, y + h, cz - r - 1, cx + r + 1, y + h + r + 1, cz + r + 1,
                  lambda X, Y, Z: (np.hypot(np.hypot(X - cx, Z - cz), (Y - y - h) * 1.25) <= r + 0.6) &
                  (np.hypot(np.hypot(X - cx, Z - cz), (Y - y - h) * 1.25) > r - 0.6) & (Y >= y + h), ROOF[k % 2])
    bb.fill_where(cx - r - 1, y + h, cz - r - 1, cx + r + 1, y + h, cz + r + 1,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 1.5) & (np.hypot(X - cx, Z - cz) > r + 0.5), "minecraft:cut_sandstone_slab[type=bottom]")
    bb.fill_where(cx - r, y, cz - r, cx + r, y, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.5, "minecraft:jungle_planks")
    dx, dz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[door_dir]
    if buried == 2:
        return
    # door with an awning
    px, pz = cx + dx * r, cz + dz * r
    bb.fill(px, y + 1, pz, px - dx * 1, y + 3, pz - dz * 1, AIR)
    bb.set(px, y + 1, pz, f"minecraft:jungle_door[facing={door_dir},half=lower,hinge=left]")
    bb.set(px, y + 2, pz, f"minecraft:jungle_door[facing={door_dir},half=upper,hinge=left]")
    ox, oz = (1, 0) if dz else (0, 1)
    for s in (-1, 0, 1):
        bb.set(px + dx + ox * s, y + 4, pz + dz + oz * s, ("minecraft:white_wool", "minecraft:orange_wool")[(s + k) % 2])
    for s in (-1, 1):
        bb.fill(px + dx * 2 + ox * s, y + 1, pz + dz * 2 + oz * s, px + dx * 2 + ox * s, y + 3, pz + dz * 2 + oz * s, "minecraft:jungle_fence")
    # windows: deep holes with an open shutter, at the other three sides
    for (wx, wz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        if (wx, wz) == (dx, dz):
            continue
        bx, bz = cx + wx * r, cz + wz * r
        bb.set(bx, y + 2, bz, AIR)
        bb.set(bx - wx, y + 2, bz - wz, AIR)
        bb.set(bx, y + 3, bz, f"minecraft:jungle_trapdoor[facing={f},half=top,open=true]") if buried == 0 else None
    # inside: one room in the square that fits the circle
    q = int((r - 1.2) / 1.42)
    room = (cx - q, cz - q, cx + q, cz + q)
    P.furnish_room(bb, room, y + 1, ("bedroom", "kitchen", "living", "storage", "dining")[k % 5], height=h - 1, seed=seed_of("yb", k),
                   doors=[(px - dx, pz - dz)], wood="jungle", tracker=tracker)
    txt, ok = P.audit_props(bb, [room], y + 1, h - 1)
    if not ok:
        audit.append(txt)
    bb.set(cx, y + h + r - 1, cz, "minecraft:lantern[hanging=true]")
    if buried == 1:
        # trench through the sand to the door, with sandstone steps
        for i in range(1, 16):
            tx, tz = px + dx * i, pz + dz * i
            if tx < 1 or tz < 1 or tx > N - 2 or tz > N - 2:
                break
            tt = top(tx, tz)
            floor = min(tt, y + (i - 2) // 1) if i > 2 else y
            for s in (-1, 0, 1):
                bb.fill(tx + ox * s, floor + 1, tz + oz * s, tx + ox * s, y + 16, tz + oz * s, AIR)
                bb.set(tx + ox * s, floor, tz + oz * s, "minecraft:smooth_sandstone")
            if floor >= tt:
                break


def town(bb, tracker, audit, rng, taken):
    spots = []
    k = 0
    for _ in range(4000):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(LAKE[2] + 10, 58)
        cx, cz = int(LAKE[0] + rr * math.cos(a)), int(LAKE[1] + rr * math.sin(a))
        r = int(rng.integers(4, 7))
        if edge_d(np.array([cx]), np.array([cz]))[0] < r + 12:
            continue
        box = (cx - r - 3, cz - r - 3, cx + r + 3, cz + r + 3)
        if any(box[0] <= t[2] and t[0] <= box[2] and box[1] <= t[3] and t[1] <= box[3] for t in taken):
            continue
        dune = DUNEH[cx, cz]
        h = 5 if r < 6 else 6
        buried = 2 if dune >= h + 2 else 1 if dune >= 3 else 0
        # doors face the lake
        ang = math.atan2(LAKE[1] - cz, LAKE[0] - cx)
        door = ("east", "south", "west", "north")[int(round(ang / (math.pi / 2))) % 4]
        adobe_house(bb, cx, cz, r, h, tracker, audit, k, door, buried)
        taken.append(box)
        k += 1
        if k >= 22:
            break
    print("houses:", k)


# ------------------------------------------------------------------ the lake bed, Toto, the inn, the camp
def toto(bb, tracker):
    px, pz = PIT
    y = gy(px, pz)
    bot = y - 14
    bb.fill_where(px - 4, bot, pz - 4, px + 4, y + 2, pz + 4, lambda X, Y, Z: np.hypot(X - px, Z - pz) <= 3.6, "minecraft:packed_mud")
    bb.fill_where(px - 4, bot + 1, pz - 4, px + 4, y + 3, pz + 4, lambda X, Y, Z: np.hypot(X - px, Z - pz) <= 2.6, AIR)
    bb.fill_where(px - 4, bot, pz - 4, px + 4, bot, pz + 4, lambda X, Y, Z: np.hypot(X - px, Z - pz) <= 2.6, "minecraft:mud")
    bb.fill(px - 1, bot + 1, pz - 1, px, bot + 1, pz, "minecraft:water")
    bb.fill(px + 2, bot + 1, pz, px + 2, y, pz, "minecraft:ladder[facing=west]")
    for yy in range(bot + 2, y, 4):
        bb.set(px - 2, yy, pz - 1, "minecraft:lantern[hanging=false]") if False else None
    bb.set(px - 2, bot + 1, pz + 1, "minecraft:lantern[hanging=false]")
    # spoil heap and tools at the rim
    bb.fill_where(px + 4, y, pz - 6, px + 10, y + 3, pz + 2, lambda X, Y, Z: (X - px - 7) ** 2 + ((Y - y) * 1.8) ** 2 + (Z - pz + 2) ** 2 <= 12,
                  "minecraft:coarse_dirt")
    bb.set(px - 4, y + 1, pz + 3, "minecraft:barrel[facing=up,open=false]")
    bb.set(px - 5, y + 1, pz + 3, "minecraft:composter")
    bb.set(px - 4, y + 1, pz + 4, "minecraft:grindstone[face=floor,facing=north]")
    # Toto's tent: canvas on poles, a bedroll, a water jug, a lantern
    tx, tz = px - 10, pz - 2
    for i in range(4):
        bb.fill(tx - 3 + i, y + 1 + i, tz, tx - 3 + i, y + 1 + i, tz + 5, "minecraft:white_wool")
        bb.fill(tx + 3 - i, y + 1 + i, tz, tx + 3 - i, y + 1 + i, tz + 5, "minecraft:white_wool")
    bb.fill(tx - 2, y + 1, tz + 5, tx + 2, y + 3, tz + 5, "minecraft:brown_wool")
    bb.set(tx, y + 1, tz + 5, "minecraft:brown_wool")
    bb.set(tx - 1, y + 1, tz + 2, "minecraft:light_gray_carpet")
    bb.set(tx + 1, y + 1, tz + 3, "minecraft:decorated_pot")
    bb.set(tx + 1, y + 1, tz + 1, "minecraft:lantern[hanging=false]")
    # the old well: a stone ring with a roof, dry
    wx, wz = px - 6, pz + 9
    wy = gy(wx, wz)
    bb.fill_where(wx - 2, wy - 8, wz - 2, wx + 2, wy + 1, wz + 2, lambda X, Y, Z: (np.hypot(X - wx, Z - wz) <= 2.2) & (np.hypot(X - wx, Z - wz) > 1),
                  "minecraft:sandstone")
    bb.fill(wx, wy - 7, wz, wx, wy + 1, wz, AIR)
    for (a, b) in ((wx - 2, wz), (wx + 2, wz)):
        bb.fill(a, wy + 2, b, a, wy + 4, b, "minecraft:jungle_fence")
    bb.fill(wx - 2, wy + 5, wz - 1, wx + 2, wy + 5, wz + 1, "minecraft:jungle_slab[type=bottom]")
    bb.fill(wx - 1, wy + 4, wz, wx + 1, wy + 4, wz, "minecraft:jungle_log[axis=x]")
    bb.set(wx, wy + 3, wz, "minecraft:iron_chain[axis=y]")
    return (px - 14, pz - 8, px + 11, pz + 13)


def inn(bb, tracker, audit):
    x1, z1, x2, z2 = INN
    w, d = x2 - x1 + 1, z2 - z1 + 1
    m, topy, au = house_module(seed_of("inn"), d, w, 2, "flat:orange", tracker, ["dining", "bedroom"], pal=INN_PAL, timber=False,
                               jetty=False, chimney=False)
    audit += au
    y = TY
    bb.fill(x1, y - 3, z1, x2, y, z2, "minecraft:sandstone")
    place_house(bb, m, d, w, x1, y, z1, 1)              # door west, to the lake
    return (x1 - 3, z1 - 2, x2 + 2, z2 + 2)


def camp(bb, rng):
    cx, cz = CAMP
    y = TY
    # torn tents
    for i, (tx, tz) in enumerate(((cx - 10, cz - 8), (cx + 2, cz - 12), (cx + 10, cz - 2), (cx - 6, cz + 6), (cx + 6, cz + 9))):
        ty = top(tx, tz)
        cloth = ("minecraft:white_wool", "minecraft:light_gray_wool", "minecraft:brown_wool")[i % 3]
        for k in range(3):
            for z in range(tz, tz + 5):
                if rng.random() < 0.85:
                    bb.set(tx - 2 + k, ty + 1 + k, z, cloth)
                if rng.random() < 0.85:
                    bb.set(tx + 2 - k, ty + 1 + k, z, cloth)
        bb.fill(tx, ty + 1, tz - 1, tx, ty + 4, tz - 1, "minecraft:jungle_fence")
        bb.set(tx - 1, ty + 1, tz + 2, "minecraft:white_carpet")
    # weapon racks and crates
    for (x, z) in ((cx - 2, cz - 2), (cx - 1, cz - 2), (cx, cz - 2), (cx + 1, cz - 2)):
        bb.set(x, top(x, z) + 1, z, "minecraft:jungle_fence")
        bb.set(x, top(x, z) + 2, z, "minecraft:grindstone[face=floor,facing=south]" if x % 2 else "minecraft:jungle_fence")
    for (x, z) in ((cx + 3, cz + 1), (cx + 4, cz + 1), (cx + 3, cz + 2), (cx - 4, cz + 2)):
        bb.set(x, top(x, z) + 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.set(cx + 3, top(cx + 3, cz + 1) + 2, cz + 1, "minecraft:barrel[facing=up,open=false]")
    bb.set(cx, top(cx, cz) + 1, cz + 2, "minecraft:campfire[lit=false,signal_fire=false]")
    # the watchtower, one leg broken
    wx, wz = cx + 14, cz + 8
    wy = top(wx, wz)
    for (a, b) in ((wx - 2, wz - 2), (wx + 2, wz - 2), (wx - 2, wz + 2)):
        bb.fill(a, wy - 2, b, a, wy + 10, b, "minecraft:jungle_log[axis=y]")
    bb.fill(wx + 2, wy - 2, wz + 2, wx + 2, wy + 4, wz + 2, "minecraft:jungle_log[axis=y]")
    bb.fill(wx - 2, wy + 10, wz - 2, wx + 2, wy + 10, wz + 2, "minecraft:jungle_planks")
    bb.fill(wx + 1, wy + 10, wz + 1, wx + 2, wy + 10, wz + 2, AIR)
    for x in range(wx - 2, wx + 3):
        bb.set(x, wy + 11, wz - 2, "minecraft:jungle_fence")
    bb.fill(wx - 1, wy + 1, wz - 2, wx - 1, wy + 9, wz - 2, "minecraft:ladder[facing=south]")
    # the rebels' flag: a white flag with the green rebel sign
    fx, fz = cx - 2, cz + 12
    fy = top(fx, fz)
    bb.fill(fx, fy + 1, fz, fx, fy + 12, fz, "minecraft:jungle_fence")
    for r in range(5):
        for c in range(7):
            bb.set(fx, fy + 12 - r, fz + 1 + c, "minecraft:green_wool" if (r in (1, 3) and 1 <= c <= 5) or c == 3 else "minecraft:white_wool")
    return (cx - 16, cz - 16, cx + 18, cz + 16)


def town_wall(bb):
    """The old wall round the town: mud-brick, crumbling, half under the dunes on the west."""
    rng = np.random.default_rng(8830)
    for a in range(0, 360):
        t = math.radians(a)
        x, z = int(round(LAKE[0] + 64 * math.cos(t))), int(round(LAKE[1] + 60 * math.sin(t)))
        if edge_d(np.array([x]), np.array([z]))[0] < 10 or 330 < a or a < 30:
            continue
        hgt = 3 + int(2 * NT.noise(np.array([x]), np.array([z]), 8831, 7)[0] * 3)
        bb.fill(x, TY - 1, z, x, TY + hgt, z, "minecraft:mud_bricks" if rng.random() < 0.7 else "minecraft:sandstone")


def design():
    bb = BigBuild(seed=8810, y_min=-18, y_max=50)
    tracker = P.PropTracker(8810)
    audit = []
    rng = np.random.default_rng(8810)
    terrain(bb)
    town_wall(bb)
    taken = [toto(bb, tracker), inn(bb, tracker, audit), camp(bb, rng), (LAKE[0] - LAKE[2] - 3, LAKE[1] - LAKE[2] - 3,
                                                                          LAKE[0] + LAKE[2] + 3, LAKE[1] + LAKE[2] + 3)]
    town(bb, tracker, audit, rng, taken)
    # dead palms
    k = 0
    for _ in range(2000):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken) and not (abs(lake_d(np.array([x]), np.array([z]))[0] - LAKE[2]) < 3):
            continue
        y = top(x, z) + 1
        h = int(rng.integers(5, 10))
        lean = ((1, 0), (0, 1), (-1, 0), (0, -1))[k % 4]
        for i in range(h):
            bb.set(x + lean[0] * (i // 4), y + i, z + lean[1] * (i // 4), "minecraft:stripped_jungle_log[axis=y]")
        tx, tz = x + lean[0] * ((h - 1) // 4), z + lean[1] * ((h - 1) // 4)
        for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(tx + ox, y + h - 1, tz + oz, "minecraft:dead_bush") if False else bb.set(tx + ox, y + h - 1, tz + oz, "minecraft:stripped_jungle_log[axis=x]" if ox else "minecraft:stripped_jungle_log[axis=z]")
        bb.set(tx, y + h, tz, "minecraft:dead_bush") if False else None
        taken.append((x - 2, z - 2, x + 2, z + 2))
        k += 1
        if k >= 24:
            break
    NT.plants(bb, 0, 0, N - 1, N - 1, lambda X, Z: GROUND[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] +
              DUNEH[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)], 8890, density=0.04,
              kinds=["minecraft:dead_bush"], flowers=(), mask=lambda X, Z: lake_d(X, Z) > LAKE[2])
    return bb, audit


def steady(b):
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    x1, z1, x2, z2 = INN
    b.chest(x2 - 2, TY + 1, z1 + 2, "easy", "west")
    b.chest(CAMP[0] + 4, top(CAMP[0] + 4, CAMP[1] + 2) + 1, CAMP[1] + 2, "easy", "west")
    return b, 0
