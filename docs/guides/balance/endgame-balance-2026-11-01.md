# Endgame and boss balance pass (2026-11-01)

How it was checked: a small calculator (`tools/balance/endgame_model.py`) works out how long each fight lasts.
It uses each boss's real health, armor and Resistance from the mod, and two kinds of player:
- **Story-end player**: just beat the story, about 15 damage per second.
- **Maxed player**: level 60, full netherite, maxed sword/strength, awakened fruit, about 25 damage per second.

Fight times are rough guides, not stopwatch results. Full tables: `tools/balance/before.txt` and `after.txt`.

## What was wrong, and what changed

| Problem | Before | Fix | After |
|---|---|---|---|
| Roger raid could not be won solo, even maxed | ~35 min, limit 25 min | Roger 12000 to 8000 health, Rayleigh 7000 to 5000, Resistance III to II, limit 30 min | ~16 min maxed, ~27 min story-end |
| Rocks raid was a race against the clock | ~20 min maxed, ~34 min story-end | Resistance II to I | ~15 min maxed, ~25 min story-end |
| Raids in New Game+ 5 ran 30-40 min (fail) | NG+ gave raid bosses +25% health per cycle AND extra Resistance | Raids: +15% health per cycle, no NG Resistance (damage still +20% per cycle) | 13-28 min |
| Legend Ladder fights were long health sponges | Legend V Kaido ~12 min, Whitebeard ~13 min (maxed) | Health +15% per rung instead of +40% (hits still +15% per rung) | Legend V Kaido ~7 min, Whitebeard ~8 min |
| Early bosses were a joke in New Game+ | NG+1 Buggy 125 health, 4 seconds | Every boss gets at least 1000 + 300 x cycle health, 14 + 2 x cycle damage | NG+1 Buggy ~1 min, NG+5 ~3 min |

## Checked and left alone (already on target)
- Story bosses: ~20 s early, 1-2.5 min at the end (Imu ~1.5-2.5 min). Matches the 20-50 h plan.
- Hard and Expert: about 2x and 3.5x the Normal fight. Expert emperors 3.5-6.5 min, a good optional challenge.
- Emperor raids: 7-9 min maxed, 12-15 min story-end. Good.
- Rewards: raid loot once per 7 days, rematch Berries 15%, ladder prizes. No change needed; Berries are plentiful by the endgame anyway.
- Expert Xebec is the one long fight left (~8 min maxed, ~13 min story-end). He is the optional superboss, so kept as is.

## Not tested yet
The mod builds and the server starts fine. The new numbers have not been played in a real game yet.
Good test: `/ladder fight kaido 5` (ops), a New Game+ Buggy fight, and the Roger raid (`/endgame raid roger`).
