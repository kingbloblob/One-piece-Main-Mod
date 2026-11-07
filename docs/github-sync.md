# Keeping the shared source and GitHub in step

_Written 2026-11-01, after the "Merge shared source with GitHub main" thread._

## What went wrong

The mod lives in two places:

- **Shared source**: the `source/` folder in the project files. The playable jar is built from this.
- **GitHub main**: `ryanmTCG/one-piece-mod`. Pull requests land here.

Nothing kept the two in step, so by 1 November 229 files differed. Three things caused it:

1. **Some threads only opened a pull request.** Naval battles (`/seabattle fleet`, enemy boarders,
   gun crews), cannon and gun add-ons, `util/Motion`, the `fist_weapons`/`holds_dial` tags, two naval
   achievements, the Onigashima redo and about 60 other edits were merged on GitHub but never copied
   into the shared source. Your jar didn't have them.
2. **Some threads only saved to the shared source.** The release prep (MIT license, new icon,
   CHANGELOG, longer mod description) never reached GitHub.
3. **A merge kept the older side.** When PR #4 (build batch 10) was combined with main, the new
   Angel Beach, Banaro Island, Chocolate Town and hideout flag builds were swapped back for older
   versions. GitHub had the old builds after that, and the shared source still had the new ones.

There was also a trap waiting. `tools/push-github.sh` replaces GitHub with whatever is in the
shared folder. Running it during the drift would have deleted all the GitHub-only work.

## How it was fixed

For each of the 229 files, the merge checked which side was newer. If the shared copy matched an
older GitHub version, GitHub's was newer. If it matched nothing on GitHub, the shared copy was
newer. Images that differed only in how they were saved, with the same pixels, were left alone.
The playtest fixes from PR #39 went in on top. The result compiled, the server reached "Done", and
it was then saved into the shared source and pushed to GitHub.

## How to avoid it from now on

- **One rule for every thread:** whatever lands in one place goes into the other in the same thread.
  If a thread merges a pull request, it also runs `tools/pull-github.sh`.
- **After a PR merges:** `sh /mnt/project-files/one-piece-mod/tools/pull-github.sh`.
  It copies GitHub's changes into the shared source. If a file was edited in both places, it is
  flagged as a CONFLICT and left alone so someone can merge it by hand. Then build and boot-test.
- **Before backing up to GitHub:** `sh /mnt/project-files/one-piece-mod/tools/push-github.sh "message"`.
  It now **refuses to push** if GitHub has changes the shared source is missing, and names those files.
  It records the last commit it synced in `/mnt/project-files/one-piece-mod/.github-last-sync`.
- **When combining two versions, never "keep main" or "keep mine" for every file.** Compare each
  file and keep the newer one.

## 4 November 2026: PRs #51 to #60

After PRs #51 to #60 merged, `pull-github.sh` brought most of them in, but 40 files were flagged as
CONFLICT and had to be merged by hand:

- `OnePieceMod.java`: the shared copy was missing `DungeonBosses.initialize()`, so the five dungeon
  mini-bosses never switched on. Took GitHub's version (log now says "Dungeon mini-bosses: 5").
- `onepiece_advancements/lang/en_us.json`: GitHub's copy had every shared entry plus the two dungeon
  achievements. Took GitHub's.
- 36 PNGs (dungeon NPC skins, Collector's Log, three music discs): same pixels on both sides, only
  saved differently. **The project-files folder re-saves PNGs when they are written**, so byte
  comparison always flags them. `pull-github.sh` now compares PNGs by pixels instead.
- `tools/advancements/gen_advancements.py`: kept the shared late-game rewards entries and added
  GitHub's dungeon entries.
- `tools/npcs/gen_kits.py`: took GitHub's (dungeon kits, source-dir argument) but kept the Pacifista
  brawler loadout from PR #45, which GitHub's copy had lost.

Compiled and boot-tested (server reached Done) from a copy, then saved, jar rebuilt, sync point
moved to GitHub main. The two generator scripts and the `pull-github.sh` fix went back to GitHub as
a pull request.

Cloud build tip: Maven Central often answers 429. Put a mirror in `~/.gradle/init.d/` that rewrites
`repo.maven.apache.org` to `https://maven-central.storage-download.googleapis.com/maven2/`.
