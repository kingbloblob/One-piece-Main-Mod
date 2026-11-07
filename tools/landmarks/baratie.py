"""The Baratie: Zeff's fish-shaped sea restaurant (East Blue), built to match the show (reference picture in
previews/references/baratie-reference.png).

What the show has, and where it is here:
- a red-brown wooden hull with a white deck edge and a purple railed deck;
- a big WHITE fish head over the bow with thick orange-and-yellow lips round a wide open mouth, small round eyes
  and an orange collar where it meets the hull;
- a tall orange tail fin with yellow edges at the stern;
- three stepped mint-green tiers: the wide ground floor with arched yellow-framed windows and the yellow arched
  front door; a narrower second floor under a white band with the BARATIE sign and red-and-white life rings;
  a narrower top floor with RESTAURANT across its face, a yellow-and-white scalloped awning and a red door;
  every step is a balcony with a purple rail;
- an orange-red tiled hip roof with a small green cupola on the ridge;
- two green masts with round tops, yards hung with yellow-and-white striped swag sails, red BT flags and
  rope-ladder shrouds.
Life size: ~115 blocks long (tail to mouth), 31 wide, 75 tall. Water surface = y 0. Bow (fish head) points +x."""
import math, random
from canvas import *
import interiors as I

SID = "baratie"
TITLE = "Baratie"
WATER_Y = 0
CUTS = [6, 15, 22, 29]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

DARK = "minecraft:dark_oak_planks"
HULL = "minecraft:mangrove_planks"
WHITE = "minecraft:smooth_quartz"
SNOW = "minecraft:white_concrete"
MINT = "minecraft:prismarine_bricks"
YEL = "minecraft:bamboo_planks"
YEL_ST = "minecraft:bamboo_stairs"
ORANGE = "minecraft:orange_concrete"
ORANGE2 = "minecraft:orange_terracotta"
GOLD = "minecraft:yellow_concrete"
BLACK = "minecraft:black_concrete"
ROOF_ST = "onepiece:dressrosa_tile_stairs"
ROOF = "onepiece:dressrosa_tiles"
DECK = "minecraft:spruce_planks"
FLOOR = "minecraft:dark_oak_planks"
POST = "minecraft:purpur_pillar[axis=y]"
RAIL = "minecraft:purple_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]"
BLUE = "minecraft:light_blue_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]"
MAST = "minecraft:stripped_warped_stem[axis=y]"

CZ = 17
DECK_Y = 3
X0, X1 = 7, 65                      # ground floor of the restaurant along the deck
CX = (X0 + X1) / 2
F1, F2, F2B, F3 = DECK_Y, 12, 19, 26  # floors: ground, second, second-floor attic (behind the BARATIE band), top
TOP = 37                            # roof base
# the three tiers: (grow, superellipse power, wall bottom, wall top)
TIERS = ((0.0, 4, F1 + 1, F2 - 1), (-2.0, 4, F2 + 1, F3 - 1), (-4.0, 8, F3 + 1, TOP - 1))
HX, HY, HR = 78, 6, 16              # fish head: centre x, centre y, length radius (a tall egg, as high as the 2nd floor)
HEAD_BACK = 68
MOUTH_Y = 7                         # the mouth's axis; its lower lip sits on the water


def inside(x, z, grow=0.0, p=4):
    """Tier footprint: a superellipse round at the ends, shrunk by -grow for the upper tiers."""
    hx = (X1 - X0) / 2 + 0.5 + grow; hz = 10.5 + grow
    return (abs(x - CX) / hx) ** p + (abs(z - CZ) / hz) ** p <= 1.0


def ring(grow=0.0, p=4):
    """Edge cells of a footprint with their outward direction."""
    out = []
    for x in range(X0 - 2, X1 + 3):
        for z in range(CZ - 13, CZ + 14):
            if not inside(x, z, grow, p): continue
            for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
                if not inside(x + dx, z + dz, grow, p):
                    out.append((x, z, f)); break
    return out


def face_z(grow, p, side):
    """z of the flat long wall of a tier on the north (-1) or south (+1) side."""
    z = CZ
    while inside(int(CX), z + side, grow, p): z += side
    return z


def face_text(b, xc, y, z, msg, s, side):
    """Text centred on xc on a long wall, reading the right way round from outside (side +1 = south face)."""
    w = len(msg) * 4 - 1
    if side > 0: b.text(int(xc - w // 2), y, z, msg, s, axis="x", step=1)
    else: b.text(int(xc + w // 2), y, z, msg, s, axis="x", step=-1)


def head_in(x, y, z):
    """The fish head: an egg cut flat at the back (the collar)."""
    if x < HEAD_BACK: return False
    return ((x - HX) / HR) ** 2 + ((y - HY) / 13.0) ** 2 + ((z - CZ) / 12.0) ** 2 <= 1.0


def head_front(y, z):
    """x of the front surface of the head at (y, z), or None."""
    for x in range(HX + HR, HX - 1, -1):
        if head_in(x, y, z): return x
    return None


def mouth_d(y, z):
    """Distance measure in the mouth's cross-section: < 1 is the opening."""
    return ((y - MOUTH_Y) / 5.3) ** 2 + ((z - CZ) / 7.0) ** 2


def build():
    b = B()
    rnd = random.Random(7)

    # ---------------- hull: dark oak under the water, red-brown planks above, a white edge under the deck rail
    def paint(x, y, z, zr):
        if y == DECK_Y: return WHITE
        if y >= 0: return HULL
        return DARK
    halfw = b.hull(0, HEAD_BACK + 18, CZ, 30, -7, DECK_Y, HULL, bow_len=18, stern_len=10, stern_round=True, fill_deck=DECK, flare=0.12, paint=paint)
    hw = lambda x: halfw.get(x, 0)
    for x in sorted(halfw):  # purple deck rail with purpur posts
        zr = int(round(hw(x)))
        if zr < 2 or x >= HEAD_BACK + 1: continue
        for z in (CZ - zr, CZ + zr):
            b.set(x, DECK_Y + 1, z, POST if x % 4 == 0 else RAIL)
    x0 = min(halfw); zr = int(round(hw(x0)))
    for z in range(CZ - zr, CZ + zr + 1): b.set(x0, DECK_Y + 1, z, POST if z % 4 == 0 else RAIL)
    # stores deck inside the hull
    b.box(4, -3, CZ - 10, HEAD_BACK - 2, -3, CZ + 10, "minecraft:spruce_planks")
    for x in range(6, HEAD_BACK - 4, 3):
        for z in (CZ - 8, CZ + 8):
            b.set(x, -2, z, "onepiece:sake_barrel[axis=y]" if x % 2 else BARREL)
            b.set(x + 1, -2, z, "onepiece:mikan_crate[axis=y]" if x % 4 else "onepiece:cola_crate[axis=y]")
    LD = HEAD_BACK - 6
    for y in range(-2, DECK_Y): b.set(LD, y, CZ + 4, ladder("west"))
    b.set(LD - 1, -2, CZ + 4, "minecraft:spruce_planks")
    for y in range(-1, DECK_Y): b.set(LD - 1, y, CZ + 4, "minecraft:spruce_planks")
    b.set(LD, DECK_Y, CZ + 4, trapdoor("minecraft:spruce_trapdoor", "west", "top"))

    # ---------------- the white fish head over the bow
    def head_mat(x, y, z):
        if x <= HEAD_BACK + 1: return ORANGE          # the orange collar
        if x == HEAD_BACK + 2: return GOLD
        if y <= -2: return "minecraft:light_gray_concrete"  # shade under the chin
        return WHITE
    b.shape(head_in, HEAD_BACK, -8, CZ - 13, HX + HR, 20, CZ + 13, head_mat, interior=None)
    # hollow above a floor at y 1, so the mouth leads into a little room (the "fish-mouth lounge")
    for x in range(HEAD_BACK + 1, HX + HR):
        for y in range(-8, 20):
            for z in range(CZ - 13, CZ + 14):
                if head_in(x, y, z) and all(head_in(x + d[0], y + d[1], z + d[2]) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                    b.set(x, y, z, AIR if y >= 2 else "minecraft:spruce_planks")
    # the open mouth on the front: a tunnel into the head, framed by thick rolled lips that stand out
    # one block from the face, orange with a yellow outer edge
    for y in range(-2, 19):
        for z in range(CZ - 12, CZ + 13):
            d = mouth_d(y, z)
            if d > 2.2: continue
            xf = head_front(y, z)
            if xf is None:  # beyond the head's outline: only the lip rim itself
                if d <= 1.0: continue
                xf = max((head_front(yy, zz) or 0) for yy in (y - 1, y, y + 1) for zz in (z - 1, z, z + 1)) - 1
                if xf <= 0: continue
            if d <= 1.0:
                for x in range(HX + 6, xf + 1): b.set(x, y, z, AIR)
                b.set(HX + 5, y, z, BLACK)  # the dark throat
            else:
                outer = d > 1.75
                reach = 2 if y > MOUTH_Y + 2 else 1  # the upper lip juts out further, like a beak
                for x in range(xf - 2, xf + reach + 1): b.set(x, y, z, GOLD if (outer and x >= xf) else ORANGE)
    # the mouth floor is a tongue
    for z in range(CZ - 4, CZ + 5):
        for x in range(HX + 6, HX + HR):
            yb = min((y for y in range(0, 14) if mouth_d(y, z) <= 1.0 and b.get(x, y, z) == AIR), default=None)
            if yb is not None and b.get(x, yb - 1, z) not in (None, AIR): b.set(x, yb - 1, z, "minecraft:pink_terracotta")
    # small round eyes high on both sides: black pupil, white ring, grey outline
    for side in (-1, 1):
        ex, ey = HX + 1, 14
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                r2 = dx * dx + dy * dy
                if r2 > 6: continue
                zz = CZ + side * 13
                while not head_in(ex + dx, ey + dy, zz) and zz != CZ: zz -= side
                b.set(ex + dx, ey + dy, zz, BLACK if r2 <= 1 else SNOW if r2 <= 4 else "minecraft:gray_concrete")
    # a door from the bow deck into the head
    for y in (DECK_Y + 1, DECK_Y + 2): b.set(HEAD_BACK, y, CZ, AIR); b.set(HEAD_BACK + 1, y, CZ, AIR)
    b.set(HEAD_BACK, DECK_Y + 1, CZ, door("minecraft:spruce_door", "east", "lower"))
    b.set(HEAD_BACK, DECK_Y + 2, CZ, door("minecraft:spruce_door", "east", "upper"))
    b.box(HEAD_BACK + 1, 2, CZ - 1, HEAD_BACK + 2, DECK_Y, CZ + 1, "minecraft:spruce_planks")
    for (tx, tz) in ((HEAD_BACK + 6, CZ - 4), (HEAD_BACK + 6, CZ + 4), (HX + 1, CZ)):
        b.table_set(tx, 2, tz, "spruce", "white")

    # ---------------- tall tail fin at the stern: orange slats, yellow edges, forked top
    for x in range(-12, 2):
        k = 1 - x
        top = 23 - int(abs((k - 7) / 7.0) ** 2 * 6) - (4 if 5 <= k <= 9 else 0)  # forked: dips in the middle
        top = max(top, 8)
        for y in range(-2, top + 1):
            w = 2 - min(2, k // 6)
            if k > 1 + (y + 2) * 0.55 + 2: continue  # the fin leans back as it rises
            edge = y == top or k == 1 + int((y + 2) * 0.55) + 2 or y == -2
            for z in range(CZ - 1, CZ + 2):
                if z != CZ and w < 1: continue
                b.set(x, y, z, GOLD if edge else (ORANGE if x % 2 else ORANGE2))
    b.box(-1, -1, CZ - 2, 1, DECK_Y + 2, CZ + 2, ORANGE2)

    # ---------------- the three mint tiers
    lowest, highest = {}, {}
    for ti, (g, p, y0, y1) in enumerate(TIERS):
        floor_y = y0 - 1
        for x in range(X0 - 2, X1 + 3):
            for z in range(CZ - 13, CZ + 14):
                if inside(x, z, g, p):
                    b.set(x, floor_y, z, FLOOR if ti == 0 else "minecraft:spruce_planks")
                    for y in range(y0, y1 + 1): b.set(x, y, z, AIR)
        edge = ring(g, p)
        for (x, z, f) in edge:
            for y in range(y0, y1 + 1): b.set(x, y, z, MINT)
            b.set(x, y0, z, WHITE)          # white skirting
            b.set(x, floor_y, z, WHITE)     # white floor edge = balcony fascia
    # balcony decks: the roof of each tier round the foot of the next one, with a white fascia at the edge
    for ti in (0, 1):
        g, p, y0, y1 = TIERS[ti]; gn, pn = TIERS[ti + 1][0], TIERS[ti + 1][1]
        deck_y = TIERS[ti + 1][2] - 1
        for x in range(X0 - 2, X1 + 3):
            for z in range(CZ - 13, CZ + 14):
                if inside(x, z, g, p) and not inside(x, z, gn, pn): b.set(x, deck_y, z, "minecraft:spruce_planks")
        for (x, z, f) in ring(g, p): b.set(x, deck_y, z, WHITE)
    # ceiling of the top tier
    g, p, y0, y1 = TIERS[2]
    for x in range(X0, X1 + 1):
        for z in range(CZ - 10, CZ + 11):
            if inside(x, z, g, p): b.set(x, TOP, z, "minecraft:spruce_planks")
    # second-floor attic behind the BARATIE band
    for x in range(X0, X1 + 1):
        for z in range(CZ - 10, CZ + 11):
            if inside(x, z, -2.0) and not any(e[0] == x and e[1] == z for e in ()):
                pass
    g2 = TIERS[1][0]
    for x in range(X0, X1 + 1):
        for z in range(CZ - 10, CZ + 11):
            if inside(x, z, g2 + 1): b.set(x, F2B, z, "minecraft:spruce_planks")

    # arched windows with yellow frames, rows per tier: (tier, first pane row, pane rows, spacing)
    for ti, wy, wh, every in ((0, F1 + 2, 4, 6), (1, F2 + 2, 3, 6), (2, F3 + 1, 3, 8)):
        g, p, y0, y1 = TIERS[ti]
        for (x, z, f) in ring(g, p):
            u = x if f in ("north", "south") else z
            base = int(CX) if f in ("north", "south") else CZ
            m = (u - base) % every
            if f in ("north", "south"):
                if ti == 0 and abs(x - CX) <= 3: continue   # the front doors
                if ti == 2 and abs(x - CX) <= 2: continue
            if f in ("east", "west") and abs(z - CZ) > 3: continue
            if m in (2, 3):
                for y in range(wy, wy + wh): b.set(x, y, z, BLUE)
                b.set(x, wy - 1, z, YEL); b.set(x, wy + wh, z, YEL)
            elif m in (1, 4):
                for y in range(wy, wy + wh): b.set(x, y, z, YEL)
                b.set(x, wy + wh, z, stairs(YEL_ST, "east" if (m == 1) == (f == "north") else "west", "top") if f in ("north", "south")
                      else stairs(YEL_ST, "south" if (m == 1) == (f == "east") else "north", "top"))

    # ground floor front doors (both long sides): red double doors in a yellow arch, lamps either side
    for side in (-1, 1):
        z = face_z(0.0, 4, side); f = "south" if side > 0 else "north"
        x = int(CX)
        for y in range(F1 + 1, F1 + 6):
            for xx in (x - 2, x + 2): b.set(xx, y, z, YEL)
        for xx in range(x - 1, x + 2):
            b.set(xx, F1 + 4, z, YEL); b.set(xx, F1 + 5, z, YEL)
        b.set(x, F1 + 3, z, "minecraft:red_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]")
        for xx, hinge in ((x - 1, "left" if side > 0 else "right"), (x + 1, "right" if side > 0 else "left")):
            b.set(xx, F1 + 1, z, door("minecraft:mangrove_door", f, "lower", hinge)); b.set(xx, F1 + 2, z, door("minecraft:mangrove_door", f, "upper", hinge))
            b.set(xx, F1 + 3, z, YEL)
        b.set(x, F1 + 1, z, door("minecraft:mangrove_door", f, "lower")); b.set(x, F1 + 2, z, door("minecraft:mangrove_door", f, "upper"))
        for xx in (x - 3, x + 3): b.set(xx, F1 + 3, z + side, f"onepiece:wall_lamp[facing={f}]")
        b.set(x, F1 + 6, z + side, slab("minecraft:bamboo_slab", "top"))
        for xx in range(x - 2, x + 3): b.set(xx, F1 + 6, z + side, slab("minecraft:bamboo_slab", "top"))
    # bow end door onto the foredeck
    for y in (F1 + 1, F1 + 2): b.set(X1, y, CZ, AIR)
    b.set(X1, F1 + 1, CZ, door("minecraft:mangrove_door", "west", "lower")); b.set(X1, F1 + 2, CZ, door("minecraft:mangrove_door", "west", "upper"))
    for z in (CZ - 1, CZ + 1): b.column(X1, z, F1 + 1, F1 + 3, YEL)
    b.set(X1, F1 + 3, CZ, YEL)

    # balconies: purple rails on the roof edge of the tier below, posts every 4, lanterns on some posts
    for ti in (1, 2):
        g, p, y0, y1 = TIERS[ti - 1]
        ry = TIERS[ti][2]  # rail sits on the floor level of the tier above
        for (x, z, f) in ring(g, p):
            if inside(x, z, TIERS[ti][0], TIERS[ti][1]): continue
            b.set(x, ry, z, POST if (x + z) % 4 == 0 else RAIL)
            if (x + z) % 8 == 0: b.set(x, ry + 1, z, LANTERN)
    # balcony doors on the second and top floors
    for ti, xs in ((1, (int(CX) - 14, int(CX) + 14)), (2, (int(CX),))):
        g, p, y0, y1 = TIERS[ti]
        for side in (-1, 1):
            z = face_z(g, p, side); f = "south" if side > 0 else "north"
            for x in xs:
                b.set(x, y0, z, door("minecraft:mangrove_door", f, "lower")); b.set(x, y0 + 1, z, door("minecraft:mangrove_door", f, "upper"))
                b.set(x - 1, y0, z, YEL); b.set(x + 1, y0, z, YEL); b.set(x - 1, y0 + 1, z, YEL); b.set(x + 1, y0 + 1, z, YEL)
                b.set(x - 1, y0 + 2, z, YEL); b.set(x, y0 + 2, z, YEL); b.set(x + 1, y0 + 2, z, YEL)
                if ti == 2:  # the lit frame round the top-floor door
                    b.set(x - 1, y0 + 1, z + side, f"onepiece:wall_lamp[facing={f}]"); b.set(x + 1, y0 + 1, z + side, f"onepiece:wall_lamp[facing={f}]")

    # the white BARATIE band on the second floor with life rings either side
    g, p, y0, y1 = TIERS[1]
    for (x, z, f) in ring(g, p):
        for y in range(F2B, y1 + 1): b.set(x, y, z, WHITE)
    for side in (-1, 1):
        z = face_z(g, p, side)
        face_text(b, CX, F2B + 1, z, "BARATIE", "minecraft:brown_concrete", side)
        for xr in (int(CX) - 18, int(CX) + 18):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0: continue
                    b.set(xr + dx, F2B + 3 + dy, z + side, "minecraft:red_concrete" if (dx == 0 or dy == 0) else SNOW)
    # RESTAURANT across the top floor, the scalloped yellow-and-white awning above it
    g, p, y0, y1 = TIERS[2]
    for side in (-1, 1):
        z = face_z(g, p, side)
        face_text(b, CX, y1 - 5, z, "RESTAURANT", "minecraft:brown_concrete", side)
        for (x, zz, f) in ring(g, p):
            if zz != z: continue
            b.set(x, y1, z + side, SNOW if (x // 2) % 2 else GOLD)
            if (x % 4) in (1, 2): b.set(x, y1 - 1, z + side, SNOW if (x // 2) % 2 else GOLD)

    # ---------------- roof: orange-red tiled hip roof over the top floor, eave brackets, a green cupola
    xs = [x for (x, z, f) in ring(g, p)]; zs = [z for (x, z, f) in ring(g, p)]
    rx0, rx1, rz0, rz1 = min(xs), max(xs), min(zs), max(zs)
    b.hip_roof(rx0, rz0, rx1, rz1, TOP + 1, ROOF_ST, ROOF, overhang=1)
    for x in range(rx0 - 1, rx1 + 2, 2):
        b.set(x, TOP, rz0 - 1, stairs("minecraft:dark_oak_stairs", "south", "top")); b.set(x, TOP, rz1 + 1, stairs("minecraft:dark_oak_stairs", "north", "top"))
    for z in range(rz0, rz1 + 1):
        for x in range(rx0, rx1 + 1):
            if not inside(x, z, g, p) and b.get(x, TOP, z) in (None, AIR): b.set(x, TOP, z, "minecraft:spruce_planks")
    ridge = TOP + 1 + (rz1 - rz0 + 2) // 2
    cx0 = rx0 + 8
    b.box(cx0, ridge - 1, CZ - 2, cx0 + 4, ridge + 3, CZ + 2, MINT)
    b.box(cx0 + 1, ridge, CZ - 1, cx0 + 3, ridge + 2, CZ + 1, AIR)
    for z in (CZ - 2, CZ + 2): b.set(cx0 + 2, ridge + 1, z, BLUE)
    b.box(cx0 - 1, ridge + 4, CZ - 3, cx0 + 5, ridge + 4, CZ + 3, slab("minecraft:dark_oak_slab", "bottom"))
    b.box(cx0, ridge + 4, CZ - 2, cx0 + 4, ridge + 4, CZ + 2, ROOF)

    # ---------------- masts: green, round tops, swag sails in yellow and white stripes, red BT flags
    for mx, yards in ((X0 + 9, ((50, 14), (59, 11))), (X1 - 9, ((54, 16), (63, 13)))):  # the bow mast is the taller
        mh = yards[-1][0] + 5
        for y in range(F1 + 1, mh + 1): b.set(mx, y, CZ, MAST)
        for (yy, half) in yards:
            for x in range(mx - half, mx + half + 1): b.set(x, yy, CZ + 1, log("spruce", "x"))
            b.disk(mx, yy + 1, CZ, 2, "minecraft:spruce_planks")  # the round top over each yard
            for i in range(0, 360, 30):
                a = math.radians(i); b.set(round(mx + 2 * math.cos(a)), yy + 2, round(CZ + 2 * math.sin(a)), "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
            b.set(mx, yy + 1, CZ, MAST)
            # swags: four scallops hanging from the yard, deepest in the middle of each
            n = 4; span = 2 * half + 1
            for x in range(mx - half, mx + half + 1):
                s = ((x - (mx - half)) * n / span) % 1.0
                depth = 1 + int(round(4.5 * math.sin(math.pi * s)))
                col = GOLD.replace("concrete", "wool") if ((x - mx) // 2) % 2 == 0 else "minecraft:white_wool"
                for d in range(1, depth + 1): b.set(x, yy - d, CZ + 1, col)
        # the BT flag: red with white letters, on a pole over the mast
        for y in range(mh + 1, mh + 10): b.set(mx, y, CZ, fence("dark_oak"))
        b.box(mx + 1, mh + 3, CZ - 1, mx + 11, mh + 9, CZ, "minecraft:red_wool")  # two layers, so BT reads right from both sides
        b.text(mx + 3, mh + 4, CZ, "BT", "minecraft:white_wool", axis="x", step=1)
        b.text(mx + 9, mh + 4, CZ - 1, "BT", "minecraft:white_wool", axis="x", step=-1)
        # rope-ladder shrouds from the lower top down to the roof eaves on both sides (never through a wall)
        ylow = yards[0][0]
        for side in (-1, 1):
            for dx in (-1, 1):
                (ax, ay, az), (bx, by, bz) = (mx + dx, ylow - 1, CZ + side * 2), (mx + dx, TOP, CZ + side * 9)
                n = max(abs(ay - by), abs(az - bz)) + 1
                for i in range(n + 1):
                    t = i / n
                    q = (ax, round(ay + (by - ay) * t), round(az + (bz - az) * t))
                    if b.get(*q) in (None, AIR): b.set(*q, fence("dark_oak"))
                    elif i > 2: break
        # ladders up the mast inside the rooms
        for yy in range(F1 + 1, ylow):
            if b.get(mx - 1, yy, CZ) in (None, AIR): b.set(mx - 1, yy, CZ, ladder("west"))

    # ---------------- deck dressing
    b.box(1, DECK_Y + 1, CZ - 3, 4, DECK_Y + 1, CZ + 3, "minecraft:spruce_planks")
    b.set(3, DECK_Y + 2, CZ, "onepiece:ships_wheel[facing=east]")
    b.set(1, DECK_Y + 2, CZ - 2, "onepiece:rope_coil[facing=east]"); b.set(1, DECK_Y + 2, CZ + 2, "onepiece:rope_coil[facing=east]")
    for x in range(9, HEAD_BACK - 4, 7):
        for side in (-1, 1):
            z = CZ + side * (int(hw(x)) - 1)
            if not inside(x, z, 1.0): b.set(x, DECK_Y + 1, z, BARREL if x % 2 else "onepiece:rope_coil[facing=north]")
    for x in range(4, HEAD_BACK, 8):
        for side in (-1, 1):
            z = CZ + side * int(round(hw(x)))
            if hw(x) > 3: b.set(x, DECK_Y + 2, z, LANTERN)
    b.set(HEAD_BACK - 2, DECK_Y + 1, CZ - 9, "onepiece:anchor[facing=east]"); b.set(HEAD_BACK - 2, DECK_Y + 1, CZ + 9, "onepiece:anchor[facing=east]")
    for x in (24, 50):  # life rings on the hull sides
        for side in (-1, 1):
            z = CZ + side * int(round(hw(x)))
            b.set(x, 1, z, "minecraft:red_concrete"); b.set(x, 0, z, SNOW)

    # ---------------- ground floor: kitchen (stern end) + the dining hall
    KX = X0 + 12
    for z in range(CZ - 9, CZ + 10):
        if inside(KX, z):
            for y in range(F1 + 1, F2): b.set(KX, y, z, "minecraft:spruce_planks")
    for z in (CZ - 1, CZ, CZ + 1):
        for y in (F1 + 1, F1 + 2): b.set(KX, y, z, AIR)
    for z in range(CZ - 6, CZ + 7):
        if z % 2: b.set(X0 + 4, F1 + 1, z, "minecraft:smoker[facing=east,lit=true]" if z % 4 == 1 else "minecraft:furnace[facing=east,lit=true]")
        else: b.set(X0 + 4, F1 + 1, z, "onepiece:ships_galley[facing=east]" if z % 4 == 0 else "minecraft:blast_furnace[facing=east,lit=false]")
        b.set(X0 + 4, F1 + 2, z, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
    for x in range(X0 + 6, X0 + 11):  # prep islands
        for z in (CZ - 4, CZ + 4):
            b.set(x, F1 + 1, z, BARREL if x % 2 else "minecraft:cauldron")
            b.set(x, F1 + 2, z, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]" if x % 2 else AIR)
    b.set(X0 + 6, F1 + 1, CZ - 7, "minecraft:crafting_table"); b.set(X0 + 8, F1 + 1, CZ - 7, "minecraft:water_cauldron[level=3]")
    b.chest(X0 + 6, F1 + 1, CZ + 7, "galley", "north")
    b.set(X0 + 7, F1 + 1, CZ + 7, BARREL)
    for x in range(KX + 1, X1): b.set(x, F1 + 1, CZ, "minecraft:red_carpet")
    for tx in range(KX + 4, X1 - 4, 5):
        if abs(tx - CX) <= 1: continue
        for tz in (CZ - 6, CZ - 3, CZ + 3, CZ + 6):
            b.table_set(tx, F1 + 1, tz, "dark_oak", "white")
    for z in range(CZ - 6, CZ - 2):  # the bar by the bow door
        b.set(X1 - 4, F1 + 1, z, "minecraft:dark_oak_planks"); b.set(X1 - 4, F1 + 2, z, slab("minecraft:polished_andesite_slab"))
        b.set(X1 - 3, F1 + 1, z, BARREL)
    for z in range(CZ + 3, CZ + 7):
        b.set(X1 - 4, F1 + 1, z, "minecraft:jukebox" if z == CZ + 4 else "minecraft:note_block[instrument=harp,note=0,powered=false]" if z == CZ + 5 else "minecraft:dark_oak_planks")
    # stairs to the second floor along the inside of the south wall, climbing west
    b.stairs_up(KX + 10, F1 + 1, CZ + 6, 8, "minecraft:spruce_stairs", "west", w=1)
    for x in range(KX + 3, KX + 11): b.set(x, F2 + 1, CZ + 5, fence("spruce"))
    b.set(KX + 2, F2, CZ + 6, "minecraft:spruce_planks")
    b.npc(int(CX) + 6, F1 + 1, CZ, "sanji")

    # ---------------- second floor: private dining room + Zeff's office; ladder to the attic and the top floor
    LX = int(CX) - 3
    for y in range(F2 + 1, F3): b.set(LX - 1, y, CZ, "minecraft:spruce_planks")
    for y in range(F2 + 1, F3): b.set(LX, y, CZ, ladder("east"))
    b.set(LX, F2B, CZ, ladder("east")); b.set(LX, F3, CZ, trapdoor("minecraft:spruce_trapdoor", "east", "top"))
    b.box(int(CX) + 6, F2 + 1, CZ - 7, int(CX) + 6, F2B - 1, CZ + 7, "minecraft:spruce_planks")  # office wall
    b.set(int(CX) + 6, F2 + 1, CZ - 2, door("minecraft:spruce_door", "east", "lower")); b.set(int(CX) + 6, F2 + 2, CZ - 2, door("minecraft:spruce_door", "east", "upper"))
    b.box(int(CX) + 10, F2 + 1, CZ + 6, int(CX) + 16, F2 + 3, CZ + 6, "minecraft:bookshelf")
    b.set(int(CX) + 12, F2 + 1, CZ + 3, "minecraft:lectern[facing=north,has_book=false,powered=false]")
    b.table_set(int(CX) + 14, F2 + 1, CZ, "dark_oak", "red")
    b.set(int(CX) + 15, F2 + 1, CZ - 5, "minecraft:cartography_table")

    # ---------------- furnished rooms (the interiors kit fills only the empty spots)
    I.furnish(b, X0 + 3, F1 + 1, CZ - 7, KX - 1, CZ + 7, F2 - F1 - 1, "kitchen", "pirate")
    r = I.Room(b, KX + 1, F1 + 1, CZ - 7, X1 - 3, CZ + 7, F2 - F1 - 1, "royal", random.Random(3))
    r.paintings(5); r.plants(4); r.wall_banners(7)
    I.furnish(b, X0 + 6, F2 + 1, CZ - 6, int(CX) + 5, CZ + 4, F2B - F2 - 1, "dining", "royal")
    I.furnish(b, int(CX) + 7, F2 + 1, CZ - 6, X1 - 6, CZ + 6, F2B - F2 - 1, "study", "pirate")
    I.furnish(b, X0 + 6, F2B + 1, CZ - 6, int(CX) - 5, CZ + 6, F3 - F2B - 1, "barracks", "pirate")
    I.furnish(b, int(CX) - 1, F2B + 1, CZ - 6, X1 - 6, CZ + 6, F3 - F2B - 1, "storage", "pirate")
    I.furnish(b, X0 + 8, F3 + 1, CZ - 4, int(CX) - 3, CZ + 4, TOP - F3 - 1, "captain", "pirate")
    I.furnish(b, int(CX) + 3, F3 + 1, CZ - 4, X1 - 8, CZ + 4, TOP - F3 - 1, "bedroom", "pirate")
    I.furnish(b, 8, -2, CZ - 6, HEAD_BACK - 10, CZ + 6, 4, "storage", "pirate")
    return b, 0  # ground_y = water surface
