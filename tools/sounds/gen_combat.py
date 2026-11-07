import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import save_ogg
import sfx_combat
import numpy as np

def trim(x, floor=0.003):
    """Cuts the silent end of the reverb tail (keeps files small), with a short fade."""
    loud = np.nonzero(np.abs(x) > floor)[0]
    end = min(len(x), (loud[-1] if len(loud) else len(x)) + 2205)
    x = x[:end].copy(); f = min(2205, end // 4); x[-f:] *= np.linspace(1, 0, f)
    return x

def run(sounds, out, only=()):
  for name, fn in sounds.items():
    if only and name.split('/')[1] not in only: continue
    t=time.time(); x=trim(fn()); assert x.ndim==1 and abs(x).max()<=1.0 and not (x!=x).any(), name
    save_ogg(x, f"{out}/{name}.ogg"); print(name, round(len(x)/44100,2),'s rms',round(float(np.sqrt((x**2).mean())),3), round(time.time()-t,1))

if __name__ == '__main__':
    run(sfx_combat.ALL, sys.argv[1], sys.argv[2:])
