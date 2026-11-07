import struct, gzip
class Byte(int): pass
class Int(int): pass
class Double(float): pass
class Float(float): pass
class IntList(list): pass   # list of Int
class DoubleList(list): pass
def _tid(v):
    if isinstance(v, Byte) or isinstance(v, bool): return 1
    if isinstance(v, Int) or (isinstance(v, int)): return 3
    if isinstance(v, Float): return 5
    if isinstance(v, (Double, float)): return 6
    if isinstance(v, str): return 8
    if isinstance(v, list): return 9
    if isinstance(v, dict): return 10
    raise TypeError(type(v))
def _str(s):
    b = s.encode('utf-8'); return struct.pack('>H', len(b)) + b
def _payload(v):
    t = _tid(v)
    if t == 1: return struct.pack('>b', int(v))
    if t == 3: return struct.pack('>i', int(v))
    if t == 5: return struct.pack('>f', v)
    if t == 6: return struct.pack('>d', v)
    if t == 8: return _str(v)
    if t == 9:
        if isinstance(v, IntList): et = 3
        elif isinstance(v, DoubleList): et = 6
        elif v: et = _tid(v[0])
        else: et = 0
        out = struct.pack('>bi', et, len(v))
        for e in v:
            out += _payload(Double(e) if et == 6 else (Int(e) if et == 3 else e))
        return out
    if t == 10:
        out = b''
        for k, e in v.items():
            out += struct.pack('>b', _tid(e)) + _str(k) + _payload(e)
        return out + b'\x00'
def write(path, root):
    data = struct.pack('>b', 10) + _str('') + _payload(root)
    with gzip.open(path, 'wb') as f: f.write(data)
