"""Rusukaina v2, redesigned with the Minecraft Builder skill: the Calm Belt island where Luffy trained two years with
Rayleigh (anime ep 517 flashbacks; manga ch 597/602): a savage jungle of huge trees and giant beasts.

Silhouette first: a jagged grey mountain in the middle with sheer cliffs and a white waterfall falling into a jungle
pool, ringed by colossal jungle trees (2x2 trunks, buttress roots, vines) that tower over everything else; one
giant tree lies knocked flat across the clearing where Luffy punched it down.

Around it: the beasts' bone field (a giant rib cage and skull, scattered bones), the training clearing (Luffy's
lean-to hut with a hammock and drying meat, a fire pit with a roasting spit, sparring boulders cracked by Haki
punches, a fist-dented stone, footprints), Rayleigh's camp by the pool (tent, sake barrels, a fishing line, a stool),
the mountain-top lookout with Rayleigh's view of the sea, jungle trails. 144 x 144, land site, ground y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "rusukaina"
TITLE = "Rusukaina Training Grounds"
CUTS = [3, 14, 30]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 144
MX, MZ = 82, 54                    # mountain centre
PX, PZ = 82, 92                    # waterfall pool
CX, CZ = 44, 92                    # training clearing
_LAND = NT.outline(72, 72, 68, 7301, wobble=0.12)
_MTN = NT.outline(MX, MZ, 26, 7302, wobble=0.3, lobes=((3, 0.12), (5, 0.08), (7, 0.05)))
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.12), ("minecraft:mossy_cobblestone", 0.12),
        ("minecraft:cobblestone", 0.08), ("minecraft:moss_block", 0.08)]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    base = 2 + NT.fbm(X, Z, 7303, 20) * 5
    base = np.where(d < 14, base * np.clip(d / 14.0, 0, 1), base)
    m = _MTN(X, Z)
    cliff = np.clip((m + 2) / 3.0, 0, 1)                            # sheer step at the outline
    peak = 24 + np.clip(m, 0, None) * 1.1 + NT.fbm(X, Z, 7304, 7) * 10
    h = np.maximum(base, cliff * peak)
    clear = np.hypot(X - CX, Z - CZ) < 15                          # the training clearing is flattish
    h = np.where(clear, np.minimum(h, 3), h)
    pool = np.hypot((X - PX) / 1.2, Z - PZ)
    h = np.where(pool < 9, -3, h)
    h = np.where((pool >= 9) & (pool < 12), np.minimum(h, 1), h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def onland(X, Z):
    return _LAND(np.asarray(X, float), np.asarray(Z, float)) > 0


def terrain(bb):
    rock = lambda X, Z: onland(X, Z) & (_MTN(X, Z) > -2) & (height(X, Z) > 8)
    pool = lambda X, Z: np.hypot((X - PX) / 1.2, Z - PZ) < 9
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.JUNGLE, 7305, mask=lambda X, Z: onland(X, Z) & ~rock(X, Z) & ~pool(X, Z),
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 7306, mask=rock, under="minecraft:stone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:gravel", 0.4), ("minecraft:mud", 0.3), ("minecraft:clay", 0.3)], 7307,
             mask=pool, under="minecraft:stone", core="minecraft:stone", base=-8)
    bb.fill_where(PX - 12, -2, PZ - 10, PX + 12, 0, PZ + 10, lambda X, y, Z: pool(X, Z), "minecraft:water")
    # stone columns on the cliffs (stacked ledges) so the faces are never smooth
    rng = np.random.default_rng(7308)
    for _ in range(60):
        a = rng.uniform(0, 6.283)
        r = 20 + rng.uniform(0, 10)
        x, z = int(MX + r * math.cos(a)), int(MZ + r * math.sin(a))
        if abs(_MTN(np.array(float(x)), np.array(float(z)))) < 3 and hy(x, z) > 6:
            NT.boulder(bb, x, int(rng.integers(6, max(7, hy(x, z)))), z, rng.uniform(2, 3.5), rng,
                       blocks=("minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:mossy_cobblestone"))
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 7309, density=0.45, kinds=NT.PLANTS_JUNGLE + ["onepiece:giant_fern"],
              flowers=["minecraft:blue_orchid", "minecraft:poppy"], mask=lambda X, Z: onland(X, Z) & ~rock(X, Z))


def jungle(bb, taken):
    """Colossal trees ring the mountain and fill the island; ordinary jungle trees and bushes between them."""
    rng = np.random.default_rng(7310)
    placed = []
    for _ in range(900):
        if len(placed) >= 30:
            break
        x, z = int(rng.integers(8, N - 9)), int(rng.integers(8, N - 9))
        d = _LAND(np.array(float(x)), np.array(float(z)))
        if d < 8 or _MTN(np.array(float(x)), np.array(float(z))) > -3 or any(a <= x <= c and b <= z <= e for (a, b, c, e) in taken):
            continue
        if any((x - a) ** 2 + (z - b) ** 2 < 15 ** 2 for (a, b) in placed):
            continue
        placed.append((x, z))
        NT.giant_tree(bb, x, hy(x, z), z, int(rng.integers(22, 36)), rng)
    for _ in range(140):
        x, z = int(rng.integers(6, N - 7)), int(rng.integers(6, N - 7))
        d = _LAND(np.array(float(x)), np.array(float(z)))
        if d < 4 or hy(x, z) > 9 or hy(x, z) < 1 or any(a <= x <= c and b <= z <= e for (a, b, c, e) in taken):
            continue
        if rng.random() < 0.55:
            P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 13)), "jungle")
        else:
            bb.fill_where(x - 2, hy(x, z) + 1, z - 2, x + 2, hy(x, z) + 2, z + 2,
                          lambda X, y, Z: (X - x) ** 2 + (Z - z) ** 2 + (y - hy(x, z) - 1) ** 2 * 2 < 5,
                          "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", only_empty=True)


def waterfall(bb):
    """Water drops down the south cliff into the pool: a notch cut into the rock, a source pond on the ledge above."""
    # find the cliff top straight north of the pool
    z_top = PZ - 9
    while z_top > MZ and hy(PX, z_top) < 16:
        z_top -= 1
    top = hy(PX, z_top)
    for x in range(PX - 1, PX + 2):
        for z in range(z_top - 4, PZ - 8):
            hz = hy(x, z)
            bb.fill(x, 0, z, x, max(hz, top), z, AIR)
            bb.set(x, -1, z, "minecraft:stone")
    for x in (PX - 2, PX + 2):
        bb.fill(x, 0, z_top - 4, x, top, PZ - 9, "minecraft:mossy_cobblestone")
    bb.fill(PX - 2, -1, z_top - 6, PX + 2, top, z_top - 5, "minecraft:mossy_cobblestone")
    # the falling column against the back of the notch, a stepped run down to the pool
    bb.fill(PX - 1, 1, z_top - 4, PX + 1, top, z_top - 4, "minecraft:water")
    bb.fill(PX - 1, 0, z_top - 4, PX + 1, 0, PZ - 9, "minecraft:water")
    # mist: white stained glass speckles low over the pool's back
    for (dx, dz) in ((-3, -6), (2, -7), (4, -5), (-1, -8)):
        bb.set(PX + dx, 1, PZ + dz, "minecraft:white_stained_glass_pane")
    return z_top, top


def bones(bb):
    """The bone field of a giant beast: a rib cage over a spine, a horned skull, scattered bones."""
    sx, sz, y = 112, 96, hy(112, 96)
    for k in range(22):
        bb.set(sx - k, y + 3 + (1 if 6 < k < 14 else 0), sz, "minecraft:bone_block[axis=x]")
    for k in range(2, 18, 3):
        r = 7 - abs(k - 9) * 0.35
        for a in range(0, 181, 9):
            t = math.radians(a)
            dz = int(round(r * math.cos(t)))
            dy = int(round(r * 0.9 * math.sin(t)))
            if dy < 0:
                continue
            bb.set(sx - k, y + dy, sz + dz, "minecraft:bone_block[axis=y]")
    # skull east of the spine with eye sockets and horns
    hx = sx + 3
    bb.fill_where(hx - 1, y, sz - 4, hx + 7, y + 6, sz + 4,
                  lambda X, yy, Z: ((X - hx - 3) / 4.5) ** 2 + ((yy - y - 2) / 3.5) ** 2 + ((Z - sz) / 4.2) ** 2 <= 1,
                  "minecraft:bone_block")
    bb.fill_where(hx, y + 1, sz - 3, hx + 6, y + 4, sz + 3,
                  lambda X, yy, Z: ((X - hx - 3) / 3.5) ** 2 + ((yy - y - 2) / 2.5) ** 2 + ((Z - sz) / 3.2) ** 2 <= 1, AIR)
    for dz in (-2, 2):
        bb.fill(hx + 6, y + 3, sz + dz, hx + 7, y + 3, sz + dz, AIR)
    for s in (-1, 1):
        for k in range(6):
            bb.set(hx + 2 + k // 2, y + 5 + k, sz + s * (4 + k // 2), "minecraft:bone_block")
    bb.fill(hx + 7, y, sz - 2, hx + 9, y, sz + 2, "minecraft:bone_block")
    for (dx, dz) in ((2, 3), (3, -3), (5, 2), (6, -2)):
        bb.set(hx + 7 + dx // 3, y + 1, sz + dz // 2, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up]")
    rng = np.random.default_rng(7311)
    for _ in range(26):
        x, z = sx - 26 + int(rng.integers(0, 40)), sz - 14 + int(rng.integers(0, 28))
        if _LAND(np.array(float(x)), np.array(float(z))) < 5:
            continue
        yy = hy(x, z)
        ax = "x" if rng.random() < 0.5 else "z"
        L = int(rng.integers(2, 5))
        for i in range(L):
            bb.set(x + (i if ax == "x" else 0), yy + 1, z + (i if ax == "z" else 0), f"minecraft:bone_block[axis={ax}]")
        if rng.random() < 0.3:
            bb.set(x, yy + 1, z, "minecraft:skeleton_skull")
    return (sx, sz, y)


def fallen_tree(bb):
    """The giant tree Luffy knocked down: a broken stump with splinters, the 3x3 trunk lying across the clearing's
    north edge, its torn root plate standing up, a dead crown of leaves at the far end."""
    x0, z0 = CX - 22, CZ - 18
    y0 = hy(x0, z0)
    log = "minecraft:jungle_log"
    bb.fill(x0 - 1, y0 - 2, z0 - 1, x0 + 2, y0 + 3, z0 + 2, log + "[axis=y]")
    for (dx, dz, h) in ((-1, -1, 6), (2, 0, 5), (0, 2, 7), (1, -1, 4)):
        bb.fill(x0 + dx, y0 + 4, z0 + dz, x0 + dx, y0 + h, z0 + dz, "minecraft:stripped_jungle_log[axis=y]")
    L = 46
    for k in range(4, L):
        x = x0 + k
        z = z0 + int(round(k * 0.2))
        y = max(hy(x, z), hy(x, z + 1)) + 2
        bb.fill(x, y - 1, z - 1, x, y + 1, z + 1, log + "[axis=x]")
        if k % 9 == 4:
            bb.fill(x, y + 2, z, x, y + 4, z, log + "[axis=y]")
            bb.fill(x - 1, y + 4, z - 2, x + 1, y + 5, z + 2, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]")
    ex, ez = x0 + L, z0 + int(round(L * 0.2))
    ey = hy(ex, ez) + 1
    bb.fill_where(ex - 2, ey, ez - 7, ex + 8, ey + 8, ez + 7,
                  lambda X, y, Z: (((X - ex - 3) / 5.5) ** 2 + ((y - ey - 3) / 4) ** 2 + ((Z - ez) / 6.5) ** 2 <= 1)
                  & (NT.noise(X, Z * 2 + y, 7312, 2) > 0.2),
                  "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", only_empty=True)
    # root plate torn up at the stump side, with soil in it
    for dz in range(-5, 6):
        for dy in range(0, 8):
            if dz * dz + (dy - 3) ** 2 <= 22:
                bb.set(x0 + 4, y0 + dy, z0 + dz, "minecraft:rooted_dirt" if (dz + dy) % 3 else "minecraft:mangrove_roots")
    return (x0, z0)


def camp(bb):
    """Luffy's training clearing: lean-to hut, hammock, drying meat, fire pit with a spit, sparring rocks."""
    y = hy(CX, CZ)
    # trampled ground
    bb.fill_where(CX - 14, y, CZ - 14, CX + 14, y, CZ + 14,
                  lambda X, yy, Z: (np.hypot(X - CX, Z - CZ) < 13) & (NT.noise(X, Z, 7313, 4) > 0.35), "minecraft:coarse_dirt")
    bb.fill_where(CX - 14, y + 1, CZ - 14, CX + 14, y + 4, CZ + 14, lambda X, yy, Z: np.hypot(X - CX, Z - CZ) < 13, AIR)
    # fire pit with a ring of stones and a roasting spit with a big joint of meat
    bb.set(CX, y, CZ, "minecraft:campfire[lit=true]")
    bb.set(CX, y - 1, CZ, "minecraft:stone")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.set(CX + int(round(2 * math.cos(t))), y, CZ + int(round(2 * math.sin(t))), "minecraft:cobblestone")
    bb.fill(CX - 2, y + 1, CZ, CX - 2, y + 2, CZ, "minecraft:jungle_fence")
    bb.fill(CX + 2, y + 1, CZ, CX + 2, y + 2, CZ, "minecraft:jungle_fence")
    bb.fill(CX - 1, y + 3, CZ, CX + 1, y + 3, CZ, "minecraft:stripped_jungle_log[axis=x]")
    bb.set(CX, y + 2, CZ, "minecraft:brown_mushroom_block")
    for (dx, dz) in ((-4, -1), (4, 1), (0, 4)):
        bb.fill(CX + dx, y + 1, CZ + dz, CX + dx + (1 if dz else 0), y + 1, CZ + dz + (0 if dz else 1),
                "minecraft:stripped_jungle_log[axis=x]" if dz else "minecraft:stripped_jungle_log[axis=z]")
    # lean-to hut (palm thatch on a slanted pole frame), hammock between two posts, meat on a drying rack
    hx, hz = CX - 9, CZ + 4
    bb.fill(hx, y, hz, hx + 6, y, hz + 5, "minecraft:jungle_planks")
    for z in range(hz, hz + 6):
        for k in range(6):
            bb.set(hx + k, y + 5 - (k * 4) // 6, z, "minecraft:jungle_slab[type=top]" if k < 5 else "minecraft:jungle_slab[type=bottom]")
        bb.set(hx, y + 5, z, "minecraft:jungle_trapdoor[half=top,facing=east,open=false]" if False else "minecraft:mud_brick_slab[type=bottom]")
    for z in (hz, hz + 5):
        bb.fill(hx, y + 1, z, hx, y + 4, z, "minecraft:jungle_log[axis=y]")
        bb.fill(hx + 5, y + 1, z, hx + 5, y + 1, z, "minecraft:jungle_fence")
    bb.fill(hx - 1, y + 1, hz, hx - 1, y + 4, hz + 5, "minecraft:jungle_planks")
    bb.fill(hx + 1, y + 1, hz + 1, hx + 2, y + 1, hz + 2, "minecraft:brown_wool")
    bb.set(hx + 1, y + 1, hz + 4, "minecraft:barrel[facing=up]")
    bb.set(hx + 2, y + 1, hz + 4, "minecraft:straw_hat" if False else "minecraft:hay_block")
    bb.fill(hx + 8, y + 1, hz + 2, hx + 8, y + 3, hz + 2, "minecraft:jungle_fence")
    bb.fill(hx + 8, y + 1, hz + 7, hx + 8, y + 3, hz + 7, "minecraft:jungle_fence")
    bb.fill(hx + 8, y + 2, hz + 3, hx + 8, y + 2, hz + 6, "minecraft:white_carpet" if False else "minecraft:brown_wool")
    rx, rz = CX + 6, CZ - 7
    bb.fill(rx, y + 1, rz, rx, y + 3, rz, "minecraft:jungle_fence"); bb.fill(rx + 4, y + 1, rz, rx + 4, y + 3, rz, "minecraft:jungle_fence")
    bb.fill(rx, y + 4, rz, rx + 4, y + 4, rz, "minecraft:stripped_jungle_log[axis=x]")
    for k in range(1, 4):
        bb.set(rx + k, y + 3, rz, "minecraft:iron_chain[axis=y]")
        bb.set(rx + k, y + 2, rz, "minecraft:red_mushroom_block" if k % 2 else "minecraft:brown_mushroom_block")
    # sparring boulders: big stones cracked through, one with a fist-sized hole punched clean through it
    rng = np.random.default_rng(7314)
    for (bx, bz, r) in ((CX + 9, CZ + 6, 3.2), (CX + 4, CZ + 10, 2.4), (CX - 3, CZ - 10, 2.8), (CX + 11, CZ - 2, 2.2)):
        by = hy(bx, bz)
        NT.boulder(bb, bx, by + 1, bz, r, rng, blocks=("minecraft:stone", "minecraft:cracked_stone_bricks", "minecraft:andesite"))
    bb.fill(CX + 9, hy(CX + 9, CZ + 6) + 1, CZ + 3, CX + 9, hy(CX + 9, CZ + 6) + 2, CZ + 9, AIR)
    for (bx, bz) in ((CX + 6, CZ + 12), (CX + 1, CZ + 12), (CX - 6, CZ - 12)):
        bb.set(bx, hy(bx, bz) + 1, bz, "minecraft:cobblestone_slab[type=bottom]")
        bb.set(bx + 1, hy(bx, bz) + 1, bz, "minecraft:gravel")
    # Rayleigh's training post: a thick log wrapped with rope
    tx, tz = CX - 2, CZ + 9
    bb.fill(tx, y + 1, tz, tx, y + 5, tz, "minecraft:stripped_spruce_log[axis=y]")
    for yy in (y + 2, y + 4):
        bb.set(tx + 1, yy, tz, "minecraft:tripwire_hook[facing=east]" if False else "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]")
    return (hx, hz, y)


def rayleigh_camp(bb):
    """Rayleigh's camp on the pool shore: a canvas tent, stool, sake barrels, a fishing line and a drying fish."""
    x, z = PX + 13, PZ + 4
    y = hy(x, z)
    bb.fill(x - 3, y, z - 3, x + 4, y, z + 4, "minecraft:coarse_dirt")
    bb.fill(x - 3, y + 1, z - 3, x + 4, y + 5, z + 4, AIR)
    for k in range(4):
        bb.fill(x - 2 + k, y + 1 + k, z - 2, x - 2 + k, y + 1 + k, z + 3, "minecraft:white_wool")
        bb.fill(x + 4 - k, y + 1 + k, z - 2, x + 4 - k, y + 1 + k, z + 3, "minecraft:white_wool")
    bb.fill(x + 1, y + 5, z - 2, x + 1, y + 5, z + 3, "minecraft:white_wool")
    bb.fill(x - 1, y + 1, z - 1, x + 3, y + 3, z + 2, AIR)
    bb.fill(x - 1, y + 1, z + 3, x + 3, y + 3, z + 3, AIR)
    bb.set(x, y + 1, z, "minecraft:brown_bed[facing=north,part=foot]"); bb.set(x, y + 1, z - 1, "minecraft:brown_bed[facing=north,part=head]")
    bb.set(x + 2, y + 1, z - 1, "minecraft:barrel[facing=up]"); bb.set(x + 2, y + 2, z - 1, "minecraft:decorated_pot")
    bb.set(x - 2, y + 1, z + 5, "minecraft:spruce_stairs[facing=south]")
    bb.set(x - 3, y + 1, z + 5, "minecraft:campfire[lit=true]")
    bb.set(x - 4, y + 1, z + 5, "minecraft:barrel[facing=up]"); bb.set(x - 4, y + 1, z + 6, "minecraft:barrel[facing=up]")
    bb.set(x - 4, y + 2, z + 5, "minecraft:barrel[facing=up]")
    # fishing pole leaning over the water
    for k in range(5):
        bb.set(x - 6 - k, y + 1 + k // 2, z - 1, "minecraft:bamboo_fence" if False else "minecraft:spruce_fence")
    bb.fill(x - 10, y - 1, z - 1, x - 10, y + 2, z - 1, "minecraft:iron_chain[axis=y]") if hy(x - 10, z - 1) < 0 else None
    return (x, z, y)


def lookout(bb):
    """A flat rock on the summit with a cairn and a tattered flag: where Rayleigh watched the sea."""
    best = max(((hy(x, z), x, z) for x in range(MX - 10, MX + 11, 2) for z in range(MZ - 10, MZ + 11, 2)))
    y, x, z = best
    bb.fill(x - 3, y, z - 3, x + 3, y, z + 3, "minecraft:smooth_stone")
    bb.fill(x - 3, y + 1, z - 3, x + 3, y + 6, z + 3, AIR)
    for (dx, dz) in ((-3, -3), (3, -2), (2, 3), (-2, 3)):
        bb.set(x + dx, y + 1, z + dz, "minecraft:cobblestone_wall")
    bb.fill(x - 2, y + 1, z - 2, x - 2, y + 3, z - 2, "minecraft:cobblestone")
    bb.fill(x + 2, y + 1, z + 2, x + 2, y + 7, z + 2, "minecraft:spruce_fence")
    bb.fill(x + 3, y + 6, z + 2, x + 5, y + 7, z + 2, "minecraft:red_wool")
    # a rough climbing path cut down the north-west face
    for k in range(40):
        px, pz = x - 3 - k // 2, z - 3 - k // 3
        if hy(px, pz) < 5:
            break
        ty = hy(px, pz)
        bb.fill(px, ty, pz, px + 1, ty, pz, "minecraft:cobblestone_stairs[facing=north]" if k % 2 else "minecraft:gravel")
        bb.fill(px, ty + 1, pz, px + 1, ty + 3, pz, AIR)
    return (x, z, y)


def trails(bb):
    """Packed dirt trails: clearing to the pool camp, pool to the bone field, clearing to the beach."""
    for (a, b) in (((CX, CZ), (PX - 10, PZ)), ((PX + 10, PZ + 2), (100, 96)), ((CX, CZ + 12), (CX - 6, 136))):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]))
        for k in range(n):
            t = k / max(n, 1)
            x = int(round(a[0] + (b[0] - a[0]) * t + 3 * math.sin(t * 6)))
            z = int(round(a[1] + (b[1] - a[1]) * t))
            for dx in (-1, 0, 1):
                y = hy(x + dx, z)
                if y >= 0 and onland(np.array(float(x + dx)), np.array(float(z))):
                    bb.set(x + dx, y, z, "minecraft:dirt_path" if (k + dx) % 5 else "minecraft:coarse_dirt")


def design():
    bb = BigBuild(seed=7300, y_min=-10, y_max=90)
    terrain(bb)
    wz, wy = waterfall(bb)
    bonepos = bones(bb)
    trails(bb)
    hut = camp(bb)
    fallen_tree(bb)
    ray = rayleigh_camp(bb)
    top = lookout(bb)
    taken = [(CX - 16, CZ - 22, CX + 30, CZ + 16), (PX - 14, PZ - 14, PX + 22, PZ + 12), (bonepos[0] - 28, bonepos[1] - 10, bonepos[0] + 14, bonepos[1] + 10)]
    jungle(bb, taken)
    return bb, [], hut, ray, top


def build():
    bb, audit, hut, ray, top = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(hut[0] + 2, hut[2] + 1, hut[1] + 1, "hard", "west")
    b.chest(112 - 6, hy(106, 99) + 1, 99, "hard", "north")
    b.chest(top[0] + 1, top[2] + 1, top[1] - 1, "medium", "south")
    return b, 0
