# Settings, Simple mode and modpacks

All server-side settings live in `config/onepiece.properties`. Change them in game (Esc > **One Piece Settings**, or Mod Menu), with `/onepiece_config` (operators), or by editing the file.

## Difficulty

`difficulty` now has five levels. It scales the health and damage of bosses, creatures, pirates and Marines, on top of the per-group multipliers.

| Level | Enemy health | Enemy damage |
|---|---|---|
| story (new) | 50% | 40% |
| easy | 75% | 60% |
| normal (default) | 100% | 100% |
| hard | 140% | 140% |
| brutal | 200% | 200% |

## Easy Play tab

| Setting | Default | What it does |
|---|---|---|
| `simple_mode` | off | For players new to the mod (see below). |
| `power_cooldowns` | 1 | Devil Fruit move and fighting style technique cooldowns. 0.5 = half as long. |
| `death_mastery_loss` | 0.1 | Share of Devil Fruit mastery lost on death (before awakening). |
| `safe_until_bosses` | 0 | The Navy, bounty hunters and Marine hunts wait until you've beaten this many story bosses. |

### Simple mode

When `simple_mode=on`:
- Navy raids, bounty hunters and Marine hunts wait until you beat your first story boss, then come half as often (hideout sieges and Marine-career ambushes also come half as often).
- Dying never costs Devil Fruit mastery.
- Move cooldowns are 25% shorter (on top of `power_cooldowns`).
- Haki and Pirate Level XP come 25% faster.

Three minutes into a single-player world, a one-time tip points new players to the Easy Play tab (not shown once Simple mode is on, or when settings are locked).

### Presets

One click (or `/onepiece_config preset <name>`) sets difficulty, Simple mode and the Easy Play settings together. Other settings are left alone.

| Preset | difficulty | simple_mode | power_cooldowns | death_mastery_loss | safe_until_bosses |
|---|---|---|---|---|---|
| story | story | on | 0.5 | 0 | 2 |
| simple | easy | on | 1 | 0 | 1 |
| standard | normal | off | 1 | 0.1 | 0 |
| challenge | hard | off | 1.25 | 0.2 | 0 |

`/onepiece_config preset` with no name lists them and marks the one that matches the current settings.

## For modpack makers

- Ship `config/onepiece.properties` in your pack. The mod keeps your values and adds new settings with comments when it updates.
- Set `lock_settings=on` (Multiplayer tab) to make the in-game settings screen read-only, so players keep your pack's balance. The file and `/onepiece_config` still work.
- On a server, the server's file is the one that counts.

## JEI

With JEI (31.16.0.90 for 26.3, which uses MezzConfig 0.6.8) installed:
- Every crafting station has its own recipe page, plus "Drops, Trades & Quests".
- Every Devil Fruit has an Information page: English name, type, power, both moves, and where to get it (leaf chance and which bosses drop it).
- Search finds fruits by English name, by a user's name and by type: try `Gum-Gum`, `Luffy` or `logia`.
- The mod adds no JEI or MezzConfig settings of its own; JEI's own config screen is unchanged.
