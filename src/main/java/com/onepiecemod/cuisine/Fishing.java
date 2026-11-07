package com.onepiecemod.cuisine;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.FishingHook;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.BuiltInLootTables;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.SeaItems;

/**
 * Fishing with a normal fishing rod now catches the fish of whichever sea you are in.
 *
 *  - In the Overworld, 60% of the fish you reel in are swapped for a fish of the local sea (East Blue,
 *    Calm Belt, Grand Line or New World, by distance from spawn). Around some islands (Fishman Island,
 *    Skypiea, Wano, Drum, Alabasta, Thriller Bark) the island's own fish bite most.
 *  - In the Calm Belt you can now and then hook a slab of Sea King meat.
 *  - In the All Blue every catch is a fish (junk turns into fish, treasure stays), any fish can bite,
 *    and 1 catch in 3 brings up a second fish.
 *
 * Every new kind you catch goes into your fish log (/fishlog).
 */
public class Fishing {
	/** Share of reeled-in fish that become a fish of the local sea. */
	private static final float LOCAL_FISH_CHANCE = 0.6f;
	/** In the Calm Belt: share of regional catches that are Sea King meat instead. */
	private static final float SEA_KING_MEAT_CHANCE = 0.12f;
	private static final float ALL_BLUE_DOUBLE_CHANCE = 0.33f;
	/** Island fish weigh this much more than the sea's own fish around their island. */
	private static final int ISLAND_BOOST = 3;

	public static final AttachmentType<List<String>> CAUGHT = AttachmentRegistry.create(
			OnePieceMod.id("fish_caught"), builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	public static void initialize() {
		LootTableEvents.MODIFY_DROPS.register(Fishing::modifyDrops);
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("fishlog").executes(context -> {
				context.getSource().sendSystemMessage(log(context.getSource().getPlayerOrException()));
				return 1;
			}));
			dispatcher.register(Commands.literal("allblue")
					.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
					.executes(context -> {
						BlockPos center = AllBlue.center(context.getSource().getServer());
						context.getSource().sendSystemMessage(Component.literal("The All Blue is centred on " + center.getX() + " "
								+ center.getZ() + " (radius " + AllBlue.RADIUS + ")."));
						return 1;
					}));
		});
	}

	private static void modifyDrops(Holder<LootTable> table, LootContext context, List<ItemStack> drops) {
		if (!table.is(BuiltInLootTables.FISHING)) {
			return;
		}
		// A real catch: THIS_ENTITY is the bobber. The /loot ... fish command run by a player passes the player instead.
		Entity entity = context.getOptional(LootContextParams.THIS_ENTITY);
		Vec3 origin = context.getOptional(LootContextParams.ORIGIN);
		ServerPlayer player;
		if (entity instanceof FishingHook hook && hook.getPlayerOwner() instanceof ServerPlayer owner) {
			player = owner;
			origin = hook.position();
		} else if (entity instanceof ServerPlayer commandUser && origin != null) {
			player = commandUser;
		} else {
			return;
		}
		ServerLevel level = context.getLevel();
		if (level.dimension() != Level.OVERWORLD) {
			return;
		}
		BlockPos pos = BlockPos.containing(origin);
		RandomSource random = context.getRandom();
		boolean allBlue = AllBlue.contains(level, origin.x, origin.z);
		for (int i = 0; i < drops.size(); i++) {
			ItemStack stack = drops.get(i);
			boolean fish = isVanillaFish(stack);
			boolean swap = allBlue ? fish || !isTreasure(stack) : fish && random.nextFloat() < LOCAL_FISH_CHANCE;
			if (swap) {
				drops.set(i, catchAt(level, pos, allBlue, random));
			}
		}
		if (allBlue && random.nextFloat() < ALL_BLUE_DOUBLE_CHANCE) {
			drops.add(catchAt(level, pos, true, random));
			player.sendOverlayMessage(Component.literal("Two at once! The All Blue is teeming.").withStyle(ChatFormatting.AQUA));
		}
		for (ItemStack stack : drops) {
			if (stack.getItem() instanceof CuisineItems.FishItem fishItem) {
				record(player, fishItem.fish());
			}
		}
	}

	/** Picks a fish for this spot. */
	private static ItemStack catchAt(ServerLevel level, BlockPos pos, boolean allBlue, RandomSource random) {
		CalmBelt.Sea sea = CalmBelt.seaByDistance(pos);
		if (!allBlue && sea == CalmBelt.Sea.CALM_BELT && random.nextFloat() < SEA_KING_MEAT_CHANCE) {
			return new ItemStack(SeaItems.SEA_KING_MEAT);
		}
		String biome = level.getBiome(pos).unwrapKey().map(key -> key.identifier().toString()).orElse("");
		List<Fish> pool = new ArrayList<>();
		List<Integer> weights = new ArrayList<>();
		for (Fish fish : Fish.values()) {
			int weight = switch (fish.where) {
				case SEA -> allBlue || fish.sea == sea ? fish.weight : 0;
				case ISLAND -> fish.biomes.contains(biome) ? fish.weight * ISLAND_BOOST : allBlue ? fish.weight / 2 : 0;
				case ALL_BLUE -> allBlue ? fish.weight : 0;
			};
			if (weight > 0) {
				pool.add(fish);
				weights.add(weight);
			}
		}
		int total = weights.stream().mapToInt(Integer::intValue).sum();
		int roll = random.nextInt(total);
		for (int i = 0; i < pool.size(); i++) {
			roll -= weights.get(i);
			if (roll < 0) {
				return new ItemStack(CuisineItems.fish(pool.get(i)));
			}
		}
		return new ItemStack(CuisineItems.fish(pool.getFirst()));
	}

	private static boolean isVanillaFish(ItemStack stack) {
		return stack.is(Items.COD) || stack.is(Items.SALMON) || stack.is(Items.TROPICAL_FISH) || stack.is(Items.PUFFERFISH);
	}

	/** Enchanted gear, books, name tags, saddles and nautilus shells: the fishing treasure. */
	private static boolean isTreasure(ItemStack stack) {
		return stack.isEnchanted() || stack.has(DataComponents.STORED_ENCHANTMENTS) || stack.is(Items.NAME_TAG)
				|| stack.is(Items.SADDLE) || stack.is(Items.NAUTILUS_SHELL);
	}

	// ---- Fish log ----

	private static void record(ServerPlayer player, Fish fish) {
		List<String> caught = new ArrayList<>(player.getAttachedOrElse(CAUGHT, List.of()));
		if (caught.contains(fish.id)) {
			return;
		}
		caught.add(fish.id);
		player.setAttached(CAUGHT, caught);
		player.sendSystemMessage(Component.literal("New catch: " + fish.title + "! ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal("(" + caught.size() + "/" + Fish.values().length + " kinds, see /fishlog)")
						.withStyle(ChatFormatting.GRAY)));
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.5f, 1.4f);
		if (caught.size() == Fish.values().length) {
			player.sendSystemMessage(Component.literal("You've caught every fish there is. Sanji would be proud!")
					.withStyle(ChatFormatting.AQUA));
		}
	}

	private static Component log(ServerPlayer player) {
		List<String> caught = player.getAttachedOrElse(CAUGHT, List.of());
		MutableComponent text = Component.literal("Fish log: " + caught.size() + "/" + Fish.values().length + " kinds caught")
				.withStyle(ChatFormatting.GOLD);
		for (Fish fish : Fish.values()) {
			boolean got = caught.contains(fish.id);
			text.append(Component.literal("\n " + (got ? "✔ " + fish.title : "? ???") + " - " + fish.habitat())
					.withStyle(got ? ChatFormatting.GREEN : ChatFormatting.DARK_GRAY));
		}
		return text;
	}

}
