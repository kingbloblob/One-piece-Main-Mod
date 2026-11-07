"""Weatheria v2, redesigned with the Minecraft Builder skill: the sky island of weather science where Nami trained
with old Haredas during the time skip.

A cluster of cloud islets floating high above the sea, each a round bowl of island cloud with a mossy top, held
together by sagging chains and plank rope bridges. Every islet carries round domed buildings in white with sky-blue
bands and roofs, ribbed domes and weathervanes. The main islet: the Weather Library (a big two-floor rotunda lined
with bookshelves round a reading floor), Haredas' laboratory (cauldrons, brewing stands, the weather-ball bench) and
the observatory tower with the great weathervane, a gallery and a telescope at the top. Smaller islets hold the
scientists' houses with bedrooms and a kitchen, the kitchen garden and the weather-ball launch pad. Weather balls
(round white, blue and yellow balloons) float everywhere on tethers. ~140 x 140, floats at a fixed height
(canvas y 0 = world y 168). (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "weatheria"
TITLE = "Weatheria (weather science island)"
CUTS = [2, 9, 20]
TILER = dict(terrain="none", sky_y=168)

N = 140
CLOUD = "onepiece:island_cloud"
PUFF = "onepiece:cloud_puff"
MOSS = "onepiece:cloud_moss"
SHRUB = "onepiece:cloud_shrub"
WALL = ["minecraft:white_concrete", "minecraft:white_terracotta", "minecraft:calcite"]
BAND = "minecraft:light_blue_terracotta"
DOME = "minecraft:light_blue_concrete"
RIB = "minecraft:white_concrete"
GLASS = "minecraft:light_blue_stained_glass_pane"
# islets: centre x, z, radius, top y
ISLES = [(70, 70, 26, 0), (28, 40, 13, 3), (108, 34, 14, -2), (116, 92, 15, 2), (32, 104, 14, -3), (72, 120, 11, 4), (66, 20, 10, 5)]
BRIDGES = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 6), (3, 5)]


def isle_top(i):
    return ISLES[i][3]


def islets(bb, rng):
    for i, (cx, cz, r, ty) in enumerate(ISLES):
        out = NT.outline(cx, cz, r, 9300 + i, wobble=0.1)
        # the cloud bowl: deeper in the middle, puffy underneath
        bb.fill_where(cx - r - 6, ty - r, cz - r - 6, cx + r + 6, ty - 1, cz + r + 6,
                      lambda X, Y, Z: (out(X, Z) > 0) & (Y >= ty - 1 - np.sqrt(np.maximum(out(X, Z), 0)) * (2.2 + 0.6 * NT.noise(X, Z, 9310 + i, 5))),
                      CLOUD)
        bb.fill_where(cx - r - 6, ty, cz - r - 6, cx + r + 6, ty, cz + r + 6,
                      lambda X, Y, Z: (out(X, Z) > 0), CLOUD)
        bb.fill_where(cx - r - 6, ty, cz - r - 6, cx + r + 6, ty, cz + r + 6,
                      lambda X, Y, Z: (out(X, Z) > 3) & (NT.noise(X, Z, 9320 + i, 4) > 0.72), "minecraft:grass_block")
        # puffs round the rim and hanging below
        for _ in range(int(r * 1.4)):
            a = rng.uniform(0, 2 * math.pi)
            rr = r * rng.uniform(0.85, 1.05)
            px, pz = int(cx + rr * math.cos(a)), int(cz + rr * math.sin(a))
            py = ty - int(rng.integers(1, 5))
            pr = float(rng.uniform(1.8, 3.4))
            bb.fill_where(px - 4, py - 3, pz - 4, px + 4, py + 3, pz + 4,
                          lambda X, Y, Z, px=px, py=py, pz=pz, pr=pr: ((X - px) ** 2 + ((Y - py) * 1.6) ** 2 + (Z - pz) ** 2) <= pr * pr, PUFF,
                          only_empty=True)
        for _ in range(int(r * 0.6)):
            px, pz = cx + int(rng.integers(-r // 2, r // 2 + 1)), cz + int(rng.integers(-r // 2, r // 2 + 1))
            py = ty - int(r * 0.9) - int(rng.integers(0, 4))
            pr = float(rng.uniform(2, 4))
            bb.fill_where(px - 5, py - 4, pz - 5, px + 5, py + 4, pz + 5,
                          lambda X, Y, Z, px=px, py=py, pz=pz, pr=pr: ((X - px) ** 2 + ((Y - py) * 1.4) ** 2 + (Z - pz) ** 2) <= pr * pr, PUFF,
                          only_empty=True)


def rotunda(bb, cx, cz, y, r, floors, fh, tracker, audit, kinds, door="south", wood="birch", vane=True):
    """A round domed building: white walls with sky-blue bands, ring of windows each floor, ribbed blue dome,
    weathervane. Floors furnished on the inscribed square. Returns the dome top y."""
    H = floors * (fh + 1)
    bb.fill_where(cx - r - 1, y - 1, cz - r - 1, cx + r + 1, y - 1, cz + r + 1, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 1.3,
                  "minecraft:smooth_quartz")
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 0.4, WALL[0])
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 0.4) & (NT.noise(X + Y * 2, Z, 9330, 3) > 0.7), WALL[2])
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.8, AIR)
    for f in range(floors):
        fy = y + f * (fh + 1)
        bb.fill_where(cx - r, fy, cz - r, cx + r, fy, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.8, f"minecraft:{wood}_planks")
        bb.fill_where(cx - r, fy + fh, cz - r, cx + r, fy + fh, cz + r,
                      lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 0.4) & (np.hypot(X - cx, Z - cz) > r - 0.8), BAND)
        # windows round the wall
        n = max(6, int(r * 1.2))
        for k in range(n):
            a = 2 * math.pi * k / n
            wx, wz = cx + int(round(r * math.cos(a))), cz + int(round(r * math.sin(a)))
            bb.fill(wx, fy + 2, wz, wx, fy + 3, wz, GLASS)
    # floors between storeys get a ladder hole
    for f in range(1, floors):
        fy = y + f * (fh + 1)
        bb.fill(cx - r + 2, fy, cz, cx - r + 2, fy, cz, AIR)
        bb.fill(cx - r + 2, y + (f - 1) * (fh + 1) + 1, cz, cx - r + 2, fy, cz, "minecraft:ladder[facing=east]")
    # door
    dx, dz = {"south": (0, r), "north": (0, -r), "east": (r, 0), "west": (-r, 0)}[door]
    bb.fill(cx + dx, y + 1, cz + dz, cx + dx, y + 2, cz + dz, AIR)
    bb.set(cx + dx, y + 1, cz + dz, f"minecraft:{wood}_door[facing={door},half=lower,hinge=left]")
    bb.set(cx + dx, y + 2, cz + dz, f"minecraft:{wood}_door[facing={door},half=upper,hinge=left]")
    sx, sz = (1 if dx else 0) * (1 if dx > 0 else -1), (1 if dz else 0) * (1 if dz > 0 else -1)
    bb.set(cx + dx + sx, y, cz + dz + sz, "minecraft:smooth_quartz_slab[type=top]")
    bb.set(cx + dx + sx + (sz != 0), y + 3, cz + dz + sz + (sx != 0), "minecraft:lantern[hanging=false]") if False else None
    # furnish each floor on the inscribed square
    q = int((r - 1) / 1.42)
    for f in range(floors):
        fy = y + f * (fh + 1) + 1
        room = (cx - q, cz - q, cx + q, cz + q)
        doors = [(cx + dx - sx * 1, cz + dz - sz * 1)] if f == 0 else [(cx - r + 2, cz)]
        P.furnish_room(bb, room, fy, kind=kinds[f % len(kinds)], height=fh, seed=seed_of("rot", cx, cz, f), wood=wood, tracker=tracker,
                       doors=doors)
        txt, ok = P.audit_props(bb, [room], fy, fh)
        if not ok:
            audit.append(txt)
    # the dome: blue with white ribs, a lantern ring at the base
    top = y + H
    R = r + 0.4
    bb.fill_where(cx - r - 1, top, cz - r - 1, cx + r + 1, top + r + 1, cz + r + 1,
                  lambda X, Y, Z: (((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - top) / (R * 0.75)) ** 2 <= 1) &
                                  (((X - cx) ** 2 + (Z - cz) ** 2) / (R - 1.2) ** 2 + ((Y - top) / (R * 0.75 - 1.2)) ** 2 > 1), DOME)
    bb.fill_where(cx - r - 1, top, cz - r - 1, cx + r + 1, top + r + 1, cz + r + 1,
                  lambda X, Y, Z: (((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - top) / (R * 0.75)) ** 2 <= 1) &
                                  (((X - cx) ** 2 + (Z - cz) ** 2) / (R - 1.2) ** 2 + ((Y - top) / (R * 0.75 - 1.2)) ** 2 > 1) &
                                  ((np.abs(X - cx) <= 0) | (np.abs(Z - cz) <= 0) | (np.abs(np.abs(X - cx) - np.abs(Z - cz)) <= 0)), RIB)
    dtop = top + int(R * 0.75)
    bb.fill_where(cx - r - 1, top, cz - r - 1, cx + r + 1, top, cz + r + 1,
                  lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - (r + 1.2)) < 0.6, "minecraft:smooth_quartz_slab[type=bottom]")
    if vane:
        weathervane(bb, cx, dtop + 1, cz, 4)
    return dtop


def weathervane(bb, x, y, z, h):
    bb.fill(x, y, z, x, y + h, z, "minecraft:iron_bars")
    bb.set(x, y + h + 1, z, "minecraft:lightning_rod")
    for i in range(-2, 3):
        bb.set(x + i, y + h - 1, z, "minecraft:iron_bars" if i else "minecraft:iron_bars")
    bb.set(x + 3, y + h - 1, z, "minecraft:light_blue_stained_glass_pane")
    bb.fill(x - 3, y + h - 2, z, x - 3, y + h, z, "minecraft:iron_bars")
    bb.set(x, y + 1, z + 1, "minecraft:copper_bulb[lit=false]") if False else None


def observatory(bb, cx, cz, y, tracker, audit):
    """The tall tower: a slim round shaft with a ladder, a gallery, the lens room and the great weathervane."""
    r = 5
    H = 42
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 0.4, WALL[0])
    bb.fill_where(cx - r, y, cz - r, cx + r, y + H, cz + r,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r + 0.4) & ((Y - y) % 8 == 7), BAND)
    bb.fill_where(cx - r, y + 1, cz - r, cx + r, y + H, cz + r, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r - 0.8, AIR)
    bb.fill(cx, y + 1, cz + r - 1, cx, y + H, cz + r - 1, "minecraft:ladder[facing=north]")
    for yy in range(y + 4, y + H - 4, 6):
        for (dx, dz) in ((r, 0), (-r, 0), (0, -r)):
            bb.fill(cx + dx, yy, cz + dz, cx + dx, yy + 1, cz + dz, GLASS)
        bb.fill_where(cx - r, yy + 3, cz - r, cx + r, yy + 3, cz + r,
                      lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r - 0.8) & (np.abs(X - cx) + np.abs(Z - cz - (r - 1)) > 1), "minecraft:birch_slab[type=top]")
    bb.fill(cx, y + 1, cz - r, cx, y + 2, cz - r, AIR)
    bb.set(cx, y + 1, cz - r, "minecraft:birch_door[facing=north,half=lower,hinge=left]")
    bb.set(cx, y + 2, cz - r, "minecraft:birch_door[facing=north,half=upper,hinge=left]")
    # the gallery round the lens room
    gy = y + H
    bb.fill_where(cx - r - 3, gy, cz - r - 3, cx + r + 3, gy, cz + r + 3, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= r + 2.6, "minecraft:smooth_quartz")
    bb.fill_where(cx - r - 3, gy + 1, cz - r - 3, cx + r + 3, gy + 1, cz + r + 3,
                  lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - (r + 2.3)) < 0.6, "minecraft:white_stained_glass_pane")
    bb.fill(cx, gy, cz + r - 1, cx, gy, cz + r - 1, AIR)
    # the lens room: glass drum with the telescope
    bb.fill_where(cx - r, gy + 1, cz - r, cx + r, gy + 6, cz + r, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - (r - 0.3)) < 0.7, "minecraft:glass")
    bb.fill(cx, gy + 1, cz - r + 1, cx, gy + 2, cz - r + 1, AIR) if False else None
    bb.set(cx - 1, gy + 1, cz, "minecraft:birch_fence")
    bb.set(cx - 1, gy + 2, cz, "minecraft:lightning_rod[facing=north]")
    bb.set(cx - 1, gy + 3, cz - 1, "minecraft:end_rod[facing=north]")
    bb.set(cx + 2, gy + 1, cz - 1, "minecraft:cartography_table")
    bb.set(cx + 2, gy + 1, cz + 1, "minecraft:lectern[facing=west]")
    top = rotunda_cap(bb, cx, cz, gy + 7, r)
    weathervane(bb, cx, top + 1, cz, 7)


def rotunda_cap(bb, cx, cz, y, r):
    R = r + 0.6
    bb.fill_where(cx - r - 1, y, cz - r - 1, cx + r + 1, y + r + 2, cz + r + 1,
                  lambda X, Y, Z: ((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - y) / (R * 1.2)) ** 2 <= 1, DOME)
    bb.fill_where(cx - r - 1, y, cz - r - 1, cx + r + 1, y, cz + r + 1, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= R, RIB)
    return y + int(R * 1.2)


def library(bb, cx, cz, y, tracker, audit):
    """The Weather Library: a big two-floor rotunda, bookshelf walls, a gallery floor round an open well."""
    r = 13
    top = rotunda(bb, cx, cz, y, r, 2, 6, tracker, audit, ["library", "library"], door="south", wood="birch")
    # open well in the upper floor, rails round it, shelves on the walls of both floors
    bb.fill_where(cx - 6, y + 7, cz - 6, cx + 6, y + 7, cz + 6, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 5.2, AIR)
    bb.fill_where(cx - 7, y + 8, cz - 7, cx + 7, y + 8, cz + 7, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - 5.8) < 0.6, "minecraft:birch_fence")
    for fy in (y + 1, y + 8):
        bb.fill_where(cx - r, fy, cz - r, cx + r, fy + 2, cz + r,
                      lambda X, Y, Z: (np.abs(np.hypot(X - cx, Z - cz) - (r - 1.3)) < 0.6) & (NT.noise(X, Z, 9340, 2) < 0.8), "minecraft:bookshelf")
    # reading tables in the well
    for (dx, dz) in ((-2, 0), (2, 0)):
        bb.set(cx + dx, y + 1, cz + dz, "minecraft:birch_fence")
        bb.set(cx + dx, y + 2, cz + dz, "minecraft:light_blue_carpet")
    bb.set(cx, y + 1, cz - 2, "minecraft:lectern[facing=south]")
    bb.set(cx, y + 1, cz + 2, "minecraft:enchanting_table") if False else None
    # big globe of the skies hanging in the well
    bb.fill(cx, y + 10, cz, cx, top - 2, cz, "minecraft:iron_chain[axis=y]")
    bb.fill_where(cx - 2, y + 6, cz - 2, cx + 2, y + 9, cz + 2, lambda X, Y, Z: (X - cx) ** 2 + (Y - (y + 8)) ** 2 + (Z - cz) ** 2 <= 2.5,
                  "minecraft:light_blue_stained_glass")
    bb.set(cx, y + 8, cz, "minecraft:sea_lantern")
    # clear the doorway through the shelves
    bb.fill(cx, y + 1, cz + r - 1, cx, y + 2, cz + r - 1, AIR)
    bb.fill(cx - r + 2, y + 1, cz, cx - r + 1, y + 3, cz, AIR) if False else None


def haredas_lab(bb, cx, cz, y, tracker, audit):
    r = 8
    rotunda(bb, cx, cz, y, r, 1, 6, tracker, audit, ["workshop"], door="east", wood="birch")
    for (dx, dz, s) in ((-3, -3, "minecraft:brewing_stand"), (-3, 3, "minecraft:cauldron"), (3, -4, "minecraft:cauldron"),
                        (0, -5, "minecraft:smithing_table"), (-5, 0, "minecraft:barrel[facing=up,open=false]")):
        set_if_air(bb, cx + dx, y + 1, cz + dz, s)
    # the weather-ball bench: little balls on the table
    bb.fill(cx - 1, y + 1, cz + 4, cx + 2, y + 1, cz + 4, "minecraft:birch_slab[type=top]")
    for x, c in ((cx - 1, "white"), (cx, "light_blue"), (cx + 1, "yellow"), (cx + 2, "light_gray")):
        bb.set(x, y + 2, cz + 4, f"minecraft:{c}_carpet")


def weather_ball(bb, x, y, z, color, r=2.2, ground=None):
    bb.fill_where(x - 3, y - 3, z - 3, x + 3, y + 3, z + 3, lambda X, Y, Z: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r,
                  f"minecraft:{color}_wool", only_empty=True)
    bb.set(x, y + int(r) + 1, z, "minecraft:white_wool") if False else None
    if ground is not None:
        for yy in range(ground + 1, y - int(r)):
            set_if_air(bb, x, yy, z, "minecraft:iron_chain[axis=y]")


def bridges(bb):
    for (a, b) in BRIDGES:
        ax, az, ar, ay = ISLES[a]
        bx, bz, br, by = ISLES[b]
        d = math.hypot(bx - ax, bz - az)
        ux, uz = (bx - ax) / d, (bz - az) / d
        s0, s1 = ar - 3, d - br + 3
        n = int(s1 - s0) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            s = s0 + (s1 - s0) * t
            x, z = ax + ux * s, az + uz * s
            y = int(round(ay + (by - ay) * t - 3 * math.sin(t * math.pi)))
            px, pz = -uz, ux
            for k in (-1, 0, 1):
                xx, zz = int(round(x + px * k)), int(round(z + pz * k))
                set_if_air(bb, xx, y, zz, "minecraft:spruce_slab[type=top]" if k == 0 or i % 5 else "minecraft:spruce_slab[type=top]")
            for k in (-2, 2):
                xx, zz = int(round(x + px * k)), int(round(z + pz * k))
                set_if_air(bb, xx, y + 1, zz, "minecraft:spruce_fence" if i % 4 == 0 else "minecraft:iron_chain[axis=y]" if False else "minecraft:spruce_fence")
        # a heavy chain beside the bridge (what really holds the islets together)
        for i in range(n):
            t = i / max(1, n - 1)
            s = s0 + (s1 - s0) * t
            x, z = ax + ux * s + (-uz) * 4, az + uz * s + ux * 4
            y = int(round(ay - 4 + (by - ay) * t - 5 * math.sin(t * math.pi)))
            set_if_air(bb, int(round(x)), y, int(round(z)), "minecraft:iron_chain[axis=x]" if abs(ux) > abs(uz) else "minecraft:iron_chain[axis=z]")


def garden(bb, cx, cz, y):
    for i, (dx, dz) in enumerate(((-6, -5), (1, -5), (-6, 2), (1, 2))):
        x0, z0 = cx + dx, cz + dz
        bb.fill(x0 - 1, y, z0 - 1, x0 + 5, y, z0 + 4, "minecraft:birch_planks")
        bb.fill(x0, y, z0, x0 + 4, y, z0 + 3, "minecraft:farmland[moisture=7]")
        bb.set(x0 + 2, y, z0 + 1, "minecraft:water")
        crop = ("minecraft:carrots[age=7]", "minecraft:wheat[age=6]", "minecraft:potatoes[age=7]", "minecraft:beetroots[age=3]")[i]
        for x in range(x0, x0 + 5):
            for z in range(z0, z0 + 4):
                if (x, z) != (x0 + 2, z0 + 1):
                    bb.set(x, y + 1, z, crop)
    bb.set(cx - 1, y + 1, cz - 8, "minecraft:composter")
    bb.set(cx + 1, y + 1, cz - 8, "minecraft:barrel[facing=up,open=false]")


def launch_pad(bb, cx, cz, y):
    bb.fill_where(cx - 6, y, cz - 6, cx + 6, y, cz + 6, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 5.6, "minecraft:smooth_quartz")
    bb.fill_where(cx - 6, y, cz - 6, cx + 6, y, cz + 6, lambda X, Y, Z: np.abs(np.hypot(X - cx, Z - cz) - 3.5) < 0.5, "minecraft:light_blue_concrete")
    for a in range(0, 360, 90):
        x, z = cx + int(round(5 * math.cos(math.radians(a)))), cz + int(round(5 * math.sin(math.radians(a))))
        bb.fill(x, y + 1, z, x, y + 2, z, "minecraft:birch_fence")
    weather_ball(bb, cx, y + 9, cz, "yellow", r=3.2, ground=y)


def design():
    bb = BigBuild(seed=9300, y_min=-34, y_max=72)
    tracker = P.PropTracker(9300)
    audit = []
    rng = np.random.default_rng(9300)
    islets(bb, rng)
    bridges(bb)
    cx, cz, r, y0 = ISLES[0]
    library(bb, cx - 4, cz + 4, y0 + 1, tracker, audit)
    observatory(bb, cx + 14, cz - 12, y0 + 1, tracker, audit)
    haredas_lab(bb, cx - 12, cz - 12, y0 + 1, tracker, audit)
    # scientists' houses on the islets round it
    for i, (k, door, kinds) in enumerate(((1, "east", ["bedroom", "living"]), (2, "west", ["kitchen", "bedroom"]),
                                          (4, "north", ["bedroom", "storage"]))):
        x, z, rr, yy = ISLES[k]
        rotunda(bb, x, z, yy + 1, 6, 2, 4, tracker, audit, kinds, door=door, wood="birch")
    x, z, rr, yy = ISLES[3]
    garden(bb, x, z, yy)
    rotunda(bb, x + 8, z + 6, yy + 1, 4, 1, 4, tracker, audit, ["storage"], door="west", wood="birch", vane=False)
    x, z, rr, yy = ISLES[5]
    launch_pad(bb, x, z, yy)
    x, z, rr, yy = ISLES[6]
    bb.set(x, yy + 1, z, "minecraft:bell[attachment=floor,facing=south]")
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bb.fill(x + dx, yy + 1, z + dz, x + dx, yy + 3, z + dz, "minecraft:birch_fence")
    bb.fill(x - 2, yy + 4, z - 2, x + 2, yy + 4, z + 2, "minecraft:light_blue_concrete")
    # weather balls floating on tethers all over
    cols = ["white", "light_blue", "yellow", "white", "light_gray", "blue"]
    k = 0
    for _ in range(300):
        i = int(rng.integers(0, len(ISLES)))
        x, z, rr, yy = ISLES[i]
        a = rng.uniform(0, 2 * math.pi)
        d = rr * rng.uniform(0.3, 0.85)
        bx, bz = int(x + d * math.cos(a)), int(z + d * math.sin(a))
        by = yy + int(rng.integers(10, 26))
        reg = bb.get_region(bx - 3, yy + 1, bz - 3, bx + 3, by + 3, bz + 3)
        if (reg > 1).any():
            continue
        weather_ball(bb, bx, by, bz, cols[k % len(cols)], r=float(rng.uniform(1.4, 2.6)), ground=yy)
        k += 1
        if k >= 22:
            break
    # cloud moss: a thin cover (not a block) lying on the cloud tops
    for i, (x, z, rr, yy) in enumerate(ISLES):
        reg_top = bb.get_region(x - rr - 6, yy, z - rr - 6, x + rr + 6, yy, z + rr + 6)[:, 0, :]
        reg_up = bb.get_region(x - rr - 6, yy + 1, z - rr - 6, x + rr + 6, yy + 1, z + rr + 6)[:, 0, :]
        for (ix, iz) in zip(*np.nonzero((reg_top > 1) & (reg_up == 0))):
            px, pz = x - rr - 6 + int(ix), z - rr - 6 + int(iz)
            name = bb.names[int(reg_top[ix, iz])]
            if NT.noise(np.array([px]), np.array([pz]), 9360 + i, 4)[0] > 0.45 and name.split("[")[0] in (CLOUD, "minecraft:grass_block"):
                bb.set(px, yy + 1, pz, MOSS)
    # lamp posts and cloud shrubs
    for i, (x, z, rr, yy) in enumerate(ISLES):
        for _ in range(int(rr * 0.6)):
            a = rng.uniform(0, 2 * math.pi)
            d = rr * rng.uniform(0.4, 0.8)
            px, pz = int(x + d * math.cos(a)), int(z + d * math.sin(a))
            reg = bb.get_region(px, yy + 1, pz, px, yy + 1, pz)
            if (reg == 0).all() and (bb.get_region(px, yy, pz, px, yy, pz) > 1).all():
                bb.set(px, yy + 1, pz, SHRUB)
        if rr >= 13:
            for a in range(0, 360, 72):
                px, pz = int(x + (rr - 4) * math.cos(math.radians(a))), int(z + (rr - 4) * math.sin(math.radians(a)))
                if (bb.get_region(px, yy + 1, pz, px, yy + 5, pz) == 0).all() and (bb.get_region(px, yy, pz, px, yy, pz) > 1).all():
                    lamp_post(bb, px, yy + 1, pz, post="minecraft:birch_fence", h=3)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    cx, cz, r, y0 = ISLES[0]
    b.chest(cx - 12 + 4, y0 + 2, cz - 12, "lab", "west")
    b.chest(cx - 4 + 5, y0 + 2, cz + 4 - 5, "library", "east")
    x, z, rr, yy = ISLES[6]
    b.chest(x + 1, yy + 1, z - 1, "sky_treasure", "south")
    return b, 0
