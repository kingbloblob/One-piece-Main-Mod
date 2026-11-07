"""seastone_deep_mine: the design lives in tools/landmarks/mcb/seastone_deep_mine.py; this wrapper lets make_structures.py
run it through the cave pipeline (cave finish, springproof rock, cull, structure json)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "landmarks"))
from mcb.seastone_deep_mine import *  # noqa
from mcb.seastone_deep_mine import build, TITLE, CUTS, TILER, SID  # noqa
