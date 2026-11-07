"""Moby Dick, Whitebeard's whale-headed flagship, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/moby_dick.md).

A long white hull with two gun decks, a hold and a stern castle, the great white sperm-whale head for a bow (smiling
mouth, eyes, a lounge inside and a lookout deck on top), red paddle wheels amidships, four masts with square sails
carrying Whitebeard's mark and his Jolly Roger at the main top. On deck: Whitebeard's giant chair and bisento, party
tables and sake barrels. Inside: the hold with the treasure room and stores, the lower gun deck with the sixteen
division quarters between the cannon rows, the upper gun deck with the mess hall, galley, infirmary (the nurses)
and armory, and the stern castle with Whitebeard's cabin, the chart room and the helm. ~222 x 70, main mast ~100.
Water surface = y 0, the whale head points +x. (v2)"""
import math
import numpy as np
from mcb.kit import BigBuild, P, AIR, seed_of, st, wing_floor, furnish, table, set_if_air
from mcb.bridge import to_canvas
from canvas import whitebeard_mark

SID = "moby_dick"
TITLE = "Moby Dick"
WATER_Y = 0
CUTS = [3, 9, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

HULL = "minecraft:white_concrete"
HULL2 = "minecraft:light_gray_concrete"
LOW = "minecraft:gray_concrete"
WALE = "minecraft:stripped_dark_oak_log[axis=x]"
DECKB = "minecraft:birch_planks"
WOOD = "minecraft:dark_oak_planks"
TRIM = "minecraft:stripped_dark_oak_log[axis=y]"
PANE = "minecraft:glass_pane"
LANT = "minecraft:lantern[hanging=true]"

L0, L1 = 4, 186          # hull stern / where the whale head takes over
CZ, NZ = 35, 71
HALF = 28
KEEL, HOLD, GUN1, GUN2, DECK = -14, -10, -2, 5, 13
HX, HY = 194, 8          # whale head centre
RX, RY, RZ = 26, 21, 25
STERN = (6, 44)          # stern castle x range


def hw(X):
    t = (np.asarray(X, dtype=float) - L0) / (L1 - L0)
    w = np.where(t < 0.07, HALF * (0.8 + 0.2 * t / 0.07), HALF)
    return np.where((t < 0) | (t > 1.05), -1, w)


def width_at(X, y):
    k = np.sin(np.clip((y - KEEL) / (DECK - KEEL), 0, 1) * math.pi / 2) ** 0.5
    return hw(X) * (0.35 + 0.65 * k)


def head(X, y, Z, shrink=0):
    dx = np.abs(X - HX) / (RX - shrink)
    dy = abs(y - HY) / (RY - shrink)
    dz = np.abs(Z - CZ) / (RZ - shrink)
    return (dx ** 2.6 + dy ** 2.6 + dz ** 2.6 <= 1.0) & (y >= -8 + shrink)


# ---------------------------------------------------------------- hull and decks
def hull(bb):
    for y in range(KEEL, DECK + 1):
        inside = lambda X, yy, Z, y=y: (np.abs(Z - CZ) <= width_at(X, y)) & ~head(X, y, Z, 0.0)
        shell = lambda X, yy, Z, y=y: inside(X, yy, Z) & ((np.abs(Z - CZ) > width_at(X, y) - 2) | (X <= L0 + 1))
        mat = WALE if y in (DECK - 1, GUN2 + 3) else LOW if y < -2 else HULL2 if y < 2 else HULL
        if y <= HOLD:
            bb.fill_where(L0 - 1, y, 0, L1 + 6, y, NZ - 1, inside, LOW)
        else:
            bb.fill_where(L0 - 1, y, 0, L1 + 6, y, NZ - 1, shell, mat)
    for (y, m) in ((HOLD, "minecraft:spruce_planks"), (GUN1, WOOD), (GUN2, WOOD), (DECK, DECKB)):
        bb.fill_where(L0, y, 0, L1 + 6, y, NZ - 1,
                      lambda X, yy, Z, y=y: (np.abs(Z - CZ) <= width_at(X, y) - 1) & ~head(X, y, Z, 0.0), m)
    # gun ports on both gun decks, cannons inside, a black strake of upper ports under the rail
    for (gy, py) in ((GUN1, 1), (GUN2, 8)):
        for x in range(L0 + 14, L1 - 6, 6):
            w = float(width_at(x, py))
            for s in (-1, 1):
                z = int(round(CZ + s * w))
                bb.fill(x, py, z - s, x, py + 1, z, AIR)
                bb.set(x, gy + 1, z - 2 * s, f"onepiece:cannon[facing={'south' if s > 0 else 'north'}]")
    # deck rail
    for x in range(L0, L1 + 1):
        w = int(float(hw(x)))
        for z in (CZ - w, CZ + w):
            bb.set(x, DECK + 1, z, HULL)
            bb.set(x, DECK + 2, z, "minecraft:dark_oak_fence" if x % 4 else TRIM)
    # hatches with ladders from the deck all the way down
    for hx in (60, 120):
        bb.fill(hx, HOLD + 1, CZ, hx, DECK, CZ, "minecraft:ladder[facing=west]")
        for y in (GUN1, GUN2, DECK):
            bb.set(hx, y, CZ, "minecraft:ladder[facing=west]")


def interiors(bb, tracker, audit):
    """Hold: stores round the treasure room. Lower gun deck: the division quarters between the cannon rows. Upper gun
    deck: mess hall, galley, infirmary, armory."""
    x1, x2 = STERN[1] + 2, L1 - 18
    inner = HALF - 6
    # hold
    wing_floor(bb, x1, CZ - inner + 4, x2, CZ + inner - 4, HOLD + 1, 6, WOOD, seed_of("mdhold"), tracker,
               ["storage", "storage", "workshop"], corridor="x", cw=3, audit=audit, max_room=13, wood="dark_oak",
               keep=[(58, CZ - 1, 62, CZ + 1), (118, CZ - 1, 122, CZ + 1)])
    tx = 90
    bb.fill(tx - 6, HOLD + 1, CZ - 7, tx + 6, HOLD + 6, CZ + 7, AIR)
    bb.fill(tx - 7, HOLD + 1, CZ - 8, tx + 7, HOLD + 6, CZ - 8, WOOD)
    bb.fill(tx - 7, HOLD + 1, CZ + 8, tx + 7, HOLD + 6, CZ + 8, WOOD)
    bb.fill(tx - 4, HOLD, CZ - 4, tx + 4, HOLD, CZ + 4, "minecraft:gold_block")
    bb.fill(tx - 1, HOLD + 1, CZ - 8, tx + 1, HOLD + 2, CZ - 8, AIR)
    for (dx, dz) in ((-5, -6), (5, -6), (-5, 6), (5, 6)):
        bb.set(tx + dx, HOLD + 1, CZ + dz, "minecraft:barrel[facing=up]")
        bb.set(tx + dx, HOLD + 2, CZ + dz, "minecraft:lantern[hanging=false]")
    # lower gun deck: quarters in the middle band, the cannon rows clear along both sides
    wing_floor(bb, x1, CZ - inner + 3, x2, CZ + inner - 3, GUN1 + 1, 6, WOOD, seed_of("mdq"), tracker,
               ["bedroom", "bedroom", "living", "bedroom"], corridor="x", cw=3, audit=audit, max_room=11,
               wood="dark_oak", carpet=(None, "minecraft:blue_carpet"),
               keep=[(58, CZ - 1, 62, CZ + 1), (118, CZ - 1, 122, CZ + 1)])
    for x in range(x1, x2 + 1, 6):
        for s in (-1, 1):
            bb.set(x, GUN1 + 6, CZ + s * (inner - 1), LANT)
    # upper gun deck: the mess hall (open, long tables), galley, infirmary, armory
    mx1, mx2 = 64, 116
    bb.fill(mx1, GUN2 + 1, CZ - inner + 3, mx2, GUN2 + 6, CZ + inner - 3, AIR)
    for x in range(mx1 + 3, mx2 - 2, 9):
        for zc in (CZ - 8, CZ + 8):
            for xx in range(x, x + 6):
                table(bb, xx, GUN2 + 1, zc, wood="dark_oak")
            for xx in range(x, x + 6):
                bb.set(xx, GUN2 + 1, zc - 1, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
                bb.set(xx, GUN2 + 1, zc + 1, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
        bb.set(x + 2, GUN2 + 6, CZ, "onepiece:chandelier[facing=north]")
    for z in range(CZ - 3, CZ + 4, 3):
        bb.set(mx1 + 1, GUN2 + 1, z, "onepiece:sake_barrel[axis=y]")
        bb.set(mx1 + 1, GUN2 + 2, z, "onepiece:sake_barrel[axis=y]")
    bb.fill(mx1, GUN2 + 1, CZ - 1, mx1, GUN2 + 3, CZ + 1, AIR)
    bb.fill(mx2, GUN2 + 1, CZ - 1, mx2, GUN2 + 3, CZ + 1, AIR)
    for (a, b, kinds, nm) in ((x1, mx1 - 2, ["kitchen", "storage"], "galley"), (mx2 + 2, x2, ["bedroom", "library", "workshop"], "inf")):
        wing_floor(bb, a, CZ - inner + 3, b, CZ + inner - 3, GUN2 + 1, 6, WOOD, seed_of("md", nm), tracker, kinds,
                   corridor="x", cw=3, audit=audit, max_room=11, wood="dark_oak",
                   keep=[(58, CZ - 1, 62, CZ + 1), (118, CZ - 1, 122, CZ + 1)])


def whale_head(bb, tracker, audit):
    shell = lambda X, y, Z: head(X, y, Z) & ~head(X, y, Z, 2.0)
    for y in range(-8, HY + RY + 1):
        bb.fill_where(L1 - 20, y, 0, HX + RX, y, NZ - 1, lambda X, yy, Z, y=y: head(X, y, Z, 2.0) & (X > L1 - 14),
                      AIR)
        bb.fill_where(L1 - 20, y, 0, HX + RX, y, NZ - 1, lambda X, yy, Z, y=y: shell(X, y, Z),
                      HULL if y > -1 else HULL2)
    # the smiling mouth: a black line across the front, curving up at the corners
    for z in range(CZ - RZ, CZ + RZ + 1):
        y0 = int(round(HY - 6 + 0.014 * (z - CZ) ** 2))
        for yy in (y0, y0 + 1):
            for x in range(HX + RX, HX, -1):
                if bool(head(np.array([x]), yy, np.array([z]))[0]):
                    if x > HX + 6:
                        bb.set(x, yy, z, "minecraft:black_concrete")
                        bb.set(x - 1, yy, z, "minecraft:black_concrete")
                    break
    # eyes on both sides
    for s in (-1, 1):
        ex, ey = HX + 9, HY + 6
        ez = next(z for z in range(RZ, 0, -1) if bool(head(np.array([ex]), ey, np.array([CZ + s * z]))[0]))
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 5:
                    bb.set(ex + dx, ey + dy, CZ + s * ez, "minecraft:black_concrete")
        bb.set(ex + 1, ey + 1, CZ + s * ez, "minecraft:white_concrete")
    # inside: the whale-head lounge on the deck level, a lookout deck on the crown
    bb.fill_where(L1 - 14, DECK, 0, HX + RX, DECK, NZ - 1, lambda X, y, Z: head(X, DECK, Z, 2.0), DECKB)
    for fy in (GUN1, GUN2):                      # two store decks inside the head, reached by the spiral stair
        bb.fill_where(L1 - 14, fy, 0, HX + RX, fy, NZ - 1, lambda X, y, Z, fy=fy: head(X, fy, Z, 2.0), WOOD)
        for x in range(L1 - 6, HX + 16, 4):
            for z in (CZ - 10, CZ + 10):
                set_if_air(bb, x, fy + 1, z, "minecraft:barrel[facing=up]")
                set_if_air(bb, x, fy + 2, z, "onepiece:sake_barrel[axis=y]" if x % 8 else "minecraft:barrel[facing=up]")
        bb.set(HX, fy + 6, CZ, LANT)
    P.square_spiral_stair(bb, L1 + 14, GUN1 + 1, CZ - 2, 5, DECK, "minecraft:birch_stairs", core=WOOD)
    rooms = [(L1 - 8, CZ - 12, L1 + 10, CZ - 2), (L1 - 8, CZ + 2, L1 + 10, CZ + 12)]
    for r in rooms:
        bb.fill(r[0] - 1, DECK + 1, r[1] - 1, r[2] + 1, DECK + 6, r[3] + 1, WOOD)
        bb.fill(r[0], DECK + 1, r[1], r[2], DECK + 6, r[3], AIR)
        bb.fill((r[0] + r[2]) // 2, DECK + 1, CZ - 2 if r[1] < CZ else CZ + 2, (r[0] + r[2]) // 2 + 1, DECK + 2,
                CZ - 2 if r[1] < CZ else CZ + 2, AIR)
    furnish(bb, rooms, DECK + 1, 6, ["living", "kitchen"], seed_of("mdhead"), tracker, wood="birch", audit=audit)
    top = HY + RY - 2
    bb.fill_where(L1 - 6, top, 0, HX + RX, top, NZ - 1, lambda X, y, Z: head(X, top, Z, 1.0), DECKB)
    bb.fill_where(L1 - 6, top + 1, 0, HX + RX, top + 1, NZ - 1,
                  lambda X, y, Z: head(X, top, Z, 1.0) & ~head(X, top, Z, 2.5), "minecraft:birch_fence")
    P.square_spiral_stair(bb, L1 + 14, DECK + 1, CZ - 2, 5, top, "minecraft:birch_stairs", core=WOOD)
    # door from the main deck into the head
    bb.fill(L1 - 16, DECK + 1, CZ - 2, L1 - 9, DECK + 5, CZ + 2, AIR)
    for z in (CZ - 6, CZ + 6):
        bb.set(L1 + 6, top + 1, z, "minecraft:lantern[hanging=false]")
    # the bowsprit out of the forehead
    for i in range(8):
        bb.set(HX + RX - 4 + i, top - 2 + i // 2, CZ, "minecraft:spruce_log[axis=x]")


def stern_castle(bb, tracker, audit):
    x0, x1 = STERN
    w = HALF - 1
    tiers = ((DECK, 7, 0, ["bedroom", "library"]), (DECK + 8, 7, 3, ["library", "living"]), (DECK + 16, 6, 7, ["living"]))
    for (y0, h, inset, kinds) in tiers:
        a, b_ = x0 + inset, x1 - inset * 2
        z0, z1 = CZ - w + inset, CZ + w - inset
        bb.fill(a, y0 + 1, z0, b_, y0 + h, z1, HULL)
        bb.fill(a + 1, y0 + 1, z0 + 1, b_ - 1, y0 + h, z1 - 1, AIR)
        for x in range(a, b_ + 1, 4):
            bb.fill(x, y0 + 1, z0, x, y0 + h, z0, TRIM)
            bb.fill(x, y0 + 1, z1, x, y0 + h, z1, TRIM)
        for x in range(a + 2, b_ - 1, 4):
            for z in (z0, z1):
                bb.fill(x, y0 + 3, z, x, y0 + 4, z, PANE)
            bb.set(x, y0 + 2, z0 - 1, st("minecraft:dark_oak_stairs", "south", "top"))
            bb.set(x, y0 + 2, z1 + 1, st("minecraft:dark_oak_stairs", "north", "top"))
        for z in range(z0 + 2, z1 - 1, 2):                        # lit stern gallery
            bb.fill(a, y0 + 3, z, a, y0 + 5, z, "minecraft:yellow_stained_glass")
            bb.set(a - 1, y0 + 2, z, st("minecraft:dark_oak_stairs", "east", "top"))
        for z in range(z0 + 2, z1 - 1, 4):
            if abs(z - CZ) > 3:
                bb.fill(b_, y0 + 3, z, b_, y0 + 4, z, PANE)
        bb.fill(a, y0 + h, z0, b_, y0 + h, z1, WALE)
        bb.fill(a, y0 + h + 1, z0, b_, y0 + h + 1, z1, DECKB)
        for x in range(a, b_ + 1):
            for z in (z0, z1):
                bb.set(x, y0 + h + 2, z, "minecraft:dark_oak_fence")
        for z in range(z0, z1 + 1):
            bb.set(a, y0 + h + 2, z, "minecraft:dark_oak_fence")
            bb.set(b_, y0 + h + 2, z, "minecraft:dark_oak_fence")
        bb.fill(b_, y0 + 1, CZ - 1, b_, y0 + 3, CZ + 1, AIR)
        rs, ds = P.bsp_rooms(bb, a + 1, z0 + 1, b_ - 1, z1 - 1, y0 + 1, h - 1, WOOD, min_room=6,
                             seed=seed_of("stern", y0), max_room=14)
        furnish(bb, rs, y0 + 1, h - 1, kinds, seed_of("sternf", y0), tracker, doors=ds, wood="dark_oak", audit=audit)
        bb.fill(b_ - 1, y0 + 1, CZ - 1, b_ - 1, y0 + 3, CZ + 1, AIR)
        bb.set((a + b_) // 2, y0 + h - 1, CZ, LANT)
    # stairs up the front of each tier (port side)
    for (y0, h, inset, _) in tiers[:-1]:
        b_ = x1 - inset * 2
        n = h + 1
        for i in range(n):
            bb.set(b_ + 1 + n - i, y0 + 1 + i, CZ + 8, st("minecraft:dark_oak_stairs", "west"))
            bb.set(b_ + 1 + n - i, y0 + 1 + i, CZ + 9, st("minecraft:dark_oak_stairs", "west"))
    # Whitebeard's giant bed in his cabin, the helm on the top tier
    bb.fill(x0 + 2, DECK + 1, CZ - 4, x0 + 5, DECK + 1, CZ + 4, "minecraft:white_wool")
    bb.fill(x0 + 1, DECK + 1, CZ - 4, x0 + 1, DECK + 3, CZ + 4, "minecraft:red_wool")
    bb.set(x0 + 14, DECK + 24, CZ, "onepiece:ships_wheel[facing=east]")
    for z in (CZ - w, CZ + w):
        bb.fill(x0, DECK + 9, z, x0, DECK + 13, z, "minecraft:dark_oak_fence")
        bb.set(x0, DECK + 14, z, "minecraft:lantern[hanging=false]")


def main_deck(bb):
    # Whitebeard's chair (he is 6.66 m tall) with his bisento beside it
    c = 52
    bb.fill(c, DECK + 1, CZ - 5, c + 6, DECK + 2, CZ + 5, "minecraft:red_terracotta")
    bb.fill(c, DECK + 3, CZ - 5, c + 1, DECK + 12, CZ + 5, "minecraft:red_terracotta")
    for z in (CZ - 5, CZ + 5):
        bb.fill(c + 2, DECK + 3, z, c + 6, DECK + 5, z, "minecraft:gold_block")
    bb.fill(c + 2, DECK + 3, CZ - 4, c + 6, DECK + 3, CZ + 4, "minecraft:red_wool")
    bb.fill(c, DECK + 13, CZ - 3, c, DECK + 13, CZ + 3, "minecraft:gold_block")
    bx, bz = c + 8, CZ + 8
    bb.fill(bx, DECK + 1, bz, bx, DECK + 15, bz, TRIM)
    bb.set(bx, DECK + 16, bz, "minecraft:gold_block")
    for (dx, dy) in ((0, 17), (1, 17), (0, 18), (1, 18), (2, 18), (1, 19), (2, 19), (2, 20), (3, 20), (3, 21), (4, 21)):
        bb.set(bx + dx, DECK + dy, bz, "minecraft:iron_block")
    # party tables with sake down the deck
    for x in range(c + 12, c + 52, 6):
        for z in (CZ - 11, CZ + 11):
            for dz in (-1, 0, 1):
                table(bb, x, DECK + 1, z + dz, wood="dark_oak")
            bb.set(x - 1, DECK + 1, z, "minecraft:dark_oak_stairs[facing=east,half=bottom]")
            bb.set(x + 1, DECK + 1, z, "minecraft:dark_oak_stairs[facing=west,half=bottom]")
        bb.set(x, DECK + 1, CZ + 4, "onepiece:sake_barrel[axis=y]")
    for x in range(48, L1 - 20, 9):
        for s in (-1, 1):
            z = CZ + s * (int(float(hw(x))) - 2)
            set_if_air(bb, x, DECK + 1, z, "onepiece:rope_coil[facing=north]" if x % 2 else "minecraft:barrel[facing=up]")
    for x in (76, 134):
        for s in (-1, 1):
            bb.set(x, DECK + 1, CZ + s * (HALF - 2), f"onepiece:cannon[facing={'south' if s > 0 else 'north'}]")
    bb.set(160, DECK + 1, CZ - 8, "onepiece:anchor[facing=east]")
    bb.set(160, DECK + 1, CZ + 8, "onepiece:anchor[facing=east]")
    for (x, z) in ((c + 10, CZ - 9), (c + 10, CZ + 9)):
        bb.fill(x, DECK + 1, z, x, DECK + 4, z, "minecraft:dark_oak_fence")
        bb.set(x, DECK + 5, z, "minecraft:lantern[hanging=false]")


MASTS = ((66, 78, 3, 21), (104, 92, 3, 23), (140, 78, 3, 20), (168, 58, 2, 15))


def masts(bb):
    for (mx, mh, ns, half) in MASTS:
        top = DECK + mh
        bb.cylinder(mx, GUN1, CZ, 1, top, "minecraft:spruce_log[axis=y]")
        nest = top - 7
        bb.cylinder(mx, nest, CZ, 3, nest, "minecraft:spruce_planks")
        for a in range(0, 360, 30):
            t = math.radians(a)
            bb.set(round(mx + 3 * math.cos(t)), nest + 1, round(CZ + 3 * math.sin(t)), "minecraft:spruce_fence")
        for s in (-1, 1):                                  # shrouds down to the rails
            for k in range(3):
                x0, y0, z0 = mx - 2 + 2 * k, nest, CZ
                x1_, y1, z1 = mx - 4 + 4 * k, DECK + 2, CZ + s * (HALF - 1)
                n = max(abs(y1 - y0), abs(z1 - z0))
                for i in range(n + 1):
                    f = i / n
                    set_if_air(bb, round(x0 + (x1_ - x0) * f), round(y0 + (y1 - y0) * f), round(z0 + (z1 - z0) * f),
                               "minecraft:spruce_fence")


def paddles(bb):
    px, py = 96, 3
    for s in (-1, 1):
        zw = CZ + s * (HALF + 2)
        for z in (zw, zw + s):
            for a in range(0, 360, 3):
                t = math.radians(a)
                for rr, m in ((12, "minecraft:red_terracotta"), (11, WOOD)):
                    bb.set(round(px + rr * math.cos(t)), round(py + rr * math.sin(t)), z, m)
        for a in range(0, 360, 30):
            t = math.radians(a)
            for r in range(1, 11):
                bb.set(round(px + r * math.cos(t)), round(py + r * math.sin(t)), zw, "minecraft:stripped_dark_oak_log[axis=z]")
            for k in (0, 1, 2):
                bb.set(round(px + 10 * math.cos(t)), round(py + 10 * math.sin(t)), zw + s * k, WOOD)
        bb.fill(px, py, min(CZ + s * (HALF - 1), zw), px, py, max(CZ + s * (HALF - 1), zw), "minecraft:iron_block")
        for a in range(0, 181, 2):                           # the paddle box
            t = math.radians(a)
            for z in range(min(zw - s, zw + 3 * s), max(zw - s, zw + 3 * s) + 1):
                bb.set(round(px + 14 * math.cos(t)), round(py + 14 * math.sin(t)), z, HULL)
        bb.fill(px - 3, DECK - 2, min(zw + 4 * s, zw - s), px + 3, DECK - 2, max(zw + 4 * s, zw - s), "minecraft:red_terracotta")
    # lifeboats hung on the quarters
    for x0 in (128, 150):
        for s in (-1, 1):
            zz = CZ + s * (HALF + 2)
            for x in range(x0, x0 + 9):
                k = 1 if 1 <= x - x0 <= 7 else 0
                bb.fill(x, DECK - 1, zz - k, x, DECK - 1, zz + k, "minecraft:spruce_planks")
            for x in (x0, x0 + 8):
                bb.fill(x, DECK, zz - s, x, DECK + 3, zz - s, "minecraft:dark_oak_fence")


def design():
    bb = BigBuild(seed=1616, y_min=-16, y_max=DECK + 110)
    tracker = P.PropTracker(1616)
    audit = []
    hull(bb)
    interiors(bb, tracker, audit)
    whale_head(bb, tracker, audit)
    stern_castle(bb, tracker, audit)
    main_deck(bb)
    masts(bb)
    paddles(bb)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    # square sails (bellied, painted with Whitebeard's mark on the lower courses) and the Jolly Roger
    for i, (mx, mh, ns, half0) in enumerate(MASTS):
        span = (mh - 16) // ns
        for s in range(ns):
            y0 = DECK + 10 + s * span
            y1 = y0 + span - 3
            half = max(6, half0 - s * 4)
            pat = whitebeard_mark() if s == 0 and i < 3 else None
            b.square_sail(mx + 2, CZ, y0, y1, half, "minecraft:white_wool", belly=3, pattern=pat)
            for z in range(CZ - half - 2, CZ + half + 3):
                b.set(mx + 1, y1 + 1, z, "minecraft:spruce_log[axis=z]")
        if i == 1:
            top = DECK + mh
            for y in range(top + 1, top + 6):
                b.set(mx, y, CZ, "minecraft:spruce_log[axis=y]")
            b.jolly_roger(mx, top + 5, CZ + 1, 17, 11, style="whitebeard")
    b.chest(90, HOLD + 1, CZ - 2, "legendary", "south")
    b.chest(90, HOLD + 1, CZ + 2, "treasure", "north")
    b.npc(54, DECK + 4, CZ, "whitebeard", True)
    b.npc(104, DECK + 1, CZ + 4, "marco")
    b.guards("whitebeard_pirate", ((76, CZ - 6), (86, CZ + 6), (120, CZ), (140, CZ - 8), (146, CZ + 8), (47, CZ - 12),
                                   (47, CZ + 12)), y=DECK + 1)
    b.guards("whitebeard_pirate", ((90, CZ - 12), (100, CZ + 12)), y=GUN2 + 1)
    return b, 0
