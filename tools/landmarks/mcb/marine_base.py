"""Marine Branch Base v2, redesigned with the Minecraft Builder skill: a Navy branch fortress the way the anime draws
them on East Blue and Paradise islands (153rd branch ep 2-3, Loguetown ep 48-53, Navarone ep 197): white walls with
blue trim, a tall white headquarters with the round command tower and the big MARINE letters, the gull crest.

Silhouette first: the HQ block (4 storeys) with the cylindrical tower rising out of its middle to a blue cone roof
and a lightning rod, MARINE in blue on the tower face, the gull crest above the doors, round corner towers with blue
cone caps on a white curtain wall, the flagpole in the drill yard, a warship at the quay.

Inside the walls: the HQ (office floors, the commander's office on top with the base's chest, Garp's guest room),
barracks (two storeys, bunk rooms), the mess hall with kitchen, the armory, the jail block with barred cells, the
drill yard with training posts and targets, the gatehouse. Outside: the harbour basin with quay, cannon battery,
crane, stacked crates and the sloop. 144 x 132, land site, yard at y 2, harbour water y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, tier, cornice, wing_floor, lamp_post, glyph, steady
from mcb.kit_interiors import furnish_kit, bench, bar_counter
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "marine_base"
TITLE = "Marine Branch Base"
CUTS = [3, 12, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 144, 132
GY = 2                              # yard level
X1, Z1, X2, Z2 = 22, 14, 122, 88    # curtain wall
GATE_X = 72
HX1, HZ1, HX2, HZ2 = 50, 22, 94, 44  # HQ block
TCX, TCZ = 72, 40                   # command tower centre (front of the HQ)
WHITE = "minecraft:white_concrete"
BLUE = "minecraft:blue_concrete"
LBLUE = "minecraft:light_blue_concrete"
_LAND = NT.outline(72, 62, 66, 9101, wobble=0.12)
QUAY_Z = 100                        # harbour basin from here south
BZ2 = NZ - 6                        # basin's south breakwater


def basin(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (Z >= QUAY_Z) & (Z <= BZ2) & (X >= 33) & (X <= 111)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    h = 1 + NT.fbm(X, Z, 9102, 18) * 4
    inside = (X >= X1 - 4) & (X <= X2 + 4) & (Z >= Z1 - 4) & (Z <= QUAY_Z - 1)
    h = np.where(inside, GY, h)
    h = np.where(d < 10, np.minimum(h, GY) * np.clip(d / 10.0, 0, 1) + (h - np.minimum(h, GY)) * 0, h)
    h = np.where(basin(X, Z), -6, h)
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def onland(X, Z):
    return (_LAND(np.asarray(X, float), np.asarray(Z, float)) > 0) | basin(X, Z)


def terrain(bb):
    yard = lambda X, Z: (X >= X1) & (X <= X2) & (Z >= Z1) & (Z <= Z2)
    quay = lambda X, Z: (Z > Z2) & (Z < QUAY_Z) & (np.abs(X - 72) < 44)
    out = lambda X, Z: (_LAND(X, Z) > 0) & ~yard(X, Z) & ~quay(X, Z) & ~basin(X, Z)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, NT.MEADOW, 9103, mask=out, core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:gravel", 0.3), ("minecraft:dirt_path", 0.0), ("minecraft:coarse_dirt", 0.25),
                                                 ("minecraft:packed_mud", 0.15), ("minecraft:andesite", 0.3)], 9104, mask=yard,
             core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:stone_bricks", 0.5), ("minecraft:polished_andesite", 0.3),
                                                 ("minecraft:cracked_stone_bricks", 0.2)], 9105, mask=quay, under="minecraft:stone",
             core="minecraft:stone", base=-8)
    # harbour basin: stone walls, water to y 0
    bx1, bx2 = 33, 111
    bb.fill(bx1, -7, QUAY_Z, bx2, -7, BZ2, "minecraft:gravel")
    bb.fill(bx1, -6, QUAY_Z, bx2, 0, BZ2, "minecraft:water")
    for x in (bx1 - 1, bx2 + 1):
        bb.fill(x, -7, QUAY_Z, x, GY, BZ2 + 1, "minecraft:stone_bricks")
    bb.fill(bx1 - 1, -7, BZ2 + 1, bx2 + 1, GY, BZ2 + 2, "minecraft:stone_bricks")
    bb.fill(bx1 - 1, GY + 1, BZ2 + 2, bx2 + 1, GY + 1, BZ2 + 2, "minecraft:stone_brick_wall")
    for x in (bx1 + 6, bx2 - 6):
        bb.fill(x, GY + 1, BZ2 + 1, x, GY + 6, BZ2 + 1, "minecraft:white_concrete")
        bb.set(x, GY + 7, BZ2 + 1, "minecraft:redstone_lamp[lit=true]")
    bb.fill(bx1 - 1, -7, QUAY_Z - 1, bx2 + 1, GY, QUAY_Z - 1, "minecraft:stone_bricks")
    bb.fill(bx1 - 1, GY + 1, QUAY_Z - 1, bx2 + 1, GY + 1, QUAY_Z - 1, "minecraft:stone_brick_wall")
    for x in range(bx1, bx2 + 1, 8):
        bb.set(x, GY + 1, QUAY_Z - 1, "minecraft:polished_andesite")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 9106, density=0.18, kinds=NT.PLANTS_MEADOW, flowers=["minecraft:cornflower", "minecraft:oxeye_daisy"],
              mask=out)


def round_tower(bb, x, z, r, h, y0=GY):
    bb.cylinder(x, y0 - 4, z, r + 1, y0, "minecraft:stone_bricks")
    bb.cylinder(x, y0 + 1, z, r, y0 + h, WHITE, hollow=True)
    for yy in (y0 + 5, y0 + h - 1):
        bb.ring(x, yy, z, r, r + 1, yy, LBLUE) if False else bb.cylinder(x, yy, z, r, yy, BLUE, hollow=True)
    for k in range(1, h // 5):
        for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
            bb.fill(x + dx, y0 + 5 * k + 1, z + dz, x + dx, y0 + 5 * k + 2, z + dz, "minecraft:glass_pane")
    for k in range(h // 5 + 1):
        bb.cylinder(x, y0 + 5 * k, z, r - 1, y0 + 5 * k, "minecraft:spruce_planks")
        bb.fill(x, y0 + 5 * k, z - r + 1, x, y0 + 5 * k, z - r + 1, AIR)
    bb.fill(x, y0 + 1, z - r + 1, x, y0 + h, z - r + 1, "minecraft:ladder[facing=south]")
    top = y0 + h + 1
    bb.cylinder(x, top - 1, z, r + 1, top - 1, "minecraft:smooth_stone")
    for a in range(0, 360, 20):
        t = math.radians(a)
        bb.set(x + int(round((r + 1) * math.cos(t))), top, z + int(round((r + 1) * math.sin(t))), WHITE if a % 40 else "minecraft:white_concrete")
    P.cone_roof(bb, x, top + 2, z, r + 1, r + 3, BLUE)
    for (dx, dz) in ((r + 1, 0), (-r - 1, 0), (0, r + 1), (0, -r - 1)):
        bb.fill(x + dx, top + 1, z + dz, x + dx, top + 1, z + dz, "minecraft:white_concrete")


def curtain(bb):
    """White curtain wall with a blue band, wall walk with crenels, corner and mid towers, the gatehouse."""
    for (a, b, c, d) in ((X1, Z1, X2, Z1), (X1, Z2, X2, Z2), (X1, Z1, X1, Z2), (X2, Z1, X2, Z2)):
        bb.fill(a, GY - 4, b, c, GY, d, "minecraft:stone_bricks")
        bb.fill(a, GY + 1, b, c, GY + 8, d, WHITE)
        bb.fill(a, GY + 6, b, c, GY + 6, d, BLUE)
        bb.fill(a, GY + 9, b, c, GY + 9, d, "minecraft:white_concrete")
    # inner walk + crenels (merlons every other block)
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            if x % 2 == 0:
                bb.set(x, GY + 10, z, WHITE)
    for z in range(Z1, Z2 + 1):
        for x in (X1, X2):
            if z % 2 == 0:
                bb.set(x, GY + 10, z, WHITE)
    bb.fill(X1 + 1, GY + 9, Z1 + 1, X2 - 1, GY + 9, Z1 + 1, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(X1 + 1, GY + 9, Z2 - 1, X2 - 1, GY + 9, Z2 - 1, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(X1 + 1, GY + 9, Z1 + 1, X1 + 1, GY + 9, Z2 - 1, "minecraft:smooth_stone_slab[type=top]")
    bb.fill(X2 - 1, GY + 9, Z1 + 1, X2 - 1, GY + 9, Z2 - 1, "minecraft:smooth_stone_slab[type=top]")
    # pilasters on the outside every 8
    for x in range(X1 + 4, X2, 8):
        bb.fill(x, GY + 1, Z1 - 1, x, GY + 8, Z1 - 1, "minecraft:quartz_pillar[axis=y]")
        bb.fill(x, GY + 1, Z2 + 1, x, GY + 8, Z2 + 1, "minecraft:quartz_pillar[axis=y]")
    for z in range(Z1 + 4, Z2, 8):
        bb.fill(X1 - 1, GY + 1, z, X1 - 1, GY + 8, z, "minecraft:quartz_pillar[axis=y]")
        bb.fill(X2 + 1, GY + 1, z, X2 + 1, GY + 8, z, "minecraft:quartz_pillar[axis=y]")
    for (x, z) in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        round_tower(bb, x, z, 5, 16)
    for (x, z) in ((X1, (Z1 + Z2) // 2), (X2, (Z1 + Z2) // 2)):
        round_tower(bb, x, z, 4, 13)
    # the gatehouse on the south wall, opening to the quay
    gx = GATE_X
    bb.fill(gx - 7, GY + 1, Z2 - 3, gx + 7, GY + 14, Z2 + 3, WHITE)
    bb.fill(gx - 3, GY + 1, Z2 - 3, gx + 3, GY + 7, Z2 + 3, AIR)
    for dx in (-3, 3):
        bb.set(gx + dx, GY + 7, Z2 + 3, "minecraft:quartz_stairs[facing=" + ("east" if dx < 0 else "west") + ",half=top]")
    bb.fill(gx - 7, GY + 11, Z2 + 4, gx + 7, GY + 11, Z2 + 4, BLUE)
    bb.fill(gx - 7, GY + 14, Z2 - 3, gx + 7, GY + 14, Z2 + 3, "minecraft:light_gray_concrete")
    for x in range(gx - 7, gx + 8, 2):
        bb.set(x, GY + 15, Z2 - 3, WHITE); bb.set(x, GY + 15, Z2 + 3, WHITE)
    bb.fill(gx - 2, GY + 8, Z2 - 2, gx + 2, GY + 12, Z2 + 2, AIR)
    furnish_kit(bb, (gx - 2, Z2 - 2, gx + 2, Z2 + 2), GY + 8, 4, "office", wood="birch", seed=9107, doors=[], accent="blue")
    for dz in (-2, 2):
        bb.fill(gx - 6, GY + 1, Z2 + dz, gx - 6, GY + 9, Z2 + dz, AIR) if False else None
    bb.fill(gx - 5, GY + 1, Z2 - 2, gx - 5, GY + 8, Z2 - 2, "minecraft:ladder[facing=east]")
    bb.fill(gx - 6, GY + 1, Z2 - 2, gx - 6, GY + 1, Z2 - 2, WHITE)
    bb.fill(gx - 5, GY + 1, Z2 - 3, gx - 5, GY + 2, Z2 - 3, AIR)
    for x in range(gx - 2, gx + 3):
        bb.set(x, GY + 7, Z2 + 3, "minecraft:iron_bars")
    for z in (Z2 + 5,):
        for dx in (-5, 5):
            lamp_post(bb, gx + dx, GY + 1, z, post="minecraft:birch_fence", h=4)


def hq(bb, tracker):
    """Four white storeys, light-blue bands, quartz pilasters, a deep porch; the round command tower in front with
    MARINE letters and the gull crest, commander's office in the tower top."""
    top = tier(bb, HX1, HZ1, HX2, HZ2, GY, 4, 5, WHITE, "minecraft:glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band=LBLUE, top_plate="minecraft:light_gray_concrete", every=3, pil_every=4)
    cornice(bb, HX1, HZ1, HX2, HZ2, top, "minecraft:quartz_stairs", parapet=WHITE)
    kinds = [("dining", "kitchen", "storage"), ("library", "office" if False else "living", "bedroom"),
             ("bedroom", "bedroom", "living"), ("library", "living", "bedroom")]
    for k in range(4):
        wing_floor(bb, HX1 + 1, HZ1 + 1, HX2 - 1, HZ2 - 1, GY + 1 + 5 * k, 4, WHITE, seed_of("mb_hq", k), tracker, kinds[k],
                   corridor="x", cw=3, carpet=(None, "minecraft:light_blue_carpet"), wood="birch",
                   keep=[(HX1 + 1, HZ1 + 1, HX1 + 3, HZ1 + 3), (TCX - 7, HZ2 - 7, TCX + 7, HZ2 - 1)])
    bb.fill(HX1 + 2, GY + 1, HZ1 + 2, HX1 + 2, top, HZ1 + 2, "minecraft:ladder[facing=south]")
    bb.fill(HX1 + 2, top + 1, HZ1 + 2, HX1 + 2, top + 1, HZ1 + 2, AIR)
    # the command tower: cylinder r 7 centred on the front face, 4 floors above the roof
    R = 7
    T = top + 18
    bb.cylinder(TCX, GY - 3, TCZ, R + 1, GY, "minecraft:stone_bricks")
    bb.cylinder(TCX, GY + 1, TCZ, R, T, WHITE, hollow=True)
    for yy in range(GY + 5, T, 5):
        bb.cylinder(TCX, yy, TCZ, R, yy, LBLUE, hollow=True)
        bb.cylinder(TCX, yy, TCZ, R - 1, yy, "minecraft:birch_planks")
    for k, yy in enumerate(range(GY + 6, T - 2, 5)):
        for a in range(0, 360, 30):
            t = math.radians(a)
            px, pz = TCX + int(round(R * math.cos(t))), TCZ + int(round(R * math.sin(t)))
            if pz > TCZ + 3:
                continue
            bb.fill(px, yy + 1, pz, px, yy + 2, pz, "minecraft:glass_pane")
    bb.fill(TCX + R - 2, GY + 1, TCZ, TCX + R - 2, T, TCZ, "minecraft:ladder[facing=west]")
    for yy in range(GY + 5, T, 5):
        bb.set(TCX + R - 2, yy, TCZ, "minecraft:ladder[facing=west]")
    # tower ground floor opens into the HQ hall; front doors
    bb.fill(TCX - 2, GY + 1, TCZ + R, TCX + 2, GY + 4, TCZ + R, AIR)
    bb.fill(TCX - 2, GY + 1, HZ2, TCX + 2, GY + 3, HZ2, AIR)
    # the commander's office at the top of the tower
    OY = T - 4
    furnish_kit(bb, (TCX - 4, TCZ - 4, TCX + 3, TCZ + 4), OY + 1, 3, "office", wood="dark_oak", seed=9108, doors=[(TCX + R - 2, TCZ)], accent="blue")
    bb.cylinder(TCX, T, TCZ, R + 1, T, "minecraft:smooth_stone")
    for a in range(0, 360, 15):
        t = math.radians(a)
        bb.set(TCX + int(round((R + 1) * math.cos(t))), T + 1, TCZ + int(round((R + 1) * math.sin(t))), WHITE)
    P.cone_roof(bb, TCX, T + 2, TCZ, R + 1, 10, BLUE)
    bb.fill(TCX, T + 12, TCZ, TCX, T + 16, TCZ, "minecraft:iron_bars")
    bb.set(TCX, T + 17, TCZ, "minecraft:lightning_rod")
    # porch: four quartz columns, blue canopy
    for x in (TCX - 6, TCX - 2, TCX + 2, TCX + 6):
        bb.fill(x, GY + 1, TCZ + R + 4, x, GY + 6, TCZ + R + 4, "minecraft:quartz_pillar[axis=y]")
    bb.fill(TCX - 7, GY + 7, TCZ + R, TCX + 7, GY + 7, TCZ + R + 5, LBLUE)
    bb.fill(TCX - 7, GY + 8, TCZ + R + 1, TCX + 7, GY + 8, TCZ + R + 5, "minecraft:quartz_slab[type=bottom]")
    bb.fill(TCX - 6, GY, TCZ + R + 1, TCX + 6, GY, TCZ + R + 6, "minecraft:polished_diorite")
    gull = ["..#.......#..", ".###.....###.", "#####...#####", "..#########..", "....#####....", "......#......"]
    # the signboard on the tower front: MARINE (written in build()) under the gull crest
    bb.fill(TCX - 13, GY + 9, TCZ + R, TCX + 13, GY + 24, TCZ + R, WHITE)
    bb.fill(TCX - 13, GY + 9, TCZ + R + 1, TCX + 13, GY + 9, TCZ + R + 1, BLUE)
    bb.fill(TCX - 13, GY + 24, TCZ + R + 1, TCX + 13, GY + 24, TCZ + R + 1, BLUE)
    bb.fill(TCX - 13, GY + 9, TCZ + R + 1, TCX - 13, GY + 24, TCZ + R + 1, BLUE)
    bb.fill(TCX + 13, GY + 9, TCZ + R + 1, TCX + 13, GY + 24, TCZ + R + 1, BLUE)
    glyph(bb, gull, TCX - 6, GY + 23, TCZ + R + 1, BLUE, axis="x")          # rows run downward from y
    return top, T, OY


def barracks(bb, tracker, x1, z1, x2, z2, floors, kinds, seed):
    top = tier(bb, x1, z1, x2, z2, GY, floors, 5, WHITE, "minecraft:glass_pane", "minecraft:smooth_stone_slab",
               band=LBLUE, top_plate="minecraft:light_gray_concrete", every=3)
    for k in range(floors):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, GY + 1 + 5 * k, 4, WHITE, seed_of(seed, k), tracker, kinds,
                   corridor="x" if x2 - x1 > z2 - z1 else "z", cw=3, wood="birch", keep=[(x1 + 1, z1 + 1, x1 + 3, z1 + 3)])
    bb.fill(x1 + 2, GY + 1, z1 + 2, x1 + 2, top - 1, z1 + 2, "minecraft:ladder[facing=south]")
    bb.fill(x1 - 1, top, z1 - 1, x2 + 1, top, z2 + 1, LBLUE)
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:deepslate_tile_stairs", gable_fill=WHITE, overhang=1)
    return top


def jail(bb):
    """The jail block: thick grey walls, a corridor between two rows of barred cells, a guard desk."""
    x1, z1, x2, z2 = 98, 58, 118, 74
    bb.fill(x1, GY + 1, z1, x2, GY + 6, z2, "minecraft:stone_bricks")
    bb.fill(x1 + 1, GY + 1, z1 + 1, x2 - 1, GY + 5, z2 - 1, AIR)
    bb.fill(x1, GY + 6, z1, x2, GY + 6, z2, "minecraft:smooth_stone")
    cz = (z1 + z2) // 2
    for x in range(x1 + 1, x2, 4):
        for (za, zb) in ((z1 + 1, cz - 2), (cz + 2, z2 - 1)):
            bb.fill(x, GY + 1, za, x, GY + 5, zb, "minecraft:stone_bricks")
            bb.fill(x + 1, GY + 1, cz - 2 if za < cz else cz + 2, x + 3, GY + 3, cz - 2 if za < cz else cz + 2, "onepiece:prison_bars")
            bb.set(x + 2, GY + 1, za if za < cz else zb, "minecraft:white_bed[facing=" + ("north" if za < cz else "south") + ",part=head]" if False else "minecraft:white_carpet")
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            bb.set(x, GY + 4, z, "minecraft:iron_bars")
    bb.fill(x1, GY + 1, cz, x1, GY + 3, cz, AIR)
    bb.set(x1 + 2, GY + 1, cz + 1, "minecraft:spruce_stairs[facing=east]")
    bb.set(x1 + 3, GY + 1, cz + 1, "minecraft:spruce_slab[type=top]")
    for x in range(x1 + 3, x2 - 2, 5):
        bb.set(x, GY + 5, cz, "minecraft:lantern[hanging=true]")
    return (x1, z1, x2, z2)


def mess_hall(bb):
    x1, z1, x2, z2 = 26, 58, 48, 82
    top = tier(bb, x1, z1, x2, z2, GY, 1, 6, WHITE, "minecraft:glass_pane", "minecraft:smooth_stone_slab", band=LBLUE,
               top_plate="minecraft:light_gray_concrete", every=3)
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z1 + 15), GY + 1, 5, "dining", wood="birch", seed=9109, doors=[(x2, z1 + 8)], accent="blue")
    furnish_kit(bb, (x1 + 1, z1 + 17, x2 - 1, z2 - 1), GY + 1, 5, "kitchen", wood="birch", seed=9110, doors=[(x2, z2 - 3)], accent="blue")
    bb.fill(x1 + 1, GY + 1, z1 + 16, x2 - 1, GY + 5, z1 + 16, WHITE)
    bb.fill(x1 + 10, GY + 1, z1 + 16, x1 + 11, GY + 3, z1 + 16, AIR)
    for z in (z1 + 8, z2 - 3):
        bb.fill(x2, GY + 1, z, x2, GY + 3, z, AIR)
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:deepslate_tile_stairs", gable_fill=WHITE, overhang=1)
    bb.fill(x1 + 3, top + 1, z2 - 4, x1 + 3, top + 9, z2 - 4, "minecraft:bricks")


def armory(bb):
    x1, z1, x2, z2 = 94, 20, 116, 34
    top = tier(bb, x1, z1, x2, z2, GY, 1, 6, ["minecraft:stone_bricks", "minecraft:polished_andesite"], "minecraft:iron_bars",
               "minecraft:smooth_stone_slab", band=BLUE, top_plate="minecraft:smooth_stone", every=4)
    for x in range(x1 + 2, x2 - 1, 3):
        bb.set(x, GY + 1, z1 + 1, "minecraft:barrel[facing=up]")
        bb.set(x, GY + 2, z1 + 1, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true]" if False else "minecraft:smithing_table" if x % 2 else "minecraft:grindstone[face=floor,facing=north]")
    for x in range(x1 + 2, x2 - 1, 4):
        bb.set(x, GY + 1, z2 - 2, "onepiece:cannonball_pile")
        bb.set(x + 1, GY + 1, z2 - 2, "onepiece:cannon[facing=south]")
    bb.fill(x1 + 1, GY + 1, z1 + 5, x2 - 1, GY + 1, z1 + 5, "minecraft:birch_slab[type=top]")
    bb.fill((x1 + x2) // 2, GY + 1, z2, (x1 + x2) // 2 + 1, GY + 3, z2, AIR)
    bb.set(x1 + 3, GY + 1, z1 + 8, "minecraft:anvil[facing=north]")
    cornice(bb, x1, z1, x2, z2, top, "minecraft:stone_brick_stairs", merlons="minecraft:stone_brick_wall")


def yard(bb):
    """Drill yard: the flagpole on a stepped plinth, rows of training posts, a target range, benches, lamps."""
    fx, fz = TCX, 60
    bb.fill(fx - 3, GY + 1, fz - 3, fx + 3, GY + 1, fz + 3, "minecraft:polished_andesite")
    bb.fill(fx - 2, GY + 2, fz - 2, fx + 2, GY + 2, fz + 2, "minecraft:smooth_stone")
    bb.fill(fx, GY + 3, fz, fx, GY + 26, fz, "minecraft:iron_bars")
    for u in range(10):
        for v in range(6):
            gull = (v == 2 and 2 <= u <= 7) or (v == 1 and u in (1, 2, 7, 8)) or (v == 3 and 4 <= u <= 5)
            bb.set(fx + 1 + u, GY + 26 - v, fz, BLUE.replace("concrete", "wool") if gull else "minecraft:white_wool")
    # training posts: dummies (fence + hay + carved pumpkin face away)
    for k in range(6):
        x, z = 54 + k * 4, 70
        bb.set(x, GY + 1, z, "minecraft:spruce_fence"); bb.set(x, GY + 2, z, "minecraft:hay_block"); bb.set(x, GY + 3, z, "minecraft:carved_pumpkin[facing=north]")
        bb.set(x, GY + 2, z + 4, "minecraft:target"); bb.set(x, GY + 1, z + 4, "minecraft:spruce_fence")
    for x in (52, 92):
        for z in (52, 66, 80):
            lamp_post(bb, x, GY + 1, z, post="minecraft:birch_fence", h=4)
    for z in (52, 58, 64):
        bench(bb, 56, GY + 1, z, 5, "x", "birch") if False else bb.fill(55, GY + 1, z, 59, GY + 1, z, "minecraft:birch_stairs[facing=north]")
    # paths
    bb.fill(GATE_X - 2, GY, TCZ + R0 + 6, GATE_X + 2, GY, Z2 - 1, "minecraft:polished_andesite")
    bb.fill(50, GY, 50, 94, GY, 52, "minecraft:polished_andesite")


R0 = 7


def harbour(bb):
    """Quay with a cannon battery facing the sea, a crane, stacked crates, a pier, and the sloop moored."""
    for x in range(38, 108, 6):
        bb.set(x, GY + 1, QUAY_Z - 2, "onepiece:cannon[facing=south]")
        bb.set(x + 1, GY + 1, QUAY_Z - 3, "onepiece:cannonball_pile")
    for (x, z) in ((46, 92), (47, 92), (46, 93), (98, 93), (99, 93), (98, 92)):
        bb.set(x, GY + 1, z, "minecraft:barrel[facing=up]")
    bb.fill(90, GY + 1, 92, 92, GY + 2, 94, "minecraft:spruce_planks")
    bb.fill(90, GY + 3, 92, 91, GY + 3, 93, "minecraft:barrel[facing=up]")
    # crane
    cx, cz = 102, QUAY_Z - 3
    bb.fill(cx, GY + 1, cz, cx, GY + 12, cz, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(cx, GY + 12, cz, cx, GY + 12, cz + 8, "minecraft:dark_oak_planks")
    bb.fill(cx, GY + 4, cz + 8, cx, GY + 11, cz + 8, "minecraft:iron_chain[axis=y]")
    bb.set(cx, GY + 3, cz + 8, "minecraft:barrel[facing=up]")
    # pier into the basin
    for z in range(QUAY_Z, QUAY_Z + 24):
        bb.fill(60, 1, z, 64, 1, z, "minecraft:spruce_planks")
        if z % 4 == 0:
            bb.fill(59, -6, z, 59, 2, z, "minecraft:stripped_spruce_log[axis=y]")
            bb.fill(65, -6, z, 65, 2, z, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(60, 1, QUAY_Z - 1, 64, 2, QUAY_Z - 1, "minecraft:polished_andesite")
    bb.fill(60, 2, QUAY_Z - 1, 64, 2, QUAY_Z - 1, AIR)
    stamp_ship(bb, "marine_warship", 84, QUAY_Z + 18, water_y=0, rot=0)


def design():
    bb = BigBuild(seed=9100, y_min=-12, y_max=100)
    tracker = P.PropTracker(9100)
    terrain(bb)
    curtain(bb)
    top, T, OY = hq(bb, tracker)
    barracks(bb, tracker, 26, 22, 44, 50, 2, ("bedroom", "bedroom", "storage"), "mb_bar_w")
    mess_hall(bb)
    armory(bb)
    cells = jail(bb)
    yard(bb)
    harbour(bb)
    return bb, [], top, T, OY, cells


def build():
    bb, audit, top, T, OY, cells = design()
    b = to_canvas(bb)
    steady(b)
    b.text(TCX - 11, GY + 11, TCZ + R0 + 1, "MARINE", BLUE, axis="x", step=1)
    b.chest(TCX - 3, OY + 1, TCZ - 3, "marine", "south")
    b.chest(96, GY + 1, 22, "marine", "south")
    b.chest(cells[0] + 2, GY + 1, cells[1] + 2, "medium", "east")
    b.npc(TCX + 2, OY + 1, TCZ - 2, "garp", False)
    for (x, z, kit) in ((GATE_X - 4, Z2 + 6, "marine"), (GATE_X + 4, Z2 + 6, "marine"), (TCX, 62, "elite_marine"), (60, 72, "marine_rifle"),
                        (cells[0] + 4, (cells[1] + cells[3]) // 2, "marine"), (80, QUAY_Z - 4, "marine_rifle")):
        b.guard(x, GY + 1, z, kit)
    return b, 0
