package com.onepiecemod.guide;

import java.util.function.Consumer;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.story.StoryFeature;

/**
 * The Crafter's Journal (it used to be called the Pirate's Handbook; the item id is still pirates_handbook): an in-game guide.
 * The book screen is journal/client/JournalScreen. Right-click it to read about races, Haki,
 * fighting styles, crafting stations, the story and everything else. The text is in onepiece/guide.json.
 * - You get one the first time you join (players who joined before this book existed get one too).
 * - Lost it? Type /guide, or craft one from a Book and a Paper.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class GuideFeature {
	/**
	 * Opens the book screen. The screen only exists on the client, so the client part of the mod
	 * fills this in when the game starts. On a dedicated server it stays empty and does nothing.
	 */
	public static Consumer<InteractionHand> openBook = hand -> {};

	public static final Item HANDBOOK = register("pirates_handbook", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Crafter's Journal");
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (level.isClientSide()) {
				openBook.accept(hand);
			}
			return InteractionResult.SUCCESS;
		}
	}, new Item.Properties().stacksTo(1));

	/** True once a player got their first handbook, so they only get it once. */
	public static final AttachmentType<Boolean> GOT_HANDBOOK = AttachmentRegistry.create(
			OnePieceMod.id("got_handbook"),
			builder -> builder.persistent(Codec.BOOL).copyOnDeath()
	);

	public static void initialize() {
		// Shown in the "One Piece: Story" creative tab, right after the Captain's Log.
		CreativeModeTabEvents.modifyOutputEvent(StoryFeature.TAB_KEY)
				.register(output -> output.insertAfter(StoryFeature.CAPTAINS_LOG, HANDBOOK));

		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			ServerPlayer player = handler.player;
			if (!Boolean.TRUE.equals(player.getAttached(GOT_HANDBOOK))) {
				player.setAttached(GOT_HANDBOOK, true);
				give(player);
				player.sendSystemMessage(Component.literal("You got a Crafter's Journal. Right-click it to read about everything: recipes, Devil Fruits, creatures, bosses and more.")
						.withStyle(ChatFormatting.GOLD));
			}
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("guide").executes(GuideFeature::newBook)));
	}

	/** /guide: a new handbook, if you lost yours. */
	private static int newBook(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (player.getInventory().countItem(HANDBOOK) > 0) {
			context.getSource().sendFailure(Component.literal("You already have a Crafter's Journal. Right-click it to read it."));
			return 0;
		}
		give(player);
		return 1;
	}

	private static void give(ServerPlayer player) {
		ItemStack stack = new ItemStack(HANDBOOK);
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY); // Inventory full: drop it at their feet.
		}
	}

	private static Item register(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}
}
