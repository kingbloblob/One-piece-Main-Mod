"""Chocolate Town on Cacao Island in Totto Land: a whole town made of chocolate. Chocolate houses with frosting
trim and wafer roofs, Pudding's café with its patio, the chocolatier's workshop, the cocoa press, chocolate-
paved streets and a canal of melted chocolate crossed by cookie bridges, the harbour with candy-striped
bollards, lollipop trees and the town square with a big chocolate fountain. ~100 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import whole_cake as WC

SID = "chocolate_town"
TITLE = "Cacao Island Chocolate Town"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 100, 96
CHOC = "onepiece:chocolate_block"
COOKIE = "onepiece:cookie_bricks"
FROST = "onepiece:frosting_block"
CANE = "onepiece:candy_cane_block"
SEA_Z = 82


def build():
    rnd = random.Random(601)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:brown_terracotta", deco=0)
    for x in range(NX):
        for z in range(NZ):
            if (x // 3 + z // 3) % 2 == 0: b.set(x, 0, z, CHOC)
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z, depth=5)
    # the chocolate canal across town, with cookie bridges
    CZ = 44
    for x in range(NX):
        zc = CZ + round(2 * math.sin(x * 0.1))
        for dz in range(-2, 3):
            b.set(x, 0, zc + dz, "minecraft:brown_concrete" if abs(dz) < 2 else COOKIE)
            if abs(dz) < 2: b.set(x, -1, zc + dz, "minecraft:brown_concrete")
    for bx in (20, 50, 80):
        for z in range(CZ - 4, CZ + 5):
            for x in (bx - 1, bx, bx + 1): b.set(x, 1, z, COOKIE)
            b.set(bx - 2, 2, z, CANE if z % 2 else FROST); b.set(bx + 2, 2, z, CANE if z % 2 else FROST)
    # ---------------- streets and the town square with the chocolate fountain
    for z in (20, 64):
        for x in range(2, NX - 2):
            for dz in (-1, 0, 1): b.set(x, 0, z + dz, "minecraft:white_concrete" if (x + dz) % 4 else "minecraft:pink_concrete")
    SX, SZ = 50, 64
    b.cyl(SX, SZ, 8, 0, 0, "minecraft:white_concrete")
    b.cyl(SX, SZ, 4, 1, 1, COOKIE); b.cyl(SX, SZ, 3, 1, 1, "minecraft:brown_concrete")
    b.cyl(SX, SZ, 1.5, 2, 5, CHOC); b.cyl(SX, SZ, 2.5, 6, 6, COOKIE); b.set(SX, 7, SZ, CHOC); b.set(SX, 8, SZ, "minecraft:red_concrete")
    # ---------------- houses
    spots = ((4, 4), (16, 6), (28, 4), (64, 4), (76, 6), (88, 4), (4, 26), (16, 28), (64, 26), (78, 28), (88, 28),
             (4, 50), (16, 52), (28, 50), (66, 50), (80, 52), (4, 68), (16, 70), (70, 68), (84, 68))
    k = 0
    kinds = ("kitchen", "bedroom", "dining", "bedroom", "storage", "kitchen")
    for (x0, z0) in spots:
        w, d = rnd.randint(8, 10), rnd.randint(7, 9)
        if z0 + d >= CZ - 3 and z0 <= CZ + 3: continue
        if x0 + w >= NX - 2 or z0 + d >= SEA_Z - 1: continue
        WC.cake_house(b, x0, z0, w, d, 5, rnd)
        b.box(x0, 1, z0, x0 + w, 1, z0 + d, CHOC) if False else None
        I.furnish(b, x0 + 1, 1, z0 + 1, x0 + w - 1, z0 + d - 1, 4, kinds[k % len(kinds)], "candy", seed=x0 * 13 + z0); k += 1
    # Pudding's café with a patio, and the chocolatier's workshop
    PX0, PZ0 = 38, 4
    WC.cake_house(b, PX0, PZ0, 16, 11, 7, rnd)
    I.furnish(b, PX0 + 1, 1, PZ0 + 1, PX0 + 15, PZ0 + 10, 6, "dining", "candy", seed=91)
    for (x, z) in ((PX0 + 2, PZ0 + 14), (PX0 + 7, PZ0 + 14), (PX0 + 12, PZ0 + 14)): b.table_set(x, 1, z, wood="cherry", cloth="pink")
    for x in range(PX0, PX0 + 17, 2): b.set(x, 1, PZ0 + 12, "minecraft:cherry_fence")
    WC.cake_house(b, 30, 26, 14, 10, 6, rnd)
    I.furnish(b, 31, 1, 27, 43, 35, 5, "workshop", "candy", seed=92)
    for x in range(32, 42, 3): b.set(x, 1, 33, "minecraft:cauldron"); b.set(x, 2, 33, "minecraft:brown_carpet")
    # the cocoa press: a big wheel by the canal
    for a in range(0, 360, 10):
        t = math.radians(a)
        b.set(56, round(7 + 5 * math.sin(t)), round(CZ - 8 + 5 * math.cos(t)), "minecraft:brown_concrete" if a % 30 else COOKIE)
    b.column(56, CZ - 8, 1, 7, CHOC)
    # lollipop trees and candy lamps
    for (x, z) in ((10, 40), (36, 40), (64, 40), (90, 40), (40, 74), (60, 74), (30, 16), (70, 16)):
        WC.lollipop(b, x, z, rnd.randint(5, 8), rnd.choice(("pink", "red", "lime", "yellow", "light_blue")), rnd)
    for x in range(6, NX - 4, 10):
        b.column(x, 22, 1, 4, CANE); b.set(x, 5, 22, "minecraft:pearlescent_froglight[axis=y]")
    # the harbour
    for x in range(2, NX - 2):
        b.set(x, 0, SEA_Z, COOKIE)
        if x % 6 == 0: b.set(x, 1, SEA_Z, CANE)
    T.pier(b, 30, SEA_Z + 1, 10, axis="z", boat=True)
    T.pier(b, 66, SEA_Z + 1, 10, axis="z", boat=False)
    # ---------------- loot and Homies
    b.chest(PX0 + 2, 1, PZ0 + 2, "candy", "east"); b.chest(32, 1, 28, "candy", "east")
    b.guards("homie", ((SX, SZ + 10), (50, 20), (20, 64)))
    return b, 0
