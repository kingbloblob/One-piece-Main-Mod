package com.onepiecemod.baseworks;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.building.Parts;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.hideout.HideoutLevels;
import com.onepiecemod.hideout.Hideouts;

/**
 * Hideout upgrades you pay builders for. Your bounty is your reputation: shipwrights, smugglers and gunners
 * only work for a pirate famous enough (each tier needs a bounty), and they want Berries up front (from your
 * bag, or from your own town's treasury). Each tier also needs the hideout to have reached that level.
 *
 * The hideout package asks this class for its numbers (defence, haul, warning time, cannon reload, rest).
 * Saved on the Overworld: captain uuid -> upgrade id -> tier.
 */
public final class BaseUpgrades {
	public enum Upgrade {
		PALISADE("palisade", "Palisade Walls", "Defence +8 / +16 / +28 against Navy attacks while you're away.",
				new long[] {0, 30_000_000L, 150_000_000L}, new int[] {40, 120, 300}),
		GUN_CREWS("gun_crews", "Gun Crews", "Hideout cannons reload in 3.2 / 2.6 / 2 seconds (instead of 4), +1 defence per cannon each tier.",
				new long[] {10_000_000L, 80_000_000L, 400_000_000L}, new int[] {60, 160, 400}),
		STOREHOUSE("storehouse", "Storehouse", "The crew's daily haul +15% / +30% / +50%.",
				new long[] {0, 50_000_000L, 200_000_000L}, new int[] {50, 150, 350}),
		LOOKOUT("lookout", "Lookout Post", "Navy attacks are spotted 30 / 60 seconds earlier. Defence +4 / +8.",
				new long[] {20_000_000L, 100_000_000L}, new int[] {60, 180}),
		SICK_BAY("sick_bay", "Sick Bay", "Resting in the claim heals faster (Regeneration II). Tier 2: crewmates living here heal too.",
				new long[] {30_000_000L, 120_000_000L}, new int[] {80, 200}),
		SMUGGLERS_COVE("smugglers_cove", "Smuggler's Cove", "Fences pay to use your cove: Berries into the stash every day, more the bigger your bounty.",
				new long[] {50_000_000L, 300_000_000L}, new int[] {150, 400});

		public final String id;
		public final String title;
		public final String effect;
		/** Bounty needed for tier 1, 2, 3. */
		final long[] bounty;
		/** Berries for tier 1, 2, 3. */
		final int[] cost;

		Upgrade(String id, String title, String effect, long[] bounty, int[] cost) {
			this.id = id;
			this.title = title;
			this.effect = effect;
			this.bounty = bounty;
			this.cost = cost;
		}

		public int maxTier() {
			return cost.length;
		}

		static Upgrade byId(String id) {
			for (Upgrade upgrade : values()) {
				if (upgrade.id.equals(id)) {
					return upgrade;
				}
			}
			return null;
		}
	}

	public static final AttachmentType<Map<String, Map<String, Integer>>> UPGRADES = AttachmentRegistry.create(
			OnePieceMod.id("base_upgrades"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.unboundedMap(Codec.STRING, Codec.INT))));

	private BaseUpgrades() {
	}

	// ---------- Saved tiers ----------

	public static int tier(MinecraftServer server, UUID captain, Upgrade upgrade) {
		if (server == null || captain == null) {
			return 0;
		}
		Map<String, Integer> mine = server.overworld().getAttachedOrElse(UPGRADES, Map.of()).get(captain.toString());
		return mine == null ? 0 : mine.getOrDefault(upgrade.id, 0);
	}

	static void setTier(MinecraftServer server, UUID captain, Upgrade upgrade, int tier) {
		Map<String, Map<String, Integer>> all = new HashMap<>(server.overworld().getAttachedOrElse(UPGRADES, Map.of()));
		Map<String, Integer> mine = new HashMap<>(all.getOrDefault(captain.toString(), Map.of()));
		mine.put(upgrade.id, tier);
		all.put(captain.toString(), mine);
		server.overworld().setAttached(UPGRADES, all);
	}

	// ---------- What the hideout asks for ----------

	/** Extra defence rating from the Palisade, the Gun Crews and the Lookout. */
	public static int defenceBonus(MinecraftServer server, UUID captain, int cannons) {
		int palisade = tier(server, captain, Upgrade.PALISADE);
		int bonus = palisade == 1 ? 8 : palisade == 2 ? 16 : palisade >= 3 ? 28 : 0;
		bonus += Math.min(cannons, 12) * tier(server, captain, Upgrade.GUN_CREWS);
		bonus += 4 * tier(server, captain, Upgrade.LOOKOUT);
		return bonus;
	}

	/** Ticks between two shots of one hideout cannon. */
	public static int cannonReload(MinecraftServer server, UUID captain, int normal) {
		int tier = tier(server, captain, Upgrade.GUN_CREWS);
		return switch (tier) {
			case 1 -> normal * 4 / 5;
			case 2 -> normal * 13 / 20;
			case 3 -> normal / 2;
			default -> normal;
		};
	}

	/** How much earlier a Navy attack is announced. */
	public static int extraWarningTicks(MinecraftServer server, UUID captain) {
		return 20 * 30 * tier(server, captain, Upgrade.LOOKOUT);
	}

	/** Regeneration level for resting in the claim (0 = Regeneration I). */
	public static int restAmplifier(MinecraftServer server, UUID captain) {
		return tier(server, captain, Upgrade.SICK_BAY) >= 1 ? 1 : 0;
	}

	public static boolean crewHealing(MinecraftServer server, UUID captain) {
		return tier(server, captain, Upgrade.SICK_BAY) >= 2;
	}

	/** The Storehouse makes each stack of the day's haul bigger. */
	public static void boostHaul(MinecraftServer server, UUID captain, List<ItemStack> items, RandomSource random) {
		int tier = tier(server, captain, Upgrade.STOREHOUSE);
		if (tier <= 0) {
			return;
		}
		double boost = tier == 1 ? 0.15 : tier == 2 ? 0.30 : 0.50;
		for (ItemStack stack : items) {
			double extra = stack.getCount() * boost;
			int add = (int) extra + (random.nextDouble() < extra - (int) extra ? 1 : 0);
			stack.setCount(Math.min(stack.getMaxStackSize(), stack.getCount() + add));
		}
	}

	/** Once a day with the haul: what the Smuggler's Cove pays, by the captain's bounty. */
	public static List<ItemStack> dailyExtras(MinecraftServer server, UUID captain, int days) {
		List<ItemStack> list = new ArrayList<>();
		int tier = tier(server, captain, Upgrade.SMUGGLERS_COVE);
		if (tier <= 0) {
			return list;
		}
		long bounty = knownBounty(server, captain);
		int perDay = (int) Math.min(tier == 1 ? 30 : 80, Math.max(3, bounty / 10_000_000L) * tier);
		int total = perDay * Math.max(1, days);
		while (total > 0) {
			int stack = Math.min(64, total);
			list.add(new ItemStack(CharacterFeature.BERRY, stack));
			total -= stack;
		}
		ServerPlayer player = server.getPlayerList().getPlayer(captain);
		if (player != null) {
			player.sendSystemMessage(Component.literal("[Hideout] The smugglers paid " + perDay * Math.max(1, days)
					+ " Berries to use your cove.").withStyle(ChatFormatting.GOLD));
		}
		return list;
	}

	private static long knownBounty(MinecraftServer server, UUID captain) {
		ServerPlayer player = server.getPlayerList().getPlayer(captain);
		return player != null ? Bounty.get(player) : 0L;
	}

	// ---------- Buying ----------

	/** Why this tier can't be built yet, or null if it can. */
	static String blocker(ServerPlayer player, Upgrade upgrade, int nextTier) {
		if (nextTier > upgrade.maxTier()) {
			return "fully built";
		}
		long needBounty = upgrade.bounty[nextTier - 1];
		if (Bounty.get(player) < needBounty) {
			return "needs a " + money(needBounty) + " bounty";
		}
		Hideouts.Hideout hideout = Hideouts.of(player.level().getServer(), player.getUUID());
		if (hideout == null) {
			return "needs a hideout";
		}
		if (hideout.level() < nextTier) {
			return "needs a " + HideoutLevels.NAMES[Math.min(HideoutLevels.MAX, nextTier)] + " (hideout level " + nextTier + ")";
		}
		return null;
	}

	/** /base build <id>. Returns a message for failures, or null on success. */
	static String build(ServerPlayer player, String id) {
		Upgrade upgrade = Upgrade.byId(id);
		if (upgrade == null) {
			return "There's no upgrade called " + id + ".";
		}
		MinecraftServer server = player.level().getServer();
		Hideouts.Hideout hideout = Hideouts.of(server, player.getUUID());
		if (hideout == null) {
			return "You need a hideout first. Plant a Hideout Flag on an island (only the captain can hire builders).";
		}
		if (!hideout.contains(player.position()) || player.level() != server.overworld()) {
			return "The builders want to see the place. Stand inside your hideout's claim.";
		}
		int next = tier(server, player.getUUID(), upgrade) + 1;
		String blocker = blocker(player, upgrade, next);
		if (blocker != null) {
			return upgrade.title + " " + roman(next) + ": " + blocker + ".";
		}
		int cost = upgrade.cost[next - 1];
		if (!pay(player, cost)) {
			return upgrade.title + " " + roman(next) + " costs " + cost + " Berries. You have " + Parts.count(player, CharacterFeature.BERRY)
					+ " (plus " + com.onepiecemod.settlement.Settlements.treasury(player) + " in your town's treasury).";
		}
		setTier(server, player.getUUID(), upgrade, next);
		ServerLevel level = (ServerLevel) player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.PLAYERS, 0.8f, 1.0f);
		player.sendSystemMessage(Component.literal("Builders hired! " + upgrade.title + " " + roman(next) + " is done. " + upgrade.effect)
				.withStyle(ChatFormatting.GREEN));
		return null;
	}

	/** Takes Berries from the bag, then from the town treasury. */
	static boolean pay(ServerPlayer player, int cost) {
		int carried = Parts.count(player, CharacterFeature.BERRY);
		long treasury = com.onepiecemod.settlement.Settlements.treasury(player);
		if (carried + treasury < cost) {
			return false;
		}
		int fromBag = Math.min(carried, cost);
		Parts.take(player, CharacterFeature.BERRY, fromBag);
		if (cost > fromBag) {
			com.onepiecemod.settlement.Settlements.spendTreasury(player, cost - fromBag);
		}
		return true;
	}

	// ---------- The menu ----------

	/** The Builder's Ledger page: every upgrade with its tier, price and a [Build] button. */
	public static void menu(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		player.sendSystemMessage(Component.literal("=== Builder's Ledger ===").withStyle(ChatFormatting.GOLD));
		Hideouts.Hideout hideout = Hideouts.of(server, player.getUUID());
		long bounty = Bounty.get(player);
		player.sendSystemMessage(Component.literal("Your bounty: " + money(bounty) + ". Berries: " + Parts.count(player, CharacterFeature.BERRY)
				+ ". Town treasury: " + com.onepiecemod.settlement.Settlements.treasury(player) + ".").withStyle(ChatFormatting.YELLOW));
		if (hideout == null) {
			player.sendSystemMessage(Component.literal("No hideout yet. Plant a Hideout Flag, then come back to hire builders.")
					.withStyle(ChatFormatting.GRAY));
		} else {
			player.sendSystemMessage(Component.literal("Hideout: " + HideoutLevels.NAMES[hideout.level()] + " (level " + hideout.level()
					+ "), defence " + hideout.defence() + ".").withStyle(ChatFormatting.AQUA));
		}
		for (Upgrade upgrade : Upgrade.values()) {
			int tier = tier(server, player.getUUID(), upgrade);
			MutableComponent line = Component.literal(upgrade.title + " " + (tier == 0 ? "-" : roman(tier)) + "/" + roman(upgrade.maxTier()) + "  ")
					.withStyle(ChatFormatting.WHITE);
			if (tier >= upgrade.maxTier()) {
				line.append(Component.literal("done").withStyle(ChatFormatting.GREEN));
			} else {
				int next = tier + 1;
				String blocker = blocker(player, upgrade, next);
				String price = upgrade.cost[next - 1] + " Berries";
				if (blocker == null) {
					line.append(Component.literal("[Build " + roman(next) + ": " + price + "]").withStyle(ChatFormatting.GREEN)
							.withStyle(style -> style.withClickEvent(new ClickEvent.RunCommand("/base build " + upgrade.id))
									.withHoverEvent(new HoverEvent.ShowText(Component.literal(upgrade.effect)))));
				} else {
					line.append(Component.literal(roman(next) + ": " + price + ", " + blocker).withStyle(ChatFormatting.DARK_GRAY)
							.withStyle(style -> style.withHoverEvent(new HoverEvent.ShowText(Component.literal(upgrade.effect)))));
				}
			}
			player.sendSystemMessage(line);
		}
		player.sendSystemMessage(Component.literal("Hover an upgrade to see what it does. Builders only work inside your claim.")
				.withStyle(ChatFormatting.GRAY));
		player.sendSystemMessage(Component.literal("Plans built: " + PlanOutlines.builtCount(player) + " of "
				+ (PlanBooks.DECK.size() + PlanBooks.BASE.size()) + ".").withStyle(ChatFormatting.GRAY));
		com.onepiecemod.settlement.Settlements.ledgerLines(player);
	}

	// ---------- Text ----------

	static String roman(int n) {
		return switch (n) {
			case 1 -> "I";
			case 2 -> "II";
			case 3 -> "III";
			case 4 -> "IV";
			default -> String.valueOf(n);
		};
	}

	public static String money(long berries) {
		if (berries >= 1_000_000_000L) {
			return String.format("%.1fB", berries / 1_000_000_000.0);
		}
		if (berries >= 1_000_000L) {
			return (berries / 1_000_000L) + "M";
		}
		return String.valueOf(berries);
	}

	/** Player-facing helper so other code can say "Bounty X". */
	static long bounty(Player player) {
		return Bounty.get(player);
	}
}
