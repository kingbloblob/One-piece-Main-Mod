"""The Going Merry's farewell off the coast past Enies Lobby: the beloved little caravel, life size (~36 m), lying
on the calm sea and burning in her Viking funeral, her ram's-head figurehead still smiling. On the shore the crew's
farewell spot: a stone beach with a memorial cairn, a bench to watch from, Usopp's toolbox, flowers, and a lantern
for every crew mate.

What the show has, and where it is here:
- a light-brown planked caravel hull with white railings and white curled trim along the top of the sides (the
  "sheep's wool" decoration);
- the big white sheep's head figurehead on a white neck over the bow: a round woolly head with a smiling face,
  black dot eyes and light, curled ram's horns on both sides;
- a raised forecastle behind the figurehead, a low main deck, and a raised quarterdeck at the stern over the cabin
  (the galley and lounge), reached by two staircases either side of the cabin door; the stern has a row of windows
  and the rudder;
- Nami's three mikan (tangerine) trees on the quarterdeck;
- one main mast with a white square main sail painted with the black Straw Hat Jolly Roger, a topsail, a crow's
  nest, and the black Straw Hat flag (white skull wearing a yellow straw hat with a red band) at the masthead;
- the funeral fire burning all over her decks, and the crack amidships where her keel gave out.
Ground = y 0, the sea to the south. Bow points +x."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "going_merry_farewell"
TITLE = "Going Merry's Farewell"
CUTS = [2, 5]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 64, 70
SEA_Z = 30
CZ = 50
MERRY = dict(wood="oak", rug="orange", rug2="white", bed="white", light="minecraft:lantern", accent="minecraft:white_wool",
             banner="black", candle="orange")

PLANK = "minecraft:oak_planks"
DARKP = "minecraft:spruce_planks"
WHITE = "minecraft:smooth_quartz"
WHITE_ST = "minecraft:smooth_quartz_stairs"
WHITE_SL = "minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]"
RAIL = fence("pale_oak")          # the white railings
WOOL = "minecraft:white_wool"     # the sheep's fleece
FACE = "minecraft:white_concrete"
HORN = "minecraft:smooth_sandstone"
BLACK = "minecraft:black_concrete"
DECKP = "minecraft:oak_planks"
CHAR = ("minecraft:coal_block", "minecraft:blackstone", "minecraft:polished_blackstone")

HX, HL = 12, 36                   # stern x, hull length (bow tip near x 47)
BEAM = 12
DECK = 3                          # main deck
QD = 7                            # quarterdeck over the stern cabin
QX = HX + 9                       # front wall of the stern cabin
FD = 5                            # forecastle deck
MASTX = HX + 19                   # main mast

# the Straw Hat Jolly Roger: Y straw hat, R hat band, W bone/skull, K eye sockets, . background
JOLLY = ["....YYY....",
         "...YRRRY...",
         ".YYYYYYYYY.",
         "W..WWWWW..W",
         ".W.WKWKW.W.",
         "..WWWWWWW..",
         "...WW.WW...",
         ".W..WWW..W.",
         "W.........W"]


def build():
    rnd = random.Random(801)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.1)
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z + 2 * math.sin(x * 0.18), depth=7)
    for x in range(NX):
        for z in range(NZ):
            s = SEA_Z + 2 * math.sin(x * 0.18)
            if s - 8 < z <= s: b.set(x, 0, z, "minecraft:gravel" if rnd.random() < 0.5 else "minecraft:stone"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None

    # ---------------- the Going Merry: hull
    FX = HX + HL - 9              # aft edge of the forecastle

    def top_of(x):
        return QD if x <= QX else FD if x >= FX else DECK

    def side_mat(x, y):
        """Light-brown planking with the white curled trim along the top of the side."""
        t = top_of(x)
        if y == t: return WHITE if x % 4 != 3 else PLANK
        if y == t - 1 and x % 4 == 1: return WHITE
        return PLANK

    def paint(x, y, z, zr):
        if y <= -1: return DARKP
        if abs(z - CZ) >= zr: return side_mat(x, y)
        return PLANK

    b.hull(HX, HL, CZ, BEAM, -4, DECK, PLANK, bow_len=13, stern_len=5, fill_deck=DECKP, paint=paint)

    def half(x):
        k = 0
        while b.get(x, DECK, CZ + k + 1) not in (None, AIR) and k < BEAM: k += 1
        return k
    xs = [x for x in range(HX, HX + HL) if b.get(x, DECK, CZ) not in (None, AIR)]
    BOW = max(xs)
    for x in xs:  # deck planks run fore and aft, with a log seam every 3 blocks
        zr = half(x)
        for z in range(CZ - zr + 1, CZ + zr):
            b.set(x, DECK, z, DECKP if (z - CZ) % 3 else "minecraft:stripped_oak_log[axis=x]")

    # ---------------- raised stern: side walls up to the quarterdeck, the cabin inside, the transom
    for x in range(HX, QX + 1):
        zr = half(x)
        for y in range(DECK + 1, QD + 1):
            for z in (CZ - zr, CZ + zr): b.set(x, y, z, side_mat(x, y))
        for z in range(CZ - zr + 1, CZ + zr):
            b.set(x, QD, z, DECKP)
            for y in range(DECK + 1, QD): b.set(x, y, z, AIR)
    zs = half(HX)
    for z in range(CZ - zs, CZ + zs + 1):
        for y in range(DECK + 1, QD + 1): b.set(HX, y, z, side_mat(HX, y) if abs(z - CZ) == zs or y == QD else PLANK)
    for z in range(CZ - zs, CZ + zs + 1):  # moulding under the stern windows
        b.set(HX - 1, 4, z, stairs("minecraft:oak_stairs", "west", "top"))
    for z in (CZ - 2, CZ, CZ + 2):  # stern windows of the galley, white sills
        b.set(HX, 5, z, pane("white"))
        b.set(HX - 1, 4, z, stairs(WHITE_ST, "west", "top"))
    for y in range(-3, QD): b.set(HX - 1, y, CZ, "minecraft:stripped_spruce_log[axis=y]")  # the rudder
    b.set(HX - 2, -1, CZ, DARKP); b.set(HX - 2, 0, CZ, DARKP)
    # cabin front wall: white corner posts, a door in the middle and a window either side
    zq = half(QX)
    for z in range(CZ - zq + 1, CZ + zq):
        for y in range(DECK + 1, QD): b.set(QX, y, z, PLANK)
        b.set(QX + 1, QD, z, stairs(WHITE_ST, "east", "top"))  # white cornice under the quarterdeck edge
    for y in range(DECK + 1, QD): b.set(QX, y, CZ - zq + 1, WHITE); b.set(QX, y, CZ + zq - 1, WHITE)
    b.set(QX, DECK + 1, CZ, door("minecraft:oak_door", "east", "lower")); b.set(QX, DECK + 2, CZ, door("minecraft:oak_door", "east", "upper"))
    for z in (CZ - 2, CZ + 2):
        b.set(QX, 5, z, pane("white")); b.set(QX + 1, 4, z, stairs(WHITE_ST, "east", "top"))
    # two staircases from the main deck up to the quarterdeck, either side of the cabin door
    for sz in (CZ - zq + 1, CZ + zq - 1):
        for (sx, sy) in ((QX + 3, 4), (QX + 2, 5), (QX + 1, 6)):
            b.set(sx, sy, sz, stairs("minecraft:oak_stairs", "west"))
            for y in range(DECK + 1, sy): b.set(sx, y, sz, PLANK)
            for y in range(sy + 1, sy + 4): b.set(sx, y, sz, AIR)
    # quarterdeck rails (white), open where the stairs arrive
    for x in range(HX, QX + 1):
        zr = half(x)
        b.set(x, QD + 1, CZ - zr, RAIL); b.set(x, QD + 1, CZ + zr, RAIL)
    for z in range(CZ - zs, CZ + zs + 1): b.set(HX, QD + 1, z, RAIL)
    for z in range(CZ - zq + 2, CZ + zq - 1): b.set(QX, QD + 1, z, RAIL)
    # Nami's three mikan trees in planters on the quarterdeck
    for (tx, tz) in ((HX + 3, CZ - 2), (HX + 3, CZ + 2), (HX + 6, CZ)):
        b.set(tx, QD + 1, tz, "minecraft:rooted_dirt")
        for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            b.set(tx + dx, QD + 1, tz + dz, trapdoor("minecraft:oak_trapdoor", f, "bottom", "true"))
        b.column(tx, tz, QD + 2, QD + 3, "minecraft:oak_log[axis=y]")
        for dy in (0, 1, 2):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dy != 1 and abs(dx) + abs(dz) > 1: continue
                    if dy == 0 and dx == 0 and dz == 0: continue
                    fruit = dy == 1 and abs(dx) + abs(dz) == 2 and (dx + dz + tx) % 2 == 0 or dy == 0 and (dx + 2 * dz + tz) % 3 == 0
                    b.set(tx + dx, QD + 3 + dy, tz + dz, "minecraft:orange_concrete" if fruit else leaves("oak"))

    # ---------------- raised forecastle behind the figurehead, one step up from the main deck
    for x in range(FX, BOW + 1):
        zr = half(x)
        for z in range(CZ - zr, CZ + zr + 1):
            for y in range(DECK + 1, FD + 1):
                b.set(x, y, z, side_mat(x, y) if abs(z - CZ) == zr else DECKP if y == FD else PLANK)
        b.set(x, FD + 1, CZ - zr, RAIL); b.set(x, FD + 1, CZ + zr, RAIL)
    zf = half(FX)
    for z in range(CZ - zf + 1, CZ + zf):
        if abs(z - CZ) <= 1: b.set(FX - 1, DECK + 1, z, stairs("minecraft:oak_stairs", "east"))
        else: b.set(FX, FD + 1, z, RAIL)
    for z in (CZ - 2, CZ + 2): b.set(FX, FD + 1, z, WHITE); b.set(FX, FD + 2, z, WHITE_SL)
    # the waist: white railings along the main deck, with white posts
    for x in range(QX + 1, FX):
        zr = half(x)
        b.set(x, DECK + 1, CZ - zr, RAIL); b.set(x, DECK + 1, CZ + zr, RAIL)
    for x in range(QX + 4, FX - 1, 5):
        zr = half(x)
        for z in (CZ - zr, CZ + zr): b.set(x, DECK + 1, z, WHITE); b.set(x, DECK + 2, z, WHITE_SL)

    # ---------------- the sheep's head figurehead on its white neck over the bow
    HCX, HCY = BOW + 2, 10        # centre of the woolly head
    for x in range(BOW - 1, BOW + 3):  # cutwater (stem) sweeping forward from the water up to the neck
        for y in range(-1, FD + 1):
            if x - BOW <= (y + 1) * 0.45: b.set(x, y, CZ, PLANK if y < FD - 1 else WHITE)
    for y in range(FD, HCY - 1):  # the neck
        for dz in (-1, 0, 1):
            b.set(BOW + 1, y, CZ + dz, WOOL)
            if dz == 0 or y > FD + 1: b.set(BOW + 2, y, CZ + dz, WOOL)
        b.set(BOW, y, CZ, WOOL)

    def head_in(x, y, z):
        bump = 0.16 if y >= HCY and (x * 7 + y * 3 + z * 5) % 3 == 0 else 0.0  # curly fleece on the crown
        cran = ((x - HCX) / 3.4) ** 2 + ((y - HCY) / 3.4) ** 2 + ((z - CZ) / 3.5) ** 2 <= 1.0 + bump
        snout = ((x - HCX - 2.9) / 2.4) ** 2 + ((y - HCY + 1.5) / 2.1) ** 2 + ((z - CZ) / 2.5) ** 2 <= 1.0
        return cran or snout
    b.shape(head_in, HCX - 5, HCY - 5, CZ - 5, HCX + 7, HCY + 5, CZ + 5,
            lambda x, y, z: FACE if x >= HCX + 2 and y <= HCY else WOOL, interior=WOOL)

    def front(y, z):
        for x in range(HCX + 8, HCX - 6, -1):
            if head_in(x, y, z): return x
        return None
    for dz in (-2, 2):  # round black eyes just above the muzzle
        xf = front(HCY + 1, CZ + dz)
        if xf: b.set(xf, HCY + 1, CZ + dz, BLACK)
    for (dy, dz) in ((-3, -1), (-3, 0), (-3, 1), (-2, -2), (-2, 2)):  # the smile
        xf = front(HCY + dy, CZ + dz)
        if xf: b.set(xf, HCY + dy, CZ + dz, "minecraft:gray_concrete")
    # curled ram's horns on both sides: a spiral from the crown, back, down, forward and in, round the ear
    for side in (-1, 1):
        for i in range(160):
            t = i / 159
            ang = math.pi * 0.5 + t * math.pi * 2.7
            r = 3.0 - 2.5 * t
            x, y = round(HCX - 1.4 + r * math.cos(ang)), round(HCY + 0.3 + r * math.sin(ang))
            b.set(x, y, CZ + side * 4, HORN)
            if not head_in(x, y, CZ + side * 3): b.set(x, y, CZ + side * 3, HORN)

    # ---------------- the main mast with its sails, crow's nest and the Straw Hat flag
    MTOP = 32
    b.mast(MASTX, CZ, DECK + 1, MTOP - DECK, wood="oak", nest_y=27)
    for z in range(CZ - 1, CZ + 2):  # mast step
        b.set(MASTX - 1, DECK + 1, z, stairs("minecraft:oak_stairs", "east")); b.set(MASTX + 1, DECK + 1, z, stairs("minecraft:oak_stairs", "west"))

    def sail(y0, y1, halfw, emblem):
        x0 = MASTX + 1
        rows, cols = len(JOLLY), len(JOLLY[0])
        for y in range(y0, y1 + 1):
            for z in range(CZ - halfw, CZ + halfw + 1):
                t = 1 - abs(z - CZ) / (halfw + 1)
                v = math.sin((y - y0) / max(1, y1 - y0) * math.pi)
                bx = int(round(1.4 * t * v))
                blk = WOOL
                if emblem:
                    r = (y1 - 1) - y; c = z - (CZ - cols // 2)
                    if 0 <= r < rows and 0 <= c < cols and JOLLY[r][c] in "YRW": blk = "minecraft:black_wool"
                if y == y0 and rnd.random() < 0.45: blk = rnd.choice(("minecraft:gray_wool", "minecraft:black_wool", "minecraft:light_gray_wool"))  # scorched hem
                for k in range(0, bx + 1): b.set(x0 + k, y, z, blk)
        for z in range(CZ - halfw - 1, CZ + halfw + 2): b.set(x0, y1 + 1, z, "minecraft:stripped_oak_log[axis=z]")
    sail(9, 19, 7, True)
    sail(22, 25, 4, False)
    # the black Straw Hat flag on a pole above the masthead, flying aft
    FTOP = MTOP + 6
    for y in range(MTOP + 1, FTOP + 1): b.set(MASTX, y, CZ, fence("oak"))
    cols = {"Y": "minecraft:yellow_wool", "R": "minecraft:red_wool", "W": WOOL, "K": "minecraft:black_wool", ".": "minecraft:black_wool"}
    for r, row in enumerate(JOLLY):
        for c, ch in enumerate(row):
            b.set(MASTX - 1 - c, FTOP - r, CZ, cols[ch])

    # ---------------- the crack where the keel gave out, scorched planks, and the funeral fire
    CRACK = HX + 15
    for z in range(CZ - BEAM // 2 - 1, CZ + BEAM // 2 + 2):
        x = CRACK + (z * 7) % 3 - 1
        for y in range(-1, DECK + 1):
            s = b.get(x, y, z)
            if s in (None, AIR) or "water" in s: continue
            if y == DECK and abs(z - CZ) < half(x) - 1 and rnd.random() < 0.5: b.set(x, y, z, AIR)
            else: b.set(x, y, z, rnd.choice(CHAR))
    for k, v in list(b.blocks.items()):
        x, y, z = k
        if not (HX <= x <= BOW and abs(z - CZ) <= BEAM // 2 + 1 and 0 <= y <= QD): continue
        if ("planks" in v or "quartz" in v) and "stairs" not in v and rnd.random() < 0.07:
            b.blocks[k] = rnd.choice(CHAR + ("minecraft:magma_block",))
    fires = 0
    for i in range(600):
        x, z = rnd.randint(HX + 1, BOW - 1), rnd.randint(CZ - 4, CZ + 4)
        for y in (QD, FD, DECK):
            s = b.get(x, y, z)
            if s in (None, AIR): continue
            if any(k in s for k in ("planks", "_log", "blackstone", "coal_block")) and "stairs" not in s \
                    and b.get(x, y + 1, z) in (None, AIR) and b.get(x, y + 2, z) in (None, AIR):
                b.set(x, y + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]" if fires % 3 else "minecraft:magma_block")
                fires += 1
            break
        if fires >= 28: break

    # stern cabin: the galley and lounge
    zi = half(HX + 1) - 1
    I.furnish(b, HX + 1, DECK + 1, CZ - zi, QX - 1, CZ + zi, 3, "kitchen", MERRY)

    # ---------------- the farewell spot on the shore
    MX, MZ = 32, 14
    for (dx, dz, h) in ((0, 0, 4), (1, 0, 3), (-1, 0, 3), (0, 1, 2), (0, -1, 3)): b.column(MX + dx, MZ + dz, 1, h, "minecraft:cobblestone" if h % 2 else "minecraft:mossy_cobblestone")
    b.set(MX, 5, MZ, "minecraft:white_wool"); b.set(MX, 6, MZ, "minecraft:yellow_carpet")
    for x in range(MX - 3, MX + 4): b.set(x, 1, MZ + 4, "minecraft:oak_slab[type=bottom,waterlogged=false]")
    b.set(MX - 4, 1, MZ + 4, "minecraft:oak_fence"); b.set(MX + 4, 1, MZ + 4, "minecraft:oak_fence")
    for k, x in enumerate(range(MX - 12, MX + 13, 3)):  # a lantern for every crew mate
        b.set(x, 1, MZ + 8, "minecraft:oak_fence"); b.set(x, 2, MZ + 8, lantern())
    for (x, z) in ((MX - 2, MZ - 2), (MX + 2, MZ - 2), (MX + 3, MZ + 1), (MX - 3, MZ + 1)):
        b.set(x, 1, z, rnd.choice(("minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy")))
    b.set(MX + 6, 1, MZ + 3, "minecraft:barrel[facing=up,open=false]"); b.set(MX + 7, 1, MZ + 3, "minecraft:smithing_table")
    # ---------------- loot
    b.chest(HX + 3, DECK + 1, CZ + 1, "easy", "east"); b.chest(MX + 6, 1, MZ + 2, "easy", "south")
    return b, 0
