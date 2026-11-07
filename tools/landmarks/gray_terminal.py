"""The Gray Terminal outside Goa Kingdom: a vast smoking junk heap where the kingdom dumps its trash and the poor
live among it. Hills of scrap, broken furniture and rotting wood, shanty huts patched from boards and sheet
metal, the bandit Dadan's mountain hideout lodge at the edge of the forest (with the boys' bunk room), the
treehouse Ace, Sabo and Luffy built, the bridge gate to Goa's wall and smouldering fires. ~96 x 88. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "gray_terminal"
TITLE = "Gray Terminal"
CUTS = [2, 6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 96, 88
JUNK = ("minecraft:coarse_dirt", "minecraft:gravel", "minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:mud", "minecraft:packed_mud",
        "minecraft:rooted_dirt", "minecraft:barrel[facing=up,open=false]", "minecraft:exposed_copper", "minecraft:iron_block", "minecraft:dark_oak_planks",
        "minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:composter[level=4]", "minecraft:hay_block[axis=y]", "minecraft:brown_wool")
BANDIT = dict(wood="spruce", rug="brown", rug2="green", bed="brown", light="minecraft:lantern", accent="minecraft:barrel[facing=up,open=false]",
              banner="brown", candle="brown")


def shanty(b, x0, z0, w, d, rnd, seed):
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            b.set(x, 0, z, "minecraft:coarse_dirt")
            edge = x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1)
            for y in range(1, 4):
                b.set(x, y, z, rnd.choice(("minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:exposed_cut_copper", "minecraft:stripped_spruce_log[axis=y]", "minecraft:mossy_cobblestone")) if edge else AIR)
            b.set(x, 4, z, rnd.choice(("minecraft:spruce_slab[type=bottom,waterlogged=false]", "minecraft:weathered_cut_copper_slab[type=bottom,waterlogged=false]", "minecraft:oak_slab[type=bottom,waterlogged=false]")))
    b.set(x0 + w // 2, 1, z0 + d - 1, AIR); b.set(x0 + w // 2, 2, z0 + d - 1, AIR)
    I.furnish(b, x0 + 1, 1, z0 + 1, x0 + w - 2, z0 + d - 2, 3, rnd.choice(("bedroom", "storage", "kitchen")), BANDIT, seed=seed)


def build():
    rnd = random.Random(701)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:coarse_dirt", deco=0.0)
    for x in range(NX):
        for z in range(NZ):
            if z < 20: b.set(x, 0, z, "minecraft:grass_block"); b.set(x, 1, z, "minecraft:short_grass") if rnd.random() < 0.2 else None
    # the forest behind (north)
    for i in range(30):
        x, z = rnd.randint(2, NX - 3), rnd.randint(2, 16)
        if 6 < x < 34: continue
        h = rnd.randint(7, 11); b.cyl(x, z, 0.6, 1, h, "minecraft:oak_log[axis=y]"); b.sphere(x, h + 1, z, 3, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.2)
    # ---------------- the junk hills
    for (x, z, r, h) in ((48, 46, 13, 11), (24, 60, 10, 8), (74, 62, 11, 9), (70, 34, 8, 6), (36, 76, 7, 5), (86, 80, 6, 5), (12, 40, 6, 4)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                d = math.hypot(dx, dz) / r
                if d > 1: continue
                top = int(h * (1 - d ** 1.6)) + rnd.randint(0, 1)
                for y in range(1, top + 1): b.set(x + dx, y, z + dz, rnd.choice(JUNK))
                if top and rnd.random() < 0.06: b.set(x + dx, top + 1, z + dz, rnd.choice(("minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]", "minecraft:oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]", "minecraft:anvil[facing=north]", "minecraft:cauldron", "minecraft:oak_fence")))
    # ---------------- the shanty huts
    for i, (x, z) in enumerate(((6, 26), (16, 24), (30, 28), (60, 22), (82, 24), (84, 44), (6, 74), (54, 70), (62, 80), (18, 80))):
        shanty(b, x, z, rnd.randint(6, 8), rnd.randint(5, 7), rnd, i)
    # ---------------- Dadan's lodge at the forest edge
    LX0, LZ0 = 8, 4
    b.box(LX0, 0, LZ0, LX0 + 22, 0, LZ0 + 14, "minecraft:spruce_planks")
    b.walls(LX0, 1, LZ0, LX0 + 22, 5, LZ0 + 14, "minecraft:spruce_log[axis=y]")
    b.box(LX0 + 1, 1, LZ0 + 1, LX0 + 21, 5, LZ0 + 13, AIR)
    for x in range(LX0, LX0 + 23, 3): b.set(x, 3, LZ0 + 14, "minecraft:glass_pane"); b.set(x, 3, LZ0, "minecraft:glass_pane")
    b.gable_roof(LX0, LZ0, LX0 + 22, LZ0 + 14, 6, "minecraft:spruce_stairs", "minecraft:spruce_planks", gable_wall="minecraft:stripped_spruce_log[axis=y]")
    b.set(LX0 + 11, 1, LZ0 + 14, AIR); b.set(LX0 + 11, 2, LZ0 + 14, AIR)
    for z in range(LZ0 + 1, LZ0 + 14):
        for y in range(1, 6): b.set(LX0 + 12, y, z, "minecraft:spruce_planks")
    b.set(LX0 + 12, 1, LZ0 + 8, AIR); b.set(LX0 + 12, 2, LZ0 + 8, AIR)
    I.furnish(b, LX0 + 1, 1, LZ0 + 1, LX0 + 11, LZ0 + 13, 4, "tavern", BANDIT, seed=1)
    I.furnish(b, LX0 + 13, 1, LZ0 + 1, LX0 + 21, LZ0 + 13, 4, "barracks", BANDIT, seed=2)
    # the brothers' treehouse
    TX, TZ = 40, 8
    b.cyl(TX, TZ, 1.2, 1, 18, "minecraft:oak_log[axis=y]")
    b.box(TX - 4, 12, TZ - 3, TX + 4, 12, TZ + 3, "minecraft:spruce_planks")
    b.walls(TX - 4, 13, TZ - 3, TX + 4, 15, TZ + 3, "minecraft:oak_planks"); b.box(TX - 3, 13, TZ - 2, TX + 3, 15, TZ + 2, AIR)
    b.cyl(TX, TZ, 1.2, 13, 15, "minecraft:oak_log[axis=y]")
    b.box(TX - 5, 16, TZ - 4, TX + 5, 16, TZ + 4, "minecraft:oak_slab[type=bottom,waterlogged=false]")
    b.set(TX + 4, 14, TZ, AIR); b.set(TX + 3, 13, TZ - 2, "minecraft:brown_bed[facing=east,occupied=false,part=head]"); b.set(TX + 2, 13, TZ - 2, "minecraft:brown_bed[facing=east,occupied=false,part=foot]")
    b.set(TX - 3, 13, TZ + 2, "minecraft:barrel[facing=up,open=false]"); b.set(TX - 2, 13, TZ - 2, "minecraft:crafting_table")
    b.sphere(TX, 20, TZ, 6, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", ry=3)
    for y in range(1, 12): b.set(TX + 2, y, TZ, "minecraft:ladder[facing=east,waterlogged=false]")
    b.set(TX + 2, 12, TZ, AIR)
    b.box(TX + 5, 17, TZ - 1, TX + 5, 20, TZ - 1, "minecraft:oak_fence"); b.box(TX + 5, 18, TZ, TX + 5, 20, TZ + 3, "minecraft:black_wool")  # their pirate flag
    # Goa's wall and gate at the south edge
    for x in range(NX):
        for y in range(1, 14): b.set(x, y, NZ - 2, "minecraft:stone_bricks" if y < 13 else ("minecraft:stone_brick_wall" if x % 2 else AIR))
    for x in range(44, 52):
        for y in range(1, 8): b.set(x, y, NZ - 2, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    # ---------------- loot and bandits
    b.chest(LX0 + 2, 1, LZ0 + 12, "easy", "east"); b.chest(TX - 3, 13, TZ - 2, "easy", "east"); b.chest(48, 12, 46, "easy", "south")
    b.guards("bandit", ((LX0 + 11, LZ0 + 17), (30, 40), (66, 50), (20, 70)))
    return b, 0
