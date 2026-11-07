"""Amazon Lily v2, the island of women in the Calm Belt, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/amazon_lily.md).

The Kuja capital in a ring of sheer jungle cliffs, open to a cove in the south, now on a 168 site (v1: 112). The
Kuja Palace is a real palace: a two-storey-high throne hall under a great purple onion dome on a drum, two
three-floor wings of furnished rooms (the sisters' rooms, guest rooms, library, armory, kitchen), Hancock's bath on
the top floor, four corner towers with gold onion domes, a front colonnade, a grand stair and the two coiled snake
statues. The Kuja Battle Arena is a proper amphitheatre with tiered seats, two gates and the petrified snakes. The
town has ~25 round huts with striped thatch cones (one or two floors, furnished, ladders), a market street of
stalls, the warriors' longhouse, an archery range and a training yard, jungle on the cliffs, and the Perfume Yuda
with its two serpents in the cove. Ground = y 0, the cove to the south. (v2)
v3 (2026-10-30): two giant serpents coiled on plinths either side of the stair whose heads meet over the palace door,
and a serpent spiralling up each corner tower."""
import math
import random
import numpy as np
from canvas import B, AIR
from mcb.kit import BigBuild, P, seed_of, st, furnish, tier, cornice, stair_core, wing_floor, house_module, \
    place_house, onion_dome, set_if_air, lamp_post
from mcb.bridge import to_canvas
import amazon_lily as OLD
import interiors as I
import townkit as T
import landkit as L
from mcb import perfume_yuda as Y

SID = "amazon_lily"
TITLE = OLD.TITLE
CUTS = [3, 10, 16]
TILER = OLD.TILER
N = 168
CX, CZ = 84, 74
PURP = "minecraft:purple_terracotta"
GOLD = "minecraft:gold_block"
QZ = "minecraft:smooth_quartz"
KUJA = OLD.KUJA
PX0, PX1, PZ0, PZ1 = CX - 32, CX + 32, 24, 62
HW = 12                                   # throne hall half width
FH = 6
MARKET_Z = (108, 112)
LONG = dict(walls=["minecraft:mud_bricks", "minecraft:packed_mud", "minecraft:mud_bricks"],
            frame="minecraft:stripped_jungle_log", base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks"],
            floor="minecraft:jungle_planks", wood="jungle", chimney="minecraft:mud_bricks")


def ring_d(x, z):
    """0 at the town centre, ~0.92 on the cliff crest. The crest is pulled in on the north side so the cliffs stand
    inside the site (v2.0 had their peak right on the site edge, so they ended in a flat wall)."""
    return math.hypot((x - CX) / 74, (z - CZ) / (72 if z >= CZ else 66))


def cove_v(x, z):
    """< 1 inside the cove's water (an ellipse opening to the south edge), 1..1.5 its beach."""
    return ((x - CX) / 48) ** 2 + ((z - N - 6) / 30) ** 2


def open_ground(x, z):
    return (ring_d(x, z) < 0.81 or (z > 118 and abs(x - CX) < 42)) and cove_v(x, z) > 1.3


def cliff_h(x, z):
    """Height of the cliff ring at a column: a steep inner face up to the crest, a long rugged slope outward, a gap
    for the cove that widens gradually (no straight cut), and an outer slope that runs out to nothing before the site
    edge at a noisy margin, so the island ends in rolling ground and beaches instead of a sheer cut."""
    d = ring_d(x, z)
    w = 0.07 if d < 0.92 else 0.17
    h = 42 * math.exp(-((d - 0.92) / w) ** 2)
    # the cove gap: the ring dips down smoothly toward the harbour mouth
    if z > CZ:
        gap = min(1.0, max(0.0, (abs(x - CX) - 34) / 18))
        mouth = min(1.0, max(0.0, (z - 100) / 20))
        h *= 1 - mouth * (1 - gap * gap * (3 - 2 * gap))
    # and the cliffs only rise behind the beach
    t = min(1.0, max(0.0, (cove_v(x, z) - 1.1) / 0.9))
    h *= t * t * (3 - 2 * t)
    # rugged top: two scales of noise, never a regular sine pattern
    h *= 0.78 + 0.32 * L.noise2(x, z, 5011, 9) + 0.12 * L.noise2(x, z, 5012, 3)
    # fade out toward the site edge: the outer slope may not be steeper than ~2 blocks per block
    edge = min(x, z, N - 1 - x, N - 1 - z) - (3 + 7 * L.noise2(x, z, 5013, 11))
    return min(h, max(0.0, 2.1 * edge))


def cliffs(b, rnd):
    for x in range(N):
        for z in range(N):
            if ring_d(x, z) < 0.78:
                continue
            h = int(cliff_h(x, z)) + (rnd.randint(0, 1) if rnd.random() < 0.5 else 0)
            if h < 2:
                continue
            for y in range(1, h + 1):
                b.set(x, y, z, L._rock(x, y, z, 5020, moss=True) if y < h - 1 else ("minecraft:grass_block" if y == h else "minecraft:dirt"))
            if rnd.random() < 0.045 and h > 6:
                t = rnd.randint(5, 9)
                for y in range(h + 1, h + t):
                    b.set(x, y, z, "minecraft:jungle_log[axis=y]")
                b.sphere(x, h + t, z, rnd.choice((2.5, 3.0, 3.5)),
                         "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]")


def beach(b):
    """A sand beach round the cove, and a sea floor that shelves up toward it, instead of grass straight to an
    8-deep wall of water."""
    for x in range(N):
        for z in range(96, N):
            v = cove_v(x, z)
            if v < 0.55:
                continue
            if v < 1:
                depth = 1 + int((1 - v) / 0.45 * 7)              # 1 deep at the shore .. 8 out in the cove
                for y in range(-9, -depth):
                    b.set(x, y, z, "minecraft:sand" if y == -depth - 1 else "minecraft:sandstone")
                continue
            if v < 1.0 + 0.5 * L.noise2(x, z, 5031, 6):
                top = b.get(x, 1, z)
                if top is None or top == AIR or "grass" in top or "fern" in top or "flower" in top:
                    b.set(x, 1, z, AIR)
                    b.set(x, 0, z, "minecraft:sand")
                    b.set(x, -1, z, "minecraft:sandstone")


def palace(bb, tracker, audit):
    MZ = (PZ0 + PZ1) // 2
    bb.fill(PX0 - 4, 0, PZ0 - 4, PX1 + 4, 2, PZ1 + 4, QZ)
    # the wings: three floors of rooms
    tops = []
    for (x1, x2, nm) in ((PX0, CX - HW - 1, "w"), (CX + HW + 1, PX1, "e")):
        top = tier(bb, x1, PZ0, x2, PZ1, 2, 3, FH, PURP, "minecraft:purple_stained_glass_pane", "minecraft:quartz_stairs",
                   pilaster="minecraft:quartz_pillar[axis=y]", band=QZ, plate="minecraft:jungle_planks", top_plate=QZ,
                   every=3, pil_every=4, win_h=3)
        cornice(bb, x1, PZ0, x2, PZ1, top, "minecraft:quartz_stairs")
        for x in range(x1, x2 + 1, 4):
            for z in (PZ0 - 1, PZ1 + 1):
                bb.set(x, top, z, GOLD)
        tops.append(top)
        sx = x1 + 2 if nm == "w" else x2 - 6
        stair_core(bb, sx, PZ1 - 6, 5, 3, 3 + FH * 2, [3 + FH, 3 + FH * 2], PURP, "minecraft:jungle_stairs",
                   newel="minecraft:quartz_pillar[axis=y]", slit=None)
        kinds = [["kitchen", "storage", "living"], ["bedroom", "library", "bedroom"], ["bedroom", "living", "bedroom"]] \
            if nm == "w" else [["workshop", "storage", "living"], ["library", "bedroom", "living"], ["bedroom", "bedroom"]]
        for k in range(3):
            y = 3 + FH * k
            z1 = PZ0 + 1
            if nm == "e" and k == 2:                  # Hancock's bath takes the north end of the top floor
                bb.fill(x1 + 1, y, PZ0 + 15, x2 - 1, y + FH - 2, PZ0 + 15, PURP)
                bb.fill((x1 + x2) // 2, y, PZ0 + 15, (x1 + x2) // 2, y + 1, PZ0 + 15, AIR)
                z1 = PZ0 + 16
            wing_floor(bb, x1 + 1, z1, x2 - 1, PZ1 - 1, y, FH - 1, PURP, seed_of("kuja", nm, k), tracker, kinds[k],
                       corridor="z", cw=3, keep=[(sx - 1, PZ1 - 7, sx + 5, PZ1 - 1)], wood="jungle", audit=audit,
                       max_room=9, carpet=(None, "minecraft:purple_carpet"))
        # a small onion dome on each wing
        onion_dome(bb, (x1 + x2) // 2, top + 1, MZ, 6, "minecraft:purple_concrete")
    # the throne hall, open two storeys high
    hx1, hx2 = CX - HW, CX + HW
    top = tier(bb, hx1, PZ0, hx2, PZ1, 2, 1, 22, PURP, "minecraft:purple_stained_glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band=QZ, plate=QZ, top_plate=QZ, every=3, pil_every=4, win_h=9)
    cornice(bb, hx1, PZ0, hx2, PZ1, top, "minecraft:quartz_stairs")
    for (x, z) in ((hx1 - 1, PZ1 - 3), (hx2 + 1, PZ1 - 3), (hx1 - 1, PZ0 + 20), (hx2 + 1, PZ0 + 20)):
        bb.fill(x, 3, z, x, 4, z, AIR)                                         # doors into the wings
    for k in (1, 2):
        for x in (hx1, hx2):
            bb.fill(x, 3 + FH * k, PZ1 - 3, x, 4 + FH * k, PZ1 - 3, AIR)
    # the drum and the great onion dome
    bb.cylinder(CX, top + 1, MZ, 12, top + 4, QZ)
    bb.cylinder(CX, top + 3, MZ, 12, top + 3, GOLD)
    dome_top = onion_dome(bb, CX, top + 5, MZ, 12, "minecraft:purple_concrete")
    # the front: arched door, colonnade, grand stair
    P.arched_opening(bb, "x", CX, 3, PZ1, 9, 10, depth=1, trim=GOLD)
    for x in range(PX0, PX1 + 1, 4):
        bb.fill(x, 3, PZ1 + 3, x, 10, PZ1 + 3, "minecraft:quartz_pillar[axis=y]")
        bb.set(x, 11, PZ1 + 3, GOLD)
    bb.fill(PX0, 12, PZ1 + 1, PX1, 12, PZ1 + 4, QZ)
    bb.fill(PX0, 13, PZ1 + 4, PX1, 13, PZ1 + 4, "minecraft:purple_concrete")
    for k in range(3):
        bb.fill(CX - 6, 2 - k, PZ1 + 5 + k, CX + 6, 2 - k, PZ1 + 5 + k, st("minecraft:quartz_stairs", "north"))
        bb.fill(CX - 6, 3 - k, PZ1 + 5 + k, CX + 6, 3 - k, PZ1 + 5 + k, AIR)
    bb.fill(CX - 6, 0, PZ1 + 4, CX + 6, 2, PZ1 + 4, QZ)
    bb.fill(CX - 6, 3, PZ1 + 4, CX + 6, 3, PZ1 + 4, AIR)
    # four corner towers with gold onion domes
    for (tx, tz) in ((PX0 - 1, PZ0 - 1), (PX1 + 1, PZ0 - 1), (PX0 - 1, PZ1 + 1), (PX1 + 1, PZ1 + 1)):
        bb.cylinder(tx, 2, tz, 4, 30, QZ)
        bb.cylinder(tx, 3, tz, 3, 29, AIR)
        bb.fill(tx, 3, tz - 3, tx, 29, tz - 3, "minecraft:ladder[facing=south]")
        for y in (8, 14, 20, 26):
            for (dx, dz) in ((4, 0), (-4, 0), (0, 4)):
                bb.set(tx + dx, y, tz + dz, "minecraft:purple_stained_glass_pane")
        bb.cylinder(tx, 30, tz, 5, 30, PURP)
        onion_dome(bb, tx, 31, tz, 5, GOLD, tip="minecraft:purple_concrete")
        dx = 1 if tx < CX else -1
        dz = 1 if tz < MZ else -1
        bb.fill(tx + dx * 3, 3, tz + dz * 3, tx + dx * 4, 4, tz + dz * 4, AIR)
    return MZ, dome_top


def arena(bb, ax, az, R=19):
    """The Kuja Battle Arena: a sand pit inside a ring wall, seven rows of seats rising outward, two gates, banners."""
    bb.cylinder(ax, 0, az, R + 2, 0, "minecraft:sandstone")
    for k in range(8):
        r = 10 + k
        bb.fill_where(ax - R - 1, 1, az - R - 1, ax + R + 1, k + 1, az + R + 1,
                      lambda X, yy, Z, r=r: (np.hypot(X - ax, Z - az) <= r + 0.5) & (np.hypot(X - ax, Z - az) > r - 0.5),
                      "minecraft:smooth_sandstone" if k % 2 else "minecraft:cut_sandstone")
    bb.fill_where(ax - R - 2, 1, az - R - 2, ax + R + 2, 11, az + R + 2,
                  lambda X, yy, Z: (np.hypot(X - ax, Z - az) <= R + 1.5) & (np.hypot(X - ax, Z - az) > R + 0.5),
                  "minecraft:sandstone")
    bb.cylinder(ax, 0, az, 9, 0, "minecraft:sand")
    bb.cylinder(ax, -1, az, 9, -1, "minecraft:sandstone")
    bb.fill_where(ax - 10, 1, az - 10, ax + 10, 2, az + 10,
                  lambda X, yy, Z: (np.hypot(X - ax, Z - az) <= 10.5) & (np.hypot(X - ax, Z - az) > 9.5),
                  "minecraft:chiseled_sandstone")
    for (dx, dz) in ((0, R + 2), (-(R + 2), 0)):                                       # the two gates (south, west)
        sx, sz = (1, 0) if dz else (0, 1)
        for i in range(-2, 3):
            for r in range(9, R + 3):
                px = ax + (0 if dz else -r) + i * sx
                pz = az + (r if dz else 0) + i * sz
                bb.fill(px, 1, pz, px, 4, pz, AIR)
                bb.set(px, 0, pz, "minecraft:smooth_sandstone")
        gx, gz = ax + (0 if dz else -(R + 2)), az + (R + 2 if dz else 0)
        for s in (-3, 3):
            px, pz = gx + s * sx, gz + s * sz
            bb.fill(px, 1, pz, px, 9, pz, "minecraft:chiseled_sandstone")
            bb.set(px, 10, pz, "minecraft:lantern[hanging=false]")
        bb.fill(gx - 3 * sx, 8, gz - 3 * sz, gx + 3 * sx, 9, gz + 3 * sz, "minecraft:cut_sandstone")
        bb.fill(gx - 2 * sx, 7, gz - 2 * sz, gx + 2 * sx, 7, gz + 2 * sz, "minecraft:purple_wool")
    for a in range(0, 360, 30):
        t = math.radians(a)
        x, z = round(ax + (R + 1) * math.cos(t)), round(az + (R + 1) * math.sin(t))
        if bb.get_region(x, 11, z, x, 11, z)[0, 0, 0] > 1:
            bb.set(x, 12, z, "minecraft:purple_wool")
            bb.set(x, 13, z, "minecraft:purple_wool")
    # a royal box for Hancock on the north side
    bb.fill(ax - 3, 8, az - R, ax + 3, 8, az - R + 3, QZ)
    bb.fill(ax - 3, 12, az - R, ax + 3, 12, az - R + 3, "minecraft:purple_concrete")
    for x in (ax - 3, ax + 3):
        bb.fill(x, 9, az - R + 3, x, 11, az - R + 3, "minecraft:quartz_pillar[axis=y]")
    bb.set(ax, 9, az - R + 1, st("minecraft:purpur_stairs", "south"))


def kuja_hut(seed, r, floors, tracker, audit, kind_list):
    """A round Kuja hut: mud-brick walls, a striped purple-and-straw thatch cone, trapdoor shutters, a door south,
    every floor furnished, a ladder between floors."""
    m = BigBuild(seed=seed, y_min=-2, y_max=40)
    rng = np.random.default_rng(seed)
    h = floors * 5
    wall = ["minecraft:mud_bricks", "minecraft:packed_mud", "minecraft:mud_bricks"][int(rng.integers(3))]
    m.fill(-r - 1, -2, -r - 1, r + 1, 0, r + 1, "minecraft:cobblestone")
    m.cylinder(0, 0, 0, r, 0, "minecraft:jungle_planks")
    m.cylinder(0, 1, 0, r, h, wall)
    m.cylinder(0, 1, 0, r - 1, h, AIR)
    for f in range(1, floors):
        m.cylinder(0, f * 5, 0, r - 1, f * 5, "minecraft:jungle_planks")
    m.cylinder(0, h + 1, 0, r + 1, h + 1, "minecraft:stripped_jungle_log[axis=x]")
    for k in range(int(r * 1.6) + 2):
        rr = (r + 1.5) * (1 - k / (r * 1.6 + 2))
        m.fill_where(-r - 2, h + 2 + k, -r - 2, r + 2, h + 2 + k, r + 2,
                     lambda X, yy, Z, rr=rr: np.hypot(X, Z) <= rr + 0.3,
                     "minecraft:purple_wool" if k % 2 else "minecraft:hay_block[axis=y]")
    top = h + 2 + int(r * 1.6) + 2
    m.set(0, top, 0, "minecraft:gold_block")
    for f in range(floors):
        y = f * 5 + 2
        for a in (0, 90, 180):
            t = math.radians(a)
            x, z = round(r * math.cos(t)), round(-r * math.sin(t))
            m.fill(x, y, z, x, y + 1, z, AIR)
            fx = {0: "east", 90: "north", 180: "west"}[a]
            m.set(x + (1 if a == 0 else -1 if a == 180 else 0), y + 1, z + (-1 if a == 90 else 0),
                  f"minecraft:jungle_trapdoor[facing={fx},half=top,open=true]")
    m.fill(0, 1, r, 0, 2, r, AIR)
    m.set(0, 1, r, "minecraft:jungle_door[facing=south,half=lower,hinge=left,open=false]")
    m.set(0, 2, r, "minecraft:jungle_door[facing=south,half=upper,hinge=left,open=false]")
    m.set(0, 3, r + 1, "minecraft:jungle_trapdoor[facing=south,half=top,open=false]")
    q = int((r - 1) / math.sqrt(2))
    for f in range(floors):
        furnish(m, [(-q, -q, q, q)], f * 5 + 1, 4, [kind_list[f % len(kind_list)]], seed + f, tracker, doors=[(0, r)],
                wood="jungle", audit=audit)
        m.set(0, f * 5 + 4, 0, "minecraft:lantern[hanging=true]")
    if floors > 1:
        m.fill(-r + 1, 1, 0, -r + 1, (floors - 1) * 5, 0, "minecraft:ladder[facing=east]")
    return m


def town(bb, rng, tracker, audit):
    taken = [(PX0 - 8, PZ0 - 8, PX1 + 8, PZ1 + 12), (96, 62, 144, 110),          # palace, arena
             (14, 58, 46, 80),                                                 # longhouse + archery
             (20, MARKET_Z[0] - 4, 104, MARKET_Z[1] + 4),                      # market street
             (CX - 4, PZ1 + 8, CX + 4, 150)]                                   # main avenue
    kinds = (["kitchen", "bedroom"], ["living", "bedroom"], ["storage", "workshop"], ["bedroom", "library"])
    n = 0
    for _ in range(4000):
        r = int(rng.integers(4, 7))
        x, z = int(rng.integers(16, 152)), int(rng.integers(64, 146))
        box = (x - r - 1, z - r - 1, x + r + 1, z + r + 1)
        if not all(open_ground(px, pz) for px in (box[0], box[2]) for pz in (box[1], box[3])):
            continue
        if cove_v(x, z) < 1.3:                                                    # keep off the cove
            continue
        if any(box[0] <= t[2] and t[0] <= box[2] and box[1] <= t[3] and t[1] <= box[3] for t in taken):
            continue
        floors = 2 if r >= 5 and rng.random() < 0.6 else 1
        m = kuja_hut(seed_of("hut", n), r, floors, tracker, audit, kinds[n % 4])
        rot = 0 if z < MARKET_Z[0] else 2                                        # doors face the market street
        bb.stamp(m, x, 0, z, rot=rot, include_air=True)
        taken.append(box)
        n += 1
        if n >= 26:
            break
    return n


def longhouse_and_range(bb, tracker, audit):
    m, top, au = house_module(seed_of("longhouse"), 18, 9, 1, "minecraft:jungle_stairs", tracker,
                              ["bedroom", "bedroom", "storage"], pal=LONG, fh=6, chimney=True, timber=True, jetty=False)
    audit += au
    place_house(bb, m, 18, 9, 18, 0, 70, 3)                                     # door east
    for z in range(58, 69, 3):                                                   # archery range
        bb.set(44, 1, z, "minecraft:target[power=0]")
        bb.set(44, 2, z, "minecraft:hay_block[axis=y]")
        bb.set(20, 1, z, "minecraft:jungle_fence")
    bb.fill(20, 0, 58, 44, 0, 68, "minecraft:coarse_dirt")
    for x in range(22, 43, 4):
        bb.set(x, 1, 57, "minecraft:jungle_fence")
        bb.set(x, 2, 57, "minecraft:torch")
    for (x, z) in ((30, 84), (34, 84), (38, 84)):                               # training yard dummies
        bb.set(x, 1, z, "minecraft:jungle_fence")
        bb.set(x, 2, z, "minecraft:hay_block[axis=y]")
        bb.set(x, 3, z, "minecraft:carved_pumpkin[facing=south]")


# ---------------------------------------------------------------- v3: the Kuja serpents (audit: palace lacked snakes)
SCALE = ["minecraft:green_terracotta", "minecraft:green_terracotta", "minecraft:lime_terracotta",
         "minecraft:green_terracotta", "minecraft:green_terracotta", "minecraft:purple_terracotta"]
BELLY = "minecraft:yellow_terracotta"


def serpent_body(b, pts, r):
    """A scaled tube along pts [(x, y, z)...]: green with lime and Kuja purple bands, a pale belly underneath."""
    done = set()
    R = int(r) + 1
    for i, (px, py, pz) in enumerate(pts):
        blk = SCALE[(i // 2) % len(SCALE)]
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    if dx * dx + dy * dy + dz * dz > r * r + 0.4:
                        continue
                    q = (round(px + dx), round(py + dy), round(pz + dz))
                    if q in done:
                        continue
                    done.add(q)
                    b.set(*q, BELLY if dy <= -r + 0.8 else blk)


def serpent_head(b, x, y, z, fx, fz, s=1.0):
    """A reared snake head looking along (fx, fz): a long wedge skull, gold eyes, white fangs, open mouth and a red
    forked tongue. s scales it."""
    L, W, H = int(7 * s), max(2, int(2.6 * s)), max(2, int(2.4 * s))
    px, pz = -fz, fx
    for t in range(-1, L + 1):
        w = W - (t * W) // (L + 2)
        for u in range(-w, w + 1):
            for v in range(-H, H + 1):
                if t > L // 2 and abs(v) <= 0 and t < L:       # the open mouth: a slot in the front half
                    continue
                if abs(u) == w and abs(v) == H:
                    continue
                X, Z = round(x + fx * t + px * u), round(z + fz * t + pz * u)
                b.set(X, y + v, Z, "minecraft:yellow_terracotta" if v < -H + 1 else SCALE[0])
    for u in (-W + 1, W - 1):                                     # eyes and brow
        X, Z = round(x + fx * 2 + px * u), round(z + fz * 2 + pz * u)
        b.set(X, y + H, Z, "minecraft:gold_block")
        b.set(X, y + H - 1, round(Z), "minecraft:gold_block")
    for u in (-1, 1):                                             # fangs
        X, Z = round(x + fx * (L - 1) + px * u), round(z + fz * (L - 1) + pz * u)
        b.set(X, y - 1, Z, "minecraft:white_concrete")
        b.set(X, y + 1, Z, "minecraft:white_concrete")
    for t in range(L, L + 3):                                     # the forked tongue
        b.set(round(x + fx * t), y, round(z + fz * t), "minecraft:red_concrete")
    for u in (-1, 1):
        b.set(round(x + fx * (L + 3) + px * u), y, round(z + fz * (L + 3) + pz * u), "minecraft:red_concrete")


def gate_serpents(b):
    """Two giant serpents coiled on plinths either side of the grand stair; their necks rise and lean in so the two
    heads meet over the palace door, the Kuja's snake gate."""
    for side in (-1, 1):
        bx, bz = CX + side * 19, PZ1 + 14
        for x in range(bx - 7, bx + 8):                           # plinth
            for z in range(bz - 7, bz + 8):
                if math.hypot(x - bx, z - bz) <= 7.2:
                    for y in range(-2, 3):
                        b.set(x, y, z, QZ)
                    if math.hypot(x - bx, z - bz) > 6.2:
                        b.set(x, 3, z, GOLD if (x + z) % 3 == 0 else "minecraft:quartz_slab[type=bottom]")
        pts = []
        a0 = 0.0 if side < 0 else math.pi
        for k in range(150):                                      # 2.5 turns of coil
            a = a0 + side * k * 0.105
            pts.append((bx + 4.6 * math.cos(a), 4.5 + k * 0.11, bz + 4.6 * math.sin(a)))
        ex, ey, ez = pts[-1]
        hx, hy, hz = CX + side * 5, 34, PZ1 + 9
        for k in range(1, 70):                                    # the neck: up, then leaning in over the door
            t = k / 69
            mx, my, mz = bx, 40, bz - 2
            x = (1 - t) ** 2 * ex + 2 * (1 - t) * t * mx + t * t * hx
            y = (1 - t) ** 2 * ey + 2 * (1 - t) * t * my + t * t * hy
            z = (1 - t) ** 2 * ez + 2 * (1 - t) * t * mz + t * t * hz
            pts.append((x, y, z))
        serpent_body(b, pts, 2.2)
        serpent_head(b, hx, hy, hz, 0, 1, s=1.25)
        for k in range(14):                                       # the tail trailing off the plinth
            a = a0 - side * k * 0.2
            serpent_body(b, [(bx + (6 + k * 0.5) * math.cos(a), 3.5 - k * 0.2, bz + (6 + k * 0.5) * math.sin(a))], 2.2 - k * 0.1)


def tower_serpents(b):
    """A smaller snake spirals up each corner tower and rears over the gallery under the gold dome."""
    for (tx, tz) in ((PX0 - 1, PZ0 - 1), (PX1 + 1, PZ0 - 1), (PX0 - 1, PZ1 + 1), (PX1 + 1, PZ1 + 1)):
        fx = 1 if tx > CX else -1
        fz = 1 if tz > (PZ0 + PZ1) // 2 else -1
        a0 = math.atan2(fz, fx)
        pts = [(tx + 5.6 * math.cos(a0 + k * 0.09), 3 + k * 0.13, tz + 5.6 * math.sin(a0 + k * 0.09)) for k in range(176)]
        serpent_body(b, pts, 1.3)
        ex, ey, ez = pts[-1]
        n = math.hypot(fx, fz)
        serpent_head(b, round(ex), round(ey) + 1, round(ez), 0 if abs(fz) > abs(fx) else fx, fz if abs(fz) >= abs(fx) else 0, s=0.7)


def design():
    bb = BigBuild(seed=501, y_min=-8, y_max=90)
    tracker = P.PropTracker(501)
    audit = []
    rng = np.random.default_rng(501)
    palace(bb, tracker, audit)
    arena(bb, 120, 86)
    longhouse_and_range(bb, tracker, audit)
    print("huts:", town(bb, rng, tracker, audit))
    for z in range(PZ1 + 16, 136, 8):
        for x in (CX - 5, CX + 5):
            lamp_post(bb, x, 1, z, post="minecraft:jungle_fence")
    return bb, audit


def build():
    rnd = random.Random(501)
    b = B()
    T.ground(b, N, N, rnd, deco=0.12, decos=("minecraft:short_grass", "onepiece:amazon_flower", "minecraft:fern", "minecraft:short_grass"))
    T.sea(b, N, N, lambda x, z: cove_v(x, z) < 1, depth=8)
    cliffs(b, rnd)
    beach(b)
    T.path(b, [(CX, PZ1 + 8), (CX, 138)], w=2, s="minecraft:smooth_sandstone")
    T.path(b, [(24, (MARKET_Z[0] + MARKET_Z[1]) // 2), (104, (MARKET_Z[0] + MARKET_Z[1]) // 2)], w=2, s="minecraft:smooth_sandstone")
    T.path(b, [(CX + 4, 86), (100, 86)], w=1, s="minecraft:smooth_sandstone")
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    to_canvas(bb, b)
    MZ = (PZ0 + PZ1) // 2
    # the throne hall and Hancock's bath (v1 interiors)
    I.furnish(b, CX - HW + 1, 3, PZ0 + 1, CX + HW - 1, PZ1 - 1, 18, "throne", KUJA, seed=1)
    for z in range(PZ0 + 4, PZ1 - 1, 5):
        for x in (CX - 8, CX + 8):
            b.column(x, z, 3, 20, "minecraft:quartz_pillar[axis=y]")
            b.set(x, 21, z, GOLD)
    I.furnish(b, CX + HW + 2, 3 + FH * 2, PZ0 + 1, PX1 - 1, PZ0 + 14, FH - 1, "bath", KUJA, seed=2)
    gate_serpents(b)
    tower_serpents(b)
    for (dx, dz) in ((-5, 0), (5, 0)):                                           # the petrified snakes
        b.sphere(120 + dx, 2, 86 + dz, 1.8, "minecraft:stone")
    OLD.snake_statue(b, 120, 86 - 24, 12, facing=1)
    for i, x in enumerate(range(28, 104, 6)):
        if abs(x + 1 - CX) <= 5:
            continue
        col = ("purple", "pink", "magenta", "yellow", "lime", "orange")[i % 6]
        goods = (("minecraft:melon", "onepiece:amazon_flower", None), ("minecraft:hay_block[axis=y]", "minecraft:pumpkin", None))[i % 2]
        T.stall(b, x, MARKET_Z[0] - 4, col, goods)
        T.stall(b, x, MARKET_Z[1] + 2, col, goods, facing="north")
    # the Perfume Yuda in the cove (built with the ship kit) and the two Yuda serpents harnessed to her bow
    SZ = 158
    bow_x, ship = Y.place(b, CX - 35, SZ)
    for k, side in enumerate((-1, 1)):
        Y.yuda(b, bow_x + 6, SZ + side * 6, 11, side, k * 1.7, (bow_x - 3, 9, SZ + side * 2))
    # Hancock, warriors and loot
    b.npc(CX, 3, PZ0 + 5, "hancock", False)
    b.chest(CX + HW - 2, 3, PZ0 + 3, "treasure", "west")
    b.chest(120, 1, 86 + 7, "medium", "north")
    b.guards("kuja_warrior", ((CX - 4, PZ1 + 14), (CX + 4, PZ1 + 14), (112, 86), (40, 66), (CX, PZ0 + 12),
                              (CX - 6, 120), (CX + 6, 120), (60, 110)))
    return b, 0
