"""Arlong Park (Conomi Islands, East Blue): the Fish-Man pirates' walled Chinese-style compound with the central tower,
the seawater pool in the courtyard and the canal that lets sea creatures swim in through a pair of tall iron sea gates.
The main building is eight storeys (two-storey main hall + a six-level pagoda tower, Nami's map room at the top),
~104 x 104, tower ~70 tall.
Ground = y 0. The gate faces +z (south); the canal leaves through the north wall toward the sea."""
import math
from canvas import *

SID = "arlong_park"
TITLE = "Arlong Park"
CUTS = [6]
TILER = dict(terrain="beard_thin")

WALL = "onepiece:dressrosa_stucco"
WALL2 = "minecraft:smooth_sandstone"
TRIM = "minecraft:cut_red_sandstone"
ROOF_ST = "minecraft:prismarine_brick_stairs"
ROOF = "minecraft:prismarine_bricks"
ROOF_SLAB = "minecraft:prismarine_brick_slab"
PAVE = "minecraft:smooth_stone"
PAVE2 = "minecraft:stone_bricks"
RED = "minecraft:red_terracotta"
POST = "minecraft:stripped_mangrove_log[axis=y]"
N = 104
CX = 52


def chinese_hall(b, x0, z0, x1, z1, y, h, floors=1, roof_layers=3):
    """A hall with red posts, cream walls, lattice windows and a flared teal tile roof. Returns the roof top y."""
    for f in range(floors):
        fy = y + f * (h + 1)
        b.box(x0, fy, z0, x1, fy, z1, "minecraft:spruce_planks")
        b.walls(x0, fy + 1, z0, x1, fy + h, z1, WALL)
        b.box(x0 + 1, fy + 1, z0 + 1, x1 - 1, fy + h, z1 - 1, AIR)
        for x in range(x0, x1 + 1, 4):
            for z in (z0, z1):
                for yy in range(fy + 1, fy + h + 1): b.set(x, yy, z, POST)
        for z in range(z0, z1 + 1, 4):
            for x in (x0, x1):
                for yy in range(fy + 1, fy + h + 1): b.set(x, yy, z, POST)
        for x in range(x0 + 2, x1 - 1, 4):
            for z in (z0, z1):
                b.set(x, fy + 2, z, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]".replace("north", "south" if z == z1 else "north"))
                b.set(x, fy + 3, z, pane_of("minecraft:glass_pane"))
        for z in range(z0 + 2, z1 - 1, 4):
            for x in (x0, x1):
                b.set(x, fy + 3, z, pane_of("minecraft:glass_pane"))
        for x in range(x0, x1 + 1):
            b.set(x, fy + h, z0, TRIM); b.set(x, fy + h, z1, TRIM)
        for z in range(z0, z1 + 1):
            b.set(x0, fy + h, z, TRIM); b.set(x1, fy + h, z, TRIM)
        if f < floors - 1:  # small eave between floors
            for x in range(x0 - 1, x1 + 2):
                b.set(x, fy + h + 1, z0 - 1, stairs(ROOF_ST, "south")); b.set(x, fy + h + 1, z1 + 1, stairs(ROOF_ST, "north"))
            for z in range(z0 - 1, z1 + 2):
                b.set(x0 - 1, fy + h + 1, z, stairs(ROOF_ST, "east")); b.set(x1 + 1, fy + h + 1, z, stairs(ROOF_ST, "west"))
    top = y + floors * (h + 1)
    cx = (x0 + x1) // 2; cz = (z0 + z1) // 2
    hw = (x1 - x0) // 2 + 2; hd = (z1 - z0) // 2 + 2
    b.box(x0, top, z0, x1, top, z1, "minecraft:spruce_planks")
    t = b.pagoda_roof(cx, cz, hw, hd, top, ROOF_ST, ROOF, layers=min(roof_layers, min(hw, hd)), slab_block=ROOF_SLAB)
    # ridge
    for x in range(cx - max(0, hw - roof_layers), cx + max(0, hw - roof_layers) + 1):
        b.set(x, t, cz, slab(ROOF_SLAB))
    return t


def build():
    b = B()
    # ---------------- ground plate (foundation down into the terrain)
    b.box(0, -4, 0, N, -1, N, "minecraft:stone")
    b.box(0, 0, 0, N, 0, N, PAVE)
    for x in range(4, N - 3, 6):
        for z in range(4, N - 3, 6): b.set(x, 0, z, PAVE2)
    # ---------------- outer wall with walkway and crenellations
    H = 13
    for (x0, z0, x1, z1) in ((2, 2, N - 2, 4), (2, N - 4, N - 2, N - 2), (2, 2, 4, N - 2), (N - 4, 2, N - 2, N - 2)):
        b.box(x0, 1, z0, x1, H, z1, WALL)
    for x in range(2, N - 1):
        for z in (2, N - 2):
            b.set(x, H + 1, z, WALL if x % 2 else AIR); b.set(x, 2, z, TRIM); b.set(x, H, z, TRIM)
    for z in range(2, N - 1):
        for x in (2, N - 2):
            b.set(x, H + 1, z, WALL if z % 2 else AIR); b.set(x, 2, z, TRIM); b.set(x, H, z, TRIM)
    for x in range(5, N - 4, 8):  # inner buttress posts and lanterns on the walkway
        for z in (5, N - 5):
            b.column(x, z, 1, H, POST); b.set(x, H + 1, z, "onepiece:paper_lantern[hanging=false]")
    # corner turrets
    for (tx, tz) in ((3, 3), (N - 3, 3), (3, N - 3), (N - 3, N - 3)):
        b.box(tx - 4, 1, tz - 4, tx + 4, H + 6, tz + 4, WALL)
        b.box(tx - 3, H + 1, tz - 3, tx + 3, H + 6, tz + 3, AIR)
        for dx in (-4, 4):
            for dz in (-4, 4): b.column(tx + dx, tz + dz, 1, H + 6, POST)
        for d in (-2, 0, 2):
            for (px, pz) in ((tx + d, tz - 4), (tx + d, tz + 4), (tx - 4, tz + d), (tx + 4, tz + d)):
                b.set(px, H + 4, pz, pane_of("minecraft:glass_pane"))
        b.box(tx - 3, H, tz - 3, tx + 3, H, tz + 3, "minecraft:spruce_planks")
        b.pagoda_roof(tx, tz, 6, 6, H + 7, ROOF_ST, ROOF, layers=5, slab_block=ROOF_SLAB)
        b.set(tx, H + 12, tz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # stairs up to the wall walkway (inside, by the gate)
    for sx in (CX - 14, CX + 14):
        for i in range(H - 1):
            for k in range(3):
                b.set(sx + (i if sx > CX else -i) * 0 + k * (1 if sx > CX else -1), 1 + i, N - 6 - i, stairs(PAVE2.replace("stone_bricks", "stone_brick_stairs"), "north"))
                b.box(sx + k * (1 if sx > CX else -1), 1, N - 6 - i, sx + k * (1 if sx > CX else -1), i, N - 6 - i, PAVE2) if i else None
    # ---------------- the gate (south) with the ARLONG PARK sign
    G0, G1 = CX - 6, CX + 6
    b.box(G0 - 4, 1, N - 6, G1 + 4, H + 9, N - 1, WALL)
    b.box(G0, 1, N - 6, G1, 11, N - 1, AIR)
    b.arch_x(G0, G1, N - 6, 9, 2, TRIM, thick=6)
    for x in (G0 - 1, G1 + 1, G0 - 4, G1 + 4):
        for z in (N - 1, N - 6): b.column(x, z, 1, H + 8, POST)
    # gate doors: heavy dark oak, opened inwards
    for z in range(N - 11, N - 6):
        for y in range(1, 11):
            b.set(G0 - 0, y, z, "minecraft:dark_oak_planks" if (y + z) % 5 else "minecraft:iron_block")
            b.set(G1, y, z, "minecraft:dark_oak_planks" if (y + z) % 5 else "minecraft:iron_block")
    # sign board
    b.box(CX - 25, H + 2, N, CX + 25, H + 9, N, "minecraft:white_concrete")
    for x in range(CX - 25, CX + 26): b.set(x, H + 2, N, RED); b.set(x, H + 9, N, RED)
    for y in range(H + 2, H + 10): b.set(CX - 25, y, N, RED); b.set(CX + 25, y, N, RED)
    b.text(CX - 22, H + 3, N + 1, "ARLONG PARK", "minecraft:blue_concrete", axis="x", step=1)
    b.pagoda_roof(CX, N - 3, 27, 5, H + 10, ROOF_ST, ROOF, layers=4, slab_block=ROOF_SLAB)
    for x in (CX - 24, CX + 24): b.set(x, H + 1, N + 1, "onepiece:paper_lantern[hanging=false]")
    # ---------------- courtyard pool, connected to the sea by a canal through the north wall
    PX, PZ, RX, RZ = CX, 60, 24, 17
    for x in range(PX - RX - 2, PX + RX + 3):
        for z in range(PZ - RZ - 2, PZ + RZ + 3):
            d = ((x - PX) / RX) ** 2 + ((z - PZ) / RZ) ** 2
            if d <= 1.0:
                for y in range(-7, 1): b.set(x, y, z, WATER)
                b.set(x, -8, z, "minecraft:sandstone")
            elif d <= 1.22:
                for y in range(-8, 1): b.set(x, y, z, "minecraft:stone_bricks")
                b.set(x, 1, z, wall("minecraft:stone_brick_wall") if (x + z) % 3 else "minecraft:chiseled_stone_bricks")
    # canal (8 wide) running north from the pool, under an arch in the wall, out past the edge
    for z in range(-6, PZ - RZ + 2):
        for x in range(CX - 4, CX + 5):
            for y in range(-7, 1): b.set(x, y, z, WATER)
            for y in range(1, 9 if 0 <= z <= 6 else 1): b.set(x, y, z, AIR)
            b.set(x, -8, z, "minecraft:sandstone")
        for x in (CX - 5, CX + 5):
            for y in range(-8, 2): b.set(x, y, z, "minecraft:stone_bricks")
    b.arch_x(CX - 5, CX + 5, 2, 7, 1, TRIM, thick=3)
    # the pair of tall iron sea gates (opened for Momoo the sea cow): hinge posts in the wall, leaves swung inwards
    for x in (CX - 5, CX + 5):
        for y in range(-2, 10): b.set(x, y, 5, "minecraft:iron_block")
    for side in (-1, 1):
        x = CX + side * 4
        for z in range(6, 11):
            for y in range(-2, 9):
                wl = "true" if y <= 0 else "false"
                edge = y in (-2, 8) or z == 10
                b.set(x, y, z, "minecraft:iron_block" if edge else f"minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged={wl}]")
        b.set(x, 9, 6, "minecraft:iron_chain[axis=y,waterlogged=false]")
    for x in range(CX - 5, CX + 6): b.set(x, 9, 4, "minecraft:iron_block")
    # bridge over the canal
    for z in range(16, 21):
        for x in range(CX - 6, CX + 7): b.set(x, 1, z, "minecraft:spruce_planks")
        b.set(CX - 6, 2, z, fence("spruce")); b.set(CX + 6, 2, z, fence("spruce"))
    # Arlong's big white lounge chair at the pool's edge, facing the gate, under a parasol, a side table next to it
    cz = PZ + RZ + 4
    b.box(CX - 3, 1, cz - 1, CX + 3, 1, cz + 3, "minecraft:smooth_quartz")
    for x in (CX - 1, CX, CX + 1):
        b.set(x, 2, cz, stairs("minecraft:smooth_quartz_stairs", "north"))        # foot rest
        b.set(x, 2, cz + 1, slab("minecraft:smooth_quartz_slab", "bottom"))       # seat
        b.set(x, 2, cz + 2, "minecraft:smooth_quartz"); b.set(x, 3, cz + 2, stairs("minecraft:smooth_quartz_stairs", "north"))  # reclined back
    for x in (CX - 2, CX + 2): b.set(x, 2, cz + 1, slab("minecraft:smooth_quartz_slab", "top")); b.set(x, 2, cz + 2, "minecraft:smooth_quartz")
    b.table_set(CX + 4, 2, cz + 1, "birch")
    b.column(CX - 4, cz + 2, 2, 6, fence("birch"))
    b.disk(CX - 4, 7, cz + 2, 3, "minecraft:white_wool")
    for i in range(0, 360, 30):
        a = math.radians(i); b.set(round(CX - 4 + 3 * math.cos(a)), 7, round(cz + 2 + 3 * math.sin(a)), "minecraft:light_blue_wool")
    # ---------------- main hall + the great tower at the back (north)
    MX0, MX1, MZ0, MZ1 = CX - 22, CX + 22, 10, 30
    # left and right wings of the main hall (2 floors), leaving the canal clear
    chinese_hall(b, MX0, MZ0, CX - 8, MZ1, 1, 5, floors=2)
    chinese_hall(b, CX + 8, MZ0, MX1, MZ1, 1, 5, floors=2)
    # covered bridge across the canal between the wings, 2nd floor
    for x in range(CX - 7, CX + 8):
        for z in range(MZ0 + 6, MZ0 + 13):
            b.set(x, 7, z, "minecraft:spruce_planks")
        b.set(x, 8, MZ0 + 6, fence("spruce")); b.set(x, 8, MZ0 + 12, fence("spruce"))
    # the tower: 4 storeys of shrinking floors with flared roofs, standing on the bridge's north side
    TX, TZ = CX, 18
    levels = [(9, 7, 13, 6), (8, 7, 20, 6), (7, 6, 27, 6), (7, 6, 34, 6), (6, 5, 41, 6), (5, 4, 48, 7)]  # half-w, half-d, base y, height
    for i, (hx, hz, y0, h) in enumerate(levels):
        b.box(TX - hx, y0, TZ - hz, TX + hx, y0, TZ + hz, "minecraft:spruce_planks")
        b.walls(TX - hx, y0 + 1, TZ - hz, TX + hx, y0 + h, TZ + hz, WALL)
        b.box(TX - hx + 1, y0 + 1, TZ - hz + 1, TX + hx - 1, y0 + h, TZ + hz - 1, AIR)
        for (px, pz) in ((TX - hx, TZ - hz), (TX + hx, TZ - hz), (TX - hx, TZ + hz), (TX + hx, TZ + hz)):
            b.column(px, pz, y0 + 1, y0 + h, POST)
        for x in range(TX - hx + 2, TX + hx - 1, 2):
            b.set(x, y0 + 3, TZ - hz, pane_of("minecraft:glass_pane")); b.set(x, y0 + 3, TZ + hz, pane_of("minecraft:glass_pane"))
        for z in range(TZ - hz + 2, TZ + hz - 1, 2):
            b.set(TX - hx, y0 + 3, z, pane_of("minecraft:glass_pane")); b.set(TX + hx, y0 + 3, z, pane_of("minecraft:glass_pane"))
        for x in range(TX - hx, TX + hx + 1): b.set(x, y0 + h, TZ - hz, TRIM); b.set(x, y0 + h, TZ + hz, TRIM)
        for z in range(TZ - hz, TZ + hz + 1): b.set(TX - hx, y0 + h, z, TRIM); b.set(TX + hx, y0 + h, z, TRIM)
        # flared eave around this level
        b.pagoda_roof(TX, TZ, hx + 3, hz + 3, y0 + h + 1, ROOF_ST, ROOF, layers=2, slab_block=ROOF_SLAB)
        b.box(TX - hx + 1, y0 + h + 1, TZ - hz + 1, TX + hx - 1, y0 + h + 2, TZ + hz - 1, AIR) if i < len(levels) - 1 else None
        # ladder up through every level
        for y in range(y0 + 1, (levels[i + 1][2] if i + 1 < len(levels) else y0 + h) + 1):
            b.set(TX + hx - 1, y, TZ, ladder("west"))
    # tower crown
    top = levels[-1][2] + levels[-1][3] + 1
    t = b.pagoda_roof(TX, TZ, 8, 7, top, ROOF_ST, ROOF, layers=6, slab_block=ROOF_SLAB)
    for y in range(t, t + 5): b.set(TX, y, TZ, "minecraft:gold_block" if y == t + 4 else fence("mangrove"))
    b.flag(TX, t + 5, TZ, h=8, colors=("minecraft:black_wool", "minecraft:light_blue_wool"))
    # base of the tower bridges down to the courtyard (stairs from the bridge)
    b.stairs_up(CX - 4, 1, MZ1 + 7, 6, "minecraft:stone_brick_stairs", "north", w=9)  # spans the canal, resting on its walls
    # ---------------- interiors
    # Arlong's map room at the top: Nami's charts everywhere
    ry = levels[-1][2]
    for x in range(TX - 4, TX + 4):
        b.set(x, ry + 1, TZ - 3, "minecraft:cartography_table" if x % 2 else "minecraft:bookshelf")
    b.set(TX, ry + 1, TZ, "onepiece:navigators_desk[facing=south]")
    b.set(TX - 2, ry + 1, TZ + 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.set(TX + 2, ry + 1, TZ + 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.chest(TX - 3, ry + 1, TZ + 2, "pirate", "east")
    for x in range(TX - 3, TX + 4): b.set(x, ry + 3, TZ - hz if False else TZ - 3, "minecraft:white_banner[rotation=0]" if False else "minecraft:bookshelf")
    b.set(TX, ry + 6, TZ, "onepiece:paper_lantern[hanging=true]")
    # the wings: mess hall and bunks
    for x in range(MX0 + 3, CX - 9, 4):
        b.table_set(x, 2, MZ0 + 6, "spruce"); b.table_set(x, 2, MZ1 - 6, "spruce")
        b.set(x, 6, MZ0 + 10, "onepiece:paper_lantern[hanging=true]")
    for x in range(CX + 9, MX1 - 1, 3):
        bed("blue", x, 8, MZ0 + 1, b, "south"); bed("cyan", x, 8, MZ1 - 2, b, "south")
        b.set(x, 8, MZ0 + 3, BARREL)
    for x in range(CX + 10, MX1 - 1, 4): b.set(x, 2, MZ0 + 2, "onepiece:sake_barrel[axis=x]"); b.set(x, 3, MZ0 + 2, "onepiece:sake_barrel[axis=x]")
    for z in range(MZ0 + 4, MZ1 - 3, 3): b.set(MX1 - 1, 2, z, "minecraft:grindstone[face=floor,facing=west]" if z % 2 else "minecraft:smithing_table")
    # stairs inside the wings
    b.stairs_up(MX0 + 2, 2, MZ1 - 2, 5, "minecraft:spruce_stairs", "east")
    b.stairs_up(MX1 - 2, 2, MZ1 - 2, 5, "minecraft:spruce_stairs", "west")
    # ---------------- side barracks along the east and west walls
    for (x0, x1) in ((6, 20), (N - 20, N - 6)):
        chinese_hall(b, x0, 40, x1, 84, 1, 6, floors=1, roof_layers=4)
        for z in range(42, 83, 3):
            bed("light_blue", x0 + 1, 2, z, b, "east") if x0 < CX else bed("light_blue", x1 - 2, 2, z, b, "east")
        b.set((x0 + x1) // 2, 6, 50, "onepiece:paper_lantern[hanging=true]"); b.set((x0 + x1) // 2, 6, 74, "onepiece:paper_lantern[hanging=true]")
        for z in (60, 62):
            for y in (2, 3, 4): b.set(x1 if x0 < CX else x0, y, z, AIR)
    # ---------------- yard dressing: tents, weapon racks, barrels, lanterns on posts
    for (x, z) in ((28, 84), (76, 84), (28, 36), (76, 36)):
        b.column(x, z, 1, 5, POST); b.set(x, 6, z, "onepiece:paper_lantern[hanging=false]")
    for x in range(32, 74, 6):
        b.set(x, 1, 90, BARREL); b.set(x + 1, 1, 90, "minecraft:barrel[facing=north,open=false]"); b.set(x, 2, 90, "onepiece:rope_coil[facing=south]")
    for (x, z) in ((24, 94), (80, 94)):  # weapon racks
        for i in range(5): b.set(x + i, 1, z, fence("dark_oak")); b.set(x + i, 2, z, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    # palm trees and a beach strip outside the north wall toward the sea
    for x in range(0, N + 1):
        for z in range(-8, 0):
            if not (CX - 5 <= x <= CX + 5): b.set(x, 0, z, "minecraft:sand"); b.box(x, -4, z, x, -1, z, "minecraft:sandstone")
    for (x, z) in ((10, -4), (30, -5), (74, -4), (94, -5)): b.palm(x, 1, z, 8)
    for (x, z) in ((10, N + 4), (94, N + 4), (CX - 18, N + 3), (CX + 18, N + 3)):
        b.set(x, 0, z, "minecraft:grass_block[snowy=false]"); b.palm(x, 1, z, 7)
    # ---------------- people
    b.guards("fishman", ((CX - 10, PZ + RZ + 6), (CX + 10, PZ + RZ + 6), (CX, 34), (20, 60), (84, 60), (CX - 4, 92)))
    # ---------------- furnished rooms
    import interiors as I
    I.furnish(b, MX0 + 1, 2, MZ0 + 1, CX - 9, MZ1 - 1, 5, "dining", "sea")
    I.furnish(b, MX0 + 1, 8, MZ0 + 1, CX - 9, MZ1 - 1, 5, "captain", "sea")
    I.furnish(b, CX + 9, 2, MZ0 + 1, MX1 - 1, MZ1 - 1, 5, "armory", "sea")
    I.furnish(b, CX + 9, 8, MZ0 + 1, MX1 - 1, MZ1 - 1, 5, "barracks", "sea")
    for (kind, (hx, hz, y0, h)) in zip(("tavern", "barracks", "treasure", "bedroom", "library", "study"), levels):
        I.furnish(b, TX - hx + 1, y0 + 1, TZ - hz + 1, TX + hx - 1, TZ + hz - 1, h, kind, "sea")
    for (x0, x1) in ((6, 20), (N - 20, N - 6)):
        I.furnish(b, x0 + 1, 2, 41, x1 - 1, 83, 6, "barracks", "sea")
    return b, 0
