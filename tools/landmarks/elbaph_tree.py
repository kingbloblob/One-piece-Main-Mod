"""Elbaph, the land of the giants: a snowy valley ruled by a tree so vast its crown is a land of its own. The
trunk of the great tree (Adam wood) rises 100 m, with roots like hills, a stair winding up inside its hollow
and a lookout on the first great bough. At its foot the giants' village, built to their size (20 m tall
people): two great longhouses with carved dragon-head gables, giant tables, benches, mead barrels and a hearth
the size of a house, the warriors' training ring with giant weapons, and the rune stones. Wolves roam the pines.
~112 x 112. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "elbaph_tree"
TITLE = "Elbaph Great Tree"
CUTS = [3, 20, 60]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
TX, TZ = 70, 40
TR = 11
ADAM = "onepiece:adam_log"
ADAMW = "onepiece:adam_planks"
GIANT = dict(wood="spruce", rug="red", rug2="brown", bed="brown", light="minecraft:lantern", accent="onepiece:adam_planks",
             banner="red", candle="orange")


def longhouse(b, x0, z0, L, W, H, rnd, seed):
    """A giant longhouse along x: log walls, a steep roof, dragon-head gable ends, door at the west end."""
    b.box(x0, 0, z0, x0 + L, 0, z0 + W, "minecraft:spruce_planks")
    b.walls(x0, 1, z0, x0 + L, H, z0 + W, "minecraft:spruce_log[axis=x]")
    for x in range(x0, x0 + L + 1):
        for y in range(1, H + 1):
            if (y // 3) % 2: b.set(x, y, z0, "minecraft:stripped_spruce_log[axis=x]"); b.set(x, y, z0 + W, "minecraft:stripped_spruce_log[axis=x]")
    b.box(x0 + 1, 1, z0 + 1, x0 + L - 1, H + 12, z0 + W - 1, AIR)
    cz = z0 + W // 2
    for k in range(W // 2 + 2):  # steep roof
        y = H + 1 + k
        for x in range(x0 - 1, x0 + L + 2):
            for zz in (z0 - 1 + k, z0 + W + 1 - k):
                b.set(x, y, zz, "minecraft:dark_oak_planks" if (x // 4) % 2 else "minecraft:spruce_planks")
        for xe in (x0, x0 + L):
            for zz in range(z0 - 1 + k + 1, z0 + W + 1 - k): b.set(xe, y, zz, "minecraft:spruce_planks")
    rt = H + 1 + W // 2 + 1
    for xe, s in ((x0 - 1, -1), (x0 + L + 1, 1)):  # dragon heads on the gables
        for k in range(6): b.set(xe + s * (k // 2), rt + k, cz, "minecraft:dark_oak_log[axis=y]")
        b.box(xe + s * 3, rt + 5, cz - 1, xe + s * 5, rt + 7, cz + 1, "minecraft:dark_oak_planks"); b.set(xe + s * 5, rt + 6, cz, "minecraft:red_concrete")
    for y in range(1, 13):
        for zz in range(cz - 4, cz + 5): b.set(x0, y, zz, AIR)
    for x in range(x0 + 4, x0 + L - 3, 5):  # roof posts down the hall
        b.column(x, z0 + 3, 1, H + 4, "minecraft:spruce_log[axis=y]"); b.column(x, z0 + W - 3, 1, H + 4, "minecraft:spruce_log[axis=y]")
    hx = x0 + L // 2  # the giant hearth
    b.box(hx - 3, 1, cz - 3, hx + 3, 1, cz + 3, "minecraft:cobblestone"); b.box(hx - 2, 2, cz - 2, hx + 2, 2, cz + 2, "minecraft:magma_block")
    b.box(hx - 1, 3, cz - 1, hx + 1, 3, cz + 1, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    for (tx0, tx1) in ((x0 + 3, hx - 5), (hx + 5, x0 + L - 3)):  # giant tables and benches
        b.box(tx0, 1, cz - 4, tx1, 5, cz - 4, "minecraft:spruce_log[axis=x]") if False else None
        b.box(tx0, 6, z0 + 5, tx1, 6, z0 + 8, "minecraft:spruce_planks")
        for x in (tx0, tx1): b.column(x, z0 + 5, 1, 5, "minecraft:spruce_log[axis=y]"); b.column(x, z0 + 8, 1, 5, "minecraft:spruce_log[axis=y]")
        b.box(tx0, 3, z0 + 10, tx1, 3, z0 + 11, "minecraft:spruce_slab[type=top,waterlogged=false]")
        for x in range(tx0 + 2, tx1, 6):  # giant mugs and plates on the table
            b.cyl(x, z0 + 6.5, 1.2, 7, 9, "minecraft:spruce_planks", hollow=True); b.set(x, 7, z0 + 6, "minecraft:honey_block")
    for x in range(x0 + 3, x0 + L - 2, 6): b.cyl(x, z0 + W - 3.5, 2, 1, 5, "minecraft:spruce_planks", hollow=True)  # mead barrels
    b.box(x0 + L - 10, 1, z0 + W - 10, x0 + L - 2, 3, z0 + W - 2, "minecraft:brown_wool")  # a giant's bed of furs
    for x in range(x0 + 2, x0 + L - 1, 4): b.set(x, H - 1, cz, "minecraft:lantern[hanging=true,waterlogged=false]")
    # a human-sized loft for the little people visiting the giants
    I.furnish(b, x0 + 1, 1, z0 + 1, x0 + 8, z0 + 5, 4, "bedroom", GIANT, seed=seed)


def build():
    rnd = random.Random(641)
    b = B()
    T.ground(b, N, N, rnd, top="minecraft:snow_block", deco=0.3, decos=("minecraft:snow[layers=1]", "minecraft:snow[layers=2]", "minecraft:short_grass"))
    for x in range(N):
        for z in range(N):
            if (x * 3 + z) % 7 == 0: b.set(x, 0, z, "minecraft:podzol[snowy=true]")
    # pines round the valley
    for i in range(55):
        x, z = rnd.randint(2, N - 3), rnd.randint(2, N - 3)
        if math.hypot(x - TX, z - TZ) < TR + 18 or (6 <= x <= 60 and 54 <= z <= 104): continue
        h = rnd.randint(10, 16)
        for y in range(1, h): b.set(x, y, z, "minecraft:spruce_log[axis=y]")
        for k in range(h - 7, h + 1): b.cyl(x, z, max(0.6, (h - k) * 0.5 + 0.5), k, k, "minecraft:spruce_leaves[distance=7,persistent=true,waterlogged=false]")
        b.set(x, h + 1, z, "minecraft:snow_block")
    # ---------------- the great tree
    for y in range(-3, 100):
        r = TR * (1.6 - 0.6 * min(1, y / 12)) * (1 - 0.15 * y / 100)
        b.cyl(TX, TZ, r, y, y, ADAM)
    for k in range(8):  # roots like hills
        a = k * math.pi / 4 + 0.2
        for t in range(0, 26):
            rx, rz = TX + (TR + t) * math.cos(a), TZ + (TR + t) * math.sin(a)
            rr = max(1.2, 5 - t * 0.17)
            b.cyl(rx, rz, rr, 0, max(0, int(9 - t * 0.35)), ADAM)
    b.cyl(TX, TZ, TR - 3, 1, 70, AIR)  # the hollow
    for y in range(1, 70):  # the stair inside
        a = y / 4.0
        for w in (TR - 5, TR - 4):
            b.set(round(TX + w * math.cos(a)), y, round(TZ + w * math.sin(a)), ADAMW)
    for y in range(4, 70, 6):
        a = y / 4.0
        b.set(round(TX + (TR - 6) * math.cos(a)), y + 2, round(TZ + (TR - 6) * math.sin(a)), "minecraft:lantern[hanging=false,waterlogged=false]") if False else None
        b.set(round(TX + (TR - 3) * math.cos(a)), y + 2, round(TZ + (TR - 3) * math.sin(a)), lantern(True))
    for y in (1, 2, 3, 4, 5):
        for dz in range(-2, 3): b.set(TX - round(TR * 1.4) + 0, y, TZ + dz, AIR)
    for x in range(TX - round(TR * 1.6) - 2, TX - TR + 4):
        for y in range(1, 6):
            for dz in range(-2, 3): b.set(x, y, TZ + dz, AIR)
    # the first great bough with a lookout platform, then the crown
    for t in range(0, 30):
        bx, by = TX + 8 + t, 70 + t * 0.5
        b.cyl(bx, TZ, 3.2 - t * 0.05, round(by) - 2, round(by) + 1, ADAM)
    b.cyl(TX + 34, TZ, 7, 86, 86, ADAMW); b.cyl(TX + 34, TZ, 7.4, 87, 87, "minecraft:spruce_fence", hollow=True)
    b.cyl(TX, TZ, TR - 3, 70, 70, ADAMW)
    for y in range(70, 88): b.set(TX + TR - 4, y, TZ, "minecraft:ladder[facing=west,waterlogged=false]")
    for (cx, cy, cz, r) in ((TX, 108, TZ, 26), (TX - 18, 98, TZ + 6, 16), (TX + 22, 100, TZ - 6, 17), (TX + 2, 96, TZ - 20, 15)):
        b.sphere(cx, cy, cz, r, "minecraft:spruce_leaves[distance=7,persistent=true,waterlogged=false]", ry=r * 0.45)
    for k in range(6):
        a = k * 1.05
        b.line((TX, 96, TZ), (TX + 22 * math.cos(a), 104, TZ + 22 * math.sin(a)), ADAM)
    # ---------------- the giants' village (south-west)
    longhouse(b, 8, 58, 44, 18, 16, rnd, 1)
    longhouse(b, 12, 84, 36, 16, 14, rnd, 2)
    # the training ring with giant weapons
    RX, RZ = 30, 34
    b.cyl(RX, RZ, 14, 0, 0, "minecraft:coarse_dirt"); b.cyl(RX, RZ, 14.5, 1, 2, "minecraft:spruce_log[axis=y]", hollow=True)
    for (wx, wz) in ((RX - 10, RZ - 8), (RX + 10, RZ - 8)):  # giant axe and sword stuck in the ground
        b.column(wx, wz, 1, 22, "minecraft:stripped_spruce_log[axis=y]")
    for y in range(15, 23):
        for k in range(1, 8 - abs(y - 19)): b.set(RX - 10 + k, y, RZ - 8, "minecraft:iron_block")
    for y in range(1, 24): b.set(RX + 10, y, RZ - 8, "minecraft:iron_block"); b.set(RX + 10, y, RZ - 7, "minecraft:iron_block") if y < 20 else None
    for z in range(RZ - 12, RZ - 3): b.set(RX + 10, 24, z, "minecraft:gold_block")
    # rune stones
    for k, (x, z) in enumerate(((6, 8), (14, 6), (22, 10), (10, 18))):
        b.box(x, 1, z, x + 1, 5 + k % 3, z, "minecraft:stone")
        b.set(x, 3, z - 1, "minecraft:chiseled_stone_bricks"); b.set(x + 1, 4, z - 1, "minecraft:chiseled_stone_bricks")
    T.path(b, [(30, 57), (RX, RZ + 15)], w=2, s="minecraft:packed_mud")
    T.path(b, [(52, 67), (TX - round(TR * 1.6) - 2, TZ)], w=2, s="minecraft:packed_mud")
    # ---------------- loot and wolves' hunters
    b.chest(10, 1, 60, "medium", "east"); b.chest(TX + 34, 87, TZ + 3, "treasure", "west"); b.chest(TX, 71, TZ + 4, "medium", "south")
    b.guards("bounty_hunter", ((RX, RZ), (60, 90)))
    return b, 0
