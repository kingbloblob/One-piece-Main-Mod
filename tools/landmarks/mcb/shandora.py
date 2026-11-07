"""Shandora v2, the lost City of Gold on Upper Yard (Skypiea), redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/shandora.md).

The island grows from 124 to 180 across and the extra room is spent on the city: ~34 ruined Shandian buildings drawn
as two-storey stone shells with gold friezes, broken wall tops, half-fallen upper floors, ladders and furnished
ground floors (old stores, libraries, workshops); small stepped shrines; a much bigger great temple (five tiers)
with a temple hall, treasure vault, shrine and scroll room inside; the sacrificial altar on the island's edge where
the Going Merry was left; Enel's golden ark Maxim on its building cradle in a clearing; more giant Upper Yard trees.
Giant Jack, the Upper Ruins cloud and the Golden Belfry with the bell are the v1 pieces in the middle. Floats at a
fixed height (canvas y 0 = world y 162). (v2)"""
import math
import random
import numpy as np
from canvas import B, AIR, stairs, slab
from mcb.kit import BigBuild, P, seed_of, st, furnish, set_if_air
from mcb.bridge import to_canvas
import shandora as OLD
from mcb import ark_maxim as AM
import interiors as I

SID = "shandora"
TITLE = OLD.TITLE
CUTS = [4, 12]
TILER = OLD.TILER
EDGE_REACH = 4
N = 240                                       # v3: Upper Yard grows to 240 (sky builds may reach 128)
CX, CZ = 120, 120
OLD.N, OLD.CX, OLD.CZ = N, CX, CZ           # the v1 Giant Jack / Upper Ruins / Belfry builders read these
# v3 (2026-10-30 audit: "a small floating island with a short vine"): Giant Jack becomes the hero, almost twice as
# tall and half again as thick, its Upper Ruins cloud and the Golden Belfry raised with it
OLD.TOPJ, OLD.U_Y, OLD.T_Y = 150, 64, 120
OLD.jack_R = lambda y: 15.0 - 8.0 * min(1.0, max(0, y) / OLD.TOPJ)
RUIN, RUIN_ST, RUIN_SL, RUIN_W = OLD.RUIN, OLD.RUIN_ST, OLD.RUIN_SL, OLD.RUIN_W
GOLDB, GOLDB_ST, MOSS = OLD.GOLDB, OLD.GOLDB_ST, OLD.MOSS
TX, TZ = CX - 44, CZ - 40                    # the great temple
AX, AZ = CX + 64, CZ + 26                    # the sacrificial altar (east edge)
KX, KZ = CX + 22, CZ + 54                    # Ark Maxim's cradle (south)


def island_r(a):
    return 110 + 5 * math.sin(3 * a) + 2.5 * math.sin(8 * a + 1)


def sky_tree(bb, x, z, h, r, rng):
    """A giant Upper Yard tree (v3): a thick tapering trunk with plank-buttress roots, boughs that fork out high up and
    end in flat, broken leaf pads, so the jungle canopy towers over the ruins as in the show."""
    from mcb import nature as NT
    seed = int(x * 13 + z * 7) & 0xFFFF
    ri = int(r * 2) + 8
    bb.fill_where(x - ri, -3, z - ri, x + ri, h, z + ri,
                  lambda X, Y, Z: np.hypot(X - x, Z - z) <= r * (1 - 0.4 * max(0, Y) / h) + 0.8 * NT.noise(X * 2 + Y, Z * 2, seed, 3) - 0.2,
                  "minecraft:jungle_wood")
    for k in range(6):                                            # buttress flanges
        a = k * math.pi / 3 + rng.uniform(-0.3, 0.3)
        L = r + rng.uniform(4, 8)
        for i in range(int(L) + 1):
            hh = int((L - i) * 1.6) - 1
            if hh < 0 or i < r - 0.5:
                continue
            bx, bz = int(round(x + i * math.cos(a))), int(round(z + i * math.sin(a)))
            bb.fill(bx, -2, bz, bx, hh, bz, "minecraft:jungle_log[axis=y]")
    for k in range(int(rng.integers(4, 7))):                     # boughs and their leaf pads
        a = rng.uniform(0, 2 * math.pi)
        ys = int(h * rng.uniform(0.62, 0.9))
        L = r * 2 + rng.uniform(5, 10)
        for i in range(int(L) + 1):
            t = i / L
            bx, by, bz = x + i * math.cos(a), ys + int(L * 0.5 * t), z + i * math.sin(a)
            bb.fill(int(bx), by, int(bz), int(bx), by + (1 if r > 2.5 else 0), int(bz), "minecraft:jungle_wood")
        cx_, cz_, cy_ = x + L * math.cos(a), z + L * math.sin(a), ys + int(L * 0.5) + 2
        R = rng.uniform(6, 10)
        bb.fill_where(int(cx_ - R - 1), int(cy_ - R / 2 - 1), int(cz_ - R - 1), int(cx_ + R + 1), int(cy_ + R / 2 + 1), int(cz_ + R + 1),
                      lambda X, Y, Z, cx_=cx_, cy_=cy_, cz_=cz_, R=R: (((X - cx_) ** 2 + (Z - cz_) ** 2) / R ** 2 + ((Y - cy_) / (R / 2)) ** 2
                                                                     + 0.3 * NT.noise(X + Y * 4, Z, seed + k, 2) <= 1) & (NT.noise(X * 2 - Y, Z * 2 + Y, seed + 9 + k, 2) < 0.7),
                      "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", only_empty=True)
    R = r * 2 + 5
    bb.fill_where(int(x - R - 1), h - 2, int(z - R - 1), int(x + R + 1), h + int(R / 2) + 2, int(z + R + 1),
                  lambda X, Y, Z: (((X - x) ** 2 + (Z - z) ** 2) / R ** 2 + ((Y - h - 1) / (R / 2)) ** 2 + 0.3 * NT.noise(X + Y * 4, Z, seed + 50, 2) <= 1),
                  "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", only_empty=True)


def ruin_module(seed, w, d, floors, tracker, audit):
    """A ruined Shandian building: stone walls with a gold frieze, broken uneven wall tops, doorway and window
    gaps, the ground floor furnished, the upper floor half fallen in, a ladder up."""
    rng = np.random.default_rng(seed)
    m = BigBuild(seed=seed, y_min=-2, y_max=30)
    H = floors * 5
    m.fill(0, -1, 0, w - 1, 0, d - 1, RUIN)
    m.fill(0, 1, 0, w - 1, H, d - 1, RUIN)
    m.fill(1, 1, 1, w - 2, H, d - 2, AIR)
    for x in range(w):                                 # broken tops
        for z in (0, d - 1):
            cut = int(H * 0.6 * abs(math.sin(x * 1.3 + z * 0.7 + seed % 7)))
            if cut:
                m.fill(x, H - cut + 1, z, x, H, z, AIR)
    for z in range(d):
        for x in (0, w - 1):
            cut = int(H * 0.6 * abs(math.sin(z * 1.1 + x * 0.5 + seed % 5)))
            if cut:
                m.fill(x, H - cut + 1, z, x, H, z, AIR)
    for (x1, z1, x2, z2) in ((0, 0, w - 1, 0), (0, d - 1, w - 1, d - 1), (0, 0, 0, d - 1), (w - 1, 0, w - 1, d - 1)):
        reg = m.get_region(x1, 4, z1, x2, 4, z2)
        for i, (x, z) in enumerate((xx, zz) for xx in range(x1, x2 + 1) for zz in range(z1, z2 + 1)):
            if reg.reshape(-1)[i] > 1 and (x + z) % 2 == 0:
                m.set(x, 4, z, GOLDB)
    for x in range(2, w - 2, 3):
        m.fill(x, 2, 0, x, 3, 0, AIR)
        m.fill(x, 2, d - 1, x, 3, d - 1, AIR)
    m.fill(w // 2, 1, d - 1, w // 2 + 1, 3, d - 1, AIR)                          # doorway (south)
    if floors > 1:
        m.fill(1, 5, 1, w - 2, 5, d - 2, RUIN)
        for _ in range(int(w * d * 0.25)):                                     # the fallen-in half
            x, z = int(rng.integers(1, w - 1)), int(rng.integers(1, d - 1))
            m.fill(x, 5, z, min(w - 2, x + 1), 5, min(d - 2, z + 1), AIR)
            if rng.random() < 0.5:
                m.set(x, 1, z, RUIN_SL + "[type=bottom,waterlogged=false]")
        m.fill(1, 1, 1, 1, 5, 1, "minecraft:ladder[facing=east]")
        m.fill(1, 6, 1, 1, 6, 1, AIR)
    kind = ["storage", "library", "workshop", "living"][int(rng.integers(4))]
    furnish(m, [(2, 2, w - 3, d - 3)], 1, 4, [kind], seed, tracker, doors=[(w // 2, d - 1)], wood="jungle", audit=audit)
    for _ in range(int(w * d * 0.08)):
        x, z = int(rng.integers(1, w - 1)), int(rng.integers(1, d - 1))
        set_if_air(m, x, 1, z, "minecraft:moss_carpet")
    if rng.random() < 0.5:
        set_if_air(m, 1, 1, d - 2, "minecraft:decorated_pot")
    return m


def shrine(bb, x, z, hw):
    """A small stepped shrine: three stepped tiers, gold band, a stair up the south face, a tiny gold top house."""
    for i in range(3):
        h = hw - i * 2
        bb.fill(x - h, 1 + i * 3, z - h, x + h, 3 + i * 3, z + h, RUIN)
        bb.fill(x - h, 3 + i * 3, z - h, x + h, 3 + i * 3, z - h, GOLDB)
        bb.fill(x - h, 3 + i * 3, z + h, x + h, 3 + i * 3, z + h, GOLDB)
    top = 10
    for k in range(9):
        bb.fill(x - 1, 1 + k, z + hw - k, x + 1, 1 + k, z + hw - k, st(RUIN_ST, "north"))
    bb.fill(x - 1, top, z - 1, x + 1, top + 2, z + 1, GOLDB)
    bb.set(x, top, z + 1, AIR)
    bb.set(x, top + 1, z + 1, AIR)
    bb.set(x, top + 3, z, "minecraft:gold_block")


def temple(bb, tracker, audit):
    """The great temple: five stepped tiers with gold friezes, a stair up the south face to the gold top shrine;
    inside the lower two tiers a pillared temple hall with a treasure vault, a shrine room and a scroll room."""
    tiers = (22, 18, 14, 10, 6)
    for i, hw in enumerate(tiers):
        y0 = i * 6
        bb.fill(TX - hw, y0 + 1, TZ - hw, TX + hw, y0 + 6, TZ + hw, RUIN)
        for k in range(-hw, hw + 1, 3):
            for (x, z) in ((TX + k, TZ - hw), (TX + k, TZ + hw), (TX - hw, TZ + k), (TX + hw, TZ + k)):
                bb.set(x, y0 + 5, z, GOLDB)
    bb.fill(TX - 20, 1, TZ - 20, TX + 20, 11, TZ + 20, AIR)                     # the hall (lower two tiers)
    for x in range(TX - 16, TX + 17, 8):
        for z in range(TZ - 16, TZ + 17, 8):
            if abs(x - TX) + abs(z - TZ) > 0:
                bb.fill(x, 1, z, x, 11, z, "minecraft:chiseled_stone_bricks")
                bb.set(x, 11, z, GOLDB)
                bb.set(x, 11, z + 1, "minecraft:lantern[hanging=true]")
    bb.fill(TX - 3, 0, TZ - 20, TX + 3, 0, TZ + 20, GOLDB)
    # side rooms along the back wall: vault, shrine and scroll room
    rooms, doors = P.bsp_rooms(bb, TX - 20, TZ - 20, TX + 20, TZ - 11, 1, 6, RUIN, min_room=7, seed=seed_of("tmp"),
                               max_room=14)
    bb.fill(TX - 20, 1, TZ - 10, TX + 20, 6, TZ - 10, RUIN)
    for r in rooms:
        dx = (r[0] + r[2]) // 2
        bb.fill(dx, 1, TZ - 10, dx + 1, 3, TZ - 10, AIR)
        doors.append((dx, TZ - 10))
    furnish(bb, rooms, 1, 6, ["storage", "library", "living"], seed_of("tmpf"), tracker, doors=doors, wood="jungle",
            audit=audit)
    bb.fill(TX - 20, 7, TZ - 20, TX + 20, 7, TZ - 11, RUIN)
    # front door and the grand stair to the top
    bb.fill(TX - 3, 1, TZ + 21, TX + 3, 6, TZ + 22, AIR)
    for i in range(30):
        z = TZ + 24 - i
        if z < TZ + 6:
            break
        bb.fill(TX - 3, 1 + i, z, TX + 3, 1 + i, z, st(RUIN_ST, "north"))
        bb.fill(TX - 3, 2 + i, z, TX + 3, 4 + i, z, AIR)
    bb.fill(TX - 3, 1, TZ + 21, TX + 3, 6, TZ + 22, AIR)
    bb.fill(TX - 3, 7, TZ + 19, TX + 3, 11, TZ + 22, RUIN)                      # roof of the doorway under the stair
    top = 31
    bb.fill(TX - 5, top, TZ - 5, TX + 5, top, TZ + 5, GOLDB)
    for (x, z) in ((TX - 4, TZ - 4), (TX + 4, TZ - 4), (TX - 4, TZ + 4), (TX + 4, TZ + 4)):
        bb.fill(x, top + 1, z, x, top + 6, z, GOLDB)
    bb.fill(TX - 5, top + 7, TZ - 5, TX + 5, top + 7, TZ + 5, GOLDB)
    bb.fill(TX - 3, top + 8, TZ - 3, TX + 3, top + 8, TZ + 3, GOLDB)
    bb.fill(TX - 1, top + 9, TZ - 1, TX + 1, top + 9, TZ + 1, GOLDB)
    bb.set(TX, top + 10, TZ, "minecraft:gold_block")


def altar(bb):
    """The sacrificial altar at the island's edge: a raised round stone platform, steps, a gold ring, four broken
    obelisks and the altar table."""
    bb.cylinder(AX, 0, AZ, 11, 2, RUIN)
    bb.cylinder(AX, 2, AZ, 9, 2, "minecraft:polished_andesite")
    bb.cylinder(AX, 2, AZ, 7, 2, GOLDB, hollow=True)
    for k in range(3):
        bb.fill(AX - 12 - k, 2 - k, AZ - 2, AX - 12 - k, 2 - k, AZ + 2, st(RUIN_ST, "east"))
    bb.fill(AX - 2, 3, AZ - 1, AX + 2, 3, AZ + 1, "minecraft:chiseled_stone_bricks")
    bb.fill(AX - 2, 4, AZ - 1, AX + 2, 4, AZ + 1, RUIN_SL + "[type=bottom,waterlogged=false]")
    for (dx, dz, h) in ((7, 7, 9), (-7, 7, 5), (7, -7, 7), (-7, -7, 10)):
        bb.fill(AX + dx, 3, AZ + dz, AX + dx, 3 + h, AZ + dz, RUIN)
        bb.set(AX + dx, 4 + h, AZ + dz, GOLDB)


def build():
    rnd = random.Random(16)
    b = B()
    # the floating island: cloud base under a ruined crust
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - CX, z - CZ)
            r = island_r(math.atan2(z - CZ, x - CX))
            if d > r:
                continue
            depth = int(4 + (r - d) * 0.3 + 2 * math.sin(x * 0.3) * math.cos(z * 0.27))
            for y in range(-depth, -2):
                b.set(x, y, z, OLD.CLOUD)
            for y in (-2, -1):
                b.set(x, y, z, "minecraft:dirt")
            b.set(x, 0, z, "minecraft:grass_block" if d > 12 and (x + z) % 7 else MOSS)
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(108, 113)
        b.sphere(round(CX + rr * math.cos(a)), rnd.randint(-6, 2), round(CZ + rr * math.sin(a)), rnd.uniform(2, 4.5),
                 OLD.PUFF, ry=1.5)
    # stone avenues with gold inlay, out to the edges
    r2 = random.Random(1616)
    for x in range(CX - 2, CX + 3):
        for z in range(10, N - 10):
            b.set(x, 0, z, GOLDB if (x == CX and z % 3 == 0) or (abs(x - CX) == 2 and z % 6 == 0) else (MOSS if r2.random() < 0.1 else RUIN))
    for z in range(CZ - 2, CZ + 3):
        for x in range(10, N - 10):
            b.set(x, 0, z, GOLDB if (z == CZ and x % 3 == 0) or (abs(z - CZ) == 2 and x % 6 == 0) else (MOSS if r2.random() < 0.1 else RUIN))
    # the new city pieces, drawn with the skill
    bb = BigBuild(seed=16, y_min=-4, y_max=110)
    tracker = P.PropTracker(16)
    audit = []
    temple(bb, tracker, audit)
    altar(bb)
    taken = [(TX - 26, TZ - 26, TX + 26, TZ + 30), (AX - 14, AZ - 14, AX + 14, AZ + 14), (KX - 28, KZ - 18, KX + 30, KZ + 18),
             (CX - 20, CZ - 20, CX + 20, CZ + 20), (CX - 4, 0, CX + 4, N), (0, CZ - 4, N, CZ + 4)]
    n = 0
    rng = np.random.default_rng(16)
    for _ in range(3000):
        w, d = int(rng.integers(8, 14)), int(rng.integers(7, 11))
        x0, z0 = int(rng.integers(10, N - 24)), int(rng.integers(10, N - 22))
        box = (x0 - 2, z0 - 2, x0 + w + 2, z0 + d + 2)
        if any(math.hypot(px - CX, pz - CZ) > island_r(math.atan2(pz - CZ, px - CX)) - 6
               for px in (box[0], box[2]) for pz in (box[1], box[3])):
            continue
        if any(box[0] <= t[2] and t[0] <= box[2] and box[1] <= t[3] and t[1] <= box[3] for t in taken):
            continue
        if n % 6 == 5 and w >= 11:
            shrine(bb, x0 + w // 2, z0 + d // 2, min(w, d) // 2 + 1)
        else:
            m = ruin_module(seed_of("ruin", n), w, d, 2 if rng.random() < 0.6 else 1, tracker, audit)
            bb.stamp(m, x0, 0, z0, rot=0, include_air=True)
        taken.append(box)
        n += 1
        if n >= 62:
            break
    print("ruins:", n)
    # v3: the giant Upper Yard trees, 3-4x the height of the ruins (Giant Jack is twice theirs again)
    trng = np.random.default_rng(1617)
    k = 0
    for _ in range(3000):
        a, rr = trng.uniform(0, 2 * math.pi), trng.uniform(26, 100)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if abs(x - CX) < 9 or abs(z - CZ) < 9 or rr > island_r(a) - 10:
            continue
        if any(t[0] - 4 <= x <= t[2] + 4 and t[1] - 4 <= z <= t[3] + 4 for t in taken):
            continue
        h = int(trng.integers(36, 58)); r = float(trng.uniform(2.4, 3.6))
        sky_tree(bb, x, z, h, r, trng)
        taken.append((x - 6, z - 6, x + 6, z + 6))
        k += 1
        if k >= 36:
            break
    print("giant trees:", k)
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    to_canvas(bb, b)
    for i in range(900):
        x, z = rnd.randint(8, N - 8), rnd.randint(8, N - 8)
        if b.get(x, 0, z) == "minecraft:grass_block" and b.get(x, 1, z) in (None, AIR):
            b.set(x, 1, z, rnd.choice(("minecraft:fern", "minecraft:short_grass", "onepiece:sky_lotus", "minecraft:large_fern[half=lower]")))
    # the temple's treasure vault and shrine (v1 interiors)
    I.furnish(b, TX - 19, 1, TZ + 4, TX - 5, TZ + 19, 8, "treasure", "royal")
    I.furnish(b, TX + 5, 1, TZ + 4, TX + 19, TZ + 19, 8, "chapel", "desert")
    # Enel's golden ark Maxim on its building cradle (the ship kit hull, mcb/ark_maxim.py)
    for x in range(KX - 22, KX + 23, 4):
        for z in (KZ - 3, KZ + 3):
            b.column(x, z, 1, 4, RUIN)
        b.column(x, KZ, 1, 3, RUIN)
        for z in (KZ - 5, KZ + 5):                                               # raking shores holding the hull upright
            b.column(x, z, 1, 6, "minecraft:stripped_birch_log[axis=y]")
    AM.place(b, KX - 25, 9, KZ)
    # the old city plaza where Giant Jack bursts out of the ruins
    for x in range(CX - 17, CX + 18):
        for z in range(CZ - 17, CZ + 18):
            d = math.hypot(x - CX, z - CZ)
            if d <= 16.5:
                ring = abs(d - 15) < 0.6 or abs(d - 11) < 0.6
                b.set(x, 0, z, GOLDB if ring and (x + z) % 2 else (MOSS if r2.random() < 0.12 else RUIN))
                for y in range(1, 3):
                    if b.get(x, y, z) not in (None, AIR):
                        b.set(x, y, z, AIR)
    for k in range(12):
        a = k * math.pi / 6 + 0.13
        x, z = round(CX + 15 * math.cos(a)), round(CZ + 15 * math.sin(a))
        if abs(x - CX) < 4 or abs(z - CZ) < 4:
            continue
        h = (8, 3, 6, 2, 8, 5, 7, 2, 8, 4, 6, 3)[k]
        for y in range(1, h + 1):
            b.set(x, y, z, RUIN if y % 3 else "minecraft:chiseled_stone_bricks")
        if h >= 6:
            b.set(x, h + 1, z, GOLDB)
            b.set(x, h + 2, z, slab(RUIN_SL))
        else:
            b.set(x, h + 1, z, slab(RUIN_SL))
    # Giant Jack, the Upper Ruins on its cloud and the Golden Belfry (v1)
    OLD.giant_jack(b, rnd)
    OLD.upper_ruins(b, rnd)
    BX, BZ, PY = OLD.golden_belfry(b, rnd)
    b.npc(BX, PY, BZ + 9, "enel", True)
    b.chest(TX - 12, 1, TZ + 10, "sky_treasure", "south")
    b.chest(BX + 7, PY + 1, BZ, "sky_treasure", "west")
    b.chest(AX, 3, AZ + 4, "medium", "north")
    b.guards("sky_priest", ((CX - 22, CZ + 7), (CX + 22, CZ - 7), (TX, TZ + 30), (CX + 7, CZ + 22), (CX - 9, CZ + 22),
                            (AX - 14, AZ), (KX, KZ - 12)))
    return b, 0
