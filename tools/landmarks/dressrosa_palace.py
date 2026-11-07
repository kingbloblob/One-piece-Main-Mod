"""Dressrosa Royal Palace on the King's Plateau, under Doflamingo's Birdcage, built to match the show:
- the King's Plateau: a sheer-sided natural rock mesa rising high out of the middle of the town, its cliffs banded
  with strata and broken by ribs and buttresses, ivy spilling over the edge; a grand quartz stair climbs the south
  face to a garden courtyard with a fountain;
- the palace on top: a pink-and-white stucco block with three furnished floors (throne hall, banquet, royal rooms,
  Doflamingo's suite), four round corner towers and a tall central keep with cone roofs, flying the Donquixote
  Jolly Roger (a smiley face struck through with a slash) from the keep's spire;
- the flower town of Dressrosa all round: pastel stucco houses on stone plinths with shutters, flower boxes and
  orange tiled roofs, cafe awnings, sunflowers and fountains on mosaic streets;
- the Birdcage: Doflamingo's strings coming down from the sky in a tall dome over the whole town.
~112 x 112. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "dressrosa_palace"
TITLE = "Dressrosa Royal Palace"
CUTS = [28, 36]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
CX, CZ = 56, 50
STUCCO = "onepiece:dressrosa_stucco"
TILE = "onepiece:dressrosa_tiles"
TILE_ST = "onepiece:dressrosa_tile_stairs"
MOSAIC = "onepiece:dressrosa_mosaic"
PINK = "minecraft:pink_terracotta"
WHITE = "minecraft:white_terracotta"
STONE = "minecraft:stone_bricks"
PLAT = 24          # plateau top surface y: the King's Plateau towers over the town
P0, P1 = CX - 30, CX + 30   # plateau x extent
Q0, Q1 = CZ - 30, CZ + 28   # plateau z extent
FLAMINGO = dict(wood="dark_oak", rug="pink", rug2="magenta", bed="pink", light="minecraft:lantern", accent="minecraft:gold_block",
                banner="pink", candle="pink")
ROYAL = dict(wood="cherry", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:gold_block",
             banner="red", candle="yellow")


def cone(b, cx, cz, r, y, h, s, tip="minecraft:gold_block"):
    for k in range(h):
        rr = r * (1 - k / h) + 0.4
        b.cyl(cx, cz, rr, y + k, y + k, s, hollow=rr > 1.5)
    b.set(cx, y + h, cz, tip); b.set(cx, y + h + 1, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")


def round_tower(b, cx, cz, r, y0, y1, wall=WHITE, roof=TILE, roof_h=None, floors=()):
    b.cyl(cx, cz, r, y0, y1, wall, hollow=True)
    for f in floors: b.cyl(cx, cz, r - 1, f, f, "minecraft:spruce_planks")
    for y in range(y0 + 3, y1, 5):  # window slits (none on the north side: the ladder needs that wall solid behind it)
        for (dx, dz) in ((r, 0), (-r, 0), (0, r)):
            b.set(cx + dx, y, cz + dz, "minecraft:glass_pane"); b.set(cx + dx, y + 1, cz + dz, "minecraft:glass_pane")
    b.cyl(cx, cz, r + 1, y1, y1, PINK)
    for a in range(0, 360, 30):  # battlement ring
        t = math.radians(a); b.set(round(cx + (r + 1) * math.cos(t)), y1 + 1, round(cz + (r + 1) * math.sin(t)), PINK)
    cone(b, cx, cz, r + 1, y1 + 1, roof_h or int(r * 2.6), roof)
    for yy in range(y0, y1):  # ladder up the inside
        b.set(cx, yy, cz - r + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for f in floors: b.set(cx, f, cz - r + 1, "minecraft:ladder[facing=south,waterlogged=false]")


def town_house(b, x0, z0, w, d, floors, rnd):
    """A Dressrosa town house: pastel stucco on a stone plinth, sandstone quoins and string courses, framed
    windows with wooden shutters, sills and flower boxes, a door with a lamp, an orange tiled hip roof on brackets."""
    h = 4 * floors + 1
    wall = rnd.choice((STUCCO, STUCCO, "minecraft:white_concrete", "minecraft:yellow_terracotta", PINK))
    trim = "minecraft:white_terracotta" if wall in ("minecraft:yellow_terracotta", PINK) else "minecraft:smooth_sandstone"
    xa, xb, za, zb = x0, x0 + w - 1, z0, z0 + d - 1
    b.box(xa, 0, za, xb, 0, zb, "minecraft:spruce_planks")
    b.walls(xa, 1, za, xb, h, zb, wall)
    b.box(xa + 1, 1, za + 1, xb - 1, h, zb - 1, AIR)
    for x in range(xa, xb + 1):          # stone plinth, string courses and the cornice band
        for z in (za, zb):
            b.set(x, 1, z, STONE)
            for f in range(1, floors): b.set(x, 4 * f, z, trim)
            b.set(x, h, z, trim)
    for z in range(za, zb + 1):
        for x in (xa, xb):
            b.set(x, 1, z, STONE)
            for f in range(1, floors): b.set(x, 4 * f, z, trim)
            b.set(x, h, z, trim)
    for (cx, cz) in ((xa, za), (xb, za), (xa, zb), (xb, zb)): b.column(cx, cz, 2, h, trim)   # quoins
    mx = x0 + w // 2
    shut = "minecraft:spruce_trapdoor"
    for f in range(floors):
        y = 1 + f * 4
        if f: b.box(xa + 1, y - 1, za + 1, xb - 1, y - 1, zb - 1, "minecraft:spruce_planks")
        faces = [((x, zb), (0, 1), "south") for x in range(xa + 2, xb - 1, 3)] + [((x, za), (0, -1), "north") for x in range(xa + 2, xb - 1, 3)]
        faces += [((xb, z), (1, 0), "east") for z in range(za + 2, zb - 1, 3)] + [((xa, z), (-1, 0), "west") for z in range(za + 2, zb - 1, 3)]
        for ((wx, wz), (ox, oz), fs) in faces:
            if f == 0 and fs == "south" and abs(wx - mx) <= 1: continue
            for yy in (y + 1, y + 2): b.set(wx, yy, wz, "minecraft:glass_pane")
            sx, sz = wx + ox, wz + oz
            b.set(sx, y, sz, stairs("minecraft:smooth_sandstone_stairs", OPP[fs], "top") if f == 0 else f"onepiece:flower_box[facing={fs}]")
            ax, az = (1, 0) if fs in ("north", "south") else (0, 1)
            for sgn in (-1, 1):
                for yy in (y + 1, y + 2):
                    if b.get(sx + ax * sgn, yy, sz + az * sgn) in (None, AIR): b.set(sx + ax * sgn, yy, sz + az * sgn, trapdoor(shut, fs, "bottom", "true"))
        I.furnish(b, xa + 1, y, za + 1, xb - 1, zb - 1, 3, rnd.choice(("bedroom", "kitchen", "tavern", "dining", "study", "workshop")),
                  ROYAL, seed=rnd.randint(0, 9999))
        if floors > 1 and f < floors - 1: b.set(xa + 1, y, za + 1, AIR); [b.set(xa + 1, y + k, za + 1, "minecraft:ladder[facing=east,waterlogged=false]") for k in range(4)]
    b.set(mx, 1, zb, door("minecraft:spruce_door", "south", "lower")); b.set(mx, 2, zb, door("minecraft:spruce_door", "south", "upper"))
    b.set(mx, 3, zb, trim)
    b.set(mx + 1, 3, zb + 1, "onepiece:wall_lamp[facing=south]")
    b.hip_roof(xa - 1, za - 1, xb + 1, zb + 1, h + 1, TILE_ST, TILE)
    for x in range(xa - 1, xb + 2, 2):   # brackets under the eaves
        for (z, fs) in ((za - 1, "south"), (zb + 1, "north")):
            if b.get(x, h, z) in (None, AIR): b.set(x, h, z, stairs("minecraft:spruce_stairs", fs, "top"))
    for z in range(za + 1, zb + 1, 2):
        for (x, fs) in ((xa - 1, "east"), (xb + 1, "west")):
            if b.get(x, h, z) in (None, AIR): b.set(x, h, z, stairs("minecraft:spruce_stairs", fs, "top"))
    if rnd.random() < 0.5:  # cafe awning in bright stripes over the shop front
        col = rnd.choice(("red", "yellow", "orange", "lime"))
        for x in range(xa, xb + 1):
            b.set(x, 4, zb + 1, f"minecraft:{col}_wool" if x % 2 else "minecraft:white_wool")
    else:                   # a little awning of slabs over the door
        for x in (mx - 1, mx, mx + 1): b.set(x, 4, zb + 1, slab("minecraft:spruce_slab", "top"))


def build():
    rnd = random.Random(7)
    b = B()
    # ---------------- ground: flower town
    for x in range(N):
        for z in range(N):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            b.set(x, 0, z, "minecraft:grass_block")
    # streets in a grid of mosaic and tiles
    for x in range(N):
        for z in range(N):
            if x % 22 in (0, 1, 2) or z % 22 in (0, 1, 2) or abs(x - CX) <= 3: b.set(x, 0, z, MOSAIC if (x + z) % 3 else "onepiece:dressrosa_tiles")
    taken = set()
    def free(x0, z0, w, d):
        for x in range(x0 - 1, x0 + w + 1):
            for z in range(z0 - 1, z0 + d + 1):
                if (x, z) in taken: return False
                if P0 - 5 <= x <= P1 + 5 and Q0 - 5 <= z <= Q1 + PLAT + 2: return False
                if x % 22 in (0, 1, 2) or z % 22 in (0, 1, 2) or abs(x - CX) <= 3: return False
        return True
    for bx in range(0, N, 22):
        for bz in range(0, N, 22):
            for (ox, oz) in ((4, 4), (12, 4), (4, 12), (12, 12)):
                w, d = rnd.randint(6, 8), rnd.randint(6, 8)
                x0, z0 = bx + ox, bz + oz
                if x0 + w >= N - 1 or z0 + d >= N - 1 or not free(x0, z0, w, d): continue
                for x in range(x0 - 1, x0 + w + 1):
                    for z in range(z0 - 1, z0 + d + 1): taken.add((x, z))
                town_house(b, x0, z0, w, d, rnd.choice((1, 2, 2, 3)), rnd)
    # flower beds, sunflowers, fountains in the free gaps
    for x in range(1, N - 1):
        for z in range(1, N - 1):
            if b.get(x, 0, z) == "minecraft:grass_block" and b.get(x, 1, z) is None and (x, z) not in taken and not (P0 - 5 <= x <= P1 + 5 and Q0 - 5 <= z <= Q1 + PLAT + 2):
                r = rnd.random()
                if r < 0.10: b.set(x, 1, z, rnd.choice(("minecraft:poppy", "minecraft:allium", "minecraft:pink_tulip", "minecraft:oxeye_daisy", "minecraft:cornflower")))
                elif r < 0.13: b.set(x, 1, z, "minecraft:sunflower[half=lower]"); b.set(x, 2, z, "minecraft:sunflower[half=upper]")
    for (fx, fz) in ((11, 99), (99, 11), (11, 11), (99, 99)):
        if b.get(fx, 1, fz) is None:
            b.cyl(fx, fz, 2.5, 0, 1, "minecraft:quartz_bricks"); b.cyl(fx, fz, 1.6, 1, 1, WATER)
            b.set(fx, 2, fz, "minecraft:quartz_pillar[axis=y]"); b.set(fx, 3, fz, "minecraft:water[level=0]") if False else b.set(fx, 3, fz, "minecraft:sea_lantern")
    # ---------------- the King's Plateau: a sheer-sided natural rock mesa in the middle of the town, its cliffs
    # banded with strata and broken by ribs and buttresses that step out toward the foot
    def rock(x, y, z):
        hsh = (x * 73856093 ^ y * 19349663 ^ z * 83492791) % 100
        band = (y + (x * 3 + z * 5) // 23) % 7
        if y <= 2: return "minecraft:mossy_cobblestone" if hsh < 25 else ("minecraft:cobblestone" if hsh < 60 else "minecraft:andesite")
        if band == 0: return "minecraft:tuff" if hsh < 70 else "minecraft:andesite"
        if band == 4: return "minecraft:andesite" if hsh < 75 else "minecraft:stone"
        return "minecraft:stone" if hsh < 72 else ("minecraft:andesite" if hsh < 90 else "minecraft:cobblestone")
    for x in range(P0, P1 + 1):
        for z in range(Q0, Q1 + 1):
            edge = min(x - P0, P1 - x, z - Q0, Q1 - z)
            for y in range(0, PLAT + 1):
                b.set(x, y, z, rock(x, y, z) if edge <= 1 else "minecraft:stone")
    def ribs(cells, out):
        """cells: the face cells in order along one side; out: outward (dx, dz). Ribs step out toward the foot."""
        n = len(cells)
        for i, (x, z) in enumerate(cells):
            if min(i, n - 1 - i) < 3: continue
            if abs(x - CX) <= 7 and out == (0, 1): continue          # leave the grand stair clear
            dep = 1.1 + 1.0 * math.sin(i * 0.47 + x * 0.05 + z * 0.11) + 0.9 * math.sin(i * 1.31 + 2.0)
            dep = max(0, min(3, int(round(dep))))
            for k in range(1, dep + 1):
                top = PLAT - 3 - (k - 1) * 6 - int(2 * abs(math.sin(i * 0.33 + k)))
                for y in range(0, top + 1): b.set(x + out[0] * k, y, z + out[1] * k, rock(x + out[0] * k, y, z + out[1] * k))
                b.set(x + out[0] * k, top + 1, z + out[1] * k, "minecraft:moss_block" if (i + k) % 3 else "minecraft:grass_block")
    ribs([(x, Q0) for x in range(P0, P1 + 1)], (0, -1))
    ribs([(x, Q1) for x in range(P0, P1 + 1)], (0, 1))
    ribs([(P0, z) for z in range(Q0, Q1 + 1)], (-1, 0))
    ribs([(P1, z) for z in range(Q0, Q1 + 1)], (1, 0))
    for x in range(P0, P1 + 1):  # balustrade around the top
        for z in (Q0, Q1):
            b.set(x, PLAT + 1, z, "minecraft:quartz_slab[type=bottom,waterlogged=false]" if x % 3 else "minecraft:quartz_pillar[axis=y]")
    for z in range(Q0, Q1 + 1):
        for x in (P0, P1):
            b.set(x, PLAT + 1, z, "minecraft:quartz_slab[type=bottom,waterlogged=false]" if z % 3 else "minecraft:quartz_pillar[axis=y]")
    # ivy and flowers spilling over the plateau walls
    for i in range(300):
        side = rnd.randint(0, 3)
        if side == 0: x, z, f = rnd.randint(P0, P1), Q0 - 1, "north"
        elif side == 1: x, z, f = rnd.randint(P0, P1), Q1 + 1, "south"
        elif side == 2: x, z, f = P0 - 1, rnd.randint(Q0, Q1), "west"
        else: x, z, f = P1 + 1, rnd.randint(Q0, Q1), "east"
        y = rnd.randint(PLAT - 8, PLAT)
        vs = {"north": "south", "south": "north", "west": "east", "east": "west"}[f]
        for k in range(rnd.randint(2, 6)):
            if b.get(x, y - k, z) is None: b.set(x, y - k, z, f"minecraft:vine[{','.join(d + '=' + ('true' if d == vs else 'false') for d in ('east', 'north', 'south', 'up', 'west'))}]")
    # grand stair from the town up the south face, between quartz parapets with lamp posts
    sz0 = Q1 + 1
    for i in range(PLAT):
        z = sz0 + PLAT - 1 - i
        for x in range(CX - 4, CX + 5):
            for y in range(0, i + 1): b.set(x, y, z, STONE)
            b.set(x, i + 1, z, stairs("minecraft:quartz_stairs", "north"))
        for x in (CX - 5, CX + 5):
            for y in range(0, i + 2): b.set(x, y, z, "minecraft:quartz_bricks")
            if i % 5 == 0: b.set(x, i + 2, z, "minecraft:quartz_pillar[axis=y]"); b.set(x, i + 3, z, lantern())
    for x in range(CX - 4, CX + 5): b.set(x, PLAT + 1, Q1, AIR)
    # ---------------- courtyard garden with the fountain
    for x in range(P0 + 1, P1):
        for z in range(Q0 + 1, Q1):
            b.set(x, PLAT, z, "minecraft:grass_block")
    for x in range(P0 + 1, P1):
        for z in range(CZ + 10, Q1):
            if abs(x - CX) <= 2: b.set(x, PLAT, z, MOSAIC)
            elif (x - CX) % 6 == 0 and z % 3 == 0: b.set(x, PLAT + 1, z, "minecraft:rose_bush[half=lower]"); b.set(x, PLAT + 2, z, "minecraft:rose_bush[half=upper]")
            elif abs(x - CX) in (4, 5): b.set(x, PLAT + 1, z, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    for z in range(CZ + 11, Q1):
        for x in range(P0 + 1, P1):
            if abs(x - CX) > 8 and (z - CZ) % 5 == 0 and x % 5 == 0:
                b.set(x, PLAT + 1, z, "minecraft:oak_log[axis=y]"); b.set(x, PLAT + 2, z, "minecraft:oak_log[axis=y]")
                b.sphere(x, PLAT + 4, z, 2, "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    FX, FZ = CX, CZ + 19
    b.cyl(FX, FZ, 4.5, PLAT + 1, PLAT + 1, "minecraft:quartz_bricks"); b.cyl(FX, FZ, 3.6, PLAT + 1, PLAT + 1, WATER)
    b.cyl(FX, FZ, 1.5, PLAT + 1, PLAT + 3, "minecraft:quartz_pillar[axis=y]")
    b.cyl(FX, FZ, 2.5, PLAT + 4, PLAT + 4, "minecraft:quartz_slab[type=bottom,waterlogged=false]"); b.set(FX, PLAT + 5, FZ, "minecraft:sea_lantern")
    for x in range(CX - 2, CX + 3): b.set(x, PLAT, FZ + 5, MOSAIC); b.set(x, PLAT, FZ - 5, MOSAIC)
    # ---------------- palace block: three floors
    X0, X1, Z0, Z1 = CX - 22, CX + 22, CZ - 22, CZ + 8
    F1, F2, F3, ROOFY = PLAT + 1, PLAT + 9, PLAT + 17, PLAT + 25
    b.box(X0, PLAT, Z0, X1, PLAT, Z1, "minecraft:polished_diorite")
    b.walls(X0, F1, Z0, X1, ROOFY, Z1, STUCCO)
    b.box(X0 + 1, F1, Z0 + 1, X1 - 1, ROOFY, Z1 - 1, AIR)
    for fy in (F2 - 1, F3 - 1, ROOFY):
        b.box(X0 + 1, fy, Z0 + 1, X1 - 1, fy, Z1 - 1, "minecraft:dark_oak_planks" if fy != ROOFY else STUCCO)
    for x in range(X0, X1 + 1, 4):  # pilasters and tall arched windows
        for z in (Z0, Z1):
            b.column(x, z, F1, ROOFY, WHITE)
    for fy in (F1, F2, F3):
        for x in range(X0 + 2, X1 - 1, 4):
            for z in (Z0, Z1):
                for k in range(1, 5): b.set(x, fy + k, z, "minecraft:pink_stained_glass_pane" if k == 4 else "minecraft:glass_pane")
        for z in range(Z0 + 2, Z1 - 1, 4):
            for x in (X0, X1):
                for k in range(1, 5): b.set(x, fy + k, z, "minecraft:pink_stained_glass_pane" if k == 4 else "minecraft:glass_pane")
        for x in range(X0, X1 + 1):  # string course between floors
            for z in (Z0 - 1, Z1 + 1): b.set(x, fy - 1, z, "minecraft:quartz_slab[type=top,waterlogged=false]") if fy != F1 else None
    for x in range(X0 - 1, X1 + 2):  # cornice and balustrade on the roof
        for z in (Z0 - 1, Z1 + 1):
            b.set(x, ROOFY, z, "minecraft:quartz_bricks"); b.set(x, ROOFY + 1, z, wall("minecraft:diorite_wall") if x % 2 else "minecraft:quartz_pillar[axis=y]")
    for z in range(Z0 - 1, Z1 + 2):
        for x in (X0 - 1, X1 + 1):
            b.set(x, ROOFY, z, "minecraft:quartz_bricks"); b.set(x, ROOFY + 1, z, wall("minecraft:diorite_wall") if z % 2 else "minecraft:quartz_pillar[axis=y]")
    b.hip_roof(X0 + 3, Z0 + 3, X1 - 3, Z1 - 3, ROOFY + 1, TILE_ST, TILE)
    # main entrance: portico with columns and a big doorway
    for x in (CX - 6, CX - 3, CX + 3, CX + 6):
        b.column(x, Z1 + 3, F1, F1 + 8, "minecraft:quartz_pillar[axis=y]")
    b.box(CX - 7, F1 + 9, Z1 + 1, CX + 7, F1 + 9, Z1 + 4, "minecraft:quartz_bricks")
    for x in range(CX - 7, CX + 8): b.set(x, F1 + 10, Z1 + 4, stairs("minecraft:quartz_stairs", "south"))
    b.set(CX, F1 + 10, Z1 + 1, "onepiece:kingdom_flag") if False else None
    for x in range(CX - 2, CX + 3):
        for y in range(F1, F1 + 5): b.set(x, y, Z1, AIR)
    # stairs between floors (east end) and a keep-out box for the subdivided floors
    SX = X1 - 6
    for (fy, ny) in ((F1, F2), (F2, F3)):
        for i in range(ny - fy):
            for x in (SX, SX + 1, SX + 2): b.set(x, fy + i, Z0 + 2 + i, stairs("minecraft:dark_oak_stairs", "south"))
            for x in (SX, SX + 1, SX + 2): b.set(x, ny - 1, Z0 + 2 + i, AIR) if i < ny - fy - 1 else None
        for x in (SX, SX + 1, SX + 2):
            for i in range(ny - fy + 1):
                for k in range(1, 4):
                    if fy + i + k < ny + 3 and b.get(x, fy + i + k, Z0 + 2 + i) not in (None, AIR) and not b.get(x, fy + i + k, Z0 + 2 + i).startswith("minecraft:dark_oak_stairs"): b.set(x, fy + i + k, Z0 + 2 + i, AIR)
    KEEP = ((SX - 1, Z0 + 1, SX + 3, Z0 + 12),)
    # floor 1: throne hall in the middle, banquet hall west, kitchen and guard room east
    TX0, TX1 = CX - 9, CX + 9
    for z in range(Z0 + 1, Z1):
        for y in range(F1, F2 - 1):
            for x in (TX0 - 1, TX1 + 1): b.set(x, y, z, STUCCO)
    for y in (F1, F1 + 1, F1 + 2):
        for x in (TX0 - 1, TX1 + 1): b.set(x, y, Z1 - 4, AIR); b.set(x, y, Z1 - 5, AIR)
    for x in range(TX0, TX1 + 1):
        for z in range(Z0 + 1, Z1):
            b.set(x, F1 - 1, z, "minecraft:polished_diorite" if (x + z) % 2 else "minecraft:pink_glazed_terracotta[facing=north]")
    for z in range(Z0 + 3, Z1):  # red carpet to the throne
        for x in range(CX - 1, CX + 2): b.set(x, F1, z, "minecraft:red_carpet" if x == CX else "minecraft:yellow_carpet")
    for x in (TX0 + 2, TX1 - 2):
        for z in range(Z0 + 4, Z1 - 1, 5): b.round_column(x, z, 1, F1, F2 - 2, "minecraft:quartz_pillar[axis=y]") if False else b.column(x, z, F1, F2 - 2, "minecraft:quartz_pillar[axis=y]")
    b.box(CX - 3, F1, Z0 + 1, CX + 3, F1, Z0 + 3, "minecraft:gold_block")
    b.set(CX, F1 + 1, Z0 + 2, stairs("minecraft:red_nether_brick_stairs", "north"))
    b.set(CX - 1, F1 + 1, Z0 + 2, "minecraft:gold_block"); b.set(CX + 1, F1 + 1, Z0 + 2, "minecraft:gold_block")
    b.set(CX, F1 + 2, Z0 + 1, "minecraft:gold_block"); b.set(CX, F1 + 3, Z0 + 1, "minecraft:gold_block")
    for x in range(CX - 4, CX + 5): b.set(x, F1 + 5, Z0 + 1, "minecraft:pink_wool" if x % 2 else "minecraft:magenta_wool")  # feather drapes
    r = I.furnish(b, TX0, F1, Z0 + 1, TX1, Z1 - 1, F2 - F1 - 1, "throne", ROYAL)
    r.chandelier(CX, Z0 + 10, 2, 2); r.chandelier(CX, Z1 - 6, 2, 2)
    I.furnish(b, X0 + 1, F1, Z0 + 1, TX0 - 2, Z1 - 1, F2 - F1 - 1, "banquet", ROYAL)
    I.furnish(b, TX1 + 2, F1, Z0 + 13, X1 - 1, Z1 - 1, F2 - F1 - 1, "kitchen", ROYAL)
    for x in range(TX1 + 2, X1):
        for y in range(F1, F2 - 1): b.set(x, y, Z0 + 12, STUCCO) if not (KEEP[0][0] <= x <= KEEP[0][2]) else None
    I.furnish(b, TX1 + 2, F1, Z0 + 1, SX - 2, Z0 + 11, F2 - F1 - 1, "armory", ROYAL)
    # floor 2: royal rooms off a corridor; floor 3: Doflamingo's suite and the treasury
    I.subdivide(b, X0 + 1, F2, Z0 + 1, X1 - 1, Z1 - 1, F3 - F2 - 1, STUCCO,
                ("bedroom", "library", "bath", "study", "bedroom", "workshop", "dining", "bedroom"), ROYAL, cell=11, keepout=KEEP, seed=4)
    for x in range(X0 + 1, X1):
        for y in range(F3, ROOFY): b.set(x, y, CZ - 8, STUCCO) if not (KEEP[0][0] <= x <= KEEP[0][2]) else None
    for y in (F3, F3 + 1, F3 + 2): b.set(CX, y, CZ - 8, AIR); b.set(CX + 1, y, CZ - 8, AIR)
    r = I.furnish(b, X0 + 1, F3, CZ - 7, X1 - 1, Z1 - 1, ROOFY - F3, "throne", FLAMINGO)
    r.chandelier(CX - 10, CZ, 2, 2); r.chandelier(CX + 10, CZ, 2, 2)
    b.set(CX, F3, CZ + 4, "minecraft:pink_wool"); b.set(CX - 1, F3, CZ + 4, "minecraft:pink_wool"); b.set(CX + 1, F3, CZ + 4, "minecraft:pink_wool")
    I.furnish(b, X0 + 1, F3, Z0 + 1, CX - 1, CZ - 9, ROOFY - F3, "bedroom", FLAMINGO)
    I.furnish(b, CX + 2, F3, Z0 + 1, SX - 2, CZ - 9, ROOFY - F3, "treasure", FLAMINGO)
    # ---------------- corner towers and the central keep
    for (tx, tz) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        round_tower(b, tx, tz, 4, F1, ROOFY + 10, floors=(F2 - 1, F3 - 1, ROOFY))
        for fy in (F1, F2, F3):  # doorway from the palace into each tower
            dx = 3 if tx == X0 else -3; dz = 3 if tz == Z0 else -3
            for k in (0, 1, 2): b.set(tx + dx, fy + k, tz + dz // 3 * 0 + (2 if tz == Z0 else -2), AIR)
    KX, KZ = CX, CZ - 8
    round_tower(b, KX, KZ, 6, ROOFY, ROOFY + 26, wall=PINK, floors=(ROOFY, ROOFY + 8, ROOFY + 17))
    # the way up into the keep: a ladder from the third floor (the hall north of Doflamingo's suite) on a stucco pier
    # with quartz edges, up through a hatch in the ceiling into the keep's ground room and on up the keep's own ladder
    for y in range(F3, ROOFY):
        b.set(KX, y, KZ - 6, STUCCO)
        for sx in (-1, 1): b.set(KX + sx, y, KZ - 6, "minecraft:quartz_pillar[axis=y]")
    for y in range(F3, ROOFY + 1): b.set(KX, y, KZ - 5, "minecraft:ladder[facing=south,waterlogged=false]")
    I.furnish(b, KX - 4, ROOFY + 1, KZ - 4, KX + 4, KZ + 4, 6, "armory", FLAMINGO, seed=5)
    I.furnish(b, KX - 4, ROOFY + 9, KZ - 4, KX + 4, KZ + 4, 7, "study", FLAMINGO)
    I.furnish(b, KX - 4, ROOFY + 18, KZ - 4, KX + 4, KZ + 4, 7, "treasure", FLAMINGO)
    # the Donquixote Jolly Roger on a pole from the keep's spire: a smiley face struck through with a slash,
    # two blocks thick so it reads from both sides
    tip = ROOFY + 27 + int(6 * 2.6)
    for y in range(tip + 1, tip + 14): b.set(KX, y, KZ, "minecraft:dark_oak_fence")
    FW, FH = 13, 11
    for c in range(FW):
        for r in range(FH):
            dx, dy = c - 6, r - 5
            ring = 4.5 <= math.hypot(dx, dy) <= 5.5
            eye = c in (4, 8) and r in (3, 4)
            smile = (r == 6 and c in (3, 9)) or (r == 7 and 4 <= c <= 8)
            slash = r == round(c * (FH - 1) / (FW - 1))
            fg = ring or eye or smile or slash
            for zz in (KZ, KZ + 1):
                b.set(KX + 1 + c, tip + 13 - r, zz, "minecraft:black_wool" if fg else "minecraft:pink_wool")
    # ---------------- the Birdcage: Doflamingo's strings come down from the sky in a great dome over the whole
    # town, like the bars of a birdcage (convex: steep at the foot, curving in to meet overhead)
    AY, R = 110, 50
    def put(c):
        x, y, z = c
        if 0 <= x < N and 0 <= z < N and y >= 1 and b.get(x, y, z) is None: b.set(x, y, z, "minecraft:white_stained_glass_pane")
    for k in range(24):
        t = 2 * math.pi * k / 24
        prev = None
        for st in range(0, 1601):
            ph = (math.pi / 2) * st / 1600
            r = R * math.sin(ph)
            c = (round(CX + r * math.cos(t)), round(AY * math.cos(ph)), round(CZ + r * math.sin(t)))
            if prev is not None and c != prev:
                x, y, z = prev
                while (x, y, z) != c:   # step one axis at a time so the string is one unbroken line
                    if x != c[0]: x += 1 if c[0] > x else -1
                    elif z != c[2]: z += 1 if c[2] > z else -1
                    else: y += 1 if c[1] > y else -1
                    put((x, y, z))
            elif prev is None: put(c)
            prev = c
    # rugs laid over the stair wells would hang in the air: take them up
    for (x, y, z), blk in list(b.blocks.items()):
        if "carpet" in blk and b.get(x, y - 1, z) in (None, AIR): b.set(x, y, z, AIR)
    # ---------------- people and loot
    b.npc(CX, F3, CZ + 2, "doflamingo", True)
    b.chest(CX + 6, F3, Z0 + 2, "legendary", "south"); b.chest(KX + 3, ROOFY + 18, KZ, "legendary", "west")
    b.chest(X0 + 2, F1, Z1 - 2, "treasure", "east"); b.chest(TX1 + 3, F1, Z0 + 2, "treasure", "south")
    b.guards("donquixote", ((CX - 2, Z1 + 6), (CX + 2, Z1 + 6), (CX - 6, Z0 + 8), (CX + 6, Z0 + 8)), y=F1)
    b.guards("gladiator", ((CX - 8, CZ + 20), (CX + 8, CZ + 20), (CX - 3, Q1 - 2)), y=PLAT + 1)
    b.guards("donquixote", ((CX - 12, CZ), (CX + 12, CZ)), y=F3)
    return b, 0
