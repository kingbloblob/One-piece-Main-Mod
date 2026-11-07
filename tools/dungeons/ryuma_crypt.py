"""Ryuma's Crypt (Thriller Bark, Paradise): a gloomy graveyard round a gothic mausoleum; below it the crypt where
the legendary samurai's shade still guards the blade the Sword God carried. Mini-boss: the Shade of the Sword God,
a fast undead swordsman with flying slashes who raises the crypt's dead.
Signature: the mausoleum's steep roof with a rose window and pinnacles, leaning gravestones, dead trees."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgkit import Dungeon, AIR, stairs, slab, wall_of, fence, N_X, N_Z  # noqa: E402

SID = "ryuma_crypt"
TITLE = "Ryuma's Crypt"
CUTS = [-13]
BIOMES = ["onepiece:thriller_bark"]

THEME = dict(
    rock=[("minecraft:deepslate", 4), ("minecraft:tuff", 2), ("minecraft:cobbled_deepslate", 1)],
    subsoil=[("minecraft:dirt", 3), ("minecraft:coarse_dirt", 1), ("minecraft:mud", 1)],
    surface=[("minecraft:podzol", 4), ("minecraft:coarse_dirt", 3), ("minecraft:grass_block", 2), ("minecraft:mud", 1)],
    path=[("minecraft:cobblestone", 2), ("minecraft:mossy_cobblestone", 2), ("minecraft:gravel", 1)],
    ruin=[("minecraft:mossy_stone_bricks", 2), ("minecraft:cracked_stone_bricks", 2), ("minecraft:stone_bricks", 1)],
    ruin_slab="minecraft:mossy_stone_brick_slab",
    wall=[("minecraft:deepslate_bricks", 4), ("minecraft:cracked_deepslate_bricks", 2), ("minecraft:deepslate_tiles", 1)],
    floor=[("minecraft:polished_deepslate", 3), ("minecraft:deepslate_tiles", 2), ("minecraft:cracked_deepslate_tiles", 1)],
    ceil=[("minecraft:deepslate_tiles", 1)],
    base="minecraft:polished_blackstone_bricks",
    pillar="minecraft:polished_deepslate", pillar_base="minecraft:chiseled_deepslate",
    lamp="minecraft:verdant_froglight[axis=y]", hang="minecraft:soul_lantern[hanging=true,waterlogged=false]",
    stair="minecraft:deepslate_brick_stairs", carpet="gray", cloth="purple", bed="gray", wood="dark_oak",
    urn="minecraft:skeleton_skull[powered=false,rotation=0]",
    pit=[("minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]", 1)],
    brazier_base="minecraft:polished_blackstone", brazier="minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]",
    channel="minecraft:water[level=0]", rail=fence("dark_oak"),
    accent="minecraft:crying_obsidian", dais=[("minecraft:polished_blackstone_bricks", 2), ("minecraft:polished_deepslate", 1)],
    throne="minecraft:polished_blackstone_stairs", throne_side="minecraft:chiseled_polished_blackstone",
    throne_back=[("minecraft:polished_blackstone", 1)], altar_top="minecraft:chiseled_deepslate",
)


def mausoleum(d):
    b = d.b
    x0, z0, x1, z1 = 25, 52, 39, 66
    d.mixbox(x0, 1, z0, x1, 7, z1, THEME["wall"])
    d.air(x0 + 1, 1, z0 + 1, x1 - 1, 6, z1 - 1)
    d.mixbox(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, THEME["floor"])
    d.air(30, 0, 56, 32, 0, 58)                          # stair head
    for x in (x0, x1):                                   # buttresses with pinnacles
        for z in (z0, z0 + 7, z1):
            for y in range(1, 9):
                b.set(x + (-1 if x == x0 else 1), y, z, "minecraft:polished_blackstone_bricks" if y < 8 else
                      wall_of("minecraft:polished_blackstone_brick_wall"))
    for z in range(z0 + 2, z1 - 1, 3):                   # tall lancet windows
        for x in (x0, x1):
            for y in (2, 3, 4):
                b.set(x, y, z, "minecraft:purple_stained_glass_pane[east=false,north=true,south=true,waterlogged=false,west=false]")
    b.gable_roof(x0, z0, x1, z1, 8, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", gable_wall="minecraft:deepslate_bricks", overhang=1)
    # rose window and pointed door on the south gable
    for (x, y) in ((32, 10), (31, 9), (33, 9), (31, 11), (33, 11), (32, 12), (32, 8)):
        b.set(x, y, z1, "minecraft:purple_stained_glass")
    b.set(32, 10, z1, "minecraft:crying_obsidian")
    d.air(31, 1, z1, 33, 4, z1)
    b.set(32, 5, z1, AIR)
    for y in range(1, 6):
        b.set(30, y, z1, "minecraft:chiseled_deepslate"); b.set(34, y, z1, "minecraft:chiseled_deepslate")
    b.set(30, 6, z1 + 1, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    b.set(34, 6, z1 + 1, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    # inside: coffins on plinths along the walls, cobwebs high up
    for z in (54, 61):
        for x in (27, 37):
            d.mixbox(x - 1, 1, z, x + 1, 1, z + 2, [("minecraft:polished_blackstone", 1)])
            b.set(x, 2, z + 1, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for (x, z) in ((26, 53), (38, 53), (26, 65), (38, 65)):
        b.set(x, 6, z, "minecraft:cobweb")
    b.set(32, 6, 61, "minecraft:soul_lantern[hanging=true,waterlogged=false]")


def graves(d):
    b, rnd = d.b, d.rnd
    for gx in list(range(6, 22, 4)) + list(range(44, 60, 4)):
        for gz in range(10, 72, 5):
            if rnd.random() < 0.3:
                continue
            lean = rnd.random() < 0.3
            b.set(gx, 1, gz, "minecraft:mossy_stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
                  if not lean else "minecraft:cracked_stone_bricks")
            b.set(gx, 2, gz, slab("minecraft:stone_brick_slab") if not lean else AIR)
            b.set(gx, 0, gz + 1, "minecraft:coarse_dirt")
            b.set(gx, 0, gz + 2, "minecraft:coarse_dirt")
            if rnd.random() < 0.2:
                b.set(gx, 1, gz + 1, "minecraft:jack_o_lantern[facing=south]" if rnd.random() < 0.5 else "minecraft:wither_rose")


def dead_tree(d, x, z, h):
    b = d.b
    for y in range(1, h):
        b.set(x, y, z, "minecraft:dark_oak_log[axis=y]")
    for (dx, dz, ax) in ((1, 0, "x"), (-1, 0, "x"), (0, 1, "z")):
        for k in range(1, 3):
            b.set(x + dx * k, h - 2 + (k // 2), z + dz * k, f"minecraft:dark_oak_log[axis={ax}]")


def build():
    d = Dungeon(SID, THEME, 2026)
    d.ground()
    d.underground()
    mausoleum(d)
    graves(d)
    d.path(30, 34, 67, N_Z - 1)
    for x in (24, 40):                                    # iron cemetery fence along the path
        for z in range(68, N_Z - 1):
            d.b.set(x, 1, z, "minecraft:iron_bars[east=false,north=true,south=true,waterlogged=false,west=false]")
    for (x, z, h) in ((4, 6, 8), (58, 8, 7), (12, 46, 9), (52, 48, 8), (4, 74, 7), (60, 72, 6)):
        dead_tree(d, x, z, h)
    d.ruin_wall(2, 2, 61, 2, 3)
    d.scatter(["minecraft:dead_bush", "minecraft:short_grass", "minecraft:brown_mushroom", "minecraft:cobweb"], 60,
              keep_out=((22, 50, 42, N_Z - 1),))
    d.entities("sword_shade", ["undead_pirate"], "undead_pirate")
    return d.b
