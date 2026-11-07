"""The Going Merry's farewell v2, redesigned with the Minecraft Builder skill: the Viking funeral of the Straw Hats'
first ship, on the calm sea after Enies Lobby, snow falling.

A rocky, snow-dusted crescent of an islet wraps round a calm cove. In the middle of the cove the Going Merry (the
show-accurate ship kit model, life size) burns: fires all over her decks with tall smoke columns, charred planks, a
crack amidships where her keel gave out, her sail scorched round the Jolly Roger, her ram's head still smiling. Round
her at a respectful distance four small boats of the Franky Family and Galley-La, lanterns lit, where the crew
watched. On the islet's headland the farewell spot: a stone cairn with a straw hat on top, a bench, a lantern for
every crew mate, flowers, Usopp's toolbox and the carpenter's tools he used to patch her, and a little jetty down to
the beach. 144 x 144, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, lamp_post, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "going_merry_farewell"
TITLE = "Going Merry's Farewell"
CUTS = [2, 6, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 144
MX, MZ = 72, 98                    # the Merry (hull centre)
HEAD = (34, 66)                    # the farewell spot on the west headland
_OUT = NT.outline(72, 64, 54, 4410, wobble=0.06)
ROCK = [("minecraft:stone", 0.35), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.12), ("minecraft:cobblestone", 0.1),
        ("minecraft:snow_block", 0.15), ("minecraft:mossy_cobblestone", 0.08)]
TOP = [("minecraft:grass_block", 0.38), ("minecraft:snow_block", 0.34), ("minecraft:podzol", 0.08), ("minecraft:coarse_dirt", 0.08),
       ("minecraft:moss_block", 0.06), ("minecraft:stone", 0.06)]
SAND = [("minecraft:sand", 0.7), ("minecraft:gravel", 0.0), ("minecraft:sandstone", 0.1), ("minecraft:snow_block", 0.2)]
FLOWERS = ["minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy", "minecraft:white_tulip", "minecraft:cornflower"]


def shore(X, Z):
    """How far inside the islet: the outline minus the cove bitten out of its south side."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _OUT(X, Z)
    cove = (1 - np.hypot((X - 72) / 38.0, (Z - 100) / 36.0)) * 34
    return np.minimum(d, -cove)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    rocks = 4 + NT.fbm(X, Z, 4411, 14) * 16
    h = np.where(d < 14, 1 + (rocks - 1) * np.clip((d - 1) / 13.0, 0, 1) ** 1.3, rocks)
    head = np.clip(1 - np.hypot(X - HEAD[0], Z - HEAD[1]) / 10.0, 0, 1)
    h = h * (1 - head) + 9 * head
    return np.where(d < 1, -6 - np.clip(-d * 0.3, 0, 6), np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)
SH = shore(X_, Z_)
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


def terrain(bb):
    steep = lambda X, Z: G[_ix(X, Z)] >= 2
    beach = lambda X, Z: (SH[_ix(X, Z)] < 6) & (height(X, Z) <= 2)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, TOP, 4412, mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ~beach(X, Z), under="minecraft:dirt",
             core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 4413, mask=lambda X, Z: land(X, Z) & steep(X, Z) & ~beach(X, Z), under="minecraft:stone",
             core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 4414, mask=lambda X, Z: land(X, Z) & beach(X, Z), under="minecraft:sandstone",
             core="minecraft:stone", base=-8)
    # rock layers on the cliff faces
    off = lambda X, Z: (NT.fbm(X, Z, 4416, 14) * 5).astype(int)
    for i, blk in enumerate(["minecraft:andesite", "minecraft:tuff", "minecraft:cobblestone", "minecraft:diorite"]):
        bb.fill_where(0, -8, 0, N - 1, 30, N - 1, lambda X, y, Z, i=i: land(X, Z) & (y <= height(X, Z) - 1) & (((y + off(X, Z)) // 2) % 6 == i)
                      & (NT.noise(X + y * 5, Z - y * 3, 4417 + i, 4) > 0.35), blk)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2)
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:stone")
    # fresh snow on the flat tops
    bb.fill_where(0, 1, 0, N - 1, 30, N - 1, lambda X, y, Z: land(X, Z) & ~steep(X, Z) & ~beach(X, Z) & (y == height(X, Z) + 1)
                  & (NT.noise(X, Z, 4415, 5) > 0.42), "minecraft:snow[layers=1]")


# ------------------------------------------------------------------ the burning Merry
FLAME = ["minecraft:orange_stained_glass", "minecraft:red_stained_glass", "minecraft:yellow_stained_glass"]


def burn_merry(bb, rng, box):
    """Fires on her decks (campfires with tall smoke, magma beds, glass flame tongues), charred planks, the sail
    scorched round the edges, the crack amidships."""
    x1, z1, x2, z2 = box
    y1, y2 = -6, 34
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    names = bb.names
    wood = {int(i) for i in np.unique(reg) if i > 1 and any(k in names[int(i)] for k in ("planks", "_log", "stripped"))
            and not names[int(i)].split("[")[0].endswith(("_stairs", "_slab", "_fence", "_trapdoor", "_door"))}
    cloth = {int(i) for i in np.unique(reg) if i > 1 and names[int(i)].split("[")[0].endswith("_wool")}
    cx = (x1 + x2) // 2
    # char planks (more near the crack), scorch the sail edges
    for (ix, iy, iz) in zip(*np.nonzero(np.isin(reg, list(wood)))):
        x, y, z = x1 + ix, y1 + iy, z1 + iz
        p = 0.12 + 0.35 * math.exp(-abs(x - cx) / 4.0)
        if rng.random() < p:
            bb.set(x, y, z, ["minecraft:blackstone", "minecraft:coal_block", "minecraft:polished_blackstone", "minecraft:dark_oak_planks"][int(rng.integers(4))])
    for (ix, iy, iz) in zip(*np.nonzero(np.isin(reg, list(cloth)))):
        x, y, z = x1 + ix, y1 + iy, z1 + iz
        n = names[int(reg[ix, iy, iz])]
        if "white" not in n:
            continue
        # holes and scorch where the sail is near its edges / low down
        if rng.random() < 0.10:
            bb.set(x, y, z, AIR)
        elif rng.random() < 0.12:
            bb.set(x, y, z, "minecraft:gray_wool" if rng.random() < 0.6 else "minecraft:black_wool")
    # the crack amidships: a jagged line of charred and missing planks across the hull
    for z in range(z1, z2 + 1):
        x = cx + int(rng.integers(-1, 2))
        for y in range(-3, 6):
            v = int(bb.get_region(x, y, z, x, y, z)[0, 0, 0])
            if v > 1 and v in wood | {bb.ids.get("minecraft:blackstone", -1), bb.ids.get("minecraft:coal_block", -1)}:
                bb.set(x, y, z, AIR if (y > 0 and rng.random() < 0.5) else "minecraft:coal_block")
    # fires on top of every open deck surface
    top = {}
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    solid = reg > 1
    for ix in range(reg.shape[0]):
        for iz in range(reg.shape[2]):
            col = np.nonzero(solid[ix, :, iz])[0]
            col = col[col <= 12 - y1]
            if len(col):
                top[(ix, iz)] = int(col.max())
    fires = 0
    keys = list(top.keys())
    rng.shuffle(keys)
    for (ix, iz) in keys:
        iy = top[(ix, iz)]
        n = names[int(reg[ix, iy, iz])].split("[")[0]
        if not any(k in n for k in ("planks", "blackstone", "coal_block", "stripped")) or n.endswith(("_stairs", "_slab")):
            continue
        x, y, z = x1 + ix, y1 + iy + 1, z1 + iz
        if y < 2:
            continue
        r = rng.random()
        if r < 0.25:
            bb.set(x, y, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        elif r < 0.45:
            bb.set(x, y - 1, z, "minecraft:magma_block")
        elif r < 0.75:
            h = int(rng.integers(1, 4))
            for k in range(h):
                if bb.get_region(x, y + k, z, x, y + k, z)[0, 0, 0] < 2:
                    bb.set(x, y + k, z, FLAME[min(2, k)] if rng.random() < 0.7 else FLAME[int(rng.integers(3))])
        else:
            bb.set(x, y - 1, z, "minecraft:shroomlight")
        fires += 1
        if fires > 70:
            break
    return fires


def rowboat(bb, x, z, facing, rng, lantern=True):
    """A small rowing boat: a pointed hull of stairs and planks, two thwarts, oars, a lantern on a post."""
    L, W = 9, 4
    dx, dz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[facing]
    px, pz = -dz, dx
    for i in range(L):
        half = 1 if i in (0, L - 1) else 2 if i in (1, L - 2) else 2
        span = [0] if i == L - 1 else [-1, 0, 1] if i in (0, L - 2) else [-2, -1, 0, 1, 2] if False else [-1, 0, 1, 2] if False else [-1, 0, 1]
        span = [0] if i == L - 1 else [-1, 0, 1] if i == L - 2 or i == 0 else [-2, -1, 0, 1, 2]
        for j in span:
            X, Z = x + dx * i + px * j, z + dz * i + pz * j
            edge = abs(j) == max(abs(s) for s in span)
            bb.set(X, -1, Z, "minecraft:spruce_planks" if not edge else "minecraft:spruce_slab[type=top,waterlogged=true]")
            if edge:
                side = "west" if (px * j) < 0 else "east" if (px * j) > 0 else ("north" if (pz * j) < 0 else "south")
                if dx == 0:
                    side = "west" if j * px < 0 else "east"
                else:
                    side = "north" if j * pz < 0 else "south"
                bb.set(X, 0, Z, st("minecraft:spruce_stairs", side))
            else:
                bb.set(X, 0, Z, AIR)
        if i in (3, 6):
            for j in (-1, 0, 1):
                bb.set(x + dx * i + px * j, 0, z + dz * i + pz * j, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    bb.set(x + dx * (L - 1), 1, z + dz * (L - 1), "minecraft:spruce_fence")
    if lantern:
        bb.set(x + dx * (L - 1), 2, z + dz * (L - 1), "minecraft:lantern[hanging=false]")
    for j in (-3, 3):
        bb.set(x + dx * 4 + px * j, 0, z + dz * 4 + pz * j, "minecraft:spruce_fence") if False else None


def farewell_spot(bb, rng):
    hx, hz = HEAD
    y = hy(hx, hz)
    # the cairn with the straw hat on top
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 1), (-2, -1), (1, -2), (-1, 2)):
        bb.fill(hx + dx, y + 1, hz + dz, hx + dx, y + 2, hz + dz, "minecraft:cobblestone" if (dx + dz) % 2 else "minecraft:mossy_cobblestone")
    for (dx, dz, h) in ((0, 0, 4), (1, 0, 4), (-1, 0, 4), (0, 1, 4), (0, -1, 4), (1, 1, 4), (-1, -1, 4), (1, -1, 4), (-1, 1, 4)):
        bb.fill(hx + dx, y + 1, hz + dz, hx + dx, y + h, hz + dz, "minecraft:cobblestone" if (dx + dz) % 2 else "minecraft:mossy_cobblestone")
    bb.set(hx, y + 5, hz, "minecraft:red_carpet") if False else None
    bb.fill(hx - 1, y + 5, hz - 1, hx + 1, y + 5, hz + 1, "minecraft:yellow_carpet")
    bb.set(hx, y + 5, hz, "minecraft:hay_block[axis=y]")
    bb.set(hx, y + 6, hz, "minecraft:red_carpet")
    # a bench looking out over the cove (south-east)
    for i in range(4):
        bb.set(hx + 4 + i, y + 1, hz + 5, st("minecraft:oak_stairs", "north"))
    bb.set(hx + 3, y + 1, hz + 5, "minecraft:oak_wall_sign[facing=west]"); bb.set(hx + 8, y + 1, hz + 5, "minecraft:oak_wall_sign[facing=east]")
    # nine lanterns, one for every crew mate, in an arc facing the sea
    for k in range(9):
        a = math.radians(10 + k * 12)
        x, z = int(round(hx + 9 * math.cos(a))), int(round(hz + 9 * math.sin(a)))
        yy = hy(x, z)
        bb.fill(x, yy + 1, z, x, yy + 1, z, "minecraft:oak_fence")
        bb.set(x, yy + 2, z, "minecraft:lantern[hanging=false]")
    # Usopp's toolbox and the carpenter's tools
    bb.set(hx - 4, y + 1, hz + 3, "minecraft:smithing_table")
    bb.set(hx - 4, y + 1, hz + 4, "minecraft:barrel[facing=up,open=false]")
    bb.set(hx - 5, y + 1, hz + 3, "minecraft:oak_planks"); bb.set(hx - 5, y + 2, hz + 3, "minecraft:oak_pressure_plate")
    bb.set(hx - 3, y + 1, hz + 2, "minecraft:grindstone[face=floor,facing=east]")
    # flowers left for her
    for _ in range(40):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(2, 7)
        x, z = int(round(hx + d * math.cos(a))), int(round(hz + d * math.sin(a)))
        yy = hy(x, z)
        if bb.get_region(x, yy + 1, z, x, yy + 1, z)[0, 0, 0] < 2 and bb.get_region(x, yy, z, x, yy, z)[0, 0, 0] > 1:
            bb.set(x, yy, z, "minecraft:grass_block")
            bb.set(x, yy + 1, z, FLOWERS[int(rng.integers(len(FLOWERS)))])
    # a path and steps down to the beach, then a little jetty into the cove
    path = []
    x, z = hx + 6, hz + 8
    while z < N - 1 and SH[min(x, N - 1), min(z, N - 1)] > 4:
        path.append((x, z)); z += 1
        if z % 3 == 0:
            x += 1
    for (x, z) in path:
        bb.fill(x, hy(x, z), z, x + 1, hy(x, z), z, "minecraft:coarse_dirt")
    if path:
        jx, jz = path[-1]
        for k in range(1, 14):
            bb.fill(jx, -1, jz + k, jx + 2, 0, jz + k, "minecraft:oak_planks" if False else AIR)
            bb.fill(jx, 0, jz + k, jx + 2, 0, jz + k, "minecraft:spruce_slab[type=top,waterlogged=false]")
            if k % 4 == 1:
                bb.fill(jx, -6, jz + k, jx, -1, jz + k, "minecraft:spruce_log[axis=y]")
                bb.fill(jx + 2, -6, jz + k, jx + 2, -1, jz + k, "minecraft:spruce_log[axis=y]")
        bb.set(jx, 1, jz + 13, "minecraft:spruce_fence"); bb.set(jx, 2, jz + 13, "minecraft:lantern[hanging=false]")


def scenery(bb, rng):
    for _ in range(1600):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if not land(np.array([[x]]), np.array([[z]]))[0, 0] or SH[x, z] < 5:
            continue
        if math.hypot(x - HEAD[0], z - HEAD[1]) < 12:
            continue
        y = hy(x, z)
        if bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] > 1 or G[x, z] >= 2:
            continue
        r = rng.random()
        if r < 0.04:
            P.tree(bb, x, y + 1, z, height=int(rng.integers(6, 10)), kind="spruce", rng=rng)
        elif r < 0.06:
            NT.boulder(bb, x, y, z, int(rng.integers(1, 3)), rng, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:snow_block"))
        elif r < 0.12:
            bb.set(x, y + 1, z, "minecraft:sweet_berry_bush[age=1]" if r < 0.08 else "minecraft:fern")


def design():
    bb = BigBuild(seed=4410, y_min=-16, y_max=44)
    rng = np.random.default_rng(4410)
    terrain(bb)
    box = stamp_ship(bb, "going_merry", MX, MZ, water_y=0, rot=0)
    fires = burn_merry(bb, rng, box)
    print("fires:", fires)
    for (x, z, f) in ((MX - 34, MZ - 10, "east"), (MX + 30, MZ - 14, "west"), (MX - 18, MZ + 22, "north"), (MX + 22, MZ + 20, "north")):
        rowboat(bb, x, z, f, rng)
    farewell_spot(bb, rng)
    scenery(bb, rng)
    return bb, [], box


def build():
    bb, audit, box = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(HEAD[0] - 5, hy(HEAD[0] - 5, HEAD[1] + 4) + 1, HEAD[1] + 4, "easy", "south")
    b.chest(box[0] + 3, 3, (box[1] + box[3]) // 2, "medium", "east") if False else None
    return b, 0
