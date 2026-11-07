"""Dungeon kit: one layout, many themes. Each dungeon (tools/dungeons/<sid>.py) is a THEME dict plus a few
signature pieces; this file draws the shared parts so a new dungeon is mostly data.

The layout (canvas x 0..63, z 0..67, ground y 0, built as a LAND structure on its island):

  surface   a themed entrance building over a stairwell, ruined walls, a path south, ground dressing
  stairwell 17 steps down north (z 58 -> 42) to the main floor F = -16
  antechamber  x 22..42, z 30..42: pillars, guards
  west wing    barracks (x 4..10) + armory (x 12..18), z 31..41
  east wing    trap corridor over a pit (x 43..51), then the side vault x 53..60, z 29..42
  arena        x 16..48, z 8..26, sunken to A = -19, 12 high: pillar ring, braziers, side channels, the
               mini-boss in the middle, the throne dais on the north
  sanctum      x 27..37, z 1..6 behind the throne, on the dais level: the legendary blade's altar + treasure

Entities: guards get the tags onepiece_guard + onepiece_kit_<kit> (NpcFeature dresses them); the mini-boss also
gets onepiece_miniboss_<sid> (com.onepiecemod.dungeon.DungeonBosses gives it its boss bar, moves and drops).
Chests point at loot tables onepiece:chests/dungeon_*.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "landmarks"))
from canvas import B, AIR, stairs, slab, wall as wall_of, fence  # noqa: E402

GUARD_TAG = "onepiece_guard"
F = -16          # main floor (air starts here)
A = -19          # arena floor
DAIS = A + 2     # throne dais / sanctum floor
N_X, N_Z = 64, 80


def _pick(rnd, mix):
    """mix: a block id or a list of (block, weight)."""
    if isinstance(mix, str):
        return mix
    r = rnd.random() * sum(w for _, w in mix)
    for b, w in mix:
        r -= w
        if r <= 0:
            return b
    return mix[-1][0]


class Dungeon:
    def __init__(self, sid, theme, seed):
        self.sid, self.T, self.rnd = sid, theme, random.Random(seed)
        self.b = B()
        self.guard_spots = []

    # ---------- basics ----------
    def mixbox(self, x0, y0, z0, x1, y1, z1, mix):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.b.set(x, y, z, _pick(self.rnd, mix))

    def air(self, x0, y0, z0, x1, y1, z1):
        self.b.box(x0, y0, z0, x1, y1, z1, AIR)

    def hall(self, x0, z0, x1, z1, y, h, floor=None, wall=None, ceil=None):
        """Carve a room (inner x0..x1, z0..z1, air y..y+h-1) with a 1-thick wall shell, floor and ceiling."""
        T = self.T
        self.mixbox(x0 - 1, y - 1, z0 - 1, x1 + 1, y + h, z1 + 1, wall or T["wall"])
        self.mixbox(x0, y - 1, z0, x1, y - 1, z1, floor or T["floor"])
        self.mixbox(x0, y + h, z0, x1, y + h, z1, ceil or T["ceil"])
        self.air(x0, y, z0, x1, y + h - 1, z1)
        # a trim band of the dark stone at the foot of every wall
        for x in range(x0 - 1, x1 + 2):
            for z in (z0 - 1, z1 + 1):
                self.b.set(x, y - 1, z, T["base"])
        for z in range(z0 - 1, z1 + 2):
            for x in (x0 - 1, x1 + 1):
                self.b.set(x, y - 1, z, T["base"])

    def pillar(self, x, z, y0, y1, cap=True):
        T = self.T
        for y in range(y0, y1 + 1):
            self.b.set(x, y, z, T["pillar"])
        if cap:
            self.b.set(x, y0, z, T["pillar_base"])
            self.b.set(x, y1, z, T["pillar_base"])

    def wall_lamp(self, x, y, z):
        self.b.set(x, y, z, self.T["lamp"])

    def hang(self, x, y, z):
        self.b.set(x, y, z, self.T["hang"])

    def chest(self, x, y, z, loot, facing):
        self.b.set(x, y, z, f"minecraft:chest[facing={facing},type=single,waterlogged=false]",
                   {"id": "minecraft:chest", "LootTable": f"onepiece:chests/{loot}"})

    def guard(self, x, y, z, kit, extra=()):
        from nbt import Byte  # tools/worldgen/nbt.py (on the path through canvas -> kit)
        tags = [GUARD_TAG, "onepiece_kit_" + kit] + list(extra)
        self.b.entities.append(("onepiece:sea_pirate", x, y, z, {"PersistenceRequired": Byte(1), "Tags": tags}))

    def banner_strip(self, x, y0, y1, z, color, trim=None):
        """A cloth hanging on a wall: wool strip with a trim at the bottom."""
        for y in range(y0, y1 + 1):
            self.b.set(x, y, z, f"minecraft:{color}_wool")
        if trim:
            self.b.set(x, y0, z, trim)

    # ---------- ground and rock ----------
    def ground(self):
        T = self.T
        # rock mass: make_dungeons.py keeps only what lies within 4 blocks of the dungeon's air
        self.mixbox(0, -26, 0, N_X - 1, -4, N_Z - 1, T["rock"])
        self.mixbox(0, -3, 0, N_X - 1, -1, N_Z - 1, T["subsoil"])
        self.mixbox(0, 0, 0, N_X - 1, 0, N_Z - 1, T["surface"])

    # ---------- underground ----------
    def stairwell(self):
        T = self.T
        for i in range(17):
            z = 58 - i
            y = -1 - i
            for x in (29, 33):
                self.mixbox(x, y - 1, z, x, y + 5, z, T["wall"])
            self.mixbox(30, y - 1, z, 32, y - 1, z, T["floor"])
            for x in range(30, 33):
                self.b.set(x, y, z, stairs(T["stair"], "south"))
            self.air(30, y + 1, z, 32, y + 4, z)
            self.mixbox(30, y + 5, z, 32, y + 5, z, T["ceil"])
            if i % 4 == 2:
                self.wall_lamp(29, y + 3, z)
                self.wall_lamp(33, y + 3, z)
        # the stair's top opens into the entrance building's floor
        self.air(30, 0, 56, 32, 3, 60)

    def antechamber(self):
        T = self.T
        self.hall(22, 30, 42, 42, F, 6)
        self.air(30, F, 43, 32, F + 3, 43)                 # stairwell opening
        for x in (25, 39):
            for z in (33, 39):
                self.pillar(x, z, F, F + 5)
        # a carpet runner from the stairs to the arena gate, wall cloths, lamps
        for z in range(30, 43):
            self.b.set(31, F, z, f"minecraft:{T['carpet']}_carpet")
        for x in (21, 43):
            for z in (32, 40):
                self.wall_lamp(x, F + 3, z)
        for x in (26, 36):
            self.banner_strip(x, F + 1, F + 4, 29, T["cloth"], T["base"])
        self.b.set(23, F, 31, "minecraft:barrel[facing=up,open=false]")
        self.b.set(23, F, 41, "minecraft:barrel[facing=up,open=false]")
        self.b.set(41, F, 41, T["urn"])
        self.b.set(41, F, 31, T["urn"])
        self.guard_spots += [(27, F, 36), (35, F, 36)]

    def west_wing(self):
        T = self.T
        self.air(19, F, 35, 21, F + 2, 37)               # corridor
        self.mixbox(19, F - 1, 35, 21, F - 1, 37, T["floor"])
        self.mixbox(19, F + 3, 34, 21, F + 3, 38, T["ceil"])
        for x in range(19, 22):
            for z in (34, 38):
                self.mixbox(x, F, z, x, F + 2, z, T["wall"])
        self.hall(4, 31, 10, 41, F, 5)                     # barracks
        self.hall(12, 31, 18, 41, F, 5)                    # armory
        self.air(11, F, 35, 11, F + 1, 36)
        self.air(19, F, 35, 19, F + 2, 37)
        # barracks: bunks along both walls, a table in the middle
        for z in (32, 35, 38):
            for x, facing in ((4, "east"), (10, "west")):
                self.b.set(x, F, z, f"minecraft:{T['bed']}_bed[facing={'west' if facing == 'east' else 'east'},occupied=false,part=head]")
                self.b.set(x + (1 if facing == "east" else -1), F, z,
                           f"minecraft:{T['bed']}_bed[facing={'west' if facing == 'east' else 'east'},occupied=false,part=foot]")
        self.b.set(7, F, 36, fence(T["wood"]))
        self.b.set(7, F + 1, 36, f"minecraft:{T['wood']}_pressure_plate[powered=false]")
        self.b.set(7, F, 35, stairs(f"minecraft:{T['wood']}_stairs", "south"))
        self.b.set(7, F, 37, stairs(f"minecraft:{T['wood']}_stairs", "north"))
        self.chest(7, F, 41, "dungeon_common", "north")
        self.b.set(6, F, 41, "minecraft:barrel[facing=up,open=false]")
        self.b.set(8, F, 41, "minecraft:barrel[facing=up,open=false]")
        self.hang(7, F + 4, 33)
        self.hang(7, F + 4, 39)
        # armory: weapon racks (grindstone, anvil, smithing table), crates, a target dummy
        for z, blk in ((31, "minecraft:anvil[facing=east]"), (33, "minecraft:grindstone[face=floor,facing=east]"),
                       (39, "minecraft:smithing_table"), (41, "minecraft:fletching_table")):
            self.b.set(12, F, z, blk)
        for z in range(31, 42, 2):
            self.b.set(18, F + 1, z, f"minecraft:{T['wood']}_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]")
            self.b.set(18, F, z, "minecraft:barrel[facing=west,open=false]")
        self.b.set(15, F, 36, "minecraft:hay_block[axis=y]")
        self.b.set(15, F + 1, 36, "minecraft:carved_pumpkin[facing=south]")
        self.hang(15, F + 4, 33)
        self.hang(15, F + 4, 39)
        self.guard_spots += [(7, F, 34), (15, F, 38)]

    def east_wing(self):
        T = self.T
        # trap corridor: a 3-wide pit with a stepping stone, its floor the theme's hazard (magma, soul sand, ...)
        self.hall(44, 34, 51, 36, F, 4)
        self.air(43, F, 34, 43, F + 2, 36)
        for x in (46, 48):
            self.air(x, F - 5, 34, x, F - 1, 36)
            self.mixbox(x, F - 6, 34, x, F - 6, 36, T["pit"])
            self.mixbox(x, F - 5, 33, x, F - 1, 33, T["wall"])
            self.mixbox(x, F - 5, 37, x, F - 1, 37, T["wall"])
        self.mixbox(47, F - 6, 34, 47, F - 1, 36, T["pillar"])
        for x in (45, 49):
            self.mixbox(x, F - 6, 34, x, F - 2, 36, T["wall"])
        self.b.set(44, F, 36, T["urn"])
        self.wall_lamp(44, F + 2, 33)
        self.wall_lamp(50, F + 2, 37)
        # side vault
        self.hall(53, 29, 60, 42, F, 5)
        self.air(52, F, 34, 52, F + 2, 36)
        for z in (31, 40):
            self.pillar(55, z, F, F + 4)
            self.pillar(58, z, F, F + 4)
        for x, z in ((54, 30), (59, 30), (59, 41)):
            self.mixbox(x, F, z, x, F, z, "minecraft:gold_block")
        self.chest(56, F, 29, "dungeon_vault_" + self.sid, "south")
        self.chest(57, F, 29, "dungeon_common", "south")
        self.b.set(60, F, 35, T["urn"])
        self.b.set(60, F, 36, T["urn"])
        self.hang(56, F + 4, 35)
        self.hang(57, F + 4, 38)
        self.guard_spots += [(57, F, 36)]

    def arena(self):
        T = self.T
        x0, z0, x1, z1 = 16, 8, 48, 26
        h = 12
        self.hall(x0, z0, x1, z1, A, h)
        # passage from the antechamber, steps down into the arena
        self.air(30, F, 27, 34, F + 4, 29)
        self.mixbox(30, F - 1, 27, 34, F - 1, 29, T["floor"])
        for x in (29, 35):
            self.mixbox(x, F - 1, 27, x, F + 5, 29, T["wall"])
            self.b.set(x, F + 2, 28, T["lamp"])
        self.mixbox(30, F + 5, 27, 34, F + 5, 29, T["ceil"])
        for i, z in enumerate((26, 25, 24)):
            y = F - 1 - i
            for x in range(30, 35):
                self.b.set(x, y, z, stairs(T["stair"], "south"))
                for yy in range(A - 1, y):
                    self.b.set(x, yy, z, _pick(self.rnd, T["floor"]))
        # the gate: an arch of the trim stone with bars hung over the top
        for x in range(29, 36):
            self.b.set(x, F + 4, 29, T["base"])
        # pillar ring and braziers
        for x in (20, 26, 38, 44):
            for z in (14, 23):
                self.pillar(x, z, A, A + h - 1)
                self.b.set(x, A + 4, z, T["lamp"])
        for x, z in ((23, 17), (41, 17)):
            self.b.set(x, A, z, T["brazier_base"])
            self.b.set(x, A + 1, z, T["brazier"])
        # side channels with railings (lava, water or poison mire by theme)
        for xa, xb in ((17, 18), (46, 47)):
            for z in range(10, 25):
                self.mixbox(xa, A - 2, z, xb, A - 2, z, T["base"])
                for x in (xa, xb):
                    self.b.set(x, A - 1, z, T["channel"])
                rail = xb + 1 if xa < 30 else xa - 1
                self.b.set(rail, A, z, T["rail"])
        # floor emblem: a ring of the accent block around the boss's spot
        cx, cz = 32, 17
        for x in range(cx - 5, cx + 6):
            for z in range(cz - 5, cz + 6):
                d = math.hypot(x - cx, z - cz)
                if 4.3 <= d <= 5.2:
                    self.b.set(x, A - 1, z, T["accent"])
        self.b.set(cx, A - 1, cz, T["accent"])
        # dais and throne
        self.mixbox(25, A, 8, 39, A + 1, 11, T["dais"])
        for x in range(25, 40):
            self.b.set(x, A + 1, 12, stairs(T["stair"], "north"))
            self.b.set(x, A, 13, stairs(T["stair"], "north"))
            if x in (25, 39):
                continue
            self.b.set(x, A, 12, _pick(self.rnd, T["dais"]))
        tx = 32
        self.b.set(tx, DAIS, 10, stairs(T["throne"], "north"))
        self.b.set(tx - 1, DAIS, 10, T["throne_side"])
        self.b.set(tx + 1, DAIS, 10, T["throne_side"])
        self.mixbox(tx - 1, DAIS, 9, tx + 1, DAIS + 2, 9, T["throne_back"])
        self.b.set(tx, DAIS + 3, 9, T["accent"])
        for x in (26, 38):
            self.b.set(x, DAIS, 9, T["brazier_base"])
            self.b.set(x, DAIS + 1, 9, T["brazier"])
        # chains from the roof
        for x, z in ((24, 16), (40, 16), (32, 22)):
            for y in range(A + 8, A + h):
                self.b.set(x, y, z, "minecraft:iron_chain[axis=y,waterlogged=false]")
            self.hang(x, A + 7, z)
        # lamps on the side walls
        for z in (11, 17, 23):
            self.wall_lamp(x0 - 1, A + 5, z)
            self.wall_lamp(x1 + 1, A + 5, z)
        for x in (21, 43):
            self.wall_lamp(x, A + 5, z0 - 1)
            self.wall_lamp(x, A + 5, z1 + 1)

    def arena_cloths(self):
        """Big wall cloths behind the throne (after the sanctum, whose wall shares that row)."""
        for x in (28, 36):
            self.banner_strip(x, DAIS + 1, A + 9, 7, self.T["cloth"], self.T["base"])

    def sanctum(self):
        T = self.T
        self.hall(27, 1, 37, 6, DAIS, 5)
        self.air(31, DAIS, 7, 33, DAIS + 2, 7)            # door behind the throne
        self.b.set(30, DAIS + 3, 7, T["base"])
        self.b.set(34, DAIS + 3, 7, T["base"])
        # the altar where the legendary blade lay
        self.mixbox(31, DAIS, 2, 33, DAIS, 2, T["dais"])
        self.b.set(32, DAIS + 1, 2, T["altar_top"])
        self.b.set(32, DAIS + 2, 1, T["accent"])
        self.chest(29, DAIS, 2, "dungeon_sanctum_" + self.sid, "south")
        self.chest(35, DAIS, 2, "dungeon_sanctum_" + self.sid, "south")
        for x, z in ((28, 2), (36, 2), (28, 5), (36, 5)):
            self.b.set(x, DAIS, z, "minecraft:gold_block" if (x + z) % 2 else T["urn"])
        self.hang(30, DAIS + 4, 4)
        self.hang(34, DAIS + 4, 4)

    # ---------- surface ----------
    def path(self, x0, x1, z0, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if self.rnd.random() < 0.85:
                    self.b.set(x, 0, z, _pick(self.rnd, self.T["path"]))

    def ruin_wall(self, x0, z0, x1, z1, h):
        """A broken wall: full height in places, crumbled to 1-2 elsewhere."""
        n = max(abs(x1 - x0), abs(z1 - z0))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i // max(1, n)
            z = z0 + (z1 - z0) * i // max(1, n)
            top = h if (i // 3) % 3 != 1 else self.rnd.choice((1, 2))
            for y in range(1, top + 1):
                self.b.set(x, y, z, _pick(self.rnd, self.T["ruin"]))
            if top == h:
                self.b.set(x, h + 1, z, slab(self.T["ruin_slab"]))

    def scatter(self, blocks, n, area=(2, 2, N_X - 3, N_Z - 3), keep_out=()):
        x0, z0, x1, z1 = area
        for _ in range(n):
            x, z = self.rnd.randint(x0, x1), self.rnd.randint(z0, z1)
            if any(a <= x <= c and b <= z <= d for (a, b, c, d) in keep_out):
                continue
            if self.b.get(x, 1, z) not in (None, AIR):
                continue
            self.b.set(x, 1, z, self.rnd.choice(blocks))

    def entities(self, boss_kit, guard_kits, minion_kit):
        """Guards on their spots (kit picked round-robin), the mini-boss in the arena and two of its minions."""
        for i, (x, y, z) in enumerate(self.guard_spots):
            self.guard(x, y, z, guard_kits[i % len(guard_kits)])
        self.guard(32, A, 17, boss_kit, ["onepiece_miniboss_" + self.sid])
        self.guard(26, A, 18, minion_kit)
        self.guard(38, A, 18, minion_kit)

    def underground(self):
        self.stairwell()
        self.antechamber()
        self.west_wing()
        self.east_wing()
        self.arena()
        self.sanctum()
        self.arena_cloths()

    def avenue(self, z0, z1, xs, column, step=4, h=5, cap=None):
        """Pairs of columns (or statues) along the approach path, every `step` blocks; a few are broken."""
        for z in range(z0, z1 + 1, step):
            for x in xs:
                top = h if self.rnd.random() > 0.25 else self.rnd.randint(1, h - 2)
                for y in range(1, top + 1):
                    self.b.set(x, y, z, column)
                if top == h and cap:
                    self.b.set(x, h + 1, z, cap)
                elif top < h:
                    # the fallen piece lies beside it
                    dx = 1 if x < 32 else -1
                    for k in range(1, 3):
                        if self.b.get(x - dx * k, 1, z) in (None, AIR):
                            self.b.set(x - dx * k, 1, z, column)
