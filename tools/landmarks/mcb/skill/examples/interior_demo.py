import sys; sys.path.insert(0,"/home/claude/minecraft-builder/scripts")
from mcbig import BigBuild
import mcparts as P
b=BigBuild(y_min=-2,y_max=30,seed=2)
W,D,H=30,20,5
b.box(0,-1,0,W,-1,D,"minecraft:stone_bricks")              # floor slab
b.walls(0,0,0,W,H,D,"minecraft:white_terracotta")           # outer walls (y 0..H)
rooms,doors=P.bsp_rooms(b,1,1,W-1,D-1,0,H,"minecraft:oak_planks",min_room=5,seed=7)
kinds=["living","bedroom","workshop","kitchen","storage","library"]
for i,r in enumerate(rooms): P.furnish_room(b,r,0,kinds[i%len(kinds)],height=H,seed=i,doors=doors)
b.box(0,H+1,0,W,H+1,D,"minecraft:stone_bricks")             # ceiling/roof deck
print(len(rooms),"rooms", rooms)
b.save_function("/tmp/interior.mcfunction")
# top view with the roof deck removed for inspection
b2=b
b2.clear(0,H+1,0,W,H+1,D)
b2.render_top("/tmp/interior_top.png",px=12,max_side=620)
print(b2.summary(12))
