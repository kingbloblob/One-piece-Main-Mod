"""The Cursed Forge (Kuri, Wano, New World): a burnt-out smithy on the volcanic hills where the Kitetsu line of
swordsmiths worked; below it the forge halls where the first Kitetsu was quenched. The Beasts Pirates hold it now.
Mini-boss: Kurogane, the Cursed Smith, a hammer brute who sets the ground on fire and slams the arena.
Signature: the smithy's curved tiled roof with a tall brick chimney trailing smoke, lava channels below."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgkit import Dungeon, AIR, stairs, slab, wall_of, fence, N_X, N_Z  # noqa: E402

SID = "kitetsu_forge"
TITLE = "The Cursed Forge of Kitetsu"
CUTS = [-13]
BIOMES = ["onepiece:kuri", "onepiece:wano", "onepiece:withered_forest"]

THEME = dict(
    rock=[("minecraft:blackstone", 3), ("minecraft:basalt[axis=y]", 2), ("minecraft:deepslate", 2)],
    subsoil=[("minecraft:coarse_dirt", 2), ("minecraft:packed_mud", 1), ("minecraft:tuff", 1)],
    surface=[("minecraft:coarse_dirt", 3), ("minecraft:podzol", 2), ("minecraft:packed_mud", 1), ("minecraft:tuff", 1)],
    path=[("minecraft:polished_tuff", 2), ("minecraft:tuff_bricks", 2), ("minecraft:cobbled_deepslate", 1)],
    ruin=[("minecraft:polished_blackstone_bricks", 2), ("minecraft:cracked_polished_blackstone_bricks", 2)],
    ruin_slab="minecraft:polished_blackstone_brick_slab",
    wall=[("minecraft:polished_blackstone_bricks", 4), ("minecraft:cracked_polished_blackstone_bricks", 2), ("minecraft:blackstone", 1)],
    floor=[("minecraft:polished_basalt[axis=y]", 2), ("minecraft:smooth_basalt", 2), ("minecraft:polished_blackstone", 1)],
    ceil=[("minecraft:dark_oak_planks", 1)],
    base="minecraft:magma_block",
    pillar="minecraft:stripped_dark_oak_log[axis=y]", pillar_base="minecraft:polished_blackstone",
    lamp="minecraft:ochre_froglight[axis=y]", hang="minecraft:lantern[hanging=true,waterlogged=false]",
    stair="minecraft:polished_blackstone_brick_stairs", carpet="red", cloth="black", bed="red", wood="dark_oak",
    urn="minecraft:anvil[facing=north]",
    pit=[("minecraft:magma_block", 1)],
    brazier_base="minecraft:polished_blackstone", brazier="minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]",
    channel="minecraft:lava[level=0]", rail=wall_of("minecraft:polished_blackstone_wall"),
    accent="minecraft:gilded_blackstone", dais=[("minecraft:polished_blackstone_bricks", 2), ("minecraft:blackstone", 1)],
    throne="minecraft:polished_blackstone_stairs", throne_side="minecraft:anvil[facing=east]",
    throne_back=[("minecraft:blast_furnace[facing=south,lit=true]", 1)], altar_top="minecraft:smithing_table",
)
ROOF = "minecraft:deepslate_tile_stairs"


def smithy(d):
    b = d.b
    x0, z0, x1, z1 = 24, 52, 40, 66
    for x in range(x0, x1 + 1):                          # stone base, posts and plaster
        for z in range(z0, z1 + 1):
            b.set(x, 1, z, "minecraft:polished_blackstone_bricks" if x in (x0, x1) or z in (z0, z1) else AIR)
    for y in range(2, 7):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                b.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]" if (x - x0) % 4 == 0 else "minecraft:white_terracotta")
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                b.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]" if (z - z0) % 4 == 0 else "minecraft:white_terracotta")
    d.air(x0 + 1, 2, z0 + 1, x1 - 1, 6, z1 - 1)
    d.mixbox(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, THEME["floor"])
    d.air(30, 0, 56, 32, 0, 58)
    d.air(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1)
    b.box(x0 + 1, 7, z0 + 1, x1 - 1, 7, z1 - 1, "minecraft:dark_oak_planks")
    b.pagoda_roof(32, 59, 10, 9, 8, ROOF, "minecraft:deepslate_tiles", layers=4, slab_block="minecraft:deepslate_tile_slab")
    # the open front: wide doorway with a noren curtain of black wool
    d.air(29, 1, z1, 35, 4, z1)
    for x in range(29, 36):
        b.set(x, 5, z1, "minecraft:dark_oak_planks"); b.set(x, 4, z1, "minecraft:black_wool" if x % 2 else AIR)
    # windows
    for x in (27, 37):
        for z in (z0, z1):
            b.set(x, 3, z, "minecraft:dark_oak_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]" if z == z0 else
                  "minecraft:dark_oak_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    # chimney with a smoking fire on top, the hearth inside
    for y in range(1, 16):
        for x in (37, 38):
            for z in (54, 55):
                b.set(x, y, z, "minecraft:bricks")
    b.set(37, 16, 54, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    b.set(37, 1, 56, "minecraft:blast_furnace[facing=south,lit=true]")
    b.set(38, 1, 56, "minecraft:furnace[facing=south,lit=true]")
    for x, s in ((26, "minecraft:anvil[facing=east]"), (27, "minecraft:grindstone[face=floor,facing=east]"),
                 (35, "minecraft:water_cauldron[level=3]"), (36, "minecraft:smithing_table")):
        b.set(x, 1, 63, s)
    for z in range(54, 62, 2):                           # sword racks on the west wall
        b.set(25, 3, z, "minecraft:dark_oak_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
        b.set(25, 1, z, "minecraft:barrel[facing=east,open=false]")
    b.set(32, 6, 61, "minecraft:lantern[hanging=true,waterlogged=false]")
    b.set(28, 6, 56, "minecraft:lantern[hanging=true,waterlogged=false]")


def rocks(d):
    """Volcanic outcrops and charred stumps round the yard."""
    b, rnd = d.b, d.rnd
    for (x, z, r) in ((8, 12, 4), (54, 10, 5), (10, 50, 3), (56, 54, 4), (6, 72, 3), (58, 74, 3)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                hgt = int((r - (dx * dx + dz * dz) ** 0.5) * 1.3 + rnd.random())
                for y in range(1, hgt + 1):
                    b.set(x + dx, y, z + dz, rnd.choice(("minecraft:basalt[axis=y]", "minecraft:blackstone", "minecraft:tuff")))
    for (x, z) in ((20, 30), (44, 28), (16, 70), (48, 68)):
        for y in range(1, rnd.randint(2, 4)):
            b.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]")


def build():
    d = Dungeon(SID, THEME, 2027)
    d.ground()
    d.underground()
    smithy(d)
    rocks(d)
    d.path(30, 34, 67, N_Z - 1)
    d.avenue(70, N_Z - 2, (28, 36), "minecraft:stone_bricks", step=5, h=3, cap="minecraft:lantern[hanging=false,waterlogged=false]")
    d.ruin_wall(16, 40, 16, 66, 3)
    d.ruin_wall(48, 40, 48, 66, 3)
    d.scatter(["minecraft:fern", "minecraft:dead_bush", "minecraft:short_grass"], 50, keep_out=((22, 50, 42, N_Z - 1),))
    d.entities("cursed_smith", ["gifter", "ronin"], "gifter")
    return d.b
