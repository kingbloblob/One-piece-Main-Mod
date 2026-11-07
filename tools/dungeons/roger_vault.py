"""Roger's Hidden Vault (God Valley / Hachinosu, New World): a ruined stone fort on a rocky rise with the wreck of
an old galleon run aground beside it; below it the vault where the Roger Pirates stored a share of their plunder,
and the sword Roger carried, "Ace". The last of the old Rocks Pirates found it first and won't let go.
Mini-boss: Gorvak the Undying, a Haki brute of the Rocks Pirates who calls his crew and goes berserk.
Signature: the fort's crenellated gatehouse with the Roger flag flying, the beached wreck, cannons on the walls."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgkit import Dungeon, AIR, stairs, slab, wall_of, fence, N_X, N_Z  # noqa: E402

SID = "roger_vault"
TITLE = "Roger's Hidden Vault"
CUTS = [-13]
BIOMES = ["onepiece:god_valley", "onepiece:hachinosu"]

THEME = dict(
    rock=[("minecraft:stone", 4), ("minecraft:andesite", 2), ("minecraft:cobblestone", 1)],
    subsoil=[("minecraft:dirt", 3), ("minecraft:coarse_dirt", 1), ("minecraft:stone", 1)],
    surface=[("minecraft:grass_block", 5), ("minecraft:coarse_dirt", 2), ("minecraft:stone", 1), ("minecraft:moss_block", 1)],
    path=[("minecraft:cobblestone", 2), ("minecraft:stone_bricks", 2), ("minecraft:gravel", 1)],
    ruin=[("minecraft:stone_bricks", 2), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1)],
    ruin_slab="minecraft:stone_brick_slab",
    wall=[("minecraft:stone_bricks", 4), ("minecraft:cracked_stone_bricks", 2), ("minecraft:polished_andesite", 1)],
    floor=[("minecraft:spruce_planks", 2), ("minecraft:stone_bricks", 2), ("minecraft:polished_andesite", 1)],
    ceil=[("minecraft:spruce_planks", 1)],
    base="minecraft:polished_deepslate",
    pillar="minecraft:spruce_log[axis=y]", pillar_base="minecraft:chiseled_stone_bricks",
    lamp="minecraft:sea_lantern", hang="minecraft:lantern[hanging=true,waterlogged=false]",
    stair="minecraft:stone_brick_stairs", carpet="red", cloth="black", bed="red", wood="spruce",
    urn="minecraft:barrel[facing=up,open=false]",
    pit=[("minecraft:magma_block", 1)],
    brazier_base="minecraft:chiseled_stone_bricks", brazier="minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]",
    channel="minecraft:lava[level=0]", rail=wall_of("minecraft:stone_brick_wall"),
    accent="minecraft:gold_block", dais=[("minecraft:gold_block", 1), ("minecraft:chiseled_stone_bricks", 2)],
    throne="minecraft:spruce_stairs", throne_side="minecraft:gold_block",
    throne_back=[("minecraft:gold_block", 1), ("minecraft:raw_gold_block", 1)], altar_top="minecraft:chiseled_stone_bricks",
)


def fort(d):
    b, rnd = d.b, d.rnd
    x0, z0, x1, z1 = 18, 46, 46, 68
    for x in range(x0, x1 + 1):                          # curtain wall with crenels
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                h = 6 if rnd.random() > 0.15 else rnd.randint(2, 4)
                for y in range(1, h + 1):
                    b.set(x, y, z, d.rnd.choice(("minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks")))
                if h == 6 and (x + z) % 2 == 0:
                    b.set(x, 7, z, "minecraft:stone_bricks")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):   # corner towers
        b.cyl(x, z, 3, 1, 10, "minecraft:stone_bricks", hollow=True)
        for k in range(0, 360, 45):
            import math
            b.set(x + round(3 * math.cos(math.radians(k))), 11, z + round(3 * math.sin(math.radians(k))), "minecraft:stone_bricks")
    # gatehouse on the south wall
    d.mixbox(27, 1, z1 - 1, 37, 10, z1 + 1, THEME["ruin"])
    d.air(30, 1, z1 - 1, 34, 5, z1 + 1)
    for x in range(30, 35):
        b.set(x, 5, z1 + 1, "minecraft:iron_bars[east=true,north=false,south=false,waterlogged=false,west=true]")
    for x in range(27, 38, 2):
        b.set(x, 11, z1 + 1, "minecraft:stone_bricks")
    b.flag(32, 11, z1, h=9) if hasattr(b, "flag") else None
    # the keep over the stair: a stone hall with a timber roof
    d.mixbox(26, 1, 52, 38, 6, 62, THEME["wall"])
    d.air(27, 1, 53, 37, 5, 61)
    d.mixbox(27, 0, 53, 37, 0, 61, THEME["floor"])
    d.air(30, 0, 56, 32, 0, 58)
    d.air(31, 1, 62, 33, 4, 62)
    b.gable_roof(26, 52, 38, 62, 7, "minecraft:spruce_stairs", "minecraft:spruce_planks", gable_wall="minecraft:stone_bricks")
    b.set(32, 5, 59, "minecraft:lantern[hanging=true,waterlogged=false]")
    # cannons on the wall walk and a yard of crates
    for (x, z) in ((22, z1 - 1), (42, z1 - 1), (x0 + 1, 56), (x1 - 1, 56)):
        b.set(x, 7, z, "minecraft:anvil[facing=north]" if z == z1 - 1 else "minecraft:anvil[facing=east]")
    for (x, z) in ((21, 50), (22, 50), (21, 51), (43, 64), (42, 64)):
        b.set(x, 1, z, "minecraft:barrel[facing=up,open=false]")
    b.set(43, 1, 50, "minecraft:target")


def wreck(d):
    """An old galleon on its side west of the fort: a hull of planks with a broken mast."""
    b = d.b
    if hasattr(b, "ship"):
        b.ship(2, 0, 8, 26, 9, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks", masts=((10, 12),), sail="minecraft:white_wool")
    for x in range(4, 26, 3):                             # sand drifted round the hull
        b.set(x, 1, 7, "minecraft:coarse_dirt")


def build():
    d = Dungeon(SID, THEME, 2029)
    d.ground()
    d.underground()
    fort(d)
    wreck(d)
    d.path(30, 34, 69, N_Z - 1)
    d.scatter(["minecraft:short_grass", "minecraft:fern", "minecraft:poppy", "minecraft:dandelion"], 70,
              keep_out=((16, 44, 48, N_Z - 1), (0, 4, 30, 20)))
    d.entities("rocks_captain", ["rocks_pirate"], "rocks_pirate")
    return d.b
