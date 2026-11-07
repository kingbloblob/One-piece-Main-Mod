package com.onepiecemod.story;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.Locations;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.item.DevilFruitItem;
import com.onepiecemod.item.ModItems;

/**
 * Story gates: shortcuts that would skip the voyage are held back until the right chapter.
 * - A story boss's Wanted Poster only works after you beat that boss at its lair (posters are for rematches).
 * - Devil Fruit awakening opens after Wano.
 * - Rayleigh's paid Haki lessons open at Sabaody and stop at level 3.
 * - Conqueror's Haki only has a chance to awaken the first time you beat each boss.
 * - Leaves, treasure hoards and Sea Kings only drop Devil Fruits that fit your saga (an Emperor's fruit won't drop on day one).
 * - Shopkeepers keep their best wares for later sagas (see shopLevelCap).
 * - The Corrida Colosseum opens at the Dressrosa chapter.
 * - Laugh Tale's treasure and Roger wait until you carry all four Road Poneglyph rubbings.
 *
 * Gates never apply in Creative. An operator can turn them all off for the world with /story gates off.
 */
public class StoryGates {
	/** Saved on the Overworld: true when an operator turned the gates off. */
	public static final AttachmentType<Boolean> GATES_OFF = AttachmentRegistry.create(
			OnePieceMod.id("story_gates_off"),
			builder -> builder.persistent(Codec.BOOL)
	);

	/** Runs before the rest of the mod's right-click handlers, so a gate can stop a click first. */
	private static final Identifier EARLY = OnePieceMod.id("story_gates");

	public static final String SABAODY = "sabaody";
	public static final String AFTER_WANO = "wano";
	public static final String SHOP_JOURNEYMAN = "drum_island";
	public static final String SHOP_MASTER = "fishman_island";
	/** The Corrida Colosseum opens with the Dressrosa arc's first chapter (its Champion Cup is a goal there). */
	public static final String DRESSROSA = "dressrosa_colosseum";

	public static void initialize() {
		UseBlockCallback.EVENT.addPhaseOrdering(EARLY, Event.DEFAULT_PHASE);
		UseEntityCallback.EVENT.addPhaseOrdering(EARLY, Event.DEFAULT_PHASE);

		UseBlockCallback.EVENT.register(EARLY, (player, level, hand, hitResult) -> {
			if (!(player instanceof ServerPlayer serverPlayer) || !gatesOn(player)) {
				return InteractionResult.PASS;
			}
			// Wanted Posters are used on a block.
			String boss = posterBoss(player.getItemInHand(hand));
			if (boss != null && !posterAllowed(player, boss)) {
				CharacterData data = CharacterData.get(boss);
				String lair = Locations.home(boss);
				tell(serverPlayer, "The poster's too old to lure " + data.name + " out. Beat them"
						+ (lair != null ? " at " + Locations.name(lair) : "") + " first; after that this poster calls them out for a rematch.");
				return InteractionResult.FAIL;
			}
			// Laugh Tale's chests.
			if (level.getBlockEntity(hitResult.getBlockPos()) instanceof Container && !laughTaleOpen(player)
					&& StoryPlaces.isInside((ServerLevel) level, hitResult.getBlockPos(), "laugh_tale")) {
				tell(serverPlayer, "The lid won't move. Old writing on it says it opens only for one who has read all four Road Poneglyphs.");
				return InteractionResult.FAIL;
			}
			return InteractionResult.PASS;
		});

		UseEntityCallback.EVENT.register(EARLY, (player, level, hand, entity, hitResult) -> {
			if (!(player instanceof ServerPlayer serverPlayer) || !(entity instanceof CharacterEntity character)
					|| character.isBoss() || !gatesOn(player)) {
				return InteractionResult.PASS;
			}
			String id = character.getCharacterId();
			if ("roger".equals(id) && !laughTaleOpen(player)) {
				tell(serverPlayer, "Gol D. Roger: Wahahaha! You came early. Come back when you've read all four Road Poneglyphs.");
				return InteractionResult.FAIL;
			}
			if ("rayleigh".equals(id) && player.isShiftKeyDown()) {
				if (!StoryProgress.orStart(player).reached(SABAODY)) {
					tell(serverPlayer, "Silvers Rayleigh: Haki lessons? Make it to Sabaody first, kid. Then we'll talk.");
					return InteractionResult.FAIL;
				}
				HakiData haki = HakiAttachments.get(player);
				if (haki.observationLevel() >= 3 && haki.armamentLevel() >= 3) {
					tell(serverPlayer, "Silvers Rayleigh: I've taught you all I can. The rest you'll only learn in real fights. But I can still help you choose your path.");
					com.onepiecemod.progression.PathTraining.showHaki(serverPlayer);
					return InteractionResult.FAIL;
				}
			}
			return InteractionResult.PASS;
		});

		// Leaves, treasure hoards, Sea Kings: swap a fruit that's too strong for your saga for one that fits.
		LootTableEvents.MODIFY_DROPS.register((table, context, drops) -> {
			ServerPlayer player = context.getOptional(LootContextParams.THIS_ENTITY) instanceof ServerPlayer opener ? opener
					: context.getOptional(LootContextParams.LAST_DAMAGE_PLAYER) instanceof ServerPlayer killer ? killer : null;
			if (player == null || !gatesOn(player)) {
				return;
			}
			drops.replaceAll(drop -> fitFruit(player, drop));
		});
	}

	// ---- The gates. Other parts of the mod call these. ----

	/** False in Creative, and everywhere once an operator types /story gates off. */
	public static boolean gatesOn(Player player) {
		if (player.isCreative() || player.isSpectator() || !(player instanceof ServerPlayer serverPlayer)) {
			return false;
		}
		return !gatesOff(serverPlayer.level().getServer());
	}

	public static boolean gatesOff(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(GATES_OFF, false);
	}

	public static void setGatesOff(MinecraftServer server, boolean off) {
		server.overworld().setAttached(GATES_OFF, off);
	}

	/** Devil Fruit awakening (power/Awakening.java): only after Wano. */
	public static boolean awakeningAllowed(Player player) {
		return !gatesOn(player) || StoryProgress.orStart(player).completed(AFTER_WANO);
	}

	/**
	 * Conqueror's Haki's random awakening when a boss falls (haki/HakiPowers.java): only the first win against each boss rolls.
	 * Calling this uses up the roll for that boss.
	 */
	public static boolean conquerorRollAllowed(Player player, String bossId) {
		if (!gatesOn(player)) {
			return true;
		}
		StoryProgress progress = StoryProgress.orStart(player);
		String flag = "conqueror_roll:" + bossId;
		if (progress.hasFlag(flag)) {
			return false;
		}
		StoryProgress.set(player, progress.withFlag(flag));
		return true;
	}

	/**
	 * The highest shop level (1 Novice to 5 Master) a player may buy from, however much a trader has levelled up.
	 * East Blue sees Novice and Apprentice wares; Journeyman opens in Paradise, Expert at Sabaody, Master in the New World.
	 */
	public static int shopLevelCap(Player player) {
		if (!gatesOn(player)) {
			return 5;
		}
		StoryProgress progress = StoryProgress.orStart(player);
		if (progress.reached(SHOP_MASTER)) {
			return 5;
		}
		if (progress.reached(SABAODY)) {
			return 4;
		}
		return progress.reached(SHOP_JOURNEYMAN) ? 3 : 2;
	}

	/** What a trader says about the wares a player can't buy yet. */
	public static String shopCapHint(int cap) {
		return switch (cap) {
			case 2 -> "I keep my better stock for pirates who've made it into the Grand Line.";
			case 3 -> "My best wares? Come back once you've reached Sabaody.";
			default -> "My finest goods are for New World pirates only.";
		};
	}

	/** The Corrida Colosseum (arena/) opens at the start of the Dressrosa arc. */
	public static boolean colosseumOpen(Player player) {
		return !gatesOn(player) || StoryProgress.orStart(player).reached(DRESSROSA);
	}

	/** A story boss's Wanted Poster works once you've beaten that boss (at its lair). */
	public static boolean posterAllowed(Player player, String bossId) {
		CharacterData data = CharacterData.get(bossId);
		if (data == null || !data.isBossRole() || !gatesOn(player)) {
			return true; // Posters of friendly characters are just for fun fights.
		}
		return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, bossId);
	}

	/** Laugh Tale opens for players carrying all four Road Poneglyph rubbings, or who already finished the story. */
	public static boolean laughTaleOpen(Player player) {
		if (StoryProgress.orStart(player).finished()) {
			return true;
		}
		for (Item rubbing : StoryFeature.RUBBINGS) {
			if (player.getInventory().countItem(rubbing) == 0) {
				return false;
			}
		}
		return true;
	}

	/**
	 * A Devil Fruit stronger than the player's saga allows becomes a random fruit that fits; anything else comes back unchanged.
	 * Leaves, treasure hoards and Sea Kings all go through this.
	 */
	public static ItemStack fitFruit(ServerPlayer player, ItemStack drop) {
		if (!(drop.getItem() instanceof DevilFruitItem) || !gatesOn(player)) {
			return drop;
		}
		int maxTier = fruitTier(player);
		if (tierOf(drop.getItem()) <= maxTier) {
			return drop;
		}
		List<Item> allowed = new ArrayList<>();
		for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
			if (tierOf(fruit) <= maxTier) {
				allowed.add(fruit);
			}
		}
		return allowed.isEmpty() ? drop : new ItemStack(allowed.get(player.getRandom().nextInt(allowed.size())));
	}

	// ---- Helpers ----

	/** The boss id of a Wanted Poster, like "kaido", or null for any other item. */
	private static String posterBoss(ItemStack stack) {
		String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
		return path.startsWith("wanted_poster_") ? path.substring("wanted_poster_".length()) : null;
	}

	private static int fruitTier(Player player) {
		StoryData.Chapter chapter = StoryData.chapter(StoryProgress.orStart(player).chapter());
		return chapter == null ? 5 : chapter.saga.fruitTier;
	}

	private static Map<Item, Integer> fruitTiers;

	/** How strong a fruit is: the tier of the character who eats it in the story. Fruits nobody has are tier 1. */
	private static int tierOf(Item fruit) {
		if (fruitTiers == null) {
			fruitTiers = new HashMap<>();
			for (CharacterData character : CharacterData.all().values()) {
				if (character.fruitItem != null) {
					Item item = CharacterData.item(character.fruitItem);
					fruitTiers.merge(item, character.tier, Math::max);
				}
			}
		}
		return fruitTiers.getOrDefault(fruit, 1);
	}

	private static void tell(ServerPlayer player, String text) {
		player.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.YELLOW));
	}
}
