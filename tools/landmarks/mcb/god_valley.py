"""God Valley v3, redesigned with the Minecraft Builder skill to match the anime: the holy island where the World
Nobles held their Native Hunting Tournament 38 years ago, and where Roger and Garp fought the Rocks Pirates.

The island is one steep mountain split down the middle: two towering ochre-orange rock spires (~100 high), ribbed
with vertical fluting and banded in reds and tans, stand side by side with a narrow chasm between them that cuts
right down through the rock massif at their feet (a gorge road runs through it). Smaller spires rise at the flanks.

Round the mountain sprawls the World Nobles' city: white marble mansions with stacked grey pagoda eaves and gold
finials, packed along the lanes from the mountain foot to the shore, every floor furnished. South of the mountain
the Nobles' stage from the tournament: a raised semicircular stage with a white wall of pointed arched windows,
columns, and a huge round arch framing it, facing a plaza with rows of benches (Rocks D. Xebec waits there).
North-east, the natives' hunting forest with their village of thatched huts; on the west beach the Rocks Pirates'
camp beside the charred wreck of their ship; Garp's warship lies off the south-east shore.
192 x 192, y 0 = sea surface. (v3)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, st, steady, lamp_post
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "god_valley"
TITLE = "God Valley"
CUTS = [3, 10, 20, 32]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 192
GY = 4
_ISLE = NT.outline(96, 96, 82, 9710, wobble=0.06)
MAS = (96, 78, 48, 32, 40)                 # rock massif: centre x, z, radii x, z, height
SPLIT_X = 96                               # the chasm between the twin spires
SPIRES = ((84, 78, 15.0, 106, 1), (108, 79, 14.0, 100, 2), (60, 86, 7.0, 54, 3), (134, 84, 6.5, 46, 4), (124, 100, 5.0, 32, 5),
          (70, 62, 5.5, 38, 6), (118, 58, 5.0, 36, 7))
STAGE = (96, 140)                          # the Nobles' stage (centre of its semicircle; it opens south)
PLAZA = (74, 122, 118, 166)                # plaza x1, z1, x2, z2 (levelled)
FOREST = (150, 38, 20)                     # natives' hunting forest (x, z, r)
VIL = (150, 38, 11)                        # the native village
CAMP = (24, 120)                           # Rocks camp
MEADOW = [("minecraft:grass_block", 0.75), ("minecraft:moss_block", 0.08), ("minecraft:podzol", 0.06), ("minecraft:rooted_dirt", 0.06),
          ("minecraft:coarse_dirt", 0.05)]
LANE = [("minecraft:smooth_stone", 0.25), ("minecraft:polished_diorite", 0.25), ("minecraft:calcite", 0.2), ("minecraft:stone_bricks", 0.15),
        ("minecraft:polished_andesite", 0.15)]
ROCK_LIT = ["minecraft:orange_terracotta", "minecraft:red_sandstone", "minecraft:smooth_red_sandstone", "minecraft:terracotta",
            "minecraft:orange_terracotta", "minecraft:cut_red_sandstone"]
ROCK_DARK = ["minecraft:brown_terracotta", "minecraft:terracotta", "minecraft:brown_terracotta", "minecraft:terracotta", "minecraft:red_sandstone"]
FLOWERS = ["minecraft:lily_of_the_valley", "minecraft:oxeye_daisy", "minecraft:white_tulip", "minecraft:azure_bluet", "minecraft:cornflower",
           "minecraft:poppy"]
MANSION = [("minecraft:smooth_quartz", "minecraft:quartz_pillar[axis=y]"), ("minecraft:calcite", "minecraft:polished_diorite"),
           ("minecraft:white_concrete", "minecraft:smooth_quartz"), ("minecraft:polished_diorite", "minecraft:calcite"),
           ("minecraft:quartz_bricks", "minecraft:smooth_quartz")]
ROOF = [("minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles"), ("minecraft:polished_andesite_stairs", "minecraft:polished_andesite"),
        ("minecraft:stone_brick_stairs", "minecraft:stone_bricks"), ("minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks")]
KINDS = ["dining", "bedroom", "library", "office", "kitchen", "bedroom", "storeroom", "dining"]
WOODS = ["dark_oak", "spruce", "birch", "cherry"]


def _mas(X, Z):
    """0..1 inside the massif footprint."""
    cx, cz, rx, rz, _ = MAS
    e = np.hypot((X - cx) / rx, (Z - cz) / rz) + (NT.noise(X, Z, 9720, 9) - 0.5) * 0.25
    return np.clip(1 - e, 0, 1)


def gorge(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (np.abs(X - SPLIT_X) <= 2) & (Z > MAS[1] - MAS[3] - 6) & (Z < MAS[1] + MAS[3] + 6)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    h = GY + (NT.fbm(X, Z, 9711, 22) - 0.5) * 5
    m = _mas(X, Z)
    h = h + MAS[4] * np.clip(m * 2.2, 0, 1) ** 0.8 + (NT.fbm(X, Z, 9719, 8) - 0.5) * 8 * (m > 0.05)
    x1, z1, x2, z2 = PLAZA
    pl = (X >= x1) & (X <= x2) & (Z >= z1) & (Z <= z2)
    h = np.where(pl, GY + 1, h)
    h = np.where(gorge(X, Z), GY + 2, h)
    h = np.where(d < 10, 1 + (h - 1) * np.clip(d / 10.0, 0, 1) ** 1.4, h)
    h = np.where(d < 1.5, -5 - np.clip(-d, 0, 6), h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)
G = np.zeros_like(HMAP)
for _a, _b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))), ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
    _d = np.abs(HMAP[_a] - HMAP[_b]); G[_a] = np.maximum(G[_a], _d); G[_b] = np.maximum(G[_b], _d)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def lane(X, Z):
    """The avenue from the stage plaza up through the gorge, and the ring road round the mountain."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return land(X, Z) & (_ISLE(X, Z) > 8) & (np.abs(X - SPLIT_X) <= 2) & (Z < PLAZA[1] + 1)


def _rockpick(X, y, Z, cx, cz, seed):
    """Colour pick for rock: lit (south/west faces) or dark, banded by height."""
    lit = ((X - cx) * -0.6 + (Z - cz) * 0.8) > -2
    band = (np.asarray(y, float) / 7.0 + NT.noise(X * 1.0 + y * 0.5, Z + y * 0.3, seed, 5) * 3.5).astype(int)
    return lit, band


def rockpaint(bb, box, inside, cx, cz, seed):
    x1, y1, z1, x2, y2, z2 = box
    for i, blk in enumerate(ROCK_LIT):
        bb.fill_where(x1, y1, z1, x2, y2, z2,
                      lambda X, y, Z, i=i: inside(X, y, Z) & _rockpick(X, y, Z, cx, cz, seed)[0] & (_rockpick(X, y, Z, cx, cz, seed)[1] % len(ROCK_LIT) == i), blk)
    for i, blk in enumerate(ROCK_DARK):
        bb.fill_where(x1, y1, z1, x2, y2, z2,
                      lambda X, y, Z, i=i: inside(X, y, Z) & ~_rockpick(X, y, Z, cx, cz, seed)[0] & (_rockpick(X, y, Z, cx, cz, seed)[1] % len(ROCK_DARK) == i), blk)


def terrain(bb):
    steep = lambda X, Z: (G[_ix(X, Z)] >= 2) | (height(X, Z) > GY + 12)
    beach = lambda X, Z: (_ISLE(X, Z) < 7) & (height(X, Z) <= 3)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, MEADOW, 9713, mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ~beach(X, Z),
             under="minecraft:dirt", core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [(b, 1.0 / len(ROCK_LIT)) for b in ROCK_LIT], 9714,
             mask=lambda X, Z: land(X, Z) & steep(X, Z) & ~beach(X, Z), under="minecraft:terracotta", core="minecraft:terracotta", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:sand", 0.8), ("minecraft:sandstone", 0.1), ("minecraft:smooth_sandstone", 0.1)], 9716,
             mask=lambda X, Z: land(X, Z) & beach(X, Z), under="minecraft:sandstone", core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, LANE, 9717, mask=lane, under="minecraft:stone", core="minecraft:stone", depth=1, base=-2)
    x1, z1, x2, z2 = PLAZA
    NT.cover(bb, x1, z1, x2, z2, height, LANE, 9718, mask=lambda X, Z: land(X, Z), under="minecraft:stone", core="minecraft:stone", depth=1, base=-2)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:stone")
    # the massif's slopes in the lit/dark rock scheme, moss on gentle ledges
    cx, cz, rx, rz, mh = MAS
    box = (cx - rx - 2, GY, cz - rz - 2, cx + rx + 2, GY + mh + 8, cz + rz + 2)
    inside = lambda X, y, Z: (_mas(X, Z) > 0.08) & (y <= height(X, Z)) & (y >= height(X, Z) - 2) & (y > GY + 2)
    rockpaint(bb, box, inside, cx, cz, 9721)
    bb.fill_where(*box, lambda X, y, Z: (_mas(X, Z) > 0.08) & (y == height(X, Z)) & (G[_ix(X, Z)] <= 1) & (NT.noise(X, Z, 9722, 4) > 0.45) & ~gorge(X, Z),
                  "minecraft:moss_block")


def spires(bb):
    """The twin split spires and their smaller neighbours: fluted, banded rock columns, then the chasm."""
    for (cx, cz, rb, h, s) in SPIRES:
        base = GY - 2
        def inside(X, y, Z, cx=cx, cz=cz, rb=rb, h=h, s=s):
            t = np.clip((y - GY) / h, 0, 1)
            r = rb * (1 - 0.38 * t) * np.where(t > 0.88, np.sqrt(np.clip(1 - ((t - 0.88) / 0.12) ** 2, 0, 1)), 1.0)
            a = np.arctan2(Z - cz, X - cx)
            flute = 1 + 0.11 * np.sin(a * 9 + s) + 0.06 * np.sin(a * 4 - y * 0.05 + s)
            ledge = 1 + 0.08 * ((np.asarray(y) + s * 3) % 17 < 2)
            r = r * flute * ledge * (0.9 + 0.2 * NT.noise(X + y * 0.2, Z - y * 0.2, 9730 + s, 6))
            return (np.hypot(X - cx, Z - cz) <= r) & (y <= GY + h)
        R = int(rb * 1.4) + 2
        box = (cx - R, base, cz - R, cx + R, GY + h + 1, cz + R)
        rockpaint(bb, box, inside, cx, cz, 9740 + s)
        bb.fill_where(*box, lambda X, y, Z, f=inside: f(X, y - 1, Z) & ~f(X, y, Z) & (y < GY + 70) & (NT.noise(X * 2, Z * 2 + y, 9750, 3) > 0.62),
                      "minecraft:moss_carpet", only_empty=True)
    cz = MAS[1]
    bb.fill_where(SPLIT_X - 8, GY + 3, cz - MAS[3] - 8, SPLIT_X + 8, GY + 110, cz + MAS[3] + 8,
                  lambda X, y, Z: np.abs(X - SPLIT_X - 1.2 * np.sin(y / 11.0) - 0.8 * np.sin(Z / 7.0)) < 2.2 + 0.035 * (y - GY), AIR)


# ------------------------------------------------------------------ the Nobles' city

def mansion(bb, x0, z0, w, d, y0, floors, rng, face, fh=5):
    """White marble mansion with stacked grey pagoda eaves and a hip roof, every floor furnished. Returns roof top y."""
    wall, trim = MANSION[int(rng.integers(0, len(MANSION)))]
    rst, rfull = ROOF[int(rng.integers(0, len(ROOF)))]
    wood = WOODS[int(rng.integers(0, len(WOODS)))]
    cx, cz = x0 + w // 2, z0 + d // 2
    door = {"south": (cx, z0 + d - 1), "north": (cx, z0), "east": (x0 + w - 1, cz), "west": (x0, cz)}[face]
    yb = y0
    fx1, fz1, fx2, fz2 = x0, z0, x0 + w - 1, z0 + d - 1
    for i in range(floors):
        if i and fx2 - fx1 >= 7 and fz2 - fz1 >= 7:
            fx1, fz1, fx2, fz2 = fx1 + 1, fz1 + 1, fx2 - 1, fz2 - 1
        top = yb + fh - 1
        bb.fill(fx1, yb, fz1, fx2, top, fz2, wall)
        bb.fill(fx1 + 1, yb, fz1 + 1, fx2 - 1, top - 1, fz2 - 1, AIR)
        for (a, b) in ((fx1, fz1), (fx2, fz1), (fx1, fz2), (fx2, fz2)):
            bb.fill(a, yb, b, a, top - 1, b, trim)
        bb.fill(fx1 + 1, yb - 1, fz1 + 1, fx2 - 1, yb - 1, fz2 - 1, f"minecraft:{wood}_planks")
        for x in range(fx1 + 2, fx2 - 1, 2):
            for z in (fz1, fz2):
                if i == 0 and abs(x - door[0]) <= 1 and z == door[1]:
                    continue
                bb.fill(x, yb + 1, z, x, yb + 2, z, "minecraft:gray_stained_glass_pane")
        for z in range(fz1 + 2, fz2 - 1, 2):
            for x in (fx1, fx2):
                if i == 0 and abs(z - door[1]) <= 1 and x == door[0]:
                    continue
                bb.fill(x, yb + 1, z, x, yb + 2, z, "minecraft:gray_stained_glass_pane")
        # the eave: a stair skirt one block out at the ceiling plate
        for x in range(fx1 - 1, fx2 + 2):
            bb.set(x, top, fz1 - 1, st(rst, "south")); bb.set(x, top, fz2 + 1, st(rst, "north"))
        for z in range(fz1 - 1, fz2 + 2):
            bb.set(fx1 - 1, top, z, st(rst, "east")); bb.set(fx2 + 1, top, z, st(rst, "west"))
        for (a, b) in ((fx1 - 1, fz1 - 1), (fx2 + 1, fz1 - 1), (fx1 - 1, fz2 + 1), (fx2 + 1, fz2 + 1)):
            bb.set(a, top, b, rfull)
        doors = [(cx, cz), (cx, cz + 1)]
        if i == 0:
            doors.append(door)
        furnish_kit(bb, (fx1 + 1, fz1 + 1, fx2 - 1, fz2 - 1), yb, fh - 1, KINDS[int(rng.integers(0, len(KINDS)))], wood=wood,
                    seed=int(rng.integers(0, 1 << 30)), doors=doors, accent=["red", "purple", "yellow", "blue", "white"][int(rng.integers(0, 5))])
        yb = top + 1
    top = yb - 1
    # hip roof stepping in from the top floor
    k = 0
    while True:
        y = top + 1 + k
        a1, b1, a2, b2 = fx1 + k, fz1 + k, fx2 - k, fz2 - k
        if a2 - a1 <= 1 or b2 - b1 <= 1:
            bb.fill(a1, y, b1, max(a1, a2), y, max(b1, b2), rfull)
            break
        for x in range(a1, a2 + 1):
            bb.set(x, y, b1, st(rst, "south")); bb.set(x, y, b2, st(rst, "north"))
        for z in range(b1 + 1, b2):
            bb.set(a1, y, z, st(rst, "east")); bb.set(a2, y, z, st(rst, "west"))
        for (a, b) in ((a1, b1), (a2, b1), (a1, b2), (a2, b2)):
            bb.set(a, y, b, rfull)
        k += 1
    peak = top + 1 + k
    bb.set(cx, peak + 1, cz, "minecraft:gold_block" if rng.random() < 0.35 else "minecraft:lightning_rod")
    # ladder up the middle (on a marble pillar), through each floor plate
    if floors > 1:
        bb.fill(cx, y0, cz, cx, top - fh, cz, trim)
        bb.fill(cx, y0, cz + 1, cx, top - fh, cz + 1, "minecraft:ladder[facing=south]")
        for i in range(1, floors):
            bb.set(cx, y0 + i * fh - 1, cz + 1, "minecraft:ladder[facing=south]")
            bb.set(cx, y0 + i * fh, cz + 1, "minecraft:ladder[facing=south]") if False else None
    dx, dz = door
    ox, oz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[face]
    bb.set(dx, y0, dz, f"minecraft:{wood}_door[facing={face},half=lower,hinge=left]")
    bb.set(dx, y0 + 1, dz, f"minecraft:{wood}_door[facing={face},half=upper,hinge=left]")
    g = hy(dx + ox, dz + oz)
    if g < y0 - 1:
        bb.fill(dx + ox, g + 1, dz + oz, dx + ox, y0 - 1, dz + oz, trim)
    bb.fill(dx + ox, y0, dz + oz, dx + ox, y0 + 2, dz + oz, AIR)
    sx, sz = (dx + 1, dz) if face in ("south", "north") else (dx, dz + 1)
    bb.set(sx + ox, y0 + 2, sz + oz, f"minecraft:wall_torch[facing={face}]")
    return peak


def city(bb, rng):
    houses = []
    def blocked(x0, z0, x1, z1):
        X = np.arange(x0 - 1, x1 + 2)[:, None]; Z = np.arange(z0 - 1, z1 + 2)[None, :]
        if (~land(X, Z)).any() or (_ISLE(X, Z) < 9).any() or lane(X, Z).any():
            return True
        if (height(X, Z) > GY + 16).any() or (height(X, Z).max() - height(X, Z).min() > 8):
            return True
        x1p, z1p, x2p, z2p = PLAZA
        if ((X >= x1p - 1) & (X <= x2p + 1) & (Z >= z1p - 1) & (Z <= z2p + 1)).any():
            return True
        if (np.hypot(X - FOREST[0], Z - FOREST[1]) < FOREST[2]).any() or (np.hypot(X - CAMP[0] - 8, Z - CAMP[1]) < 16).any():
            return True
        if any(np.hypot(X - c[0], Z - c[1]).min() < c[2] * 1.4 + 2 for c in SPIRES):
            return True
        return any(x0 - 1 <= b[2] and b[0] <= x1 + 1 and z0 - 1 <= b[3] and b[1] <= z1 + 1 for b in houses)
    cand = [(x, z) for x in range(8, N - 16) for z in range(8, N - 16)]
    key = [float(np.hypot(x - MAS[0], (z - MAS[1]) * 1.3)) + rng.random() * 40 for (x, z) in cand]
    for i in np.argsort(key):
        x0, z0 = cand[i]
        w, d = int(rng.integers(6, 10)), int(rng.integers(6, 10))
        x1, z1 = x0 + w - 1, z0 + d - 1
        if blocked(x0, z0, x1, z1):
            continue
        X = np.arange(x0, x1 + 1)[:, None]; Z = np.arange(z0, z1 + 1)[None, :]
        hs = height(X, Z)
        g = int(hs.max())
        floors = 1 + int(rng.random() < 0.75) + int(rng.random() < 0.45) + int(rng.random() < 0.15)
        mx, mz = (x0 + x1) / 2 - MAS[0], (z0 + z1) / 2 - MAS[1]
        face = ("south" if mz > 0 else "north") if abs(mz) >= abs(mx) else ("east" if mx > 0 else "west")
        bb.fill(x0, int(hs.min()) - 2, z0, x1, g, z1, "minecraft:stone_bricks" if rng.random() < 0.5 else "minecraft:polished_andesite")
        mansion(bb, x0, z0, w, d, g + 1, floors, rng, face)
        houses.append((x0, z0, x1, z1))
    print("mansions:", len(houses))
    return houses


# ------------------------------------------------------------------ the Nobles' stage (manga ch. 1095)

def stage(bb):
    cx, cz = STAGE
    y = GY + 2
    R = 15
    bb.fill_where(cx - R, y - 1, cz - R, cx + R, y + 1, cz, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= R, "minecraft:smooth_quartz")
    bb.fill_where(cx - R, y + 1, cz - R, cx + R, y + 1, cz, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= R - 3, "minecraft:polished_diorite")
    bb.fill(cx - 2, y + 2, cz - 10, cx + 2, y + 2, cz, "minecraft:red_carpet")
    for x in range(cx - R + 2, cx + R - 1):
        bb.set(x, y + 1, cz + 1, st("minecraft:quartz_stairs", "north"))
        bb.set(x, y, cz + 2, st("minecraft:quartz_stairs", "north"))
    # the curved back wall with five pointed arched windows
    H = 18
    bb.fill_where(cx - R - 2, y + 2, cz - R - 2, cx + R + 2, y + H, cz, lambda X, Y, Z: (np.hypot(X - cx, Z - cz) > R - 0.5) & (np.hypot(X - cx, Z - cz) <= R + 1.5),
                  "minecraft:smooth_quartz")
    bb.fill_where(cx - R - 3, y + H + 1, cz - R - 3, cx + R + 3, y + H + 1, cz, lambda X, Y, Z: (np.hypot(X - cx, Z - cz) > R - 1) & (np.hypot(X - cx, Z - cz) <= R + 2.5),
                  "minecraft:quartz_bricks")
    for k in range(5):
        a = math.pi * (0.15 + 0.7 * k / 4)
        ux, uz = math.cos(a), -math.sin(a)             # outward from the centre
        tx, tz = -uz, ux                               # along the wall
        for o in range(-2, 3):
            top = y + 12 + (2 - abs(o)) * 1.3
            for yy in range(y + 4, int(top) + 1):
                for dd in (-0.6, 0.4, 1.4):
                    x, z = int(round(cx + ux * (R + dd) + tx * o)), int(round(cz + uz * (R + dd) + tz * o))
                    bb.set(x, yy, z, AIR)
                xg, zg = int(round(cx + ux * (R + 0.6) + tx * o)), int(round(cz + uz * (R + 0.6) + tz * o))
                bb.set(xg, yy, zg, "minecraft:black_stained_glass" if abs(o) < 2 else "minecraft:chiseled_quartz_block")
    for k in range(6):
        a = math.pi * (0.06 + 0.88 * k / 5)
        px, pz = int(round(cx + (R - 2) * math.cos(a))), int(round(cz - (R - 2) * math.sin(a)))
        bb.fill(px, y + 2, pz, px, y + 13, pz, "minecraft:quartz_pillar[axis=y]")
        bb.set(px, y + 14, pz, "minecraft:chiseled_quartz_block")
        bb.set(px, y + 2, pz, "minecraft:chiseled_quartz_block")
    # the great round arch framing the stage: a half ring standing on the front edge
    for x in range(cx - 25, cx + 26):
        for yy in range(y, y + 26):
            r = math.hypot(x - cx, yy - y)
            if 21 <= r <= 24.5:
                for z in (cz + 3, cz + 4):
                    bb.set(x, yy, z, "minecraft:quartz_bricks" if r < 23.5 else "minecraft:smooth_quartz")
                if 22 <= r <= 23.4:
                    bb.set(x, yy, cz + 5, "minecraft:gold_block" if (x + yy) % 6 == 0 else "minecraft:smooth_quartz")
    bb.fill(cx - 25, GY - 2, cz + 3, cx - 21, y, cz + 5, "minecraft:quartz_bricks")
    bb.fill(cx + 21, GY - 2, cz + 3, cx + 25, y, cz + 5, "minecraft:quartz_bricks")
    # the nobles' benches facing the stage
    for row, z in enumerate(range(cz + 9, cz + 26, 3)):
        for x in range(cx - 19, cx + 20):
            if abs(x - cx) <= 2:
                continue
            bb.set(x, hy(x, z) + 1, z, st("minecraft:quartz_stairs" if row < 2 else "minecraft:birch_stairs", "south"))
    for s in (-1, 1):
        for z in range(cz + 8, cz + 28, 6):
            lamp_post(bb, cx + s * 22, hy(cx + s * 22, z) + 1, z, post="minecraft:dark_oak_fence", h=3)
        x = cx + s * 28
        bb.fill(x, hy(x, cz) + 1, cz, x, hy(x, cz) + 14, cz, "minecraft:dark_oak_fence")
        for r in range(5):
            for c in range(4):
                bb.set(x + s * (c + 1), hy(x, cz) + 14 - r, cz, "minecraft:white_wool" if (r + c) % 4 else "minecraft:yellow_wool")


def forest(bb, rng, taken):
    """The natives' hunting forest (north-east) and a few trees and flowers in the city's green gaps."""
    fx, fz, fr = FOREST
    for _ in range(5000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or _ISLE(X, Z)[0, 0] < 8 or lane(X, Z)[0, 0] or _mas(X, Z)[0, 0] > 0.1:
            continue
        if any(b[0] - 2 <= x <= b[2] + 2 and b[1] - 2 <= z <= b[3] + 2 for b in taken):
            continue
        y = hy(x, z)
        if bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] > 1 or bb.get_region(x, y, z, x, y, z)[0, 0, 0] <= 1:
            continue
        inf = math.hypot(x - fx, z - fz) < fr
        if rng.random() < (0.09 if inf else 0.012):
            if inf and rng.random() < 0.1:
                NT.giant_tree(bb, x, y + 1, z, int(rng.integers(16, 22)), rng, kind="jungle")
            else:
                P.tree(bb, x, y + 1, z, height=int(rng.integers(5, 9)), kind="jungle" if inf else ["oak", "birch", "cherry"][int(rng.integers(3))], rng=rng)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 9718, density=0.22, flowers=FLOWERS,
              mask=lambda X, Z: land(X, Z) & (_ISLE(X, Z) > 7) & (_mas(X, Z) < 0.05) & ~lane(X, Z))


def design():
    bb = BigBuild(seed=9710, y_min=-14, y_max=GY + 112)
    tracker = P.PropTracker(9710)
    rng = np.random.default_rng(9710)
    terrain(bb)
    spires(bb)
    stage(bb)
    huts = village(bb, rng, tracker)
    rocks_camp(bb, rng)
    stamp_ship(bb, "marine_warship", 156, 174, water_y=0, rot=0)
    houses = city(bb, rng)
    taken = huts + houses + [(PLAZA[0], PLAZA[1] - 20, PLAZA[2], PLAZA[3]), (CAMP[0] - 20, CAMP[1] - 20, CAMP[0] + 30, CAMP[1] + 40)]
    forest(bb, rng, taken)
    return bb, []


def build():
    bb, audit = design()
    b = to_canvas(bb)
    steady(b)
    cx, cz = STAGE
    b.npc(cx, GY + 4, cz - 6, "xebec", True)
    b.chest(cx, GY + 4, cz - 13, "legendary", "south")
    b.chest(CAMP[0] + 14, hy(CAMP[0] + 14, CAMP[1] - 12) + 1, CAMP[1] - 12, "treasure", "south")
    b.chest(VIL[0], hy(VIL[0], VIL[1] + 3) + 1, VIL[1] + 3, "medium", "north")
    b.chest(SPLIT_X, GY + 3, MAS[1], "treasure", "south")
    for (x, z) in ((CAMP[0] + 8, CAMP[1]), (CAMP[0] + 16, CAMP[1] + 4), (cx - 14, cz + 12), (cx + 14, cz + 12)):
        b.guard(x, hy(x, z) + 1, z, "pirate")
    b.guards("marine", ((SPLIT_X, MAS[1] + 36), (SPLIT_X, MAS[1] - 36)), y=GY + 3)
    return b, 0


def village(bb, rng, tracker):
    """Round thatched huts round a well and a totem; the western half burnt."""
    cx, cz, r = VIL
    huts = []
    for k in range(9):
        a = 2 * math.pi * k / 9
        x, z = int(round(cx + r * 0.75 * math.cos(a))), int(round(cz + r * 0.75 * math.sin(a)))
        burnt = math.cos(a) < -0.2
        y = hy(x, z)
        rr = 4
        bb.fill_where(x - rr, y - 2, z - rr, x + rr, y, z + rr, lambda X, Y, Z: np.hypot(X - x, Z - z) <= rr + 0.3, "minecraft:packed_mud")
        wall = "minecraft:mud_bricks" if not burnt else "minecraft:blackstone"
        bb.cylinder(x, y + 1, z, rr, y + 3, wall, hollow=True)
        bb.cylinder(x, y + 1, z, rr - 1, y + 4, AIR)
        dx, dz = int(round(math.cos(a + math.pi) * rr)), int(round(math.sin(a + math.pi) * rr))
        bb.fill(x + dx, y + 1, z + dz, x + dx, y + 2, z + dz, AIR)
        if not burnt:
            for i in range(5):
                bb.cylinder(x, y + 4 + i, z, max(0, rr + 1 - i), y + 4 + i, "minecraft:hay_block[axis=y]", hollow=i < 4)
            bb.set(x, y + 9, z, "minecraft:spruce_fence")
            bb.set(x, y + 3, z, "minecraft:lantern[hanging=true]")
            bb.set(x + 2, y + 1, z, "minecraft:brown_bed[facing=east,part=head]") if False else None
            bb.set(x - 1, y + 1, z - 2, "minecraft:barrel[facing=up,open=false]")
            bb.set(x + 1, y + 1, z - 2, "minecraft:brown_bed[facing=north,part=head]"); bb.set(x + 1, y + 1, z - 1, "minecraft:brown_bed[facing=north,part=foot]")
            bb.set(x - 2, y + 1, z + 1, "minecraft:campfire[lit=false]") if False else bb.set(x - 2, y + 1, z + 1, "minecraft:cauldron")
            bb.set(x - 1, y, z + 1, "minecraft:brown_carpet") if False else None
        else:
            for _ in range(6):
                bb.set(x + int(rng.integers(-2, 3)), y + 1, z + int(rng.integers(-2, 3)), "minecraft:coal_block" if rng.random() < 0.5 else "minecraft:black_carpet")
            for _ in range(5):
                xx, zz = x + int(rng.integers(-rr, rr + 1)), z + int(rng.integers(-rr, rr + 1))
                bb.set(xx, y + 3, zz, AIR)
        huts.append((x - rr, z - rr, x + rr, z + rr))
    y = hy(cx, cz)
    bb.cylinder(cx, y - 6, cz, 2, y + 1, "minecraft:cobblestone", hollow=True)
    bb.cylinder(cx, y - 5, cz, 1, y - 1, "minecraft:water")
    bb.fill(cx - 2, y + 2, cz, cx + 2, y + 2, cz, "minecraft:spruce_fence") if False else None
    tx, tz = cx + 6, cz
    bb.fill(tx, y + 1, tz, tx, y + 8, tz, "minecraft:stripped_jungle_log[axis=y]")
    for (yy, s) in ((y + 3, "minecraft:carved_pumpkin[facing=west]"), (y + 6, "minecraft:carved_pumpkin[facing=west]")):
        bb.set(tx, yy, tz, s)
    bb.fill(tx, y + 7, tz - 2, tx, y + 7, tz + 2, "minecraft:stripped_jungle_log[axis=z]")
    return huts


def rocks_camp(bb, rng):
    """Tents, a bonfire, crates and the Rocks Pirates' charred ship hauled up on the west beach."""
    cx, cz = CAMP
    for k, (dx, dz) in enumerate(((-6, -10), (4, -12), (10, -2), (-8, 4), (2, 8))):
        x, z = cx + dx + 12, cz + dz
        y = hy(x, z)
        for i in range(4):
            bb.fill(x - 3 + i, y + 1 + i, z - 2, x - 3 + i, y + 1 + i, z + 2, "minecraft:black_wool" if k % 2 else "minecraft:gray_wool")
            bb.fill(x + 3 - i, y + 1 + i, z - 2, x + 3 - i, y + 1 + i, z + 2, "minecraft:black_wool" if k % 2 else "minecraft:gray_wool")
        bb.fill(x, y + 1, z - 2, x, y + 4, z - 2, "minecraft:dark_oak_fence")
        bb.set(x - 1, y + 1, z, "minecraft:black_bed[facing=south,part=head]"); bb.set(x - 1, y + 1, z + 1, "minecraft:black_bed[facing=south,part=foot]")
        bb.set(x + 1, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    y = hy(cx + 12, cz)
    bb.set(cx + 12, y + 1, cz, "minecraft:campfire[lit=true]")
    for (a, b, f) in ((cx + 10, cz, "west"), (cx + 14, cz, "east"), (cx + 12, cz - 2, "north"), (cx + 12, cz + 2, "south")):
        bb.set(a, hy(a, b) + 1, b, st("minecraft:dark_oak_stairs", f))
    # the black flag on a pole
    fx, fz = cx + 20, cz - 4
    y = hy(fx, fz)
    bb.fill(fx, y + 1, fz, fx, y + 14, fz, "minecraft:dark_oak_fence")
    for r in range(6):
        for c in range(8):
            sk = (r in (1, 2) and 2 <= c <= 5) or (r == 3 and c in (2, 5)) or (r == 4 and c in (1, 6))
            bb.set(fx + 1 + c, y + 14 - r, fz, "minecraft:white_wool" if sk else "minecraft:black_wool")
    # the wreck
    stamp_ship(bb, "bezan_black", cx - 4, cz + 14, water_y=0, rot=1)
    burn_box(bb, cx - 20, -4, cz - 10, cx + 12, 40, cz + 40, rng)


def burn_box(bb, x1, y1, z1, x2, y2, z2, rng):
    """Char a ship: planks to dark/blackened wood, sails mostly burnt away, some holes."""
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    names = bb.names
    for i in np.unique(reg):
        if i < 2:
            continue
        n = names[int(i)]
        s = n.split("[")[0]
        new = None
        if s.endswith("_wool") or s.endswith("_carpet") or s.endswith("_banner"):
            new = "burn"
        elif "planks" in s or s.endswith("_log") or s.endswith("_wood"):
            new = "minecraft:blackstone" if "log" in s else "minecraft:dark_oak_planks"
        elif s.endswith(("_stairs", "_slab", "_fence", "_trapdoor")) and any(k in s for k in ("oak", "spruce", "birch", "jungle", "mangrove", "cherry", "acacia")):
            new = n.replace(s.split(":")[1].split("_")[0], "dark_oak").replace("dark_dark_oak", "dark_oak") if "dark_oak" not in s else n
        if new is None:
            continue
        idx = np.argwhere(reg == i)
        for (ix, iy, iz) in idx:
            if new == "burn":
                if rng.random() < 0.75:
                    bb.set(x1 + ix, y1 + iy, z1 + iz, AIR)
                elif rng.random() < 0.5:
                    bb.set(x1 + ix, y1 + iy, z1 + iz, "minecraft:black_wool")
            elif rng.random() < 0.08 and y1 + iy > 2:
                bb.set(x1 + ix, y1 + iy, z1 + iz, AIR)
            else:
                bb.set(x1 + ix, y1 + iy, z1 + iz, new)


