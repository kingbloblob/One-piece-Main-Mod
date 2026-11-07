import sys, socket, struct
# fast rcon block finder: findblk.py block y x1 z1 x2 z2 step
def pkt(s, i, t, body):
    d = struct.pack("<ii", i, t) + body.encode() + b"\0\0"
    s.sendall(struct.pack("<i", len(d)) + d)
    n = struct.unpack("<i", s.recv(4))[0]; r = b""
    while len(r) < n: r += s.recv(n - len(r))
    return r[8:-2].decode()
s = socket.create_connection(("localhost", 25575)); pkt(s, 1, 3, "test")
blk, y, x1, z1, x2, z2, step = sys.argv[1], int(sys.argv[2]), *map(int, sys.argv[3:8])
hits = []
for x in range(x1, x2 + 1, step):
    for z in range(z1, z2 + 1, step):
        if "passed" in pkt(s, 2, 2, f"execute if block {x} {y} {z} {blk}"): hits.append((x, z))
print(len(hits), hits[:5])
if hits: print("centre", sum(h[0] for h in hits) / len(hits), sum(h[1] for h in hits) / len(hits))
