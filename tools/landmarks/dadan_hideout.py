"""Dadan's Hideout on Mt. Colubo: the mountain bandits' big log lodge in a dense forest, with its dining hall, bunk
rooms and Dadan's room, a smokehouse and woodpile, a lookout platform, and up the slope the treehouse that Ace,
Sabo and Luffy built in a giant tree, with the three sake cups on the stump where they swore brotherhood.
~80 x 80. Ground = y 0, the mountain rises to the north."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "dadan_hideout"
TITLE = "Dadan's Hideout (Mt. Colubo)"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 80
LOG = "minecraft:spruce_log[axis=y]"
LOGX = "minecraft:spruce_log[axis=x]"
LOGZ = "minecraft:spruce_log[axis=z]"
BANDIT = dict(wood="spruce", rug="brown", rug2="red", bed="brown", light="minecraft:lantern", accent="minecraft:spruce_log[axis=y]",
              banner="brown", candle="orange")


def hgt(x, z):
    return max(0, int((40 - z) / 6)) if z < 40 else 0


def build():
    rnd = random.Random(211)
    b = B()
    # ---------------- forested slope
    for x in range(N):
        for z in range(N):
            h = hgt(x, z)
            for y in range(-3, h + 1): b.set(x, y, z, "minecraft:dirt" if y < h else ("minecraft:podzol" if (x * 3 + z) % 5 == 0 else "minecraft:grass_block"))
    for i in range(110):
        x, z = rnd.randint(1, N - 2), rnd.randint(1, N - 2)
        if 18 <= x <= 62 and 30 <= z <= 64: continue
        if 50 <= x <= 72 and 4 <= z <= 26: continue
        h = hgt(x, z)
        if b.get(x, h + 1, z) is not None: continue
        kind = rnd.choice(("spruce", "spruce", "oak", "dark_oak"))
        th = rnd.randint(6, 11)
        for y in range(h + 1, h + th): b.set(x, y, z, f"minecraft:{kind}_log[axis=y]")
        b.sphere(x, h + th, z, rnd.uniform(2.2, 3.2), f"minecraft:{kind}_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.4 if kind != "spruce" else 3.2)
    for i in range(200):
        x, z = rnd.randint(0, N - 1), rnd.randint(0, N - 1); h = hgt(x, z)
        if b.get(x, h + 1, z) is None: b.set(x, h + 1, z, rnd.choice(("minecraft:fern", "minecraft:short_grass", "minecraft:sweet_berry_bush[age=3]", "minecraft:brown_mushroom")))
    # clearing around the lodge
    for x in range(18, 63):
        for z in range(30, 65):
            if b.get(x, 1, z) and ("fern" in b.get(x, 1, z) or "grass" in b.get(x, 1, z) or "berry" in b.get(x, 1, z) or "mushroom" in b.get(x, 1, z)): b.set(x, 1, z, AIR)
            b.set(x, 0, z, "minecraft:coarse_dirt" if (x + z) % 4 == 0 else "minecraft:grass_block")
    # ---------------- the log lodge: two storeys of stacked logs
    X0, X1, Z0, Z1 = 24, 50, 36, 52
    b.box(X0, 0, Z0, X1, 0, Z1, "minecraft:spruce_planks")
    for y in range(1, 11):
        for x in range(X0, X1 + 1):
            for z in (Z0, Z1): b.set(x, y, z, LOGX)
        for z in range(Z0, Z1 + 1):
            for x in (X0, X1): b.set(x, y, z, LOGZ)
    for (x, z) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        for y in range(1, 12): b.set(x, y, z, LOG)
    b.box(X0 + 1, 1, Z0 + 1, X1 - 1, 10, Z1 - 1, AIR)
    b.box(X0 + 1, 5, Z0 + 1, X1 - 1, 5, Z1 - 1, "minecraft:spruce_planks")
    for fy in (2, 7):
        for x in range(X0 + 3, X1 - 2, 4):
            for z in (Z0, Z1): b.set(x, fy, z, "minecraft:glass_pane"); b.set(x + 1, fy, z, "minecraft:glass_pane")
        for z in range(Z0 + 3, Z1 - 2, 4):
            for x in (X0, X1): b.set(x, fy, z, "minecraft:glass_pane")
    b.gable_roof(X0 - 1, Z0, X1 + 1, Z1, 11, "minecraft:spruce_stairs", "minecraft:spruce_planks", gable_wall=LOGX)
    # porch with a roof on the south
    for x in range(X0 + 6, X1 - 5):
        for z in range(Z1 + 1, Z1 + 5): b.set(x, 0, z, "minecraft:spruce_planks")
        b.set(x, 5, Z1 + 4, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        for z in range(Z1 + 1, Z1 + 4): b.set(x, 5, z, "minecraft:spruce_planks")
    for x in (X0 + 6, X1 - 6): b.column(x, Z1 + 4, 1, 4, LOG)
    for x in (37, 38):
        b.set(x, 1, Z1, f"minecraft:spruce_door[facing=south,half=lower,hinge={'left' if x == 37 else 'right'},open=false,powered=false]")
        b.set(x, 2, Z1, f"minecraft:spruce_door[facing=south,half=upper,hinge={'left' if x == 37 else 'right'},open=false,powered=false]")
    # inside: dining hall (east) and kitchen (west), upstairs bunks + Dadan's room
    for z in range(Z0 + 1, Z1):
        for y in range(1, 5): b.set(32, y, z, LOGZ)
    for y in (1, 2): b.set(32, y, 44, AIR)
    I.furnish(b, 33, 1, Z0 + 1, X1 - 1, Z1 - 1, 3, "dining", BANDIT)
    I.furnish(b, X0 + 1, 1, Z0 + 1, 31, Z1 - 1, 3, "kitchen", BANDIT)
    for k in range(1, 5): b.set(X1 - 1, k, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    b.set(X1 - 1, 5, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for z in range(Z0 + 1, Z1):
        for y in range(6, 10): b.set(40, y, z, "minecraft:spruce_planks")
    for y in (6, 7): b.set(40, y, 44, AIR)
    I.furnish(b, X0 + 1, 6, Z0 + 1, 39, Z1 - 1, 4, "barracks", BANDIT)
    I.furnish(b, 41, 6, Z0 + 1, X1 - 1, Z1 - 1, 4, "bedroom", BANDIT)
    # smokehouse, woodpile, the outhouse and the yard
    T.house(b, 52, 40, 7, 7, 1, "shack", rnd, kinds=["storage"])
    for x in range(20, 24):
        for y in (1, 2): b.set(x, y, 56, LOGZ); b.set(x, y, 57, LOGZ)
    b.set(22, 3, 56, LOGZ)
    b.set(36, 1, 58, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((34, 58), (38, 58), (36, 60)): b.set(x, 1, z, LOGX)
    b.set(30, 1, 58, "minecraft:brown_carpet"); b.set(31, 1, 58, "minecraft:brown_carpet")  # bear pelt
    # lookout platform on stilts
    for (dx, dz) in ((0, 0), (3, 0), (0, 3), (3, 3)): b.column(56 + dx, 56 + dz, 1, 9, LOG)
    b.box(55, 10, 55, 60, 10, 60, "minecraft:spruce_planks")
    for x in range(55, 61):
        for z in (55, 60): b.set(x, 11, z, fence("spruce"))
    for z in range(55, 61):
        for x in (55, 60): b.set(x, 11, z, fence("spruce"))
    for k in range(1, 11): b.set(57, k, 55, "minecraft:ladder[facing=north,waterlogged=false]")
    b.set(57, 11, 55, AIR)
    # ---------------- the brothers' treehouse up the slope
    TX, TZ = 61, 14
    th = hgt(TX, TZ)
    b.cyl(TX, TZ, 2.2, th, th + 20, "minecraft:oak_wood[axis=y]")
    for k in range(5):
        a = k * 72
        for s in range(9):
            t = math.radians(a)
            b.set(round(TX + (2 + s) * math.cos(t)), th + 14 + s // 3, round(TZ + (2 + s) * math.sin(t)), "minecraft:oak_log[axis=x]" if abs(math.cos(t)) > 0.7 else "minecraft:oak_log[axis=z]")
    b.sphere(TX, th + 22, TZ, 8, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", ry=5)
    py = th + 12
    b.box(TX - 5, py, TZ - 4, TX + 5, py, TZ + 4, "minecraft:spruce_planks")
    b.walls(TX - 4, py + 1, TZ - 3, TX + 4, py + 4, TZ + 3, "minecraft:oak_planks")
    b.box(TX - 3, py + 1, TZ - 2, TX + 3, py + 4, TZ + 2, AIR)
    for x in range(TX - 3, TX + 4):
        for z in range(TZ - 2, TZ + 3):
            if math.hypot(x - TX, z - TZ) <= 2.3: b.set(x, py + 1, z, "minecraft:oak_wood[axis=y]") if False else None
    b.gable_roof(TX - 4, TZ - 3, TX + 4, TZ + 3, py + 5, "minecraft:oak_stairs", "minecraft:oak_planks", gable_wall="minecraft:oak_planks")
    b.set(TX, py + 2, TZ + 3, AIR); b.set(TX, py + 1, TZ + 3, AIR); b.set(TX + 2, py + 2, TZ - 3, "minecraft:glass_pane")
    I.furnish(b, TX - 3, py + 1, TZ - 2, TX + 3, TZ + 2, 3, "bedroom", "pirate", seed=3)
    for k in range(th + 1, py + 1): b.set(TX, k, TZ + 3, "minecraft:ladder[facing=south,waterlogged=false]")
    b.jolly_roger(TX + 5, py + 8, TZ, 5, 3, axis="z")
    for y in range(py + 1, py + 9): b.set(TX + 5, y, TZ - 1, "minecraft:spruce_fence")
    # the oath stump with three sake cups
    sx, sz = 54, 22
    sh = hgt(sx, sz)
    b.cyl(sx, sz, 1.5, sh + 1, sh + 1, "minecraft:stripped_oak_wood[axis=y]")
    for (dx, dz) in ((-1, 0), (1, 0), (0, 1)): b.set(sx + dx, sh + 2, sz + dz, "minecraft:flower_pot")
    # ---------------- people and loot
    b.chest(X1 - 2, 6, Z0 + 2, "easy", "west"); b.chest(TX + 2, py + 1, TZ - 2, "easy", "south")
    b.guards("bandit", ((40, 60), (28, 58), (46, 56)))
    return b, 0
