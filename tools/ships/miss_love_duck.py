"""Miss Love Duck: Alvida's ship. A stubby pink caravel with red hearts on her sides, a red wale, white trim, a cream
deck, one mast with a pink sail bearing Alvida's mark (skull with a heart) and a big yellow duck head on the bow with
an orange bill and a red bow under its chin.

Layout (x = 0 stern .. 26 bow, z across the ship, CZ = 0, main deck at y 4, keel y -4):
  x 0..6    stern castle: Alvida's perfumed cabin (door at x 6), the poop deck on its roof (y 8) with the Ship's Wheel
            at the front edge; a red heart painted on the transom.
  x 7..18   main deck: the mast at x 14 with the pink sail; cannons at x 9 and x 18 on both sides behind black gunports
            framed red; hatch down to the hold at (7, 4, -3); barrels and rope coils.
  x 19..26  bow (the sheer lifts it to y 5-6): the anchor and the duck head on top of the stem (x 26..33), with a red
            bow (pink knot, two loops, two tails) in front of the neck under the chin.
Hull colours (midships, from the water up): dusty pink (terracotta) at and under the waterline (y <= 0), bright pink
(concrete) y 1..3 with the red hearts on y 0..3, red wale at y 4 (the deck-edge course), white bulwark at y 5, birch
rail at y 6. A small 7x5 pink flag with Alvida's skull at the mast head.
"""
from shipkit import *  # noqa: F401,F403

CUTS = (5,)       # one cut just above the main deck: the deck layout and the cabin

CZ = 0
X0, LEN = 0, 27
X1 = X0 + LEN - 1                 # 26 = the stem
BEAM = 11                         # half width 5 -> deck z -5..5
KEEL, DECK = -4, 4
POOP = DECK + 4                   # roof of the castle = floor of the poop deck (y 8)
CASTLE_X1 = 6
MAST_X = 14
SAIL_Y0, SAIL_Y1 = DECK + 4, DECK + 14          # y 8..18, 11 rows: the mark maps 1:1
HEART_XS = (8, 17)                              # left edge of the two hearts on each side

PINK_T = TERRACOTTA["pink"]
PINK_C = CONCRETE["pink"]
PINK_W = WOOL["pink"]
RED = CONCRETE["red"]
RED_W = WOOL["red"]
WHITE = CONCRETE["white"]
WHITE_W = WOOL["white"]
BLACK = CONCRETE["black"]
YELLOW = CONCRETE["yellow"]
ORANGE = CONCRETE["orange"]
DARK_OAK = "minecraft:dark_oak_planks"
CREAM = "minecraft:birch_planks"
RAIL = fence("birch")
BARREL = "minecraft:barrel[facing=up,open=false]"
SAKE = "onepiece:sake_barrel[axis=y]"
WINDOW = pane()
PINK_CANDLE = "minecraft:pink_candle[candles=3,lit=true,waterlogged=false]"
TULIP = "minecraft:potted_pink_tulip"

# Alvida's mark redrawn 15 wide x 11 tall (skull, red heart on the forehead, crossbones) so it maps 1:1 onto the
# 15-wide sail. The kit's ALVIDA uses a pink heart, invisible on a pink sail, so the heart is red here.
SAIL_ROWS = [
    "W....WWWWW....W",
    ".W..WWRWRWW..W.",
    "..W.WRRRRRW.W..",
    "...WWWRRRWWW...",
    "....WWWRWWW....",
    "....WKKWKKW....",
    "....WKKWKKW....",
    "...W.WWKWW.W...",
    "..W.WKWKWKW.W..",
    ".W...WWWWW...W.",
    "W.............W",
]
SAIL_MARK = (SAIL_ROWS, {"W": WHITE_W, "K": WOOL["black"], "R": RED_W})

# A small 7x5 Alvida skull for the flag at the mast head (red heart on the skull, crossed bones), on pink.
FLAG_ROWS = [
    ".WRWRW.",
    ".WRRRW.",
    "..WKW..",
    ".W.W.W.",
    "W.....W",
]
ALVIDA_FLAG = (FLAG_ROWS, {"W": WHITE_W, "K": WOOL["black"], "R": RED_W})
PINK_FLAG = (["P" * 7] * 5, {"P": PINK_W})

# A red heart, 5 wide x 4 tall, for the hull sides and the transom.
HEART_ROWS = [
    ".R.R.",
    "RRRRR",
    ".RRR.",
    "..R..",
]
HEART = (HEART_ROWS, {"R": RED_W})


class DuckShip(Ship):
    """Ship whose '<id>_front.png' really looks from the bow (the kit's elevation keeps the stern-most block per
    pixel, which hides the duck head behind the transom)."""

    def elevation(self, out, axis="z", scale=8, title=None):
        import render
        from PIL import Image, ImageDraw
        pts = {}
        for (x, y, z), st in self.blocks.items():
            if st == AIR or st.split("[")[0] in render.SKIP:
                continue
            key, depth = ((x, y), z) if axis == "z" else ((-z, y), x)
            if key not in pts or depth > pts[key][0]:
                pts[key] = (depth, st)
        if not pts:
            return
        us = [k[0] for k in pts]
        vs = [k[1] for k in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        pad = 12
        W = (u1 - u0 + 1) * scale + 2 * pad
        H = (v1 - v0 + 1) * scale + 2 * pad + (30 if title else 0)
        img = Image.new("RGB", (W, H), (206, 224, 236))
        d = ImageDraw.Draw(img)
        sea_y = pad + (v1 - 0) * scale + (30 if title else 0)
        d.rectangle([0, sea_y + scale, W, H], fill=(96, 140, 210))
        depths = [p[0] for p in pts.values()]
        dmin, dmax = min(depths), max(depths)
        for (u, v), (depth, st) in pts.items():
            cols = render.block_colors(st)
            if cols is None:
                continue
            t = 0.75 + 0.25 * ((depth - dmin) / max(1, dmax - dmin))
            c = tuple(int(min(255, cc * t)) for cc in cols[1])
            px = pad + (u - u0) * scale
            py = pad + (v1 - v) * scale + (30 if title else 0)
            d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
        if title:
            d.text((pad, 8), title, fill=(30, 40, 60))
        img.save(out)
        return out


def hull_paint(x, y, z, kind):
    """Bright pink sides, white bulwark, dusty pink under water (the red wale is painted after, all the way round)."""
    if kind == "bulwark":
        return WHITE
    if kind in ("side", "bow", "stern", "bottom"):
        return PINK_T if y <= 0 else PINK_C          # dusty pink terracotta under water, bright pink concrete above
    return None


def paint_side(s, x0, y0, rows, palette, side):
    """Paints a bitmap on the outside of the hull on one side (+1 starboard, -1 port): for every pixel the outermost
    hull block at that (x, y) is recoloured, so the picture follows the curve of the hull."""
    h = len(rows)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            blk = palette.get(ch)
            if not blk:
                continue
            x, y = x0 + i, y0 + h - 1 - j
            for w in range(9, -1, -1):
                z = CZ + side * w
                if s.get(x, y, z) not in (None, AIR):
                    s.set(x, y, z, blk)
                    break


def one_helm(s):
    """The interior furnisher may drop a Ship's Wheel in the cabin: keep only s.helm's."""
    for p, b in list(s.blocks.items()):
        if "ships_wheel" in b and p != s.helm_pos:
            s.set(p[0], p[1], p[2], "minecraft:lectern[facing=east,has_book=false,powered=false]")


def build():
    s = DuckShip("miss_love_duck", "Miss Love Duck", faction="pirate", tiers=[0], crew="Alvida Pirates")

    # ------------------------------------------------------------------ hull
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=PINK_C, bottom=PINK_T, deck=CREAM,
           bow_len=8, stern_len=4, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=0,
           fullness=0.6, flat=0.4, bulwark=1, bulwark_mat=WHITE, rail=RAIL, paint=hull_paint)
    inside = s._inside

    def footprint(x):
        return [z for z in range(CZ - 7, CZ + 8) if inside(x, DECK, z)]

    def is_edge(x, z):
        return not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x + 1, DECK, z) and inside(x - 1, DECK, z))

    def edge_z(x):
        """z of the bulwark on the starboard side at x (the port side is -edge_z)."""
        return s.halfwidth(x, DECK)

    # the red wale on the deck-edge course, all the way round (it follows the sheer up to the bow)
    for x in range(X0, X1 + 1):
        dy = s.deck_y(x)
        for z in range(-8, 9):
            if s.get(x, dy, z) == PINK_C:
                s.set(x, dy, z, RED)
    # the hollowed skin only touches diagonally where the bottom steps up toward the bow and stern: fill the corners
    steps = [(x, y, z) for x in range(X0, X1 + 1) for y in range(KEEL, 1) for z in range(-7, 8)
             if inside(x, y, z) and s.get(x, y, z) == AIR and s.get(x, y - 1, z) not in (None, AIR)
             and (s.get(x + 1, y, z) not in (None, AIR) or s.get(x - 1, y, z) not in (None, AIR))]
    for (x, y, z) in steps:
        s.set(x, y, z, PINK_T)
    # rudder hanging off the transom, down under the water
    for y in range(KEEL + 1, DECK):
        s.set(X0 - 1, y, CZ, DARK_OAK)
    # red hearts on both sides of the hull, on the bright pink band y 0..3 (between the waterline and the wale)
    for hx in HEART_XS:
        for side in (-1, 1):
            paint_side(s, hx, 0, HEART_ROWS, HEART[1], side)

    # ------------------------------------------------------------------ stern castle (Alvida's cabin) + poop deck
    for x in range(X0, CASTLE_X1 + 1):
        for z in footprint(x):
            if is_edge(x, z) or x == CASTLE_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, PINK_C)
                s.set(x, POOP, z, WHITE)                                 # white trim round the roof edge
                s.set(x, POOP + 1, z, RAIL)                              # rail round the poop deck
            else:
                s.set(x, POOP, z, CREAM)                                 # roof = poop deck floor
    # a red heart on the transom (the wale course below it makes the point)
    s.paint_wall(X0, DECK + 1, -2, ([".R.R.", "RRRRR", ".RRR."], {"R": RED_W}), axis="z")
    # windows on the sides of the cabin, framed white
    for x in (2, 4):
        hw = edge_z(x)
        for side in (-1, 1):
            s.set(x, DECK + 2, side * hw, WINDOW)
            s.set(x, DECK + 3, side * hw, WHITE)
            s.set(x, DECK + 1, side * hw, WHITE)
    # cabin door onto the main deck
    s.set(CASTLE_X1, DECK + 1, CZ, AIR)
    s.set(CASTLE_X1, DECK + 2, CZ, AIR)
    I.furnish(s, X0 + 1, DECK + 1, -2, CASTLE_X1 - 1, 2, 3, "captain", "royal", seed=5)
    s.set(CASTLE_X1, DECK + 1, CZ, door("minecraft:dark_oak_door", "west", "lower"))
    s.set(CASTLE_X1, DECK + 2, CZ, door("minecraft:dark_oak_door", "west", "upper"))
    # the perfume: pink candles and tulips in the cabin
    s.set(X0 + 1, DECK + 1, -2, TULIP)
    s.set(X0 + 1, DECK + 1, 2, TULIP)
    s.set(CASTLE_X1 - 1, DECK + 1, -2, PINK_CANDLE)
    s.set(CASTLE_X1 - 1, DECK + 1, 2, PINK_CANDLE)
    s.lamp(CASTLE_X1 + 1, POOP - 1, CZ, hanging=True)
    # ladder up the front wall of the castle to the poop deck (starboard side)
    s.ladder_up(CASTLE_X1 + 1, 3, DECK + 1, POOP, facing="east")
    s.set(CASTLE_X1, POOP + 1, 3, AIR)                       # gap in the front rail where the ladder arrives
    # the Ship's Wheel at the front edge of the poop deck, facing the bow
    s.set(CASTLE_X1, POOP + 1, CZ, AIR)
    s.helm(CASTLE_X1, POOP + 1, CZ)
    one_helm(s)
    s.lamp(CASTLE_X1, POOP + 2, -3)
    s.lamp(X0, POOP + 2, -3)
    s.lamp(X0, POOP + 2, 3)
    s.set(2, POOP + 1, 2, BARREL)
    s.set(2, POOP + 1, -2, "onepiece:rope_coil[facing=north]")

    # ------------------------------------------------------------------ main deck
    # hatch down to the hold beside the castle; the ladder leans on a post against the cabin front
    for y in range(KEEL + 1, DECK):
        s.set(CASTLE_X1, y, -3, DARK_OAK)
    s.open_hatch(CASTLE_X1 + 1, DECK, -3, w=1, ladder_facing="east", down_to=KEEL + 2)
    # cannons fore and aft of the mast on both sides
    s.broadside([9, 18], DECK + 1, CZ, lambda x: 5, gunport=BLACK, gunport_y=DECK + 1)
    for x in (9, 18):                                            # each gunport framed red in place of the rail
        for side in (-1, 1):
            s.set(x, DECK + 2, side * 5, RED)
    s.set(10, DECK + 1, 3, BARREL)
    s.set(11, DECK + 1, 4, SAKE)
    s.set(17, DECK + 1, -3, BARREL)
    s.set(16, DECK + 1, 2, "onepiece:rope_coil[facing=east]")
    for x in (9, 18):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * 5)                        # lanterns on the rail posts

    # ------------------------------------------------------------------ mast, sail, flag, rigging
    s.square_sail(MAST_X, CZ, SAIL_Y0, SAIL_Y1, 7, PINK_W, belly=1, yard="spruce", bitmap=SAIL_MARK)
    yard_y = SAIL_Y1 + 1                                         # 21
    top = s.mast(MAST_X, CZ, DECK + 1, yard_y + 4 - DECK, wood="spruce")   # y 7..24
    s.flag(MAST_X, top + 1, CZ, PINK_FLAG, w=7, h=5)
    s.flag(MAST_X, top + 1, CZ, ALVIDA_FLAG, w=7, h=5)
    for x in (MAST_X - 2, MAST_X):                               # shrouds to the rails on both sides
        for side in (-1, 1):
            s.rope((MAST_X, yard_y - 1, CZ), (x, DECK + 2, side * edge_z(x)))
    s.rope((MAST_X + 1, top, CZ), (X1 - 1, s.deck_y(X1 - 1) + 3, CZ))   # forestay down to the duck's neck
    s.rope((MAST_X - 1, top, CZ), (X0 + 1, POOP + 1, CZ))                # backstay down to the poop deck
    s.lamp(MAST_X, yard_y - 1, 8, hanging=True)
    s.lamp(MAST_X, yard_y - 1, -8, hanging=True)

    # ------------------------------------------------------------------ bow
    s.anchor(22, s.deck_y(22), -(edge_z(22) + 1), "north")       # hangs on the port bow
    s.set(21, s.deck_y(21) + 1, 2, BARREL)
    s.set(23, s.deck_y(23) + 1, 0, "onepiece:rope_coil[facing=east]")
    for side in (-1, 1):
        s.lamp(23, s.deck_y(23) + 3, side * edge_z(23))

    # ------------------------------------------------------------------ the figurehead: the duck head
    bow_deck = s.deck_y(X1)                                      # 8
    neck_y0, neck_y1 = bow_deck + 1, bow_deck + 4                # neck y 9..12 on top of the stem, 3 wide, 2 long
    for x in (X1, X1 + 1):
        for y in range(neck_y0, neck_y1 + 1):
            for z in (-1, 0, 1):
                s.set(x, y, z, YELLOW)
    s.set(X1, bow_deck, -1, YELLOW)                              # the neck's root spreads onto the stem
    s.set(X1, bow_deck, 1, YELLOW)
    hx, hy = X1 + 2.5, neck_y1 + 2.5                             # head centre (28.5, 14.5): y 12..17, x 26..31
    head = set()

    def head_mat(x, y, z):
        head.add((x, y, z))
        return YELLOW
    s.blob(hx, hy, CZ, 2.6, 2.8, 2.6, head_mat, power=2.2)        # solid: every block touches its neighbours

    def front(y, z):
        """x of the front of the face at that height and side."""
        return max(x for (xx, yy, zz) in head for x in (xx,) if yy == y and zz == z)
    eye_y = int(hy + 0.5)                                        # 15
    bill_y = int(hy - 1.5)                                       # 13: the bill, 2 rows (13, 14)
    tip_x = front(bill_y + 1, 0) + 3                             # the bill sticks out 3 past the face
    # the bill: orange, 3 wide, 2 thick, growing straight out of the face, the tip drooping one
    for z in (-1, 0, 1):
        for x in range(front(bill_y, z) + 1, tip_x + 1):
            s.set(x, bill_y, z, ORANGE)
        for x in range(front(bill_y + 1, z) + 1, tip_x):
            s.set(x, bill_y + 1, z, ORANGE)
    s.set(tip_x, bill_y - 1, CZ, ORANGE)
    # eyes: two black blocks set into the front of the face above the bill, and on the cheeks so they read side-on
    for z in (-1, 1):
        s.set(front(eye_y, z), eye_y, z, BLACK)
    for side in (-1, 1):
        cheek_z = max(abs(zz) for (xx, yy, zz) in head if yy == eye_y and xx == int(hx) + 1)
        s.set(int(hx) + 1, eye_y, side * cheek_z, BLACK)
    # a little curled tuft on the crown, leaning back
    top_y = max(y for (x, y, z) in head)
    s.set(int(hx), top_y + 1, CZ, YELLOW)
    s.set(int(hx), top_y + 2, CZ, YELLOW)
    s.set(int(hx) - 1, top_y + 2, CZ, YELLOW)
    # the red bow under the chin, in front of the neck: a pink knot with two red loops (2 deep, widening to 3 tall
    # at their ends, sticking out past the 3-wide neck) and two short tails hanging down
    ky = neck_y0 + 1
    s.set(X1 + 2, ky, CZ, RED_W)                                 # behind the knot, ties it to the loops
    s.set(X1 + 3, ky, CZ, PINK_W)                                # the knot
    for side in (-1, 1):
        for dz, half in ((1, 0), (2, 1), (3, 1)):
            for x in (X1 + 2, X1 + 3):
                for y in range(ky - half, ky + half + 1):
                    s.set(x, y, side * dz, RED_W)
        for y in (neck_y0 - 1, neck_y0):                         # the tails
            s.set(X1 + 3, y, side, RED_W)

    # ------------------------------------------------------------------ the hold: loot and barrels down on the keel
    hy0 = KEEL + 1
    s.chest(10, hy0, -2, "pirate", facing="south")
    s.chest(11, hy0, -2, "easy", facing="south")
    s.chest(16, hy0, 2, "treasure", facing="north")
    s.set(13, hy0, 2, BARREL)
    s.set(14, hy0, 2, SAKE)
    s.set(17, hy0, -2, BARREL)
    s.lamp(10, DECK - 1, CZ, hanging=True)
    s.lamp(17, DECK - 1, CZ, hanging=True)
    return s
