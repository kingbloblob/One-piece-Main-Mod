"""Egghead Labophase: Dr. Vegapunk's island of the future. The Faustphase town below with white rounded labs,
glowing paths, robot workshops, a Pacifista assembly line and Seraphim pods, and above it the giant cracked egg
of the Labophase on its stalk: a glass elevator tube runs up the stalk into three lab floors inside the egg
(the research lab, Vegapunk's library of knowledge, the Frontier Dome control room) with a viewing ring on top.
~104 x 104, egg top ~92. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "egghead_lab"
TITLE = "Egghead Labophase"
CUTS = [4, 50]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 104
CX, CZ = 52, 48
PANEL = "onepiece:lab_panel"
PANEL_SL = "onepiece:lab_panel_slab"
LIGHT = "onepiece:lab_light"
WHITE = "minecraft:white_concrete"
QUARTZ = "minecraft:smooth_quartz"
CYAN = "minecraft:cyan_concrete"
GLASS = "minecraft:light_blue_stained_glass"
LAB = dict(wood="birch", rug="cyan", rug2="white", bed="light_blue", light="onepiece:lab_light", accent="onepiece:lab_panel",
           banner="cyan", candle="cyan")
EY, ERX, ERY = 62, 24, 30        # egg centre y and radii
FLOORS = (44, 56, 68)


def in_egg(x, y, z):
    dy = y - EY
    ry = ERY * (1.0 if dy > 0 else 0.85)
    rx = ERX * (1 - 0.18 * dy / ERY)   # pointier at the top
    return (math.hypot(x - CX, z - CZ) / rx) ** 2 + (dy / ry) ** 2 <= 1


def pod_lab(b, cx, cz, r, h, rnd, kind):
    b.cyl(cx, cz, r, 0, 0, PANEL)
    b.cyl(cx, cz, r, 1, h, WHITE, hollow=True)
    for y in (2, 3):
        for a in range(0, 360, 40):
            t = math.radians(a); b.set(round(cx + r * math.cos(t)), y, round(cz + r * math.sin(t)), GLASS)
    b.dome(cx, cz, h + 1, r, h=r, s=QUARTZ, tip=None)
    b.cyl(cx, cz, r + 0.6, h, h, CYAN, hollow=True)
    for y in (1, 2, 3): b.set(cx, y, cz + r, AIR)
    I.furnish(b, round(cx - r * 0.6), 1, round(cz - r * 0.6), round(cx + r * 0.6), round(cz + r * 0.6), h - 1, kind, LAB, seed=rnd.randint(0, 9999))


def build():
    rnd = random.Random(101)
    b = B()
    # ---------------- island ground: grass, white paths with glowing strips, little trees
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:stone" if y < -2 else "minecraft:dirt")
            b.set(x, 0, z, "minecraft:grass_block")
            if rnd.random() < 0.03: b.set(x, 1, z, rnd.choice(("minecraft:short_grass", "minecraft:oxeye_daisy", "minecraft:cornflower")))
    for a in range(0, 360, 45):  # radial paths
        t = math.radians(a)
        for k in range(6, 52):
            for w in (-1, 0, 1):
                x = round(CX + k * math.cos(t) - w * math.sin(t)); z = round(CZ + k * math.sin(t) + w * math.cos(t))
                if 0 <= x < N and 0 <= z < N: b.set(x, 0, z, "minecraft:sea_lantern" if w == 0 and k % 5 == 0 else QUARTZ); b.set(x, 1, z, AIR) if b.get(x, 1, z) and "grass" in b.get(x, 1, z) else None
    for rr in (20, 36):
        for a in range(0, 360, 1):
            t = math.radians(a)
            for w in (0, 1):
                x, z = round(CX + (rr + w) * math.cos(t)), round(CZ + (rr + w) * math.sin(t))
                if 0 <= x < N and 0 <= z < N: b.set(x, 0, z, QUARTZ)
    for i in range(24):  # round future trees
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(40, 50)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if not (3 < x < N - 4 and 3 < z < N - 4) or b.get(x, 0, z) != "minecraft:grass_block": continue
        for y in range(1, 5): b.set(x, y, z, "minecraft:birch_log[axis=y]")
        b.sphere(x, 6, z, 2.5, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]" if i % 2 else "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    # ---------------- Faustphase: pod labs, the robot workshop, the Pacifista line, Seraphim pods
    for (cx, cz, r, h, kind) in ((CX - 28, CZ - 22, 6, 6, "lab"), (CX + 28, CZ - 22, 6, 6, "workshop"), (CX - 30, CZ + 24, 7, 7, "library"),
                                 (CX + 30, CZ + 24, 6, 6, "lab"), (CX, CZ - 38, 5, 5, "kitchen"), (CX - 40, CZ, 5, 5, "bedroom"), (CX + 40, CZ, 5, 5, "storage")):
        pod_lab(b, cx, cz, r, h, rnd, kind)
    # Pacifista assembly line (south): conveyor, robot frames and arms
    for x in range(CX - 18, CX + 19):
        for z in (CZ + 40, CZ + 41): b.set(x, 1, z, "minecraft:black_concrete" if x % 2 else "minecraft:gray_concrete")
    for x in range(CX - 15, CX + 16, 6):  # half-built Pacifistas on the line
        for y in range(2, 9): b.set(x, y, CZ + 40, "minecraft:iron_block" if y < 7 else "minecraft:black_concrete")
        b.set(x - 1, 6, CZ + 40, "minecraft:iron_block"); b.set(x + 1, 6, CZ + 40, "minecraft:iron_block")
        b.set(x, 9, CZ + 40, "minecraft:white_concrete"); b.set(x, 8, CZ + 39, "minecraft:red_stained_glass")
        for y in range(1, 12): b.set(x + 3, y, CZ + 43, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.set(x + 3, 12, CZ + 43, "minecraft:iron_block"); b.set(x + 2, 12, CZ + 42, "minecraft:iron_block"); b.set(x + 1, 11, CZ + 41, "minecraft:lightning_rod[facing=down,powered=false,waterlogged=false]")
    b.box(CX - 20, 13, CZ + 38, CX + 20, 13, CZ + 45, "minecraft:white_concrete")
    for (x, z) in ((CX - 20, CZ + 38), (CX + 20, CZ + 38), (CX - 20, CZ + 45), (CX + 20, CZ + 45)): b.column(x, z, 1, 12, QUARTZ)
    # Seraphim pods: glass capsules with a figure inside
    for i, a in enumerate(range(200, 340, 20)):
        t = math.radians(a); x, z = round(CX + 28 * math.cos(t)), round(CZ + 28 * math.sin(t) * -1 + 0)
        z = round(CZ - 28 * math.sin(t) * -1)
        b.set(x, 1, z, PANEL)
        for y in range(2, 6): b.set(x, y, z, GLASS if y != 3 else "minecraft:black_concrete")
        b.set(x, 6, z, LIGHT)
    # ---------------- the Labophase egg on its stalk
    for y in range(1, FLOORS[0] - 6):
        rr = 5 + 4 * math.exp(-y / 4)  # flared foot
        b.cyl(CX, CZ, rr, y, y, WHITE, hollow=True)
        if y % 6 == 0: b.cyl(CX, CZ, rr + 0.5, y, y, CYAN, hollow=True)
    b.cyl(CX, CZ, 8, 0, 0, PANEL)
    for y in range(1, 4):
        for w in (-1, 0, 1): b.set(CX + w, y, CZ + 9, AIR); b.set(CX + w, y, CZ + 8, AIR)
    for y in range(1, FLOORS[-1] + 1):  # elevator tube
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)): b.set(CX + dx, y, CZ + dz, GLASS) if y > FLOORS[0] - 6 or True else None
        b.set(CX, y, CZ, "minecraft:ladder[facing=south,waterlogged=false]") if False else b.set(CX, y, CZ, AIR)
    for y in range(1, FLOORS[-1] + 1):
        b.set(CX, y, CZ - 1, PANEL); b.set(CX, y, CZ, "minecraft:ladder[facing=south,waterlogged=false]")
    for f in FLOORS:
        for y in (f, f + 1, f + 2): b.set(CX, y, CZ + 1, AIR)
    b.cyl(CX, CZ, 2.2, 1, 1, PANEL_SL + "[type=bottom,waterlogged=false]") if False else None
    # egg shell: white with a cyan band and the crack at the top
    def shell(x, y, z):
        if EY + 19 < y < EY + 22: return CYAN
        if (x + z + y) % 11 == 0 and y > EY: return "minecraft:white_stained_glass"
        return WHITE if y < EY + 20 else QUARTZ
    b.shape(in_egg, CX - ERX - 1, EY - ERY, CZ - ERX - 1, CX + ERX + 1, EY + ERY, CZ + ERX + 1, shell, interior=AIR)
    for a in range(0, 360, 8):  # jagged cracked top, opened like a hatched egg
        t = math.radians(a); jag = 3 + (a // 8) % 3 * 2
        for rr in range(0, ERX):
            x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
            for y in range(EY + ERY - 10 + jag, EY + ERY + 1): b.set(x, y, z, AIR) if (x, y, z) in b.blocks else None
    # window bands for each lab floor
    for f in FLOORS:
        for a in range(0, 360, 4):
            t = math.radians(a)
            for rr in range(ERX - 2, ERX + 2):
                for dy in (2, 3):
                    x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
                    if (x, f + dy, z) in b.blocks and b.blocks[(x, f + dy, z)] not in (AIR,) and (a // 4) % 4: b.set(x, f + dy, z, GLASS)
    # lab floors inside the egg
    kinds = ("lab", "library", "study")
    for i, f in enumerate(FLOORS):
        rr = None
        for k in range(ERX, 0, -1):
            if in_egg(CX + k, f, CZ) and in_egg(CX + k, f - 1, CZ): rr = k - 1; break
        if not rr: continue
        b.cyl(CX, CZ, rr, f - 1, f - 1, PANEL if i else "minecraft:polished_diorite")
        for (dx, dz) in ((0, 0), (0, -1)): b.set(CX + dx, f - 1, CZ + dz, PANEL if dz else AIR)
        b.set(CX, f - 1, CZ, "minecraft:ladder[facing=south,waterlogged=false]")
        hw = int(rr * 0.68)
        for x in range(CX - hw - 1, CX + hw + 2):  # lab partitions: a square of rooms round the elevator
            for z in range(CZ - hw - 1, CZ + hw + 2):
                if x in (CX - hw - 1, CX + hw + 1) or z in (CZ - hw - 1, CZ + hw + 1):
                    for y in range(f, f + 6): b.set(x, y, z, PANEL if y < f + 5 else LIGHT)
        for (x, z) in ((CX - hw - 1, CZ), (CX + hw + 1, CZ), (CX, CZ + hw + 1), (CX, CZ - hw - 1)):
            for y in (f, f + 1, f + 2): b.set(x, y, z, AIR)
        floor_kinds = (("lab", "workshop", "lab", "storage"), ("library", "study", "library", "lab"), ("study", "treasure", "lab", "bedroom"))[i]
        I.subdivide(b, CX - hw, f, CZ - hw, CX + hw, CZ + hw, 6, "minecraft:white_stained_glass", floor_kinds, LAB, cell=max(8, hw),
                    keepout=((CX - 2, CZ - 2, CX + 2, CZ + 2),), seed=300 + i)
        for a in range(0, 360, 30):  # glowing consoles round the rim
            t = math.radians(a); x, z = round(CX + (rr - 1) * math.cos(t)), round(CZ + (rr - 1) * math.sin(t))
            if b.get(x, f, z) in (None, AIR): b.set(x, f, z, PANEL); b.set(x, f + 1, z, LIGHT if a % 60 else "minecraft:white_stained_glass_pane")
    # the brain-like Punk Records sphere floating over the top floor
    b.sphere(CX, FLOORS[-1] + 12, CZ, 4, "minecraft:pink_concrete")
    for k in range(6): b.set(CX, FLOORS[-1] + 6 + k, CZ, "minecraft:end_rod[facing=up]") if k < 2 else None
    # viewing ring at the crack line
    yv = EY + ERY - 10
    for a in range(0, 360, 2):
        t = math.radians(a)
        for rr in range(ERX - 8, ERX - 5):
            x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
            if b.get(x, yv, z) in (None, AIR): b.set(x, yv, z, PANEL)
        x, z = round(CX + (ERX - 8) * math.cos(t)), round(CZ + (ERX - 8) * math.sin(t))
        if b.get(x, yv + 1, z) in (None, AIR): b.set(x, yv + 1, z, "minecraft:white_stained_glass_pane")
    # ---------------- people and loot
    b.npc(CX + 4, FLOORS[-1], CZ + 2, "kizaru", True)
    b.chest(CX - 4, FLOORS[-1], CZ - 4, "legendary", "south"); b.chest(CX + 4, FLOORS[0], CZ - 4, "lab", "south"); b.chest(CX - 28, 1, CZ - 22, "lab", "east")
    b.guards("seraphim", ((CX - 6, CZ + 6), (CX + 6, CZ - 6)), y=FLOORS[1])
    b.guards("pacifista", ((CX - 10, CZ + 34), (CX + 10, CZ + 34), (CX, CZ + 16)))
    return b, 0
