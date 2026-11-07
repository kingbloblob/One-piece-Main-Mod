# Base building tools: player guide

This guide covers four new things: plan books for ship rooms and island bases, the Builder's Ledger (base upgrades paid for by your bounty), the Town Planner (found and grow your own town), and 35 regional furniture pieces.

## Plan books: Deck Plans and Island Base Plans

These are books of build plans. They show see-through "ghost" blocks where each piece of a room or base build goes. You place the real blocks yourself.

- **Recipes (shapeless):** Deck Plans = book + blue dye + oak boat. Island Base Plans = book + blue dye + campfire.
- **Use in the air:** turn to the next page. Sneak and use in the air to go back a page. The page shows the plan's name and what it does.
- **Use on a block:** lay the plan out there, facing the way you look. Ghost blocks appear, and chat lists what is still missing ("9 more fences or railings", and so on).
- **Sneak and use on a block:** hide the ghosts.
- The ghosts update as you build and fade after 10 minutes. The first time you finish each plan you get Berries and XP. The Ledger shows how many of the 22 you have built.

**Deck Plans (14 crew-ship rooms).** Each plan matches what that room needs on your crew home ship:

| Plan | What it does |
|---|---|
| Helm Station | The ship turns 15% faster |
| Galley | Your cook keeps the crew fed |
| Infirmary | Your doctor heals the crew |
| Chart Room | Sails 10% faster |
| Library | Old books, gold and gems in the haul |
| Workshop | Patches the hull, even mid-battle |
| Weapons Factory | Special cannon shot in the haul |
| Crow's Nest Gym | Counts as the Training Room: Strength I aboard |
| Music Bar | Everyone's haul +20% |
| Captain's Cabin | Needed for the Pirate Brig |
| Deck Garden | Mikan and herbs in the haul |
| Bath | Clears poison, hunger and other bad effects |
| Broadside Battery | Cannons count toward the ship's level |
| Crew Bunks | Each bunk lets one more crewmate live aboard |

**Island Base Plans (8 hideout builds):** Beach Camp, Crew Bunkhouse, Cookhouse, Cannon Battery, Lookout Tower (a finished Marine Watchtower with the Alarm Bell), Palisade Gate, Pirate Pier and Flag Square. Together they give a hideout what it needs to reach the next level.

## Builder's Ledger: base upgrades paid for by your bounty

Recipe: book + gold nugget + feather. Use it, or type `/base`, to open the upgrade menu. Click an upgrade to buy it, or type `/base build <upgrade>`.

Each tier needs three things:
- a big enough **bounty**, which unlocks it
- **Berries**, taken from your bag first and then from your town's treasury
- a **hideout level** at least as high as the tier

You must stand inside your own hideout claim to buy.

| Upgrade | Tiers | Effect | Bounty needed (I / II / III) |
|---|---|---|---|
| Palisade Walls | 3 | +8 / 16 / 28 raid defence | none / 30M / 150M |
| Gun Crews | 3 | Cannons reload faster, +1 defence per cannon per tier | 10M / 80M / 400M |
| Storehouse | 3 | Crew haul +15 / 30 / 50% | none / 50M / 200M |
| Lookout Post | 2 | +30 s warning before a Navy raid per tier, +4 defence | 20M / 100M |
| Sick Bay | 2 | Regeneration II at the hideout. Tier II heals crewmates too | 30M / 120M |
| Smuggler's Cove | 2 | Daily Berries that grow with your bounty | 50M / 300M |

## Town Planner: found your own town

Recipe: map + ink sac + stick.

1. **Found the town.** Place a bell in the Overworld and use the planner on it. The town can't be within 32 blocks of another town, and town bells must be 128 blocks apart.
2. **Pick a plot kind.** Use the planner in the air to cycle: House, Shop, Tavern, Restaurant, Farm, Dock, Shipyard, Smithy, Clinic, Library or Plaza. Chat tells you what each kind needs.
3. **Mark the plot.** Click two opposite corners on the ground, within 48 blocks of the bell. Plots can be 2 to 20 blocks a side (24 for a Plaza, Farm or Shipyard). While you hold the planner, every plot is outlined in coloured glass, and settled plots get gold corners.
4. **Build what the plot needs.** For example, a House needs a bed, a door and a light, and a Shop needs 2 counters, barrels or chests plus a light. When it's done the plot is settled. Two townsfolk move in for each House, and a worker moves in for each workplace (a merchant, bartender, cook, farmer and so on).
5. **Grow the town.** The town goes from Hamlet to Village, Town, Port Town and then City as you add houses and workplaces. The sneak + use report, or `/mytown`, says what the next level needs.
6. **Collect rent.** Townsfolk pay rent every day into the town treasury, and rent goes up with the town's level. Collect it by using the planner on your bell, or with `/mytown collect`.

**Other controls**
- Sneak and use the planner on a plot to remove it.
- `/mytown name <name>` renames the town.
- `/mytown culture <style>` sets how new townsfolk dress and what the market sells (east_blue, wano, alabasta and others).
- `/mytown abandon confirm` gives up the town.

**Town upgrades** (bought from the Ledger or with `/mytown upgrade <id>`):

| Upgrade | Cost | Needs | Effect |
|---|---|---|---|
| Market Charter | 150 Berries | Village and a settled Shop | Opens a town market |
| Festival Grounds | 120 Berries | Village and a settled Plaza | Holds the town's festival |
| Harbor Office | 200 Berries | Town and a settled Dock | Sailors and a shipwright move in |
| Lamplighters | 250 Berries | Town | Rent ×1.25 |

## Regional furniture (35 new pieces)

All 35 are crafted at a crafting table from their region's materials (look them up in JEI). They also show in the journal.

| Region | Pieces |
|---|---|
| Wano | Tansu chest (storage), engawa bench, golden byobu screen, hibachi brazier, kakejiku scroll |
| Alabasta | Divan, brass oil lamp, clay water jar, rug, sand floor pillow |
| Skypiea | Cloud sofa, cloud table, cloud stool, Shandian drum, sky shell lamp |
| Fishman Island | Coral throne chair, coral table, pearl lamp, giant clam basin, bubble dome lamp |
| Marines | Marine desk (storage), marine locker (storage), flag stand, office chair, supply crate |
| Whole Cake | Candy chair, cake table, lollipop lamp, cookie cabinet (storage), cupcake stool |
| Water 7 | Street lamp, canal bench, blueprint board, shipwright tool chest (storage), mooring bollard |

## Admin commands (operators)
- `/base set <upgrade> <tier>` sets an upgrade's tier.
- `/mytown rent` makes the townsfolk pay a day's rent now.
