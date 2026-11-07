"""Tequila Wolf v2, redesigned with the Minecraft Builder skill: the endless bridge in the East Blue, built for over
700 years by slaves of the World Government (anime ep. 420 / 455: Robin lands in the snow on it, Soran shelters her,
the Revolutionary Army frees the workers from the prison tower).

Silhouette first: one colossal grey stone bridge striding across open sea on giant square piers, each pier pierced by
a small arch and joined to the next by a huge round arch, a wide snowy deck with a whole slave town on it, and the
west end unfinished: the last arch only half built on timber centering, the deck ending in scaffolding and cranes
over the void, with stone blocks hauled up from barges. The tall prison tower stands on the east end.

Inside the bridge (a vaulted gallery under the deck): the stonecutters' workshops, the store of cut blocks, the
soup kitchen and the barrack dormitories. On the deck: rows of workers' huts, the overseers' office, guard towers
along the parapets, the whipping post square, block stacks, sledges and cranes; the prison tower with cells on every
floor and the chief's room on top. Barges and work boats below. 212 x 76, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, tier, cornice, lamp_post, steady, house_module, place_house
from mcb.kit_interiors import furnish_kit, bench, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "tequila_wolf"
TITLE = "Tequila Wolf"
WATER_Y = 0
CUTS = [14, 26, 34]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")
EDGE_REACH = 2

NX, NZ = 212, 76
CZ = 38
HW = 16                  # half width of the bridge (z CZ-16..CZ+16)
DECK = 26                # deck surface (blocks at y DECK, people stand at DECK+1)
GAL = 17                 # gallery floor inside the bridge
PIERS = [26, 64, 102, 140, 178]   # pier centres (x); 38 apart
PW = 6                   # half thickness of a pier along x
WEST_END = 14            # the deck stops here (scaffolding beyond)
STONE = ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:andesite", "minecraft:polished_andesite",
         "minecraft:mossy_stone_bricks"]
SW = [0.5, 0.14, 0.14, 0.14, 0.08]
DARK = ["minecraft:deepslate_bricks", "minecraft:cracked_deepslate_bricks", "minecraft:deepslate_tiles"]


def arch_y(x):
    """Underside of the deck structure at x: piers are solid, the spans between them are round arches (crown y 20)."""
    for i in range(len(PIERS) - 1):
        a, b = PIERS[i] + PW, PIERS[i + 1] - PW
        if a < x < b:
            r = (b - a) / 2.0
            c = (a + b) / 2.0
            return 6 + math.sqrt(max(r * r - (x - c) ** 2, 0)) * (13.0 / r)
    return -30


def bridge_body(bb):
    z1, z2 = CZ - HW, CZ + HW
    xe = PIERS[-1] + PW + 12
    # piers from the sea bed: battered (wider at the waterline), cutwaters pointing up and down stream
    for px in PIERS:
        for y in range(-12, DECK):
            grow = 2 if y < 2 else (1 if y < 6 else 0)
            bb.mix(px - PW - grow, y, z1 - grow, px + PW + grow, y, z2 + grow, STONE, SW)
        for k in range(8):          # cutwaters (pointed noses on both long faces) up to y 10
            for y in range(-12, 10 - k // 2):
                bb.fill(px - PW + k, y, z1 - 1 - (7 - k), px + PW - k, y, z1 - 1 - (7 - k), "minecraft:stone_bricks") if k < PW else None
                bb.fill(px - PW + k, y, z2 + 1 + (7 - k), px + PW - k, y, z2 + 1 + (7 - k), "minecraft:stone_bricks") if k < PW else None
        # small pedestrian arch through each pier along z at sea level (boats pass)
        for x in range(px - 3, px + 4):
            for y in range(0, 10):
                if (x - px) ** 2 / 9.0 + (y - 2) ** 2 / 49.0 <= 1 or y < 3:
                    bb.fill(x, y, z1 - 2, x, y, z2 + 2, AIR if y > 0 else "minecraft:water")
        bb.fill(px - 3, -1, z1 - 2, px + 3, -1, z2 + 2, "minecraft:stone_bricks")
        # string course and the dark tide band
        bb.fill(px - PW - 1, 10, z1 - 1, px + PW + 1, 10, z2 + 1, "minecraft:polished_andesite")
        bb.fill(px - PW - 2, -1, z1 - 2, px + PW + 2, 1, z2 + 2, "minecraft:mossy_stone_bricks")
    # the spans: solid masonry from the arch line up to the deck
    for x in range(WEST_END + 8, xe + 1):
        ay = arch_y(x)
        if ay < -20:
            continue
        y0 = int(math.ceil(ay))
        bb.mix(x, y0, z1, x, DECK, z2, STONE, SW)
        bb.fill(x, y0, z1, x, y0, z2, "minecraft:polished_andesite")        # voussoir line
    # buttresses standing 1 proud over every pier up to the parapet, with a lamp niche
    for px in PIERS:
        for z in (z1 - 1, z2 + 1):
            bb.fill(px - 3, 10, z, px + 3, DECK - 2, z, "minecraft:stone_bricks")
            bb.fill(px - 2, 11, z, px + 2, DECK - 3, z, "minecraft:polished_andesite")
            bb.set(px, DECK - 6, z, "minecraft:lantern")
            bb.fill(px - 3, DECK - 2, z, px + 3, DECK - 2, z, f"minecraft:stone_brick_stairs[facing={'south' if z < CZ else 'north'},half=bottom]")
    # the east abutment beyond the last pier
    for y in range(-12, DECK + 1):
        bb.mix(PIERS[-1] + PW, y, z1, xe, y, z2, STONE, SW)
    # the gallery: a vaulted hall inside the bridge between the arch crowns and the deck, the whole length
    for x in range(WEST_END + 10, xe - 2):
        if any(abs(x - px) <= PW for px in PIERS) or arch_y(x) < GAL - 1:
            for z in range(z1 + 3, z2 - 2):
                for y in range(GAL, DECK - 1):
                    if (z - CZ) ** 2 / (HW - 3) ** 2 + (y - GAL) ** 2 / 64.0 <= 1:
                        bb.set(x, y, z, AIR)
            bb.fill(x, GAL - 1, z1 + 3, x, GAL - 1, z2 - 3, "minecraft:spruce_planks" if x % 7 else "minecraft:stripped_spruce_log[axis=z]")
    # arrow-slit windows into the gallery on both faces every 4
    for x in range(WEST_END + 12, xe - 4, 4):
        if arch_y(x) < GAL - 2 or any(abs(x - px) <= PW for px in PIERS):
            for z in (z1, z2):
                bb.fill(x, GAL + 1, z, x, GAL + 3, z, "minecraft:iron_bars")
    # deck: paving with a snowy crust, parapets with merlons, a cornice of corbels under it
    bb.mix(WEST_END, DECK, z1, xe, DECK, z2, ["minecraft:stone_bricks", "minecraft:polished_andesite", "minecraft:cobblestone", "minecraft:gravel"],
           [0.45, 0.25, 0.25, 0.05])
    for x in range(WEST_END, xe + 1):
        for z in (z1 - 1, z2 + 1):
            bb.set(x, DECK - 1, z, f"minecraft:stone_brick_stairs[facing={'south' if z < CZ else 'north'},half=top]")
            bb.set(x, DECK, z, "minecraft:stone_bricks")
            bb.set(x, DECK + 1, z, "minecraft:stone_bricks")
            if x % 3 == 0:
                bb.set(x, DECK + 2, z, "minecraft:stone_brick_wall")
    snow = lambda X, Z: NT.noise(X, Z, 4201, 6) > 0.38
    bb.fill_where(WEST_END, DECK + 1, z1, xe, DECK + 1, z2, lambda X, y, Z: snow(X, Z), "minecraft:snow[layers=1]", only_empty=True)
    return xe


def gallery_rooms(bb):
    """Workshops, block store, soup kitchen and dormitories in the gallery bays between the piers."""
    z1, z2 = CZ - HW + 4, CZ + HW - 4
    kinds = ["workshop", "storeroom", "kitchen", "barracks", "mess", "barracks", "workshop", "barracks"]
    k = 0
    for i in range(len(PIERS) - 1):
        a, b = PIERS[i] + PW + 3, PIERS[i + 1] - PW - 3
        mid = (a + b) // 2
        for (x1, x2) in ((a, mid - 1), (mid + 1, b)):
            furnish_kit(bb, (x1, z1 + 1, x2, z2 - 1), GAL, 5, kinds[k % len(kinds)], wood="spruce", seed=4210 + k,
                        doors=[(x1, CZ), (x2, CZ)], accent="gray")
            k += 1
        bb.fill(mid, GAL, z1, mid, GAL + 5, z2, "minecraft:stone_bricks")
        bb.fill(mid, GAL, CZ - 1, mid, GAL + 2, CZ + 1, AIR)
    # lamps in the vault and stairs up to the deck at every pier
    for x in range(WEST_END + 12, PIERS[-1] + PW, 6):
        bb.set(x, GAL + 6, CZ, "minecraft:lantern[hanging=true]") if bb.get_region(x, GAL + 7, CZ, x, GAL + 7, CZ)[0, 0, 0] > 1 else None
    for px in PIERS:
        for k in range(DECK - GAL):
            bb.fill(px - 4 + k, GAL + k, CZ + HW - 6, px - 4 + k, GAL + k, CZ + HW - 5, "minecraft:stone_brick_stairs[facing=east]")
            bb.fill(px - 4 + k, GAL + k + 1, CZ + HW - 6, px - 4 + k, GAL + k + 4, CZ + HW - 5, AIR)
        bb.fill(px - 4 + DECK - GAL - 1, DECK, CZ + HW - 6, px + 4, DECK, CZ + HW - 5, AIR)


def unfinished_end(bb):
    """The west end: the last arch half built over timber centering, scaffolding and cranes over the open end."""
    x0 = PIERS[0] - PW
    z1, z2 = CZ - HW, CZ + HW
    # a half-built pier further west standing in the sea, only up to y 12
    for y in range(-12, 13):
        bb.mix(2, y, z1 + 2, 9, y, z2 - 2, STONE, SW)
    bb.fill(2, 13, z1 + 2, 9, 13, z2 - 2, "minecraft:cobblestone")
    for (x, z) in ((3, z1 + 3), (8, z2 - 3), (5, CZ)):
        bb.fill(x, 14, z, x, 14 + (x % 3), z, "minecraft:stone_bricks")
    # timber centering for the next arch between x 10 and x0: a wooden semicircle with trestle legs
    c, r = (10 + x0) / 2.0, (x0 - 10) / 2.0
    for x in range(10, x0 + 1):
        y = int(6 + math.sqrt(max(r * r - (x - c) ** 2, 0)) * (13.0 / max(r, 1)))
        for z in range(z1 + 2, z2 - 1, 4):
            bb.set(x, y, z, "minecraft:spruce_planks"); bb.set(x, y - 1, z, "minecraft:spruce_fence")
        if x % 4 == 0:
            for z in range(z1 + 2, z2 - 1, 4):
                bb.fill(x, 0, z, x, y - 2, z, "minecraft:spruce_fence")
    # the first courses of voussoirs already laid on the eastern half of the centering
    for x in range(int(c), x0 + 1):
        y = int(6 + math.sqrt(max(r * r - (x - c) ** 2, 0)) * (13.0 / max(r, 1)))
        bb.fill(x, y + 1, z1, x, y + 2, z2, "minecraft:stone_bricks")
    # scaffold tower on the deck end with ladders and planks, two cranes reaching out over the gap
    for x in range(WEST_END, WEST_END + 7, 3):
        for z in range(z1, z2 + 1, 4):
            bb.fill(x, DECK + 1, z, x, DECK + 12, z, "minecraft:spruce_fence")
    for y in (DECK + 4, DECK + 8, DECK + 12):
        bb.fill(WEST_END, y, z1, WEST_END + 6, y, z2, "minecraft:spruce_slab[type=bottom]")
    bb.fill(WEST_END + 1, DECK + 1, CZ, WEST_END + 1, DECK + 12, CZ, "minecraft:ladder[facing=east]")
    for cz in (z1 + 4, z2 - 4):
        bb.fill(WEST_END + 8, DECK + 1, cz, WEST_END + 8, DECK + 16, cz, "minecraft:stripped_spruce_log[axis=y]")
        bb.fill(WEST_END - 6, DECK + 16, cz, WEST_END + 10, DECK + 16, cz, "minecraft:stripped_spruce_log[axis=x]")
        bb.fill(WEST_END - 6, DECK + 6, cz, WEST_END - 6, DECK + 15, cz, "minecraft:iron_chain[axis=y]")
        bb.fill(WEST_END - 7, DECK + 4, cz - 1, WEST_END - 5, DECK + 5, cz + 1, "minecraft:stone_bricks")
        bb.fill(WEST_END + 9, DECK + 1, cz - 1, WEST_END + 10, DECK + 2, cz + 1, "minecraft:cobblestone")   # counterweight
    # the deck simply stops: a ragged edge of unfinished paving
    for z in range(z1, z2 + 1):
        if (z * 7) % 5 < 2:
            bb.set(WEST_END, DECK, z, AIR)


def prison_tower(bb, xe):
    """The prison tower on the east end: a tall square keep with cells on every floor, the chief's room on top."""
    x1, z1 = xe - 22, CZ - 10
    x2, z2 = xe - 2, CZ + 10
    top = tier(bb, x1, z1, x2, z2, DECK, 6, 6, DARK, "minecraft:iron_bars", "minecraft:stone_brick_stairs",
               pilaster="minecraft:polished_deepslate", band="minecraft:polished_andesite", plate="minecraft:stone_bricks",
               top_plate="minecraft:deepslate_tiles", weights=[0.7, 0.2, 0.1], every=3, pil_every=5)
    for f in range(5):
        fy = DECK + 1 + 6 * f
        # a corridor down the middle, cells either side behind iron bars
        for x in range(x1 + 1, x2, 4):
            for z in (CZ - 2, CZ + 2):
                bb.fill(x, fy, z, x, fy + 4, z, "minecraft:polished_deepslate")
            for z0, z3 in ((z1 + 1, CZ - 3), (CZ + 3, z2 - 1)):
                bb.fill(x, fy, z0, x, fy + 4, z3, "minecraft:deepslate_bricks")
            for xx in range(x + 1, min(x + 4, x2)):
                bb.fill(xx, fy, CZ - 2, xx, fy + 3, CZ - 2, "onepiece:prison_bars")
                bb.fill(xx, fy, CZ + 2, xx, fy + 3, CZ + 2, "onepiece:prison_bars")
            if x + 2 < x2:
                for (zc, side) in ((z1 + 2, "north"), (z2 - 2, "south")):
                    bb.set(x + 2, fy, zc, "minecraft:red_carpet" if False else "minecraft:hay_block")
                    bb.set(x + 1, fy, zc, "minecraft:cauldron")
        for x in range(x1 + 3, x2, 5):
            bb.set(x, fy + 4, CZ, "minecraft:lantern[hanging=true]")
    # the chief's room at the top
    fy = DECK + 1 + 6 * 5
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), fy, 5, "captain", wood="dark_oak", seed=4230, doors=[(x1 + 2, z1 + 1)], accent="gray")
    # stair core in the north-west corner on every floor
    for f in range(6):
        fy = DECK + 1 + 6 * f
        bb.fill(x1 + 1, fy - 1, z1 + 1, x1 + 2, fy + 4, z1 + 2, AIR)
        bb.fill(x1 + 1, fy - 1, z1 + 1, x1 + 1, fy + 5, z1 + 1, "minecraft:ladder[facing=east]")
    bb.fill(x1 + 8, DECK + 1, z2, x1 + 10, DECK + 4, z2, AIR)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:deepslate_brick_stairs", merlons="minecraft:deepslate_brick_wall")
    # a pointed slate cap and the World Government flag
    P.hip_roof(bb, x1 + 3, z1 + 3, x2 - 3, z2 - 3, top + 1, "minecraft:deepslate_tile_stairs", ridge="minecraft:deepslate_tile_slab[type=bottom]")
    cx = (x1 + x2) // 2
    bb.fill(cx, top + 10, CZ, cx, top + 20, CZ, "minecraft:iron_bars")
    for u in range(7):
        for v in range(5):
            bb.set(cx + 1 + u, top + 19 - v, CZ, "minecraft:white_wool" if (u - 3) ** 2 + (v - 2) ** 2 > 3 else "minecraft:light_blue_wool")
    return top


def deck_town(bb, tracker, rng, xe):
    """Rows of workers' huts along both parapets, the overseers' office, guard towers, the punishment square."""
    z1, z2 = CZ - HW, CZ + HW
    hut = dict(walls=["minecraft:spruce_planks", "minecraft:stripped_spruce_wood", "minecraft:cobblestone"], frame="minecraft:spruce_log",
               base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks",
               wood="spruce", chimney="minecraft:cobblestone")
    roofs = ["minecraft:spruce_stairs", "minecraft:dark_oak_stairs", "minecraft:cobblestone_stairs"]
    k = 0
    x = WEST_END + 14
    while x < xe - 34:
        w = int(rng.integers(7, 10))
        if abs(x + w / 2 - 102) < 12:                  # the punishment square in the middle
            x += 26
            continue
        for side, rot in ((z1 + 1, 0), (z2 - 8, 2)):
            if rng.random() < 0.12:
                continue
            mod, _, _ = house_module(seed_of("tw", k), w, 7, 1 if rng.random() < 0.65 else 2, roofs[k % 3], tracker,
                                     ["barracks", "kitchen", "bedroom"], pal=hut, fh=5, kit=True, jetty=False)
            place_house(bb, mod, w, 7, x, DECK + 1, side, rot)
            k += 1
        x += w + 2
    # the overseers' office: a two-storey stone block by the square
    ox = 92
    top = tier(bb, ox, CZ - 6, ox + 20, CZ + 6, DECK, 2, 5, STONE[:3], "minecraft:glass_pane", "minecraft:stone_brick_stairs",
               band="minecraft:polished_andesite", plate="minecraft:spruce_planks", top_plate="minecraft:stone_bricks",
               weights=[0.7, 0.15, 0.15], every=3)
    P.hip_roof(bb, ox - 1, CZ - 7, ox + 21, CZ + 7, top + 1, "minecraft:dark_oak_stairs", ridge="minecraft:dark_oak_slab[type=bottom]")
    furnish_kit(bb, (ox + 1, CZ - 5, ox + 19, CZ + 5), DECK + 1, 4, "office", wood="dark_oak", seed=4240, doors=[(ox + 10, CZ + 6)], accent="gray")
    furnish_kit(bb, (ox + 1, CZ - 5, ox + 19, CZ + 5), DECK + 6, 4, "armory", wood="dark_oak", seed=4241, doors=[(ox + 2, CZ - 5)], accent="gray")
    bb.fill(ox + 1, DECK + 1, CZ - 5, ox + 1, DECK + 6, CZ - 5, "minecraft:ladder[facing=east]")
    bb.fill(ox + 10, DECK + 1, CZ + 6, ox + 10, DECK + 2, CZ + 6, AIR)
    # the punishment square: a post with chains, a raised overseer's stand
    bb.fill(84, DECK + 1, CZ - 1, 84, DECK + 4, CZ - 1, "minecraft:dark_oak_log[axis=y]")
    bb.set(84, DECK + 3, CZ, "minecraft:iron_chain[axis=z]"); bb.set(84, DECK + 3, CZ - 2, "minecraft:iron_chain[axis=z]")
    bb.fill(78, DECK + 1, CZ + 6, 82, DECK + 2, CZ + 9, "minecraft:spruce_planks")
    for (a, b) in ((78, CZ + 6), (82, CZ + 6), (78, CZ + 9), (82, CZ + 9)):
        bb.fill(a, DECK + 3, b, a, DECK + 5, b, "minecraft:spruce_fence")
    bb.fill(78, DECK + 6, CZ + 6, 82, DECK + 6, CZ + 9, "minecraft:spruce_slab[type=bottom]")
    # guard towers on the parapets over every pier
    for px in PIERS:
        for z in (z1 - 1, z2 + 1):
            bb.fill(px - 2, DECK + 1, z - 2 if z < CZ else z, px + 2, DECK + 9, z + 2 if z > CZ else z, "minecraft:stone_bricks")
            zi = z - 1 if z < CZ else z + 1
            bb.fill(px - 1, DECK + 1, zi - (0 if z < CZ else 0), px + 1, DECK + 8, zi, AIR)
            bb.fill(px - 2, DECK + 10, z - 2 if z < CZ else z, px + 2, DECK + 10, z + 2 if z > CZ else z, "minecraft:stone_brick_slab[type=bottom]")
            bb.set(px, DECK + 7, z, "minecraft:iron_bars")
            bb.set(px, DECK + 11, z - 1 if z < CZ else z + 1, "minecraft:lantern")
    # stacks of cut blocks, sledges on log rollers, a lift cranes at the deck edge hauling blocks up from barges
    for i in range(16):
        x = int(rng.integers(WEST_END + 10, xe - 30))
        z = int(rng.integers(CZ - 4, CZ + 5))
        if 80 <= x <= 114:
            continue
        h = int(rng.integers(1, 3))
        bb.fill(x, DECK + 1, z, x + 1, DECK + h, z + 1, "minecraft:smooth_stone" if i % 2 else "minecraft:stone")
    for cx in (48, 120, 160):
        zc = z2 + 1
        bb.fill(cx, DECK + 2, zc, cx, DECK + 12, zc, "minecraft:stripped_spruce_log[axis=y]")
        bb.fill(cx, DECK + 12, zc, cx, DECK + 12, zc + 7, "minecraft:stripped_spruce_log[axis=z]")
        bb.fill(cx, 3, zc + 7, cx, DECK + 11, zc + 7, "minecraft:iron_chain[axis=y]")
        bb.fill(cx - 1, 1, zc + 6, cx + 1, 2, zc + 8, "minecraft:stone_bricks")
        bb.set(cx, DECK + 2, zc - 1, "minecraft:grindstone[face=floor,facing=south]")
    # lamps along the street
    for x in range(WEST_END + 12, xe - 24, 10):
        lamp_post(bb, x, DECK + 1, CZ - 6, post="minecraft:spruce_fence")
        lamp_post(bb, x + 5, DECK + 1, CZ + 6, post="minecraft:spruce_fence")


def boats(bb):
    """Barges loaded with blocks moored to the piers and two rowing boats."""
    for (bx, bz) in ((44, CZ - HW - 12), (120, CZ + HW + 6), (158, CZ - HW - 11)):
        for dx in range(12):
            half = 2 if 1 <= dx <= 10 else 1
            bb.fill(bx + dx, -1, bz - half, bx + dx, 0, bz + half, "minecraft:spruce_planks")
            bb.set(bx + dx, 1, bz - half, "minecraft:spruce_slab[type=bottom]"); bb.set(bx + dx, 1, bz + half, "minecraft:spruce_slab[type=bottom]")
        bb.fill(bx + 3, 1, bz - 1, bx + 8, 2, bz + 1, "minecraft:smooth_stone")
    for (bx, bz) in ((90, CZ - HW - 6), (140, CZ + HW + 9)):
        for dx in range(6):
            bb.fill(bx + dx, 0, bz - 1, bx + dx, 0, bz + 1, "minecraft:dark_oak_planks")
        bb.set(bx + 2, 1, bz, "minecraft:dark_oak_trapdoor[facing=north,half=bottom]")


def design():
    bb = BigBuild(seed=4200, y_min=-14, y_max=100)
    tracker = P.PropTracker(4200)
    rng = np.random.default_rng(4200)
    bb.fill(0, -12, 0, NX - 1, -12, NZ - 1, "minecraft:gravel")
    xe = bridge_body(bb)
    gallery_rooms(bb)
    unfinished_end(bb)
    top = prison_tower(bb, xe)
    deck_town(bb, tracker, rng, xe)
    boats(bb)
    return bb, [], top


def build():
    bb, audit, top = design()
    b = to_canvas(bb)
    steady(b)
    xe = PIERS[-1] + PW + 12
    b.chest(70, GAL, CZ + 4, "medium", "south")
    b.chest(xe - 4, DECK + 31, CZ + 2, "hard", "west")
    b.chest(96, DECK + 1, CZ - 4, "medium", "south")
    for (x, z) in ((60, CZ), (100, CZ + 3), (140, CZ - 2), (180, CZ + 1)):
        b.guard(x, DECK + 1, z, "jailer")
    b.guard(xe - 12, DECK + 31, CZ, "warden_jailer")
    b.guard(86, DECK + 1, CZ + 3, "cp_agent")
    return b, 0
