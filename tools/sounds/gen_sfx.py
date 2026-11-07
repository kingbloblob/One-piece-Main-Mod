import sys, time
sys.path.insert(0, __import__('os').path.dirname(__file__))
from synth import save_ogg
import sfx
out = sys.argv[1]
for name, fn in sfx.ALL.items():
    t=time.time(); save_ogg(fn(), f"{out}/{name}.ogg"); print(name, round(time.time()-t,1))
