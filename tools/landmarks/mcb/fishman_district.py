"""The Fish-Man District v2, redesigned with the Minecraft Builder skill (with its new underwater kit, mcreef).

The poor, lawless quarter of Fish-Man Island where the outcasts gathered, in its own air bubble sunk into a crater in the
sea floor. Outside: the crater's rock walls overgrown with coral heads and kelp, fish schools in ribbons, a manta ray
and jellyfish drifting over it, and a glass tube with a door (the airlock: doors keep water out) coming down from the
crater rim to the district gate. Inside the bubble, under bubble lamps: a buttressed coral-stone wall with the gate, and
crooked stacked houses of dark prismarine, mud brick and coral bricks with mangrove frames leaning over winding alleys;
the Fish-Man Karate dojo (a big timber hall with training dummies and a sparring floor), the Breaking Sea tavern, the
hideout of the New Fish-Man Pirates with their weapon racks and crates of Energy Steroids, a little market, and the
memorial to Queen Otohime with flowers at its foot. 150 x 150. Sea floor = y 0; the bubble's top stays at y 10."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT
import mcreef as R

SID = "fishman_district"
TITLE = "Fish-Man District"
CUTS = [-18, -10, 0]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

N = 150
C = 75
RX, RY, BASE = 54, 36, -26          # the bubble: horizontal radius, height above its base, base y
G = BASE + 3                         # district ground top (people walk on G + 1)
CR = 72                              # crater rim radius (sea floor y 0 there)
BUBBLE = "onepiece:bubble_glass"
CORAL = "onepiece:coral_bricks"
CORAL_ST = "onepiece:coral_brick_stairs"
CORAL_W = "onepiece:coral_brick_wall"
LAMP = "onepiece:bubble_lamp[hanging=false]"
HLAMP = "onepiece:bubble_lamp[hanging=true]"
DOJO = (C - 40, C - 22, C - 16, C - 2)
HIDE = (C + 18, C + 14, C + 40, C + 32)
TAVERN = (C + 14, C - 30, C + 34, C - 14)
MEMO = (C, C - 6)
GATE_Z = C + RX - 9                  # the gate in the ring wall (south)
WALL_R = 46
PALS = [
    dict(walls=["minecraft:dark_prismarine", "minecraft:prismarine_bricks", CORAL], frame="minecraft:mangrove_log",
         base=["minecraft:mud_bricks", "minecraft:packed_mud", "minecraft:tuff"], floor="minecraft:mangrove_planks", wood="mangrove",
         chimney="minecraft:mud_bricks"),
    dict(walls=["minecraft:mud_bricks", "minecraft:packed_mud", "minecraft:dark_prismarine"], frame="minecraft:stripped_mangrove_log",
         base=["minecraft:tuff", "minecraft:mud_bricks", "minecraft:cobbled_deepslate"], floor="minecraft:dark_oak_planks", wood="dark_oak",
         chimney="minecraft:deepslate_bricks"),
    dict(walls=[CORAL, "minecraft:prismarine_bricks", "minecraft:mud_bricks"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobbled_deepslate", "minecraft:tuff", "minecraft:mud_bricks"], floor="minecraft:mangrove_planks", wood="mangrove",
         chimney="minecraft:mud_bricks"),
    dict(walls=["minecraft:prismarine_bricks", "minecraft:dark_prismarine", "minecraft:warped_planks"], frame="minecraft:stripped_warped_stem",
         base=["minecraft:tuff", "minecraft:cobbled_deepslate", "minecraft:mud_bricks"], floor="minecraft:warped_planks", wood="warped",
         chimney="minecraft:deepslate_bricks"),
]
ROOFS = ["minecraft:dark_prismarine_stairs", "minecraft:prismarine_brick_stairs", CORAL_ST, "minecraft:mud_brick_stairs",
         "minecraft:warped_stairs", "minecraft:dark_prismarine_stairs"]
KINDS = [["kitchen", "bedroom", "bedroom"], ["storage", "bedroom"], ["living", "bedroom", "storage"], ["workshop", "bedroom"],
         ["dining", "bedroom", "bedroom"]]
GROUND = [("minecraft:mud", 0.2), ("minecraft:packed_mud", 0.2), ("minecraft:sand", 0.15), ("minecraft:coarse_dirt", 0.15),
          ("minecraft:mud_bricks", 0.1), ("minecraft:tuff", 0.1), ("minecraft:moss_block", 0.1)]
STREET = [(CORAL, 0.35), ("minecraft:prismarine_bricks", 0.25), ("minecraft:mud_bricks", 0.2), ("minecraft:tuff_bricks", 0.2)]


def in_bubble(X, y, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (y >= BASE) & (((X - C) / RX) ** 2 + ((y - BASE) / RY) ** 2 + ((Z - C) / RX) ** 2 <= 1.0)


def dist(X, Z):
    return np.hypot(np.asarray(X, float) - C, np.asarray(Z, float) - C)


def crater_y(X, Z):
    """Crater floor outside the bubble: y 0 at the rim, sloping down to the bubble's base."""
    d = dist(X, Z)
    t = np.clip((CR - d) / (CR - RX + 2), 0, 1)
    return np.round(-(BASE * -1 - 2) * t ** 0.8 + NT.fbm(np.asarray(X, float), np.asarray(Z, float), 7710, 9) * 3 * t)


def streets(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = dist(X, Z)
    a = np.arctan2(Z - C, X - C)
    m = np.abs(d - 29 - 1.5 * np.sin(a * 3)) <= 1.4                                 # the winding ring alley
    m |= (np.abs(X - C - 2 * np.sin(Z * 0.15)) <= 1.6) & (Z > C - WALL_R) & (Z < C + WALL_R + 4)   # the north-south lane
    m |= np.abs(d - 42) <= 1.0                                                      # the alley inside the wall
    for a0 in (0.3, 2.5, 4.3):                                        # crooked spokes
        ang = a0 + 0.12 * np.sin(d * 0.3)
        m |= (np.abs(np.sin(a - ang) * d) <= 1.2) & (np.cos(a - ang) > 0) & (d > 8) & (d < 42)
    m |= np.hypot(X - MEMO[0], Z - MEMO[1]) <= 7
    return m


def terrain(bb):
    # the crater and its walls
    lo, hi = 0, N - 1
    bb.fill_where(lo, BASE - 6, lo, hi, 0, hi, lambda X, y, Z: (dist(X, Z) <= CR + 4) & (y <= crater_y(X, Z) - 1) & (y >= crater_y(X, Z) - 4),
                  "minecraft:stone")
    bb.fill_where(lo, BASE - 6, lo, hi, 0, hi, lambda X, y, Z: (dist(X, Z) <= CR + 4) & (y == crater_y(X, Z)) & (NT.noise(X, Z, 7711, 5) < 0.5),
                  "minecraft:sand")
    bb.fill_where(lo, BASE - 6, lo, hi, 0, hi, lambda X, y, Z: (dist(X, Z) <= CR + 4) & (y == crater_y(X, Z)) & (NT.noise(X, Z, 7711, 5) >= 0.5),
                  "minecraft:gravel")
    # the district's ground mass inside the bubble
    bb.fill_where(lo, BASE - 4, lo, hi, G, hi, lambda X, y, Z: dist(X, Z) <= RX + 1, "minecraft:mud_bricks")
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.full(np.broadcast(np.asarray(X), np.asarray(Z)).shape, G), GROUND, 7712,
             mask=lambda X, Z: (dist(X, Z) <= RX - 1) & ~streets(X, Z), under="minecraft:packed_mud", core="minecraft:mud_bricks", base=BASE - 4)
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.full(np.broadcast(np.asarray(X), np.asarray(Z)).shape, G), STREET, 7713,
             mask=lambda X, Z: (dist(X, Z) <= RX - 1) & streets(X, Z), under="minecraft:packed_mud", core="minecraft:mud_bricks", base=BASE - 4)
    # empty the bubble, then glass the shell
    bb.fill_where(lo, G + 1, lo, hi, BASE + RY + 1, hi, lambda X, y, Z: in_bubble(X, y, Z), AIR)
    R.bubble_dome(bb, C, BASE, C, RX, glass=BUBBLE, ry=RY, frame=CORAL, ribs=12, below=0.0, thickness=1)
    bb.fill_where(lo, BASE, lo, hi, G, hi, lambda X, y, Z: (dist(X, Z) > RX - 1) & (dist(X, Z) <= RX + 1), CORAL)


# ------------------------------------------------------------------ the wall and gate, the airlock tube
def ring_wall(bb):
    y = G
    bb.fill_where(C - WALL_R - 2, y + 1, C - WALL_R - 2, C + WALL_R + 2, y + 7, C + WALL_R + 2,
                  lambda X, yy, Z: (np.abs(dist(X, Z) - WALL_R) <= 0.8), "minecraft:mud_bricks")
    bb.fill_where(C - WALL_R - 2, y + 7, C - WALL_R - 2, C + WALL_R + 2, y + 8, C + WALL_R + 2,
                  lambda X, yy, Z: (np.abs(dist(X, Z) - WALL_R) <= 0.8) & ((yy == y + 7) | ((np.round(np.degrees(np.arctan2(Z - C, X - C))) % 6) < 3)),
                  CORAL)
    for a in range(0, 360, 20):
        t = math.radians(a)
        x, z = C + int(round((WALL_R + 1.5) * math.cos(t))), C + int(round((WALL_R + 1.5) * math.sin(t)))
        bb.fill(x, y + 1, z, x, y + 5, z, "minecraft:tuff_bricks")
        bb.set(x, y + 6, z, "minecraft:tuff_brick_slab[type=bottom]")
        xi, zi = C + int(round((WALL_R - 1.5) * math.cos(t))), C + int(round((WALL_R - 1.5) * math.sin(t)))
        bb.set(xi, y + 5, zi, LAMP)
    # walkway on the inner side
    bb.fill_where(C - WALL_R, y + 6, C - WALL_R, C + WALL_R, y + 6, C + WALL_R,
                  lambda X, yy, Z: (dist(X, Z) <= WALL_R - 0.8) & (dist(X, Z) > WALL_R - 2.2), "minecraft:mangrove_slab[type=top]")
    # the gate (south)
    gz = C + WALL_R
    bb.fill(C - 3, y + 1, gz - 2, C + 3, y + 6, gz + 2, AIR)
    for x in (C - 4, C + 4):
        bb.fill(x, y + 1, gz - 2, x, y + 10, gz + 2, "minecraft:dark_prismarine")
        bb.set(x, y + 11, gz, LAMP)
    bb.fill(C - 4, y + 7, gz - 2, C + 4, y + 9, gz + 2, "minecraft:dark_prismarine")
    bb.fill(C - 3, y + 6, gz - 1, C + 3, y + 6, gz + 1, "minecraft:iron_bars")
    bb.fill(C - 2, y + 7, gz + 3, C + 2, y + 9, gz + 3, CORAL)


def airlock_tube(bb):
    """A glass tube from the gate up the crater slope to the rim, ending in a door: water stays outside."""
    pts = []
    for z in range(C + WALL_R + 3, N - 3):
        d = z - C
        if d < RX - 1:
            fy = G
        else:
            fy = int(min(0, crater_y(np.array([C]), np.array([z]))[0])) + 1
        pts.append((z, max(G, fy)))
    last = None
    for (z, fy) in pts:
        if last is not None and fy > last + 1:
            fy = last + 1
        bb.fill(C - 3, fy - 1, z, C + 3, fy + 5, z, BUBBLE)
        bb.fill(C - 2, fy, z, C + 2, fy + 4, z, AIR)
        bb.fill(C - 2, fy - 1, z, C + 2, fy - 1, z, CORAL)
        if last is not None and fy > last:
            bb.fill(C - 2, fy - 1, z, C + 2, fy - 1, z, CORAL_ST + "[facing=south,half=bottom]")
            bb.fill(C - 2, fy - 1, z, C + 2, fy - 1, z, CORAL)
            bb.fill(C - 2, fy - 1, z - 1, C + 2, fy - 1, z - 1, CORAL_ST + "[facing=south,half=bottom]")
        if z % 6 == 0:
            bb.set(C, fy + 4, z, HLAMP)
        last = fy
        if fy >= 1 and z > C + CR - 4:
            break
    # the end: a coral-framed door, the only way in; a lamp post on the rim to find it
    zend = z
    bb.fill(C - 3, last - 1, zend + 1, C + 3, last + 5, zend + 1, CORAL)
    bb.fill(C, last, zend + 1, C, last + 1, zend + 1, AIR)
    bb.set(C, last, zend + 1, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left]")
    bb.set(C, last + 1, zend + 1, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left]")
    bb.fill(C - 1, last, zend + 2, C + 1, last, zend + 3, CORAL)
    bb.fill(C + 3, last, zend + 3, C + 3, last + 8, zend + 3, CORAL_W)
    bb.set(C + 3, last + 9, zend + 3, "minecraft:sea_lantern")
    return zend


# ------------------------------------------------------------------ the landmarks of the district
def hall(bb, box, wall, roof_st, h=8, wood="mangrove"):
    x1, z1, x2, z2 = box
    y = G
    bb.fill(x1, y - 1, z1, x2, y, z2, "minecraft:tuff_bricks")
    bb.fill(x1, y, z1, x2, y, z2, f"minecraft:{wood}_planks")
    bb.fill(x1, y + 1, z1, x2, y + h, z2, wall)
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + h, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 1, z, x, y + h, z, f"minecraft:{'stripped_' if wood != 'warped' else ''}{wood}_{'log' if wood != 'warped' else 'stem'}[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 1, z, x, y + h, z, f"minecraft:{'stripped_' if wood != 'warped' else ''}{wood}_{'log' if wood != 'warped' else 'stem'}[axis=y]")
    for x in range(x1 + 2, x2 - 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 3, z, x + 1, y + 5, z, "minecraft:cyan_stained_glass_pane")
    for z in range(z1 + 2, z2 - 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 3, z, x, y + 5, z + 1, "minecraft:cyan_stained_glass_pane")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y + h + 1, roof_st, ridge_axis="x", gable_fill=wall, overhang=1)
    return y


def dojo(bb, tracker, audit):
    """The Fish-Man Karate dojo: one big timber hall, a sparring floor of mats, training dummies, scrolls on the walls,
    the master's seat, a changing room and a store room at the back."""
    x1, z1, x2, z2 = DOJO
    y = hall(bb, DOJO, "minecraft:dark_prismarine", "minecraft:dark_prismarine_stairs", h=9)
    cz = (z1 + z2) // 2
    bb.fill(x1 + 3, y + 1, z1 + 3, x2 - 8, y + 1, z2 - 3, "minecraft:light_blue_carpet")
    bb.fill(x1 + 4, y + 1, z1 + 4, x2 - 9, y + 1, z2 - 4, "minecraft:cyan_carpet")
    for x in range(x1 + 3, x2 - 7, 4):
        for z in (z1 + 1, z2 - 1):
            bb.fill(x, y + 1, z, x, y + 2, z, "minecraft:hay_block[axis=y]")
            bb.set(x, y + 3, z, "minecraft:carved_pumpkin[facing=south]" if z == z1 + 1 else "minecraft:carved_pumpkin[facing=north]")
    bb.fill(x1 + 1, y + 6, z1 + 1, x2 - 1, y + 6, z1 + 1, "minecraft:white_banner[rotation=0]") if False else None
    for x in range(x1 + 2, x2 - 6, 3):
        bb.set(x, y + 6, z1 + 1, "minecraft:cyan_wool"); bb.set(x, y + 5, z1 + 1, "minecraft:white_wool")
    bb.set(x2 - 7, y + 1, cz, st("minecraft:mangrove_stairs", "east"))
    bb.fill(x2 - 6, y + 1, z1 + 1, x2 - 6, y + 9, z2 - 1, "minecraft:mangrove_planks")
    bb.fill(x2 - 6, y + 1, cz, x2 - 6, y + 2, cz, AIR)
    bb.fill(x2 - 5, y + 1, cz, x2 - 1, y + 9, cz, "minecraft:mangrove_planks")
    rooms = [(x2 - 5, z1 + 1, x2 - 1, cz - 1), (x2 - 5, cz + 1, x2 - 1, z2 - 1)]
    bb.fill(x2 - 6, y + 1, cz - 3, x2 - 6, y + 2, cz - 3, AIR)
    bb.fill(x2 - 6, y + 1, cz + 3, x2 - 6, y + 2, cz + 3, AIR)
    for i, (r, k) in enumerate(zip(rooms, ("storage", "bedroom"))):
        P.furnish_room(bb, r, y + 1, k, height=5, seed=seed_of("dojo", i), doors=[(x2 - 6, cz - 3), (x2 - 6, cz + 3)], wood="mangrove",
                       tracker=tracker)
        txt, ok = P.audit_props(bb, [r], y + 1, 5)
        if not ok:
            audit.append(txt)
    bb.fill(x1, y + 1, cz - 1, x1, y + 3, cz + 1, AIR)
    for x in range(x1 + 4, x2 - 6, 5):
        bb.set(x, y + 8, cz, HLAMP)
    rows = ["#...#.###.###.###.", "#...#.#.#.#...#...", "#.#.#.###.#...###.", "##.##.#.#.#...#...", "#...#.#.#.###.###."]
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


def tavern(bb, tracker, audit):
    x1, z1, x2, z2 = TAVERN
    y = hall(bb, TAVERN, "minecraft:mud_bricks", "minecraft:mud_brick_stairs", h=7, wood="dark_oak")
    cz = (z1 + z2) // 2
    bb.fill(x1, y + 1, cz - 1, x1, y + 3, cz + 1, AIR)
    bb.fill(x2 - 3, y + 1, z1 + 2, x2 - 3, y + 1, z2 - 2, "minecraft:dark_oak_planks")
    bb.fill(x2 - 3, y + 2, z1 + 2, x2 - 3, y + 2, z2 - 2, "minecraft:dark_oak_slab[type=bottom]")
    for z in range(z1 + 1, z2):
        bb.set(x2 - 1, y + 1, z, "minecraft:barrel[facing=west,open=false]")
        if z % 2:
            bb.set(x2 - 1, y + 2, z, "onepiece:sake_barrel[axis=z]")
    for tx in range(x1 + 3, x2 - 5, 4):
        for tz in range(z1 + 3, z2 - 2, 4):
            bb.set(tx, y + 1, tz, "minecraft:dark_oak_fence"); bb.set(tx, y + 2, tz, "minecraft:dark_oak_pressure_plate")
            bb.set(tx - 1, y + 1, tz, st("minecraft:dark_oak_stairs", "east")); bb.set(tx + 1, y + 1, tz, st("minecraft:dark_oak_stairs", "west"))
    for x in range(x1 + 3, x2 - 2, 4):
        bb.set(x, y + 6, cz, HLAMP)
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


def hideout(bb, tracker, audit):
    """The New Fish-Man Pirates' den: a squat fortified hall, weapon racks (tridents and swords on armour stands are
    entities, so racks of fences and grindstones here), crates and barrels of Energy Steroids, Hody's chair and map table."""
    x1, z1, x2, z2 = HIDE
    y = hall(bb, HIDE, "minecraft:cobbled_deepslate", "minecraft:deepslate_tile_stairs", h=7, wood="dark_oak")
    cz = (z1 + z2) // 2
    bb.fill(x1, y + 1, cz - 1, x1, y + 3, cz + 1, AIR)
    for x in (x1 - 1, x1 - 1):
        for z in (cz - 2, cz + 2):
            bb.fill(x, y + 1, z, x, y + 4, z, "minecraft:deepslate_brick_wall")
            bb.set(x, y + 5, z, "minecraft:soul_lantern[hanging=false]")
    for z in range(z1 + 2, z2 - 1, 2):
        bb.set(x2 - 1, y + 1, z, "minecraft:grindstone[face=floor,facing=west]")
        bb.set(x2 - 1, y + 2, z, "minecraft:dark_oak_fence")
    for (x, z) in ((x1 + 2, z1 + 1), (x1 + 3, z1 + 1), (x1 + 2, z1 + 2), (x1 + 4, z1 + 1), (x1 + 2, z2 - 1), (x1 + 3, z2 - 1)):
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, y + 2, z, "minecraft:red_candle[candles=3,lit=true]") if (x + z) % 2 else None
    bb.fill(x1 + 8, y + 1, cz - 1, x1 + 11, y + 1, cz + 1, "minecraft:dark_oak_planks")
    bb.fill(x1 + 8, y + 2, cz - 1, x1 + 11, y + 2, cz + 1, "minecraft:red_carpet")
    bb.set(x2 - 4, y + 1, cz, st("minecraft:deepslate_brick_stairs", "east"))
    bb.fill(x2 - 3, y + 1, cz - 1, x2 - 3, y + 4, cz + 1, "minecraft:red_wool")
    for x in range(x1 + 3, x2 - 2, 5):
        bb.set(x, y + 6, cz, "minecraft:soul_lantern[hanging=true]")
    return (x1 - 3, z1 - 2, x2 + 2, z2 + 2)


def memorial(bb):
    """Queen Otohime's memorial: a stepped coral plinth, a pale statue of the queen with her crown, flowers at the foot."""
    x, z = MEMO
    y = G
    bb.cylinder(x, y + 1, z, 4, y + 1, "minecraft:prismarine_bricks")
    bb.cylinder(x, y + 2, z, 3, y + 2, CORAL)
    bb.cylinder(x, y + 3, z, 2, y + 3, "minecraft:quartz_block")
    bb.fill(x, y + 4, z, x, y + 9, z, "minecraft:white_concrete")
    bb.fill(x - 1, y + 5, z, x + 1, y + 8, z, "minecraft:white_concrete")
    bb.fill(x, y + 4, z - 1, x, y + 6, z + 1, "minecraft:pink_concrete")
    bb.set(x, y + 10, z, "minecraft:white_concrete")
    bb.set(x, y + 11, z, "minecraft:gold_block")
    bb.set(x - 1, y + 9, z, "minecraft:light_blue_concrete"); bb.set(x + 1, y + 9, z, "minecraft:light_blue_concrete")
    for a in range(0, 360, 30):
        t = math.radians(a)
        bb.set(x + int(round(4 * math.cos(t))), y + 2, z + int(round(4 * math.sin(t))),
               ("minecraft:pink_tulip", "minecraft:white_tulip", "minecraft:blue_orchid")[(a // 30) % 3])
    for (ox, oz) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
        bb.fill(x + ox, y + 1, z + oz, x + ox, y + 3, z + oz, CORAL_W)
        bb.set(x + ox, y + 4, z + oz, LAMP)


def market(bb, rng):
    for i, a in enumerate(range(200, 340, 28)):
        t = math.radians(a)
        x, z = C + int(round(24 * math.cos(t))), C + int(round(24 * math.sin(t)))
        for (px, pz) in ((x, z), (x + 3, z), (x, z + 3), (x + 3, z + 3)):
            bb.fill(px, G + 1, pz, px, G + 3, pz, "minecraft:mangrove_fence")
        bb.fill(x, G + 4, z, x + 3, G + 4, z + 3, ("minecraft:cyan_wool", "minecraft:orange_wool", "minecraft:purple_wool")[i % 3])
        bb.fill(x + 1, G + 1, z + 1, x + 2, G + 1, z + 2, "minecraft:barrel[facing=up,open=false]")
        bb.set(x + 1, G + 2, z + 1, ("minecraft:dried_kelp_block", "minecraft:sponge", "minecraft:melon")[i % 3])


def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(90000):
        w, d = int(rng.integers(5, 9)), int(rng.integers(5, 8))
        x0, z0 = int(rng.integers(C - WALL_R + 2, C + WALL_R - w - 2)), int(rng.integers(C - WALL_R + 2, C + WALL_R - d - 2))
        xs = np.arange(x0, x0 + w)[:, None]; zs = np.arange(z0, z0 + d)[None, :]
        if streets(xs, zs).any() or (dist(xs, zs) > WALL_R - 5).any():
            continue
        box = (x0 - 1, z0 - 1, x0 + w + 1, z0 + d + 1)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        cand = {}
        for rot, (px, pz) in {0: (x0 + w // 2, z0 + d + 1), 2: (x0 + w // 2, z0 - 2), 1: (x0 - 2, z0 + d // 2), 3: (x0 + w + 1, z0 + d // 2)}.items():
            for s in range(0, 6):
                qx = px + (0 if rot in (0, 2) else (-s if rot == 1 else s))
                qz = pz + (s if rot == 0 else -s if rot == 2 else 0)
                if streets(np.array([[qx]]), np.array([[qz]]))[0, 0]:
                    cand[rot] = s
                    break
        if not cand:
            continue
        rot = min(cand, key=cand.get)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        # houses get lower toward the bubble's edge so the roofs stay inside the glass
        r_far = float(dist(np.array([x0, x0 + w, x0, x0 + w]), np.array([z0, z0, z0 + d, z0 + d])).max())
        room_h = BASE + RY * math.sqrt(max(0.0, 1 - (r_far / RX) ** 2)) - G - 4
        fl = min(int(rng.integers(2, 5)), int(room_h // 6) - 1)
        if fl < 1:
            continue
        m, top, au = house_module(seed_of("fm", x0, z0), mw, md, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=(k % 2 == 0), jetty=(k % 3 != 2), chimney=(k % 3 == 1))
        audit += au
        place_house(bb, m, mw, md, x0, G, z0, rot)
        # lean: a few blocks of odd material patched on
        for _p in range(int(rng.integers(2, 6))):
            px, pz = int(rng.integers(x0, x0 + w)), int(rng.integers(z0, z0 + d))
            py = G + 1 + int(rng.integers(0, fl * 5))
            if px in (x0, x0 + w - 1) or pz in (z0, z0 + d - 1):
                bb.set(px, py, pz, (CORAL, "minecraft:mangrove_planks", "minecraft:warped_planks", "minecraft:tuff")[_p % 4])
        taken.append(box)
        k += 1
        if k >= 60:
            break
    print("houses:", k)
    for a in range(0, 360, 24):
        t = math.radians(a)
        x, z = C + int(round(28 * math.cos(t))), C + int(round(28 * math.sin(t)))
        if not any(r[0] <= x <= r[2] and r[1] <= z <= r[3] for r in taken):
            bb.fill(x, G + 1, z, x, G + 4, z, "minecraft:mangrove_fence")
            bb.set(x, G + 5, z, LAMP)


def ring_houses(bb, tracker, audit, rng, taken):
    """Houses in a ring between the ring alley (r 29) and the wall alley (r 42), doors facing the town centre."""
    k = 0
    a = 0.0
    while a < 2 * math.pi:
        cx, cz = C + 35.5 * math.cos(a), C + 35.5 * math.sin(a)
        ix, iz = -math.cos(a), -math.sin(a)
        rot = (0 if iz > 0 else 2) if abs(iz) >= abs(ix) else (3 if ix > 0 else 1)
        w = int(rng.integers(6, 9))
        dep = 7
        fw, fd = (w, dep) if rot % 2 == 0 else (dep, w)
        x0, z0 = int(round(cx - fw / 2)), int(round(cz - fd / 2))
        xs = np.arange(x0, x0 + fw)[:, None]; zs = np.arange(z0, z0 + fd)[None, :]
        box = (x0 - 1, z0 - 1, x0 + fw, z0 + fd)
        if streets(xs, zs).any() or (dist(xs, zs) > WALL_R - 4).any() or \
                any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            a += 0.05
            continue
        mw, md = (fw, fd) if rot % 2 == 0 else (fd, fw)
        m, top, au = house_module(seed_of("fmr", x0, z0), mw, md, 2 if k % 3 else 1, ROOFS[k % len(ROOFS)], tracker,
                                  KINDS[k % len(KINDS)], pal=PALS[(k + 1) % len(PALS)], timber=(k % 2 == 1), jetty=False,
                                  chimney=(k % 3 == 0))
        audit += au
        place_house(bb, m, mw, md, x0, G, z0, rot)
        taken.append(box)
        k += 1
        a += (w + 1.5) / 35.5
    print("ring houses:", k)


# ------------------------------------------------------------------ the reef outside
def reef(bb, rng):
    outside = lambda x, z: dist(np.array([x]), np.array([z]))[0] <= RX + 3 or dist(np.array([x]), np.array([z]))[0] > CR - 2 or \
        abs(x - C) <= 5 and z > C
    for _ in range(140):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if outside(x, z):
            continue
        y = int(crater_y(np.array([x]), np.array([z]))[0]) + 1
        R.coral_cluster(bb, x, y, z, int(rng.integers(4, 9)), rng=rng)
    k = 0
    for _ in range(600):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if outside(x, z):
            continue
        y = int(crater_y(np.array([x]), np.array([z]))[0]) + 1
        h = int(min(rng.integers(10, 30), 12 - y))
        if h < 6:
            continue
        R.kelp(bb, x, y, z, h, rng=rng, sway=2)
        k += 1
        if k >= 70:
            break
    # fish schools in ribbons round the bubble, a manta ray, two jellyfish
    for i in range(4):
        a0 = rng.uniform(0, 2 * math.pi)
        path = [(int(C + (RX + 8) * math.cos(a0 + j * 0.12)), int(-6 + 3 * math.sin(j * 0.5) + i * 3), int(C + (RX + 8) * math.sin(a0 + j * 0.12)))
                for j in range(14)]
        R.fish_school(bb, path, 18, rng=rng)
    R.manta_ray(bb, C - 40, 2, C - 52, span=20)
    R.jellyfish(bb, C + 44, 6, C - 46, bell_r=4, tentacles=8, rng=rng)
    R.jellyfish(bb, C - 52, 4, C + 40, bell_r=3, tentacles=6, rng=rng)


def design():
    bb = BigBuild(seed=7710, y_min=BASE - 8, y_max=40)
    tracker = P.PropTracker(7710)
    audit = []
    rng = np.random.default_rng(7710)
    terrain(bb)
    ring_wall(bb)
    taken = [dojo(bb, tracker, audit), tavern(bb, tracker, audit), hideout(bb, tracker, audit),
             (MEMO[0] - 8, MEMO[1] - 8, MEMO[0] + 8, MEMO[1] + 8)]
    memorial(bb)
    market(bb, rng)
    for a in range(200, 340, 28):
        t = math.radians(a)
        x, z = C + int(round(24 * math.cos(t))), C + int(round(24 * math.sin(t)))
        taken.append((x - 1, z - 1, x + 4, z + 4))
    ring_houses(bb, tracker, audit, rng, taken)
    town(bb, tracker, audit, rng, taken)
    airlock_tube(bb)
    # water in the crater outside the bubble (the world's sea fills everything above y 0)
    bb.fill_where(0, BASE - 6, 0, N - 1, 0, N - 1, lambda X, y, Z: (dist(X, Z) <= CR + 3) & (y > crater_y(X, Z)) & ~in_bubble(X, y, Z) &
                  ~((np.abs(np.asarray(X) - C) <= 3) & (np.asarray(Z) > C + WALL_R) & (y <= 6)), "minecraft:water", only_empty=True)
    reef(bb, rng)
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall (and break into items) when the build generates."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    x1, z1, x2, z2 = HIDE
    b.chest(x1 + 5, G + 1, z1 + 1, "pirate", "south")
    b.chest(DOJO[2] - 3, G + 1, DOJO[1] + 2, "medium", "south")
    b.guards("fishman", ((C - 4, C + WALL_R - 4), (C + 4, C + WALL_R - 4), (x1 - 3, (z1 + z2) // 2 + 3), (x1 - 3, (z1 + z2) // 2 - 3),
                         (C - 28, C + 4), (C + 26, C - 8)), y=G + 1)
    b.guards("fishman", ((DOJO[0] + 8, DOJO[1] + 10),), y=G + 1)
    return b, 0
