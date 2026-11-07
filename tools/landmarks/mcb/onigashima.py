"""Onigashima v2: Kaido's Skull Dome with new interiors drawn with the Minecraft Builder skill
(dossier: mcb/dossiers/onigashima.md).

The island already fills the 220-block site cap and its shell (the skull face, horns, rooftop, Live Floor, castle
tiers) was matched to the show in the landmark review, so v2 keeps that shell from the older module and spends the
extra size on what is inside: Kaido's castle storeys split into furnished rooms (the Headliners' barracks, the
officers' rooms, the library and tea rooms, the shogun's chambers), every Live Floor building furnished on both
floors with a ladder between them, the ground hall lined with Gifter bunk rooms and an armory, and the watch pagodas
furnished. Uses the skill's bsp_rooms / furnish_room with one PropTracker and audit_props on every room. (v2)

v3 (2026-10-30, audit: "the castle on top is too small, and the island sits on grass instead of the sea"): Kaido's
castle now stands ON the skull's rooftop as in the show: a four-storey tenshu 41 wide on a stone plinth, white plaster
and dark boards, tiled eaves with turned-up tips, chidori gables, a gold-finned top roof, rising ~45 above the roof.
The small gatehouse it replaces is gone (the ladder still comes up behind it). The island is lifted 3 blocks out of a
round patch of sea: a rocky coast at ~84 from the centre, the old outer crags left standing as sea stacks, a wooden
pier at the torii path. (Interiors from v2 are kept.)

v4 (2026-10-30, ryan: "darker, on a floating island with an upside-down jagged cone as the bottom", three reference
pictures): the whole island hangs in the sky as when Kaido lifts it. The old ground disc, crags, trees and pier are
dropped; the island top sits G=78 above a round patch of sea, with a jagged rock cone hanging under it to a point just
above the water. The skull is dark (smooth basalt skin, tuff ridges, glowing shroomlight eyes and nose), the horns
black, the rooftop castle black-walled. Round the skull: a packed festival town of ~70 dark timber and red lacquer
Wano houses with paper lanterns, a torii avenue with lantern strings and stalls, a pond with an arched red bridge and
a red pavilion, a giant katana stuck in the ground, sakura and snowy pines. Way up: a dock on the sea, a wooden stair
tower, and a lantern-lit stair cut into the side of the cone that comes out at the front of the island."""
import math
import numpy as np
from mcb.kit import BigBuild, P, AIR, seed_of, furnish, set_if_air
from mcb.bridge import to_canvas
from mcb import nature as NT
import onigashima as OLD
import random
from mcb import flower_capital as FC
from mcb.kit import place_house

SID = "onigashima"
TITLE = OLD.TITLE
CUTS = [78 + 2, 78 + 26]
TILER = OLD.TILER
EDGE_REACH = 2
SOFT_EDGES = False
LIFT = 3                                  # the island stands this far out of the sea
CX, SZ = OLD.CX, OLD.SZ
WALL = "minecraft:white_concrete"
LAQ = OLD.LAQ
TIERS = ((22, SZ + 11, SZ + 33, 25, 12), (18, SZ + 14, SZ + 32, 38, 9), (14, SZ + 17, SZ + 31, 48, 8),
         (11, SZ + 19, SZ + 30, 57, 7), (8, SZ + 21, SZ + 29, 65, 6), (6, SZ + 22, SZ + 28, 72, 6))
LADDER = (CX, SZ + 24)


def castle_rooms(bb, tracker, audit):
    kinds = {1: ["bedroom", "storage", "bedroom"], 3: ["library", "living"], 4: ["bedroom", "living"]}
    lx, lz = LADDER
    for i, ks in kinds.items():
        hw, z0, z1, y0, h = TIERS[i]
        x1, x2, za, zb = CX - hw + 1, CX + hw - 1, z0 + 1, z1 - 1
        bb.fill(x1, y0, za, x2, y0 + h - 2, zb, AIR)
        rooms, doors = P.bsp_rooms(bb, x1, za, x2, zb, y0, h - 1, WALL, min_room=5, seed=seed_of("oni", i),
                                   max_room=10)
        furnish(bb, rooms, y0, h - 1, ks, seed_of("onif", i), tracker, doors=doors + [(lx, lz - 1)], wood="dark_oak",
                audit=audit)
        for r in rooms:
            bb.set((r[0] + r[2]) // 2, y0 + h - 2, (r[1] + r[3]) // 2, OLD.HLANT)
        # the climbing ladder runs through every storey: keep its shaft and the cell in front of it clear
        bb.fill(lx - 1, y0 - 1, lz - 1, lx + 1, y0 + h - 2, lz - 1, AIR)
        bb.fill(lx, y0 - 1, lz, lx, y0 + h - 1, lz, "minecraft:ladder[facing=north]")
        bb.fill(lx, y0 - 1, lz + 1, lx, y0 + h - 1, lz + 1, "minecraft:polished_blackstone_bricks")
        bb.fill(lx - 1, y0 - 1, lz - 1, lx + 1, y0 - 1, lz - 1, "onepiece:tatami")


def live_floor(bb, tracker, audit):
    """Each two-storey building lining the Live Floor gets a furnished shop below, a room above, a ladder between."""
    i = 0
    for sx in (-1, 1):
        for z0 in (SZ - 22, SZ - 13, SZ - 4):
            xf, xb = CX + sx * 30, CX + sx * 37
            lo, hi = min(xf, xb), max(xf, xb)
            r = (lo + 1, z0 + 1, hi - 1, z0 + 6)
            for (y, h, k) in ((25, 4, ["kitchen", "storage"][i % 2]), (31, 5, ["bedroom", "living"][i % 2])):
                furnish(bb, [r], y, h, [k], seed_of("live", i, y), tracker, doors=[(xf, z0 + 3)], wood="dark_oak",
                        audit=audit)
            lx = hi - 1 if sx > 0 else lo + 1
            bb.fill(lx, 25, z0 + 1, lx, 31, z0 + 1, "minecraft:ladder[facing=south]")
            bb.set(lx, 30, z0 + 1, "minecraft:ladder[facing=south]")
            i += 1


def ground_hall(bb, tracker, audit):
    """Gifter bunk rooms and an armory along the back of the ground hall, behind the war beast pens."""
    z1, z2 = SZ + 16, SZ + 23
    for (x1, x2, nm, ks) in ((CX - 21, CX - 6, "w", ["bedroom", "bedroom", "storage"]),
                             (CX + 6, CX + 21, "e", ["workshop", "bedroom", "storage"])):
        ok = all(OLD.in_skull(x, 1, z) and OLD.in_skull(x, 9, z) for x in (x1 - 1, x2 + 1) for z in (z1 - 1, z2 + 1))
        if not ok:
            continue
        bb.fill(x1 - 1, 1, z1 - 1, x2 + 1, 8, z2 + 1, "minecraft:polished_blackstone_bricks")
        bb.fill(x1, 1, z1, x2, 7, z2, AIR)
        bb.fill(x1 - 1, 9, z1 - 1, x2 + 1, 9, z2 + 1, "minecraft:dark_oak_planks")
        rooms, doors = P.bsp_rooms(bb, x1, z1, x2, z2, 1, 7, "minecraft:dark_oak_planks", min_room=5,
                                   seed=seed_of("gh", nm), max_room=9)
        door_x = (x1 + x2) // 2
        bb.fill(door_x - 1, 1, z1 - 1, door_x + 1, 3, z1 - 1, AIR)
        furnish(bb, rooms, 1, 7, ks, seed_of("ghf", nm), tracker, doors=doors + [(door_x, z1 - 1)], wood="dark_oak",
                audit=audit)
        for r in rooms:
            bb.set((r[0] + r[2]) // 2, 7, (r[1] + r[3]) // 2, OLD.HLANT)


def design():
    bb = BigBuild(seed=1, y_min=-8, y_max=140)
    tracker = P.PropTracker(1)
    audit = []
    castle_rooms(bb, tracker, audit)
    live_floor(bb, tracker, audit)
    ground_hall(bb, tracker, audit)
    return bb, audit


def rooftop_castle(b):
    """Kaido's castle on the crown of the skull: stone plinth, four storeys, eaves, gables, top hip roof."""
    T, CXo = OLD.TOP, CX
    z0, z1 = SZ + 1, SZ + 21
    # clear the old gatehouse
    b.box(CXo - 9, T + 1, SZ + 14, CXo + 9, T + 18, SZ + 27, AIR)
    # the plinth: sloped stone walls (ishigaki), filled down to the skull wherever it overhangs
    for x in range(CXo - 23, CXo + 24):
        for z in range(z0 - 3, z1 + 4):
            inset = max(0, max(abs(x - CXo) - 20, z0 - z, z - z1))
            if inset > 3:
                continue
            top = T + 4 - inset
            for y in range(top, T - 30, -1):
                if y <= T and OLD.in_skull(x, y, z) and b.get(x, y, z) not in (None, AIR):
                    break
                b.set(x, y, z, OLD.PBB if (x + y + z) % 5 else "minecraft:blackstone")
    b.box(CXo - 20, T + 4, z0, CXo + 20, T + 4, z1, "minecraft:polished_blackstone")
    tiers = ((20, z0, z1, T + 5, 10), (16, z0 + 2, z1 - 2, T + 16, 9), (12, z0 + 4, z1 - 4, T + 26, 8),
             (8, z0 + 5, z1 - 5, T + 35, 7))
    for i, (hw, za, zb, y0, h) in enumerate(tiers):
        OLD.tier(b, CXo - hw, CXo + hw, za, zb, y0, h, floor=None if i == 0 else "onepiece:tatami")
        top = y0 + h - 1
        if i < len(tiers) - 1:
            b.box(CXo - hw, top + 1, za, CXo + hw, top + 1, zb, OLD.ROOF)
            OLD.eave(b, CXo - hw, CXo + hw, za, zb, top, depth=3)
        if i in (0, 2):
            OLD.chidori(b, CXo, za, top, 5 if i == 0 else 3)
        # an inside stair: a ladder up the back wall through every storey
        b.box(CXo - 1, y0, zb - 1, CXo + 1, y0 + h - 1, zb - 1, AIR)
        for y in range(y0 - 1, y0 + h):
            b.set(CXo, y, zb - 1, OLD.ladder("north"))
        for (dx, dz) in ((-hw + 3, za + 3), (hw - 3, za + 3), (-hw + 3, zb - 3), (hw - 3, zb - 3)):
            b.set(CXo + dx, y0 + h - 2, dz, OLD.HLANT)
    hw, za, zb, y0, h = tiers[-1]
    b.hip_roof(CXo - hw, za, CXo + hw, zb, y0 + h, OLD.ROOF_ST, OLD.ROOF, overhang=3)
    ridge = y0 + h + (zb - za + 6) // 2 + 1
    for sx in (-1, 1):
        b.set(CXo + sx * 4, ridge, (za + zb) // 2, "minecraft:gold_block")
        b.set(CXo + sx * 4, ridge + 1, (za + zb) // 2, "minecraft:gold_block")
    # the great door on the front, gold-studded leaves, steps up the plinth, lanterns
    for x in range(CXo - 3, CXo + 4):
        for y in range(T + 5, T + 12):
            b.set(x, y, z0, AIR)
    for sx in (-1, 1):
        for y in range(T + 5, T + 12):
            b.set(CXo + sx * 4, y, z0 - 1, OLD.LAQ)
        for k in range(1, 3):
            for y in range(T + 5, T + 12):
                b.set(CXo + sx * (4 + k), y, z0 - 1, "minecraft:gold_block" if (y - T) % 3 == 0 else "minecraft:dark_oak_planks")
    for x in range(CXo - 4, CXo + 5):
        b.set(x, T + 12, z0 - 1, OLD.LAQ)
    for k in range(4):
        for x in range(CXo - 3, CXo + 4):
            b.set(x, T + 1 + k, z0 - 4 + k, OLD.stairs("minecraft:polished_blackstone_brick_stairs", "south"))
            b.set(x, T + k, z0 - 4 + k, OLD.PBB) if k else None
    for x in (CXo - 6, CXo + 6):
        b.set(x, T + 5, z0 - 2, OLD.LANT)
    # the rooftop ladder comes up behind the castle: keep its head clear
    b.box(OLD.CX - 1, T + 1, SZ + 23, OLD.CX + 1, T + 4, SZ + 26, AIR)


# ---------------------------------------------------------------------------------------------------------------- v4
# Floating Onigashima: the whole island hangs in the sky over the sea, as when Kaido lifts it (ryan's references).
G = 78                                   # the island top (canvas ground y 0) is lifted this far above the sea
DEPTH = 54                               # how far the upside-down rock cone hangs below the island top
SEA_R = 106
SKIN = "minecraft:smooth_basalt"         # the dark skull: one clean skin colour, lighter tuff on the bony ridges
RIDGE = "minecraft:tuff"
TEETH = "minecraft:polished_tuff"
GLOW = "minecraft:shroomlight"
CONE_ROCK = ("minecraft:deepslate", "minecraft:cobbled_deepslate", "minecraft:blackstone", "minecraft:basalt[axis=y]",
             "minecraft:cobbled_deepslate", "minecraft:smooth_basalt", "minecraft:deepslate", "minecraft:blackstone")
DARKEN = {"minecraft:stone": "minecraft:deepslate", "minecraft:andesite": "minecraft:tuff",
          "minecraft:cobblestone": "minecraft:cobbled_deepslate", "minecraft:diorite": "minecraft:tuff"}
A_UP = -math.pi / 2                      # where the cliff stair comes up: the front of the island (-z)


def coast(a):
    return 93 + 3 * np.sin(3 * a + 1) + 1.5 * np.sin(5 * a) + 1 * np.sin(11 * a + 0.3)


def _grids():
    X, Z = np.meshgrid(np.arange(221), np.arange(221), indexing="ij")
    return X, Z


def island_maps():
    """inside (blocks inside the rim, <0 outside) and the cone depth under every column of the island."""
    X, Z = _grids()
    dx, dz = X - CX, Z - OLD.CZ
    a = np.arctan2(dz, dx)
    d = np.hypot(dx, dz)
    R = coast(a) * (0.97 + 0.06 * NT.noise(X, Z, 911, 9))
    inside = R - d
    s = np.clip(d / R, 0, 1)
    ridge = 1 + 0.14 * np.sin(7 * a + 4 * s) + 0.08 * np.sin(13 * a + 1 + 3 * s)
    n = NT.fbm(X, Z, 77, cell=18)
    u = 7 + (DEPTH - 7) * (1 - s) ** 1.15 * ridge + 8 * (n - 0.5)
    rng = np.random.default_rng(1234)
    # jagged points hanging from the underside: many small ones, longer toward the middle, a cluster at the tip
    spikes = []
    for i in range(300):
        r = math.sqrt(rng.uniform(0.02, 0.97)) * 88
        t = rng.uniform(-math.pi, math.pi)
        if abs((t - A_UP + math.pi) % (2 * math.pi) - math.pi) < 0.9 and r > 20:
            continue                                         # keep the cliff stair's side clean
        L = rng.uniform(5, 14) + 12 * (1 - r / 80) ** 2
        spikes.append((CX + r * math.cos(t), OLD.CZ + r * math.sin(t), rng.uniform(2.0, 4.5), L))
    for k in range(6):
        t = k / 6 * 2 * math.pi + 0.4
        spikes.append((CX + 7 * math.cos(t), OLD.CZ + 7 * math.sin(t), 5.0, rng.uniform(10, 18)))
    spikes.append((CX + 1, OLD.CZ - 1, 7.0, 26))
    add = np.zeros_like(u)
    for (sx, sz, r0, L) in spikes:
        dd = np.hypot(X - sx, Z - sz)
        add = np.maximum(add, np.where(dd < r0, L * np.clip(1 - dd / r0, 0, 1) ** 1.5, 0))
    u = u + add
    u = np.minimum(np.where(inside > 0, u, 0), G - 6)
    return inside, u.astype(int), a, d


def cone_mat(x, y, z, nb):
    """Rock of the hanging cone: strata that wobble with smooth noise, a mix per band (no modulo patterns)."""
    band = (y + int(nb[x, z] * 9)) // 6
    h = (x * 73856093 ^ z * 19349663 ^ band * 83492791) & 0xffff
    v = (nb[(x + 37) % 221, (z + 11) % 221] * 5 + band * 3 + (h % 3)) % len(CONE_ROCK)
    return CONE_ROCK[int(v)]


def strip_old_outside(b):
    """Drop the old ground disc, crags, trees, pagodas, storehouse, torii path and pier: v4 builds its own island.
    Keeps the skull, its rock skirt, the horns and everything inside or on top of it."""
    gate_z = int(OLD.front_z(0, 10))
    for p, s in list(b.blocks.items()):
        x, y, z = p
        ds = math.hypot(x - CX, z - SZ)
        if y <= 0:
            if not (OLD.in_skull(x, 1, z) or OLD.in_skull(x, 0, z)):
                del b.blocks[p]; b.nbt.pop(p, None)
            continue
        if y >= 30:
            continue
        skirt = s in OLD.ROCKS and not OLD.in_skull(x, y, z)          # the old rock skirt: the town climbs the skull now
        if ds > 60 or skirt or (z < gate_z - 3 and not OLD.in_skull(x, y, z)):
            del b.blocks[p]; b.nbt.pop(p, None)
    b.entities = [e for e in b.entities if not (e[2] <= 1 and e[3] < 40)]


def darken(b):
    """The skull, its horns and its rock skirt in the dark night palette, with glowing eyes and nose."""
    sk = {OLD.BONE, OLD.CALC, "minecraft:smooth_quartz", "minecraft:diorite", "minecraft:smooth_sandstone"}
    for p, s in list(b.blocks.items()):
        x, y, z = p
        if y < 0 or abs(x - CX) > 80 or abs(z - SZ) > 60:
            continue
        if s in sk:
            inside = OLD.in_skull(x, y, z)
            if y > 60 and not inside and abs(x - CX) >= 26:          # horns: black at the root, dark grey tips
                t = (y - 66) / 46
                b.blocks[p] = "minecraft:polished_blackstone" if t < 0.35 else "minecraft:blackstone" if t < 0.75 else "minecraft:deepslate_tiles"
            elif s == OLD.TOOTH and y < 18:
                b.blocks[p] = TEETH
            elif s == OLD.CALC and not inside:
                b.blocks[p] = RIDGE
            else:
                b.blocks[p] = SKIN
        elif s == OLD.PLAST and y >= OLD.TOP:                         # Kaido's castle on the crown: black walls
            b.blocks[p] = "minecraft:black_terracotta"
        elif s in DARKEN and y <= 30 and not OLD.in_skull(x, y, z):
            b.blocks[p] = DARKEN[s]
    # eye sockets: black ring, glowing core deep inside (the skull's fiery eyes at night)
    EY, ER = 57, 13
    for ex in (CX - 20, CX + 20):
        for x in range(ex - ER, ex + ER + 1):
            for y in range(EY - ER, EY + ER + 1):
                rr = math.hypot(x - ex, (y - EY) * 1.15) / ER
                if rr > 0.78:
                    continue
                fz = OLD.front_z(x - CX, y)
                if fz > 1e8:
                    continue
                deep = 2 + int(round(3.5 * math.sqrt(1 - rr * rr)))
                b.set(x, y, fz + deep, GLOW)
    for p, s in list(b.blocks.items()):                             # the nose's back wall glows too
        x, y, z = p
        if s == OLD.DARK and 25 <= y <= 45 and abs(x - CX) <= 10 and z < SZ - 20:
            if (x, y, z - 1) in b.blocks and b.blocks[(x, y, z - 1)] == AIR:
                b.blocks[p] = GLOW


GROUND = (("minecraft:podzol", 0.34), ("minecraft:coarse_dirt", 0.20), ("minecraft:rooted_dirt", 0.12),
          ("minecraft:snow_block", 0.10), ("minecraft:blackstone", 0.10), ("minecraft:packed_mud", 0.14))


def _pick(recipe, v):
    acc = 0
    for s, w in recipe:
        acc += w
        if v <= acc:
            return s
    return recipe[-1][0]


def island(b, inside, u):
    """The island top (dark soil and snow in smooth patches) and the upside-down jagged rock cone under it."""
    X, Z = _grids()
    nb = NT.noise(X, Z, 515, 7)
    ng = NT.fbm(X, Z, 303, cell=16)
    for x in range(221):
        for z in range(221):
            if inside[x, z] <= 0:
                continue
            if OLD.in_skull(x, 1, z) or OLD.in_skull(x, 0, z):
                top = 0                                             # the skull's own floor stays
                for y in range(-1, -u[x, z] - 1, -1):
                    b.set(x, y, z, cone_mat(x, y, z, nb))
                continue
            e = inside[x, z]
            g = _pick(GROUND, float(ng[x, z]))
            if e < 3:
                g = "minecraft:blackstone" if nb[x, z] < 0.5 else "minecraft:cobbled_deepslate"
            if b.get(x, 0, z) is None:
                b.set(x, 0, z, g)
            for y in (-1, -2):
                b.set(x, y, z, "minecraft:dirt" if e >= 3 else "minecraft:deepslate")
            for y in range(-3, -u[x, z] - 1, -1):
                b.set(x, y, z, cone_mat(x, y, z, nb))
    # hanging roots and short dripstone teeth under the rim
    rng = np.random.default_rng(42)
    for x in range(221):
        for z in range(221):
            if inside[x, z] <= 0 or rng.random() > 0.035:
                continue
            y = -u[x, z] - 1
            if b.get(x, y + 1, z) is None or b.get(x, y, z) is not None:
                continue
            if inside[x, z] < 14:
                b.set(x, y, z, "minecraft:hanging_roots[waterlogged=false]")
            else:
                b.set(x, y, z, "minecraft:pointed_dripstone[thickness=frustum,vertical_direction=down,waterlogged=false]")
                b.set(x, y - 1, z, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")


def rim_crags(b, inside):
    """Dark rock crags along the rim, as in the manga panel, with a gap where the cliff stair arrives."""
    rng = random.Random(7)
    for i in range(30):
        a = i / 30 * 2 * math.pi + rng.uniform(-0.06, 0.06)
        if abs((a - A_UP + math.pi) % (2 * math.pi) - math.pi) < 0.22:
            continue
        r = float(coast(a)) - rng.uniform(4, 8)
        x, z = round(CX + r * math.cos(a)), round(OLD.CZ + r * math.sin(a))
        if math.hypot(x - CX, z - SZ) < 64:
            continue
        hgt = rng.randint(7, 22)
        rad0 = rng.uniform(3.0, 5.0)
        for y in range(1, hgt):
            rad = (1 - y / hgt) * rad0 + 0.6
            b.cyl(x + (y // 7) % 2, z, rad, y, y, rng.choice(("minecraft:blackstone", "minecraft:deepslate", "minecraft:basalt[axis=y]",
                                                                "minecraft:tuff", "minecraft:cobbled_deepslate")))
        for y in range(-4, 1):
            b.cyl(x, z, rad0 + 1, y, y, "minecraft:deepslate")


def _facing(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


STAIR_BOTTOM = -60                       # the cliff stair's lowest landing (18 above the sea)


def cliff_stair(b, inside, u):
    """A lantern-lit stair cut into the side of the hanging cone, from a sea dock up to the front of the island."""
    def r_surface(a, y):
        r_ok = 0
        for r in range(0, 110):
            x, z = int(round(CX + r * math.cos(a))), int(round(OLD.CZ + r * math.sin(a)))
            if not (0 <= x < 221 and 0 <= z < 221) or inside[x, z] <= 0:
                break
            if u[x, z] >= 1 - y:
                r_ok = r
        return r_ok
    a, y, step = A_UP, 0.0, 0
    cells, rails = {}, []
    order = []
    while y >= STAIR_BOTTOM:
        yf = int(math.floor(y))
        rs = r_surface(a, yf)
        rc = max(6, rs - 2)
        for k in (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5):
            for t in (-0.5, 0.0, 0.5):
                r = rc + k
                x = int(round(CX + r * math.cos(a) - t * math.sin(a)))
                z = int(round(OLD.CZ + r * math.sin(a) + t * math.cos(a)))
                cells[(x, z)] = max(cells.get((x, z), -999), yf)
        rx, rz = int(round(CX + (rc + 2.5) * math.cos(a))), int(round(OLD.CZ + (rc + 2.5) * math.sin(a)))
        rails.append((rx, rz, yf, step))
        order.append((CX + rc * math.cos(a), OLD.CZ + rc * math.sin(a), yf, a, rc))
        a -= 0.9 / rc
        y -= 1 / 3
        step += 1
    for (x, z), yf in cells.items():
        b.set(x, yf - 1, z, "minecraft:deepslate")
        b.set(x, yf, z, "minecraft:polished_blackstone_bricks" if (x * 3 + z) % 7 else "minecraft:cracked_polished_blackstone_bricks")
        for yy in range(yf + 1, yf + 5):
            b.set(x, yy, z, AIR)
    for (x, z), yf in cells.items():                                 # steps: a stair where the next cell up starts
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if cells.get((x - dx, z - dz)) == yf - 1:
                b.set(x, yf, z, f"minecraft:polished_blackstone_brick_stairs[facing={_facing(dx, dz)},half=bottom,shape=straight,waterlogged=false]")
                break
    for (x, z, yf, i) in rails:
        if (x, z) in cells:
            continue
        b.set(x, yf, z, "minecraft:polished_blackstone_bricks")
        b.set(x, yf - 1, z, "minecraft:deepslate")
        b.set(x, yf + 1, z, "minecraft:polished_blackstone_brick_wall" if i % 9 == 0 else "minecraft:dark_oak_fence")
        if i % 9 == 0:
            b.set(x, yf + 2, z, "onepiece:paper_lantern[hanging=false]")
        for yy in range(yf + 2 + (i % 9 == 0), yf + 5):
            if b.get(x, yy, z) not in (None, AIR):
                b.set(x, yy, z, AIR)
    # the bottom: a landing, a wooden stair tower down to a dock on the sea
    bx, bz, yb, ab, rcb = order[-1]
    ox, oz = math.cos(ab), math.sin(ab)
    tx, tz = int(round(bx + ox * 6)), int(round(bz + oz * 6))
    sea = -G
    for k in range(0, 7):                                            # landing bridge from the stair to the tower
        px, pz = int(round(bx + ox * k)), int(round(bz + oz * k))
        for (qx, qz) in ((px, pz), (px + 1, pz), (px, pz + 1)):
            if (qx, qz) not in cells:
                b.set(qx, yb, qz, "minecraft:dark_oak_planks")
                for yy in range(yb + 1, yb + 4):
                    if b.get(qx, yy, qz) not in (None, AIR):
                        b.set(qx, yy, qz, AIR)
    for y in range(sea - 13, yb + 5):                               # no hanging rock spike through the tower
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                q = b.get(tx + dx, y, tz + dz)
                if q is not None and (q in CONE_ROCK or "dripstone" in q or "roots" in q):
                    b.set(tx + dx, y, tz + dz, AIR)
    ring = ((-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0))
    top = yb
    for y in range(sea - 12, top + 4):
        b.set(tx, y, tz, "minecraft:dark_oak_log[axis=y]")
    n = top - (sea + 1)
    for i in range(n):
        y = sea + 1 + i
        cx_, cz_ = ring[i % 8]
        nx_, nz_ = ring[(i + 1) % 8]
        for yy in range(y + 1, y + 4):
            if b.get(tx + cx_, yy, tz + cz_) is None or b.get(tx + cx_, yy, tz + cz_) != OLD.LAQ:
                b.set(tx + cx_, yy, tz + cz_, AIR)
        b.set(tx + cx_, y, tz + cz_, f"minecraft:dark_oak_stairs[facing={_facing(nx_ - cx_, nz_ - cz_)},half=bottom,shape=straight,waterlogged=false]")
    for y in (sea + 1, top):                                         # floors at the dock and at the top
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if max(abs(dx), abs(dz)) == 2:
                    b.set(tx + dx, y, tz + dz, "minecraft:dark_oak_planks")
        if y == top:
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if (dx, dz) != (0, 0) and (dx, dz) != ring[(n - 1) % 8]:
                        b.set(tx + dx, y, tz + dz, "minecraft:dark_oak_planks")
    for dx in (-2, 2):                                               # corner posts and a railing frame
        for dz in (-2, 2):
            for y in range(sea - 12, top + 4):
                b.set(tx + dx, y, tz + dz, "minecraft:dark_oak_log[axis=y]")
    for y in range(sea + 2, top + 4):
        for dx in range(-1, 2):
            for dz in (-2, 2):
                if (y - sea) % 5 == 0:
                    b.set(tx + dx, y, tz + dz, "minecraft:dark_oak_planks")
                    b.set(tx + dz, y, tz + dx, "minecraft:dark_oak_planks")
    for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):              # open doorways at the dock and the top
        for y in (sea + 2, sea + 3, top + 1, top + 2):
            b.set(tx + dx, y, tz + dz, AIR)
    b.box(tx - 3, top + 4, tz - 3, tx + 3, top + 4, tz + 3, OLD.ROOF)
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        b.set(tx + dx, top + 3, tz + dz, OLD.HLANT)
    # the dock out over the water
    for k in range(3, 16):
        px, pz = int(round(tx + ox * k)), int(round(tz + oz * k))
        for j in (-2, -1, 0, 1, 2):
            qx, qz = int(round(px - oz * j)), int(round(pz + ox * j))
            b.set(qx, sea + 1, qz, "minecraft:spruce_planks")
        if k % 4 == 3:
            for j in (-3, 3):
                qx, qz = int(round(px - oz * j)), int(round(pz + ox * j))
                for y in range(sea - 12, sea + 2):
                    b.set(qx, y, qz, "minecraft:spruce_log[axis=y]")
                b.set(qx, sea + 2, qz, "onepiece:paper_lantern[hanging=false]")
    return (tx, tz)


POND = (CX - 38, 56, 13)                 # x, z, radius of the festival pond
SWORD = (CX + 36, 60)


def _occupied(b):
    occ = np.zeros((221, 221), bool)
    for (x, y, z), s in b.blocks.items():
        if 1 <= y <= 40 and s != AIR and 0 <= x < 221 and 0 <= z < 221:
            occ[x, z] = True
    o2 = occ.copy()
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            o2 |= np.roll(np.roll(occ, dx, 0), dz, 1)
    return o2


def reserved(x, z):
    px, pz, pr = POND
    if math.hypot(x - px, z - pz) < pr + 4:
        return True
    if math.hypot(x - SWORD[0], z - SWORD[1]) < 8:
        return True
    if abs(x - CX) <= 7 and z < 86:
        return True                                           # the torii avenue up to the gate
    ux, uz = CX, OLD.CZ - float(coast(A_UP))
    if math.hypot(x - ux, z - uz) < 16:
        return True                                           # where the cliff stair arrives
    return False


def house(seed, w, d, floors, tracker, style):
    """A Wano town house (flower_capital.machiya) in the night palette: dark timber, red lacquer or old plaster."""
    m, top, au = FC.machiya(seed, w, d, floors, tracker, FC.KINDS[seed % len(FC.KINDS)], red=(style == "red"),
                            roof=FC.TILE)
    remap = {"dark": {"minecraft:white_concrete": "minecraft:stripped_dark_oak_wood", "minecraft:white_terracotta": "minecraft:dark_oak_planks",
                      "minecraft:calcite": "minecraft:stripped_dark_oak_wood", "minecraft:stripped_spruce_wood": "minecraft:spruce_planks"},
             "plaster": {"minecraft:white_concrete": "minecraft:white_terracotta", "minecraft:calcite": "minecraft:white_terracotta"},
             "red": {}}[style]
    m.names = [remap.get(n, n) if n else n for n in m.names]
    m.ids = {n: i for i, n in enumerate(m.names) if i}
    dx = w // 2
    for lx in (dx - 2, dx + 2):
        if 0 < lx < w - 1:
            m.set(lx, 4, d, "onepiece:paper_lantern[hanging=true]")
    return m, au


def town(b, inside, tracker, audit):
    """The festival town round the skull: 60-90 packed Wano houses with lanterns, doors toward the skull or avenue."""
    bb = BigBuild(seed=5, y_min=-6, y_max=60)
    occ = _occupied(b)
    rng = np.random.default_rng(2026)
    cand = [(x, z) for x in range(4, 217, 2) for z in range(4, 217, 2) if inside[x, z] > 9]
    rng.shuffle(cand)
    cand.sort(key=lambda c: math.hypot(c[0] - CX, c[1] - SZ) + float(rng.uniform(0, 22)))
    taken = np.zeros((221, 221), bool)
    k = 0
    for (x0, z0) in cand:
        w, d = int(rng.integers(6, 10)), int(rng.integers(7, 10))
        if rng.random() < 0.5:
            w, d = d, w
        x1, z1 = x0 + w - 1, z0 + d - 1
        if x1 > 216 or z1 > 216:
            continue
        box = (slice(x0 - 1, x1 + 2), slice(z0 - 1, z1 + 2))
        if occ[box].any() or taken[box].any() or (inside[box] < 7).any():
            continue
        if any(reserved(x, z) for x in (x0, x1, (x0 + x1) // 2) for z in (z0, z1, (z0 + z1) // 2)):
            continue
        cx_, cz_ = (x0 + x1) / 2, (z0 + z1) / 2
        if abs(cx_ - CX) < 24 and cz_ < 86:
            vx, vz = CX - cx_, 0.0                            # face the avenue
        else:
            vx, vz = CX - cx_, SZ - cz_
        rot = (3 if vx > 0 else 1) if abs(vx) > abs(vz) else (0 if vz > 0 else 2)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        style = ("dark", "dark", "red", "plaster", "dark", "plaster")[k % 6]
        floors = 2 if rng.random() < 0.75 else (3 if math.hypot(cx_ - CX, cz_ - SZ) < 75 else 1)
        mod, au = house(int(seed_of("onih", k)) % 100000, mw, md, floors, tracker, style)
        audit += au
        place_house(bb, mod, mw, md, x0, 0, z0, rot)
        taken[x0 - 1:x1 + 2, z0 - 1:z1 + 2] = True
        k += 1
    print("festival houses:", k)
    to_canvas(bb, b)
    return taken


def avenue(b):
    """Torii avenue from the cliff stair to the skull's gate: red gates, lantern strings, festival stalls."""
    gate_z = int(OLD.front_z(0, 10))
    z_start = int(OLD.CZ - float(coast(A_UP))) + 4
    for z in range(z_start, gate_z):
        for x in range(CX - 4, CX + 5):
            b.set(x, 0, z, "minecraft:stone_bricks" if (x * 5 + z * 3) % 11 else "minecraft:cracked_stone_bricks")
            for y in range(1, 4):
                if b.get(x, y, z) not in (None, AIR) and not OLD.in_skull(x, y, z):
                    b.set(x, y, z, AIR)
    for z in range(z_start + 6, gate_z - 6, 12):
        OLD.torii(b, CX, z, w=6, h=11)
    for z in range(z_start + 12, gate_z - 4, 12):                 # lantern strings between the torii
        for x in (CX - 6, CX + 6):
            for y in range(1, 8):
                b.set(x, y, z, "minecraft:dark_oak_fence")
        for x in range(CX - 5, CX + 6):
            b.set(x, 8, z, "minecraft:dark_oak_fence")
            if x % 2 == 0:
                b.set(x, 7, z, "onepiece:paper_lantern[hanging=true]")
    rng = random.Random(3)
    for z in range(z_start + 3, gate_z - 4, 6):                   # stalls under red and white awnings
        for sx in (-1, 1):
            if rng.random() < 0.3:
                continue
            x = CX + sx * 9
            col = rng.choice(("red", "white", "purple", "orange"))
            for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                for y in (1, 2):
                    b.set(x + dx, y, z + dz, "minecraft:spruce_fence")
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    b.set(x + dx, 3, z + dz, f"minecraft:{col}_wool" if (dx + dz) % 2 == 0 else "minecraft:white_wool")
            b.set(x, 1, z, rng.choice(("minecraft:barrel[facing=up,open=false]", "onepiece:sake_barrel[axis=y]", "minecraft:smoker[facing=north,lit=false]")))
            b.set(x - sx, 1, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
            b.set(x, 2, z, "onepiece:paper_lantern[hanging=false]")


def pond(b):
    """The festival pond: dark water, lily pads, an arched red bridge to a red pavilion on its islet."""
    px, pz, pr = POND
    rng = random.Random(9)
    for x in range(px - pr - 2, px + pr + 3):
        for z in range(pz - pr - 2, pz + pr + 3):
            a = math.atan2(z - pz, x - px)
            r = pr * (1 + 0.12 * math.sin(3 * a + 1) + 0.06 * math.sin(5 * a))
            d = math.hypot(x - px, z - pz)
            if d > r + 1.5:
                continue
            if d > r:
                b.set(x, 0, z, "minecraft:mossy_cobblestone" if rng.random() < 0.5 else "minecraft:stone_bricks")
                continue
            if d < 4.5:
                b.set(x, 0, z, "minecraft:stone_bricks")             # the islet
                continue
            for y in range(1, 4):
                b.set(x, y, z, AIR)
            b.set(x, 0, z, "minecraft:water"); b.set(x, -1, z, "minecraft:water")
            b.set(x, -2, z, "minecraft:mud")
            if rng.random() < 0.08:
                b.set(x, 1, z, "minecraft:lily_pad")
    # the pavilion
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for y in range(1, 6):
            b.set(px + dx, y, pz + dz, "minecraft:red_concrete")
    b.hip_roof(px - 3, pz - 3, px + 3, pz + 3, 6, OLD.ROOF_ST, OLD.ROOF, overhang=2)
    b.hip_roof(px - 1, pz - 1, px + 1, pz + 1, 9, OLD.ROOF_ST, OLD.ROOF, overhang=1)
    for (dx, dz) in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        b.set(px + dx, 5, pz + dz, OLD.HLANT)
    b.set(px, 1, pz, "onepiece:sake_barrel[axis=y]")
    # arched red bridge from the east shore to the islet
    for x in range(px + 4, px + pr + 3):
        t = (x - (px + 4)) / (pr - 1)
        y = 1 + int(round(2 * math.sin(math.pi * min(1, t))))
        for z in (pz - 1, pz, pz + 1):
            b.set(x, y, z, "minecraft:crimson_planks")
        b.set(x, y + 1, pz - 2, "minecraft:crimson_fence"); b.set(x, y + 1, pz + 2, "minecraft:crimson_fence")
        b.set(x, y, pz - 2, "minecraft:crimson_planks"); b.set(x, y, pz + 2, "minecraft:crimson_planks")
    for (qx, qz) in ((px + 4, pz - 2), (px + pr + 2, pz - 2), (px + 4, pz + 2), (px + pr + 2, pz + 2)):
        b.set(qx, 3, qz, "onepiece:paper_lantern[hanging=false]")


def sword(b):
    """A giant katana stuck in the ground beside the skull (from ryan's festival picture)."""
    sx, sz = SWORD
    dv = np.array([0.22, 1.0, -0.12]); dv = dv / np.linalg.norm(dv)
    side = np.array([1.0, 0, 0]) - dv * dv[0]; side /= np.linalg.norm(side)
    flat = np.cross(dv, side)
    base = np.array([sx, -6.0, sz])
    for i in range(0, 60):
        c = base + dv * i
        if i < 42:                                                    # the blade: tapering to the buried tip
            half = 1.6 if i > 4 else 0.6 + i * 0.25
            for k in np.arange(-half, half + 0.01, 0.5):
                p = c + side * k
                s = "minecraft:white_concrete" if k < -half + 0.6 else "minecraft:iron_block"
                b.set(int(round(p[0])), int(round(p[1])), int(round(p[2])), s)
                q = p + flat * 0.5
                b.set(int(round(q[0])), int(round(q[1])), int(round(q[2])), s)
        elif i < 44:                                                  # the guard (tsuba)
            for u_ in np.arange(-4, 4.01, 0.5):
                for v_ in np.arange(-2, 2.01, 0.5):
                    if (u_ / 4) ** 2 + (v_ / 2) ** 2 <= 1:
                        p = c + side * u_ + flat * v_
                        b.set(int(round(p[0])), int(round(p[1])), int(round(p[2])), "minecraft:gold_block")
        else:                                                         # the hilt, wrapped black and purple
            for u_ in np.arange(-1, 1.01, 0.5):
                for v_ in np.arange(-0.5, 1.01, 0.5):
                    p = c + side * u_ + flat * v_
                    s = "minecraft:gold_block" if i >= 58 else ("minecraft:purple_wool" if (i + int(u_ * 2)) % 3 == 0 else "minecraft:black_wool")
                    b.set(int(round(p[0])), int(round(p[1])), int(round(p[2])), s)
    rng = random.Random(4)
    for k in range(14):                                               # cracked ground round the blade
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(2, 6)
        x, z = int(round(sx + r * math.cos(a))), int(round(sz + r * math.sin(a)))
        b.set(x, 1, z, rng.choice(("minecraft:cobbled_deepslate", "minecraft:blackstone", "minecraft:deepslate")))


def trees(b, inside, taken):
    """Sakura by the pond and the avenue, snowy dark pines everywhere else that is free."""
    occ = _occupied(b)
    rng = random.Random(21)
    n = 0
    for i in range(900):
        x, z = rng.randint(6, 214), rng.randint(6, 214)
        if inside[x, z] < 6 or occ[x, z] or taken[max(0, x - 2):x + 3, max(0, z - 2):z + 3].any():
            continue
        if any(b.get(x + dx, y, z + dz) not in (None, AIR) for dx in (-2, 0, 2) for dz in (-2, 0, 2) for y in (1, 4)):
            continue
        near = math.hypot(x - POND[0], z - POND[1]) < POND[2] + 9 or (abs(x - CX) < 14 and z < 86)
        if near:
            if math.hypot(x - POND[0], z - POND[1]) < POND[2] + 2 or abs(x - CX) < 8:
                continue
            h = rng.randint(5, 7)
            for y in range(1, h):
                b.set(x, y, z, "onepiece:sakura_log[axis=y]")
            b.sphere(x, h, z, rng.uniform(2.6, 3.6), "onepiece:sakura_leaves[distance=7,persistent=true,waterlogged=false]", ry=2)
        else:
            h = rng.randint(7, 13)
            for y in range(1, h):
                b.set(x, y, z, "minecraft:spruce_log[axis=y]")
            for y in range(3, h + 2):
                rr = max(0.6, (h + 2 - y) * 0.42)
                for dx in range(-3, 4):
                    for dz in range(-3, 4):
                        if dx * dx + dz * dz <= rr * rr and b.get(x + dx, y, z + dz) is None:
                            b.set(x + dx, y, z + dz, "minecraft:spruce_leaves[distance=7,persistent=true,waterlogged=false]")
                            if y == h + 1 or dx * dx + dz * dz > (rr - 1) ** 2:
                                if b.get(x + dx, y + 1, z + dz) is None and rng.random() < 0.5:
                                    b.set(x + dx, y + 1, z + dz, "minecraft:snow[layers=1]")
        n += 1
    print("trees:", n)


def lift_and_sea(b):
    b.blocks = {(x, y + G, z): s for (x, y, z), s in b.blocks.items()}
    b.nbt = {(x, y + G, z): v for (x, y, z), v in b.nbt.items()}
    b.entities = [(e[0], e[1], e[2] + G, e[3]) + tuple(e[4:]) for e in b.entities]
    # paintings: their wall block lives in their data and one still fell off in some rotations, so leave them out
    b.entities = [e for e in b.entities if e[0] != "minecraft:painting"]
    X, Z = _grids()
    rr = np.hypot(X - CX, Z - OLD.CZ) / (SEA_R * (0.95 + 0.06 * NT.noise(X, Z, 61, 13)))
    for x in range(221):
        for z in range(221):
            if rr[x, z] >= 1:
                continue
            bed = -10 if rr[x, z] < 0.78 else int(round(-10 + 10 * (rr[x, z] - 0.78) / 0.22))
            bed = min(bed, -1)
            for y in range(bed + 1, 1):
                if (x, y, z) not in b.blocks:
                    b.set(x, y, z, "minecraft:water")
            if (x, bed, z) not in b.blocks:
                b.set(x, bed, z, "minecraft:sand" if NT.noise(x, z, 7, 5) > 0.3 else "minecraft:gravel")
                b.set(x, bed - 1, z, "minecraft:stone")


def build():
    b, g = OLD.build()
    bb, audit = design()
    to_canvas(bb, b)
    rooftop_castle(b)
    strip_old_outside(b)
    darken(b)
    inside, u = island_maps()[:2]
    island(b, inside, u)
    rim_crags(b, inside)
    avenue(b)
    pond(b)
    sword(b)
    tracker = P.PropTracker(2)
    taken = town(b, inside, tracker, audit)
    trees(b, inside, taken)
    cliff_stair(b, inside, u)
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    lift_and_sea(b)
    return b, g
