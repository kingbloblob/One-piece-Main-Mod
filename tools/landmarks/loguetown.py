"""Loguetown, the Town of the Beginning and the End. The great execution square with the tall wooden scaffold
where Gol D. Roger died, ringed by three- and four-storey brick and stone townhouses with shops on the ground
floor (Ipponmatsu's sword shop, the tailor, the bar, the restaurant), the Marine base where Captain Smoker is
stationed, the harbour and the clock tower. ~100 x 100. Ground = y 0, sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "loguetown"
TITLE = "Loguetown Execution Square"
CUTS = [3, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 100
CX, CZ = 50, 44
SZ = CZ - 4  # the scaffold stands north of the square's centre, so its long stair lands on open paving
SEA = 88
MAR = I.THEMES["marine"]


H = 20  # deck level of the execution platform (the condemned kneel at y H + 1)


def scaffold(b, cx, cz):
    """The execution platform where Roger died and Buggy later locked Luffy in the stocks: a tall open timber tower
    (dark oak legs and ring beams, X-braced panels), a railed deck on bracket stairs, the wooden stocks at the front of
    the deck, and the long straight stair down to the square with its stringers, handrails and props."""
    LEG, BEAM, BRACE = "minecraft:dark_oak_log[axis=y]", "minecraft:dark_oak_log", "minecraft:stripped_spruce_log[axis=y]"
    ring = (7, 13)
    for (ya, yb) in ((0, 7), (7, 13), (13, H - 1)):  # an X brace in every panel
        for (a0, a1) in ((cx - 5, cx), (cx, cx + 5)):
            for z in (cz - 5, cz + 5):
                b.line((a0, ya, z), (a1, yb, z), BRACE); b.line((a1, ya, z), (a0, yb, z), BRACE)
        for (a0, a1) in ((cz - 5, cz), (cz, cz + 5)):
            for x in (cx - 5, cx + 5):
                b.line((x, ya, a0), (x, yb, a1), BRACE); b.line((x, ya, a1), (x, yb, a0), BRACE)
    for y in ring + (H - 1,):  # ring beams round the tower
        for x in range(cx - 5, cx + 6):
            for z in (cz - 5, cz + 5):
                if (x - cx) % 5: b.set(x, y, z, BEAM + "[axis=x]")
        for z in range(cz - 5, cz + 6):
            for x in (cx - 5, cx + 5):
                if (z - cz) % 5: b.set(x, y, z, BEAM + "[axis=z]")
    for x in (cx - 5, cx, cx + 5):  # legs on stone pads, and a king post in the middle
        for z in (cz - 5, cz, cz + 5): b.column(x, z, 1, H - 1, LEG)
    for x in range(cx - 5, cx + 6):  # the ground under the braces stays paved
        for z in (cz - 5, cz + 5): b.set(x, 0, z, "minecraft:polished_andesite")
    for z in range(cz - 5, cz + 6):
        for x in (cx - 5, cx + 5): b.set(x, 0, z, "minecraft:polished_andesite")
    # the deck: dark planks with a lighter border, bracket stairs under the overhang, a rail with lanterns at the corners
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            edge = x in (cx - 6, cx + 6) or z in (cz - 6, cz + 6)
            b.set(x, H, z, "minecraft:spruce_planks" if edge else "minecraft:dark_oak_planks")
    for k in range(-6, 7, 2):
        for (x, z, f) in ((cx + k, cz - 6, "south"), (cx + k, cz + 6, "north"), (cx - 6, cz + k, "east"), (cx + 6, cz + k, "west")):
            if b.get(x, H - 1, z) in (None, AIR): b.set(x, H - 1, z, stairs("minecraft:dark_oak_stairs", f, "top"))
    for x in range(cx - 6, cx + 7):
        for z in (cz - 6, cz + 6): b.set(x, H + 1, z, fence("dark_oak"))
    for z in range(cz - 6, cz + 7):
        for x in (cx - 6, cx + 6): b.set(x, H + 1, z, fence("dark_oak"))
    for (dx, dz) in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
        b.set(cx + dx, H + 1, cz + dz, "minecraft:dark_oak_log[axis=y]"); b.set(cx + dx, H + 2, cz + dz, lantern())
    # the stocks: two posts with a split board across them, the hole for the neck in the middle, facing the square
    sz = cz + 2
    for x in (cx - 2, cx + 2): b.column(x, sz, H + 1, H + 3, "minecraft:dark_oak_log[axis=y]")
    for x in (cx - 1, cx + 1): b.set(x, H + 2, sz, "minecraft:spruce_planks")
    b.set(cx, H + 2, sz, AIR)
    for x in range(cx - 1, cx + 2): b.set(x, H + 3, sz, slab("minecraft:spruce_slab", "bottom"))
    b.set(cx, H + 1, sz, AIR)
    # the long stair from the square, with stringers, a handrail and props down to the paving
    for i in range(H):
        z = cz + 7 + H - 1 - i
        for w in (-1, 0, 1):
            b.set(cx + w, i + 1, z, stairs("minecraft:dark_oak_stairs", "north"))
            if i >= 1: b.set(cx + w, i, z, "minecraft:dark_oak_planks")
        for w in (-2, 2):
            b.set(cx + w, i + 1, z, "minecraft:spruce_planks")
            if i >= 1: b.set(cx + w, i, z, "minecraft:spruce_planks")
            b.set(cx + w, i + 2, z, fence("dark_oak"))
            if i % 5 == 4: b.column(cx + w, z, 1, i - 1, "minecraft:dark_oak_log[axis=y]")
    for z in range(cz + 6, cz + 8):
        for w in (-1, 0, 1): b.set(cx + w, H + 1, z, AIR)


def townhouse(b, x0, z0, w, d, floors, rnd, shop=None, facing="south", sign=None):
    style = rnd.choice(("brick", "stone", "plaster", "brick"))
    kinds = [shop or "tavern"] + ["bedroom", "study", "bedroom"][:floors - 1]
    return T.house(b, x0, z0, w, d, floors, style, rnd, kinds=kinds, door=facing, sign=sign, chimney=True)


# the Marine gull emblem, spread wings over the head (rows top to bottom), 16 wide so it centres on an even facade
GULL = ("##............##",
        ".###........###.",
        "..####....####..",
        "...####..####...",
        ".....######.....",
        "......####......")


def gull(b, x0, y, z, s):
    """The gull with its left edge at x0 and top row at y, in the plane z (symmetric, so it reads from both sides)."""
    for r, row in enumerate(GULL):
        for c, ch in enumerate(row):
            if ch == "#": b.set(x0 + c, y - r, z, s)


def marine_base(b, x0, z0, x1, z1):
    """The Marine base: two storeys of white Marine brick framed by quartz pilasters (one every five blocks), paired
    windows with sills and lintels, light-blue floor and cornice bands, a tall parapet with MARINE in blue towards the
    town and the harbour, a raised centre panel with the blue gull on both faces, the flag, and a columned porch."""
    WH, PIL, BL, DB = "onepiece:marine_bricks", "minecraft:quartz_pillar[axis=y]", "minecraft:light_blue_concrete", "minecraft:blue_concrete"
    TOP = 19
    b.box(x0, 0, z0, x1, 0, z1, "minecraft:polished_andesite")
    b.walls(x0, 1, z0, x1, TOP, z1, WH)
    b.box(x0 + 1, 1, z0 + 1, x1 - 1, TOP, z1 - 1, AIR)
    b.box(x0 + 1, 6, z0 + 1, x1 - 1, 6, z1 - 1, "minecraft:birch_planks")
    b.box(x0 + 1, 12, z0 + 1, x1 - 1, 12, z1 - 1, "minecraft:birch_planks")
    b.box(x0 + 1, 13, z0 + 1, x1 - 1, 13, z1 - 1, "onepiece:marine_tiles")
    faces = [("north", [(x, z0) for x in range(x0, x1 + 1)], (0, -1)), ("south", [(x, z1) for x in range(x0, x1 + 1)], (0, 1)),
             ("west", [(x0, z) for z in range(z0, z1 + 1)], (-1, 0)), ("east", [(x1, z) for z in range(z0, z1 + 1)], (1, 0))]
    for (f, cells, (ox, oz)) in faces:
        for k, (x, z) in enumerate(cells):
            for y in (6, 12, TOP): b.set(x, y, z, BL)                # floor band, cornice, coping
            if k % 2 == 0: b.set(x, TOP + 1, z, "onepiece:marine_brick_wall")
            if k % 5 == 0 or k == len(cells) - 1:                   # a pilaster every five blocks and at the corners
                for y in range(1, 13): b.set(x + ox, y, z + oz, PIL)
                b.set(x + ox, 13, z + oz, stairs("minecraft:quartz_stairs", OPP[f], "top"))
                b.set(x + ox, 0, z + oz, "minecraft:polished_andesite")
            elif k % 5 in (2, 3):                                   # paired windows between the pilasters
                for fy in (2, 8):
                    for y in (fy, fy + 1, fy + 2): b.set(x, y, z, pane_of("minecraft:light_blue_stained_glass_pane"))
                    b.set(x + ox, fy - 1, z + oz, stairs("minecraft:quartz_stairs", OPP[f], "top"))
                    b.set(x, fy + 3, z, "minecraft:smooth_quartz")
    # MARINE on the parapet, towards the town (north, read from -z) and the harbour (south)
    b.text(x1 - 2, 14, z0, "MARINE", DB, axis="x", step=-1)
    b.text(x0 + 1, 14, z1, "MARINE", DB, axis="x", step=1)
    # a raised centre panel on both faces with the gull, stepped shoulders either side
    xm = (x0 + x1 + 1) // 2                                         # the facade is an even number of blocks wide
    for z in (z0, z1):
        for y in range(TOP + 1, TOP + 9):
            hw = 10 if y <= TOP + 2 else 8
            for x in range(xm - hw, xm + hw):
                b.set(x, y, z, BL if y == TOP + 8 or (y == TOP + 2 and abs(x - xm + 0.5) > 8) else WH)
        gull(b, xm - 8, TOP + 7, z, DB)
        for x in (xm - 11, xm + 10): b.set(x, TOP + 1, z, "onepiece:marine_brick_wall")
    for z in range(z0 + 1, z1):  # tie the two panels together over the roof
        b.set(xm - 1, TOP + 8, z, BL); b.set(xm, TOP + 8, z, BL)
    # the flagpole with the Marine flag
    fz = (z0 + z1) // 2
    for y in range(14, TOP + 13): b.set(xm, y, fz, fence("birch"))
    for zz in range(1, 6):
        for y in (TOP + 9, TOP + 10, TOP + 11): b.set(xm, y, fz + zz, BL if y == TOP + 10 else "minecraft:white_wool")
    # the entrance porch on the town side: two columns, a blue canopy, steps
    for y in (1, 2, 3):
        for x in (xm - 1, xm): b.set(x, y, z0, AIR)
    b.set(xm - 1, 1, z0, door("minecraft:birch_door", "north", "lower", "left")); b.set(xm - 1, 2, z0, door("minecraft:birch_door", "north", "upper", "left"))
    b.set(xm, 1, z0, door("minecraft:birch_door", "north", "lower", "right")); b.set(xm, 2, z0, door("minecraft:birch_door", "north", "upper", "right"))
    for x in (xm - 1, xm):  # a glass transom over the doors and the quartz lintel above it close the frame
        b.set(x, 3, z0, pane_of("minecraft:light_blue_stained_glass_pane")); b.set(x, 4, z0, "minecraft:smooth_quartz")
    for x in (xm - 3, xm + 2): b.column(x, z0 - 3, 1, 4, PIL, base="minecraft:polished_andesite")
    for x in range(xm - 4, xm + 4):
        for z in range(z0 - 3, z0): b.set(x, 5, z, BL)
        for z in (z0 - 1, z0 - 2, z0 - 3): b.set(x, 0, z, "minecraft:polished_andesite")
    for x in range(xm - 2, xm + 2):
        for z in range(z0 - 3, z0): b.set(x, 1, z, AIR)
    # ladder between the floors and the interiors
    for k in range(1, 13): b.set(x0 + 1, k, z1 - 1, "minecraft:ladder[facing=north,waterlogged=false]")
    b.set(x0 + 1, 13, z1 - 1, trapdoor("minecraft:birch_trapdoor", "north", "bottom"))
    I.subdivide(b, x0 + 1, 1, z0 + 1, x1 - 1, z1 - 1, 4, "minecraft:white_concrete", ("armory", "dining", "barracks", "storage"), MAR, cell=7,
                keepout=((x0 + 1, z1 - 3, x0 + 3, z1 - 1), (xm - 2, z0 + 1, xm + 1, z0 + 2)), seed=7)
    I.subdivide(b, x0 + 1, 7, z0 + 1, x1 - 1, z1 - 1, 4, "minecraft:white_concrete", ("captain", "barracks", "library", "armory"), MAR, cell=7,
                keepout=((x0 + 1, z1 - 3, x0 + 3, z1 - 1),), seed=8)


def build():
    rnd = random.Random(251)
    b = B()
    T.ground(b, N, N, rnd, top="minecraft:stone_bricks", deco=0)
    T.sea(b, N, N, lambda x, z: z > SEA, depth=5)
    # the paved square with a ring pattern
    for x in range(CX - 22, CX + 23):
        for z in range(CZ - 20, CZ + 25):
            d = math.hypot(x - CX, z - CZ)
            b.set(x, 0, z, "minecraft:polished_andesite" if int(d) % 6 == 0 else ("minecraft:stone_bricks" if (x + z) % 2 else "minecraft:smooth_stone"))
    scaffold(b, CX, SZ)
    # the ring of townhouses round the square, shops facing in
    rows = []
    for i, x0 in enumerate(range(CX - 30, CX + 26, 11)):
        rows.append((x0, CZ - 34, 10, 10, "south")); rows.append((x0, CZ + 28, 10, 10, "north"))
    for i, z0 in enumerate(range(CZ - 20, CZ + 22, 11)):
        rows.append((CX - 36, z0, 10, 10, "south")); rows.append((CX + 27, z0, 10, 10, "south"))
    shops = [("armory", "minecraft:gray_wool"), ("workshop", "minecraft:white_wool"), ("tavern", "minecraft:red_wool"),
             ("dining", "minecraft:yellow_wool"), ("kitchen", "minecraft:orange_wool"), ("storage", "minecraft:brown_wool"), ("library", "minecraft:blue_wool")]
    for i, (x0, z0, w, d, f) in enumerate(rows):
        if x0 < 1 or z0 < 1 or x0 + w >= N - 1 or z0 + d >= SEA - 2: continue
        if x0 + w >= 65 and z0 + d >= 71: continue  # leave room for the Marine base
        shop, sign = shops[i % len(shops)]
        townhouse(b, x0, z0, w, d, rnd.choice((3, 3, 4)), rnd, shop, f, sign)
    # the Marine base by the harbour (south-east), where Captain Smoker is stationed
    mx0, mz0 = 66, 72
    marine_base(b, mx0, mz0, mx0 + 25, mz0 + 13)
    # clock tower (west)
    cx, cz = 10, 76
    b.walls(cx - 3, 1, cz - 3, cx + 3, 26, cz + 3, "minecraft:bricks"); b.box(cx - 2, 1, cz - 2, cx + 2, 26, cz + 2, AIR)
    for y in range(1, 26): b.set(cx, y, cz - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for (dx, dz) in ((0, 3), (0, -3), (3, 0), (-3, 0)):
        b.set(cx + dx, 22, cz + dz, "minecraft:white_concrete"); b.set(cx + dx, 21, cz + dz, "minecraft:black_concrete")
    b.hip_roof(cx - 3, cz - 3, cx + 3, cz + 3, 27, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles")
    b.set(cx, 23, cz, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    b.set(cx, 1, cz + 3, AIR); b.set(cx, 2, cz + 3, AIR)
    # harbour quay and piers
    for x in range(N):
        for z in (SEA - 1, SEA):
            b.set(x, 0, z, "minecraft:stone_bricks"); b.set(x, 1, z, "minecraft:stone_brick_wall") if z == SEA and x % 9 else None
    for x0 in (20, 44): T.pier(b, x0, SEA + 1, 10)
    for x in range(4, N - 4, 12): T.lamp_post(b, x, SEA - 2)
    for x in range(CX - 20, CX + 21, 8):
        for z in (CZ - 18, CZ + 22): T.lamp_post(b, x, z)
    # crowds' crates and stalls
    for (x, z, c) in ((CX - 18, CZ + 10, "red"), (CX + 14, CZ + 10, "blue"), (CX - 18, CZ - 12, "yellow"), (CX + 14, CZ - 12, "green")):
        T.stall(b, x, z, c, ("minecraft:melon", "minecraft:pumpkin", "onepiece:mikan_crate", None))
    # ---------------- people and loot
    b.npc(CX, H + 1, SZ - 2, "smoker", True)
    b.chest(mx0 + 3, 7, mz0 + 3, "marine", "east")
    b.guards("marine", ((CX - 8, CZ + 10), (CX + 8, CZ + 10), (CX - 3, CZ + 20)))
    b.guards("marine_rifle", ((CX - 5, SZ - 5), (CX + 5, SZ - 5)), y=H + 1)
    # the empty paved corners outside the ring turn to grass and roll (guide 9b.1, 11a); the square and the quay stay paved
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, meadow=True, unpave="minecraft:stone_bricks",
                keep=lambda x, z: z >= SEA - 3 or (CX - 23 <= x <= CX + 23 and CZ - 21 <= z <= CZ + 25))
    return b, 0
