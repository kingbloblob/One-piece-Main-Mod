import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_combat, sfx_world
gen_combat.run(sfx_world.ALL, sys.argv[1], sys.argv[2:])
