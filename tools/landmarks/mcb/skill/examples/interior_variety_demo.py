import sys; sys.path.insert(0,"/home/claude/minecraft-builder/scripts")
from mcbig import BigBuild
import mcparts as P
def shell(seed, W=34, D=22, H=5):
    b=BigBuild(y_min=-2,y_max=30,seed=seed)
    b.box(0,-1,0,W,-1,D,"minecraft:stone_bricks"); b.walls(0,0,0,W,H,D,"minecraft:white_terracotta")
    rooms,doors=P.bsp_rooms(b,1,1,W-1,D-1,0,H,"minecraft:oak_planks",min_room=5,seed=seed)
    b.box(0,H+1,0,W,H+1,D,"minecraft:stone_bricks")
    return b,rooms,doors,H
# 1) the failure mode: spam brewing stands and cake on every table
b,rooms,doors,H=shell(1)
for r in rooms:
    x1,z1,x2,z2=r
    for x in range(x1+1,x2,3):
        b.set(x,0,z1+1,"minecraft:oak_fence"); b.set(x,1,z1+1,"minecraft:oak_slab[type=bottom]")
        b.set(x,2,z1+1,"minecraft:brewing_stand"); b.set(x+1,2,z1+1,"minecraft:cake")
txt,ok=P.audit_props(b,rooms,0,H); print("SPAM VERSION ->", "OK" if ok else "REJECTED"); print("\n".join(txt.splitlines()[:6]))
# 2) new generator with one tracker for the whole building
for seed in (3,4,5):
    b,rooms,doors,H=shell(seed)
    tr=P.PropTracker(seed); kinds=["living","bedroom","workshop","kitchen","storage","library"]
    for i,r in enumerate(rooms): P.furnish_room(b,r,0,kinds[i%6],height=H,seed=seed*100+i,doors=doors,tracker=tr)
    txt,ok=P.audit_props(b,rooms,0,H)
    print(f"seed {seed}:", txt.splitlines()[-1], "| warnings:", [l for l in txt.splitlines() if l.startswith(('FAIL','WARN'))][:3], "| tracker:", dict(tr.counts.most_common(5)))
