"""The Sexy Foxy: Foxy the Silver Fox's flagship, moored off Long Ring Long Land for the Davy Back Fight. Built with the
ship kit (tools/ships/shipkit.py) like the Perfume Yuda: a lofted, curved hull, not a box.

Ship coordinates (shipkit): +x is the bow, z across (centre line z 0), y 0 is the sea surface.
  x 0..9    stern castle: Foxy's cabin (furnished), poop deck on its roof with the Ship's Wheel.
  x 10..33  main deck: main mast x 19, fore mast x 28, white square sails with Foxy's mark (a skull with fox ears
            and a long fox nose), cannons, barrels, a hatch to the hold.
  x 34..43  raised forecastle; the big fox-head figurehead on the stem, orange with white cheeks and pointed ears.
Hull: dark oak under water, brown and orange sides with a white wale, spruce deck.
"""
import math
import os
import sys

_SHIPS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ships")
if not os.path.isdir(_SHIPS):
    _SHIPS = "/mnt/project-files/one-piece-mod/tools/ships"
if _SHIPS not in sys.path:
    sys.path.insert(0, _SHIPS)
from shipkit import Ship, WOOL, CONCRETE, TERRACOTTA, pane, fence, door, AIR, I  # noqa: E402

LEN, BEAM = 44, 13
KEEL, DECK = -5, 4
CASTLE_X1 = 9
POOP = DECK + 5
FORE_X0 = 35
MAIN_X, FORE_X = 19, 28

SIDE = "minecraft:spruce_planks"
BAND = TERRACOTTA["orange"]
BOTTOM = "minecraft:dark_oak_planks"
WALE = CONCRETE["white"]
DECK_M = "minecraft:spruce_planks"
RAIL = fence("spruce")
FOX = CONCRETE["orange"]
FOX2 = TERRACOTTA["orange"]
CHEEK = CONCRETE["white"]
SAIL = WOOL["white"]
BARREL = "minecraft:barrel[facing=up,open=false]"

# Foxy's mark: a skull with fox ears and a long nose, crossbones behind. 13 x 11.
MARK_ROWS = [
    ".KK.......KK.",
    ".KKK.....KKK.",
    "..KKKKKKKKK..",
    "..KKWWWWWKK..",
    "..KWWWWWWWK..",
    "..KWKKWKKWK..",
    "..KWWWWWWWK..",
    "...KWWKWWK...",
    "K...KWKWK...K",
    ".KK..KKK..KK.",
    "...KK...KK...",
]
MARK = (MARK_ROWS, {"W": WOOL["white"], "K": WOOL["black"]})
FLAG = (MARK_ROWS[:9], {"W": WOOL["white"], "K": WOOL["black"], ".": WOOL["black"]})


def _paint(x, y, z, kind):
    if kind == "bulwark":
        return SIDE
    if kind in ("side", "bow", "stern", "bottom"):
        if y <= 0:
            return BOTTOM
        if y in (1, 2):
            return BAND
        return SIDE
    return None


def fox_head(s, x, y):
    """The fox figurehead: a long snout pointing forward, white cheeks, two tall pointed ears, black eyes and nose."""
    s.blob(x, y + 2, 0, 3.4, 3.0, 3.0, FOX, power=2)                         # head
    s.blob(x + 4, y + 1, 0, 3.2, 1.6, 1.6, FOX, power=2)                     # snout
    for side in (-1, 1):
        s.blob(x + 1, y, side * 2, 2.0, 1.5, 1.4, CHEEK, power=2)             # white cheeks
        for k in range(5):                                                     # pointed ears
            r = 1.4 * (1 - k / 5)
            s.blob(x - 1, y + 5 + k, side * (1.8 + k * 0.15), max(0.5, r), 0.6, max(0.5, r), FOX2 if k < 4 else CONCRETE["black"])
        s.set(x + 2, y + 3, side * 2, CONCRETE["black"])                       # eyes
    s.set(x + 7, y + 1, 0, CONCRETE["black"])                                  # nose
    s.set(x + 6, y, 0, CHEEK)


def build():
    s = Ship("sexy_foxy", "Sexy Foxy", faction="pirate", crew="Foxy Pirates")
    s.hull(x0=0, length=LEN, cz=0, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=SIDE, bottom=BOTTOM, deck=DECK_M,
           bow_len=13, stern_len=5, bow="sharp", stern="transom", sheer_bow=3, sheer_stern=2, fullness=0.6, flat=0.4,
           bulwark=1, bulwark_mat=SIDE, rail=RAIL, paint=_paint, wale=WALE)
    inside = s._inside

    def hw(x):
        return s.halfwidth(x, DECK)

    for y in range(KEEL + 1, DECK):                                           # rudder
        s.set(-1, y, 0, "minecraft:dark_oak_planks")

    # stern castle with Foxy's cabin
    for x in range(0, CASTLE_X1 + 1):
        for z in range(-8, 9):
            if not inside(x, DECK, z):
                continue
            edge = not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x - 1, DECK, z))
            if edge or x == CASTLE_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, SIDE if y != DECK + 4 else BAND)
                s.set(x, POOP, z, "minecraft:stripped_spruce_log[axis=x]")
                s.set(x, POOP + 1, z, RAIL)
            else:
                s.set(x, POOP, z, DECK_M)
    for x in (2, 5, 8):
        for side in (-1, 1):
            z = side * hw(x)
            s.set(x, DECK + 2, z, pane("orange"))
            s.set(x, DECK + 3, z, pane("orange"))
    I.furnish(s, 1, DECK + 1, -4, CASTLE_X1 - 1, 4, 4, "captain", "pirate", seed=41)
    s.set(CASTLE_X1, DECK + 1, 0, door("minecraft:spruce_door", "west", "lower"))
    s.set(CASTLE_X1, DECK + 2, 0, door("minecraft:spruce_door", "west", "upper"))
    s.lamp(CASTLE_X1 + 1, DECK + 3, -2)
    s.ladder_up(CASTLE_X1 + 1, 4, DECK + 1, POOP, facing="east")
    s.set(CASTLE_X1, POOP + 1, 4, AIR)
    s.helm(CASTLE_X1 - 2, POOP + 1, 0)
    for p, blk in list(s.blocks.items()):
        if "ships_wheel" in blk and p != s.helm_pos:
            s.set(p[0], p[1], p[2], "minecraft:lectern[facing=east,has_book=false,powered=false]")
    s.lamp(0, POOP + 2, -3)
    s.lamp(0, POOP + 2, 3)

    # forecastle and the fox head
    for x in range(FORE_X0, LEN):
        dy = s.deck_y(x)
        for z in range(-8, 9):
            if inside(x, dy, z):
                edge = not (inside(x, dy, z + 1) and inside(x, dy, z - 1) and inside(x + 1, dy, z))
                s.set(x, dy + 2, z, DECK_M)
                s.set(x, dy + 1, z, SIDE)
                if edge:
                    s.set(x, dy + 3, z, RAIL)
    s.set(FORE_X0, s.deck_y(FORE_X0) + 1, 0, AIR)
    s.set(FORE_X0 - 1, s.deck_y(FORE_X0 - 1) + 1, 0, "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    fox_head(s, LEN - 1, s.deck_y(LEN - 1) + 1)
    s.anchor(38, s.deck_y(38), -(hw(38) + 1), "north")

    s.broadside([13, 23, 31], DECK + 1, 0, lambda x: hw(x), gunport=CONCRETE["black"], gunport_y=DECK)
    s.open_hatch(CASTLE_X1 + 3, DECK, -2, w=1, ladder_facing="east", down_to=KEEL + 2)
    for (x, z, b) in ((12, 3, BARREL), (22, -3, BARREL), (22, -4, "onepiece:sake_barrel[axis=y]"), (26, 3, BARREL),
                      (17, 4, "onepiece:rope_coil[facing=east]"), (32, -2, "onepiece:rope_coil[facing=north]")):
        s.set(x, DECK + 1, z, b)
    for x in (14, 21, 30):
        for side in (-1, 1):
            s.lamp(x, DECK + 2, side * (hw(x) - 1))

    main_top = s.mast(MAIN_X, 0, DECK + 1, 30, wood="spruce", nest=DECK + 24)
    s.square_sail(MAIN_X, 0, DECK + 6, DECK + 16, 8, SAIL, belly=2, yard="spruce", bitmap=MARK)
    s.square_sail(MAIN_X, 0, DECK + 18, DECK + 22, 6, SAIL, belly=1, yard="spruce")
    fore_top = s.mast(FORE_X, 0, DECK + 1, 25, wood="spruce")
    s.square_sail(FORE_X, 0, DECK + 6, DECK + 14, 7, SAIL, belly=2, yard="spruce")
    s.square_sail(FORE_X, 0, DECK + 16, DECK + 20, 5, SAIL, belly=1, yard="spruce")
    s.tri_sail(0, (FORE_X + 2, DECK + 8), (FORE_X + 2, fore_top - 6), (LEN + 1, s.deck_y(LEN - 1) + 7), WOOL["orange"])
    s.flag(MAIN_X, main_top + 1, 0, FLAG, w=13, h=9)
    for mx, my in ((MAIN_X, DECK + 22), (FORE_X, DECK + 18)):
        for dx in (-3, 0):
            for side in (-1, 1):
                x = mx + dx
                s.rope((mx, my, 0), (x, s.deck_y(x) + 2, side * hw(x)))
    s.rope((MAIN_X + 1, main_top, 0), (FORE_X - 1, fore_top - 2, 0))
    s.rope((MAIN_X - 1, main_top - 2, 0), (1, POOP + 2, 0))

    s.chest(15, KEEL + 1, -2, "medium", facing="south")
    for (x, z) in ((17, -2), (18, -2), (21, 2), (22, 2)):
        s.set(x, KEEL + 1, z, BARREL)
    s.lamp(16, DECK - 1, 0, hanging=True)
    return s


def place(b, ox, oz):
    """Copies the ship into a landmark canvas with its stern at x = ox, centre line at z = oz. Returns the bow x."""
    s = build()
    for (x, y, z), st in s.blocks.items():
        b.set(x + ox, y, z + oz, st, s.nbt.get((x, y, z)))
    return ox + LEN, s
