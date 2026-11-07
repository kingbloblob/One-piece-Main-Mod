"""The Fish-Man District of Fish-Man Island: the poor, lawless quarter where the island's outcasts gathered, in its
own smaller air bubble sunk into the sea floor, fenced off from the rest of the island by a buttressed stone wall
and a gate. Crooked stacked houses of dark prismarine, coral and mud brick lean over winding alleys: timber-framed
storeys that shift and overhang on brackets, porthole windows and shuttered windows, steep prismarine roofs,
ladders up through the floors. The Fish-Man Karate dojo, the tavern where pirates drink, the hidden den of the New
Fish-Man Pirates with their weapons and the crates of Energy Steroids, a little market and the memorial to Queen
Otohime. ~100 x 100. Sea floor = y 0; the bubble is sunk so its top stays under the sea."""
import math, random
from canvas import *
import interiors as I

SID = "fishman_district"
TITLE = "Fish-Man District"
CUTS = [-10, 0]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

N = 100
C = 50
RX, RY, BASE = 44, 34, -22
FLOOR = -12
BUBBLE = "onepiece:bubble_glass"
CORAL = "onepiece:coral_bricks"
DARK = "minecraft:dark_prismarine"
SLUM = dict(wood="mangrove", rug="cyan", rug2="gray", bed="cyan", light="onepiece:bubble_lamp[hanging=true]", accent="minecraft:prismarine_bricks",
            banner="cyan", candle="cyan")
POST = "minecraft:mangrove_log[axis=y]"
BEAM = {"x": "minecraft:mangrove_log[axis=x]", "z": "minecraft:mangrove_log[axis=z]"}
WOOD_ST = "minecraft:mangrove_stairs"
MATS = (DARK, CORAL, "minecraft:prismarine_bricks", "minecraft:mossy_stone_bricks", "minecraft:mud_bricks")
ROOFS = (("minecraft:dark_prismarine_stairs", DARK), ("minecraft:prismarine_brick_stairs", "minecraft:prismarine_bricks"),
         ("minecraft:mud_brick_stairs", "minecraft:mud_bricks"))
SLABS = {DARK: "minecraft:dark_prismarine_slab", "minecraft:prismarine_bricks": "minecraft:prismarine_brick_slab", "minecraft:mud_bricks": "minecraft:mud_brick_slab"}
PANE = "minecraft:light_blue_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]"


def inside(x, y, z):
    return ((x - C) / RX) ** 2 + ((y - BASE) / RY) ** 2 + ((z - C) / RX) ** 2 < 1


def shutter(face):
    return f"minecraft:mangrove_trapdoor[facing={face},half=bottom,open=true,powered=false,waterlogged=false]"


def door_of(x0, z0, w, d):
    """The front door of a house on this plot: in the south wall, between two posts."""
    return x0 + w // 2 + (1 if (w // 2) % 4 == 0 else 0), z0 + d - 1


def stack_house(b, x0, z0, w, d, floors, rnd, kinds, flat=False, lean=(-1, 1, -1, 1), crowd=()):
    """A crooked tower of storeys: each one shifts by a block and overhangs the one below on brackets.
    lean = how far the upper storeys may shift (-x, +x, -z, +z): never toward a neighbour one block away.
    crowd = the cells other houses stand on (no junk is dumped in a lane that is only one block wide)."""
    y = FLOOR
    ox = oz = 0
    shells = []
    prev = None
    mx, fz = door_of(x0, z0, w, d)  # the front door (south face)
    for f in range(floors):
        if f:
            ox = max(lean[0], min(lean[1], ox + rnd.choice((-1, 0, 1))))
            oz = max(lean[2], min(lean[3], oz + rnd.choice((-1, 0, 0, 1))))
        mat = rnd.choice(MATS)
        bx0, bx1, bz0, bz1 = x0 + ox, x0 + w - 1 + ox, z0 + oz, z0 + d - 1 + oz
        b.box(bx0, y, bz0, bx1, y, bz1, "minecraft:mangrove_planks")
        b.walls(bx0, y + 1, bz0, bx1, y + 4, bz1, mat)
        b.box(bx0 + 1, y + 1, bz0 + 1, bx1 - 1, y + 4, bz1 - 1, AIR)
        # timber frame: corner posts, a post every 4 blocks, a beam ring at the ceiling
        xs = sorted(set(list(range(bx0, bx1 + 1, 4)) + [bx1])); zs = sorted(set(list(range(bz0, bz1 + 1, 4)) + [bz1]))
        for yy in range(y + 1, y + 4):
            for x in xs: b.set(x, yy, bz0, POST); b.set(x, yy, bz1, POST)
            for z in zs: b.set(bx0, yy, z, POST); b.set(bx1, yy, z, POST)
        for x in range(bx0, bx1 + 1): b.set(x, y + 4, bz0, BEAM["x"]); b.set(x, y + 4, bz1, BEAM["x"])
        for z in range(bz0, bz1 + 1): b.set(bx0, y + 4, z, BEAM["z"]); b.set(bx1, y + 4, z, BEAM["z"])
        # brackets under the overhang where this storey sticks out past the one below
        if prev:
            px0, px1, pz0, pz1 = prev
            for x in range(bx0, bx1 + 1):
                for z in range(bz0, bz1 + 1):
                    if (x in (bx0, bx1) or z in (bz0, bz1)) and not (px0 <= x <= px1 and pz0 <= z <= pz1):
                        face = "east" if x < px0 else "west" if x > px1 else "south" if z < pz0 else "north"
                        b.set(x, y - 1, z, stairs(WOOD_ST, face, "top"))
        # windows between the posts: portholes, or two panes with open shutters
        for (side, cells) in (("north", [(x, bz0) for x in range(bx0 + 2, bx1 - 1, 4)]), ("south", [(x, bz1) for x in range(bx0 + 2, bx1 - 1, 4)]),
                              ("west", [(bx0, z) for z in range(bz0 + 2, bz1 - 1, 4)]), ("east", [(bx1, z) for z in range(bz0 + 2, bz1 - 1, 4)])):
            dx, dz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[side]
            for (x, z) in cells:
                if rnd.random() < 0.45:
                    b.set(x, y + 2, z, f"onepiece:porthole[facing={side}]")
                else:
                    b.set(x, y + 2, z, PANE); b.set(x, y + 3, z, PANE)
                    for s in (-1, 1):
                        sx, sz = x + s * abs(dz) + dx, z + s * abs(dx) + dz
                        if f == 0 and side == "south" and sx == mx: continue  # never a shutter across the doorway
                        if b.get(sx, y + 2, sz) in (None, AIR):
                            b.set(sx, y + 2, sz, shutter(side)); b.set(sx, y + 3, sz, shutter(side))
                    if b.get(x + dx, y + 1, z + dz) in (None, AIR) and f: b.set(x + dx, y + 1, z + dz, stairs(WOOD_ST, OPP[side], "top"))  # sill
        shells.append((bx0, bx1, bz0, bz1, y))
        prev = (bx0, bx1, bz0, bz1)
        y += 5
    # attic floor and a steep gable roof with an overhang
    bx0, bx1, bz0, bz1 = prev
    st, full = rnd.choice(ROOFS)
    b.box(bx0, y, bz0, bx1, y, bz1, "minecraft:mangrove_planks")
    if flat:  # under the low edge of the bubble: a flat roof with a parapet of slabs and a rooftop shed of junk
        b.box(bx0 - 1, y, bz0 - 1, bx1 + 1, y, bz1 + 1, full)
        sl = slab(SLABS[full])
        for x in range(bx0 - 1, bx1 + 2): b.set(x, y + 1, bz0 - 1, sl); b.set(x, y + 1, bz1 + 1, sl)
        for z in range(bz0 - 1, bz1 + 2): b.set(bx0 - 1, y + 1, z, sl); b.set(bx1 + 1, y + 1, z, sl)
        b.set(bx0 + 1, y + 1, bz0 + 1, BARREL); b.set(bx1 - 1, y + 1, bz1 - 1, "minecraft:dried_kelp_block")
    else:
        b.gable_roof(bx0, bz0, bx1, bz1, y, st, full, gable_wall=rnd.choice(MATS), overhang=1)
    # a ladder up through every floor, on a post in the corner of the rooms
    lx, lz = x0 + 2, z0 + 2
    for yy in range(FLOOR + 1, y): b.set(lx, yy, lz, POST)
    for yy in range(FLOOR + 1, y - 4): b.set(lx + 1, yy, lz, ladder("east"))
    # the front door with a frame, an awning and junk outside
    for yy in (FLOOR + 1, FLOOR + 2): b.set(mx, yy, fz, AIR)
    b.set(mx, FLOOR + 3, fz, BEAM["x"])
    for x in range(mx - 1, mx + 2): b.set(x, FLOOR + 3, fz + 1, slab("minecraft:mangrove_slab", "top"))
    narrow = any((x, fz + 2) in crowd for x in range(x0 - 1, x0 + w + 1))  # the lane in front is a single block wide
    if b.get(mx + 2, FLOOR + 1, fz + 1) in (None, AIR) and not narrow: b.set(mx + 2, FLOOR + 1, fz + 1, BARREL)
    if b.get(mx - 2, FLOOR + 1, fz + 1) in (None, AIR) and rnd.random() < 0.6 and not narrow: b.set(mx - 2, FLOOR + 1, fz + 1, "minecraft:dried_kelp_block")
    for i, (sx0, sx1, sz0, sz1, sy) in enumerate(shells):
        I.furnish(b, sx0 + 1, sy + 1, sz0 + 1, sx1 - 1, sz1 - 1, 3, kinds[min(i, len(kinds) - 1)], SLUM, seed=rnd.randint(0, 99999))

    # then keep the way in and the climb open: furniture must not stand in the doorway or cap the ladder hole
    def clear(x, yy, z, keep_carpet=True):
        s = b.get(x, yy, z)
        if s in (None, AIR) or (keep_carpet and "carpet" in s): return
        if "_bed[" in s:  # take the whole bed, not half of it
            for (ddx, ddz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if "_bed[" in (b.get(x + ddx, yy, z + ddz) or ""): b.set(x + ddx, yy, z + ddz, AIR)
        b.set(x, yy, z, AIR)
        if b.get(x, yy + 1, z) not in (None, AIR) and any(t in b.get(x, yy + 1, z) for t in ("candle", "carpet", "pressure_plate", "pot", "lantern")):
            b.set(x, yy + 1, z, AIR)  # a candle or a cloth left standing on nothing
    for yy in range(FLOOR + 1, y - 4):  # the ladder itself, through every storey
        if "ladder" not in (b.get(lx + 1, yy, lz) or ""): b.set(lx + 1, yy, lz, ladder("east"))
    if floors > 1:
        for yy in (y - 4, y - 3): clear(lx + 1, yy, lz, keep_carpet=False)  # the way out at the top of the ladder
    for (sx0, sx1, sz0, sz1, sy) in shells:  # a free cell beside the ladder on every storey, to get on and off it
        for yy in (sy + 1, sy + 2): clear(lx + 1, yy, lz + 1)
    for yy in (FLOOR + 1, FLOOR + 2):  # the doorway: open on both sides
        clear(mx, yy, fz + 1, keep_carpet=False); clear(mx, yy, fz - 1)
    return y


SHACK_MATS = ("minecraft:mangrove_planks", "minecraft:mud_bricks", DARK, "minecraft:prismarine_bricks", "minecraft:mossy_stone_bricks", CORAL)


def shack(b, x0, z0, w, d, face, rnd):
    """A one-room lean-to of scavenged planks, mud brick and coral under a patched slab roof: the poorest homes,
    squeezed in wherever the bubble is too low for a house. The doorway faces `face`."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    b.box(x0, FLOOR, z0, x1, FLOOR, z1, "minecraft:mangrove_planks")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                corner = x in (x0, x1) and z in (z0, z1)
                m = POST if corner else rnd.choice(SHACK_MATS)
                for y in range(FLOOR + 1, FLOOR + 4): b.set(x, y, z, m if corner or rnd.random() < 0.85 else rnd.choice(SHACK_MATS))
            else:
                for y in range(FLOOR + 1, FLOOR + 4): b.set(x, y, z, AIR)
    for x in range(x0 - 1, x1 + 2):  # the patched roof, overhanging by a block all round
        for z in range(z0 - 1, z1 + 2):
            b.set(x, FLOOR + 4, z, slab(rnd.choice(("minecraft:mangrove_slab", "minecraft:mangrove_slab", "minecraft:dark_prismarine_slab", "minecraft:mud_brick_slab"))))
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    dx, dz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[face]
    door_x = x0 if dx < 0 else x1 if dx > 0 else cx
    door_z = z0 if dz < 0 else z1 if dz > 0 else cz
    for y in (FLOOR + 1, FLOOR + 2): b.set(door_x, y, door_z, AIR)
    front = (door_x + dx, door_z + dz)
    # a porthole in a side wall, a lamp from the roof, a barrel and a bed roll of carpet
    sx, sz = (cx, z0) if dx else (x0, cz)
    if (sx, sz) != (door_x, door_z): b.set(sx, FLOOR + 2, sz, f"onepiece:porthole[facing={'north' if dx else 'west'}]")
    b.set(cx, FLOOR + 3, cz, "onepiece:bubble_lamp[hanging=true]")
    bx, bz = (x0 + 1 if dx >= 0 else x1 - 1), (z0 + 1 if dz >= 0 else z1 - 1)  # the back corner, away from the door
    b.set(bx, FLOOR + 1, bz, BARREL)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if b.get(x, FLOOR + 1, z) in (None, AIR) and (x, z) != (door_x - dx, door_z - dz) and abs(x - bx) + abs(z - bz) == 1:
                b.set(x, FLOOR + 1, z, "minecraft:gray_carpet")
    return front


def build():
    rnd = random.Random(521)
    b = B()
    # ---------------- the bubble: shell of bubble glass, air inside, floor of rock
    for x in range(C - RX - 1, C + RX + 2):
        for z in range(C - RX - 1, C + RX + 2):
            for y in range(BASE, BASE + RY + 1):
                if inside(x, y, z):
                    if not (inside(x + 1, y, z) and inside(x - 1, y, z) and inside(x, y + 1, z) and inside(x, y, z + 1) and inside(x, y, z - 1)):
                        b.set(x, y, z, BUBBLE)
                    elif y <= FLOOR:
                        b.set(x, y, z, "minecraft:stone" if y < FLOOR else "minecraft:packed_mud")
                    else:
                        b.set(x, y, z, AIR)
    # rock and sea floor round the outside of the bubble
    for x in range(N):
        for z in range(N):
            if math.hypot(x - C, z - C) > RX - 2:
                for y in range(BASE, 1):
                    if not inside(x, y, z) and b.get(x, y, z) is None: b.set(x, y, z, "minecraft:sand" if y == 0 else "minecraft:sandstone")
                if rnd.random() < 0.05: b.set(x, 1, z, rnd.choice(("minecraft:seagrass", "minecraft:tube_coral[waterlogged=true]", "minecraft:brain_coral[waterlogged=true]")))
    # ---------------- the dividing wall and the gate (south): buttressed, with a walk along the top
    WZ = C + 30
    for x in range(C - RX, C + RX + 1):
        for y in range(FLOOR + 1, FLOOR + 9):
            if inside(x, y, WZ) and inside(x, y, WZ + 1): b.set(x, y, WZ, DARK if y < FLOOR + 8 else ("minecraft:prismarine_wall" if x % 2 else DARK))
        if x % 6 == 0 and inside(x, FLOOR + 7, WZ - 1) and inside(x, FLOOR + 7, WZ + 2):  # buttresses on both faces
            for y in range(FLOOR + 1, FLOOR + 7):
                b.set(x, y, WZ - 1, "minecraft:prismarine_bricks" if y < FLOOR + 6 else stairs("minecraft:prismarine_brick_stairs", "south"))
                b.set(x, y, WZ + 1, "minecraft:prismarine_bricks" if y < FLOOR + 6 else stairs("minecraft:prismarine_brick_stairs", "north"))
    for x in range(C - 3, C + 4):
        for y in range(FLOOR + 1, FLOOR + 6): b.set(x, y, WZ, AIR)
    for (gx, sgn) in ((C - 4, -1), (C + 4, 1)):  # gate towers of coral, two blocks thick, with lamps
        for y in range(FLOOR + 1, FLOOR + 11):
            for dz in (-1, 0, 1):
                b.set(gx, y, WZ + dz, CORAL); b.set(gx + sgn, y, WZ + dz, CORAL)
        b.set(gx, FLOOR + 11, WZ, "onepiece:bubble_lamp[hanging=false]")
    b.box(C - 4, FLOOR + 6, WZ, C + 4, FLOOR + 7, WZ, CORAL)
    for x in range(C - 3, C + 4):
        b.set(x, FLOOR + 5, WZ, stairs("onepiece:coral_brick_stairs", "east" if x < C else "west", "top") if abs(x - C) == 3 else AIR)
        b.set(x, FLOOR + 8, WZ, slab("minecraft:prismarine_brick_slab"))
        b.set(x, FLOOR + 5, WZ - 1, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]" if abs(x - C) < 3 else AIR)  # the raised portcullis
    # ---------------- alleys and houses
    alley = set()
    for (pts) in (((C, WZ), (C, C + 10), (C - 20, C), (C - 30, C - 14)), ((C, C + 10), (C + 22, C + 4), (C + 26, C - 18)), ((C - 20, C), (C - 6, C - 24), (C + 26, C - 18))):
        for (p0, p1) in zip(pts, pts[1:]):
            n = int(math.hypot(p1[0] - p0[0], p1[1] - p0[1])) + 1
            for i in range(n + 1):
                x = p0[0] + (p1[0] - p0[0]) * i / n; z = p0[1] + (p1[1] - p0[1]) * i / n
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        b.set(round(x + dx), FLOOR, round(z + dz), "minecraft:mud_bricks"); alley.add((round(x + dx), round(z + dz)))
    DX0, DZ0 = C - 12, C - 4          # the dojo
    MX, MZ = C + 6, C + 2             # the market and the memorial
    HX0, HZ0 = C - 8, C - 40          # the den (under the rock)
    GUARDS = ((C, C + 20), (C - 20, C + 2), (C + 22, C - 6), (C - 6, C - 26), (MX, MZ + 6), (C, WZ - 3))  # fish-man thugs in the lanes
    reserved = [(DX0 - 2, DZ0 - 2, DX0 + 16, DZ0 + 12), (MX - 7, MZ - 6, MX + 7, MZ + 6), (HX0 + 15, HZ0 + 3, HX0 + 21, HZ0 + 9), (C - 6, WZ - 4, C + 6, WZ + 1)]
    reserved += [(gx - 1, gz - 1, gx + 1, gz + 1) for (gx, gz) in GUARDS]  # keep the thugs' spots in the open
    kinds = (("kitchen", "bedroom", "storage"), ("tavern", "storage", "bedroom"), ("bedroom", "bedroom", "storage"), ("storage", "bedroom", "bedroom"),
             ("dining", "bedroom", "bedroom"), ("workshop", "storage", "bedroom"))
    spots = ((C - 34, C - 4), (C - 26, C + 8), (C - 14, C + 12), (C + 8, C + 14), (C + 18, C + 14), (C + 30, C + 2), (C + 30, C - 10),
             (C + 12, C - 12), (C - 4, C - 12), (C - 18, C - 16), (C - 30, C - 24), (C + 6, C - 30), (C - 14, C - 32), (C + 20, C - 28),
             (C - 28, C + 18), (C + 28, C + 18), (C - 4, C + 20), (C + 14, C + 22), (C - 16, C + 22), (C + 2, C - 22), (C - 24, C - 10),
             (C + 18, C - 4), (C + 32, C - 24), (C - 36, C + 6))
    # then pack the rest of the quarter, the plots nearest the middle first: houses front straight onto the alleys and
    # crowd each other with only a one-block lane between them (a body wide), the way the slum is drawn
    pr = random.Random(5210)
    extra = sorted(((x, z) for x in range(C - 40, C + 36) for z in range(C - 40, C + 26)), key=lambda p: math.hypot(p[0] + 4 - C, p[1] + 3 - C))
    taken = set()
    plots = []
    for n, (x0, z0) in enumerate(list(spots) + extra):
        if len(plots) >= 26: break
        w, d = (rnd.randint(6, 8), rnd.randint(6, 7)) if n < len(spots) else (pr.randint(6, 8), pr.randint(6, 7))
        foot = [(x, z) for x in range(x0, x0 + w) for z in range(z0, z0 + d)]
        cells = [(x, z) for x in range(x0 - 1, x0 + w + 1) for z in range(z0 - 1, z0 + d + 1)]  # the plot and its lane
        if any(c in alley for c in foot): continue
        if any(rx0 <= x <= rx1 and rz0 <= z <= rz1 for (x, z) in cells for (rx0, rz0, rx1, rz1) in reserved): continue
        if any(c in taken for c in foot): continue
        if any(b.get(x, FLOOR + 1, z) not in (None, AIR) for (x, z) in cells): continue
        floors, flat = 0, False
        for fl in (3, 2, 1):  # as many storeys as fit under the bubble: eaves at the corners, the ridge at the gable ends
            eave, ridge = FLOOR + 5 * fl + 1, FLOOR + 5 * fl + (d + 3) // 2
            if (all(inside(x, eave + 2, z) for x in (x0 - 2, x0 + w + 1) for z in (z0 - 2, z0 + d + 1)) and
                    all(inside(x, ridge + 2, z) for x in (x0 - 2, x0 + w + 1) for z in (z0 + d // 2 - 1, z0 + (d - 1) // 2 + 1))):
                floors = fl; break
        if not floors and all(inside(x, FLOOR + 7, z) for x in (x0 - 2, x0 + w + 1) for z in (z0 - 2, z0 + d + 1)): floors, flat = 1, True
        if not floors: continue
        plots.append((x0, z0, w, d, floors, flat))
        taken.update(cells)
    crowd = {}
    for i, (x0, z0, w, d, fl, flat) in enumerate(plots):
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + d): crowd[(x, z)] = i

    def near(i, xs, zs):
        return any(crowd.get((x, z), i) != i for x in xs for z in zs)
    for k, (x0, z0, w, d, fl, flat) in enumerate(plots):
        lean = (0 if near(k, range(x0 - 2, x0), range(z0 - 2, z0 + d + 2)) else -1, 0 if near(k, range(x0 + w, x0 + w + 2), range(z0 - 2, z0 + d + 2)) else 1,
                0 if near(k, range(x0 - 2, x0 + w + 2), range(z0 - 2, z0)) else -1, 0 if near(k, range(x0 - 2, x0 + w + 2), range(z0 + d, z0 + d + 2)) else 1)
        stack_house(b, x0, z0, w, d, fl, rnd, kinds[k % len(kinds)], flat=flat, lean=lean, crowd=crowd)
    # lean-to shacks in the gaps that are left, out to where the bubble comes down too low even for a flat-roofed house
    sr = random.Random(5211)
    nshack = 0
    fronts = [(mx, fz + 1) for (mx, fz) in (door_of(x0, z0, w, d) for (x0, z0, w, d, fl, flat) in plots)]
    for (x0, z0) in sorted(((x, z) for x in range(C - 42, C + 40) for z in range(C - 42, C + 28)), key=lambda p: math.hypot(p[0] + 2 - C, p[1] + 2 - C)):
        if nshack >= 18: break
        w, d = sr.randint(4, 6), sr.randint(4, 5)
        foot = [(x, z) for x in range(x0, x0 + w) for z in range(z0, z0 + d)]
        cells = [(x, z) for x in range(x0 - 1, x0 + w + 1) for z in range(z0 - 1, z0 + d + 1)]
        if any(c in alley or c in taken for c in foot): continue
        if any(rx0 <= x <= rx1 and rz0 <= z <= rz1 for (x, z) in cells for (rx0, rz0, rx1, rz1) in reserved): continue
        if any(b.get(x, FLOOR + 1, z) not in (None, AIR) or b.get(x, FLOOR, z) in (None, AIR) for (x, z) in cells): continue
        if not all(inside(x, FLOOR + 6, z) for x in (x0 - 2, x0 + w + 1) for z in (z0 - 2, z0 + d + 1)): continue  # roof clear of the glass
        ddx, ddz = C - (x0 + w / 2), C - (z0 + d / 2)
        face = ("east" if ddx > 0 else "west") if abs(ddx) > abs(ddz) else ("south" if ddz > 0 else "north")
        fronts.append(shack(b, x0, z0, w, d, face, sr)); nshack += 1
        taken.update(cells)
    for (x, z) in fronts:  # a shutter hung on a neighbour's wall must not stand in front of anyone's door
        for y in (FLOOR + 1, FLOOR + 2, FLOOR + 3):
            if y < FLOOR + 3 or "trapdoor" in (b.get(x, y, z) or ""): b.set(x, y, z, AIR)
    # ---------------- the Fish-Man Karate dojo: framed coral hall under a broad hipped roof with deep eaves
    b.box(DX0, FLOOR, DZ0, DX0 + 14, FLOOR, DZ0 + 9, "minecraft:mangrove_planks")
    b.walls(DX0, FLOOR + 1, DZ0, DX0 + 14, FLOOR + 5, DZ0 + 9, CORAL); b.box(DX0 + 1, FLOOR + 1, DZ0 + 1, DX0 + 13, FLOOR + 5, DZ0 + 8, AIR)
    for y in range(FLOOR + 1, FLOOR + 5):
        for x in range(DX0, DX0 + 15, 3): b.set(x, y, DZ0, POST); b.set(x, y, DZ0 + 9, POST)
        for z in (DZ0, DZ0 + 3, DZ0 + 6, DZ0 + 9): b.set(DX0, y, z, POST); b.set(DX0 + 14, y, z, POST)
    for x in range(DX0, DX0 + 15): b.set(x, FLOOR + 5, DZ0, BEAM["x"]); b.set(x, FLOOR + 5, DZ0 + 9, BEAM["x"])
    for x in range(DX0 + 1, DX0 + 14, 3):  # high slit windows between the posts
        for zz in (DZ0, DZ0 + 9):
            if x + 1 != DX0 + 7: b.set(x + 1, FLOOR + 3, zz, PANE); b.set(x + 1, FLOOR + 4, zz, PANE)
    b.hip_roof(DX0, DZ0, DX0 + 14, DZ0 + 9, FLOOR + 6, "minecraft:prismarine_brick_stairs", "minecraft:prismarine_bricks", trim="minecraft:dark_prismarine_slab[type=top,waterlogged=false]")
    for x in range(DX0 - 1, DX0 + 16, 2):  # eave brackets
        b.set(x, FLOOR + 5, DZ0 - 1, stairs(WOOD_ST, "south", "top")); b.set(x, FLOOR + 5, DZ0 + 10, stairs(WOOD_ST, "north", "top"))
    for y in (FLOOR + 1, FLOOR + 2, FLOOR + 3): b.set(DX0 + 7, y, DZ0 + 9, AIR)
    b.set(DX0 + 6, FLOOR + 3, DZ0 + 9, POST); b.set(DX0 + 8, FLOOR + 3, DZ0 + 9, POST)
    for x in range(DX0 + 5, DX0 + 10): b.set(x, FLOOR + 4, DZ0 + 10, slab("minecraft:mangrove_slab", "top"))
    I.furnish(b, DX0 + 1, FLOOR + 1, DZ0 + 1, DX0 + 13, DZ0 + 8, 4, "barracks", SLUM, seed=3)
    for x in range(DX0 + 3, DX0 + 12, 3): b.set(x, FLOOR + 1, DZ0 + 4, "onepiece:training_post[facing=north]")
    # ---------------- the New Fish-Man Pirates' den (sunk into the rock, north)
    b.box(HX0, FLOOR - 6, HZ0, HX0 + 18, FLOOR - 1, HZ0 + 12, AIR)
    b.walls(HX0 - 1, FLOOR - 7, HZ0 - 1, HX0 + 19, FLOOR - 1, HZ0 + 13, DARK); b.box(HX0, FLOOR - 7, HZ0, HX0 + 18, FLOOR - 7, HZ0 + 12, DARK)
    b.box(HX0, FLOOR - 1, HZ0, HX0 + 18, FLOOR - 1, HZ0 + 12, DARK)  # a real ceiling, so the den's lamps have something to hang from
    I.subdivide(b, HX0, FLOOR - 6, HZ0, HX0 + 18, HZ0 + 12, 5, DARK, ("armory", "lab", "barracks", "treasure"), SLUM, cell=9, corridor=2, seed=9)
    for y in range(FLOOR - 6, FLOOR + 1): b.set(HX0 + 18, y, HZ0 + 6, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(HX0 + 18, FLOOR, HZ0 + 6, "minecraft:mangrove_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    # ---------------- market and Otohime's memorial
    for i, (dx, dz) in enumerate(((-4, -3), (4, -3), (-4, 3), (4, 3))):
        x, z = MX + dx, MZ + dz
        for yy in (FLOOR + 1, FLOOR + 2): b.set(x - 1, yy, z, "minecraft:mangrove_fence"); b.set(x + 1, yy, z, "minecraft:mangrove_fence")
        b.set(x, FLOOR + 1, z, ("minecraft:barrel[facing=up,open=false]", "minecraft:sea_pickle[pickles=4,waterlogged=false]", "minecraft:melon", "minecraft:dried_kelp_block")[i])
        for xx in (x - 1, x, x + 1): b.set(xx, FLOOR + 3, z, ("minecraft:cyan_wool", "minecraft:light_blue_wool")[i % 2])
    b.cyl(MX, MZ, 1.6, FLOOR + 1, FLOOR + 1, "onepiece:pearl_block"); b.column(MX, MZ, FLOOR + 2, FLOOR + 6, "minecraft:quartz_pillar[axis=y]")
    b.set(MX, FLOOR + 7, MZ, "onepiece:pearl_block"); b.set(MX, FLOOR + 8, MZ, "minecraft:pink_tulip")
    for s in range(0, 360, 30):  # bubble lamps hung from the bubble roof
        t = math.radians(s)
        x, z = round(C + 26 * math.cos(t)), round(C + 26 * math.sin(t))
        if b.get(x, FLOOR + 10, z) in (None, AIR) and b.get(x, FLOOR + 11, z) in (None, AIR):
            b.set(x, FLOOR + 10, z, "onepiece:bubble_lamp[hanging=true]"); b.set(x, FLOOR + 11, z, "minecraft:chain[axis=y,waterlogged=false]")
    # ---------------- loot and fish-men
    b.chest(HX0 + 2, FLOOR - 6, HZ0 + 2, "pirate", "east"); b.chest(DX0 + 2, FLOOR + 1, DZ0 + 2, "medium", "east")
    b.guards("fishman", GUARDS, y=FLOOR + 1)
    b.guards("fishman", ((HX0 + 9, HZ0 + 6),), y=FLOOR - 6)
    return b, 0
