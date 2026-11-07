"""Seastone Deep Mine v1 (2026-11-05, thread "Expand ores and underground mining"), designed with the Minecraft
Builder skill: an old World Government seastone quarry run like Impel Down. Convicts were sent down to cut the
kairoseki that lines the great prison, level by level, deeper and hotter, with jailers on every floor.

Brief. 72 x 72, three stacked caverns joined by one central pit (5x5, ladder on its north wall, a timber head frame
with winding chains on top). Palette: seastone bricks + seastone block (walls, cells), deepslate / tuff / sea prism
stone (rock), dark oak (timbering, head frame), iron bars and prison bars, rails. Silhouette inside the cave: the
tall head frame over the pit and the stepped levels you see down the shaft.
- Level 1, Quarry Gate (canvas y 0, world -6): the head frame, a two-storey jailers' block house, the ore yard
  (Ore Carts on rails, a Mining Drill facing the rock, ore heaps, barrels, supply chest), two timbered ore drifts
  east and west with veins in their walls, and a rough tunnel out to the caves north.
- Level 2, Convict Galleries (y -16): two tiers of barred cells round a square hall where the miners slept, the mess
  block house, ore-studded walls with Sea Prism Veins.
- Level 3, Abyss (y -32): a hot, dim cave of Abyss Stone and magma, dense Sea Prism Veins, and the VAULT: an Abyss
  Stone Brick room whose doorway is sealed with Abyss Stone, so only a Sea Prism pickaxe (or drill bit) gets in.
Signature details: the head frame and chains; seeing all three levels down the pit; the sealed Abyss vault.
Lessons applied: lair = compound with 4+ zones and 3 levels, 2+ furnished interiors (block houses, cells); walls
studded (not flat rock); lights hidden in the floors/ceiling."""
import numpy as np

from mcb.kit import BigBuild, lamp_post
from mcb.bridge import to_canvas
from mcb import impel_kit as K
from mcb.blazing_hell_furnace import block_house

SID = "seastone_deep_mine"
TITLE = "Seastone Deep Mine"
CUTS = [3, -13, -29]
TILER = dict(terrain="none", sky_y=-6)

N = 72
CX, CZ = 36, 36
L2, L3 = -16, -32                     # floor heights of the lower levels (canvas y)
SEA = "onepiece:seastone_bricks"
SEAB = "onepiece:seastone_block"
BARS = "onepiece:prison_bars"
RAIL_BARS = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
LOG = "minecraft:dark_oak_log[axis=y]"
PLANK = "minecraft:dark_oak_planks"
FENCE = "minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
ROCK1 = ("minecraft:deepslate", "minecraft:tuff", "minecraft:cobbled_deepslate", "onepiece:sea_prism_stone")
ROCK2 = ("minecraft:deepslate", "onepiece:sea_prism_stone", "minecraft:tuff", "minecraft:deepslate_tiles")
ROCK3 = ("onepiece:abyss_stone", "minecraft:deepslate", "onepiece:abyss_stone", "minecraft:blackstone")
FLOOR1 = ("minecraft:gravel", "minecraft:cobbled_deepslate", "minecraft:tuff", "minecraft:coarse_dirt")
FLOOR2 = ("minecraft:polished_deepslate", "minecraft:cobbled_deepslate", "minecraft:deepslate_tiles")
FLOOR3 = ("minecraft:magma_block", "minecraft:blackstone", "onepiece:abyss_stone", "minecraft:basalt[axis=y]")
# Ores studded into each level's walls: (block, chance per exposed rock face)
ORES1 = (("onepiece:seastone_ore", 0.035), ("minecraft:iron_ore", 0.02), ("minecraft:coal_ore", 0.03))
ORES2 = (("onepiece:deepslate_seastone_ore", 0.05), ("onepiece:sea_prism_vein", 0.02), ("minecraft:deepslate_iron_ore", 0.015))
ORES3 = (("onepiece:sea_prism_vein", 0.06), ("onepiece:deepslate_seastone_ore", 0.03), ("onepiece:deepslate_kokuto_ore", 0.006))


def pit(bb, top, bottom):
    """The shaft down to the level below: a 7x7 seastone tube from `bottom` (the lower floor) to `top` + 1 (a railing
    on this level), a 5x5 hole, a ladder on its north wall and a gap in the railing over the ladder."""
    bb.fill(CX - 3, bottom, CZ - 3, CX + 3, top + 1, CZ + 3, SEA)
    bb.fill(CX - 2, bottom + 1, CZ - 2, CX + 2, top + 2, CZ + 2, "minecraft:air")
    bb.fill(CX, bottom + 1, CZ - 2, CX, top, CZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    bb.set(CX, top + 1, CZ - 3, "minecraft:air")
    # the tube opens on the lower level: a doorway 3 wide, 3 high on its south side
    bb.fill(CX - 1, bottom + 1, CZ + 3, CX + 1, bottom + 3, CZ + 3, "minecraft:air")


def head_frame(bb):
    """Timber head frame over the pit: four posts, cross beams, a winding drum, chains hanging into the shaft."""
    for dx, dz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        bb.fill(CX + dx, 2, CZ + dz, CX + dx, 10, CZ + dz, LOG)
    for y in (6, 10):
        bb.fill(CX - 3, y, CZ - 3, CX + 3, y, CZ - 3, "minecraft:dark_oak_log[axis=x]")
        bb.fill(CX - 3, y, CZ + 3, CX + 3, y, CZ + 3, "minecraft:dark_oak_log[axis=x]")
        bb.fill(CX - 3, y, CZ - 2, CX - 3, y, CZ + 2, "minecraft:dark_oak_log[axis=z]")
        bb.fill(CX + 3, y, CZ - 2, CX + 3, y, CZ + 2, "minecraft:dark_oak_log[axis=z]")
    bb.fill(CX - 2, 11, CZ, CX + 2, 11, CZ, "minecraft:stripped_dark_oak_log[axis=x]")    # winding drum
    bb.set(CX - 3, 11, CZ, "minecraft:dark_oak_fence[east=true,north=false,south=false,waterlogged=false,west=false]")
    bb.set(CX + 3, 11, CZ, "minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=true]")
    for x in (CX - 1, CX + 1):
        bb.fill(x, L2 + 4, CZ, x, 10, CZ, "minecraft:iron_chain[axis=y]")
    bb.set(CX - 1, L2 + 3, CZ, "minecraft:lantern[hanging=true,waterlogged=false]")
    bb.set(CX + 1, L2 + 3, CZ, "minecraft:lantern[hanging=true,waterlogged=false]")


def drift(bb, x1, x2, z, y, ores_wall=SEAB):
    """A timbered ore drift along x: 3 wide, 4 high, rails down the middle, a timber set every 4 blocks."""
    lo, hi = min(x1, x2), max(x1, x2)
    bb.fill(lo, y, z - 2, hi, y + 5, z + 2, "minecraft:tuff")
    bb.fill(lo, y, z - 1, hi, y, z + 1, "minecraft:gravel")
    bb.fill(lo, y + 1, z - 1, hi, y + 4, z + 1, "minecraft:air")
    bb.fill(lo, y + 1, z, hi, y + 1, z, "minecraft:rail[shape=east_west,waterlogged=false]")
    for x in range(lo + 2, hi, 4):
        bb.fill(x, y + 1, z - 1, x, y + 3, z - 1, FENCE)
        bb.fill(x, y + 1, z + 1, x, y + 3, z + 1, FENCE)
        bb.fill(x, y + 4, z - 1, x, y + 4, z + 1, PLANK)
        if (x // 4) % 2:
            bb.set(x, y + 3, z, "minecraft:lantern[hanging=true,waterlogged=false]")


def ore_yard(bb):
    """South-west of the pit: carts on a rail spur, ore heaps, the drill, barrels and the supply chest."""
    z = CZ + 9
    bb.fill(CX - 20, 1, z, CX - 4, 1, z, "minecraft:rail[shape=east_west,waterlogged=false]")
    for x in (CX - 18, CX - 13, CX - 8):
        bb.set(x, 1, z + 2, "onepiece:ore_cart[facing=east]")
    for (x, zz, r) in ((CX - 18, CZ + 15, 2), (CX - 11, CZ + 16, 3)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                h = r - max(abs(dx), abs(dz))
                for y in range(1, h + 2):
                    blk = ("minecraft:cobbled_deepslate", "minecraft:gravel", "onepiece:sea_prism_stone", "minecraft:tuff")[(dx * 3 + dz + y) % 4]
                    bb.set(x + dx, y, zz + dz, blk)
    bb.set(CX - 22, 1, CZ + 4, "onepiece:mining_drill[facing=west,lit=false]")
    for (x, zz) in ((CX - 22, CZ + 2), (CX - 22, CZ + 6), (CX - 21, CZ + 6)):
        bb.set(x, 1, zz, "minecraft:barrel[facing=up,open=false]")
    lamp_post(bb, CX - 15, 1, CZ + 5)
    lamp_post(bb, CX - 7, 1, CZ + 13)


def level1():
    bb = BigBuild(seed=1105, y_min=-18, y_max=24)
    inside = K.cavern(bb, CX, CZ, 30, 30, 13, ROCK1, 11050, FLOOR1, thick=4)
    pit(bb, 0, L2)
    head_frame(bb)
    block_house(bb, CX + 9, CZ - 22, CX + 19, CZ - 12, 2, SEA, PLANK, SEAB,
                "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]", ("office", "bedroom"),
                "dark_oak", "south", 11060)
    ore_yard(bb)
    drift(bb, CX + 26, CX + 34, CZ + 2, 0)
    drift(bb, CX - 26, CX - 34, CZ - 4, 0)
    # rails from the pit to both drifts
    bb.fill(CX + 4, 1, CZ + 2, CX + 26, 1, CZ + 2, "minecraft:rail[shape=east_west,waterlogged=false]")
    bb.fill(CX - 26, 1, CZ - 4, CX - 4, 1, CZ - 4, "minecraft:rail[shape=east_west,waterlogged=false]")
    # rough tunnel north out to the caves
    for z in range(CZ - 28, -1, -1):
        w = 1 + (z % 3 == 0)
        bb.fill(CX - 4 - w, 1, z, CX - 4 + w, 4, z, "minecraft:air")
        bb.fill(CX - 4 - w, 0, z, CX - 4 + w, 0, z, "minecraft:cobbled_deepslate")
    K.ceiling_lights(bb, CX, CZ, 24, inside, "minecraft:glowstone", step=11, seed=1107)
    K.floor_lights(bb, 6, 6, N - 7, N - 7, (1,), step=9)
    return bb


def level2():
    bb = BigBuild(seed=1205, y_min=-18, y_max=22)
    inside = K.cavern(bb, CX, CZ, 27, 27, 11, ROCK2, 12050, FLOOR2, thick=4)
    K.gallery(bb, CX, CZ, 14, 6, 2, 5, SEA, BARS, "minecraft:polished_deepslate", RAIL_BARS, "dark_oak", 12060,
              light="minecraft:lantern[hanging=true,waterlogged=false]", gaps=[("south", -4, 4)])
    pit(bb, 0, L3 - L2)
    block_house(bb, CX - 10, CZ - 10, CX - 4, CZ - 4, 1, SEA, PLANK, SEAB,
                "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]", ("kitchen",),
                "dark_oak", "east", 12070)
    K.chains(bb, ((CX - 9, CZ + 8), (CX + 9, CZ - 8), (CX + 9, CZ + 9)), 3, inside)
    K.ceiling_lights(bb, CX, CZ, 20, inside, "minecraft:shroomlight", step=10, seed=1207)
    K.floor_lights(bb, 6, 6, N - 7, N - 7, (1, 6), step=8)
    return bb


def vault(bb):
    """The Abyss vault east of the pit: Abyss Stone Bricks 11x9, 6 high, its only doorway sealed with Abyss Stone."""
    x1, z1, x2, z2 = CX + 9, CZ - 5, CX + 19, CZ + 5
    bb.fill(x1, 0, z1, x2, 6, z2, "onepiece:abyss_stone_bricks")
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, 5, z2 - 1, "minecraft:air")
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:polished_blackstone_bricks")
    bb.fill(x1, 1, CZ - 1, x1, 3, CZ + 1, "onepiece:abyss_stone")          # the seal
    for dz in (-2, 2):
        bb.set(x1 - 1, 1, CZ + dz, "minecraft:polished_blackstone_wall")
        bb.set(x1 - 1, 2, CZ + dz, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    bb.set(CX + 14, 5, CZ, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    for (x, z) in ((x2 - 1, z1 + 1), (x2 - 1, z2 - 1)):
        bb.set(x, 1, z, "onepiece:sea_prism_crystal")


def level3():
    bb = BigBuild(seed=1305, y_min=-6, y_max=22)
    inside = K.cavern(bb, CX, CZ, 23, 23, 10, ROCK3, 13050, FLOOR3, thick=5, drips=None)
    vault(bb)
    # the warden's post west of the pit: a low seastone guard room
    block_house(bb, CX - 16, CZ - 5, CX - 8, CZ + 3, 1, SEA, PLANK, SEAB,
                "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]", ("storeroom",),
                "dark_oak", "east", 13060)
    K.chains(bb, ((CX - 6, CZ + 10), (CX + 6, CZ + 12), (CX, CZ - 12)), 1, inside)
    K.ceiling_lights(bb, CX, CZ, 18, inside, "minecraft:shroomlight", step=12, seed=1307)
    K.floor_lights(bb, 6, 6, N - 7, N - 7, (1,), step=9, level=9)
    return bb


def stud(b, ylo, yhi, ores, rock, seed):
    """Swap rock that faces the cave air for ore, so the walls show veins (only blocks in `rock`, never the build)."""
    rng = np.random.default_rng(seed)
    air = {"minecraft:air", "minecraft:cave_air"}
    swaps = {}
    for (x, y, z), s in b.blocks.items():
        if not (ylo <= y <= yhi) or s not in rock:
            continue
        if any(b.blocks.get((x + dx, y + dy, z + dz)) in air for dx, dy, dz in
               ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            r = rng.random()
            for ore, p in ores:
                if r < p:
                    swaps[(x, y, z)] = ore
                    break
                r -= p
    b.blocks.update(swaps)
    return len(swaps)


def build():
    b = to_canvas(level3(), dy=L3)
    to_canvas(level2(), b, dy=L2)
    to_canvas(level1(), b)
    stud(b, -4, 18, ORES1, set(ROCK1), 1)
    stud(b, L2 - 4, L2 + 14, ORES2, set(ROCK2), 2)
    stud(b, L3 - 5, L3 + 14, ORES3, set(ROCK3), 3)
    b.chest(CX - 21, 1, CZ + 3, "deep_mine", "east")
    b.chest(CX + 13, 1, CZ - 13, "deep_mine", "south")
    b.chest(CX - 4, L2 + 1, CZ + 11, "deep_mine", "north")
    b.chest(CX + 17, L3 + 1, CZ, "deep_mine_vault", "west")
    b.chest(CX + 14, L3 + 1, CZ - 3, "deep_mine_vault", "south")
    b.guards("jailer", ((CX - 8, CZ - 8), (CX + 10, CZ + 8), (CX + 30, CZ + 2)))
    b.guards("jailer", ((CX - 10, CZ + 4), (CX + 8, CZ - 6)), y=L2 + 1)
    b.guards("warden_jailer", ((CX + 6, CZ - 6), (CX - 6, CZ + 8)), y=L3 + 1)
    return b, 0
