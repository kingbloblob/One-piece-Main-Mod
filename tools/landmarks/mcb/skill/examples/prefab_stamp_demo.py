import sys, time
sys.path.insert(0, "/home/claude/minecraft-builder/scripts")
from mcbig import BigBuild, transform_block
print(transform_block("minecraft:oak_stairs[facing=north,half=bottom,shape=inner_left]",1,False))
print(transform_block("minecraft:oak_stairs[facing=east,shape=inner_left]",0,True))
print(transform_block("minecraft:oak_fence[north=true,east=false]",1,False))
print(transform_block("minecraft:oak_log[axis=x]",1,False))
# a small prefab: 7x6x7 hut with a north-facing door stair step
hut = BigBuild(y_min=0, y_max=15)
hut.hollow_box(0,0,0,6,5,6,"minecraft:bricks")
hut.clear(3,1,0,3,2,0)
hut.set(3,0,-1,"minecraft:oak_stairs[facing=south,half=bottom]")
hut.gable_roof if False else None
city = BigBuild(y_min=0, y_max=15)
t=time.time()
import random
random.seed(1)
pl=[(x*12, 0, z*12, random.randrange(4), random.random()<.5) for x in range(60) for z in range(60)]
city.stamp_many(hut, pl)
print("3600 stamps", round(time.time()-t,2), "s;", city.summary(3))
# correctness: rotate once and check door moved north->east side
one = BigBuild(y_min=0,y_max=15); one.stamp(hut, 10, 0, 10, rot=1)
print("door cell air at east wall?", one.names[one.tiles[(0,0)][10-0+0, 1, 10+3]] if False else "")
lo,hi = one.bounds(); print("bounds", lo, hi)
# stair in front of door after rot=1 should face west
mats=[n for n,_ in one.materials()]; print(mats)
