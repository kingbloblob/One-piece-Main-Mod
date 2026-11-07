"""Impel Down Level 6, Eternal Hell, v3 (2026-10-30 audit: the v1 cavern was a small rock shell). Redone with the
Minecraft Builder skill: the secret bottom level the World Government denies exists. A black, silent obsidian cave
120 across and 40 high, almost dark: four sides of THREE tiers of seastone cells for the criminals erased from history
(Shiryu, Catarina Devon, Sanjuan Wolf...), railed walkways, soul-fire watch posts at the corners; in the middle the
great SEALED VAULT, a seastone cube on a stepped plinth with iron doors and chains, a single chained prisoner inside;
the execution chamber with its iron chair, the records room of erased names and the sealed shaft above.
Canvas y 0 = the cavern floor, world y 33."""
import math

import numpy as np

from mcb.kit import BigBuild, set_if_air, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import impel_kit as K
from mcb.blazing_hell_furnace import block_house

SID = "eternal_hell_vault"
TITLE = "Impel Down Level 6: Eternal Hell"
CUTS = [3, 9, 18]
TILER = dict(terrain="none", sky_y=33)

N = 128
CX, CZ = 64, 64
RX, RZ, H = 58, 58, 40
ROCK = ("minecraft:obsidian", "minecraft:blackstone", "minecraft:obsidian", "minecraft:crying_obsidian", "minecraft:deepslate_tiles")
FLOOR = ("minecraft:polished_deepslate", "minecraft:deepslate_tiles", "minecraft:polished_blackstone")
SEA = "onepiece:seastone_bricks"
SEAB = "onepiece:seastone_block"
BARS = "onepiece:prison_bars"
RAIL = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
HALF = 38
FH = 6


def vault(bb):
    """The sealed vault: a stepped obsidian plinth, a 17-wide seastone cube 13 high with iron doors and chains
    crossing its faces, a chained cell inside lit by one soul lantern."""
    for i in range(3):
        bb.fill(CX - 13 + i * 2, i, CZ - 13 + i * 2, CX + 13 - i * 2, i, CZ + 13 - i * 2, "minecraft:polished_blackstone_bricks")
    x1, z1, x2, z2 = CX - 8, CZ - 8, CX + 8, CZ + 8
    bb.fill(x1, 3, z1, x2, 16, z2, SEA)
    bb.fill(x1 + 1, 3, z1 + 1, x2 - 1, 15, z2 - 1, "minecraft:air")
    bb.fill(x1 - 1, 16, z1 - 1, x2 + 1, 16, z2 + 1, SEAB)
    for x in range(x1, x2 + 1, 4):                       # chains crossing the faces
        for y in range(4, 16):
            bb.set(x, y, z1 - 1, "minecraft:iron_chain[axis=y]"); bb.set(x, y, z2 + 1, "minecraft:iron_chain[axis=y]")
    bb.fill(CX - 1, 3, z2, CX + 1, 3, z2, "minecraft:air")
    bb.set(CX - 1, 3, z2, "minecraft:iron_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
    bb.set(CX - 1, 4, z2, "minecraft:iron_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
    bb.set(CX + 1, 3, z2, "minecraft:iron_door[facing=north,half=lower,hinge=right,open=false,powered=false]")
    bb.set(CX + 1, 4, z2, "minecraft:iron_door[facing=north,half=upper,hinge=right,open=false,powered=false]")
    bb.set(CX, 3, z2, SEA); bb.set(CX, 4, z2, SEA)
    bb.fill(CX - 2, 3, z2 + 1, CX + 2, 3, z2 + 3, "minecraft:polished_blackstone_bricks")
    # inside: the chained cell
    bb.fill(CX - 3, 3, CZ - 3, CX + 3, 3, CZ + 3, "minecraft:black_carpet")
    for (dx, dz) in ((-2, -2), (2, -2)):
        bb.fill(CX + dx, 4, CZ + dz, CX + dx, 15, CZ + dz, "minecraft:iron_chain[axis=y]")
    bb.set(CX, 3, CZ - 3, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
    bb.set(CX, 15, CZ, "minecraft:soul_lantern[hanging=true,waterlogged=false]")


def execution(bb, x1, z1, x2, z2):
    """The execution chamber: a bare seastone room with the iron chair on a dais and drains in the floor."""
    block_house(bb, x1, z1, x2, z2, 1, SEA, "minecraft:polished_deepslate", SEAB, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]",
                ("storeroom",), "dark_oak", "west", 6010)
    mx, mz = (x1 + x2) // 2, (z1 + z2) // 2
    bb.fill(mx - 1, 1, mz - 1, mx + 1, 1, mz + 1, "minecraft:polished_blackstone")
    bb.set(mx, 2, mz, "minecraft:polished_blackstone_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    bb.set(mx + 1, 2, mz, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    bb.set(mx + 1, 3, mz, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    bb.set(mx, 5, mz, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    bb.set(mx - 3, 0, mz, "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")


def watch_post(bb, x, z):
    """A soul-fire watch post: a squat seastone tower with a soul campfire brazier on top."""
    bb.fill(x - 2, 0, z - 2, x + 2, 8, z + 2, SEA)
    bb.fill(x - 1, 1, z - 1, x + 1, 7, z + 1, "minecraft:air")
    bb.fill(x - 3, 8, z - 3, x + 3, 8, z + 3, "minecraft:polished_blackstone_bricks")
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        bb.set(x + dx, 9, z + dz, "minecraft:polished_blackstone_brick_wall")
    bb.set(x, 9, z, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bb.fill(x, 1, z - 1, x, 7, z - 1, "minecraft:ladder[facing=south,waterlogged=false]")
    bb.fill(x, 1, z + 2, x, 2, z + 2, "minecraft:air")


def design():
    bb = BigBuild(seed=600, y_min=-6, y_max=H + 8)
    inside = K.cavern(bb, CX, CZ, RX, RZ, H, ROCK, 6000, FLOOR, thick=4)
    K.gallery(bb, CX, CZ, HALF, 7, 3, FH, SEA, BARS, "minecraft:polished_blackstone_bricks", RAIL, "dark_oak", 6020,
              light="minecraft:soul_lantern[hanging=true,waterlogged=false]")
    vault(bb)
    c1, c2 = HALF - 13, HALF - 4
    execution(bb, CX + c1, CZ + c1, CX + c2, CZ + c2)
    block_house(bb, CX - c2, CZ + c1, CX - c1, CZ + c2, 2, SEA, "minecraft:dark_oak_planks", SEAB, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]",
                ("library", "office"), "dark_oak", "east", 6030)
    K.shaft(bb, CX - (c1 + c2) // 2, CZ - (c1 + c2) // 2, H - 2, SEA)
    watch_post(bb, CX + (c1 + c2) // 2, CZ - (c1 + c2) // 2)
    for a in range(0, 360, 45):          # soul-fire braziers round the vault plinth
        t = math.radians(a + 22)
        lamp_post(bb, round(CX + 17 * math.cos(t)), 1, round(CZ + 17 * math.sin(t)), post="minecraft:polished_blackstone_wall", h=2,
                  light="minecraft:soul_lantern[hanging=false,waterlogged=false]")
    K.ceiling_lights(bb, CX, CZ, RX - 8, inside, "minecraft:crying_obsidian", step=13, seed=601)
    K.floor_lights(bb, 4, 4, N - 5, N - 5, (1, 7, 13))
    return bb


def build():
    bb = design()
    b = to_canvas(bb)
    b.chest(CX + 2, 3, CZ - 2, "impel_down", "south")
    b.chest(CX - HALF + 6, 1, CZ + HALF - 6, "impel_down", "east")
    b.guards("warden_jailer", ((CX - 20, CZ), (CX + 20, CZ)))
    b.guards("jailer", ((CX, CZ - 24), (CX, CZ + 24), (CX - 26, CZ - 26), (CX + 26, CZ + 26)))
    return b, 0
