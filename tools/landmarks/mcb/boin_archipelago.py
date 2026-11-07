"""Boin Archipelago v2, redesigned with the Minecraft Builder skill: the Greenhouse Island where Usopp was sent for
the timeskip (manga ch 591/595, anime ep 513/517): plants many times the size of a man, everything alive and hungry.

Silhouette first: a skyline of GIANT plants, never ordinary trees: towering pitcher plants with red lips, giant
spotted mushrooms on twisted stalks, a sunflower taller than the treehouse, thick green vines arching between them
like bridges, a lagoon covered with lily pads big enough to stand on, and Heracles(un)'s treehouse lab on a huge
bulbous trunk with a leaf-thatched roof.

Ground level: the snapper plants (red jaws with teeth), puffball clusters, a giant fern belt, the glass greenhouse
with Pop Green seed beds, Heracles' specimen garden of jars and labelled pots, Usopp's lean-to with his slingshot
target, trails and stepping stones. 136 x 128, land site, ground y 0, the lagoon dips under it. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "boin_archipelago"
TITLE = "Boin Archipelago"
CUTS = [3, 14, 30]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 136, 128
LX, LZ = 70, 66                    # lagoon
TX, TZ = 34, 40                    # treehouse trunk
GX0, GZ0 = 92, 22                  # greenhouse corner
_LAND = NT.outline(68, 64, 62, 8401, wobble=0.14)
_LAG = NT.outline(LX, LZ, 20, 8402, wobble=0.2)
LEAF = "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]"


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    h = 1 + NT.fbm(X, Z, 8403, 18) * 5
    h = np.where(d < 12, h * np.clip(d / 12.0, 0, 1), h)
    lg = _LAG(X, Z)
    h = np.where(lg > 0, -1 - np.clip(lg / 3.0, 0, 4), h)
    h = np.where((lg <= 0) & (lg > -4), np.minimum(h, 1), h)
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def onland(X, Z):
    return _LAND(np.asarray(X, float), np.asarray(Z, float)) > 0


def terrain(bb):
    lag = lambda X, Z: _LAG(X, Z) > 0
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, NT.JUNGLE, 8404, mask=lambda X, Z: onland(X, Z) & ~lag(X, Z), core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:mud", 0.5), ("minecraft:clay", 0.2), ("minecraft:moss_block", 0.3)], 8405,
             mask=lag, under="minecraft:mud", core="minecraft:stone", base=-8)
    bb.fill_where(LX - 30, -5, LZ - 30, LX + 30, 0, LZ + 30, lambda X, y, Z: lag(X, Z) & (y > height(X, Z)), "minecraft:water")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 8406, density=0.5,
              kinds=["minecraft:fern", "minecraft:large_fern", "onepiece:giant_fern", "minecraft:short_grass", "minecraft:moss_carpet", "minecraft:bush"],
              flowers=["minecraft:allium", "minecraft:pink_tulip", "minecraft:blue_orchid", "minecraft:pitcher_plant" if False else "minecraft:poppy"],
              mask=lambda X, Z: onland(X, Z) & ~lag(X, Z))


def pitcher(bb, x, z, h, r):
    """A giant pitcher plant: a swelling green urn with darker veins, a red lip, a lid leaf, water inside."""
    y0 = hy(x, z)
    for k in range(h):
        y = y0 + 1 + k
        t = k / max(h - 1, 1)
        rr = r * (0.55 + 0.7 * math.sin(math.pi * min(t * 0.9 + 0.1, 1.0)) ** 0.8) if t < 0.85 else r * 0.75
        blk = "minecraft:green_concrete" if (k % 5 == 0) else "minecraft:lime_terracotta" if (k % 2) else "minecraft:lime_concrete"
        bb.fill_where(x - r - 2, y, z - r - 2, x + r + 2, y, z + r + 2,
                      lambda X, yy, Z, rr=rr: (np.hypot(X - x, Z - z) <= rr) & (np.hypot(X - x, Z - z) > rr - 1.4), blk)
        bb.fill_where(x - r - 2, y, z - r - 2, x + r + 2, y, z + r + 2,
                      lambda X, yy, Z, rr=rr: np.hypot(X - x, Z - z) <= rr - 1.4,
                      "minecraft:water" if k < h * 0.35 else AIR)
    lip = y0 + h
    bb.fill_where(x - r - 2, lip, z - r - 2, x + r + 2, lip, z + r + 2,
                  lambda X, yy, Z: (np.hypot(X - x, Z - z) <= r * 0.75 + 1) & (np.hypot(X - x, Z - z) > r * 0.75 - 0.6), "minecraft:red_concrete")
    for k in range(int(r * 1.5)):                                   # the lid leaf leaning back
        bb.fill(x - 2 + 0, lip + 1 + k, z - int(r * 0.75) - k // 2, x + 2, lip + 1 + k, z - int(r * 0.75) - k // 2,
                "minecraft:green_concrete" if k % 2 else "minecraft:red_terracotta")
    bb.fill(x, y0 + 1, z + int(r) + 1, x, y0 + 4, z + int(r) + 1, "minecraft:green_concrete")


def mushroom(bb, x, z, h, r, cap="minecraft:red_mushroom_block", lean=(0, 0)):
    """A giant mushroom on a slightly twisted stalk, a domed cap with white spots and gills underneath."""
    y0 = hy(x, z)
    for k in range(h):
        t = k / max(h - 1, 1)
        cx, cz = x + int(round(lean[0] * t * t)), z + int(round(lean[1] * t * t))
        s = 1 if k < h - 3 else 2
        bb.fill_where(cx - 2, y0 + 1 + k, cz - 2, cx + 2, y0 + 1 + k, cz + 2,
                      lambda X, yy, Z, cx=cx, cz=cz, s=s: np.hypot(X - cx, Z - cz) <= s + 0.5, "minecraft:mushroom_stem")
    cx, cz, top = x + lean[0], z + lean[1], y0 + h + 1
    R = int(r) + 1
    bb.fill_where(cx - R, top - 1, cz - R, cx + R, top + int(r * 0.6) + 1, cz + R,
                  lambda X, y, Z: (((X - cx) ** 2 + (Z - cz) ** 2) / r ** 2 + ((y - top + 1) / (r * 0.6)) ** 2 <= 1) & (y >= top), cap)
    bb.fill_where(cx - R, top, cz - R, cx + R, top + int(r * 0.6) + 1, cz + R,
                  lambda X, y, Z: (((X - cx) ** 2 + (Z - cz) ** 2) / r ** 2 + ((y - top + 1) / (r * 0.6)) ** 2 <= 1)
                  & (NT.noise(X * 3 + y, Z * 3, x * 7 + z, 2) > 0.82), "minecraft:white_concrete")
    bb.fill_where(cx - R, top - 1, cz - R, cx + R, top - 1, cz + R,
                  lambda X, y, Z: ((X - cx) ** 2 + (Z - cz) ** 2 <= (r - 0.5) ** 2) & ((X - cx) ** 2 + (Z - cz) ** 2 > 4), "minecraft:brown_mushroom_block[up=false,down=true]" if False else "minecraft:mushroom_stem")
    bb.set(cx, top - 2, cz, "minecraft:shroomlight")


def sunflower(bb, x, z, h):
    """A sunflower taller than a house: thick stalk with paired leaves, a brown seed disc ringed with yellow petals."""
    y0 = hy(x, z)
    bb.fill(x, y0 + 1, z, x + 1, y0 + h, z + 1, "minecraft:green_concrete")
    for k in range(6, h - 4, 7):
        s = 1 if (k // 7) % 2 else -1
        for i in range(1, 6):
            bb.fill(x + (i if s > 0 else -i + 1), y0 + k + i // 3, z, x + (i if s > 0 else -i + 1), y0 + k + i // 3, z + 1, "minecraft:lime_concrete")
    cy, cz = y0 + h + 6, z - 1
    for u in range(-9, 11):
        for v in range(-9, 10):
            d = math.hypot(u - 0.5, v)
            if d <= 4.5:
                bb.set(x + u, cy + v, cz, "minecraft:brown_terracotta" if (u + v) % 2 else "minecraft:brown_concrete")
            elif d <= 9.5 and (math.atan2(v, u - 0.5) * 16 / math.pi) % 2 < 1.4:
                bb.set(x + u, cy + v, cz, "minecraft:yellow_concrete" if d < 8 else "minecraft:yellow_terracotta")
    bb.fill(x, y0 + h, z, x + 1, cy - 4, z + 1, "minecraft:green_concrete")
    bb.fill(x, cy - 4, z - 1, x + 1, cy - 4, z, "minecraft:green_concrete")


def vine_arch(bb, a, b, ya, yb, sag, w=1):
    """A vine thick as a trunk hanging between two points (a catenary-ish curve), with leaf tufts and a few hanging
    tendrils."""
    n = int(math.hypot(b[0] - a[0], b[1] - a[1])) * 2
    for k in range(n + 1):
        t = k / n
        x = a[0] + (b[0] - a[0]) * t
        z = a[1] + (b[1] - a[1]) * t
        y = ya + (yb - ya) * t - sag * 4 * t * (1 - t)
        xi, yi, zi = int(round(x)), int(round(y)), int(round(z))
        bb.fill(xi - w + 1, yi - w + 1, zi - w + 1, xi, yi, zi, "minecraft:green_concrete" if k % 7 else "minecraft:moss_block")
        if k % 11 == 5:
            bb.fill(xi, yi + 1, zi, xi, yi + 2, zi, LEAF)
        if k % 17 == 8:
            for d in range(1, 6):
                bb.set(xi, yi - w - d + 1, zi, "minecraft:cave_vines[berries=" + ("true" if d == 5 else "false") + "]" if d < 5 else "minecraft:cave_vines_plant[berries=true]")


def snapper(bb, x, z, facing=1):
    """A carnivorous snapper plant: a stalk with an open red jaw lined with white teeth."""
    y0 = hy(x, z)
    bb.fill(x, y0 + 1, z, x, y0 + 4, z, "minecraft:green_concrete")
    for s in (-1, 1):
        for k in range(4):
            yy = y0 + 5 + (s * (1 + k // 2) if True else 0)
            bb.fill(x - 2 + k, y0 + 5 + s * (1 + (3 - k) // 2), z - 1, x - 2 + k, y0 + 5 + s * (1 + (3 - k) // 2), z + 1, "minecraft:red_concrete")
        bb.fill(x - 2, y0 + 5 + s, z - 1, x + 1, y0 + 5 + s, z + 1, "minecraft:red_concrete")
    for k in (-2, 0, 1):
        bb.set(x + k, y0 + 5, z - 1, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up]" if k % 2 else "minecraft:white_concrete")
    bb.set(x - 1, y0 + 5, z, "minecraft:red_terracotta")
    for d in (-1, 1):
        bb.set(x + d, y0 + 1, z, "minecraft:lime_concrete"); bb.set(x, y0 + 1, z + d, "minecraft:lime_concrete")


def puffballs(bb, x, z, rng):
    for _ in range(int(rng.integers(3, 6))):
        px, pz = x + int(rng.integers(-4, 5)), z + int(rng.integers(-4, 5))
        r = rng.uniform(1.2, 2.6)
        py = hy(px, pz)
        R = int(r) + 1
        bb.fill_where(px - R, py, pz - R, px + R, py + 2 * R, pz + R,
                      lambda X, y, Z: (X - px) ** 2 + (Z - pz) ** 2 + ((y - py - r) * 1.1) ** 2 <= r * r,
                      "minecraft:white_terracotta" if rng.random() < 0.5 else "minecraft:white_concrete_powder", only_empty=True)


def lily_pads(bb, rng):
    """Giant lily pads on the lagoon (lime discs with a notch), a few small real lily pads, a pink lotus."""
    pads = []
    for _ in range(300):
        if len(pads) >= 9:
            break
        x, z = LX + int(rng.integers(-16, 17)), LZ + int(rng.integers(-14, 15))
        r = rng.uniform(2.5, 4.5)
        if _LAG(np.array(float(x)), np.array(float(z))) < r + 1 or any(math.hypot(x - a, z - b) < r + c + 1 for (a, b, c) in pads):
            continue
        pads.append((x, z, r))
        R = int(r) + 1
        a0 = rng.uniform(0, 6.28)
        bb.fill_where(x - R, 0, z - R, x + R, 0, z + R,
                      lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) & (np.abs(((np.arctan2(Z - z, X - x) - a0 + 3.14) % 6.28) - 3.14) > 0.3),
                      "minecraft:lime_concrete")
        bb.fill_where(x - R, 0, z - R, x + R, 0, z + R,
                      lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) & ((X - x) ** 2 + (Z - z) ** 2 > (r - 1) ** 2)
                      & (np.abs(((np.arctan2(Z - z, X - x) - a0 + 3.14) % 6.28) - 3.14) > 0.3), "minecraft:green_concrete")
        if rng.random() < 0.4:
            bb.set(x, 1, z, "minecraft:pink_petals[flower_amount=4,facing=north]" if False else "minecraft:pink_tulip")
    for _ in range(40):
        x, z = LX + int(rng.integers(-18, 19)), LZ + int(rng.integers(-16, 17))
        if _LAG(np.array(float(x)), np.array(float(z))) > 1 and bb.get_region(x, 0, z, x, 1, z)[0, 1, 0] in (0, 1):
            if "water" in bb.names[bb.get_region(x, 0, z, x, 0, z)[0, 0, 0]]:
                bb.set(x, 1, z, "minecraft:lily_pad")
    return pads


def treehouse(bb):
    """Heracles(un)'s lab: a bulbous giant trunk, a round deck with a leaf-thatched house on it, specimen jars,
    a rope ladder and a vine bridge."""
    y0 = hy(TX, TZ)
    log = "minecraft:jungle_wood"
    for k in range(0, 34):
        r = 3.2 + 1.6 * math.sin(math.pi * min(k / 18.0, 1.0)) if k < 18 else 2.4
        bb.fill_where(TX - 6, y0 - 2 + k, TZ - 6, TX + 6, y0 - 2 + k, TZ + 6,
                      lambda X, y, Z, r=r: np.hypot(X - TX, Z - TZ) <= r + 0.4 * NT.noise(X * 3, Z * 3 + y, 8407, 2), log)
    rng = np.random.default_rng(8408)
    for a in range(0, 360, 60):                                    # buttress roots
        t = math.radians(a + 15)
        for s in range(4, 9):
            x, z = TX + int(round(s * math.cos(t))), TZ + int(round(s * math.sin(t)))
            bb.fill(x, hy(x, z) - 1, z, x, hy(x, z) + max(0, 5 - s // 2), z, log)
    DY = y0 + 18
    bb.fill_where(TX - 11, DY, TZ - 11, TX + 11, DY, TZ + 11, lambda X, y, Z: np.hypot(X - TX, Z - TZ) <= 10.5, "minecraft:jungle_planks")
    bb.fill_where(TX - 11, DY + 1, TZ - 11, TX + 11, DY + 1, TZ + 11,
                  lambda X, y, Z: (np.hypot(X - TX, Z - TZ) <= 10.5) & (np.hypot(X - TX, Z - TZ) > 9.6), "minecraft:jungle_fence")
    for a in range(0, 360, 45):
        t = math.radians(a)
        x, z = TX + int(round(8 * math.cos(t))), TZ + int(round(8 * math.sin(t)))
        for k in range(1, 7):
            bb.set(int(round(TX + (8 - k) * math.cos(t))), DY - k, int(round(TZ + (8 - k) * math.sin(t))), "minecraft:jungle_log[axis=y]")
    # the hut: round-ish timber walls with windows, conical thatch of leaves and moss
    hx1, hz1, hx2, hz2 = TX - 5, TZ - 5, TX + 5, TZ + 5
    bb.fill(hx1, DY + 1, hz1, hx2, DY + 5, hz2, "minecraft:jungle_planks")
    bb.fill(hx1 + 1, DY + 1, hz1 + 1, hx2 - 1, DY + 5, hz2 - 1, AIR)
    for (x, z) in ((hx1, hz1), (hx2, hz1), (hx1, hz2), (hx2, hz2)):
        bb.fill(x, DY + 1, z, x, DY + 5, z, "minecraft:stripped_jungle_log[axis=y]")
    for x in (TX - 3, TX + 3):
        bb.fill(x, DY + 2, hz1, x, DY + 3, hz1, "minecraft:glass_pane"); bb.fill(x, DY + 2, hz2, x, DY + 3, hz2, "minecraft:glass_pane")
    bb.fill(hx2, DY + 2, TZ - 2, hx2, DY + 3, TZ + 2, "minecraft:glass_pane")
    bb.fill(TX, DY + 1, hz2, TX, DY + 2, hz2, AIR)
    furnish_kit(bb, (hx1 + 1, hz1 + 1, hx2 - 1, hz2 - 1), DY + 1, 4, "study", wood="jungle", seed=8409, doors=[(TX, hz2)], accent="green")
    P.cone_roof(bb, TX, DY + 6, TZ, 8, 8, "minecraft:moss_block")
    bb.fill_where(TX - 9, DY + 6, TZ - 9, TX + 9, DY + 14, TZ + 9,
                  lambda X, y, Z: (np.hypot(X - TX, Z - TZ) <= 8 - (y - DY - 6)) & (np.hypot(X - TX, Z - TZ) > 7 - (y - DY - 6))
                  & (NT.noise(X * 2, Z * 2 + y, 8410, 2) > 0.4), LEAF)
    # specimen jars on the deck: glass with coloured "specimens"
    for k, (dx, dz) in enumerate(((-8, -2), (-8, 2), (-7, 5), (7, -5), (8, 2))):
        bb.set(TX + dx, DY + 1, TZ + dz, "minecraft:glass")
        bb.set(TX + dx, DY + 2, TZ + dz, ["minecraft:slime_block", "minecraft:honey_block", "minecraft:sea_lantern", "minecraft:moss_block", "minecraft:amethyst_block"][k])
        bb.set(TX + dx, DY + 3, TZ + dz, "minecraft:glass")
    # ladder down the trunk's south side
    lz = TZ + 5
    while bb.get_region(TX, DY - 3, lz, TX, DY - 3, lz)[0, 0, 0] not in (0, 1) and lz < TZ + 12:
        lz += 1
    bb.fill(TX, hy(TX, lz) + 1, lz, TX, DY - 1, lz, "minecraft:ladder[facing=south]")
    bb.fill(TX, DY, lz, TX, DY, lz, AIR)
    for y in range(hy(TX, lz) + 1, DY):
        bb.set(TX, y, lz - 1, log)
    return DY


def greenhouse(bb):
    """Glass greenhouse with Pop Green seed beds, potting bench, a bubbling cauldron, labelled pots outside."""
    x1, z1, x2, z2 = GX0, GZ0, GX0 + 20, GZ0 + 12
    y = max(hy(x, z) for x in range(x1, x2 + 1, 2) for z in range(z1, z2 + 1, 2))
    bb.fill(x1 - 1, y - 4, z1 - 1, x2 + 1, y, z2 + 1, "minecraft:mossy_stone_bricks")
    bb.fill(x1, y + 1, z1, x2, y + 6, z2, "minecraft:glass")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 7, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, y + 1, z1, x, y + 6, z1, "minecraft:dark_oak_log[axis=y]"); bb.fill(x, y + 1, z2, x, y + 6, z2, "minecraft:dark_oak_log[axis=y]")
    for k in range(4):
        bb.fill(x1, y + 7 + k, z1 + k, x2, y + 7 + k, z1 + k, "minecraft:glass")
        bb.fill(x1, y + 7 + k, z2 - k, x2, y + 7 + k, z2 - k, "minecraft:glass")
        bb.fill(x1, y + 7 + k, z1 + k, x1, y + 7 + k, z2 - k, "minecraft:glass")
        bb.fill(x2, y + 7 + k, z1 + k, x2, y + 7 + k, z2 - k, "minecraft:glass")
    bb.fill(x1, y + 11, z1 + 4, x2, y + 11, z2 - 4, "minecraft:dark_oak_slab[type=bottom]")
    plants = ["minecraft:sweet_berry_bush[age=3]", "minecraft:carrots[age=7]", "minecraft:beetroots[age=3]", "minecraft:wheat[age=7]",
              "minecraft:pitcher_crop[age=4,half=lower]" if False else "minecraft:torchflower_crop[age=1]"]
    for r, z in enumerate((z1 + 2, z1 + 5, z1 + 8)):
        bb.fill(x1 + 2, y, z, x2 - 6, y, z + 1, "minecraft:farmland[moisture=7]")
        for x in range(x1 + 2, x2 - 5):
            for dz in (0, 1):
                bb.set(x, y + 1, z + dz, plants[(x + r) % len(plants)])
    bb.fill(x2 - 4, y + 1, z1 + 2, x2 - 1, y + 1, z1 + 2, "minecraft:spruce_slab[type=top]")
    for (x, p) in ((x2 - 4, "minecraft:potted_fern"), (x2 - 3, "minecraft:potted_red_mushroom"), (x2 - 2, "minecraft:potted_cactus")):
        bb.set(x, y + 2, z1 + 2, p)
    bb.set(x2 - 2, y + 1, z2 - 2, "minecraft:water_cauldron[level=3]"); bb.set(x2 - 3, y + 1, z2 - 2, "minecraft:composter[level=5]")
    bb.set(x2 - 1, y + 1, z2 - 4, "minecraft:brewing_stand")
    for x in range(x1 + 3, x2 - 2, 5):
        bb.set(x, y + 6, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    bb.fill(x1, y + 1, (z1 + z2) // 2, x1, y + 2, (z1 + z2) // 2, AIR)
    return (x1, z1, y)


def usopp_camp(bb):
    """Usopp's lean-to with his slingshot target on a tree and a pile of Pop Green seed sacks."""
    x, z = 44, 98
    y = hy(x, z)
    bb.fill(x - 3, y, z - 2, x + 3, y, z + 3, "minecraft:coarse_dirt")
    bb.fill(x - 3, y + 1, z - 2, x + 3, y + 5, z + 3, AIR)
    for k in range(5):
        bb.fill(x - 3, y + 4 - k // 2, z - 2 + k, x + 3, y + 4 - k // 2, z - 2 + k, LEAF if k % 2 else "minecraft:moss_block")
    bb.fill(x - 3, y + 1, z - 2, x - 3, y + 4, z - 2, "minecraft:bamboo_block[axis=y]"); bb.fill(x + 3, y + 1, z - 2, x + 3, y + 4, z - 2, "minecraft:bamboo_block[axis=y]")
    bb.set(x - 1, y + 1, z, "minecraft:green_bed[facing=east,part=head]"); bb.set(x - 2, y + 1, z, "minecraft:green_bed[facing=east,part=foot]")
    bb.set(x + 2, y + 1, z - 1, "minecraft:barrel[facing=up]")
    bb.set(x + 2, y + 1, z + 1, "minecraft:fletching_table")
    bb.set(x + 1, y + 1, z + 3, "minecraft:campfire[lit=false]")
    # target on a stump
    tx, tz = x + 12, z - 2
    ty = hy(tx, tz)
    bb.fill(tx, ty + 1, tz, tx, ty + 2, tz, "minecraft:jungle_log[axis=y]")
    bb.set(tx, ty + 3, tz, "minecraft:target")
    for (dx, dz) in ((-1, 2), (0, 3), (1, 2)):
        bb.set(x + 5 + dx, hy(x + 5 + dx, z + dz) + 1, z + dz, "minecraft:hay_block")


def design():
    bb = BigBuild(seed=8400, y_min=-12, y_max=100)
    rng = np.random.default_rng(8411)
    terrain(bb)
    lily_pads(bb, rng)
    DY = treehouse(bb)
    gh = greenhouse(bb)
    usopp_camp(bb)
    # the giant plants: placed around the lagoon and island, never on the treehouse/greenhouse/camp
    keep = [(TX - 14, TZ - 14, TX + 14, TZ + 14), (GX0 - 4, GZ0 - 4, GX0 + 24, GZ0 + 16), (36, 90, 60, 106)]
    free = lambda x, z, m=4: onland(np.array(float(x)), np.array(float(z))) and _LAND(np.array(float(x)), np.array(float(z))) > 8 \
        and _LAG(np.array(float(x)), np.array(float(z))) < -m and not any(a - m <= x <= c + m and b - m <= z <= e + m for (a, b, c, e) in keep)
    spots = []

    def pick(r, tries=400):
        for _ in range(tries):
            x, z = int(rng.integers(10, NX - 10)), int(rng.integers(10, NZ - 10))
            if free(x, z, int(r) + 2) and all(math.hypot(x - a, z - b) > r + c + 3 for (a, b, c) in spots):
                spots.append((x, z, r))
                return x, z
        return None
    s = pick(10)
    if s:
        sunflower(bb, s[0], s[1], 40)
    for (h, r) in ((30, 5), (24, 4), (20, 4), (16, 3), (14, 3)):
        s = pick(r)
        if s:
            pitcher(bb, s[0], s[1], h, r)
    caps = ["minecraft:red_mushroom_block", "minecraft:brown_mushroom_block", "minecraft:red_mushroom_block", "minecraft:purple_concrete",
            "minecraft:orange_concrete", "minecraft:red_mushroom_block"]
    for k, (h, r) in enumerate(((26, 11), (20, 9), (16, 7), (12, 6), (9, 5), (22, 8))):
        s = pick(r)
        if s:
            mushroom(bb, s[0], s[1], h, r, caps[k], lean=(int(rng.integers(-3, 4)), int(rng.integers(-3, 4))))
    for _ in range(7):
        s = pick(2)
        if s:
            snapper(bb, s[0], s[1])
    for _ in range(5):
        s = pick(4)
        if s:
            puffballs(bb, s[0], s[1], rng)
    # vine arches between the tallest plants and the treehouse deck
    tall = sorted(spots, key=lambda p: -p[2])[:4]
    prev = (TX, TZ, DY + 2)
    for (x, z, r) in tall:
        top = hy(x, z) + 18
        vine_arch(bb, (prev[0], prev[1]), (x, z), prev[2], top, 8, w=2)
        prev = (x, z, top)
    for _ in range(26):
        s = pick(3)
        if s:
            NT.giant_tree(bb, s[0], hy(s[0], s[1]), s[1], int(rng.integers(14, 22)), rng) if rng.random() < 0.3 else \
                P.tree(bb, s[0], hy(s[0], s[1]) + 1, s[1], int(rng.integers(6, 11)), "jungle")
    return bb, [], DY, gh


def build():
    bb, audit, DY, gh = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(TX - 4, DY + 1, TZ + 3, "easy", "east")
    b.chest(gh[0] + 10, gh[2] + 1, gh[1] + 11, "easy", "north")
    b.chest(46, hy(46, 99) + 1, 99, "easy", "south")
    return b, 0
