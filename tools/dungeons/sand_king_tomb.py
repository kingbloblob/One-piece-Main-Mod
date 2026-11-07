"""The Sand King's Tomb (Alabasta, Paradise): a stepped sandstone pyramid in the desert with obelisks and fallen
walls; under it the tomb of an ancient king of the Nefertari line's rivals, robbed and re-guarded by a band of
tomb raiders. Mini-boss: Tomb Warden Hassad, who fights with a heavy khopesh and calls sandstorms.
Signature: the pyramid's gold capstone, blue-and-gold bands, a sunken arena with an oasis channel each side."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgkit import Dungeon, AIR, stairs, slab, wall_of, N_X, N_Z  # noqa: E402

SID = "sand_king_tomb"
TITLE = "The Sand King's Tomb"
CUTS = [-13]
BIOMES = ["onepiece:alabasta"]
SS = "minecraft:sandstone"

THEME = dict(
    rock=[("minecraft:sandstone", 5), ("minecraft:smooth_sandstone", 2), ("minecraft:terracotta", 1)],
    subsoil=[("minecraft:sandstone", 3), ("minecraft:smooth_sandstone", 1)],
    surface=[("minecraft:sand", 8), ("minecraft:smooth_sandstone", 1), ("minecraft:red_sand", 1)],
    path=[("minecraft:smooth_sandstone", 3), ("minecraft:cut_sandstone", 2), ("minecraft:sandstone", 1)],
    ruin=[("minecraft:cut_sandstone", 3), ("minecraft:sandstone", 2), ("minecraft:chiseled_sandstone", 1)],
    ruin_slab="minecraft:sandstone_slab",
    wall=[("minecraft:cut_sandstone", 5), ("minecraft:sandstone", 3), ("minecraft:chiseled_sandstone", 1)],
    floor=[("minecraft:smooth_sandstone", 5), ("minecraft:cut_sandstone", 2)],
    ceil=[("minecraft:smooth_sandstone", 1)],
    base="minecraft:orange_terracotta",
    pillar="minecraft:cut_sandstone", pillar_base="minecraft:chiseled_sandstone",
    lamp="minecraft:shroomlight", hang="minecraft:lantern[hanging=true,waterlogged=false]",
    stair="minecraft:sandstone_stairs", carpet="orange", cloth="blue", bed="yellow", wood="acacia",
    urn="minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]",
    pit=[("minecraft:magma_block", 1)],
    brazier_base="minecraft:chiseled_sandstone", brazier="minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]",
    channel="minecraft:water[level=0]", rail=wall_of("minecraft:sandstone_wall"),
    accent="minecraft:gold_block", dais=[("minecraft:cut_sandstone", 3), ("minecraft:smooth_sandstone", 1)],
    throne="minecraft:smooth_sandstone_stairs", throne_side="minecraft:chiseled_sandstone",
    throne_back=[("minecraft:gold_block", 1), ("minecraft:chiseled_sandstone", 1)], altar_top="minecraft:chiseled_sandstone",
)


def pyramid(d):
    b, rnd = d.b, d.rnd
    x0, z0, x1, z1 = 22, 50, 42, 66
    for t in range(9):
        y = 1 + t
        for x in range(x0 + t, x1 - t + 1):
            for z in range(z0 + t, z1 - t + 1):
                edge = x in (x0 + t, x1 - t) or z in (z0 + t, z1 - t)
                if edge:
                    s = "minecraft:blue_terracotta" if t == 3 else "minecraft:orange_terracotta" if t == 6 else \
                        rnd.choice(("minecraft:cut_sandstone", "minecraft:sandstone", "minecraft:smooth_sandstone"))
                else:
                    s = SS
                b.set(x, y, z, s)
        # step lip: slabs on each tier's outer ring so the faces read as steps, not a cube
        if t < 8:
            for x in range(x0 + t, x1 - t + 1):
                for z in (z0 + t, z1 - t):
                    if b.get(x, y + 1, z) is None:
                        b.set(x, y + 1, z, slab("minecraft:smooth_sandstone_slab"))
            for z in range(z0 + t, z1 - t + 1):
                for x in (x0 + t, x1 - t):
                    if b.get(x, y + 1, z) is None:
                        b.set(x, y + 1, z, slab("minecraft:smooth_sandstone_slab"))
    b.set(32, 10, 58, "minecraft:gold_block")
    b.set(32, 11, 58, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the way in: a corridor from the south face to the stair head, a little hall round it
    d.air(30, 1, 59, 32, 3, 66)
    d.air(28, 1, 55, 36, 4, 60)
    d.mixbox(28, 0, 55, 36, 0, 60, THEME["floor"])
    d.air(30, 0, 56, 32, 0, 58)                          # stair head (the treads start at y -1)
    for z in (55, 60):
        for x in (28, 36):
            b.set(x, 1, z, "minecraft:chiseled_sandstone"); b.set(x, 2, z, "minecraft:cut_sandstone"); b.set(x, 3, z, "minecraft:chiseled_sandstone")
    b.set(28, 3, 57, "minecraft:shroomlight"); b.set(36, 3, 57, "minecraft:shroomlight")
    b.set(27, 3, 57, "minecraft:sandstone"); b.set(37, 3, 57, "minecraft:sandstone")
    for x in range(29, 36):
        b.set(x, 4, 55, "minecraft:blue_terracotta")
    # portal on the south face: chiseled jambs, a gold-banded lintel, two guardian statues
    for y in range(1, 5):
        b.set(29, y, 66, "minecraft:chiseled_sandstone"); b.set(33, y, 66, "minecraft:chiseled_sandstone")
    for x in range(29, 34):
        b.set(x, 4, 66, "minecraft:gold_block" if x == 31 else "minecraft:chiseled_sandstone")
        b.set(x, 5, 66, stairs("minecraft:sandstone_stairs", "north"))
    d.air(30, 1, 66, 32, 3, 66)
    for x in (26, 38):
        b.set(x, 1, 67, "minecraft:chiseled_sandstone")
        b.set(x, 2, 67, "minecraft:cut_sandstone")
        b.set(x, 3, 67, "minecraft:cut_sandstone")
        b.set(x, 4, 67, "minecraft:chiseled_sandstone")
        b.set(x, 5, 67, stairs("minecraft:sandstone_stairs", "south"))
        b.set(x + (1 if x < 32 else -1), 3, 67, slab("minecraft:sandstone_slab", "top"))


def obelisk(d, x, z, h=11):
    b = d.b
    b.box(x - 1, 1, z - 1, x + 1, 1, z + 1, "minecraft:chiseled_sandstone")
    for y in range(2, h):
        b.set(x, y, z, "minecraft:cut_sandstone" if y % 3 else "minecraft:chiseled_sandstone")
    b.set(x, h, z, "minecraft:gold_block")
    b.set(x, h + 1, z, "minecraft:end_rod[facing=up]")


def build():
    d = Dungeon(SID, THEME, 2011)
    d.ground()
    d.underground()
    pyramid(d)
    d.path(29, 33, 67, N_Z - 1)
    # the processional way: sandstone columns from the south edge, a sphinx-like guardian pair at the far end
    d.avenue(70, N_Z - 2, (27, 35), "minecraft:cut_sandstone", step=3, h=5, cap="minecraft:chiseled_sandstone")
    for x0 in (12, 46):
        d.mixbox(x0, 1, 22, x0 + 6, 1, 30, THEME["ruin"])          # collapsed side temples: a plinth, broken columns
        for (x, z) in ((x0, 22), (x0 + 6, 22), (x0, 30), (x0 + 6, 30), (x0 + 3, 22), (x0 + 3, 30)):
            for y in range(2, 2 + d.rnd.randint(1, 5)):
                d.b.set(x, y, z, "minecraft:cut_sandstone")
        d.b.set(x0 + 3, 2, 26, THEME["urn"])
    for x, z in ((18, 60), (46, 60), (18, 44), (46, 44)):
        obelisk(d, x, z)
    d.ruin_wall(8, 46, 8, 64, 3)
    d.ruin_wall(56, 46, 56, 64, 3)
    d.ruin_wall(10, 40, 20, 40, 2)
    d.ruin_wall(44, 40, 54, 40, 2)
    for (x, z) in ((6, 20), (54, 14), (12, 8), (58, 30), (4, 52)):
        d.b.palm(x, 1, z, 7) if hasattr(d.b, "palm") else None
    d.scatter(["minecraft:dead_bush", "minecraft:cactus", "minecraft:short_dry_grass", "minecraft:dead_bush"], 70,
              keep_out=((20, 48, 44, N_Z - 1),))
    d.scatter([THEME["urn"], "minecraft:sandstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]",
               "minecraft:bone_block[axis=x]"], 14, keep_out=((20, 48, 44, N_Z - 1),))
    d.entities("tomb_warden", ["tomb_guard", "baroque_agent"], "tomb_guard")
    return d.b
