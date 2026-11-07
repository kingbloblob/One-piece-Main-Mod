package com.onepiecemod.keepsake;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Prediction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.character.QuestHandler;
import com.onepiecemod.news.NewsCoo;
import com.onepiecemod.news.Newspaper;
import com.onepiecemod.news.WantedPosterBlock;
import com.onepiecemod.news.WantedPosterBlockEntity;

/**
 * How survival players collect character Wanted Posters and Vivre Cards:
 * - Vivre Cards are given by their owner: finish that character's quest line, or trade with them at Master level.
 * - Wanted Posters are bought with Berries at a wall Wanted Poster (hold Berries and right-click it). You get the
 *   pirate shown on it if they are a character (the wall already only shows pirates from your part of the story),
 *   otherwise a random one whose saga your story has reached. A boss's poster only sells after you've beaten them
 *   (it's a rematch ticket).
 * - Now and then the morning newspaper comes with a poster tucked inside.
 * A poster summons that character for a fight, so the saga gate keeps late-game fights (and their Devil Fruits) late.
 */
public class Keepsakes {
	/** Characters whose Vivre Card this player has been given (character ids). */
	public static final AttachmentType<List<String>> CARDS_GIVEN = list("vivre_cards_given");
	/** Characters whose poster this player has bought or found (character ids). */
	public static final AttachmentType<List<String>> POSTERS_GOT = list("posters_collected");
	/** The newspaper day this player was last checked for a poster insert. */
	public static final AttachmentType<Long> PAPER_CHECKED = AttachmentRegistry.create(
			OnePieceMod.id("poster_paper_checked"), builder -> builder.persistent(Codec.LONG).copyOnDeath());

	/** Poster price in Berries by character tier (1-5). */
	private static final int[] PRICE = {10, 10, 20, 40, 80, 150};
	/** Chance that a morning paper has a poster inside. */
	private static final float PAPER_POSTER_CHANCE = 0.25f;
	private static final int CHECK_EVERY_TICKS = 100;
	/** The top trader level (Master). */
	private static final int MASTER_LEVEL = 5;

	private static AttachmentType<List<String>> list(String name) {
		return AttachmentRegistry.create(OnePieceMod.id(name), builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());
	}

	public static void initialize() {
		UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
			ItemStack held = player.getItemInHand(hand);
			if (!held.is(CharacterFeature.BERRY) || !(level.getBlockState(hit.getBlockPos()).getBlock() instanceof WantedPosterBlock)) {
				return InteractionResult.PASS;
			}
			if (player instanceof ServerPlayer serverPlayer && level.getBlockEntity(hit.getBlockPos()) instanceof WantedPosterBlockEntity poster) {
				buyPoster(serverPlayer, poster.subject((ServerLevel) level).name());
			}
			return InteractionResult.SUCCESS;
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				checkQuestLines(player);
				checkNewspaper(player);
			}
		});
	}

	// ---- Rules ----

	/** The saga (0-5, as Newspaper.sagaNumber) from which a character's poster is for sale. */
	public static int posterSaga(CharacterData character) {
		return Math.max(0, Math.min(5, character.tier - 1));
	}

	public static int posterPrice(CharacterData character) {
		return PRICE[Math.max(0, Math.min(5, character.tier))];
	}

	public static final String[] SAGA_NAMES = {"Romance Dawn", "East Blue", "Paradise", "Summit War", "New World", "Final Saga"};

	public static boolean hasPoster(CharacterData character) {
		return !CharacterData.stack("onepiece:wanted_poster_" + character.id, 1).isEmpty();
	}

	public static boolean hasCard(CharacterData character) {
		return !character.isBossRole() && !CharacterData.stack("onepiece:vivre_card_" + character.id, 1).isEmpty();
	}

	/** Why this player can't buy the poster yet, or null if they can. */
	private static String posterLock(ServerPlayer player, CharacterData character) {
		if (character.isBossRole()) {
			return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, character.id) ? null : "Beat " + character.name + " first";
		}
		return Newspaper.sagaNumber(player) >= posterSaga(character) ? null : "Not wanted yet in your part of the story";
	}

	// ---- Buying posters ----

	private static void buyPoster(ServerPlayer player, String shownName) {
		CharacterData shown = byName(shownName);
		CharacterData pick = null;
		if (shown != null && hasPoster(shown)) {
			// The wall only shows pirates from your part of the story, so the one on it is always for sale (bosses still need beating).
			String lock = shown.isBossRole() ? posterLock(player, shown) : null;
			if (lock != null) {
				player.sendSystemMessage(Component.literal("The Marines won't sell " + shown.name + "'s poster yet. " + lock + ".")
						.withStyle(ChatFormatting.RED));
				return;
			}
			pick = shown;
		} else {
			pick = randomForSale(player, true);
			if (pick == null) {
				pick = randomForSale(player, false);
			}
		}
		if (pick == null) {
			player.sendSystemMessage(Component.literal("No posters for sale yet. Get further in the story.").withStyle(ChatFormatting.GRAY));
			return;
		}
		int price = posterPrice(pick);
		Inventory inventory = player.getInventory();
		if (inventory.countItem(CharacterFeature.BERRY) < price) {
			player.sendSystemMessage(Component.literal(pick.name + "'s poster costs " + price + " Berries.").withStyle(ChatFormatting.RED));
			return;
		}
		takeBerries(inventory, price);
		give(player, CharacterData.stack("onepiece:wanted_poster_" + pick.id, 1));
		CharacterAttachments.add(player, POSTERS_GOT, pick.id);
		player.sendSystemMessage(Component.literal("You buy " + pick.name + "'s Wanted Poster for " + price + " Berries. Use it on the ground to fight them.")
				.withStyle(ChatFormatting.GOLD));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	/** A random character whose poster this player may buy; onlyNew = one they don't have yet. */
	private static CharacterData randomForSale(ServerPlayer player, boolean onlyNew) {
		List<CharacterData> options = new ArrayList<>();
		for (CharacterData character : CharacterData.all().values()) {
			if (hasPoster(character) && posterLock(player, character) == null
					&& (!onlyNew || !CharacterAttachments.has(player, POSTERS_GOT, character.id))) {
				options.add(character);
			}
		}
		return options.isEmpty() ? null : options.get(player.getRandom().nextInt(options.size()));
	}

	private static CharacterData byName(String name) {
		if (name == null) {
			return null;
		}
		String wanted = name.toLowerCase(Locale.ROOT);
		for (CharacterData character : CharacterData.all().values()) {
			if (character.name != null && character.name.toLowerCase(Locale.ROOT).equals(wanted)) {
				return character;
			}
		}
		return null;
	}

	private static void takeBerries(Inventory inventory, int count) {
		for (ItemStack stack : inventory.getNonEquipmentItems()) {
			if (count <= 0) {
				break;
			}
			if (stack.is(CharacterFeature.BERRY)) {
				int take = Math.min(count, stack.getCount());
				stack.shrink(take);
				count -= take;
			}
		}
		inventory.setChanged();
	}

	// ---- Vivre Cards ----

	/** Finishing a character's whole quest line earns their Vivre Card. */
	private static void checkQuestLines(ServerPlayer player) {
		for (CharacterData character : CharacterData.all().values()) {
			if (!hasCard(character) || character.quests.isEmpty() || CharacterAttachments.has(player, CARDS_GIVEN, character.id)) {
				continue;
			}
			if (CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, QuestHandler.key(character, character.quests.size() - 1))) {
				giveCard(player, character, "for finishing their quests");
			}
		}
	}

	/** Called by CharacterEntity after each trade: trading at Master level earns their Vivre Card. */
	public static void onTrade(Player player, String characterId, int tradeLevel) {
		CharacterData character = CharacterData.get(characterId);
		if (player instanceof ServerPlayer serverPlayer && character != null && tradeLevel >= MASTER_LEVEL && hasCard(character)
				&& !CharacterAttachments.has(player, CARDS_GIVEN, characterId)) {
			giveCard(serverPlayer, character, "as a thank-you for being such a good customer");
		}
	}

	private static void giveCard(ServerPlayer player, CharacterData character, String why) {
		CharacterAttachments.add(player, CARDS_GIVEN, character.id);
		give(player, CharacterData.stack("onepiece:vivre_card_" + character.id, 1));
		player.sendSystemMessage(Component.literal(character.name + " gives you their Vivre Card " + why + ". It always points the way back to them.")
				.withStyle(ChatFormatting.AQUA));
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.6f, 1.4f);
	}

	// ---- Newspaper inserts ----

	/** When a new paper has come (NewsCoo.LAST_PAPER moved on), sometimes slip a poster in with it. */
	private static void checkNewspaper(ServerPlayer player) {
		Long paperDay = player.getAttached(NewsCoo.LAST_PAPER);
		if (paperDay == null) {
			return;
		}
		long checked = player.getAttachedOrElse(PAPER_CHECKED, -1L);
		if (checked == paperDay) {
			return;
		}
		player.setAttached(PAPER_CHECKED, paperDay);
		if (checked < 0 || player.getRandom().nextFloat() >= PAPER_POSTER_CHANCE) {
			return; // The first check only remembers the day.
		}
		CharacterData pick = randomForSale(player, true);
		if (pick != null && !pick.isBossRole()) {
			give(player, CharacterData.stack("onepiece:wanted_poster_" + pick.id, 1));
			CharacterAttachments.add(player, POSTERS_GOT, pick.id);
			player.sendSystemMessage(Component.literal("A Wanted Poster falls out of today's paper: " + pick.name + "!").withStyle(ChatFormatting.GOLD));
		}
	}

	private static void give(Player player, ItemStack stack) {
		if (!stack.isEmpty() && !player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY);
		}
	}
}
