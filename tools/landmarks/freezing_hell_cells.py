"""Impel Down Level 5, Freezing Hell, life size: a frozen cavern where a never-ending blizzard keeps the worst
prisoners half dead. A forest of frozen dead trees and ice spires, snow drifts with hidden powder-snow pits, the
frozen lake, rows of cells cut into the ice cliffs with frozen prisoners inside, the wolves' den of the Jailer
Beasts, the guards' heated watch house with its stove and bunks, and the secret crack in the wall that leads to
Newkama Land. Canvas y 0 = the cavern floor, world y 33."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "freezing_hell_cells"
TITLE = "Impel Down Level 5: Freezing Hell"
CUTS = [3, 8, 16]
TILER = dict(terrain="none", sky_y=33)

N = 96
CX, CZ = 48, 48
RX, RZ, H = 44, 44, 30
ICE = ("minecraft:packed_ice", "minecraft:packed_ice", "minecraft:blue_ice", "minecraft:snow_block", "minecraft:packed_ice")
COLD = dict(wood="spruce", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="minecraft:packed_ice",
            banner="light_blue", candle="white")
WATCH = dict(wood="spruce", rug="red", rug2="brown", bed="red", light="minecraft:lantern", accent="minecraft:furnace[facing=south,lit=true]",
             banner="blue", candle="orange")


def build():
    rnd = random.Random(911)
    b = B()
    U.cavern(b, CX, CZ, RX, RZ, H, ICE, rnd, floor="minecraft:snow_block", thick=3, below=3)
    for x in range(N):  # snow drifts on the floor
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:snow_block" and b.get(x, 1, z) == AIR:
                k = int(2 + 2 * math.sin(x * 0.3) * math.cos(z * 0.25))
                b.set(x, 1, z, f"minecraft:snow[layers={max(1, min(7, k))}]")
    # the frozen lake
    LX, LZ = 62, 60
    b.shape(lambda x, y, z: ((x - LX) / 14) ** 2 + ((z - LZ) / 9) ** 2 < 1, LX - 14, 0, LZ - 9, LX + 14, 1, LZ + 9, "minecraft:ice", interior=None)
    for x in range(LX - 14, LX + 15):
        for z in range(LZ - 9, LZ + 10):
            if ((x - LX) / 14) ** 2 + ((z - LZ) / 9) ** 2 < 1: b.set(x, 1, z, AIR); b.set(x, -1, z, WATER); b.set(x, -2, z, "minecraft:packed_ice")
    # frozen dead trees and ice spires
    for i in range(70):
        x, z = rnd.randint(12, N - 12), rnd.randint(12, N - 12)
        if ((x - LX) / 16) ** 2 + ((z - LZ) / 11) ** 2 < 1 or (34 <= x <= 62 and 8 <= z <= 30) or (6 <= x <= 22 and 30 <= z <= 66): continue
        if i % 3:
            h = rnd.randint(7, 13)
            for y in range(1, h): b.set(x, y, z, "minecraft:stripped_spruce_log[axis=y]")
            for k in range(4):
                dx, dz = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                for j in range(1, 4): b.set(x + dx * j, h - 3 + k + j // 2, z + dz * j, "minecraft:stripped_spruce_log[axis=x]" if dx else "minecraft:stripped_spruce_log[axis=z]")
            b.set(x, h, z, "minecraft:snow_block")
        else:
            h = rnd.randint(8, 18)
            for y in range(1, h): b.cyl(x, z, max(0.5, 2.2 * (1 - y / h)), y, y, "minecraft:packed_ice" if y % 4 else "minecraft:blue_ice")
    for i in range(30):  # icicles from the roof
        x, z = rnd.randint(10, N - 10), rnd.randint(10, N - 10)
        top = H - 2 - int(H * (((x - CX) / RX) ** 2 + ((z - CZ) / RZ) ** 2))
        for k in range(rnd.randint(2, 6)): b.set(x, top - k, z, "minecraft:packed_ice") if top - k > 4 else None
    # powder-snow pits, hidden under snow
    for i in range(12):
        x, z = rnd.randint(28, 70), rnd.randint(32, 46)
        b.set(x, 0, z, "minecraft:powder_snow"); b.set(x, -1, z, "minecraft:powder_snow")
    # ---------------- cells cut into the ice cliffs (north wall) with frozen prisoners
    for tier in range(2):
        U.cell_row(b, 34, 1 + tier * 6, 10, 5, 7, 7, 5, "minecraft:blue_ice", "south", COLD, seed=10 + tier * 10)
        for x in range(34, 64): b.set(x, 6, 17, "minecraft:spruce_slab[type=top,waterlogged=false]")
    for i in range(5):
        for tier in range(2):
            x, y = 37 + i * 6, 1 + tier * 6
            b.set(x, y, 13, "minecraft:ice"); b.set(x, y + 1, 13, "minecraft:ice")  # a prisoner frozen solid
            b.set(x, y + 2, 13, "minecraft:skeleton_skull[powered=false,rotation=0]")
    for y in range(1, 7): b.set(33, y, 17, "minecraft:ladder[facing=west,waterlogged=false]") if False else b.set(34, y, 18, "minecraft:ladder[facing=south,waterlogged=false]")
    U.cell_row(b, 74, 1, 30, 5, 7, 7, 5, "minecraft:packed_ice", "west", COLD, seed=40, axis="z")
    # ---------------- the guards' heated watch house (west)
    WX0, WZ0, WX1, WZ1 = 6, 34, 22, 62
    b.box(WX0, 0, WZ0, WX1, 0, WZ1, "minecraft:spruce_planks")
    b.walls(WX0, 1, WZ0, WX1, 6, WZ1, "minecraft:spruce_log[axis=y]"); b.box(WX0 + 1, 1, WZ0 + 1, WX1 - 1, 6, WZ1 - 1, AIR)
    b.gable_roof(WX0, WZ0, WX1, WZ1, 7, "minecraft:spruce_stairs", "minecraft:spruce_planks", gable_wall="minecraft:spruce_planks") if False else None
    b.hip_roof(WX0, WZ0, WX1, WZ1, 7, "minecraft:spruce_stairs", "minecraft:spruce_planks")
    for z in range(WZ0 + 2, WZ1 - 1, 4): b.set(WX1, 3, z, "minecraft:glass_pane")
    for z in range(46, 49):
        for y in (1, 2, 3): b.set(WX1, y, z, AIR)
    I.subdivide(b, WX0 + 1, 1, WZ0 + 1, WX1 - 1, WZ1 - 1, 4, "minecraft:spruce_planks", ("kitchen", "barracks", "barracks", "armory"), WATCH, cell=8, seed=1, door="east")
    for k in range(H): b.set(WX0 + 3, 8 + k, WZ0 + 3, "minecraft:cobblestone_wall") if 8 + k < H - 4 else None
    # the wolves' den
    DX, DZ = 30, 76
    b.cyl(DX, DZ, 7, 1, 4, "minecraft:snow_block", hollow=True); b.cyl(DX, DZ, 7.5, 5, 5, "minecraft:snow_block")
    for x in range(DX - 1, DX + 2):
        for y in (1, 2): b.set(x, y, DZ - 7, AIR)
    for i in range(10): b.set(DX + rnd.randint(-5, 5), 1, DZ + rnd.randint(-5, 5), rnd.choice(("minecraft:bone_block[axis=y]", "minecraft:hay_block[axis=y]", "minecraft:white_wool")))
    # the secret crack to Newkama Land (south-east wall)
    for k in range(10):
        x, z = 80 + k // 2, 80 + k // 2
        for y in range(1, 4): b.set(x, y, z, AIR); b.set(x + 1, y, z, AIR)
    b.set(84, 3, 84, "minecraft:pink_stained_glass")
    # ---------------- loot and guards
    b.chest(WX0 + 2, 1, WZ0 + 2, "impel_down", "east"); b.chest(DX, 1, DZ + 3, "impel_down", "north"); b.chest(LX, 1, LZ - 11, "impel_down", "south")
    b.guards("frost_soldier", ((40, 30), (56, 40), (66, 26), (24, 70)))
    b.guards("jailer", ((26, 48), (70, 48)))
    b.guards("warden_jailer", ((DX, DZ),))
    return b, 0
