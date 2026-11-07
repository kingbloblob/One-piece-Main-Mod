"""Drum Castle on the Drum Rockies: the tallest of the sheer, flat-topped, drum-shaped snowy rock columns (two lower
peaks of the range stand beside it), with Dr. Kureha's castle on the summit. Over the main tower flies Dr. Hiluluk's
Jolly Roger, and along the summit parapet stand the castle cannons that fired his pink powder into the sky, so the
snow on the summit lies pink: the 'Sakura of Hiluluk'. The ropeway cable runs down to the snowfields and the
snowed-in town of Bighorn at the foot (furnished cabins, the inn, the doctor's office). Inside the castle: the great
hall, Kureha's clinic with beds and medicine shelves, the library, Chopper's room, the armory of the old king.
~96 x 96, summit at 60, flag at ~109. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "drum_castle"
TITLE = "Drum Castle"
CUTS = [3, 66]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
MX, MZ = 56, 40
MR = 18
TOP = 60
SNOWB = "onepiece:snow_bricks"
COLD = dict(wood="spruce", rug="red", rug2="white", bed="white", light="minecraft:lantern", accent="minecraft:snow_block",
            banner="red", candle="red")


STONE = "minecraft:stone_bricks"
PINK = "minecraft:pink_concrete_powder"
PEAKS = ((18, 22, 9, 44), (84, 82, 7, 34))  # the lower Drum Rockies beside the castle peak: x, z, radius, height

# Dr. Hiluluk's Jolly Roger: a white skull and crossbones surrounded by pink sakura petals on black, the flag that
# flies at the top of the castle (Luffy held it up against Wapol). 15 wide, 11 tall, top row first.
HILULUK = ("##...p...p...##",
           ".##...###...##.",
           ".p.#.#####.#.p.",
           "....#######....",
           "p...#..#..#...p",
           ".p..#######..p.",
           ".....##.##.....",
           "p..#.#####.#..p",
           ".##..#.#.#..##.",
           "##...........##",
           "...p...p...p...")


def flag(b, x, y, z, art=HILULUK):
    """A flag in the plane x hanging off a pole at (x, z-1), top row at y. Symmetric art reads the same both sides."""
    for r, row in enumerate(art):
        for c, ch in enumerate(row):
            b.set(x, y - r, z + c, {"#": "minecraft:white_wool", "p": "minecraft:pink_wool"}.get(ch, "minecraft:black_wool"))


def cannon(b, x, y, z, out):
    """A castle cannon on its carriage, barrel pointing out over the parapet (out = facing)."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[out]
    ax = "x" if dx else "z"
    b.set(x, y, z, "minecraft:spruce_planks"); b.set(x - dx, y, z - dz, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for k in (0, 1):
        b.set(x + dx * k, y + 1, z + dz * k, f"minecraft:polished_basalt[axis={ax}]")
    b.set(x - dx, y + 1, z - dz, "minecraft:polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    px, pz = (1, 0) if dz else (0, 1)
    for sgn in (-1, 1):  # wheels
        b.set(x + px * sgn, y, z + pz * sgn, "minecraft:dark_oak_trapdoor[facing=%s,half=bottom,open=true,powered=false,waterlogged=false]" % (
            {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(px * sgn, pz * sgn)]))


def build():
    rnd = random.Random(281)
    b = B()
    T.ground(b, N, N, rnd, top="minecraft:snow_block", deco=0.3, decos=("minecraft:snow[layers=1]", "minecraft:snow[layers=2]"))
    # spruce forest
    for i in range(60):
        x, z = rnd.randint(2, N - 3), rnd.randint(2, N - 3)
        if math.hypot(x - MX, z - MZ) < MR + 6 or (8 <= x <= 44 and 56 <= z <= 92): continue
        if any(math.hypot(x - px, z - pz) < pr + 3 for (px, pz, pr, ph) in PEAKS): continue
        h = rnd.randint(6, 10)
        for y in range(1, h): b.set(x, y, z, "minecraft:spruce_log[axis=y]")
        for k in range(h - 5, h + 1):
            b.cyl(x, z, max(0.6, (h - k) * 0.55 + 0.5), k, k, "minecraft:spruce_leaves[distance=7,persistent=true,waterlogged=false]")
        b.set(x, h + 1, z, "minecraft:snow_block")
    # ---------------- the rock column
    def drum(cx, cz, R, top, seed):
        for y in range(0, top + 1):
            rr = R * (1.10 - 0.10 * y / top) + 0.7 * math.sin(y * 0.5 + seed)
            b.cyl(cx, cz, rr, y, y, "minecraft:stone" if (y // 4 + seed) % 3 else "minecraft:andesite")
            if y % 6 == 3: b.cyl(cx, cz, rr + 0.6, y, y, "minecraft:snow_block", hollow=True)
        for a in range(0, 360, 9):  # icicles hanging from the ledges, cracks of packed ice down the walls
            t = math.radians(a + seed * 17)
            k = (a * 7 + seed) % 5
            for y in range(9 + k * 6, top - 4, 30):
                rr = R * (1.10 - 0.10 * y / top) + 0.7 * math.sin(y * 0.5 + seed)
                ix, iz = round(cx + (rr + 0.3) * math.cos(t)), round(cz + (rr + 0.3) * math.sin(t))
                for yy in range(y - 2, y + 1):
                    if b.get(ix, yy, iz) in (None, AIR): b.set(ix, yy, iz, "minecraft:packed_ice")
        b.cyl(cx, cz, R + 0.5, top, top, "minecraft:snow_block")
    drum(MX, MZ, MR, TOP, 0)
    for i, (px, pz, pr, ph) in enumerate(PEAKS):
        drum(px, pz, pr, ph, i + 1)
        for y in (ph + 1,):
            for x in range(px - pr, px + pr + 1):
                for z in range(pz - pr, pz + pr + 1):
                    if math.hypot(x - px, z - pz) <= pr and rnd.random() < 0.5: b.set(x, y, z, "minecraft:snow[layers=2]")
    # ropeway: cable from the summit to the town
    sx, sz = MX - 10, MZ + 12
    ex, ez = 26, 66
    for i in range(140):
        t = i / 139
        x = sx + (ex - sx) * t; z = sz + (ez - sz) * t; y = TOP + 2 + (1 - TOP) * t + 14 * math.sin(t * math.pi) * -0.5
        b.set(round(x), round(y), round(z), "minecraft:chain[axis=y,waterlogged=false]" if False else "minecraft:dark_oak_fence")
    for (x, z, h) in ((ex, ez, 6), (sx, sz, 4)):
        base = 1 if h == 6 else TOP + 1
        b.column(x, z, base, base + h - 1, "minecraft:dark_oak_log[axis=y]")
    # ---------------- the castle on the summit
    C0, C1, D0, D1 = MX - 12, MX + 12, MZ - 10, MZ + 8
    G = TOP + 1
    FL = (G, G + 7)
    b.walls(C0, G, D0, C1, G + 13, D1, SNOWB)
    b.box(C0 + 1, G, D0 + 1, C1 - 1, G + 13, D1 - 1, AIR)
    b.box(C0 + 1, FL[1] - 1, D0 + 1, C1 - 1, FL[1] - 1, D1 - 1, "minecraft:spruce_planks")
    # wall relief: stone pilasters every 4, a string course at the upper floor, framed windows between the pilasters
    for x in range(C0, C1 + 1):
        for (z, o, f) in ((D0, -1, "north"), (D1, 1, "south")):
            if (x - C0) % 4 == 0:
                for y in range(G, G + 14): b.set(x, y, z + o, STONE)
                b.set(x, G + 14, z + o, stairs("minecraft:stone_brick_stairs", OPP[f], "top"))
            else:
                b.set(x, FL[1] - 1, z + o, stairs("minecraft:stone_brick_stairs", OPP[f], "top"))
                b.set(x, G, z + o, stairs("minecraft:stone_brick_stairs", OPP[f]))
            if (x - C0) % 4 == 2:
                for fy in (G, FL[1]):
                    for k in (1, 2, 3, 4): b.set(x, fy + k, z, STONE)
                    for k in (2, 3): b.set(x, fy + k, z, pane_of("minecraft:light_blue_stained_glass_pane"))
                    b.set(x, fy + 1, z + o, stairs("minecraft:stone_brick_stairs", OPP[f], "top"))
                    b.set(x, fy + 4, z + o, slab("minecraft:stone_brick_slab", "top"))
    for z in range(D0 + 1, D1):
        for (x, o, f) in ((C0, -1, "west"), (C1, 1, "east")):
            if (z - D0) % 4 == 0:
                for y in range(G, G + 14): b.set(x + o, y, z, STONE)
            else:
                b.set(x + o, FL[1] - 1, z, stairs("minecraft:stone_brick_stairs", OPP[f], "top"))
                b.set(x + o, G, z, stairs("minecraft:stone_brick_stairs", OPP[f]))
            if (z - D0) % 4 == 2:
                for fy in (G, FL[1]):
                    for k in (2, 3): b.set(x, fy + k, z, pane_of("minecraft:light_blue_stained_glass_pane"))
                    b.set(x + o, fy + 1, z, stairs("minecraft:stone_brick_stairs", OPP[f], "top"))
                    b.set(x + o, fy + 4, z, slab("minecraft:stone_brick_slab", "top"))
    # the roof first, then the four corner towers over it: the towers rise clean and white through the eaves
    # instead of the overhang cutting dark notches into their walls
    b.hip_roof(C0, D0, C1, D1, G + 14, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", overhang=2)
    for (tx, tz) in ((C0, D0), (C1, D0), (C0, D1), (C1, D1)):
        b.cyl(tx, tz, 3, G, G + 22, SNOWB, hollow=True)
        for k in range(8): b.cyl(tx, tz, 3.8 - k * 0.5, G + 23 + k, G + 23 + k, "minecraft:blue_terracotta")
        b.set(tx, G + 31, tz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the main tower with the domed top (the 'onion' of Drum Castle)
    b.cyl(MX, D0 + 3, 4, G + 14, G + 26, SNOWB, hollow=True)
    dt = b.dome(MX, D0 + 3, G + 27, 5, s="minecraft:light_blue_terracotta", onion=True, tip="minecraft:gold_block")
    # Hiluluk's Jolly Roger on a pole over the main tower
    for y in range(dt + 1, dt + 11): b.set(MX, y, D0 + 3, "minecraft:dark_oak_fence")
    b.set(MX, dt + 11, D0 + 3, "minecraft:gold_block")
    flag(b, MX, dt + 10, D0 + 4)
    # the castle gate (south, onto the summit courtyard): arched opening in a stone surround, lamps either side
    for x in range(MX - 2, MX + 3):
        for y in range(G, G + 4 + (1 if abs(x - MX) < 2 else 0)): b.set(x, y, D1, AIR); b.set(x, y, D1 + 1, AIR)
    for x in range(MX - 3, MX + 4):
        for y in range(G, G + 7):
            if abs(x - MX) == 3 or y >= G + 5 + (0 if abs(x - MX) < 2 else -1): b.set(x, y, D1 + 1, STONE)
    for x in range(MX - 4, MX + 5): b.set(x, G + 7, D1 + 1, stairs("minecraft:stone_brick_stairs", "north", "top")) if abs(x - MX) <= 4 else None
    for x in (MX - 4, MX + 4):  # the front door stands open (for the snowbirds); lamps on posts either side
        b.set(x, G + 3, D1 + 2, stairs("minecraft:stone_brick_stairs", "north", "top")); b.set(x, G + 4, D1 + 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    # ladder up to the upper floor on the solid north wall, clear of the NE tower (at C1 - 2 it stood inside the
    # tower's wall ring with the hollow tower shaft behind it and the ring wall over its top). It runs one rung above
    # the upper floor so the furnishing keeps the way off it clear
    for k in range(FL[1] - G + 1):
        b.set(C1 - 4, G + k, D0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for z in range(D0 + 1, D1):
        for y in range(G, FL[1] - 1): b.set(MX - 3, y, z, SNOWB); b.set(MX + 4, y, z, SNOWB)
    for y in (G, G + 1, G + 2):
        b.set(MX - 3, y, MZ, AIR); b.set(MX + 4, y, MZ, AIR)
    r = I.furnish(b, MX - 2, G, D0 + 1, MX + 3, D1 - 1, 5, "hall", COLD); r.chandelier(MX, MZ - 1, 2, 2)
    I.furnish(b, C0 + 1, G, D0 + 1, MX - 4, D1 - 1, 5, "lab", COLD)
    I.furnish(b, MX + 5, G, D0 + 1, C1 - 1, D1 - 1, 5, "kitchen", COLD)
    I.subdivide(b, C0 + 1, FL[1], D0 + 1, C1 - 1, D1 - 1, 5, SNOWB, ("library", "bedroom", "armory", "bedroom"), COLD, cell=12,
                keepout=((C1 - 5, D0 + 1, C1 - 3, D0 + 3),), seed=9)
    # summit parapet round the rim, with the cannons Kureha fired Hiluluk's pink powder from
    for x in range(MX - MR - 2, MX + MR + 3):
        for z in range(MZ - MR - 2, MZ + MR + 3):
            d = math.hypot(x - MX, z - MZ)
            if MR - 1.0 <= d <= MR + 0.4 and b.get(x, G, z) in (None, AIR):
                b.set(x, G, z, SNOWB)
                if (x + z) % 2 and b.get(x, G + 1, z) in (None, AIR): b.set(x, G + 1, z, wall("minecraft:stone_brick_wall"))
    # two batteries of three on the open terraces, south of the gate and north behind the castle, every cannon well
    # clear of the corner towers (more than 4.5 blocks from each tower centre)
    for a in (60, 90, 120, 250, 270, 290):
        t = math.radians(a)
        cx, cz = round(MX + (MR - 3) * math.cos(t)), round(MZ + (MR - 3) * math.sin(t))
        out = "south" if 45 <= a <= 135 else "north" if 225 <= a <= 315 else "east" if math.cos(t) > 0 else "west"
        dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[out]
        cannon(b, cx, G, cz, out)
        for k in (2, 3):  # open the parapet in front of the muzzle
            if b.get(cx + dx * k, G + 1, cz + dz * k) and "wall" in b.get(cx + dx * k, G + 1, cz + dz * k): b.set(cx + dx * k, G + 1, cz + dz * k, AIR)
    # the Sakura of Hiluluk: the snow on the summit lies pink where the powder fell
    for x in range(MX - MR - 1, MX + MR + 2):
        for z in range(MZ - MR - 1, MZ + MR + 2):
            if math.hypot(x - MX, z - MZ) > MR + 0.5 or b.get(x, TOP, z) != "minecraft:snow_block": continue
            if any(b.get(x, y, z) not in (None, AIR) for y in range(G, G + 30)): continue  # open sky only, not indoors
            n = math.sin(x * 0.7) + math.cos(z * 0.6) + rnd.random()
            if n > 0.4: b.set(x, TOP, z, PINK)
            if rnd.random() < 0.12: b.set(x, G, z, "minecraft:pink_petals[facing=north,flower_amount=4]")
    # ---------------- Bighorn town at the foot
    spots = [(8, 58, "tavern"), (20, 58, None), (32, 58, "lab"), (8, 72, None), (20, 74, None), (32, 72, "kitchen"), (12, 84, None), (28, 84, None)]
    for (x0, z0, kind) in spots:
        # the snow style lays snow on every roof part itself (townkit.snow_roofs over the house's rects + 3: wings,
        # porch, bay and dormers too, not only the old 8x7 box)
        T.house(b, x0, z0, 8, 7, 2 if kind else rnd.choice((1, 2)), "snow", rnd, kinds=[kind, "bedroom"] if kind else None,
                door="north" if z0 > 66 else "south", sign="minecraft:red_wool" if kind else None, theme=COLD)
    T.path(b, [(4, 66), (40, 66), (ex, ez)], w=1, s="minecraft:packed_ice" if False else "minecraft:snow_block")
    for x in range(4, 42, 6): T.lamp_post(b, x, 68)
    # ---------------- people and loot
    b.npc(MX, G, MZ, "chopper", False)
    b.chest(C0 + 2, G, D0 + 2, "medicine", "east"); b.chest(C1 - 3, FL[1], D1 - 2, "medicine", "west")
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open snow rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0
