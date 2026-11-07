"""Nanohana v2, Alabasta's port of perfume and trade, redesigned with the Minecraft Builder skill.

A dry sandy island coast with the harbour on the north. White flat-roofed houses of two and three storeys climb in
narrow lanes from the quay, roof terraces with awnings and potted palms; down the middle runs the covered bazaar,
a long arcade roofed with striped cloth, dozens of stalls of spices, perfume, fruit, cloth and pottery; the perfume
shop with its domed roof, inns, and the restaurant where Ace and Luffy ate, with its terrace over the street. Along
the waterfront a palm-lined stone quay, long piers with dhows (lateen-sailed trading boats) moored at them, warehouses,
and the lighthouse at the harbour mouth. 168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post, palm, onion_dome
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "nanohana_port"
TITLE = "Nanohana Port"
CUTS = [4, 10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
SHORE = NT.outline(84, 96, 72, 2920, wobble=0.08)
QUAY_Z = 44
TY = 2
TOWN = (24, QUAY_Z, 144, 140)
BAZ = (78, 50, 90, 124)                    # the covered bazaar street
SMOOTH = "minecraft:smooth_sandstone"
CUT = "minecraft:cut_sandstone"
SAND_B = "onepiece:alabasta_sandstone_bricks"
PAL = dict(walls=["minecraft:white_concrete", "minecraft:white_terracotta", "minecraft:calcite"], frame=SMOOTH,
           base=[SMOOTH, CUT, "minecraft:sandstone"], floor="minecraft:birch_planks", wood="jungle", chimney=SMOOTH, parapet=SMOOTH)
PAL2 = dict(walls=[SMOOTH, "minecraft:sandstone", CUT], frame=CUT, base=["minecraft:sandstone", CUT, SMOOTH],
            floor="minecraft:birch_planks", wood="jungle", chimney=SMOOTH, parapet=SMOOTH)
DUNE = [("minecraft:sand", 0.6), ("minecraft:sandstone", 0.12), ("minecraft:smooth_sandstone", 0.06), ("minecraft:coarse_dirt", 0.08),
        ("minecraft:grass_block", 0.08), ("minecraft:terracotta", 0.06)]
PAVE = [(SMOOTH, 0.3), (CUT, 0.25), ("minecraft:sandstone", 0.2), (SAND_B, 0.15), ("minecraft:chiseled_sandstone", 0.1)]
CLOTH = ["red", "orange", "yellow", "light_blue", "white", "purple", "cyan", "lime"]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def streets(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    m = (X >= BAZ[0]) & (X <= BAZ[2]) & (Z >= BAZ[1]) & (Z <= BAZ[3])
    m |= (Z >= QUAY_Z) & (Z <= QUAY_Z + 7)
    for z in (74, 102, 128):
        m |= (np.abs(Z - z) <= 2)
    for x in (44, 120):
        m |= (np.abs(X - x) <= 2) & (Z > QUAY_Z)
    return m & (rect_d(X, Z, TOWN) == 0)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 4 + NT.fbm(X, Z, 2922, 24) * 12 - 3
    h = h * np.clip((d - 1.5) / 10.0, 0, 1)
    w = np.clip(rect_d(X, Z, TOWN) / 10.0, 0, 1)
    h = TY * (1 - w) + h * w
    h = np.where(Z < QUAY_Z, -4, h)
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


def land(X, Z):
    return (SHORE(X, Z) > 1.5) & (np.asarray(Z) >= QUAY_Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, DUNE, 2931, mask=lambda X, Z: land(X, Z), under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 2932, mask=lambda X, Z: land(X, Z) & streets(X, Z), under="minecraft:sandstone",
             core="minecraft:sandstone")
    bed = lambda X, Z: np.where((np.asarray(Z) < QUAY_Z) & (SHORE(X, Z) > -6), np.minimum(-4 - np.clip((QUAY_Z - np.asarray(Z)) * 0.3, 0, 5),
                                                                                         np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:sandstone")


def quay(bb, rng):
    xs = [x for x in range(N) if SHORE(np.array([[x]]), np.array([[QUAY_Z]]))[0, 0] > 3]
    qx1, qx2 = min(xs), max(xs)
    for x in range(qx1, qx2 + 1):
        bb.fill(x, -6, QUAY_Z, x, TY, QUAY_Z, SAND_B)
        bb.set(x, TY, QUAY_Z, CUT)
        if x % 7 == 0:
            bb.set(x, TY + 1, QUAY_Z, "onepiece:alabasta_sandstone_brick_wall")
    for x in range(qx1 + 4, qx2 - 3, 9):
        palm(bb, x, TY + 1, QUAY_Z + 5, 9 + (x % 3), (0, -1))
    # long piers and dhows
    for k, px in enumerate(range(qx1 + 12, qx2 - 8, 26)):
        L = 22
        for z in range(QUAY_Z - L, QUAY_Z):
            bb.fill(px - 1, TY - 1, z, px + 1, TY - 1, z, "minecraft:jungle_planks")
            if z % 4 == 0:
                bb.fill(px - 2, -8, z, px - 2, TY - 1, z, "minecraft:jungle_log[axis=y]")
                bb.fill(px + 2, -8, z, px + 2, TY - 1, z, "minecraft:jungle_log[axis=y]")
                bb.set(px + 2, TY, z, "minecraft:jungle_fence")
        for (side, dz) in ((-1, -8), (1, -16)):
            if k % 2 == 0 or side < 0:
                dhow(bb, px + side * 8, QUAY_Z + dz, CLOTH[(k * 2 + side) % len(CLOTH)])
    # warehouses on the quay ends
    return qx1, qx2


def dhow(bb, cx, cz, cloth):
    """A small lateen-rigged trading boat lying along z, bow north: a curved plank hull, a deck, crates and jars, a
    raked mast with a big triangular sail."""
    L, B = 16, 3
    for i in range(L):
        z = cz - L // 2 + i
        t = i / (L - 1)
        hw = max(0, round(B * math.sin(math.pi * min(1, 0.15 + t * 0.85)) + 0.2))
        for x in range(cx - hw, cx + hw + 1):
            bb.set(x, -1, z, "minecraft:jungle_planks" if abs(x - cx) < hw else "minecraft:stripped_jungle_wood")
            bb.set(x, 0, z, "minecraft:jungle_planks")
        bb.set(cx - hw, 1, z, "minecraft:jungle_fence"); bb.set(cx + hw, 1, z, "minecraft:jungle_fence")
        bb.set(cx, -2, z, "minecraft:stripped_jungle_wood")
    bb.set(cx, 1, cz - L // 2, "minecraft:stripped_jungle_wood"); bb.set(cx, 2, cz - L // 2 - 1, "minecraft:jungle_fence")
    for (dx, dz, b) in ((0, 2, "minecraft:barrel[facing=up,open=false]"), (-1, 3, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                        (1, 4, "minecraft:barrel[facing=up,open=false]"), (0, 5, "onepiece:keg[facing=north]")):
        bb.set(cx + dx, 1, cz + dz, b)
    mz = cz - 1
    bb.fill(cx, 1, mz, cx, 14, mz, "minecraft:jungle_fence")
    for k in range(13):                                         # the lateen yard: a long spar sloping fore-high
        bb.set(cx, 6 + k, mz - 6 + k, "minecraft:jungle_fence") if False else None
    for y in range(3, 15):
        z_lo = mz - (y - 3) // 2
        z_hi = mz + 1 + (14 - y) // 2
        for z in range(z_lo, z_hi + 1):
            if z != mz:
                bb.set(cx + 1, y, z, f"minecraft:{cloth}_wool" if (y + z) % 5 else "minecraft:white_wool")


def bazaar(bb, rng):
    """The covered bazaar: arcades of sandstone posts down both sides, a roof of striped cloth, stalls under it."""
    x1, z1, x2, z2 = BAZ
    y = TY
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if z % 4 == 0:
                bb.fill(x, y + 1, z, x, y + 6, z, CUT)
                bb.set(x, y + 7, z, "minecraft:chiseled_sandstone")
        if any(abs(z - s) <= 2 for s in (74, 102)):
            continue
        for x in range(x1, x2 + 1):
            c = CLOTH[(z // 6) % len(CLOTH)]
            bb.set(x, y + 7 + (1 if abs(x - (x1 + x2) / 2) < 3 else 0), z, f"minecraft:{c}_wool" if (x + z // 3) % 2 else "minecraft:white_wool")
    for z in range(z1 + 2, z2 - 1, 4):
        if any(abs(z - s) <= 3 for s in (74, 102)):
            continue
        for (x, f) in ((x1 + 1, "east"), (x2 - 1, "west")):
            k = int(rng.integers(0, 6))
            bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
            bb.set(x, y + 1, z + 1, ("minecraft:composter", "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]",
                                     "onepiece:keg[facing=north]", "minecraft:barrel[facing=up,open=false]", "minecraft:hay_block[axis=y]",
                                     "minecraft:melon")[k])
            bb.set(x, y + 2, z, ("minecraft:flower_pot", "minecraft:orange_candle[candles=3,lit=false]", "minecraft:pink_candle[candles=2,lit=false]",
                                 "minecraft:brown_mushroom", "minecraft:sea_pickle[pickles=3,waterlogged=false]", "minecraft:flower_pot")[k])
            bb.set(x, y + 1, z + 2, f"minecraft:{CLOTH[k]}_carpet")
        if z % 8 == 2:
            bb.set((x1 + x2) // 2, y + 6, z, "minecraft:lantern[hanging=true]")
            bb.fill((x1 + x2) // 2, y + 7, z, (x1 + x2) // 2, y + 7, z, "minecraft:chain[axis=y]") if False else None
    return (x1 - 1, z1, x2 + 1, z2)


def perfume_shop(bb, tracker, audit, x0, z0):
    w, d = 14, 12
    m, top, au = house_module(seed_of("perfume"), w, d, 2, "flat:purple", tracker, ["living", "storage", "bedroom"], pal=PAL,
                              timber=False, jetty=False, chimney=False)
    audit += au
    place_house(bb, m, w, d, x0, TY, z0, 3)
    onion_dome(bb, x0 + d // 2, TY + top + 1, z0 + w // 2, 4, "minecraft:purple_terracotta", tip="minecraft:gold_block")
    for z in range(z0 + 1, z0 + w - 1, 2):
        bb.set(x0 + d, TY + 2, z, "minecraft:purple_stained_glass_pane") if False else None
    return (x0 - 1, z0 - 1, x0 + d + 1, z0 + w + 1)


def restaurant(bb, tracker, audit, x0, z0):
    """The restaurant where Ace and Luffy ate: two storeys, a wide open front with tables, a terrace on the roof."""
    w, d = 18, 12
    m, top, au = house_module(seed_of("nanores"), w, d, 2, "flat:orange", tracker, ["dining", "kitchen", "dining", "bedroom"], pal=PAL2,
                              timber=False, jetty=False, chimney=True)
    audit += au
    place_house(bb, m, w, d, x0, TY, z0, 0)
    for x in range(x0, x0 + w):
        for z in range(z0 + d, z0 + d + 5):
            bb.set(x, TY, z, "minecraft:jungle_planks")
        bb.set(x, TY + 4, z0 + d + 4, "minecraft:orange_wool" if x % 2 else "minecraft:white_wool")
    for x in (x0, x0 + w - 1):
        bb.fill(x, TY + 1, z0 + d + 4, x, TY + 3, z0 + d + 4, "minecraft:jungle_fence")
    for x in range(x0 + 2, x0 + w - 2, 4):
        bb.set(x, TY + 1, z0 + d + 2, "minecraft:jungle_fence"); bb.set(x, TY + 2, z0 + d + 2, "minecraft:white_carpet")
        bb.set(x - 1, TY + 1, z0 + d + 2, "onepiece:bar_stool"); bb.set(x + 1, TY + 1, z0 + d + 2, "onepiece:bar_stool")
    return (x0 - 1, z0 - 1, x0 + w, z0 + d + 5)


def lighthouse(bb, qx1):
    x, z = qx1 + 4, QUAY_Z - 3
    for y in range(-6, 22):
        bb.fill_where(x - 3, y, z - 3, x + 3, y, z + 3, lambda X, Y, Z: np.hypot(X - x, Z - z) <= (3.2 if y < TY else 2.4),
                      SAND_B if y < TY else ("minecraft:white_terracotta" if (y // 4) % 2 else SMOOTH))
    bb.fill(x - 3, 22, z - 3, x + 3, 22, z + 3, SAND_B)
    bb.set(x, 23, z, "minecraft:glowstone")
    for (a, b) in ((x - 2, z - 2), (x + 2, z - 2), (x - 2, z + 2), (x + 2, z + 2)):
        bb.fill(a, 23, b, a, 24, b, "onepiece:alabasta_sandstone_brick_wall")
    onion_dome(bb, x, 25, z, 3, "minecraft:light_blue_terracotta", tip="minecraft:gold_block")


def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(5000):
        w, d = int(rng.integers(8, 13)), int(rng.integers(8, 11))
        x0, z0 = int(rng.integers(TOWN[0], TOWN[2] - w)), int(rng.integers(QUAY_Z + 9, TOWN[3] - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 4).any() or (np.abs(HMAP[xs, zs] - TY) > 1).any():
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        # face the nearest street
        dists = {0: min(abs(z0 + d - s) for s in (QUAY_Z + 7, 74, 102, 128)), 2: min(abs(z0 - s) for s in (QUAY_Z + 7, 74, 102, 128)),
                 3: min(abs(x0 + w - s) for s in (44, 120, BAZ[0])), 1: min(abs(x0 - s) for s in (44, 120, BAZ[2]))}
        rot = min(dists, key=dists.get)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        fl = int(rng.integers(2, 4))
        m, top, au = house_module(seed_of("nh", x0, z0), mw, md, fl, "flat:" + CLOTH[k % len(CLOTH)], tracker,
                                  [["kitchen", "living", "workshop", "dining", "bedroom"][k % 5], "bedroom", "storage"],
                                  pal=(PAL, PAL, PAL2)[k % 3], timber=False, jetty=False, chimney=False)
        audit += au
        bb.fill(x0, TY - 2, z0, x0 + w - 1, TY, z0 + d - 1, "minecraft:sandstone")
        place_house(bb, m, mw, md, x0, TY, z0, rot)
        taken.append(box)
        k += 1
        if k >= 50:
            break
    print("houses:", k)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(QUAY_Z + 2, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 4 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if rect_d(X, Z, TOWN)[0, 0] == 0 and rng.random() < 0.6:
            continue
        palm(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 11)), (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))))
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 55:
            break
    print("palms:", k)


def design():
    bb = BigBuild(seed=2920, y_min=-14, y_max=70)
    tracker = P.PropTracker(2920)
    audit = []
    rng = np.random.default_rng(2920)
    terrain(bb)
    qx1, qx2 = quay(bb, rng)
    lighthouse(bb, qx1)
    taken = [bazaar(bb, rng), (0, 0, N, QUAY_Z + 8)]
    taken.append(perfume_shop(bb, tracker, audit, 64, 78))
    taken.append(restaurant(bb, tracker, audit, 94, 56))
    town(bb, tracker, audit, rng, taken)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2990, density=0.1,
              kinds=["minecraft:dead_bush", "minecraft:short_dry_grass", "minecraft:short_grass"], flowers=["minecraft:cactus[age=0]"],
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, TOWN) > 2))
    return bb, audit


def steady(b):
    """Sand with nothing solid under it would fall when the build generates (at sea the world's water fills in under
    it): turn it into blocks that stay put."""
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
    b.chest(BAZ[0] + 1, TY + 1, 60, "easy", "east")
    return b, 0
