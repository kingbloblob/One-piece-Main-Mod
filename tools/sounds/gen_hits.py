import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_combat, sfx_hits
gen_combat.run(sfx_hits.ALL, sys.argv[1], sys.argv[2:])
