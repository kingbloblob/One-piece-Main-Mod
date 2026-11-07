import sys; sys.path.insert(0, "/root")
from rcon import cmd
x1, z1, x2, z2 = map(int, sys.argv[1:5])
for x in range(x1, x2, 64):
    for z in range(z1, z2, 64):
        cmd(f"forceload add {x} {z} {x+63} {z+63}")
        cmd(f"fill {x} 54 {z} {x+63} 61 {z+63} minecraft:dirt")
        cmd(f"fill {x} 62 {z} {x+63} 62 {z+63} minecraft:grass_block")
print("ok")
