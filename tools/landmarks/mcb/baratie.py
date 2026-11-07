"""The Baratie, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/baratie.md).

Zeff's fish-shaped sea restaurant: an oval hull with a big white fish head and fat orange lips at the bow, a tall
orange tail fin at the stern, three stepped mint-green tiers (dining hall, kitchen + attic, cooks' quarters + loft),
every step a purple-railed balcony, a red tiled hip roof with a little cupola, BARATIE in big letters on a white band,
RESTAURANT on the top tier, and two green masts with yellow/white swag sails, crow's nests and red BT flags.
Below deck: a crew deck (mess, bunk rooms, laundry) with portholes, and a lower hold (pantry, wine cellar, stores).
The fish head holds a two-level bar. Bow (fish head) points +x. Water surface = y 0. ~193 x 51, flags at y ~123.
(v2, 2026-10-29: ryan asked for builds ~50% bigger with more rooms and decor, not just magnified.)"""
import math
import numpy as np
from mcb.bridge import BigBuild, P, to_canvas
from canvas import B

SID = "baratie"
TITLE = "Baratie"
WATER_Y = -4                             # v3: the sea sits 4 lower, so 10 blocks of hull show (was 5, "thin")
CUTS = [2, 9, 24, 36, 46]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

# ---------------------------------------------------------------- palette roles
HULL = "minecraft:mangrove_planks"
HULL_LOW = "minecraft:dark_oak_planks"
STRAKE = "minecraft:smooth_quartz"
DECK = "minecraft:spruce_planks"
FLOOR = "minecraft:dark_oak_planks"
PART = "minecraft:spruce_planks"                 # partition walls
MINT = ["minecraft:waxed_oxidized_cut_copper", "minecraft:waxed_oxidized_copper", "minecraft:prismarine_bricks"]
MINT_W = [0.55, 0.25, 0.20]
WHITE = "minecraft:smooth_quartz"
WHITE_ST = "minecraft:smooth_quartz_stairs"
YEL = "minecraft:bamboo_planks"
ROOF = "onepiece:dressrosa_tiles"
ROOF_ST = "onepiece:dressrosa_tile_stairs"
ROOF_SL = "onepiece:dressrosa_tile_slab"
POST = "minecraft:purpur_pillar[axis=y]"
RAIL = "minecraft:purple_stained_glass_pane"
GLASS = "minecraft:light_blue_stained_glass_pane"
PORT = "minecraft:light_blue_stained_glass"
MAST = "minecraft:stripped_warped_stem[axis=y]"
NEST = "minecraft:mangrove_planks"
ORANGE = "minecraft:orange_concrete"
ORANGE2 = "minecraft:orange_terracotta"
GOLD = "minecraft:yellow_concrete"
FISH = ["minecraft:white_concrete", "minecraft:smooth_quartz", "minecraft:calcite"]
RED = "minecraft:red_concrete"
AIR = "minecraft:air"

# ---------------------------------------------------------------- layout (all numbers in one place)
CZ = 25                                  # keel line; the site runs z 0..50
ZW = 50
DECK_Y = 6
MID = 83                                 # main doors, dormers, lettering centre
HX0, HX1 = 21, 147                       # hull stern / bow (the head overlaps the bow)
HCX, HHL, HHW = 84.0, 63.75, 23.25
# tiers: (x1, x2, half width, corner radius, floor y, wall top y)
T1 = (39, 126, 17, 10, DECK_Y, 20)       # dining hall (y 7-20), balcony 1 at y 21
T2 = (46, 118, 12, 8, 21, 42)            # kitchen (22-30) + attic behind the BARATIE band (32-42), balcony 2 at y 43
T3 = (52, 112, 8, 5, 43, 58)             # quarters (44-49) + loft behind the RESTAURANT board (51-58), roof from 59
KITCHEN_CEIL = 31
QUARTERS_CEIL = 50
BAND = (31, 42)                          # white BARATIE band on tier 2
MID_DECK = -1                            # crew deck floor (0-5); lower hold floor -8 (-7..-2)
HOLD_FLOOR = -8
HEAD = dict(back=138, cx=150.0, cy=10.0, rx=36.0, ry=19.5, rz=19.5)
MOUTH = dict(cy=7.5, ry=9.0, rz=13.5)
HEAD_MEZZ = 15                           # floor of the upper lounge inside the head
MASTS = ((30, 123), (135, 114))          # (x, top y of the topmast)


def rrect(X, Z, x1, x2, hz, r):
    """Rounded-rectangle footprint mask (stadium-ish ends)."""
    cx = (x1 + x2) / 2.0
    hx = (x2 - x1) / 2.0
    dx = np.maximum(0, np.abs(X - cx) - (hx - r))
    dz = np.maximum(0, np.abs(Z - CZ) - (hz - r))
    return dx * dx + dz * dz <= r * r + 0.5


def hull_half(x):
    """Half-beam of the hull at deck level."""
    t = abs(x - HCX) / HHL
    return HHW * max(0.0, 1 - t ** 3) ** (1 / 3) if t < 1 else 0.0


def hull_mask(X, y, Z, shrink=0.0):
    t = np.clip(np.abs(X - HCX) / HHL, 0, 1)
    half = HHW * np.maximum(0.0, 1 - t ** 3) ** (1 / 3)
    k = 1.0 if y >= 1 else math.sqrt(max(0.0, 1 - ((1 - y) / 14.0) ** 2))  # round bilge down to the keel
    return np.abs(Z - CZ) <= half * k - shrink


def head_mask(X, y, Z, grow=0.0):
    h = HEAD
    return (X >= h["back"]) & (((X - h["cx"]) / (h["rx"] + grow)) ** 2 + ((y - h["cy"]) / (h["ry"] + grow)) ** 2
                               + ((Z - CZ) / (h["rz"] + grow)) ** 2 <= 1.0)


def _cells(bb, x1, y1, z1, x2, y2, z2, name):
    """Yield ((x, y, z), name) of cells painted with `name` in a box."""
    if name not in bb.ids:
        return
    vid = bb.ids[name]
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    for x, y, z in zip(*np.nonzero(reg == vid)):
        yield (x1 + int(x), y1 + int(y), z1 + int(z)), name


def is_air(bb, x, y, z):
    return int(bb.get_region(x, y, z, x, y, z)[0, 0, 0]) in (0, 1)


def set_if_air(bb, x, y, z, block):
    if is_air(bb, x, y, z):
        bb.set(x, y, z, block)


def table(bb, x, y, z, cloth="minecraft:white_carpet", wood="spruce", skip=None):
    """Round restaurant table: fence leg + cloth, a stair chair on each side (one left out now and then)."""
    bb.set(x, y, z, "minecraft:dark_oak_fence")
    bb.set(x, y + 1, z, cloth)
    for i, (dx, dz, f) in enumerate(((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south"))):
        if i == skip:
            continue
        set_if_air(bb, x + dx, y, z + dz, f"minecraft:{wood}_stairs[facing={f},half=bottom]")


# ---------------------------------------------------------------- hull and below deck
def build_hull(bb):
    # shell from the keel up to the deck, then the hold carved out of it
    for y in range(-10, DECK_Y + 1):
        mat = HULL_LOW if y < 0 else (STRAKE if y == DECK_Y - 1 else HULL)
        bb.fill_where(HX0 - 2, y, 0, HX1 + 2, y, ZW, lambda X, yy, Z, y=y: hull_mask(X, y, Z), mat)
    for y in range(HOLD_FLOOR, DECK_Y):
        bb.fill_where(HX0, y, 1, HX1, y, ZW - 1, lambda X, yy, Z, y=y: hull_mask(X, y, Z, 1.2), AIR)
    for fy in (HOLD_FLOOR, MID_DECK):
        bb.fill_where(HX0, fy, 1, HX1, fy, ZW - 1, lambda X, yy, Z, fy=fy: hull_mask(X, fy, Z, 1.2), FLOOR)
    # planked deck with the white strake showing at the edge, and dark planks over the hull beams every 9
    bb.fill_where(HX0, DECK_Y, 1, HX1, DECK_Y, ZW - 1, lambda X, yy, Z: hull_mask(X, DECK_Y, Z, 1.0), DECK)
    for x in range(HX0 + 4, HX1, 9):
        bb.fill_where(x, DECK_Y, 1, x, DECK_Y, ZW - 1, lambda X, yy, Z: hull_mask(X, DECK_Y, Z, 1.0), FLOOR)
    # rubbing strakes: darker wales above the water give the hull relief
    for y in (-3, 0, 3):
        bb.fill_where(HX0, y, 0, HX1, y, ZW, lambda X, yy, Z, y=y: hull_mask(X, y, Z) & ~hull_mask(X, y, Z, 1.0),
                      "minecraft:stripped_mangrove_wood[axis=x]")
    # the boot-top: a dark band at the waterline, gold trim along the top wale
    bb.fill_where(HX0, WATER_Y, 0, HX1, WATER_Y, ZW, lambda X, yy, Z: hull_mask(X, WATER_Y, Z) & ~hull_mask(X, WATER_Y, Z, 1.0),
                  "minecraft:dark_oak_planks")
    bb.fill_where(HX0, 4, 0, HX1, 4, ZW, lambda X, yy, Z: hull_mask(X, 4, Z) & ~hull_mask(X, 4, Z, 1.0), GOLD)
    # portholes for the crew deck, between the wales
    for x in range(HX0 + 9, HX1 - 4, 6):
        hw = hull_half(x)
        if hw < 6:
            continue
        for side in (-1, 1):
            for k in range(0, 3):
                z = CZ + side * (int(hw) - k)
                for y in (1, 2, -2, -1):
                    if y < 0 and (x // 6) % 2:
                        continue
                    if not is_air(bb, x, y, z):
                        bb.set(x, y, z, PORT)
    # purple deck rail round the hull edge (posts every 4), open where the head joins
    for x in range(HX0, HEAD["back"]):
        hw = hull_half(x)
        if hw < 2:
            continue
        zr = int(math.floor(hw - 0.5))
        for z in (CZ - zr, CZ + zr):
            bb.set(x, DECK_Y + 1, z, POST if x % 4 == 0 else RAIL)
    # folded stabiliser fins along the waterline (they fold out in storms)
    for side in (-1, 1):
        for x in range(66, 100):
            u = (x - 66) / 33.0
            out = int(round(5 * math.sin(math.pi * u)))
            z0 = CZ + side * int(hull_half(x))
            for k in range(1, out + 1):
                bb.set(x, WATER_Y, z0 + side * k, ORANGE if k < out else GOLD)
                bb.set(x, WATER_Y - 1, z0 + side * k, ORANGE2)
    # masts run down through the decks to the keel
    for (mx, mtop) in MASTS:
        bb.fill(mx - 1, HOLD_FLOOR, CZ - 1, mx + 1, DECK_Y, CZ + 1, MAST)


def below_deck(bb, tracker, rooms_all):
    """Crew deck (y 0-5) with side passages under the portholes, and the lower hold (y -7..-2)."""
    y = MID_DECK + 1
    # crew deck: a block of rooms down the middle, passages along both hull sides, an open stair lobby aft
    bb.fill(43, y, CZ - 15, 125, y + 5, CZ - 15, PART)
    bb.fill(43, y, CZ + 15, 125, y + 5, CZ + 15, PART)
    bb.fill(43, y, CZ - 14, 43, y + 5, CZ + 14, PART)
    bb.fill(125, y, CZ - 14, 125, y + 5, CZ + 14, PART)
    for (x, z) in ((43, CZ), (125, CZ), (64, CZ - 15), (104, CZ + 15), (84, CZ - 15)):
        bb.fill(x, y, z, x, y + 1, z, AIR)
    rms, doors = P.bsp_rooms(bb, 44, CZ - 14, 124, CZ + 14, y, 6, PART, min_room=7, seed=41, max_room=16)
    doors = list(doors) + [(43, CZ), (125, CZ), (64, CZ - 15), (104, CZ + 15), (84, CZ - 15)]
    kinds = ["kitchen", "bedroom", "storage", "bedroom", "workshop", "living", "bedroom"]
    for i, rm in enumerate(rms):
        P.furnish_room(bb, rm, y, kind=kinds[i % len(kinds)], height=5, seed=60 + i, doors=doors,
                       wood="dark_oak", tracker=tracker)
        rooms_all.append((rm, y, 5))
    # lanterns along the side passages
    for x in range(48, 124, 10):
        for side in (-1, 1):
            bb.set(x, y + 4, CZ + side * 16, "minecraft:lantern[hanging=true]")
            bb.set(x, y + 5, CZ + side * 16, "minecraft:iron_chain[axis=y]")
    # lower hold: big store rooms
    y = HOLD_FLOOR + 1
    rms, doors = P.bsp_rooms(bb, 36, CZ - 12, 130, CZ + 12, y, 6, PART, min_room=9, seed=43, max_room=26)
    kinds = ["storage", "kitchen", "storage", "workshop"]
    for i, rm in enumerate(rms):
        P.furnish_room(bb, rm, y, kind=kinds[i % len(kinds)], height=6, seed=80 + i, doors=doors,
                       wood="dark_oak", tracker=tracker)
        rooms_all.append((rm, y, 6))
    # stairs: lower hold -> crew deck, crew deck -> main deck (an aft hatch with a rail round it)
    P.stair_run(bb, 28, HOLD_FLOOR + 1, CZ + 4, 7, 2, "east", "minecraft:spruce_stairs")
    bb.fill(30, MID_DECK, CZ + 4, 33, MID_DECK, CZ + 5, AIR)
    P.stair_run(bb, 26, MID_DECK + 1, CZ - 6, 7, 2, "east", "minecraft:spruce_stairs")
    bb.fill(28, DECK_Y, CZ - 6, 31, DECK_Y, CZ - 5, AIR)
    for x in range(26, 33):
        bb.set(x, DECK_Y + 1, CZ - 7, "minecraft:spruce_fence")
        if x < 32:
            bb.set(x, DECK_Y + 1, CZ - 4, "minecraft:spruce_fence")
    bb.fill(25, DECK_Y + 1, CZ - 6, 25, DECK_Y + 1, CZ - 5, "minecraft:spruce_fence")


# ---------------------------------------------------------------- fish head (two-level bar inside)
def build_head(bb, tracker, rooms_all):
    h = HEAD
    lo_x, hi_x = h["back"], int(h["cx"] + h["rx"]) + 1
    m = MOUTH
    xm = int(h["cx"] + 12)
    throat = xm + 5
    for y in range(int(h["cy"] - h["ry"]), int(h["cy"] + h["ry"]) + 1):
        if y < -10:
            continue
        shell = lambda X, yy, Z, y=y: head_mask(X, y, Z) & ~head_mask(X, y, Z, -2.0)
        bb.fill_where(lo_x, y, 0, hi_x, y, ZW, shell, FISH[0])
        # solid in front of the throat (only the mouth tunnel is open there), closed back wall at the hull
        bb.fill_where(throat, y, 0, hi_x, y, ZW, lambda X, yy, Z, y=y: head_mask(X, y, Z) & (X >= throat), FISH[0])
        bb.fill_where(lo_x, y, 0, lo_x, y, ZW, lambda X, yy, Z, y=y: head_mask(X, y, Z), FISH[0])
    # texture: smooth quartz / calcite flecks on the white
    rng = np.random.default_rng(11)
    for (x, y, z), _ in list(_cells(bb, lo_x, -10, 0, hi_x, 30, ZW, FISH[0])):
        r = rng.random()
        if r < 0.2: bb.set(x, y, z, FISH[1])
        elif r < 0.3: bb.set(x, y, z, FISH[2])
    # inside: the bar on the deck, a lounge floor above it
    inner = lambda X, y, Z: head_mask(X, y, Z, -2.0) & (X > lo_x) & (X < throat)
    bb.fill_where(lo_x, DECK_Y + 1, 0, throat, 28, ZW, inner, AIR)
    bb.fill_where(lo_x, DECK_Y, 0, throat, DECK_Y, ZW, lambda X, y, Z: head_mask(X, DECK_Y, Z, -2.0), FLOOR)
    bb.fill_where(lo_x + 1, HEAD_MEZZ, 0, throat - 1, HEAD_MEZZ, ZW,
                  lambda X, y, Z: head_mask(X, HEAD_MEZZ, Z, -2.0) & (X > lo_x), FLOOR)
    # collar: an orange band where the head meets the hull, a little proud of the head
    for y in range(-9, 28):
        bb.fill_where(lo_x, y, 0, lo_x + 3, y, ZW,
                      lambda X, yy, Z, y=y: head_mask(X, y, Z, 1.0) & ~head_mask(X, y, Z, -1.0), ORANGE)
    # mouth: carve an oval tunnel through the front, ring it with fat orange lips and a yellow inner edge
    def mouth_d(y, Z):
        return ((y - m["cy"]) / m["ry"]) ** 2 + ((Z - CZ) / m["rz"]) ** 2
    for y in range(int(m["cy"] - m["ry"] - 4), int(m["cy"] + m["ry"] + 5)):
        lips = lambda X, yy, Z, y=y: (mouth_d(y, Z) <= 2.0) & (mouth_d(y, Z) > 1.0) & head_mask(X, y, Z, 3.0) & (X >= xm)
        bb.fill_where(xm, y, 0, hi_x + 4, y, ZW, lips, ORANGE)
        edge = lambda X, yy, Z, y=y: (mouth_d(y, Z) <= 1.25) & (mouth_d(y, Z) > 1.0) & head_mask(X, y, Z, 3.0) & (X >= xm)
        bb.fill_where(xm, y, 0, hi_x + 4, y, ZW, edge, GOLD)
        hole = lambda X, yy, Z, y=y: (mouth_d(y, Z) <= 1.0) & (X > throat) & head_mask(X, y, Z, 3.3)
        bb.fill_where(throat + 1, y, 0, hi_x + 4, y, ZW, hole, AIR)
    # throat (dark) and three cannons in the mouth (Bandai note), sitting on a dark plank floor
    bb.fill_where(throat, int(m["cy"] - m["ry"]), 0, throat, int(m["cy"] + m["ry"]), ZW,
                  lambda X, y, Z: mouth_d(y, Z) <= 1.0, "minecraft:black_concrete")
    yfloor = int(m["cy"] - m["ry"]) + 1
    bb.fill_where(throat + 1, yfloor, 0, hi_x + 4, yfloor, ZW,
                  lambda X, y, Z: (mouth_d(yfloor + 1, Z) <= 1.0) & head_mask(X, yfloor, Z, 1.0), "minecraft:dark_oak_planks")
    for dz in (-6, 0, 6):
        bb.set(throat + 4, yfloor + 1, CZ + dz, "onepiece:cannon[facing=east]")
    # eyes: white disc, orange ring, black pupil, on both cheeks
    ex, ey = int(h["cx"] + 13), int(h["cy"] + 9)
    for side in (-1, 1):
        zs = CZ + side * int(round(h["rz"] * math.sqrt(max(0, 1 - ((ex - h["cx"]) / h["rx"]) ** 2 - ((ey - h["cy"]) / h["ry"]) ** 2))))
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                d = math.hypot(dx, dy)
                if d > 5.0:
                    continue
                s = "minecraft:black_concrete" if d <= 2.2 else ("minecraft:white_concrete" if d <= 3.7 else ORANGE)
                bb.set(ex + dx, ey + dy, zs + side, s)
    # pectoral fins behind the cheeks, standing just off the head surface
    for side in (-1, 1):
        for i in range(8):
            x, y = h["back"] + 6 + i, 3 - i // 2
            zsurf = h["rz"] * math.sqrt(max(0, 1 - ((x - h["cx"]) / h["rx"]) ** 2 - ((y - h["cy"]) / h["ry"]) ** 2))
            for t in (0, 1):
                bb.set(x, y - t, CZ + side * (int(zsurf) + 1), GOLD if i == 7 else ORANGE)
    # door from the deck through the back wall, with an orange arch
    P.arched_opening(bb, "z", CZ, DECK_Y + 1, lo_x, 3, 4, depth=4, trim=None, fill=AIR)
    bb.set(lo_x, DECK_Y + 1, CZ - 1, "minecraft:spruce_door[facing=west,half=lower,hinge=left,open=true]")
    bb.set(lo_x, DECK_Y + 2, CZ - 1, "minecraft:spruce_door[facing=west,half=upper,hinge=left,open=true]")
    # the bar: a long counter, stools, barrels and shelves behind, little tables by the cheeks
    y = DECK_Y + 1
    bx = lo_x + 18
    for z in range(CZ - 8, CZ + 9):
        bb.set(bx, y, z, "onepiece:spruce_counter[facing=west]")
    for z in range(CZ - 7, CZ + 8, 3):
        bb.set(bx - 2, y, z, "minecraft:spruce_trapdoor[facing=west,half=top,open=false]")
    for z in range(CZ - 7, CZ + 8, 2):
        set_if_air(bb, bx + 3, y, z, "minecraft:barrel[facing=west]")
        set_if_air(bb, bx + 3, y + 2, z, "minecraft:spruce_slab[type=bottom]" if z % 4 else "minecraft:brewing_stand")
    for z in (CZ - 4, CZ + 4):
        bb.set(bx + 1, y, z, "minecraft:brewing_stand")
    for (tx, tz) in ((lo_x + 6, CZ - 9), (lo_x + 6, CZ + 9), (lo_x + 11, CZ - 12), (lo_x + 11, CZ + 12)):
        table(bb, tx, y, tz, cloth="minecraft:orange_carpet", wood="dark_oak", skip=(tx + tz) % 4)
    # stairs up to the lounge (along the starboard side), with a rail round the opening
    P.stair_run(bb, lo_x + 3, y, CZ + 8, 9, 2, "east", "minecraft:spruce_stairs")
    bb.fill(lo_x + 7, HEAD_MEZZ, CZ + 8, lo_x + 10, HEAD_MEZZ, CZ + 9, AIR)
    for x in range(lo_x + 7, lo_x + 11):
        bb.set(x, HEAD_MEZZ + 1, CZ + 7, "minecraft:spruce_fence")
    lounge = (lo_x + 4, CZ - 10, lo_x + 24, CZ + 6)
    P.furnish_room(bb, lounge, HEAD_MEZZ + 1, kind="living", height=6, seed=17, wood="dark_oak", tracker=tracker)
    rooms_all.append((lounge, HEAD_MEZZ + 1, 6))


def build_tail(bb):
    """Tall fan tail fin at the stern: radial orange ribs, yellow rim, scalloped top."""
    rx, ry = 22, 4          # root of the fan
    for x in range(-3, 25):
        for y in range(WATER_Y + 1, 46):
            top = 18 + (22 - x) * 0.95 - (2.0 if (x % 6) == 1 else 0)
            bot = WATER_Y + 1 + max(0, 13 - x) * 0.9
            if not (bot <= y <= top) or x > 22:
                continue
            ang = math.atan2(y - ry, rx - x)
            rim = y >= top - 1 or y <= bot + 0.6 or x <= -2
            s = GOLD if rim else (ORANGE if int(ang * 12) % 2 == 0 else ORANGE2)
            for dz in (-2, -1, 0, 1, 2):
                if dz and (rim or x < 3):
                    continue
                if abs(dz) == 2 and x < 9:
                    continue
                bb.set(x, y, CZ + dz, s)


# ---------------------------------------------------------------- the stepped building
def build_tier(bb, t):
    x1, x2, hz, r, fy, top = t
    reg = (x1 - 2, fy, CZ - hz - 2, x2 + 2, top, CZ + hz + 2)
    outer = lambda X, Z: rrect(X, Z, x1, x2, hz, r)
    inner = lambda X, Z: rrect(X, Z, x1 + 1, x2 - 1, hz - 1, max(1, r - 1))
    for y in range(fy + 1, top + 1):
        bb.fill_where(reg[0], y, reg[2], reg[3], y, reg[5], lambda X, yy, Z: outer(X, Z) & ~inner(X, Z), MINT[0])
    bb.fill_where(reg[0], fy + 1, reg[2], reg[3], top, reg[5], lambda X, y, Z: inner(X, Z), AIR)
    bb.fill_where(reg[0], fy, reg[2], reg[3], fy, reg[5], lambda X, y, Z: outer(X, Z), FLOOR)
    # mottled mint: mix the three greens over the wall shell
    rng = np.random.default_rng(x1)
    for (x, y, z), _ in list(_cells(bb, *reg, MINT[0])):
        v = rng.random()
        if v < MINT_W[1]: bb.set(x, y, z, MINT[1])
        elif v < MINT_W[1] + MINT_W[2]: bb.set(x, y, z, MINT[2])
    # white plinth one proud of the wall
    bb.fill_where(reg[0], fy + 1, reg[2], reg[3], fy + 1, reg[5],
                  lambda X, yy, Z: rrect(X, Z, x1 - 1, x2 + 1, hz + 1, r + 1) & ~outer(X, Z), WHITE)
    # ceiling / balcony floor one proud all round
    bb.fill_where(reg[0], top + 1, reg[2], reg[3], top + 1, reg[5],
                  lambda X, y, Z: rrect(X, Z, x1 - 1, x2 + 1, hz + 1, r + 1), "minecraft:spruce_planks")


def window_xs(t, spacing, center=MID):
    x1, x2, hz, r, fy, top = t
    lo, hi = x1 + r + 2, x2 - r - 2
    return [center + spacing * k for k in range(-30, 31) if lo <= center + spacing * k <= hi]


def long_wall_windows(bb, t, y0, h, spacing=9, width=5, skip=(), ptop=None):
    """Arched light-blue windows with bamboo (yellow) frames and a quartz sill, white pilasters between them,
    on both long faces of a tier. Windows are laid out symmetrically about MID."""
    x1, x2, hz, r, fy, top = t
    xs = window_xs(t, spacing)
    for side in (-1, 1):
        zf = CZ + side * hz
        for xc in xs:
            if xc in skip:
                continue
            P.arched_opening(bb, "x", xc, y0, zf, width, h, depth=1, trim=YEL, fill=GLASS)
            for dx in range(-(width // 2), width // 2 + 1):  # sill: an upside-down stair poking out
                bb.set(xc + dx, y0 - 1, zf + side, f"{WHITE_ST}[facing={'north' if side > 0 else 'south'},half=top]")
        for xc in xs[:-1]:
            px = xc + spacing // 2
            bb.fill(px, fy + 1, zf + side, px, ptop or top, zf + side, WHITE)
    return xs


def end_windows(bb, t, y0):
    """A tall window in each curved end."""
    x1, x2, hz, r, fy, top = t
    for x in (x1, x2):
        bb.fill(x, y0, CZ - 1, x, y0 + 2, CZ + 1, GLASS)
        bb.fill(x, y0 - 1, CZ - 2, x, y0 - 1, CZ + 2, YEL); bb.fill(x, y0 + 3, CZ - 2, x, y0 + 3, CZ + 2, YEL)
        bb.fill(x, y0, CZ - 2, x, y0 + 2, CZ - 2, YEL); bb.fill(x, y0, CZ + 2, x, y0 + 2, CZ + 2, YEL)


def balcony_rail(bb, t):
    x1, x2, hz, r, fy, top = t
    y = top + 2
    reg = (x1 - 2, y, CZ - hz - 2, x2 + 2, y, CZ + hz + 2)
    ring = lambda X, yy, Z: rrect(X, Z, x1 - 1, x2 + 1, hz + 1, r + 1) & ~rrect(X, Z, x1, x2, hz, r)
    bb.fill_where(*reg, ring, RAIL)
    for (x, yy, z), _ in list(_cells(bb, *reg, RAIL)):
        if (x + z) % 4 == 0:
            bb.set(x, yy, z, POST)


def grand_door(bb, xc, side, t):
    """Main dining-hall door: a 5-wide bamboo arch, two pairs of doors with a post between, glass transom."""
    x1, x2, hz, r, fy, top = t
    zf = CZ + side * hz
    face = "south" if side > 0 else "north"
    P.arched_opening(bb, "x", xc, fy + 1, zf, 5, 8, depth=1, trim=YEL, fill=GLASS)
    for dx, hinge in ((-2, "left"), (-1, "right"), (1, "left"), (2, "right")):
        bb.set(xc + dx, fy + 1, zf, f"minecraft:spruce_door[facing={face},half=lower,hinge={hinge},open=false]")
        bb.set(xc + dx, fy + 2, zf, f"minecraft:spruce_door[facing={face},half=upper,hinge={hinge},open=false]")
    bb.fill(xc, fy + 1, zf, xc, fy + 2, zf, YEL)
    bb.fill(xc - 2, fy + 3, zf, xc + 2, fy + 3, zf, YEL)


def small_door(bb, x, side, t, leaf="minecraft:spruce_door"):
    x1, x2, hz, r, fy, top = t
    zf = CZ + side * hz
    face = "south" if side > 0 else "north"
    bb.set(x, fy + 1, zf, f"{leaf}[facing={face},half=lower,hinge=left,open=false]")
    bb.set(x, fy + 2, zf, f"{leaf}[facing={face},half=upper,hinge=left,open=false]")


def build_building(bb):
    # ---- tier 1: dining hall
    build_tier(bb, T1)
    x1, x2, hz, r, fy, top = T1
    long_wall_windows(bb, T1, fy + 3, 9, spacing=9, width=5, skip=(MID,))
    end_windows(bb, T1, fy + 6)
    for side in (-1, 1):
        grand_door(bb, MID, side, T1)
        zf = CZ + side * hz
        # yellow arch canopy over the main doors (the show's yellow arched entrance)
        for dx in range(-4, 5):
            hgt = 10 + (1 if abs(dx) <= 1 else 0) - (1 if abs(dx) == 4 else 0)
            bb.set(MID + dx, fy + hgt, zf + side, GOLD)
            bb.set(MID + dx, fy + hgt, zf + 2 * side, GOLD)
        for dx in (-4, 4):
            bb.fill(MID + dx, fy + 1, zf + 2 * side, MID + dx, fy + 8, zf + 2 * side, GOLD)
        bb.set(MID - 3, fy + 4, zf + side, "onepiece:wall_lamp[facing=" + ("south" if side > 0 else "north") + "]")
        bb.set(MID + 3, fy + 4, zf + side, "onepiece:wall_lamp[facing=" + ("south" if side > 0 else "north") + "]")
    balcony_rail(bb, T1)
    # ---- tier 2: kitchen with the white BARATIE band (the attic sits behind it)
    build_tier(bb, T2)
    x1, x2, hz, r, fy, top = T2
    long_wall_windows(bb, T2, fy + 3, 5, spacing=8, width=3, ptop=BAND[0] - 1)
    end_windows(bb, T2, fy + 4)
    bb.fill_where(x1 - 2, BAND[0], CZ - hz - 2, x2 + 2, BAND[1], CZ + hz + 2,
                  lambda X, y, Z: rrect(X, Z, x1, x2, hz, r) & ~rrect(X, Z, x1 + 1, x2 - 1, hz - 1, max(1, r - 1)), WHITE)
    for yb in (BAND[0], BAND[1] + 1):
        bb.fill_where(x1 - 2, yb, CZ - hz - 2, x2 + 2, yb, CZ + hz + 2,
                      lambda X, y, Z: rrect(X, Z, x1 - 1, x2 + 1, hz + 1, r + 1) & ~rrect(X, Z, x1, x2, hz, r),
                      "minecraft:stripped_dark_oak_wood[axis=y]")
    bb.fill_where(x1 + 1, KITCHEN_CEIL, CZ - hz + 1, x2 - 1, KITCHEN_CEIL, CZ + hz - 1,
                  lambda X, y, Z: rrect(X, Z, x1 + 1, x2 - 1, hz - 1, max(1, r - 1)), "minecraft:spruce_planks")
    for side in (-1, 1):     # doors from the kitchen onto balcony 1, both ends
        small_door(bb, 57, side, T2)
        small_door(bb, 108, side, T2)
    balcony_rail(bb, T2)
    # ---- tier 3: quarters + loft; RESTAURANT board on the upper half of both long faces
    build_tier(bb, T3)
    x1, x2, hz, r, fy, top = T3
    long_wall_windows(bb, T3, fy + 3, 4, spacing=9, width=3, skip=(MID,), ptop=fy + 7)
    end_windows(bb, T3, fy + 3)
    end_windows(bb, T3, QUARTERS_CEIL + 3)
    bb.fill_where(x1 + 1, QUARTERS_CEIL, CZ - hz + 1, x2 - 1, QUARTERS_CEIL, CZ + hz - 1,
                  lambda X, y, Z: rrect(X, Z, x1 + 1, x2 - 1, hz - 1, max(1, r - 1)), "minecraft:spruce_planks")
    for side in (-1, 1):
        zf = CZ + side * hz
        bb.fill(x1 + 4, fy + 8, zf, x2 - 4, top, zf, WHITE)               # board
        bb.fill(x1 + 4, fy + 8, zf + side, x2 - 4, fy + 8, zf + side, f"{WHITE_ST}[facing={'north' if side > 0 else 'south'},half=top]")
        bb.fill(x1 + 4, top, zf + side, x2 - 4, top, zf + side, f"{WHITE_ST}[facing={'north' if side > 0 else 'south'},half=bottom]")
        P.arched_opening(bb, "x", MID, fy + 1, zf, 3, 5, depth=1, trim=YEL, fill=AIR)
        small_door(bb, MID, side, T3, leaf="minecraft:crimson_door")
    # ---- roof: red hip roof, quartz eave line, cross gables, a mint cupola and a chimney
    ry = top + 1
    bb.fill_where(x1 - 2, ry, CZ - hz - 2, x2 + 2, ry, CZ + hz + 2,
                  lambda X, y, Z: rrect(X, Z, x1 - 1, x2 + 1, hz + 1, r + 1), WHITE)
    peak = P.hip_roof(bb, x1 - 1, CZ - hz - 1, x2 + 1, CZ + hz + 1, ry + 1, ROOF_ST, ridge=ROOF_SL + "[type=bottom]", overhang=0)
    for i in range(0, peak - ry):
        if x1 + i <= x2 - i and CZ - hz + i <= CZ + hz - i:
            bb.fill(x1 + i, ry + 1 + i, CZ - hz + i, x2 - i, ry + 1 + i, CZ + hz - i, ROOF)
    for gx in (MID, 64, 102):     # dormers: a big one over the doors, two small ones
        big = gx == MID
        n = 6 if big else 4
        for side in (-1, 1):
            zf = CZ + side * (hz + 1)
            for i in range(n):
                yy = ry + 1 + i
                for dz in range(0, n - 1):
                    z = zf - side * dz
                    bb.set(gx - n + 1 + i, yy, z, f"{ROOF_ST}[facing=east,half=bottom]")
                    bb.set(gx + n - 1 - i, yy, z, f"{ROOF_ST}[facing=west,half=bottom]")
                    if gx - n + 2 + i <= gx + n - 2 - i:
                        bb.fill(gx - n + 2 + i, yy, z, gx + n - 2 - i, yy, z, MINT[0] if dz == 0 else ROOF)
            bb.fill(gx - (1 if big else 0), ry + 2, zf, gx + (1 if big else 0), ry + 3, zf, GLASS)
    cx = 72
    bb.fill(cx - 3, peak, CZ - 3, cx + 3, peak + 5, CZ + 3, MINT[0])
    bb.fill(cx - 2, peak + 1, CZ - 3, cx + 2, peak + 4, CZ + 3, GLASS)
    bb.fill(cx - 3, peak + 1, CZ - 2, cx + 3, peak + 4, CZ + 2, GLASS)
    bb.fill(cx - 2, peak, CZ - 2, cx + 2, peak + 5, CZ + 2, AIR)
    P.hip_roof(bb, cx - 3, CZ - 3, cx + 3, CZ + 3, peak + 6, ROOF_ST, overhang=1)
    bb.fill(99, peak - 5, CZ + 3, 100, peak + 4, CZ + 4, "minecraft:bricks")
    bb.set(99, peak + 5, CZ + 3, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    bb.set(100, peak + 5, CZ + 4, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")


def disc(bb, cx, cz, r, y1, y2, block, hollow=False):
    """Cylinder with a half-block centre (mcbig.cylinder wants integer centres)."""
    R = int(math.ceil(r)) + 1
    def f(X, y, Z):
        d = (X - cx) ** 2 + (Z - cz) ** 2
        m = d <= r * r
        return m & (d > (r - 1) ** 2) if hollow else m
    bb.fill_where(int(cx) - R, y1, int(cz) - R, int(cx) + R, y2, int(cz) + R, f, block)


def build_masts(bb):
    """Green masts, crow's nests, a square sail and a furled topsail on each, BT flags, ratlines."""
    for (mx, mtop) in MASTS:
        nest1 = mtop - 51
        bb.fill(mx - 1, DECK_Y + 1, CZ - 1, mx + 1, mtop, CZ + 1, MAST)
        for ny, rad in ((nest1, 4.8), (mtop - 12, 3.4)):
            disc(bb, mx, CZ, rad - 0.8, ny - 1, ny - 1, NEST)
            disc(bb, mx, CZ, rad, ny, ny + 1, "minecraft:stripped_mangrove_wood[axis=y]", hollow=True)
            disc(bb, mx, CZ, rad - 1.0, ny, ny, NEST)
            bb.fill(mx - 1, ny, CZ - 1, mx + 1, ny + 1, CZ + 1, MAST)
            bb.set(mx + 2, ny + 2, CZ + 2, "minecraft:lantern[hanging=false]")
        # yards braced round 30 degrees (as the show draws them). v3: a full square sail on the lower yard (white with
        # an orange band, bellied forward, tapering a little) and a furled sail rolled on the upper yard, instead of
        # the yellow/white swags that read as fringe
        brace = math.radians(30)
        ux, uz = math.sin(brace), math.cos(brace)          # along the yard
        for (yy, half, drop, furl) in ((nest1 - 18, 22, 15, False), (mtop - 30, 17, 0, True)):
            done = set()
            for i in range(-half * 4, half * 4 + 1):
                t = i / 4.0
                x = int(math.floor(mx + 0.5 + ux * t)); z = int(math.floor(CZ + 0.5 + uz * t))
                if (x, z) in done:
                    continue
                done.add((x, z))
                bb.set(x, yy, z, "minecraft:stripped_spruce_log[axis=z]")
                if furl:
                    bb.set(x + 1, yy, z, "minecraft:white_wool"); bb.set(x + 1, yy - 1, z, "minecraft:white_wool")
                    continue
                edge = abs(t) / half
                d = drop - int(round(2 * edge ** 2))
                for k in range(1, d + 1):
                    v = k / d
                    belly = int(round(2.2 * math.sin(math.pi * v) * (1 - 0.6 * edge ** 2)))
                    col = ORANGE if 0.38 <= v <= 0.62 else "minecraft:white_wool"
                    if abs(t) >= half - 0.5 or k == d:
                        col = GOLD
                    bb.set(x + 1 + belly, yy - k, z, col)
        # the sheets: lines from the lower sail's corners down to the rail
        for side in (-1, 1):
            t = side * 21.5
            x = int(math.floor(mx + 0.5 + ux * t)); z = int(math.floor(CZ + 0.5 + uz * t))
            y0 = nest1 - 18 - 14
            zr = CZ + side * int(hull_half(mx + 8) - 1)
            n = max(1, y0 - DECK_Y - 2)
            for i in range(n + 1):
                u = i / n
                bb.set(int(round(x + 1 + (mx + 8 - x - 1) * u)), int(round(y0 - (y0 - DECK_Y - 2) * u)),
                       int(round(z + (zr - z) * u)), "minecraft:spruce_fence")
        # red BT flag at the top, flying aft (-x)
        for dx in range(2, 15):
            for dy in range(0, 9):
                bb.set(mx - dx, mtop - dy, CZ, RED)
        # ratlines: three shrouds per side from the deck rail to the lower nest
        for side in (-1, 1):
            zr = CZ + side * int(hull_half(mx) - 1)
            for dx in (-4, 0, 4):
                p0 = (mx + dx, DECK_Y + 2, zr)
                p1 = (mx + (1 if dx > 0 else -1 if dx < 0 else 0), nest1 - 1, CZ + side * 3)
                n = max(abs(p1[1] - p0[1]), abs(p1[2] - p0[2]))
                for i in range(n + 1):
                    t = i / n
                    bb.set(int(round(p0[0] + (p1[0] - p0[0]) * t)), int(round(p0[1] + (p1[1] - p0[1]) * t)),
                           int(round(p0[2] + (p1[2] - p0[2]) * t)), "minecraft:spruce_fence")


# ---------------------------------------------------------------- interiors
def furnish(bb, tracker, rooms_all):
    # dining hall (hero room): four rows of tables, an aisle between the main doors, a bar at the stern end, a
    # little stage with a piano at the bow end; chandeliers come from the finishing pass
    x1, x2, hz, r, fy, top = T1
    y = fy + 1
    for x in range(x1 + 12, x2 - 8, 7):
        if abs(x - MID) <= 4:
            continue
        for k, z in enumerate((CZ - 11, CZ - 4, CZ + 4, CZ + 11)):
            if 56 <= x <= 74 and z == CZ + 11:
                continue                                  # stairs to the kitchen run here
            table(bb, x, y, z, skip=(x + k) % 5)
    for z in range(CZ - 12, CZ + 13):
        if abs(z - CZ) > 1:
            set_if_air(bb, x1 + 6, y, z, "onepiece:spruce_counter[facing=east]")
    for z in range(CZ - 12, CZ + 13, 3):
        set_if_air(bb, x1 + 3, y, z, "minecraft:barrel[facing=east]")
        set_if_air(bb, x1 + 3, y + 1, z, "minecraft:barrel[facing=east]" if z % 2 else "minecraft:brewing_stand")
    for z in range(CZ - 10, CZ + 11, 4):
        set_if_air(bb, x1 + 8, y, z, "minecraft:spruce_trapdoor[facing=east,half=top,open=false]")
    # stage at the bow end: raised planks, a piano (blackstone + quartz keys), note blocks and a jukebox
    bb.fill(x2 - 7, fy, CZ - 6, x2 - 2, fy, CZ + 6, "minecraft:dark_oak_planks")
    bb.fill(x2 - 7, y, CZ - 6, x2 - 3, y, CZ + 6, "minecraft:dark_oak_slab[type=bottom]")
    bb.fill(x2 - 4, y + 1, CZ - 3, x2 - 4, y + 1, CZ + 1, "minecraft:polished_blackstone")
    bb.fill(x2 - 5, y + 1, CZ - 3, x2 - 5, y + 1, CZ + 1, "minecraft:quartz_slab[type=bottom]")
    bb.set(x2 - 6, y + 1, CZ - 1, "minecraft:dark_oak_stairs[facing=east,half=bottom]")
    bb.set(x2 - 4, y + 1, CZ + 4, "minecraft:jukebox")
    bb.set(x2 - 4, y + 1, CZ - 5, "minecraft:note_block")
    for z in (CZ - 6, CZ + 6):
        bb.set(x2 - 7, y + 1, z, "minecraft:potted_azalea_bush")
    # stairs up to the kitchen (inside the dining hall along the starboard wall), rail round the hole
    P.stair_run(bb, 58, y, CZ + 10, 15, 2, "east", "minecraft:spruce_stairs")
    bb.fill(67, T2[4], CZ + 10, 71, T2[4], CZ + 11, AIR)
    for x in range(66, 72):
        bb.set(x, T2[4] + 1, CZ + 9, "minecraft:spruce_fence")
    # kitchen: stoves and counters along the north wall, two rows of prep islands, a sink corner, Zeff's office
    x1, x2, hz, r, fy, top = T2
    y = fy + 1
    for x in range(x1 + 8, x2 - 16, 3):
        bb.set(x, y, CZ - hz + 1, "onepiece:iron_stove[facing=south]" if x % 2 else "minecraft:smoker[facing=south,lit=true]")
        bb.set(x + 1, y, CZ - hz + 1, "onepiece:spruce_counter[facing=south]")
        bb.set(x + 2, y, CZ - hz + 1, "onepiece:spruce_counter[facing=south]")
        bb.set(x, y + 3, CZ - hz + 1, "minecraft:iron_chain[axis=y]") if x % 6 == 0 else None
    for x in range(x1 + 14, x2 - 22, 9):
        bb.fill(x, y, CZ - 3, x + 4, y, CZ - 2, "onepiece:spruce_counter[facing=north]")
        bb.fill(x, y, CZ + 2, x + 4, y, CZ + 3, "onepiece:spruce_counter[facing=south]")
        bb.set(x + 2, y + 1, CZ - 2, "minecraft:candle[candles=2,lit=true]")
    for x in (76, 78, 80):
        bb.set(x, y, CZ + hz - 1, "minecraft:water_cauldron[level=3]")
    bb.set(82, y, CZ + hz - 1, "minecraft:crafting_table")
    bb.set(84, y, CZ + hz - 1, "minecraft:barrel[facing=north]")
    bb.set(85, y, CZ + hz - 1, "minecraft:barrel[facing=north]")
    bb.set(86, y, CZ + hz - 1, "minecraft:composter[level=0]")
    ox = x2 - 14
    bb.fill(ox, y, CZ - hz + 1, ox, KITCHEN_CEIL - 1, CZ + hz - 1, PART)  # office wall
    bb.set(ox, y, CZ, "minecraft:spruce_door[facing=east,half=lower,hinge=left,open=false]")
    bb.set(ox, y + 1, CZ, "minecraft:spruce_door[facing=east,half=upper,hinge=left,open=false]")
    office = (ox + 2, CZ - 8, x2 - 6, CZ + 8)
    P.furnish_room(bb, office, y, kind="library", height=KITCHEN_CEIL - y, seed=3, wood="spruce", tracker=tracker)
    rooms_all.append((office, y, KITCHEN_CEIL - y))
    # stairs kitchen -> attic -> quarters
    P.stair_run(bb, x1 + 6, y, CZ - 9, 10, 2, "east", "minecraft:spruce_stairs")
    bb.fill(x1 + 11, KITCHEN_CEIL, CZ - 9, x1 + 14, KITCHEN_CEIL, CZ - 8, AIR)
    ay = KITCHEN_CEIL + 1
    P.stair_run(bb, x1 + 4, ay, CZ + 5, 12, 2, "east", "minecraft:spruce_stairs")
    bb.fill(x1 + 11, T3[4], CZ + 5, x1 + 14, T3[4], CZ + 6, AIR)
    rms, doors = P.bsp_rooms(bb, x1 + 18, CZ - hz + 2, x2 - 6, CZ + hz - 2, ay, BAND[1] - ay + 1, PART,
                             min_room=8, seed=5, max_room=22)
    kinds = ["storage", "workshop", "storage", "bedroom"]
    for i, rm in enumerate(rms):
        P.furnish_room(bb, rm, ay, kind=kinds[i % len(kinds)], height=BAND[1] - ay + 1, seed=50 + i, doors=doors,
                       wood="spruce", tracker=tracker)
        rooms_all.append((rm, ay, BAND[1] - ay + 1))
    # cooks' quarters: BSP bedrooms; a loft library above them
    x1, x2, hz, r, fy, top = T3
    qy = fy + 1
    qh = QUARTERS_CEIL - qy
    rms, doors = P.bsp_rooms(bb, x1 + 12, CZ - hz + 1, x2 - 5, CZ + hz - 1, qy, qh, PART, min_room=6, seed=9)
    for i, rm in enumerate(rms):
        P.furnish_room(bb, rm, qy, kind="bedroom" if i % 3 else "living", height=qh, seed=20 + i,
                       doors=doors, wood="spruce", tracker=tracker)
        rooms_all.append((rm, qy, qh))
    P.stair_run(bb, x1 + 4, qy, CZ - 5, 7, 2, "east", "minecraft:spruce_stairs")
    bb.fill(x1 + 7, QUARTERS_CEIL, CZ - 5, x1 + 10, QUARTERS_CEIL, CZ - 4, AIR)
    loft = (x1 + 12, CZ - hz + 2, x2 - 6, CZ + hz - 2)
    P.furnish_room(bb, loft, QUARTERS_CEIL + 1, kind="library", height=top - QUARTERS_CEIL, seed=33, wood="spruce",
                   tracker=tracker)
    rooms_all.append((loft, QUARTERS_CEIL + 1, top - QUARTERS_CEIL))


def outdoor_decor(bb):
    """Café tables on the balcony ends, flower pots along the kitchen wall, barrels and lamps on deck."""
    y = T1[5] + 2
    for (x, z) in ((42, CZ - 5), (42, CZ + 5), (122, CZ - 5), (122, CZ + 5), (44, CZ)):
        table(bb, x, y, z, cloth="minecraft:yellow_carpet", skip=(x + z) % 4)
    pots = ["minecraft:potted_poppy", "minecraft:potted_azure_bluet", "minecraft:potted_red_tulip", "minecraft:potted_fern"]
    for i, x in enumerate(range(58, 110, 9)):
        for side in (-1, 1):
            set_if_air(bb, x, y, CZ + side * (T2[2] + 1), pots[(i + side) % 4])
    y = DECK_Y + 1
    for (x, z) in ((36, CZ + 9), (36, CZ + 10), (37, CZ + 9), (130, CZ - 9), (130, CZ - 8)):
        set_if_air(bb, x, y, z, "minecraft:barrel[facing=up]")
    for (x, z) in ((24, CZ + 6), (24, CZ - 10), (131, CZ + 10), (131, CZ - 12)):
        if is_air(bb, x, y, z):
            bb.fill(x, y, z, x, y + 2, z, "minecraft:spruce_fence")
            bb.set(x, y + 3, z, "minecraft:lantern[hanging=false]")


def design():
    bb = BigBuild(seed=7, y_min=-14, y_max=136)
    tracker = P.PropTracker(7)
    rooms_all = []
    build_hull(bb)
    build_tail(bb)
    build_building(bb)
    build_head(bb, tracker, rooms_all)
    build_masts(bb)
    below_deck(bb, tracker, rooms_all)
    furnish(bb, tracker, rooms_all)
    outdoor_decor(bb)
    report = []
    for rm, yy, hh in rooms_all:
        txt, ok = P.audit_props(bb, [rm], yy, hh)
        if not ok:
            report.append(txt)
    return bb, report


def build():
    bb, audit = design()
    for a in audit:
        print("audit:", a)
    b = to_canvas(bb)
    # lettering (canvas font): BARATIE twice the size on the band, RESTAURANT on the top board; both faces read
    # from outside
    def word(msg, xc, y, z, side, s, scale=1):
        w = (len(msg) * 4 - 1) * scale
        if side > 0: b.text(int(xc - w // 2), y, z, msg, s, axis="x", step=1, scale=scale)
        else: b.text(int(xc + w // 2), y, z, msg, s, axis="x", step=-1, scale=scale)
    for side in (-1, 1):
        word("BARATIE", MID, BAND[0] + 1, CZ + side * (T2[2] + 1), side, RED, scale=2)
        word("RESTAURANT", MID, T3[4] + 10, CZ + side * (T3[2] + 1), side, "minecraft:brown_concrete")
        # red/white life rings on the dining-hall pilasters either side of the doors
        z = CZ + side * (T1[2] + 2)
        for xr in (69, 96):           # on the pilasters
            b.set(xr, T1[4] + 9, z, f"onepiece:life_ring[facing={'south' if side > 0 else 'north'}]")
    for (mx, mtop) in MASTS:   # BT on both faces of the red flags (flag spans x mx-14..mx-2, y mtop-8..mtop)
        b.text(mx - 11, mtop - 7, CZ + 1, "BT", "minecraft:white_concrete", axis="x", step=1)
        b.text(mx - 5, mtop - 7, CZ - 1, "BT", "minecraft:white_concrete", axis="x", step=-1)
    b.npc(90, T2[4] + 1, CZ + 5, "sanji")
    return b, 0
