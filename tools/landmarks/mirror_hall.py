"""Katakuri's Mirror Hall on Cacao Island (Totto Land). Chocolate Town's sweet houses, a chocolate fountain and
cocoa trees surround Brulee's Mirror Hall: a round hall of tall mirrors (dark glass on black frames) with a domed
glass roof, mirror corridors off it, and Katakuri's mochi-white throne room at its heart. Upstairs is Katakuri's
secret snack room with the donut feast, his trophy room and Brulee's dressing room. A huge mochi tower rises out
of the roof. ~96 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "mirror_hall"
TITLE = "Katakuri's Mirror Hall"
CUTS = [3, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 48, 46
CHOC = "onepiece:chocolate_block"
CHOC_ST = "onepiece:chocolate_stairs"
COOKIE = "onepiece:cookie_bricks"
FROST = "onepiece:frosting_block"
MOCHI = "minecraft:white_wool"
MIRROR = "minecraft:tinted_glass"
FRAME = "minecraft:polished_blackstone"
CANDY = dict(wood="cherry", rug="pink", rug2="white", bed="pink", light="minecraft:pearlescent_froglight[axis=y]",
             accent=FROST, banner="pink", candle="pink")
MOCHI_T = dict(wood="dark_oak", rug="red", rug2="white", bed="red", light="minecraft:lantern", accent="minecraft:quartz_block",
               banner="red", candle="red")
R_HALL = 17
F1, F2, TOPY = 1, 11, 20


def sweet_house(b, x0, z0, w, d, rnd):
    wall = rnd.choice((CHOC, COOKIE, "minecraft:pink_terracotta", FROST))
    h = rnd.choice((5, 6, 9))
    b.box(x0, 0, z0, x0 + w - 1, 0, z0 + d - 1, "minecraft:cherry_planks")
    b.walls(x0, 1, z0, x0 + w - 1, h, z0 + d - 1, wall)
    b.box(x0 + 1, 1, z0 + 1, x0 + w - 2, h, z0 + d - 2, AIR)
    for x in range(x0 + 1, x0 + w - 1, 2):
        for z in (z0, z0 + d - 1): b.set(x, 2, z, "minecraft:pink_stained_glass_pane")
    for z in range(z0 + 1, z0 + d - 1, 2):
        for x in (x0, x0 + w - 1): b.set(x, 2, z, "minecraft:pink_stained_glass_pane")
    if h == 9:
        b.box(x0 + 1, 5, z0 + 1, x0 + w - 2, 5, z0 + d - 2, "minecraft:cherry_planks")
        for k in range(1, 5): b.set(x0 + 1, k, z0 + 1, "minecraft:ladder[facing=east,waterlogged=false]")
        b.set(x0 + 1, 5, z0 + 1, "minecraft:ladder[facing=east,waterlogged=false]")
        I.furnish(b, x0 + 1, 6, z0 + 1, x0 + w - 2, z0 + d - 2, 3, "bedroom", CANDY, seed=rnd.randint(0, 9999))
    I.furnish(b, x0 + 1, 1, z0 + 1, x0 + w - 2, z0 + d - 2, min(h - 1, 3), rnd.choice(("kitchen", "dining", "tavern", "storage")), CANDY,
              seed=rnd.randint(0, 9999))
    mx = x0 + w // 2
    b.set(mx, 1, z0 + d - 1, door("minecraft:cherry_door", "south", "lower")); b.set(mx, 2, z0 + d - 1, door("minecraft:cherry_door", "south", "upper"))
    # frosting roof with drips and a cherry on top
    b.box(x0 - 1, h + 1, z0 - 1, x0 + w, h + 1, z0 + d, FROST)
    b.box(x0, h + 2, z0, x0 + w - 1, h + 2, z0 + d - 1, "onepiece:frosting_slab[type=bottom,waterlogged=false]")
    for x in range(x0 - 1, x0 + w + 1):
        for z in (z0 - 1, z0 + d):
            if rnd.random() < 0.4: b.set(x, h, z, FROST)
    b.set(x0 + w // 2, h + 3, z0 + d // 2, "minecraft:red_concrete") if rnd.random() < 0.6 else b.set(x0 + w // 2, h + 3, z0 + d // 2, I.candle_str("pink", 3))


def build():
    rnd = random.Random(41)
    b = B()
    # ---------------- ground: Chocolate Town on Cacao Island
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            d = math.hypot(x - CX, z - CZ)
            b.set(x, 0, z, "minecraft:grass_block" if d > 28 and (x + z) % 9 else ("minecraft:mud_bricks" if d > 26 else "minecraft:polished_granite"))
    for x in range(N):  # cocoa-brick streets
        for z in range(N):
            if (abs(x - CX) <= 2 or abs(z - CZ) <= 2 or x % 24 in (0, 1) or z % 24 in (0, 1)) and math.hypot(x - CX, z - CZ) > 26: b.set(x, 0, z, "minecraft:mud_bricks")
    taken = set()
    for (x0, z0) in ((4, 4), (14, 4), (26, 4), (60, 4), (72, 4), (84, 4), (4, 14), (84, 14), (4, 60), (84, 60), (4, 72), (84, 72),
                     (4, 84), (14, 84), (26, 84), (60, 84), (72, 84), (84, 84), (16, 16), (72, 16), (16, 72), (72, 72)):
        w, d = rnd.randint(6, 8), rnd.randint(6, 8)
        if x0 + w >= N or z0 + d >= N: continue
        if any(math.hypot(x - CX, z - CZ) < 29 for x in (x0, x0 + w) for z in (z0, z0 + d)): continue
        sweet_house(b, x0, z0, w, d, rnd)
        for x in range(x0 - 1, x0 + w + 1):
            for z in range(z0 - 1, z0 + d + 1): taken.add((x, z))
    # cocoa trees, lollipops and candy canes in the gaps
    for i in range(90):
        x, z = rnd.randint(2, N - 3), rnd.randint(2, N - 3)
        if (x, z) in taken or math.hypot(x - CX, z - CZ) < 29 or b.get(x, 0, z) != "minecraft:grass_block" or b.get(x, 1, z) is not None: continue
        r = rnd.random()
        if r < 0.35:
            for y in range(1, 5): b.set(x, y, z, "minecraft:jungle_log[axis=y]")
            b.sphere(x, 6, z, 2, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]")
            b.set(x + 1, 3, z, "minecraft:cocoa[age=2,facing=west]")
        elif r < 0.6: b.set(x, 1, z, "onepiece:lollipop_flower")
        elif r < 0.8: b.set(x, 1, z, "onepiece:candy_cane_sprout")
        else: b.set(x, 1, z, rnd.choice(("minecraft:pink_tulip", "minecraft:allium", "minecraft:peony[half=lower]")))
    # the chocolate fountain on the south plaza
    FX, FZ = CX, CZ + 32
    b.cyl(FX, FZ, 4.5, 0, 1, COOKIE); b.cyl(FX, FZ, 3.5, 1, 1, "minecraft:brown_concrete_powder" if False else "minecraft:brown_concrete")
    b.cyl(FX, FZ, 1.5, 1, 4, CHOC); b.cyl(FX, FZ, 2.5, 5, 5, CHOC); b.cyl(FX, FZ, 1.0, 6, 7, CHOC)
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(FX + dx, 4, FZ + dz, "minecraft:brown_terracotta")
    # ---------------- Mirror Hall: round hall of mirrors, two floors
    b.cyl(CX, CZ, R_HALL + 1, 0, 0, "minecraft:polished_blackstone_bricks")
    for x in range(CX - R_HALL, CX + R_HALL + 1):
        for z in range(CZ - R_HALL, CZ + R_HALL + 1):
            d = math.hypot(x - CX, z - CZ)
            if d <= R_HALL - 1: b.set(x, 0, z, "minecraft:quartz_block" if (x + z) % 2 else "minecraft:black_concrete")  # checkered floor
            if R_HALL - 1 < d <= R_HALL:
                ang = math.degrees(math.atan2(z - CZ, x - CX)) % 360
                pier = (ang % 12) < 3
                for y in range(1, TOPY + 1):
                    if y in (F2 - 1, TOPY): b.set(x, y, z, "minecraft:polished_blackstone_bricks")
                    elif pier: b.set(x, y, z, FRAME if y % 9 else "minecraft:gilded_blackstone")
                    else: b.set(x, y, z, MIRROR)
    b.cyl(CX, CZ, R_HALL - 1, F2 - 1, F2 - 1, "minecraft:dark_oak_planks")
    b.cyl(CX, CZ, 5, F2 - 1, F2 - 1, AIR)  # balcony well over the throne
    b.cyl(CX, CZ, 5.6, F2, F2, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]", hollow=True)
    b.dome(CX, CZ, TOPY + 1, R_HALL, h=10, s="minecraft:pink_stained_glass", tip=None, hollow=True)
    for a in range(0, 360, 30):  # dome ribs
        t = math.radians(a)
        for k in range(R_HALL + 1):
            yy = int(10 * math.sqrt(max(0, 1 - (k / R_HALL) ** 2)))
            b.set(round(CX + k * math.cos(t)), TOPY + 1 + yy, round(CZ + k * math.sin(t)), "minecraft:gold_block" if k % 4 == 0 else FRAME)
    # entrance hall to the south, with mirror-door frames
    for z in range(CZ + R_HALL - 1, CZ + R_HALL + 7):
        for x in range(CX - 4, CX + 5):
            for y in range(1, 8): b.set(x, y, z, AIR if abs(x - CX) < 4 else FRAME)
            b.set(x, 8, z, "minecraft:polished_blackstone_bricks"); b.set(x, 0, z, "minecraft:quartz_block")
    for y in range(1, 7):
        for x in (CX - 3, CX + 3): b.set(x, y, CZ + R_HALL + 6, MIRROR)
    for x in range(CX - 2, CX + 3): b.set(x, 7, CZ + R_HALL + 6, "minecraft:gilded_blackstone")
    for z in range(CZ + 5, CZ + R_HALL + 7): b.set(CX, 1, z, "minecraft:red_carpet")
    # floor 1: Katakuri's mochi throne in the middle, four mirror side rooms in the hall rim
    b.cyl(CX, CZ, 4.5, 1, 1, "minecraft:white_concrete")
    for (dx, dz) in ((0, -2), (-1, -2), (1, -2)): b.set(CX + dx, 2, CZ + dz, "minecraft:quartz_block")
    b.set(CX, 2, CZ - 1, stairs("minecraft:quartz_stairs", "north")); b.set(CX, 3, CZ - 2, "minecraft:quartz_block"); b.set(CX, 4, CZ - 2, "minecraft:quartz_block")
    for i in range(30):  # mochi blobs dripping and coiling round the throne
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(3, 6)
        b.sphere(round(CX + rr * math.cos(a)), 1, round(CZ + rr * math.sin(a)), rnd.uniform(0.8, 1.6), MOCHI, upper=True)
    for (x0, z0, x1, z1, kind) in ((CX - 14, CZ - 8, CX - 7, CZ + 8, "armory"), (CX + 7, CZ - 8, CX + 14, CZ + 8, "library"),
                                   (CX - 8, CZ - 14, CX + 8, CZ - 7, "treasure")):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if math.hypot(x - CX, z - CZ) < R_HALL - 1 and (x in (x0, x1) or z in (z0, z1)):
                    for y in range(1, F2 - 1): b.set(x, y, z, MIRROR if (x + z) % 3 else FRAME)
        dx, dz = ((x0 + x1) // 2, z1) if kind == "treasure" else ((x1 if x0 < CX else x0), (z0 + z1) // 2)
        for y in (1, 2, 3): b.set(dx, y, dz, AIR)
        I.furnish(b, x0 + 1, 1, z0 + 1, x1 - 1, z1 - 1, F2 - 3, kind, MOCHI_T)
    # stairs up to the balcony floor (south-west)
    for i in range(F2 - 1):
        for w in (0, 1): b.set(CX - 12 + i, 1 + i, CZ + 10 + w, stairs("minecraft:polished_blackstone_brick_stairs", "east"))
        for w in (0, 1): b.set(CX - 12 + i, F2 - 1, CZ + 10 + w, AIR) if i >= 2 else None
    # floor 2: the secret snack room (donut feast), trophy room, Brulee's dressing room
    y = F2
    for x in range(CX - R_HALL + 2, CX + R_HALL - 1):
        if abs(x - CX) > 6: [b.set(x, yy, CZ, FRAME) for yy in range(F2, TOPY)]
    for z in range(CZ - R_HALL + 2, CZ):
        [b.set(CX, yy, z, FRAME) for yy in range(F2, TOPY) if abs(z - CZ) > 6]
    for (xx, zz) in ((CX - 9, CZ), (CX + 9, CZ), (CX, CZ - 9)):
        for yy in (F2, F2 + 1, F2 + 2): b.set(xx, yy, zz, AIR)
    r = I.furnish(b, CX - 12, F2, CZ + 1, CX + 12, CZ + 12, TOPY - F2 - 1, "banquet", CANDY)
    for x in range(CX - 6, CX + 7, 2):  # piles of donuts (cakes) and tea on the long table
        if b.get(x, F2, CZ + 12) is None: b.set(x, F2, CZ + 12, "minecraft:cake[bites=0]")
    I.furnish(b, CX - 12, F2, CZ - 12, CX - 1, CZ - 1, TOPY - F2 - 1, "treasure", MOCHI_T)
    I.furnish(b, CX + 1, F2, CZ - 12, CX + 12, CZ - 1, TOPY - F2 - 1, "bedroom", CANDY)
    # ---------------- the mochi tower rising from the roof
    for y in range(TOPY + 4, TOPY + 30):
        rr = 3.2 + 1.2 * math.sin(y * 0.35)
        b.cyl(CX, CZ, rr, y, y, MOCHI)
    b.sphere(CX, TOPY + 31, CZ, 4, MOCHI)
    for k in range(6):  # mochi arms reaching out
        a = math.radians(k * 60 + 20); y0 = TOPY + 10 + k * 3
        for s in range(10):
            b.sphere(round(CX + (3 + s) * math.cos(a)), y0 + int(math.sin(s / 9 * math.pi) * 3), round(CZ + (3 + s) * math.sin(a)), 1.2, MOCHI)
    # ---------------- people
    b.npc(CX, 3, CZ - 1, "katakuri", True)
    b.chest(CX - 3, 1, CZ - 12, "candy", "south"); b.chest(CX - 10, F2, CZ - 10, "candy", "east"); b.chest(CX + 3, 1, CZ - 12, "candy", "south")
    b.guards("homie", ((CX - 4, CZ + R_HALL + 4), (CX + 4, CZ + R_HALL + 4), (CX - 10, CZ + 6), (CX + 10, CZ + 6)))
    b.guards("homie", ((CX, CZ + 30), (CX - 20, CZ + 30), (CX + 20, CZ + 30)))
    return b, 0
