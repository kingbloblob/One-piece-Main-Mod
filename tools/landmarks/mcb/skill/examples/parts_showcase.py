import sys, time
sys.path.insert(0, "/home/claude/minecraft-builder/scripts")
from mcbig import BigBuild
import mcparts as P
b = BigBuild(seed=4, y_min=-2, y_max=60)
B="minecraft:stone_bricks"
b.box(-2,-1,-2,150,-1,70,"minecraft:grass_block")
# 1 gable house with arched door + windows
b.hollow_box(0,0,0,12,6,8,B)
P.gable_roof(b,0,0,12,8,7,"minecraft:oak_stairs",gable_fill="minecraft:oak_planks",overhang=1,ends_overhang=1)
P.arched_opening(b,"x",6,1,0,3,4,depth=1,trim="minecraft:polished_andesite")
# 2 square tower with hip roof + spiral stair inside
b.hollow_box(20,0,0,28,14,8,B)
P.hip_roof(b,20,0,28,8,15,"minecraft:stone_brick_stairs",overhang=1)
P.square_spiral_stair(b,22,1,2,5,13,"minecraft:oak_stairs",core="minecraft:oak_log",support=None)
# 3 round tower with cone roof
b.cylinder(45,0,10,6,16,B,hollow=True)
P.cone_roof(b,45,17,10,7,9,"minecraft:red_terracotta")
# 4 arcade + colonnade
b.box(60,0,0,90,8,2,B)
P.arcade(b,"x",60,90,0,0,3,5,pier=2,depth=3,trim="minecraft:chiseled_stone_bricks")
P.colonnade(b,"x",60,90,12,0,6,7,"minecraft:quartz_pillar",base="minecraft:smooth_quartz",capital="minecraft:chiseled_quartz_block",beam="minecraft:smooth_quartz")
# 5 trees
P.scatter_trees(b,100,0,145,30,0,25,kinds=("oak","birch","spruce","acacia"),min_spacing=5,seed=3)
# 6 ship
P.ship(b,0,12,30,length=31,beam=9,depth=5,masts=2)
# 7 weathered wall
b.box(60,0,40,100,12,42,B)
n=P.weather(b,60,0,40,100,12,42,P.STONE_AGING,height_bias=1.5,seed=1)
print("weathered", n)
print(b.summary(10))
b.render_top("/tmp/parts_top.png",px=4)
b.render_section("/tmp/parts_sec_house.png","z",4,px=10)
b.render_section("/tmp/parts_sec_ship.png","z",30,px=8)
b.render_section("/tmp/parts_sec_tower.png","z",4,px=10)
print(b.save_function("/tmp/parts.mcfunction", clear_first=False))
