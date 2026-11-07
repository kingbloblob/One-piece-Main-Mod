import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx_polish
from gen_combat import run
run(sfx_polish.ALL, sys.argv[1], sys.argv[2:])
