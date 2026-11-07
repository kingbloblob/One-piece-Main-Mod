"""treasure_grotto v2: the design lives in tools/landmarks/mcb/treasure_grotto.py (Builder skill redo); this wrapper lets make_structures.py
run it through the cave pipeline (cave finish, springproof rock, cull, structure json)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "landmarks"))
from mcb.treasure_grotto import *  # noqa
from mcb.treasure_grotto import build, TITLE, CUTS, TILER, SID  # noqa
