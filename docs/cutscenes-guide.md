# Boss intros and flashbacks

**Boss intros.** The first time a big boss starts a fight with you, black cinema bars slide in, the boss's name and title sweep across the screen, and they say a line. Your view turns gently toward them. The boss stands still and doesn't attack while it plays (about 4 seconds), so it is never a free hit. It ends early if you press **Enter** (Skip cutscene) or if anyone hits the boss. Each intro plays once per player; after that the fight starts right away.

**Flashbacks.** When certain story chapters start, a memory plays: a warm old-photo tint, the title, then a few lines typed out one by one (Roger's execution, Shanks's hat, Bell-mère, Zeff's rock, Hiriluk, Noland, Ohara, the Roger Pirates, Ace, Whitebeard, after Marineford, Fisher Tiger, Kyros, Oden, God Valley, Kuma, Laugh Tale, Joy Boy, the Empty Throne). A flashback waits while a screen (inventory, death screen) is open, so you don't miss it.

**Commands.** `/flashback` lists the memories you have found (click one to watch it again). `/flashback reset` makes intros and flashbacks play again.

**Settings** (One Piece Settings > Screen, or config/onepiece-client.properties): `cutscenes` on / bosses_only / flashbacks_only / off, and `cutscene_camera` on / off. The skip key can be changed under Options > Controls.

**Editing.** All text is in `src/main/resources/onepiece/cutscenes.json`: `bosses` (title, line, colour) and `flashbacks` (chapter id, title, when, lines as "Speaker: text" or narration).

Code: `com.onepiecemod.cutscene` (CutsceneFeature, BossIntros) and `cutscene.client` (CutsceneClient, CutsceneOverlay). Hooks: CharacterEntity (intro start, hold, hit ends it), StoryTracker.startChapter, OnePieceMod/OnePieceModClient init, ClientConfig options, lang keys.
