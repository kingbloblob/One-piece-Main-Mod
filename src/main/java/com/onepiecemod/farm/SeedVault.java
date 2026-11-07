package com.onepiecemod.farm;

import java.util.HashMap;
import java.util.Map;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.util.Prediction;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.OnePieceMod;

/**
 * The Seed Vault catalog: which island seeds a player has banked. Banking a kind keeps one seed;
 * from then on any Seed Vault gives that player one free seed of it per in-game day, so a seed
 * found once on a far island is never lost. Banking more kinds pays out farm rewards.
 */
public final class SeedVault {
	/** Crop id -> the last day a free seed of it was drawn (-1 = never). A key means the kind is banked. */
	public static final AttachmentType<Map<String, Long>> CATALOG = AttachmentRegistry.create(
			OnePieceMod.id("seed_vault"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.LONG)).copyOnDeath());

	private static final int REACH = 6;

	private SeedVault() {
	}

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("seedvault")
						.executes(context -> {
							showCatalog(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("take").then(Commands.argument("crop", StringArgumentType.word()).executes(context -> {
							take(context.getSource().getPlayerOrException(), StringArgumentType.getString(context, "crop"));
							return 1;
						})))));
	}

	public static Map<String, Long> catalog(ServerPlayer player) {
		return player.getAttachedOrElse(CATALOG, Map.of());
	}

	private static long today(ServerPlayer player) {
		return player.level().getGameTime() / 24000L;
	}

	static void bank(ServerPlayer player, IslandCrop crop, ItemStack stack) {
		Map<String, Long> catalog = new HashMap<>(catalog(player));
		if (catalog.containsKey(crop.id)) {
			tell(player, crop.title + " is already in your vault. Use an empty hand to draw your free seed for today.",
					ChatFormatting.GRAY);
			return;
		}
		stack.consume(1, player);
		catalog.put(crop.id, -1L);
		player.setAttached(CATALOG, catalog);
		player.level().playSound(null, player.blockPosition(), SoundEvents.CHISELED_BOOKSHELF_INSERT, SoundSource.BLOCKS, 1.0f, 1.0f);
		int count = catalog.size();
		int total = IslandCrop.values().length;
		tell(player, "Banked " + crop.title + " seeds (" + count + "/" + total + "). You can draw one free each day.",
				ChatFormatting.GREEN);
		reward(player, count, total);
	}

	private static void reward(ServerPlayer player, int count, int total) {
		ItemStack prize = switch (count) {
			case 3 -> new ItemStack(Items.BONE_MEAL, 16);
			case 6 -> new ItemStack(FarmItems.DIAL_SPRINKLER, 2);
			case 9 -> new ItemStack(FarmItems.RANCH_MANURE, 16);
			default -> ItemStack.EMPTY;
		};
		if (count == total) {
			prize = new ItemStack(FarmItems.DIAL_SPRINKLER, 4);
			player.getInventory().placeItemBackInInventory(new ItemStack(Items.ENCHANTED_GOLDEN_APPLE), Prediction.SERVER_ONLY);
			tell(player, "Every island crop of the Grand Line is in your vault. A true green thumb!", ChatFormatting.GOLD);
		}
		if (!prize.isEmpty()) {
			tell(player, "Seed Vault reward: " + prize.getCount() + " " + prize.getHoverName().getString(), ChatFormatting.GOLD);
			player.getInventory().placeItemBackInInventory(prize, Prediction.SERVER_ONLY);
		}
	}

	static void showCatalog(ServerPlayer player) {
		Map<String, Long> catalog = catalog(player);
		long today = today(player);
		tell(player, "Seed Vault: " + catalog.size() + "/" + IslandCrop.values().length + " island crops banked.", ChatFormatting.GOLD);
		for (IslandCrop crop : IslandCrop.values()) {
			MutableComponent line = Component.literal(" " + crop.title + " ").withStyle(ChatFormatting.WHITE);
			if (!catalog.containsKey(crop.id)) {
				line.append(Component.literal("- not banked (find seeds on " + crop.homeName + ")").withStyle(ChatFormatting.DARK_GRAY));
			} else if (catalog.get(crop.id) >= today) {
				line.append(Component.literal("- taken today").withStyle(ChatFormatting.GRAY));
			} else {
				line.append(Component.literal("[Take a seed]").withStyle(style -> style.withColor(ChatFormatting.GREEN).withUnderlined(true)
						.withClickEvent(new ClickEvent.RunCommand("/seedvault take " + crop.id))));
			}
			player.sendSystemMessage(line);
		}
		if (catalog.isEmpty()) {
			tell(player, "Right-click the vault with an island seed to bank it. Break grass on an island to find its seeds.",
					ChatFormatting.GRAY);
		}
	}

	static void take(ServerPlayer player, String id) {
		IslandCrop crop = IslandCrop.byId(id);
		Map<String, Long> catalog = new HashMap<>(catalog(player));
		if (crop == null || !catalog.containsKey(crop.id)) {
			tell(player, "You haven't banked that seed.", ChatFormatting.RED);
			return;
		}
		if (!nearVault(player)) {
			tell(player, "Stand next to a Seed Vault.", ChatFormatting.RED);
			return;
		}
		long today = today(player);
		if (catalog.get(crop.id) >= today) {
			tell(player, "You already drew " + crop.title + " seeds today. Come back tomorrow.", ChatFormatting.GRAY);
			return;
		}
		catalog.put(crop.id, today);
		player.setAttached(CATALOG, catalog);
		player.getInventory().placeItemBackInInventory(new ItemStack(FarmItems.seeds(crop)), Prediction.SERVER_ONLY);
		tell(player, "Took a " + crop.title + " seed from the vault.", ChatFormatting.GREEN);
	}

	private static boolean nearVault(ServerPlayer player) {
		BlockPos center = player.blockPosition();
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-REACH, -REACH, -REACH), center.offset(REACH, REACH, REACH))) {
			if (player.level().getBlockState(pos).is(FarmBlocks.SEED_VAULT)) {
				return true;
			}
		}
		return false;
	}

	private static void tell(ServerPlayer player, String text, ChatFormatting color) {
		player.sendSystemMessage(Component.literal(text).withStyle(color));
	}
}
