import sys, time, resource
sys.path.insert(0, "/home/claude/minecraft-builder/scripts")
import numpy as np
from mcbig import BigBuild
t0=time.time()
b = BigBuild(seed=2, y_min=0, y_max=255)
R=200
b.cylinder(0,0,0,R,40,"minecraft:stone_bricks")
b.tapered_cylinder(0,41,0,120,R-10,60,"minecraft:smooth_stone",hollow=True,thickness=3)
rng=np.random.default_rng(1)
roofs=["minecraft:red_terracotta","minecraft:orange_terracotta","minecraft:brown_terracotta"]
walls=["minecraft:white_concrete","minecraft:sandstone","minecraft:smooth_sandstone"]
n=0
while n<3500:
    x=int(rng.integers(-180,170)); z=int(rng.integers(-180,170))
    if x*x+z*z>185*185: continue
    w=int(rng.integers(5,9)); d=int(rng.integers(5,9)); h=int(rng.integers(4,8))
    y0=41
    b.hollow_box(x,y0,z,x+w,y0+h,z+d,walls[n%3])
    for i in range((d+1)//2+1):
        b.fill(x-1,y0+h+1+i,z+i-1,x+w+1,y0+h+1+i,z+i-1,roofs[n%3]) if False else None
    for i in range(min(w,d)//2+1):
        b.fill(x+i,y0+h+1+i,z+i,x+w-i,y0+h+1+i,z+d-i,roofs[n%3])
    n+=1
print("build", round(time.time()-t0,1),"s")
print(b.summary(5))
t1=time.time()
st=b.save_sharded("out_demo", namespace="s", name="big", origin=(0,64,0), max_commands=4000)
print("export", round(time.time()-t1,1),"s", st)
print("peak MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
