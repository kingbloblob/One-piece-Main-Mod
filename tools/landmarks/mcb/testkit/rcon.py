import socket, struct, sys, time
def cmd(c, host="127.0.0.1", port=25575, pw="test"):
    s = socket.create_connection((host, port), timeout=120)
    def send(i, t, body):
        p = struct.pack("<ii", i, t) + body.encode() + b"\x00\x00"
        s.sendall(struct.pack("<i", len(p)) + p)
    def recv():
        n = struct.unpack("<i", s.recv(4))[0]; d = b""
        while len(d) < n: d += s.recv(n - len(d))
        return d[8:-2].decode(errors="replace")
    send(1, 3, pw); recv()
    send(2, 2, c); out = recv(); s.close(); return out
if __name__ == "__main__":
    for c in sys.argv[1:]: print(cmd(c))
