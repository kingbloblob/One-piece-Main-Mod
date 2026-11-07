"""A Marine battleship at sea, life size (~84 m): a white hull with a blue wale and gun decks of cannons, the
seagull figurehead on the bow, three masts with white square sails painted with the blue MARINE gull and the
word MARINE, the bridge and the captain's cabin in the stern castle, the officers' mess, a gun deck with
powder room, crew hammock decks, the brig with sea-stone bars and the hold of supplies. Water surface = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "marine_battleship"
TITLE = "Marine Battleship"
WATER_Y = 0
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

HX, HL = 2, 84
CZ = 13
DECK = 10
KEEL = -6
WHITE = "minecraft:white_concrete"
BLUE = "minecraft:blue_concrete"
MAR = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="onepiece:marine_bricks",
           banner="light_blue", candle="white")


def gull(u, v):
    """The Marine gull mark on a sail (u, v in -1..1)."""
    if abs(v + 0.55 * abs(u) - 0.25) < 0.16 and abs(u) < 0.85: return "minecraft:blue_wool"
    if u * u + (v - 0.05) ** 2 < 0.03: return "minecraft:blue_wool"
    return None


def build():
    rnd = random.Random(761)
    b = B()
    def paint(x, y, z, zr):
        if y in (DECK - 2, DECK - 1): return BLUE
        if y == 1: return "minecraft:light_blue_concrete"
        return WHITE if y > 0 else "minecraft:gray_concrete"
    hw = b.hull(HX, HL, CZ, 22, KEEL, DECK, WHITE, bottom="minecraft:gray_concrete", rail="minecraft:white_concrete_powder" if False else "minecraft:birch_fence",
                bow_len=26, stern_len=8, rail_h=1, fill_deck="minecraft:birch_planks", flare=0.1, waterline=0, paint=paint)
    def half(x): return hw.get(x, 0)
    # decks inside: hold (-4), lower deck (1), gun deck (5), weather deck (10)
    for (fy, kinds, seed) in ((-4, ("storage", "storage", "cell", "storage"), 1), (1, ("barracks", "barracks", "kitchen", "dining", "bath", "barracks"), 2),
                              (5, ("armory", "storage", "armory", "barracks", "armory"), 3)):
        for x in range(HX + 4, HX + HL - 8):
            zr = int(half(x)) - 1
            for z in range(CZ - zr, CZ + zr + 1): b.set(x, fy - 1, z, "minecraft:birch_planks" if fy > -4 else "minecraft:spruce_planks")
        x0, x1 = HX + 10, HX + HL - 26
        zr = int(min(half(x0), half(x1))) - 2
        I.subdivide(b, x0, fy, CZ - zr, x1, CZ + zr, 3, "minecraft:birch_planks", kinds, MAR, cell=11, seed=seed,
                    keepout=((HX + 40, CZ - 1, HX + 42, CZ + 1),))
    for y in range(-4, DECK + 1): b.set(HX + 41, y, CZ, "minecraft:ladder[facing=north,waterlogged=false]"); b.set(HX + 41, y, CZ + 1, "minecraft:birch_planks") if y < DECK else None
    for (fy,) in ((0,), (4,), (DECK,)): b.set(HX + 41, fy, CZ, "minecraft:ladder[facing=north,waterlogged=false]")
    for y in (-4, -3, -2):  # the brig with sea-stone bars (inside the hold's cell room)
        for z in range(CZ - 3, CZ + 4): b.set(HX + 14, y, z, "onepiece:prison_bars")
    # gun ports on two decks
    for x in range(HX + 12, HX + HL - 20, 5):
        for side in (-1, 1):
            z = CZ + side * int(round(half(x)))
            for gy in (3, 7):
                b.set(x, gy, z, "minecraft:black_concrete")
                b.set(x, gy - 1, CZ + side * (int(round(half(x))) - 1), f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
            b.set(x, DECK + 1, CZ + side * (int(round(half(x))) - 1), f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
    # ---------------- stern castle: the bridge and the captain's cabin
    S0, S1 = HX + 1, HX + 18
    for x in range(S0, S1 + 1):
        zr = int(round(half(x))) - 1
        for z in range(CZ - zr, CZ + zr + 1):
            for y in range(DECK + 1, DECK + 9):
                edge = x in (S0, S1) or abs(z - CZ) == zr
                b.set(x, y, z, (BLUE if y == DECK + 8 else WHITE) if edge else AIR)
            b.set(x, DECK + 9, z, "minecraft:birch_planks")
            if abs(z - CZ) == zr or x == S0: b.set(x, DECK + 10, z, "minecraft:birch_fence")
        if x % 3 == 0:
            b.set(x, DECK + 4, CZ - zr, "minecraft:glass_pane"); b.set(x, DECK + 4, CZ + zr, "minecraft:glass_pane")
    for z in range(CZ - 1, CZ + 2):
        for y in range(DECK + 1, DECK + 4): b.set(S1, y, z, AIR)
    for z in range(CZ - 7, CZ + 8, 2): b.set(S0, DECK + 4, z, "minecraft:glass_pane"); b.set(S0, DECK + 5, z, "minecraft:glass_pane")
    zz = int(half(S0 + 8)) - 2
    I.furnish(b, S0 + 1, DECK + 1, CZ - zz, S1 - 1, CZ + zz, 7, "captain", MAR)
    b.set(S0 + 4, DECK + 10, CZ, "onepiece:ships_wheel[facing=east]")
    b.box(S0 + 6, DECK + 10, CZ - 3, S0 + 10, DECK + 13, CZ + 3, WHITE); b.box(S0 + 7, DECK + 10, CZ - 2, S0 + 9, DECK + 12, CZ + 2, AIR)
    for z in range(CZ - 2, CZ + 3): b.set(S0 + 10, DECK + 12, z, "minecraft:glass_pane")
    b.set(S0 + 8, DECK + 10, CZ, "onepiece:den_den_relay")
    for i in range(8): b.set(S1 + 1 + i, DECK + 1 + i, CZ + int(half(S1)) - 3, stairs("minecraft:birch_stairs", "west"))
    # ---------------- three masts with MARINE sails
    for (mx, mh) in ((HX + 28, 46), (HX + 46, 52), (HX + 62, 40)):
        b.cyl(mx, CZ, 1, 0, DECK + mh, "minecraft:birch_log[axis=y]")
        nest = DECK + mh - 5
        b.disk(mx, nest, CZ, 2, "minecraft:birch_planks")
        for a in range(0, 360, 45):
            t = math.radians(a); b.set(round(mx + 2 * math.cos(t)), nest + 1, round(CZ + 2 * math.sin(t)), "minecraft:birch_fence")
        for s in range(3):
            span = (mh - 12) // 3
            y0 = DECK + 6 + s * span; y1 = y0 + span - 2
            hh = 13 - s * 3
            b.square_sail(mx + 2, CZ, y0, y1, hh, "minecraft:white_wool", belly=2, pattern=gull if s == 1 else None)
            for z in range(CZ - hh - 2, CZ + hh + 3): b.set(mx + 1, y1 + 1, z, "minecraft:birch_log[axis=z]")
        for y in range(DECK + mh + 1, DECK + mh + 6): b.set(mx, y, CZ, "minecraft:birch_fence")
        b.box(mx, DECK + mh + 2, CZ + 1, mx, DECK + mh + 5, CZ + 5, "minecraft:light_blue_wool"); b.box(mx, DECK + mh + 3, CZ + 2, mx, DECK + mh + 4, CZ + 4, "minecraft:white_wool")
        for side in (-1, 1):
            for k in range(3): b.line((mx - 2 + 2 * k, nest, CZ), (mx - 4 + 4 * k, DECK + 2, CZ + side * int(half(mx))), fence("birch"))
    # ---------------- the seagull figurehead
    bx, by = HX + HL - 1, DECK + 1
    b.shape(lambda x, y, z: ((x - bx) / 4) ** 2 + ((y - by - 2) / 3) ** 2 + ((z - CZ) / 3) ** 2 <= 1, bx - 4, by - 1, CZ - 3, bx + 4, by + 5, CZ + 3, WHITE, interior=None)
    for k in range(4): b.set(bx + 4 + k, by + 2, CZ, "minecraft:yellow_concrete")
    b.set(bx + 3, by + 3, CZ - 2, "minecraft:black_concrete"); b.set(bx + 3, by + 3, CZ + 2, "minecraft:black_concrete")
    for side in (-1, 1):
        for k in range(8): b.set(bx - 2 - k // 2, by + 3 + k // 3, CZ + side * (3 + k), WHITE)
    b.line((bx - 4, DECK + 1, CZ), (bx + 10, DECK + 9, CZ), "minecraft:birch_log[axis=x]")
    # ---------------- loot and crew
    b.chest(S0 + 3, DECK + 1, CZ + 3, "marine", "east"); b.chest(HX + 20, -4, CZ - 4, "marine", "south"); b.chest(HX + 30, 5, CZ + 5, "hard", "north")
    b.guards("elite_marine", ((HX + 22, CZ),), y=DECK + 1)
    b.guards("marine", ((HX + 34, CZ - 6), (HX + 34, CZ + 6), (HX + 54, CZ - 6), (HX + 54, CZ + 6)), y=DECK + 1)
    b.guards("marine_rifle", ((HX + 60, CZ), (HX + 8, CZ)), y=DECK + 1)
    return b, 0
