"""Whole Cake Chateau: Big Mom's towering castle at the heart of Whole Cake Island, built like a giant five-layer cake
that rises like a mountain over Sweet City. Frosting drips down every layer, a jam-and-cream filling stripe runs round
each one, castle turrets with pointed spires stand on every ledge between strawberries and candles, and the top
layer is crowned by the chateau's keep and its tall spire. An arched candy-cane gate, a checkered grand hall, Big
Mom's throne room, the treasure room with the Road Poneglyph, and Sweet City around it: cake houses, lollipop trees,
candy-cane lamps and the Seducing Woods. ~210 x 210, ~106 tall. Ground = y 0, the front gate faces -z."""
import math, random
from canvas import *

SID = "whole_cake_chateau"
TITLE = "Whole Cake Chateau"
CUTS = [20, 34]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

CX, CZ = 105, 108
FROST = "onepiece:frosting_block"
FROST_ST = "onepiece:frosting_stairs"
FROST_SL = "onepiece:frosting_slab"
CHOC = "onepiece:chocolate_block"
CHOC_ST = "onepiece:chocolate_stairs"
COOKIE = "onepiece:cookie_bricks"
COOKIE_ST = "onepiece:cookie_brick_stairs"
CANE = "onepiece:candy_cane_block"
GLASS = "minecraft:pink_stained_glass"
# (radius, height, wall, inner floor)
TIERS = ((40, 17, CHOC, "minecraft:pink_concrete"), (33, 16, "minecraft:pink_terracotta", "minecraft:white_concrete"),
         (26, 15, COOKIE, "minecraft:red_wool"), (19, 14, "minecraft:white_terracotta", "minecraft:pink_wool"),
         (12, 13, "minecraft:pink_concrete", "minecraft:white_wool"))


def strawberry(b, x, y, z, r=2.2):
    b.sphere(x, y + r, z, r, "minecraft:red_concrete", ry=r * 1.2)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)): b.set(x + dx, round(y + r * 2.2), z + dz, "minecraft:lime_concrete")
    for a in range(0, 360, 60):
        t = math.radians(a); b.set(round(x + r * math.cos(t)), round(y + r), round(z + r * math.sin(t)), "minecraft:yellow_concrete")


def candle_big(b, x, y, z, h, color):
    for yy in range(y, y + h): b.set(x, yy, z, color if (yy - y) % 4 < 2 else "minecraft:white_concrete")
    b.set(x, y + h, z, "minecraft:black_wool" if False else "minecraft:shroomlight"); b.set(x, y + h + 1, z, "minecraft:orange_stained_glass")


def cone(b, x, y, z, r, h, colors, tip="minecraft:gold_block"):
    """A pointed turret roof: rings shrinking from radius r to a point over h layers, striped in `colors`."""
    for i in range(h):
        rr = max(0.4, r * (1 - i / h))
        b.cyl(x, z, rr, y + i, y + i, colors[(i // 2) % len(colors)])
    b.set(x, y + h, z, tip); b.set(x, y + h + 1, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")


def turret(b, x, y, z, r, h, body, rnd):
    """A round castle turret standing on a ledge: body with window slits, a frosting cornice with drips, pointed spire."""
    b.cyl(x, z, r, y, y + h - 1, body, hollow=True)
    b.disk(x, y + h - 1, z, max(1, int(r) - 1), body)
    for a in range(0, 360, 90):
        t = math.radians(a + 45)
        for yy in (y + 2, y + 3, y + h - 5, y + h - 4):
            if y + 1 < yy < y + h - 2: b.set(round(x + r * math.cos(t)), yy, round(z + r * math.sin(t)), GLASS)
    b.cyl(x, z, r + 1, y + h, y + h, FROST, hollow=True)
    b.disk(x, y + h, z, int(r), FROST)
    for a in range(0, 360, 30):
        t = math.radians(a)
        dx, dz = round(x + (r + 1) * math.cos(t)), round(z + (r + 1) * math.sin(t))
        for yy in range(y + h - rnd.choice((1, 1, 2, 3)), y + h): b.set(dx, yy, dz, FROST)
    cone(b, x, y + h + 1, z, r + 0.6, int(r * 3.4) + 3, ("minecraft:pink_concrete", "minecraft:magenta_concrete") if rnd.random() < 0.5
         else ("minecraft:pink_concrete", "minecraft:white_concrete"))


def lollipop(b, x, z, h, color, rnd):
    for y in range(1, h): b.set(x, y, z, "minecraft:birch_fence" if y > 1 else "minecraft:white_concrete")
    b.sphere(x, h + 2, z, 2.6, f"minecraft:{color}_concrete")
    for a in range(0, 360, 40):
        t = math.radians(a); b.set(round(x + 2.6 * math.cos(t)), h + 2, round(z + 2.6 * math.sin(t)), "minecraft:white_concrete")


def cake_house(b, x, z, w, d, h, rnd):
    wallm = rnd.choice((CHOC, COOKIE, "minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:yellow_terracotta"))
    b.box(x, 0, z, x + w, 0, z + d, "minecraft:white_concrete")
    b.walls(x, 1, z, x + w, h, z + d, wallm)
    b.box(x + 1, 1, z + 1, x + w - 1, h, z + d - 1, AIR)
    roof = rnd.choice(("pink", "white", "lime", "light_blue", "yellow"))
    for i in range(0, min(w, d) // 2 + 2):
        y = h + 1 + i
        x0, x1, z0, z1 = x - 1 + i, x + w + 1 - i, z - 1 + i, z + d + 1 - i
        if x0 > x1 or z0 > z1: break
        b.walls(x0, y, z0, x1, y, z1, f"minecraft:{roof}_concrete")
        if x1 - x0 <= 1 or z1 - z0 <= 1: b.box(x0, y, z0, x1, y, z1, f"minecraft:{roof}_concrete")
    for xx in range(x, x + w + 1):  # frosting drip under the roof
        if rnd.random() < 0.6: b.set(xx, h, z, FROST)
        if rnd.random() < 0.6: b.set(xx, h, z + d, FROST)
    b.set(x + w // 2, 1, z, AIR); b.set(x + w // 2, 2, z, AIR)
    for xx in range(x + 2, x + w - 1, 3): b.set(xx, 3, z, GLASS); b.set(xx, 3, z + d, GLASS)
    b.set(x + 1, 1, z + d - 1, "minecraft:cake"); b.set(x + w - 1, h, z + d - 1, HANG)


def build():
    rnd = random.Random(7)
    b = B()
    # ---------------- ground: island meadow and the city ring road
    for x in range(0, 211):
        for z in range(0, 217):
            d = math.hypot(x - CX, z - CZ); a = math.atan2(z - CZ, x - CX)
            r = 100 + 4 * math.sin(4 * a) + 2 * math.sin(9 * a)
            if d > r: continue
            for y in range(-4, 0): b.set(x, y, z, "minecraft:dirt")
            if 52 <= d <= 58: s = "minecraft:pink_concrete" if int(d) % 2 else "minecraft:white_concrete"
            elif d < 52: s = "minecraft:pink_concrete" if (x // 3 + z // 3) % 2 else "minecraft:white_concrete"
            else: s = "minecraft:grass_block"
            b.set(x, 0, z, s)
            if s == "minecraft:grass_block" and d > 62:
                rr = rnd.random()
                if rr < 0.03: b.set(x, 1, z, "onepiece:lollipop_flower")
                elif rr < 0.05: b.set(x, 1, z, "onepiece:frost_bloom")
                elif rr < 0.06: b.set(x, 1, z, "onepiece:candy_cane_sprout")
                elif rr < 0.12: b.set(x, 1, z, "minecraft:short_grass")
    # main avenue to the gate
    for z in range(4, CZ - 44):
        for x in range(CX - 4, CX + 5): b.set(x, 0, z, "minecraft:pink_concrete" if (z // 2) % 2 else "minecraft:white_concrete")
    # ---------------- the cake
    y = 0
    floors = []
    for ti, (r, h, wallm, floorm) in enumerate(TIERS):
        b.disk(CX, y, CZ, r, floorm if ti else CHOC)
        if ti == 0:
            for x in range(CX - r, CX + r + 1):
                for z in range(CZ - r, CZ + r + 1):
                    if math.hypot(x - CX, z - CZ) < r - 1: b.set(x, y, z, "minecraft:pink_concrete" if (x // 4 + z // 4) % 2 else "minecraft:white_concrete")
        b.cyl(CX, CZ, r, y + 1, y + h, wallm, hollow=True)
        # a jam and cream filling stripe halfway up
        b.cyl(CX, CZ, r, y + h // 2, y + h // 2, "minecraft:red_concrete" if ti % 2 == 0 else "minecraft:white_concrete", hollow=True)
        # windows: tall arched slits in pairs above and below the filling, framed by pale jambs and a keystone
        jamb = "minecraft:pink_concrete" if "white" in wallm else "minecraft:white_concrete"
        n = max(8, int(2 * math.pi * r / 7))
        for k in range(n):
            t = 2 * math.pi * k / n
            wx, wz = round(CX + r * math.cos(t)), round(CZ + r * math.sin(t))
            for (ya, yb) in ((y + 3, y + h // 2 - 1), (y + h // 2 + 2, y + h - 3)):
                for yy in range(ya, yb + 1): b.set(wx, yy, wz, GLASS)
                b.set(wx, yb + 1, wz, "minecraft:gold_block" if ti % 2 == 0 else jamb)
                for dt in (-1.0 / r, 1.0 / r):
                    jx, jz = round(CX + r * math.cos(t + dt)), round(CZ + r * math.sin(t + dt))
                    if (jx, jz) == (wx, wz): continue
                    for yy in range(ya, yb + 2): b.set(jx, yy, jz, jamb)
        # frosting roof: the ring between this layer and the next, with drips down the wall
        nr = TIERS[ti + 1][0] if ti + 1 < len(TIERS) else 0
        b.disk(CX, y + h + 1, CZ, r, FROST)
        b.cyl(CX, CZ, r + 1, y + h, y + h, FROST, hollow=True)
        for k in range(int(2 * math.pi * (r + 1))):
            t = k / (r + 1)
            dx, dz = round(CX + (r + 1) * math.cos(t)), round(CZ + (r + 1) * math.sin(t))
            ln = rnd.choice((1, 1, 2, 3, 4, 5))
            for yy in range(y + h - ln, y + h): b.set(dx, yy, dz, FROST)
        b.cyl(CX, CZ, r + 1, y + h + 2, y + h + 2, FROST_SL and slab(FROST_SL), hollow=True)
        # on the ledge: castle turrets with pointed spires, strawberries and candles between them
        if nr:
            ledge = (r + nr) / 2
            cnt = max(8, int(2 * math.pi * ledge / 11))
            cnt += cnt % 2
            for k in range(cnt):
                t = 2 * math.pi * (k + 0.5) / cnt + ti * 0.35
                sx, sz = round(CX + ledge * math.cos(t)), round(CZ + ledge * math.sin(t))
                if k % 2 == 0:
                    turret(b, sx, y + h + 2, sz, 2.6 if ti < 2 else 2.1, (12, 11, 10, 8)[ti],
                           rnd.choice((CANE, "minecraft:white_concrete", "minecraft:pink_concrete", "minecraft:white_terracotta")), rnd)
                elif k % 4 == 1: strawberry(b, sx, y + h + 2, sz, 2.0 if ti < 3 else 1.6)
                else: candle_big(b, sx, y + h + 2, sz, 5 if ti < 3 else 4, rnd.choice(("minecraft:red_concrete", "minecraft:pink_concrete", "minecraft:light_blue_concrete")))
        floors.append((y, r, h))
        y += h + 1
    top_y = y
    # the very top: the chateau's keep with its tall spire, strawberries and candles round it
    KR = 8
    b.cyl(CX, CZ, KR, top_y + 1, top_y + 12, "minecraft:white_terracotta", hollow=True)
    b.cyl(CX, CZ, KR, top_y + 6, top_y + 6, "minecraft:red_concrete", hollow=True)
    for k in range(8):
        t = 2 * math.pi * (k + 0.5) / 8
        wx, wz = round(CX + KR * math.cos(t)), round(CZ + KR * math.sin(t))
        for yy in (top_y + 3, top_y + 4, top_y + 8, top_y + 9, top_y + 10): b.set(wx, yy, wz, GLASS)
    b.disk(CX, top_y + 12, CZ, KR, FROST)
    b.cyl(CX, CZ, KR + 1, top_y + 12, top_y + 12, FROST, hollow=True)
    for k in range(int(2 * math.pi * (KR + 1))):
        t = k / (KR + 1)
        dx, dz = round(CX + (KR + 1) * math.cos(t)), round(CZ + (KR + 1) * math.sin(t))
        for yy in range(top_y + 12 - rnd.choice((1, 2, 3)), top_y + 12): b.set(dx, yy, dz, FROST)
    cone(b, CX, top_y + 13, CZ, KR + 0.5, 16, ("minecraft:pink_concrete", "minecraft:magenta_concrete"))
    for k in range(8):
        t = 2 * math.pi * (k + 0.25) / 8
        sx, sz = round(CX + 10.2 * math.cos(t)), round(CZ + 10.2 * math.sin(t))
        if k % 2: strawberry(b, sx, top_y + 1, sz, 1.5)
        else: candle_big(b, sx, top_y + 1, sz, 4, rnd.choice(("minecraft:red_concrete", "minecraft:light_blue_concrete")))
    # ---------------- inside
    # front gate: chocolate door frame with candy-cane pillars and stairs
    r0 = TIERS[0][0]
    for x in range(CX - 5, CX + 6):
        for yy in range(1, 11):
            for z in range(CZ - r0 - 1, CZ - r0 + 3):
                if b.get(x, yy, z) not in (None, AIR) and math.hypot(x - CX, z - CZ) >= r0 - 1.5: b.set(x, yy, z, AIR)
    for x in (CX - 6, CX + 6): b.column(x, CZ - r0 - 1, 1, 12, CANE, cap="minecraft:gold_block")
    for x in range(CX - 6, CX + 7): b.set(x, 12, CZ - r0 - 1, CANE)
    b.arch_x(CX - 6, CX + 6, CZ - r0 - 1, 12, 0, CANE)  # a round candy-cane arch over the lintel, filled with frosting
    for x in range(CX - 5, CX + 6):
        for yy in range(13, 12 + int(round(math.sqrt(max(0, 36 - (x - CX) ** 2)) * 0.6))): b.set(x, yy, CZ - r0 - 1, FROST)
    b.set(CX, 17, CZ - r0 - 1, "minecraft:gold_block")
    # grand hall columns (layer 1) and a chandelier
    for k in range(12):
        t = 2 * math.pi * k / 12
        px, pz = round(CX + 28 * math.cos(t)), round(CZ + 28 * math.sin(t))
        b.column(px, pz, 1, TIERS[0][1], "minecraft:quartz_pillar[axis=y]")
    for k in range(16):
        t = 2 * math.pi * k / 16
        b.set(round(CX + 8 * math.cos(t)), TIERS[0][1], round(CZ + 8 * math.sin(t)), HANG)
    # every floor gets a ceiling (= next floor) with a ladder shaft at the back
    LX, LZ = CX, CZ + 8
    for (fy, r, h) in floors[1:]:
        b.disk(CX, fy, CZ, r - 1, b.get(CX, fy, CZ) or "minecraft:white_concrete")
    for yy in range(1, top_y + 1):
        b.set(LX, yy, LZ, "minecraft:quartz_pillar[axis=y]"); b.set(LX, yy, LZ - 1, ladder("north"))
    # roof hatch so the top crown can be reached
    b.set(LX, top_y, LZ - 1, ladder("north")); b.set(LX, top_y + 1, LZ - 1, AIR)
    # layer 2: Big Mom's throne room
    f2 = floors[1][0]
    b.box(CX - 6, f2 + 1, CZ + 22, CX + 6, f2 + 2, CZ + 30, "minecraft:gold_block")
    b.box(CX - 4, f2 + 3, CZ + 26, CX + 4, f2 + 3, CZ + 29, "minecraft:red_wool")
    b.box(CX - 5, f2 + 3, CZ + 30, CX + 5, f2 + 11, CZ + 31, "minecraft:red_wool")
    for x in (CX - 5, CX + 5): b.box(x, f2 + 3, CZ + 26, x, f2 + 6, CZ + 30, "minecraft:gold_block")
    for z in range(CZ - 30, CZ + 22): b.set(CX, f2 + 1, z, "minecraft:red_carpet"); b.set(CX - 1, f2 + 1, z, "minecraft:red_carpet"); b.set(CX + 1, f2 + 1, z, "minecraft:red_carpet")
    for z in range(CZ - 24, CZ + 20, 6):
        for x in (CX - 8, CX + 8): b.set(x, f2 + 1, z, "minecraft:cake"); b.set(x, f2 + TIERS[1][1], z, HANG)
    b.chest(CX + 8, f2 + 1, CZ + 26, "legendary", "west")
    # layer 3: treasure room and the Road Poneglyph
    f3 = floors[2][0]
    b.box(CX - 1, f3 + 1, CZ - 18, CX + 1, f3 + 1, CZ - 16, CHOC)
    b.set(CX, f3 + 2, CZ - 17, "onepiece:poneglyph"); b.set(CX, f3 + 3, CZ - 17, "onepiece:poneglyph")
    b.chest(CX - 6, f3 + 1, CZ - 14, "candy", "east"); b.chest(CX + 6, f3 + 1, CZ - 14, "candy", "west")
    for k in range(10):
        t = 2 * math.pi * k / 10
        b.set(round(CX + 22 * math.cos(t)), f3 + 1, round(CZ + 22 * math.sin(t)), "minecraft:gold_block")
    # ---------------- Sweet City
    for k in range(34):
        a = 2 * math.pi * k / 34 + rnd.uniform(-0.04, 0.04)
        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.18: continue  # the avenue
        rr = rnd.uniform(64, 74)
        w, d = rnd.randint(7, 10), rnd.randint(6, 9)
        x, z = round(CX + rr * math.cos(a) - w / 2), round(CZ + rr * math.sin(a) - d / 2)
        cake_house(b, x, z, w, d, rnd.randint(5, 8), rnd)
    for k in range(28):
        a = 2 * math.pi * k / 28
        x, z = round(CX + 55 * math.cos(a)), round(CZ + 55 * math.sin(a))
        b.column(x, z, 1, 5, CANE); b.set(x, 6, z, HANG if False else "minecraft:pearlescent_froglight[axis=y]")
    colors = ("pink", "magenta", "light_blue", "yellow", "lime", "orange", "purple")
    for i in range(60):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(78, 94)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if abs(x - CX) < 7 and z < CZ: continue
        if rnd.random() < 0.55:
            lollipop(b, x, z, rnd.randint(5, 9), rnd.choice(colors), rnd)
        else:  # Seducing Woods tree
            h = rnd.randint(7, 11)
            for y in range(1, h): b.set(x, y, z, "minecraft:oak_log[axis=y]")
            b.set(x, h // 2, z - 1, "minecraft:carved_pumpkin[facing=north]") if rnd.random() < 0.25 else None
            b.sphere(x, h + 1, z, 3.6, "minecraft:cherry_leaves[distance=7,persistent=true,waterlogged=false]" if rnd.random() < 0.5 else "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.6)
    # ---------------- people
    b.npc(CX, f2 + 3, CZ + 24, "big_mom", True)
    b.guards("homie", ((CX - 8, CZ - r0 - 6), (CX + 8, CZ - r0 - 6), (CX - 20, CZ - 20), (CX + 20, CZ - 20), (CX, CZ + 20)))
    b.guards("homie", ((CX - 10, CZ - 10), (CX + 10, CZ + 10)), y=f2 + 1)
    b.guards("donquixote", ((CX - 8, CZ - 8), (CX + 8, CZ - 8)), y=f3 + 1)
    # ---------------- furnished rooms
    import interiors as I
    (y0, r0_, h0), (y1, r1, h1), (y2, r2, h2), (y3, r3, h3), (y4, r4, h4) = floors
    r = I.Room(b, CX - 27, y0 + 1, CZ - 27, CX + 27, CZ + 27, h0, "candy", random.Random(21))
    r.plants(4)
    I.furnish(b, CX - 22, y0 + 1, CZ - 6, CX + 22, CZ + 6, h0, "banquet", "candy")
    r.scatter(("minecraft:cake", "onepiece:frosting_block", "onepiece:candy_cane_block", "onepiece:lollipop_flower", "minecraft:pink_candle[candles=4,lit=true,waterlogged=false]"), 40)
    r = I.Room(b, CX - 22, y1 + 1, CZ - 22, CX + 22, CZ + 22, h1, "royal", random.Random(22))
    r.scatter(("minecraft:cake", "onepiece:feast_table[facing=north]", "minecraft:potted_flowering_azalea_bush", "minecraft:gold_block", "minecraft:pink_candle[candles=3,lit=true,waterlogged=false]"), 30)
    I.furnish(b, CX - 17, y2 + 1, CZ - 17, CX + 17, CZ + 17, h2, "treasure", "candy")
    I.subdivide(b, CX - 12, y3 + 1, CZ - 12, CX + 12, CZ + 12, h3, COOKIE, ("bedroom", "kitchen", "library", "bath"), "candy", cell=12,
                keepout=((LX - 2, LZ - 3, LX + 2, LZ + 1),), seed=5)
    I.furnish(b, CX - 7, y4 + 1, CZ - 7, CX + 7, CZ + 7, h4, "study", "candy")
    I.furnish(b, CX - 5, top_y + 1, CZ - 5, CX + 5, CZ + 5, 10, "bedroom", "candy")
    return b, 0
