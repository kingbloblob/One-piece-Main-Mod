"""Impel Down Level 4, Blazing Hell, v3 (2026-10-30 audit: the v1 cavern was a small rock shell). Redone with the
Minecraft Builder skill to the show's look: a vast red-black furnace cave, 140 across and 56 high, the GREAT CAULDRON
of boiling blood in the middle (a 52-wide nether-brick bowl of lava with magma froth, fire grates round its rim)
and the iron bridge hung over it on chains from the dome, where Luffy and Bon Clay crossed. Round the hall stand three
tiers of barred cells on all four sides with railed walkways and stairs; in the corners Chief Warden Magellan's
seastone office block (office, bedroom, his famous bathroom, armory), the guards' barracks and mess, the Jailer
Beasts' kennels and the sealed lift shaft up to Level 3. Magma veins run across the black floor, braziers and
chained posts stand about, and lights hang from the dome. Canvas y 0 = the cavern floor, world y 33."""
import math

import numpy as np

from mcb.kit import BigBuild, st, wing_floor, set_if_air, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import impel_kit as K
from mcb.kit_interiors import furnish_kit

SID = "blazing_hell_furnace"
TITLE = "Impel Down Level 4: Blazing Hell"
CUTS = [3, 14, 26]
TILER = dict(terrain="none", sky_y=33)

N = 150
CX, CZ = 75, 75
RX, RZ, H = 70, 70, 56
ROCK = ("minecraft:blackstone", "minecraft:basalt[axis=y]", "minecraft:smooth_basalt", "minecraft:blackstone",
        "minecraft:netherrack", "minecraft:magma_block")
FLOOR = ("minecraft:blackstone", "minecraft:polished_blackstone", "minecraft:blackstone", "minecraft:basalt[axis=y]")
BRICK = "minecraft:polished_blackstone_bricks"
NB = "minecraft:nether_bricks"
RNB = "minecraft:red_nether_bricks"
BARS = "onepiece:prison_bars"
SEA = "onepiece:seastone_bricks"
RAIL = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
CAUL_R = 26
HALF = 44                       # cell fronts 44 from the centre
FH = 6                          # tier height


def floor_veins(bb):
    """Glowing magma cracks across the floor in smooth noise lines (no sine stripes)."""
    v = lambda X, Z: np.abs(NT.fbm(X, Z, 4401, 26) - 0.5) < 0.025
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: v(X, Z) & (np.hypot(X - CX, Z - CZ) < RX - 4), "minecraft:magma_block")
    bb.fill_where(0, -1, 0, N - 1, -1, N - 1, lambda X, y, Z: v(X, Z) & (np.hypot(X - CX, Z - CZ) < RX - 4), "minecraft:lava[level=0]")


def cauldron(bb):
    """The cauldron of boiling blood: a round nether-brick bowl, 7 high outside, lava 2 below its rim with magma
    froth, buttresses and fire grates round it."""
    d = lambda X, Z: np.hypot(X - CX, Z - CZ)
    R = CAUL_R
    bb.fill_where(CX - R - 4, -6, CZ - R - 4, CX + R + 4, 6, CZ + R + 4, lambda X, y, Z: d(X, Z) <= R + 2 - max(0, y - 3) * 0.3, NB)
    bb.fill_where(CX - R - 4, 5, CZ - R - 4, CX + R + 4, 6, CZ + R + 4, lambda X, y, Z: (d(X, Z) <= R + 2) & (d(X, Z) > R - 0.5)
                  & (NT.noise(X, Z, 4402, 4) > 0.55), RNB)
    bb.fill_where(CX - R, -5, CZ - R, CX + R, 6, CZ + R, lambda X, y, Z: d(X, Z) <= R - 1, "minecraft:air")
    bb.fill_where(CX - R, -5, CZ - R, CX + R, 3, CZ + R, lambda X, y, Z: d(X, Z) <= R - 1, "minecraft:lava[level=0]")
    bb.fill_where(CX - R, 3, CZ - R, CX + R, 3, CZ + R, lambda X, y, Z: (d(X, Z) <= R - 1) & (NT.noise(X, Z, 4403, 3) > 0.72), "minecraft:magma_block")
    bb.fill_where(CX - R - 3, 7, CZ - R - 3, CX + R + 3, 7, CZ + R + 3, lambda X, y, Z: np.abs(d(X, Z) - (R + 1)) < 0.6,
                  "minecraft:nether_brick_fence")
    for k in range(16):                  # buttresses with fire grates between them
        a = 2 * math.pi * k / 16
        x, z = round(CX + (R + 3) * math.cos(a)), round(CZ + (R + 3) * math.sin(a))
        bb.fill(x - 1, 1, z - 1, x + 1, 5, z + 1, RNB)
        bb.set(x, 6, z, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        a2 = a + math.pi / 16
        gx, gz = round(CX + (R + 4) * math.cos(a2)), round(CZ + (R + 4) * math.sin(a2))
        bb.set(gx, 0, gz, "minecraft:magma_block")
        bb.fill(gx, 1, gz, gx, 2, gz, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")


def bridge(bb, inside):
    """The iron bridge across the cauldron at y 14, chained to the dome, with stairs down at both ends to the
    second-tier walkways."""
    Y = 1 + 2 * FH - 1              # = the third tier's walkway level
    for x in range(CX - HALF + 1, CX + HALF):
        for dz in (-1, 0, 1):
            bb.set(x, Y, CZ + dz, "minecraft:iron_block" if (x % 5 == 0 and dz == 0) else
                   "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for s in (-2, 2):
            bb.set(x, Y + 1, CZ + s, RAIL)
        if x % 7 == 0:
            K.chains(bb, ((x, CZ - 2), (x, CZ + 2)), Y + 2, inside)
            bb.set(x, Y - 1, CZ, "minecraft:lantern[hanging=true,waterlogged=false]")


def block_house(bb, x1, z1, x2, z2, floors, wall, plank, roof, glass, kinds, wood, door, seed):
    """A small square stone block house in a hall corner: `floors` floors of 5, one furnished room each (kit), a
    ladder in a corner, windows, a crenellated roof and a door on side `door`."""
    top = floors * 6
    bb.fill(x1, 0, z1, x2, top, z2, wall)
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, top - 1, z2 - 1, "minecraft:air")
    for f in range(1, floors):
        bb.fill(x1 + 1, f * 6, z1 + 1, x2 - 1, f * 6, z2 - 1, plank)
    bb.fill(x1 - 1, top, z1 - 1, x2 + 1, top, z2 + 1, roof)
    for x in range(x1 - 1, x2 + 2, 2):
        bb.set(x, top + 1, z1 - 1, roof); bb.set(x, top + 1, z2 + 1, roof)
    for z in range(z1 - 1, z2 + 2, 2):
        bb.set(x1 - 1, top + 1, z, roof); bb.set(x2 + 1, top + 1, z, roof)
    for f in range(floors):
        y = f * 6 + 3
        for x in range(x1 + 2, x2 - 1, 3):
            bb.set(x, y, z1, glass); bb.set(x, y, z2, glass)
        for z in range(z1 + 2, z2 - 1, 3):
            bb.set(x1, y, z, glass); bb.set(x2, y, z, glass)
    mx, mz = (x1 + x2) // 2, (z1 + z2) // 2
    dx, dz = {"north": (mx, z1), "south": (mx, z2), "west": (x1, mz), "east": (x2, mz)}[door]
    if door in ("north", "south"):
        bb.fill(dx - 1, 1, dz, dx, 3, dz, "minecraft:air")
    else:
        bb.fill(dx, 1, dz - 1, dx, 3, dz, "minecraft:air")
    lx, lz = x2 - 1, z1 + 1
    for f in range(floors):
        furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), f * 6 + 1, 5, kinds[f % len(kinds)], wood=wood, seed=seed + f,
                    doors=[(dx, dz), (lx, lz)])
    bb.fill(lx, 1, lz, lx, top - 1, lz, "minecraft:ladder[facing=south,waterlogged=false]")


def kennels(bb, cx, cz):
    """The Jailer Beasts' pens: barred pens with hay, bones and chains round a feeding yard."""
    for i, (dx, dz) in enumerate(((-4, -4), (4, -4), (-4, 4), (4, 4))):
        x, z = cx + dx, cz + dz
        bb.fill(x - 3, 0, z - 3, x + 3, 0, z + 3, "minecraft:coarse_dirt")
        bb.fill(x - 3, 1, z - 3, x + 3, 4, z + 3, BARS)
        bb.fill(x - 2, 1, z - 2, x + 2, 4, z + 2, "minecraft:air")
        bb.fill(x - 3, 5, z - 3, x + 3, 5, z + 3, BRICK)
        bb.fill(x - 1, 1, z + (3 if dz < 0 else -3), x + 1, 3, z + (3 if dz < 0 else -3), "minecraft:air")
        bb.set(x - 1, 1, z - 1, "minecraft:hay_block[axis=y]")
        bb.set(x + 1, 1, z + 1, "minecraft:bone_block[axis=y]")
        bb.set(x, 4, z, "minecraft:iron_chain[axis=y]")
    bb.set(cx, 1, cz, "minecraft:cauldron")


def props(bb, rng, taken):
    """Braziers, chained posts, bone heaps and anvils on the open floor."""
    n = 0
    for _ in range(600):
        x, z = int(rng.integers(12, N - 12)), int(rng.integers(12, N - 12))
        d = math.hypot(x - CX, z - CZ)
        if d < CAUL_R + 8 or d > RX - 8 or any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
            continue
        if abs(x - CX) > HALF - 4 or abs(z - CZ) > HALF - 4:
            continue
        k = n % 4
        if k == 0:
            bb.set(x, 1, z, "minecraft:polished_blackstone_wall"); bb.set(x, 2, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        elif k == 1:
            bb.fill(x, 1, z, x, 3, z, "minecraft:dark_oak_log[axis=y]"); bb.set(x, 4, z, "minecraft:iron_chain[axis=y]")
        elif k == 2:
            bb.set(x, 1, z, "minecraft:bone_block[axis=y]"); set_if_air(bb, x + 1, 1, z, "minecraft:skeleton_skull[powered=false,rotation=4]")
        else:
            bb.set(x, 1, z, "minecraft:anvil[facing=north]")
        n += 1
        if n >= 44:
            break


def design():
    bb = BigBuild(seed=440, y_min=-8, y_max=H + 8)
    inside = K.cavern(bb, CX, CZ, RX, RZ, H, ROCK, 4400, FLOOR, thick=4)
    floor_veins(bb)
    cauldron(bb)
    # cells: 3 tiers on all four sides, a gate gap on the south side for the tunnel from the lift
    K.gallery(bb, CX, CZ, HALF, 7, 3, FH, BRICK, BARS, BRICK, RAIL, "crimson", 4430, light="minecraft:soul_lantern[hanging=true,waterlogged=false]",
              )
    bridge(bb, inside)
    # the four inner corners of the hall: Magellan's seastone office (office, bedroom with his bath, records), the
    # guards' block (mess, barracks), the Jailer Beasts' kennels and the sealed lift shaft up to Level 3
    c1, c2 = HALF - 14, HALF - 5
    block_house(bb, CX - c2, CZ - c2, CX - c1, CZ - c1, 3, SEA, "minecraft:dark_oak_planks", BRICK, "minecraft:purple_stained_glass_pane",
                ("office", "bedroom", "library"), "dark_oak", "east", 4410)
    block_house(bb, CX + c1, CZ + c1, CX + c2, CZ + c2, 2, BRICK, "minecraft:crimson_planks", NB, "minecraft:red_stained_glass_pane",
                ("mess", "barracks"), "crimson", "west", 4420)
    kennels(bb, CX + (c1 + c2) // 2, CZ - (c1 + c2) // 2)
    K.shaft(bb, CX - (c1 + c2) // 2, CZ + (c1 + c2) // 2, H - 2, SEA)
    rng = np.random.default_rng(441)
    taken = [(CX + sx * (HALF - 15) - 12 * (sx < 0), CZ + sz * (HALF - 15) - 12 * (sz < 0), CX + sx * (HALF - 15) + 12 * (sx > 0), CZ + sz * (HALF - 15) + 12 * (sz > 0))
             for sx in (-1, 1) for sz in (-1, 1)]
    props(bb, rng, taken)
    for a in range(0, 360, 30):          # lamp posts round the cauldron
        t = math.radians(a + 15)
        lamp_post(bb, round(CX + (CAUL_R + 9) * math.cos(t)), 1, round(CZ + (CAUL_R + 9) * math.sin(t)),
                  post="minecraft:nether_brick_fence", h=3, light="minecraft:soul_lantern[hanging=false,waterlogged=false]")
    K.ceiling_lights(bb, CX, CZ, RX - 6, inside, "minecraft:shroomlight", step=11, seed=442)
    K.floor_lights(bb, 4, 4, N - 5, N - 5, (1, 7, 13))
    return bb


def build():
    bb = design()
    b = to_canvas(bb)
    b.chest(CX - HALF + 7, 1, CZ - HALF + 9, "impel_down", "east")
    b.chest(CX + HALF - 7, 1, CZ + HALF - 9, "impel_down", "west")
    b.chest(CX, 2 * FH + 1, CZ, "impel_down", "south")
    b.npc(CX - HALF + 18, 1, CZ - HALF + 10, "magellan", True)
    b.guards("jailer", ((CX - 30, CZ - 36), (CX + 30, CZ - 36), (CX - 30, CZ + 36), (CX + 30, CZ + 36), (CX, CZ + HALF - 6)))
    b.guards("flame_guard", ((CX - CAUL_R - 6, CZ + 6), (CX + CAUL_R + 6, CZ - 6)))
    b.guards("warden_jailer", ((CX + HALF - 18, CZ - HALF + 10),))
    return b, 0
