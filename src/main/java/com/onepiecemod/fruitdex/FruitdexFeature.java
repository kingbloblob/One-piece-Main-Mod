package com.onepiecemod.fruitdex;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.util.Prediction;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.item.DevilFruitItem;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.power.ModAttachments;

/**
 * The Devil Fruit Encyclopedia: a book that fills in a page for every fruit you get your hands on.
 * A fruit counts as found once it has been in your inventory (or you ate it).
 * Finding more fruits pays out berries at a few milestones.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class FruitdexFeature {
	/** Ids of every fruit this player has found, like "mera_mera_no_mi". Kept forever, even after death. */
	public static final AttachmentType<List<String>> DISCOVERED = AttachmentRegistry.create(
			OnePieceMod.id("fruits_discovered"),
			builder -> builder
					.persistent(Codec.STRING.listOf())
					.copyOnDeath()
	);

	/** Fruits you've seen a boss use but don't have yet. Their page shows who has them. Kept forever. */
	public static final AttachmentType<List<String>> SIGHTED = AttachmentRegistry.create(
			OnePieceMod.id("fruits_sighted"),
			builder -> builder
					.persistent(Codec.STRING.listOf())
					.copyOnDeath()
	);

	/** Berries for finding every fruit of one type. */
	private static final Map<DevilFruit.Type, Integer> TYPE_REWARDS = Map.of(
			DevilFruit.Type.PARAMECIA, 1200, DevilFruit.Type.LOGIA, 600, DevilFruit.Type.ZOAN, 800);

	/** How many fruits you need to find for each berry reward, and how many berries it pays. */
	private static final Map<Integer, Integer> MILESTONES = Map.of(5, 25, 15, 60, 30, 120, 50, 250, 75, 400, 108, 1500); // 108 = every fruit (DevilFruits.ALL)

	public static final Item ENCYCLOPEDIA = register("devil_fruit_encyclopedia", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Devil Fruit Encyclopedia");
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				open(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		}
	}, new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));

	public static void initialize() {
		FruitdexPayloads.initialize();
		FirstBite.initialize();
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> output.accept(ENCYCLOPEDIA));

		// Once a second, look through everyone's inventory for fruits they haven't found yet.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				var inventory = player.getInventory();
				for (int i = 0; i < inventory.getContainerSize(); i++) {
					if (inventory.getItem(i).getItem() instanceof DevilFruitItem fruitItem) {
						discover(player, fruitItem.getFruit());
					}
				}
				// Bosses close by who have eaten a fruit: you've seen it in action.
				for (com.onepiecemod.character.CharacterEntity boss : player.level().getEntitiesOfClass(
						com.onepiecemod.character.CharacterEntity.class, player.getBoundingBox().inflate(24), c -> c.isBoss() && c.isAlive())) {
					var data = boss.getData();
					if (data != null && data.fruitItem != null && data.fruitItem.startsWith("onepiece:")) {
						DevilFruit fruit = DevilFruits.get(data.fruitItem.substring("onepiece:".length()));
						if (fruit != null) {
							sight(player, fruit, data.name);
						}
					}
				}
			}
		});
	}

	public static List<String> discovered(Player player) {
		return player.getAttachedOrElse(DISCOVERED, List.of());
	}

	/** Adds a fruit to the player's encyclopedia, if it isn't there yet. */
	public static void discover(ServerPlayer player, DevilFruit fruit) {
		List<String> found = discovered(player);
		if (found.contains(fruit.id())) {
			return;
		}
		List<String> updated = new ArrayList<>(found);
		updated.add(fruit.id());
		player.setAttached(DISCOVERED, updated);

		int count = updated.size();
		int total = DevilFruits.ALL.size();
		player.sendSystemMessage(Component.literal("New encyclopedia page: ").withStyle(ChatFormatting.LIGHT_PURPLE)
				.append(Component.literal(fruit.name()).withStyle(ChatFormatting.GOLD))
				.append(Component.literal(" (" + count + "/" + total + " found)").withStyle(ChatFormatting.GRAY)));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0f, 1.0f);

		// Every fruit of one type found: a bonus from the World Economy Journal.
		int ofType = 0, typeTotal = 0;
		for (DevilFruit other : DevilFruits.ALL) {
			if (other.type() == fruit.type()) {
				typeTotal++;
				if (updated.contains(other.id())) {
					ofType++;
				}
			}
		}
		if (ofType == typeTotal) {
			int bonus = TYPE_REWARDS.getOrDefault(fruit.type(), 500);
			String typeName = fruit.type().name().charAt(0) + fruit.type().name().substring(1).toLowerCase();
			ItemStack reward = new ItemStack(CharacterFeature.BERRY, bonus);
			if (!player.getInventory().add(reward)) {
				player.drop(reward, false, Prediction.SERVER_ONLY);
			}
			player.sendSystemMessage(Component.literal("Every " + typeName + " fruit is in your encyclopedia! +" + bonus + " berries.")
					.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/fruitdex_" + fruit.type().name().toLowerCase());
		}

		Integer berries = MILESTONES.get(count);
		if (berries != null) {
			ItemStack reward = new ItemStack(CharacterFeature.BERRY, berries);
			if (!player.getInventory().add(reward)) {
				player.drop(reward, false, Prediction.SERVER_ONLY);
			}
			player.sendSystemMessage(Component.literal("Encyclopedia milestone! " + count + " fruits found. The World Economy Journal pays you "
					+ berries + " berries for your research.").withStyle(ChatFormatting.GREEN));
			player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0f, 1.2f);
		}
	}

	public static List<String> sighted(Player player) {
		return player.getAttachedOrElse(SIGHTED, List.of());
	}

	/** Marks a fruit as seen in a fight (only if you don't have its page already). */
	public static void sight(ServerPlayer player, DevilFruit fruit, String user) {
		if (discovered(player).contains(fruit.id()) || sighted(player).contains(fruit.id())) {
			return;
		}
		List<String> updated = new ArrayList<>(sighted(player));
		updated.add(fruit.id());
		player.setAttached(SIGHTED, updated);
		player.sendSystemMessage(Component.literal("Encyclopedia: you saw " + user + " use the ").withStyle(ChatFormatting.LIGHT_PURPLE)
				.append(Component.literal(fruit.name()).withStyle(ChatFormatting.GOLD))
				.append(Component.literal(". Beat them to claim it!").withStyle(ChatFormatting.LIGHT_PURPLE)));
	}

	private static void open(ServerPlayer player) {
		if (!ServerPlayNetworking.canSend(player, FruitdexPayloads.Open.TYPE)) {
			player.sendSystemMessage(Component.literal("You have found " + discovered(player).size() + " of " + DevilFruits.ALL.size() + " Devil Fruits."));
			return;
		}
		ServerPlayNetworking.send(player, new FruitdexPayloads.Open(
				discovered(player),
				sighted(player),
				player.getAttachedOrElse(ModAttachments.DEVIL_FRUIT, ""),
				player.getAttachedOrElse(ModAttachments.AWAKENED, false),
				player.getAttachedOrElse(ModAttachments.FRUIT_MASTERY, 0)
		));
	}

	private static Item register(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}
}
