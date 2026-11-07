"""Corrida Colosseum (Dressrosa): the great round arena where gladiators fight for the Mera Mera fruit, built to
match the show:
- a Roman-amphitheatre drum of three arcaded storeys in sandstone and terracotta, flags all round the crown;
- three levels of seating all round, each tier a run of stepped rows behind a podium wall, with radial stairways;
- in the middle a ROUND stone stage standing in a ring of water, the moat of fighting fish (fins cut the surface),
  reached by four walkways from the four fighters' gates;
- the royal box with a canopy on the north side;
- under the stands a ring of rooms: gladiator barracks, armories, a kitchen, a doctor's room, the cells of the toy
  prisoners and the trophy room where the fruit waits. A strip of the Sunflower Field outside. ~100 x 100.
Ground = y 0; the moat surface is y 0 and its floor y -6."""
import math, random
from canvas import *
import interiors as I

SID = "corrida_colosseum"
TITLE = "Corrida Colosseum"
CUTS = [3, 12]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 100
CX, CZ = 50, 50
R_OUT = 44     # outer wall radius
R_SEAT = 38    # front of the outer room ring / back of the seats
R_RING = 20    # arena wall radius
H = 24         # outer wall height
STONE = "minecraft:smooth_sandstone"
TERR = "minecraft:orange_terracotta"
WARM = dict(wood="spruce", rug="red", rug2="orange", bed="red", light="minecraft:lantern", accent="minecraft:cut_sandstone",
            banner="red", candle="orange")


def build():
    rnd = random.Random(19)
    b = B()
    # ---------------- ground and the sunflower field
    for x in range(N):
        for z in range(N):
            for y in (-6, -5, -4, -3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            d = math.hypot(x - CX, z - CZ)
            b.set(x, 0, z, "onepiece:dressrosa_mosaic" if d <= R_OUT + 3 else "minecraft:grass_block")
            if d > R_OUT + 3 and z > CZ + 30 and rnd.random() < 0.55:
                b.set(x, 1, z, "minecraft:sunflower[half=lower]"); b.set(x, 2, z, "minecraft:sunflower[half=upper]")
            elif d > R_OUT + 3 and rnd.random() < 0.08: b.set(x, 1, z, rnd.choice(("minecraft:poppy", "minecraft:short_grass", "minecraft:dandelion")))
    # ---------------- outer wall: three storeys of arches
    def outer(x, y, z):
        d = math.hypot(x - CX, z - CZ)
        return R_OUT - 2 <= d <= R_OUT and 1 <= y <= H
    for x in range(CX - R_OUT - 1, CX + R_OUT + 2):
        for z in range(CZ - R_OUT - 1, CZ + R_OUT + 2):
            d = math.hypot(x - CX, z - CZ)
            if not (R_OUT - 2 <= d <= R_OUT): continue
            ang = math.degrees(math.atan2(z - CZ, x - CX)) % 360
            seg = (ang % 7.5) / 7.5          # position inside one arch bay
            pier = seg <= 0.2 or seg >= 0.8
            for y in range(1, H + 1):
                storey = (y - 1) // 8; yy = (y - 1) % 8
                opening = not pier and (yy <= 4 or (yy == 5 and 0.32 < seg < 0.68))
                if d > R_OUT - 1 and opening:
                    continue  # open arch on the outer face, recessed one block
                if yy == 7: s = "minecraft:cut_sandstone"          # cornice between storeys
                elif pier: s = "minecraft:chiseled_sandstone" if yy == 0 else ("minecraft:cut_sandstone" if d > R_OUT - 1 else STONE)
                elif d <= R_OUT - 1: s = TERR if storey == 1 else ("minecraft:orange_stained_glass_pane" if storey == 0 and yy in (2, 3) and int(ang / 7.5) % 2 else STONE)
                else: s = STONE
                b.set(x, y, z, s)
            b.set(x, H + 1, z, "minecraft:cut_sandstone_slab[type=bottom,waterlogged=false]" if int(ang) % 4 else "minecraft:cut_sandstone")
    for a in range(0, 360, 15):  # flag poles and long banners on the crown
        t = math.radians(a + 3.75)
        x, z = round(CX + (R_OUT - 1) * math.cos(t)), round(CZ + (R_OUT - 1) * math.sin(t))
        for y in range(H + 1, H + 6): b.set(x, y, z, "minecraft:spruce_fence")
        b.set(x, H + 6, z, "minecraft:red_wool" if (a // 15) % 2 else "minecraft:yellow_wool")
        b.set(x + (1 if x > CX else -1), H + 5, z, "minecraft:red_wool" if (a // 15) % 2 else "minecraft:yellow_wool")
    # ---------------- the ring of rooms under the stands (y1..7) and the stands above them
    # The show: three levels of seating all round the arena. Each tier is a run of stepped rows; a flat walkway
    # (aisle) separates the tiers and the next tier starts behind a podium wall, as in a Roman amphitheatre.
    def seat_top(d):
        if d < 28.0: return 9 + int((d - 21.5) * 0.7), "seat"          # tier 1: 9..13
        if d < 30.0: return 13, "aisle"
        if d < 31.0: return 16, "podium"
        if d < 36.0: return 16 + int((d - 30.0) * 0.8), "seat"         # tier 2: 16..19
        if d < 38.0: return 19, "aisle"
        if d < 39.0: return 22, "podium"
        return 22 + int((d - 38.0) * 0.6), "seat"                      # tier 3: 22..24
    for x in range(CX - R_OUT, CX + R_OUT + 1):   # the whole drum, so the top tier meets the outer wall all round
        for z in range(CZ - R_OUT, CZ + R_OUT + 1):
            d = math.hypot(x - CX, z - CZ)
            if R_RING + 1 < d < R_OUT - 2:
                top, kind = seat_top(d)
                for y in range(8, top + 1): b.set(x, y, z, STONE)
                if kind == "seat":
                    b.set(x, top, z, "minecraft:cut_sandstone" if top % 2 else "minecraft:smooth_sandstone_slab[type=top,waterlogged=false]")
                elif kind == "aisle":
                    b.set(x, top, z, "minecraft:polished_granite")
                else:  # podium wall: orange band with a cut-stone coping
                    for y in range(top - 2, top): b.set(x, y, z, TERR)
                    b.set(x, top, z, "minecraft:cut_sandstone")
                b.set(x, 7, z, "minecraft:spruce_planks")
                b.set(x, 0, z, "minecraft:spruce_planks" if d < R_SEAT - 1.5 else "minecraft:polished_granite")
                if d >= R_SEAT - 0.5 and int(math.degrees(math.atan2(z - CZ, x - CX))) % 9 == 0 and abs(d - (R_SEAT + 1.5)) < 0.5: b.set(x, 6, z, lantern(True))
            if R_RING <= d <= R_RING + 1:
                for y in range(1, 10): b.set(x, y, z, "minecraft:stone_bricks" if y < 9 else "minecraft:cut_sandstone")
                b.set(x, 7, z, "minecraft:chiseled_stone_bricks" if int(math.degrees(math.atan2(z - CZ, x - CX))) % 6 == 0 else "minecraft:polished_andesite")
            if R_OUT - 2.5 <= d < R_OUT - 2 or R_RING + 1 <= d < R_RING + 1.6:
                for y in range(1, 7): b.set(x, y, z, "minecraft:stone_bricks")
    # radial stairways (aisles) up through the three tiers, between the gates
    for k in range(8):
        a = math.radians(22.5 + k * 45)
        ox, oz = math.cos(a), math.sin(a)
        face = ("east" if ox > 0 else "west") if abs(ox) > abs(oz) else ("south" if oz > 0 else "north")
        seen = set()
        for i in range(int((R_RING + 1.6) * 4), int((R_OUT - 2.2) * 4)):
            rr = i / 4
            for w in (-0.5, 0.5):
                x, z = round(CX + rr * ox - w * oz), round(CZ + rr * oz + w * ox)
                if (x, z) in seen: continue
                seen.add((x, z))
                d = math.hypot(x - CX, z - CZ)
                if not (R_RING + 1 < d < R_OUT - 2): continue
                top, kind = seat_top(d)
                st = stairs("minecraft:sandstone_stairs", face)
                # each podium wall is climbed by three steps: one on the back of the aisle, one cut into the podium
                # (a notch in its coping) and one cut into the first row behind it, so all three tiers link up
                step = None
                for (a0, base) in ((29.0, 14), (37.0, 20)):
                    if a0 <= d < a0 + 3: step = base + int(d - a0)
                if step is not None:
                    for y in range(step + 1, max(top, step) + 1): b.set(x, y, z, AIR)
                    b.set(x, step, z, st)
                elif kind == "seat": b.set(x, top, z, st)
    # radial walls that split the under-stand ring into 16 rooms, with doorways onto a ring corridor
    rooms = []
    for k in range(16):
        a0 = math.radians(k * 22.5)
        for rr in range(R_RING + 2, R_OUT - 2):
            x, z = round(CX + rr * math.cos(a0)), round(CZ + rr * math.sin(a0))
            for y in range(1, 7):
                if not (R_SEAT - 4 <= rr <= R_SEAT - 2 and y <= 3): b.set(x, y, z, "minecraft:stone_bricks")
        rooms.append(k)
    for x in range(CX - R_OUT, CX + R_OUT + 1):  # ring corridor wall (inner side of the outer rooms)
        for z in range(CZ - R_OUT, CZ + R_OUT + 1):
            d = math.hypot(x - CX, z - CZ)
            if R_SEAT - 1.5 <= d < R_SEAT - 0.5:
                ang = math.degrees(math.atan2(z - CZ, x - CX)) % 360
                for y in range(1, 7): b.set(x, y, z, "minecraft:stone_bricks")
                if abs((ang % 22.5) - 11.25) < 1.2:
                    for y in (1, 2, 3): b.set(x, y, z, AIR)
    # stairwells (vomitoria) from the gate passages up into the stands: beside the east, south and west fighters' gates
    # (the north one has the royal box over it) a two-wide flight climbs toward the arena in a stone-brick shaft, from a
    # landing off the gate passage, up through the y7 ceiling and the stands, and comes out in the lower rows of tier 1
    # inside a sandstone parapet
    FA = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1)):
        for sg in (-1, 1):
            def P(rr, w): return CX + dx * rr + dz * w * sg, CZ + dz * rr + dx * w * sg
            def top_at(rr, w):
                x, z = P(rr, w)
                return seat_top(math.hypot(x - CX, z - CZ))
            for rr in range(24, 36):
                for w in (3, 6):
                    if w == 3 and rr >= 34: continue          # the doorway from the gate passage onto the landing
                    x, z = P(rr, w)
                    for y in range(1, 7): b.set(x, y, z, "minecraft:stone_bricks")
            flight, opening = set(), set()
            for i in range(14):
                rr, y = 34 - i, 1 + i
                if y > top_at(rr, 4)[0]: break
                for w in (4, 5):
                    x, z = P(rr, w)
                    for yy in range(1, y): b.set(x, yy, z, STONE)
                    b.set(x, y, z, stairs("minecraft:sandstone_stairs", FA[(dx, dz)]))
                    for yy in range(y + 1, y + 4): b.set(x, yy, z, AIR)
                    flight.add((rr, w))
                    if y + 3 >= top_at(rr, w)[0]: opening.add((rr, w))
            for (rr, w) in opening:   # parapet round the opening, open on the arena side where the flight comes out
                for (r2, w2) in ((rr + 1, w), (rr, w - 1), (rr, w + 1), (rr + 1, w - 1), (rr + 1, w + 1)):
                    if (r2, w2) in opening: continue
                    t, kind = top_at(r2, w2)
                    x, z = P(r2, w2)
                    if kind == "seat" and b.get(x, t + 1, z) in (None, AIR): b.set(x, t + 1, z, wall("minecraft:sandstone_wall"))
    # furnish each wedge: inner wedge rooms (between arena wall and the corridor ring) and outer rooms
    kinds = ("barracks", "armory", "kitchen", "barracks", "cell", "cell", "storage", "lab", "barracks", "armory", "tavern", "bath",
             "cell", "workshop", "storage", "treasure")
    for k in range(16):
        a = math.radians(k * 22.5 + 11.25)
        for (rm, ww, sk) in ((R_RING + 6, 3, 0), (R_SEAT - 6, 4, 7)):
            cx, cz = CX + rm * math.cos(a), CZ + rm * math.sin(a)
            x0, z0, x1, z1 = round(cx - ww), round(cz - ww), round(cx + ww), round(cz + ww)
            I.furnish(b, x0, 1, z0, x1, z1, 6, kinds[(k + sk) % 16], WARM, seed=k * 31 + sk)
    # fighters' gates: four tunnels through the outer wall into the ring corridor and on to the arena
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for rr in range(R_RING - 1, R_OUT + 2):
            for w in (-2, -1, 0, 1, 2):
                x = CX + dx * rr + dz * w; z = CZ + dz * rr + dx * w
                for y in range(1, 6): b.set(x, y, z, AIR)
                b.set(x, 0, z, "minecraft:stone_bricks")
            if rr % 4 == 0 and R_RING + 2 <= rr <= R_OUT - 1:   # ribbed tunnel: pilasters along the sides
                for w in (-2, 2):
                    for y in range(1, 6): b.set(CX + dx * rr + dz * w, y, CZ + dz * rr + dx * w, "minecraft:stone_bricks")
        for w in (-2, -1, 0, 1, 2):  # portcullis bars on the arena side
            x = CX + dx * (R_RING) + dz * w; z = CZ + dz * (R_RING) + dx * w
            b.set(x, 5, z, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]" if dz else "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    # ---------------- the arena: in the show a ROUND stone stage stands in a ring of water (the moat of fighting
    # fish); four walkways from the four fighters' gates cross the water to the stage.
    RS = 12            # stage radius
    for x in range(CX - R_RING, CX + R_RING + 1):
        for z in range(CZ - R_RING, CZ + R_RING + 1):
            d = math.hypot(x - CX, z - CZ)
            if d >= R_RING: continue
            b.set(x, -6, z, "minecraft:stone")
            if d <= RS:   # the stage: a stone drum from the moat floor to y 2
                for y in range(-5, 2): b.set(x, y, z, "minecraft:stone_bricks" if d > RS - 1 else "minecraft:stone")
                ring = abs(d - (RS - 0.5)) < 0.5
                inner = abs(d - 6.5) < 0.5
                h = (x * 73856093 ^ z * 19349663) % 100
                b.set(x, 2, z, "minecraft:polished_andesite" if ring else ("minecraft:polished_diorite" if inner else
                       ("minecraft:cracked_stone_bricks" if h < 9 else ("minecraft:stone" if h < 30 else "minecraft:smooth_stone"))))
                if d > RS - 1: b.set(x, 1, z, "minecraft:mossy_stone_bricks" if (x * 5 + z) % 4 == 0 else "minecraft:stone_bricks")
            else:         # the moat
                for y in range(-5, 1): b.set(x, y, z, WATER)
                b.set(x, -5, z, WATER)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):   # the four walkways
        fa = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
        for rr in range(RS - 1, R_RING + 1):
            for w in (-2, -1, 0, 1, 2):
                x = CX + dx * rr + dz * w; z = CZ + dz * rr + dx * w
                if math.hypot(x - CX, z - CZ) <= RS - 0.5: continue
                for y in range(-5, 0): b.set(x, y, z, "minecraft:stone_bricks" if (rr + w) % 3 else "minecraft:polished_andesite")
                b.set(x, 0, z, "minecraft:polished_andesite" if abs(w) == 2 else "minecraft:smooth_stone")
                if rr == RS + 1: b.set(x, 1, z, stairs("minecraft:stone_brick_stairs", fa))
                if rr == RS:   # second step at the stage edge: the walkway climbs y0 -> y1 -> y2 onto the stage top
                    b.set(x, 1, z, "minecraft:stone_bricks"); b.set(x, 2, z, stairs("minecraft:stone_brick_stairs", fa))
        # the gate in the arena wall: framed opening with pillars standing in the water and a lintel
        rr = R_RING - 1
        for w in (-3, 3):
            for y in range(-5, 7): b.set(CX + dx * rr + dz * w, y, CZ + dz * rr + dx * w, "minecraft:polished_andesite" if y < 6 else "minecraft:chiseled_stone_bricks")
        for w in range(-2, 3):
            b.set(CX + dx * rr + dz * w, 6, CZ + dz * rr + dx * w, "minecraft:chiseled_stone_bricks" if w == 0 else "minecraft:stone_bricks")
            b.set(CX + dx * (rr + 1) + dz * w, 6, CZ + dz * (rr + 1) + dx * w, "minecraft:stone_bricks")
    # the fighting fish: big fish cruising the moat, a dorsal fin cutting the surface
    for (ang, rr, ln) in ((52, 16.2, 5), (205, 16.0, 4), (318, 16.4, 4)):
        a = math.radians(ang)
        tx, tz = -math.sin(a), math.cos(a)        # tangent: the fish swims round the ring
        fx, fz = CX + rr * math.cos(a), CZ + rr * math.sin(a)
        for i in range(-ln * 4, ln * 4 + 1):
            u = i / 4
            for vv in range(-6, 7):
                v = vv / 4
                if (u / ln) ** 2 + (v / 1.6) ** 2 > 1: continue
                x, z = round(fx + u * tx - v * tz), round(fz + u * tz + v * tx)
                if not (RS + 0.5 < math.hypot(x - CX, z - CZ) < R_RING - 0.5): continue
                hh = 1.6 * math.sqrt(max(0, 1 - (u / ln) ** 2 - (v / 1.6) ** 2))
                for y in range(-5, -5 + int(round(hh * 1.6)) + 1):
                    b.set(x, y, z, "minecraft:gray_terracotta" if y > -4 else "minecraft:light_gray_terracotta")
        for (u, top) in ((-2, 0), (-1, 1), (0, 2), (1, 1)):   # the dorsal fin
            x, z = round(fx + u * tx), round(fz + u * tz)
            for y in range(-3, top + 1): b.set(x, y, z, "minecraft:cyan_terracotta" if y > 0 else "minecraft:gray_terracotta")
        for v in (-1, 0, 1):   # tail fin, just under the surface
            x, z = round(fx - (ln + 1) * tx - v * tz), round(fz - (ln + 1) * tz + v * tx)
            for y in range(-4, -1 + abs(v)): b.set(x, y, z, "minecraft:cyan_terracotta")
    # ---------------- the royal box (north side) with a canopy
    bx0, bx1 = CX - 7, CX + 7
    bz = CZ - R_RING - 6
    b.box(bx0, 12, bz - 4, bx1, 12, bz + 3, "minecraft:polished_granite")
    b.box(bx0, 13, bz - 4, bx1, 17, bz + 3, AIR)
    for x in range(bx0, bx1 + 1): b.set(x, 13, bz + 3, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
    for x in range(bx0, bx1 + 1, 2): b.set(x, 13, bz - 1, stairs("minecraft:dark_oak_stairs", "north")); b.set(x, 13, bz - 2, "minecraft:red_carpet")
    b.set(CX, 13, bz - 3, stairs("minecraft:red_nether_brick_stairs", "north")); b.set(CX - 1, 13, bz - 3, "minecraft:gold_block"); b.set(CX + 1, 13, bz - 3, "minecraft:gold_block")
    for x in (bx0, bx1):
        for z in (bz - 4, bz + 3): b.column(x, z, 13, 17, "minecraft:quartz_pillar[axis=y]")
    for x in range(bx0 - 1, bx1 + 2):
        for z in range(bz - 5, bz + 5): b.set(x, 18, z, "minecraft:red_wool" if (x + z) % 2 else "minecraft:yellow_wool")
    # a short stair at each side of the box: the tier-1 rows beside it are turned into sandstone steps climbing north,
    # from the front rows up to the level of the box floor, where you step in between the corner pillars
    for x in (bx0 - 2, bx0 - 1, bx1 + 1, bx1 + 2):
        for z in range(bz - 1, bz + 5):
            top, kind = seat_top(math.hypot(x - CX, z - CZ))
            if kind == "seat" and top <= 12: b.set(x, top, z, stairs("minecraft:sandstone_stairs", "north"))
    # ---------------- sunflower field shed, a few market stalls outside the gate
    for (sx, sz, col) in ((CX - 14, CZ + R_OUT + 5, "minecraft:red_wool"), (CX + 10, CZ + R_OUT + 5, "minecraft:yellow_wool"),
                         (CX + R_OUT + 4, CZ - 10, "minecraft:orange_wool")):
        if 0 < sx < N - 4 and 0 < sz < N - 4: b.stall(sx, 1, sz, col)
    # ---------------- people
    b.npc(CX, 3, CZ, "fujitora", True)
    b.chest(CX, 1, CZ + R_RING + 4, "hard", "south"); b.chest(CX + 1, 13, bz - 3, "hard", "south")
    b.guards("gladiator", ((CX - 6, CZ - 6), (CX + 6, CZ - 6), (CX - 6, CZ + 6), (CX + 6, CZ + 6)), y=3)
    b.guards("gladiator", ((CX + R_RING + 6, CZ), (CX - R_RING - 6, CZ), (CX, CZ + R_RING + 6)), y=1)
    return b, 0
