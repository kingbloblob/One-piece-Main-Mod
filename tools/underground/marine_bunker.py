"""marine_bunker v2: the design lives in tools/landmarks/mcb/marine_bunker.py (Builder skill redo); this wrapper lets make_structures.py
run it through the cave pipeline (cave finish, springproof rock, cull, structure json)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "landmarks"))
from mcb.marine_bunker import *  # noqa
from mcb.marine_bunker import build, TITLE, CUTS, TILER, SID  # noqa
