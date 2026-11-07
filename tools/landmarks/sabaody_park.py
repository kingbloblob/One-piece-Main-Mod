"""Sabaody Park, the amusement park of the Archipelago, as the show has it: the giant Ferris wheel that towers over
the mangrove canopy (white double rim, colourful hanging cabins), a roller coaster on timber trestles with a lift
hill, a big drop and a vertical loop, the carousel, the bubble ride, game and food stalls, the fountain plaza with
a balloon cart, and the park gate with its SABAODY PARK sign, all in among the Yarukiman mangroves with soap
bubbles welling up from the roots and the ground. Inside: the ticket hall, the park café, the staff house and the
prize shop. ~104 x 100. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import sabaody_kit as S

SID = "sabaody_park"
TITLE = "Sabaody Park"
CUTS = [2]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 104, 100
FUN = dict(wood="birch", rug="pink", rug2="yellow", bed="pink", light="onepiece:bubble_lamp[hanging=true]", accent="minecraft:pink_glazed_terracotta",
           banner="pink", candle="pink")
PAVE = ("minecraft:smooth_quartz", "minecraft:smooth_quartz", "minecraft:calcite", "minecraft:white_terracotta")
EDGE = "minecraft:pink_concrete"
GX = 47            # the park's main axis: gate, boulevard and fountain
COLORS = ("pink", "light_blue", "yellow", "lime", "magenta", "orange")
LOOSE = ("minecraft:short_grass", "minecraft:fern", "minecraft:moss_carpet", "minecraft:pink_tulip", "minecraft:allium",
         "minecraft:azure_bluet", "minecraft:oxeye_daisy")


def pave(b, x, z, rnd, s=None):
    above = b.get(x, 1, z)
    if above not in (None, AIR) and not above.startswith(LOOSE): return
    b.set(x, 0, z, s or rnd.choice(PAVE))
    if above is not None: b.set(x, 1, z, AIR)


def walk(b, x0, z0, x1, z1, rnd):
    """A paved walk with a pink kerb along its long sides."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            kerb = (x in (x0, x1)) if (x1 - x0) < (z1 - z0) else (z in (z0, z1))
            pave(b, x, z, rnd, EDGE if kerb else None)


def plaza(b, cx, cz, r, rnd):
    for x in range(int(cx - r) - 1, int(cx + r) + 2):
        for z in range(int(cz - r) - 1, int(cz + r) + 2):
            d = math.hypot(x - cx, z - cz)
            if d <= r: pave(b, x, z, rnd, EDGE if d > r - 1 else None)


def bubble(b, x, z, rnd, n=1):
    """Soap bubbles welling up from the ground and the mangrove roots: a bubble just formed, still sitting where it
    came up (on the first solid block below), sometimes with a smaller one lifting off its top."""
    y = 9
    while y > 0 and b.get(x, y - 1, z) in (None, AIR): y -= 1
    if y <= 0 and b.get(x, 0, z) in (None, AIR): return
    for i in range(n):
        r = rnd.choice((1.5, 2.0, 2.0, 2.5)) if i == 0 else 1.0
        cy = y + int(r)
        b.sphere(x, cy, z, r, S.BUB, hollow=True)
        y = cy + int(r) + 1
        x += rnd.choice((-1, 0, 1)); z += rnd.choice((-1, 0, 1))


def ferris(b, x, z, RR):
    """The giant Ferris wheel in the x/y plane: two white rims (z-3 and z+3) with a pink inner ring, spokes to a
    golden hub on a long axle, two A-frame towers, and 16 cabins hanging from pivots between the rims."""
    hy = RR + 7
    bars = pane_of("minecraft:iron_bars")
    for zz in (z - 3, z + 3):
        for a10 in range(0, 3600, 12):
            t = math.radians(a10 / 10)
            c, s = math.cos(t), math.sin(t)
            b.set(round(x + RR * c), round(hy + RR * s), zz, "minecraft:sea_lantern" if a10 % 300 == 0 else "minecraft:white_concrete")
            b.set(round(x + (RR - 1) * c), round(hy + (RR - 1) * s), zz, "minecraft:pink_concrete" if (a10 // 225) % 2 else "minecraft:white_concrete")
        for k in range(16):  # thin steel spokes
            t = math.radians(k * 22.5)
            b.line((x, hy, zz), (x + (RR - 2) * math.cos(t), hy + (RR - 2) * math.sin(t), zz), bars)
        for dx in range(-2, 3):  # the hub
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 5: b.set(x + dx, hy + dy, zz, "minecraft:gold_block")
    for zz in range(z - 6, z + 7): b.set(x, hy, zz, "minecraft:iron_block")  # the axle
    b.set(x, hy, z - 7, "minecraft:gold_block"); b.set(x, hy, z + 7, "minecraft:gold_block")
    # the two A-frame towers carrying the axle, with cross braces
    for zz in (z - 5, z + 5):
        for s in (-1, 1):
            for w in (0, 1):
                b.line((x + s * (round(RR * 0.62) + w), 1, zz), (x + s * w, hy - 1, zz), "minecraft:white_concrete")
            b.set(x + s * round(RR * 0.62), 0, zz, "minecraft:polished_andesite"); b.set(x + s * (round(RR * 0.62) + 1), 0, zz, "minecraft:polished_andesite")
        for yb in (9, 17):
            half = round(RR * 0.62 * (1 - (yb - 1) / (hy - 2)))
            for xx in range(x - half, x + half + 1): b.set(xx, yb, zz, "minecraft:pink_concrete")
    # cabins hanging from pivots on the rim, always upright
    for k in range(16):
        t = math.radians(k * 22.5 + 11.25)
        gx, gy = round(x + RR * math.cos(t)), round(hy + RR * math.sin(t))
        col = COLORS[k % len(COLORS)]
        for zz in range(z - 2, z + 3): b.set(gx, gy, zz, "minecraft:iron_chain[axis=z,waterlogged=false]")
        b.set(gx, gy - 1, z, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.box(gx - 1, gy - 2, z - 1, gx + 1, gy - 2, z + 1, f"minecraft:{col}_concrete")
        for yy in (gy - 3, gy - 4):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == 0 and dz == 0: s_ = AIR
                    elif dx == 0 or dz == 0: s_ = pane_of(f"minecraft:{col}_stained_glass_pane")
                    else: s_ = "minecraft:white_concrete"
                    b.set(gx + dx, yy, z + dz, s_)
        b.box(gx - 1, gy - 5, z - 1, gx + 1, gy - 5, z + 1, f"minecraft:{col}_concrete")
        b.set(gx, gy - 4, z, "minecraft:white_carpet")
    # the boarding platform under the lowest cabins, with steps all round
    b.box(x - 7, 1, z - 2, x + 7, 1, z + 2, "minecraft:smooth_quartz")
    for xx in range(x - 7, x + 8):
        b.set(xx, 1, z - 3, stairs("minecraft:quartz_stairs", "south")); b.set(xx, 1, z + 3, stairs("minecraft:quartz_stairs", "north"))
    for zz in range(z - 2, z + 3):
        b.set(x - 8, 1, zz, stairs("minecraft:quartz_stairs", "east")); b.set(x + 8, 1, zz, stairs("minecraft:quartz_stairs", "west"))
    return hy


def track_y(u):
    """Height of the coaster track; u = 0 at the station, growing along the ride."""
    keys = ((0.0, 2), (0.5, 2), (1.45, 31), (1.6, 31), (2.05, 4), (2.5, 16), (2.85, 5), (math.pi, 4), (3.45, 5), (3.95, 13),
            (4.45, 6), (4.95, 10), (5.45, 4), (5.85, 2), (2 * math.pi, 2))
    for (u0, y0), (u1, y1) in zip(keys, keys[1:]):
        if u0 <= u <= u1:
            f = (u - u0) / max(1e-6, u1 - u0)
            return y0 + (y1 - y0) * (1 - math.cos(f * math.pi)) / 2
    return 2


def coaster(b, CX, CZ, AX, AZ):
    """An oval roller coaster: red track with rails on timber trestles, the station on the west side, the lift hill
    on the north, a vertical loop on the east."""
    TRACK = "minecraft:red_concrete"
    cells = []
    prev = None
    for i in range(900):
        u = i / 900 * 2 * math.pi
        t = math.pi + u
        x, z = CX + AX * math.cos(t), CZ + AZ * math.sin(t)
        p = (round(x), round(track_y(u)), round(z))
        if prev and p != prev: b.line(prev, p, TRACK)
        if p != prev: cells.append(p)
        prev = p
    b.line(prev, cells[0], TRACK)
    # the vertical loop on the east side (the track runs along +z there)
    lx, lz, ly, lr = CX + AX, CZ, 4, 6
    for a in range(0, 360, 3):
        r = math.radians(a)
        b.set(lx, round(ly + lr - lr * math.cos(r)), round(lz + lr * math.sin(r)), TRACK)
    track = {q for q, s in b.blocks.items() if s == TRACK}
    for (x, y, z) in track:
        if (x, y + 1, z) in track: continue
        if x == lx and abs(z - lz) <= lr and y > ly + 1: continue  # the loop's upper half runs upside down
        sh = "east_west" if ((x + 1, y, z) in track or (x - 1, y, z) in track) else "north_south"
        b.set(x, y + 1, z, f"minecraft:rail[shape={sh},waterlogged=false]")
    # trestles every few cells: a birch post banded with planks
    for n, (x, y, z) in enumerate(cells):
        if n % 9 or y < 4: continue
        for yy in range(1, y): b.set(x, yy, z, "minecraft:stripped_birch_log[axis=y]" if yy % 5 else "minecraft:birch_planks")
        b.set(x, 0, z, "minecraft:polished_andesite")
    # the station: a boarding platform beside the track under a striped canopy on posts
    sx = CX - AX
    for z in range(CZ - 6, CZ + 7):
        for x in range(sx - 4, sx):
            b.box(x, 1, z, x, 2, z, "minecraft:birch_planks")
        b.box(sx + 1, 1, z, sx + 1, 2, z, "minecraft:birch_planks")
    for z in range(CZ - 6, CZ + 7, 4):
        for x in (sx - 4, sx + 1): b.column(x, z, 3, 7, fence("birch"))
    for z in range(CZ - 7, CZ + 8):
        for x in range(sx - 5, sx + 3):
            b.set(x, 8, z, "minecraft:pink_wool" if (z // 2) % 2 else "minecraft:white_wool")
    for z in range(CZ - 6, CZ + 7):
        if (z - CZ) % 4: b.set(sx - 4, 3, z, fence("birch"))
    for z in (CZ - 1, CZ, CZ + 1):  # steps up onto the platform, through a gap in its rail
        b.set(sx - 6, 1, z, stairs("minecraft:birch_stairs", "east")); b.set(sx - 5, 1, z, "minecraft:birch_planks")
        b.set(sx - 5, 2, z, stairs("minecraft:birch_stairs", "east")); b.set(sx - 4, 3, z, AIR)
    for k, col in enumerate(("yellow", "pink", "light_blue")):  # a train of three cars waiting at the platform
        zc = CZ - 3 + 3 * k
        b.set(sx, 3, zc, f"minecraft:{col}_concrete"); b.set(sx, 3, zc + 1, stairs("minecraft:quartz_stairs", "north"))
    return track


def carousel(b, KX, KZ):
    b.cyl(KX, KZ, 7.5, 0, 0, "minecraft:polished_andesite")
    for x in range(KX - 8, KX + 9):  # the turntable: white with a pink rim
        for z in range(KZ - 8, KZ + 9):
            d = math.hypot(x - KX, z - KZ)
            if d <= 7.35: b.set(x, 1, z, "minecraft:pink_concrete" if d > 6.5 else "minecraft:white_concrete")
    b.cyl(KX, KZ, 1.2, 2, 6, "minecraft:smooth_quartz"); b.cyl(KX, KZ, 1.2, 2, 2, "minecraft:gold_block")
    for k in range(12):  # horses on golden poles, three colours
        t = math.radians(k * 30)
        hx, hz = round(KX + 5 * math.cos(t)), round(KZ + 5 * math.sin(t))
        tx, tz = round(KX + 5 * math.cos(t + 0.2)), round(KZ + 5 * math.sin(t + 0.2))
        for yy in range(2, 7): b.set(hx, yy, hz, "minecraft:end_rod[facing=up]")
        wool = ("minecraft:white_wool", "minecraft:pink_wool", "minecraft:light_blue_wool")[k % 3]
        b.set(hx, 3 + k % 2, hz, wool); b.set(tx, 4 + k % 2, tz, wool)
    # the canopy: a cone of pink and white wedges with a yellow scalloped valance and a golden finial
    for y, rr in ((7, 8.5), (8, 7), (9, 5.5), (10, 4), (11, 2.5), (12, 1.2)):
        for x in range(int(KX - rr) - 1, int(KX + rr) + 2):
            for z in range(int(KZ - rr) - 1, int(KZ + rr) + 2):
                if math.hypot(x - KX, z - KZ) <= rr + 0.35:
                    a = math.degrees(math.atan2(z - KZ, x - KX)) % 360
                    b.set(x, y, z, "minecraft:pink_concrete" if int(a // 30) % 2 else "minecraft:white_concrete")
    for a in range(0, 360, 6):
        t = math.radians(a)
        x, z = round(KX + 8 * math.cos(t)), round(KZ + 8 * math.sin(t))
        if (a // 18) % 2: b.set(x, 6, z, "minecraft:yellow_wool")
    b.set(KX, 13, KZ, "minecraft:gold_block"); b.set(KX, 14, KZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")


def gate(b, gx, gz):
    """The park gate: two pink towers with white domes, a scalloped arch and a two-sided board reading SABAODY / PARK."""
    W = 15
    for x0 in (gx - W - 4, gx + W + 1):
        b.box(x0 - 1, 0, gz - 2, x0 + 4, 0, gz + 3, "minecraft:polished_andesite")
        b.box(x0, 1, gz - 1, x0 + 3, 18, gz + 2, "minecraft:pink_concrete")
        for y in (1, 6, 12, 18): b.box(x0, y, gz - 1, x0 + 3, y, gz + 2, "minecraft:white_concrete")
        for (wx, wz) in ((x0 + 1, gz - 1), (x0 + 2, gz - 1), (x0 + 1, gz + 2), (x0 + 2, gz + 2)):
            for y in (8, 9, 14, 15): b.set(wx, y, wz, "minecraft:light_blue_stained_glass")
        b.box(x0 - 1, 19, gz - 2, x0 + 4, 19, gz + 3, "minecraft:white_concrete")
        b.dome(x0 + 1.5, gz + 0.5, 20, 3, s="minecraft:white_concrete", tip="minecraft:gold_block")
    # the board across the top, two blocks thick, framed in pink
    for x in range(gx - W, gx + W + 1):
        for y in range(9, 22):
            frame = y in (9, 21) or x in (gx - W, gx + W)
            for z in (gz, gz + 1): b.set(x, y, z, "minecraft:pink_concrete" if frame else "minecraft:white_concrete")
    for x in range(gx - W, gx + W + 1):  # the arch under the board: rounded shoulders, open in the middle
        d = abs(x - gx) / W
        low = 9 - round(6 * max(0.0, d - 0.55) / 0.45)
        for y in range(max(1, low), 9):
            for z in (gz, gz + 1): b.set(x, y, z, "minecraft:pink_concrete")
    for (msg, y) in (("SABAODY", 15), ("PARK", 10)):
        w = len(msg) * 4 - 1
        b.text(gx - w // 2, y, gz + 2, msg, "minecraft:red_concrete", axis="x", step=1)            # reads from the south (outside)
        b.text(gx - w // 2 + w - 1, y, gz - 1, msg, "minecraft:red_concrete", axis="x", step=-1)   # reads from the north (inside)
    for x in (gx - W, gx + W):
        for z in (gz, gz + 1): b.set(x, 22, z, "minecraft:gold_block")


def fountain(b, x, z):
    b.cyl(x, z, 5, 0, 0, "minecraft:quartz_bricks")
    b.cyl(x, z, 4.5, 1, 1, "minecraft:quartz_bricks", hollow=True); b.cyl(x, z, 3.6, 1, 1, "minecraft:water[level=0]")
    b.cyl(x, z, 1, 1, 4, "minecraft:quartz_pillar[axis=y]")
    b.cyl(x, z, 2.2, 5, 5, "minecraft:quartz_bricks", hollow=True); b.cyl(x, z, 1.2, 5, 5, "minecraft:quartz_bricks")
    b.set(x, 6, z, "minecraft:water[level=0]")


def balloon_cart(b, x, z):
    """A balloon seller's cart: two barrels under a slab counter, balloons on strings tied to it."""
    b.set(x, 1, z, "minecraft:barrel[facing=up,open=false]"); b.set(x + 1, 1, z, "minecraft:barrel[facing=up,open=false]")
    b.set(x + 2, 1, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
    b.set(x - 1, 1, z, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    for k, (dx, h) in enumerate(((0, 4), (1, 6), (2, 5))):
        for yy in range(2, 2 + h): b.set(x + dx, yy, z, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.set(x + dx, 2 + h, z, f"minecraft:{('red', 'yellow', 'light_blue')[k]}_wool")


def build():
    rnd = random.Random(461)
    b = B()
    S.ground(b, NX, NZ, rnd)
    for x in range(10, NX - 10):  # a lawn with flower beds inside the park
        for z in range(10, NZ - 10):
            if b.get(x, 1, z) in (None, AIR) and rnd.random() < 0.05:
                b.set(x, 1, z, rnd.choice(("minecraft:pink_tulip", "minecraft:allium", "minecraft:azure_bluet", "minecraft:oxeye_daisy", "minecraft:short_grass")))
    for (x, z, r, h) in ((5, 5, 3.5, 26), (98, 6, 3.5, 28), (6, 94, 3, 24), (97, 93, 3.5, 26), (52, 4, 3, 22)): S.yarukiman(b, x, z, rnd, r=r, h=h)
    # ---------------- walks and plazas
    walk(b, GX - 3, 18, GX + 3, NZ - 9, rnd)              # the boulevard from the gate
    walk(b, 10, 44, GX + 3, 48, rnd)                       # the avenue west to the Ferris wheel and the ticket hall
    walk(b, 36, 12, 72, 19, rnd)                           # the stall row
    walk(b, GX + 3, 52, 56, 56, rnd)                       # to the coaster station
    plaza(b, GX, 80, 8, rnd)                               # the fountain plaza
    plaza(b, 27, 36, 9, rnd)                               # round the Ferris wheel
    plaza(b, 30, 74, 10.5, rnd)                            # round the bubble ride
    plaza(b, 74, 54, 9.5, rnd)                             # round the carousel
    # ---------------- the giant Ferris wheel, the park's landmark
    ferris(b, 27, 36, 21)
    # ---------------- the roller coaster round the carousel
    coaster(b, 74, 54, 18, 24)
    carousel(b, 74, 54)
    # ---------------- the bubble ride: giant bubbles tethered over a pool
    b.cyl(30, 74, 8.6, 0, 1, "minecraft:quartz_bricks", hollow=True)   # the rim first: a hollow cylinder clears its inside
    b.cyl(30, 74, 8, 0, 0, "minecraft:water[level=0]"); b.cyl(30, 74, 8, -1, -1, "minecraft:light_blue_concrete")
    for k in range(6):
        t = math.radians(k * 60)
        bx, bz = round(30 + 5 * math.cos(t)), round(74 + 5 * math.sin(t))
        y = 6 + k % 3 * 2
        b.set(bx, 0, bz, "minecraft:quartz_bricks")
        for yy in range(1, y - 1): b.set(bx, yy, bz, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.sphere(bx, y + 1, bz, 2.2, S.BUB, hollow=True)
    # ---------------- the fountain plaza, the balloon cart and the park gate
    fountain(b, GX, 80)
    balloon_cart(b, GX + 6, 73)
    gate(b, GX, NZ - 10)
    # ---------------- the ticket hall, café, staff house and prize shop
    T.house(b, 12, 52, 12, 10, 1, "plaster", rnd, kinds=["dining"], theme=FUN, door="east", sign="minecraft:pink_wool")
    T.house(b, 68, 84, 12, 8, 1, "plaster", rnd, kinds=["storage"], theme=FUN, door="north", sign="minecraft:yellow_wool")
    T.house(b, 14, 84, 10, 8, 2, "plaster", rnd, kinds=["tavern", "bedroom"], theme=FUN, door="north")
    T.house(b, 82, 12, 10, 8, 1, "plaster", rnd, kinds=["treasure"], theme=FUN, door="south", sign="minecraft:light_blue_wool")
    for i, x in enumerate(range(40, 66, 6)):
        T.stall(b, x, 14, ("pink", "yellow", "light_blue", "lime", "orange")[i], (("minecraft:cake[bites=0]", "minecraft:melon", None), ("minecraft:target[power=0]", "minecraft:hay_block[axis=y]", None))[i % 2])
    for z in range(24, NZ - 12, 8):  # lamp posts down both sides of the boulevard
        for x in (GX - 4, GX + 4):
            if b.get(x, 1, z) in (None, AIR): T.lamp_post(b, x, z)
    for x in range(14, GX - 4, 8):
        if b.get(x, 1, 43) in (None, AIR): T.lamp_post(b, x, 43)
    # ---------------- soap bubbles welling up from the roots and the lawns
    for (tx, tz) in ((5, 5), (98, 6), (6, 94), (97, 93), (52, 4)):  # on the arching roots of the mangroves
        for k in range(3):
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(6, 9)
            x, z = round(tx + d * math.cos(a)), round(tz + d * math.sin(a))
            if 1 <= x < NX - 1 and 1 <= z < NZ - 1: bubble(b, x, z, rnd, n=rnd.choice((1, 2)))
    for i in range(40):
        x, z = rnd.randint(4, NX - 5), rnd.randint(4, NZ - 5)
        if all(b.get(x + dx, y, z + dz) in (None, AIR) or (b.get(x + dx, y, z + dz) or "").startswith(LOOSE)
               for dx in (-3, 0, 3) for dz in (-3, 0, 3) for y in range(1, 8)):
            bubble(b, x, z, rnd, n=rnd.choice((1, 1, 2)))
    # ---------------- loot
    b.chest(84, 1, 14, "medium", "south"); b.chest(14, 1, 54, "easy", "east")
    return b, 0
