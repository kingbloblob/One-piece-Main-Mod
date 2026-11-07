"""Impel Down Level 6, Eternal Hell, life size: the secret deepest level, never spoken of, where the World
Government hides criminals too dangerous to exist. A black, silent cavern of obsidian. A long hall of sealed
cells with seastone bars on two tiers, each holding a chained cell, the great sealed vault in the middle behind
seastone doors, the execution chamber with its iron chair, the records room of erased names, watch posts lit by
soul fire, and the sealed shaft above. Canvas y 0 = the cavern floor, world y 33."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "eternal_hell_vault"
TITLE = "Impel Down Level 6: Eternal Hell"
CUTS = [3, 9, 15]
TILER = dict(terrain="none", sky_y=33)

N = 96
CX, CZ = 48, 48
RX, RZ, H = 44, 40, 28
ROCK = ("minecraft:obsidian", "minecraft:obsidian", "minecraft:crying_obsidian", "minecraft:blackstone", "minecraft:deepslate_tiles")
SEA = "onepiece:seastone_bricks"
DARK = dict(wood="dark_oak", rug="black", rug2="gray", bed="black", light="minecraft:soul_lantern", accent="onepiece:seastone_block",
            banner="black", candle="black")


def build():
    rnd = random.Random(931)
    b = B()
    U.cavern(b, CX, CZ, RX, RZ, H, ROCK, rnd, floor="minecraft:polished_deepslate", thick=3, below=3)
    for x in range(N):
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:polished_deepslate" and (x + z) % 6 == 0: b.set(x, 0, z, "minecraft:deepslate_tiles")
    # ---------------- the hall of sealed cells, two tiers each side of the central hall
    for (z0, face) in ((20, "south"), (69, "north")):
        for tier in range(2):
            U.cell_row(b, 16, 1 + tier * 7, z0, 10, 8, 8, 6, SEA, face, DARK, seed=z0 + tier)
        wz = z0 + 8 if face == "south" else z0 - 1
        for x in range(16, 87):
            b.set(x, 7, wz, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
            b.set(x, 8, wz + (1 if face == "south" else -1), "onepiece:prison_bars")
        for i in range(10):
            for tier in range(2):
                x = 19 + i * 7
                y = 1 + tier * 7
                cz = z0 + 3
                b.set(x, y + 4, cz, "minecraft:iron_chain[axis=y]"); b.set(x, y + 3, cz, "minecraft:iron_chain[axis=y]")
                b.set(x + 1, y, cz, "minecraft:soul_lantern[hanging=false,waterlogged=false]") if i % 3 == 0 else None
        lz = wz + (1 if face == "south" else -1)
        for y in range(1, 8): b.set(15, y, lz, "minecraft:ladder[facing=%s,waterlogged=false]" % face)
    # ---------------- soul-fire corridor down the middle and the sealed vault
    for x in range(12, 86, 4):
        b.set(x, 0, CZ - 6, "minecraft:soul_soil"); b.set(x, 1, CZ - 6, "minecraft:soul_fire")
        b.set(x, 0, CZ + 6, "minecraft:soul_soil"); b.set(x, 1, CZ + 6, "minecraft:soul_fire")
    VX0, VZ0, VX1, VZ1 = 40, 40, 56, 56
    b.box(VX0, 0, VZ0, VX1, 0, VZ1, "minecraft:obsidian")
    b.walls(VX0, 1, VZ0, VX1, 10, VZ1, SEA); b.box(VX0 + 1, 1, VZ0 + 1, VX1 - 1, 9, VZ1 - 1, AIR)
    b.box(VX0, 11, VZ0, VX1, 11, VZ1, "minecraft:obsidian")
    for x in range(VX0 + 6, VX0 + 11):
        for y in range(1, 6): b.set(x, y, VZ1, "onepiece:seastone_block")
    for x in range(VX0 + 7, VX0 + 10): b.set(x, 6, VZ1, "minecraft:chiseled_polished_blackstone")
    I.furnish(b, VX0 + 1, 1, VZ0 + 1, VX1 - 1, VZ1 - 1, 8, "treasure", DARK, seed=1)
    b.box(CX - 1, 1, CZ - 1, CX + 1, 1, CZ + 1, "minecraft:obsidian")
    # ---------------- the execution chamber (west) and the records room of erased names (east)
    b.walls(6, 1, 38, 14, 8, 58, SEA); b.box(7, 1, 39, 13, 8, 57, AIR); b.box(6, 9, 38, 14, 9, 58, "minecraft:obsidian")
    b.box(7, 0, 39, 13, 0, 57, "minecraft:deepslate_tiles")
    b.set(10, 1, 48, "minecraft:iron_block"); b.set(10, 2, 48, "minecraft:polished_blackstone_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    for y in range(3, 9): b.set(10, y, 48, "minecraft:iron_chain[axis=y]")
    for z in (42, 54): b.set(8, 1, z, "minecraft:grindstone[face=floor,facing=north]"); b.set(12, 1, z, "minecraft:anvil[facing=east]")
    for z in range(46, 51):
        for y in (1, 2, 3): b.set(14, y, z, AIR)
    b.walls(82, 1, 38, 90, 8, 58, SEA); b.box(83, 1, 39, 89, 8, 57, AIR); b.box(82, 9, 38, 90, 9, 58, "minecraft:obsidian")
    b.box(83, 0, 39, 89, 0, 57, "minecraft:dark_oak_planks")
    I.furnish(b, 83, 1, 39, 89, 57, 7, "library", DARK, seed=2)
    for z in range(46, 51):
        for y in (1, 2, 3): b.set(82, y, z, AIR)
    # ---------------- the sealed shaft above (north) and watch posts
    b.box(CX - 3, 0, 4, CX + 3, H + 4, 10, SEA); b.box(CX - 2, 1, 5, CX + 2, H + 4, 9, AIR)
    b.box(CX - 2, H - 2, 5, CX + 2, H - 2, 9, "onepiece:seastone_block")
    for y in range(1, H - 2): b.set(CX, y, 5, "minecraft:ladder[facing=south,waterlogged=false]")
    for dx in (-1, 0, 1):
        for y in (1, 2, 3): b.set(CX + dx, y, 10, AIR)
    for (x, z) in ((22, CZ), (74, CZ), (CX, 34), (CX, 62)):
        b.box(x - 1, 1, z - 1, x + 1, 1, z + 1, "minecraft:polished_blackstone_bricks"); b.set(x, 2, z, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    U.pillars(b, ((CX - 30, CZ - 28), (CX + 30, CZ - 28), (CX - 30, CZ + 28), (CX + 30, CZ + 28)), -3, -6, "minecraft:obsidian")
    # ---------------- loot and guards
    b.chest(CX, 2, CZ, "eternal_hell", "south"); b.chest(VX0 + 2, 1, VZ0 + 2, "eternal_hell", "east"); b.chest(88, 1, 40, "impel_down", "west")
    b.guards("warden_jailer", ((30, CZ), (66, CZ)))
    b.guards("jailer", ((CX - 12, CZ - 3), (CX + 12, CZ + 3), (20, 60), (76, 36)))
    return b, 0
