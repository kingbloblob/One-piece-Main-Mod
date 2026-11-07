"""Impel Down Level 5, Freezing Hell, v3 (2026-10-30 audit: the v1 cavern was a small rock shell). Redone with the
Minecraft Builder skill: a 132-wide frozen cave, 46 high, where a never-ending cold keeps the worst prisoners half
dead. Its middle is a FOREST of dead frozen trees in snow drifts round a frozen lake, with blue-ice spires rising
through it and hidden powder-snow pits; on two sides two tiers of ice-walled cells with frozen prisoners, a railed
walkway and stairs; in the north-east the guards' heated watch house (stove, mess, bunks) and in the south-east the
wolves' den of the Jailer Beasts, a bone-strewn rock hollow. In the far wall a narrow crack, lit pink, is the secret
way into Newkama Land. Icicles hang from a dome of packed ice and snow. Canvas y 0 = the cavern floor, world y 33."""
import math

import numpy as np

from mcb.kit import BigBuild, set_if_air
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import impel_kit as K
from mcb.blazing_hell_furnace import block_house

SID = "freezing_hell_cells"
TITLE = "Impel Down Level 5: Freezing Hell"
CUTS = [3, 10, 20]
TILER = dict(terrain="none", sky_y=33)

N = 140
CX, CZ = 70, 70
RX, RZ, H = 64, 64, 46
ROCK = ("minecraft:packed_ice", "minecraft:snow_block", "minecraft:packed_ice", "minecraft:blue_ice", "minecraft:calcite",
        "minecraft:deepslate")
FLOOR = ("minecraft:snow_block", "minecraft:snow_block", "minecraft:powder_snow", "minecraft:packed_ice")
ICEW = "minecraft:packed_ice"
BARS = "onepiece:prison_bars"
SEA = "onepiece:seastone_bricks"
RAIL = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
HALF = 42
FH = 6


def lake(bb):
    """The frozen lake: ice over still water, blue-ice cracks, snow at its shore."""
    shp = NT.outline(CX + 6, CZ + 4, 17, 5101, wobble=0.18)
    bb.fill_where(0, -2, 0, N - 1, -1, N - 1, lambda X, y, Z: shp(X, Z) > 0, "minecraft:water")
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: shp(X, Z) > 0, "minecraft:ice")
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: (shp(X, Z) > 1) & (np.abs(NT.fbm(X, Z, 5102, 9) - 0.5) < 0.03),
                  "minecraft:blue_ice")
    return shp


def dead_tree(bb, x, z, h, rng):
    """A dead frozen tree: a bare spruce trunk, a few crooked branches, snow caps and icicles."""
    for y in range(1, h + 1):
        bb.set(x, y, z, "minecraft:stripped_spruce_log[axis=y]" if y > h - 3 else "minecraft:spruce_log[axis=y]")
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 2 * math.pi)
        y0 = int(rng.integers(h // 2, h))
        L = int(rng.integers(2, 5))
        for i in range(1, L + 1):
            bx, bz = round(x + i * math.cos(a)), round(z + i * math.sin(a))
            by = y0 + i // 2
            ax = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            bb.set(bx, by, bz, f"minecraft:spruce_log[axis={ax}]")
            set_if_air(bb, bx, by + 1, bz, "minecraft:snow[layers=2]")
            if i == L and rng.random() < 0.5:
                set_if_air(bb, bx, by - 1, bz, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    set_if_air(bb, x, h + 1, z, "minecraft:snow[layers=3]")


def spire(bb, x, z, h, r):
    """An ice spire: a tapering cone of packed and blue ice."""
    for y in range(1, h + 1):
        rr = r * (1 - y / (h + 1)) ** 1.2 + 0.4
        ri = int(rr) + 1
        bb.fill_where(x - ri, y, z - ri, x + ri, y, z + ri, lambda X, yy, Z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr,
                      "minecraft:blue_ice" if y % 7 < 3 else "minecraft:packed_ice")


def drifts(bb, inside, shp):
    """Snow drifts in noise mounds over the floor (snow layers 1-6), powder-snow pits hidden among them."""
    d = NT.fbm
    for lv in range(1, 7):
        bb.fill_where(4, 1, 4, N - 5, 1, N - 5,
                      lambda X, y, Z, lv=lv: (np.minimum((d(X, Z, 5103, 14) * 9).astype(int) - 2, 6) == lv) & inside(X, 1, Z) & (shp(X, Z) <= 0),
                      f"minecraft:snow[layers={lv}]", only_empty=True)
    bb.fill_where(4, 0, 4, N - 5, 0, N - 5, lambda X, y, Z: (NT.noise(X, Z, 5104, 5) > 0.86) & (shp(X, Z) <= -3)
                  & (np.abs(X - CX) < HALF - 4) & (np.abs(Z - CZ) < HALF - 4), "minecraft:powder_snow")


def wolves_den(bb, x, z):
    """The Jailer Beasts' den: a low rock hollow of deepslate, bones and a broken cell gate."""
    bb.fill_where(x - 9, 1, z - 9, x + 9, 8, z + 9, lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2) / 81 + (y / 8) ** 2 < 1,
                  "minecraft:cobbled_deepslate")
    bb.fill_where(x - 8, 1, z - 8, x + 8, 6, z + 8, lambda X, y, Z: ((X - x) ** 2 + (Z - z) ** 2) / 49 + (y / 6) ** 2 < 1,
                  "minecraft:air")
    bb.fill(x - 2, 1, z - 9, x + 2, 4, z - 6, "minecraft:air")
    for (dx, dz) in ((-3, 2), (2, 3), (4, -1), (-1, -3)):
        bb.set(x + dx, 1, z + dz, "minecraft:bone_block[axis=y]")
    bb.set(x, 1, z, "minecraft:hay_block[axis=y]")
    bb.set(x + 1, 1, z - 1, "minecraft:skeleton_skull[powered=false,rotation=8]")


def crack(bb, x, z):
    """The secret crack in the wall to Newkama Land: a narrow zigzag passage lit pink at its end."""
    for i in range(12):
        xx = x + i
        zz = z + (1 if (i // 3) % 2 else 0)
        bb.fill(xx, 1, zz, xx, 4, zz + 1, "minecraft:air")
    bb.set(x + 11, 1, z, "minecraft:pearlescent_froglight[axis=y]")
    bb.set(x + 11, 4, z + 1, "minecraft:pearlescent_froglight[axis=y]")


def design():
    bb = BigBuild(seed=510, y_min=-6, y_max=H + 8)
    inside = K.cavern(bb, CX, CZ, RX, RZ, H, ROCK, 5100, FLOOR, thick=4, drips="minecraft:pointed_dripstone")
    shp = lake(bb)
    # cells: 2 tiers on the north and west sides, cut into the ice
    K.gallery(bb, CX, CZ, HALF, 7, 2, FH, ICEW, BARS, "minecraft:spruce_planks", RAIL, "spruce", 5110,
              light="minecraft:lantern[hanging=true,waterlogged=false]", sides=("north", "west"))
    # frozen prisoners: a blue-ice block in a corner of some cells
    rng = np.random.default_rng(511)
    for a in range(-HALF + 6, HALF - 6, 6):
        if rng.random() < 0.6:
            bb.set(CX + a, 1, CZ - HALF - 4, "minecraft:blue_ice")
        if rng.random() < 0.6:
            bb.set(CX - HALF - 4, 1 + FH, CZ + a, "minecraft:blue_ice")
    # the guards' heated watch house (north-east) and the wolves' den (south-east)
    block_house(bb, CX + HALF - 18, CZ - HALF - 6, CX + HALF - 4, CZ - HALF + 8, 2, "minecraft:spruce_planks", "minecraft:spruce_planks",
                "minecraft:dark_oak_planks", "minecraft:glass_pane", ("kitchen", "barracks"), "spruce", "south", 5120)
    for (x, z) in ((CX + HALF - 18, CZ - HALF - 6), (CX + HALF - 4, CZ - HALF - 6), (CX + HALF - 18, CZ - HALF + 8), (CX + HALF - 4, CZ - HALF + 8)):
        bb.fill(x, 0, z, x, 12, z, "minecraft:spruce_log[axis=y]")
    bb.fill(CX + HALF - 6, 13, CZ - HALF - 3, CX + HALF - 6, 16, CZ - HALF - 3, "minecraft:cobblestone")
    bb.set(CX + HALF - 6, 17, CZ - HALF - 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    wolves_den(bb, CX + 34, CZ + 34)
    crack(bb, CX + RX - 6, CZ + 8)
    # the forest: dead trees and ice spires everywhere outside the lake and the buildings
    taken = [(CX + HALF - 22, CZ - HALF - 10, CX + HALF, CZ - HALF + 12), (CX + 22, CZ + 22, CX + 46, CZ + 46)]
    nt = ns = 0
    for _ in range(4000):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        if not inside(np.array([[x]]), 14, np.array([[z]]))[0, 0] or shp(np.array([[x]]), np.array([[z]]))[0, 0] > -2:
            continue
        if (x - CX < -HALF + 3 and True) or (z - CZ < -HALF + 3):      # keep the cell fronts and walkways clear
            continue
        if any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
            continue
        if ns < 9 and rng.random() < 0.08:
            spire(bb, x, z, int(rng.integers(14, 30)), float(rng.uniform(2.5, 4.5)))
            taken.append((x - 6, z - 6, x + 6, z + 6))
            ns += 1
        elif nt < 70:
            dead_tree(bb, x, z, int(rng.integers(7, 16)), rng)
            taken.append((x - 3, z - 3, x + 3, z + 3))
            nt += 1
        if nt >= 70 and ns >= 9:
            break
    drifts(bb, inside, shp)
    K.shaft(bb, CX - HALF + 2, CZ + HALF - 4, H - 2, SEA)
    K.ceiling_lights(bb, CX, CZ, RX - 6, inside, "minecraft:sea_lantern", step=12, seed=512)
    K.floor_lights(bb, 4, 4, N - 5, N - 5, (1, 7))
    for a in range(0, 360, 36):           # lanterns on posts along the lake shore
        t = math.radians(a)
        x, z = round(CX + 6 + 21 * math.cos(t)), round(CZ + 4 + 21 * math.sin(t))
        bb.fill(x, 1, z, x, 3, z, "minecraft:spruce_fence")
        bb.set(x, 4, z, "minecraft:lantern[hanging=false,waterlogged=false]")
    return bb


def build():
    bb = design()
    b = to_canvas(bb)
    b.chest(CX + HALF - 16, 1, CZ - HALF - 4, "impel_down", "east")
    b.chest(CX + 34, 1, CZ + 36, "impel_down", "north")
    b.guards("jailer", ((CX - 20, CZ - 30), (CX - 30, CZ + 10), (CX + 10, CZ - 30)))
    b.guards("frost_soldier", ((CX + 20, CZ + 20), (CX - 10, CZ + 30)))
    return b, 0
