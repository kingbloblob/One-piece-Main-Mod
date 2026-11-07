import sys; sys.path.insert(0, "/home/claude/minecraft-builder/scripts")
from mcbuild import Build, Palette
pal = Palette.load("/tmp/palette.json")
b = Build(palette=pal, seed=3)
# foundation + shell
b.box(-1, -2, -1, 11, -1, 9, "minecraft:stone_bricks")
b.hollow_box(0, 0, 0, 10, 5, 8, "mymod:copper_bricks")
b.fill(0, 6, 0, 10, 6, 8, "minecraft:oak_planks")
for x, z in [(0,0),(10,0),(0,8),(10,8)]:
    b.pillar(x, 0, z, 5, "minecraft:stripped_oak_log")
b.clear(5, 1, 0, 5, 2, 0)          # door
for x in (2, 8):
    b.clear(x, 2, 0, x, 3, 0)      # windows
b.gable_roof(0, 0, 10, 8, 6, "mymod:copper_bricks_stairs", ridge="mymod:copper_bricks", overhang=1)
b.set(5, 4, 0, "mymod:glow_crystal")
try:
    b.set(1, 1, 1, "mymod:fake_block")
except ValueError as e:
    print("validation ok:", e)
print(b.summary())
print(b.layer(1))
print(b.side("z"))
n = b.save("/tmp/house.mcfunction", clear_bbox=True)
print("commands:", n)
