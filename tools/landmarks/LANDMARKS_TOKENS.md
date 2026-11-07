# Working on landmarks: keep it cheap (tools/landmarks/LANDMARKS_TOKENS.md)

Every turn re-reads the whole thread, so a file, image or long print you pull in is paid for again on every
later turn. Most of the token bill comes from that, not from the build itself.

- **Read the index, not the kits.** `API.md` lists every kit function (canvas, archkit, townkit, landkit,
  interiors, finish, mcb/*). Run `python3 apiindex.py --check` first and `python3 apiindex.py` if it is stale.
  For one function: `grep -n "def name" file.py`, then `sed -n` that range. Never `cat` a kit or a landmark module.
- **Read one guide section.** `grep -n "^#" BUILDING_GUIDE.md`, then `sed -n` just the section the job needs
  (e.g. 4 Windows, 13 Roofs, 14d Wano). Do not read the whole guide or the project `README.md`; grep them for the part you need.
- **Copy the nearest landmark, don't start blank.** Find a similar one (`grep -l "townkit.house" *.py`), read its
  top (constants, layout), and change the layout numbers. New helper code goes into a kit so it is written once.
- **One command per round:** `python3 make.py <id> --sheet 2>&1 | tail -15`. Read the finish counts and any
  `UNKNOWN BLOCK IDS` / `WARN` lines first. Look at `<id>_sheet.png` (all views in one 1000 px image) only when the
  numbers pass, and at most once per round; never open the separate `_se`/`_nw`/`_cut` renders unless the sheet
  shows a problem you need to zoom into.
- **At most two fix rounds,** then deliver and ask ryan for in-game feedback.
- **Edit, don't rewrite** a module: change the numbers or the one function with a targeted edit.
- **One landmark per thread.** When it is done, write what is left into the module's docstring or
  `mcb/dossiers/<id>.md`, and start the next landmark in a new thread.
