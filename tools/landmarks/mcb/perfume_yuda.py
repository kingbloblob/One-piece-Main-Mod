"""The Perfume Yuda: the Kuja Pirates' ship, moored in the Amazon Lily cove, with the two Yuda sea serpents that tow it
through the Calm Belt. Built with the ship kit (tools/ships/shipkit.py) so it has a lofted, curved hull instead of the
canvas box ship v2.0 used (ryan: "so basic and bad").

Ship coordinates (shipkit): +x is the bow, z across (centre line z 0), y 0 is the sea surface (block just under water).
  x 0..10   stern castle: Hancock's cabin (two rooms, furnished), poop deck on its roof with the Ship's Wheel and a
            little purple onion-dome pavilion (the Amazon Lily style).
  x 11..33  main deck: main mast x 21, fore mast x 30, scarlet square sails with the Kuja mark, a lateen on the mizzen
            x 12, side paddle wheels at x 17 in gold-trimmed housings, cannons, barrels, a hatch to the hold.
  x 34..41  raised forecastle; the twin serpent figureheads rise from the stem.
Hull: deep purple under water, purple concrete sides with a gold wale and a gold scale band, white quartz bulwark with
gold studs, jungle-plank deck.

yuda(b, ...) draws one towing serpent straight into a landmark canvas (body weaving through the water with humps
breaking the surface, raised neck and head, harness ropes back to the bow).
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

LEN, BEAM = 42, 13
KEEL, DECK = -5, 4
CASTLE_X1 = 10
POOP = DECK + 5
FORE_X0 = 34
MAIN_X, FORE_X, MIZ_X = 21, 30, 12
WHEEL_X = 17

PURP_T = TERRACOTTA["purple"]
PURP = CONCRETE["purple"]
MAG = CONCRETE["magenta"]
GOLD = "minecraft:gold_block"
GOLDT = TERRACOTTA["yellow"]
QZ = "minecraft:smooth_quartz"
QZP = "minecraft:quartz_pillar[axis=y]"
RED_W = WOOL["red"]
DECK_M = "minecraft:jungle_planks"
RAIL = fence("jungle")
BARREL = "minecraft:barrel[facing=up,open=false]"
SNAKE = TERRACOTTA["green"]
SNAKE2 = TERRACOTTA["lime"]
BELLY = TERRACOTTA["yellow"]

# The Kuja mark (a skull with a snake coiled through it), 13 wide x 11 tall, white/black/gold on the scarlet sail.
MARK_ROWS = [
    "......GG.....",
    ".....G..G....",
    "...WWWWW.G...",
    "..WWWWWWW.G..",
    "..WKKWKKW.G..",
    "..WKKWKKW.G..",
    "...WWKWW.G...",
    "..G.WWW.G....",
    ".G..W.W.G....",
    "G........G...",
    ".GG.......GG.",
]
MARK = (MARK_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "G": WOOL["yellow"]})
FLAG_ROWS = [".WWW.", "WKWKW", ".WWW.", "G.G.G", ".G.G."]
FLAG = (FLAG_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "G": WOOL["yellow"], ".": WOOL["purple"]})


def _paint(x, y, z, kind):
    if kind == "bulwark":
        return QZ
    if kind in ("side", "bow", "stern", "bottom"):
        if y <= 0:
            return PURP_T
        if y == 2:                                   # a gold scale band along the sides, broken like scales
            return GOLDT if (x + (1 if z > 0 else 0)) % 3 else GOLD
        return PURP
    return None


def onion(s, cx, y, cz, r, mat, tip=GOLD):
    """A small onion dome: bulges past r above its base, then tapers to a gold finial."""
    h = int(r * 2.4)
    for k in range(h):
        t = k / h
        rr = r * (1.0 + 0.3 * math.sin(math.pi * min(1.0, t / 0.45))) * (1 - t) ** 0.85
        if rr < 0.6:
            s.set(cx, y + k, cz, mat)
        else:
            s.cyl(cx, cz, rr, y + k, y + k, mat)
    for k in range(3):
        s.set(cx, y + h + k, cz, tip)
    return y + h + 2


def serpent_head(s, x, y, z, side, mat=GOLD, eye="minecraft:emerald_block"):
    """A carved figurehead serpent: neck curving forward and up off the stem, head facing +x with eyes and fangs."""
    pts = []
    for i in range(12):
        t = i / 11
        pts.append((x + 6 * math.sin(t * math.pi / 2) + 1.5 * t, y + 9 * t - 1.5 * math.sin(t * math.pi) * 0, z + side * (0.6 + 1.6 * math.sin(t * math.pi))))
    for (px, py, pz) in pts:
        s.blob(px, py, pz, 1.2, 1.2, 1.2, mat, power=2)
    hx, hy, hz = pts[-1]
    s.blob(hx + 1.5, hy + 0.8, hz, 2.6, 1.4, 1.5, mat, power=2.2)             # the head, long and flat
    s.set(round(hx + 1.5), round(hy + 2.2), round(hz - 1), eye)               # eyes on top, both sides
    s.set(round(hx + 1.5), round(hy + 2.2), round(hz + 1), eye)
    s.set(round(hx + 4), round(hy), round(hz - 1), "minecraft:white_concrete")  # fangs
    s.set(round(hx + 4), round(hy), round(hz + 1), "minecraft:white_concrete")
    s.set(round(hx + 4), round(hy - 0.5) - 1, round(hz - 1), "minecraft:white_concrete")
    s.set(round(hx + 4), round(hy - 0.5) - 1, round(hz + 1), "minecraft:white_concrete")
    s.set(round(hx + 5), round(hy), round(hz), CONCRETE["red"])               # forked tongue
    s.set(round(hx + 6), round(hy), round(hz - 1), CONCRETE["red"])
    s.set(round(hx + 6), round(hy), round(hz + 1), CONCRETE["red"])
    return hx, hy, hz


def paddle_wheel(s, x, side, hw):
    """A gold-rimmed paddle wheel on the ship's side in a half-round quartz housing."""
    z = side * (hw + 2)
    cy = 1
    for dz in (0, side):
        s.ring(x, cy, z + dz, 4, GOLD, axis="z")
    for a in range(0, 360, 45):
        t = math.radians(a)
        for rr in range(1, 5):
            s.set(round(x + rr * math.cos(t)), round(cy + rr * math.sin(t)), z, "minecraft:dark_oak_planks")
            s.set(round(x + rr * math.cos(t)), round(cy + rr * math.sin(t)), z + side, "minecraft:dark_oak_planks")
    s.set(x, cy, z - side, "minecraft:dark_oak_log[axis=z]")                   # the axle into the hull
    # the housing: a half-round hood over the top of the wheel, gold rim along its edge
    for a in range(0, 181, 4):
        t = math.radians(a)
        for dz in (-side, 0, side, 2 * side):
            u, v = 5.3 * math.cos(t), 5.3 * math.sin(t)
            blk = GOLD if dz in (-side, 2 * side) else QZ
            s.set(round(x + u), round(cy + v), z + dz, blk)
    # remove what the hood put inside the hull
    for xx in range(x - 6, x + 7):
        for yy in range(cy, cy + 7):
            zz = side * (hw + 1)
            if s.get(xx, yy, zz) in (GOLD, QZ) and abs(zz) <= hw:
                s.set(xx, yy, zz, AIR)


def build():
    s = Ship("perfume_yuda", "Perfume Yuda", faction="pirate", crew="Kuja Pirates")
    s.hull(x0=0, length=LEN, cz=0, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=PURP, bottom=PURP_T, deck=DECK_M,
           bow_len=12, stern_len=5, bow="sharp", stern="round", sheer_bow=3, sheer_stern=1, fullness=0.62, flat=0.35,
           bulwark=1, bulwark_mat=QZ, rail=RAIL, paint=_paint)
    inside = s._inside

    def hw(x):
        return s.halfwidth(x, DECK)

    # the gold wale on the deck-edge course (follows the sheer), gold studs on the white bulwark
    for x in range(0, LEN):
        dy = s.deck_y(x)
        for z in range(-8, 9):
            if s.get(x, dy, z) == PURP:
                s.set(x, dy, z, GOLD)
            if s.get(x, dy + 1, z) == QZ and x % 4 == 1:
                s.set(x, dy + 1, z, GOLD)
    for y in range(KEEL + 1, DECK):                                           # rudder
        s.set(-1, y, 0, "minecraft:dark_oak_planks")

    # ------------------------------------------------------------------ stern castle: Hancock's cabin + poop deck
    for x in range(0, CASTLE_X1 + 1):
        for z in range(-8, 9):
            if not inside(x, DECK, z):
                continue
            edge = not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x - 1, DECK, z))
            if edge or x == CASTLE_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, QZ)
                s.set(x, POOP, z, GOLD)
                s.set(x, POOP + 1, z, RAIL)
            else:
                s.set(x, POOP, z, DECK_M)
    for x in (2, 5, 8):                                                        # purple windows on both sides
        for side in (-1, 1):
            z = side * hw(x)
            s.set(x, DECK + 2, z, pane("purple"))
            s.set(x, DECK + 3, z, pane("purple"))
            s.set(x, DECK + 4, z, GOLD)
    for z in (-3, 0, 3):                                                       # stern gallery windows
        for x in range(-1, 3):
            if s.get(x, DECK + 2, z) == QZ:
                s.set(x, DECK + 2, z, pane("magenta"))
                s.set(x, DECK + 3, z, pane("magenta"))
                break
    I.furnish(s, 1, DECK + 1, -4, CASTLE_X1 - 1, 4, 4, "captain", "royal", seed=31)
    s.set(CASTLE_X1, DECK + 1, 0, door("minecraft:jungle_door", "west", "lower"))
    s.set(CASTLE_X1, DECK + 2, 0, door("minecraft:jungle_door", "west", "upper"))
    for z in (-1, 1):                                                          # pillars either side of the door
        s.set(CASTLE_X1 + 1, DECK + 1, z * 2, QZP)
        s.set(CASTLE_X1 + 1, DECK + 2, z * 2, QZP)
        s.set(CASTLE_X1 + 1, DECK + 3, z * 2, QZP)
        s.set(CASTLE_X1 + 1, DECK + 4, z * 2, GOLD)
    s.lamp(CASTLE_X1 + 1, DECK + 3, 0, hanging=True)
    s.ladder_up(CASTLE_X1 + 1, 4, DECK + 1, POOP, facing="east")
    s.set(CASTLE_X1, POOP + 1, 4, AIR)
    # the helm at the front of the poop deck, the onion-dome pavilion behind it
    s.set(CASTLE_X1, POOP + 1, 0, AIR)
    s.helm(CASTLE_X1 - 1, POOP + 1, 0)
    for (x, z) in ((2, -2), (2, 2), (6, -2), (6, 2)):
        for y in range(POOP + 1, POOP + 5):
            s.set(x, y, z, QZP)
    s.box(1, POOP + 5, -3, 7, POOP + 5, 3, PURP)
    s.box(1, POOP + 5, -3, 7, POOP + 5, -3, GOLD)
    s.box(1, POOP + 5, 3, 7, POOP + 5, 3, GOLD)
    onion(s, 4, POOP + 6, 0, 2.6, PURP)
    s.lamp(4, POOP + 4, 0, hanging=True)
    for (x, z) in ((0, -4), (0, 4), (CASTLE_X1, -5), (CASTLE_X1, 5)):
        s.lamp(x, POOP + 2, z)
    # one ship's wheel only: the furnisher may add one in the cabin
    for p, blk in list(s.blocks.items()):
        if "ships_wheel" in blk and p != s.helm_pos:
            s.set(p[0], p[1], p[2], "minecraft:lectern[facing=east,has_book=false,powered=false]")

    # ------------------------------------------------------------------ forecastle and the twin serpent figureheads
    for x in range(FORE_X0, LEN):
        dy = s.deck_y(x)
        for z in range(-8, 9):
            if inside(x, dy, z):
                edge = not (inside(x, dy, z + 1) and inside(x, dy, z - 1) and inside(x + 1, dy, z))
                s.set(x, dy + 2, z, DECK_M)
                for y in range(dy + 1, dy + 2):
                    s.set(x, y, z, QZ if edge or x == FORE_X0 else DECK_M)
                if edge:
                    s.set(x, dy + 3, z, RAIL)
    s.set(FORE_X0, s.deck_y(FORE_X0) + 1, 0, AIR)                             # step up onto the forecastle
    s.set(FORE_X0 - 1, s.deck_y(FORE_X0 - 1) + 1, 0, "minecraft:jungle_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    stem_y = s.deck_y(LEN - 1) + 2
    heads = [serpent_head(s, LEN - 2, stem_y, side * 1, side) for side in (-1, 1)]
    s.anchor(37, s.deck_y(37), -(hw(37) + 1), "north")

    # ------------------------------------------------------------------ main deck gear
    for side in (-1, 1):
        paddle_wheel(s, WHEEL_X, side, hw(WHEEL_X))
    s.broadside([14, 25, 28], DECK + 1, 0, lambda x: hw(x), gunport=CONCRETE["black"], gunport_y=DECK)
    s.open_hatch(CASTLE_X1 + 3, DECK, -2, w=1, ladder_facing="east", down_to=KEEL + 2)
    for (x, z, b) in ((13, 3, BARREL), (24, -3, BARREL), (24, -4, "onepiece:sake_barrel[axis=y]"), (27, 3, BARREL),
                      (19, 4, "onepiece:rope_coil[facing=east]"), (32, -2, "onepiece:rope_coil[facing=north]")):
        s.set(x, DECK + 1, z, b)
    for x in (14, 22, 29):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * hw(x))

    # ------------------------------------------------------------------ masts, scarlet sails, rigging
    main_top = s.mast(MAIN_X, 0, DECK + 1, 31, wood="jungle", r=0, nest=DECK + 25)
    s.square_sail(MAIN_X, 0, DECK + 6, DECK + 16, 8, RED_W, belly=2, yard="jungle", bitmap=MARK)
    s.square_sail(MAIN_X, 0, DECK + 18, DECK + 23, 6, RED_W, belly=1, yard="jungle")
    fore_top = s.mast(FORE_X, 0, s.deck_y(FORE_X) + 1, 25, wood="jungle")
    s.square_sail(FORE_X, 0, DECK + 6, DECK + 14, 7, RED_W, belly=2, yard="jungle")
    s.square_sail(FORE_X, 0, DECK + 16, DECK + 20, 5, RED_W, belly=1, yard="jungle")
    miz_top = s.mast(MIZ_X, 0, DECK + 1, 20, wood="jungle")
    s.tri_sail(1, (MIZ_X - 7, DECK + 7), (MIZ_X + 1, DECK + 19), (MIZ_X + 1, DECK + 7), WOOL["magenta"])
    s.tri_sail(0, (FORE_X + 2, DECK + 8), (FORE_X + 2, fore_top - 6), (LEN + 2, s.deck_y(LEN - 1) + 5), WOOL["pink"])
    s.flag(MAIN_X, main_top + 1, 0, FLAG, w=5, h=5)
    s.flag(FORE_X, fore_top + 1, 0, FLAG, w=5, h=5)
    for mx, my in ((MAIN_X, DECK + 22), (FORE_X, DECK + 18), (MIZ_X, DECK + 16)):
        for dx in (-3, 0):
            for side in (-1, 1):
                x = mx + dx
                s.rope((mx, my, 0), (x, s.deck_y(x) + 2, side * hw(x)))
    s.rope((MAIN_X + 1, main_top, 0), (FORE_X - 1, fore_top - 2, 0))
    s.rope((FORE_X + 1, fore_top, 0), (LEN, s.deck_y(LEN - 1) + 3, 0))
    s.rope((MIZ_X - 1, miz_top, 0), (1, POOP + 2, 0))
    s.rope((MAIN_X - 1, main_top, 0), (MIZ_X + 1, miz_top - 1, 0))

    # ------------------------------------------------------------------ the hold
    s.chest(15, KEEL + 1, -2, "treasure", facing="south")
    s.chest(20, KEEL + 1, 2, "medium", facing="north")
    for (x, z) in ((17, -2), (18, -2), (23, 2), (24, 2)):
        s.set(x, KEEL + 1, z, BARREL)
    s.lamp(16, DECK - 1, 0, hanging=True)
    s.lamp(24, DECK - 1, 0, hanging=True)
    s.heads = heads
    return s


def place(b, ox, oz):
    """Copies the ship into a landmark canvas with its stern at x = ox, centre line at z = oz. Returns the bow x."""
    s = build()
    for (x, y, z), st in s.blocks.items():
        b.set(x + ox, y, z + oz, st, s.nbt.get((x, y, z)))
    return ox + LEN, s


def yuda(b, x0, z0, length, side, phase, harness_to, rnd=None):
    """One Yuda towing serpent swimming toward +x from x0 at z0: the body weaves (sine in z), humps break the surface,
    the neck rears up at the front and the head looks ahead with gold eyes and a forked tongue. A harness of ropes runs
    from a gold collar back to harness_to (a point on the bow). Drawn straight into the canvas b."""
    pts = []
    for i in range(length):
        t = i / (length - 1)
        x = x0 + i
        z = z0 + side * 2.5 * math.sin(i * 0.35 + phase)
        hump = math.sin(i * 0.5 + phase * 1.3)
        y = -1.2 + (2.4 * (hump - 0.2) if hump > 0.2 else 0)                  # under water between the humps
        r = 1.9 - 1.1 * (1 - t) ** 3                                           # tail thin, body thick
        pts.append((x, y, z, r))
    # the neck rears up from the front of the body in an S: straight up first, then arching forward
    nx, ny, nz, _ = pts[-1]
    for k in range(1, 13):
        u = k / 12
        pts.append((nx + 4 * u ** 2.2, ny + 11 * math.sin(u * math.pi / 2), nz, 1.8 - 0.5 * u))
    for i, (x, y, z, r) in enumerate(pts):
        for xx in range(int(x - r) - 1, int(x + r) + 2):
            for yy in range(int(y - r) - 1, int(y + r) + 2):
                for zz in range(int(z - r) - 1, int(z + r) + 2):
                    if (xx - x) ** 2 + (yy - y) ** 2 + (zz - z) ** 2 <= r * r:
                        under = yy < y - r * 0.35
                        blk = BELLY if under else (SNAKE2 if (xx * 3 + int(zz)) % 7 == 0 else SNAKE)
                        if yy <= 0 and b.get(xx, yy, zz) not in (None, AIR) and "water" not in (b.get(xx, yy, zz) or ""):
                            continue
                        b.set(xx, yy, zz, blk)
    hx, hy, hz, _ = pts[-1]
    # the head: a long, flat wedge pointing ahead (+x), with a brow ridge, eyes, fangs and a forked tongue
    hx0 = int(round(hx)) - 1
    for xx in range(hx0, hx0 + 8):
        f = (xx - hx0) / 7
        half = 1.7 - 0.9 * f
        top = hy + 1.4 - 0.9 * f
        bot = hy - 1.0 + 0.3 * f
        for yy in range(int(round(bot)), int(round(top)) + 1):
            for zz in range(int(round(hz - half)), int(round(hz + half)) + 1):
                b.set(xx, yy, zz, BELLY if yy == int(round(bot)) else SNAKE)
    ey = int(round(hy + 1))
    for s_ in (-1, 1):
        ez = int(round(hz + s_ * 2))
        b.set(hx0 + 2, ey, ez, "minecraft:gold_block")                        # eyes bulging from the sides
        b.set(hx0 + 2, ey + 1, int(round(hz + s_)), SNAKE2)                   # brow ridges
        b.set(hx0 + 7, int(round(hy - 1)), int(round(hz + s_)), "minecraft:white_concrete")   # fangs
    b.set(hx0 + 8, int(round(hy)), int(round(hz)), CONCRETE["red"])          # forked tongue
    b.set(hx0 + 9, int(round(hy)), int(round(hz - 1)), CONCRETE["red"])
    b.set(hx0 + 9, int(round(hy)), int(round(hz + 1)), CONCRETE["red"])
    for k in range(4):                                                         # a fin crest down the back of the neck
        px, py, pz, pr = pts[-12 + k * 3]
        b.set(int(round(px - pr)), int(round(py)), int(round(pz)), SNAKE2)
    # a gold collar at the base of the neck and the harness ropes back to the bow
    cx, cy, cz = nx + 0.5, ny + 3, nz
    for a in range(0, 360, 15):
        t = math.radians(a)
        b.set(round(cx), round(cy + 2.4 * math.sin(t)), round(cz + 2.4 * math.cos(t)), "minecraft:gold_block")
    hx2, hy2, hz2 = harness_to
    b.line((round(cx), round(cy + 1), round(cz)), (hx2, hy2, hz2), "minecraft:jungle_fence")
    b.line((round(cx) - 1, round(cy + 2), round(cz)), (hx2, hy2 + 1, hz2), "minecraft:jungle_fence")
