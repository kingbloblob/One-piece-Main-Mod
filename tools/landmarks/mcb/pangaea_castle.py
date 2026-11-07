"""Pangaea Castle v3 (2026-10-30 audit: the v1 build was a quartz box with four domes on a flat plate). Redone with
the Minecraft Builder skill: the World Government's palace on its own floating island of Red Line rock in the End.
Silhouette first: a white octagonal curtain wall with eight round towers under slate cones and gold finials, the
great gatehouse with WG flags on the south, and rising inside it the Chambord-like palace shared with Mary Geoise
(round corner towers, chimney spires, the central lantern tower and its gold dome). Inside the palace: the hall of
the Empty Throne ringed by the twenty swords, the Five Elders' chamber, Im's flower room, libraries and state rooms,
and the freezer with the giant straw hat below. In the courtyard: the white boulevard with fountains and lamps,
hedged parterres with rose beds and clipped trees, the CP0 barracks, the banquet hall, and behind the palace Im's
walled flower garden with a gazebo. Outside the wall: meadows, cherry and birch groves and a white rail on the rim.
180 x 180. Canvas y 0 = the island top, world y 62."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, st, lamp_post, wg_flag
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import holy_kit as HK
from mcb import mary_geoise as MG
from mcb.blazing_hell_furnace import block_house

SID = "pangaea_castle"
TITLE = "Pangaea Castle (Holy Land)"
CUTS = [3, 10, 24]
TILER = dict(terrain="none", sky_y=62)

N = 180
CX, CZ = 90, 90
CXC, CZC = 90, 74            # the palace (52 x 32, door south at z ~90)
WR = 60                      # curtain wall "radius" (octagon)
WC = (90, 92)                # wall centre
Q, QB, QP = MG.Q, MG.QB, MG.QP
GOLD, SLATE = MG.GOLD, MG.SLATE
PAVE = [(Q, 0.5), (QB, 0.3), ("minecraft:quartz_block", 0.2)]
LEAF = "minecraft:azalea_leaves[persistent=true,waterlogged=false]"


def octa(X, Z, r):
    dx, dz = np.abs(X - WC[0]), np.abs(Z - WC[1])
    return np.maximum(np.maximum(dx, dz), (dx + dz) / 1.38) - r


def curtain(bb):
    """The octagonal curtain wall: 3 thick, 12 high, a walk with merlons on top, string course in gold, arrow slits;
    eight round towers with slate cones; the south gatehouse."""
    H = 12
    wall = lambda X, y, Z: (octa(X, Z, WR) <= 0) & (octa(X, Z, WR - 3) > 0)
    x1, x2, z1, z2 = WC[0] - WR - 2, WC[0] + WR + 2, WC[1] - WR - 2, WC[1] + WR + 2
    for y in range(-1, H + 1):
        bb.fill_where(x1, y, z1, x2, y, z2, wall, QB if y % 4 else Q)
    bb.fill_where(x1, 1, z1, x2, 1, z2, lambda X, y, Z: (octa(X, Z, WR + 1) <= 0) & (octa(X, Z, WR) > 0), "minecraft:polished_diorite")
    bb.fill_where(x1, H - 3, z1, x2, H - 3, z2, lambda X, y, Z: (octa(X, Z, WR + 0.5) <= 0) & (octa(X, Z, WR - 3.5) > 0), GOLD)
    bb.fill_where(x1, H + 1, z1, x2, H + 1, z2,                      # merlons on both faces
                  lambda X, y, Z: ((octa(X, Z, WR) <= 0) & (octa(X, Z, WR - 1) > 0) | (octa(X, Z, WR - 2) <= 0) & (octa(X, Z, WR - 3) > 0))
                  & (((X + Z) % 3) != 0), QB)
    bb.fill_where(x1, 5, z1, x2, 6, z2, lambda X, y, Z: (octa(X, Z, WR) <= 0) & (octa(X, Z, WR - 1) > 0) & ((X * 3 + Z) % 9 == 0),
                  "minecraft:light_blue_stained_glass_pane")
    # eight towers at the octagon's corners (the dx==dz / axis points)
    towers = []
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        rr = WR / max(abs(math.cos(a)), abs(math.sin(a)), (abs(math.cos(a)) + abs(math.sin(a))) / 1.38)
        towers.append((round(WC[0] + rr * math.cos(a)), round(WC[1] + rr * math.sin(a))))
    for (tx, tz) in towers:
        bb.cylinder(tx, -2, tz, 5, H + 8, Q)
        bb.cylinder(tx, 1, tz, 4, H + 7, AIR)
        for y in (H - 3, H + 3):
            bb.ring(tx, y, tz, 4, 6, y, GOLD if y == H - 3 else QB)
        bb.cylinder(tx, 0, tz, 4, 0, "minecraft:polished_andesite")
        bb.cylinder(tx, H, tz, 4, H, "minecraft:spruce_planks")
        for (dx, dz) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
            bb.fill(tx + dx, 4, tz + dz, tx + dx, 6, tz + dz, "minecraft:light_blue_stained_glass_pane")
            bb.fill(tx + dx, H + 3, tz + dz, tx + dx, H + 5, tz + dz, "minecraft:light_blue_stained_glass_pane")
        bb.ring(tx, H + 8, tz, 5, 6, H + 8, QB)
        P.cone_roof(bb, tx, H + 9, tz, 6, 12, SLATE)
        bb.fill(tx, H + 21, tz, tx, H + 23, tz, GOLD)
        bb.set(tx, H + 24, tz, "minecraft:end_rod[facing=up]")
        # a door from the courtyard, a ladder up, a door onto the wall walk
        sx, sz = int(np.sign(WC[0] - tx)), int(np.sign(WC[1] - tz))
        bb.fill(tx + sx * 4, 1, tz + sz * 4, tx + sx * 5, 3, tz + sz * 5, AIR)
        bb.fill(tx, 1, tz, tx, H, tz, "minecraft:ladder[facing=north,waterlogged=false]")
        bb.fill(tx, 1, tz + 1, tx, H, tz + 1, QB)
        bb.set(tx, H, tz, AIR)
        bb.set(tx + 2, 3, tz - 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    # the south gatehouse: two square towers, the arch, a gold portcullis band, the flags of the World Government
    gz = WC[1] + WR
    for sx in (-1, 1):
        x = WC[0] + sx * 9
        bb.fill(x - 4, -2, gz - 6, x + 4, H + 12, gz + 3, QB)
        bb.fill(x - 3, 1, gz - 5, x + 3, H + 11, gz + 2, AIR)
        for y in (H, H + 6):
            bb.fill(x - 3, y, gz - 5, x + 3, y, gz + 2, "minecraft:spruce_planks")
        bb.fill(x - 5, H + 12, gz - 7, x + 5, H + 12, gz + 4, Q)
        for i in range(x - 5, x + 6, 2):
            bb.set(i, H + 13, gz - 7, QB); bb.set(i, H + 13, gz + 4, QB)
        for i in range(gz - 7, gz + 5, 2):
            bb.set(x - 5, H + 13, i, QB); bb.set(x + 5, H + 13, i, QB)
        for y in (6, 13, 19):
            bb.fill(x - 1, y, gz + 3, x + 1, y + 2, gz + 3, "minecraft:light_blue_stained_glass_pane")
        bb.fill(x, H + 13, gz - 1, x, H + 26, gz - 1, "minecraft:white_concrete")
        wg_flag(bb, x + (1 if sx < 0 else -9), H + 25, gz - 1, w=9, h=6, axis="x")
        bb.fill(x, 1, gz - 5 + 1, x, H + 11, gz - 5 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
        bb.fill(x - sx * 4, 1, gz - 3, x - sx * 4, 3, gz - 2, AIR)
        for y in (H, H + 6):
            bb.set(x, y, gz - 4, "minecraft:ladder[facing=south,waterlogged=false]")
    bb.fill(WC[0] - 5, -1, gz - 6, WC[0] + 5, H + 6, gz + 3, Q)
    P.arched_opening(bb, "x", WC[0], 1, gz - 6, 7, 10, depth=10, trim=GOLD)
    bb.fill(WC[0] - 5, H + 7, gz - 6, WC[0] + 5, H + 7, gz + 3, QB)
    for x in range(WC[0] - 5, WC[0] + 6, 2):
        bb.set(x, H + 8, gz + 3, QB); bb.set(x, H + 8, gz - 6, QB)
    bb.fill(WC[0] - 3, 9, gz + 3, WC[0] + 3, 9, gz + 3, GOLD)
    MG.wg_emblem(bb, WC[0], H + 4, gz + 4, GOLD, k=0.45, axis="x")
    bb.fill(WC[0] - 3, 0, gz - 6, WC[0] + 3, 0, gz + 8, QB)
    return towers


def boulevard(bb, rng):
    """From the gate to the palace steps: white paving with worn edges, lamp posts, two fountains, parterres."""
    z1, z2 = CZC + 26, WC[1] + WR - 6
    NT.cover(bb, CXC - 5, z1, CXC + 5, z2 + 14, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), PAVE, 4401)
    NT.cover(bb, CXC - 38, CZC + 24, CXC + 38, CZC + 28, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), PAVE, 4402)
    for z in range(z1 + 2, z2, 7):
        for x in (CXC - 6, CXC + 6):
            lamp_post(bb, x, 1, z, post="minecraft:quartz_pillar[axis=y]", h=3, light="minecraft:lantern[hanging=false,waterlogged=false]")
    for fz in (CZC + 38, WC[1] + WR - 16):
        bb.cylinder(CXC, 0, fz, 7, 0, PAVE[0][0])
        MG.fountain(bb, CXC, 1, fz, 5)
        bb.cylinder(CXC, 0, fz, 5, 0, QB)
    # parterres either side: hedges round rose beds and clipped trees
    for sx in (-1, 1):
        for (pz1, pz2) in ((CZC + 31, CZC + 47), (CZC + 51, CZC + 67)):
            x1, x2 = sorted((CXC + sx * 9, CXC + sx * 33))
            HK.hedge(bb, x1, pz1, x2, pz1, 2, LEAF); HK.hedge(bb, x1, pz2, x2, pz2, 2, LEAF)
            HK.hedge(bb, x1, pz1, x1, pz2, 2, LEAF); HK.hedge(bb, x2, pz1, x2, pz2, 2, LEAF)
            mz = (pz1 + pz2) // 2
            bb.fill(x1, 1, mz - 1, x2, 2, mz + 1, AIR)
            bb.fill(x1 + 1, 0, mz - 1, x2 - 1, 0, mz + 1, "minecraft:gravel")
            for bx in range(x1 + 3, x2 - 4, 7):
                HK.rose_bed(bb, bx, pz1 + 2, bx + 4, mz - 3, int(rng.integers(0, 999)))
                HK.rose_bed(bb, bx, mz + 3, bx + 4, pz2 - 2, int(rng.integers(0, 999)))
            for bx in (x1 + 2, x2 - 2):
                HK.topiary(bb, bx, mz, 4, LEAF)
            bb.set((x1 + x2) // 2, 1, mz, "minecraft:quartz_pillar[axis=y]")
            bb.set((x1 + x2) // 2, 2, mz, "onepiece:candelabra[facing=north]")


def flower_garden(bb):
    """Behind the palace: Im's walled flower garden, rows of white and gold flowers, a domed gazebo."""
    x1, x2, z1, z2 = CXC - 24, CXC + 24, WC[1] - WR + 5, CZC - 22
    bb.fill(x1, 0, z1, x2, 3, z2, QB)
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, 3, z2 - 1, AIR)
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:grass_block")
    bb.fill(x1, 4, z1, x2, 4, z2, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    bb.fill(x1 + 1, 4, z1 + 1, x2 - 1, 4, z2 - 1, AIR)
    bb.fill(CXC - 1, 1, z2, CXC + 1, 3, z2, AIR)
    fl = ("minecraft:lily_of_the_valley", "minecraft:white_tulip", "minecraft:oxeye_daisy", "minecraft:dandelion", "minecraft:azure_bluet")
    for x in range(x1 + 2, x2 - 1):
        for z in range(z1 + 2, z2 - 1):
            if (x - CXC) % 6 in (0, 1) or abs(x - CXC) < 3:
                bb.set(x, 0, z, "minecraft:gravel" if abs(x - CXC) < 3 else "minecraft:grass_block")
                continue
            bb.set(x, 1, z, fl[((x - x1) // 6 + (z // 4)) % len(fl)])
    gz = (z1 + z2) // 2
    bb.cylinder(CXC, 0, gz, 6, 0, QB)
    bb.cylinder(CXC, 0, gz, 5, 0, Q)
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.fill(round(CXC + 5 * math.cos(t)), 1, round(gz + 5 * math.sin(t)), round(CXC + 5 * math.cos(t)), 5, round(gz + 5 * math.sin(t)), QP)
    bb.cylinder(CXC, 6, gz, 6, 6, Q)
    bb.dome(CXC, 7, gz, 5, GOLD)
    bb.set(CXC, 13, gz, "minecraft:end_rod[facing=up]")
    bb.set(CXC, 5, gz, "minecraft:lantern[hanging=true,waterlogged=false]")
    bb.fill(CXC - 1, 1, gz - 1, CXC + 1, 1, gz + 1, "minecraft:white_carpet")
    bb.set(CXC, 1, gz - 2, st("minecraft:quartz_stairs", "south"))


def groves(bb, shp, rng):
    """Outside the wall: cherry and birch groves, flower meadows, plants in drifts."""
    out = lambda X, Z: (octa(X, Z, WR + 4) > 0) & (shp(X, Z) > 4)
    n = 0
    for _ in range(2000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if not out(np.array([[x]]), np.array([[z]]))[0, 0] or abs(x - CX) < 7 and z > WC[1]:
            continue
        P.tree(bb, x, 1, z, height=int(rng.integers(6, 10)), kind="cherry" if NT.noise(x, z, 4410, 30) > 0.45 else "birch", rng=rng)
        n += 1
        if n >= 34:
            break
    NT.plants(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), 4411, density=0.3,
              kinds=NT.PLANTS_MEADOW, flowers=["minecraft:white_tulip", "minecraft:oxeye_daisy", "minecraft:lily_of_the_valley",
                                               "minecraft:allium"], mask=lambda X, Z: (octa(X, Z, WR + 1) > 0) & (shp(X, Z) > 2))
    NT.plants(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), 4412, density=0.1,
              kinds=["minecraft:short_grass"], flowers=["minecraft:white_tulip"], mask=lambda X, Z: octa(X, Z, WR - 4) < 0)


def design():
    _saved = MG.TOP, MG.CXC, MG.CZC
    MG.TOP, MG.CXC, MG.CZC = 0, CXC, CZC
    bb = BigBuild(seed=4400, y_min=-60, y_max=90)
    tracker = P.PropTracker(4400)
    audit = []
    rng = np.random.default_rng(4400)
    shp = HK.floating_island(bb, CX, CZ + 2, 84, 4403, depth=48)
    curtain(bb)
    MG.castle(bb, tracker, audit)
    boulevard(bb, rng)
    flower_garden(bb)
    # the CP0 barracks (west) and the banquet hall (east), flanking the palace forecourt
    block_house(bb, CXC - 52, CZC + 2, CXC - 36, CZC + 20, 2, QB, "minecraft:birch_planks", Q, "minecraft:light_blue_stained_glass_pane",
                ("barracks", "armory"), "birch", "east", 4420)
    block_house(bb, CXC + 36, CZC + 2, CXC + 52, CZC + 20, 2, QB, "minecraft:birch_planks", Q, "minecraft:light_blue_stained_glass_pane",
                ("dining", "kitchen"), "birch", "west", 4421)
    for x in (CXC - 44, CXC + 44):
        bb.set(x, 14, CZC + 11, GOLD)
        bb.fill(x, 15, CZC + 11, x, 22, CZC + 11, "minecraft:white_concrete")
        wg_flag(bb, x + 1, 22, CZC + 11, w=7, h=5, axis="x")
    groves(bb, shp, rng)
    HK.balustrade(bb, shp, 0, 0, N - 1, N - 1, skip=lambda X, Z: (np.abs(X - CX) < 4) & (Z > CZ))
    # the landing on the south rim, under the gate: steps down to a little pier for sky boats
    pz = int(max(z for z in range(CZ, N) if shp(np.array([[CX]]), np.array([[z]]))[0, 0] > 0))
    bb.fill(CX - 3, 0, WC[1] + WR + 8, CX + 3, 0, pz + 6, QB)
    for x in (CX - 4, CX + 4):
        for z in range(WC[1] + WR + 8, pz + 7, 3):
            bb.set(x, 1, z, QP)
            bb.set(x, 2, z, "minecraft:lantern[hanging=false,waterlogged=false]" if z % 2 else "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    MG.TOP, MG.CXC, MG.CZC = _saved
    return bb, audit


def build():
    bb, audit = design()
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.chest(CXC - 3, 2, CZC - 13, "legendary", "south")
    b.chest(CXC + 3, 2, CZC - 13, "celestial", "south")
    b.chest(CXC + 3, -13, CZC - 8, "treasure", "west")
    b.chest(CXC - 50, 1, CZC + 4, "celestial", "east")
    b.guards("cp0_agent", ((CXC - 4, CZC + 26), (CXC + 4, CZC + 26), (CXC, CZC + 8), (CXC - 44, CZC + 24)), y=1)
    b.guards("vice_admiral", ((CXC, WC[1] + WR - 10),), y=1)
    b.guards("pacifista", ((CXC - 8, WC[1] + WR - 9), (CXC + 8, WC[1] + WR - 9)), y=1)
    return b, 0
