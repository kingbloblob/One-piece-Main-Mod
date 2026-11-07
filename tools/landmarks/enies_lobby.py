"""Enies Lobby, the judicial island: the Main Gate, the town, the Courthouse, the bottomless waterfall chasm,
the drawbridge, the Tower of Justice on its rock pillar, the Bridge of Hesitation and the Gates of Justice.
~230 x 230, tower ~95 tall. Island top = y 0 (the structure sits on top of its own rock base)."""
import math, random
from canvas import *

SID = "tower_of_justice"
TITLE = "Enies Lobby"
CUTS = [10]
TILER = dict(terrain="beard_thin")

ROCK = "minecraft:stone"
ROCK2 = "minecraft:andesite"
WHITE = "onepiece:marine_bricks"
WHITE_ST = "onepiece:marine_brick_stairs"
TILE = "onepiece:marine_tiles"
TILE_ST = "onepiece:marine_tile_stairs"
ROOF = "minecraft:deepslate_tiles"
ROOF_ST = "minecraft:deepslate_tile_stairs"
PIL = "onepiece:marine_pillar[axis=y]"
FALL = "minecraft:light_blue_stained_glass"
FOAM = "minecraft:white_stained_glass"
CX = 112
N = 224


def wg_emblem(b, cu, cy, plane, s, k=1.0, axis="x"):
    """The World Government emblem: five linked rings, one in the middle and four round it in a cross.
    axis="x": drawn in the plane z=plane centred on x=cu; axis="z": in the plane x=plane centred on z=cu."""
    rc, rs, d = 2.4 * k, 1.7 * k, 3.6 * k
    R = int(d + rs + 2)
    for u in range(-R, R + 1):
        for v in range(-R, R + 1):
            on = abs(math.hypot(u, v) - rc) <= 0.55
            for (a, c) in ((d, 0), (-d, 0), (0, d), (0, -d)):
                if abs(math.hypot(u - a, v - c) - rs) <= 0.55: on = True
            if on:
                if axis == "x": b.set(cu + u, cy + v, plane, s)
                else: b.set(plane, cy + v, cu + u, s)


def wg_flag(b, x, y, z, w=11, h=7):
    """World Government flag (blue, white emblem) hanging in the plane x, spanning +z."""
    for i in range(w):
        for j in range(h):
            b.set(x, y - j, z + i, "minecraft:blue_wool")
    wg_emblem(b, z + w // 2, y - h // 2, x, "minecraft:white_wool", k=min(w, h) / 13.0, axis="z")


def facade(b, cx, cz, hw, y0, y1, skip=()):
    """Depth for a square tier: pilasters between the window bays, framed windows with sills on every floor,
    and a cornice under the terrace. Windows sit in bays of 4 between the pilasters."""
    for k in range(-hw + 2, hw - 1):
        for (x, z, ox, oz, f) in ((cx + k, cz - hw, 0, -1, "north"), (cx + k, cz + hw, 0, 1, "south"),
                                  (cx - hw, cz + k, -1, 0, "west"), (cx + hw, cz + k, 1, 0, "east")):
            if (f, k) in skip: continue
            if k % 4 == 0 and abs(k) <= hw - 3:
                b.column(x + ox, z + oz, y0 + 1, y1 - 1, PIL)
                b.set(x + ox, y0 + 1, z + oz, WHITE)
            elif k % 4 == 2 and abs(k) <= hw - 4:
                for y in range(y0 + 3, y1 - 2, 6):
                    b.set(x, y, z, PANE); b.set(x, y + 1, z, PANE); b.set(x, y + 2, z, pane_of("minecraft:blue_stained_glass_pane"))
                    b.set(x + ox, y - 1, z + oz, stairs(WHITE_ST, OPP[f], "top"))  # sill
                    b.set(x + ox, y + 3, z + oz, stairs(TILE_ST, OPP[f], "top"))  # head
            b.set(x + ox, y1, z + oz, stairs(TILE_ST, OPP[f], "top"))  # cornice


def spire_roof(b, cx, cz, r, y, h, st=ROOF_ST, full=ROOF):
    for i in range(h):
        rr = r * (1 - i / h)
        if rr < 0.6:
            b.set(cx, y + i, cz, full); continue
        b.cyl(cx, cz, rr, y + i, y + i, full)
    b.column(cx, cz, y + h, y + h + 3, fence("dark_oak"))
    return y + h + 3


def building(b, x0, z0, x1, z1, y, h, wallb=WHITE, roof=True, rnd=None):
    b.box(x0, y, z0, x1, y, z1, TILE)
    b.walls(x0, y + 1, z0, x1, y + h, z1, wallb)
    b.box(x0 + 1, y + 1, z0 + 1, x1 - 1, y + h, z1 - 1, AIR)
    for x in range(x0 + 2, x1 - 1, 3):
        for z in (z0, z1):
            for yy in range(y + 2, y + h - 1, 4): b.set(x, yy, z, PANE); b.set(x, yy + 1, z, PANE)
    for z in range(z0 + 2, z1 - 1, 3):
        for x in (x0, x1):
            for yy in range(y + 2, y + h - 1, 4): b.set(x, yy, z, PANE); b.set(x, yy + 1, z, PANE)
    if roof: b.hip_roof(x0, z0, x1, z1, y + h + 1, ROOF_ST, ROOF, overhang=1)
    return y + h


def build():
    rnd = random.Random(5)
    b = B()
    # ---------------- island rock: south main island, north tower pillar, and the chasm between
    def island_top(x, z):
        r_main = math.hypot((x - CX) / 102, (z - 170) / 53)
        r_tower = math.hypot((x - CX) / 34, (z - 72) / 30)
        r_gate = math.hypot((x - CX) / 60, (z - 14) / 16)
        return r_main <= 1 or r_tower <= 1 or r_gate <= 1, (r_main, r_tower, r_gate)
    for x in range(0, N + 1):
        for z in range(0, N + 1):
            ok, rs = island_top(x, z)
            n = math.sin(x * 0.3) * 1.5 + math.cos(z * 0.23) * 1.5
            if ok:
                depth = -22 if min(rs) < 0.97 else -20
                for y in range(depth, 1): b.set(x, y, z, ROCK if (y + x // 3) % 7 else ROCK2)
                b.set(x, 0, z, "minecraft:stone_bricks" if rs[0] <= 1 else "minecraft:polished_andesite")
            else:
                # the chasm floor far below, with a churning pool, and the falling sea on its walls
                for y in range(-26, -22): b.set(x, y, z, ROCK)
                b.set(x, -22, z, WATER); b.set(x, -21, z, WATER)
                for y in range(-20, 1): b.set(x, y, z, AIR)  # keep the chasm open whatever terrain is there
                if x in (0, N) or z in (0, N):  # the rim of the great hole
                    for y in range(-26, 1): b.set(x, y, z, ROCK if (y + x) % 5 else ROCK2)
    # waterfall curtain: wherever an island edge faces the chasm, sheets of glass "water" pour down the cliff
    for x in range(0, N + 1):
        for z in range(0, N + 1):
            ok, rs = island_top(x, z)
            if ok: continue
            nb = [island_top(x + dx, z + dz)[0] for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any(nb):
                for y in range(-20, 1): b.set(x, y, z, FALL if (y + x + z) % 6 else FOAM)
            # outer rim of the whole site: the sea pouring in from the edge
            if (x in (1, N - 1) or z in (1, N - 1)) and not (x in (0, N) or z in (0, N)):  # the sea pouring over the rim
                for y in range(-20, 0): b.set(x, y, z, FALL if (y + x * 3 + z) % 5 else FOAM)
    # ---------------- Main Gate (south) with its walls
    GZ = 222
    for x in range(CX - 40, CX + 41):
        zz = 170 + int(53 * math.sqrt(max(0, 1 - ((x - CX) / 102) ** 2))) - 2
        b.box(x, 1, zz - 2, x, 12, zz, WHITE)
        b.set(x, 13, zz, wall("onepiece:marine_brick_wall") if x % 2 else WHITE)
    b.box(CX - 10, 1, 216, CX + 10, 24, 223, WHITE)
    b.box(CX - 5, 1, 216, CX + 5, 16, 223, AIR)
    b.arch_x(CX - 5, CX + 5, 223, 13, 2, "onepiece:marine_tiles", thick=1)
    for x in range(CX - 10, CX + 11): b.set(x, 25, 223, wall("onepiece:marine_brick_wall") if x % 2 else WHITE)
    for x in (CX - 13, CX + 13):
        b.cyl(x, 219, 4, 1, 30, WHITE); spire_roof(b, x, 219, 5, 31, 10)
    for x in range(CX - 6, CX + 7):  # the World Government emblem over the gate
        for y in range(16, 26): b.set(x, y, 224, "minecraft:blue_wool")
    wg_emblem(b, CX, 21, 225, "minecraft:white_wool", k=0.85)
    # ---------------- town of the main island: houses for the officials
    road = set()
    for z in range(150, 216):
        for x in range(CX - 5, CX + 6): b.set(x, 0, z, "minecraft:polished_andesite"); road.add((x, z))
    for (x0, z0) in [(x, z) for x in list(range(CX - 75, CX - 10, 14)) + list(range(CX + 12, CX + 75, 14)) for z in (168, 186, 204)]:
        if not island_top(x0 - 2, z0 - 2)[0] or not island_top(x0 + 12, z0 + 12)[0]: continue
        hh = rnd.choice((8, 12))
        building(b, x0, z0, x0 + 10, z0 + 10, 0, hh, rnd.choice((WHITE, "minecraft:white_terracotta", "onepiece:dressrosa_stucco")))
        import interiors as I
        if hh == 12:  # two storeys
            b.box(x0 + 1, 6, z0 + 1, x0 + 9, 6, z0 + 9, "minecraft:spruce_planks")
            b.box(x0 + 8, 6, z0 + 2, x0 + 8, 6, z0 + 4, AIR)
            b.stairs_up(x0 + 8, 1, z0 + 7, 5, "minecraft:spruce_stairs", "north")
            I.furnish(b, x0 + 1, 7, z0 + 1, x0 + 9, z0 + 9, 5, rnd.choice(("bedroom", "library", "study")), "justice", seed=rnd.randint(0, 9999))
        b.set(x0 + 5, 1, z0 + 10, "minecraft:dark_oak_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
        b.set(x0 + 5, 2, z0 + 10, "minecraft:dark_oak_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
        I.furnish(b, x0 + 1, 1, z0 + 1, x0 + 9, z0 + 9, 5 if hh == 12 else 7, rnd.choice(("study", "tavern", "kitchen", "dining", "barracks")), "justice", seed=rnd.randint(0, 9999))
    for z in range(152, 216, 8):
        for x in (CX - 7, CX + 7): b.column(x, z, 1, 4, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]"); b.set(x, 5, z, LANTERN)
    # ---------------- the Courthouse (north edge of the main island, facing the chasm)
    C0, C1, Z0, Z1 = CX - 30, CX + 30, 126, 150
    building(b, C0, Z0, C1, Z1, 0, 16, WHITE, roof=False)
    b.box(C0, 17, Z0, C1, 17, Z1, WHITE)
    for x in range(C0, C1 + 1): b.set(x, 18, Z1, wall("onepiece:marine_brick_wall")); b.set(x, 18, Z0, wall("onepiece:marine_brick_wall"))
    for x in range(C0 + 2, C1 - 1, 4): b.column(x, Z1 + 1, 1, 15, PIL)  # front colonnade
    b.box(C0, 16, Z1 + 1, C1, 16, Z1 + 3, WHITE)
    for x in range(C0, C1 + 1): b.set(x, 17, Z1 + 3, stairs(TILE_ST, "north"))
    # central clock tower with a dome
    b.box(CX - 7, 17, 132, CX + 7, 36, 146, WHITE)
    b.box(CX - 6, 17, 133, CX + 6, 36, 145, AIR)
    for (fx, fz) in ((CX, 147), (CX, 131)):
        for i in range(-3, 4):
            for j in range(-3, 4):
                if i * i + j * j <= 9: b.set(fx + i, 30 + j, fz, "minecraft:white_concrete" if i * i + j * j < 7 else GOLD if False else "minecraft:gold_block")
        b.set(fx, 30, fz, "minecraft:black_concrete"); b.set(fx, 31, fz, "minecraft:black_concrete"); b.set(fx + 1, 30, fz, "minecraft:black_concrete")
    b.dome(CX, 139, 37, 8, s=TILE, onion=False)
    spire_roof(b, CX, 139, 1, 46, 3)
    for x in range(CX - 5, CX + 6): b.set(x, 1, Z1, AIR); b.set(x, 2, Z1, AIR); b.set(x, 3, Z1, AIR)
    # court room inside: judges' bench (the three-headed judge Baskerville), benches
    b.box(CX - 8, 1, Z0 + 2, CX + 8, 3, Z0 + 3, "minecraft:dark_oak_planks")
    for x in (CX - 4, CX, CX + 4): b.set(x, 4, Z0 + 2, stairs("minecraft:dark_oak_stairs", "south"))
    for z in range(Z0 + 8, Z1 - 2, 3):
        for x in list(range(C0 + 3, CX - 3)) + list(range(CX + 4, C1 - 2)):
            b.set(x, 1, z, stairs("minecraft:dark_oak_stairs", "south"))
    for x in range(C0 + 4, C1 - 3, 6): b.set(x, 15, (Z0 + Z1) // 2, HANG)
    for x in range(CX - 4, CX + 5): b.set(x, 1, Z1 - 1, "minecraft:red_carpet")
    for z in range(Z0 + 4, Z1): b.set(CX, 1, z, "minecraft:red_carpet")
    # ---------------- the drawbridge across the chasm, from the courthouse roof to the tower
    for z in range(96, Z0):
        for x in range(CX - 3, CX + 4):
            b.set(x, 0, z, "minecraft:dark_oak_planks" if abs(x - CX) < 3 else "minecraft:stripped_dark_oak_log[axis=z]")
        b.set(CX - 3, 1, z, fence("dark_oak")); b.set(CX + 3, 1, z, fence("dark_oak"))
    # the drawbridge's two winch pylons on the tower side, its chains running down to the far end
    for x in (CX - 5, CX + 5):
        b.box(x - 1, 1, 98, x + 1, 10, 100, WHITE)
        b.column(x, 101, 1, 9, PIL)
        b.box(x - 2, 11, 97, x + 2, 11, 101, TILE)
        spire_roof(b, x, 99, 2.5, 12, 4)
        b.set(x, 9, 102, "minecraft:polished_deepslate")
    for x in (CX - 3, CX + 3):
        b.line((x, 1, 116), (x + (2 if x > CX else -2), 8, 103), CHAIN)
    for x in range(CX - 2, CX + 3):
        for y in range(1, 4): b.set(x, y, Z0, AIR)
    # ---------------- the Tower of Justice
    TZ = 72
    for x in range(CX - 30, CX + 31):  # its plaza on the pillar
        for z in range(44, 100):
            if island_top(x, z)[1][1] <= 1: b.set(x, 0, z, "minecraft:polished_andesite")
    TW, TD = 16, 16
    levels = ((0, 30, 16), (30, 54, 13), (54, 76, 10))
    for (y0, y1, hw) in levels:
        b.walls(CX - hw, y0 + 1, TZ - hw, CX + hw, y1, TZ + hw, WHITE)
        b.box(CX - hw + 1, y0 + 1, TZ - hw + 1, CX + hw - 1, y1, TZ + hw - 1, AIR)
        for f in list(range(y0 + 6, y1, 6)) + ([y1] if y1 < levels[-1][1] else []):  # every floor, and the floor of the tier above
            b.box(CX - hw + 1, f, TZ - hw + 1, CX + hw - 1, f, TZ + hw - 1, TILE)
            b.box(CX + hw - 4, f, TZ - 1, CX + hw - 2, f, TZ + 1, AIR)
        for y in range(y0 + 1, y1 + 1): b.set(CX + hw - 1, y, TZ, ladder("west"))
        for (px, pz) in ((CX - hw, TZ - hw), (CX + hw, TZ - hw), (CX - hw, TZ + hw), (CX + hw, TZ + hw)):
            b.cyl(px, pz, 2, y0 + 1, y1 + 3, WHITE); spire_roof(b, px, pz, 3, y1 + 4, 7)
        facade(b, CX, TZ, hw, y0, y1, skip={("south", k) for k in range(-4, 5)} if y0 == 0 else {("south", 0)} if y0 == 54 else ())
        b.box(CX - hw - 1, y1 + 1, TZ - hw - 1, CX + hw + 1, y1 + 1, TZ + hw + 1, TILE)
        for x in range(CX - hw - 1, CX + hw + 2):
            b.set(x, y1 + 2, TZ - hw - 1, wall("onepiece:marine_brick_wall")); b.set(x, y1 + 2, TZ + hw + 1, wall("onepiece:marine_brick_wall"))
        for z in range(TZ - hw - 1, TZ + hw + 2):
            b.set(CX - hw - 1, y1 + 2, z, wall("onepiece:marine_brick_wall")); b.set(CX + hw + 1, y1 + 2, z, wall("onepiece:marine_brick_wall"))
    # front door facing the drawbridge: a pillared, stepped portal with the WG emblem on a blue medallion above
    for x in range(CX - 3, CX + 4):
        for y in range(1, 8): b.set(x, y, TZ + 16, AIR)
    for x in (CX - 4, CX + 4):
        b.column(x, TZ + 17, 1, 8, PIL); b.set(x, 9, TZ + 17, WHITE)
    for x in range(CX - 4, CX + 5):
        b.set(x, 8, TZ + 17, stairs(WHITE_ST, "north", "top")); b.set(x, 9, TZ + 17, WHITE)
    for i in range(-6, 7):
        for j in range(-6, 7):
            r2 = i * i + j * j
            if r2 <= 42: b.set(CX + i, 16 + j, TZ + 17, "minecraft:blue_concrete" if r2 <= 30 else "minecraft:gold_block")
    wg_emblem(b, CX, 16, TZ + 18, "minecraft:white_concrete", k=1.15)
    # Robin's balcony: a door from the top tier out onto the front terrace, facing the courthouse
    for y in (56, 57): b.set(CX, y, TZ + 10, AIR)
    b.set(CX, 56, TZ + 10, door("minecraft:dark_oak_door", "south", "lower")); b.set(CX, 57, TZ + 10, door("minecraft:dark_oak_door", "south", "upper"))
    # spire and the World Government flag on top (the one Usopp shoots down)
    t = spire_roof(b, CX, TZ, 9, 78, 10)
    for y in range(t, t + 10): b.set(CX, y, TZ, fence("dark_oak"))
    wg_flag(b, CX, t + 9, TZ + 1, 15, 11)
    # Lucci's room near the top: the boss fight hall, Robin's cuffs key chest
    b.chest(CX + 3, 61, TZ - 3, "hard", "west")
    for x in range(CX - 8, CX + 9, 4): b.set(x, 75, TZ, HANG)
    b.box(CX - 3, 55, TZ - 8, CX + 3, 55, TZ - 7, "minecraft:red_carpet")
    # ---------------- Bridge of Hesitation (north) to the Gates of Justice
    for z in range(22, 44):
        for x in range(CX - 3, CX + 4):
            b.set(x, 0, z, "minecraft:polished_andesite" if abs(x - CX) < 3 else "minecraft:stone_bricks")
        b.set(CX - 3, 1, z, wall("minecraft:stone_brick_wall")); b.set(CX + 3, 1, z, wall("minecraft:stone_brick_wall"))
        if z % 6 == 0:
            b.column(CX - 3, z, 2, 4, "minecraft:stone_brick_wall".replace("wall", "wall") and wall("minecraft:stone_brick_wall")); b.set(CX - 3, 5, z, LANTERN)
            b.column(CX + 3, z, 2, 4, wall("minecraft:stone_brick_wall")); b.set(CX + 3, 5, z, LANTERN)
    # The Gates of Justice: two towering doors set in a frame on the north rock
    GW, GH = 26, 80  # they tower over everything on the island
    b.box(CX - GW - 6, 1, 6, CX + GW + 6, GH + 8, 12, "minecraft:polished_deepslate")
    b.box(CX - GW, 1, 6, CX + GW, GH, 12, AIR)
    for x in range(CX - GW, CX + GW + 1):
        for y in range(1, GH + 1):
            edge = abs(x - CX) in (0, 1) or y in (1, GH) or abs(x - CX) == GW
            b.set(x, y, 9, "minecraft:iron_block" if edge else "minecraft:gray_concrete" if (x + y) % 9 else "minecraft:light_gray_concrete")
            b.set(x, y, 10, "minecraft:gray_concrete")
    for y in range(8, GH, 14):  # studs and bands across the doors
        for x in range(CX - GW + 1, CX + GW): b.set(x, y, 8, "minecraft:polished_deepslate")
    for side in (-1, 1):  # the World Government emblem on each door leaf, both faces
        wg_emblem(b, CX + side * 13, GH * 5 // 8, 11, "minecraft:white_concrete", k=2.0)
        wg_emblem(b, CX + side * 13, GH * 5 // 8, 8, "minecraft:white_concrete", k=2.0)
    for side in (-1, 1):  # the guardian figures on top
        sx = CX + side * (GW + 3)
        b.box(sx - 3, GH + 9, 7, sx + 3, GH + 12, 11, "minecraft:polished_deepslate")
        b.dome(sx, 9, GH + 13, 3, s="minecraft:polished_deepslate", onion=False, tip=None)
    b.box(CX - 8, GH + 9, 7, CX + 8, GH + 14, 11, "minecraft:polished_deepslate")
    for x in range(CX - 6, CX + 7):
        for y in range(GH + 10, GH + 14): b.set(x, y, 12, "minecraft:blue_concrete")
    # ---------------- people
    b.npc(CX, 55, TZ, "lucci", True)
    b.guards("cp_agent", ((CX - 6, TZ + 20), (CX + 6, TZ + 20), (CX - 8, TZ - 4), (CX + 8, TZ + 4)), y=1)
    b.guards("marine_rifle", ((CX - 8, 215), (CX + 8, 215)), y=1)
    # ---------------- furnished rooms: courthouse and every floor of the Tower of Justice
    import interiors as I
    r = I.Room(b, C0 + 1, 1, Z0 + 1, C1 - 1, Z1 - 1, 15, "justice", random.Random(8))
    r.wall_banners(4, 5); r.paintings(4); r.plants(6); r.lights(6)
    kinds = ("hall", "barracks", "armory", "library", "study", "dining", "kitchen", "barracks", "cell", "library", "bedroom", "treasure", "throne")
    k = 0
    for (y0, y1, hw) in levels:
        for f in range(y0 + 1, y1, 6):
            top = min(f + 5, y1) - 1
            I.furnish(b, CX - hw + 1, f, TZ - hw + 1, CX + hw - 1, TZ + hw - 1, top - f + 1, kinds[min(k, len(kinds) - 1)], "justice")
            k += 1
    b.set(CX, 55, TZ + 9, stairs(TILE_ST, "south"))  # step up to Robin's balcony door
    for y in (56, 57, 58): b.set(CX, y, TZ + 9, AIR)
    for y in (55, 56): b.set(CX, y, TZ, AIR)  # room for Lucci to stand
    return b, 0
