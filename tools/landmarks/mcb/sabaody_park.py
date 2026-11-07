"""Sabaody Park v2, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/sabaody_park.md).

The site grows from 104 x 100 to 156 x 150, and the extra room goes into more park, not a stretched one: the giant
Ferris wheel grows to a 30-block radius, the roller coaster gets a longer oval round the carousel, and new rides
fill the lawns: a striped circus big top with a sawdust ring and tiered seats, a drop tower, a swing ride, an
open-air show stage with benches, a food court of umbrella tables round the fountain plaza, and a haunted house. The
park buildings are now furnished multi-floor houses from the skill kit (ticket hall, park cafe, staff house, prize
shop, game hall) in pastel park colours. Rides, gate, fountain, balloon cart, bubbles and Yarukiman mangroves reuse
the v1 pieces. Ground = y 0. (v2)"""
import math
import random
import numpy as np
from canvas import B, AIR
from mcb.kit import BigBuild, P, seed_of, st, house_module, place_house, set_if_air, table
from mcb.bridge import to_canvas
from mcb.mangrove import yarukiman
import sabaody_park as OLD
import sabaody_kit as S
import townkit as T
import landkit as L

FLOWERS = ("minecraft:pink_tulip", "minecraft:allium", "minecraft:azure_bluet", "minecraft:oxeye_daisy",
           "minecraft:pink_petals[facing=north,flower_amount=4]", "minecraft:cornflower")

SID = "sabaody_park"
TITLE = OLD.TITLE
CUTS = [2]
TILER = OLD.TILER
NX, NZ = 156, 150
GX = 78
COLORS = OLD.COLORS
PARK = [dict(walls=["minecraft:pink_terracotta", "minecraft:pink_concrete", "minecraft:white_terracotta"],
             frame="minecraft:stripped_birch_log", base=["minecraft:quartz_bricks", "minecraft:smooth_quartz", "minecraft:calcite"],
             floor="minecraft:birch_planks", wood="birch", chimney="minecraft:white_concrete"),
        dict(walls=["minecraft:light_blue_terracotta", "minecraft:light_blue_concrete", "minecraft:white_terracotta"],
             frame="minecraft:stripped_birch_log", base=["minecraft:quartz_bricks", "minecraft:smooth_quartz", "minecraft:calcite"],
             floor="minecraft:cherry_planks", wood="cherry", chimney="minecraft:white_concrete"),
        dict(walls=["minecraft:yellow_terracotta", "minecraft:white_concrete", "minecraft:white_terracotta"],
             frame="minecraft:stripped_cherry_log", base=["minecraft:quartz_bricks", "minecraft:smooth_quartz", "minecraft:calcite"],
             floor="minecraft:birch_planks", wood="birch", chimney="minecraft:pink_concrete")]
SPOOKY = dict(walls=["minecraft:deepslate_tiles", "minecraft:polished_blackstone_bricks", "minecraft:cracked_deepslate_tiles"],
              frame="minecraft:stripped_dark_oak_log", base=["minecraft:cobbled_deepslate", "minecraft:mossy_cobblestone",
                                                             "minecraft:cobbled_deepslate"],
              floor="minecraft:dark_oak_planks", wood="dark_oak", chimney="minecraft:polished_blackstone_bricks")
ROOFS = ["minecraft:cherry_stairs", "minecraft:prismarine_brick_stairs", "minecraft:red_nether_brick_stairs"]
# park buildings: (x0, z0, w, d, floors, rot, kinds, palette, roof)
HOUSES = [(50, 126, 12, 9, 2, 3, ["kitchen", "storage"], 0, 0),          # ticket hall by the gate, door east
          (8, 66, 13, 10, 2, 3, ["kitchen", "living"], 1, 1),             # the park cafe, door east
          (138, 112, 10, 9, 2, 2, ["bedroom", "storage"], 2, 0),          # staff house, door north
          (98, 128, 11, 9, 1, 2, ["storage", "living"], 0, 1),            # prize shop, door north
          (112, 8, 14, 10, 2, 0, ["workshop", "library"], 1, 2)]          # game hall, door south


def circus(bb, cx, cz, R=13):
    """The big top: red and white striped canvas walls and cone roof on a centre pole, flags on top, a sawdust ring
    inside with tiered seats round it and an entrance on the north."""
    stripe = lambda X, Z: (np.floor((np.arctan2(Z - cz, X - cx) + math.pi) / (2 * math.pi) * 24) % 2) == 0
    bb.cylinder(cx, 0, cz, R + 1, 0, "minecraft:smooth_quartz")
    for y in range(1, 6):
        bb.fill_where(cx - R, y, cz - R, cx + R, y, cz + R,
                      lambda X, yy, Z: (np.hypot(X - cx, Z - cz) <= R) & (np.hypot(X - cx, Z - cz) > R - 1) & stripe(X, Z),
                      "minecraft:red_wool")
        bb.fill_where(cx - R, y, cz - R, cx + R, y, cz + R,
                      lambda X, yy, Z: (np.hypot(X - cx, Z - cz) <= R) & (np.hypot(X - cx, Z - cz) > R - 1) & ~stripe(X, Z),
                      "minecraft:white_wool")
    H = 13
    for k in range(H):
        r = R * (1 - k / H) + 0.6
        y = 6 + k
        ring = lambda X, yy, Z, r=r: (np.hypot(X - cx, Z - cz) <= r) & (np.hypot(X - cx, Z - cz) > r - 1.5)
        bb.fill_where(cx - R - 1, y, cz - R - 1, cx + R + 1, y, cz + R + 1,
                      lambda X, yy, Z, ring=ring: ring(X, yy, Z) & stripe(X, Z), "minecraft:red_wool")
        bb.fill_where(cx - R - 1, y, cz - R - 1, cx + R + 1, y, cz + R + 1,
                      lambda X, yy, Z, ring=ring: ring(X, yy, Z) & ~stripe(X, Z), "minecraft:white_wool")
    bb.fill(cx, 1, cz, cx, 6 + H + 3, cz, "minecraft:stripped_birch_log[axis=y]")
    bb.set(cx, 6 + H + 4, cz, "minecraft:red_wool")
    for (dx, col) in ((1, "yellow"), (2, "yellow")):
        bb.set(cx + dx, 6 + H + 3, cz, f"minecraft:{col}_wool")
    bb.cylinder(cx, 0, cz, 5, 0, "minecraft:smooth_sandstone")                       # the ring
    bb.cylinder(cx, 1, cz, 5, 1, "minecraft:red_concrete", hollow=True)
    bb.fill(cx - 1, 1, cz - 5, cx + 1, 1, cz - 5, AIR)
    for tier, r in enumerate((7, 8.5, 10, 11.5)):                                  # tiered seats
        bb.fill_where(cx - R, 1, cz - R, cx + R, tier + 1, cz + R,
                      lambda X, yy, Z, r=r: (np.hypot(X - cx, Z - cz) <= r + 0.7) & (np.hypot(X - cx, Z - cz) > r - 0.7),
                      "minecraft:spruce_planks")
    bb.fill(cx - 2, 1, cz - R, cx + 2, 6, cz - 6, AIR)                               # the entrance aisle (north)
    bb.fill(cx - 2, 0, cz - R, cx + 2, 0, cz - 6, "minecraft:red_carpet")
    bb.fill(cx - 2, 0, cz - R, cx + 2, 0, cz - 6, "minecraft:smooth_quartz")
    bb.fill(cx - 2, 1, cz - R, cx + 2, 1, cz - 6, "minecraft:red_carpet")
    for (dx, dz) in ((4, 0), (-4, 0), (0, 4)):
        bb.set(cx + dx, 1, cz + dz, "minecraft:hay_block[axis=y]")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.set(round(cx + 3 * math.cos(t)), 12, round(cz + 3 * math.sin(t)), "minecraft:lantern[hanging=true]")
        bb.fill(round(cx + 3 * math.cos(t)), 13, round(cz + 3 * math.sin(t)),
                round(cx + 3 * math.cos(t)), 6 + round(H * 0.75), round(cz + 3 * math.sin(t)), "minecraft:iron_chain[axis=y]")


def drop_tower(bb, x, z, H=44):
    """A drop tower: a 3x3 white mast with light bands, a ring of seats round it high up, a crown of lights, a fenced
    queue pen at the foot."""
    bb.fill(x - 4, 0, z - 4, x + 4, 0, z + 4, "minecraft:polished_andesite")
    bb.fill(x - 1, 1, z - 1, x + 1, H, z + 1, "minecraft:white_concrete")
    for y in range(4, H, 6):
        bb.fill(x - 1, y, z - 1, x + 1, y, z + 1, "minecraft:sea_lantern")
    for y in range(1, H, 2):
        for (dx, dz) in ((-1, -2), (1, 2), (-2, 1), (2, -1)):
            bb.set(x + dx, y, z + dz, "minecraft:iron_bars")
    cy = int(H * 0.7)
    for (dx, dz, f) in ((0, -2, "north"), (0, 2, "south"), (-2, 0, "west"), (2, 0, "east"),
                        (-2, -2, "north"), (2, 2, "south"), (-2, 2, "west"), (2, -2, "east")):
        bb.set(x + dx, cy - 1, z + dz, "minecraft:pink_concrete")
        bb.set(x + dx, cy, z + dz, st("minecraft:quartz_stairs", {"north": "south", "south": "north",
                                                                   "west": "east", "east": "west"}[f]))
    bb.fill(x - 3, cy + 2, z - 3, x + 3, cy + 2, z + 3, "minecraft:magenta_concrete")
    bb.fill(x - 1, cy + 2, z - 1, x + 1, cy + 2, z + 1, "minecraft:white_concrete")
    bb.fill(x - 2, H + 1, z - 2, x + 2, H + 1, z + 2, "minecraft:pink_concrete")
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bb.set(x + dx, H + 2, z + dz, "minecraft:sea_lantern")
    bb.set(x, H + 2, z, "minecraft:gold_block")
    for i in range(-4, 5):
        for (px, pz) in ((x + i, z - 4), (x + i, z + 4), (x - 4, z + i), (x + 4, z + i)):
            if not (pz == z + 4 and abs(px - x) <= 1):
                bb.set(px, 1, pz, "minecraft:birch_fence")


def swing_ride(bb, x, z):
    """A swing ride: a striped canopy on a pillar, chairs on chains hanging from its rim."""
    bb.cylinder(x, 0, z, 9, 0, "minecraft:smooth_quartz")
    bb.cylinder(x, 0, z, 9, 0, "minecraft:pink_concrete", hollow=True)
    bb.fill(x - 1, 1, z - 1, x + 1, 14, z + 1, "minecraft:white_concrete")
    bb.fill(x - 1, 6, z - 1, x + 1, 6, z + 1, "minecraft:sea_lantern")
    for k, r in enumerate((7, 6, 5, 3, 1)):
        bb.fill_where(x - 7, 15 + k, z - 7, x + 7, 15 + k, z + 7,
                      lambda X, yy, Z, r=r: np.hypot(X - x, Z - z) <= r + 0.4,
                      "minecraft:white_wool")
        bb.fill_where(x - 7, 15 + k, z - 7, x + 7, 15 + k, z + 7,
                      lambda X, yy, Z, r=r: (np.hypot(X - x, Z - z) <= r + 0.4) &
                      ((np.floor((np.arctan2(Z - z, X - x) + math.pi) / (2 * math.pi) * 12) % 2) == 0),
                      "minecraft:light_blue_wool")
    bb.set(x, 20, z, "minecraft:gold_block")
    for a in range(0, 360, 30):
        t = math.radians(a)
        sx, sz = round(x + 6 * math.cos(t)), round(z + 6 * math.sin(t))
        bb.fill(sx, 7, sz, sx, 14, sz, "minecraft:iron_chain[axis=y]")
        bb.set(sx, 6, sz, "minecraft:" + COLORS[a // 30 % len(COLORS)] + "_concrete")


def stage(bb, x0, z0):
    """The open-air show stage: a raised plank stage under a pink arch with red curtains, footlights, rows of
    benches facing it, lamp posts round the seating."""
    W, D = 18, 8
    bb.fill(x0, 1, z0, x0 + W, 2, z0 + D, "minecraft:spruce_planks")
    bb.fill(x0, 3, z0, x0 + W, 12, z0, "minecraft:pink_concrete")
    bb.fill(x0 + 2, 3, z0 + 1, x0 + W - 2, 10, z0 + 1, "minecraft:red_wool")
    bb.fill(x0 + 6, 3, z0 + 1, x0 + W - 6, 8, z0 + 1, "minecraft:black_wool")
    for x in (x0, x0 + W):
        bb.fill(x, 3, z0, x, 12, z0 + D, "minecraft:white_concrete")
    bb.fill(x0, 13, z0, x0 + W, 13, z0 + D, "minecraft:white_concrete")
    bb.fill(x0 + 1, 12, z0 + 1, x0 + W - 1, 12, z0 + D, "minecraft:pink_concrete")
    for x in range(x0 + 1, x0 + W):
        bb.set(x, 11, z0 + D, "minecraft:red_wool" if x % 2 else "minecraft:yellow_wool")
        if x % 3 == 0:
            bb.set(x, 3, z0 + D, "minecraft:sea_pickle[pickles=3,waterlogged=false]")
    for i in range(3):
        bb.set(x0 + W // 2 - 1 + i, 2, z0 + D + 1, st("minecraft:spruce_stairs", "south"))
    for row in range(5):
        z = z0 + D + 4 + row * 2
        for x in range(x0 + 1, x0 + W):
            if x != x0 + W // 2:
                bb.set(x, 1, z, st("minecraft:birch_stairs", "south"))
        bb.set(x0, 1, z, "minecraft:birch_fence")
        bb.set(x0 + W, 1, z, "minecraft:birch_fence")
        bb.set(x0, 2, z, "minecraft:lantern[hanging=false]")
        bb.set(x0 + W, 2, z, "minecraft:lantern[hanging=false]")


def food_court(bb, cx, cz, r=14):
    """Umbrella tables round the fountain plaza."""
    for k, a in enumerate(range(20, 360, 40)):
        t = math.radians(a)
        x, z = round(cx + r * math.cos(t)), round(cz + r * math.sin(t))
        if abs(x - GX) <= 5 and z > cz:
            continue
        col = COLORS[k % len(COLORS)]
        bb.set(x, 1, z, "minecraft:birch_fence")
        bb.set(x, 2, z, "minecraft:birch_fence")
        bb.set(x, 3, z, "minecraft:birch_fence")
        bb.fill(x - 1, 4, z - 1, x + 1, 4, z + 1, f"minecraft:{col}_wool")
        bb.set(x, 5, z, "minecraft:white_wool")
        for (dx, dz, f) in ((-1, 0, "east"), (1, 0, "west"), (0, -1, "south"), (0, 1, "north")):
            bb.set(x + dx, 1, z + dz, st("minecraft:birch_stairs", f))


def haunted_house(bb, tracker, audit):
    m, top, au = house_module(seed_of("haunt"), 14, 11, 2, "minecraft:deepslate_tile_stairs", tracker,
                              ["storage", "library"], pal=SPOOKY, fh=5, chimney=True, timber=True, jetty=True)
    audit += au
    x0, z0 = 116, 116
    place_house(bb, m, 14, 11, x0, 0, z0, 2)
    rng = np.random.default_rng(seed_of("web"))
    for _ in range(40):
        x, y, z = x0 + int(rng.integers(0, 14)), int(rng.integers(1, 10)), z0 + int(rng.integers(0, 11))
        if bb.get_region(x, y, z, x, y, z)[0, 0, 0] == 1 and bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] > 1:
            bb.set(x, y, z, "minecraft:cobweb")
    for x in range(x0 - 2, x0 + 16):                     # a crooked iron fence and gravestones out front
        if x % 2:
            bb.set(x, 1, z0 - 3, "minecraft:iron_bars")
    for (dx,) in ((1,), (4,), (10,), (13,)):
        bb.set(x0 + dx, 1, z0 - 5, "minecraft:cobblestone_wall")
        bb.set(x0 + dx, 2, z0 - 5, "minecraft:jack_o_lantern[facing=north]")
    bb.set(x0 + 6, 1, z0 - 3, AIR)
    bb.set(x0 + 7, 1, z0 - 3, AIR)


def buildings(bb, tracker, audit):
    for i, (x0, z0, w, d, fl, rot, kinds, pal, roof) in enumerate(HOUSES):
        m, top, au = house_module(seed_of("sbp", i), w, d, fl, ROOFS[roof], tracker, kinds, pal=PARK[pal], fh=5,
                                  chimney=i % 2 == 0, timber=True, jetty=False)
        audit += au
        place_house(bb, m, w, d, x0, 0, z0, rot)


# v3 (2026-10-30): the giant Yarukiman mangroves use the shared mcb/mangrove.py (arching prop roots you can walk
# under, lumpy bark, a broken crown, bubbles from the roots); set further in so their roots stay on the site
TREES = ((18, 18, 4, 44), (138, 18, 4, 46), (18, 132, 3.5, 40), (138, 132, 4, 44), (80, 12, 3, 34), (12, 98, 3, 34),
         (146, 62, 3.5, 38))


def design():
    bb = BigBuild(seed=461, y_min=-6, y_max=100)
    tracker = P.PropTracker(461)
    audit = []
    trng = np.random.default_rng(4611)
    for (x, z, r, h) in TREES:
        yarukiman(bb, x, 0, z, r, h, trng)
    circus(bb, 30, 128)
    drop_tower(bb, 100, 116)
    swing_ride(bb, 58, 104)
    stage(bb, 18, 10)
    food_court(bb, GX, 120)
    haunted_house(bb, tracker, audit)
    buildings(bb, tracker, audit)
    return bb, audit


def free_spot(b, x1, z1, x2, z2):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if b.get(x, 1, z) in (None, AIR) and b.get(x, 2, z) in (None, AIR) and b.get(x, 0, z) not in (None, AIR):
                return x, z
    return x1, z1


def build():
    rnd = random.Random(461)
    b = B()
    S.ground(b, NX, NZ, rnd)
    for x in range(10, NX - 10):
        for z in range(10, NZ - 10):
            # wild flowers in one-colour clumps (not an even speckle), only on grass
            fl = L.noise2(x, z, 4621, 5)
            if fl > 0.68 and b.get(x, 0, z) == "minecraft:grass_block" and L.noise2(x * 3, z * 3, 4622, 1) < (fl - 0.68) * 2.2:
                b.set(x, 1, z, FLOWERS[int(L.noise2(x, z, 4623, 11) * len(FLOWERS) * 0.999)])
    trees = TREES
    # walks and plazas
    OLD.walk(b, GX - 3, 26, GX + 3, NZ - 12, rnd)            # the boulevard from the gate
    OLD.walk(b, 10, 80, GX + 3, 85, rnd)                      # the avenue west to the Ferris wheel and the cafe
    OLD.walk(b, 50, 26, 106, 33, rnd)                         # the stall row
    OLD.walk(b, GX + 3, 70, 88, 75, rnd)                      # to the coaster station
    OLD.walk(b, 12, 26, 50, 30, rnd)                          # to the show stage
    OLD.walk(b, GX + 3, 110, 136, 114, rnd)                   # east to the drop tower, haunted house, staff house
    OLD.walk(b, 34, 112, GX - 3, 116, rnd)                    # west to the big top
    OLD.plaza(b, GX, 120, 11, rnd)                            # the fountain plaza
    OLD.plaza(b, 36, 50, 12, rnd)                             # round the Ferris wheel
    OLD.plaza(b, 30, 100, 10.5, rnd)                          # round the bubble ride
    OLD.plaza(b, 116, 70, 10, rnd)                            # round the carousel
    OLD.plaza(b, 78, 56, 6, rnd)                              # a small rest plaza on the boulevard
    # the giant Ferris wheel, the roller coaster and the carousel (v1 pieces, bigger)
    OLD.ferris(b, 36, 50, 30)
    OLD.coaster(b, 116, 70, 26, 32)
    OLD.carousel(b, 116, 70)
    # the bubble ride
    b.cyl(30, 100, 9.6, 0, 1, "minecraft:quartz_bricks", hollow=True)
    b.cyl(30, 100, 9, 0, 0, "minecraft:water[level=0]")
    b.cyl(30, 100, 9, -1, -1, "minecraft:light_blue_concrete")
    for k in range(8):
        t = math.radians(k * 45)
        bx, bz = round(30 + 6 * math.cos(t)), round(100 + 6 * math.sin(t))
        y = 6 + k % 3 * 2
        b.set(bx, 0, bz, "minecraft:quartz_bricks")
        for yy in range(1, y - 1):
            b.set(bx, yy, bz, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.sphere(bx, y + 1, bz, 2.2, S.BUB, hollow=True)
    OLD.fountain(b, GX, 120)
    OLD.balloon_cart(b, GX + 7, 110)
    OLD.gate(b, GX, NZ - 11)
    # the new rides and the furnished park buildings
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    to_canvas(bb, b)
    for i, x in enumerate(range(52, 104, 6)):
        if abs(x + 1 - GX) > 4:
            T.stall(b, x, 22, ("pink", "yellow", "light_blue", "lime", "orange")[i % 5],
                    (("minecraft:melon", "minecraft:pumpkin", None), ("minecraft:target[power=0]", "minecraft:hay_block[axis=y]", None))[i % 2])
    for z in range(30, NZ - 14, 8):                          # lamp posts down the boulevard and the avenues
        for x in (GX - 4, GX + 4):
            if b.get(x, 1, z) in (None, AIR):
                T.lamp_post(b, x, z)
    for x in range(14, GX - 4, 8):
        if b.get(x, 1, 79) in (None, AIR):
            T.lamp_post(b, x, 79)
    for x in range(GX + 8, 136, 8):
        if b.get(x, 1, 109) in (None, AIR):
            T.lamp_post(b, x, 109)
    # soap bubbles welling up from the roots and the lawns
    for (tx, tz, r, h) in trees:
        for k in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            d = rnd.uniform(6, 9)
            x, z = round(tx + d * math.cos(a)), round(tz + d * math.sin(a))
            if 1 <= x < NX - 1 and 1 <= z < NZ - 1:
                OLD.bubble(b, x, z, rnd, n=rnd.choice((1, 2)))
    for i in range(70):
        x, z = rnd.randint(4, NX - 5), rnd.randint(4, NZ - 5)
        if all(b.get(x + dx, y, z + dz) in (None, AIR) or (b.get(x + dx, y, z + dz) or "").startswith(OLD.LOOSE)
               for dx in (-3, 0, 3) for dz in (-3, 0, 3) for y in range(1, 8)):
            OLD.bubble(b, x, z, rnd, n=rnd.choice((1, 1, 2)))
    x, z = free_spot(b, 99, 129, 107, 135)
    b.chest(x, 1, z, "medium", "south")
    x, z = free_spot(b, 9, 67, 19, 74)
    b.chest(x, 1, z, "easy", "east")
    x, z = free_spot(b, 117, 117, 128, 125)
    b.chest(x, 1, z, "medium", "north")
    return b, 0
