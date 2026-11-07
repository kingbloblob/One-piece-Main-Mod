import socket, struct, sys
def pkt(i, t, s): b = s.encode() + b'\x00\x00'; return struct.pack('<iii', len(b) + 8, i, t) + b
port = int(sys.argv[1])
s = socket.create_connection(('127.0.0.1', port)); s.settimeout(600)
def rd():
    n = struct.unpack('<i', s.recv(4))[0]; d = b''
    while len(d) < n: d += s.recv(n - len(d))
    return d[8:-2].decode(errors='replace')
s.send(pkt(1, 3, 'test')); rd()
for c in sys.argv[2:]:
    s.send(pkt(2, 2, c)); print(rd())
