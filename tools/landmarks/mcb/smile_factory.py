"""SMILE Factory v2, redesigned with the Minecraft Builder skill: the Donquixote Family's secret underground trade
port, like the one under Dressrosa (ch 727-760, ep 657+: the underground trade port where Doflamingo's men ship
SMILE fruits to Kaido; the factory run by Caesar's formula, the toy-slaves' workshops, Sugar's lookout).

Silhouette first: a vast cavern with a flooded canal down its middle and a stone quay where a smuggling ship lies
loading crates under a wooden crane; on the far side the factory hall, a big brick shed with three tall smoke stacks
rising into the dark, rows of copper brewing tanks with glowing glass sight-panes and pipes snaking over the roof,
and SMILE painted huge in yellow on its wall with the Donquixote Jolly Roger.

Around it: the warehouse (stacked crates and barrels, a cart rail to the quay), the overseers' office on stilts with a
view of the floor, the workers' cramped little houses in rows along a back lane, Sugar's grape table on a balcony,
lamp posts, catwalks, cave walls with dripstone and lanterns hung on chains, tunnels out.
Canvas y 0 = the quay level (world y -34). 128 x 96. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady, lamp_post
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.hulls import galleon, transfer

SID = "smile_factory"
TITLE = "SMILE Factory (Underground Trade Port)"
CUTS = [5, 12, 20]
TILER = dict(terrain="none", sky_y=-34)

NX, NZ = 128, 96
DOME_H = 30
BLOBS = [(64, 48, 60, 44, DOME_H)]
CANAL = (40, 52)                     # canal z range, runs along x
FX1, FZ1, FX2, FZ2 = 30, 8, 78, 34   # factory hall
WX1, WZ1, WX2, WZ2 = 84, 10, 112, 32  # warehouse
BRICK = ["minecraft:bricks", "minecraft:bricks", "minecraft:mud_bricks", "minecraft:packed_mud"]


def cavern(X, y, Z, grow=0.0):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    best = np.full(np.broadcast(X, Z, y).shape, 9.0)
    for (cx, cz, rx, rz, h) in BLOBS:
        v = ((X - cx) / (rx + grow)) ** 4 + ((Z - cz) / (rz + grow)) ** 4 + (np.maximum(0, y) / (h + grow)) ** 2
        best = np.minimum(best, v)
    n = 1 + 0.12 * np.sin(X * 0.31 + Z * 0.17 + y * 0.23) * np.cos(Z * 0.27 - X * 0.11 + y * 0.19)
    return best / n


def cave(bb):
    bb.fill_where(0, -8, 0, NX - 1, DOME_H + 4, NZ - 1, lambda X, y, Z: cavern(X, y, Z, 4) < 1, "minecraft:deepslate")
    bb.fill_where(0, -8, 0, NX - 1, DOME_H + 4, NZ - 1,
                  lambda X, y, Z: (cavern(X, y, Z, 4) < 1) & (NT.noise(X + y * 3, Z, 5401, 5) > 0.65), "minecraft:tuff")
    bb.fill_where(0, 0, 0, NX - 1, DOME_H + 1, NZ - 1, lambda X, y, Z: cavern(X, y + 1, Z) < 1, AIR)       # floor at y -1
    floor = [("minecraft:polished_andesite", 0.25), ("minecraft:stone_bricks", 0.3), ("minecraft:cracked_stone_bricks", 0.15),
             ("minecraft:gravel", 0.1), ("minecraft:andesite", 0.2)]
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, lambda X, Z: np.full(np.broadcast(X, Z).shape, -1), floor, 5402,
             mask=lambda X, Z: cavern(X, 1, Z) < 1, under="minecraft:deepslate", base=-3)
    # canal: cut stone walls, water to y -1, a stone quay edge with bollards
    z1, z2 = CANAL
    bb.fill_where(0, -6, z1, NX - 1, -1, z2, lambda X, y, Z: cavern(X, 1, Z) < 1.15, AIR)
    bb.fill_where(0, -7, z1, NX - 1, -7, z2, lambda X, y, Z: cavern(X, 1, Z) < 1.15, "minecraft:gravel")
    bb.fill_where(0, -6, z1, NX - 1, -2, z2, lambda X, y, Z: cavern(X, 1, Z) < 1.15, "minecraft:water")
    for z in (z1 - 1, z2 + 1):
        bb.fill_where(0, -7, z, NX - 1, -1, z, lambda X, y, Z: cavern(X, 1, Z) < 1.15, "minecraft:stone_bricks")
        for x in range(6, NX - 6, 8):
            if cavern(np.array(float(x)), 1, np.array(float(z))) < 1:
                bb.set(x, 0, z, "minecraft:andesite_wall")
    # the canal runs out under the rock at both ends (water gates: iron bars)
    for x in range(NX):
        if cavern(np.array(float(x)), 1, np.array(float((z1 + z2) / 2))) >= 1:
            bb.fill(x, -6, z1, x, -2, z2, "minecraft:stone_bricks")
    for (x, z) in ((5, 0), (NX - 6, 0)):
        pass


def ship(bb):
    """The smuggling ship at the quay: dark hull, black sails with the Donquixote mark (a crossed-out smile), crates on deck."""
    src = galleon(length=30, beam=11, depth=8, masts=2, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks",
                  sail="minecraft:black_wool", castle=True, guns=True, figure="minecraft:pink_wool")
    where = transfer(bb, src, -2, 36, 20, -6, (CANAL[0] + CANAL[1]) // 2, drop_above=25)          # waterline at y -2
    for (dx, dz) in ((14, -2), (15, -2), (14, 2), (18, 0), (19, 0), (18, -2)):
        x, y, z = where(dx, 7, dz)
        bb.set(x, y, z, "minecraft:barrel[facing=up]" if (dx + dz) % 2 else "minecraft:spruce_planks")
    # Jolly Roger on the main sail: a smiling face crossed out
    mx, my, mz = where(int(0.68 * 29) + 1, 16, 0)
    for (u, v) in ((-2, 0), (2, 0), (-2, -2), (-1, -3), (0, -3), (1, -3), (2, -2)):
        bb.set(mx, my + v, mz + u, "minecraft:yellow_wool")
    for k in range(-3, 4):
        bb.set(mx, my - 1 + k, mz + k, "minecraft:red_wool")
    # crane on the quay
    cx, cz = 52, CANAL[0] - 3
    bb.fill(cx, 1, cz, cx, 14, cz, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(cx, 14, cz, cx, 14, cz + 9, "minecraft:dark_oak_planks")
    bb.fill(cx, 8, cz + 9, cx, 13, cz + 9, "minecraft:iron_chain[axis=y]")
    bb.fill(cx, 6, cz + 8, cx, 7, cz + 10, "minecraft:spruce_planks")
    for k in range(4):
        bb.set(cx - 1 - k, 13 - k * 3, cz, "minecraft:dark_oak_fence")
    return where


def factory(bb):
    """Brick shed with clerestory windows, three smoke stacks, brewing tanks inside with glowing sight-panes, pipes,
    a long workbench line, SMILE painted on the canal-side wall."""
    x1, z1, x2, z2 = FX1, FZ1, FX2, FZ2
    H = 12
    bb.mix(x1, 0, z1, x2, H, z2, BRICK, [0.5, 0.2, 0.15, 0.15])
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, H - 1, z2 - 1, AIR)
    bb.fill(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, "minecraft:polished_deepslate")
    for x in range(x1, x2 + 1, 6):
        for z in (z1, z2):
            bb.fill(x, 0, z, x, H, z, "minecraft:stone_bricks")
            if x + 3 <= x2:
                bb.fill(x + 2, 6, z, x + 4, 9, z, "minecraft:glass_pane" if z == z2 else "minecraft:brown_stained_glass_pane")
    # saw-tooth roof
    for k, x in enumerate(range(x1, x2 + 1, 8)):
        for s in range(5):
            bb.fill(x + s, H + 1 + s // 2, z1, x + s, H + 1 + s // 2, z2, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]" if s % 2 == 0 else "minecraft:deepslate_tiles")
        bb.fill(x + 5, H + 1, z1, x + 5, H + 3, z2, "minecraft:glass")
    # smoke stacks
    for x in (x1 + 8, x1 + 24, x1 + 40):
        bb.cylinder(x, 0, z1 + 4, 2, DOME_H - 2, "minecraft:bricks", hollow=True)
        bb.cylinder(x, DOME_H - 3, z1 + 4, 3, DOME_H - 3, "minecraft:bricks")
        for y in range(H + 4, DOME_H - 3, 5):
            bb.set(x, y, z1 + 4 - 3, "minecraft:iron_bars")
        bb.set(x, 0, z1 + 4, "minecraft:campfire[lit=true]")
    # brewing tanks: copper cylinders with glowing panes, catwalk on top, pipes to the roof
    for k, x in enumerate(range(x1 + 5, x2 - 3, 8)):
        z = z1 + 12
        bb.cylinder(x, 0, z, 2, 7, "minecraft:waxed_copper_block")
        bb.set(x + 2, 3, z, "minecraft:lime_stained_glass"); bb.set(x + 2, 4, z, "minecraft:lime_stained_glass")
        bb.set(x - 2, 3, z, "minecraft:ochre_froglight")
        bb.fill(x, 8, z, x, H - 1, z, "minecraft:waxed_cut_copper")
        bb.fill(x, H - 1, z, x + 4, H - 1, z, "minecraft:waxed_cut_copper")
    bb.fill(x1 + 2, 8, z1 + 15, x2 - 2, 8, z1 + 15, "minecraft:spruce_slab[type=top,waterlogged=false]")
    bb.fill(x1 + 2, 9, z1 + 15, x2 - 2, 9, z1 + 15, "minecraft:iron_bars")
    for k in range(8):
        bb.set(x2 - 2, k, z1 + 16 + k // 3 if False else z1 + 15, "minecraft:ladder[facing=west]") if False else None
    bb.fill(x2 - 2, 0, z1 + 16, x2 - 2, 8, z1 + 16, "minecraft:ladder[facing=north]")
    # workbench line: fruit sorting tables with baskets of SMILE fruits (pink/purple/orange blocks)
    for x in range(x1 + 3, x2 - 2, 3):
        bb.set(x, 0, z2 - 4, "minecraft:spruce_slab[type=top,waterlogged=false]")
        bb.set(x, 1, z2 - 4, ["minecraft:pink_concrete", "minecraft:purple_terracotta", "minecraft:orange_terracotta"][x % 3] if x % 2 else "minecraft:composter[level=7]")
        bb.set(x, 0, z2 - 3, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    bb.set(x1 + 2, 0, z1 + 2, "minecraft:brewing_stand"); bb.set(x1 + 3, 0, z1 + 2, "minecraft:cauldron")
    for x in range(x1 + 4, x2 - 3, 6):
        bb.set(x, H - 1, (z1 + z2) // 2, "minecraft:lantern[hanging=true,waterlogged=false]")
    # doors to the quay
    for x in ((x1 + x2) // 2 - 1, (x1 + x2) // 2, (x1 + x2) // 2 + 1):
        bb.fill(x, 0, z2, x, 3, z2, AIR)


def warehouse(bb):
    x1, z1, x2, z2 = WX1, WZ1, WX2, WZ2
    bb.fill(x1, 0, z1, x2, 9, z2, "minecraft:spruce_planks")
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 8, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, 0, z, x, 9, z, "minecraft:stripped_spruce_log[axis=y]")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, 10, "minecraft:dark_oak_stairs", ridge="minecraft:dark_oak_slab[type=bottom]",
                 ridge_axis="x", gable_fill="minecraft:spruce_planks", overhang=1)
    for x in range(x1 + 2, x2 - 1, 3):
        for z in range(z1 + 2, z2 - 4, 4):
            h = 1 + (x + z) % 4
            for y in range(h):
                bb.set(x, y, z, "minecraft:barrel[facing=up]" if (x + y) % 2 else "minecraft:spruce_planks")
                bb.set(x + 1, y, z, "minecraft:spruce_planks" if (x + y) % 2 else "minecraft:barrel[facing=up]")
    bb.fill((x1 + x2) // 2 - 1, 0, z2, (x1 + x2) // 2 + 1, 3, z2, AIR)
    # cart rail from the warehouse door to the quay
    for z in range(z2 + 1, CANAL[0] - 1):
        bb.set((x1 + x2) // 2, 0, z, "minecraft:rail[shape=north_south]")
    bb.set((x1 + x2) // 2, 0, CANAL[0] - 2, "minecraft:rail[shape=north_south]")


def office_and_houses(bb):
    """The overseers' office on stilts beside the factory, Sugar's balcony, and the workers' little houses south of the
    canal in two cramped rows."""
    ox, oz = 14, 12
    for (a, b) in ((0, 0), (9, 0), (0, 8), (9, 8)):
        bb.fill(ox + a, 0, oz + b, ox + a, 6, oz + b, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(ox - 1, 7, oz - 1, ox + 10, 7, oz + 9, "minecraft:dark_oak_planks")
    bb.fill(ox, 8, oz, ox + 9, 12, oz + 8, "minecraft:pink_terracotta")
    bb.fill(ox + 1, 8, oz + 1, ox + 8, 11, oz + 7, AIR)
    for x in (ox + 2, ox + 5, ox + 8):
        bb.fill(x, 9, oz + 8, x, 10, oz + 8, "minecraft:glass_pane")
    bb.fill(ox - 1, 13, oz - 1, ox + 10, 13, oz + 9, "minecraft:magenta_terracotta")
    furnish_kit(bb, (ox + 1, oz + 1, ox + 8, oz + 7), 8, 3, "office", wood="dark_oak", seed=5403, doors=[(ox + 9, oz + 4)], accent="pink")
    bb.fill(ox + 9, 8, oz + 4, ox + 9, 9, oz + 4, AIR)
    bb.fill(ox + 10, 7, oz + 2, ox + 13, 7, oz + 6, "minecraft:dark_oak_planks")         # Sugar's balcony
    bb.fill(ox + 13, 8, oz + 2, ox + 13, 8, oz + 6, "minecraft:dark_oak_fence")
    bb.set(ox + 11, 8, oz + 4, "minecraft:dark_oak_fence"); bb.set(ox + 11, 9, oz + 4, "minecraft:purple_carpet")
    bb.set(ox + 12, 8, oz + 4, "minecraft:dark_oak_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    for k in range(7):
        bb.set(ox + 11, k, oz + 8 + k // 2 if False else oz + 8, "minecraft:ladder[facing=south]") if False else None
    bb.fill(ox + 11, 0, oz + 7, ox + 11, 7, oz + 7, "minecraft:ladder[facing=north]")
    bb.set(ox + 11, 7, oz + 7, "minecraft:ladder[facing=north]")
    # workers' houses: rows of small shacks south of the canal
    cols = ["minecraft:white_terracotta", "minecraft:light_gray_terracotta", "minecraft:brown_terracotta", "minecraft:yellow_terracotta"]
    k = 0
    for z0 in (CANAL[1] + 8, CANAL[1] + 22):
        for x0 in range(18, 112, 9):
            if cavern(np.array(float(x0)), 4, np.array(float(z0))) >= 0.85 or cavern(np.array(float(x0 + 6)), 4, np.array(float(z0 + 7))) >= 0.85:
                continue
            c = cols[k % 4]; k += 1
            bb.fill(x0, 0, z0, x0 + 6, 4, z0 + 6, c)
            bb.fill(x0 + 1, 0, z0 + 1, x0 + 5, 3, z0 + 5, AIR)
            bb.fill(x0 + 3, 0, z0, x0 + 3, 1, z0, AIR)
            bb.set(x0 + 1, 2, z0, "minecraft:glass_pane"); bb.set(x0 + 5, 2, z0, "minecraft:glass_pane")
            P.gable_roof(bb, x0 - 1, z0 - 1, x0 + 7, z0 + 7, 5, "minecraft:spruce_stairs", ridge="minecraft:spruce_slab[type=bottom]",
                         ridge_axis="x", gable_fill=c, overhang=0)
            bb.set(x0 + 1, 0, z0 + 5, "minecraft:white_bed[facing=east,part=foot]"); bb.set(x0 + 2, 0, z0 + 5, "minecraft:white_bed[facing=east,part=head]")
            bb.set(x0 + 5, 0, z0 + 5, "minecraft:barrel[facing=up]")
            bb.set(x0 + 5, 0, z0 + 1, "minecraft:lantern")
    for x in range(14, 116, 12):
        lamp_post(bb, x, 0, CANAL[1] + 18, post="minecraft:dark_oak_fence", h=4)
        lamp_post(bb, x, 0, CANAL[0] - 4, post="minecraft:dark_oak_fence", h=4)
    return (ox, oz)


def design():
    bb = BigBuild(seed=5400, y_min=-10, y_max=DOME_H + 6)
    cave(bb)
    where = ship(bb)
    factory(bb)
    warehouse(bb)
    office = office_and_houses(bb)
    # bridge over the canal
    for x in range(64, 69):
        bb.fill(x, 0, CANAL[0] - 1, x, 0, CANAL[1] + 1, "minecraft:spruce_planks")
        bb.fill(x, 1, CANAL[0] - 1, x, 3, CANAL[1] + 1, AIR)
        bb.fill(x, -1, CANAL[0], x, -1, CANAL[1], AIR)
    bb.fill(63, 1, CANAL[0], 63, 1, CANAL[1], "minecraft:spruce_fence"); bb.fill(69, 1, CANAL[0], 69, 1, CANAL[1], "minecraft:spruce_fence")
    # lanterns hanging on chains from the roof
    rng = np.random.default_rng(5404)
    for _ in range(40):
        x, z = int(rng.integers(8, NX - 8)), int(rng.integers(8, NZ - 8))
        col = bb.get_region(x, 0, z, x, DOME_H + 2, z)[0, :, 0]
        air = np.nonzero(col == 1)[0]
        if len(air) < 20:
            continue
        top = int(air[-1])
        L = int(rng.integers(3, 9))
        bb.fill(x, top - L + 1, z, x, top, z, "minecraft:iron_chain[axis=y]")
        bb.set(x, top - L, z, "minecraft:lantern[hanging=true,waterlogged=false]")
    # tunnels out
    for (a, b, c) in (((8, 2, 20), (0, 8, 14), 2), ((120, 2, 80), (NX - 1, 8, 88), 2)):
        n = abs(b[0] - a[0])
        for k in range(n + 1):
            t = k / max(n, 1)
            x, y, z = (int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
            bb.fill(x, y, z - c, x, y + 3, z + c, AIR)
    return bb, [], where, office


def build():
    bb, audit, where, office = design()
    b = to_canvas(bb)
    # SMILE in big yellow letters on the factory's canal-side wall (read from the quay, the +z side)
    b.text(FX1 + 9, 3, FZ2 + 1, "SMILE", "minecraft:yellow_concrete", axis="x", step=1, scale=2)
    x, y, z = where(5, 7, 0)
    b.chest(x, y, z, "smile_factory", "east")
    b.chest(FX2 - 2, 0, FZ1 + 2, "smile_factory", "west")
    b.chest(FX1 + 2, 0, FZ2 - 2, "lab", "east")
    b.chest(WX2 - 2, 0, WZ1 + 2, "smile_factory", "west")
    b.chest(office[0] + 2, 8, office[1] + 2, "smile_factory", "east")
    for (x, z, kit) in ((48, CANAL[0] - 6, "donquixote"), (90, CANAL[0] - 4, "donquixote"), (30, CANAL[1] + 16, "donquixote"),
                        (70, 20, "donquixote"), (100, 36, "gifter"), (20, 30, "gifter"), (54, 28, "headliner")):
        b.guard(x, 0, z, kit)
    return b, 0
