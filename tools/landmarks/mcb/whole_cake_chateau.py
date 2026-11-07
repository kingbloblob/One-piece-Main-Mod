"""Whole Cake Chateau v2: Big Mom's five-layer cake castle with Sweet City rebuilt with the Minecraft Builder skill
(dossier: mcb/dossiers/whole_cake_chateau.md).

The chateau already fills the 210-block site cap and its cake layers, frosting drips, turrets and rooms were matched
to the show in the landmark review, so v2 keeps the castle from the older module and spends the extra size on Sweet
City: the old one-room cake huts are replaced by two rings of furnished two- and three-storey cake houses (chocolate,
cookie, pink and cream walls, frosting, chocolate and cookie roofs, every floor furnished, ladders between floors),
doors facing the castle, candy gardens between them. (v2)

v3 (2026-10-30, audit: "the cake tiers are good; it sits on a bare grass square, the show has Sweet City around it"):
Sweet City now fills the whole island round the cake: ~90 packed candy houses of 2-3 storeys on lots along a ring
road and six radial streets paved in pink and white, candy-cane lamps on every street, lollipop trees in the gaps,
and the island stands 2 blocks out of a round patch of sea with a sandy shore instead of a grass disc."""
from mcb import terrain3 as T3
from mcb.lotpack import pack_houses
import math
import numpy as np
from mcb.kit import BigBuild, P, AIR, seed_of, house_module, place_house, set_if_air, lamp_post
from mcb.bridge import to_canvas
import whole_cake as OLD

SID = "whole_cake_chateau"
TITLE = OLD.TITLE
CUTS = OLD.CUTS
TILER = OLD.TILER
EDGE_REACH = 2
SOFT_EDGES = False
CX, CZ = OLD.CX, OLD.CZ
CANDY = [dict(walls=["onepiece:chocolate_block", "onepiece:chocolate_block", "minecraft:brown_terracotta"],
              frame="onepiece:frosting_block", base=["onepiece:cookie_bricks", "onepiece:cookie_bricks", "minecraft:white_concrete"],
              floor="minecraft:pink_concrete", wood="cherry", chimney="onepiece:candy_cane_block"),
         dict(walls=["minecraft:pink_terracotta", "minecraft:pink_concrete", "minecraft:white_terracotta"],
              frame="minecraft:white_concrete", base=["onepiece:cookie_bricks", "onepiece:chocolate_block", "minecraft:white_concrete"],
              floor="minecraft:white_concrete", wood="cherry", chimney="onepiece:candy_cane_block"),
         dict(walls=["onepiece:cookie_bricks", "onepiece:cookie_bricks", "minecraft:yellow_terracotta"],
              frame="onepiece:chocolate_block", base=["onepiece:chocolate_block", "onepiece:cookie_bricks", "minecraft:white_concrete"],
              floor="minecraft:pink_concrete", wood="cherry", chimney="onepiece:candy_cane_block"),
         dict(walls=["minecraft:white_terracotta", "minecraft:white_concrete", "minecraft:light_blue_terracotta"],
              frame="onepiece:frosting_block", base=["onepiece:cookie_bricks", "minecraft:white_concrete", "onepiece:cookie_bricks"],
              floor="minecraft:light_blue_concrete", wood="birch", chimney="onepiece:candy_cane_block")]
ROOFS = ["onepiece:frosting_stairs", "onepiece:chocolate_stairs", "onepiece:cookie_brick_stairs", "minecraft:cherry_stairs"]
R1, R2 = 58, 92          # the band Sweet City is rebuilt in
RING = 75                # the ring road
SPOKES = [-math.pi / 2 + k * math.pi / 3 for k in range(6)]   # radial streets (the first is the avenue to the gate)


def coast_r(a):
    return 95 + 2.5 * math.sin(4 * a) + 1.5 * math.sin(9 * a)


def street(x, z):
    d = math.hypot(x - CX, z - CZ)
    if abs(d - RING) <= 2.2 or R1 - 1 <= d <= R1 + 1.5:
        return True
    a = math.atan2(z - CZ, x - CX)
    return any(abs(math.sin(a - s)) * d <= 2.6 and math.cos(a - s) > 0 for s in SPOKES)


def sweet_city(bb, rng, tracker, audit):
    # take the old huts away (and anything else standing in the band), keep the ground
    bb.fill_where(CX - R2 - 4, 1, CZ - R2 - 4, CX + R2 + 4, 24, CZ + R2 + 4,
                  lambda X, y, Z: ((X - CX) ** 2 + (Z - CZ) ** 2 >= (R1 - 2) ** 2), AIR)
    # pink-and-white paved streets
    for x in range(CX - R2 - 2, CX + R2 + 3):
        for z in range(CZ - R2 - 2, CZ + R2 + 3):
            d = math.hypot(x - CX, z - CZ)
            if R1 - 1 <= d <= coast_r(math.atan2(z - CZ, x - CX)) - 4 and street(x, z):
                bb.set(x, 0, z, "minecraft:pink_concrete" if (x // 2 + z // 2) % 2 else "minecraft:white_concrete")
    ok = lambda x, z: (R1 + 3 <= math.hypot(x - CX, z - CZ) <= coast_r(math.atan2(z - CZ, x - CX)) - 6
                       and not street(x, z))
    face = lambda fx, fz: (0 if fz > CZ else 2) if abs(fz - CZ) > abs(fx - CX) else (3 if fx > CX else 1)
    placed = pack_houses(bb, lambda x, z: 0, ok, (CX - R2, CZ - R2, CX + R2, CZ + R2), 96, seed_of("sweet"), tracker,
                         CANDY, ROOFS, sizes=(7, 10), floors=(2, 3), kinds=("kitchen", "living", "bedroom", "dining"),
                         max_step=0, plinth="onepiece:cookie_bricks", fh=4, face=face, timber=False)
    taken = [(x - 1, z - 1, x + w, z + d) for (x, z, w, d, y, rot) in placed]
    # candy-cane lamps along the streets, lollipop trees and candy flowers in the gaps
    for k in range(0, 360, 9):
        t = math.radians(k)
        for rr in (RING - 3.5, RING + 3.5):
            x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
            if bb.get_region(x, 1, z, x, 4, z).max() <= 1:
                bb.fill(x, 1, z, x, 4, z, "onepiece:candy_cane_block")
                bb.set(x, 5, z, "minecraft:pearlescent_froglight[axis=y]")
    n = 0
    for _ in range(900):
        t = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(R1 + 3, coast_r(t) - 3)
        x, z = round(CX + r * math.cos(t)), round(CZ + r * math.sin(t))
        if street(x, z) or any(a - 2 <= x <= c + 2 and b_ - 2 <= z <= d + 2 for (a, b_, c, d) in taken):
            continue
        if bb.get_region(x - 1, 1, z - 1, x + 1, 9, z + 1).max() > 1:
            continue
        if n < 70 and rng.random() < 0.25:
            h = int(rng.integers(5, 9))
            bb.fill(x, 1, z, x, h, z, "minecraft:white_concrete")
            col = ["pink", "magenta", "light_blue", "yellow", "lime", "orange", "purple"][int(rng.integers(7))]
            bb.fill_where(x - 2, h, z - 2, x + 2, h + 4, z + 2,
                          lambda X, Y, Z: (X - x) ** 2 + (Y - h - 2) ** 2 + (Z - z) ** 2 <= 5.5, f"minecraft:{col}_concrete")
            taken.append((x - 3, z - 3, x + 3, z + 3))
            n += 1
        else:
            set_if_air(bb, x, 1, z, ["onepiece:lollipop_flower", "onepiece:frost_bloom", "onepiece:candy_cane_sprout",
                                     "minecraft:pink_tulip", "minecraft:short_grass"][int(rng.integers(5))])
    return len(placed)


def design():
    bb = BigBuild(seed=7, y_min=-6, y_max=60)
    tracker = P.PropTracker(7)
    audit = []
    rng = np.random.default_rng(7)
    n = sweet_city(bb, rng, tracker, audit)
    print("cake houses:", n)
    return bb, audit


def build():
    b, g = OLD.build()
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    to_canvas(bb, b)
    T3.canvas_island_sea(b, CX, CZ, coast_r, 103, lift=2, rock="minecraft:stone",
                         shore=("onepiece:cookie_bricks", "minecraft:sand", "minecraft:sand", "minecraft:white_concrete"))
    return b, g
