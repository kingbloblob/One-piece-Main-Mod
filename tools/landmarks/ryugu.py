"""Fish-Man Island and the Ryugu Palace: a giant air bubble on the deep sea floor holding the island town, with the
coral-and-pearl Ryugu Palace in its own smaller bubble sitting on top of the island's bubble (as in the show: the
palace is wrapped in its own bubble layers and the only way in is the connection corridor, here a glass tube running
up the palace hill from the ring road). King Neptune's throne hall, shell houses, the Sea Forest garden with the
Poneglyph, and a coral reef outside. ~150 x 150. Sea floor = y 0; the bubbles are sunk into the floor so their tops
stay under the sea."""
import math, random
from canvas import *

SID = "ryugu_palace"
TITLE = "Fish-Man Island (Ryugu Palace)"
CUTS = [0, 10]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

BUBBLE = "onepiece:bubble_glass"
CORAL = "onepiece:coral_bricks"
CORAL_ST = "onepiece:coral_brick_stairs"
CORAL_W = "onepiece:coral_brick_wall"
PEARL = "onepiece:pearl_block"
PEARL_ST = "onepiece:pearl_stairs"
ROOF = "minecraft:prismarine_bricks"
ROOF_ST = "minecraft:prismarine_brick_stairs"
LAMP = "onepiece:bubble_lamp[hanging=false]"
HLAMP = "onepiece:bubble_lamp[hanging=true]"
C = 75
RX, RY, BASE = 70, 36, -30     # island bubble radius, height above its base, base y
HILL = -14                      # palace plateau
PR, PCY = 28, -6                # the palace bubble: radius and centre height (it bulges out of the island bubble's top)
PLAT = 27.5                     # radius of the palace plateau


def shell_house(b, x, y, z, r, rnd):
    mat = rnd.choice((PEARL, CORAL, "minecraft:prismarine", "minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:yellow_terracotta"))
    b.cyl(x, z, r, y, y + 4, mat, hollow=True)
    b.dome(x, z, y + 5, r, s=mat, onion=True, tip=PEARL)
    b.disk(x, y, z, r - 1, "minecraft:smooth_sandstone")
    b.set(x, y + 1, z + r, AIR); b.set(x, y + 2, z + r, AIR)
    for a in (45, 135, 225, 315):
        t = math.radians(a); b.set(round(x + r * math.cos(t)), y + 3, round(z + r * math.sin(t)), pane_of("minecraft:light_blue_stained_glass_pane"))
    b.set(x, y + 4, z, HLAMP); b.set(x - 1, y + 1, z - 1, BARREL)
    import interiors as I
    I.furnish(b, x - r + 2, y + 1, z - r + 2, x + r - 2, z + r - 2, 4, rnd.choice(("bedroom", "kitchen", "tavern", "storage")), "sea", seed=rnd.randint(0, 9999), lit=False)


def build():
    rnd = random.Random(21)
    b = B()
    # ---------------- outside: coral reef ring and kelp on the sea floor
    corals = ("tube", "brain", "bubble", "fire", "horn")
    for x in range(C - RX - 8, C + RX + 9):
        for z in range(C - RX - 8, C + RX + 9):
            d = math.hypot(x - C, z - C)
            if RX + 1 < d <= RX + 8 and rnd.random() < 0.55:
                k = rnd.choice(corals)
                r = rnd.random()
                if r < 0.4: b.set(x, 0, z, f"minecraft:{k}_coral_block")
                if r < 0.15: b.set(x, 1, z, f"minecraft:{k}_coral_block"); b.set(x, 2, z, f"minecraft:{k}_coral[waterlogged=true]")
                elif r < 0.6: b.set(x, 1, z, f"minecraft:{k}_coral_fan[waterlogged=true]")
                elif r < 0.8:
                    for y in range(1, rnd.randint(3, 9)): b.set(x, y, z, "minecraft:kelp_plant")
                else: b.set(x, 1, z, "minecraft:seagrass")
    # ---------------- the bubble: glass shell, air inside, floor of white sand
    def in_b(x, y, z):
        if y < BASE: return False
        return ((x - C) / RX) ** 2 + ((y - BASE) / RY) ** 2 + ((z - C) / RX) ** 2 <= 1.0

    def in_p(x, y, z):
        return y > HILL and (x - C) ** 2 + (y - PCY) ** 2 + (z - C) ** 2 <= PR * PR

    b.shape(lambda x, y, z: in_b(x, y, z) or in_p(x, y, z), C - RX - 1, BASE, C - RX - 1, C + RX + 1, PCY + PR + 1, C + RX + 1, BUBBLE, interior=AIR)
    # the palace bubble's own skin inside the island bubble: a glass wall round the palace plateau
    for x in range(C - PR - 1, C + PR + 2):
        for z in range(C - PR - 1, C + PR + 2):
            for y in range(HILL + 1, PCY + PR):
                if in_p(x, y, z) and in_b(x, y, z) and not all(in_p(x + dx, y + dy, z + dz) for dx, dy, dz in
                                                               ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1))):
                    b.set(x, y, z, BUBBLE)
    # bubble floor (sand) and the island ground with a central hill
    for x in range(C - RX, C + RX + 1):
        for z in range(C - RX, C + RX + 1):
            d = math.hypot(x - C, z - C)
            if not in_b(x, BASE + 1, z): continue
            top = HILL if d < PLAT else max(BASE + 2, HILL - int((d - PLAT) * 2.0))  # plateau and its steep coral cliff
            b.set(x, BASE, z, BUBBLE)
            for y in range(BASE + 1, top): b.set(x, y, z, "minecraft:sandstone" if d < PLAT - 1 or y % 4 else "minecraft:prismarine")
            b.set(x, top, z, "minecraft:white_concrete_powder" if d > 34.5 else CORAL if d >= PLAT else "minecraft:smooth_sandstone" if d > 22 else PEARL)
            if PLAT <= d <= 34.5:  # the cliff face: coral brick and prismarine, not bare sand
                for y in range(top - 3, top): b.set(x, y, z, CORAL if (x * 3 + y + z) % 7 else "minecraft:prismarine")
            if d > 40 and rnd.random() < 0.02: b.set(x, top + 1, z, LAMP)
    # a ring road and a canal of real water around the palace hill (held in a basin)
    for x in range(C - 50, C + 51):
        for z in range(C - 50, C + 51):
            d = math.hypot(x - C, z - C)
            if 36 <= d <= 40:
                b.set(x, BASE + 1, z, "minecraft:light_blue_terracotta"); b.set(x, BASE + 2, z, WATER)
            elif 40 < d <= 41.2 or 34.8 <= d < 36:
                b.set(x, BASE + 2, z, "minecraft:smooth_sandstone"); b.set(x, BASE + 3, z, wall(CORAL_W) if (x + z) % 5 else LAMP)
    # ---------------- shell houses of the Fish-Man District around the bubble floor
    def house_fits(x, z, r, y=BASE + 2, head=3):
        """Every part of a shell house (round wall, onion dome, tip and rod) has open water-sky above it: the cell
        `head` blocks over its outer face is still inside the bubble, so the roof never touches the bubble glass."""
        h = int(r * 2.1)
        levels = [(y + yy, r) for yy in range(0, 5)]
        for yy in range(0, h + 1):  # the onion profile, as B.dome draws it
            t = yy / h
            rd = r * (0.85 + 0.25 * math.sin(t / 0.45 * math.pi / 2)) if t < 0.45 else r * 1.1 * math.cos((t - 0.45) / 0.55 * math.pi / 2) ** 1.3
            levels.append((y + 5 + yy, rd))
        for (ly, rd) in levels:
            for k in range(16):
                t = k * math.pi / 8
                if not in_b(x + (rd + 1) * math.cos(t), ly + head, z + (rd + 1) * math.sin(t)): return False
        return in_b(x, y + 5 + h + 2 + head, z)  # pearl tip and lightning rod

    for a in range(0, 360, 14):
        rr = rnd.uniform(46, 60)
        r = rnd.choice((3, 4))
        if 70 <= a <= 110: continue  # leave the Sea Forest
        while True:  # pull the outer houses in until they sit well inside the bubble, clear of its ceiling
            x, z = round(C + rr * math.cos(math.radians(a))), round(C + rr * math.sin(math.radians(a)))
            if house_fits(x, z, r) or rr <= 46: break
            rr -= 1
        if house_fits(x, z, r): shell_house(b, x, BASE + 2, z, r, rnd)
    # ---------------- Ryugu Palace on the hill
    Y0 = HILL
    K = 13  # keep half size
    b.box(C - K, Y0, C - K, C + K, Y0, C + K, PEARL)
    for f in range(3):
        fy = Y0 + f * 6
        b.walls(C - K + f * 2, fy + 1, C - K + f * 2, C + K - f * 2, fy + 6, C + K - f * 2, CORAL)
        b.box(C - K + f * 2 + 1, fy + 1, C - K + f * 2 + 1, C + K - f * 2 - 1, fy + 5, C + K - f * 2 - 1, AIR)
        b.box(C - K + f * 2, fy + 6, C - K + f * 2, C + K - f * 2, fy + 6, C + K - f * 2, PEARL)
        e = K - f * 2
        for k in range(-e + 2, e - 1, 3):
            # each window: two tall panes, coral jambs standing proud of the wall, a pearl sill below and a hood above
            for (x, z, ox, oz, out) in ((C + k, C - e, 0, -1, "north"), (C + k, C + e, 0, 1, "south"), (C - e, C + k, -1, 0, "west"), (C + e, C + k, 1, 0, "east")):
                b.set(x, fy + 3, z, pane_of("minecraft:light_blue_stained_glass_pane")); b.set(x, fy + 4, z, pane_of("minecraft:light_blue_stained_glass_pane"))
                px, pz = (1, 0) if oz else (0, 1)
                for j in (-1, 1):
                    for y in range(fy + 2, fy + 6): b.set(x + px * j + ox, y, z + pz * j + oz, wall(CORAL_W))
                b.set(x + ox, fy + 2, z + oz, stairs(PEARL_ST, OPP[out], "top"))
                b.set(x + ox, fy + 5, z + oz, stairs(PEARL_ST, OPP[out], "top"))
        hw = K - f * 2 + 1
        for x in range(C - hw, C + hw + 1):
            b.set(x, fy + 7, C - hw, stairs(PEARL_ST, "south")); b.set(x, fy + 7, C + hw, stairs(PEARL_ST, "north"))
        for z in range(C - hw, C + hw + 1):
            b.set(C - hw, fy + 7, z, stairs(PEARL_ST, "east")); b.set(C + hw, fy + 7, z, stairs(PEARL_ST, "west"))
        if f < 2: b.stairs_up(C + K - f * 2 - 4, fy + 1, C - 3, 6, PEARL_ST, "south")
    # central pearl dome and shell-spire towers
    b.dome(C, C, Y0 + 19, 6, s=PEARL, onion=True, tip="minecraft:sea_lantern")
    for (tx, tz) in ((C - K, C - K), (C + K, C - K), (C - K, C + K), (C + K, C + K)):
        b.cyl(tx, tz, 3, Y0, Y0 + 16, CORAL)
        b.cyl(tx, tz, 4, Y0 + 17, Y0 + 17, PEARL)
        # spiral shell top, tapered so its tip stays a couple of blocks under the palace bubble's skin
        n = 10
        while n > 5 and not all(in_p(tx + (3.2 * (1 - i / (n + 2)) + 1) * math.cos(k * math.pi / 4), Y0 + 18 + i + 2,
                                     tz + (3.2 * (1 - i / (n + 2)) + 1) * math.sin(k * math.pi / 4)) for i in range(n) for k in range(8)):
            n -= 1
        for i in range(n):
            r = 3.2 * (1 - i / (n + 2))
            a = math.radians(i * 50)
            b.cyl(tx, tz, max(0.5, r), Y0 + 18 + i, Y0 + 18 + i, ROOF if i % 2 else "minecraft:dark_prismarine")
            b.set(round(tx + r * math.cos(a)), Y0 + 18 + i, round(tz + r * math.sin(a)), PEARL)
        for y in range(Y0 + 4, Y0 + 15, 5):
            for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(tx + dx, y, tz + dz, pane_of("minecraft:pink_stained_glass_pane"))
    # the connection corridor: a glass tube from the ring road up the palace cliff, through the palace bubble's skin,
    # onto the forecourt in front of the main gate (south)
    Z0 = C + 24                                  # the tube starts on the forecourt, inside the palace bubble
    def floor_y(z):
        return HILL if z < C + 28 else HILL - 1 - (z - (C + 28))
    for z in range(Z0, C + 42):
        yf = floor_y(z)
        d = z - C
        for x in range(C - 4, C + 5):
            if z >= C + 28: b.set(x, yf, z, stairs(PEARL_ST, "north") if z < C + 41 else "minecraft:smooth_sandstone")
            else: b.set(x, yf, z, PEARL if abs(x - C) > 1 else "minecraft:light_blue_terracotta")
            if not 36 <= d <= 40:  # solid causeway under the stair, except where it bridges the canal
                for y in range(BASE + 1, yf): b.set(x, y, z, CORAL if abs(x - C) == 4 else "minecraft:sandstone")
        for x in range(C - 5, C + 6):  # the tube: glass walls and a stepped glass vault, air inside
            ax = abs(x - C)
            for y in range(yf + 1, yf + 8):
                h = y - yf
                inner = (ax <= 4 and h <= 4) or (ax <= 3 and h == 5) or (ax <= 1 and h == 6)
                shell = (ax == 5 and h <= 4) or (ax == 4 and h == 5) or (2 <= ax <= 3 and h == 6) or (ax <= 1 and h == 7)
                if inner: b.set(x, y, z, AIR)
                elif shell: b.set(x, y, z, BUBBLE)
            if ax == 5: b.set(x, yf, z, CORAL)
        if z % 4 == 0: b.set(C - 4, yf + 1, z, LAMP); b.set(C + 4, yf + 1, z, LAMP)
    for x in (C - 4, C + 4):  # piers carrying the bridge over the canal
        for y in range(BASE + 1, floor_y(C + 38)): b.set(x, y, C + 38, CORAL)
    for x in range(C - 4, C + 5): b.set(x, BASE + 3, C + 41, AIR)  # gap in the promenade railing at the tube's mouth
    for x in range(C - 3, C + 4):
        for y in range(Y0 + 1, Y0 + 5): b.set(x, y, C + K, AIR)
    for x in (C - 5, C + 5): b.column(x, C + K + 1, Y0 + 1, Y0 + 7, PEARL); b.set(x, Y0 + 8, C + K + 1, LAMP)
    # Neptune's throne hall (ground floor): a giant throne, he is ~15 m tall
    b.box(C - 4, Y0 + 1, C - K + 1, C + 4, Y0 + 2, C - K + 4, "minecraft:gold_block")
    b.box(C - 4, Y0 + 3, C - K + 1, C + 4, Y0 + 5, C - K + 1, PEARL)
    for x in (C - 4, C + 4): b.box(x, Y0 + 3, C - K + 2, x, Y0 + 4, C - K + 4, "minecraft:gold_block")
    for z in range(C - K + 5, C + K): b.set(C, Y0 + 1, z, "minecraft:cyan_carpet"); b.set(C - 1, Y0 + 1, z, "minecraft:cyan_carpet"); b.set(C + 1, Y0 + 1, z, "minecraft:cyan_carpet")
    for z in range(C - K + 4, C + K - 1, 4):
        for x in (C - 8, C + 8): b.column(x, z, Y0 + 1, Y0 + 5, "minecraft:prismarine_bricks"); b.set(x, Y0 + 5, z, HLAMP)
    b.chest(C + 6, Y0 + 1, C - K + 2, "treasure", "south")
    # Princess Shirahoshi's tower room (top floor): a big bed and her toys
    b.box(C - 3, Y0 + 13, C - 3, C + 3, Y0 + 13, C + 1, "minecraft:pink_wool")
    b.set(C, Y0 + 17, C, HLAMP)
    # ---------------- the Sea Forest: garden with the Poneglyph (Joy Boy's apology)
    SX, SZ = C, C + 53   # pulled in from the rim so the mangrove crowns stay clear of the bubble glass
    for x in range(SX - 14, SX + 15):
        for z in range(SZ - 10, SZ + 10):
            if in_b(x, BASE + 10, z) and math.hypot(x - SX, z - SZ) < 12:
                b.set(x, BASE + 2, z, "minecraft:moss_block")
                r = rnd.random()
                tree_ok = math.hypot(x - C, z - C) >= 46 and all(in_b(x + dx, BASE + 12, z + dz) for dx, dz in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (2, -2), (-2, 2), (-2, -2)))
                if r < 0.12: b.set(x, BASE + 3, z, "onepiece:amazon_flower[half=lower]"); b.set(x, BASE + 4, z, "onepiece:amazon_flower[half=upper]")
                elif r < 0.2 or (r < 0.25 and not tree_ok): b.set(x, BASE + 3, z, "minecraft:azalea")
                elif r < 0.25:
                    for y in range(BASE + 3, BASE + 8): b.set(x, y, z, "minecraft:mangrove_log[axis=y]")
                    b.sphere(x, BASE + 8, z, 2.2, "minecraft:mangrove_leaves[distance=7,persistent=true,waterlogged=false]", ry=1.6)
    b.box(SX - 1, BASE + 2, SZ - 1, SX + 1, BASE + 2, SZ + 1, "minecraft:mossy_stone_bricks")
    b.set(SX, BASE + 3, SZ, "onepiece:poneglyph"); b.set(SX, BASE + 4, SZ, "onepiece:poneglyph")
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)): b.set(SX + dx, BASE + 3, SZ + dz, LAMP)
    # ---------------- people
    b.npc(C, Y0 + 1, C + 2, "jinbe")
    b.guards("fishman", ((C - 6, C + K + 4), (C + 6, C + K + 4)), y=Y0 + 1)
    # ---------------- furnished palace floors
    import interiors as I
    r = I.Room(b, C - K + 1, Y0 + 1, C - K + 1, C + K - 1, C + K - 1, 5, "sea", random.Random(2))
    r.wall_banners(3, 3); r.plants(4); r.paintings(4)
    I.subdivide(b, C - K + 3, Y0 + 7, C - K + 3, C + K - 3, C + K - 3, 5, CORAL, ("library", "dining", "study", "bath"), "sea", cell=11,
                keepout=((C + K - 8, C - 5, C + K - 3, C + 5),), seed=3)
    I.furnish(b, C - K + 5, Y0 + 13, C - K + 5, C + K - 5, C + K - 5, 5, "bedroom", "candy")
    # keep the stairwells open (furniture over a stair hole would float, and the finishing pass turns it into water)
    for f in range(2):
        sx, fy = C + K - f * 2 - 4, Y0 + f * 6
        for i in range(6):
            z = C - 3 + i
            if b.get(sx, fy + 6, z) in (None, AIR):
                for y in range(fy + 7, fy + 9):
                    if b.get(sx, y, z) not in (None, AIR) and "stairs" not in b.get(sx, y, z): b.set(sx, y, z, AIR)
                for xx in (sx - 1, sx + 1):
                    if b.get(xx, fy + 7, z) in (None, AIR) and b.get(xx, fy + 6, z) not in (None, AIR): b.set(xx, fy + 7, z, fence("mangrove"))
    for (x, y, z), st in list(b.blocks.items()):  # no half plants left over (they would turn into water too)
        if "amazon_flower" in st and "half=upper" in st and "half=lower" not in (b.get(x, y - 1, z) or ""): b.set(x, y, z, AIR)
    return b, 0
