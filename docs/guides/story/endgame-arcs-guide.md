# Endgame story arcs: Elbaph, the Road to Laugh Tale and the Holy Land

Added November 6, 2026. The story now has **46 chapters** (was 42). Four new chapters, plus three new pages of the
true history, so Wano, Egghead and Elbaph all feed into the Void Century ending.

## The new order of the endgame

| # | Chapter id | Title | What you do |
|---|---|---|---|
| | `egghead` | Egghead, Island of the Future | (as before) |
| | `egghead_incident` | The Egghead Incident | (as before) Finishing it now also writes the page **Vegapunk's Broadcast** |
| new | `elbaph_arrival` | Elbaph, Land of the Giants | Climb the Great Tree (`elbaph_tree`), talk to Shanks there (he comes to you), read the giants' Poneglyph with your archaeologist (page **The Sun God's Island**) |
| new | `holy_knights` | The Holy Knights | Hold the Great Tree for 4 waves of Holy Knights, CP0 and Seraphim, then beat **Saint Gunko** and **Figarland Shamrock** (new bosses) |
| | `hachinosu` | Hachinosu | (as before, new intro) |
| new | `final_island` | The Road to Laugh Tale | Carry all four Road Poneglyph rubbings (moved here from Laugh Tale) |
| | `laugh_tale` | Laugh Tale | Reach Laugh Tale, hold the shore for 4 waves of Blackbeard Pirates (Teach joins the last), talk to Roger |
| | *post-game* `red_line`, `void_century` | | `void_century` now asks for **12** pages |
| new | `god_knights` | The Gates of the Holy Land | Reach Pangaea Castle, break through 4 waves of Holy Knights, beat Shamrock again on **Hard** |
| | `empty_throne` | The Empty Throne | (as before) Beat Imu |
| | `dawn` | The Dawn of the World | Gather all **13** pages, read the last Poneglyph at Laugh Tale |

Wano's last chapter (`wano`) now also writes the page **Oden's Log**.

## The true history: 13 pages (was 10)

- 9 Poneglyph pages as before, plus **The Sun God's Island** on the Poneglyph under Elbaph's Great Tree.
  If the tree has no Poneglyph, one rises next to you the first time you walk in (PoneglyphSites).
- 2 pages written by the story: **Oden's Log** (finish Wano) and **Vegapunk's Broadcast** (finish the Egghead Incident).
  Old saves that already finished those chapters get them quietly when they log in.
- 1 page from Imu, as before.
- `/endgame history` shows hints for missing pages, including "The story writes this one".
- The Dawn scene has one new line: Vegapunk's recording ends and the giants of Elbaph start to sing.

## New things

- **Boss Saint Gunko** (`gunko`): tier 5 titan, 1200 HP, the Holy Knight who leads the attack on Elbaph.
  Mechanics: judgment glare and Haki crash, ultimate "Sentence of the Holy Knights". Calls Holy Knights as her crew.
  Home `elbaph_tree`; bounty 600,000,000; wanted poster; boss intro and news taunts.
- **Boss Figarland Shamrock** (`shamrock`): tier 5 titan, 1400 HP, commander of the Holy Knights and Shanks's twin.
  Mechanics: Haki crash and judgment glare, ultimate "Judgment of the Holy Land". Home `elbaph_tree`; bounty 800,000,000.
  At phase 2 he lets loose his sword **Cerberus**: a big three-headed dog (the `cerberus` creature, 220 HP, 2.4x size,
  stronger on Hard/Expert) that fights beside him and leaves when the fight ends. Any boss can do this with the new
  `companion` fields in boss_fights.json.
- Neither is in any structure: only the story (or their poster) brings them.
- **NPC kit `holy_knight`**: white-and-gold uniforms with capes (6 skins), swords, Haki and pistols. Strong (120 HP).
- **Story raids** (StoryRaids): `holy_knights_raid` at Elbaph, `laugh_tale_race` at Laugh Tale (Blackbeard on the last wave),
  `pangaea_siege` at Pangaea Castle.
- **Flashbacks**: The Hundred-Year Duel (Dorry and Brogy), The Baby in the Treasure Chest (Shanks and Shamrock),
  The Man Who Could Read the Stones (Oden and Roger's crew).
- **Achievements**: Land of the Giants (`journey/elbaph`), Through the Holy Gates (`journey/god_knights`),
  No Ifs, No Buts (`pirate/gunko`), The Other Red Hair (`pirate/shamrock`). Hachinosu's achievement now hangs under Elbaph, and the Empty Throne's under the Holy Gates.

## For code

- New goal type `page` (field `page`): "has read this page of the true history". StoryData checks the page id at startup.
- `VoidCentury.Page` has a new `chapter` field: finishing that story chapter writes the page (`VoidCentury.chapterDone`, called from StoryTracker).
- New chapter field `goalsChanged` (a date). Goals are saved by position, so when a chapter's goal list changes, saves on that
  chapter start its goals fresh once (StoryProgress.placed adds the flag `goals:<chapter>:<date>`). Laugh Tale uses it now.
- Saves on any chapter keep their place by id, as before. A save that was already past Egghead skips the new Elbaph chapters,
  but still needs the Elbaph page for the Dawn.

## Testing

- `/story set <player> <n>` to jump to a chapter; `/endgame history` to see pages; `/endgame history all` (op) gives every page.
- Elbaph raid: stand inside `elbaph_tree` on chapter `holy_knights` in Survival.
