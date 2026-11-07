"""Syrup Village: the quiet farming village where Usopp grew up. Kaya's grand mansion behind its iron gate on the
hill (entrance hall, dining room, library, Kaya's bedroom, servants' quarters, the garden with the fountain),
the village houses and Usopp's little house, the inn, the orchard, the Usopp Pirates' hideout in the hollow tree,
and the steep slope road down to the north coast. ~88 x 88. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "syrup_village"
TITLE = "Syrup Village (Kaya's Mansion)"
CUTS = [3, 10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 88
POSH = dict(wood="dark_oak", rug="red", rug2="yellow", bed="white", light="minecraft:lantern", accent="minecraft:gold_block",
            banner="white", candle="white")


def shallow_hip(b, x0, z0, x1, z1, y, st, full):
    """A big-house hip roof at half pitch: one block up for every two in (stair, then a full block), so a wide
    mansion is not crowned by a pyramid. Returns the top y."""
    x0 -= 1; z0 -= 1; x1 += 1; z1 += 1
    i = 0
    while True:
        a0, c0, a1, c1 = x0 + 2 * i, z0 + 2 * i, x1 - 2 * i, z1 - 2 * i
        yy = y + i
        if a1 - a0 < 2 or c1 - c0 < 2:
            b.box(a0, yy, c0, a1, yy, c1, slab(st.replace("_stairs", "_slab"), "bottom"))
            return yy
        for x in range(a0 + 1, a1):
            b.set(x, yy, c0, stairs(st, "south")); b.set(x, yy, c1, stairs(st, "north"))
        for z in range(c0 + 1, c1):
            b.set(a0, yy, z, stairs(st, "east")); b.set(a1, yy, z, stairs(st, "west"))
        b.set(a0, yy, c0, stairs(st, "east", shape="outer_right")); b.set(a1, yy, c0, stairs(st, "south", shape="outer_right"))
        b.set(a0, yy, c1, stairs(st, "north", shape="outer_right")); b.set(a1, yy, c1, stairs(st, "west", shape="outer_right"))
        b.box(a0 + 1, yy, c0 + 1, a1 - 1, yy, c1 - 1, full)
        i += 1


def mansion_facade(b, x0, z0, x1, z1, G, FL, top, gx):
    """Depth for Kaya's mansion: a stone base course, quartz pilasters standing proud of the white walls, cornices at
    every floor and under the eaves, sills and lintels at every window, a centre pavilion brought forward with a
    pediment, a half-pitch slate hip roof with dormers, and tall chimneys."""
    Q, QS, QP = "minecraft:smooth_quartz", "minecraft:quartz_stairs", "minecraft:quartz_pillar[axis=y]"
    faces = (("north", [(x, z0) for x in range(x0, x1 + 1)], (0, -1)), ("south", [(x, z1) for x in range(x0, x1 + 1)], (0, 1)),
             ("west", [(x0, z) for z in range(z0, z1 + 1)], (-1, 0)), ("east", [(x1, z) for z in range(z0, z1 + 1)], (1, 0)))
    win = lambda x, y, z: "glass_pane" in (b.get(x, y, z) or "")
    for (f, cells, (ox, oz)) in faces:
        for k, (x, z) in enumerate(cells):
            b.set(x, G + 1, z, "minecraft:stone_bricks")                     # base course
            ex, ez = x + ox, z + oz
            if k % 6 == 0 or k == len(cells) - 1:                             # pilasters
                b.column(ex, ez, G + 1, top - 1, QP)
                b.set(ex, G + 1, ez, "minecraft:stone_bricks")
                continue
            for yc in (FL[1] - 1, FL[2] - 1):                                 # floor cornices
                b.set(ex, yc, ez, stairs(QS, OPP[f], "top"))
            b.set(ex, top, ez, stairs(QS, OPP[f], "top"))                     # eave cornice
            for fy in FL:                                                     # sills and lintels
                if win(x, fy + 1, z):
                    if fy > FL[0]: b.set(ex, fy, ez, stairs(QS, OPP[f], "top"))
                    b.set(x, fy + 4, z, Q) if fy + 4 not in (FL[1] - 1, FL[2] - 1) else None
            if b.get(ex, G + 1, ez) in (None, AIR): b.set(ex, G + 1, ez, slab("minecraft:stone_brick_slab", "bottom"))
    # the centre pavilion, one block forward of the north front, with its own pilasters and a pediment
    px0, px1, pz = gx - 6, gx + 6, z0 - 1
    for x in range(px0, px1 + 1):
        for y in range(G + 1, top + 1):
            behind = b.get(x, y, z0) or ""
            b.set(x, y, pz, "minecraft:glass_pane" if "glass_pane" in behind else ("minecraft:stone_bricks" if y == G + 1 else "minecraft:white_concrete"))
        for fy in FL:
            if win(x, fy + 1, pz):
                if fy > FL[0]: b.set(x, fy, pz - 1, stairs(QS, "south", "top"))
                b.set(x, fy + 4, pz, Q) if fy + 4 not in (FL[1] - 1, FL[2] - 1) else None
        for yc in (FL[1] - 1, FL[2] - 1, top): b.set(x, yc, pz - 1, stairs(QS, "south", "top"))
    for x in (px0, px1): b.column(x, pz - 1, G + 1, top - 1, QP)
    roof_top = shallow_hip(b, x0, z0, x1, z1, top + 1, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles")
    # the pediment: a triangle of white over the pavilion, edged with slate stairs, a round window in it
    for i in range(0, 8):
        y = top + 1 + i
        for z in range(pz - 1, z0 + 6):
            if px0 - 1 + i <= px1 + 1 - i:
                b.set(px0 - 1 + i, y, z, stairs("minecraft:deepslate_tile_stairs", "east"))
                b.set(px1 + 1 - i, y, z, stairs("minecraft:deepslate_tile_stairs", "west"))
        for x in range(px0 + i, px1 - i + 1):
            b.set(x, y, pz, "minecraft:white_concrete")
            for z in range(pz + 1, z0 + 6):
                if b.get(x, y, z) in (None, AIR): b.set(x, y, z, "minecraft:deepslate_tiles")
    b.set(gx, top + 7, pz - 1, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
    for z in range(pz - 1, z0 + 6): b.set(gx, top + 8, z, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
    b.set(gx, top + 3, pz, "minecraft:glass_pane"); b.set(gx, top + 4, pz, "minecraft:glass_pane")
    for (dx, dy) in ((-1, 3), (1, 3), (-1, 4), (1, 4), (0, 2), (0, 5)): b.set(gx + dx, top + dy, pz, Q)
    # dormers on the long slopes, over every other window bay
    for x in range(x0 + 5, x1 - 2, 6):
        for (zf, f, inward) in ((z0 + 1, "north", 1), (z1 - 1, "south", -1)):
            if f == "north" and px0 - 2 <= x <= px1 + 2: continue
            for dx in (-1, 1):
                for y in (top + 2, top + 3): b.set(x + dx, y, zf, "minecraft:white_concrete")
            for y in (top + 2, top + 3): b.set(x, y, zf, "minecraft:glass_pane")
            b.set(x, top + 1, zf - inward, stairs(QS, OPP[f], "top"))
            for zz in (zf, zf + inward, zf + 2 * inward):
                b.set(x - 1, top + 4, zz, stairs("minecraft:deepslate_tile_stairs", "east"))
                b.set(x + 1, top + 4, zz, stairs("minecraft:deepslate_tile_stairs", "west"))
                b.set(x, top + 4, zz, "minecraft:deepslate_tiles"); b.set(x, top + 5, zz, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
                for dx in (-1, 0, 1):
                    for y in (top + 2, top + 3):
                        if zz != zf and b.get(x + dx, y, zz) in (None, AIR): b.set(x + dx, y, zz, "minecraft:deepslate_tiles")
    # tall chimneys with a stone cap, smoking
    for x in (x0 + 4, x1 - 4):
        zc = (z0 + z1) // 2
        for yy in range(top + 1, roof_top + 4): b.set(x, yy, zc, "minecraft:bricks"); b.set(x + 1, yy, zc, "minecraft:bricks")
        b.set(x, roof_top + 4, zc, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
        b.set(x + 1, roof_top + 4, zc, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def kaya_tree(b, wx, wz, fy, G):
    """A big oak beside the east wall with a stout branch reaching the sill of Kaya's window (floor fy)."""
    tx, tz = wx + 5, wz
    for yy in range(G + 1, fy + 9):
        for (dx, dz) in ((0, 0), (1, 0), (0, -1), (1, -1)): b.set(tx + dx, yy, tz + dz, "minecraft:oak_log[axis=y]")
    for (dx, dz) in ((-1, 0), (2, -1), (0, 1), (1, -2)): b.set(tx + dx, G + 1, tz + dz, "minecraft:oak_wood[axis=y]")  # root flare
    for x in range(wx + 2, tx): b.set(x, fy, wz, "minecraft:oak_log[axis=x]")    # the branch to the window sill
    b.set(wx + 2, fy + 1, wz, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")
    for x in range(tx + 2, tx + 5): b.set(x, fy + 3, tz - 1, "minecraft:oak_log[axis=x]")
    cy = fy + 9
    for x in range(tx - 4, tx + 7):
        for y in range(cy - 4, cy + 5):
            for z in range(tz - 6, tz + 6):
                if x <= wx + 1: continue
                d = ((x - tx - 0.5) / 5.5) ** 2 + ((y - cy) / 4.2) ** 2 + ((z - tz + 0.5) / 5.5) ** 2
                if d <= 1 and b.get(x, y, z) in (None, AIR) and (x * 3 + y * 5 + z * 7) % 13:
                    b.set(x, y, z, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")


def build():
    rnd = random.Random(231)
    b = B()
    T.ground(b, N, N, rnd)
    T.sea(b, N, N, lambda x, z: z < 6 + 2 * math.sin(x * 0.2), depth=4)
    # the slope road down to the coast (north)
    for z in range(4, 20):
        for x in range(60, 66):
            b.set(x, 0, z, "minecraft:dirt_path" if (x + z) % 3 else "minecraft:coarse_dirt")
            for yy in (1, 2): b.set(x, yy, z, AIR) if (x, yy, z) in b.blocks else None
    for z in range(4, 20, 4):
        for x in (59, 66): b.set(x, 1, z, fence("oak"))
    # ---------------- Kaya's mansion on a low terrace (south-west)
    MX0, MX1, MZ0, MZ1 = 8, 40, 50, 76
    for x in range(MX0 - 6, MX1 + 7):
        for z in range(MZ0 - 12, MZ1 + 6):
            b.set(x, 1, z, "minecraft:grass_block"); b.set(x, 0, z, "minecraft:dirt")
            if b.get(x, 2, z) is not None: b.set(x, 2, z, AIR)
    G = 1  # ground level of the estate
    for x in range(MX0 - 6, MX1 + 7):  # iron fence with stone posts
        for z in (MZ0 - 12, MZ1 + 5):
            b.set(x, G + 1, z, "minecraft:stone_bricks" if x % 5 == 0 else "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
            if x % 5 == 0: b.set(x, G + 2, z, "minecraft:lantern[hanging=false,waterlogged=false]")
    for z in range(MZ0 - 12, MZ1 + 6):
        for x in (MX0 - 6, MX1 + 6):
            b.set(x, G + 1, z, "minecraft:stone_bricks" if z % 5 == 0 else "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    gx = (MX0 + MX1) // 2
    for x in range(gx - 2, gx + 3): b.set(x, G + 1, MZ0 - 12, AIR)
    # the iron gate Usopp is always being thrown out of: two leaves standing open, an iron arch between the posts
    for x in (gx - 2, gx + 2):
        for z in (MZ0 - 11, MZ0 - 10):
            for y in (G + 1, G + 2, G + 3): b.set(x, y, z, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    for x in range(gx - 2, gx + 3):
        b.set(x, G + 4, MZ0 - 12, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.set(gx, G + 5, MZ0 - 12, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    for x in (gx - 3, gx + 3): b.column(x, MZ0 - 12, G + 1, G + 4, "minecraft:stone_bricks", cap="minecraft:lantern[hanging=false,waterlogged=false]")
    for z in range(MZ0 - 11, MZ0):  # gravel drive and the fountain
        for x in range(gx - 2, gx + 3): b.set(x, G, z, "minecraft:gravel")
    b.cyl(gx, MZ0 - 6, 3, G + 1, G + 1, "minecraft:quartz_bricks"); b.cyl(gx, MZ0 - 6, 2, G + 1, G + 1, WATER)
    b.set(gx, G + 2, MZ0 - 6, "minecraft:quartz_pillar[axis=y]"); b.set(gx, G + 3, MZ0 - 6, "minecraft:sea_lantern")
    for (x, z) in ((MX0 - 3, MZ0 - 8), (MX1 + 3, MZ0 - 8), (MX0 - 3, MZ1 + 2), (MX1 + 3, MZ1 + 2)): T.tree(b, x, z, y=G, kind="birch", h=6)
    for x in range(MX0 - 4, MX1 + 5, 2):  # flower borders
        for z in (MZ0 - 2, MZ0 - 10): b.set(x, G + 1, z, rnd.choice(("minecraft:rose_bush[half=lower]", "minecraft:peony[half=lower]", "minecraft:lilac[half=lower]")))
    for x in range(MX0 - 4, MX1 + 5, 2):
        for z in (MZ0 - 2, MZ0 - 10):
            low = b.get(x, G + 1, z); b.set(x, G + 2, z, low.replace("lower", "upper")) if low and "lower" in low else None
    # the house: three floors, white walls, dark blue mansard roof
    WALL = "minecraft:white_concrete"
    FL = (G + 1, G + 7, G + 13)
    top = G + 19
    b.box(MX0, G, MZ0, MX1, G, MZ1, "minecraft:polished_andesite")
    b.walls(MX0, G + 1, MZ0, MX1, top, MZ1, WALL)
    b.box(MX0 + 1, G + 1, MZ0 + 1, MX1 - 1, top, MZ1 - 1, AIR)
    for f in FL[1:]: b.box(MX0 + 1, f - 1, MZ0 + 1, MX1 - 1, f - 1, MZ1 - 1, "minecraft:dark_oak_planks")
    for f in FL:
        for x in range(MX0 + 2, MX1 - 1, 3):
            for z in (MZ0, MZ1):
                for k in (1, 2, 3): b.set(x, f + k, z, "minecraft:glass_pane")
        for z in range(MZ0 + 2, MZ1 - 1, 3):
            for x in (MX0, MX1):
                for k in (1, 2, 3): b.set(x, f + k, z, "minecraft:glass_pane")
    mansion_facade(b, MX0, MZ0, MX1, MZ1, G, FL, top, gx)
    # porch with columns in front of the centre pavilion, the door behind it
    for x in (gx - 4, gx + 4): b.column(x, MZ0 - 4, G + 1, G + 5, "minecraft:quartz_pillar[axis=y]")
    b.box(gx - 5, G + 6, MZ0 - 5, gx + 5, G + 6, MZ0 - 2, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    for x in range(gx - 5, gx + 6): b.set(x, G + 5, MZ0 - 5, stairs("minecraft:quartz_stairs", "south", "top")) if x not in (gx - 4, gx + 4) else None
    for x in range(gx - 4, gx + 5):
        for z in range(MZ0 - 4, MZ0 - 1): b.set(x, G, z, "minecraft:polished_andesite")
    for x in range(gx - 1, gx + 2):
        for y in range(G + 1, G + 5):
            for z in (MZ0 - 1, MZ0): b.set(x, y, z, AIR)
    b.set(gx - 1, G + 1, MZ0, door("minecraft:dark_oak_door", "north", "lower", "left")); b.set(gx - 1, G + 2, MZ0, door("minecraft:dark_oak_door", "north", "upper", "left"))
    b.set(gx + 1, G + 1, MZ0, door("minecraft:dark_oak_door", "north", "lower", "right")); b.set(gx + 1, G + 2, MZ0, door("minecraft:dark_oak_door", "north", "upper", "right"))
    for y in (G + 1, G + 2): b.set(gx, y, MZ0, "minecraft:quartz_pillar[axis=y]")  # the mullion between the pair
    for x in range(gx - 1, gx + 2):  # a glass fanlight over the doors and a smooth quartz lintel, in the wall and the pavilion
        for z in (MZ0 - 1, MZ0):
            b.set(x, G + 3, z, "minecraft:glass_pane"); b.set(x, G + 4, z, "minecraft:smooth_quartz")
    # the big tree outside Kaya's bedroom window that Usopp climbs to tell her his stories: the branch reaches the east
    # window at z MZ0+14 of the floor above the ground floor, which is the window of Kaya's room (see the rooms below)
    kaya_tree(b, MX1, MZ0 + 14, FL[1], G)
    # rooms
    SX = MX1 - 4
    for f, nf in zip(FL, FL[1:]):
        for i in range(nf - f):
            for w in (0, 1, 2): b.set(SX + w - 1, f + i, MZ1 - 2 - i, stairs("minecraft:dark_oak_stairs", "north"))
            for w in (0, 1, 2):
                for k in (1, 2, 3):
                    c = b.get(SX + w - 1, f + i + k, MZ1 - 2 - i)
                    if c not in (None, AIR) and "dark_oak_stairs" not in c: b.set(SX + w - 1, f + i + k, MZ1 - 2 - i, AIR)
    KEEP = ((SX - 2, MZ1 - 10, SX + 2, MZ1 - 1),)
    for z in range(MZ0 + 1, MZ1):  # entrance hall in the middle of the ground floor
        for y in range(FL[0], FL[1] - 1):
            for x in (gx - 5, gx + 5): b.set(x, y, z, WALL)
    for y in (FL[0], FL[0] + 1, FL[0] + 2):
        for x in (gx - 5, gx + 5): b.set(x, y, MZ0 + 8, AIR)
    r = I.furnish(b, gx - 4, FL[0], MZ0 + 1, gx + 4, MZ1 - 1, 5, "hall", POSH); r.chandelier(gx, (MZ0 + MZ1) // 2, 2, 2)
    I.furnish(b, MX0 + 1, FL[0], MZ0 + 1, gx - 6, MZ1 - 1, 5, "dining", POSH)
    I.furnish(b, gx + 6, FL[0], MZ0 + 1, MX1 - 1, MZ1 - 1, 5, "kitchen", POSH)
    # the floor above (FL[1]): a corridor runs east from the west wall to Kaya's door. Kaya's bedroom fills the east end
    # north of the stair well (x KX+1..MX1-1, z MZ0+1..MZ0+14), so the window the tree's branch reaches is hers. West of
    # her wall the corridor has the library, the bath, the study and, in the south-east, a second library that opens
    # straight onto the stair well.
    KX = MX1 - 7
    for z in range(MZ0 + 1, MZ0 + 16):  # her west wall, with her door at the end of the corridor
        for y in range(FL[1], FL[1] + 5):
            b.set(KX, y, z, AIR if (z in (MZ0 + 12, MZ0 + 13) and y < FL[1] + 3) else WALL)
    for x in range(KX + 1, MX1):  # her south wall, between her room and the stair well
        for y in range(FL[1], FL[1] + 5): b.set(x, y, MZ0 + 15, WALL)
    I.subdivide(b, MX0 + 1, FL[1], MZ0 + 1, KX - 1, MZ1 - 1, 5, WALL, ("library", "bath", "study", "library"), POSH, cell=10, keepout=KEEP, seed=4)
    I.furnish(b, KX + 1, FL[1], MZ0 + 1, MX1 - 1, MZ0 + 14, 5, "bedroom", POSH, seed=41)
    # Kaya's dressing table against her west wall: a dark oak desk three wide with a tall tinted-glass mirror in the
    # middle, a candle and a flower pot either side of it, and a stool in front
    vx, vz = KX + 1, MZ0 + 4
    for dz in (-1, 0, 1):
        b.set(vx, FL[1], vz + dz, stairs("minecraft:dark_oak_stairs", "west", "top"))
        for y in (FL[1], FL[1] + 1, FL[1] + 2): b.set(vx + 1, y, vz + dz, AIR)
    for y in (FL[1] + 1, FL[1] + 2): b.set(vx, y, vz, "minecraft:tinted_glass")
    b.set(vx, FL[1] + 1, vz - 1, "minecraft:white_candle[candles=2,lit=true,waterlogged=false]")
    b.set(vx, FL[1] + 1, vz + 1, "minecraft:potted_pink_tulip")
    b.set(vx + 1, FL[1], vz, stairs("minecraft:dark_oak_stairs", "east"))
    # and her chair at the tree window, facing out, where she listens to Usopp's stories
    for y in (FL[1], FL[1] + 1, FL[1] + 2): b.set(MX1 - 1, y, MZ0 + 14, AIR)
    b.set(MX1 - 1, FL[1], MZ0 + 14, stairs("minecraft:dark_oak_stairs", "west"))
    I.subdivide(b, MX0 + 1, FL[2], MZ0 + 1, MX1 - 1, MZ1 - 1, 5, WALL, ("bedroom", "bedroom", "barracks", "storage", "bedroom"), POSH, cell=10, keepout=KEEP, seed=5)
    # ---------------- the village
    T.path(b, [(gx, MZ0 - 13), (gx, 40), (80, 40)], w=1, alt="minecraft:coarse_dirt")
    T.path(b, [(62, 40), (62, 18)], w=1)
    spots = [(46, 46, "tavern"), (58, 46, None), (70, 46, None), (46, 28, None), (70, 28, "kitchen"), (76, 58, None), (48, 60, None),
             (60, 60, None), (34, 28, None), (22, 28, None), (10, 26, None)]
    for (x0, z0, kind) in spots:
        w, d = rnd.randint(7, 9), rnd.randint(6, 8)
        T.house(b, x0, z0, w, d, 2 if kind else rnd.choice((1, 2)), rnd.choice(("cottage", "east_blue", "orange")), rnd,
                kinds=[kind, "bedroom"] if kind else None, door="north" if z0 > 40 else "south", sign="minecraft:red_wool" if kind == "tavern" else None)
    # Usopp's house: small, with his workbench and slingshot target
    T.house(b, 74, 70, 7, 6, 1, "cottage", rnd, kinds=["workshop"], door="north")
    for (x, z) in ((72, 66), (80, 66)): b.set(x, 1, z, "minecraft:target"); b.set(x, 2, z, "minecraft:target")
    # orchard and fields
    for i in range(10): T.orchard_tree(b, 20 + (i % 5) * 5, 10 + (i // 5) * 6)
    T.garden(b, 46, 8, 56, 16, crop="minecraft:potatoes[age=7]")
    # the Usopp Pirates' hollow-tree hideout
    hx, hz = 80, 12
    b.cyl(hx, hz, 3, 1, 9, "minecraft:oak_wood[axis=y]", hollow=True); b.cyl(hx, hz, 2, 0, 0, "minecraft:oak_planks")
    b.sphere(hx, 12, hz, 5, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", ry=3.5)
    b.set(hx, 1, hz + 3, AIR); b.set(hx, 2, hz + 3, AIR)
    b.set(hx - 1, 1, hz - 1, "minecraft:crafting_table"); b.set(hx + 1, 1, hz - 1, "minecraft:barrel[facing=up,open=false]")
    b.jolly_roger(hx, 15, hz + 1, 5, 3, axis="z")
    for y in range(9, 16): b.set(hx, y, hz, "minecraft:oak_fence")
    # ---------------- people and loot
    b.npc(72, 1, 67, "usopp", False)
    b.chest(MX0 + 2, FL[2], MZ0 + 2, "easy", "east"); b.chest(hx + 1, 1, hz + 1, "easy", "west")
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open ground rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0
