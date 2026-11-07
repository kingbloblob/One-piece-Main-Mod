package com.onepiecemod.style;

import java.util.List;

import net.minecraft.util.Prediction;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.event.player.UseEntityCallback;

import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;

/**
 * Learning a style from its master: sneak and right-click the friendly (Vivre Card) version of
 * a master (Zoro, Sanji, Jinbe, Koby, Sabo, Oden, Kin'emon, Brook, Garp or Usopp). A normal right-click still opens their shop or quest as before.
 * The master tells you what they want; bring it and sneak-click again to learn.
 */
public class StyleMasters {
	public static void initialize() {
		UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
			if (hand != InteractionHand.MAIN_HAND || !player.isShiftKeyDown()
					|| !(entity instanceof CharacterEntity character) || character.isBoss()) {
				return InteractionResult.PASS;
			}
			FightingStyle style = FightingStyle.byMaster(character.getCharacterId());
			if (style == null) {
				return InteractionResult.PASS; // Not a master: let the normal shop or quest happen.
			}
			if (player instanceof ServerPlayer serverPlayer) {
				askToLearn(serverPlayer, character, style);
			}
			return InteractionResult.SUCCESS; // Handled: don't also open the shop.
		});
	}

	private static void askToLearn(ServerPlayer player, CharacterEntity master, FightingStyle style) {
		String name = master.getData().name;
		if (StyleAttachments.knows(player, style)) {
			StyleAttachments.setActive(player, style);
			say(player, name, "Show me your " + style.title() + " again. (You switched to it.)");
			com.onepiecemod.progression.PathTraining.showStyle(player, style); // Branching upgrades this master can train.
			return;
		}

		boolean free = player.getAbilities().instabuild; // Creative mode learns for free, handy for testing.
		Inventory inventory = player.getInventory();
		int bosses = player.getAttachedOrElse(CharacterAttachments.BOSSES_DEFEATED, List.<String>of()).size();
		int berries = inventory.countItem(CharacterFeature.BERRY);
		int trialItems = style.trialItem() == Items.AIR ? 0 : inventory.countItem(style.trialItem());
		int swords = countSwords(inventory);

		if (!free) {
			String missing = "";
			if (berries < style.berryCost()) {
				missing += "\n- " + style.berryCost() + " Berries (you have " + berries + ")";
			}
			if (style.trialCount() > 0 && trialItems < style.trialCount()) {
				missing += "\n- " + style.trialCount() + " " + itemName(style.trialItem()) + " (you have " + trialItems + ")";
			}
			if (swords < style.swordsNeeded()) {
				missing += "\n- " + style.swordsNeeded() + " swords in your hotbar or off hand, any kind (you have " + swords + ")";
			}
			if (bosses < style.bossesNeeded()) {
				missing += "\n- beat " + style.bossesNeeded() + " different bosses first (you've beaten " + bosses + ")";
			}
			if (!missing.isEmpty()) {
				say(player, name, pitch(style));
				player.sendSystemMessage(Component.literal("To learn " + style.title() + " bring:" + missing).withStyle(ChatFormatting.RED));
				return;
			}
			take(inventory, CharacterFeature.BERRY, style.berryCost());
			if (style.trialCount() > 0) {
				take(inventory, style.trialItem(), style.trialCount());
			}
		}

		say(player, name, welcome(style));
		teach(player, style);
		if (style == FightingStyle.SANTORYU) {
			player.getInventory().placeItemBackInInventory(new ItemStack(StyleItems.WADO_ICHIMONJI), Prediction.SERVER_ONLY);
			say(player, name, "Take this one. Wado Ichimonji. It belonged to someone who never got to finish her dream.");
		}
	}

	/** Teaches the style, switches to it and explains the controls. Used by masters and Dojo Scrolls. */
	public static void teach(ServerPlayer player, FightingStyle style) {
		StyleAttachments.learn(player, style);
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0f, 1.0f);
		player.sendSystemMessage(Component.literal("You learned " + style.title() + "!").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal(style.howToFight()).withStyle(ChatFormatting.YELLOW));
		player.sendSystemMessage(Component.literal("Press Z to use a technique, Shift+Z to pick the next one. Type /style for the full list.")
				.withStyle(ChatFormatting.YELLOW));
	}

	private static String pitch(FightingStyle style) {
		return switch (style) {
			case SANTORYU -> "You want to learn Three Sword Style? Then come back with three swords. And pay for the booze.";
			case BLACK_LEG -> "A cook never fights with his hands. Bring me some cooked salmon and I'll teach you to kick.";
			case FISHMAN_KARATE -> "Fish-Man Karate moves the water inside your enemy. Bring shards from the sea and I'll teach you.";
			case ROKUSHIKI -> "The Six Powers took me years of Marine training. Prove yourself against some real bosses first.";
			case RYUSOKEN -> "Dragon Claw Fist crushes steel. Bring me iron, and show me you've beaten a couple of strong foes.";
			case NITORYU -> "Two swords, no fear. Beat some real bosses and bring two swords, and I'll show you Oden's way.";
			case KITSUNEBI -> "Fox Fire Style cuts through flame. Bring me blaze powder and we'll begin.";
			case SOUL_FENCING -> "Yohoho! Bring me some bones and I'll teach you to fence. Though I have no bones to spare myself... oh wait.";
			case FIST_OF_LOVE -> "You want my Fist of Love? Bring me bread, prove you can take down some bosses, and grit your teeth!";
			case SOGEKING -> "I am the Sniper King! Bring me seeds for my Pop Greens and I'll teach you to shoot.";
		};
	}

	private static String welcome(FightingStyle style) {
		return switch (style) {
			case SANTORYU -> "Alright. One in each hand, one in your mouth. Don't get lost.";
			case BLACK_LEG -> "Kick with your whole body, and never let a lady or a hungry person get hurt.";
			case FISHMAN_KARATE -> "Feel the water in the air and in your enemy. Strike it, not the skin.";
			case ROKUSHIKI -> "Kick the air ten times in a blink and you'll stand on it. Let's begin!";
			case RYUSOKEN -> "Grip like a dragon. Whatever you grab, you break.";
			case NITORYU -> "Two swords, and the will to protect. That's all Oden Nitoryu needs.";
			case KITSUNEBI -> "Flames are just another thing to cut. Strike fast and they can't touch you.";
			case SOUL_FENCING -> "Light feet, a cold blade, and a song in your heart. Yohoho!";
			case FIST_OF_LOVE -> "No tricks. Just punch it until it stops moving!";
			case SOGEKING -> "Aim true, and never tell anyone who's behind the mask.";
		};
	}

	private static void say(ServerPlayer player, String name, String text) {
		player.sendSystemMessage(Component.literal("<" + name + "> " + text));
	}

	public static void tell(ServerPlayer player, String text) {
		player.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.YELLOW));
	}

	/** Swords in the main hand, off hand and hotbar. Three Sword Style needs three of them. */
	public static int countSwords(Inventory inventory) {
		int swords = 0;
		for (int slot = 0; slot < 9; slot++) {
			if (inventory.getItem(slot).is(ItemTags.SWORDS)) {
				swords++;
			}
		}
		if (inventory.player.getOffhandItem().is(ItemTags.SWORDS)) {
			swords++;
		}
		return swords;
	}

	private static String itemName(Item item) {
		return item.getName(new ItemStack(item)).getString();
	}

	private static void take(Inventory inventory, Item item, int amount) {
		for (int i = 0; i < inventory.getContainerSize() && amount > 0; i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(item)) {
				int taken = Math.min(amount, stack.getCount());
				stack.shrink(taken);
				amount -= taken;
			}
		}
		inventory.setChanged();
	}
}
