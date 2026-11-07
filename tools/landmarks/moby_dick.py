"""Moby Dick: Whitebeard's giant whale-headed flagship. ~170 blocks long, 40 beam, main mast ~75 tall.
Water surface = y 0, bow (whale head) points +x."""
import math, random
from canvas import *

SID = "moby_dick"
TITLE = "Moby Dick"
WATER_Y = 0
CUTS = [12, 18]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

HULL = "minecraft:white_concrete"
HULL2 = "minecraft:light_gray_concrete"
LOW = "minecraft:gray_concrete"
WALE = "minecraft:stripped_dark_oak_log[axis=x]"
DECK = "minecraft:birch_planks"
WOOD = "minecraft:dark_oak_planks"
WHALE = "minecraft:white_concrete"
L = 150         # hull length before the whale head
BEAM = 40
CZ = 20
KEEL = -11
DECK_Y = 12
GUN_Y = 5       # lower gun deck floor


def hw(x):
    if x < 0 or x > L: return 0.0
    f = x / L
    k = 1.0
    if f > 0.72: k = math.sqrt(max(0.0, 1 - ((f - 0.72) / 0.30) ** 2))
    if f < 0.08: k = 0.82 + 0.18 * f / 0.08
    return BEAM / 2 * k


def hull_in(x, y, z):
    if y > DECK_Y or x < 0 or x > L: return False
    t = (y - KEEL) / (DECK_Y - KEEL)
    rise = 0
    f = x / L
    if f > 0.8: rise = (f - 0.8) / 0.2 * 9
    if f < 0.06: rise = (0.06 - f) / 0.06 * 5
    if y < KEEL + rise: return False
    w = hw(x) * math.sin(min(1.0, max(0.0, t)) * math.pi / 2) ** 0.45
    return abs(z - CZ) <= w


def build():
    b = B()

    def mat(x, y, z):
        if y == DECK_Y: return DECK
        if y in (DECK_Y - 1, GUN_Y + 4): return WALE
        if y < -1: return LOW
        if y < 2: return HULL2
        return HULL
    b.shape(hull_in, -1, KEEL, 0, L + 1, DECK_Y, BEAM, mat)
    # stern castle walls go straight up; deck rails
    for x in range(0, L + 1):
        w = int(hw(x))
        if w < 1: continue
        for z in range(CZ - w + 1, CZ + w):
            if hull_in(x, DECK_Y, z): b.set(x, DECK_Y, z, DECK)
        for z in (CZ - w, CZ + w):
            b.set(x, DECK_Y + 1, z, HULL); b.set(x, DECK_Y + 2, z, fence("dark_oak") if x % 4 else "minecraft:stripped_dark_oak_log[axis=y]")
    # inner decks
    for y, m in ((GUN_Y, WOOD), (-3, "minecraft:spruce_planks")):
        for x in range(2, L - 4):
            w = int(hw(x)) - 2
            for z in range(CZ - w, CZ + w + 1):
                if hull_in(x, y, z) and hull_in(x, y - 1, z): b.set(x, y, z, m)
    # gun ports with cannons along both gun decks
    for (gy, yport) in ((GUN_Y, GUN_Y + 2), (-3, -1)):
        if yport < 1: continue
        for x in range(12, L - 20, 6):
            for side in (-1, 1):
                zz = CZ + side * max(z for z in range(0, 25) if hull_in(x, yport, CZ + side * z) or z == 0)
                b.set(x, yport, zz, AIR); b.set(x, yport + 1, zz, AIR)
                b.set(x, gy + 1, zz - side, f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
    for x in range(12, L - 20, 6):  # upper row of ports just under the deck
        for side in (-1, 1):
            zz = CZ + side * int(hw(x) * math.sin((DECK_Y - 3 - KEEL) / (DECK_Y - KEEL) * math.pi / 2) ** 0.45)
            if hull_in(x, DECK_Y - 3, zz): b.set(x, DECK_Y - 3, zz, "minecraft:black_concrete")
    # lights and life inside the gun deck
    for x in range(8, L - 15, 8):
        b.set(x, DECK_Y - 1, CZ, HANG)
        for side in (-6, 6):
            bed("blue", x, GUN_Y + 1, CZ + side, b, "south" if side < 0 else "north")
        b.set(x + 3, GUN_Y + 1, CZ, BARREL); b.set(x + 3, GUN_Y + 2, CZ, "onepiece:sake_barrel[axis=x]")
    for x in range(10, L - 20, 5):
        for z in (CZ - 8, CZ + 8): b.set(x, -2, z, "onepiece:sake_barrel[axis=y]" if x % 2 else BARREL); b.set(x, -1, z, BARREL)
    # treasure hold
    b.box(L // 2 - 6, -2, CZ - 3, L // 2 + 6, -2, CZ + 3, "minecraft:gold_block")
    b.chest(L // 2, -1, CZ - 1, "legendary", "south"); b.chest(L // 2, -1, CZ + 1, "treasure", "north")
    for y in range(-2, DECK_Y): b.set(L // 2 + 8, y, CZ, ladder("west"))
    b.set(L // 2 + 8, DECK_Y, CZ, trapdoor("minecraft:dark_oak_trapdoor", "west"))
    b.box(L // 2 + 8, GUN_Y, CZ, L // 2 + 8, GUN_Y, CZ, AIR); b.set(L // 2 + 8, GUN_Y, CZ, ladder("west"))

    # ---------------- whale head figurehead
    HX, HY = L + 8, 6
    def whale_in(x, y, z):
        if x < L - 16: return False
        # boxy sperm-whale head: super-ellipse
        dx = (x - HX) / 26; dy = (y - HY) / 15; dz = (z - CZ) / 17
        return abs(dx) ** 2.6 + abs(dy) ** 2.6 + abs(dz) ** 2.6 <= 1.0 and y >= -6
    b.shape(whale_in, L - 18, -6, CZ - 18, HX + 27, HY + 16, CZ + 18, lambda x, y, z: WHALE if y > -2 else HULL2, interior=AIR)
    # smiling mouth line, eyes and a deck on the head
    mx = HX + 18
    for z in range(CZ - 16, CZ + 17):
        for x in range(L, HX + 27):
            yy = int(round(HY - 4 + 0.012 * (z - CZ) ** 2 - 0 * x))
            if whale_in(x, yy, z) and not all(whale_in(x + d[0], yy, z + d[1]) for d in ((1, 0), (0, 1), (0, -1))):
                if x > HX + 8: b.set(x, yy, z, "minecraft:black_concrete")
    for side in (-1, 1):
        ex, ey = HX + 10, HY + 4
        ez = max((z for z in range(0, 20) if whale_in(ex, ey, CZ + side * z)), default=12)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 5: b.set(ex + dx, ey + dy, CZ + side * ez, "minecraft:black_concrete")
        b.set(ex + 1, ey + 1, CZ + side * ez, "minecraft:white_concrete")
    # head-top deck and ramp from the main deck
    for x in range(L - 16, HX + 22):
        for z in range(CZ - 15, CZ + 16):
            if whale_in(x, HY + 14, z) and not whale_in(x, HY + 15, z):
                if not all(whale_in(x + d[0], HY + 14, z + d[1]) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    b.set(x, HY + 15, z, fence("birch"))
    b.stairs_up(L - 22, DECK_Y + 1, CZ - 2, 8, "minecraft:birch_stairs", "east", w=5)
    for i in range(1, 8): b.box(L - 22 + i, DECK_Y + 1, CZ - 2, L - 22 + i, DECK_Y + i, CZ + 2, DECK)
    for x in range(L - 16, L - 12):
        for z in range(CZ - 2, CZ + 3):
            for y in range(DECK_Y + 1, HY + 15): b.set(x, y, z, AIR if y > DECK_Y + 7 else b.get(x, y, z) or AIR)

    # ---------------- stern castle: 3 storeys, captain's cabin with stern windows
    S0, S1 = 2, 30
    W = int(hw(16)) - 1
    for lvl, (y0, h, inset) in enumerate(((DECK_Y, 6, 0), (DECK_Y + 7, 6, 2), (DECK_Y + 14, 5, 5))):
        x0, x1 = S0 + inset, S1 - inset * 2
        z0, z1 = CZ - W + inset, CZ + W - inset
        b.box(x0, y0, z0, x1, y0, z1, DECK)
        b.walls(x0, y0 + 1, z0, x1, y0 + h, z1, HULL)
        b.box(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y0 + h, z1 - 1, AIR)
        for x in range(x0, x1 + 1, 4):
            for z in (z0, z1):
                b.column(x, z, y0 + 1, y0 + h, "minecraft:stripped_dark_oak_log[axis=y]")
        for x in range(x0 + 2, x1 - 1, 4):
            for z in (z0, z1): b.set(x, y0 + 3, z, PANE); b.set(x, y0 + 4, z, PANE)
        for z in range(z0 + 2, z1 - 1, 2):  # stern gallery windows
            b.set(x0, y0 + 3, z, pane_of("minecraft:yellow_stained_glass_pane")); b.set(x0, y0 + 4, z, pane_of("minecraft:yellow_stained_glass_pane"))
        for x in range(x0 + 2, x1 - 1, 4):  # sills under the side windows
            b.set(x, y0 + 2, z0 - 1, stairs("minecraft:dark_oak_stairs", "south", "top")); b.set(x, y0 + 2, z1 + 1, stairs("minecraft:dark_oak_stairs", "north", "top"))
        for z in range(z0 + 4, z1 - 3, 4):  # framed bulkhead facing the main deck: posts and windows either side of the door
            if abs(z - CZ) > 1: b.column(x1, z, y0 + 1, y0 + h, "minecraft:stripped_dark_oak_log[axis=y]")
        for z in range(z0 + 2, z1 - 1, 4):
            if abs(z - CZ) <= 2: continue
            b.set(x1, y0 + 3, z, PANE); b.set(x1, y0 + 4, z, PANE)
            b.set(x1 + 1, y0 + 2, z, stairs("minecraft:dark_oak_stairs", "west", "top"))
        for z in range(z0 + 2, z1 - 1, 2):  # the stern gallery: a sill under the row of lit stern windows
            b.set(x0 - 1, y0 + 2, z, stairs("minecraft:dark_oak_stairs", "east", "top"))
        for z in range(z0, z1 + 1): b.set(x0, y0 + h, z, WALE.replace("axis=x", "axis=z")); b.set(x1, y0 + h, z, WALE.replace("axis=x", "axis=z"))
        for x in range(x0, x1 + 1): b.set(x, y0 + h, z0, WALE); b.set(x, y0 + h, z1, WALE)
        # a planked roof deck over the whole tier (the next tier stands on it), with a cornice and a rail round it
        b.box(x0, y0 + h + 1, z0, x1, y0 + h + 1, z1, DECK)
        for x in range(x0, x1 + 1):
            b.set(x, y0 + h + 1, z0 - 1, stairs("minecraft:dark_oak_stairs", "south", "top")); b.set(x, y0 + h + 1, z1 + 1, stairs("minecraft:dark_oak_stairs", "north", "top"))
            b.set(x, y0 + h + 2, z0, fence("dark_oak")); b.set(x, y0 + h + 2, z1, fence("dark_oak"))
        for z in range(z0, z1 + 1):
            b.set(x0 - 1, y0 + h + 1, z, stairs("minecraft:dark_oak_stairs", "east", "top")); b.set(x1 + 1, y0 + h + 1, z, stairs("minecraft:dark_oak_stairs", "west", "top"))
            b.set(x1, y0 + h + 2, z, fence("dark_oak")); b.set(x0, y0 + h + 2, z, fence("dark_oak"))
        for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)): b.set(x, y0 + h + 2, z, "minecraft:stripped_dark_oak_log[axis=y]")
        for z in range(CZ - 1, CZ + 2):
            for y in range(y0 + 1, y0 + 4): b.set(x1, y, z, AIR)
        b.set((x0 + x1) // 2, y0 + h - 1, CZ, HANG)
    # cabin furniture: the captain's giant bed, nurses' infirmary, map room
    for z in range(CZ - 4, CZ + 5): b.set(S0 + 3, DECK_Y + 1, z, "minecraft:white_wool"); b.set(S0 + 4, DECK_Y + 1, z, "minecraft:white_wool")
    for z in range(CZ - 4, CZ + 5): b.set(S0 + 2, DECK_Y + 2, z, "minecraft:red_wool")
    for x in range(S0 + 8, S1 - 2, 3):
        bed("pink", x, DECK_Y + 1, CZ - W + 2, b, "south"); bed("pink", x, DECK_Y + 1, CZ + W - 3, b, "south")
        b.set(x + 1, DECK_Y + 1, CZ - W + 2, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    b.set(S0 + 6, DECK_Y + 8, CZ, "onepiece:navigators_desk[facing=east]"); b.set(S0 + 6, DECK_Y + 8, CZ - 2, "minecraft:cartography_table")
    b.set(S0 + 8, DECK_Y + 15, CZ, "onepiece:ships_wheel[facing=east]")
    b.stairs_up(S1 + 1, DECK_Y + 1, CZ + W - 3, 7, "minecraft:dark_oak_stairs", "west", w=2)
    b.stairs_up(S1 - 4 + 1 - 4 + 2, DECK_Y + 8, CZ - W + 4, 7, "minecraft:dark_oak_stairs", "west", w=2)
    # stern lanterns
    for z in (CZ - W, CZ + W): b.column(S0, z, DECK_Y + 9, DECK_Y + 13, fence("dark_oak")); b.set(S0, DECK_Y + 14, z, LANTERN)
    for x in range(S0 + 9, S1 - 9, 4):  # lanterns on posts round the top deck
        for z in (CZ - W + 5, CZ + W - 5): b.set(x, DECK_Y + 22, z, LANTERN)

    # ---------------- Whitebeard's chair on the main deck (he is 6.66 m tall)
    CX0 = 40
    b.box(CX0, DECK_Y + 1, CZ - 4, CX0 + 4, DECK_Y + 2, CZ + 4, "minecraft:red_terracotta")
    b.box(CX0, DECK_Y + 3, CZ - 4, CX0, DECK_Y + 9, CZ + 4, "minecraft:red_terracotta")
    for z in (CZ - 4, CZ + 4): b.box(CX0 + 1, DECK_Y + 3, z, CX0 + 4, DECK_Y + 4, z, "minecraft:gold_block")
    b.box(CX0 + 1, DECK_Y + 3, CZ - 3, CX0 + 4, DECK_Y + 3, CZ + 3, "minecraft:red_wool")
    for y in range(DECK_Y + 1, DECK_Y + 13): b.set(CX0 + 6, y, CZ + 6, "minecraft:stripped_dark_oak_log[axis=y]")  # bisento shaft
    b.set(CX0 + 6, DECK_Y + 13, CZ + 6, "minecraft:gold_block")  # the collar
    for (dx, dy) in ((0, 14), (1, 14), (0, 15), (1, 15), (2, 15), (1, 16), (2, 16), (2, 17), (3, 17), (3, 18)):
        b.set(CX0 + 6 + dx, DECK_Y + dy, CZ + 6, "minecraft:iron_block")  # broad blade curving forward
    for (x, z) in ((CX0 + 8, CZ - 7), (CX0 + 8, CZ + 7)): b.column(x, z, DECK_Y + 1, DECK_Y + 4, fence("dark_oak")); b.set(x, DECK_Y + 5, z, LANTERN)
    for x in range(CX0 + 9, CX0 + 30, 5):  # party tables with sake
        b.table_set(x, DECK_Y + 1, CZ - 9, "dark_oak"); b.table_set(x, DECK_Y + 1, CZ + 9, "dark_oak")
        b.set(x, DECK_Y + 1, CZ, "onepiece:sake_barrel[axis=y]")

    # ---------------- masts: 4 masts with 3 square sails each, the main sail carries the mark
    MASTS = ((52, 66, 3), (88, 76, 3), (118, 66, 3), (140, 50, 2))
    for i, (mx, mh, ns) in enumerate(MASTS):
        top = DECK_Y + mh
        b.cyl(mx, CZ, 1, GUN_Y, top, "minecraft:spruce_log[axis=y]")
        for y in range(top + 1, top + 6): b.set(mx, y, CZ, log("spruce"))
        nest = top - 6
        b.disk(mx, nest, CZ, 3, "minecraft:spruce_planks")
        for a in range(0, 360, 30):
            r = math.radians(a); b.set(round(mx + 3 * math.cos(r)), nest + 1, round(CZ + 3 * math.sin(r)), fence("spruce"))
        span = (mh - 12) // ns
        half0 = 17 if i in (0, 1) else 14 if i == 2 else 11
        for s in range(ns):
            y0 = DECK_Y + 8 + s * span; y1 = y0 + span - 2
            half = max(5, half0 - s * 3)
            pat = whitebeard_mark() if s == 0 and i in (0, 1, 2) else None
            b.square_sail(mx + 2, CZ, y0, y1, half, "minecraft:white_wool", belly=3, pattern=pat)
            for z in range(CZ - half - 2, CZ + half + 3): b.set(mx + 1, y1 + 1, z, log("spruce", "z"))
        for side in (-1, 1):  # shrouds
            for k in range(0, 3):
                b.line((mx - 2 + k * 2, nest, CZ), (mx - 4 + k * 4, DECK_Y + 2, CZ + side * int(hw(mx))), fence("spruce"))
        # flag on the main mast
        if i == 1:
            b.jolly_roger(mx, top + 5, CZ + 1, 15, 10, style="whitebeard")
    # bowsprit
    b.line((HX + 18, HY + 13, CZ), (HX + 36, HY + 22, CZ), log("spruce", "x"))
    for i in range(6): b.line((HX + 20 + i * 3, HY + 14 + i * 1.5, CZ), (88, DECK_Y + 70 - i * 6, CZ), fence("spruce")) if i % 2 == 0 else None

    # ---------------- paddle wheels on both sides amidships
    PX, PY = 74, 2
    for side in (-1, 1):
        zw = CZ + side * (int(hw(PX)) + 2)
        for a in range(0, 360, 4):
            r = math.radians(a)
            for rr in (10, 9):
                b.set(round(PX + rr * math.cos(r)), round(PY + rr * math.sin(r)), zw, "minecraft:red_terracotta" if rr == 10 else WOOD)
        for a in range(0, 360, 30):  # spokes and paddles
            r = math.radians(a)
            b.line((PX, PY, zw), (PX + 9 * math.cos(r), PY + 9 * math.sin(r), zw), "minecraft:stripped_dark_oak_log[axis=y]")
            for k in (0, 1):
                b.set(round(PX + 9 * math.cos(r)), round(PY + 9 * math.sin(r)), zw + side * k, WOOD)
        for zz in range(CZ + side * (int(hw(PX)) - 1), zw + side, side): b.set(PX, PY, zz, "minecraft:iron_block")
        # paddle box housing
        for a in range(0, 181, 3):
            r = math.radians(a)
            for zz in (zw - side, zw, zw + side * 2):
                b.set(round(PX + 12 * math.cos(r)), round(PY + 12 * math.sin(r)), zz, HULL)
        for x in range(PX - 12, PX + 13):
            y = PY + int(round(math.sqrt(max(0, 144 - (x - PX) ** 2))))
            for zz in range(zw - side, zw + side * 3, side): b.set(x, y, zz, HULL)
    # lifeboats hanging on the quarters
    for x0 in (100, 124):
        for side in (-1, 1):
            zz = CZ + side * (int(hw(x0 + 4)) + 2)
            for x in range(x0, x0 + 9):
                k = 1 if 1 <= x - x0 <= 7 else 0
                for dz in range(-k, k + 1): b.set(x, DECK_Y - 1, zz + dz, "minecraft:spruce_planks")
            for x in (x0, x0 + 8): b.column(x, zz - side, DECK_Y, DECK_Y + 3, fence("dark_oak"))
    # deck dressing
    for x in range(56, 140, 9):
        for side in (-1, 1):
            z = CZ + side * (int(hw(x)) - 2)
            b.set(x, DECK_Y + 1, z, "onepiece:rope_coil[facing=north]" if x % 2 else BARREL)
    for x in (66, 104):
        for side in (-1, 1): b.set(x, DECK_Y + 1, CZ + side * (int(hw(x)) - 1), f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
    b.set(130, DECK_Y + 1, CZ - 6, "onepiece:anchor[facing=east]"); b.set(130, DECK_Y + 1, CZ + 6, "onepiece:anchor[facing=east]")
    # ---------------- people
    b.npc(CX0 + 2, DECK_Y + 4, CZ, "whitebeard", True)  # seated on the cushion of his chair
    b.npc(88, DECK_Y + 1, CZ + 4, "marco")
    b.guards("whitebeard_pirate", ((60, CZ - 6), (70, CZ + 6), (100, CZ), (120, CZ - 8), (124, CZ + 8), (35, CZ - 10), (35, CZ + 10)), y=DECK_Y + 1)
    # ---------------- furnished rooms
    import interiors as I
    # gun deck: cabins down the middle, cannon corridors along both sides
    secs = ((12, 40, "kitchen"), (41, 68, "dining"), (69, 96, "barracks"), (97, 126, "armory"))
    for (x0, x1, kind) in secs:
        for x in range(x0, x1 + 1):
            for z in range(CZ - 12, CZ + 13):
                edge = x in (x0, x1) or z in (CZ - 12, CZ + 12)
                if edge and hull_in(x, GUN_Y + 1, z):
                    for y in range(GUN_Y + 1, DECK_Y):
                        if b.get(x, y, z) in (None, AIR) or "bed" in (b.get(x, y, z) or "") or "barrel" in (b.get(x, y, z) or ""): b.set(x, y, z, WOOD)
        for y in (GUN_Y + 1, GUN_Y + 2):
            for z in (CZ - 1, CZ, CZ + 1):
                b.set(x0, y, z, AIR); b.set(x1, y, z, AIR)
            for x in ((x0 + x1) // 2, (x0 + x1) // 2 + 1):
                b.set(x, y, CZ - 12, AIR); b.set(x, y, CZ + 12, AIR)
        b.set((x0 + x1) // 2, GUN_Y + 3, CZ - 12, "minecraft:lantern"); b.set((x0 + x1) // 2, GUN_Y + 3, CZ + 12, "minecraft:lantern")
        I.furnish(b, x0 + 1, GUN_Y + 1, CZ - 11, x1 - 1, CZ + 11, DECK_Y - GUN_Y - 1, kind, "pirate")
    # hold: stores around the treasure
    I.furnish(b, 10, -2, CZ - 9, L // 2 - 9, CZ + 9, 6, "storage", "pirate")
    I.furnish(b, L // 2 + 10, -2, CZ - 9, L - 30, CZ + 9, 6, "storage", "pirate")
    I.furnish(b, L // 2 - 8, -2, CZ - 6, L // 2 + 7, CZ + 6, 6, "treasure", "royal")
    # stern castle: Whitebeard's cabin and the infirmary, the map room, the helm room
    for lvl, (y0, h, inset, kind) in enumerate(((DECK_Y, 6, 0, "bedroom"), (DECK_Y + 7, 6, 2, "study"), (DECK_Y + 14, 5, 5, "captain"))):
        I.furnish(b, S0 + inset + 1, y0 + 1, CZ - W + inset + 1, S1 - inset * 2 - 1, CZ + W - inset - 1, h, kind, "royal")
    return b, 0
