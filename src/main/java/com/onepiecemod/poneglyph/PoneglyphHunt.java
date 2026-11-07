package com.onepiecemod.poneglyph;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Prediction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.endgame.VoidCentury;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.resource.PoneglyphBlock;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.story.StoryGates;

/**
 * Poneglyph hunting: twelve Lost Poneglyphs lie hidden around the world, three in the East Blue, five in the
 * Grand Line and four in the New World. Where they are depends on the world seed. Each one is raised (a small ruin,
 * or a sunken one on the sea floor) the first time a player comes near it.
 *
 * Ohara Survey Notes point toward the nearest one you haven't found, and list what you've found so far.
 * Walking up to a Lost Poneglyph marks it found. Reading it (right-click, with an archaeologist in your crew)
 * gives a piece of the lost history, berries and Pirate XP, with bigger prizes at 4, 8 and 12 read.
 * /poneglyphs shows your log too; ops can use /poneglyphs locate to list every site.
 */
public final class PoneglyphHunt {
	/** One Lost Poneglyph. minDistance/maxDistance from spawn decide which sea it's in. */
	public record Site(String name, int minDistance, int maxDistance, String text) {
	}

	public static final List<Site> SITES = List.of(
			new Site("Stone of the Windmill Coast", 450, 1250,
					"\"Those who would reach the end of the sea, seek the Road. Four red stones point the way.\""),
			new Site("Sunken Stone of the Blue", 450, 1250,
					"The masons who cut this stone left a mark at its base: the crest of the Kozuki family of Wano."),
			new Site("Stone of the Old Lighthouse", 450, 1250,
					"\"Paper burns. Stone does not. We carve the truth so that it outlives those who would erase it.\""),
			new Site("Desert Stone", 1800, 3300,
					"A warning: three great weapons were left behind when the kingdom fell. They sleep, waiting for hands that can bear them."),
			new Site("Stone in the Fog", 1800, 3300,
					"It names Joy Boy, the first pirate, a man who could make people laugh even in the middle of a war."),
			new Site("Sky-Fallen Stone", 1800, 3300,
					"\"When the drums of liberation sound again, someone will come to set the sea free.\""),
			new Site("Stone of the Twin Capes", 1800, 3300,
					"It tells of the day the sea rose. Whole lands sank beneath the waves, and the old shores were never seen again."),
			new Site("Jungle Stone", 1800, 3300,
					"It speaks of a mermaid princess, born once in many centuries, whose voice the Sea Kings obey."),
			new Site("Volcanic Stone", 3700, 6000,
					"Twenty kings won the war and swore to rule the world from atop the Red Line. One of the twenty refused to climb."),
			new Site("Frozen Stone", 3700, 6000,
					"It names a weapon of the sky, a light that falls from the heavens. The rest of the line is shattered."),
			new Site("Thunder Stone", 3700, 6000,
					"The Great Kingdom shared what it knew with the whole world. That, it says, is why it had to be erased."),
			new Site("Last Lost Stone", 3700, 6000,
					"\"Gather every piece. The treasure at the end is real, and whoever finds it will understand why the world was hidden.\""));

	/** Berries and Pirate XP for reading a stone in each sea, and the big prizes at 4, 8 and 12 read. */
	private static final int[] READ_BERRIES = {150, 400, 900};
	private static final int[] READ_XP = {100, 250, 500};
	private static final int[] MILESTONE_COUNT = {4, 8, 12};
	private static final int[] MILESTONE_BERRIES = {1000, 3000, 8000};

	private static final int CHECK_EVERY = 100;
	/** How close a player gets before the ruin is raised, and before the stone counts as found. */
	private static final int RAISE_DISTANCE = 72;
	private static final int FIND_DISTANCE = 10;

	/** On the Overworld: "x,z,y" for each site, in SITES order. y is NOT_PLACED until the ruin is raised. */
	private static final AttachmentType<List<String>> WORLD_SITES = AttachmentRegistry.create(
			OnePieceMod.id("lost_poneglyph_sites"),
			builder -> builder.persistent(Codec.STRING.listOf()));
	private static final int NOT_PLACED = Integer.MIN_VALUE;

	/** Site numbers ("0".."11") this player has found, and read. Kept forever. */
	public static final AttachmentType<List<String>> FOUND = AttachmentRegistry.create(
			OnePieceMod.id("lost_poneglyphs_found"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());
	public static final AttachmentType<List<String>> READ = AttachmentRegistry.create(
			OnePieceMod.id("lost_poneglyphs_read"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	public static final Item SURVEY_NOTES = register("ohara_survey_notes", NotesItem::new,
			new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));

	private static Item register(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> output.accept(SURVEY_NOTES));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY != 11) {
				return;
			}
			for (ServerPlayer player : server.overworld().players()) {
				if (!player.isSpectator()) {
					check(server, player);
				}
			}
		});
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("poneglyphs")
						.executes(context -> {
							log(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("locate")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									MinecraftServer server = context.getSource().getServer();
									List<int[]> sites = sites(server);
									for (int i = 0; i < sites.size(); i++) {
										int[] s = sites.get(i);
										String line = (i + 1) + ". " + SITES.get(i).name() + " at " + s[0] + " " + (s[2] == NOT_PLACED ? "~" : String.valueOf(s[2]))
												+ " " + s[1] + (s[2] == NOT_PLACED ? " (not raised yet)" : "");
										context.getSource().sendSuccess(() -> Component.literal(line), false);
									}
									return 1;
								}))));
	}

	// ---------- Where the sites are ----------

	/** Every site as {x, z, y}. Worked out from the seed the first time, then remembered on the Overworld. */
	static List<int[]> sites(MinecraftServer server) {
		ServerLevel overworld = server.overworld();
		List<String> saved = overworld.getAttachedOrElse(WORLD_SITES, List.of());
		if (saved.size() != SITES.size()) {
			Random random = new Random(overworld.getSeed() ^ 0x504F4E45474C5950L);
			List<String> made = new ArrayList<>();
			for (int i = 0; i < SITES.size(); i++) {
				if (i < saved.size()) {
					made.add(saved.get(i)); // Keep sites already placed if the list ever grows.
					continue;
				}
				Site site = SITES.get(i);
				double angle = i * 2.39996 + random.nextDouble() * 0.8; // Golden angle: spread around the compass.
				double distance = site.minDistance() + random.nextDouble() * (site.maxDistance() - site.minDistance());
				made.add((int) (Math.cos(angle) * distance) + "," + (int) (Math.sin(angle) * distance) + "," + NOT_PLACED);
			}
			overworld.setAttached(WORLD_SITES, made);
			saved = made;
		}
		List<int[]> out = new ArrayList<>();
		for (String entry : saved) {
			String[] parts = entry.split(",");
			out.add(new int[] {Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2])});
		}
		return out;
	}

	private static void save(MinecraftServer server, List<int[]> sites) {
		List<String> list = new ArrayList<>();
		for (int[] s : sites) {
			list.add(s[0] + "," + s[1] + "," + s[2]);
		}
		server.overworld().setAttached(WORLD_SITES, list);
	}

	/** 0 = East Blue, 1 = Grand Line, 2 = New World. */
	private static int seaTier(int index) {
		int distance = SITES.get(index).minDistance();
		return distance >= 3700 ? 2 : distance >= 1800 ? 1 : 0;
	}

	// ---------- Raising ruins and finding them ----------

	private static void check(MinecraftServer server, ServerPlayer player) {
		ServerLevel level = server.overworld();
		List<int[]> sites = sites(server);
		boolean changed = false;
		for (int i = 0; i < sites.size(); i++) {
			int[] s = sites.get(i);
			double dx = player.getX() - s[0], dz = player.getZ() - s[1];
			double distance = Math.sqrt(dx * dx + dz * dz);
			if (s[2] == NOT_PLACED && distance < RAISE_DISTANCE) {
				int[] placed = raise(level, s[0], s[1]);
				if (placed != null) {
					sites.set(i, placed);
					changed = true;
				}
			} else if (s[2] != NOT_PLACED && distance < FIND_DISTANCE && Math.abs(player.getY() - s[2]) < 16) {
				find(player, i);
			}
		}
		if (changed) {
			save(server, sites);
		}
	}

	/** Builds the ruin around x, z. Returns where the Poneglyph stands {x, z, y}, or null if the land isn't loaded yet. */
	private static int[] raise(ServerLevel level, int x, int z) {
		// Step aside from towns and landmarks so the ruin never lands inside one.
		for (int attempt = 0; attempt < 5; attempt++) {
			BlockPos probe = new BlockPos(x, level.getSeaLevel(), z);
			if (!loaded(level, x, z)) {
				return null;
			}
			if (!level.structureManager().getStructureWithPieceAt(probe.atY(level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1), holder -> true).isValid()) {
				break;
			}
			x += 40;
		}
		if (!loaded(level, x, z)) {
			return null;
		}
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z) - 1;
		// Frozen seas: the ice on top isn't the ground. Go down through ice and water to the real sea floor.
		while (floor > level.getMinY() + 1 && (level.getBlockState(new BlockPos(x, floor, z)).is(net.minecraft.tags.BlockTags.ICE)
				|| level.getFluidState(new BlockPos(x, floor, z)).is(FluidTags.WATER))) {
			floor--;
		}
		BlockState above = level.getBlockState(new BlockPos(x, floor + 1, z));
		boolean sunken = level.getFluidState(new BlockPos(x, floor + 1, z)).is(FluidTags.WATER) || above.is(net.minecraft.tags.BlockTags.ICE);
		var random = level.getRandom();
		BlockState empty = sunken ? Blocks.WATER.defaultBlockState() : Blocks.AIR.defaultBlockState();
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 2; dz++) {
				BlockPos at = new BlockPos(x + dx, floor, z + dz);
				BlockState floorBlock = sunken
						? (random.nextInt(3) == 0 ? Blocks.DARK_PRISMARINE : Blocks.PRISMARINE_BRICKS).defaultBlockState()
						: (random.nextInt(3) == 0 ? Blocks.CRACKED_STONE_BRICKS : random.nextBoolean() ? Blocks.MOSSY_STONE_BRICKS : Blocks.STONE_BRICKS).defaultBlockState();
				if (Math.abs(dx) == 2 && Math.abs(dz) == 2 && random.nextInt(4) == 0) {
					continue; // a corner crumbled away
				}
				level.setBlockAndUpdate(at, floorBlock);
				// Fill a little underneath so the ruin doesn't float on a slope.
				for (int down = 1; down <= 6; down++) {
					BlockPos below = at.below(down);
					if (!level.getBlockState(below).canBeReplaced()) {
						break;
					}
					level.setBlockAndUpdate(below, Blocks.STONE.defaultBlockState());
				}
				for (int up = 1; up <= 4; up++) {
					level.setBlockAndUpdate(at.above(up), empty);
				}
			}
		}
		// Broken pillars on the corners.
		int[][] corners = {{-2, -2}, {2, -2}, {-2, 2}, {2, 2}};
		for (int[] c : corners) {
			int height = 1 + random.nextInt(3);
			for (int up = 1; up <= height; up++) {
				BlockState pillar = sunken ? Blocks.PRISMARINE_WALL.defaultBlockState()
						: (random.nextBoolean() ? Blocks.MOSSY_STONE_BRICK_WALL : Blocks.STONE_BRICK_WALL).defaultBlockState();
				level.setBlockAndUpdate(new BlockPos(x + c[0], floor + up, z + c[1]), pillar);
			}
			if (sunken && random.nextBoolean()) {
				level.setBlockAndUpdate(new BlockPos(x + c[0], floor + height + 1, z + c[1]), Blocks.SEA_LANTERN.defaultBlockState());
			}
		}
		level.setBlockAndUpdate(new BlockPos(x, floor + 1, z), Resources.PONEGLYPH.defaultBlockState());
		level.setBlockAndUpdate(new BlockPos(x, floor + 2, z), Resources.PONEGLYPH.defaultBlockState());
		return new int[] {x, z, floor + 1};
	}

	private static boolean loaded(ServerLevel level, int x, int z) {
		return level.hasChunkAt(new BlockPos(x - 3, 0, z - 3)) && level.hasChunkAt(new BlockPos(x + 3, 0, z + 3));
	}

	private static void find(ServerPlayer player, int index) {
		List<String> found = player.getAttachedOrElse(FOUND, List.of());
		String key = String.valueOf(index);
		if (found.contains(key)) {
			return;
		}
		List<String> updated = new ArrayList<>(found);
		updated.add(key);
		player.setAttached(FOUND, updated);
		player.sendSystemMessage(Component.literal("You found a Lost Poneglyph: " + SITES.get(index).name() + "! (" + updated.size() + "/"
				+ SITES.size() + " found)").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		if (!read(player).contains(key)) {
			player.sendSystemMessage(Component.literal("Right-click it to read it. You'll need an archaeologist in your crew.").withStyle(ChatFormatting.GRAY));
		}
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.5f, 0.6f);
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/lost_poneglyph");
	}

	public static List<String> found(Player player) {
		return player.getAttachedOrElse(FOUND, List.of());
	}

	public static List<String> read(Player player) {
		return player.getAttachedOrElse(READ, List.of());
	}

	/**
	 * Called first thing when someone right-clicks a Poneglyph block. If it's a Lost Poneglyph, reads it and returns true;
	 * otherwise returns false so the block does its usual thing.
	 */
	public static boolean onUse(ServerLevel level, BlockPos pos, ServerPlayer player) {
		if (level.dimension() != Level.OVERWORLD) {
			return false;
		}
		List<int[]> sites = sites(level.getServer());
		for (int i = 0; i < sites.size(); i++) {
			int[] s = sites.get(i);
			if (s[2] == NOT_PLACED || Math.abs(pos.getX() - s[0]) > 1 || Math.abs(pos.getZ() - s[1]) > 1 || Math.abs(pos.getY() - s[2]) > 3) {
				continue;
			}
			find(player, i);
			String key = String.valueOf(i);
			Site site = SITES.get(i);
			if (read(player).contains(key)) {
				player.sendSystemMessage(Component.literal(site.name() + ": ").withStyle(ChatFormatting.GOLD)
						.append(Component.literal(site.text()).withStyle(ChatFormatting.YELLOW)));
				return true;
			}
			if (StoryGates.gatesOn(player) && !PoneglyphBlock.hasArchaeologist(player)) {
				player.sendSystemMessage(Component.literal("Ancient script covers the stone, but no one can read it anymore. "
						+ "Bring an archaeologist in your crew, then come back. Your Survey Notes will remember this place.").withStyle(ChatFormatting.GRAY));
				return true;
			}
			List<String> updated = new ArrayList<>(read(player));
			updated.add(key);
			player.setAttached(READ, updated);
			int tier = seaTier(i);
			player.sendSystemMessage(Component.literal("You read the " + site.name() + ":").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
			player.sendSystemMessage(Component.literal(site.text()).withStyle(ChatFormatting.YELLOW, ChatFormatting.ITALIC));
			give(player, new ItemStack(CharacterFeature.BERRY, READ_BERRIES[tier]));
			com.onepiecemod.stats.StatTraining.addXp(player, READ_XP[tier], true);
			level.playSound(null, pos, SoundEvents.BOOK_PAGE_TURN, SoundSource.BLOCKS, 1.0f, 0.7f);
			player.sendSystemMessage(Component.literal("Lost Poneglyphs read: " + updated.size() + "/" + SITES.size()
					+ ". The World Economy Journal would pay well for this... +" + READ_BERRIES[tier] + " berries.").withStyle(ChatFormatting.GREEN));
			for (int m = 0; m < MILESTONE_COUNT.length; m++) {
				if (updated.size() == MILESTONE_COUNT[m]) {
					give(player, new ItemStack(CharacterFeature.BERRY, MILESTONE_BERRIES[m]));
					player.sendSystemMessage(Component.literal("Milestone! " + updated.size() + " Lost Poneglyphs read. Scholars everywhere want your notes: +"
							+ MILESTONE_BERRIES[m] + " berries.").withStyle(ChatFormatting.LIGHT_PURPLE));
					player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0f, 0.9f);
				}
			}
			if (updated.size() >= SITES.size()) {
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/poneglyph_scholar");
				player.sendSystemMessage(Component.literal("You have read every Lost Poneglyph. The scholars of Ohara would be proud.")
						.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
			}
			return true;
		}
		return false;
	}

	// ---------- Survey Notes and the log ----------

	/** Points at the nearest Lost Poneglyph this player hasn't found, on the action bar. */
	static void point(ServerPlayer player) {
		List<int[]> sites = sites(player.level().getServer());
		List<String> found = found(player);
		int best = -1;
		double bestDistance = Double.MAX_VALUE;
		for (int i = 0; i < sites.size(); i++) {
			if (found.contains(String.valueOf(i))) {
				continue;
			}
			double dx = sites.get(i)[0] - player.getX(), dz = sites.get(i)[1] - player.getZ();
			double distance = Math.sqrt(dx * dx + dz * dz);
			if (distance < bestDistance) {
				bestDistance = distance;
				best = i;
			}
		}
		if (best < 0) {
			player.connection.send(new ClientboundSetActionBarTextPacket(
					Component.literal("You've found every Lost Poneglyph.").withStyle(ChatFormatting.GOLD)));
			return;
		}
		int[] s = sites.get(best);
		String direction = direction(s[0] - player.getX(), s[1] - player.getZ());
		CalmBelt.Sea sea = CalmBelt.seaByDistance(new BlockPos(s[0], 0, s[1]));
		String far = bestDistance < 60 ? "very close, " : "about " + Math.max(100, Math.round(bestDistance / 100.0) * 100) + " blocks ";
		player.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(
				"Nearest lost Poneglyph: " + far + direction + " (" + sea.title() + ")").withStyle(ChatFormatting.AQUA)));
	}

	private static String direction(double dx, double dz) {
		// Minecraft: -Z is north, +X is east.
		double angle = Math.toDegrees(Math.atan2(dx, -dz));
		String[] names = {"north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"};
		return names[(int) Math.floorMod(Math.round(angle / 45.0), 8)];
	}

	static void log(ServerPlayer player) {
		List<int[]> sites = sites(player.level().getServer());
		List<String> found = found(player), read = read(player);
		player.sendSystemMessage(Component.literal("Poneglyph Log").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("Lost Poneglyphs: " + found.size() + "/" + SITES.size() + " found, "
				+ read.size() + "/" + SITES.size() + " read").withStyle(ChatFormatting.YELLOW));
		for (int i = 0; i < SITES.size(); i++) {
			String key = String.valueOf(i);
			if (!found.contains(key)) {
				continue;
			}
			int[] s = sites.get(i);
			boolean done = read.contains(key);
			player.sendSystemMessage(Component.literal((done ? " [read] " : " [found] ") + SITES.get(i).name() + " at " + s[0] + ", " + s[1])
					.withStyle(done ? ChatFormatting.GREEN : ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("Pages of the true history: " + VoidCentury.read(player).size() + "/" + VoidCentury.PAGES.size()
				+ " (from Poneglyphs in famous places)").withStyle(ChatFormatting.YELLOW));
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY);
		}
	}

	/** Ohara Survey Notes: right-click to point toward the nearest lost Poneglyph. Sneak + right-click for your log. */
	public static class NotesItem extends Item {
		public NotesItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				if (level.dimension() != Level.OVERWORLD) {
					serverPlayer.sendSystemMessage(Component.literal("The notes only cover the seas of the Overworld.").withStyle(ChatFormatting.GRAY));
				} else if (player.isShiftKeyDown()) {
					log(serverPlayer);
				} else {
					point(serverPlayer);
				}
				player.getCooldowns().addCooldown(player.getItemInHand(hand), 20);
			}
			return InteractionResult.SUCCESS;
		}
	}
}
