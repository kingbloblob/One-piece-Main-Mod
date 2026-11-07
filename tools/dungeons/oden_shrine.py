"""Oden's Hidden Shrine (Wano, New World): a path of red torii gates through cherry trees to a mountain shrine;
below it the hall where Kozuki Oden's retainers hid his second blade, Ame no Habakiri, after his death.
Mini-boss: Ronin Lord Kagemaru, a two-sword iai master with flying slashes, who calls his ronin.
Signature: the red torii avenue, the shrine's three-tier curved roof, stone lanterns and a koi pond."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgkit import Dungeon, AIR, stairs, slab, wall_of, fence, N_X, N_Z  # noqa: E402

SID = "oden_shrine"
TITLE = "Oden's Hidden Shrine"
CUTS = [-13]
BIOMES = ["onepiece:kuri", "onepiece:wano", "onepiece:withered_forest"]
RED = "minecraft:red_terracotta"

THEME = dict(
    rock=[("minecraft:stone", 4), ("minecraft:andesite", 2), ("minecraft:tuff", 1)],
    subsoil=[("minecraft:dirt", 3), ("minecraft:coarse_dirt", 1)],
    surface=[("minecraft:grass_block", 6), ("minecraft:moss_block", 2), ("minecraft:podzol", 1)],
    path=[("minecraft:stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1), ("minecraft:gravel", 1)],
    ruin=[("minecraft:stone_bricks", 2), ("minecraft:mossy_stone_bricks", 2)],
    ruin_slab="minecraft:stone_brick_slab",
    wall=[("minecraft:stone_bricks", 4), ("minecraft:mossy_stone_bricks", 2), ("minecraft:cracked_stone_bricks", 1)],
    floor=[("minecraft:dark_oak_planks", 3), ("minecraft:spruce_planks", 1)],
    ceil=[("minecraft:dark_oak_planks", 1)],
    base="minecraft:polished_andesite",
    pillar="minecraft:stripped_dark_oak_log[axis=y]", pillar_base=RED,
    lamp="minecraft:pearlescent_froglight[axis=y]", hang="minecraft:lantern[hanging=true,waterlogged=false]",
    stair="minecraft:stone_brick_stairs", carpet="red", cloth="red", bed="white", wood="dark_oak",
    urn="minecraft:flower_pot",
    pit=[("minecraft:magma_block", 1)],
    brazier_base="minecraft:stone_bricks", brazier="minecraft:lantern[hanging=false,waterlogged=false]",
    channel="minecraft:water[level=0]", rail=fence("dark_oak"),
    accent="minecraft:gold_block", dais=[("minecraft:dark_oak_planks", 2), ("minecraft:stripped_dark_oak_wood[axis=y]", 1)],
    throne="minecraft:dark_oak_stairs", throne_side=RED,
    throne_back=[(RED, 1)], altar_top="minecraft:polished_andesite",
)
ROOF = "minecraft:deepslate_tile_stairs"


def torii(d, z, x0=28, x1=36, h=7):
    b = d.b
    for x in (x0, x1):
        for y in range(1, h):
            b.set(x, y, z, RED)
        b.set(x, 0, z, "minecraft:polished_andesite")
    for x in range(x0 - 1, x1 + 2):
        b.set(x, h, z, "minecraft:black_concrete")
        b.set(x, h - 2, z, RED if x0 <= x <= x1 else AIR)
    b.set(x0 - 2, h, z, stairs("minecraft:blackstone_stairs", "east", "top"))
    b.set(x1 + 2, h, z, stairs("minecraft:blackstone_stairs", "west", "top"))


def stone_lantern(d, x, z):
    b = d.b
    b.set(x, 1, z, "minecraft:stone_bricks")
    b.set(x, 2, z, wall_of("minecraft:stone_brick_wall"))
    b.set(x, 3, z, "minecraft:lantern[hanging=false,waterlogged=false]")
    b.set(x, 4, z, slab("minecraft:stone_brick_slab"))


def shrine(d):
    b = d.b
    x0, z0, x1, z1 = 25, 52, 39, 65
    d.mixbox(x0 - 1, 1, z0 - 1, x1 + 1, 1, z1 + 1, [("minecraft:polished_andesite", 1)])     # stone podium
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(2, 7):
                if edge:
                    corner = (x - x0) % 7 == 0 and (z - z0) % 13 == 0 or (x - x0) % 7 == 0 and z in (z0, z1) or (z - z0) % 4 == 0 and x in (x0, x1)
                    b.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]" if corner else
                          ("minecraft:white_terracotta" if y > 2 else "minecraft:dark_oak_planks"))
                else:
                    b.set(x, y, z, AIR)
    d.mixbox(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, [("minecraft:bamboo_mosaic", 1)])
    d.air(30, -0, 56, 32, 1, 58)
    b.box(x0, 7, z0, x1, 7, z1, "minecraft:dark_oak_planks")
    b.pagoda_roof(32, 58, 9, 8, 8, ROOF, "minecraft:deepslate_tiles", layers=3, slab_block="minecraft:deepslate_tile_slab")
    b.box(29, 11, 55, 35, 13, 61, "minecraft:white_terracotta")
    b.pagoda_roof(32, 58, 5, 5, 14, ROOF, "minecraft:deepslate_tiles", layers=3, slab_block="minecraft:deepslate_tile_slab")
    b.set(32, 17, 58, "minecraft:gold_block")
    # front: wide opening with a red frame, offering box and bell rope
    d.air(29, 2, z1, 35, 5, z1)
    for y in range(2, 6):
        b.set(28, y, z1, RED); b.set(36, y, z1, RED)
    for x in range(28, 37):
        b.set(x, 6, z1, RED)
    b.set(32, 2, z1 + 2, "minecraft:barrel[facing=up,open=false]")
    b.set(32, 6, z1 + 1, "minecraft:bell[attachment=ceiling,facing=south,powered=false]")
    for x in range(30, 35):
        b.set(x, 1, z1 + 2, stairs("minecraft:polished_andesite_stairs", "north"))
    for z in range(z0 + 2, z1 - 1, 4):
        b.set(x0, 4, z, "minecraft:dark_oak_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
        b.set(x1, 4, z, "minecraft:dark_oak_trapdoor[facing=east,half=top,open=true,powered=false,waterlogged=false]")
    b.set(32, 6, 60, "minecraft:lantern[hanging=true,waterlogged=false]")


def cherry(d, x, z, h=6):
    b = d.b
    for y in range(1, h):
        b.set(x, y, z, "minecraft:cherry_log[axis=y]")
    b.sphere(x, h + 1, z, 3.2, "minecraft:cherry_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.2)
    for y in range(1, h + 1):
        b.set(x, y, z, "minecraft:cherry_log[axis=y]")


def pond(d, cx, cz, r=5):
    b = d.b
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            dd = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
            if dd < r - 0.5:
                b.set(x, 0, z, "minecraft:water[level=0]")
                b.set(x, -1, z, "minecraft:clay")
            elif dd < r + 0.5:
                b.set(x, 0, z, "minecraft:mossy_cobblestone")
    b.set(cx + 1, 1, cz - 1, "minecraft:lily_pad")


def build():
    d = Dungeon(SID, THEME, 2028)
    d.ground()
    d.underground()
    shrine(d)
    d.path(30, 34, 66, N_Z - 1)
    for z in range(69, N_Z - 1, 4):
        torii(d, z)
    for z in (68, 76):
        stone_lantern(d, 26, z); stone_lantern(d, 38, z)
    for (x, z) in ((14, 56), (50, 56), (8, 30), (56, 28), (16, 12), (48, 10), (10, 72), (54, 72)):
        cherry(d, x, z, 5 + (x + z) % 3)
    pond(d, 12, 42)
    pond(d, 52, 42, 4)
    d.ruin_wall(2, 2, 61, 2, 2)
    d.scatter(["minecraft:short_grass",
               "minecraft:fern", "minecraft:lily_of_the_valley", "minecraft:azure_bluet"], 80,
              keep_out=((22, 49, 42, N_Z - 1),))
    d.entities("ronin_lord", ["ronin"], "ronin")
    return d.b
