"""Angel Beach in Skypiea, 10,000 m up: a white island of Island Cloud on the White-White Sea, the creamy sea of
cloud that the sky people sail on like water (here a ring of milky white sea cloud round the beach). Soft
cloud beach with palms, the round cloud cottages of Lovely Street, Conis and Pagaya's house with the Waver
garage, the dial shop and market stalls, the Milky Road ribbon curling off the edge, and the cloud dock where the
Wavers and the Going Merry tie up. Inside the round houses: kitchens with dial lamps, bedrooms, the dial shop.
~100 x 92, floats at a fixed height (canvas y 0 = world y 168)."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "angel_beach"
TITLE = "Angel Beach (Skypiea)"
CUTS = [2]
TILER = dict(terrain="none", sky_y=168)

NX, NZ = 100, 92
CX, CZ = 50, 46
CLOUD = "onepiece:island_cloud"
PUFF = "onepiece:cloud_puff"
CBR = "onepiece:cloud_bricks"
SEA = "minecraft:white_stained_glass"   # sea cloud
SEA_DEEP = "minecraft:light_blue_stained_glass"  # a faint blue tint in the shallows by the beach
SEA_Y = -3


def sea_q(x, z):
    a = math.atan2(z - CZ, x - CX)
    r = 1 + 0.08 * math.sin(a * 5) + 0.05 * math.cos(a * 3)
    return (((x - CX) / 44) ** 2 + ((z - CZ) / 38) ** 2) / r
SKY = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:pearlescent_froglight[axis=y]",
           accent="onepiece:cloud_bricks", banner="light_blue", candle="white")


def inside(x, z):
    a = math.atan2(z - CZ, x - CX)
    r = 1 + 0.08 * math.sin(a * 5) + 0.05 * math.cos(a * 3)
    return ((x - CX) / 44) ** 2 + ((z - CZ) / 38) ** 2 < r


def cottage(b, x, z, r, rnd, kind, door="south"):
    """A round cloud cottage: white dome walls, a sky-blue band, round windows, a little chimney."""
    b.cyl(x, z, r, 0, 0, "minecraft:birch_planks")
    b.cyl(x, z, r, 1, 3, "minecraft:white_concrete", hollow=True)
    b.dome(x, z, 4, r, h=r - 1, s="minecraft:white_concrete", tip=None, hollow=False)
    b.dome(x, z, 4, r - 1, h=r - 2, s=AIR, tip=None, hollow=False)
    b.cyl(x, z, r - 1, 1, 3, AIR)
    for a in range(0, 360, 6):
        t = math.radians(a)
        b.set(round(x + r * math.cos(t)), 4, round(z + r * math.sin(t)), "minecraft:light_blue_concrete")
    for a in range(0, 360, 4):  # a base course of cloud bricks so the cottage sits on the cloud
        t = math.radians(a)
        b.set(round(x + r * math.cos(t)), 1, round(z + r * math.sin(t)), CBR)
    for a in range(0, 360, 60):  # ribs standing proud of the round wall (two of them frame the door)
        t = math.radians(a)
        for y in range(1, 4): b.set(round(x + (r + 1) * math.cos(t)), y, round(z + (r + 1) * math.sin(t)), CBR)
        b.set(round(x + (r + 1) * math.cos(t)), 4, round(z + (r + 1) * math.sin(t)), "minecraft:light_blue_concrete")  # capped by the blue band
    for a in (45, 135, 225, 315):  # windows with a cloud-brick sill and lintel
        t = math.radians(a)
        wx, wz = round(x + r * math.cos(t)), round(z + r * math.sin(t))
        b.set(wx, 2, wz, "minecraft:light_blue_stained_glass_pane"); b.set(wx, 3, wz, CBR)
    dz = r if door == "south" else -r
    for y in (1, 2): b.set(x, y, z + dz, AIR)
    b.set(x, 3, z + dz, "minecraft:birch_trapdoor[facing=%s,half=top,open=true,powered=false,waterlogged=false]" % ("south" if door == "south" else "north"))
    q = max(2, int((r - 1) / 1.42))
    I.furnish(b, x - q, 1, z - q, x + q, z + q, 3, kind, SKY, seed=x * 7 + z)
    b.set(x, 4 + r, z, "minecraft:light_blue_concrete"); b.set(x, 5 + r, z, "minecraft:end_rod[facing=up]")


def sky_palm(b, x, y, z, h, lean):
    """A tall beach palm: a trunk that curves away from the island, a crown of long drooping fronds."""
    LOG, LEAF = "onepiece:palm_log[axis=y]", "onepiece:palm_leaves[distance=7,persistent=true,waterlogged=false]"
    px = pz = 0
    for i in range(h):
        t = i / h
        px, pz = round(math.cos(lean) * 2.6 * t * t), round(math.sin(lean) * 2.6 * t * t)
        b.set(x + px, y + i, z + pz, LOG)
    tx, ty, tz = x + px, y + h, z + pz
    b.set(tx, ty, tz, LEAF); b.set(tx, ty - 1, tz, LOG)
    for k in range(8):
        a = k * math.pi / 4 + lean
        for j in range(1, 5):
            b.set(round(tx + math.cos(a) * j), ty - (0 if j < 2 else 1 if j < 4 else 2), round(tz + math.sin(a) * j), LEAF)


def build():
    rnd = random.Random(411)
    b = B()
    # ---------------- the island of cloud, thick in the middle, a soft beach sloping down to the sea at the edge
    r2 = random.Random(4110)
    for x in range(NX):
        for z in range(NZ):
            if not inside(x, z): continue
            d = math.hypot((x - CX) / 44, (z - CZ) / 38)
            depth = int(2 + 9 * max(0, 1 - d) ** 1.4 + rnd.random() * 1.5)
            q = sea_q(x, z)
            top = 0 if q < 0.84 else -1 if q < 0.93 else -2   # the beach shelves down into the sea cloud
            for y in range(-depth, top + 1): b.set(x, y, z, CLOUD)
            if d > 0.86: b.set(x, top, z, PUFF)  # the soft beach
            if d > 0.95 and rnd.random() < 0.4: b.set(x, top + 1, z, PUFF)
    # ---------------- the White-White Sea: a ring of milky sea cloud lapping at the beach (wavers and ships sail on it)
    for x in range(CX - 56, CX + 57):
        for z in range(CZ - 50, CZ + 51):
            if inside(x, z): continue
            q = sea_q(x, z)
            if q >= 1.5: continue
            # a glossy skin of sea cloud on a solid, opaque body of cloud (stained glass alone is see-through in the
            # game: players would look straight down 165 blocks), with a faint blue tint only in the shallows
            b.set(x, SEA_Y, z, SEA_DEEP if q < 1.04 else SEA)
            b.set(x, SEA_Y - 1, z, CLOUD)
            if q > 1.42 and r2.random() < 0.45: b.set(x, SEA_Y + 1, z, PUFF)  # foam where the sea cloud thins out
            elif q < 1.06 and r2.random() < 0.3: b.set(x, SEA_Y + 1, z, PUFF)  # surf on the beach
            if r2.random() < 0.08: b.set(x, SEA_Y - 2, z, PUFF)
    for i in range(26):  # cloud puffs drifting under and around
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(30, 46)
        x, z = CX + rr * math.cos(a) * 1.05, CZ + rr * math.sin(a) * 0.9
        if 2 < x < NX - 3 and 2 < z < NZ - 3:
            py, pr = rnd.randint(-10, -3), rnd.uniform(1.5, 3.2)
            if x < 16 and 32 < z < 62: continue  # not under the dock and its steps (no dark hollow there to light)
            b.sphere(x, py, z, pr, PUFF, ry=1.2)
    # ---------------- the cloud dock out on the sea cloud, with the wavers moored alongside (west edge)
    DY = SEA_Y + 1
    for z in range(36, 58):
        for x in range(2, 10):
            for y in range(DY + 1, 2): b.set(x, y, z, AIR) if b.get(x, y, z) in (CLOUD, PUFF) else None
            b.set(x, DY, z, "minecraft:birch_planks" if z % 4 else "minecraft:stripped_birch_log[axis=x]")
        if z % 4 == 0: b.set(2, DY + 1, z, fence("birch")); b.set(2, DY + 2, z, lantern())
    for z in range(38, 56, 4):  # flights of steps up from the dock (y -2) onto the beach (y 0)
        for zz in (z, z + 1):
            b.set(10, DY, zz, "minecraft:birch_planks")                            # the dock runs on under the first step
            b.set(10, DY + 1, zz, stairs("minecraft:birch_stairs", "east"))
            b.set(11, DY, zz, CLOUD); b.set(11, DY + 1, zz, CLOUD)
            b.set(11, DY + 2, zz, stairs("minecraft:birch_stairs", "east"))
            for y in range(DY, 1): b.set(12, y, zz, CLOUD)                         # the sand at the top of the flight
            if b.get(13, 0, zz) in (None, AIR): b.set(13, 0, zz, CLOUD)
            for (x, y0) in ((10, DY + 2), (11, DY + 3), (12, 1)):                  # headroom over every step
                for y in range(y0, y0 + 3): b.set(x, y, zz, AIR)
    for (z0, c) in ((38, "light_blue"), (45, "white"), (52, "yellow")):  # wavers: little dial-driven one-man boats
        for x in range(-4, 2):
            for z in (z0, z0 + 1):
                b.set(x, SEA_Y, z, SEA); b.set(x, SEA_Y - 1, z, CLOUD)
                for y in range(DY, DY + 3): b.set(x, y, z, AIR)
        for z in (z0, z0 + 1):
            b.set(-3, DY, z, slab("minecraft:birch_slab"))                       # the pointed bow
            for x in (-2, -1, 0): b.set(x, DY, z, f"minecraft:{c}_concrete")     # the painted deck
            b.set(1, DY, z, stairs("minecraft:birch_stairs", "west"))            # the raised tail with the jet dial
        b.set(-2, DY + 1, z0, fence("birch")); b.set(-2, DY + 2, z0, "minecraft:birch_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")  # steering bar
        b.set(1, DY + 1, z0 + 1, "minecraft:white_concrete")                      # the dial
    # the Milky Road: a river of sea cloud that leaves the White-White Sea off the south-west beach, lifts off the
    # edge of the sea and curls away up into the sky until it runs into a cloud bank (never over the beach or town)
    pts = ((40, 88, SEA_Y), (30, 90, SEA_Y), (20, 91, SEA_Y + 1), (10, 90, SEA_Y + 4), (3, 86, SEA_Y + 8),
           (-1, 80, SEA_Y + 12), (-2, 74, SEA_Y + 16), (-1, 69, SEA_Y + 19))

    def cr(p0, p1, p2, p3, t):  # Catmull-Rom spline through the control points
        return tuple(0.5 * (2 * b1 + (-a + c) * t + (2 * a - 5 * b1 + 4 * c - d) * t * t + (-a + 3 * b1 - 3 * c + d) * t ** 3)
                     for a, b1, c, d in zip(p0, p1, p2, p3))
    ext = (pts[0],) + pts + (pts[-1],)
    road = []
    for k in range(len(pts) - 1):
        for i in range(24):
            road.append(cr(ext[k], ext[k + 1], ext[k + 2], ext[k + 3], i / 24))
    road.append(pts[-1])
    surface = set()
    for j, (x, z, y) in enumerate(road):
        x2, z2, _ = road[min(j + 1, len(road) - 1)]; x1, z1, _ = road[max(j - 1, 0)]
        tl = math.hypot(x2 - x1, z2 - z1) or 1
        nx, nz = -(z2 - z1) / tl, (x2 - x1) / tl
        yy = round(y)
        for w2 in range(-5, 6):
            w = w2 / 2
            px, pz = round(x + nx * w), round(z + nz * w)
            if abs(w) <= 1.5:
                surface.add((px, yy, pz))
                b.set(px, yy - 1, pz, CLOUD)                                  # its opaque cloud bed
                if yy > SEA_Y + 1: b.set(px, yy - 2, pz, CLOUD)
            elif yy > SEA_Y:                                                  # soft banks once it leaves the sea
                for dy in (-1, 0, 1): b.set(px, yy + dy, pz, CLOUD)
    for p in surface:
        if b.get(p[0], p[1] + 1, p[2]) != CLOUD: b.set(*p, SEA)
    ex, ez, ey = pts[-1]
    for (dx, dz, dy, r) in ((0, 0, 0, 4.5), (3, 2, 2, 3.5), (-2, 3, 1, 3.2), (2, -3, -1, 3.0), (4, 0, -2, 2.6)):  # the cloud bank
        b.sphere(ex + dx, ey + dy, ez + dz, r, CLOUD, ry=r * 0.7)
    # ---------------- Lovely Street: two curving lanes of round cottages
    kinds = ("kitchen", "bedroom", "dining", "bedroom", "storage", "kitchen", "bedroom", "dining", "library", "bedroom")
    k = 0
    for (x, z, r) in ((24, 24, 5), (36, 18, 6), (50, 16, 5), (64, 18, 6), (78, 26, 5), (82, 42, 6), (76, 60, 5), (62, 70, 6),
                      (46, 72, 5), (30, 66, 6)):
        if not inside(x, z): continue
        cottage(b, x, z, r, rnd, kinds[k % len(kinds)], door="south" if z < CZ else "north"); k += 1
    T.path(b, [(16, 46), (30, 40), (50, 32), (70, 34), (78, 46), (64, 58), (46, 60), (28, 54), (16, 46)], w=1, s="minecraft:white_concrete", alt="minecraft:light_blue_concrete")
    # ---------------- Conis and Pagaya's house: a big two-room cottage with the Waver garage
    cottage(b, CX, CZ - 2, 8, rnd, "kitchen")
    cottage(b, CX + 13, CZ + 2, 5, rnd, "bedroom")
    for x in range(CX + 6, CX + 10):
        for y in (1, 2): b.set(x, y, CZ, AIR)
        b.set(x, 0, CZ, "minecraft:birch_planks"); b.set(x, 3, CZ, "minecraft:white_concrete")
    gx0 = CX - 16  # the garage with Pagaya's Wavers
    b.walls(gx0, 0, CZ - 4, gx0 + 6, 4, CZ + 4, "minecraft:birch_planks"); b.box(gx0 + 1, 1, CZ - 3, gx0 + 5, 4, CZ + 3, AIR)
    b.box(gx0, 5, CZ - 4, gx0 + 6, 5, CZ + 4, "minecraft:white_concrete")
    for z in range(CZ - 2, CZ + 3): b.set(gx0 + 6, 1, z, AIR); b.set(gx0 + 6, 2, z, AIR)
    I.furnish(b, gx0 + 1, 1, CZ - 3, gx0 + 5, CZ + 3, 4, "workshop", SKY, seed=44)
    # ---------------- the dial shop and the market stalls
    cottage(b, 22, 40, 6, rnd, "lab")
    for i, (x, z) in enumerate(((60, 40), (66, 44), (60, 50), (40, 50), (34, 46))):
        T.stall(b, x, z, ("light_blue", "white", "yellow", "pink", "lime")[i], (("minecraft:pearlescent_froglight[axis=y]", "minecraft:melon", None),
                                                                                 ("onepiece:cloud_puff", "minecraft:sea_pickle[pickles=3,waterlogged=false]", None))[i % 2])
    # palms on the beach
    for i in range(18):
        a = rnd.uniform(0, 2 * math.pi)
        x, z = round(CX + 40.5 * math.cos(a)), round(CZ + 34.5 * math.sin(a))
        if inside(x, z) and b.get(x, 1, z) is None and not (x < 13 and 33 < z < 61):
            gy = 0
            while gy > -3 and b.get(x, gy, z) in (None, AIR): gy -= 1
            b.set(x, gy, z, CLOUD)
            sky_palm(b, x, gy + 1, z, rnd.randint(7, 10), rnd.uniform(0, 2 * math.pi))
    for (x, z) in ((40, 40), (60, 30), (30, 30), (70, 52)): T.lamp_post(b, x, z)
    # ---------------- loot
    b.chest(CX - 2, 1, CZ - 6, "sky_treasure", "south")
    b.chest(23, 1, 44, "sky_treasure", "north")
    return b, 0
