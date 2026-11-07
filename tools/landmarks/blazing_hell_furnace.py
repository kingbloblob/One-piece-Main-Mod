"""Impel Down Level 4, Blazing Hell, life size: a vast hot cavern deep under the sea, carved from black rock just
above the Nether's lava sea. In the middle the great cauldron of boiling blood with the iron bridge hung over
it on chains, two tiers of barred cell blocks along the walls with walkways and ladders, the furnace room with
its fire grates, the guards' barracks and armory, the Jailer Beasts' kennels, the central lift shaft up to the
upper levels, and Chief Warden Magellan's office: his desk and files, his bedroom and (of course) his private
bathroom. Canvas y 0 = the cavern floor, world y 33."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "blazing_hell_furnace"
TITLE = "Impel Down Level 4: Blazing Hell"
CUTS = [3, 9, 16]
TILER = dict(terrain="none", sky_y=33)

N = 100
CX, CZ = 50, 50
RX, RZ, H = 46, 46, 38
ROCK = ("minecraft:blackstone", "minecraft:basalt[axis=y]", "minecraft:polished_blackstone_bricks", "minecraft:blackstone", "minecraft:smooth_basalt")
BRICK = "minecraft:polished_blackstone_bricks"
NB = "minecraft:nether_bricks"
JAIL = dict(wood="crimson", rug="red", rug2="black", bed="red", light="minecraft:soul_lantern", accent="minecraft:polished_blackstone_bricks",
            banner="red", candle="red")
WARDEN = dict(wood="dark_oak", rug="purple", rug2="black", bed="purple", light="minecraft:lantern", accent="onepiece:seastone_block",
              banner="purple", candle="purple")


def build():
    rnd = random.Random(901)
    b = B()
    U.cavern(b, CX, CZ, RX, RZ, H, ROCK, rnd, floor="minecraft:blackstone", thick=3, below=3)
    for x in range(N):  # magma veins in the floor
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:blackstone" and (abs(math.sin(x * 0.21 + z * 0.13) * 9 - (z * 0.4 % 9)) < 0.5 or rnd.random() < 0.02):
                b.set(x, 0, z, "minecraft:magma_block")
    # ---------------- the cauldron of boiling blood
    b.cyl(CX, CZ, 15, 0, 4, NB); b.cyl(CX, CZ, 13, -3, 4, AIR)
    b.cyl(CX, CZ, 13, -4, -4, NB); b.cyl(CX, CZ, 13, -3, 2, "minecraft:lava[level=0]")
    b.cyl(CX, CZ, 15.5, 5, 5, "minecraft:nether_brick_fence", hollow=True)
    for a in range(0, 360, 30):  # fire grates and braziers round the rim
        t = math.radians(a)
        x, z = round(CX + 17 * math.cos(t)), round(CZ + 17 * math.sin(t))
        b.set(x, 1, z, "minecraft:polished_blackstone_wall"); b.set(x, 2, z, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in range(CX - 18, CX + 19):  # the hanging iron bridge over it
        b.set(x, 9, CZ, "minecraft:iron_block" if x % 4 == 0 else "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        b.set(x, 9, CZ - 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"); b.set(x, 9, CZ + 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        b.set(x, 10, CZ - 2, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]"); b.set(x, 10, CZ + 2, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
        if x % 6 == 0:
            for y in range(11, H - 4): b.set(x, y, CZ - 2, "minecraft:iron_chain[axis=y]"); b.set(x, y, CZ + 2, "minecraft:iron_chain[axis=y]")
    for s in (-1, 1):  # stairs up to the bridge from both ends
        for i in range(9):
            for dz in (-1, 0, 1): b.set(CX + s * (27 - i), 1 + i, CZ + dz, stairs("minecraft:polished_blackstone_brick_stairs", "east" if s < 0 else "west"))
            for dz in (-1, 0, 1):
                for y in range(0, 1 + i): b.set(CX + s * (27 - i), y, CZ + dz, BRICK) if y < 1 + i else None
        for x in range(CX + s * 19, CX + s * 19 + s * 0 + 1):
            for dz in (-1, 0, 1): b.set(CX + s * 19, 9, CZ + dz, BRICK); b.set(CX + s * 18, 9, CZ + dz, BRICK)
    # ---------------- two tiers of cell blocks (north and south)
    for (z0, face) in ((14, "south"), (78, "north")):
        for tier in range(2):
            y = 1 + tier * 6
            x0 = 22 if tier == 0 else 24
            U.cell_row(b, x0, y, z0, 9 if tier == 0 else 8, 7, 7, 5, BRICK, face, JAIL, seed=z0 + tier * 20)
        wz = z0 + 7 if face == "south" else z0 - 1  # the upper walkway with a rail
        for x in range(22, 81):
            b.set(x, 6, wz, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
            b.set(x, 7, wz + (1 if face == "south" else -1), "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
        for x in (22, 80):
            for y in range(1, 7): b.set(x, y, wz, "minecraft:ladder[facing=%s,waterlogged=false]" % ("south" if face == "south" else "north")) if False else b.set(x, y, wz + (1 if face == "south" else -1), "minecraft:ladder[facing=%s,waterlogged=false]" % ("south" if face == "south" else "north"))
    # ---------------- Magellan's office (west): study, bedroom and his bathroom
    OX0, OZ0, OX1, OZ1 = 8, 36, 22, 64
    b.box(OX0, 0, OZ0, OX1, 0, OZ1, "minecraft:polished_deepslate")
    b.walls(OX0, 1, OZ0, OX1, 11, OZ1, "onepiece:seastone_bricks")
    b.box(OX0 + 1, 1, OZ0 + 1, OX1 - 1, 11, OZ1 - 1, AIR); b.box(OX0 + 1, 6, OZ0 + 1, OX1 - 1, 6, OZ1 - 1, "minecraft:dark_oak_planks")
    b.box(OX0, 12, OZ0, OX1, 12, OZ1, "minecraft:polished_blackstone_bricks")
    for z in range(OZ0 + 2, OZ1 - 1, 3):
        b.set(OX1, 3, z, "minecraft:purple_stained_glass_pane"); b.set(OX1, 8, z, "minecraft:purple_stained_glass_pane")
    for z in range(48, 53):
        for y in range(1, 5): b.set(OX1, y, z, AIR)
    I.furnish(b, OX0 + 1, 1, OZ0 + 1, OX1 - 1, OZ0 + 14, 4, "study", WARDEN, seed=1)
    I.furnish(b, OX0 + 1, 1, OZ0 + 16, OX1 - 1, OZ1 - 1, 4, "armory", WARDEN, seed=2)
    for x in range(OX0 + 1, OX1): b.set(x, 1, OZ0 + 15, "onepiece:seastone_bricks"); b.set(x, 2, OZ0 + 15, "onepiece:seastone_bricks"); b.set(x, 3, OZ0 + 15, "onepiece:seastone_bricks")
    b.set(OX1 - 2, 1, OZ0 + 15, AIR); b.set(OX1 - 2, 2, OZ0 + 15, AIR)
    I.furnish(b, OX0 + 1, 7, OZ0 + 1, OX1 - 1, OZ0 + 18, 4, "bedroom", WARDEN, seed=3)
    I.furnish(b, OX0 + 1, 7, OZ0 + 20, OX1 - 1, OZ1 - 1, 4, "bath", WARDEN, seed=4)
    for x in range(OX0 + 1, OX1): b.set(x, 7, OZ0 + 19, "onepiece:seastone_bricks"); b.set(x, 8, OZ0 + 19, "onepiece:seastone_bricks"); b.set(x, 9, OZ0 + 19, "onepiece:seastone_bricks")
    b.set(OX0 + 3, 7, OZ0 + 19, AIR); b.set(OX0 + 3, 8, OZ0 + 19, AIR)
    for (x, z) in ((OX0 + 3, OZ1 - 3), (OX0 + 5, OZ1 - 3)): b.set(x, 7, z, "minecraft:white_glazed_terracotta") if False else b.set(x, 7, z, "minecraft:cauldron")
    for y in range(1, 7): b.set(OX1 - 2, y, OZ1 - 2, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(OX1 - 2, 6, OZ1 - 2, "minecraft:ladder[facing=west,waterlogged=false]")
    # ---------------- guards' barracks, furnace room and the beast kennels (east)
    I.subdivide(b, 80, 1, 34, 92, 66, 5, BRICK, ("barracks", "armory", "kitchen", "barracks"), JAIL, cell=10, seed=5, door="west")
    b.box(80, 6, 34, 92, 6, 66, BRICK)
    for z in range(36, 66, 8):  # fire grates of the furnace room line the passage
        b.set(78, 0, z, "minecraft:magma_block"); b.set(78, 1, z, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    for (x, z) in ((70, 22), (76, 26), (70, 74), (76, 72)):  # kennels
        b.box(x - 2, 1, z - 2, x + 2, 3, z + 2, "onepiece:prison_bars"); b.box(x - 1, 1, z - 1, x + 1, 3, z + 1, AIR)
        b.set(x, 0, z, "minecraft:hay_block[axis=y]"); b.set(x + 1, 1, z + 1, "minecraft:bone_block[axis=y]")
    # ---------------- the central lift shaft (north) and the gate tunnel (south)
    LX, LZ = CX, 6
    b.box(LX - 3, 0, LZ - 3, LX + 3, H + 6, LZ + 3, "onepiece:seastone_bricks"); b.box(LX - 2, 1, LZ - 2, LX + 2, H + 6, LZ + 2, AIR)
    for y in range(1, H + 6): b.set(LX, y, LZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (1, 2, 3):
        for dx in (-1, 0, 1): b.set(LX + dx, y, LZ + 3, AIR)
    b.box(LX - 1, 1, LZ - 1, LX + 1, 1, LZ + 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for z in range(N - 8, N):
        for x in range(CX - 3, CX + 4):
            b.set(x, 0, z, BRICK)
            for y in range(1, 7): b.set(x, y, z, AIR)
            b.set(x, 7, z, BRICK)
        for y in range(0, 8): b.set(CX - 4, y, z, BRICK); b.set(CX + 4, y, z, BRICK)
    for x in range(CX - 3, CX + 4):
        for y in range(1, 6): b.set(x, y, N - 4, "onepiece:prison_bars") if x != CX else None
    # pillars down to the lava sea and lights
    U.pillars(b, ((CX - 30, CZ - 30), (CX + 30, CZ - 30), (CX - 30, CZ + 30), (CX + 30, CZ + 30)), -3, -6, BRICK)
    for a in range(0, 360, 40):
        t = math.radians(a)
        b.set(round(CX + 32 * math.cos(t)), H - 8, round(CZ + 32 * math.sin(t)), "minecraft:shroomlight")
    # scattered braziers, chained posts and bone heaps on the open floor
    for i in range(40):
        x, z = rnd.randint(10, N - 10), rnd.randint(10, N - 10)
        if math.hypot(x - CX, z - CZ) < 20 or b.get(x, 1, z) not in (None, AIR) or b.get(x, 0, z) in (None, AIR): continue
        k = i % 4
        if k == 0: b.set(x, 1, z, "minecraft:polished_blackstone_wall"); b.set(x, 2, z, "minecraft:fire" if False else "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        elif k == 1:
            for y in range(1, 4): b.set(x, y, z, "minecraft:dark_oak_log[axis=y]")
            b.set(x, 4, z, "minecraft:iron_chain[axis=y]")
        elif k == 2: b.set(x, 1, z, "minecraft:bone_block[axis=y]"); b.set(x + 1, 1, z, "minecraft:skeleton_skull[powered=false,rotation=4]") if b.get(x + 1, 1, z) in (None, AIR) else None
        else: b.set(x, 1, z, "minecraft:anvil[facing=north]")
    # ---------------- loot, warden and guards
    b.chest(OX0 + 2, 1, OZ0 + 2, "impel_down", "east"); b.chest(90, 1, 36, "impel_down", "west"); b.chest(CX, 10, CZ, "impel_down", "south")
    b.npc(OX1 + 4, 1, 50, "magellan", True)
    b.guards("jailer", ((34, 30), (66, 30), (34, 70), (66, 70), (CX, N - 10)))
    b.guards("flame_guard", ((CX - 22, CZ + 6), (CX + 22, CZ - 6)))
    b.guards("warden_jailer", ((74, 50),))
    return b, 0
