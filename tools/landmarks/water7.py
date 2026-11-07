"""Water 7: the stepped canal city rising to the Great Fountain, with Galley-La Company's Dock 1 and headquarters
on the east shore. The real city is kilometres wide, so this is its heart at full scale: ~230 x 210, fountain ~60 tall.
Ground (street level of the outer ring) = y 0, canals sit at y -4..0."""
import math, random
from canvas import *

SID = "galley_la_dock"
TITLE = "Water 7 and the Galley-La docks"
CUTS = []
TILER = dict(terrain="beard_thin")

STONE = "onepiece:canal_bricks"
STONE_ST = "onepiece:canal_brick_stairs"
STONE_SL = "onepiece:canal_brick_slab"
STONE_W = "onepiece:canal_brick_wall"
COBBLE = "onepiece:water7_cobbles"
COBBLE_ST = "onepiece:water7_cobble_stairs"
COBBLE_W = "onepiece:water7_cobble_wall"
CX, CZ = 105, 105
TIERS = ((999, 0), (70, 9), (46, 18), (24, 27))     # outer radius -> street height
CANALS = ((71, 76), (47, 50))                        # ring canals (inner r, outer r)
# Water 7's houses are pale stucco and sandstone with brick-red stone trim; roofs mostly orange-red tile
WALLS = ("onepiece:dressrosa_stucco", "onepiece:dressrosa_stucco", "minecraft:white_terracotta", "minecraft:smooth_sandstone",
         "minecraft:calcite", "onepiece:canal_bricks")
ROOFS = (("onepiece:dressrosa_tile_stairs", "onepiece:dressrosa_tiles"), ("onepiece:dressrosa_tile_stairs", "onepiece:dressrosa_tiles"),
         ("onepiece:dressrosa_tile_stairs", "onepiece:dressrosa_tiles"), ("minecraft:brick_stairs", "minecraft:bricks"),
         ("minecraft:brick_stairs", "minecraft:bricks"), ("minecraft:prismarine_brick_stairs", "minecraft:prismarine_bricks"),
         ("minecraft:mangrove_stairs", "minecraft:mangrove_planks"))
TRIM = "onepiece:canal_bricks"          # corner quoins and floor bands of the houses
TRIM_ALT = "minecraft:smooth_quartz"    # ... on the brick houses


def street_y(r):
    y = 0
    for (rr, yy) in TIERS:
        if r <= rr: y = yy
    return y


def in_canal(r):
    return any(a <= r <= b for a, b in CANALS)


def w7_house(b, x0, z0, w, d, y, floors, rnd, door="south"):
    wallb = rnd.choice(WALLS); st, full = rnd.choice(ROOFS)
    h = floors * 4
    b.box(x0, y, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:spruce_planks")
    b.walls(x0, y + 1, z0, x0 + w - 1, y + h, z0 + d - 1, wallb)
    b.box(x0 + 1, y + 1, z0 + 1, x0 + w - 2, y + h, z0 + d - 2, AIR)
    trim = TRIM_ALT if wallb == TRIM else TRIM
    for f in range(1, floors):
        b.box(x0 + 1, y + f * 4, z0 + 1, x0 + w - 2, y + f * 4, z0 + d - 2, "minecraft:spruce_planks")
        for x in range(x0, x0 + w): b.set(x, y + f * 4, z0, trim); b.set(x, y + f * 4, z0 + d - 1, trim)
        for z in range(z0, z0 + d): b.set(x0, y + f * 4, z, trim); b.set(x0 + w - 1, y + f * 4, z, trim)
    for (cx_, cz_) in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)):
        b.column(cx_, cz_, y + 1, y + h, trim)
    for x in range(x0, x0 + w):  # heavier stone plinth at street level
        b.set(x, y + 1, z0, STONE if trim == TRIM else trim); b.set(x, y + 1, z0 + d - 1, STONE if trim == TRIM else trim)
    for f in range(floors):
        wy = y + f * 4 + 2
        for x in range(x0 + 2, x0 + w - 2, 2):
            for z in (z0, z0 + d - 1):
                b.set(x, wy, z, PANE); b.set(x, wy + 1, z, PANE)
                if f > 0: b.set(x, wy - 1, z + (1 if z == z0 + d - 1 else -1), "minecraft:flower_box".replace("flower_box", "spruce_trapdoor[facing=%s,half=top,open=false,powered=false,waterlogged=false]" % ("south" if z == z0 + d - 1 else "north")))
        for z in range(z0 + 2, z0 + d - 2, 2):
            for x in (x0, x0 + w - 1): b.set(x, wy, z, PANE); b.set(x, wy + 1, z, PANE)
    dx = x0 + w // 2
    dz = {"south": z0 + d - 1, "north": z0}[door] if door in ("south", "north") else z0 + d // 2
    if door in ("south", "north"):
        b.set(dx, y + 1, dz, door_block := f"minecraft:spruce_door[facing={door},half=lower,hinge=left,open=false,powered=false]")
        b.set(dx, y + 2, dz, door_block.replace("lower", "upper"))
    else:
        xx = x0 + w - 1 if door == "east" else x0
        b.set(xx, y + 1, dz, f"minecraft:spruce_door[facing={door},half=lower,hinge=left,open=false,powered=false]")
        b.set(xx, y + 2, dz, f"minecraft:spruce_door[facing={door},half=upper,hinge=left,open=false,powered=false]")
    # steep gable roof (Water 7 houses are tall and narrow)
    top = y + h + 1
    i = 0
    while z0 - 1 + i <= z0 + d - i:
        for x in range(x0 - 1, x0 + w + 1):
            b.set(x, top + i, z0 - 1 + i, stairs(st, "south")); b.set(x, top + i, z0 + d - i, stairs(st, "north"))
        for z in range(z0 + i, z0 + d - i):
            b.set(x0, top + i, z, wallb); b.set(x0 + w - 1, top + i, z, wallb)
        i += 1
    if d % 2:
        for x in range(x0 - 1, x0 + w + 1): b.set(x, top + i - 1, z0 + d // 2, full)
    # chimney: a solid brick stack that comes up through the roof slope at the back corner (the slope is at top+2
    # there) and stands one block above the ridge, capped with a campfire
    ridge = top + i - 1
    for yy in range(top + 2, ridge + 2): b.set(x0 + 1, yy, z0 + 1, "minecraft:bricks")
    b.set(x0 + 1, ridge + 2, z0 + 1, "minecraft:campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    # a little interior
    b.set(x0 + 1, y + 1, z0 + 1, BARREL); b.set(x0 + w - 2, y + 1, z0 + 1, "minecraft:crafting_table")
    b.set(x0 + w // 2, y + 3, z0 + d // 2, HANG)
    if floors > 1: bed(rnd.choice(("red", "blue", "yellow", "white")), x0 + 1, y + 5, z0 + 1, b, "south")
    import interiors as I
    for f in range(floors):
        kind = rnd.choice(("kitchen", "tavern", "workshop", "storage", "dining")) if f == 0 else rnd.choice(("bedroom", "bedroom", "study", "library"))
        I.furnish(b, x0 + 1, y + 1 + f * 4, z0 + 1, x0 + w - 2, z0 + d - 2, 3, kind, "shipyard", seed=rnd.randint(0, 99999))
    return top + i


def build():
    rnd = random.Random(77)
    b = B()
    R = 104
    # ---------------- terrain: stepped city mound, ring canals with water
    for x in range(CX - R - 2, CX + R + 3):
        for z in range(CZ - R - 2, CZ + R + 3):
            r = math.hypot(x - CX, z - CZ)
            dock = x >= 150 and 30 <= z <= 185
            if r > R and not dock: continue
            sy = street_y(r)
            b.box(x, -6, z, x, -1, z, STONE)
            if in_canal(r) and not dock:
                b.set(x, -6, z, "minecraft:sand")
                wy = street_y(r + 4) if r < 70 else 0  # water level of the canal = street below it
                wy = {71: 0, 47: 9}[[a for a, bb in CANALS if a <= r <= bb][0]]
                for y in range(-5, wy - 0): b.set(x, y, z, WATER)
                for y in range(min(0, wy), wy): b.set(x, y, z, WATER)
                continue
            for y in range(0, sy): b.set(x, y, z, STONE)
            b.set(x, sy, z, COBBLE if (x + z) % 9 else "minecraft:smooth_stone")
    # retaining walls with railings at the tier edges and canal edges
    for x in range(CX - R, CX + R + 1):
        for z in range(CZ - R, CZ + R + 1):
            r = math.hypot(x - CX, z - CZ)
            if r > R or in_canal(r): continue
            sy = street_y(r)
            nb = [math.hypot(x + dx - CX, z + dz - CZ) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            edge_lower = any(street_y(n) < sy or in_canal(n) for n in nb)
            if edge_lower and not (x >= 150 and 30 <= z <= 185):
                b.set(x, sy + 1, z, wall(STONE_W) if (x + z) % 4 else "onepiece:paper_lantern[hanging=false]" if (x * z) % 7 == 0 else wall(STONE_W))
            if r > R - 1.2 and not (x >= 150): b.set(x, 1, z, wall(COBBLE_W))
    # great stairways between tiers on the 4 compass streets, and bridges over the canals
    for ang in (0, 90, 180, 270):
        dx, dz = round(math.cos(math.radians(ang))), round(math.sin(math.radians(ang)))
        px, pz = -dz, dx
        for rr in range(8, R):
            r_here = rr
            x, z = CX + dx * rr, CZ + dz * rr
            sy = street_y(r_here)
            for k in range(-3, 4):
                bx, bz = x + px * k, z + pz * k
                if in_canal(r_here):
                    # an arched stone bridge at the height of the street on the inner side, so it meets the
                    # tier above and the stairs down beyond the canal
                    a0, a1 = [(a, bb) for a, bb in CANALS if a <= r_here <= bb][0]
                    deck = {71: 9, 47: 18}[a0]
                    b.set(bx, deck, bz, COBBLE if abs(k) < 3 else STONE)
                    if abs(k) == 3: b.set(bx, deck + 1, bz, wall(STONE_W) if rr % 2 else "onepiece:paper_lantern[hanging=false]" if rr == (a0 + a1) // 2 else wall(STONE_W))
                    if r_here in (a0, a1):
                        for y2 in range(-5, deck): b.set(bx, y2, bz, STONE)
                    elif r_here in (a0 + 1, a1 - 1):
                        b.set(bx, deck - 1, bz, stairs(STONE_ST, "east" if (rr == a0 + 1) == (dx + dz > 0) else "west", "top") if dz == 0 else
                              stairs(STONE_ST, "south" if (rr == a0 + 1) == (dx + dz > 0) else "north", "top"))
                    for y2 in range(deck + 1, deck + 4):
                        if abs(k) < 3: b.set(bx, y2, bz, AIR)
        # stairs down from each tier (outward)
        for (ro, top, bottom) in ((46, 18, 9), (24, 27, 18), (70, 9, 0)):
            if ro == 70: start = 77; down = 9
            elif ro == 46: start = 51; down = 9
            else: start = 25; down = 9
            for i in range(down):
                rr = start + i - (0 if ro != 70 else 0)
                for k in range(-3, 4):
                    bx, bz = CX + dx * rr + px * k, CZ + dz * rr + pz * k
                    face = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
                    yy = top - 1 - i
                    b.set(bx, yy + 0, bz, stairs(COBBLE_ST, face))
                    for y2 in range(yy + 1, yy + 5): b.set(bx, y2, bz, AIR)
                    for y2 in range(bottom, yy): b.set(bx, y2, bz, STONE)
    # ---------------- houses on each ring
    placed = []
    def free(x0, z0, w, d):
        for (a0, b0, a1, b1) in placed:
            if x0 - 2 <= a1 and a0 <= x0 + w + 1 and z0 - 2 <= b1 and b0 <= z0 + d + 1: return False
        return True
    for (r0, r1, floors) in ((80, 100, 3), (54, 66, 3), (30, 42, 2)):
        for ang in range(0, 360, 9):
            if any(abs(((ang - a + 180) % 360) - 180) < 8 for a in (0, 90, 180, 270)): continue
            rr = rnd.uniform(r0, r1)
            hx = CX + rr * math.cos(math.radians(ang)); hz = CZ + rr * math.sin(math.radians(ang))
            if hx > 140 and 25 <= hz <= 190 and r0 == 80: continue  # leave the docks
            w, d = rnd.choice(((7, 9), (8, 9), (7, 11), (9, 9)))
            x0, z0 = int(hx - w / 2), int(hz - d / 2)
            corners = [math.hypot(x - CX, z - CZ) for x in (x0, x0 + w - 1) for z in (z0, z0 + d - 1)]
            if any(street_y(c) != street_y(rr) or in_canal(c) or c > R - 2 for c in corners): continue
            if not free(x0, z0, w, d): continue
            placed.append((x0, z0, x0 + w - 1, z0 + d - 1))
            door = "south" if hz > CZ else "north"
            w7_house(b, x0, z0, w, d, street_y(rr), floors + rnd.randint(0, 1), rnd, door)
    # ---------------- the Great Fountain crowning the city: stacked basins on a stone column, and from the top
    # basin the great jet of water shooting high into the sky and falling back. (Water is held in basins; the
    # jet and the falling water are glass so they never flood the city.)
    TOP = 27
    JET = "minecraft:light_blue_stained_glass"
    FOAM = "minecraft:white_stained_glass"
    WHITE = "minecraft:smooth_quartz"

    def basin(r, y, depth=1, rim=2):
        """A round basin on y: stone floor, a rim `rim` high with a white cap and an overhanging lip, water inside."""
        b.cyl(CX, CZ, r, y, y, STONE)
        for yy in range(y + 1, y + 1 + rim): b.cyl(CX, CZ, r, yy, yy, STONE, hollow=True)
        b.cyl(CX, CZ, r, y + rim, y + rim, WHITE, hollow=True)
        b.cyl(CX, CZ, r - 1, y + 1, y + depth, WATER)
        for a in range(0, 360, 4):  # moulded lip under the rim
            t = math.radians(a); x, z = round(CX + (r + 1) * math.cos(t)), round(CZ + (r + 1) * math.sin(t))
            f = "west" if abs(math.cos(t)) > abs(math.sin(t)) and math.cos(t) > 0 else "east" if abs(math.cos(t)) > abs(math.sin(t)) else "north" if math.sin(t) > 0 else "south"
            if b.get(x, y + rim, z) in (None, AIR): b.set(x, y + rim, z, stairs(STONE_ST, f, "top"))
        return y + depth

    def spill(r0, y0, r1, y1, step):
        """Arcs of water pouring over a rim at r0, y0 and landing at r1, y1, every `step` degrees."""
        for a in range(0, 360, step):
            t = math.radians(a); last = None
            for i in range(41):
                u = i / 40
                r = r0 + (r1 - r0) * u; y = y0 - (y0 - y1) * u * u
                p = (round(CX + r * math.cos(t)), round(y), round(CZ + r * math.sin(t)))
                if last: b.line(last, p, FOAM if i < 4 else JET)
                last = p

    w0 = basin(17, TOP, depth=2, rim=3)                       # the great lower basin on the plaza
    b.cyl(CX, CZ, 4.5, TOP + 1, TOP + 15, STONE)                  # central column
    for y in (TOP + 6, TOP + 11): b.cyl(CX, CZ, 5.5, y, y, WHITE)  # white bands round it
    b.cyl(CX, CZ, 7, TOP + 14, TOP + 14, STONE); b.cyl(CX, CZ, 9, TOP + 15, TOP + 15, STONE)  # the bowl under the middle basin
    w1 = basin(10, TOP + 16, depth=1, rim=2)                  # middle basin
    b.cyl(CX, CZ, 2.6, TOP + 17, TOP + 27, WHITE)                 # upper stem
    b.cyl(CX, CZ, 4, TOP + 26, TOP + 26, STONE)
    w2 = basin(6, TOP + 27, depth=1, rim=2)                   # upper basin
    spill(10.5, TOP + 18, 14.5, w0, 20)                         # middle basin pours into the lower one
    spill(6.5, TOP + 29, 9, w1 + 1, 30)                         # upper basin pours into the middle one
    # the great jet: a column of water rising from the upper basin, bursting into a crown of spray at the top
    # and falling back all round in a widening veil into the middle basin
    JT = TOP + 69
    for y in range(w2 + 1, JT):
        b.cyl(CX, CZ, 2.0 if y < JT - 25 else 1.5, y, y, JET)
        if y % 4 == 0:
            for a in range(0, 360, 90):
                t = math.radians(a + y * 23); b.set(round(CX + 2 * math.cos(t)), y, round(CZ + 2 * math.sin(t)), FOAM)
    b.shape(lambda x, y, z: ((x - CX) / 4.6) ** 2 + ((y - JT) / 2.6) ** 2 + ((z - CZ) / 4.6) ** 2 <= 1.0,
            CX - 6, JT - 3, CZ - 6, CX + 6, JT + 3, CZ + 6, lambda x, y, z: FOAM if (x + y + z) % 3 else JET, interior=JET)
    YB = w1 + 1  # the veil lands in the middle basin

    def veil_r(y):
        u = max(0.0, min(1.0, (JT - y) / (JT - YB))) ** (1 / 1.3)
        return 4.0 + 4.6 * (1 - (1 - u) ** 3)

    def in_veil(x, y, z):
        """A continuous sheet of falling water one block thick, bridging the radius between this level and the next."""
        d = math.hypot(x - CX, z - CZ); r0, r1 = veil_r(y), veil_r(y + 1)
        return min(r0, r1) - 0.5 <= d <= max(r0, r1) + 0.5

    def veil_mat(x, y, z):  # white streaks of spray down the sheet, thicker near the crown
        a = math.degrees(math.atan2(z - CZ, x - CX)) % 24
        return FOAM if a < 3 or y > JT - 6 or (x * 7 + y * 3 + z * 5) % 11 == 0 else JET

    b.shape(in_veil, CX - 10, YB, CZ - 10, CX + 10, JT - 1, CZ + 10, veil_mat, interior=None)
    # top-tier plaza: Iceburg's statue spot, benches, lamps
    for a in range(0, 360, 30):
        t = math.radians(a); x, z = round(CX + 20 * math.cos(t)), round(CZ + 20 * math.sin(t))
        b.column(x, z, TOP + 1, TOP + 3, fence("dark_oak")); b.set(x, TOP + 4, z, LANTERN)
    # ---------------- Galley-La Company: Dock 1 (east shore)
    DX0, DX1, DZ0, DZ1 = 150, 228, 30, 185
    for x in range(DX0, DX1 + 1):
        for z in range(DZ0, DZ1 + 1):
            b.box(x, -6, z, x, -1, z, STONE); b.set(x, 0, z, COBBLE if (x // 2 + z // 2) % 5 else "minecraft:smooth_stone")
    # two dry docks (slipways) open to the sea at the east end, each with a ship being built; the southern one
    # starts east of the first tier's mound
    for (sz0, sz1, xs) in ((44, 72, 168), (118, 146, 176)):
        wx = xs + 35  # the dry dock runs to wx; a caisson gate at wx + 1 holds back the sea channel beyond it
        for x in range(xs, DX1 + 1):
            for z in range(sz0, sz1 + 1):
                for y in range(-5, 1): b.set(x, y, z, WATER if x > wx else AIR)
                b.set(x, -6, z, STONE)
                if x <= wx: b.set(x, -5, z, "minecraft:spruce_planks" if (z - sz0) % 4 else "minecraft:dark_oak_planks")
        for x in range(xs, DX1 + 1):
            for z in (sz0 - 1, sz1 + 1):
                b.set(x, 1, z, wall(STONE_W))
        for z in range(sz0 - 1, sz1 + 2): b.set(xs - 1, 1, z, wall(STONE_W))
        # ship hull frame on the slip: keel, ribs, part planked
        kz = (sz0 + sz1) // 2
        for x in range(xs + 4, xs + 32):
            b.set(x, -4, kz, "minecraft:stripped_dark_oak_log[axis=x]")
            f = (x - xs - 4) / 27
            hw = 10 * math.sin(math.pi * min(1, f * 1.15 + 0.08)) ** 0.6
            for y in range(-4, 6):
                t = (y + 4) / 9; w = int(round(hw * math.sin(t * math.pi / 2) ** 0.5))
                if x % 3 == 0:
                    b.set(x, y, kz - w, "minecraft:stripped_spruce_log[axis=y]"); b.set(x, y, kz + w, "minecraft:stripped_spruce_log[axis=y]")
                elif x < xs + 18 and y < 2:
                    b.set(x, y, kz - w, "minecraft:spruce_planks"); b.set(x, y, kz + w, "minecraft:spruce_planks")
        for x in range(xs + 3, xs + 34, 6):  # scaffolds
            for z in (sz0 + 1, sz1 - 1):
                for y in range(-4, 8): b.set(x, y, z, "minecraft:scaffolding[bottom=false,distance=0,waterlogged=false]")
        for z in range(sz0, sz1 + 1):  # the dock gate: timber caisson with log posts and an iron-banded top
            for y in range(-5, 1):
                b.set(wx + 1, y, z, "minecraft:stripped_dark_oak_log[axis=y]" if (z - sz0) % 4 == 0 else
                      "minecraft:iron_block" if y == 0 else "minecraft:dark_oak_planks")
        # gantry crane spanning the dock
        g0, g1, gm = xs + 8, xs + 28, xs + 18
        for z in (sz0 - 2, sz1 + 2):
            for x in (g0, g1):
                b.column(x, z, 1, 26, "minecraft:red_concrete")
        for x in (g0, g1):
            for z in range(sz0 - 2, sz1 + 3): b.set(x, 27, z, "minecraft:red_concrete")
        for z in range(sz0 - 2, sz1 + 3, 1):
            if z % 2: b.set(gm, 27, z, "minecraft:iron_block")
        for x in range(g0, g1 + 1): b.set(x, 27, kz, "minecraft:red_concrete")
        for y in range(10, 27): b.set(gm, y, kz, CHAIN)
        b.set(gm, 9, kz, "minecraft:anvil[facing=north]")
        b.set(xs + 10, 1, sz0 - 4, "onepiece:shipyard_crane[facing=east]"); b.set(xs + 26, 1, sz1 + 4, "onepiece:shipyard_crane[facing=east]")
    # the Dock 1 gate: Galley-La's docks are each entered through a towering gate with the dock's number on it.
    # It closes the yard between the slipways at the foot of the great east stairs, facing the city (west).
    GX0, GX1 = 191, 196
    for z0_, z1_ in ((94, 99), (111, 116)):  # the two gate towers, with orange tile roofs
        b.box(GX0, 1, z0_, GX1, 26, z1_, STONE)
        for y in (8, 18, 26): b.box(GX0 - 1, y, z0_ - 1, GX1 + 1, y, z1_ + 1, "minecraft:smooth_quartz")
        for y in range(10, 25, 7):
            for zz in range(z0_ + 1, z1_, 2): b.set(GX0, y, zz, AIR); b.set(GX0, y + 1, zz, AIR); b.set(GX0 + 1, y, zz, PANE); b.set(GX0 + 1, y + 1, zz, PANE)
        b.hip_roof(GX0 - 1, z0_ - 1, GX1 + 1, z1_ + 1, 27, "onepiece:dressrosa_tile_stairs", "onepiece:dressrosa_tiles", overhang=1)
    b.box(GX0, 1, 100, GX1, 24, 110, STONE)  # the gateway between them, arched opening
    for z in range(100, 111):
        top = 11 + round(math.sqrt(max(0.0, 5.5 ** 2 - (z - 105) ** 2)) * 0.7)
        for x in range(GX0, GX1 + 1):
            for y in range(1, top + 1): b.set(x, y, z, AIR)
        b.set(GX0, top + 1, z, "minecraft:smooth_quartz")  # white voussoirs round the arch
        for y in range(1, top + 1):  # the great door leaves, dark wood with iron bands, closed
            b.set(GX0 + 3, y, z, "minecraft:iron_block" if y in (4, 9) or z == 105 else "minecraft:dark_oak_planks")
    for z in range(100, 111, 2): b.set(GX0, 25, z, wall(STONE_W)); b.set(GX1, 25, z, wall(STONE_W))
    for zw in (101, 109):  # small wicket doors in the leaves, so people can walk through
        for y, half in ((1, "lower"), (2, "upper")):
            b.set(GX0 + 3, y, zw, f"minecraft:spruce_door[facing=west,half={half},hinge=left,open=false,powered=false]")
    def big(x, y0, z0_, ch, s_, scale, step):
        for r, bits in enumerate(FONT[ch]):
            for c, bit in enumerate(bits):
                if bit != "1": continue
                for sz in range(scale):
                    for sy in range(scale):
                        b.set(x, y0 + (4 - r) * scale + sy, z0_ + (c * scale + sz) * step, s_)
    big(GX0 + 2, 2, 102, "1", "minecraft:smooth_quartz", 2, 1)    # the dock's number on the door, read from the city
    big(GX0 + 4, 2, 108, "1", "minecraft:smooth_quartz", 2, -1)   # ... and from inside the yard
    b.box(GX0 - 1, 17, 97, GX0 - 1, 23, 113, "minecraft:dark_oak_planks")  # signboard over the arch
    b.text(GX0 - 2, 18, 98, "DOCK", "minecraft:smooth_quartz", axis="z", step=1)
    for (za, zb) in ((74, 93), (117, 117)):  # curtain walls from the towers to the slipways
        b.box(GX0 + 1, 1, za, GX0 + 3, 12, zb, STONE)
        for z in range(za, zb + 1, 2): b.set(GX0 + 1, 13, z, wall(STONE_W)); b.set(GX0 + 3, 13, z, wall(STONE_W))
    # timber yard inside the gate: Adam wood and logs stacked, workbenches
    for x in range(200, 226, 4):
        for z in (80, 86):
            for y in (1, 2): b.box(x, y, z, x + 2, y, z + 2, "minecraft:spruce_log[axis=x]" if y == 1 else "onepiece:adam_log[axis=x]")
    for x in range(200, 226, 6): b.set(x, 1, 112, "onepiece:shipwright_bench[facing=south]")
    # Galley-La headquarters (Iceburg's office): big white building with a red roof and the company name
    HX0, HX1, HZ0, HZ1 = 154, 182, 150, 180
    b.box(HX0, 0, HZ0, HX1, 0, HZ1, "minecraft:polished_andesite")
    for f in range(3):
        fy = f * 6
        b.walls(HX0, fy + 1, HZ0, HX1, fy + 6, HZ1, "minecraft:white_terracotta")
        b.box(HX0 + 1, fy + 1, HZ0 + 1, HX1 - 1, fy + 5, HZ1 - 1, AIR)
        b.box(HX0 + 1, fy + 6, HZ0 + 1, HX1 - 1, fy + 6, HZ1 - 1, "minecraft:spruce_planks")
        for x in range(HX0 + 2, HX1 - 1, 3):
            for z in (HZ0, HZ1): b.set(x, fy + 3, z, PANE); b.set(x, fy + 4, z, PANE)
        for z in range(HZ0 + 2, HZ1 - 1, 3):
            for x in (HX0, HX1): b.set(x, fy + 3, z, PANE); b.set(x, fy + 4, z, PANE)
        for x in range(HX0, HX1 + 1): b.set(x, fy + 6, HZ0, "minecraft:red_terracotta"); b.set(x, fy + 6, HZ1, "minecraft:red_terracotta")
        for z in range(HZ0, HZ1 + 1): b.set(HX0, fy + 6, z, "minecraft:red_terracotta"); b.set(HX1, fy + 6, z, "minecraft:red_terracotta")
        b.stairs_up(HX1 - 2, fy + 1, HZ0 + 2, 5, "minecraft:spruce_stairs", "south")
    b.hip_roof(HX0, HZ0, HX1, HZ1, 19, "onepiece:dressrosa_tile_stairs", "onepiece:dressrosa_tiles", overhang=1)
    for z in range(HZ0 + 12, HZ0 + 19):
        for y in (1, 2, 3): b.set(HX0, y, z, AIR)
    # the company sign over the west front (facing the city): a white board standing on the roof eave, framed in red,
    # with the name on two lines (GALLEY over LA) so every letter has the board behind it
    SB0, SB1 = HZ0 + 3, HZ1 - 3                       # white board z 153..177, y 20..32
    b.box(HX0 - 1, 20, SB0, HX0 - 1, 32, SB1, "minecraft:white_concrete")
    for y in range(19, 34): b.set(HX0 - 1, y, SB0 - 1, "minecraft:red_terracotta"); b.set(HX0 - 1, y, SB1 + 1, "minecraft:red_terracotta")
    for z in range(SB0 - 1, SB1 + 2): b.set(HX0 - 1, 33, z, "minecraft:red_terracotta")
    b.box(HX0, 21, SB0, HX0, 32, SB1, "minecraft:dark_oak_planks")  # timber back of the board, above the roof slope
    for (msg, y) in (("GALLEY", 27), ("LA", 21)):
        wdt = len(msg) * 4 - 1
        b.text(HX0 - 2, y, (SB0 + SB1) // 2 - wdt // 2, msg, "minecraft:red_concrete", axis="z", step=1)
    b.set(HX0 + 14, 13, HZ0 + 15, "onepiece:navigators_desk[facing=west]"); b.set(HX0 + 14, 13, HZ0 + 13, "minecraft:lectern[facing=west,has_book=false,powered=false]")
    b.chest(HX0 + 3, 1, HZ0 + 3, "easy", "south")
    for x in range(HX0 + 3, HX1 - 2, 4):
        b.table_set(x, 7, HZ0 + 8, "spruce"); b.table_set(x, 7, HZ1 - 8, "spruce")
    # mooring posts and small boats in the canals
    for ang in range(15, 360, 40):
        for rr, lvl in ((73.5, 0), (48.5, 9)):
            x, z = round(CX + rr * math.cos(math.radians(ang))), round(CZ + rr * math.sin(math.radians(ang)))
            for k in range(-1, 2):
                b.set(x + k, lvl, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
            b.set(x, lvl + 1, z, "onepiece:rope_coil[facing=north]")
    # shoreline: posts and ropes along the dock edge
    for z in range(DZ0, DZ1 + 1, 6):
        b.column(DX1, z, 1, 2, "minecraft:stripped_dark_oak_log[axis=y]")
    # ---------------- people
    b.npc(210, 1, 96, "franky")
    # ---------------- furnished Galley-La HQ: drafting hall, canteen, Iceburg's office
    import interiors as I
    for f, kind in enumerate(("workshop", "dining", "study")):
        I.furnish(b, HX0 + 1, f * 6 + 1, HZ0 + 1, HX1 - 1, HZ1 - 1, 5, kind, "shipyard")
    return b, 0
