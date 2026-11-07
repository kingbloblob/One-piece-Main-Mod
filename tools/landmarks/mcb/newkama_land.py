"""Newkama Land, Impel Down's secret Level 5.5, v3 (2026-10-30 audit: the v1 build was only a shell of red blocks).
Redone with the Minecraft Builder skill: a 124-wide pink cave, 44 high, turned into Emporio Ivankov's paradise. In the
middle the big plaza with a glowing checkered disco floor, the great stage with NEWKAMA in gold letters, spotlights
and bunting strung over the crowd; round it a packed little town of pastel two-storey houses (bedrooms, dressing
rooms, kitchens, bars) on winding lanes; Ivankov's purple throne house, the long bar and the dining hall, a steaming
hot spring and a garden of crimson fungi, flowers and froglights. Lamps hang everywhere, so the whole cave is as bright
as a party. The secret crack from Freezing Hell comes in on the west wall. Canvas y 0 = the cave floor, world y 33."""
import math

import numpy as np

from mcb.kit import BigBuild, set_if_air, lamp_post
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import impel_kit as K
from mcb.blazing_hell_furnace import block_house

SID = "newkama_land"
TITLE = "Newkama Land (Impel Down Level 5.5)"
CUTS = [3, 9, 16]
TILER = dict(terrain="none", sky_y=33)

N = 132
CX, CZ = 66, 66
RX, RZ, H = 60, 58, 44
ROCK = ("minecraft:pink_terracotta", "minecraft:magenta_terracotta", "minecraft:purple_terracotta", "minecraft:pink_terracotta",
        "minecraft:crimson_nylium", "minecraft:white_terracotta")
FLOOR = ("minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:pink_terracotta")
WALLS = ("minecraft:pink_concrete", "minecraft:magenta_concrete", "minecraft:light_blue_concrete", "minecraft:yellow_concrete",
         "minecraft:lime_concrete", "minecraft:white_concrete", "minecraft:purple_concrete", "minecraft:orange_concrete")
ROOFS = ("minecraft:purple_terracotta", "minecraft:magenta_terracotta", "minecraft:blue_terracotta", "minecraft:pink_terracotta")
PLAZA = (CX - 16, CZ - 12, CX + 16, CZ + 16)
FONT = {"N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"], "E": ["#####", "#....", "####.", "#....", "#####"],
        "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"], "K": ["#..#.", "#.#..", "##...", "#.#..", "#..#."],
        "A": [".###.", "#...#", "#####", "#...#", "#...#"], "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"]}


def text(bb, s, x, y, z, block, scale=2):
    for ch in s:
        for r, bits in enumerate(FONT[ch]):
            for c, b_ in enumerate(bits):
                if b_ == "#":
                    bb.fill(x + c * scale, y - (r + 1) * scale + 1, z, x + c * scale + scale - 1, y - r * scale, z, block)
        x += 6 * scale


def plaza(bb):
    """The disco floor (black and coloured glass over froglights), the stage on its north side and the bunting."""
    x1, z1, x2, z2 = PLAZA
    cols = ("minecraft:magenta_stained_glass", "minecraft:light_blue_stained_glass", "minecraft:yellow_stained_glass",
            "minecraft:lime_stained_glass", "minecraft:pink_stained_glass")
    bb.fill(x1, -1, z1, x2, -1, z2, "minecraft:pearlescent_froglight[axis=y]")
    for x in range(x1, x2 + 1):
        for z in range(z1 + 8, z2 + 1):
            k = (x // 3 + z // 3)
            bb.set(x, 0, z, "minecraft:black_concrete" if k % 2 else cols[(x // 3 * 7 + z // 3 * 3) % len(cols)])
    # the stage: a raised purple platform with steps, a gold-trimmed back wall carrying NEWKAMA
    bb.fill(x1 + 2, 1, z1, x2 - 2, 3, z1 + 7, "minecraft:purple_concrete")
    bb.fill(x1 + 2, 4, z1, x2 - 2, 4, z1 + 7, "minecraft:polished_blackstone_slab[type=bottom,waterlogged=false]")
    bb.fill(x1 + 6, 1, z1 + 8, x2 - 6, 1, z1 + 8, "minecraft:purple_stained_glass")
    bb.fill(CX - 23, 1, z1 - 2, CX + 23, 22, z1 - 1, "minecraft:purple_concrete")
    bb.fill(CX - 23, 22, z1 - 2, CX + 23, 22, z1 + 1, "minecraft:gold_block")
    bb.fill(CX - 23, 1, z1, CX - 23, 22, z1 + 1, "minecraft:gold_block"); bb.fill(CX + 23, 1, z1, CX + 23, 22, z1 + 1, "minecraft:gold_block")
    text(bb, "NEWKAMA", CX - 20, 19, z1, "minecraft:gold_block", scale=1)
    for x in range(x1 + 4, x2 - 3, 4):                     # footlights and spotlights
        bb.set(x, 5, z1 + 7, "minecraft:end_rod[facing=up]")
        bb.set(x, 21, z1, "minecraft:shroomlight")
    # bunting strung across the plaza: rows of coloured wool on chains from post to post
    for z in range(z1 + 12, z2 + 1, 6):
        bb.fill(x1 - 1, 1, z, x1 - 1, 11, z, "minecraft:dark_oak_fence")
        bb.fill(x2 + 1, 1, z, x2 + 1, 11, z, "minecraft:dark_oak_fence")
        for x in range(x1, x2 + 1):
            sag = int(round(2.5 * math.sin(math.pi * (x - x1) / (x2 - x1))))
            bb.set(x, 11 - sag, z, WALLS[(x // 2) % len(WALLS)].replace("concrete", "wool"))
    # the mirror ball over the floor
    bb.fill_where(CX - 3, 14, CZ + 4 - 3, CX + 3, 20, CZ + 4 + 3, lambda X, y, Z: (X - CX) ** 2 + (y - 17) ** 2 + (Z - CZ - 4) ** 2 <= 8,
                  "minecraft:glass")
    bb.set(CX, 17, CZ + 4, "minecraft:sea_lantern")
    K.chains(bb, ((CX, CZ + 4),), 21, lambda X, y, Z: np.full((1, 1), y < H - 6))


def town(bb, rng, taken):
    """Pastel two-storey houses packed round the plaza on lanes 2-3 wide, each furnished (bedrooms, dressing rooms,
    kitchens, a bar or two)."""
    n = 0
    kinds = (("bedroom", "bedroom"), ("tavern", "bedroom"), ("kitchen", "bedroom"), ("library", "bedroom"), ("dining", "bedroom"))
    for _ in range(3000):
        w, d = int(rng.integers(7, 11)), int(rng.integers(7, 11))
        x, z = int(rng.integers(8, N - 8 - w)), int(rng.integers(8, N - 8 - d))
        ok = all(((x + i - CX) / (RX - 9)) ** 2 + ((z + j - CZ) / (RZ - 9)) ** 2 < 1 for i in (0, w) for j in (0, d))
        if not ok or any(x - 2 < t[2] and t[0] < x + w + 2 and z - 2 < t[3] and t[1] < z + d + 2 for t in taken):
            continue
        wall = WALLS[int(rng.integers(0, len(WALLS)))]
        roof = ROOFS[int(rng.integers(0, len(ROOFS)))]
        door = ("north", "south", "west", "east")[int(np.argmin([abs(z - PLAZA[3]) + 99 * (z < CZ), abs(z + d - PLAZA[1]) + 99 * (z > CZ),
                                                               abs(x - PLAZA[2]) + 99 * (x < CX), abs(x + w - PLAZA[0]) + 99 * (x > CX)]))]
        floors = 2 if rng.random() < 0.8 else 1
        block_house(bb, x, z, x + w, z + d, floors, wall, "minecraft:cherry_planks", roof, "minecraft:pink_stained_glass_pane",
                    kinds[n % len(kinds)], "cherry", door, 5300 + n * 3)
        mx, mz = x + w // 2, z + d // 2
        lx, lz = {"north": (mx, z - 1), "south": (mx, z + d + 1), "west": (x - 1, mz), "east": (x + w + 1, mz)}[door]
        set_if_air(bb, lx, 1, lz, "minecraft:pink_carpet")
        taken.append((x, z, x + w, z + d))
        n += 1
        if n >= 40:
            break
    return n


def throne_house(bb, x1, z1, x2, z2):
    """Ivankov's throne room: a purple hall with gold pillars, a red carpet up to the gold throne."""
    bb.fill(x1, 0, z1, x2, 12, z2, "minecraft:purple_concrete")
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, 11, z2 - 1, "minecraft:air")
    bb.fill(x1 - 1, 12, z1 - 1, x2 + 1, 12, z2 + 1, "minecraft:gold_block")
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, 1, z1, x, 11, z1, "minecraft:gold_block"); bb.fill(x, 1, z2, x, 11, z2, "minecraft:gold_block")
    mz = (z1 + z2) // 2
    bb.fill(x2, 1, mz - 1, x2, 4, mz + 1, "minecraft:air")
    bb.fill(x1 + 2, 1, mz - 1, x2 - 1, 1, mz + 1, "minecraft:red_carpet")
    bb.fill(x1 + 1, 1, mz - 2, x1 + 2, 1, mz + 2, "minecraft:gold_block")
    bb.set(x1 + 2, 2, mz, "minecraft:purpur_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    bb.fill(x1 + 1, 2, mz - 1, x1 + 1, 4, mz + 1, "minecraft:gold_block")
    for z in range(z1 + 2, z2 - 1, 3):
        bb.set(x1 + 1, 7, z, "minecraft:pearlescent_froglight[axis=y]"); bb.set(x2 - 1, 7, z, "minecraft:pearlescent_froglight[axis=y]")
        bb.set(x1 + 1, 3, z, "minecraft:magenta_banner[rotation=4]") if z != mz else None


def spring(bb, x, z):
    """The steaming hot spring: a round pool of water over magma (bubbles) ringed with stone and lanterns."""
    bb.fill_where(x - 8, -2, z - 8, x + 8, 0, z + 8, lambda X, y, Z: (X - x) ** 2 + (Z - z) ** 2 <= 49, "minecraft:water")
    bb.fill_where(x - 8, -3, z - 8, x + 8, -3, z + 8, lambda X, y, Z: (X - x) ** 2 + (Z - z) ** 2 <= 49, "minecraft:magma_block")
    bb.fill_where(x - 9, 0, z - 9, x + 9, 1, z + 9, lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2 > 49) & ((X - x) ** 2 + (Z - z) ** 2 <= 70)
                  & ((y == 0) | (NT.noise(X, Z, 5310, 2) > 0.5)), "minecraft:smooth_stone")
    for a in range(0, 360, 45):
        t = math.radians(a)
        lamp_post(bb, round(x + 9.5 * math.cos(t)), 1, round(z + 9.5 * math.sin(t)), post="minecraft:cherry_fence", h=2,
                  light="minecraft:lantern[hanging=false,waterlogged=false]")


def garden(bb, x, z, rng):
    """A garden of crimson fungi, roses and froglights on moss."""
    shp = NT.outline(x, z, 10, 5320, wobble=0.2)
    bb.fill_where(x - 14, 0, z - 14, x + 14, 0, z + 14, lambda X, y, Z: shp(X, Z) > 0, "minecraft:moss_block")
    for _ in range(70):
        px, pz = x + int(rng.integers(-11, 12)), z + int(rng.integers(-11, 12))
        if shp(np.array([[px]]), np.array([[pz]]))[0, 0] <= 0:
            continue
        k = rng.random()
        blk = ("minecraft:crimson_fungus" if k < 0.3 else "minecraft:rose_bush[half=lower]" if k < 0.45 else
               "minecraft:pink_tulip" if k < 0.65 else "minecraft:allium" if k < 0.85 else "minecraft:ochre_froglight[axis=y]")
        if blk.startswith("minecraft:rose_bush"):
            set_if_air(bb, px, 1, pz, blk); set_if_air(bb, px, 2, pz, "minecraft:rose_bush[half=upper]")
        else:
            set_if_air(bb, px, 1, pz, blk)
    for (dx, dz) in ((-5, -3), (4, 4), (6, -5)):          # huge crimson fungi
        tx, tz = x + dx, z + dz
        bb.fill(tx, 1, tz, tx, 6, tz, "minecraft:crimson_stem[axis=y]")
        bb.fill_where(tx - 3, 6, tz - 3, tx + 3, 8, tz + 3, lambda X, y, Z, tx=tx, tz=tz: (X - tx) ** 2 + (Z - tz) ** 2 <= 9 - (y - 6) * 3,
                      "minecraft:nether_wart_block")
        bb.set(tx, 5, tz + 1, "minecraft:shroomlight")


def design():
    bb = BigBuild(seed=530, y_min=-6, y_max=H + 8)
    inside = K.cavern(bb, CX, CZ, RX, RZ, H, ROCK, 5300, FLOOR, thick=4, drips=None)
    plaza(bb)
    rng = np.random.default_rng(531)
    TH = (CX + 26, CZ - 22, CX + 44, CZ - 6)
    BAR = (CX - 46, CZ - 20, CX - 26, CZ - 8)
    DIN = (CX - 46, CZ + 6, CX - 28, CZ + 22)
    throne_house(bb, *TH)
    block_house(bb, *BAR, 1, "minecraft:magenta_concrete", "minecraft:cherry_planks", "minecraft:purple_terracotta",
                "minecraft:pink_stained_glass_pane", ("tavern",), "cherry", "east", 5330)
    block_house(bb, *DIN, 1, "minecraft:light_blue_concrete", "minecraft:cherry_planks", "minecraft:blue_terracotta",
                "minecraft:light_blue_stained_glass_pane", ("dining",), "cherry", "east", 5331)
    spring(bb, CX + 30, CZ + 28)
    garden(bb, CX - 4, CZ + 38, rng)
    taken = [(PLAZA[0] - 3, PLAZA[1] - 3, PLAZA[2] + 3, PLAZA[3] + 3), TH, BAR, DIN, (CX + 20, CZ + 18, CX + 40, CZ + 38),
             (CX - 16, CZ + 26, CX + 8, CZ + 50), (CX - RX + 2, CZ - 4, CX - RX + 14, CZ + 4)]
    town(bb, rng, taken)
    # lamp posts all over the open ground, lights in the dome, the crack from Freezing Hell on the west wall
    for _ in range(400):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        if inside(np.array([[x]]), 2, np.array([[z]]))[0, 0] and not any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
            lamp_post(bb, x, 1, z, post="minecraft:cherry_fence", h=3, light="minecraft:pearlescent_froglight[axis=y]")
            taken.append((x - 5, z - 5, x + 5, z + 5))
    K.ceiling_lights(bb, CX, CZ, RX - 4, inside, "minecraft:pearlescent_froglight[axis=y]", step=8, seed=532)
    K.floor_lights(bb, 4, 4, N - 5, N - 5, (1, 2, 7, 8, 13, 14), step=6)
    for i in range(12):
        bb.fill(CX - RX - 3 + i, 1, CZ - 1 + (i // 3) % 2, CX - RX - 3 + i, 4, CZ + (i // 3) % 2, "minecraft:air")
    return bb


def build():
    bb = design()
    b = to_canvas(bb)
    b.chest(CX + 28, 1, CZ - 18, "medium", "east")
    b.chest(CX - 44, 1, CZ - 18, "medium", "east")
    b.npc(CX + 30, 1, CZ - 14, "ivankov", False)
    return b, 0
