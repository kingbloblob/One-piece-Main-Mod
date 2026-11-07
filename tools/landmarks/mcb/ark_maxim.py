"""Enel's golden ark Maxim, standing on its building cradle at Shandora. Built with the ship kit (tools/ships/shipkit.py)
so it has a lofted, curved hull instead of the canvas box ship v1 used (ryan: "more realistic ships").

Ship coordinates (shipkit): +x is the bow, z across (centre line z 0), y 0 is the waterline.
  x 0..11   raised stern: Enel's throne on a gold dais under a canopy, the ring of thunder drums behind it (Enel's
            drum halo, here as six gold drums standing on posts in a half circle), the Ship's Wheel; his cabin below.
  x 12..41  main deck: two tall masts with great white sails painted with a gold lightning bolt, the Raigo generator
            dome amidships (a gold sphere in a cage of copper ribs), barrels of dials.
  x 42..49  forecastle with a golden ram-head figurehead.
  Along both sides, nine golden paddle-oars (the dial-driven propellers): looms reaching out and down, flat blades.
Hull: gold blocks above a yellow terracotta band, raw gold under the waterline, white quartz bulwark with gold studs,
birch deck.
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

LEN, BEAM = 50, 15
KEEL, DECK = -5, 4
STERN_X1 = 11
POOP = DECK + 5
FORE_X0 = 42
MAIN_X, FORE_X = 20, 33

GOLD = "minecraft:gold_block"
RAWG = "minecraft:raw_gold_block"
GOLDT = TERRACOTTA["yellow"]
QZ = "minecraft:smooth_quartz"
QZP = "minecraft:quartz_pillar[axis=y]"
DECK_M = "minecraft:birch_planks"
RAIL = fence("birch")
BARREL = "minecraft:barrel[facing=up,open=false]"
COPPER = "minecraft:cut_copper"

BOLT_ROWS = [
    ".....GGG",
    "....GGG.",
    "...GGG..",
    "..GGGGGG",
    ".....GG.",
    "....GG..",
    "...GG...",
    "..GG....",
    ".G......",
]
BOLT = (BOLT_ROWS, {"G": WOOL["yellow"], ".": WOOL["white"]})
FLAG_ROWS = ["..G..", ".GG..", "GGGGG", "..GG.", "..G.."]
FLAG = (FLAG_ROWS, {"G": WOOL["yellow"], ".": WOOL["white"]})


def _paint(x, y, z, kind):
    if kind == "bulwark":
        return QZ
    if kind in ("side", "bow", "stern", "bottom"):
        if y <= 0:
            return RAWG
        if y == 1:
            return GOLDT
        return GOLD
    return None


def oar(s, x, side, hw):
    """A golden paddle-oar: a loom out through the bulwark, angled down to a broad flat blade near the waterline."""
    z0 = side * (hw + 1)
    for k in range(7):
        s.set(x, DECK + 1 - k // 2, z0 + side * k, GOLD if k < 6 else GOLDT)
    bz = z0 + side * 7
    for dy in range(-3, 1):
        for dx in (-1, 0, 1):
            s.set(x + dx, DECK - 3 + dy, bz, GOLD if dx == 0 else "minecraft:yellow_concrete")
    s.set(x, DECK + 1, side * hw, "minecraft:lightning_rod")


def build():
    s = Ship("ark_maxim", "Ark Maxim", faction="pirate", crew="Enel")
    s.hull(x0=0, length=LEN, cz=0, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=GOLD, bottom=RAWG, deck=DECK_M,
           bow_len=13, stern_len=6, bow="sharp", stern="round", sheer_bow=4, sheer_stern=2, fullness=0.68, flat=0.4,
           bulwark=1, bulwark_mat=QZ, rail=RAIL, paint=_paint)
    inside = s._inside

    def hw(x):
        return s.halfwidth(x, DECK)

    for x in range(0, LEN):
        dy = s.deck_y(x)
        for z in range(-9, 10):
            if s.get(x, dy + 1, z) == QZ and x % 4 == 2:
                s.set(x, dy + 1, z, GOLD)
    for y in range(KEEL + 1, DECK):
        s.set(-1, y, 0, GOLD)

    # ------------------------------------------------------------------ stern: Enel's cabin, throne deck, drums
    for x in range(0, STERN_X1 + 1):
        for z in range(-9, 10):
            if not inside(x, DECK, z):
                continue
            edge = not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x - 1, DECK, z))
            if edge or x == STERN_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, QZ)
                s.set(x, POOP, z, GOLD)
                s.set(x, POOP + 1, z, RAIL)
            else:
                s.set(x, POOP, z, DECK_M)
    for x in (2, 5, 8):
        for side in (-1, 1):
            z = side * hw(x)
            s.set(x, DECK + 2, z, pane("yellow"))
            s.set(x, DECK + 3, z, pane("yellow"))
    I.furnish(s, 1, DECK + 1, -5, STERN_X1 - 1, 5, 4, "captain", "royal", seed=41)
    s.set(STERN_X1, DECK + 1, 0, door("minecraft:birch_door", "west", "lower"))
    s.set(STERN_X1, DECK + 2, 0, door("minecraft:birch_door", "west", "upper"))
    s.ladder_up(STERN_X1 + 1, 5, DECK + 1, POOP, facing="east")
    s.set(STERN_X1, POOP + 1, 5, AIR)
    s.set(STERN_X1, POOP + 1, 0, AIR)
    s.helm(STERN_X1 - 1, POOP + 1, 0)
    # the throne on its dais, a canopy on quartz posts
    s.box(3, POOP + 1, -2, 6, POOP + 1, 2, GOLD)
    s.set(4, POOP + 2, 0, "minecraft:quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    s.set(3, POOP + 2, 0, GOLD); s.set(3, POOP + 3, 0, GOLD)
    s.set(4, POOP + 2, -1, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    s.set(4, POOP + 2, 1, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    for (x, z) in ((2, -3), (2, 3), (7, -3), (7, 3)):
        for y in range(POOP + 2, POOP + 7):
            s.set(x, y, z, QZP)
    s.box(2, POOP + 7, -3, 7, POOP + 7, 3, "minecraft:white_wool")
    s.box(2, POOP + 7, -3, 7, POOP + 7, -3, GOLD); s.box(2, POOP + 7, 3, 7, POOP + 7, 3, GOLD)
    # the drum halo: six gold drums in a half ring behind the throne
    for k in range(6):
        a = math.radians(95 + k * 34)
        x, z = max(1, round(4 + 3.2 * math.cos(a))), round(4.6 * math.sin(a))
        s.set(x, POOP + 2, z, QZP)
        s.set(x, POOP + 3, z, GOLD)
        s.set(x, POOP + 4, z, "minecraft:yellow_concrete")
        s.set(x, POOP + 5, z, "minecraft:lightning_rod")
    for p, blk in list(s.blocks.items()):
        if "ships_wheel" in blk and p != s.helm_pos:
            s.set(p[0], p[1], p[2], "minecraft:lectern[facing=east,has_book=false,powered=false]")

    # ------------------------------------------------------------------ forecastle and the ram-head figurehead
    for x in range(FORE_X0, LEN):
        dy = s.deck_y(x)
        for z in range(-9, 10):
            if inside(x, dy, z):
                edge = not (inside(x, dy, z + 1) and inside(x, dy, z - 1) and inside(x + 1, dy, z))
                s.set(x, dy + 2, z, DECK_M)
                s.set(x, dy + 1, z, QZ if edge or x == FORE_X0 else DECK_M)
                if edge:
                    s.set(x, dy + 3, z, RAIL)
    s.set(FORE_X0, s.deck_y(FORE_X0) + 1, 0, AIR)
    s.set(FORE_X0 - 1, s.deck_y(FORE_X0 - 1) + 1, 0, "minecraft:birch_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    sy = s.deck_y(LEN - 1) + 1
    s.blob(LEN + 1, sy + 1, 0, 2.6, 2.0, 1.8, GOLD, power=2.2)
    for side in (-1, 1):
        for k in range(5):                                       # curled horns
            a = k * 0.9
            s.set(round(LEN + 0.5 - 1.6 * math.cos(a)), round(sy + 3 + 1.6 * math.sin(a)), side * 2, GOLDT)
        s.set(LEN + 3, sy + 2, side, "minecraft:emerald_block")
    s.anchor(45, s.deck_y(45), -(hw(45) + 1), "north")

    # ------------------------------------------------------------------ main deck: oars, Raigo dome, cargo
    for k in range(9):
        x = 14 + k * 3
        for side in (-1, 1):
            oar(s, x, side, hw(x))
    cx = 27
    s.blob(cx, DECK + 5, 0, 4.2, 4.2, 4.2, GOLD, power=2.0, hollow=True)
    for a in range(0, 360, 30):
        t = math.radians(a)
        for k in range(0, 13):
            v = math.radians(-90 + k * 15)
            s.set(round(cx + 5.2 * math.cos(v) * math.cos(t)), round(DECK + 5 + 5.2 * math.sin(v)), round(5.2 * math.cos(v) * math.sin(t)), COPPER) \
                if math.sin(v) > -0.6 else None
    s.set(cx, DECK + 11, 0, "minecraft:lightning_rod"); s.set(cx, DECK + 12, 0, "minecraft:lightning_rod")
    for (x, z, b) in ((14, 3, BARREL), (15, 3, BARREL), (16, -4, BARREL), (38, 3, BARREL), (38, -3, "onepiece:sake_barrel[axis=y]"),
                      (22, 5, "onepiece:rope_coil[facing=east]"), (36, -5, "onepiece:rope_coil[facing=north]")):
        s.set(x, DECK + 1, z, b)
    s.open_hatch(STERN_X1 + 3, DECK, -3, w=1, ladder_facing="east", down_to=KEEL + 2)
    for x in (15, 24, 31, 39):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * hw(x))

    # ------------------------------------------------------------------ masts and the great white sails
    main_top = s.mast(MAIN_X, 0, DECK + 1, 34, wood="birch", r=0, nest=DECK + 28)
    s.square_sail(MAIN_X, 0, DECK + 7, DECK + 19, 9, WOOL["white"], belly=2, yard="birch", bitmap=BOLT)
    s.square_sail(MAIN_X, 0, DECK + 21, DECK + 26, 7, WOOL["white"], belly=1, yard="birch")
    fore_top = s.mast(FORE_X, 0, DECK + 1, 29, wood="birch")
    s.square_sail(FORE_X, 0, DECK + 12, DECK + 21, 8, WOOL["white"], belly=2, yard="birch", bitmap=BOLT)
    s.square_sail(FORE_X, 0, DECK + 23, DECK + 26, 5, WOOL["white"], belly=1, yard="birch")
    s.tri_sail(0, (FORE_X + 2, DECK + 8), (FORE_X + 2, fore_top - 6), (LEN + 2, s.deck_y(LEN - 1) + 6), WOOL["yellow"])
    s.flag(MAIN_X, main_top + 1, 0, FLAG, w=5, h=5)
    s.flag(FORE_X, fore_top + 1, 0, FLAG, w=5, h=5)
    for mx, my in ((MAIN_X, DECK + 25), (FORE_X, DECK + 22)):
        for dx in (-3, 0):
            for side in (-1, 1):
                x = mx + dx
                s.rope((mx, my, 0), (x, s.deck_y(x) + 2, side * hw(x)))
    s.rope((MAIN_X + 1, main_top, 0), (FORE_X - 1, fore_top - 2, 0))
    s.rope((FORE_X + 1, fore_top, 0), (LEN, s.deck_y(LEN - 1) + 4, 0))
    s.rope((MAIN_X - 1, main_top, 0), (STERN_X1 - 1, POOP + 2, 0))

    # ------------------------------------------------------------------ the hold
    s.chest(20, KEEL + 1, -2, "treasure", facing="south")
    for (x, z) in ((22, -2), (23, -2), (30, 2), (31, 2)):
        s.set(x, KEEL + 1, z, BARREL)
    s.lamp(22, DECK - 1, 0, hanging=True)
    return s


def place(b, ox, oy, oz):
    """Copies the ship into a landmark canvas with its stern at x = ox, waterline at y = oy, centre line at z = oz.
    Returns (lowest y, ship)."""
    s = build()
    for (x, y, z), st in s.blocks.items():
        b.set(x + ox, y + oy, z + oz, st, s.nbt.get((x, y, z)))
    return oy + KEEL, s
