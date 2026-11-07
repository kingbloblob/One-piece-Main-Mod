"""The Gray Terminal v2 outside Goa Kingdom, redesigned with the Minecraft Builder skill.

Along the north runs the kingdom's great white wall with round towers and blue cone roofs, the gate and its bridge
over the ditch, the roofs and spires of the High Town peeping over it. South of the wall, the vast junk heap: hills of
scrap, rotting timber, broken furniture, barrels and rusted metal, smouldering fires sending up smoke, crows on the
heaps, puddles of muck. Shanties patched from boards, sheet metal and tarps crowd the paths between the heaps, with
a trader's stall, a rag-and-bone yard and a soup pot. To the south the forest of Mt. Colubo begins and the shore
falls away to the sea. 160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.ebisu_town import shack

SID = "gray_terminal"
TITLE = "Gray Terminal"
# v3 (2026-10-30): Goa's wall is twice as tall (40) with big drum towers, a gatehouse and a real royal castle
# (keep ~85 up) over the High Town, so the kingdom towers over the junk heaps.
CUTS = [6, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
SHORE = NT.outline(80, 84, 72, 2720, wobble=0.07)
GY = 3
WALL_Z = 42                         # Goa's wall line
DUMP = (16, 54, 144, 116)
FOREST_Z = 122

DIRT = [("minecraft:coarse_dirt", 0.3), ("minecraft:packed_mud", 0.15), ("minecraft:mud", 0.1), ("minecraft:dirt", 0.15),
        ("minecraft:rooted_dirt", 0.1), ("minecraft:podzol", 0.1), ("minecraft:tuff", 0.1)]
FOREST = [("minecraft:grass_block", 0.5), ("minecraft:podzol", 0.18), ("minecraft:moss_block", 0.1), ("minecraft:coarse_dirt", 0.1),
          ("minecraft:rooted_dirt", 0.12)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.15), ("minecraft:cobblestone", 0.25)]
SAND = [("minecraft:sand", 0.55), ("minecraft:clay", 0.2), ("minecraft:stone", 0.25)]
JUNK = [("minecraft:spruce_planks", 0.1), ("minecraft:oak_planks", 0.07), ("minecraft:stripped_dark_oak_wood", 0.06),
        ("minecraft:coarse_dirt", 0.14), ("minecraft:packed_mud", 0.08), ("minecraft:cobblestone", 0.08),
        ("minecraft:weathered_cut_copper", 0.02), ("minecraft:exposed_copper", 0.02), ("minecraft:dark_oak_planks", 0.06), ("minecraft:mud", 0.05),
        ("minecraft:brown_wool", 0.04), ("minecraft:gray_wool", 0.04), ("minecraft:light_gray_terracotta", 0.05),
        ("minecraft:bone_block", 0.03), ("minecraft:dried_kelp_block", 0.04), ("minecraft:tuff", 0.06), ("minecraft:mud_bricks", 0.06)]
DEBRIS = ["minecraft:barrel[facing=up,open=false]", "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false]",
          "minecraft:oak_fence", "minecraft:iron_bars", "minecraft:cobblestone_wall", "minecraft:dead_bush", "minecraft:chain[axis=x]",
          "minecraft:spruce_slab[type=bottom]", "minecraft:composter", "minecraft:cauldron", "minecraft:flower_pot",
          "minecraft:anvil[facing=north]", "minecraft:chipped_anvil[facing=east]", "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]",
          "minecraft:grindstone[face=floor,facing=north]", "minecraft:lantern[hanging=false]", "minecraft:skeleton_skull[rotation=3]"]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def paths(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = np.abs(X - (80 + 10 * np.sin(Z * 0.05))) <= 2                      # the main track from the gate south
    m |= np.abs(Z - (72 + 6 * np.sin(X * 0.07))) <= 2
    m |= np.abs(Z - (100 + 5 * np.sin(X * 0.09 + 1))) <= 1.5
    m |= np.abs(X - (40 + 4 * np.sin(Z * 0.1))) <= 1.5
    m |= np.abs(X - (120 + 4 * np.sin(Z * 0.08))) <= 1.5
    return m & (Z > WALL_Z + 6) & (Z < FOREST_Z + 4)


def heap(X, Z):
    """Junk heap height above the ground: big lumpy hills, flat on the paths."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    h = np.clip(NT.fbm(X, Z, 2741, 16) - 0.36, 0, 1) * 48 + np.clip(NT.noise(X, Z, 2742, 5) - 0.55, 0, 1) * 6
    h = h * np.clip(1 - rect_d(X, Z, DUMP) / 6.0, 0, 1)
    h = np.where(paths(X, Z), 0, h)
    return np.round(h)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 4 + NT.fbm(X, Z, 2722, 26) * 12 - 3
    h = h * np.clip((d - 1.5) / 10.0, 0, 1)
    flat = np.clip(rect_d(X, Z, (8, 12, 152, 116)) / 10.0, 0, 1)
    h = GY * (1 - flat) + h * flat
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
HEAP = heap(np.arange(N)[:, None], np.arange(N)[None, :]).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def steep(X, Z):
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 2


def land(X, Z):
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2731, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2732, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, FOREST, 2733,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z) & ((Z >= FOREST_Z) | (Z < WALL_Z + 2)), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, DIRT, 2734,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z) & (Z < FOREST_Z) & (Z >= WALL_Z + 2), core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


def junk(bb, rng, taken):
    """Pile the junk: solid mixed rubbish up to the heap height, debris and dead bushes strewn over the tops."""
    def blocked(x, z):
        return any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken)
    mask = np.zeros((N, N), bool)
    for x in range(N):
        for z in range(N):
            mask[x, z] = HEAP[x, z] > 0 and land(np.array([[x]]), np.array([[z]]))[0, 0] and not blocked(x, z)
    top = lambda X, Z: HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] \
        + np.where(mask[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)],
                   HEAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)], 0)
    TOP = top(np.arange(N)[:, None], np.arange(N)[None, :])
    cum = np.cumsum([w for _, w in JUNK]); cum = cum / cum[-1]
    ymax = int(TOP.max()) + 1
    for i, (blk, _) in enumerate(JUNK):
        lo, hi = (cum[i - 1] if i else 0.0), cum[i]

        def f(X, Y, Z, lo=lo, hi=hi):
            Xc, Zc = np.clip(X, 0, N - 1), np.clip(Z, 0, N - 1)
            r = (NT.noise(X + Y * 3, Z - Y * 2, 2752, 4) * 0.6 + NT.noise(X, Z + Y * 2, 2753, 9) * 0.4)
            r = np.clip((r - 0.2) / 0.6, 0, 0.999)
            return mask[Xc, Zc] & (Y <= TOP[Xc, Zc]) & (Y > HMAP[Xc, Zc]) & (r >= lo) & (r < hi)
        bb.fill_where(0, GY - 2, 0, N - 1, ymax, N - 1, f, blk)
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(2, N - 2)), int(rng.integers(2, N - 2))
        if not mask[x, z]:
            continue
        y = int(top(np.array([x]), np.array([z]))[0])
        r = rng.random()
        if r < 0.05:                                      # smouldering fire with smoke
            bb.set(x, y + 1, z, "minecraft:campfire[lit=true,signal_fire=true]")
        elif r < 0.12:                                    # a broken cart wheel / board leaning
            bb.fill(x, y + 1, z, x, y + 2, z, "minecraft:spruce_fence")
            bb.set(x + 1, y + 1, z, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true]")
        else:
            bb.set(x, y + 1, z, DEBRIS[int(rng.integers(len(DEBRIS)))])
        k += 1
        if k > 700:
            break
    # puddles of muck in hollows
    for _ in range(40):
        x, z = int(rng.integers(DUMP[0], DUMP[2])), int(rng.integers(DUMP[1], DUMP[3]))
        if mask[x, z] or paths(np.array([[x]]), np.array([[z]]))[0, 0] or blocked(x, z):
            continue
        y = hy(x, z)
        bb.fill_where(x - 2, y, z - 2, x + 2, y, z + 2, lambda X, Y, Z: (np.hypot(X - x, Z - z) <= 1.8) & ~mask[np.clip(X, 0, N - 1), np.clip(Z, 0, N - 1)],
                      "minecraft:water")
        bb.fill_where(x - 2, y - 1, z - 2, x + 2, y - 1, z + 2, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 1.8, "minecraft:mud")


def goa_wall(bb, rng):
    """The kingdom wall: thick white stone, battlements, round towers with blue cone roofs, the gate and its bridge
    over the ditch, the High Town's roofs and spires showing over it."""
    y0 = hy(80, WALL_Z)
    H = 40                              # v3: was 20, dwarfed by the junk heaps (up to ~50)
    xs_ok = [x for x in range(N) if SHORE(np.array([[x]]), np.array([[WALL_Z]]))[0, 0] > 4]
    WX1, WX2 = min(xs_ok), max(xs_ok)
    for x in range(WX1, WX2 + 1):
        g = hy(x, WALL_Z)
        bb.fill(x, g - 3, WALL_Z - 3, x, g + H, WALL_Z + 2, "minecraft:smooth_stone" if x % 9 else "minecraft:stone_bricks")
        bb.fill(x, g + H - 6, WALL_Z + 3, x, g + H - 6, WALL_Z + 3, "minecraft:stone_brick_slab[type=top]")
        for z in (WALL_Z - 3, WALL_Z + 2):
            if x % 2:
                bb.set(x, g + H + 1, z, "minecraft:stone_bricks")
        bb.fill(x, g + H, WALL_Z - 2, x, g + H, WALL_Z + 1, "minecraft:polished_andesite")
        # the ditch in front
        for z in range(WALL_Z + 3, WALL_Z + 7):
            bb.fill(x, g - 2, z, x, g, z, "minecraft:water" if z < WALL_Z + 6 else "minecraft:stone_bricks")
            bb.set(x, g - 3, z, "minecraft:mud")
    for tx in sorted(set([WX1 + 3, WX2 - 3] + list(range(WX1 + 30, WX2 - 20, 28)))):
        g = hy(tx, WALL_Z)
        bb.fill_where(tx - 8, g - 3, WALL_Z - 8, tx + 8, g + H + 12, WALL_Z + 8, lambda X, Y, Z: np.hypot(X - tx, Z - WALL_Z) <= 6.5,
                      "minecraft:white_concrete")
        for yy in (g + 12, g + 26, g + H):                              # string courses
            bb.fill_where(tx - 8, yy, WALL_Z - 8, tx + 8, yy, WALL_Z + 8, lambda X, Y, Z: np.hypot(X - tx, Z - WALL_Z) <= 7.0,
                          "minecraft:stone_bricks")
        bb.fill_where(tx - 8, g + H + 12, WALL_Z - 8, tx + 8, g + H + 13, WALL_Z + 8, lambda X, Y, Z: np.hypot(X - tx, Z - WALL_Z) <= 7.4,
                      "minecraft:stone_bricks")
        for k in range(16):
            r = 7.6 - k * 0.48
            bb.fill_where(tx - 8, g + H + 14 + k, WALL_Z - 8, tx + 8, g + H + 14 + k, WALL_Z + 8,
                          lambda X, Y, Z: np.hypot(X - tx, Z - WALL_Z) <= max(r, 0.5), "minecraft:blue_terracotta" if k % 3 else "minecraft:light_blue_terracotta")
        bb.fill(tx, g + H + 30, WALL_Z, tx, g + H + 32, WALL_Z, "minecraft:gold_block")
        for yy in range(g + 6, g + H + 10, 7):
            bb.set(tx, yy, WALL_Z + 6, "minecraft:black_stained_glass"); bb.set(tx, yy + 1, WALL_Z + 6, "minecraft:black_stained_glass")
    # the gate
    gx = 80
    g = hy(gx, WALL_Z)
    bb.fill(gx - 9, g + 1, WALL_Z + 3, gx + 9, g + H + 4, WALL_Z + 5, "minecraft:stone_bricks")      # the gatehouse front
    bb.fill(gx - 9, g + H + 5, WALL_Z + 3, gx + 9, g + H + 5, WALL_Z + 5, "minecraft:stone_brick_slab[type=bottom]")
    bb.fill(gx - 5, g + 1, WALL_Z - 3, gx + 5, g + 14, WALL_Z + 5, AIR)
    bb.fill_where(gx - 6, g + 13, WALL_Z - 3, gx + 6, g + 19, WALL_Z + 5, lambda X, Y, Z: ((X - gx) / 5.5) ** 2 + ((Y - g - 13) / 5.5) ** 2 <= 1, AIR)
    bb.fill(gx - 5, g + 12, WALL_Z + 2, gx + 5, g + 12, WALL_Z + 2, "minecraft:iron_bars")
    bb.fill(gx - 5, g + 13, WALL_Z + 2, gx + 5, g + 17, WALL_Z + 2, "minecraft:iron_bars")
    for x in range(gx - 8, gx + 9, 4):                                                          # Goa's crest band
        bb.set(x, g + H - 2, WALL_Z + 6, "minecraft:blue_wall_banner[facing=south]")
    for z in range(WALL_Z - 3, WALL_Z + 3):
        bb.fill(gx - 4, g, z, gx + 4, g, z, "minecraft:stone_bricks")
    for z in range(WALL_Z + 3, WALL_Z + 8):                 # the bridge over the ditch
        bb.fill(gx - 3, g, z, gx + 3, g, z, "minecraft:spruce_planks")
        bb.set(gx - 4, g + 1, z, "minecraft:spruce_fence"); bb.set(gx + 4, g + 1, z, "minecraft:spruce_fence")
    for x in (gx - 6, gx + 6):
        bb.set(x, g + 6, WALL_Z + 3, "minecraft:lantern[hanging=false]")
        bb.set(x, g + 12, WALL_Z + 3, "minecraft:blue_wall_banner[facing=south]")
    # High Town beyond: rows of tall roofs and a palace spire showing over the wall
    for k in range(18):
        x = 6 + k * 8 + int(rng.integers(-2, 3))
        z = int(rng.integers(8, WALL_Z - 8))
        if not land(np.array([[x]]), np.array([[z]]))[0, 0] or SHORE(np.array([[x]]), np.array([[z]]))[0, 0] < 6:
            continue
        g2 = hy(x, z)
        hh = int(rng.integers(24, 42))
        bb.fill(x - 3, g2, z - 3, x + 3, g2 + hh, z + 3, ("minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone")[k % 3])
        P.gable_roof(bb, x - 4, z - 4, x + 4, z + 4, g2 + hh + 1, ("minecraft:blue_terracotta", "minecraft:red_nether_brick_stairs",
                                                                     "minecraft:deepslate_tile_stairs")[k % 3] if k % 3 else "minecraft:dark_prismarine_stairs",
                     gable_fill="minecraft:white_terracotta", overhang=0)
        for yy in range(g2 + 3, g2 + hh, 4):
            for (a, b) in ((x, z + 3), (x - 3, z), (x + 3, z)):
                bb.set(a, yy, b, "minecraft:glass_pane")
    # Goa's royal palace over the High Town (v3: a real castle, keep ~85 up, not a single 54-tall spire)
    px, pz = 104, 22
    g2 = hy(px, pz)
    bb.fill(px - 13, g2 - 2, pz - 9, px + 13, g2 + 44, pz + 9, "minecraft:white_concrete")
    for yy in range(g2 + 6, g2 + 44, 6):
        bb.fill(px - 13, yy, pz + 9, px + 13, yy, pz + 9, "minecraft:stone_bricks")
        for x in range(px - 11, px + 12, 3):
            bb.fill(x, yy + 2, pz + 9, x, yy + 4, pz + 9, "minecraft:blue_stained_glass_pane")
    P.hip_roof(bb, px - 14, pz - 10, px + 14, pz + 10, g2 + 45, "minecraft:blue_terracotta" if False else "minecraft:dark_prismarine_stairs", overhang=1)

    def spire(tx, tz, r, h, cone):
        bb.fill_where(tx - r - 2, g2 - 2, tz - r - 2, tx + r + 2, g2 + h, tz + r + 2, lambda X, Y, Z: np.hypot(X - tx, Z - tz) <= r,
                      "minecraft:white_concrete")
        bb.fill_where(tx - r - 2, g2 + h, tz - r - 2, tx + r + 2, g2 + h + 1, tz + r + 2,
                      lambda X, Y, Z: np.hypot(X - tx, Z - tz) <= r + 0.8, "minecraft:stone_bricks")
        for k in range(cone):
            rr = (r + 1.2) * (1 - k / cone)
            bb.fill_where(tx - r - 2, g2 + h + 2 + k, tz - r - 2, tx + r + 2, g2 + h + 2 + k, tz + r + 2,
                          lambda X, Y, Z, rr=rr: np.hypot(X - tx, Z - tz) <= max(rr, 0.5),
                          "minecraft:blue_terracotta" if k % 4 else "minecraft:light_blue_terracotta")
        bb.fill(tx, g2 + h + 2 + cone, tz, tx, g2 + h + 5 + cone, tz, "minecraft:gold_block")
        for yy in range(g2 + 8, g2 + h, 8):
            bb.set(tx, yy, tz + r, "minecraft:blue_stained_glass")
    spire(px, pz, 8, 62, 20)
    for (dx, dz, h) in ((-15, -6, 50), (15, -6, 54), (-15, 8, 46), (15, 8, 48)):
        spire(px + dx, pz + dz, 4, h, 13)
    return (0, 0, N, WALL_Z + 8)


def shanties(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(3000):
        w, d = int(rng.integers(5, 9)), int(rng.integers(5, 8))
        x0, z0 = int(rng.integers(DUMP[0], DUMP[2] - w)), int(rng.integers(WALL_Z + 9, FOREST_Z - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 3)[None, :]
        if (~land(xs, zs)).any() or paths(xs, zs).any() or (np.abs(HMAP[xs, zs] - GY) > 1).any():
            continue
        # must face a path: a path cell 3-4 south of the door
        if not paths(np.arange(x0, x0 + w)[:, None], np.array([[z0 + d + 3, z0 + d + 4, z0 + d + 5]])).any():
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d + 2)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        mod, au = shack(seed_of("gts", k), w, d, tracker, ("bedroom", "kitchen", "storage", "workshop")[k % 4])
        audit += au
        place_house(bb, mod, w, d, x0, GY, z0, 0)
        taken.append(box)
        k += 1
        if k >= 34:
            break
    print("shanties:", k)


def stalls(bb, taken):
    """A trader's stall at the crossing, a soup pot, a rag-and-bone yard fenced with scrap."""
    cx, cz = 82, 72
    for (x, z) in ((cx + 4, cz + 4), (cx + 9, cz + 4), (cx + 4, cz + 8), (cx + 9, cz + 8)):
        bb.fill(x, GY + 1, z, x, GY + 3, z, "minecraft:spruce_fence")
    bb.fill(cx + 3, GY + 4, cz + 3, cx + 10, GY + 4, cz + 9, "minecraft:brown_carpet") if False else \
        bb.fill(cx + 3, GY + 4, cz + 3, cx + 10, GY + 4, cz + 9, "minecraft:brown_wool")
    bb.fill(cx + 5, GY + 1, cz + 4, cx + 8, GY + 1, cz + 4, "minecraft:barrel[facing=up,open=false]")
    bb.set(cx + 6, GY + 2, cz + 4, "minecraft:flower_pot"); bb.set(cx + 7, GY + 2, cz + 4, "minecraft:lantern[hanging=false]")
    bb.set(cx + 6, GY + 1, cz + 7, "minecraft:campfire[lit=true,signal_fire=false]")
    bb.set(cx + 7, GY + 1, cz + 7, "minecraft:water_cauldron[level=2]")
    taken.append((cx + 2, cz + 2, cx + 11, cz + 10))
    yx, yz = 22, 50
    for x in range(yx, yx + 14):
        for z in (yz, yz + 10):
            bb.set(x, GY + 1, z, ("minecraft:iron_bars", "minecraft:oak_fence", "minecraft:cobblestone_wall")[(x + z) % 3])
    for z in range(yz, yz + 11):
        bb.set(yx, GY + 1, z, "minecraft:iron_bars"); bb.set(yx + 13, GY + 1, z, "minecraft:oak_fence") if z != yz + 5 else None
    for (x, z, b) in ((yx + 3, yz + 3, "minecraft:anvil[facing=north]"), (yx + 5, yz + 6, "minecraft:cauldron"),
                      (yx + 8, yz + 3, "minecraft:barrel[facing=up,open=false]"), (yx + 9, yz + 3, "minecraft:barrel[facing=up,open=false]"),
                      (yx + 10, yz + 7, "minecraft:grindstone[face=floor,facing=north]"), (yx + 4, yz + 8, "minecraft:composter")):
        bb.set(x, GY + 1, z, b)
    taken.append((yx - 1, yz - 1, yx + 14, yz + 11))


def forest(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(FOREST_Z - 6, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 3 or HEAP[x, z] > 0:
            continue
        if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 12)), ("oak", "spruce", "dark_oak", "birch")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 60:
            break
    # dead trees in the dump
    for _ in range(14):
        x, z = int(rng.integers(DUMP[0], DUMP[2])), int(rng.integers(DUMP[1], DUMP[3]))
        if HEAP[x, z] > 0 or paths(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        if any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
            continue
        y = hy(x, z)
        hh = int(rng.integers(4, 8))
        bb.fill(x, y + 1, z, x, y + hh, z, "minecraft:stripped_dark_oak_log[axis=y]")
        bb.set(x + 1, y + hh - 1, z, "minecraft:dark_oak_fence"); bb.set(x - 1, y + hh - 2, z, "minecraft:dark_oak_fence")
        taken.append((x - 1, z - 1, x + 1, z + 1))
    print("trees:", k)


def design():
    bb = BigBuild(seed=2720, y_min=-14, y_max=140)
    tracker = P.PropTracker(2720)
    audit = []
    rng = np.random.default_rng(2720)
    terrain(bb)
    taken = [goa_wall(bb, rng)]
    stalls(bb, taken)
    shanties(bb, tracker, audit, rng, taken)
    junk(bb, rng, taken)
    forest(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2790, density=0.18,
              kinds=["minecraft:short_grass", "minecraft:dead_bush", "minecraft:short_dry_grass", "minecraft:fern"],
              flowers=["minecraft:dandelion"], mask=lambda X, Z: land(X, Z) & ~paths(X, Z) & (Z > WALL_Z + 8))
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
    b.chest(25, GY + 1, 53, "easy", "east")
    b.chest(88, GY + 1, 76, "easy", "south")
    b.guards("bandit", ((80, 60), (40, 88), (120, 92), (66, 104)), y=GY + 1)
    return b, 0
