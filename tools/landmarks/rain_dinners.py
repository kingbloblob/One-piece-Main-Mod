"""Rain Dinners in Rainbase: Crocodile's casino. The golden sandstone pyramid of gambling (the show's design follows the
Luxor in Las Vegas) standing on an island in the oasis lake, with the giant Bananawani statue sprawled over its top:
banana crest on its head, jaws open over the entrance. A causeway bridge crosses the lake to the portico under the
RAIN DINNERS sign. Inside: the casino floor (slots, roulette and card tables, the bar), the VIP stair, Crocodile's
office and the Baroque Works meeting room, the vault, and below the lake the seastone cage room with glass walls where
the Bananawani swim. Around it, Rainbase: flat-roofed desert houses. ~124 x 124. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import alubarna as AL

SID = "rain_dinners"
TITLE = "Rain Dinners (Rainbase)"
CUTS = [5, -6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 124
CX, CZ = 60, 52
SAND, SAND_ST, TILE, GOLD = AL.SAND, AL.SAND_ST, AL.TILE, "minecraft:gold_block"
CUT = "minecraft:cut_sandstone"
CROC = "minecraft:green_concrete"
CROC2 = "minecraft:lime_concrete"
SEA = "onepiece:seastone_bricks"
P0 = 28           # half width of the pyramid at its foot
PTOP = 34         # flat top the crocodile lies on
MOAT = (32, 38)   # inner / outer radius of the moat (rounded square)
LX, LZ, LR = CX, CZ + 50, 17   # the oasis lake south of the casino


def H(y):
    """Half width of the pyramid at height y (3 up for every 2 in, about the Luxor's slope)."""
    return P0 - ((y - 1) * 2) // 3


def surf(x, z):
    """Top of the pyramid at column (x, z), 0 off the pyramid."""
    d = max(abs(x - CX), abs(z - CZ))
    if d > P0: return 0
    y = 1
    while y < PTOP and H(y + 1) >= d: y += 1
    return y


def in_moat(x, z):
    dx, dz = abs(x - CX), abs(z - CZ)
    se = (dx ** 8 + dz ** 8) ** 0.125
    return MOAT[0] <= se <= MOAT[1]


def in_lake(x, z):
    return math.hypot((x - LX) * 0.85, (z - LZ) * 1.2) < LR


def in_pool(x, z):
    """The deep water round the glass walls of the cage room, part of the lake."""
    return ((x - CX) / 15.5) ** 2 + ((z - CZ - 42) / 11.5) ** 2 <= 1.0


def wet(x, z):
    return in_moat(x, z) or in_lake(x, z) or in_pool(x, z)


def crocodile(b, top):
    """The Bananawani statue: tail curling down the north face, body over the top, legs gripping the slopes and the
    head raised over the south face with open jaws, golden eyes and the yellow banana on its head."""
    zt, zs = CZ - 26, CZ + 23
    S = 220
    for i in range(S + 1):  # tail, body and neck as one tapered tube lying on the pyramid
        s = i / S * 0.8
        z = zt + (zs - zt) * s
        if s < 0.38:
            u = (0.38 - s) / 0.38
            x = CX + 6.0 * math.sin(u * math.pi * 1.25) * u
            w = 1.0 + 6.0 * (s / 0.38) ** 0.85
        elif s < 0.72:
            x = CX; w = 7.0 + 0.6 * math.sin((s - 0.38) / 0.34 * math.pi)
        else:
            x = CX; w = 7.0 - (s - 0.72) / 0.08 * 2.0
        h = 0.72 * w
        belly = surf(round(x), round(z)) + 1 if s < 0.72 else round(top + 1 - (s - 0.72) / 0.08 * 3)
        zc = round(z)
        for dx in range(-int(w), int(w) + 1):
            px = round(x) + dx
            t = math.sqrt(max(0.0, 1 - (dx / max(w, 1)) ** 2))
            yt = belly + int(round(h * t))
            y0 = min(yt, max(surf(px, zc) + 1, belly - 8)) if s < 0.72 else belly
            for y in range(y0, yt + 1):
                b.set(px, y, zc, CROC2 if (abs(dx) >= w - 0.6 and y <= belly + 1) else CROC)
        if i % 5 == 0 and s < 0.74:  # ridge scales along the back
            b.set(round(x), belly + int(round(h)) + 1, zc, "minecraft:dark_prismarine")
            if 0.3 < s < 0.72:
                for dx in (-2, 2): b.set(round(x) + dx, belly + int(round(h * math.sqrt(1 - (2 / w) ** 2))) + 1, zc, "minecraft:dark_prismarine")
    # the head: long snout, jaws open over the entrance, teeth along both edges, red mouth inside
    HB = top - 3
    z0h = zt + round((zs - zt) * 0.8)
    for z in range(z0h - 1, zs + 1):
        f = (z - z0h) / (zs - z0h)
        hw = 6.0 - 3.0 * max(0.0, f)
        g = 0 if z < z0h + 3 else (1 if z < z0h + 6 else 2)
        upper_top = HB + 5 if z < z0h + 3 else HB + 3 + g
        for dx in range(-int(hw), int(hw) + 1):
            edge = abs(dx) >= int(hw)
            for y in range(HB, upper_top + 1):
                if g and HB + 2 <= y <= HB + 1 + g:
                    if edge and ((y == HB + 2 and z % 2) or (y == HB + 1 + g and not z % 2)): b.set(CX + dx, y, z, "minecraft:white_concrete")
                    else: b.set(CX + dx, y, z, AIR)
                elif y == HB and not edge: b.set(CX + dx, y, z, CROC2)
                elif g and y == HB + 1 and not edge: b.set(CX + dx, y, z, "minecraft:red_concrete")
                else: b.set(CX + dx, y, z, CROC)
    for dx in (-1, 1): b.set(CX + dx, HB + 4 + 2, zs - 1, "minecraft:black_concrete")  # nostrils on the snout tip
    for dx in (-1, 0, 1): b.set(CX + dx, HB + 6, zs - 1, CROC) if dx == 0 else None
    # golden eyes on raised brows, slit pupils on the outer side
    ez = z0h + 1
    for dx in (-3, 3):
        o = 1 if dx > 0 else -1
        b.set(CX + dx, HB + 6, ez - 1, CROC); b.set(CX + dx, HB + 7, ez - 1, CROC)
        b.set(CX + dx, HB + 6, ez, GOLD); b.set(CX + dx, HB + 6, ez + 1, GOLD)
        b.set(CX + dx + o, HB + 6, ez, "minecraft:black_concrete")
    # the banana on its head (what makes it a Bananawani): a curved yellow horn lying along the skull
    for (dz, dy, half) in ((-3, 1, 0), (-2, 1, 1), (-1, 2, 1), (0, 2, 1), (1, 3, 1), (2, 3, 0), (3, 4, 0)):
        for dx in range(-half, half + 1):
            b.set(CX + dx, HB + 5 + dy, ez + dz, "minecraft:yellow_concrete")
        for yy in range(HB + 6, HB + 5 + dy): b.set(CX, yy, ez + dz, "minecraft:yellow_concrete")
    b.set(CX, HB + 6, ez - 4, "minecraft:brown_concrete"); b.set(CX, HB + 10, ez + 3, "minecraft:brown_concrete")
    # four splayed legs gripping the pyramid, white claws at the toes
    for (lz, side) in ((CZ + 4, -1), (CZ + 4, 1), (CZ - 8, -1), (CZ - 8, 1)):
        for dz in (0, 1, 2):
            for k in range(6, 12):
                px = CX + side * k
                g = surf(px, lz + dz)
                for y in range(g + 1, max(g + 3, top + 4 - (k - 6))): b.set(px, y, lz + dz, CROC)
                if k == 11: b.set(px, g + 1, lz + dz, "minecraft:white_concrete")


def build():
    rnd = random.Random(4)
    b = B()
    # ---------------- desert ground, the moat round the casino island and the oasis lake to the south
    for x in range(N):
        for z in range(N):
            for y in range(-14, 0): b.set(x, y, z, "minecraft:sandstone" if y < -3 else "minecraft:sand")
            b.set(x, 0, z, "minecraft:sand" if (x * 7 + z * 3) % 11 else "minecraft:smooth_sandstone")
    for x in range(N):
        for z in range(N):
            if wet(x, z):
                d = math.hypot((x - LX) * 0.85, (z - LZ) * 1.2)
                depth = int(2 + (LR - d) * 0.5) if in_lake(x, z) else 4
                depth = max(depth, 4 if in_moat(x, z) else 2)
                for y in range(-depth, 1): b.set(x, y, z, WATER)
                b.set(x, -depth - 1, z, "minecraft:sand")
            elif any(wet(x + dx, z + dz) for dx in (-2, 0, 2) for dz in (-2, 0, 2)):
                if max(abs(x - CX), abs(z - CZ)) > P0 + 2:
                    b.set(x, 0, z, "minecraft:grass_block[snowy=false]")
                    if rnd.random() < 0.05 and max(abs(x - CX), abs(z - CZ)) > MOAT[1]: b.palm(x, 1, z, rnd.randint(6, 9))
    # ---------------- the pyramid: sloped faces of stairs, window bands, gold ridges
    for y in range(0, PTOP + 1):
        hw = H(max(1, y))
        for dx in range(-hw, hw + 1):
            for dz in range(-hw, hw + 1):
                b.set(CX + dx, y, CZ + dz, TILE if y == 0 else SAND)
        if y == 0: continue
        vertical = y == PTOP or H(y + 1) == hw
        for k in range(-hw, hw + 1):
            for (x, z, f) in ((CX + k, CZ - hw, "south"), (CX + k, CZ + hw, "north"), (CX - hw, CZ + k, "east"), (CX + hw, CZ + k, "west")):
                if abs(k) == hw: b.set(x, y, z, GOLD); continue
                if vertical: b.set(x, y, z, CUT if y in (1, PTOP) else ("minecraft:smooth_sandstone" if (k // 2) % 2 else CUT))
                else: b.set(x, y, z, stairs(SAND_ST, f))
    # apron round the foot
    for dx in range(-P0 - 3, P0 + 4):
        for dz in range(-P0 - 3, P0 + 4):
            if max(abs(dx), abs(dz)) > P0 and not wet(CX + dx, CZ + dz):
                b.set(CX + dx, 0, CZ + dz, CUT if max(abs(dx), abs(dz)) == P0 + 1 else TILE)
    # rooms inside: the casino hall (sloped ceiling), the upper floor, the vault
    F = 1
    for y in range(F, 12):
        c = H(y) - 2
        b.box(CX - c, y, CZ - c, CX + c, y, CZ + c, AIR)
    b.box(CX - 12, 14, CZ - 12, CX + 12, 22, CZ + 12, AIR)
    b.box(CX - 7, 25, CZ - 7, CX + 7, 30, CZ + 7, AIR)
    # windows through the vertical bands where a room is behind them
    for y in range(2, PTOP):
        hw = H(y)
        if H(y + 1) != hw: continue
        for k in range(-hw + 3, hw - 2, 3):
            for (x, z, x1, z1, x2, z2) in ((CX + k, CZ - hw, CX + k, CZ - hw + 1, CX + k, CZ - hw + 2), (CX + k, CZ + hw, CX + k, CZ + hw - 1, CX + k, CZ + hw - 2),
                                           (CX - hw, CZ + k, CX - hw + 1, CZ + k, CX - hw + 2, CZ + k), (CX + hw, CZ + k, CX + hw - 1, CZ + k, CX + hw - 2, CZ + k)):
                if b.get(x2, y, z2) == AIR:
                    b.set(x1, y, z1, AIR); b.set(x, y, z, pane_of("minecraft:orange_stained_glass_pane"))
    # ---------------- the portico at the south foot, under the RAIN DINNERS sign
    for x in range(CX - 9, CX + 10):
        for z in range(CZ + 22, CZ + 35):
            b.set(x, 0, z, TILE if abs(x - CX) > 2 else "minecraft:red_terracotta")
    for x in range(CX - 4, CX + 5):  # entrance through the shell
        for y in range(1, 8):
            for z in range(CZ + 18, CZ + 30): b.set(x, y, z, AIR)
    for x in range(CX - 5, CX + 6):
        b.set(x, 8, CZ + 29, GOLD if abs(x - CX) == 5 else CUT)
    for z in range(CZ + 22, CZ + 30):
        for x in (CX - 5, CX + 5):
            for y in range(1, 9): b.set(x, y, z, SAND if (z - CZ) % 3 else CUT)
    for x in (CX - 8, CX - 5, CX + 5, CX + 8):
        b.column(x, CZ + 33, 1, 7, AL.PILLAR); b.set(x, 0, CZ + 33, CUT)
    for x in (CX - 8, CX + 8):
        for z in range(CZ + 24, CZ + 33): b.column(x, z, 1, 8, SAND if z % 2 else CUT)
    b.box(CX - 9, 9, CZ + 22, CX + 9, 9, CZ + 34, SAND)
    for x in range(CX - 9, CX + 10): b.set(x, 8, CZ + 34, GOLD if x % 2 == 0 else CUT)  # gold frieze over the columns
    for z in range(CZ + 22, CZ + 35):
        b.set(CX - 10, 9, z, stairs(SAND_ST, "east", "top")); b.set(CX + 10, 9, z, stairs(SAND_ST, "west", "top"))
    # the sign: a red board with gold letters set into it, braced on the portico roof, read from the bridge (south)
    BZ = CZ + 34
    b.box(CX - 15, 9, BZ - 1, CX + 15, 9, BZ, SAND)
    for x in range(CX - 15, CX + 16):
        b.set(x, 9, BZ + 1, stairs(SAND_ST, "north", "top"))
        for y in range(10, 23): b.set(x, y, BZ, "minecraft:red_terracotta"); b.set(x, y, BZ - 1, "minecraft:red_terracotta" if abs(x - CX) < 15 else GOLD)
        b.set(x, 10, BZ, GOLD); b.set(x, 22, BZ, GOLD); b.set(x, 22, BZ - 1, GOLD)
        b.set(x, 23, BZ, slab("minecraft:smooth_sandstone_slab")) if x % 2 else b.set(x, 23, BZ, "minecraft:yellow_concrete")  # marquee bulbs
    for y in range(10, 23):
        b.set(CX - 15, y, BZ, GOLD); b.set(CX + 15, y, BZ, GOLD)
    b.text(CX - 7, 17, BZ, "RAIN", GOLD, axis="x", step=1)
    b.text(CX - 13, 11, BZ, "DINNERS", GOLD, axis="x", step=1)
    # ---------------- the causeway bridge over the lake
    z_end = CZ + 35
    while z_end < N - 1 and (wet(CX, z_end) or b.get(CX, 0, z_end) == "minecraft:grass_block[snowy=false]"): z_end += 1
    for z in range(CZ + 35, z_end + 1):
        for x in range(CX - 4, CX + 5):
            b.set(x, 0, z, "minecraft:red_terracotta" if abs(x - CX) <= 1 else CUT)
            for y in range(1, 12): b.set(x, y, z, AIR)
        for x in (CX - 5, CX + 5):
            b.set(x, 0, z, SAND)
            b.set(x, 1, z, wall(AL.SAND_W) if (z - CZ) % 6 else SAND)
            if (z - CZ) % 6 == 0:
                b.set(x, 2, z, fence("jungle")); b.set(x, 3, z, GOLD); b.set(x, 4, z, lantern())
    for z in range(z_end + 1, N):  # the avenue into town
        for x in range(CX - 3, CX + 4): b.set(x, 0, z, "minecraft:red_terracotta" if abs(x - CX) < 2 else CUT)
    for (px, pz) in ((CX - 7, z_end + 2), (CX + 7, z_end + 2), (CX - 12, CZ + 31), (CX + 12, CZ + 31)):
        if not wet(px, pz) and b.get(px, 1, pz) is None and pz + 4 < N:
            b.set(px, 0, pz, "minecraft:grass_block[snowy=false]"); b.palm(px, 1, pz, 8)
    # ---------------- the crocodile on the roof
    crocodile(b, PTOP)
    # ---------------- ground floor: the casino hall
    r = I.Room(b, CX - 21, F, CZ - 21, CX + 21, CZ + 21, 11, "royal", random.Random(1))
    for z in range(CZ - 20, CZ + 21, 2):  # banks of slot machines on the east and west sides, backed by a panel
        for x in (CX - 22, CX + 22):
            b.set(x, F, z, "minecraft:crafter[crafting=false,orientation=north_up,triggered=false]"); b.set(x, F + 1, z, "minecraft:redstone_lamp[lit=true]")
            b.set(x + (1 if x < CX else -1), F, z, stairs("minecraft:dark_oak_stairs", "east" if x > CX else "west"))
    for z in range(CZ - 21, CZ + 22):
        for x in (CX - 23, CX + 23):
            for y in (F, F + 1, F + 2): b.set(x, y, z, "minecraft:dark_oak_planks")
            b.set(x, F + 3, z, slab("minecraft:smooth_sandstone_slab"))
    for (x, z) in ((CX - 10, CZ - 10), (CX + 12, CZ - 10), (CX - 10, CZ + 6), (CX + 10, CZ + 6)):  # roulette tables
        b.disk(x, F, z, 2, "minecraft:dark_oak_planks"); b.disk(x, F + 1, z, 2, "minecraft:green_carpet")
        b.set(x, F + 1, z, "minecraft:red_carpet"); b.set(x, F + 1, z + 1, "minecraft:black_carpet")
        for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(x + dx, F, z + dz, stairs("minecraft:dark_oak_stairs", {(3, 0): "east", (-3, 0): "west", (0, 3): "south", (0, -3): "north"}[(dx, dz)]))
    for x in range(CX - 16, CX + 17, 8):  # card tables
        b.set(x, F, CZ + 15, "minecraft:dark_oak_fence"); b.set(x, F + 1, CZ + 15, "minecraft:green_carpet")
        for (dx, f) in ((1, "west"), (-1, "east")): b.set(x + dx, F, CZ + 15, stairs("minecraft:dark_oak_stairs", f))
    for x in range(CX - 8, CX + 9):  # bar at the back
        b.set(x, F, CZ - 18, stairs("minecraft:dark_oak_stairs", "south", "top"))
        b.set(x, F, CZ - 21, "onepiece:sake_barrel[axis=x]" if x % 2 else BARREL); b.set(x, F + 1, CZ - 21, "minecraft:dark_oak_shelf[facing=south]")
        if x % 3 == 0: b.set(x, F + 1, CZ - 18, "minecraft:brewing_stand")
    # VIP stair to the upper floor (Crocodile's office)
    b.stairs_up(CX + 4, F, CZ - 12, 13, SAND_ST, "south", w=3)
    for z in range(CZ - 12, CZ + 1):  # solid stringers either side, capped with a balustrade
        top = F + (z - CZ + 12)
        for x in (CX + 3, CX + 7):
            for y in range(F, top + 1): b.set(x, y, z, SAND if (z - CZ) % 4 else CUT)
            b.set(x, top + 1, z, wall(AL.SAND_W))
    # stairs from the casino floor down to the cage room, railed
    UY = -12
    b.stairs_up(CX - 1, UY, CZ + 6, 13, SAND_ST, "north", w=3)
    for z in range(CZ - 6, CZ - 1):
        for x in (CX - 2, CX + 2): b.set(x, F, z, fence("dark_oak"))
    for x in range(CX - 1, CX + 2): b.set(x, F, CZ - 2, fence("dark_oak"))
    for z in range(CZ - 23, CZ + 30):
        for x in range(CX - 2, CX + 3):
            below = b.get(x, F - 1, z) or AIR
            if b.get(x, F, z) in (None, AIR) and below != AIR and "stairs" not in below: b.set(x, F, z, "minecraft:red_carpet")
    for (x, z) in ((CX - 12, CZ - 12), (CX + 12, CZ - 12), (CX - 12, CZ + 12), (CX + 12, CZ + 12), (CX, CZ)):
        r.chandelier(x, z, 3, 2)
    r.plants(4); r.paintings(6)
    # ---------------- upper floor: Crocodile's office and the Baroque Works meeting room
    I.furnish(b, CX - 12, 14, CZ - 12, CX - 1, CZ + 12, 9, "study", "desert")
    I.furnish(b, CX + 1, 14, CZ - 12, CX + 12, CZ + 12, 9, "dining", "desert")
    # the VIP stair arrives at z CZ: keep a landing in front of its head clear of the first row of tables, so you step
    # off onto open floor (the long table behind it stays the agents' meeting table), and rail the stair well
    b.box(CX + 2, 14, CZ + 1, CX + 11, 16, CZ + 3, AIR)
    for z in range(CZ - 3, CZ):
        for x in (CX + 3, CX + 7): b.set(x, 14, z, wall(AL.SAND_W))
    for x in range(CX + 3, CX + 8): b.set(x, 14, CZ - 4, wall(AL.SAND_W))
    for z in range(CZ - 12, CZ + 13):
        for y in range(14, 23): b.set(CX, y, z, SAND)
    for y in (14, 15, 16): b.set(CX, y, CZ + 4, AIR); b.set(CX, y, CZ + 5, AIR)
    b.box(CX - 11, 14, CZ - 9, CX - 7, 14, CZ - 9, GOLD)  # his desk
    b.set(CX - 9, 15, CZ - 9, "onepiece:den_den_relay[facing=north]")
    for y in (14, 15, 16): b.set(CX - 9, y, CZ - 11, AIR); b.set(CX - 9, y, CZ - 10, AIR)
    b.set(CX - 10, 14, CZ - 11, stairs("minecraft:dark_oak_stairs", "north"))
    # top floor: the vault
    b.stairs_up(CX - 6, 14, CZ + 12, 11, SAND_ST, "north", w=2)
    I.furnish(b, CX - 7, 25, CZ - 7, CX + 7, CZ + 7, 6, "treasure", "royal")
    # ---------------- under the lake: the seastone cage room with glass walls
    ux0, ux1, uz0, uz1 = CX - 10, CX + 10, CZ + 24, CZ + 48
    for x in range(ux0 - 4, ux1 + 5):  # the deep water the Bananawani swim in, round the glass
        for z in range(uz0 + 8, uz1 + 5):
            if not wet(x, z): continue
            for y in range(UY - 1, 0): b.set(x, y, z, WATER)
            b.set(x, UY - 2, z, "minecraft:sand")
    b.box(ux0 - 1, UY - 1, uz0 - 1, ux1 + 1, UY + 7, uz1 + 1, SEA)
    b.box(ux0, UY, uz0, ux1, UY + 6, uz1, AIR)
    for z in range(uz0 + 8, uz1 + 1):
        for x in range(ux0, ux1 + 1): b.set(x, UY + 7, z, "minecraft:glass")
        for y in range(UY + 1, UY + 7): b.set(ux0 - 1, y, z, "minecraft:glass"); b.set(ux1 + 1, y, z, "minecraft:glass")
    for x in range(ux0, ux1 + 1):
        for y in range(UY + 1, UY + 7): b.set(x, y, uz1 + 1, "minecraft:glass")
    for x in range(ux0 + 3, ux1 - 2):  # the cage
        for y in range(UY, UY + 5): b.set(x, y, uz1 - 6, "onepiece:prison_bars")
    for z in range(uz1 - 6, uz1 + 1):
        for y in range(UY, UY + 5): b.set(ux0 + 3, y, z, "onepiece:prison_bars"); b.set(ux1 - 3, y, z, "onepiece:prison_bars")
    b.box(ux0 + 4, UY + 5, uz1 - 5, ux1 - 4, UY + 5, uz1, SEA)
    for z in range(uz0, uz1 - 7): b.set(CX, UY, z, "minecraft:red_carpet")
    for z in range(uz0 + 2, uz1 - 7, 4): b.set(ux0 + 1, UY + 6, z, lantern(True)); b.set(ux1 - 1, UY + 6, z, lantern(True))
    for z in range(CZ + 7, uz0):  # the passage under the casino
        for x in range(CX - 2, CX + 3):
            for y in range(UY, 0):
                b.set(x, y, z, AIR)
            b.set(x, UY - 1, z, SEA)
        for y in range(UY, 0): b.set(CX - 3, y, z, SEA); b.set(CX + 3, y, z, SEA)
    # ---------------- Rainbase: desert houses around the casino
    def clear_site(x0, z0, w, d):
        for x in range(x0 - 1, x0 + w + 1):
            for z in range(z0 - 1, z0 + d + 2):
                if wet(x, z) or max(abs(x - CX), abs(z - CZ)) <= MOAT[1] + 1 or (abs(x - CX) <= 5 and z > CZ): return False
                if b.get(x, 0, z) == "minecraft:grass_block[snowy=false]": return False
        return True
    k = 0
    for (x, z) in [(x, z) for x in range(4, N - 12, 14) for z in (4, 18, 100, 112)] + [(x, z) for x in (4, 18, 94, 108) for z in range(32, 92, 14)]:
        w, d, h = rnd.choice((9, 10, 11)), rnd.choice((8, 9)), rnd.choice((5, 6))
        if x + w > N - 1 or not clear_site(x, z, w, d): continue
        AL.house(b, x, z, w, d, h, k); k += 1
    # ---------------- people
    b.npc(CX - 9, 14, CZ - 11, "crocodile", True)
    b.chest(CX + 5, F, CZ - 20, "treasure", "south"); b.chest(CX, 25, CZ - 4, "treasure", "south")
    b.guards("baroque_agent", ((CX - 6, CZ + 31), (CX + 6, CZ + 31), (CX - 14, CZ), (CX + 14, CZ), (CX, CZ - 10)))
    b.guards("baroque_agent", ((CX + 8, CZ), (CX + 10, CZ + 10)), y=14)
    b.guards("baroque_agent", ((CX - 4, uz0 + 4), (CX + 4, uz0 + 4)), y=UY)
    return b, 0
