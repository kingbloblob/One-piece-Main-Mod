package com.onepiecemod.career;

import java.util.List;

import com.onepiecemod.sound.ModSounds;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;

/**
 * Everything other parts of the mod need to know about careers, and the rules for joining, leaving,
 * earning points, promotions and court-martials.
 */
public final class Careers {
	public static final AttachmentType<CareerData> CAREER = AttachmentRegistry.create(
			OnePieceMod.id("career"),
			builder -> builder.persistent(CareerData.CODEC).copyOnDeath()
	);

	/** A pirate with a bigger bounty than this is too well known to join the Marines. */
	public static final long ENLIST_BOUNTY_LIMIT = 10_000_000L;
	/** Strikes before a Marine is court-martialed. */
	public static final int MAX_STRIKES = 3;
	/** For story goals that ask for a bounty: each point of Merit counts as this many Berries of fame. */
	private static final long RENOWN_PER_MERIT = 1_000_000L;

	private Careers() {
	}

	// ---- Reading ----

	public static CareerData get(Player player) {
		return player.getAttachedOrElse(CAREER, CareerData.EMPTY);
	}

	public static Career career(Player player) {
		return get(player).path();
	}

	public static boolean isMarine(Entity entity) {
		return entity instanceof Player player && career(player) == Career.MARINE;
	}

	public static boolean isRevolutionary(Entity entity) {
		return entity instanceof Player player && career(player) == Career.REVOLUTIONARY;
	}

	/**
	 * How famous the player is, in Berries, for story goals like "reach a bounty of 30,000,000".
	 * Pirates and Revolutionaries use their bounty; Marines (who have none) use their Merit.
	 */
	public static long renown(Player player) {
		CareerData data = get(player);
		return data.path() == Career.MARINE ? Math.max(Bounty.get(player), data.points() * RENOWN_PER_MERIT) : Bounty.get(player);
	}

	/** "Lieutenant", "Army Commander", or "Pirate". */
	public static String title(Player player) {
		CareerData data = get(player);
		return data.path() == Career.PIRATE ? "Pirate" : data.currentRank().name();
	}

	public static long today(MinecraftServer server) {
		return server.overworld().getGameTime() / 24000L;
	}

	static void set(ServerPlayer player, CareerData data) {
		player.setAttached(CAREER, data);
		CareerPayloads.sync(player);
	}

	// ---- Joining and leaving ----

	/** Why this player can't join, or null if they can. */
	public static String whyNot(ServerPlayer player, Career path) {
		CareerData data = get(player);
		if (data.path() == path) {
			return "You're already " + (path == Career.MARINE ? "a Marine." : "with the Revolutionary Army.");
		}
		if (data.path() != Career.PIRATE) {
			return "You'll have to leave the " + data.path().displayName + "s first (/career leave).";
		}
		if (path == Career.MARINE) {
			if (data.has("deserter")) {
				return "The Navy doesn't take back a court-martialed deserter.";
			}
			if (Bounty.get(player) > ENLIST_BOUNTY_LIMIT) {
				return "Your bounty of " + Bounty.format(Bounty.get(player)) + " is too famous. The Navy only pardons small-time pirates (up to "
						+ Bounty.format(ENLIST_BOUNTY_LIMIT) + ").";
			}
		}
		return null;
	}

	/** Joins the Marines or the Revolutionary Army. Call only after {@link #whyNot} said yes. */
	public static void join(ServerPlayer player, Career path) {
		CareerData data = get(player).joined(path, today(player.level().getServer()));
		set(player, data);
		if (path == Career.MARINE) {
			long old = Bounty.get(player);
			Bounty.set(player, 0L);
			player.sendSystemMessage(Component.literal("You enlisted in the Marines as a Seaman Recruit!").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
			if (old > 0) {
				player.sendSystemMessage(Component.literal("Your " + Bounty.format(old) + " bounty was pardoned. The Navy won't hunt you now, but pirates will.")
						.withStyle(ChatFormatting.AQUA));
			}
			player.sendSystemMessage(Component.literal("Hunt pirates and carry out orders to earn Merit and climb the ranks to Fleet Admiral. "
					+ "Your Navy Den Den Mushi shows your rank, gives orders and calls backup.").withStyle(ChatFormatting.GRAY));
			news(player, player.getName().getString() + " has joined the Marines!");
		} else {
			player.sendSystemMessage(Component.literal("You joined the Revolutionary Army as a Sympathizer!").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD));
			player.sendSystemMessage(Component.literal("Fight the Navy and the World Government to earn Liberation and rise to Dragon's Right Hand. "
					+ "You keep your bounty: the Navy hunts you as before. Your Revolutionary Den Den Mushi gives orders and calls backup.")
					.withStyle(ChatFormatting.GRAY));
		}
		give(player, new ItemStack(path == Career.MARINE ? CareerFeature.NAVY_DEN_DEN_MUSHI : CareerFeature.REVOLUTIONARY_DEN_DEN_MUSHI));
		player.level().playSound(null, player.blockPosition(), path == Career.MARINE ? ModSounds.NAVY_BUGLE : SoundEvents.UI_TOAST_CHALLENGE_COMPLETE,
				SoundSource.PLAYERS, 1.0f, 1.0f);
		CareerMissions.clear(player);
	}

	/** Leaves the Marines or the Revolutionary Army and goes back to being a free pirate. */
	public static void leave(ServerPlayer player) {
		CareerData data = get(player);
		if (data.path() == Career.PIRATE) {
			return;
		}
		Career old = data.path();
		set(player, data.joined(Career.PIRATE, today(player.level().getServer())));
		CareerMissions.clear(player);
		player.sendSystemMessage(Component.literal(old == Career.MARINE
				? "You hand in your coat and leave the Navy with honour. You're a free sailor again."
				: "You part ways with the Revolutionary Army. Your bounty stays.").withStyle(ChatFormatting.YELLOW));
	}

	// ---- Points and promotions ----

	/**
	 * Adds Merit or Liberation, then promotes the player if they've earned it.
	 * @param big tell the player in chat (true) or just above the hotbar (false)
	 */
	public static void addPoints(ServerPlayer player, int amount, String why, boolean big) {
		CareerData data = get(player);
		if (data.path() == Career.PIRATE || amount <= 0) {
			return;
		}
		data = data.withPoints((int) Math.min(Integer.MAX_VALUE, (long) data.points() + amount));
		set(player, data);
		Component text = Component.literal("+" + amount + " " + data.path().points + (why.isEmpty() ? "" : " (" + why + ")"))
				.withStyle(data.path().color);
		if (big) {
			player.sendSystemMessage(text);
		} else {
			player.sendOverlayMessage(text);
		}
		checkPromotion(player);
	}

	/** How many of the rank's trial bosses this player has beaten (any difficulty counts). */
	public static int trialProgress(Player player, Career.Rank rank) {
		List<String> beaten = player.getAttachedOrElse(CharacterAttachments.BOSSES_DEFEATED, List.of());
		int done = 0;
		for (String boss : rank.trial()) {
			if (beaten.contains(boss) || beaten.contains(boss + ":hard") || beaten.contains(boss + ":expert")) {
				done++;
			}
		}
		return done;
	}

	public static boolean trialDone(Player player, Career.Rank rank) {
		return rank.trialCount() <= 0 || trialProgress(player, rank) >= rank.trialCount();
	}

	/** "Bring in Buggy", "Bring in 3 of: Kaido, Big Mom, ..." */
	public static String trialText(Career path, Career.Rank rank) {
		StringBuilder names = new StringBuilder();
		for (String boss : rank.trial()) {
			CharacterData data = CharacterData.get(boss);
			if (names.length() > 0) {
				names.append(rank.trialCount() == 1 ? " or " : ", ");
			}
			names.append(data != null ? data.name : boss);
		}
		String verb = path == Career.MARINE ? "Bring in " : "Defeat ";
		return rank.trialCount() > 1 ? verb + rank.trialCount() + " of: " + names : verb + names;
	}

	/** Promotes as far as the player's points and trials allow. */
	public static void checkPromotion(ServerPlayer player) {
		CareerData data = get(player);
		Career path = data.path();
		Career.Rank next = data.nextRank();
		while (next != null && data.points() >= next.need()) {
			if (!trialDone(player, next)) {
				String flag = "told_" + (data.rank() + 1);
				if (!data.has(flag)) {
					data = data.withFlag(flag);
					set(player, data);
					player.sendSystemMessage(Component.literal("You have enough " + path.points + " to become " + next.name() + ". "
							+ trialText(path, next) + " to earn the promotion.").withStyle(ChatFormatting.YELLOW));
				}
				return;
			}
			data = data.withRank(data.rank() + 1);
			set(player, data);
			promoted(player, path, next);
			next = data.nextRank();
		}
	}

	private static void promoted(ServerPlayer player, Career path, Career.Rank rank) {
		player.sendSystemMessage(Component.literal("Promoted to " + rank.name() + "!").withStyle(path.color, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("Salary " + rank.salary() + " Berries a day. Backup: " + rank.backup()
				+ (rank.backup() == 1 ? " soldier." : " soldiers.") + " Here's a bonus of " + rank.salary() * 5 + " Berries.")
				.withStyle(ChatFormatting.GRAY));
		give(player, new ItemStack(CharacterFeature.BERRY, rank.salary() * 5));
		player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
		int index = path.ranks.indexOf(rank);
		if (path == Career.MARINE && index >= 5) {
			// Captains and up make the papers. The Revolutionary Army keeps its ranks secret.
			news(player, player.getName().getString() + " has been promoted to Marine " + rank.name() + "!");
		}
	}

	// ---- Crimes ----

	/** A Marine hurt the Navy. Three strikes and they're out, with a bounty on their head. */
	public static void strike(ServerPlayer player, String why) {
		CareerData data = get(player);
		if (data.path() != Career.MARINE) {
			return;
		}
		int strikes = data.strikes() + 1;
		int lost = 50 + 25 * data.rank();
		if (strikes >= MAX_STRIKES) {
			courtMartial(player, why);
			return;
		}
		set(player, data.withStrikes(strikes).withPoints(data.points() - lost));
		player.sendSystemMessage(Component.literal(why + " Strike " + strikes + " of " + MAX_STRIKES + ": -" + lost
				+ " Merit. At " + MAX_STRIKES + " strikes you'll be court-martialed. (A promotion wipes your strikes.)").withStyle(ChatFormatting.RED));
	}

	/** Thrown out of the Navy: back to pirate, marked a deserter, with a bounty. */
	public static void courtMartial(ServerPlayer player, String why) {
		CareerData data = get(player);
		int rank = data.rank();
		set(player, data.joined(Career.PIRATE, today(player.level().getServer())).withFlag("deserter"));
		CareerMissions.clear(player);
		player.sendSystemMessage(Component.literal(why + " You've been court-martialed and thrown out of the Navy!").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		news(player, "Marine " + data.path().rank(rank).name() + " " + player.getName().getString() + " has deserted the Navy!");
		Bounty.raise(player, 5_000_000L * (rank + 1), "The Navy put a price on the deserter.", true);
	}

	/**
	 * Called at the start of Bounty.raise. Marines never get a bounty: deeds against pirates are counted as Merit
	 * elsewhere, and crimes against the Navy or the people count as strikes. Revolutionaries keep the bounty
	 * and also earn Liberation for blows against the Navy.
	 * @return true to stop the bounty from rising
	 */
	public static boolean interceptBounty(ServerPlayer player, long amount, String reason) {
		Career path = career(player);
		if (path == Career.REVOLUTIONARY) {
			if (reason.contains("Marine warship") || reason.contains("Buster Call") || reason.contains("royalty") || reason.contains("Navy")) {
				addPoints(player, (int) Math.max(10, Math.min(500, amount / 1_000_000L)), "a blow against the World Government", true);
			}
			return false;
		}
		if (path != Career.MARINE) {
			return false;
		}
		if (reason.startsWith("The Marines heard you beat") || reason.startsWith("You beat") || reason.startsWith("Your crew")
				|| reason.contains("kings at the Reverie")) {
			return true; // Bosses and Marines are handled by CareerFeature's death check; the rest just doesn't apply.
		}
		strike(player, "The Navy heard what you did. " + reason);
		return true;
	}

	// ---- Helpers ----

	static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
		}
	}

	private static void news(ServerPlayer player, String text) {
		player.level().getServer().getPlayerList().broadcastSystemMessage(
				Component.literal("[News Coo] " + text).withStyle(ChatFormatting.GOLD), false);
	}
}
