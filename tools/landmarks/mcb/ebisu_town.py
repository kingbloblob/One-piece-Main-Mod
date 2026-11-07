"""Ebisu Town v2, the poorest town in Wano, redesigned with the Minecraft Builder skill.

Bare, worn ground of dirt and mud on the edge of a hilly island, the polluted river running brown and grey across
it to the sea on the south. Patched shacks and lean-tos of grey boards, mud and straw, with tarps over the holes,
crowd along two muddy lanes and the riverbank, their porches piled with junk; laundry lines strung between them,
broken carts, puddles, scrubby dead bushes. In the middle the little square with Toko's dango stall under its red
umbrella, the soup kitchen with its big pot over the fire, and Kyoshiro's gambling den: the one solid house in town,
dark timber with lanterns and a dice board. A tiny shrine with a red torii stands at the end of the lane; up on the
hill, the grave mound of Kozuki Oden's retainers with its stone markers and swords, looking out over the river.
144 x 144. y 0 = sea surface. (v2)

v3 (2026-10-30, audit: "from afar it reads as a flat brown mass; needs clear shack shapes"): every shack now has a
readable shape: most get a steep gable roof in one of five clearly different materials (dark deepslate tiles, mud
brick, dark oak, spruce, cobbled deepslate) with pale ridge boards and a bright tarp, some are two storeys high, the
rest keep a lean-to; they stand two to four blocks apart so each one reads on its own, and the lanes between them are
pale gravel and dirt paths instead of mud. The rows are gone: the shacks crowd organically along five winding lanes
and a loop lane round the square, doors to the nearest lane, and the sea only fills a round patch inside a wobbly
rim instead of the whole square site."""
from mcb.organic_town import street_mask
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, place_house
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "ebisu_town"
TITLE = "Ebisu Town (Wano)"
CUTS = [5, 10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 144
SHORE = NT.outline(72, 70, 64, 2220, wobble=0.1)
GY = 3
TOWN = (24, 34, 118, 92)
RIVER = lambda X: 104 + 5 * np.sin(np.asarray(X) * 0.07) + 2 * np.sin(np.asarray(X) * 0.19 + 1)
HILL = (40, 22)

POOR = [("minecraft:coarse_dirt", 0.3), ("minecraft:dirt", 0.12), ("minecraft:packed_mud", 0.14), ("minecraft:mud", 0.1),
        ("minecraft:grass_block", 0.18), ("minecraft:rooted_dirt", 0.08), ("minecraft:podzol", 0.08)]
LANE = [("minecraft:gravel", 0.3), ("minecraft:dirt_path", 0.35), ("minecraft:coarse_dirt", 0.2), ("minecraft:mud", 0.15)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.15), ("minecraft:cobblestone", 0.15),
        ("minecraft:mossy_cobblestone", 0.1)]
SAND = [("minecraft:sand", 0.5), ("minecraft:mud", 0.2), ("minecraft:clay", 0.15), ("minecraft:coarse_dirt", 0.15)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def river(X, Z):
    return np.abs(np.asarray(Z) - RIVER(X)) <= 4 + 1.5 * NT.noise(X, Z, 2221, 6)


_LANES = None


def lane(X, Z):
    global _LANES
    if _LANES is None:
        GX, GZ = np.arange(N)[:, None], np.arange(N)[None, :]
        m = street_mask((0, 0, N - 1, N - 1), (72, 65), 2227, spokes=5, rings=((26, 1.2),), width=1.2, wander=0.1)
        _LANES = m & (rect_d(GX, GZ, TOWN) < 4) & (SHORE(GX, GZ) > 4) & ~river(GX, GZ)
    X = np.clip(np.asarray(X).astype(int), 0, N - 1); Z = np.clip(np.asarray(Z).astype(int), 0, N - 1)
    return _LANES[X, Z]


def in_sea_rim(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    a = np.arctan2(Z - 72, X - 72)
    return np.hypot(X - 72, Z - 72) < 70 * (0.95 + 0.04 * np.sin(3 * a + 1) + 0.02 * np.sin(7 * a))


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = GY + NT.fbm(X, Z, 2222, 22) * 8 - 2
    h = h + 9 * np.exp(-((X - HILL[0]) ** 2 + (Z - HILL[1]) ** 2) / (2 * 14.0 ** 2))
    h = h * np.clip((d - 1.5) / 8.0, 0, 1)
    w = np.clip(rect_d(X, Z, TOWN) / 10.0, 0, 1)
    h = GY * (1 - w) + h * w
    rv = np.abs(Z - RIVER(X))
    h = np.where(rv < 9, np.minimum(h, GY - 1 + np.clip((rv - 4) / 2, 0, 1)), h)
    h = np.where(river(X, Z), -2, h)
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
    return (SHORE(X, Z) > 1.5) & ~river(X, Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2231, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z),
             under="minecraft:mud", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2232, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, POOR, 2233, mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, LANE, 2234, mask=lambda X, Z: land(X, Z) & lane(X, Z), core="minecraft:stone")
    for y in range(-12, GY):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (~land(X, Z)) & in_sea_rim(X, Z) & (yy <= np.where(river(X, Z) & (SHORE(X, Z) > 1.5), GY - 2, 0))
                      & (yy > -2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10) - 2 * river(X, Z)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (~land(X, Z)) & in_sea_rim(X, Z)
                      & (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10) - 2 * river(X, Z))), "minecraft:mud")
    # the river runs murky: mud and clay drifts on its bed, scum at its edges
    bb.fill_where(0, -6, 0, N - 1, -3, N - 1, lambda X, yy, Z: river(X, Z) & (SHORE(X, Z) > 1.5) & (yy == -4) & (NT.noise(X, Z, 2236, 3) > 0.5),
                  "minecraft:clay")


# ------------------------------------------------------------------ shacks
BOARDS = ["minecraft:spruce_planks", "minecraft:stripped_spruce_wood", "minecraft:oak_planks", "minecraft:mud_bricks",
          "minecraft:packed_mud", "minecraft:stripped_oak_wood", "minecraft:spruce_planks"]


def shack(seed, w, d, tracker, kind):
    """A patched shack, door on the south: walls of mismatched boards and mud, a few gaps stuffed with straw, a lean-to
    roof of planks and straw, a tarp over a hole, a porch with junk."""
    rng = np.random.default_rng(seed)
    m = BigBuild(seed=seed, y_min=-4, y_max=24)
    h = int(rng.choice([4, 4, 5, 7]))
    gable = rng.random() < 0.68
    m.fill(0, -3, 0, w - 1, 0, d - 1, "minecraft:dirt")
    m.fill(0, 0, 0, w - 1, 0, d - 1, "minecraft:spruce_planks" if rng.random() < 0.6 else "minecraft:packed_mud")
    for x in range(w):
        for z in range(d):
            if x in (0, w - 1) or z in (0, d - 1):
                for y in range(1, h + 1):
                    m.set(x, y, z, BOARDS[int(rng.integers(0, len(BOARDS)))])
    for (x, z) in ((0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)):
        m.fill(x, 1, z, x, h + 1, z, "minecraft:stripped_spruce_log[axis=y]")
    # holes stuffed with straw, a window with a shutter
    for _ in range(2):
        x = int(rng.integers(1, w - 1))
        m.set(x, int(rng.integers(2, h)), 0, "minecraft:hay_block[axis=x]")
    m.set(w // 2 + 1, 2, d - 1, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]") if w > 5 else None
    m.set(1, 2, 0, "minecraft:glass_pane") if rng.random() < 0.5 else None
    # door
    dx = w // 2 - 1 if w > 5 else 1
    m.set(dx, 1, d - 1, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    m.set(dx, 2, d - 1, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    m.fill(dx, 3, d - 1, dx, h, d - 1, "minecraft:spruce_planks")
    if gable:
        st_, full = ROOF_SETS[int(rng.integers(0, len(ROOF_SETS)))]
        along_x = w >= d
        P.gable_roof(m, -1, -1, w, d, h + 1, st_, ridge_axis="x" if along_x else "z", gable_fill=BOARDS[int(rng.integers(0, 3))],
                     overhang=0)
        ry = h + 1 + ((d + 1) // 2 if along_x else (w + 1) // 2)
        if along_x:                                                   # pale ridge boards
            m.fill(-1, ry, d // 2, w, ry, d // 2, "minecraft:birch_slab[type=bottom]") if d % 2 else None
        else:
            m.fill(w // 2, ry, -1, w // 2, ry, d, "minecraft:birch_slab[type=bottom]") if w % 2 else None
        tc = ["blue", "light_blue", "white", "red", "yellow"][int(rng.integers(0, 5))]
        tx = int(rng.integers(0, max(1, w - 3)))
        m.fill(tx, h + 2, d, tx + 2, h + 2, d, f"minecraft:{tc}_wool") if along_x else None
        for x in (-1, w):
            m.fill(x, 1, d + 1, x, h - 1, d + 1, "minecraft:spruce_fence")
        m.fill(-1, h, d + 1, w, h, d + 1, "minecraft:spruce_slab[type=bottom]")
    else:
        # lean-to roof: sloping from the back (high) to the front (low) over a porch
        wood = ["spruce", "dark_oak", "oak", "spruce", "mangrove"][int(rng.integers(0, 5))]
        for z in range(-1, d + 2):
            y = h + 1 + (d - z) // 3
            for x in range(-1, w + 1):
                r = rng.random()
                hay = r < 0.06
                wd = wood if r < 0.85 else ("spruce", "dark_oak", "oak")[int(r * 1000) % 3]
                s_ = "minecraft:hay_block[axis=x]" if hay else f"minecraft:{wd}_slab[type=bottom]"
                if (d - z) % 3 == 0 or z == d + 1:
                    s_ = "minecraft:hay_block[axis=x]" if hay else st(f"minecraft:{wd}_stairs", "south")
                m.set(x, y, z, s_)
                if z < d and x in (0, w - 1) and y > h + 1:
                    m.fill(x, h + 1, z, x, y - 1, z, BOARDS[(x + z) % len(BOARDS)])
        for x in (-1, w):
            m.fill(x, 1, d + 1, x, h, d + 1, "minecraft:spruce_fence")
        tc = ["brown", "white", "light_gray", "blue"][int(rng.integers(0, 4))]
        tx = int(rng.integers(0, max(1, w - 3)))
        for z in range(1, 3):
            y = h + 1 + (d - z) // 3 + 1
            m.fill(tx, y, z, tx + 2, y, z, f"minecraft:{tc}_carpet")
    # porch junk
    for (x, z, b) in ((w - 1, d + 1, "minecraft:barrel[facing=up,open=false]"), (0, d + 1, "minecraft:composter"),
                      (w - 2, d + 1, "minecraft:flower_pot")):
        if rng.random() < 0.7:
            m.set(x, 1, z, b)
    # inside
    audit = []
    r = (1, 1, w - 2, d - 2)
    P.furnish_room(m, r, 1, kind=kind, height=h - 1, seed=seed, wood="spruce", tracker=tracker, doors=[(dx, d - 1)])
    txt, ok = P.audit_props(m, [r], 1, h - 1)
    if not ok:
        audit.append(txt)
    return m, audit


KINDS = ["bedroom", "kitchen", "storage", "bedroom", "workshop", "living"]
ROOF_SETS = [("minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles"), ("minecraft:mud_brick_stairs", "minecraft:mud_bricks"),
             ("minecraft:dark_oak_stairs", "minecraft:dark_oak_planks"), ("minecraft:spruce_stairs", "minecraft:spruce_planks"),
             ("minecraft:cobbled_deepslate_stairs", "minecraft:cobbled_deepslate")]


def town(bb, tracker, audit, rng):
    taken = []
    k = 0
    GX, GZ = np.arange(N)[:, None], np.arange(N)[None, :]
    L = lane(GX, GZ)
    near = L.copy()
    near[1:, :] |= L[:-1, :]; near[:-1, :] |= L[1:, :]; near[:, 1:] |= L[:, :-1]; near[:, :-1] |= L[:, 1:]
    cands = [(int(rng.integers(TOWN[0] - 4, TOWN[2] + 4)), int(rng.integers(TOWN[1] - 6, TOWN[3] + 4))) for _ in range(3000)]
    cands.sort(key=lambda p: (p[0] - 72) ** 2 + (p[1] - 65) ** 2 + rng.random() * 300)
    sq = (58, 54, 86, 76)

    def face(cx, cz):
        best, rot = 99, 0
        for (dx, dz, r) in ((0, 1, 0), (0, -1, 2), (1, 0, 1), (-1, 0, 3)):
            for s_ in range(1, 12):
                x, z = int(cx + dx * s_), int(cz + dz * s_)
                if 0 <= x < N and 0 <= z < N and L[x, z]:
                    if s_ < best:
                        best, rot = s_, r
                    break
        return rot
    for (x, z0) in cands:
        if k >= 46:
            break
        w, d = int(rng.integers(5, 10)), int(rng.integers(6, 9))
        rot = face(x + w / 2, z0 + d / 2)
        W, D = (w, d) if rot % 2 == 0 else (d, w)
        box = (x - 1, z0 - 1, x + W, z0 + D + 1)
        if box[0] < 2 or box[2] > N - 3 or box[1] < 2 or box[3] > N - 3:
            continue
        if any(a <= box[2] + 1 and box[0] <= c + 1 and b_ <= box[3] + 1 and box[1] <= e + 1 for (a, b_, c, e) in taken + [sq]):
            continue
        sub = (slice(box[0], box[2] + 1), slice(box[1], box[3] + 1))
        if L[sub].any() or not land(GX[sub[0]], GZ[:, sub[1]]).all() or (SHORE(GX[sub[0]], GZ[:, sub[1]]) < 5).any():
            continue
        if np.abs(height(GX[sub[0]], GZ[:, sub[1]]) - GY).max() > 1:
            continue
        mod, au = shack(seed_of("ebs", k), w, d, tracker, KINDS[k % len(KINDS)])
        audit += au
        place_house(bb, mod, w, d, x, GY, z0, rot)
        taken.append(box)
        k += 1
    # shacks on stilts along the riverbank
    for x in range(30, 116, 11):
        z = int(RIVER(x)) - 11
        if not land(np.array([[x + 3]]), np.array([[z + 3]]))[0, 0]:
            continue
        mod, au = shack(seed_of("ebr", x), 6, 6, tracker, "bedroom")
        audit += au
        place_house(bb, mod, 6, 6, x, GY, z, 0)
        taken.append((x - 1, z - 1, x + 6, z + 8))
        k += 1
    print("shacks:", k)
    return taken


def square(bb, tracker, audit):
    """Toko's dango stall, the soup kitchen and Kyoshiro's gambling den round a muddy square."""
    cx, cz = 72, 65
    NT.cover(bb, cx - 12, cz - 9, cx + 12, cz + 9, lambda X, Z: X * 0 + GY, LANE, 2241)
    # dango stall: a cart with a red umbrella, skewers (end rods), a bench
    sx, sz = cx - 8, cz - 4
    bb.fill(sx, GY + 1, sz, sx + 3, GY + 1, sz, "minecraft:spruce_planks")
    bb.set(sx, GY + 1, sz + 1, "minecraft:spruce_trapdoor[facing=north,half=top,open=false]")
    bb.set(sx + 1, GY + 2, sz, "minecraft:pink_candle[candles=3,lit=false]")
    bb.set(sx + 2, GY + 2, sz, "minecraft:green_candle[candles=3,lit=false]")
    bb.set(sx + 3, GY + 2, sz, "minecraft:flower_pot")
    bb.fill(sx + 1, GY + 2, sz + 2, sx + 1, GY + 5, sz + 2, "minecraft:bamboo_fence")
    bb.fill_where(sx - 2, GY + 6, sz - 1, sx + 4, GY + 6, sz + 5, lambda X, yy, Z: np.hypot(X - sx - 1, Z - sz - 2) <= 3.2, "minecraft:red_wool")
    bb.set(sx + 1, GY + 7, sz + 2, "minecraft:red_carpet")
    for x in (sx, sx + 1, sx + 2):
        bb.set(x, GY + 1, sz + 4, st("minecraft:spruce_stairs", "north"))
    # soup kitchen: a lean-to over a big pot, crates and bowls
    kx, kz = cx + 4, cz - 6
    for (x, z) in ((kx, kz), (kx + 6, kz), (kx, kz + 4), (kx + 6, kz + 4)):
        bb.fill(x, GY + 1, z, x, GY + 3, z, "minecraft:spruce_fence")
    bb.fill(kx - 1, GY + 4, kz - 1, kx + 7, GY + 4, kz + 5, "minecraft:spruce_slab[type=bottom]")
    bb.set(kx + 3, GY + 1, kz + 2, "minecraft:campfire[lit=true]")
    bb.set(kx + 3, GY + 2, kz + 2, "minecraft:cauldron") if False else None
    bb.set(kx + 2, GY + 1, kz + 2, "minecraft:water_cauldron[level=3]")
    for (x, z) in ((kx + 1, kz + 4), (kx + 5, kz), (kx + 5, kz + 4)):
        bb.set(x, GY + 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.fill(kx + 1, GY + 1, kz, kx + 3, GY + 1, kz, "onepiece:spruce_table[facing=north]")
    # Kyoshiro's gambling den: dark timber, two floors, lanterns, a dice board
    w, d = 14, 10
    gx, gz = cx - 7, cz + 4
    m = BigBuild(seed=2242, y_min=-4, y_max=30)
    m.fill(0, -3, 0, w - 1, 0, d - 1, "minecraft:stone_bricks")
    m.fill(0, 0, 0, w - 1, 0, d - 1, "minecraft:dark_oak_planks")
    for f in range(2):
        y0 = f * 5
        m.fill(0, y0 + 1, 0, w - 1, y0 + 4, d - 1, "minecraft:dark_oak_planks")
        m.fill(1, y0 + 1, 1, w - 2, y0 + 4, d - 2, AIR)
        if f:
            m.fill(1, y0, 1, w - 2, y0, d - 2, "minecraft:dark_oak_planks")
        for x in range(0, w, 3):
            m.fill(x, y0 + 1, 0, x, y0 + 4, 0, "minecraft:dark_oak_log[axis=y]"); m.fill(x, y0 + 1, d - 1, x, y0 + 4, d - 1, "minecraft:dark_oak_log[axis=y]")
        for x in range(1, w - 1):
            if x % 3:
                m.set(x, y0 + 2, d - 1, "minecraft:red_stained_glass_pane"); m.set(x, y0 + 3, d - 1, "minecraft:red_stained_glass_pane")
    m.fill(w // 2 - 1, 1, d - 1, w // 2, 2, d - 1, AIR)
    m.fill(-1, 5, d, w, 5, d, st("minecraft:deepslate_tile_stairs", "north"))
    P.gable_roof(m, -1, -1, w, d, 11, "minecraft:deepslate_tile_stairs", gable_fill="minecraft:dark_oak_planks", overhang=1)
    for x in range(1, w - 1, 3):
        m.set(x, 4, d + 1, "minecraft:red_wool") if False else m.set(x, 4, d, "minecraft:lantern[hanging=true]")
    m.fill(1, 1, 1, 1, 6, 1, "minecraft:ladder[facing=south]")
    m.set(1, 5, 1, "minecraft:ladder[facing=south]")
    # the dice board and cushions on the ground floor
    m.fill(4, 1, 3, 9, 1, 5, "onepiece:low_table[facing=north]")
    for x in range(4, 10, 2):
        m.set(x, 1, 2, "minecraft:red_carpet"); m.set(x, 1, 6, "minecraft:red_carpet")
    m.set(6, 2, 4, "minecraft:white_candle[candles=1,lit=true]")
    tr = []
    P.furnish_room(m, (1, 1, w - 2, d - 2), 6, kind="bedroom", height=4, seed=2243, wood="dark_oak", tracker=tracker, doors=[(1, 1)])
    place_house(bb, m, w, d, gx, GY, gz, 0)
    # laundry lines across the square
    for (ax, az, bx2) in ((cx - 12, cz + 1, cx - 4), (cx + 2, cz + 1, cx + 11)):
        bb.fill(ax, GY + 1, az, ax, GY + 4, az, "minecraft:spruce_fence")
        bb.fill(bx2, GY + 1, az, bx2, GY + 4, az, "minecraft:spruce_fence")
        bb.fill(ax + 1, GY + 4, az, bx2 - 1, GY + 4, az, "minecraft:tripwire[attached=false,disarmed=false,east=true,north=false,powered=false,south=false,west=true]")
        for x in range(ax + 1, bx2, 2):
            bb.set(x, GY + 3, az, ("minecraft:white_banner[rotation=0]", "minecraft:light_gray_banner[rotation=0]",
                                    "minecraft:brown_banner[rotation=0]")[x % 3]) if False else None
    return [(cx - 13, cz - 10, cx + 13, cz + 16)]


def shrine(bb, x, z):
    y = hy(x, z)
    bb.fill(x - 3, y, z - 3, x + 3, y, z + 3, "minecraft:cobblestone")
    bb.fill(x - 2, y + 1, z - 2, x + 2, y + 3, z + 1, "minecraft:spruce_planks")
    bb.fill(x - 1, y + 1, z + 1, x + 1, y + 3, z + 1, AIR)
    P.gable_roof(bb, x - 3, z - 3, x + 3, z + 2, y + 4, "minecraft:dark_oak_stairs", gable_fill="minecraft:spruce_planks", overhang=0)
    bb.set(x, y + 1, z - 1, "minecraft:candle[candles=4,lit=true]")
    bb.set(x, y + 1, z, "minecraft:bell[attachment=floor,facing=south]")
    tz = z + 6
    for dx in (-3, 3):
        bb.fill(x + dx, y + 1, tz, x + dx, y + 5, tz, "minecraft:red_concrete")
    bb.fill(x - 4, y + 6, tz, x + 4, y + 6, tz, "minecraft:red_concrete")
    bb.fill(x - 5, y + 7, tz, x + 5, y + 7, tz, "minecraft:black_concrete")
    bb.fill(x - 3, y + 4, tz, x + 3, y + 4, tz, "minecraft:red_concrete")
    return (x - 6, z - 4, x + 6, tz + 1)


def grave_mound(bb, x, z, rng):
    """The grave of Oden's retainers: a grassy mound ringed with stones, nine sword markers, flowers and sake."""
    y = hy(x, z)
    bb.fill_where(x - 6, y - 1, z - 6, x + 6, y + 3, z + 6,
                  lambda X, yy, Z: (X - x) ** 2 + ((yy - y + 1) * 2.2) ** 2 + (Z - z) ** 2 <= 30, "minecraft:dirt")
    bb.fill_where(x - 6, y - 1, z - 6, x + 6, y + 3, z + 6,
                  lambda X, yy, Z: ((X - x) ** 2 + ((yy - y + 1) * 2.2) ** 2 + (Z - z) ** 2 <= 30)
                  & ((X - x) ** 2 + ((yy - y) * 2.2) ** 2 + (Z - z) ** 2 > 30), "minecraft:grass_block")
    top = y + 2
    for k in range(9):
        a = k * 2 * math.pi / 9
        sx, sz = round(x + 3 * math.cos(a)), round(z + 3 * math.sin(a))
        g = y + 1
        while bb.names[bb.get_region(sx, g + 1, sz, sx, g + 1, sz)[0, 0, 0]] not in (None, "", "minecraft:air"):
            g += 1
        bb.set(sx, g + 1, sz, "minecraft:lightning_rod")
    for k in range(14):
        a = k * 2 * math.pi / 14
        bx, bz = round(x + 7.5 * math.cos(a)), round(z + 7.5 * math.sin(a))
        bb.set(bx, hy(bx, bz) + 1, bz, "minecraft:mossy_cobblestone_wall" if k % 2 else "minecraft:cobblestone")
    bb.set(x, top + 1, z, "minecraft:stone_brick_wall")
    bb.set(x, top + 2, z, "minecraft:stone_brick_wall")
    bb.set(x + 1, y + 1, z + 6, "minecraft:poppy") if False else None
    return (x - 9, z - 9, x + 9, z + 9)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or lane(X, Z)[0, 0]:
            continue
        if rect_d(X, Z, TOWN)[0, 0] == 0 and rng.random() < 0.85:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(5, 9)), ("spruce", "oak", "dark_oak", "spruce")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 45:
            break
    # broken carts and junk piles in the lanes
    for (x, z) in ((40, 50), (96, 76), (58, 80), (110, 54)):
        y = hy(x, z)
        bb.fill(x, y + 1, z, x + 2, y + 1, z, "minecraft:spruce_slab[type=top]")
        bb.set(x - 1, y + 1, z, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true]")
        bb.set(x + 1, y + 2, z, "minecraft:barrel[facing=east,open=false]")
        bb.set(x + 3, y + 1, z + 1, "minecraft:spruce_fence")
    print("trees:", k)


def design():
    bb = BigBuild(seed=2220, y_min=-14, y_max=60)
    tracker = P.PropTracker(2220)
    audit = []
    rng = np.random.default_rng(2220)
    terrain(bb)
    taken = square(bb, tracker, audit)
    taken += town(bb, tracker, audit, rng)
    taken.append(shrine(bb, 112, 64))
    taken.append(grave_mound(bb, HILL[0], HILL[1], rng))
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2290, density=0.22,
              kinds=["minecraft:short_grass", "minecraft:dead_bush", "minecraft:short_grass", "minecraft:fern", "minecraft:short_dry_grass"],
              flowers=["minecraft:dandelion", "minecraft:oxeye_daisy"],
              mask=lambda X, Z: land(X, Z) & ~lane(X, Z) & (rect_d(X, Z, (58, 54, 86, 82)) > 1))
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
    b.chest(66, GY + 1, 72, "wano", "east")
    b.chest(HILL[0] + 2, hy(HILL[0] + 2, HILL[1] + 7) + 1, HILL[1] + 7, "easy", "north")
    return b, 0
