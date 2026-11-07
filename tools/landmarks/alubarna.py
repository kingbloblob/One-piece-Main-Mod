"""Alubarna, capital of Alabasta: the royal palace on its cliff, the grand stairway, the palace gardens,
the clock tower on the plaza below (where Pell carried the bomb) and the royal tomb with the Poneglyph
under the palace. ~190 x 190, palace domes ~70 tall. Ground = y 0."""
import math, random
from canvas import *

SID = "alubarna_palace"
TITLE = "Alubarna Palace (Alabasta)"
CUTS = [10, 26]
TILER = dict(terrain="beard_thin")

SAND = "onepiece:alabasta_sandstone_bricks"
SAND_ST = "onepiece:alabasta_sandstone_brick_stairs"
SAND_SL = "onepiece:alabasta_sandstone_brick_slab"
SAND_W = "onepiece:alabasta_sandstone_brick_wall"
TILE = "onepiece:alabasta_tiles"
TILE_ST = "onepiece:alabasta_tile_stairs"
PILLAR = "onepiece:alubarna_pillar[axis=y]"
CUT = "minecraft:cut_sandstone"
SMOOTH = "minecraft:smooth_sandstone"
DOME = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
CLIFF = "minecraft:sandstone"
PLAT = 22          # plateau top (palace ground)
N = 190
CX = 95


def arcade(b, x0, x1, z, y, h, inward):
    """Row of pillars with pointed arches between them along x at depth z."""
    for x in range(x0, x1 + 1, 4):
        b.column(x, z, y, y + h - 1, PILLAR)
    for x in range(x0, x1):
        k = (x - x0) % 4
        if k == 0: continue
        drop = {1: 1, 2: 0, 3: 1}[k]
        b.set(x, y + h - 1 - drop + 1, z, CUT)
        for yy in range(y + h - drop + 1, y + h + 1): b.set(x, yy, z, CUT)
    for x in range(x0, x1 + 1): b.set(x, y + h + 1, z, SAND)


def tower(b, cx, cz, r, y, h, dome_r):
    b.cyl(cx, cz, r, y, y + h, SAND, hollow=True)
    b.disk(cx, y, cz, r - 1, TILE)
    for yy in range(y + 4, y + h - 2, 6):
        for a in range(0, 360, 45):
            t = math.radians(a)
            b.set(round(cx + r * math.cos(t)), yy, round(cz + r * math.sin(t)), pane_of("minecraft:orange_stained_glass_pane"))
            b.set(round(cx + r * math.cos(t)), yy + 1, round(cz + r * math.sin(t)), pane_of("minecraft:orange_stained_glass_pane"))
    for yy in (y + h - 3, y + h):
        b.cyl(cx, cz, r + 1, yy, yy, CUT, hollow=True)
    b.disk(cx, y + h, cz, r, TILE)
    for a in range(0, 360, 20):  # balcony crenels
        t = math.radians(a); b.set(round(cx + (r + 1) * math.cos(t)), y + h + 1, round(cz + (r + 1) * math.sin(t)), SAND_W.replace("wall", "wall") and wall(SAND_W))
    for yy in range(y + 1, y + h):
        b.set(cx, yy, cz - r + 1, ladder("south"))
    b.set(cx, y + h, cz - r + 1, ladder("south"))
    b.cyl(cx, cz, dome_r - 1, y + h + 1, y + h + 3, SAND)
    return b.dome(cx, cz, y + h + 4, dome_r, s=DOME, onion=True)


def house(b, x0, z0, w, d, h, seed):
    """Flat-roofed Alabasta town house with awning and roof parapet."""
    b.box(x0, 0, z0, x0 + w - 1, 0, z0 + d - 1, SMOOTH)
    b.walls(x0, 1, z0, x0 + w - 1, h, z0 + d - 1, SMOOTH if seed % 3 else CUT)
    b.box(x0 + 1, 1, z0 + 1, x0 + w - 2, h, z0 + d - 2, AIR)
    b.box(x0, h + 1, z0, x0 + w - 1, h + 1, z0 + d - 1, SAND)
    for x in range(x0, x0 + w):
        b.set(x, h + 2, z0, wall(SAND_W) if x % 2 else AIR); b.set(x, h + 2, z0 + d - 1, wall(SAND_W) if x % 2 else AIR)
    for z in range(z0, z0 + d):
        b.set(x0, h + 2, z, wall(SAND_W) if z % 2 else AIR); b.set(x0 + w - 1, h + 2, z, wall(SAND_W) if z % 2 else AIR)
    mx = x0 + w // 2
    b.box(mx, 1, z0 + d - 1, mx, 2, z0 + d - 1, AIR)
    color = ("white", "orange", "red", "light_blue", "yellow")[seed % 5]
    for x in range(mx - 2, mx + 3): b.set(x, 4, z0 + d, f"minecraft:{color}_wool".replace("wool", "carpet") if False else f"minecraft:{color}_wool")
    for x in (mx - 2, mx + 2): b.column(x, z0 + d, 1, 3, fence("jungle"))
    for x in range(x0 + 2, x0 + w - 2, 3):
        if x != mx: b.set(x, 3, z0 + d - 1, "minecraft:spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    b.set(x0 + 1, 1, z0 + 1, BARREL); b.set(x0 + w - 2, 1, z0 + 1, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
    if seed % 2: b.set(x0 + 2, h + 2, z0 + 2, "minecraft:potted_dead_bush")
    import interiors as I
    I.furnish(b, x0 + 1, 1, z0 + 1, x0 + w - 2, z0 + d - 2, h, ("bedroom", "kitchen", "tavern", "storage", "bedroom", "workshop")[seed % 6], "desert", seed=seed)


def build():
    b = B()
    # ---------------- ground: the city plaza and streets
    b.box(0, -3, 0, N, -1, N, "minecraft:sandstone")
    b.box(0, 0, 0, N, 0, N, "minecraft:sand")
    for x in range(0, N + 1):
        for z in range(118, N + 1):
            b.set(x, 0, z, SMOOTH if (x // 3 + z // 3) % 2 else CUT)
    # ---------------- the cliff / plateau the palace stands on (with rough eroded edges)
    PX0, PX1, PZ0, PZ1 = 18, 172, 4, 116
    for x in range(PX0 - 6, PX1 + 7):
        for z in range(PZ0 - 4, PZ1 + 7):
            ex = max(PX0 - x, x - PX1, PZ0 - z, z - PZ1, 0)
            n = math.sin(x * 0.37) * 2 + math.cos(z * 0.29) * 2 + math.sin((x + z) * 0.11) * 1.5
            top = PLAT if ex == 0 else int(PLAT - ex * (3.2 + n * 0.3) + n)
            for y in range(1, max(1, top) + 1):
                if y == top and ex: b.set(x, y, z, "minecraft:sand")
                else: b.set(x, y, z, CLIFF if (y + int(n)) % 5 else "minecraft:smooth_sandstone" if (x + z) % 2 else "minecraft:terracotta")
    b.box(PX0, PLAT, PZ0, PX1, PLAT, PZ1, SMOOTH)
    # ---------------- the grand stairway up the cliff (front, facing +z)
    SW = 9
    for i in range(PLAT):
        z = PZ1 + 2 + (PLAT - 1 - i)
        for x in range(CX - SW, CX + SW + 1):
            b.set(x, i + 1, z, stairs(SAND_ST, "north"))
            for yy in range(i + 2, i + 6): b.set(x, yy, z, AIR)
            for yy in range(1, i + 1): b.set(x, yy, z, SAND)
        for x in (CX - SW - 1, CX + SW + 1):
            for yy in range(1, i + 3): b.set(x, yy, z, SAND)
            if i % 4 == 0: b.set(x, i + 3, z, "minecraft:lantern[hanging=false,waterlogged=false]")
    for z in range(PZ1 - 2, PZ1 + 2):
        for x in range(CX - SW, CX + SW + 1):
            b.set(x, PLAT, z, TILE)
            for yy in range(PLAT + 1, PLAT + 5): b.set(x, yy, z, AIR)
    # ---------------- palace outer wall on the plateau edge with the main gate
    WH = 10
    for x in range(PX0, PX1 + 1):
        for z in (PZ0, PZ1):
            b.box(x, PLAT + 1, z, x, PLAT + WH, z, SAND)
            b.set(x, PLAT + WH + 1, z, wall(SAND_W) if x % 3 else SAND)
            b.set(x, PLAT + 3, z, CUT)
    for z in range(PZ0, PZ1 + 1):
        for x in (PX0, PX1):
            b.box(x, PLAT + 1, z, x, PLAT + WH, z, SAND)
            b.set(x, PLAT + WH + 1, z, wall(SAND_W) if z % 3 else SAND)
            b.set(x, PLAT + 3, z, CUT)
    for (tx, tz) in ((PX0, PZ0), (PX1, PZ0), (PX0, PZ1), (PX1, PZ1)):
        tower(b, tx, tz, 5, PLAT, 24, 5)
    # gate house
    b.box(CX - 14, PLAT + 1, PZ1 - 3, CX + 14, PLAT + WH + 8, PZ1 + 1, SAND)
    b.box(CX - 7, PLAT + 1, PZ1 - 3, CX + 7, PLAT + 12, PZ1 + 1, AIR)
    for x in range(CX - 7, CX + 8):  # pointed arch
        d = abs(x - CX)
        for y in range(PLAT + 12 - max(0, d - 3) // 1, PLAT + 15 - d // 3):
            b.set(x, y, PZ1 + 1, CUT); b.set(x, y, PZ1 - 3, CUT)
    for x in (CX - 9, CX + 9):
        for z in (PZ1 + 1, PZ1 + 2): b.column(x, z, PLAT + 1, PLAT + WH + 7, PILLAR)
    for x in range(CX - 14, CX + 15): b.set(x, PLAT + WH + 9, PZ1 - 1, wall(SAND_W) if x % 2 else GOLD)
    tower(b, CX - 14, PZ1 - 1, 4, PLAT, WH + 14, 4); tower(b, CX + 14, PZ1 - 1, 4, PLAT, WH + 14, 4)
    # royal banners on the gate (Alabasta's sun-and-wings crest in gold on red)
    for x in (CX - 11, CX + 11):
        for y in range(PLAT + 6, PLAT + 16): b.set(x, y, PZ1 + 2, "minecraft:red_wool")
        for y in range(PLAT + 9, PLAT + 13): b.set(x, y, PZ1 + 3, "minecraft:yellow_wool" if y % 2 else "minecraft:gold_block")
    # ---------------- front garden: pools, palms, flower beds
    for side in (-1, 1):
        gx = CX + side * 38
        for x in range(gx - 14, gx + 15):
            for z in range(78, 108):
                if abs(x - gx) <= 10 and 84 <= z <= 102:
                    b.set(x, PLAT, z, WATER); b.set(x, PLAT - 1, z, "minecraft:prismarine_bricks".replace("prismarine_bricks", "dark_prismarine") if (x + z) % 7 == 0 else "minecraft:light_blue_terracotta")
                elif abs(x - gx) <= 11 and 83 <= z <= 103:
                    b.set(x, PLAT, z, TILE); b.set(x, PLAT + 1, z, slab(SAND_SL))
        for (px, pz) in ((gx - 13, 80), (gx + 13, 80), (gx - 13, 106), (gx + 13, 106), (gx, 80), (gx, 106)):
            b.set(px, PLAT, pz, "minecraft:grass_block[snowy=false]"); b.palm(px, PLAT + 1, pz, 9)
        b.box(gx - 1, PLAT, 92, gx + 1, PLAT + 2, 94, SAND)
        b.set(gx, PLAT + 3, 93, "minecraft:water[level=0]")
    for z in range(76, PZ1 - 3, 2):
        for x in (CX - 10, CX + 10):
            b.set(x, PLAT, z, "minecraft:grass_block[snowy=false]"); b.set(x, PLAT + 1, z, "onepiece:desert_bloom" if z % 4 else "minecraft:dead_bush")
    for z in range(PZ0 + 1, PZ1 - 2):
        for x in range(CX - 7, CX + 8): b.set(x, PLAT, z, TILE)
    # ---------------- the palace itself
    # front arcade wing (z 56..74), central throne hall with the great dome, side wings and towers
    FY = PLAT
    b.box(CX - 54, FY, 18, CX + 54, FY, 74, TILE)
    # wings, 2 storeys
    for (x0, x1) in ((CX - 54, CX - 20), (CX + 20, CX + 54)):
        b.walls(x0, FY + 1, 24, x1, FY + 16, 66, SAND)
        b.box(x0 + 1, FY + 1, 25, x1 - 1, FY + 16, 65, AIR)
        b.box(x0 + 1, FY + 8, 25, x1 - 1, FY + 8, 65, TILE)
        b.box(x0, FY + 17, 24, x1, FY + 17, 66, SAND)
        for x in range(x0, x1 + 1):
            for z in (24, 66): b.set(x, FY + 18, z, wall(SAND_W) if x % 2 else AIR); b.set(x, FY + 8, z, CUT); b.set(x, FY + 16, z, CUT)
        for z in range(24, 67):
            for x in (x0, x1): b.set(x, FY + 18, z, wall(SAND_W) if z % 2 else AIR); b.set(x, FY + 8, z, CUT); b.set(x, FY + 16, z, CUT)
        for x in range(x0 + 3, x1 - 1, 4):  # tall arched windows on both floors
            for z in (24, 66):
                for y in list(range(FY + 3, FY + 7)) + list(range(FY + 10, FY + 15)):
                    b.set(x, y, z, pane_of("minecraft:orange_stained_glass_pane") if y in (FY + 6, FY + 14) else PANE)
        arcade(b, x0, x1, 70, FY + 1, 8, 1)          # shaded arcade in front of the wing
        b.box(x0, FY + 10, 67, x1, FY + 10, 70, SAND)
        for x in range(x0, x1 + 1): b.set(x, FY + 11, 70, wall(SAND_W))
        tower(b, x0, 24, 6, FY, 34, 6); tower(b, x1 if x0 < CX else x1, 66, 5, FY, 28, 5) if False else None
        tower(b, x0, 24, 6, FY, 34, 6)
        tower(b, (x0 if x0 < CX else x1), 66, 5, FY, 26, 5)
        # rooms: royal chambers (beds, rugs, wardrobes), library, guard room
        for x in range(x0 + 3, x1 - 2, 6):
            bed("red" if x0 < CX else "yellow", x, FY + 9, 26, b, "south")
            b.set(x + 2, FY + 9, 26, "minecraft:bookshelf"); b.set(x + 2, FY + 10, 26, "minecraft:bookshelf")
            b.box(x - 1, FY + 9, 30, x + 2, FY + 9, 33, "minecraft:red_carpet" if x % 2 else "minecraft:orange_carpet")
            b.set(x, FY + 15, 40, "minecraft:lantern[hanging=true,waterlogged=false]"); b.set(x, FY + 7, 50, "minecraft:lantern[hanging=true,waterlogged=false]")
        for z in range(28, 64, 4):
            b.set(x0 + 1, FY + 1, z, "minecraft:bookshelf"); b.set(x0 + 1, FY + 2, z, "minecraft:bookshelf"); b.set(x0 + 1, FY + 3, z, "minecraft:bookshelf")
            b.table_set(x0 + 8, FY + 1, z, "jungle", "red")
        b.stairs_up(x1 - 2, FY + 1, 30, 7, SAND_ST, "south", w=2)
        # partitions into rooms on both floors, with doorways
        for pz in (38, 52):
            for fy in (FY + 1, FY + 9):
                for x in range(x0 + 1, x1):
                    for y in range(fy, fy + 7): b.set(x, y, pz, SAND)
                for x in range((x0 + x1) // 2 - 1, (x0 + x1) // 2 + 2):
                    for y in range(fy, fy + 3): b.set(x, y, pz, AIR)
                for x in (x0 + 3, x1 - 3):
                    for y in range(fy, fy + 3): b.set(x, y, pz, AIR)
                b.set((x0 + x1) // 2, fy + 3, pz, "minecraft:chiseled_sandstone")
        import interiors as I
        left = x0 < CX
        kinds1 = ("library", "dining", "kitchen") if left else ("library", "dining", "armory")
        kinds2 = ("bedroom", "bath", "study") if left else ("bedroom", "barracks", "treasure")
        for (z0r, z1r), k1, k2 in zip(((25, 37), (39, 51), (53, 65)), kinds1, kinds2):
            I.furnish(b, x0 + 1, FY + 1, z0r, x1 - 1, z1r, 7, k1, "desert")
            I.furnish(b, x0 + 1, FY + 9, z0r, x1 - 1, z1r, 7, k2, "royal")
        # wing door into the arcade
        for x in range((x0 + x1) // 2 - 1, (x0 + x1) // 2 + 2):
            for y in range(FY + 1, FY + 5): b.set(x, y, 66, AIR)
    # central throne hall
    HX0, HX1, HZ0, HZ1 = CX - 19, CX + 19, 16, 72
    b.walls(HX0, FY + 1, HZ0, HX1, FY + 24, HZ1, SAND)
    b.box(HX0 + 1, FY + 1, HZ0 + 1, HX1 - 1, FY + 24, HZ1 - 1, AIR)
    for x in range(HX0, HX1 + 1):
        for z in (HZ0, HZ1): b.set(x, FY + 24, z, CUT); b.set(x, FY + 12, z, CUT); b.set(x, FY + 25, z, wall(SAND_W) if x % 2 else GOLD)
    for z in range(HZ0, HZ1 + 1):
        for x in (HX0, HX1): b.set(x, FY + 24, z, CUT); b.set(x, FY + 12, z, CUT); b.set(x, FY + 25, z, wall(SAND_W) if z % 2 else GOLD)
    b.box(HX0, FY + 24, HZ0, HX1, FY + 24, HZ1, SAND)
    # the great dome over the throne room, on a drum
    DZ = 40
    b.cyl(CX, DZ, 16, FY + 25, FY + 30, SAND, hollow=True)
    for a in range(0, 360, 15):
        t = math.radians(a)
        for y in (FY + 27, FY + 28): b.set(round(CX + 16 * math.cos(t)), y, round(DZ + 16 * math.sin(t)), pane_of("minecraft:yellow_stained_glass_pane"))
    b.cyl(CX, DZ, 17, FY + 30, FY + 30, CUT)
    b.box(CX - 15, FY + 24, DZ - 15, CX + 15, FY + 24, DZ + 15, AIR)
    for x in range(CX - 15, CX + 16):
        for z in range(DZ - 15, DZ + 16):
            if math.hypot(x - CX, z - DZ) > 15.4: b.set(x, FY + 24, z, SAND)
    b.dome(CX, DZ, FY + 31, 16, h=24, s=DOME, onion=True)
    for yy in range(FY + 31, FY + 34): b.cyl(CX, DZ, 15, yy, yy, "minecraft:yellow_terracotta", hollow=True)  # gold band
    # front facade of the hall: tall pointed entrance, columns, balcony where the king speaks
    for x in range(CX - 5, CX + 6):
        for y in range(FY + 1, FY + 11 - abs(x - CX) // 2): b.set(x, y, HZ1, AIR)
    for x in (CX - 7, CX + 7, CX - 13, CX + 13):
        b.column(x, HZ1 + 1, FY + 1, FY + 22, PILLAR)
    b.box(CX - 14, FY + 13, HZ1 + 1, CX + 14, FY + 13, HZ1 + 4, SAND)
    for x in range(CX - 14, CX + 15): b.set(x, FY + 14, HZ1 + 4, wall(SAND_W))
    for y in range(FY + 14, FY + 18): b.set(CX, y, HZ1, AIR); b.set(CX - 1, y, HZ1, AIR); b.set(CX + 1, y, HZ1, AIR)
    for x in range(CX - 12, CX + 13, 3):
        for y in range(FY + 16, FY + 22): b.set(x, y, HZ1, pane_of("minecraft:orange_stained_glass_pane") if y > FY + 19 else PANE)
    b.box(CX - 2, FY + 20, HZ1 + 1, CX + 2, FY + 23, HZ1 + 1, GOLD)  # royal crest
    b.set(CX, FY + 21, HZ1 + 2, "minecraft:red_concrete"); b.set(CX, FY + 22, HZ1 + 2, "minecraft:red_concrete")
    # interior of the throne hall: two rows of pillars, red carpet, throne, chandeliers
    for z in range(HZ0 + 4, HZ1 - 2, 5):
        for x in (CX - 9, CX + 9): b.column(x, z, FY + 1, FY + 23, PILLAR)
    for z in range(HZ0 + 1, HZ1):
        for x in range(CX - 2, CX + 3): b.set(x, FY + 1, z, "minecraft:red_carpet")
        for x in (CX - 3, CX + 3): b.set(x, FY + 1, z, "minecraft:yellow_carpet")
    b.box(CX - 5, FY + 1, HZ0 + 2, CX + 5, FY + 2, HZ0 + 6, "minecraft:gold_block".replace("gold_block", "smooth_quartz"))
    b.set(CX, FY + 3, HZ0 + 4, stairs("minecraft:quartz_stairs", "north"))
    for x in (CX - 1, CX + 1): b.set(x, FY + 3, HZ0 + 4, GOLD)
    b.box(CX - 1, FY + 4, HZ0 + 3, CX + 1, FY + 7, HZ0 + 3, GOLD)
    for x in (CX - 4, CX + 4): b.column(x, HZ0 + 4, FY + 3, FY + 6, fence("jungle")); b.set(x, FY + 7, HZ0 + 4, "minecraft:lantern[hanging=false,waterlogged=false]")
    for z in range(HZ0 + 10, HZ1 - 4, 10):
        b.set(CX, FY + 23, z, CHAIN); b.set(CX, FY + 22, z, CHAIN)
        b.disk(CX, FY + 21, z, 2, "minecraft:gold_block".replace("gold_block", "iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"))
        for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)): b.set(CX + dx, FY + 20, z + dz, "minecraft:lantern[hanging=true,waterlogged=false]")
    for z in range(HZ0 + 3, HZ1 - 2, 4):  # banners of the royal family along the walls
        for x in (HX0 + 1, HX1 - 1):
            for y in range(FY + 14, FY + 20): b.set(x, y, z, "minecraft:red_wool" if y > FY + 14 else "minecraft:yellow_wool")
    # back terrace overlooking the desert, with a high tower
    b.box(CX - 30, FY, PZ0 + 1, CX + 30, FY, 15, TILE)
    tower(b, CX, 10, 7, FY, 42, 7)
    b.chest(CX + 3, FY + 1, HZ0 + 3, "treasure", "west")
    # ---------------- royal tomb under the palace (the Poneglyph)
    TY = 8
    b.box(CX - 12, TY, 28, CX + 12, TY + 9, 52, SAND)
    b.box(CX - 11, TY + 1, 29, CX + 11, TY + 8, 51, AIR)
    for x in range(CX - 9, CX + 10, 6):
        for z in (32, 48): b.column(x, z, TY + 1, TY + 8, PILLAR)
    for z in range(30, 51, 5):
        for x in (CX - 8, CX + 8):  # sarcophagi of the past kings
            b.box(x - 1, TY + 1, z, x + 1, TY + 1, z + 1, "minecraft:gold_block" if z % 2 else "minecraft:chiseled_sandstone")
            b.set(x, TY + 2, z, slab(SAND_SL))
    b.box(CX - 1, TY + 1, 30, CX + 1, TY + 3, 32, "onepiece:poneglyph")  # the Poneglyph: a great black stone cube
    b.set(CX - 3, TY + 1, 34, "minecraft:soul_lantern[hanging=false,waterlogged=false]"); b.set(CX + 3, TY + 1, 34, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    for z in range(36, 51, 4): b.set(CX, TY + 8, z, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    # secret stairway from the throne room down to the tomb
    for i in range(FY - TY):
        z = 52 + i + 1
        for x in (CX + 14, CX + 15):
            b.set(x, FY - i, z, stairs(SAND_ST, "south"))
            for yy in range(FY - i + 1, FY - i + 4): b.set(x, yy, z, AIR)
    for z in range(52, 54):
        for x in (CX + 14, CX + 15):
            for y in range(TY + 1, TY + 4): b.set(x, y, z, AIR)
    for x in range(CX + 12, CX + 16):
        for y in range(TY + 1, TY + 4): b.set(x, y, 52, AIR)
    # ---------------- the round central plaza just outside the palace (where the armies met) and the clock tower
    PZC, PR = 162, 22
    for x in range(CX - PR - 1, CX + PR + 2):
        for z in range(PZC - PR - 1, PZC + PR + 2):
            d = math.hypot(x - CX, z - PZC)
            if d > PR + 0.5: continue
            ang = math.degrees(math.atan2(z - PZC, x - CX)) % 30
            ring = int(d)
            s_ = SAND if d > PR - 0.6 else TILE if (ang < 2.5 or ang > 27.5) and d > 6 else CUT if ring % 4 == 0 else SMOOTH
            b.set(x, 0, z, s_)
    for x in range(CX - 8, CX + 9):  # the stairway foot opens onto the plaza
        for z in range(PZ1 + 2 + PLAT, PZC - PR + 1): b.set(x, 0, z, TILE if abs(x - CX) > 2 else CUT)
    # fountain in the middle of the plaza
    b.cyl(CX, PZC, 7, 0, 0, SAND); b.cyl(CX, PZC, 7.4, 1, 1, CUT, hollow=True); b.cyl(CX, PZC, 6.4, 1, 1, WATER)
    b.cyl(CX, PZC, 2, 1, 2, SAND); b.cyl(CX, PZC, 2.4, 3, 3, CUT, hollow=True); b.disk(CX, 3, PZC, 1.6, WATER)
    b.column(CX, PZC, 1, 5, PILLAR); b.set(CX, 6, PZC, GOLD); b.set(CX, 7, PZC, WATER)
    # the clock tower: an extremely tall Big Ben-like tower on the south rim of the plaza, clock faces on all four
    # sides, the large open area at the very top (where Crocodile's bomb cannon was hidden) and a steep spire
    KX, KZ = CX, PZC + PR - 3
    KH = 52
    b.box(KX - 8, 0, KZ - 8, KX + 8, 0, KZ + 8, CUT)
    b.box(KX - 7, 1, KZ - 7, KX + 7, 2, KZ + 7, SAND)
    for k in range(-7, 8):
        b.set(KX + k, 1, KZ - 8, stairs(SAND_ST, "south")); b.set(KX + k, 1, KZ + 8, stairs(SAND_ST, "north"))
        b.set(KX - 8, 1, KZ + k, stairs(SAND_ST, "east")); b.set(KX + 8, 1, KZ + k, stairs(SAND_ST, "west"))
    b.walls(KX - 5, 3, KZ - 5, KX + 5, KH, KZ + 5, SAND)
    b.box(KX - 4, 1, KZ - 4, KX + 4, KH + 12, KZ + 4, AIR)
    b.box(KX - 4, 0, KZ - 4, KX + 4, 0, KZ + 4, TILE)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):  # corner buttresses with pinnacles
        for (ox, oz) in ((5, 5), (6, 5), (5, 6), (6, 6)):
            b.column(KX + sx * ox, KZ + sz * oz, 1, KH, CUT)
        b.column(KX + sx * 6, KZ + sz * 6, KH + 1, KH + 13, CUT)
    for (fx, fz, nx, nz, f) in ((0, -1, 1, 0, "north"), (0, 1, 1, 0, "south"), (-1, 0, 0, 1, "west"), (1, 0, 0, 1, "east")):
        for k in (-3, 0, 3):  # vertical pilaster strips
            for y in range(3, KH + 1): b.set(KX + fx * 6 + nx * k, y, KZ + fz * 6 + nz * k, SMOOTH)
        for y in range(3, KH + 1, 12):  # string courses
            for k in range(-5, 6): b.set(KX + fx * 6 + nx * k, y, KZ + fz * 6 + nz * k, stairs(SAND_ST, OPP[f], "top") if y > 3 else CUT)
        for y0 in range(6, KH - 4, 8):  # tall lancet windows between the strips
            for k in (-2, -1, 1, 2):
                for y in range(y0, y0 + 4): b.set(KX + fx * 5 + nx * k, y, KZ + fz * 5 + nz * k, PANE if y < y0 + 3 else pane_of("minecraft:orange_stained_glass_pane"))
                b.set(KX + fx * 6 + nx * k, y0 - 1, KZ + fz * 6 + nz * k, stairs(SAND_ST, OPP[f], "top"))
        for k in (-1, 0, 1):  # the door, facing the plaza
            if f == "north":
                for y in range(1, 6): b.set(KX + k, y, KZ - 5, AIR); b.set(KX + k, y, KZ - 6, AIR); b.set(KX + k, y, KZ - 7, AIR)
    for k in range(-2, 3): b.set(KX + k, 6, KZ - 7, CUT if abs(k) < 2 else GOLD)
    # the clock stage, wider than the shaft, a clock face proud of each side
    b.walls(KX - 6, KH + 1, KZ - 6, KX + 6, KH + 12, KZ + 6, SAND)
    for (fx, fz, nx, nz) in ((0, -1, 1, 0), (0, 1, 1, 0), (-1, 0, 0, 1), (1, 0, 0, 1)):
        cy = KH + 6
        for i in range(-5, 6):
            for j in range(-5, 6):
                r = math.hypot(i, j)
                if r > 4.6: continue
                px, pz = KX + fx * 7 + nx * i, KZ + fz * 7 + nz * i
                b.set(px, cy + j, pz, GOLD if r > 3.6 else "minecraft:white_concrete")
                b.set(KX + fx * 6 + nx * i, cy + j, KZ + fz * 6 + nz * i, CUT)
        for (i, j) in ((0, 3), (3, 0), (0, -3), (-3, 0)): b.set(KX + fx * 7 + nx * i, cy + j, KZ + fz * 7 + nz * i, "minecraft:black_concrete")
        for j in range(0, 3): b.set(KX + fx * 7, cy + j, KZ + fz * 7, "minecraft:black_concrete")  # minute hand at 12
        for i in range(1, 3): b.set(KX + fx * 7 + nx * i, cy - i // 2, KZ + fz * 7 + nz * i, "minecraft:black_concrete")  # hour hand
    b.box(KX - 7, KH + 13, KZ - 7, KX + 7, KH + 13, KZ + 7, CUT)
    for k in range(-7, 8):
        b.set(KX + k, KH + 12, KZ - 7, stairs(SAND_ST, "south", "top")); b.set(KX + k, KH + 12, KZ + 7, stairs(SAND_ST, "north", "top"))
        b.set(KX - 7, KH + 12, KZ + k, stairs(SAND_ST, "east", "top")); b.set(KX + 7, KH + 12, KZ + k, stairs(SAND_ST, "west", "top"))
    # the open area at the very top: corner piers, two arches a side, a balustrade, the bell
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        for (ox, oz) in ((6, 6), (5, 6), (6, 5)): b.column(KX + sx * ox, KZ + sz * oz, KH + 14, KH + 21, SAND)
    for (fx, fz, nx, nz) in ((0, -1, 1, 0), (0, 1, 1, 0), (-1, 0, 0, 1), (1, 0, 0, 1)):
        b.column(KX + fx * 6, KZ + fz * 6, KH + 14, KH + 21, PILLAR)
        for k in range(-4, 5):
            b.set(KX + fx * 6 + nx * k, KH + 14, KZ + fz * 6 + nz * k, wall(SAND_W))
            b.set(KX + fx * 6 + nx * k, KH + 21, KZ + fz * 6 + nz * k, CUT)
            if abs(k) in (1, 4): b.set(KX + fx * 6 + nx * k, KH + 20, KZ + fz * 6 + nz * k, stairs(SAND_ST, "east" if (nx * k) < 0 else "west", "top") if nx else stairs(SAND_ST, "south" if (nz * k) < 0 else "north", "top"))
    b.box(KX - 7, KH + 22, KZ - 7, KX + 7, KH + 22, KZ + 7, SAND)
    b.set(KX, KH + 21, KZ, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    # steep spire with a gold finial
    y = KH + 23
    for i in range(7):
        hw = 6 - i
        for k in range(-hw, hw + 1):
            for (x, z, f) in ((KX + k, KZ - hw, "south"), (KX + k, KZ + hw, "north"), (KX - hw, KZ + k, "east"), (KX + hw, KZ + k, "west")):
                b.set(x, y, z, TILE); b.set(x, y + 1, z, stairs(TILE_ST, f))
        if hw > 1: b.box(KX - hw + 1, y, KZ - hw + 1, KX + hw - 1, y + 1, KZ + hw - 1, TILE)
        y += 2
    b.set(KX, y, KZ, GOLD); b.set(KX, y + 1, KZ, GOLD); b.set(KX, y + 2, KZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # ladder all the way up inside, on a pier that runs from the floor of the shaft (bonded to the east wall) up
    # through the clock stage, so every rung has a solid block behind it
    b.column(KX + 4, KZ, 1, KH + 12, SAND)
    for yy in range(1, KH + 14): b.set(KX + 3, yy, KZ, ladder("west"))
    b.set(KX + 3, KH + 13, KZ, ladder("west"))
    # town houses round the plaza and along the streets
    import random
    rnd = random.Random(7)
    for (x0, z0) in [(x, z) for x in range(4, 70, 16) for z in (124, 146, 168)] + [(x, z) for x in range(124, 186, 16) for z in (124, 146, 168)]:
        if x0 + 13 > N: continue
        hh = rnd.choice((5, 6, 7, 9)); sd = rnd.randint(0, 99)
        if any(math.hypot(x - CX, z - PZC) < PR + 3 for x in (x0, x0 + 11) for z in (z0, z0 + 14)) or (x0 + 12 > CX - 9 and x0 < CX + 9): continue
        house(b, x0, z0, 12, 14, hh, sd)
    for (x, z) in ((70, 130), (120, 130), (CX - 16, PZC - 16), (CX + 16, PZC - 16), (CX - 22, PZC + 8), (CX + 22, PZC + 8)):
        b.set(x, 0, z, "minecraft:grass_block[snowy=false]"); b.palm(x, 1, z, 8)
    for x in range(10, N - 10, 12):  # market stalls along the plaza
        if abs(x - CX) > 12: b.stall(x, 0, 186, ("red", "orange", "yellow", "white")[x % 4])
    # ---------------- people
    b.guards("baroque_agent", ((CX - 6, 110), (CX + 6, 110), (CX - 4, 60), (CX + 4, 60), (CX, 140)), y=PLAT + 1)
    b.entities[-1] = (b.entities[-1][0], CX, 1, 140, b.entities[-1][4])
    # ---------------- extra dressing: throne hall and tomb
    import interiors as I
    r = I.Room(b, HX0 + 1, FY + 1, HZ0 + 1, HX1 - 1, HZ1 - 1, 22, "royal", random.Random(5))
    r.paintings(6); r.plants(6)
    r = I.Room(b, CX - 11, TY + 1, 29, CX + 11, 51, 8, "desert", random.Random(6))
    r.scatter(("minecraft:decorated_pot", I.candle_str("yellow", 4), "minecraft:skeleton_skull[rotation=0]", "minecraft:gold_block"), 18)
    return b, 0
