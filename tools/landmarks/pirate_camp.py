"""A rookie pirate crew's beach camp: their battered caravel run up on the sand, sailcloth tents in the crew's
colours with bedrolls and sea chests, a captain's tent with a map table and the stolen treasure, a cook tent with
a stew pot, a bonfire ring with log benches and a grog barrel, a lookout tree with a crow's nest, a wanted poster
board, a target range and stacks of crates and powder. ~72 x 64. Ground = y 0, the sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "pirate_camp"
TITLE = "Pirate Camp"
CUTS = [2, 5]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 72, 64
SEA_Z = 46
CAMP = dict(wood="spruce", rug="red", rug2="black", bed="red", light="minecraft:lantern", accent="minecraft:barrel[facing=up,open=false]",
            banner="black", candle="red")


def tent(b, x0, z0, w, d, h, wool, rnd, kind, seed, door="south"):
    """An A-frame sailcloth tent along x with a pole ridge, a rug floor and furniture inside."""
    for x in range(x0, x0 + w):
        for k in range(h):
            for zz in (z0 + k, z0 + d - 1 - k):
                b.set(x, 1 + k, zz, wool if (x + k) % 5 else "minecraft:white_wool")
        b.set(x, h + 1, z0 + d // 2, "minecraft:stripped_spruce_log[axis=x]")
    for z in range(z0, z0 + d):
        b.set(x0, 1, z, wool) if door != "west" else None
    b.box(x0 + 1, 0, z0 + 1, x0 + w - 2, 0, z0 + d - 2, "minecraft:spruce_planks")
    for k in range(h):
        for zz in range(z0 + k + 1, z0 + d - 1 - k):
            b.set(x0 + w - 1, 1 + k, zz, wool); b.set(x0, 1 + k, zz, wool)
    cz = z0 + d // 2
    b.set(x0, 1, cz, AIR); b.set(x0, 2, cz, AIR)
    I.furnish(b, x0 + 1, 1, z0 + 2, x0 + w - 2, z0 + d - 3, max(2, h - 2), kind, CAMP, seed=seed)


def build():
    rnd = random.Random(671)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.1, decos=("minecraft:short_grass", "minecraft:fern", "minecraft:short_grass"))
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z + 2 * math.sin(x * 0.2), depth=5)
    for x in range(NX):
        for z in range(NZ):
            s = SEA_Z + 2 * math.sin(x * 0.2)
            if s - 10 < z <= s: b.set(x, 0, z, "minecraft:sand"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # palms along the back
    for x in range(4, NX - 4, 9):
        z = 4 + (x * 7) % 5
        h = rnd.randint(8, 11)
        for y in range(1, h): b.set(x + (y > h // 2), y, z, "minecraft:jungle_log[axis=y]")
        b.sphere(x + 1, h, z, 3.2, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=1.2)
    # ---------------- the caravel run up on the sand
    hw = b.hull(6, 30, SEA_Z + 4, 9, -4, 3, "minecraft:spruce_planks", bottom="minecraft:dark_oak_planks", rail="minecraft:spruce_fence",
                bow_len=10, stern_len=4, fill_deck="minecraft:spruce_planks", waterline=-1)
    b.cyl(20, SEA_Z + 4, 0.6, 3, 22, "minecraft:spruce_log[axis=y]")
    b.square_sail(21, SEA_Z + 4, 9, 19, 5, "minecraft:white_wool", belly=1)
    for y in range(22, 26): b.set(20, y, SEA_Z + 4, "minecraft:spruce_fence")
    b.jolly_roger(20, 25, SEA_Z + 5, 5, 4)
    I.furnish(b, 9, 0, SEA_Z + 2, 22, SEA_Z + 6, 2, "storage", CAMP, seed=9)
    # ---------------- the tents round the fire
    tent(b, 8, 12, 9, 9, 4, "minecraft:red_wool", rnd, "barracks", 1)
    tent(b, 20, 10, 9, 9, 4, "minecraft:black_wool", rnd, "barracks", 2)
    tent(b, 46, 10, 13, 11, 5, "minecraft:red_wool", rnd, "study", 3)       # the captain's tent
    tent(b, 52, 26, 9, 9, 4, "minecraft:white_wool", rnd, "kitchen", 4)     # the cook's tent
    FX, FZ = 34, 28
    b.cyl(FX, FZ, 2, 0, 0, "minecraft:cobblestone"); b.set(FX, 1, FZ, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for a in range(0, 360, 60):
        t = math.radians(a)
        x, z = round(FX + 5 * math.cos(t)), round(FZ + 5 * math.sin(t))
        b.set(x, 1, z, "minecraft:stripped_spruce_log[axis=x]" if abs(math.cos(t)) < 0.5 else "minecraft:stripped_spruce_log[axis=z]")
    b.set(FX + 3, 1, FZ - 3, "minecraft:barrel[facing=up,open=true]"); b.set(FX - 3, 1, FZ + 3, "onepiece:sake_barrel")
    b.set(FX + 1, 1, FZ + 2, "minecraft:cauldron")
    # the lookout tree with a crow's nest
    LX, LZ = 64, 40
    for y in range(1, 18): b.set(LX, y, LZ, "minecraft:jungle_log[axis=y]")
    b.cyl(LX, LZ, 2, 15, 15, "minecraft:spruce_planks"); b.cyl(LX, LZ, 2.4, 16, 16, "minecraft:spruce_fence", hollow=True)
    for y in range(1, 15): b.set(LX - 1, y, LZ, "minecraft:ladder[facing=west,waterlogged=false]")
    b.sphere(LX, 20, LZ, 4, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=1.6)
    # wanted board, target range, supplies
    b.box(36, 1, 12, 40, 1, 12, "minecraft:spruce_fence"); b.box(36, 2, 12, 40, 4, 12, "minecraft:spruce_planks")
    for x in (37, 39): b.set(x, 3, 13, "minecraft:paper" if False else "minecraft:white_carpet") if False else b.set(x, 3, 13, "minecraft:spruce_wall_sign[facing=south,waterlogged=false]")
    for z in range(16, 26, 4): b.set(4, 1, z, "minecraft:target"); b.set(4, 2, z, "minecraft:hay_block[axis=y]")
    for (x, z) in ((40, 36), (42, 36), (41, 37), (44, 22)):
        b.set(x, 1, z, rnd.choice(("minecraft:barrel[facing=up,open=false]", "onepiece:mikan_crate", "onepiece:cola_crate")))
    b.set(42, 2, 36, "minecraft:barrel[facing=up,open=false]"); b.set(45, 1, 22, "minecraft:tnt[unstable=false]"); b.set(45, 1, 23, "minecraft:tnt[unstable=false]")
    T.path(b, [(FX, FZ), (FX, SEA_Z - 6)], w=1, s="minecraft:coarse_dirt")
    # ---------------- loot and crew
    b.chest(56, 1, 14, "pirate", "west"); b.chest(10, 1, 16, "easy", "east"); b.chest(14, 1, SEA_Z + 3, "pirate", "south")
    b.guards("rookie_pirate", ((FX + 4, FZ), (FX - 4, FZ), (30, 18), (50, 34), (18, SEA_Z + 4)))
    return b, 0
