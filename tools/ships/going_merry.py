"""Going Merry: the Straw Hats' first ship. A small, stubby, cheerful caravel with a sheep's head on the bow.

Layout (x = 0 stern .. 25 bow, z across the ship, CZ = 0, deck at y 3):
  x 0..8    stern castle: galley on the main deck (door at x 8), poop deck on its roof (y 7) with the wheel, the
            mizzen with the striped lateen sail and the three mikan trees; the lounge/store room inside the hull below.
  x 9..18   open main deck: main mast at x 14, hatch down to the hold at (10, 2).
  x 19..25  forecastle: foredeck 2 above the main deck, the bow cannon firing through a round port in the stem
            below, the sheep head on top of the stem in front (x 23..29, horns out to z +-5).
"""
from shipkit import *  # noqa: F401,F403

CUTS = (4,)       # one cut just above the main deck: shows the deck layout and what stands on it

CZ = 0
X0, LEN = 0, 26
X1 = X0 + LEN - 1                 # 25 = the stem
BEAM = 10                         # half width 4.5 -> 9 blocks wide
KEEL, DECK = -4, 3
POOP = DECK + 4                   # roof of the galley = floor of the poop deck (y 7)
FORE = DECK + 2                   # foredeck floor (y 5)
MAST_X = 14
MIZZEN_X = 1

OAK = "minecraft:oak_planks"
STRIPPED = "minecraft:stripped_oak_log[axis=x]"
WALE = "minecraft:dark_oak_planks"
SPRUCE = "minecraft:spruce_planks"
WHITE = CONCRETE["white"]
WHITE_T = TERRACOTTA["white"]
WOOL_W = WOOL["white"]
BLACK = CONCRETE["black"]
YELLOW_T = TERRACOTTA["yellow"]
ORANGE_T = TERRACOTTA["orange"]
RAIL = fence("oak")
WRAIL = fence("birch")            # the "white" railings of the fore and poop decks (pale wood)
BARREL = "minecraft:barrel[facing=up,open=false]"
SAKE = "onepiece:sake_barrel[axis=y]"
LEAVES = "minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]"
MIKAN = "onepiece:mikan_bush[age=3]"

# A 9x7 Straw Hat Jolly Roger small enough for a flag (the kit's STRAW_HAT is 20x17 and flag() crops, not scales).
MERRY_FLAG_ROWS = [
    "...YYY...",
    "..YRRRY..",
    "YYYYYYYYY",
    "W.WWWWW.W",
    ".WWKWKWW.",
    "..WWWWW..",
    "W.WKWKW.W",
]
MERRY_FLAG = (MERRY_FLAG_ROWS, {"Y": WOOL["yellow"], "R": WOOL["red"], "W": WOOL["white"], "K": WOOL["black"]})
BLACK_FLAG = (["K" * 9] * 7, {"K": WOOL["black"]})

# The mainsail emblem drawn at the sail's own size (15 wide x 13 tall) so every block maps 1:1, no resampling.
SAIL_ROWS = [
    ".....YYYYY.....",
    "....YYYYYYY....",
    "....YRRRRRY....",
    ".YYYYYYYYYYYYY.",
    "...YYYYYYYYY...",
    "....WWWWWWW....",
    "W..WWWWWWWWW..W",
    ".W.WWKKWKKWW.W.",
    "..WWWKKWKKWWW..",
    "...WWWWKWWWW...",
    "..W.WWWWWWW.W..",
    ".W..WKWKWKW..W.",
    "W....WWWWW....W",
]
# On the sail the skull and bones are BLACK on the white canvas ('W' -> black) with white sockets/teeth ('K' -> white).
SAIL_MARK = (SAIL_ROWS, {"Y": WOOL["yellow"], "R": WOOL["red"], "W": WOOL["black"], "K": WOOL["white"]})


# One curled ram's horn seen from the side (columns x 23..27 back to front, rows y 12 down to 8): a solid golden disc
# against the head (|z| 3) and the coil on top of it (|z| 4): yellow ridge, orange groove spiralling into the centre,
# the tip curling forward and down at the bottom front toward the cheek.
HORN_DISC_ROWS = [
    ".YYY.",
    "YYYYY",
    "YYYYY",
    "YYYYY",
    ".YYYY",
]
HORN_COIL_ROWS = [
    ".YYY.",
    "YOOOY",
    "YOYOY",
    "YOOYY",
    ".YYYY",
]
HORN_PAL = {"Y": YELLOW_T, "O": ORANGE_T}


# Merry's head from the side (bow to the right), one profile per distance from the centre line. The snout is 3 wide,
# the face 5 wide with the big eyes on its sides, and the wool mane 7 wide at the back of the head behind the horns.
HEAD_PROFILES = {
    0: ["...W.W.W....",
        "..WWWWWWF...",
        ".WWWWWWFFF..",
        ".WWWWWFFFFF.",
        "..WWWWFFFFF.",
        "..WWWWFFFFFF",
        "...WWWFFFFF.",
        "...WWWFF....",
        "...WW......."],
    1: ["............",
        "..WWWWWWF...",
        ".WWWWWWFFF..",
        ".WWWWWFFFFF.",
        "..WWWWFFFFF.",
        "..WWWWFFFKKF",
        "...WWWFFFFF.",
        "...WWWFF....",
        "............"],
    2: ["............",
        "...WWWW.....",
        "..WWWWWKK...",
        "..WWWWFKKF..",
        "..WWWWFFFF..",
        "...WWWFFK...",
        "....WWFFF...",
        "............",
        "............"],
    3: ["............",
        "............",
        "...WWW......",
        "..WWWW......",
        "..WWWW......",
        "...WW.......",
        "............",
        "............",
        "............"],
}


def bow_white_floor(x):
    """Lowest white course of the hull side at x: the white bow sweeps down from the wale at x 17 to the waterline at
    the stem, and every other column dips one lower, so the edge is scalloped like curls of wool."""
    if x < 17:
        return 99
    base = 3 if x <= 18 else 2 if x <= 22 else 1
    return base - 1 if x % 2 == 1 else base


def hull_paint(x, y, z, kind):
    """Warm tan hull, dark wale, white upper works; the whole bow above the wale white with a scalloped lower edge."""
    if kind == "bulwark":
        return WHITE
    if kind in ("side", "bow", "stern"):
        if y <= 0:
            return SPRUCE
        if kind != "stern" and y >= bow_white_floor(x):
            return WHITE
        if y == 1:
            return OAK if kind == "stern" else STRIPPED
        if y == 2:
            return WALE
        if y == DECK:
            return OAK
    return None


def build():
    s = Ship("going_merry", "Going Merry", faction="player", tiers=[], crew="Straw Hat Pirates")

    # ------------------------------------------------------------------ hull
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=OAK, bottom=SPRUCE, deck=OAK,
           wale=WALE, bow_len=10, stern_len=3, bow="sharp", stern="transom", sheer_bow=0, sheer_stern=0,
           fullness=0.6, flat=0.45, bulwark=1, bulwark_mat=WHITE, rail=RAIL, paint=hull_paint,
           inner_decks=[(-1, SPRUCE)])
    inside = s._inside

    def footprint(x):
        return [z for z in range(CZ - 7, CZ + 8) if inside(x, DECK, z)]

    def is_edge(x, z):
        return not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x + 1, DECK, z) and inside(x - 1, DECK, z))

    # the stern bottom tapers so steeply that the hollowed skin only touches diagonally there: fill it solid
    for x in range(X0, X0 + 3):
        for y in range(KEEL, -1):
            for z in range(-4, 5):
                if inside(x, y, z) and s.get(x, y, z) == AIR:
                    s.set(x, y, z, SPRUCE)

    # rudder hanging off the transom, down under the water
    for y in range(-3, DECK + 1):
        s.set(X0 - 1, y, CZ, WALE)
    for y in range(-3, 1):
        s.set(X0 - 2, y, CZ, WALE)

    # ------------------------------------------------------------------ stern castle (galley) + poop deck
    SC1 = 8
    for x in range(X0, SC1 + 1):
        for z in footprint(x):
            if is_edge(x, z) or x == SC1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, OAK)
                s.set(x, POOP, z, WALE)                     # dark trim under the poop deck rail
                if x == SC1:
                    s.set(x, POOP + 1, z, WRAIL)             # open rail along the front edge
                else:
                    s.set(x, POOP + 1, z, WHITE)             # white bulwark round the poop deck
                    s.set(x, POOP + 2, z, WRAIL)
            else:
                s.set(x, POOP, z, OAK)                       # roof = poop deck floor
    # stripped-log course round the galley walls
    for x in range(X0, SC1 + 1):
        for z in footprint(x):
            if (is_edge(x, z) or x == SC1) and s.get(x, DECK + 3, z) == OAK:
                s.set(x, DECK + 3, z, STRIPPED if x not in (X0, SC1) else OAK)
    # round-topped transom: a stepped arch above the poop bulwark, lanterns at the corners
    for z in range(-2, 3):
        s.set(X0, POOP + 2, z, WHITE)
    for z in range(-1, 2):
        s.set(X0, POOP + 3, z, WHITE)
    s.lamp(X0, POOP + 2, -3)
    s.lamp(X0, POOP + 2, 3)
    # portholes: galley back wall (the two on the transom), galley sides and front, lounge sides in the hull
    for z in (-2, 2):
        s.porthole(X0, DECK + 2, z, "west")
        s.porthole(SC1, DECK + 2, z, "east")
    for x in (3, 6):
        s.porthole(x, DECK + 2, 4, "south")
        s.porthole(x, DECK + 2, -4, "north")
        s.porthole(x, 2, 4, "south")
        s.porthole(x, 2, -4, "north")
    # galley door onto the main deck, with a little awning and a lantern over it
    s.set(SC1, DECK + 1, CZ, AIR)
    s.set(SC1, DECK + 2, CZ, AIR)
    for z in (-1, 0, 1):
        s.set(SC1 + 1, POOP, z, slab("minecraft:oak_slab", "top"))
    s.lamp(SC1 + 1, POOP - 1, CZ, hanging=True)
    # the galley: Sanji's kitchen
    I.furnish(s, X0 + 1, DECK + 1, -3, SC1 - 1, 3, 3, "kitchen", "pirate", seed=7)
    s.set(SC1, DECK + 1, CZ, door("minecraft:oak_door", "west", "lower"))
    s.set(SC1, DECK + 2, CZ, door("minecraft:oak_door", "west", "upper"))
    # stairs from the main deck up to the poop deck along the port side (z -3)
    for (x, y) in ((11, 4), (10, 4), (10, 5), (9, 4), (9, 5), (9, 6)):
        s.set(x, y, -3, OAK)
    s.stairs_run(12, DECK + 1, -3, 4, "minecraft:oak_stairs", "west")
    s.set(SC1, POOP + 1, -3, AIR)                            # gap in the front rail where the stairs arrive
    # the Ship's Wheel at the front edge of the poop deck, facing the bow
    s.set(SC1, POOP + 1, CZ, AIR)
    s.helm(SC1, POOP + 1, CZ)
    s.lamp(SC1, POOP + 1, -4)
    s.lamp(SC1, POOP + 1, 4)

    # mikan grove: a planter box with three little tangerine trees
    for x in range(4, 7):
        for z in range(-3, 4):
            s.set(x, POOP + 1, z, WALE if (x in (4, 6) or z in (-3, 3)) else "onepiece:deck_soil")
    for z in (-2, 0, 2):
        s.set(5, POOP + 2, z, log("oak"))
        for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            s.set(5 + dx, POOP + 3, z + dz, LEAVES)
        s.set(5, POOP + 4, z, LEAVES)
        s.set(4, POOP + 4, z, MIKAN)
        s.set(6, POOP + 4, z, MIKAN)

    # mizzen: short mast on the poop deck with a red-and-white striped lateen sail
    mz_top = s.mast(MIZZEN_X, CZ, POOP + 1, 10, wood="spruce")      # y 8..17
    s.tri_sail(CZ, (3, 11), (-4, 18), (-4, 11), WOOL_W, pattern=stripes(WOOL["red"], WOOL["white"]))
    s.line((3, 11, CZ), (-4, 18, CZ), log("spruce", "x"))              # the lateen yard
    for y in range(POOP + 1, mz_top + 1):
        s.set(MIZZEN_X, y, CZ, log("spruce"))
    s.rope((-4, 10, CZ), (X0, POOP + 2, CZ))                           # sheet from the clew down to the transom arch

    # ------------------------------------------------------------------ main deck
    # hatch down to the hold with a ladder (its backing column at x 11)
    s.open_hatch(10, DECK, 2, w=1, ladder_facing="west", down_to=-3)
    for y in range(-3, DECK):
        s.set(11, y, 2, OAK)
    # deck gear: rope coils, barrels, the two little deck guns
    s.set(12, DECK + 1, 3, "onepiece:rope_coil[facing=north]")
    s.set(13, DECK + 1, -3, "onepiece:rope_coil[facing=south]")
    s.set(9, DECK + 1, 3, BARREL)
    s.set(9, DECK + 1, 2, SAKE)
    s.set(18, DECK + 1, 0, BARREL)
    s.broadside([16], DECK + 1, CZ, lambda x: 4)
    s.lamp(11, DECK + 2, 4)
    s.lamp(11, DECK + 2, -4)
    s.lamp(MAST_X + 1, DECK + 1, 1)                              # lantern at the foot of the mast
    s.lamp(15, DECK + 2, 4)
    s.lamp(15, DECK + 2, -4)
    # wall between the lounge and the hold, with a doorway
    for y in range(0, DECK):
        for z in range(-3, 4):
            s.set(9, y, z, OAK)
    s.set(9, 0, CZ, AIR)
    s.set(9, 1, CZ, AIR)

    # ------------------------------------------------------------------ main mast, sail, crow's nest, flag, rigging
    for y in range(-1, DECK + 1):
        s.set(MAST_X, y, CZ, log("spruce"))                     # stepped on the inner deck
    sail_y0, sail_y1 = DECK + 3, DECK + 15                       # y 6..18, 15 wide: the emblem maps 1:1
    s.square_sail(MAST_X, CZ, sail_y0, sail_y1, 7, WOOL_W, belly=1, yard="spruce", bitmap=SAIL_MARK)
    yard_y = sail_y1 + 1                                         # 19
    nest_y = yard_y + 1                                          # 20: barrel crow's nest floor
    # the barrel: planks floor, oak staves with a dark hoop
    s.cyl(MAST_X, CZ, 2.0, nest_y, nest_y, WALE)
    s.cyl(MAST_X, CZ, 2.0, nest_y + 1, nest_y + 1, OAK, hollow=True)
    s.cyl(MAST_X, CZ, 2.0, nest_y + 2, nest_y + 2, WALE, hollow=True)
    top = s.mast(MAST_X, CZ, DECK + 1, nest_y + 3 - DECK, wood="spruce")   # y 4..23
    # black flag with the Straw Hat Jolly Roger
    s.flag(MAST_X, top + 1, CZ, BLACK_FLAG, w=9, h=7)
    s.flag(MAST_X, top + 1, CZ, MERRY_FLAG, w=9, h=7)
    # rigging: shrouds run from beside the yard down to the rails, one block abaft the sail so they don't cut it
    for dx in (-2, -1, 0):
        for side in (-4, 4):
            s.rope((MAST_X - 1, yard_y, CZ), (MAST_X - 1 + dx, DECK + 2, side))
    s.rope((MAST_X + 2, top, CZ), (X1, FORE + 3, CZ))            # forestay to the stem head
    s.rope((MAST_X - 2, top, 1), (4, POOP + 2, 4))               # backstays to the poop rails
    s.rope((MAST_X - 2, top, -1), (4, POOP + 2, -4))
    s.lamp(MAST_X, yard_y - 1, 8, hanging=True)                  # lanterns under the yard arms
    s.lamp(MAST_X, yard_y - 1, -8, hanging=True)

    # ------------------------------------------------------------------ forecastle and foredeck
    FC0 = 19
    for x in range(FC0, X1 + 1):
        for z in footprint(x):
            if is_edge(x, z) or x == FC0:
                s.set(x, DECK + 1, z, WHITE)
                s.set(x, DECK + 2, z, WHITE)
                if is_edge(x, z):
                    s.set(x, FORE + 1, z, WHITE)
                    s.set(x, FORE + 2, z, WRAIL)
                elif abs(z) != 2:
                    s.set(x, FORE + 1, z, WRAIL)                # rail along the step, gaps for the stairs
            else:
                s.set(x, FORE, z, OAK)
    # stairs up to the foredeck on both sides
    for zz in (-2, 2):
        s.set(FC0 - 1, DECK + 1, zz, OAK)
        s.stairs_run(FC0 - 2, DECK + 1, zz, 2, "minecraft:oak_stairs", "east")
    # the bow cannon, firing forward through a round port in the stem (dark rim round the hole)
    s.set(X1, DECK + 1, CZ, AIR)
    s.set(X1 - 1, DECK + 1, CZ, AIR)
    s.cannon(X1 - 2, DECK + 1, CZ, "east")
    s.set(X1, DECK, CZ, WALE)
    s.set(X1, DECK + 2, CZ, WALE)
    for (y, z) in ((DECK, -1), (DECK, 1), (DECK + 1, -1), (DECK + 1, 1), (DECK + 2, -1), (DECK + 2, 1)):
        s.set(X1 - 1, y, z, WALE)
    s.lamp(21, FORE + 2, 3)
    s.lamp(21, FORE + 2, -3)
    s.set(22, FORE + 1, 0, "onepiece:rope_coil[facing=east]")
    # anchor at the port bow
    s.anchor(20, DECK, -4, "north")

    # ------------------------------------------------------------------ the figurehead: Merry's sheep head
    # Like the show: a smooth white face with a long snout pointing forward, big black eyes on the sides of the face, a
    # smile along the snout, a curly wool mane over the crown and down the back of the neck, and golden ram horns curling
    # back beside the cheeks. Neck: the white stem rises and curves forward over the cannon port (port y 3-5 stays clear).
    for y in range(FORE + 1, FORE + 4):
        s.set(X1, y, CZ, WHITE)
    for z in (-1, 0, 1):
        s.set(X1 + 1, FORE + 1, z, WHITE)
        s.set(X1 + 1, FORE + 2, z, WHITE)
        s.set(X1 + 1, FORE, z, stairs("minecraft:quartz_stairs", "west", half="top"))
        s.set(X1 + 2, FORE + 2, z, WHITE)
        s.set(X1 + 2, FORE + 1, z, stairs("minecraft:quartz_stairs", "west", half="top"))
    # The head is carved from side profiles, one per |z| slice (columns x 22..33, rows y 14 down to 6):
    # W = curly wool mane, F = smooth white face, K = black (eyes, smile), the snout ends in a rounded nose.
    pal = {"W": WOOL_W, "F": WHITE, "K": BLACK}
    for dz, rows in HEAD_PROFILES.items():
        for side in ((-1, 1) if dz else (1,)):
            s.paint_wall(22, 6, side * dz, (rows, pal), axis="x")
    # Golden ram horns curling back beside the cheeks, behind the eyes (x 23..27), thickening outward at the curl.
    for side in (-1, 1):
        s.paint_wall(23, 8, side * 3, (HORN_DISC_ROWS, HORN_PAL), axis="x")
        s.paint_wall(23, 8, side * 4, (HORN_COIL_ROWS, HORN_PAL), axis="x")
        s.set(25, 10, side * 5, YELLOW_T)          # the boss at the centre of the coil

    # ------------------------------------------------------------------ below decks
    # lounge / store room in the stern (floor y -1, under the galley)
    s.table_set(4, 0, CZ, "oak")
    s.set(1, 0, -2, BARREL)
    s.set(1, 0, 2, BARREL)
    s.set(2, 0, -2, SAKE)
    s.chest(3, 0, -3, "easy", facing="south")
    s.set(7, 0, 3, "minecraft:bookshelf")
    s.set(7, 0, -3, "minecraft:crafting_table")
    s.set(6, 0, 3, "minecraft:water_cauldron[level=3]")
    s.lamp(4, 2, CZ, hanging=True)
    s.lamp(2, 2, CZ, hanging=True)
    # upper hold forward of the lounge (y 0..2)
    s.set(16, 0, 3, BARREL)
    s.set(16, 0, -3, BARREL)
    s.set(17, 0, 3, SAKE)
    s.set(20, 0, 1, BARREL)
    s.chest(13, 0, -3, "easy", facing="south")
    s.lamp(13, 2, CZ, hanging=True)
    s.lamp(19, 2, CZ, hanging=True)
    # the lower hold (y -3..-2), reached by the ladder
    s.chest(12, -3, -2, "easy", facing="south")
    s.chest(13, -3, -2, "medium", facing="south")
    s.set(15, -3, 2, BARREL)
    s.set(16, -3, 2, BARREL)
    s.set(17, -3, -2, SAKE)
    s.set(8, -3, 2, BARREL)
    s.set(8, -3, -2, "minecraft:hay_block[axis=y]")
    s.lamp(13, -2, CZ, hanging=True)
    s.lamp(7, -2, CZ, hanging=True)
    return s
