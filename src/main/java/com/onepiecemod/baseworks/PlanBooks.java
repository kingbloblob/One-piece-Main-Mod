package com.onepiecemod.baseworks;

import java.util.List;
import java.util.Map;

import net.minecraft.core.Direction;
import net.minecraft.tags.BlockTags;

/**
 * The pages of the two plan books.
 *
 * Deck Plans: every room of a crew home ship (see the crewship package's ShipRoom), each drawn so that building
 * it exactly as shown makes a room the Ship's Log counts, plus a gun deck and a crow's nest gym like Zoro's.
 *
 * Island Base Plans: the pieces of a pirate hideout (see the hideout package's HideoutLevels): a beach camp,
 * a bunkhouse, a cookhouse, a cannon battery, a lookout tower that is a working Marine Watchtower, a palisade
 * gate, a pier and a flag square. Building them is the quickest way up the hideout levels.
 *
 * How to read a drawing: see {@link LayoutPlan}. Top row = far side, bottom row = right in front of you.
 */
public final class PlanBooks {
	private PlanBooks() {
	}

	public static final List<LayoutPlan> DECK = List.of(
			new LayoutPlan("helm", "Helm Station", "The Ship's Wheel with a railing round it. Your helmsman works here: the ship turns 15% faster.")
					.exact('e', "a Ship's Wheel", "onepiece:ships_wheel", Direction.SOUTH)
					.layer("FFFFF",
							"F.e.F",
							"F...F")
					.layer("T...T",
							".....",
							".....")
					.tip("Build it near the stern, where the captain can see the whole deck."),

			new LayoutPlan("galley", "Galley", "Sanji's kitchen: a stove with a sink, counters and cupboards. Your cook works here and keeps the crew fed.")
					.key('u', "cupboards", LayoutPlan.suffix("_cupboard"), "onepiece:spruce_cupboard", Direction.SOUTH)
					.key('c', "counters", LayoutPlan.suffix("_counter"), "onepiece:spruce_counter", Direction.SOUTH)
					.exact('k', "a Galley Sink", "onepiece:galley_sink", Direction.SOUTH)
					.exact('p', "a Cooking Pot", "onepiece:cooking_pot", Direction.SOUTH)
					.layer("uKkcu",
							".....",
							"st.ts")
					.layer("...pT",
							".....",
							".....")
					.tip("Any smoker, furnace, Iron Stove or Ship's Galley works as the stove."),

			new LayoutPlan("infirmary", "Infirmary", "Chopper's sick bay: a medicine cabinet between two hammocks. Your doctor heals the crew here.")
					.key('m', "a Medicine Cabinet or brewing stand", LayoutPlan.ids("onepiece:medicine_cabinet", "minecraft:brewing_stand"),
							"onepiece:medicine_cabinet", Direction.SOUTH)
					.exact('r', "a brewing stand", "minecraft:brewing_stand", null)
					.layer("HmH",
							"...",
							"tsr")
					.layer(".T.",
							"...",
							"..."),

			new LayoutPlan("chart_room", "Chart Room", "Nami's room: a Navigator's Desk between bookshelves, with a globe and a telescope. Sails 10% faster.")
					.key('n', "a Navigator's Desk, chart table or cartography table",
							LayoutPlan.ids("onepiece:navigators_desk", "onepiece:chart_table", "minecraft:cartography_table"),
							"onepiece:navigators_desk", Direction.SOUTH)
					.key('B', "bookshelves", LayoutPlan.ids("minecraft:bookshelf", "minecraft:chiseled_bookshelf", "onepiece:book_stack"),
							"minecraft:bookshelf")
					.exact('o', "a Globe", "onepiece:globe", Direction.SOUTH)
					.exact('y', "a Telescope", "onepiece:telescope", Direction.NORTH)
					.layer("BnB",
							"...",
							"o.y")
					.layer("T.T",
							"...",
							"...")
					.tip("Hang a Grand Line Wall Map above the desk."),

			new LayoutPlan("library", "Library", "Robin's library: a lectern with a wall of bookshelves. Old books, gold and gems turn up in the haul.")
					.key('B', "bookshelves", LayoutPlan.ids("minecraft:bookshelf", "minecraft:chiseled_bookshelf", "onepiece:book_stack"),
							"minecraft:bookshelf")
					.key('l', "a lectern or writing desk", LayoutPlan.ids("minecraft:lectern", "onepiece:writing_desk"),
							"minecraft:lectern", Direction.SOUTH)
					.layer("BBBBB",
							"B...B",
							"..l..")
					.layer("BBBBB",
							"B...B",
							".....")
					.layer("T...T",
							".....",
							"....."),

			new LayoutPlan("workshop", "Workshop", "Franky's workshop: a Shipwright's Bench with an anvil and a grindstone. Patches the hull, even mid-battle.")
					.key('V', "a Shipwright's Bench, tool bench or smithing table",
							LayoutPlan.ids("onepiece:shipwright_bench", "onepiece:tool_bench", "minecraft:smithing_table"),
							"onepiece:shipwright_bench", Direction.SOUTH)
					.key('a', "an anvil", state -> state.is(BlockTags.ANVIL), "minecraft:anvil", Direction.EAST)
					.exact('i', "a grindstone", "minecraft:grindstone", Direction.SOUTH)
					.layer("aVi",
							"...",
							"X.X")
					.layer("...",
							"...",
							"T.T"),

			new LayoutPlan("weapons_factory", "Weapons Factory", "Usopp's factory: a fletching table with targets, powder and cannonballs. Special cannon shot in the haul.")
					.exact('f', "a fletching table", "minecraft:fletching_table", null)
					.exact('z', "targets", "minecraft:target", null)
					.exact('q', "a Cannonball Pile", "onepiece:cannonball_pile", Direction.SOUTH)
					.exact('Q', "a Powder Keg", "onepiece:powder_keg", Direction.SOUTH)
					.layer("zfz",
							"...",
							"qXQ")
					.layer(".T.",
							"...",
							"..."),

			new LayoutPlan("crows_nest", "Crow's Nest Gym", "A lookout platform on a mast with Zoro's giant weights and a katana stand. Counts as the Training Room: Strength I aboard.")
					.exact('Z', "Giant Training Weights", "onepiece:training_weights", Direction.SOUTH)
					.exact('J', "a Katana Stand", "onepiece:katana_stand", Direction.SOUTH)
					.key('r', "ladders", LayoutPlan.suffix("ladder"), "minecraft:ladder", Direction.SOUTH)
					.layer(".....", ".....", "..L..", "..r..", ".....")
					.layer(".....", ".....", "..L..", "..r..", ".....")
					.layer(".....", ".....", "..L..", "..r..", ".....")
					.layer(".....", ".....", "..L..", "..r..", ".....")
					.layer(".....", ".....", "..L..", "..r..", ".....")
					.layer("PPPPP", "PPPPP", "PPLPP", "PPrPP", "PPPPP")
					.layer("FFFFF", "FZ.JF", "F.L.F", "F...F", "FFFFF")
					.layer("T...T", ".....", "..L..", ".....", "T...T")
					.tip("Build it around the main mast if your ship has one: the mast counts as the post."),

			new LayoutPlan("music_bar", "Music Bar", "Brook's bar: a piano beside a bar counter with stools, a keg and a sake set. Everyone's haul +20%.")
					.key('N', "a piano, jukebox or note block", LayoutPlan.ids("onepiece:piano", "minecraft:jukebox", "minecraft:note_block"),
							"onepiece:piano", Direction.SOUTH)
					.key('M', "bar counters", LayoutPlan.ids("onepiece:tavern_bar").or(LayoutPlan.suffix("_counter")),
							"onepiece:tavern_bar", Direction.SOUTH)
					.key('e', "a keg or wine rack", LayoutPlan.ids("onepiece:keg", "onepiece:wine_rack", "onepiece:cola_barrel", "minecraft:barrel"),
							"onepiece:keg", Direction.SOUTH)
					.key('h', "bar stools", LayoutPlan.ids("onepiece:bar_stool").or(LayoutPlan.suffix("_stool")),
							"onepiece:bar_stool", Direction.SOUTH)
					.key('y', "a sake set or mugs", LayoutPlan.ids("onepiece:sake_set", "onepiece:beer_mugs"), "onepiece:sake_set", Direction.SOUTH)
					.layer("N.MMe",
							"..hh.",
							".....")
					.layer("...y.",
							".....",
							".....")
					.tip("Brook plays better with a lantern or two hung nearby."),

			new LayoutPlan("captains_cabin", "Captain's Cabin", "A small walled cabin with a captain's chair, a writing desk, a chest and a hammock. Needed for the Pirate Brig.")
					.key('q', "a captain's chair or throne", LayoutPlan.ids("onepiece:captains_chair", "onepiece:throne"),
							"onepiece:captains_chair", Direction.NORTH)
					.exact('z', "a Writing Desk", "onepiece:writing_desk", Direction.SOUTH)
					.layer("PPPPP",
							"PzXHP",
							"Pq..P",
							"P...P",
							"PPDPP")
					.layer("PwwwP",
							"PT..P",
							"P...P",
							"w...w",
							"PP.PP")
					.layer("RRRRR",
							"RRRRR",
							"RRRRR",
							"RRRRR",
							"RRRRR"),

			new LayoutPlan("garden", "Deck Garden", "Nami's mikan grove: Deck Lawn behind a little fence, with mikan trees and flowers. Mikan and herbs in the haul.")
					.key('l', "Deck Lawn or Deck Soil", LayoutPlan.ids("onepiece:deck_lawn", "onepiece:deck_soil"), "onepiece:deck_lawn")
					.key('m', "Mikan Tree Pots or Mikan Bushes", LayoutPlan.ids("onepiece:mikan_tree_pot", "onepiece:mikan_bush"),
							"onepiece:mikan_tree_pot")
					.key('f', "flowers or saplings", state -> state.is(BlockTags.FLOWERS) || state.is(BlockTags.SAPLINGS)
							|| LayoutPlan.idOf(state).equals("onepiece:bonsai"), "minecraft:poppy")
					.layer("FFFFF",
							"FlllF",
							"FlllF",
							"F...F")
					.layer(".....",
							".fmf.",
							".mfm.",
							".....")
					.tip("Mikan Tree Pots work on any deck, even one with no Deck Lawn."),

			new LayoutPlan("bath", "Bath", "A bathtub behind a low screen. A soak clears poison, hunger and other bad effects.")
					.key('U', "a bathtub or wooden tub", LayoutPlan.ids("onepiece:bathtub", "onepiece:wooden_tub"), "onepiece:bathtub", Direction.SOUTH)
					.layer("wwww",
							"wU.w",
							"w...")
					.layer("T..T",
							"....",
							"...."),

			new LayoutPlan("gun_deck", "Broadside Battery", "Three cannons in the railing with cannonballs and powder close by. Cannons count toward the ship's level.")
					.exact('q', "Cannonball Piles", "onepiece:cannonball_pile", Direction.SOUTH)
					.exact('Q', "a Powder Keg", "onepiece:powder_keg", Direction.SOUTH)
					.layer("FCFCFCF",
							".q.Q.q.",
							".......")
					.layer("T.....T",
							".......",
							".......")
					.tip("Click the deck facing the side of the ship: the cannons point the way you look."),

			new LayoutPlan("bunk_room", "Crew Bunks", "Four hammocks with sea chests. Every bunk lets one more crewmate live aboard.")
					.layer("HH.HH",
							".....",
							"X...X")
					.layer(".....",
							".....",
							"T...T")
	);

	public static final List<LayoutPlan> BASE = List.of(
			new LayoutPlan("beach_camp", "Beach Camp", "A bed, a campfire with seats, a chest and a crafting table: Pirate Camp (level 1), and a start on level 2.")
					.key('h', "a bed (head)", state -> state.getBlock() instanceof net.minecraft.world.level.block.BedBlock,
							"minecraft:red_bed", Direction.NORTH, Map.of("part", "head"))
					.key('b', "a bed (foot)", state -> state.getBlock() instanceof net.minecraft.world.level.block.BedBlock,
							"minecraft:red_bed", Direction.NORTH, Map.of("part", "foot"))
					.layer("X.h.T",
							"..b..",
							"s.O.s",
							".....",
							"W...X")
					.tip("Put your Hideout Flag down first, then build this inside the claim."),

			new LayoutPlan("bunkhouse", "Crew Bunkhouse", "A raised plank hut with four beds and sea chests: beds for the Hideout and Pirate Fort levels.")
					.key('h', "beds (head)", state -> state.getBlock() instanceof net.minecraft.world.level.block.BedBlock,
							"minecraft:red_bed", Direction.NORTH, Map.of("part", "head"))
					.key('b', "beds (foot)", state -> state.getBlock() instanceof net.minecraft.world.level.block.BedBlock,
							"minecraft:red_bed", Direction.NORTH, Map.of("part", "foot"))
					.layer("PPPPPPPPP",
							"PPPPPPPPP",
							"PPPPPPPPP",
							"PPPPPPPPP",
							"PPPPPPPPP",
							"PPPPPPPPP",
							"....S....")
					.layer("PPPPPPPPP",
							"PhXhXhXhP",
							"Pb.b.b.bP",
							"P.......P",
							"PT.....TP",
							"PPPPDPPPP",
							".........")
					.layer("PPwPPPwPP",
							"P.......P",
							"P.......P",
							"w.......w",
							"P.......P",
							"PPPP.PPPP",
							".........")
					.layer("RRRRRRRRR",
							"RRRRRRRRR",
							"RRRRRRRRR",
							"RRRRRRRRR",
							"RRRRRRRRR",
							"RRRRRRRRR",
							".........")
					.tip("The slab in front of the door is the door step."),

			new LayoutPlan("cookhouse", "Cookhouse", "An open shed on four posts with a smoker, a crafting table, a barrel and a table: the kitchen and workbench a Hideout needs.")
					.layer("LKWXL",
							".....",
							"s.t.s",
							".....",
							"L...L")
					.layer("L.T.L",
							".....",
							".....",
							".....",
							"L...L")
					.layer("RRRRR",
							"RRRRR",
							"RRRRR",
							"RRRRR",
							"RRRRR"),

			new LayoutPlan("cannon_battery", "Cannon Battery", "Two cannons in a stone wall with cannonballs and powder. They fire at Navy attackers (keep cannonballs in the flag's stash).")
					.exact('q', "a Cannonball Pile", "onepiece:cannonball_pile", Direction.SOUTH)
					.exact('Q', "a Powder Keg", "onepiece:powder_keg", Direction.SOUTH)
					.layer("#C#C#",
							"#...#",
							".q.Q.")
					.layer("#.#.#",
							".....",
							".....")
					.tip("Click the ground facing the sea: the cannons point the way you look. Build two for a Pirate Fort, eight for a Fortress."),

			new LayoutPlan("lookout_tower", "Lookout Tower", "A tower with the Alarm Bell on top: a finished Marine Watchtower, which a Pirate Fort needs. Marines nearby glow.")
					.exact('A', "the Alarm Bell", "onepiece:alarm_bell", Direction.SOUTH)
					.key('r', "ladders", LayoutPlan.suffix("ladder"), "minecraft:ladder", Direction.SOUTH)
					.layer("L...L", ".....", ".....", ".....", "L.L.L", "..r..")
					.layer("L...L", ".....", ".....", ".....", "L.L.L", "..r..")
					.layer("L...L", ".....", ".....", ".....", "L.L.L", "..r..")
					.layer("L...L", ".....", ".....", ".....", "L.L.L", "..r..")
					.layer("PPPPP", "PPPPP", "PPPPP", "PPPPP", "PPPPP", "..r..")
					.layer("FFFFF", "F...F", "F.A.F", "F...F", "FF.FF", ".....")
					.layer("T...T", ".....", ".....", ".....", "T...T", ".....")
					.tip("The Alarm Bell is crafted from its Marine Watchtower Blueprint's recipe line in the Journal."),

			new LayoutPlan("palisade_gate", "Palisade Gate", "A log wall with a gate and lanterns, to close off the way into your hideout.")
					.layer("LLLLGLLLL")
					.layer("LLLL.LLLL")
					.layer("LLLLLLLLL")
					.layer("T.F.F.F.T")
					.tip("Build several and join them with log walls round the claim."),

			new LayoutPlan("pirate_dock", "Pirate Pier", "A plank pier out over the water with posts, a rope coil and lanterns. Ships moor here and fishers like it.")
					.exact('c', "a Rope Coil", "onepiece:rope_coil", Direction.SOUTH)
					.floor(0)
					.layer("LPL",
							"PPP",
							"PPP",
							"PPP",
							"PPP",
							"PPP",
							"...")
					.layer("F.F",
							"c..",
							"...",
							"..X",
							"...",
							"F.F",
							"...")
					.layer("T.T",
							"...",
							"...",
							"...",
							"...",
							"T.T",
							"...")
					.tip("Stand on the shore and click the edge block facing the sea. The pier is built level with that block."),

			new LayoutPlan("flag_square", "Flag Square", "Your Hideout Flag on a little square with a fence and four lanterns, where the crew gathers.")
					.exact('J', "your Hideout Flag", "onepiece:hideout_flag", Direction.SOUTH)
					.layer("F...F",
							".....",
							"..J..",
							".....",
							"F...F")
					.layer("T...T",
							".....",
							".....",
							".....",
							"T...T")
	);

	public static List<LayoutPlan> book(PlanBookItem.Book book) {
		return book == PlanBookItem.Book.DECK ? DECK : BASE;
	}
}
