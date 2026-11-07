"""The Toy House of Dressrosa: the cheerful toy-box building at the foot of the King's Plateau where the toys gather,
and the main entrance to the underground complex below it. A stack of painted toy blocks in a white frame with red
floor beams, coloured window frames and sills, four candy-capped corner towers, big gears and a clock face on the
front and a carousel-horse weathervane on a stepped red-and-yellow roof. Inside: the show room of toys (with the
wide stair down), Sugar's grape room, the Donquixote officers' lounge. Underneath: the SMILE factory, a long hall
of conveyor lines, vats and crates worked by the enslaved toys and dwarves, their cramped dormitory, and the
underground trade port, a canal from a sea gate with a plank quay and cargo. ~84 x 76. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "toy_house"
TITLE = "Dressrosa Toy House"
CUTS = [2, -6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 84, 76
TOY = dict(wood="birch", rug="yellow", rug2="red", bed="lime", light="minecraft:lantern", accent="minecraft:yellow_glazed_terracotta",
           banner="yellow", candle="red")
COLS = ("red", "yellow", "lime", "light_blue", "orange", "pink", "magenta")
X0, X1, Z0, Z1 = 24, 60, 20, 48


def gear(b, cx, cy, z, r, s):
    for a in range(0, 360, 3):
        t = math.radians(a)
        rr = r + (1 if (a // 15) % 2 else 0)
        b.set(round(cx + rr * math.cos(t)), round(cy + rr * math.sin(t)), z, s)
        b.set(round(cx + (r - 1) * math.cos(t)), round(cy + (r - 1) * math.sin(t)), z, s)
    for a in (0, 60, 120):
        t = math.radians(a)
        b.line((cx - r * math.cos(t), cy - r * math.sin(t), z), (cx + r * math.cos(t), cy + r * math.sin(t), z), s)
    b.set(cx, cy, z, "minecraft:gold_block")


def build():
    rnd = random.Random(551)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.1, decos=("minecraft:short_grass", "minecraft:sunflower[half=lower]", "minecraft:poppy", "minecraft:dandelion"))
    for x in range(NX):
        for z in range(NZ):
            if b.get(x, 1, z) == "minecraft:sunflower[half=lower]": b.set(x, 2, z, "minecraft:sunflower[half=upper]")
    # ---------------- the secret SMILE factory under the house
    FX0, FX1, FZ0, FZ1, FY = 10, 74, 10, 62, -12
    b.box(FX0, FY - 1, FZ0, FX1, -1, FZ1, "minecraft:stone_bricks")
    b.box(FX0 + 1, FY, FZ0 + 1, FX1 - 1, -2, FZ1 - 1, AIR)
    b.box(FX0 + 1, FY - 1, FZ0 + 1, FX1 - 1, FY - 1, FZ1 - 1, "minecraft:polished_andesite")
    for x in range(FX0 + 4, FX1 - 3, 8):
        for z in range(FZ0 + 4, FZ1 - 3, 8): b.column(x, z, FY, -2, "minecraft:iron_block")
    for z in (FZ0 + 10, FZ0 + 22, FZ0 + 34):  # conveyor lines with SMILE fruit crates
        for x in range(FX0 + 6, FX1 - 6):
            b.set(x, FY, z, "minecraft:smooth_stone_slab[type=top,waterlogged=false]") if False else b.set(x, FY, z, "minecraft:black_concrete")
            b.set(x, FY + 1, z, "minecraft:rail[shape=east_west,waterlogged=false]")
            if x % 6 == 0: b.set(x, FY + 1, z + 1, "minecraft:barrel[facing=up,open=false]"); b.set(x, FY + 1, z - 1, "minecraft:crafting_table")
        for x in range(FX0 + 8, FX1 - 6, 12):
            b.cyl(x, z + 4, 2, FY, FY + 3, "minecraft:iron_block", hollow=True); b.cyl(x, z + 4, 1, FY + 1, FY + 2, "minecraft:purple_concrete")
    for x in range(FX0 + 2, FX1 - 1, 6): b.set(x, -2, (FZ0 + FZ1) // 2, "minecraft:redstone_lamp[lit=true]")
    I.furnish(b, FX0 + 1, FY, FZ1 - 9, FX0 + 22, FZ1 - 1, 6, "barracks", TOY, seed=11)  # the toys' cramped dormitory
    I.furnish(b, FX1 - 20, FY, FZ1 - 9, FX1 - 1, FZ1 - 1, 6, "storage", TOY, seed=12)
    I.furnish(b, FX1 - 14, FY, FZ0 + 1, FX1 - 1, FZ0 + 7, 6, "lab", TOY, seed=13)
    for y in range(FY, 1): b.set(X0 + 2, y, Z0 + 2, "minecraft:ladder[facing=south,waterlogged=false]")
    b.set(X0 + 2, 0, Z0 + 2, "minecraft:birch_trapdoor[facing=south,half=bottom,open=false,powered=false,waterlogged=false]")
    # ---------------- the Toy House itself: a stack of painted toy blocks in a white frame
    H = 22
    FRAME = "minecraft:smooth_quartz"
    b.box(X0, 0, Z0, X1, 0, Z1, "minecraft:birch_planks")
    mx, mz = (X0 + X1) // 2, (Z0 + Z1) // 2
    XP = list(range(X0, X1 + 1, 9))        # posts every 9 along the long sides
    ZP = list(range(Z0, Z1 + 1, 7))        # and every 7 along the short sides
    BEAMS = (8, 15, H)
    WROWS = ((3, 5), (10, 12), (17, 19))  # window rows per floor
    sides = ((0, 1, [(x, Z1) for x in range(X0, X1 + 1)], XP), (0, -1, [(x, Z0) for x in range(X0, X1 + 1)], XP),
             (1, 0, [(X1, z) for z in range(Z0, Z1 + 1)], ZP), (-1, 0, [(X0, z) for z in range(Z0, Z1 + 1)], ZP))
    for si, (ox, oz, cells, posts) in enumerate(sides):
        out = {(0, 1): "south", (0, -1): "north", (1, 0): "east", (-1, 0): "west"}[(ox, oz)]
        for (x, z) in cells:
            along = x if oz else z
            pi = sum(1 for p in posts if p <= along) - 1
            pa, pb = posts[max(0, min(pi, len(posts) - 2))], posts[max(0, min(pi, len(posts) - 2)) + 1]
            post = along in posts
            for y in range(1, H + 1):
                fl = 0 if y <= 8 else (1 if y <= 15 else 2)
                if post or y in BEAMS:   # the frame stands out one block: white posts, red beams at the floor lines
                    fb = FRAME if post else "minecraft:red_concrete"
                    b.set(x, y, z, fb); b.set(x + ox, y, z + oz, fb)
                    continue
                col = COLS[(pi + 2 * fl + 3 * si) % len(COLS)]
                blk = f"minecraft:{col}_concrete"
                w0, w1 = WROWS[fl]
                half = 2 if oz else 1                    # window: 4 wide on the long sides, 2 on the short
                c = (pa + pb) / 2
                inwin = abs(along - c) <= half - 0.5 + 0.01 and w0 <= y <= w1
                ring = abs(along - c) <= half + 0.5 + 0.01 and w0 - 1 <= y <= w1 + 1 and not inwin
                entrance = oz == 1 and fl == 0 and abs(along - mx) <= 8
                if entrance: b.set(x, y, z, blk); continue
                if inwin: blk = "minecraft:white_stained_glass_pane"
                elif ring: blk = f"minecraft:{col}_terracotta"   # the window frame: a darker shade of the block
                b.set(x, y, z, blk)
                if ring and y == w0 - 1:                 # sill
                    b.set(x + ox, y, z + oz, stairs("minecraft:quartz_stairs", OPP[out], "top"))
    b.box(X0 + 1, 1, Z0 + 1, X1 - 1, H, Z1 - 1, AIR)
    for y in (8, 15): b.box(X0 + 1, y, Z0 + 1, X1 - 1, y, Z1 - 1, "minecraft:birch_planks")
    # pointed toy-block roof: a stepped tent of red and yellow over a deep white eave on brackets
    b.box(X0 - 2, H + 1, Z0 - 2, X1 + 2, H + 1, Z1 + 2, "minecraft:red_concrete")
    for x in range(X0 - 2, X1 + 3, 2):
        for (z, f) in ((Z0 - 2, "south"), (Z1 + 2, "north")): b.set(x, H, z, stairs("minecraft:quartz_stairs", f, "top"))
    for z in range(Z0 - 2, Z1 + 3, 2):
        for (x, f) in ((X0 - 2, "east"), (X1 + 2, "west")): b.set(x, H, z, stairs("minecraft:quartz_stairs", f, "top"))
    for k in range(1, 10):
        b.box(X0 + k * 2 - 1, H + 1 + k, Z0 + k - 1, X1 - k * 2 + 1, H + 1 + k, Z1 - k + 1, ("minecraft:red_concrete", "minecraft:yellow_concrete")[k % 2])
    for (tx, tz, c) in ((X0, Z0, "lime"), (X1, Z0, "light_blue"), (X0, Z1, "pink"), (X1, Z1, "orange")):
        b.cyl(tx, tz, 3, 1, H + 8, f"minecraft:{c}_concrete")
        for yb in BEAMS: b.cyl(tx, tz, 3.6, yb, yb, FRAME)                   # white bands at the floor lines
        b.cyl(tx, tz, 4, H + 8, H + 8, FRAME)                                # crown under the cap
        for (dx, dz) in ((0, 4), (0, -4), (4, 0), (-4, 0)):                  # tower windows looking out
            if (X0 <= tx + dx <= X1) and (Z0 <= tz + dz <= Z1): continue
            for y0 in (3, 10, 17, H + 3):
                for y in (y0, y0 + 1): b.set(tx + dx * 3 // 4, y, tz + dz * 3 // 4, "minecraft:white_stained_glass_pane")
        for k in range(7): b.cyl(tx, tz, max(0.5, 3.6 - k * 0.6), H + 9 + k, H + 9 + k, "minecraft:red_concrete" if k % 2 else "minecraft:white_concrete")
        b.set(tx, H + 16, tz, "minecraft:gold_block")
    # gears and the clock on the front, the carousel-horse weathervane on top
    gear(b, X0 + 9, 14, Z1 + 1, 5, "minecraft:gold_block")
    gear(b, X0 + 18, 18, Z1 + 1, 3, "minecraft:iron_block")
    cx, cy = X1 - 9, 15
    b.cyl(cx, Z1 + 1, 0, cy, cy, "minecraft:white_concrete") if False else None
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx * dx + dy * dy <= 18: b.set(cx + dx, cy + dy, Z1 + 1, "minecraft:white_concrete")
    for k in range(4): b.set(cx, cy + k, Z1 + 2, "minecraft:black_concrete"); b.set(cx + k // 2, cy, Z1 + 2, "minecraft:black_concrete")
    for k in range(12):
        t = math.radians(k * 30)
        b.set(round(cx + 4 * math.cos(t)), round(cy + 4 * math.sin(t)), Z1 + 2, "minecraft:red_concrete")
    b.column(mx, mz, H + 11, H + 18, "minecraft:gold_block")
    b.box(mx - 2, H + 16, mz, mx + 2, H + 17, mz, "minecraft:white_wool"); b.set(mx + 3, H + 18, mz, "minecraft:white_wool"); b.set(mx - 2, H + 18, mz, "minecraft:red_wool")
    for x in range(mx - 3, mx + 4):       # the big front entrance, framed by white pillars under a striped lintel
        for y in range(1, 6): b.set(x, y, Z1, AIR); b.set(x, y, Z1 + 1, AIR)
    for x in (mx - 4, mx + 4):
        for y in range(1, 6): b.set(x, y, Z1 + 1, FRAME)
        b.set(x, 6, Z1 + 2, "minecraft:gold_block")
    for x in range(mx - 4, mx + 5): b.set(x, 6, Z1 + 1, "minecraft:red_concrete" if x % 2 else "minecraft:yellow_concrete")
    for x in range(mx - 3, mx + 4): b.set(x, 7, Z1 + 1, slab("minecraft:quartz_slab", "bottom"))
    # inside: show room, Sugar's grape room, the officers' lounge, stores
    I.furnish(b, X0 + 1, 1, Z0 + 1, X1 - 1, Z1 - 1, 6, "hall", TOY, seed=1)
    for i in range(16):
        x, z = rnd.randint(X0 + 3, X1 - 3), rnd.randint(Z0 + 3, Z1 - 3)
        if b.get(x, 1, z) is None: b.set(x, 1, z, f"minecraft:{rnd.choice(COLS)}_wool" if i % 2 else "minecraft:armor_stand" if False else f"minecraft:{rnd.choice(COLS)}_concrete")
    I.subdivide(b, X0 + 1, 9, Z0 + 1, X1 - 1, Z1 - 1, 5, "minecraft:birch_planks", ("dining", "bedroom", "storage", "study"), TOY, cell=12, corridor=3,
                keepout=((X0 + 1, Z0 + 1, X0 + 3, Z0 + 3),), seed=2)
    I.subdivide(b, X0 + 1, 16, Z0 + 1, X1 - 1, Z1 - 1, 6, "minecraft:birch_planks", ("throne", "tavern", "bedroom", "treasure"), TOY, cell=12, corridor=3,
                keepout=((X0 + 1, Z0 + 1, X0 + 3, Z0 + 3),), seed=3)
    for y in range(1, 16): b.set(X0 + 1, y, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (8, 15): b.set(X0 + 1, y, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    # ---------------- the Toy House is the main entrance to the underground complex: a wide stair from the show
    # room down to the factory floor, railed round its well
    b.stairs_up(46, FY, 27, 13, "minecraft:birch_stairs", "west", w=3)
    for x in range(34, 39):
        for z in (26, 30): b.set(x, 1, z, "minecraft:birch_fence")
    for z in range(26, 31): b.set(39, 1, z, "minecraft:birch_fence")
    for z in range(27, 30): b.set(33, 1, z, AIR); b.set(33, 2, z, AIR)
    for x in range(34, 39):
        for z in range(27, 30):
            if b.get(x, 0, z) in (None, AIR): b.set(x, 1, z, AIR)   # no rug over the stair well
    # and under it the underground trade port: a canal from a sea gate along the north side of the factory,
    # with a plank quay, mooring posts and cargo waiting to be shipped
    b.box(FX0 + 1, FY - 5, FZ0 + 1, FX1 - 16, FY - 1, FZ0 + 6, "minecraft:stone_bricks")
    b.box(FX0 + 1, FY - 4, FZ0 + 2, FX1 - 16, FY - 2, FZ0 + 5, WATER)
    b.box(FX0 + 1, FY - 1, FZ0 + 2, FX1 - 16, FY + 2, FZ0 + 5, AIR)
    # the factory's iron columns that fall in the canal carry on down through the water as piers, on a stone plinth
    # on the canal bed, so none of them hangs from the ceiling
    for x in range(FX0 + 4, FX1 - 3, 8):
        for z in range(FZ0 + 4, FZ1 - 3, 8):
            if FX0 + 1 <= x <= FX1 - 16 and FZ0 + 2 <= z <= FZ0 + 5:
                b.set(x, FY - 4, z, "minecraft:polished_andesite")
                b.column(x, z, FY - 3, -2, "minecraft:iron_block")
    for z in range(FZ0 + 2, FZ0 + 6):   # the sea gate in the west wall
        for y in range(FY - 1, FY + 3): b.set(FX0, y, z, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    for x in range(FX0 + 1, FX1 - 15):
        for z in (FZ0 + 6, FZ0 + 7): b.set(x, FY - 1, z, "minecraft:spruce_planks")
        if x % 6 == 2: b.set(x, FY, FZ0 + 6, "minecraft:spruce_fence")
        elif x % 6 == 4: b.set(x, FY, FZ0 + 7, "minecraft:barrel[facing=up,open=false]")
        elif x % 12 == 7: b.set(x, FY, FZ0 + 7, "minecraft:barrel[facing=up,open=false]"); b.set(x, FY + 1, FZ0 + 7, "minecraft:barrel[facing=up,open=false]")
    # ---------------- the garden: toy soldiers and a little parade road
    T.path(b, [(mx, Z1 + 1), (mx, NZ - 2)], w=2, s="minecraft:yellow_terracotta", alt="minecraft:red_terracotta")
    for z in range(Z1 + 4, NZ - 3, 4):
        for x in (mx - 4, mx + 4):
            b.set(x, 1, z, "minecraft:blue_concrete"); b.set(x, 2, z, "minecraft:red_concrete"); b.set(x, 3, z, "minecraft:white_concrete")
            b.set(x, 4, z, "minecraft:black_wool")
    for (x, z) in ((8, 8), (76, 8), (8, 68), (76, 68)): T.tree(b, x, z, kind="birch", h=6)
    for x in range(4, NX - 4, 10): T.lamp_post(b, x, 4)
    # ---------------- loot and guards
    b.chest(X1 - 3, 16, Z1 - 3, "medium", "west"); b.chest(FX1 - 3, FY, FZ0 + 3, "easy", "west")
    b.guards("donquixote", ((mx - 3, Z1 + 3), (mx + 3, Z1 + 3), (40, 40)), y=1)
    b.guards("donquixote", ((40, 40), (58, 27)), y=FY)
    return b, 0
