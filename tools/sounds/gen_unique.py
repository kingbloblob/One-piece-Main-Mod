import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx_unique
from gen_combat import run
run(sfx_unique.ALL, sys.argv[1], sys.argv[2:])
