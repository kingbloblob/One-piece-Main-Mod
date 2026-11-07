"""Secret Marine Bunker v2, redesigned with the Minecraft Builder skill: a hidden World Government base dug into the
deep rock (the Navy's off-the-books facilities: Punk Hazard's G-5 labs, Impel Down's steel corridors, the Enies
Lobby passages; concrete, steel ribs, the gull crest on the blast doors).

Silhouette first (inside a cave you see sections, not an outline): a long, tall vaulted concrete main hall with
riveted steel ribs every 4 blocks and a strip of lamps along the crown, huge two-leaf blast doors at both ends with
the Marine gull painted in blue, a two-storey command atrium in the middle with a gallery and a wall of Den Den
Mushi receivers round a big chart table.

Off the hall: the commander's office (on the gallery), barracks with bunks and lockers, the mess hall and galley,
the armory with gun racks and cannons, a row of seastone cells (sea prism stone and bars) with a guard post, the
stores and a generator room with pipes, a minecart rail along the hall to the depot; rough tunnels from both blast
doors out into the caves. Canvas y 0 = the hall floor (world y -22). 104 x 68. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady, wing_floor, seed_of
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "marine_bunker"
TITLE = "Secret Marine Bunker"
CUTS = [3, 7, 12]
TILER = dict(terrain="none", sky_y=-22)

NX, NZ = 104, 68
HZ = 34                              # hall centre line (runs along x)
HX1, HX2 = 10, 94                    # hall ends (blast doors)
HW = 5                               # hall half width
HH = 9                               # hall crown height
CONC = "minecraft:light_gray_concrete"
WALL = ["onepiece:marine_bricks", "minecraft:light_gray_concrete", "minecraft:polished_andesite"]
TILE = "onepiece:marine_tiles"
STEEL = "minecraft:iron_block"
ROCK = ["minecraft:deepslate", "minecraft:tuff", "minecraft:cobbled_deepslate", "minecraft:deepslate"]
AX, AZ = 52, 34                      # command atrium centre


def rock(bb):
    bb.mix(0, -4, 0, NX - 1, 20, NZ - 1, ROCK, [0.45, 0.25, 0.15, 0.15])


def room(bb, x1, z1, x2, z2, h=5, floor=TILE, wall=CONC, y=0):
    """Carve a room with concrete walls (1 thick, inside the rock), a tiled floor and a flush ceiling."""
    bb.fill(x1 - 1, y - 1, z1 - 1, x2 + 1, y + h, z2 + 1, wall)
    bb.fill(x1, y - 1, z1, x2, y - 1, z2, floor)
    bb.fill(x1, y, z1, x2, y + h - 1, z2, AIR)
    bb.fill(x1, y + h, z1, x2, y + h, z2, "minecraft:smooth_stone")
    for x in range(x1 + 2, x2 - 1, 5):
        for z in range(z1 + 2, z2 - 1, 5):
            bb.set(x, y + h, z, "minecraft:sea_lantern")


def hall(bb):
    """Vaulted main hall: a barrel vault of concrete, steel ribs every 4 blocks, a lamp strip, a rail, drains."""
    def inside(X, y, Z, grow=0.0):
        dz = (np.abs(Z - HZ)) / (HW + grow)
        return (y >= 0) & ((y < 4) & (dz <= 1) | (((y - 3.5) / (HH - 3.5 + grow)) ** 2 + dz ** 2 <= 1))
    bb.fill_where(HX1, -1, HZ - HW - 3, HX2, HH + 3, HZ + HW + 3,
                  lambda X, y, Z: inside(X, y, Z, 1.5) & ~inside(X, y, Z), CONC)
    bb.fill_where(HX1, 0, HZ - HW - 1, HX2, HH + 1, HZ + HW + 1, lambda X, y, Z: inside(X, y, Z), AIR)
    bb.fill(HX1, -1, HZ - HW, HX2, -1, HZ + HW, TILE)
    bb.fill(HX1, -1, HZ - HW, HX2, -1, HZ - HW, "minecraft:blue_concrete"); bb.fill(HX1, -1, HZ + HW, HX2, -1, HZ + HW, "minecraft:blue_concrete")
    for x in range(HX1 + 2, HX2 - 1, 4):
        bb.fill_where(x, -1, HZ - HW - 2, x, HH + 2, HZ + HW + 2,
                      lambda X, y, Z: inside(X, y, Z, 1.0) & ~inside(X, y, Z, -0.2), STEEL)
        bb.set(x, HH, HZ, "minecraft:sea_lantern" if (x // 4) % 2 else "minecraft:redstone_lamp[lit=true]")
    for x in range(HX1 + 1, HX2):
        bb.set(x, -1, HZ + 3, "minecraft:polished_andesite")
        bb.set(x, 0, HZ + 3, "minecraft:rail[shape=east_west]")
    for x in range(HX1 + 4, HX2 - 3, 8):
        bb.set(x, -1, HZ - 3, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
    # pipes along the walls at y 4 and 5
    for (z, y) in ((HZ - HW + 1, 5), (HZ + HW - 1, 5)):
        bb.fill(HX1 + 1, y, z, HX2 - 1, y, z, "minecraft:waxed_copper_block" if z < HZ else "minecraft:waxed_cut_copper")


def blast_door(bb, x, facing):
    """Two huge steel leaves with the Marine gull in blue; a small personnel hatch to walk through."""
    for z in range(HZ - HW, HZ + HW + 1):
        for y in range(0, 8):
            bb.set(x, y, z, "minecraft:iron_block" if (z + y) % 5 else "minecraft:heavy_core" if False else "minecraft:iron_block")
    bb.fill(x, 0, HZ, x, 7, HZ, "minecraft:polished_deepslate")
    gull = [(HZ - 3, 5), (HZ - 2, 5), (HZ - 4, 4), (HZ - 1, 4), (HZ, 3), (HZ + 1, 4), (HZ + 4, 4), (HZ + 2, 5), (HZ + 3, 5)]
    for (z, y) in gull:
        bb.set(x, y, z, "minecraft:blue_concrete")
    bb.fill(x, 0, HZ + 2, x, 1, HZ + 2, AIR)
    bb.set(x, 0, HZ + 2, f"minecraft:iron_door[facing={facing},half=lower,hinge=left,open=false,powered=false]")
    bb.set(x, 1, HZ + 2, f"minecraft:iron_door[facing={facing},half=upper,hinge=left,open=false,powered=false]")
    side = -1 if facing == "east" else 1
    bb.set(x + side, 1, HZ + 3, f"minecraft:stone_button[face=wall,facing={'west' if facing == 'east' else 'east'}]") if False else None
    bb.set(x - side, 1, HZ + 3, "minecraft:stone_button[face=wall,facing=" + ("west" if side > 0 else "east") + "]")


def atrium(bb):
    """Two-storey command room on the hall's north side: chart table, a wall of Den Den Mushi, a gallery with the
    commander's office."""
    x1, z1, x2, z2 = AX - 10, HZ - HW - 16, AX + 10, HZ - HW - 1
    room(bb, x1, z1, x2, z2, h=11)
    bb.fill(AX - 3, 0, HZ - HW - 2, AX + 3, 4, HZ - HW, AIR)              # wide opening into the hall
    # chart table
    bb.fill(AX - 3, 0, z1 + 7, AX + 3, 0, z1 + 10, "minecraft:dark_oak_fence")
    bb.fill(AX - 3, 1, z1 + 7, AX + 3, 1, z1 + 10, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false]")
    bb.fill(AX - 2, 1, z1 + 8, AX + 2, 1, z1 + 9, "minecraft:blue_carpet")
    bb.set(AX, 1, z1 + 8, "minecraft:white_carpet")
    for x in (AX - 4, AX + 4):
        bb.set(x, 0, z1 + 8, "minecraft:spruce_stairs[facing=" + ("east" if x < AX else "west") + "]")
    # snail wall: desks with Den Den Mushi (lime body block + shell) all along the back wall
    for x in range(x1 + 1, x2, 2):
        bb.set(x, 0, z1, "minecraft:smooth_stone_slab[type=top]")
        bb.set(x, 1, z1, "minecraft:lime_terracotta" if x % 4 == 1 else "minecraft:green_terracotta")
        bb.set(x, 2, z1, "minecraft:orange_terracotta" if x % 4 == 1 else "minecraft:white_terracotta")
        bb.set(x, 3, z1, "minecraft:black_concrete")                     # receiver screens
        bb.set(x, 4, z1, "minecraft:light_blue_stained_glass")
        bb.set(x, 0, z1 + 1, "minecraft:polished_andesite_stairs[facing=north]") if False else bb.set(x, 0, z1 + 2, "minecraft:birch_stairs[facing=north]")
    # gallery round three sides at y 6 with a rail, office at the west end
    bb.fill(x1, 5, z1, x2, 5, z1 + 3, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(x1, 5, z1, x1 + 3, 5, z2 - 2, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(x2 - 3, 5, z1, x2, 5, z2 - 2, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(x1 + 4, 6, z1 + 4, x2 - 4, 6, z1 + 4, "minecraft:iron_bars")
    bb.fill(x1 + 4, 6, z1 + 4, x1 + 4, 6, z2 - 2, "minecraft:iron_bars")
    bb.fill(x2 - 4, 6, z1 + 4, x2 - 4, 6, z2 - 2, "minecraft:iron_bars")
    for z in range(z1 + 4, z2 - 1):
        bb.set(x2, 0 + (z - z1 - 4) if z - z1 - 4 < 5 else 5, z, "minecraft:polished_andesite") if False else None
    for k in range(5):                                                    # stair up the east side
        bb.set(x2 - 1, k, z2 - 2 - k, "minecraft:polished_andesite_stairs[facing=north]")
        bb.fill(x2 - 1, k + 1, z2 - 2 - k, x2 - 1, k + 4, z2 - 2 - k, AIR)
    bb.fill(x2 - 1, 5, z2 - 7, x2 - 1, 5, z2 - 6, AIR)
    # commander's office cut into the rock behind the west gallery
    ox1, oz1, ox2, oz2 = x1 - 12, z1, x1 - 2, z1 + 9
    room(bb, ox1, oz1, ox2, oz2, h=5, floor="minecraft:dark_oak_planks", y=6)
    bb.fill(x1 - 1, 6, z1 + 4, x1 - 1, 8, z1 + 5, AIR)
    furnish_kit(bb, (ox1, oz1, ox2, oz2), 6, 4, "office", wood="dark_oak", seed=2701, doors=[(x1 - 1, z1 + 4)], accent="blue")
    return (ox1, oz1)


def wing(bb, x1, z1, x2, z2, kind, seed, door, h=5, wood="birch"):
    room(bb, x1, z1, x2, z2, h=h)
    dx, dz = door
    bb.fill(dx, 0, dz, dx + 1, 2, dz, AIR) if z1 <= dz <= z2 or dz in (z1 - 1, z2 + 1) else None
    furnish_kit(bb, (x1, z1, x2, z2), 0, h - 1, kind, wood=wood, seed=seed, doors=[door], accent="blue")


def cells(bb):
    """Seastone cells south of the hall: a corridor, eight cells with bars, a guard post."""
    x1, x2 = 60, 90
    cz1, cz2 = HZ + HW + 2, HZ + HW + 4                                   # corridor
    room(bb, x1, cz1, x2, cz2, h=4, floor="minecraft:polished_deepslate")
    bb.fill(x1, 0, HZ + HW, x1 + 1, 2, cz1, AIR)
    for k, x in enumerate(range(x1, x2 - 2, 4)):
        bb.fill(x, -1, cz2 + 2, x + 3, 4, cz2 + 6, "onepiece:sea_prism_stone")
        bb.fill(x + 1, 0, cz2 + 2, x + 2, 2, cz2 + 5, AIR)
        bb.fill(x + 1, 0, cz2 + 1, x + 2, 2, cz2 + 1, "onepiece:prison_bars")
        bb.set(x + 1, 0, cz2 + 5, "minecraft:white_carpet")
        if k % 3 == 1:
            bb.set(x + 2, 0, cz2 + 5, "minecraft:skeleton_skull[rotation=8]")
    bb.set(x2 - 1, 0, cz1, "minecraft:spruce_stairs[facing=west]"); bb.set(x2 - 2, 0, cz1, "minecraft:spruce_slab[type=top]")
    return (x1, cz1)


def depot(bb):
    """Generator room and stores at the east end: copper tanks, pipes, crates, the rail's end."""
    x1, z1, x2, z2 = HX2 - 12, HZ - HW - 12, HX2 - 2, HZ - HW - 2
    room(bb, x1, z1, x2, z2, h=7, floor="minecraft:polished_deepslate")
    bb.fill(x1 + 3, 0, HZ - HW - 1, x1 + 5, 3, HZ - HW - 1, AIR)
    for (x, z) in ((x1 + 1, z1 + 1), (x1 + 5, z1 + 1)):
        bb.fill(x, 0, z, x + 2, 4, z + 2, "minecraft:waxed_copper_block")
        bb.fill(x + 1, 5, z + 1, x + 1, 6, z + 1, "minecraft:waxed_cut_copper")
    bb.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z1 + 1, "minecraft:waxed_cut_copper")
    for x in range(x1 + 1, x2, 2):
        bb.set(x, 0, z2, "minecraft:barrel[facing=up]")
        bb.set(x, 1, z2, "minecraft:barrel[facing=up]" if x % 4 == 1 else "minecraft:spruce_planks")
    bb.set(x2 - 1, 0, z1 + 2, "minecraft:redstone_lamp[lit=true]"); bb.set(x2 - 1, 1, z1 + 2, "minecraft:lever[face=floor,facing=north,powered=true]")


def design():
    bb = BigBuild(seed=2700, y_min=-6, y_max=24)
    rock(bb)
    hall(bb)
    office = atrium(bb)
    # north wing rooms, doors open into the hall
    wing(bb, 14, HZ - HW - 13, 26, HZ - HW - 2, "barracks" if False else "bedroom", 2702, (20, HZ - HW - 1))
    wing(bb, 28, HZ - HW - 13, 39, HZ - HW - 2, "storage", 2703, (33, HZ - HW - 1))
    # south wing: mess + galley, armory, cells
    wing(bb, 14, HZ + HW + 2, 30, HZ + HW + 14, "dining", 2704, (22, HZ + HW + 1))
    wing(bb, 32, HZ + HW + 2, 42, HZ + HW + 14, "kitchen", 2705, (37, HZ + HW + 1))
    wing(bb, 44, HZ + HW + 2, 56, HZ + HW + 12, "storage", 2706, (50, HZ + HW + 1), wood="spruce")
    for k in range(3):                                                   # armory: cannons and gun racks
        bb.set(46 + 4 * k, 0, HZ + HW + 11, "onepiece:cannon[facing=north]")
        bb.set(46 + 4 * k, 0, HZ + HW + 3, "onepiece:cannonball_pile")
    for k in range(10):
        bb.set(45 + k, 1, HZ + HW + 12, "minecraft:spruce_trapdoor[facing=north,half=top,open=true]")
    cell = cells(bb)
    depot(bb)
    for x in (HX1, HX2):
        blast_door(bb, x, "east" if x == HX1 else "west")
    # door openings from each wing into the hall (the vault wall is 2 thick there)
    for (x, z) in ((20, HZ - HW - 1), (33, HZ - HW - 1), (22, HZ + HW + 1), (37, HZ + HW + 1), (50, HZ + HW + 1)):
        bb.fill(x, 0, min(z, HZ - HW - 2 if z < HZ else z) - (1 if z < HZ else 0), x + 1, 2, max(z, z) + (0 if z < HZ else 1), AIR)
    # tunnel stubs beyond the doors, rough rock
    for (a, b_) in (((HX1 - 1, HZ), (0, HZ - 6)), ((HX2 + 1, HZ), (NX - 1, HZ + 8))):
        n = abs(b_[0] - a[0])
        for k in range(n + 1):
            t = k / max(n, 1)
            x = int(round(a[0] + (b_[0] - a[0]) * t)); z = int(round(a[1] + (b_[1] - a[1]) * t))
            bb.fill(x, 0, z - 2, x, 3, z + 2, AIR)
            bb.fill(x, -1, z - 2, x, -1, z + 2, "minecraft:gravel")
    return bb, [], office, cell


def build():
    bb, audit, office, cell = design()
    b = to_canvas(bb)
    b.chest(office[0] + 1, 6, office[1] + 1, "marine_bunker", "east")
    b.chest(47, 0, HZ + HW + 7, "marine", "east")
    b.chest(HX2 - 3, 0, HZ - HW - 4, "marine_bunker", "west")
    b.chest(cell[0] + 2, 0, cell[1] + 9, "marine_bunker", "east")
    for (x, z, kit) in ((24, HZ - 2, "marine"), (44, HZ + 2, "marine"), (70, HZ - 2, "marine"), (14, HZ + 1, "marine_rifle"),
                        (90, HZ - 1, "marine_rifle"), (AX, HZ - HW - 9, "elite_marine"), (cell[0] + 6, cell[1] + 1, "marine_rifle")):
        b.guard(x, 0, z, kit)
    return b, 0
