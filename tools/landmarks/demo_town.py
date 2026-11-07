"""Test sheet for townkit: town houses of the sizes and styles the town modules use, a street, a well, stalls, lamps,
gardens and trees (rendered to check townkit changes; not a landmark)."""
import random
from canvas import *
import townkit as T

SID = "demo_town"
TITLE = "Townkit demo"
NX, NZ = 112, 76
CUTS = [3, 7]


def build():
    rnd = random.Random(5)
    b = B()
    T.ground(b, NX, NZ, rnd)
    T.path(b, [(2, 36), (40, 37), (80, 35), (110, 36)], w=1, alt="minecraft:coarse_dirt")
    T.path(b, [(56, 36), (56, 74)], w=1, s="minecraft:stone_bricks", alt="minecraft:cobblestone")
    styles = ("east_blue", "cottage", "orange", "plaster", "brick", "stone", "snow", "shack", "marine", "east_blue", "cottage", "orange")
    x = 3
    for i, st in enumerate(styles):  # north row, doors south to the street
        w, d = rnd.randint(7, 11), rnd.randint(6, 10)
        T.house(b, x, 34 - 2 - d, w, d, rnd.choice((1, 1, 2, 2, 3)), st, rnd, door="south", sign="minecraft:red_wool" if i == 3 else None)
        x += w + 2
        if x > NX - 12: break
    x = 3
    for i, st in enumerate(("sand", "east_blue", "brick", "plaster", "sand", "cottage", "orange", "stone")):
        w, d = rnd.randint(8, 12), rnd.randint(7, 11)
        if 50 <= x <= 60: x = 61
        T.house(b, x, 40, w, d, rnd.choice((1, 2, 2, 3)), st, rnd, door="north")
        x += w + 3
        if x > NX - 13: break
    T.well(b, 56, 62)
    T.stall(b, 44, 60, "red", ("minecraft:melon", "minecraft:pumpkin", None))
    T.stall(b, 63, 60, "blue", ("minecraft:hay_block[axis=y]", "onepiece:mikan_crate", None))
    for z in (44, 54, 66): T.lamp_post(b, 54, z)
    T.lamp_post(b, 20, 34); T.lamp_post(b, 70, 38)
    T.garden(b, 4, 58, 20, 70, rnd=rnd)
    for (x, z) in ((26, 64), (30, 70), (100, 64), (104, 70), (88, 66)): T.tree(b, x, z, h=rnd.randint(4, 6))
    T.tree(b, 94, 70, kind="birch", h=6); T.tree(b, 34, 62, kind="spruce", h=6)
    T.landscape(b, 0, 0, NX - 1, NZ - 1, rnd, amp=4, cell=16, edge=8)  # last: the open ground rolls round what stands
    return b, 0
