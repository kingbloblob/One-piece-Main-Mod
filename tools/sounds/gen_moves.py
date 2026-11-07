import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import save_ogg
import sfx_moves
out = sys.argv[1]
for name, fn in sfx_moves.ALL.items():
    if len(sys.argv) > 2 and name.split('/')[1] not in sys.argv[2:]: continue
    t=time.time(); x=fn(); assert x.ndim==1 and abs(x).max()<=1.0 and not (x!=x).any(), name
    save_ogg(x, f"{out}/{name}.ogg"); print(name, round(len(x)/44100,2),'s', round(time.time()-t,1))
