"""The Flower Capital of Wano v2, redesigned with the Minecraft Builder skill.

A green land of steep pine hills fading to the sea. At the north end the shogun's castle towers over the city on its
high battered stone base (ishigaki), ringed by a white wall with corner turrets and by the moat, crossed by the red
bridge: five white storeys under sweeping dark-tiled eaves, golden shachihoko on the top roof ridge, every storey
furnished. Below it the city on its level ground: the main avenue running south from the bridge under strings of
paper lanterns, cross streets and a canal lined with sakura with little red bridges; two-storey timber machiya
(posts and beams on the fronts, white plaster above, wooden lattices and noren below, tiled roofs) with shops and
homes inside; Komurasaki's red-lacquered teahouse, the bathhouse, the sake brewery, a five-storey pagoda, and the
great red torii at the city gate. 176 x 176. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, castle_eave, wing_floor, place_house, lamp_post, stair_core
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "flower_capital"
TITLE = "Flower Capital (Wano)"
CUTS = [6, 22, 34]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
SHORE = NT.outline(88, 90, 82, 1920, wobble=0.08)
CY = 4                                     # city level
CITY = (22, 62, 154, 152)
KEEP_Y = 50                                # castle grounds level (v3: on a towering rock above the city)
GROUNDS = (56, 14, 120, 52)
MOAT = 3
AVE = (85, 91)                             # main avenue x range
CANAL = (96, 99)
TILE = "minecraft:deepslate_tile_stairs"
TILEF = "minecraft:deepslate_tiles"

PAVE = [("minecraft:packed_mud", 0.3), ("minecraft:tuff", 0.2), ("minecraft:coarse_dirt", 0.15), ("minecraft:dirt_path", 0.2),
        ("minecraft:mud_bricks", 0.15)]
STONE = [("minecraft:stone_bricks", 0.3), ("minecraft:cobblestone", 0.2), ("minecraft:mossy_stone_bricks", 0.15),
         ("minecraft:andesite", 0.15), ("minecraft:mossy_cobblestone", 0.1), ("minecraft:cracked_stone_bricks", 0.1)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.1), ("minecraft:cobblestone", 0.1),
        ("minecraft:mossy_cobblestone", 0.12), ("minecraft:cobblestone", 0.08)]
SAND = [("minecraft:sand", 0.7), ("minecraft:clay", 0.15), ("minecraft:sandstone", 0.15)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def cliff_out(X, Z, y):
    """How far the castle rock reaches out past the grounds at height y: sheer and lumpy, a little wider at the foot."""
    t = np.clip((KEEP_Y - y) / (KEEP_Y - CY), 0, 1)
    return 1.0 + 9.0 * t ** 1.6 + 3.0 * NT.noise(X + Z, y * 2, 1951, 6) + 1.2 * np.sin(np.arctan2(Z - 33, X - 88) * 9 + y * 0.05)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    hills = 6 + NT.fbm(X, Z, 1921, 22) * 18
    h = hills * np.clip((d - 2) / 14.0, 0, 1)
    w = np.clip(rect_d(X, Z, CITY) / 10.0, 0, 1)
    h = CY * (1 - w) + h * w
    g = rect_d(X, Z, GROUNDS)
    h = np.where(g <= cliff_out(X, Z, CY), np.maximum(h, CY), h)    # the city floor runs right up to the cliff foot
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
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def street_mask(X, Z):
    m = (X >= AVE[0]) & (X <= AVE[1]) & (Z >= GROUNDS[3] + MOAT + 2) & (Z <= CITY[3])
    for z0 in (78, 112, 134):
        m |= (Z >= z0) & (Z <= z0 + 4) & (X >= CITY[0] + 4) & (X <= CITY[2] - 4)
    m |= (Z >= GROUNDS[3] + MOAT + 2) & (Z <= GROUNDS[3] + MOAT + 6) & (X >= 40) & (X <= 136)
    return m


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 1931,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z), under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 1932, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 1933,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 1934, mask=lambda X, Z: land(X, Z) & street_mask(X, Z), core="minecraft:stone")
    for y in range(-12, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy > -2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))), "minecraft:sand")


# ------------------------------------------------------------------ the castle
def castle(bb, tracker, audit):
    x1, z1, x2, z2 = GROUNDS
    # v3 (2026-10-30 audit: in the show the shogun's castle towers on a sheer rock high above the capital): a lumpy,
    # fluted rock butte from the city floor to KEEP_Y - 7, then the battered stone base (ishigaki) up to the grounds
    top_rock = KEEP_Y - 7
    for y in range(CY - 4, top_rock + 1):
        bb.fill_where(x1 - 16, y, max(0, z1 - 16), x2 + 16, y, z2 + 16,
                      lambda X, yy, Z, y=y: rect_d(X, Z, GROUNDS) <= cliff_out(X, Z, y), "minecraft:stone")
        for blk, th, sd in (("minecraft:andesite", 0.55, 1952), ("minecraft:tuff", 0.7, 1953), ("minecraft:deepslate", 0.8, 1954)):
            bb.fill_where(x1 - 16, y, max(0, z1 - 16), x2 + 16, y, z2 + 16,
                          lambda X, yy, Z, y=y, th=th, sd=sd: (rect_d(X, Z, GROUNDS) <= cliff_out(X, Z, y))
                          & (rect_d(X, Z, GROUNDS) > cliff_out(X, Z, y) - 3) & (NT.noise(X + Z, y * 2, sd, 4) > th), blk)
        # moss and grass tufts on the ledges where the face steps back
        if y > CY + 2:
            bb.fill_where(x1 - 16, y, max(0, z1 - 16), x2 + 16, y, z2 + 16,
                          lambda X, yy, Z, y=y: (rect_d(X, Z, GROUNDS) <= cliff_out(X, Z, y)) & (rect_d(X, Z, GROUNDS) > cliff_out(X, Z, y + 1) + 0.5)
                          & (NT.noise(X, Z, 1955, 3) > 0.45), "minecraft:moss_block")
    for y in range(top_rock - 1, KEEP_Y + 1):
        k = (KEEP_Y - y) // 3 + 1
        bb.fill(x1 - k, y, z1 - k, x2 + k, y, z2 + k, "minecraft:stone_bricks")
    for y in range(top_rock - 1, KEEP_Y):
        k = (KEEP_Y - y) // 3 + 1
        bb.mix(x1 - k, y, z1 - k, x2 + k, y, z1 - k, [b for b, _ in STONE], [w for _, w in STONE])
        bb.mix(x1 - k, y, z2 + k, x2 + k, y, z2 + k, [b for b, _ in STONE], [w for _, w in STONE])
        bb.mix(x1 - k, y, z1 - k, x1 - k, y, z2 + k, [b for b, _ in STONE], [w for _, w in STONE])
        bb.mix(x2 + k, y, z1 - k, x2 + k, y, z2 + k, [b for b, _ in STONE], [w for _, w in STONE])
    NT.cover(bb, x1, z1, x2, z2, lambda X, Z: X * 0 + KEEP_Y, [("minecraft:andesite", 0.25), ("minecraft:polished_andesite", 0.15), ("minecraft:grass_block", 0.35),
                                                             ("minecraft:moss_block", 0.1), ("minecraft:packed_mud", 0.15)], 1942,
             base=KEEP_Y - 2)
    # pines clinging to the cliff ledges
    prng = np.random.default_rng(1956)
    for _ in range(60):
        x, z = int(prng.integers(x1 - 12, x2 + 13)), int(prng.integers(max(2, z1 - 12), z2 + 13))
        if rect_d(np.array([x]), np.array([z]), GROUNDS)[0] < 2:
            continue
        for y in range(KEEP_Y - 9, CY + 6, -1):
            reg = bb.get_region(x, y - 1, z, x, y + 6, z)[0, :, 0]
            if reg[0] > 1 and (reg[1:] <= 1).all():
                P.tree(bb, x, y, z, height=int(prng.integers(5, 8)), kind="spruce", rng=prng)
                break
    # the moat round the base (on the city side) and the red bridge with its gate
    mz = z2 + 6
    for x in range(x1 - 8, x2 + 9):
        bb.fill(x, CY - 3, mz, x, CY - 1, mz + MOAT - 1, "minecraft:water")
        bb.fill(x, CY, mz, x, CY + 3, mz + MOAT - 1, AIR)
        bb.set(x, CY - 4, mz, "minecraft:mud"); bb.set(x, CY - 4, mz + 1, "minecraft:mud"); bb.set(x, CY - 4, mz + 2, "minecraft:mud")
        bb.set(x, CY, mz - 1, "minecraft:stone_bricks"); bb.set(x, CY, mz + MOAT, "minecraft:stone_bricks")
    bx = (AVE[0] + AVE[1]) // 2
    for z in range(mz - 1, mz + MOAT + 1):
        bb.fill(bx - 2, CY + 1, z, bx + 2, CY + 1, z, "minecraft:crimson_planks")
        bb.set(bx - 3, CY + 2, z, "minecraft:crimson_fence"); bb.set(bx + 3, CY + 2, z, "minecraft:crimson_fence")
    bb.set(bx - 3, CY + 3, mz - 1, "minecraft:lantern[hanging=false]"); bb.set(bx + 3, CY + 3, mz + MOAT, "minecraft:lantern[hanging=false]")
    # the climb: a gate in the cliff foot behind the bridge, a tunnel and a walled spiral stair inside the rock up to
    # the castle gate (v3: the rock is far too high for one straight flight)
    sx, sz, ss = bx - 3, z2 - 9, 7
    bb.fill(bx - 2, CY + 1, sz + ss, bx + 2, CY + 4, mz - 1, AIR)
    bb.fill(bx - 2, CY, sz + ss, bx + 2, CY, mz - 1, "minecraft:stone_bricks")
    for z in range(sz + ss, mz, 3):
        bb.set(bx - 2, CY + 3, z, "minecraft:lantern[hanging=true]")
    stair_core(bb, sx, sz, ss, CY + 1, KEEP_Y, [CY + 1, KEEP_Y + 1], "minecraft:stone_bricks", "minecraft:stone_brick_stairs", slit=None)
    bb.fill(bx - 2, CY + 1, sz + ss, bx + 2, CY + 3, sz + ss, AIR)
    bb.fill(bx - 3, CY + 1, mz - 1, bx - 3, CY + 5, mz - 1, "minecraft:dark_oak_log[axis=y]")
    bb.fill(bx + 3, CY + 1, mz - 1, bx + 3, CY + 5, mz - 1, "minecraft:dark_oak_log[axis=y]")
    bb.fill(bx - 4, CY + 6, mz - 1, bx + 4, CY + 6, mz - 1, "minecraft:dark_oak_planks")
    castle_eave(bb, bx - 4, mz - 2, bx + 4, mz - 1, CY + 6, TILE, TILEF, depth=1)
    # the white wall round the grounds, tile-capped, with corner turrets and the gatehouse
    for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        bb.fill(a, KEEP_Y + 1, b, c, KEEP_Y + 3, d, "minecraft:white_concrete")
        bb.fill(a, KEEP_Y + 1, b, c, KEEP_Y + 1, d, "minecraft:dark_oak_planks")
        bb.fill(a, KEEP_Y + 4, b, c, KEEP_Y + 4, d, "minecraft:deepslate_tile_slab[type=bottom]")
    bb.fill(bx - 2, KEEP_Y + 1, z2, bx + 2, KEEP_Y + 3, z2, AIR)
    gh = (bx - 5, z2 - 3, bx + 5, z2 + 1)
    bb.fill(gh[0], KEEP_Y + 4, gh[1], gh[2], KEEP_Y + 8, gh[3], "minecraft:white_concrete")
    bb.fill(gh[0] + 1, KEEP_Y + 5, gh[1] + 1, gh[2] - 1, KEEP_Y + 7, gh[3] - 1, AIR)
    for x in range(gh[0] + 2, gh[2] - 1, 3):
        bb.set(x, KEEP_Y + 6, gh[3], "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]") if False else bb.set(x, KEEP_Y + 6, gh[3], "minecraft:glass_pane")
    castle_eave(bb, gh[0], gh[1], gh[2], gh[3], KEEP_Y + 8, TILE, TILEF, depth=2)
    P.gable_roof(bb, gh[0] - 1, gh[1] - 1, gh[2] + 1, gh[3] + 1, KEEP_Y + 10, TILE, ridge_axis="x", gable_fill="minecraft:white_concrete",
                 overhang=0, ends_overhang=0)
    for (a, b) in ((bx - 2, z2), (bx + 2, z2)):
        bb.fill(a, KEEP_Y + 1, b, a, KEEP_Y + 3, b, "minecraft:dark_oak_log[axis=y]")
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        t = (tx - 3, tz - 3, tx + 3, tz + 3)
        bb.fill(t[0], KEEP_Y + 1, t[1], t[2], KEEP_Y + 9, t[3], "minecraft:white_concrete")
        bb.fill(t[0] + 1, KEEP_Y + 1, t[1] + 1, t[2] - 1, KEEP_Y + 8, t[3] - 1, AIR)
        bb.fill(t[0] + 1, KEEP_Y + 5, t[1] + 1, t[2] - 1, KEEP_Y + 5, t[3] - 1, "minecraft:spruce_planks")
        for dy in (3, 7):
            bb.set(tx, KEEP_Y + dy, t[1], "minecraft:glass_pane"); bb.set(tx, KEEP_Y + dy, t[3], "minecraft:glass_pane")
            bb.set(t[0], KEEP_Y + dy, tz, "minecraft:glass_pane"); bb.set(t[2], KEEP_Y + dy, tz, "minecraft:glass_pane")
        castle_eave(bb, *t, KEEP_Y + 9, TILE, TILEF, depth=2)
        P.gable_roof(bb, t[0] - 1, t[1] - 1, t[2] + 1, t[3] + 1, KEEP_Y + 11, TILE, ridge_axis="x",
                     gable_fill="minecraft:white_concrete", overhang=0, ends_overhang=0)
        bb.fill(tx - 1, KEEP_Y + 1, tz - 1 if tz == z1 else tz + 1, tx - 1, KEEP_Y + 4, tz - 1 if tz == z1 else tz + 1, AIR)
        bb.fill(t[0] + 1, KEEP_Y + 1, t[1] + 1, t[0] + 1, KEEP_Y + 5, t[1] + 1, "minecraft:ladder[facing=east]")
    # the keep: five storeys, each smaller, white plaster with dark posts, eaves between, the top roof with shachihoko
    kx1, kz1, kx2, kz2 = 70, 20, 106, 44
    y = KEEP_Y
    FH = 7
    tiers = []
    for k in range(5):
        a1, c1, a2, c2 = kx1 + 3 * k, kz1 + 2 * k, kx2 - 3 * k, kz2 - 2 * k
        top = y + FH
        bb.fill(a1, y, c1, a2, y, c2, "minecraft:dark_oak_planks" if k else "minecraft:polished_andesite")
        bb.fill(a1, y + 1, c1, a2, top - 1, c2, "minecraft:white_concrete")
        bb.fill(a1 + 1, y + 1, c1 + 1, a2 - 1, top - 1, c2 - 1, AIR)
        for x in range(a1, a2 + 1, 4):
            for z in (c1, c2):
                bb.fill(x, y + 1, z, x, top - 1, z, "minecraft:dark_oak_log[axis=y]")
        for z in range(c1, c2 + 1, 4):
            for x in (a1, a2):
                bb.fill(x, y + 1, z, x, top - 1, z, "minecraft:dark_oak_log[axis=y]")
        for x in range(a1 + 2, a2 - 1, 4):
            for z in (c1, c2):
                bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:spruce_trapdoor[facing=" + ("north" if z == c1 else "south") + ",half=bottom,open=true]") if False else \
                    bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:glass_pane")
        for z in range(c1 + 2, c2 - 1, 4):
            for x in (a1, a2):
                bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:glass_pane")
        bb.fill(a1, top - 1, c1, a2, top - 1, c1, "minecraft:dark_oak_planks"); bb.fill(a1, top - 1, c2, a2, top - 1, c2, "minecraft:dark_oak_planks")
        bb.fill(a1, top - 1, c1, a1, top - 1, c2, "minecraft:dark_oak_planks"); bb.fill(a2, top - 1, c1, a2, top - 1, c2, "minecraft:dark_oak_planks")
        castle_eave(bb, a1, c1, a2, c2, top - 1, TILE, TILEF, depth=2, bracket="minecraft:dark_oak_stairs")
        # a triangular gable (chidori-hafu) over the eave on the south front of tiers 1 and 3
        if k in (1, 3):
            gx = (a1 + a2) // 2
            for i in range(5):
                bb.fill(gx - 4 + i, top + i, c2 + 1, gx + 4 - i, top + i, c2 + 1, "minecraft:white_concrete")
                bb.set(gx - 5 + i, top + i, c2 + 1, st(TILE, "east")); bb.set(gx + 5 - i, top + i, c2 + 1, st(TILE, "west"))
                bb.set(gx - 5 + i, top + i, c2 + 2, st(TILE, "east")); bb.set(gx + 5 - i, top + i, c2 + 2, st(TILE, "west"))
            bb.set(gx, top + 5, c2 + 1, "minecraft:gold_block")
        tiers.append((a1, c1, a2, c2, y, top))
        y = top
    a1, c1, a2, c2, _, top = tiers[-1]
    P.gable_roof(bb, a1 - 2, c1 - 2, a2 + 2, c2 + 2, top + 1, TILE, ridge_axis="x", gable_fill="minecraft:white_concrete",
                 overhang=0, ends_overhang=1)
    ridge = top + 1 + (c2 - c1 + 4) // 2
    for x in (a1 - 2, a2 + 2):                                               # the golden shachihoko on the ridge ends
        bb.set(x, ridge, (c1 + c2) // 2, "minecraft:gold_block")
        bb.set(x, ridge + 1, (c1 + c2) // 2, "minecraft:gold_block")
        bb.set(x + (1 if x < a2 else -1), ridge + 1, (c1 + c2) // 2, "minecraft:gold_block")
        bb.set(x, ridge + 2, (c1 + c2) // 2, "minecraft:lightning_rod")
    # inside: floors furnished, a ladder up the west side through every floor
    kinds = [("storage", "kitchen", "living"), ("bedroom", "living", "library"), ("library", "living", "bedroom"),
             ("bedroom", "living"), ("living",)]
    for k, (b1, d1, b2, d2, fy, ftop) in enumerate(tiers):
        if k < 3:
            wing_floor(bb, b1 + 1, d1 + 1, b2 - 1, d2 - 1, fy + 1, FH - 2, "minecraft:white_concrete", seed_of("fc", k), tracker, kinds[k],
                       corridor="x", cw=3, carpet=(None, "minecraft:green_carpet"), keep=[(kx1 + 13, kz1 + 9, kx1 + 15, kz1 + 12)],
                       wood="dark_oak", audit=audit, lamp="minecraft:lantern[hanging=true]")
        else:
            furnish(bb, [(b1 + 1, d1 + 1, b2 - 1, d2 - 1)], fy + 1, FH - 2, list(kinds[k]), seed_of("fcf", k), tracker,
                    doors=[(kx1 + 14, kz1 + 10)], wood="dark_oak", audit=audit)
    lx, lz = kx1 + 14, kz1 + 10
    bb.fill(lx, KEEP_Y + 1, lz, lx, tiers[-1][5] - 1, lz, AIR)
    bb.fill(lx, KEEP_Y + 1, lz + 1, lx, tiers[-1][5] - 1, lz + 1, "minecraft:white_concrete") if False else None
    bb.fill(lx, KEEP_Y + 1, lz, lx, tiers[-1][5] - 1, lz, "minecraft:ladder[facing=south]")
    bb.fill(lx, KEEP_Y + 1, lz - 1, lx, tiers[-1][5] - 1, lz - 1, "minecraft:dark_oak_planks")
    bb.fill((kx1 + kx2) // 2 - 1, KEEP_Y + 1, kz2, (kx1 + kx2) // 2 + 1, KEEP_Y + 3, kz2, AIR)
    # the garden in front of the keep: raked gravel, a pine, stone lanterns
    for (x, z) in ((bx - 8, z2 - 5), (bx + 8, z2 - 5)):
        bb.set(x, KEEP_Y + 1, z, "minecraft:stone_brick_wall"); bb.set(x, KEEP_Y + 2, z, "minecraft:lantern[hanging=false]")
        bb.set(x, KEEP_Y + 3, z, "minecraft:stone_brick_slab[type=bottom]")
    rng = np.random.default_rng(1943)
    for (x, z) in ((x1 + 6, z2 - 6), (x2 - 6, z2 - 6), (x1 + 6, z1 + 6), (x2 - 6, z1 + 6)):
        P.tree(bb, x, KEEP_Y + 1, z, 8, "spruce", rng)
    return (x1 - 10, z1 - 10, x2 + 10, mz + MOAT + 1)


# ------------------------------------------------------------------ machiya
WALLS = ["minecraft:white_concrete", "minecraft:white_terracotta", "minecraft:calcite"]


def machiya(seed, w, d, floors, tracker, kinds, red=False, roof=TILE):
    """A Wano town house, door on the south (+z) face: stone plinth, dark posts every 3, lattice and noren below, white
    plaster (or red lacquer) upstairs with a little balcony rail, a tiled pent roof over the ground floor and a gable
    roof on top, every floor furnished."""
    rng = np.random.default_rng(seed)
    FH = 5
    m = BigBuild(seed=seed, y_min=-6, y_max=40)
    m.fill(-1, -6, -1, w, 0, d, "minecraft:cobblestone")
    m.fill(0, 0, 0, w - 1, 0, d - 1, "minecraft:spruce_planks")
    top = FH * floors
    wall = "minecraft:red_terracotta" if red else None
    for f in range(floors):
        y0 = f * FH
        if f:
            m.fill(0, y0, 0, w - 1, y0, d - 1, "minecraft:spruce_planks")
        if f == 0 and not red:
            m.fill(0, y0 + 1, 0, w - 1, y0 + FH - 1, d - 1, "minecraft:stripped_spruce_wood")
        else:
            if red:
                m.fill(0, y0 + 1, 0, w - 1, y0 + FH - 1, d - 1, wall)
            else:
                m.mix(0, y0 + 1, 0, w - 1, y0 + FH - 1, d - 1, WALLS, [0.7, 0.2, 0.1])
        m.fill(1, y0 + 1, 1, w - 2, y0 + FH - 1, d - 2, AIR)
        for x in range(0, w, 3):
            for z in (0, d - 1):
                m.fill(x, y0 + 1, z, x, y0 + FH - 1, z, "minecraft:dark_oak_log[axis=y]")
        for x in (0, w - 1):
            for z in range(0, d, 3):
                m.fill(x, y0 + 1, z, x, y0 + FH - 1, z, "minecraft:dark_oak_log[axis=y]")
        m.fill(0, y0 + FH - 1, 0, w - 1, y0 + FH - 1, 0, "minecraft:dark_oak_planks")
        m.fill(0, y0 + FH - 1, d - 1, w - 1, y0 + FH - 1, d - 1, "minecraft:dark_oak_planks")
        # windows: lattice (trapdoors) on the ground floor front, paper screens (white panes) upstairs
        for x in range(1, w - 1):
            if x % 3 == 0:
                continue
            if f == 0:
                m.fill(x, y0 + 2, d - 1, x, y0 + 3, d - 1, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]")
            else:
                m.set(x, y0 + 2, d - 1, "minecraft:white_stained_glass_pane"); m.set(x, y0 + 3, d - 1, "minecraft:white_stained_glass_pane")
                m.set(x, y0 + 2, 0, "minecraft:white_stained_glass_pane")
        for z in range(2, d - 2, 3):
            m.set(0, y0 + 2, z, "minecraft:white_stained_glass_pane"); m.set(w - 1, y0 + 2, z, "minecraft:white_stained_glass_pane")
        if f > 0:
            m.fill(0, y0 + 1, d, w - 1, y0 + 1, d, "minecraft:dark_oak_fence")
            m.fill(0, y0, d, w - 1, y0, d, "minecraft:dark_oak_slab[type=top]")
    # door and noren curtain
    dx = w // 2
    m.fill(dx, 1, d - 1, dx, 2, d - 1, AIR)
    m.set(dx, 1, d - 1, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    m.set(dx, 2, d - 1, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    nc = ["blue", "red", "purple", "white", "cyan"][int(rng.integers(0, 5))]
    m.set(dx, 3, d, f"minecraft:{nc}_wall_banner[facing=south]") if False else None
    m.fill(dx - 1, 4, d, dx + 1, 4, d, f"minecraft:{nc}_wool")
    # the pent roof over the ground floor front and back
    for z, f in ((d, "north"), (-1, "south")):
        m.fill(-1, FH, z, w, FH, z, st(roof, f))
    m.fill(-1, FH - 1, d + 1, w, FH - 1, d + 1, st(roof, "north")) if False else None
    P.gable_roof(m, -1, -1, w, d, top + 1, roof, gable_fill="minecraft:white_concrete" if not red else wall, overhang=1, ends_overhang=0)
    m.set(dx + 1 if dx + 1 < w - 1 else dx - 1, 3, d, "minecraft:lantern[hanging=false]") if False else None
    m.set(1, 3, d, "minecraft:lantern[hanging=true]") if False else None
    # inside: ladder in the back corner, one furnished room per floor
    if floors > 1:
        m.fill(1, 1, 1, 1, top - FH + 1, 1, "minecraft:ladder[facing=south]")
    audit = []
    for f in range(floors):
        fy = f * FH + 1
        r = (2, 1, w - 2, d - 2)
        doors = [(dx, d - 1)] if f == 0 else []
        doors += [(1, 1)]
        P.furnish_room(m, r, fy, kind=kinds[min(f, len(kinds) - 1)], height=FH - 1, seed=seed + f, wood="dark_oak", tracker=tracker,
                       doors=doors)
        txt, ok = P.audit_props(m, [r], fy, FH - 1)
        if not ok:
            audit.append(txt)
    if floors > 1:
        for f in range(1, floors):
            m.set(1, f * FH, 1, "minecraft:ladder[facing=south]")
    return m, top, audit


KINDS = [["workshop", "bedroom"], ["kitchen", "bedroom"], ["storage", "living"], ["living", "bedroom"], ["kitchen", "library"]]


def city(bb, tracker, audit, rng, avoid):
    taken = []
    k = 0
    # blocks of houses on both sides of every street; (x1, x2, z, rot) rows, doors facing the street
    rows = []
    d = 9
    for z_street, north in ((GROUNDS[3] + MOAT + 4, False), (78, False), (112, True), (134, False)):
        if north:
            rows.append((CITY[0] + 6, AVE[0] - 2, z_street - 2 - d, 0)); rows.append((AVE[1] + 2, CITY[2] - 6, z_street - 2 - d, 0))
        rows.append((CITY[0] + 6, AVE[0] - 2, z_street + 7, 2)); rows.append((AVE[1] + 2, CITY[2] - 6, z_street + 7, 2))
    for (xa, xb, zz, rot) in rows:
        x = xa
        while x < xb - 6:
            w = int(rng.integers(7, 11))
            if x + w > xb:
                w = xb - x
            if w < 7:
                break
            if zz + d > CITY[3] + 4 or (zz + d - 1 >= CANAL[0] - 1 and zz <= CANAL[1] + 1) or any(x - 1 <= t[2] and t[0] <= x + w and zz - 1 <= t[3] and t[1] <= zz + d for t in avoid):
                x += w + 1
                continue
            X, Z = np.array([[x + w // 2]]), np.array([[zz + d // 2]])
            if SHORE(X, Z)[0, 0] < 6:
                x += w + 1
                continue
            mod, _, au = machiya(seed_of("fcm", k), w, d, 2 if rng.random() < 0.8 else 1, tracker, KINDS[k % len(KINDS)],
                                 red=(k % 9 == 4), roof=(TILE, TILE, "minecraft:dark_oak_stairs", TILE)[k % 4])
            audit += au
            place_house(bb, mod, w, d, x, CY, zz, rot)
            taken.append((x - 1, zz - 1, x + w, zz + d))
            x += w + (1 if rng.random() < 0.6 else 0)
            k += 1
    print("machiya:", k)
    return taken


def canal(bb, rng):
    z1, z2 = CANAL
    for x in range(CITY[0] - 6, CITY[2] + 7):
        X, Z = np.array([[x]]), np.array([[z1]])
        bb.fill(x, CY - 3, z1, x, CY - 1, z2, "minecraft:water")
        bb.fill(x, CY - 4, z1, x, CY - 4, z2, "minecraft:mud")
        bb.fill(x, CY, z1, x, CY + 3, z2, AIR)
        bb.set(x, CY, z1 - 1, "minecraft:stone_bricks"); bb.set(x, CY, z2 + 1, "minecraft:stone_bricks")
        bb.fill(x, CY - 3, z1 - 1, x, CY - 1, z1 - 1, "minecraft:stone_bricks"); bb.fill(x, CY - 3, z2 + 1, x, CY - 1, z2 + 1, "minecraft:stone_bricks")
    # sakura along both banks
    for x in range(CITY[0] + 2, CITY[2] - 2, 9):
        for z in (z1 - 4, z2 + 4):
            if abs(x - (AVE[0] + AVE[1]) // 2) < 7:
                continue
            P.tree(bb, x, CY + 1, z, int(rng.integers(5, 7)), "cherry", rng)
    # little arched red bridges: on the avenue and two more
    for bx, w in (((AVE[0] + AVE[1]) // 2, 3), (50, 1), (126, 1)):
        for z in range(z1 - 1, z2 + 2):
            arch = 1 if z1 <= z <= z2 else 0
            bb.fill(bx - w, CY + arch, z, bx + w, CY + arch, z, "minecraft:crimson_planks")
            bb.set(bx - w - 1, CY + arch + 1, z, "minecraft:crimson_fence"); bb.set(bx + w + 1, CY + arch + 1, z, "minecraft:crimson_fence")
        for z in (z1 - 1, z2 + 1):
            bb.set(bx - w - 1, CY + 2, z, "minecraft:lantern[hanging=false]") if False else None
    return (CITY[0] - 6, z1 - 6, CITY[2] + 6, z2 + 6)


def lanterns(bb):
    """Strings of paper lanterns across the main avenue between tall posts."""
    xa, xb = AVE[0] - 1, AVE[1] + 1
    for z in range(GROUNDS[3] + MOAT + 10, CITY[3], 8):
        if CANAL[0] - 2 <= z <= CANAL[1] + 2:
            continue
        for x in (xa, xb):
            bb.fill(x, CY + 1, z, x, CY + 6, z, "minecraft:dark_oak_fence")
        bb.fill(xa + 1, CY + 6, z, xb - 1, CY + 6, z, "minecraft:dark_oak_fence")
        for x in range(xa + 1, xb, 2):
            bb.set(x, CY + 5, z, "minecraft:lantern[hanging=true]")


def torii(bb, x, z, h=12, span=10):
    y = hy(x, z)
    for dx in (-span // 2, span // 2):
        bb.fill(x + dx, y - 2, z, x + dx, y + h, z, "minecraft:red_concrete")
        bb.set(x + dx, y + 1, z, "minecraft:black_concrete")
    bb.fill(x - span // 2 - 2, y + h + 1, z, x + span // 2 + 2, y + h + 1, z, "minecraft:red_concrete")
    bb.fill(x - span // 2 - 3, y + h + 2, z, x + span // 2 + 3, y + h + 2, z, "minecraft:black_concrete")
    bb.set(x - span // 2 - 4, y + h + 2, z, st("minecraft:blackstone_stairs", "east", "top"))
    bb.set(x + span // 2 + 4, y + h + 2, z, st("minecraft:blackstone_stairs", "west", "top"))
    bb.fill(x - span // 2, y + h - 2, z, x + span // 2, y + h - 2, z, "minecraft:red_concrete")
    bb.set(x, y + h - 1, z, "minecraft:red_concrete")


def pagoda(bb, x, z, tracker, audit):
    """A five-storey pagoda: square red-and-white storeys getting smaller, deep tiled eaves, a bronze spire."""
    y = hy(x, z)
    bb.fill(x - 7, y - 3, z - 7, x + 7, y, z + 7, "minecraft:stone_bricks")
    for k in range(5):
        r = 5 - (k + 1) // 2
        top = y + 5
        bb.fill(x - r, y + 1, z - r, x + r, top - 1, z + r, "minecraft:red_terracotta")
        bb.fill(x - r + 1, y + 1, z - r + 1, x + r - 1, top - 1, z + r - 1, AIR)
        for (a, b) in ((x - r, z - r), (x + r, z - r), (x - r, z + r), (x + r, z + r)):
            bb.fill(a, y + 1, b, a, top - 1, b, "minecraft:dark_oak_log[axis=y]")
        for (a, b) in ((x, z - r), (x, z + r), (x - r, z), (x + r, z)):
            bb.fill(a, y + 2, b, a, y + 3, b, "minecraft:white_stained_glass_pane")
        bb.fill(x - r + 1, top, z - r + 1, x + r - 1, top, z + r - 1, "minecraft:dark_oak_planks")
        castle_eave(bb, x - r, z - r, x + r, z + r, top - 1, TILE, TILEF, depth=2, bracket="minecraft:dark_oak_stairs")
        y = top
    bb.fill(x, y + 1, z, x, y + 6, z, "minecraft:lightning_rod")
    bb.set(x, y + 1, z, "minecraft:cut_copper")
    bb.fill(x - 4, hy(x, z) + 1, z + 5, x - 4, y, z + 5, AIR) if False else None
    bb.fill(x, hy(x, z) + 1, z + 5, x, hy(x, z) + 2, z + 5, AIR)
    return (x - 8, z - 8, x + 8, z + 8)


def specials(bb, tracker, audit, rng):
    taken = []
    # Komurasaki's teahouse: three storeys of red lacquer with balconies, on the avenue's west side by the canal
    mod, _, au = machiya(seed_of("fckomu"), 15, 12, 3, tracker, ["living", "kitchen", "bedroom"], red=True)
    audit += au
    place_house(bb, mod, 15, 12, AVE[0] - 18, CY, CANAL[1] + 4, 2)
    taken.append((AVE[0] - 19, CANAL[1] + 3, AVE[0] - 2, CANAL[1] + 17))
    # the bathhouse: a wide low hall with a steaming pool in the yard
    bxx, bzz = 118, 140
    mod, _, au = machiya(seed_of("fcbath"), 16, 10, 1, tracker, ["living"])
    audit += au
    place_house(bb, mod, 16, 10, bxx, CY, bzz, 2)
    bb.fill(bxx + 2, CY, bzz + 12, bxx + 13, CY, bzz + 17, "minecraft:stone_bricks")
    bb.fill(bxx + 3, CY - 1, bzz + 13, bxx + 12, CY, bzz + 16, "minecraft:water")
    for x in range(bxx + 1, bxx + 15):
        bb.set(x, CY + 1, bzz + 18, "minecraft:bamboo_fence")
    for z in range(bzz + 11, bzz + 19):
        bb.set(bxx + 1, CY + 1, z, "minecraft:bamboo_fence"); bb.set(bxx + 14, CY + 1, z, "minecraft:bamboo_fence")
    bb.set(bxx + 7, CY - 2, bzz + 14, "minecraft:magma_block")
    taken.append((bxx - 1, bzz - 1, bxx + 17, bzz + 19))
    # the sake brewery: barrels stacked in the yard
    for (x, z) in ((40, 142), (41, 142), (42, 142), (40, 143), (41, 143), (40, 144)):
        bb.set(x, CY + 1, z, "minecraft:barrel[facing=up,open=false]")
        if (x + z) % 2 == 0:
            bb.set(x, CY + 2, z, "minecraft:barrel[facing=up,open=false]")
    taken.append(pagoda(bb, 138, 88, tracker, audit))
    tz = CITY[3] + 6
    torii(bb, (AVE[0] + AVE[1]) // 2, tz, 12, 12)
    taken.append((AVE[0] - 10, tz - 2, AVE[1] + 10, tz + 2))
    return taken


def scenery(bb, rng, taken):
    k = 0
    for _ in range(6000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 3 or street_mask(X, Z)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if y < 1:
            continue
        inside = rect_d(X, Z, CITY)[0, 0] == 0
        if inside and rng.random() < 0.8:
            continue
        if NT.noise(X, Z, 1971, 16)[0, 0] > 0.7 and not inside:          # bamboo groves
            for _ in range(12):
                bx, bz = x + int(rng.integers(-3, 4)), z + int(rng.integers(-3, 4))
                by = hy(bx, bz)
                if GRAD[min(bx, N - 1), min(bz, N - 1)] < 2:
                    bb.fill(bx, by + 1, bz, bx, by + int(rng.integers(6, 12)), bz, "minecraft:bamboo[age=1,leaves=large,stage=0]")
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(6, 11)), ("spruce", "cherry", "spruce", "oak", "dark_oak")[k % 5], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 110:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=1920, y_min=-14, y_max=140)
    tracker = P.PropTracker(1920)
    audit = []
    rng = np.random.default_rng(1920)
    terrain(bb)
    taken = [castle(bb, tracker, audit)]
    taken.append(canal(bb, rng))
    sp = specials(bb, tracker, audit, rng)
    taken += city(bb, tracker, audit, rng, sp)
    taken += sp
    lanterns(bb)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1990, density=0.25, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~street_mask(X, Z) & (rect_d(X, Z, GROUNDS) > 0))
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
    b.npc((AVE[0] + AVE[1]) // 2 + 4, CY + 1, CITY[3] - 4, "kinemon", False)
    b.chest(72, KEEP_Y + 1, 23, "wano", "east")
    b.chest(84, KEEP_Y + 4 * 7 + 1, 30, "treasure", "south")
    return b, 0
