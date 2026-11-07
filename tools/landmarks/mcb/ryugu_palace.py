"""Fish-Man Island and the Ryugu Palace, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/ryugu_palace.md).

A giant air bubble on the deep sea floor holding the island town, with the coral-and-pearl Ryugu Palace in its own
smaller bubble bulging out of the top. Inside the big bubble: the coral cliff of the palace hill, a canal ring with a
promenade, two rings of furnished shell houses (two floors, onion domes) in the Fish-Man District, the Mermaid Cafe,
Gyoverly Hills' market stalls, and the Sea Forest garden with Otohime's grave and the Poneglyph. On the hill the
four-tier palace: King Neptune's throne hall, the banquet hall and royal rooms on furnished floors, four shell-spire
towers, the pearl dome, and the Hard Shell Tower where Princess Shirahoshi was kept; a glass tube climbs from the
ring road to its gate. A coral reef and kelp ring the bubble outside. ~220 x 220. Sea floor = y 0. (v2)"""
import math
import numpy as np
from mcb.kit import BigBuild, P, AIR, seed_of, st, wing_floor, furnish, set_if_air, tier, cornice
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "ryugu_palace"
TITLE = "Fish-Man Island (Ryugu Palace)"
CUTS = [-56, -26, 0]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

BUBBLE = "onepiece:bubble_glass"
CORAL = "onepiece:coral_bricks"
CORAL_ST = "onepiece:coral_brick_stairs"
CORAL_W = "onepiece:coral_brick_wall"
PEARL = "onepiece:pearl_block"
PEARL_ST = "onepiece:pearl_stairs"
LAMP = "onepiece:bubble_lamp[hanging=false]"
HLAMP = "onepiece:bubble_lamp[hanging=true]"
C = 124                              # v3: site 248 (terrain none allows 128 reach) so a crater fits round the bubble
RYL = 16                             # v3: the bubble's lower half under the island
CRATER = 122                         # v3: crater radius round the bubble (the sea floor drops away)
RX, RY, BASE = 104, 70, -64         # island bubble: horizontal radius, height above its base, base y
HILL = -32                           # palace plateau top
PLAT = 38                            # plateau radius
PR, PCY = 40, -20                    # palace bubble radius and centre height
K = 24                               # palace half size
FH = 8
CAFE = 205                            # the Mermaid Cafe sits west-north-west
ROADS = (0, 180, 270)                 # radial streets (degrees; 90 = south is the Sea Forest)
G = BASE + 2                         # ground top in the town (people walk on G + 1)


def in_b(X, y, Z):
    ry = RY if y >= BASE else RYL
    return (((X - C) / RX) ** 2 + ((y - BASE) / ry) ** 2 + ((Z - C) / RX) ** 2 <= 1.0)


def in_p(X, y, Z):
    return (y > HILL) & ((X - C) ** 2 + (y - PCY) ** 2 + (Z - C) ** 2 <= PR * PR)


def ceiling(x, z):
    """Lowest y of bubble glass above (x, z) (the big bubble or the palace bubble, whichever is higher)."""
    t = 1 - ((x - C) / RX) ** 2 - ((z - C) / RX) ** 2
    yb = BASE + RY * math.sqrt(t) if t > 0 else BASE
    d2 = (x - C) ** 2 + (z - C) ** 2
    yp = PCY + math.sqrt(PR * PR - d2) if d2 < PR * PR else -999
    return max(yb, yp)


def dist(X, Z):
    return np.sqrt((X - C) ** 2 + (Z - C) ** 2)


def bubble(bb):
    lo, hi = C - RX - 1, C + RX + 1
    for y in range(BASE - RYL, PCY + PR + 2):
        def inside(X, yy, Z, y=y):
            return in_b(X, y, Z) | in_p(X, y, Z)

        def shell(X, yy, Z, y=y):
            core = (in_b(X - 1, y, Z) | in_p(X - 1, y, Z)) & (in_b(X + 1, y, Z) | in_p(X + 1, y, Z)) & \
                   (in_b(X, y, Z - 1) | in_p(X, y, Z - 1)) & (in_b(X, y, Z + 1) | in_p(X, y, Z + 1)) & \
                   (in_b(X, y + 1, Z) | in_p(X, y + 1, Z))
            return inside(X, yy, Z) & ~core
        bb.fill_where(lo, y, lo, hi, y, hi, inside, AIR)
        bb.fill_where(lo, y, lo, hi, y, hi, shell, BUBBLE)
    # the palace bubble's own skin where it rises inside the big bubble
    for y in range(HILL + 1, PCY + PR):
        def skin(X, yy, Z, y=y):
            d = np.sqrt((X - C) ** 2 + (y - PCY) ** 2 + (Z - C) ** 2)
            return in_b(X, y, Z) & (d <= PR) & (d > PR - 1.0)
        bb.fill_where(C - PR - 1, y, C - PR - 1, C + PR + 1, y, C + PR + 1, skin, BUBBLE)


def crater(bb):
    """v3 (2026-10-30 audit: from outside it read as a flat white dome). The sea floor round the bubble drops into a
    deep crater, so the whole bubble shows as a giant glass sphere sitting in a pit: its lower bowl wraps the island's
    rock root, the town glows inside. The crater wall slopes back up to the sea floor at the site edge."""
    lo, hi = C - CRATER - 1, C + CRATER + 1
    def floor_at(X, Z):
        d = dist(X, Z)
        t = np.clip((d - RX - 4) / (CRATER - RX - 4), 0, 1)
        return (BASE - RYL - 3) + ((0 - (BASE - RYL - 3)) * t ** 2.2).astype(int)
    bb.fill_where(lo, BASE - RYL - 6, lo, hi, 0, hi,
                  lambda X, y, Z: (dist(X, Z) <= CRATER) & (y > floor_at(X, Z)) & ~in_b(X, y, Z) & ~in_p(X, y, Z), "minecraft:water[level=0]")
    bb.fill_where(lo, BASE - RYL - 6, lo, hi, 0, hi,
                  lambda X, y, Z: (dist(X, Z) <= CRATER) & (y == floor_at(X, Z)) & ~in_b(X, y, Z), "minecraft:sand")
    bb.fill_where(lo, BASE - RYL - 6, lo, hi, 0, hi,
                  lambda X, y, Z: (dist(X, Z) <= CRATER) & (y < floor_at(X, Z)) & (y >= floor_at(X, Z) - 3) & ~in_b(X, y, Z)
                  & (NT.noise(X + y, Z - y, 2101, 4) > 0.5), "minecraft:sandstone")
    bb.fill_where(lo, BASE - RYL - 6, lo, hi, 0, hi,
                  lambda X, y, Z: (dist(X, Z) <= CRATER) & (y < floor_at(X, Z)) & (y >= floor_at(X, Z) - 3) & ~in_b(X, y, Z)
                  & (NT.noise(X + y, Z - y, 2101, 4) <= 0.5), "minecraft:stone")
    # the island's rock root inside the lower bowl, and sea lanterns ringing the bubble's foot in the crater
    for y in range(BASE - RYL + 1, BASE):
        bb.fill_where(lo, y, lo, hi, y, hi, lambda X, yy, Z, y=y: in_b(X, y, Z) & in_b(X - 1, y, Z) & in_b(X + 1, y, Z)
                      & in_b(X, y, Z - 1) & in_b(X, y, Z + 1) & in_b(X, y - 1, Z), "minecraft:sandstone")
    for s_ in range(0, 360, 9):
        a = math.radians(s_)
        x, z = round(C + (RX + 5) * math.cos(a)), round(C + (RX + 5) * math.sin(a))
        bb.set(x, int(floor_at(np.array([x]), np.array([z]))[0]), z, "minecraft:sea_lantern")


def eve_roots(bb, rng):
    """The roots of the Sun Tree Eve: they come down from the sunlit surface, pierce the bubble's crown and hang
    over the island carrying light, so the town is bright day down here. Thick wood with glowing froglight cores."""
    tips = [(C + 30 * math.cos(a), C + 30 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 7)[:-1] + 0.4]
    tips += [(C - 62, C + 10), (C + 58, C - 30), (C + 8, C + 64)]
    for k, (tx, tz) in enumerate(tips):
        ox, oz = C + (tx - C) * 0.35, C + (tz - C) * 0.35            # where the root enters at the crown
        top = 12                                                    # stays below the sea surface even on a shallow floor
        bot = int(ceiling(tx, tz)) - 18 if dist(np.array([tx]), np.array([tz]))[0] > PLAT + 4 else HILL + 40
        steps = top - bot
        for i in range(steps + 1):
            t = i / max(1, steps)
            x = ox + (tx - ox) * t ** 0.7 + 2.0 * math.sin(t * 5 + k)
            z = oz + (tz - oz) * t ** 0.7 + 2.0 * math.cos(t * 4 + k)
            y = top - i
            rr = 2.6 - 1.6 * t
            R_ = int(rr) + 1
            bb.fill_where(int(x) - R_, y, int(z) - R_, int(x) + R_, y, int(z) + R_,
                          lambda X, yy, Z, x=x, z=z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr, "minecraft:jungle_wood")
            if i % 4 == 0:
                bb.set(int(round(x)), y, int(round(z)), "minecraft:ochre_froglight" if k % 2 else "minecraft:shroomlight")
        # the glowing tip
        bb.fill_where(int(tx) - 3, bot - 3, int(tz) - 3, int(tx) + 3, bot + 1, int(tz) + 3,
                      lambda X, y, Z, tx=tx, tz=tz, bot=bot: (X - tx) ** 2 + (Z - tz) ** 2 + ((y - bot + 1) * 1.4) ** 2 <= 6, "minecraft:ochre_froglight")
    # the roots above the bubble: strands rising out of the crater toward the surface (it is the surface tree's root)
    return len(tips)


def daylight(bb):
    """Invisible light blocks on a grid in the bubble's air: Eve's sunlight. Only where there is air."""
    n = 0
    for y in range(G + 10, PCY + PR - 2, 12):
        for x in range(C - RX, C + RX + 1, 10):
            for z in range(C - RX, C + RX + 1, 10):
                if (in_b(np.array([x]), y, np.array([z]))[0] or in_p(np.array([x]), y, np.array([z]))[0]) and int(bb.get_region(x, y, z, x, y, z)[0, 0, 0]) in (0, 1):
                    if ceiling(x, z) > y + 3:
                        bb.set(x, y, z, "minecraft:light[level=15,waterlogged=false]"); n += 1
    return n


def ground(bb, rng):
    lo, hi = C - RX, C + RX
    X, Z = np.meshgrid(np.arange(lo, hi + 1), np.arange(lo, hi + 1), indexing="ij")
    d = np.sqrt((X - C) ** 2 + (Z - C) ** 2)
    top = np.where(d < PLAT, HILL, np.maximum(G, HILL - ((d - PLAT) * 4).astype(int)))
    inside = ((X - C) / RX) ** 2 + ((Z - C) / RX) ** 2 <= 0.995
    for y in range(BASE, HILL + 1):
        def f(XX, yy, ZZ, y=y):
            m = inside & (y < top)
            return m
        bb.fill_where(lo, y, lo, hi, y, hi, f, "minecraft:sandstone")
        bb.fill_where(lo, y, lo, hi, y, hi,
                      lambda XX, yy, ZZ, y=y: inside & (y < top) & (d >= PLAT) & (y >= top - 3) & ((XX * 3 + y + ZZ) % 7 != 0),
                      CORAL)
        bb.fill_where(lo, y, lo, hi, y, hi,
                      lambda XX, yy, ZZ, y=y: inside & (y == top), CORAL)
    surf = np.where(d > 46, "w", np.where(d >= PLAT, "c", np.where(d > 30, "s", "p")))
    for code, blk in (("w", "minecraft:calcite"), ("s", "minecraft:smooth_sandstone"), ("p", PEARL)):
        for y in sorted(set(top[surf == code].tolist())):
            bb.fill_where(lo, y, lo, hi, y, hi, lambda XX, yy, ZZ, y=y, code=code: inside & (top == y) & (surf == code), blk)
    # the island has no daylight down here: sea lanterns set into the ground on a staggered grid light the town
    # and the palace hill (houses and streets placed later simply cover the ones they stand on)
    lit = inside & (((X + 3 * (Z // 6)) % 6 == 0) & (Z % 6 == 0)) & ((d < PLAT - 2) | (d > 47))
    for y in sorted(set(top[lit].tolist())):
        bb.fill_where(lo, y, lo, hi, y, hi, lambda XX, yy, ZZ, y=y: lit & (top == y), "minecraft:sea_lantern")
    # the canal ring and promenade round the palace hill
    ring = lambda a, b: (lambda XX, yy, ZZ: (d >= a) & (d <= b))
    bb.fill_where(lo, G - 2, lo, hi, G - 2, hi, ring(50, 56), "minecraft:light_blue_terracotta")
    bb.fill_where(lo, G - 1, lo, hi, G, hi, ring(50, 56), "minecraft:water[level=0]")
    bb.fill_where(lo, G, lo, hi, G, hi, lambda XX, yy, ZZ: ((d > 56) & (d <= 58)) | ((d >= 48) & (d < 50)),
                  "minecraft:smooth_sandstone")
    bb.fill_where(lo, G + 1, lo, hi, G + 1, hi, lambda XX, yy, ZZ: ((d > 57) & (d <= 58)) | ((d >= 48) & (d < 49)), CORAL_W)
    for s in range(0, 360, 12):
        a = math.radians(s)
        for r in (48.5, 57.5):
            bb.set(round(C + r * math.cos(a)), G + 2, round(C + r * math.sin(a)), LAMP)
    for s in (0, 90, 180, 270):                                   # bridges over the canal
        a = math.radians(s)
        for r in range(47, 60):
            x, z = round(C + r * math.cos(a)), round(C + r * math.sin(a))
            for w in (-2, -1, 0, 1, 2):
                xx, zz = (x, z + w) if s in (0, 180) else (x + w, z)
                bb.set(xx, G, zz, "minecraft:smooth_sandstone")
                bb.fill(xx, G + 1, zz, xx, G + 3, zz, AIR)


def shell_house(seed, r, floors, mat, tracker, audit):
    """A round shell house: coral or pearl walls, two floors, an onion dome, windows, a door, furnished."""
    m = BigBuild(seed=seed, y_min=-2, y_max=40)
    h = floors * 5
    m.fill(-r, -2, -r, r, 0, r, "minecraft:smooth_sandstone")
    m.cylinder(0, 1, 0, r, h, mat)
    m.cylinder(0, 1, 0, r - 1, h, AIR)
    for f in range(1, floors):
        m.cylinder(0, f * 5, 0, r - 1, f * 5, "minecraft:birch_planks")
    top = h + 1
    for k in range(int(r * 2.2)):
        t = k / (r * 2.2)
        rr = r * (1.0 + 0.1 * math.sin(t / 0.45 * math.pi / 2)) if t < 0.45 else r * 1.1 * math.cos((t - 0.45) / 0.55 * math.pi / 2) ** 1.3
        if rr < 0.5:
            break
        m.cylinder(0, top + k, 0, max(1, int(round(rr))), top + k, mat)
    m.set(0, top + int(r * 2.2), 0, PEARL)
    for f in range(floors):
        y = f * 5 + 3
        for (dx, dz) in ((r, 0), (-r, 0), (0, -r)):
            m.fill(dx, y, dz, dx, y + 1, dz, "minecraft:light_blue_stained_glass_pane")
    m.fill(-1, 1, r, 1, 3, r, AIR)
    m.set(0, 4, r + 1, LAMP)
    q = int((r - 1) / math.sqrt(2))
    for f in range(floors):
        rooms = [(-q, -q, q, q)]
        furnish(m, rooms, f * 5 + 1, 4, [["kitchen", "living", "bedroom", "library"][(seed + f) % 4]], seed + f, tracker,
                doors=[(0, r)], wood="birch", audit=audit)
        m.set(0, f * 5 + 4, 0, HLAMP)
    if floors > 1:
        m.fill(-r + 1, 1, 0, -r + 1, (floors - 1) * 5, 0, "minecraft:ladder[facing=east]")
    return m, top + int(r * 2.2)


def district(bb, rng, tracker, audit):
    mats = [PEARL, CORAL, "minecraft:prismarine", "minecraft:pink_terracotta", "minecraft:white_terracotta",
            "minecraft:yellow_terracotta"]
    y = G
    n = 0
    for (rr, rlo, rhi, fl) in ((70, 5, 6, 3), (84, 4, 5, 2), (96, 4, 4, 1)):
        a = 0.0
        while a < 2 * math.pi:
            deg = math.degrees(a)
            r = int(rng.integers(rlo, rhi + 1))
            road = any(abs((deg - k + 180) % 360 - 180) < math.degrees((r + 4) / rr) for k in ROADS)
            if 55 <= deg <= 125 or abs(deg - CAFE) <= 13 or road:   # leave the Sea Forest, Mermaid Cafe and the roads
                a += 0.03
                continue
            floors = fl
            x, z = round(C + rr * math.cos(a)), round(C + rr * math.sin(a))
            mod, height = shell_house(seed_of("rh", n), r, floors, mats[n % len(mats)], tracker, audit)
            ok = all(ceiling(x + dx, z + dz) > y + height + 3 for dx in (-r - 1, 0, r + 1) for dz in (-r - 1, 0, r + 1))
            while not ok and floors > 1:
                floors -= 1
                mod, height = shell_house(seed_of("rh", n, floors), r, floors, mats[n % len(mats)], tracker, audit)
                ok = all(ceiling(x + dx, z + dz) > y + height + 3 for dx in (-r - 1, 0, r + 1) for dz in (-r - 1, 0, r + 1))
            if ok:
                # doors face the palace: rot turns the module's south (+z) door toward the centre
                dirx, dirz = C - x, C - z
                rot = (0 if dirz > 0 else 2) if abs(dirz) >= abs(dirx) else (3 if dirx > 0 else 1)
                bb.stamp(mod, x, y, z, rot=rot, include_air=True)
                n += 1
            a += (2.2 * r + 3 + rng.uniform(0, 2)) / rr
    # Gyoverly Hills market stalls along the promenade
    for s in range(15, 360, 30):
        if 60 <= s <= 120:
            continue
        a = math.radians(s)
        x, z = round(C + 61 * math.cos(a)), round(C + 61 * math.sin(a))
        for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bb.fill(x + dx, y + 1, z + dz, x + dx, y + 3, z + dz, "minecraft:birch_fence")
        col = ["cyan", "light_blue", "pink", "yellow"][s // 30 % 4]
        bb.fill(x - 2, y + 4, z - 2, x + 2, y + 4, z + 2, f"minecraft:{col}_wool")
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up]")
    return n


def streets(bb, rng):
    """Radial streets from the canal bridges out to the bubble wall, bubble lamps along them, coral trees and
    planters in the gaps between the shell houses."""
    for k in ROADS:
        a = math.radians(k)
        for r in range(58, 101):
            x, z = round(C + r * math.cos(a)), round(C + r * math.sin(a))
            for w in (-2, -1, 0, 1, 2):
                xx, zz = (x, z + w) if k in (0, 180) else (x + w, z)
                bb.set(xx, G, zz, "minecraft:smooth_sandstone" if abs(w) < 2 else PEARL)
            if r % 6 == 0:
                for w in (-3, 3):
                    xx, zz = (x, z + w) if k in (0, 180) else (x + w, z)
                    set_if_air(bb, xx, G + 1, zz, "minecraft:prismarine_wall")
                    set_if_air(bb, xx, G + 2, zz, "minecraft:prismarine_wall")
                    set_if_air(bb, xx, G + 3, zz, LAMP)
    trees = 0
    for _ in range(900):
        t, r = rng.uniform(0, 2 * math.pi), rng.uniform(61, 100)
        x, z = round(C + r * math.cos(t)), round(C + r * math.sin(t))
        reg = bb.get_region(x - 2, G + 1, z - 2, x + 2, G + 7, z + 2)
        if (reg > 1).any() or bb.get_region(x, G, z, x, G, z)[0, 0, 0] <= 1 or ceiling(x, z) < G + 12:
            continue
        if rng.random() < 0.45:
            h = int(rng.integers(3, 6))
            bb.fill(x, G + 1, z, x, G + h, z, "minecraft:prismarine_wall")
            kind = ("brain", "tube", "bubble", "fire", "horn")[int(rng.integers(5))]
            bb.fill_where(x - 2, G + h, z - 2, x + 2, G + h + 2, z + 2,
                          lambda X, yy, Z: (X - x) ** 2 + (Z - z) ** 2 + ((yy - G - h - 1) * 1.6) ** 2 <= 5,
                          f"minecraft:{kind}_coral_block")
            if h > 3:
                bb.set(x, G + h - 1, z, "minecraft:sea_lantern")
            trees += 1
        else:
            bb.set(x, G + 1, z, "minecraft:flower_pot")
            set_if_air(bb, x + 1, G + 1, z, ["minecraft:short_grass", "minecraft:sea_pickle", "minecraft:azure_bluet",
                                            "minecraft:blue_orchid"][int(rng.integers(4))])
    return trees


def mermaid_cafe(bb, tracker, audit):
    """The Mermaid Cafe: a big pink shell with a pool inside, west-north-west in the district."""
    x, z, y = round(C + 74 * math.cos(math.radians(CAFE))), round(C + 74 * math.sin(math.radians(CAFE))), G
    bb.cylinder(x, y, z, 10, y + 8, "minecraft:pink_terracotta")
    bb.cylinder(x, y + 1, z, 9, y + 8, AIR)
    bb.dome(x, y + 9, z, 10, "minecraft:pink_terracotta", hollow=True)
    bb.dome(x, y + 9, z, 9, AIR, hollow=False)
    bb.cylinder(x, y, z, 9, y, PEARL)
    bb.cylinder(x, y, z, 4, y, "minecraft:water[level=0]")
    bb.cylinder(x, y - 1, z, 4, y - 1, "minecraft:prismarine")
    for s in range(0, 360, 30):
        a = math.radians(s)
        px, pz = round(x + 7 * math.cos(a)), round(z + 7 * math.sin(a))
        bb.set(px, y + 1, pz, "minecraft:cherry_stairs[facing=north,half=bottom]")
        bb.set(round(x + 9.5 * math.cos(a)), y + 4, round(z + 9.5 * math.sin(a)), "minecraft:pink_stained_glass_pane")
    bb.set(x, y + 12, z, HLAMP)
    bb.fill(x + 10, y + 1, z - 1, x + 10, y + 3, z + 1, AIR)
    for i in range(6):
        bb.set(x + 11 + i, y + 6 - i // 2, z, "minecraft:pink_wool")


def sea_forest(bb, rng):
    SX, SZ = C, C + 82
    y = G + 1
    for _ in range(220):
        x, z = SX + int(rng.integers(-18, 19)), SZ + int(rng.integers(-12, 13))
        if (x - SX) ** 2 + ((z - SZ) * 1.4) ** 2 > 18 ** 2:
            continue
        bb.set(x, y - 1, z, "minecraft:moss_block")
        r = rng.random()
        if r < 0.15:
            set_if_air(bb, x, y, z, "minecraft:azalea")
        elif r < 0.4:
            set_if_air(bb, x, y, z, "minecraft:moss_carpet")
    for (dx, dz) in ((-12, -4), (12, -4), (-8, 6), (9, 6), (0, -9)):
        x, z = SX + dx, SZ + dz
        if ceiling(x, z) < y + 14:
            continue
        bb.fill(x, y, z, x, y + 6, z, "minecraft:mangrove_log[axis=y]")
        bb.fill_where(x - 3, y + 6, z - 3, x + 3, y + 8, z + 3,
                      lambda X, yy, Z: (X - x) ** 2 + (Z - z) ** 2 + ((yy - y - 7) * 1.5) ** 2 <= 9,
                      "minecraft:mangrove_leaves[distance=7,persistent=true,waterlogged=false]")
    bb.fill(SX - 1, y - 1, SZ - 1, SX + 1, y - 1, SZ + 1, "minecraft:mossy_stone_bricks")
    bb.set(SX, y, SZ, "onepiece:poneglyph")
    bb.set(SX, y + 1, SZ, "onepiece:poneglyph")
    bb.fill(SX + 4, y, SZ + 3, SX + 6, y, SZ + 3, "minecraft:white_concrete")          # Otohime's grave
    bb.set(SX + 5, y + 1, SZ + 3, "minecraft:quartz_pillar[axis=y]")
    bb.set(SX + 5, y + 2, SZ + 3, LAMP)
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        bb.set(SX + dx, y, SZ + dz, LAMP)


def palace(bb, tracker, audit):
    Y0 = HILL
    bb.fill(C - K - 2, Y0, C - K - 2, C + K + 2, Y0, C + K + 2, PEARL)
    tops = []
    for f in range(4):
        e = K - f * 3
        y0 = Y0 + f * FH
        top = tier(bb, C - e, C - e, C + e, C + e, y0, 1, FH, CORAL, "minecraft:light_blue_stained_glass_pane",
                   PEARL_ST, pilaster="minecraft:prismarine_bricks",
                   band=PEARL, plate=PEARL, every=3, pil_every=4, win_h=3)
        cornice(bb, C - e, C - e, C + e, C + e, top, PEARL_ST)
        tops.append((y0, e))
    # floors: throne hall (open), banquet and royal rooms (furnished), Shirahoshi's floor
    y0, e = tops[0]
    bb.fill(C - 4, y0 + 1, C - e + 1, C + 4, y0 + 2, C - e + 4, "minecraft:gold_block")
    bb.fill(C - 4, y0 + 3, C - e + 1, C + 4, y0 + 6, C - e + 1, PEARL)
    for x in (C - 4, C + 4):
        bb.fill(x, y0 + 3, C - e + 2, x, y0 + 4, C - e + 4, "minecraft:gold_block")
    bb.fill(C - 1, y0, C - e + 5, C + 1, y0, C + e - 1, "minecraft:cyan_wool")
    for z in range(C - e + 4, C + e - 1, 5):
        for x in (C - 10, C + 10):
            bb.fill(x, y0 + 1, z, x, y0 + FH - 1, z, "minecraft:prismarine_bricks")
            bb.set(x, y0 + FH - 1, z + 2, HLAMP)
    for (f, kinds, cw) in ((1, ["living", "library", "kitchen"], 3), (2, ["bedroom", "library"], 3), (3, ["bedroom", "living"], 3)):
        y0, e = tops[f]
        wing_floor(bb, C - e + 1, C - e + 1, C + e - 1, C + e - 1, y0 + 1, FH - 1, CORAL, seed_of("ryu", f), tracker,
                   kinds, corridor="x", cw=cw, audit=audit, max_room=10, wood="birch",
                   keep=[(C + e - 10, C - 4, C + e - 1, C + 4)], carpet=(None, "minecraft:cyan_carpet"))
    # stairs up through the floors on the east side
    for f in range(3):
        y0, e = tops[f]
        x = C + tops[f + 1][1] - 6
        for i in range(FH):
            bb.fill(x, y0 + 1 + i, C - 3 + i, x + 2, y0 + 1 + i, C - 3 + i, st(PEARL_ST, "south"))
            bb.fill(x, y0 + 2 + i, C - 3 + i, x + 2, y0 + 4 + i, C - 3 + i, AIR)
    # the front gate (south)
    y0, e = tops[0]
    bb.fill(C - 3, y0 + 1, C + e, C + 3, y0 + 5, C + e, AIR)
    P.arched_opening(bb, "x", C, y0 + 1, C + e, 7, 6, depth=1, trim=PEARL)
    # the pearl dome and four shell-spire towers
    yt, et = tops[3]
    bb.dome(C, yt + FH + 1, C, et - 1, PEARL, hollow=True)
    bb.set(C, yt + FH + et + 1, C, "minecraft:sea_lantern")
    for (tx, tz) in ((C - K, C - K), (C + K, C - K), (C - K, C + K), (C + K, C + K)):
        bb.cylinder(tx, Y0, tz, 4, Y0 + 22, CORAL)
        bb.cylinder(tx, Y0 + 1, tz, 3, Y0 + 21, AIR)
        bb.fill(tx, Y0 + 1, tz - 3, tx, Y0 + 21, tz - 3, "minecraft:ladder[facing=south]")
        bb.cylinder(tx, Y0 + 22, tz, 5, Y0 + 22, PEARL)
        n = 12
        while n > 4 and ceiling(tx, tz) < Y0 + 23 + n + 3:
            n -= 1
        for i in range(n):
            r = 4.0 * (1 - i / (n + 2))
            a = math.radians(i * 50)
            bb.cylinder(tx, Y0 + 23 + i, tz, max(1, int(round(r))), Y0 + 23 + i,
                        "minecraft:prismarine_bricks" if i % 2 else "minecraft:dark_prismarine")
            bb.set(round(tx + r * math.cos(a)), Y0 + 23 + i, round(tz + r * math.sin(a)), PEARL)
        for y in range(Y0 + 4, Y0 + 20, 5):
            for (dx, dz) in ((4, 0), (-4, 0), (0, 4)):
                bb.set(tx + dx, y, tz + dz, "minecraft:pink_stained_glass_pane")
        dx_ = 1 if tx < C else -1
        dz_ = 1 if tz < C else -1
        bb.fill(tx + dx_ * 3, Y0 + 1, tz + dz_ * 3, tx + dx_ * 4, Y0 + 3, tz + dz_ * 4, AIR)
    # the Hard Shell Tower: Shirahoshi's tall tower beside the palace (west), her big room at the top
    hx, hz = C - K - 9, C - 6
    htop = int(min(ceiling(hx, hz) - 8, Y0 + 44))
    bb.cylinder(hx, Y0, hz, 6, htop, PEARL)
    bb.cylinder(hx, Y0 + 1, hz, 5, htop - 1, AIR)
    room = htop - 10
    bb.cylinder(hx, room, hz, 5, room, "minecraft:pink_wool")
    bb.fill(hx, Y0 + 1, hz - 5, hx, room + 1, hz - 5, "minecraft:ladder[facing=south]")
    bb.fill(hx - 2, room + 1, hz + 1, hx + 2, room + 1, hz + 3, "minecraft:pink_wool")      # her giant bed
    bb.fill(hx - 2, room + 2, hz + 3, hx + 2, room + 2, hz + 3, "minecraft:white_wool")
    for (dx, dz) in ((-4, 0), (4, 0)):
        bb.set(hx + dx, room + 1, hz + dz, "minecraft:flower_pot")
    bb.set(hx + 3, room + 1, hz - 3, "minecraft:bookshelf")
    bb.set(hx - 3, room + 1, hz - 3, "minecraft:chest[facing=south]")
    bb.set(hx, htop - 1, hz, HLAMP)
    for y in range(Y0 + 6, htop - 1, 6):
        for (dx, dz) in ((6, 0), (-6, 0), (0, 6), (0, -6)):
            bb.fill(hx + dx, y, hz + dz, hx + dx, y + 1, hz + dz, "minecraft:pink_stained_glass_pane")
    bb.dome(hx, htop, hz, 6, "minecraft:dark_prismarine", hollow=True)
    bb.fill(hx + 6, Y0 + 1, hz - 1, hx + 6, Y0 + 3, hz + 1, AIR)
    # the connection tube from the ring road up to the palace forecourt (south)
    Z0 = C + K + 3
    for z in range(Z0, C + PLAT + (HILL - G) + 2):
        yf = HILL if z < C + PLAT else max(G, HILL - (z - (C + PLAT)) - 1)
        for x in range(C - 5, C + 6):
            for y in range(yf - 1, yf + 7):
                dx, dy = x - C, y - (yf + 2)
                rr = math.hypot(dx / 5.0, dy / 4.5)
                if rr <= 0.8:
                    bb.set(x, y, z, AIR)
                elif rr <= 1.0 and y >= yf:
                    set_if_air(bb, x, y, z, BUBBLE)
            if abs(x - C) <= 3:
                bb.set(x, yf, z, CORAL if abs(x - C) == 3 else "minecraft:smooth_sandstone")
        if z % 8 == 0 and yf > G + 2:
            for x in (C - 3, C + 3):
                for yy in range(yf - 1, G, -1):
                    set_if_air(bb, x, yy, z, CORAL_W)
        if z % 4 == 0:
            bb.set(C - 3, yf + 1, z, LAMP)
            bb.set(C + 3, yf + 1, z, LAMP)


def reef(bb, rng):
    R0 = RX * math.sqrt(1 - (BASE / RY) ** 2)                # where the dome meets the sea floor
    corals = ("tube", "brain", "bubble", "fire", "horn")
    for _ in range(5000):
        a, r = rng.uniform(0, 2 * math.pi), CRATER + 1 + rng.exponential(5)
        x, z = round(C + r * math.cos(a)), round(C + r * math.sin(a))
        if not (0 <= x < 2 * C and 0 <= z < 2 * C):
            continue
        k = corals[int(rng.integers(5))]
        q = rng.random()
        if q < 0.35:
            bb.set(x, 0, z, f"minecraft:{k}_coral_block")
            bb.set(x, 1, z, f"minecraft:{k}_coral[waterlogged=true]")
        elif q < 0.6:
            bb.set(x, 1, z, f"minecraft:{k}_coral_fan[waterlogged=true]")
        elif q < 0.8:
            h = int(rng.integers(3, 10))
            bb.fill(x, 1, z, x, h, z, "minecraft:kelp_plant")
        else:
            bb.set(x, 1, z, "minecraft:seagrass")


def design():
    bb = BigBuild(seed=21, y_min=BASE - RYL - 8, y_max=40)
    tracker = P.PropTracker(21)
    audit = []
    rng = np.random.default_rng(21)
    bubble(bb)
    crater(bb)
    ground(bb, rng)
    n = district(bb, rng, tracker, audit)
    print("shell houses:", n)
    print("coral trees:", streets(bb, rng))
    mermaid_cafe(bb, tracker, audit)
    sea_forest(bb, rng)
    palace(bb, tracker, audit)
    reef(bb, rng)
    print("eve roots:", eve_roots(bb, rng), "lights:", daylight(bb))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.chest(C + 6, HILL + 1, C - K + 2, "treasure", "south")
    b.npc(C, HILL + 1, C + 4, "jinbe")
    b.guards("fishman", ((C - 6, C + K + 4), (C + 6, C + K + 4)), y=HILL + 1)
    b.guards("fishman", ((C - 60, C + 3), (C + 60, C + 3), (C + 3, C - 60)), y=G + 1)
    return b, 0
