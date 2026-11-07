"""Kuraigana Castle: Dracule Mihawk's gloomy home on the ruined island where Zoro trained. A dark gothic castle of
deepslate on a crag, with pointed spires, flying buttresses, tall stained windows and a gate tower, over the ruins
of the old kingdom town, a graveyard and a dead misty forest where the Humandrills lurk. Inside: the great hall
with Mihawk's chair and the fire, the sword gallery, his library, the wine cellar, the dining hall, Perona's pink
ghost room, guest rooms and the training yard where Zoro learned. ~104 x 104. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "kuraigana_castle"
TITLE = "Kuraigana Castle (Mihawk)"
CUTS = [4, 13]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 104
CX, CZ = 52, 44
DS = "minecraft:deepslate_bricks"
DST = "minecraft:deepslate_tiles"
DST_ST = "minecraft:deepslate_tile_stairs"
POL = "minecraft:polished_deepslate"
GOTH = dict(wood="dark_oak", rug="red", rug2="black", bed="red", light="minecraft:soul_lantern", accent="minecraft:polished_deepslate",
            banner="black", candle="red")
GHOST = dict(wood="cherry", rug="pink", rug2="black", bed="pink", light="minecraft:soul_lantern", accent="minecraft:pink_concrete",
             banner="pink", candle="pink")
CROWN = 6               # crag top: the castle stands on y 6
K0, K1, Q0, Q1 = CX - 20, CX + 20, CZ - 16, CZ + 10   # main block
FL = (CROWN + 1, CROWN + 10, CROWN + 19)
TOPY = CROWN + 28
LAKE = (CX, 16, 26, 12)     # cx, cz, rx, rz: the small lake the castle is partly raised over (its north side)
TER0, TER1 = Q0 - 8, Q0 - 1  # the arcaded terrace over the lake, along the castle's north face
HILLS = ((92, 44, 10, 22, (0, 1)), (11, 54, 9, 20, (1, 0)))  # the island's odd hills whose summits curl inward


def in_lake(x, z, m=0.0):
    lx, lz, rx, rz = LAKE
    return ((x - lx) / (rx + m)) ** 2 + ((z - lz) / (rz + m)) ** 2 < 1


def near_hill(x, z, m=3):
    return any(math.hypot(x - hx, z - hz) <= r + m for (hx, hz, r, _, _) in HILLS)


def curl_hill(b, hc, rnd):
    """A steep hill narrowing to a neck whose summit curls over into a spiral (Kuraigana's Tim Burton hills)."""
    cx, cz, R, H, (ux, uz) = hc
    rho0, pts, th, end = 6.5, [], 0.0, 1.8 * math.pi
    while th <= end:
        rho = rho0 * (1 - 0.22 * th / math.pi)
        u, v = rho0 - rho * math.cos(th), H + rho * math.sin(th)
        pts.append((cx + ux * u, v, cz + uz * u, 2.7 - 1.6 * th / end))
        th += 0.05
    def inside(x, y, z):
        if y < 1: return False
        if y <= H and math.hypot(x - cx, z - cz) <= max(2.5, R * (1 - y / H) ** 1.4): return True
        return any((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= tr * tr for (px, py, pz, tr) in pts)
    def mat(x, y, z):
        r = rnd.random()
        return "minecraft:moss_block" if r < 0.72 else "minecraft:podzol" if r < 0.9 else "minecraft:coarse_dirt"
    span = R + 18
    b.shape(inside, cx - span, 1, cz - span, cx + span, H + 12, cz + span, mat, interior="minecraft:tuff")


def coffin_boat(b, x0, cz):
    """Mihawk's coffin-shaped black boat: a tall-backed seat at the wide head end, two green candles at the foot."""
    HALF = (1, 1, 1, 2, 2, 2, 2, 1, 1)
    hull = "minecraft:polished_blackstone"
    for i, hw_ in enumerate(HALF):
        x = x0 + i
        for z in range(cz - hw_, cz + hw_ + 1):
            b.set(x, -1, z, hull); b.set(x, 0, z, "minecraft:black_concrete")
            edge = abs(z - cz) == hw_ or i in (0, len(HALF) - 1)
            b.set(x, 1, z, hull if edge else AIR)
            if edge: b.set(x, 2, z, AIR)
    xh = x0 + len(HALF) - 1
    b.set(xh - 1, 1, cz, stairs("minecraft:dark_oak_stairs", "east"))         # the seat
    b.set(xh - 1, 1, cz - 1, stairs("minecraft:polished_blackstone_stairs", "south")); b.set(xh - 1, 1, cz + 1, stairs("minecraft:polished_blackstone_stairs", "north"))
    for y in (2, 3): b.set(xh, y, cz, hull)                                   # tall back
    b.set(xh, 4, cz, "minecraft:polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    for z in (cz - 1, cz + 1):
        b.set(x0 + 1, 2, z, "minecraft:polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        b.set(x0 + 1, 3, z, candle("green", 3))


def spire(b, cx, cz, r, y0, y1, roof_h):
    b.cyl(cx, cz, r, y0, y1, DS, hollow=True)
    for y in range(y0 + 3, y1 - 1, 6):
        for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
            b.set(cx + dx, y, cz + dz, "minecraft:red_stained_glass_pane"); b.set(cx + dx, y + 1, cz + dz, "minecraft:red_stained_glass_pane")
    for k in range(roof_h):
        rr = (r + 1) * (1 - k / roof_h) + 0.3
        b.cyl(cx, cz, rr, y1 + 1 + k, y1 + 1 + k, DST, hollow=rr > 1.5)
    b.set(cx, y1 + roof_h + 1, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    for a in range(0, 360, 45):
        t = math.radians(a); b.set(round(cx + (r + 1) * math.cos(t)), y1 + 1, round(cz + (r + 1) * math.sin(t)), "minecraft:deepslate_brick_wall")


def build():
    rnd = random.Random(83)
    b = B()
    # ---------------- island ground: dead forest, ruins, graveyard; the crag in the middle
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - CX, z - CZ)
            h = CROWN if d < 30 else (int(CROWN * max(0, 1 - (d - 30) / 8)) if d < 38 else 0)
            for y in range(-3, h + 1):
                b.set(x, y, z, "minecraft:tuff" if y < h else ("minecraft:podzol" if (x + z) % 4 else "minecraft:coarse_dirt") if h == 0 else "minecraft:moss_block" if rnd.random() < 0.2 else "minecraft:cobbled_deepslate")
            if h == 0 and d > 40:
                r = rnd.random()
                if in_lake(x, z, 4) or near_hill(x, z): r = 1.0
                if r < 0.025:  # dead trees
                    th = rnd.randint(6, 11)
                    for y in range(1, th): b.set(x, y, z, "minecraft:pale_oak_log[axis=y]" if (x + z) % 2 else "minecraft:dark_oak_log[axis=y]")
                    for k in range(3):
                        ax, az = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                        for j in range(1, 4): b.set(x + ax * j, th - 1 - k * 2 + j // 2, z + az * j, "minecraft:pale_oak_log[axis=x]" if ax else "minecraft:pale_oak_log[axis=z]")
                    b.set(x, th, z, "minecraft:pale_hanging_moss[tip=true]") if False else None
                elif r < 0.06: b.set(x, 1, z, rnd.choice(("minecraft:dead_bush", "minecraft:pale_moss_carpet", "minecraft:brown_mushroom", "minecraft:short_grass")))
    # the lake on the north side: dark water in a basin cut into the crag, the castle's back stands in it
    lrnd = random.Random(831)  # its own stream, so the rest of the island's random layout stays as it was
    for x in range(N):
        for z in range(N):
            if not in_lake(x, z): continue
            b.set(x, -3, z, "minecraft:clay" if lrnd.random() < 0.15 else "minecraft:mud")  # dark mud bed, scattered clay
            for y in (-2, -1, 0): b.set(x, y, z, WATER)
            for y in range(1, CROWN + 14): b.set(x, y, z, AIR)
    # graveyard (south-west) with crosses
    for i in range(18):
        gx, gz = 12 + (i % 6) * 4, 78 + (i // 6) * 5
        b.set(gx, 1, gz, "minecraft:stone_brick_wall"); b.set(gx, 2, gz, "minecraft:stone_brick_wall")
        b.set(gx - 1, 2, gz, "minecraft:stone_button[face=wall,facing=west,powered=false]") if False else None
        b.set(gx, 3, gz, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
        for k in (1, 2): b.set(gx, 0, gz + k, "minecraft:coarse_dirt")
    for x in range(9, 36):
        for z in (75, 93):
            b.set(x, 1, z, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]") if x % 6 else b.set(x, 1, z, "minecraft:deepslate_brick_wall")
    # ruined town (east): broken walls of old houses
    for (hx, hz) in ((80, 70), (90, 82), (76, 88), (92, 60), (82, 12), (92, 24), (12, 14), (20, 28)):
        w, d = rnd.randint(6, 9), rnd.randint(6, 8)
        for x in range(hx, hx + w):
            for z in range(hz, hz + d):
                if x in (hx, hx + w - 1) or z in (hz, hz + d - 1):
                    for y in range(1, rnd.randint(1, 6)): b.set(x, y, z, rnd.choice(("minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:stone_bricks", "minecraft:mossy_cobblestone")))
                elif rnd.random() < 0.08: b.set(x, 1, z, rnd.choice(("minecraft:cobblestone", "minecraft:mossy_cobblestone_slab[type=bottom,waterlogged=false]", "minecraft:cobweb")))
    for hc in HILLS: curl_hill(b, hc, rnd)
    # ---------------- the path up the crag and the gate tower
    for i in range(CROWN):
        z = CZ + 38 - i * 2
        for x in range(CX - 2, CX + 3):
            for zz in (z, z - 1):
                for y in range(0, i + 1): b.set(x, y, zz, "minecraft:cobbled_deepslate")
                b.set(x, i + 1, zz, stairs("minecraft:cobbled_deepslate_stairs", "north")) if zz == z else b.set(x, i + 1, zz, "minecraft:cobbled_deepslate_slab[type=bottom,waterlogged=false]")
    GZ = CZ + 24
    for x in range(CX - 6, CX + 7):
        for z in range(GZ - 3, GZ + 4):
            edge = x in (CX - 6, CX + 6) or z in (GZ - 3, GZ + 3)
            for y in range(CROWN + 1, CROWN + 16): b.set(x, y, z, DS if edge else AIR)
            b.set(x, CROWN + 16, z, POL)
    for x in range(CX - 2, CX + 3):
        for z in range(GZ - 3, GZ + 4):
            for y in range(CROWN + 1, CROWN + 6): b.set(x, y, z, AIR)
    for x in range(CX - 2, CX + 3): b.set(x, CROWN + 6, GZ + 3, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for (x, z) in ((CX - 6, GZ - 3), (CX + 6, GZ - 3), (CX - 6, GZ + 3), (CX + 6, GZ + 3)): spire(b, x, z, 2, CROWN + 1, CROWN + 20, 8)
    # courtyard and training yard (between gate and keep)
    for x in range(CX - 26, CX + 27):
        for z in range(Q1 + 1, GZ - 3):
            if math.hypot(x - CX, z - CZ) < 29: b.set(x, CROWN, z, "minecraft:polished_deepslate" if (x + z) % 3 else "minecraft:cobbled_deepslate")
    for i in range(6):
        b.set(CX + 10 + (i % 3) * 3, CROWN + 1, Q1 + 4 + (i // 3) * 3, "onepiece:training_post[facing=north]")
    b.cyl(CX - 12, Q1 + 6, 2.5, CROWN + 1, CROWN + 1, "minecraft:mossy_stone_bricks"); b.cyl(CX - 12, Q1 + 6, 1.5, CROWN + 1, CROWN + 1, WATER)
    # ---------------- the main block: three floors, gothic windows, buttresses
    b.box(K0, CROWN, Q0, K1, CROWN, Q1, POL)
    b.walls(K0, CROWN + 1, Q0, K1, TOPY, Q1, DS)
    b.box(K0 + 1, CROWN + 1, Q0 + 1, K1 - 1, TOPY, Q1 - 1, AIR)
    for f in FL[1:]: b.box(K0 + 1, f - 1, Q0 + 1, K1 - 1, f - 1, Q1 - 1, "minecraft:dark_oak_planks")
    b.box(K0 + 1, TOPY, Q0 + 1, K1 - 1, TOPY, Q1 - 1, POL)
    for f in FL:
        for x in range(K0 + 3, K1 - 2, 4):
            for z in (Q0, Q1):
                for k in range(1, 7 if f == FL[0] else 6): b.set(x, f + k, z, "minecraft:red_stained_glass_pane" if k > 4 else "minecraft:gray_stained_glass_pane")
        for z in range(Q0 + 3, Q1 - 2, 4):
            for x in (K0, K1):
                for k in range(1, 6): b.set(x, f + k, z, "minecraft:gray_stained_glass_pane")
    for f in FL:  # gothic window dressing: a sill below, a pointed hood with a finial above each long-side window
        top = f + (6 if f == FL[0] else 5)
        for x in range(K0 + 3, K1 - 2, 4):
            for (z, o, fin, fout) in ((Q0, -1, "south", "north"), (Q1, 1, "north", "south")):
                zz = z + o
                b.set(x, f, zz, stairs("minecraft:deepslate_brick_stairs", fin, "top"))
                b.set(x - 1, top + 1, zz, stairs("minecraft:deepslate_brick_stairs", "east")); b.set(x + 1, top + 1, zz, stairs("minecraft:deepslate_brick_stairs", "west"))
                b.set(x, top + 1, zz, POL); b.set(x, top + 2, zz, "minecraft:deepslate_brick_wall")
    for fy in (FL[1] - 1, FL[2] - 1):  # string courses at the floor lines
        for x in range(K0 + 1, K1):
            if (x - K0) % 8 == 0: continue
            for (z, fin) in ((Q0 - 1, "south"), (Q1 + 1, "north")):
                if b.get(x, fy, z) in (None, AIR): b.set(x, fy, z, stairs("minecraft:polished_deepslate_stairs", fin, "top"))
        for z in range(Q0 + 1, Q1):
            for (x, fin) in ((K0 - 1, "east"), (K1 + 1, "west")):
                if b.get(x, fy, z) in (None, AIR): b.set(x, fy, z, stairs("minecraft:polished_deepslate_stairs", fin, "top"))
    for x in range(K0, K1 + 1, 8):  # buttresses on the long sides
        for (z, s) in ((Q0 - 1, -1), (Q1 + 1, 1)):
            for y in range(CROWN + 1, TOPY - 4): b.set(x, y, z, DS); b.set(x, y, z + s, DS) if y < TOPY - 12 else None
            b.set(x, TOPY - 4, z, "minecraft:deepslate_brick_wall")
    # steep gable roof
    for k in range(13):
        for x in range(K0 - 1, K1 + 2):
            b.set(x, TOPY + 1 + k, Q0 - 1 + k, stairs(DST_ST, "south")); b.set(x, TOPY + 1 + k, Q1 + 1 - k, stairs(DST_ST, "north"))
        for x in (K0, K1):
            for z in range(Q0 + k, Q1 - k + 1): b.set(x, TOPY + 1 + k, z, DS)
    for x in range(K0 - 1, K1 + 2): b.set(x, TOPY + 14, CZ - 3, DST)
    for x in range(K0 + 4, K1 - 3, 8):  # dormers
        for z in (Q0 + 3, Q1 - 3): b.set(x, TOPY + 5, z, "minecraft:red_stained_glass_pane")
    for (x, z) in ((K0, Q0), (K1, Q0), (K0, Q1), (K1, Q1)): spire(b, x, z, 4, CROWN + 1, TOPY + 8, 14)
    spire(b, CX, Q0 - 4, 5, CROWN + 1, TOPY + 18, 18)  # the great rear tower, standing in the lake
    b.cyl(CX, Q0 - 4, 5, -3, CROWN, DS)
    b.cyl(CX, Q0 - 4, 6.2, -3, 0, "minecraft:cobbled_deepslate")
    for a in range(0, 360, 15):  # battered plinth at the waterline
        t = math.radians(a); b.set(round(CX + 6.2 * math.cos(t)), 1, round(Q0 - 4 + 6.2 * math.sin(t)), stairs("minecraft:cobbled_deepslate_stairs", "north" if math.sin(t) < -0.7 else "south" if math.sin(t) > 0.7 else "west" if math.cos(t) < 0 else "east"))
    # the terrace over the lake: floor at the castle's ground floor, carried on an arcade standing in the water
    for x in range(K0, K1 + 1):
        for z in range(TER0, TER1 + 1):
            if b.get(x, CROWN + 1, z) not in (None, AIR) and z > TER0: continue  # tower foundations already there
            b.set(x, CROWN, z, POL)
            if in_lake(x, z): b.set(x, CROWN - 1, z, DS)
        for z in (TER0, TER0 + 1):  # the arcade face
            t = ((x - K0) % 5) / 5
            open_to = 1 + round(2.4 * math.sin(math.pi * t))
            for y in range(-3, CROWN):
                if (x - K0) % 5 == 0 or y > open_to: b.set(x, y, z, DS if (x - K0) % 5 else POL)
        if x not in (36, 37): b.set(x, CROWN + 1, TER0, wall("minecraft:deepslate_brick_wall"))
    for z in range(TER0, TER0 + 4):  # end parapets, only out to the corner towers' rings (z TER0+4 on is inside them)
        for x in (K0, K1): b.set(x, CROWN + 1, z, wall("minecraft:deepslate_brick_wall")) if b.get(x, CROWN + 1, z) in (None, AIR) else None
    b.stairs_up(36, 1, TER0 - 5, 5, "minecraft:deepslate_brick_stairs", "south", w=2)  # water stair down to the landing
    for i in range(5):
        for xx in (36, 37):
            for y in range(-3, 1 + i): b.set(xx, y, TER0 - 5 + i, DS)
    b.box(34, -3, 12, 39, -1, 14, DS); b.box(34, 0, 12, 39, 0, 14, POL)
    coffin_boat(b, 40, 13)
    for y in range(CROWN + 1, CROWN + 4):
        b.set(CX, y, Q0, AIR); b.set(CX - 1, y, Q0, AIR)
    for x in (CX - 2, CX - 1, CX, CX + 1, CX + 2):
        for y in range(CROWN + 1, CROWN + 6): b.set(x, y, Q1, AIR)
    for x in range(CX - 2, CX + 3): b.set(x, CROWN + 6, Q1, "minecraft:deepslate_brick_stairs[facing=south,half=top,shape=straight,waterlogged=false]")
    # stairs between floors in the west end
    SX = K0 + 2
    for f, nf in zip(FL, FL[1:]):
        for i in range(nf - f):
            for w in (0, 1, 2): b.set(SX + w, f + i, Q0 + 2 + i, stairs("minecraft:dark_oak_stairs", "south"))
            for w in (0, 1, 2):
                for k in (1, 2, 3):
                    c = b.get(SX + w, f + i + k, Q0 + 2 + i)
                    if c not in (None, AIR) and "dark_oak_stairs" not in c: b.set(SX + w, f + i + k, Q0 + 2 + i, AIR)
    KEEP = ((SX - 1, Q0 + 1, SX + 3, Q0 + 12),)
    # ground floor: great hall (Mihawk's chair by the fire), dining hall, wine cellar corner
    WALLX = CX + 8
    for z in range(Q0 + 1, Q1):
        for y in range(FL[0], FL[1] - 1): b.set(WALLX, y, z, DS)
    for y in (FL[0], FL[0] + 1, FL[0] + 2): b.set(WALLX, y, CZ, AIR); b.set(WALLX, y, CZ + 1, AIR)
    r = I.furnish(b, SX + 4, FL[0], Q0 + 1, WALLX - 1, Q1 - 1, 8, "hall", GOTH)
    r.chandelier(CX - 6, CZ - 3, 2, 3); r.chandelier(CX + 2, CZ - 3, 2, 3)
    for z in range(Q0 + 1, Q0 + 4):  # fireplace
        for x in range(CX - 3, CX + 4): b.set(x, FL[0] + 4, Q0 + 1, DS)
    b.set(CX, FL[0], Q0 + 1, "minecraft:campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]"); b.set(CX - 1, FL[0], Q0 + 1, "minecraft:campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    for x in (CX - 2, CX + 1):
        for y in range(FL[0], FL[0] + 4): b.set(x, y, Q0 + 1, POL)
    b.set(CX, FL[0], Q0 + 5, stairs("minecraft:dark_oak_stairs", "north")); b.set(CX - 1, FL[0], Q0 + 5, "minecraft:dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    I.furnish(b, WALLX + 1, FL[0], Q0 + 1, K1 - 1, Q1 - 1, 8, "dining", GOTH)
    # first floor: sword gallery and library; second: bedrooms incl. Perona's
    I.subdivide(b, K0 + 1, FL[1], Q0 + 1, K1 - 1, Q1 - 1, 8, DS, ("armory", "library", "study", "library", "armory"), GOTH, cell=13, keepout=KEEP, seed=5)
    rooms = I.subdivide(b, K0 + 1, FL[2], Q0 + 1, K1 - 1, Q1 - 1, 8, DS, ("bedroom", "bath", "bedroom", "bedroom", "treasure"), GOTH, cell=13, keepout=KEEP, seed=6)
    px0, pz0, px1, pz1 = rooms[-2] if len(rooms) > 1 else rooms[0]
    for x in range(px0, px1 + 1):
        for z in range(pz0, pz1 + 1):
            c = b.get(x, FL[2], z)
            if c and "carpet" in c: b.set(x, FL[2], z, "minecraft:pink_carpet" if (x + z) % 2 else "minecraft:black_carpet")
    I.furnish(b, px0, FL[2], pz0, px1, pz1, 8, "bedroom", GHOST, seed=77)
    # wine cellar under the hall, down a stair from the courtyard side
    b.box(K1 - 12, CROWN - 5, Q0 + 2, K1 - 2, CROWN - 1, Q1 - 2, AIR)
    for i in range(5):
        for w in (0, 1): b.set(K1 - 3 - i, CROWN - i, Q1 - 3 + w, stairs("minecraft:deepslate_brick_stairs", "east")) if False else None
    for k in range(6): b.set(K1 - 2, CROWN - 5 + k, Q1 - 3, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(K1 - 2, CROWN, Q1 - 3, AIR)
    r = I.furnish(b, K1 - 12, CROWN - 5, Q0 + 2, K1 - 3, Q1 - 2, 4, "storage", GOTH)
    for x in range(K1 - 11, K1 - 3, 2): b.set(x, CROWN - 5, Q0 + 2, "minecraft:barrel[facing=up,open=false]")
    # doorways from the great hall and the dining hall out onto the lake terrace (the rear tower splits the terrace in
    # two, so one door for each half; the west half leads down the water stair to the coffin-boat landing). Each is
    # 2 wide and 3 high between a buttress and a window, with a pointed head of upside-down stairs and a drip ledge.
    for dx0 in (CX - 8, CX + 13):          # x 44-45 (great hall), x 65-66 (dining hall)
        for x in (dx0, dx0 + 1):
            for y in range(FL[0], FL[0] + 3):
                b.set(x, y, Q0, AIR)
                for z in (Q0 - 1, Q0 + 1):  # keep the step outside and inside clear (rugs on the floor may stay)
                    c = b.get(x, y, z)
                    if c not in (None, AIR) and not (y == FL[0] and "carpet" in c): b.set(x, y, z, AIR)
            b.set(x, FL[0] + 4, Q0 - 1, stairs("minecraft:deepslate_brick_stairs", "south", "top"))  # drip ledge
        b.set(dx0, FL[0] + 3, Q0, stairs("minecraft:deepslate_brick_stairs", "west", "top"))
        b.set(dx0 + 1, FL[0] + 3, Q0, stairs("minecraft:deepslate_brick_stairs", "east", "top"))
    # ---------------- people and loot
    b.npc(CX, FL[0], Q0 + 6, "mihawk", True)
    b.chest(K1 - 4, FL[2], Q0 + 2, "legendary", "west"); b.chest(K1 - 11, CROWN - 5, Q1 - 3, "legendary", "east")
    b.guards("humandrill", ((CX - 6, Q1 + 4), (CX + 14, Q1 + 3)), y=CROWN + 1)
    forest = ((14, 64), (86, 64), (60, 90), (16, 32))
    for (x, z) in forest:
        for y in range(1, 4): b.set(x, y, z, AIR)
    b.guards("humandrill", forest, y=1)
    return b, 0
