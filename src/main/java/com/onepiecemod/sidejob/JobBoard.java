package com.onepiecemod.sidejob;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.town.TownsfolkEntity;

/**
 * Makes up side jobs. What a townsperson asks for depends on their job (a fisher wants fish, a doctor wants
 * herbs, a bartender knows who has a price on their head), and how big it is depends on how far the player
 * is in the story: East Blue jobs are small, New World contracts are against 300,000,000+ Berry pirates.
 */
final class JobBoard {
	private JobBoard() {
	}

	/** 0 = East Blue, 1 = Paradise, 2 = Summit War and the two years, 3 = New World and later. */
	static int tier(ServerPlayer player) {
		StoryProgress story = StoryProgress.orStart(player);
		if (!story.reached("drum_island")) {
			return 0;
		}
		if (!story.reached("amazon_lily")) {
			return 1;
		}
		return story.reached("fishman_island") ? 3 : 2;
	}

	static String tierName(int tier) {
		return switch (tier) {
			case 0 -> "East Blue";
			case 1 -> "Paradise";
			case 2 -> "Summit War";
			default -> "New World";
		};
	}

	/** Jobs whose people hear about Wanted pirates (the bar, the docks, the old folks who know everyone). */
	static boolean postsContracts(String job) {
		return switch (job) {
			case "bartender", "sailor", "foreign_trader" -> true;
			default -> false;
		};
	}

	// ---- Town requests ----

	private record Want(String item, int count, String text) {
	}

	private static List<Want> wants(String job) {
		return switch (job) {
			case "farmer" -> List.of(new Want("minecraft:wheat", 16, "My harvest is short and the tax man comes tomorrow."),
					new Want("minecraft:bone_meal", 12, "The soil is tired. Bone meal would wake it up."),
					new Want("minecraft:carrot", 12, "The festival needs carrots and the rabbits ate mine."));
			case "fisher" -> List.of(new Want("minecraft:cod", 8, "The nets came up empty all week. Could you catch some cod?"),
					new Want("minecraft:salmon", 6, "A restaurant ordered salmon and I've got none."),
					new Want("minecraft:string", 12, "My nets are in tatters. String, please!"));
			case "merchant" -> List.of(new Want("minecraft:paper", 16, "I'm out of paper for receipts and contracts."),
					new Want("minecraft:leather", 8, "A buyer from the Grand Line wants leather goods."));
			case "bartender" -> List.of(new Want("minecraft:sugar_cane", 16, "No sugar cane, no rum. No rum, angry pirates."));
			case "cook" -> List.of(new Want("minecraft:egg", 12, "A cook without eggs is like a pirate without a ship!"),
					new Want("minecraft:sugar", 12, "I promised the kids a cake. I've got no sugar."),
					new Want("minecraft:cocoa_beans", 8, "Cocoa beans for a chocolate dish. Chopper would love it."));
			case "smith" -> List.of(new Want("minecraft:iron_ingot", 8, "A swordsman ordered a blade and I'm out of iron."),
					new Want("minecraft:coal", 16, "The forge is going cold. Coal, quick!"),
					new Want("minecraft:gold_ingot", 4, "Gold for a captain's fancy hilt. Don't ask."));
			case "shipwright" -> List.of(new Want("minecraft:oak_log", 24, "A Going Merry-sized hole in a hull. I need logs."),
					new Want("minecraft:iron_ingot", 6, "Nails and bolts. Iron, lots of it."),
					new Want("minecraft:string", 16, "Rigging snapped in the last storm. String for new ropes!"));
			case "doctor" -> List.of(new Want("minecraft:sweet_berries", 16, "Berries for a fever medicine. Doctor Kureha's recipe."),
					new Want("minecraft:honey_bottle", 3, "Honey soothes a sailor's throat. Bring me some."),
					new Want("minecraft:glow_berries", 8, "Glow berries help with the Grand Line's strange sicknesses."));
			case "scholar" -> List.of(new Want("minecraft:paper", 12, "I'm copying old texts and ran out of paper."),
					new Want("minecraft:ink_sac", 6, "Ink! The history won't write itself."),
					new Want("minecraft:book", 3, "Books for the library. Ohara's were all burned..."));
			case "dancer" -> List.of(new Want("minecraft:poppy", 8, "Red flowers for my festival costume!"),
					new Want("minecraft:dandelion", 8, "Yellow flowers for the stage. Please?"));
			case "child" -> List.of(new Want("minecraft:cookie", 4, "Cookies! Mom said no but YOU can bring them, right?"));
			default -> List.of(new Want("minecraft:bread", 8, "The old folks' home is out of bread."),
					new Want("minecraft:cod", 6, "Fish for the village feast."));
		};
	}

	private record Keepsake(String item, String name, String text) {
	}

	private static List<Keepsake> keepsakes(String job) {
		return switch (job) {
			case "fisher" -> List.of(new Keepsake("minecraft:tripwire_hook", "Grandpa's Lucky Hook", "A Sea King knocked my boat over and my lucky hook went overboard."));
			case "merchant" -> List.of(new Keepsake("minecraft:book", "The Merchant's Ledger", "Pirates robbed my cart and threw my ledger away."));
			case "scholar" -> List.of(new Keepsake("minecraft:paper", "A Poneglyph Sketch", "My sketch of an old stone blew away in the wind."));
			case "dancer" -> List.of(new Keepsake("minecraft:feather", "A Festival Fan", "I lost my fan during the last festival."));
			case "child" -> List.of(new Keepsake("minecraft:wooden_sword", "My Toy Sword", "I was playing Zoro and lost my sword!"),
					new Keepsake("minecraft:slime_ball", "My Lucky Marble", "My marble rolled away. It's my LUCKY one."));
			case "elder" -> List.of(new Keepsake("minecraft:gold_nugget", "A Wedding Ring", "My late wife's ring. I dropped it on my walk."),
					new Keepsake("minecraft:clock", "An Old Pocket Watch", "My pocket watch. It stopped the day Roger died."));
			case "sailor" -> List.of(new Keepsake("minecraft:compass", "An Old Log Pose", "My first Log Pose fell out of my pocket."));
			default -> List.of(new Keepsake("minecraft:name_tag", "A Lost Keepsake", "I lost something precious near the edge of town."));
		};
	}

	/** A town request: fetch something, chase off pirates or monsters, or find something lost. */
	static SideJob request(ServerPlayer player, TownsfolkEntity giver, String townName, RandomSource random) {
		int tier = tier(player);
		String job = giver.jobId();
		int roll = random.nextInt(10);
		int pay = new int[] {10, 18, 28, 40}[tier] + random.nextInt(5);
		BlockPos origin = giver.blockPosition();
		if (roll < 4) {
			List<Want> list = wants(job);
			Want want = list.get(random.nextInt(list.size()));
			int count = Math.max(1, Math.round(want.count * (1f + tier * 0.4f)));
			String itemName = new ItemStack(CharacterData.item(want.item)).getHoverName().getString();
			return new SideJob(newId(), "FETCH", giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, origin,
					want.item, count, 0, "Bring " + count + " " + itemName, want.text, pay, 0);
		}
		if (roll < 6) {
			int count = 4 + tier * 2;
			return new SideJob(newId(), "CULL_PIRATES", giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, origin,
					"", count, 0, "Defeat " + count + " pirates", "Pirates keep robbing us on the roads. Teach them a lesson!", pay + 4, 0);
		}
		if (roll < 7) {
			int count = 6 + tier * 2;
			return new SideJob(newId(), "CULL_MONSTERS", giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, origin,
					"", count, 0, "Defeat " + count + " monsters", "Monsters come out at night and scare the whole town.", pay, 0);
		}
		List<Keepsake> list = keepsakes(job);
		Keepsake keepsake = list.get(random.nextInt(list.size()));
		BlockPos spot = awayFrom(origin, 50, 130, random);
		return new SideJob(newId(), "LOST", giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, spot,
				keepsake.item, 1, 0, "Find " + keepsake.name, keepsake.text, pay + 2, 0);
	}

	// ---- Wanted contracts ----

	private static final String[] FIRST = {"Barlow", "Gin", "Moja", "Rocco", "Vesta", "Hackle", "Dorian", "Sable", "Kuro", "Bonz",
			"Mirella", "Tango", "Garo", "Pell", "Ishi", "Brandt", "Corsa", "Fenna", "Umo", "Rizzo", "Sasha", "Oddo", "Jinx", "Marlo"};
	private static final String[] EPITHET = {"Red-Eye", "Iron Jaw", "the Butcher", "Rattlesnake", "Two-Swords", "the Smiling",
			"Blackwater", "Cannonball", "the Wolf", "Grinning", "Bone-Crusher", "the Ghost", "Stormcaller", "Silver Tooth",
			"Mad Dog", "the Gambler", "Salt-Beard", "Hellfire", "the Shark", "Thousand-Knives"};
	private static final String[] PLACE = {"a smugglers' cove", "an abandoned fort", "a hidden camp", "a wrecked ship on the shore",
			"a sea cave", "a burned-out village", "a pirate camp"};

	private static final String[][] BEASTS = {
			{},
			{"bananawani", "sand_scorpion", "lapahn", "tyrannosaurus"},
			{"humandrill", "cerberus", "basilisk", "nola"},
			{"manticore", "punk_hazard_dragon", "basilisk", "cerberus"}
	};

	/** A Wanted contract. The target waits 200 to 450 blocks away; it shows up when you get close. */
	static SideJob contract(ServerPlayer player, TownsfolkEntity giver, String townName, RandomSource random) {
		int tier = tier(player);
		List<String> kinds = new ArrayList<>(List.of("CREW", "CREW"));
		if (tier >= 1) {
			kinds.add("FRUIT");
			kinds.add("BEAST");
		}
		if (StoryProgress.orStart(player).completed("impel_down")) {
			kinds.add("CONVICT");
		}
		String kind = kinds.get(random.nextInt(kinds.size()));
		long[] low = {5_000_000L, 30_000_000L, 100_000_000L, 300_000_000L};
		long[] high = {20_000_000L, 90_000_000L, 300_000_000L, 800_000_000L};
		long bounty = (low[tier] + (long) (random.nextDouble() * (high[tier] - low[tier]))) / 1_000_000L * 1_000_000L;
		int pay = new int[] {22, 38, 58, 85}[tier] + random.nextInt(8);
		BlockPos origin = giver.blockPosition();
		BlockPos spot = awayFrom(origin, 200, 450, random);
		String person = "\"" + EPITHET[random.nextInt(EPITHET.length)] + "\" " + FIRST[random.nextInt(FIRST.length)];
		String place = PLACE[random.nextInt(PLACE.length)];
		return switch (kind) {
			case "FRUIT" -> new SideJob(newId(), kind, giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, spot,
					"", 1, 0, "Wanted: " + person, "A Devil Fruit user hiding out at " + place + ". Careful, they've eaten something nasty.",
					pay + 6, bounty);
			case "BEAST" -> {
				String[] pool = BEASTS[Math.max(1, tier)];
				String beast = pool[random.nextInt(pool.length)];
				String beastName = "Man-Eater " + capitalize(beast.replace('_', ' '));
				yield new SideJob(newId(), kind, giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, spot,
						beast, 1, 0, "Wanted: the " + beastName, "A huge beast keeps attacking travelers. The town put a price on it.",
						pay, bounty / 4 / 1_000_000L * 1_000_000L);
			}
			case "CONVICT" -> new SideJob(newId(), kind, giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, spot,
					"pirate_captain", 1, 0, "Wanted: Escaped Convict " + person,
					"Broke out of Impel Down when the Straw Hat went in. Hiding at " + place + ".", pay + 10, bounty);
			default -> new SideJob(newId(), "CREW", giver.getUUID().toString(), giver.getDisplayName().getString(), townName, origin, spot,
					"pirate_captain", 2 + tier, 0, "Wanted: " + person, "Captain of a nasty crew camped at " + place + ".", pay, bounty);
		};
	}

	// ---- Helpers ----

	private static String newId() {
		return UUID.randomUUID().toString().substring(0, 8);
	}

	private static String capitalize(String text) {
		StringBuilder out = new StringBuilder();
		for (String word : text.split(" ")) {
			if (!word.isEmpty()) {
				out.append(out.length() > 0 ? " " : "").append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
			}
		}
		return out.toString();
	}

	static BlockPos awayFrom(BlockPos from, int min, int max, RandomSource random) {
		double angle = random.nextDouble() * Math.PI * 2;
		int distance = min + random.nextInt(max - min + 1);
		return new BlockPos(Mth.floor(from.getX() + Math.cos(angle) * distance), from.getY(), Mth.floor(from.getZ() + Math.sin(angle) * distance));
	}

	/** "north-east" for a step from a to b. */
	static String direction(BlockPos from, BlockPos to) {
		double angle = Math.toDegrees(Math.atan2(to.getZ() - from.getZ(), to.getX() - from.getX())); // 0 = east, 90 = south
		String[] names = {"east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"};
		int index = Math.floorMod((int) Math.round(angle / 45.0), 8);
		return names[index];
	}
}
