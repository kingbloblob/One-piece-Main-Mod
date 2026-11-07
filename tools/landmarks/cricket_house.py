"""Montblanc Cricket's house on Jaya: the famous castle front, a grand stone facade with towers, gate and banners
that is literally sliced in half, with the little wooden house hiding behind it. Around it: Cricket's diving
gear and boat on the pier, the Saruyama Alliance camp of Masira and Shoujou, the South Bird jungle, and Noland's
gold hidden in the cellar. Inside: the kitchen where they feasted, Cricket's study full of maps and logs of
Noland, a bedroom and the diving workshop. ~88 x 72. Ground = y 0, sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "cricket_house"
TITLE = "Montblanc Cricket's House"
CUTS = [2]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 88, 72
SEA_Z = 56
FZ = 22            # facade plane
FX0, FX1 = 14, 50  # facade from the left tower to the cut
STONE = "minecraft:stone_bricks"
WHITE = "minecraft:smooth_quartz"
CABIN = dict(wood="spruce", rug="blue", rug2="white", bed="blue", light="minecraft:lantern", accent="minecraft:gold_block",
             banner="blue", candle="white")


def tower(b, x, z, r, h, rnd):
    b.cyl(x, z, r, 1, h, WHITE, hollow=True)
    b.cyl(x, z, r - 1, 1, h - 1, AIR)
    for y in range(4, h - 2, 5):
        for a in (0, 90, 180, 270):
            t = math.radians(a)
            b.set(round(x + r * math.cos(t)), y, round(z + r * math.sin(t)), "minecraft:glass_pane")
            b.set(round(x + r * math.cos(t)), y + 1, round(z + r * math.sin(t)), "minecraft:glass_pane")
    b.cyl(x, z, r + 0.6, h, h, STONE)
    for a in range(0, 360, 30):  # crenellations
        t = math.radians(a)
        b.set(round(x + (r + 0.4) * math.cos(t)), h + 1, round(z + (r + 0.4) * math.sin(t)), "minecraft:stone_brick_wall")
    for k in range(7):  # pointed blue cap
        b.cyl(x, z, max(0.5, r - k * 0.7), h + 2 + k, h + 2 + k, "minecraft:blue_terracotta")
    b.set(x, h + 9, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")


def build():
    rnd = random.Random(401)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:grass_block", deco=0.08)
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z + 2 * math.sin(x * 0.15), depth=6)
    for x in range(NX):
        for z in range(SEA_Z - 6, SEA_Z + 3):
            if b.get(x, 0, z) == "minecraft:grass_block": b.set(x, 0, z, "minecraft:sand")
            if b.get(x, 1, z) not in (None, AIR) and "grass" in (b.get(x, 1, z) or "") or b.get(x, 1, z) in ("minecraft:dandelion", "minecraft:poppy"): b.set(x, 1, z, AIR)
    # ---------------- the South Bird jungle behind (north)
    for i in range(46):
        x, z = rnd.randint(2, NX - 3), rnd.randint(2, 16)
        if i % 3 == 0: x, z = rnd.choice((rnd.randint(2, 10), rnd.randint(NX - 12, NX - 3))), rnd.randint(16, 44)
        if 8 <= x <= 56 and z > 6: continue  # keep the castle front in view
        h = rnd.randint(9, 15)
        for y in range(1, h): b.set(x, y, z, "minecraft:jungle_log[axis=y]")
        b.sphere(x, h, z, rnd.uniform(3, 4.5), "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.4)
        if rnd.random() < 0.5:
            for y in range(h - 2, h - 7, -1): b.fill_if(x + 1, y, z, "minecraft:vine[east=false,north=false,south=false,up=false,west=true]")
    # ---------------- the half castle facade
    H = 26
    for x in range(FX0, FX1 + 1):
        cut = FX1 - 2 + (x * 7 % 3)
        if x > cut: continue
        top = H if x < FX1 - 4 else H - (x - (FX1 - 4)) * 3  # the cut edge drops away
        for y in range(1, top + 1):
            for z in (FZ, FZ + 1):
                b.set(x, y, z, WHITE if (y // 3 + x // 4) % 5 else "minecraft:white_glazed_terracotta" if False else WHITE)
        if x % 2 == 0 and top == H: b.set(x, H + 1, FZ, STONE)
        b.set(x, 1, FZ, STONE); b.set(x, 2, FZ, STONE)
    for y in (9, 18):  # cornice bands
        for x in range(FX0, FX1 - 4): b.set(x, y, FZ - 1, "minecraft:stone_brick_slab[type=top,waterlogged=false]")
    for x in range(FX0 + 4, FX1 - 4, 5):  # arched windows on two floors
        for y0 in (5, 13):
            for y in range(y0, y0 + 3): b.set(x, y, FZ, "minecraft:blue_stained_glass_pane"); b.set(x + 1, y, FZ, "minecraft:blue_stained_glass_pane")
            b.set(x, y0 + 3, FZ, "minecraft:stone_brick_stairs[facing=east,half=top,shape=straight,waterlogged=false]")
            b.set(x + 1, y0 + 3, FZ, "minecraft:stone_brick_stairs[facing=west,half=top,shape=straight,waterlogged=false]")
            b.set(x, y0 - 1, FZ - 1, "minecraft:spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
            b.set(x + 1, y0 - 1, FZ - 1, "minecraft:spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    GX = 30
    for x in range(GX - 3, GX + 4):  # great gate
        for y in range(1, 8 - (abs(x - GX) == 3)):
            for z in (FZ, FZ + 1): b.set(x, y, z, AIR)
    for x in range(GX - 2, GX + 3): b.set(x, 1, FZ, "minecraft:dark_oak_fence_gate[facing=north,in_wall=false,open=true,powered=false]") if False else None
    for y in range(1, 8): b.set(GX - 4, y, FZ - 1, "minecraft:stone_brick_wall"); b.set(GX + 4, y, FZ - 1, "minecraft:stone_brick_wall")
    for y in range(20, 25):  # banners and the crest
        for x in (GX - 6, GX + 6): b.set(x, y, FZ - 1, "minecraft:blue_wool")
    b.box(GX - 2, 20, FZ - 1, GX + 2, 24, FZ - 1, "minecraft:yellow_wool"); b.set(GX, 22, FZ - 1, "minecraft:gold_block")
    tower(b, FX0, FZ + 1, 4, H + 6, rnd)
    tower(b, GX - 9, FZ + 1, 3, H + 2, rnd)
    # ---------------- the little house hiding behind
    HX0, HZ0, HW, HD = 22, FZ + 3, 18, 13
    top = T.house(b, HX0, HZ0, HW, HD, 2, "cottage", rnd, kinds=["dining", "study"], theme=CABIN, door="west", chimney=True)
    # lean-to diving workshop
    b.walls(HX0, 0, HZ0 + HD, HX0 + 9, 4, HZ0 + HD + 7, "minecraft:spruce_planks")
    b.box(HX0 + 1, 1, HZ0 + HD + 1, HX0 + 8, 4, HZ0 + HD + 6, AIR)
    I.furnish(b, HX0 + 1, 1, HZ0 + HD + 1, HX0 + 8, HZ0 + HD + 6, 4, "workshop", CABIN, seed=41)
    b.box(HX0, 5, HZ0 + HD, HX0 + 9, 5, HZ0 + HD + 7, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for y in (1, 2): b.set(HX0 + 4, y, HZ0 + HD + 7, AIR)
    for x in range(HX0 + 2, HX0 + 8, 2):  # diving helmets and suits hung outside
        b.set(x, 1, HZ0 + HD + 8, "minecraft:armor_stand") if False else b.set(x, 3, HZ0 + HD + 8, "minecraft:copper_bulb[lit=false,powered=false]")
    # Noland's gold in the cellar under the house
    b.box(HX0 + 3, -5, HZ0 + 3, HX0 + 12, -1, HZ0 + 9, AIR)
    b.walls(HX0 + 2, -6, HZ0 + 2, HX0 + 13, -1, HZ0 + 10, "minecraft:cobblestone")
    b.box(HX0 + 3, -6, HZ0 + 3, HX0 + 12, -6, HZ0 + 9, "minecraft:cobblestone")
    I.furnish(b, HX0 + 3, -5, HZ0 + 3, HX0 + 12, HZ0 + 9, 4, "treasure", "royal", seed=42)
    for y in range(-5, 1): b.set(HX0 + 12, y, HZ0 + 3, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(HX0 + 12, 1, HZ0 + 3, AIR)
    b.chest(HX0 + 4, -5, HZ0 + 5, "treasure", "east")
    # ---------------- the Saruyama Alliance camp (east)
    SX, SZ = 66, 32
    for (x, z, c) in ((SX, SZ, "orange"), (SX + 10, SZ + 2, "brown")):
        for dx in range(-3, 4):
            for dy in range(0, 4 - abs(dx)):
                for dz in range(0, 7): b.set(x + dx, 1 + dy, z + dz, f"minecraft:{c}_wool" if dy < 3 else "minecraft:white_wool")
        for dz in range(0, 7):
            for dy in (0, 1): b.set(x, 1 + dy, z + dz, AIR) if dz < 6 else b.set(x, 1 + dy, z + dz, AIR)
        b.set(x, 1, z + 2, f"minecraft:{c}_bed[facing=north,occupied=false,part=head]"); b.set(x, 1, z + 3, f"minecraft:{c}_bed[facing=north,occupied=false,part=foot]")
        b.set(x - 2, 1, z + 4, "onepiece:sake_barrel[axis=y]")
    b.cyl(SX + 5, SZ + 12, 1.6, 0, 0, "minecraft:cobblestone"); b.set(SX + 5, 1, SZ + 12, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz) in ((-3, 0), (3, 0), (0, 3)): b.set(SX + 5 + dx, 1, SZ + 12 + dz, "minecraft:spruce_log[axis=x]" if dz == 0 else "minecraft:spruce_log[axis=z]")
    b.set(SX + 10, 1, SZ + 14, "minecraft:barrel[facing=up,open=false]"); b.set(SX + 10, 2, SZ + 14, "minecraft:barrel[facing=up,open=false]")
    for x in range(SX - 4, SX + 12): b.set(x, 6, SZ - 1, "minecraft:spruce_fence") if x % 3 == 0 else None
    # ---------------- the pier with the salvage boat, and the beach
    T.pier(b, 34, SEA_Z - 2, 14, axis="z", boat=False)
    b.ship(28, -2, SEA_Z + 6, 14, 6, masts=((6, 9),), sail="minecraft:white_wool", cabin=(4, 3, "minecraft:spruce_planks"))
    for x in range(44, 50):  # salvage gear on the pier end
        b.set(x, 1, SEA_Z + 9, "minecraft:chain[axis=y,waterlogged=false]") if False else None
    b.set(37, 2, SEA_Z + 10, "minecraft:copper_block"); b.set(37, 3, SEA_Z + 10, "minecraft:glass")
    for (x, z) in ((10, 48), (56, 50), (74, 46), (20, 52)): b.palm(x, 1, z, rnd.randint(6, 8))
    T.path(b, [(GX, FZ - 1), (GX, 40), (36, SEA_Z - 3)], w=1)
    T.path(b, [(GX, 30), (SX + 4, SZ + 9)], w=1)
    T.lamp_post(b, GX - 3, 32); T.lamp_post(b, GX + 3, 44)
    b.chest(HX0 + 2, 1, HZ0 + 2, "medium", "east")
    return b, 0
