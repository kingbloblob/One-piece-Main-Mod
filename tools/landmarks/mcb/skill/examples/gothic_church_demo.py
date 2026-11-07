"""Mini Gothic church built from measured proportions of a studied cathedral
(see references/techniques/gothic-cathedral.md). Half scale of the reference."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from mcbig import BigBuild
import mcparts as P
b = BigBuild(y_min=0, y_max=90, seed=5)
W, L = 27, 57                                    # footprint (reference 53 x 113)
ST, SLAB, BR, TR, CU, BAR = "minecraft:stone_bricks", "minecraft:smooth_stone", "minecraft:bricks", "minecraft:spruce_planks", "minecraft:oxidized_cut_copper", "minecraft:iron_bars"
CUS = "minecraft:oxidized_cut_copper_stairs"
b.box(-6, 0, -6, W + 6, 0, L + 6, "minecraft:andesite")
# nave: clerestory block (x 7..19 inner nave 13 wide), aisle blocks each side
b.box(7, 1, 4, 19, 17, L - 20, ST)                                # nave walls up to eaves (+17)
b.clear(8, 2, 5, 18, 16, L - 21)
b.box(1, 1, 4, 6, 6, L - 20, ST); b.box(20, 1, 4, 25, 6, L - 20, ST)    # aisles (+6)
b.clear(2, 2, 5, 5, 5, L - 21); b.clear(21, 2, 5, 24, 5, L - 21)
for x0 in (1, 20):                                               # aisle lean-to roofs stepping up to the clerestory
    for i, y in enumerate((7, 8, 9, 10, 11)):
        xs = x0 + i if x0 == 1 else 25 - i
        b.fill(xs, y, 4, xs, y, L - 20, CU)
P.gable_roof(b, 7, 4, 19, L - 20, 18, CUS, ridge=CU, ridge_axis="z", overhang=0)
P.ridge_cresting(b, 13, 4, 13, L - 20, 24, axis="z", block=BAR)
# buttresses every 6 blocks along both sides, with pinnacles and flying struts
for z in range(8, L - 20, 6):
    for x_out, x_wall in ((-1, 7), (W + 1, 19)):
        b.fill(x_out - 1, 1, z, x_out + 1, 10, z + 2, ST)
        P.pinnacle(b, x_out, 11, z + 1, 5, ST)
        P.flying_buttress(b, x_out + (2 if x_out < 0 else -2), 10, x_wall + (0), 14, z + 1, ST)
# lancet windows in the clerestory and aisles
for z in range(9, L - 22, 6):
    P.pointed_opening(b, "z", z + 1, 9, 7, 3, 7, depth=1, trim=SLAB, fill="minecraft:light_blue_stained_glass_pane") if False else None
# transept
b.box(-7, 1, 24, W + 7, 15, 40, ST); b.clear(-6, 2, 25, W + 6, 14, 39)
P.gable_roof(b, -7, 24, W + 7, 40, 16, CUS, ridge=CU, ridge_axis="x", gable_fill=ST)
P.square_spire(b, 13, 32, 24, 7, 28, CU)                         # crossing spire
# west facade: twin towers (measured: 17 wide shaft, 22 apart) -> scaled 9 wide
for cx in (6, 20):
    b.box(cx - 4, 1, L - 19, cx + 4, 34, L - 1, ST)
    b.fill(cx - 4, 18, L - 19, cx + 4, 18, L - 1, SLAB)
    for z in (L - 19, L - 1):
        for dx in (-4, 4): b.fill(cx + dx, 1, z, cx + dx, 34, z, TR)    # dark vertical tracery lines
    P.pointed_opening(b, "x", cx, 20, L - 1, 3, 9, depth=1, trim=SLAB, fill="minecraft:cyan_stained_glass_pane")
    b.box(cx - 3, 35, L - 18, cx + 3, 42, L - 2, ST)
    P.square_spire(b, cx, L - 10, 43, 7, 40, CU)
    P.pinnacle(b, cx - 4, 35, L - 19, 4, ST); P.pinnacle(b, cx + 4, 35, L - 19, 4, ST)
b.box(10, 1, L - 19, 16, 22, L - 1, ST)                          # central portal gable
P.pointed_opening(b, "x", 13, 1, L - 1, 5, 12, depth=1, trim=SLAB)
P.pointed_opening(b, "x", 13, 14, L - 1, 3, 7, depth=1, trim=SLAB, fill="minecraft:blue_stained_glass_pane")
if __name__ == "__main__":
    print(b.summary(6))
    b.render_elevations("/tmp/gothic_demo.png", max_side=900)
