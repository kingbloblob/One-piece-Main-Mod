package com.onepiecemod.crew;

import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterFeature;

/**
 * The rules for hiring, and the code that makes a new crewmate appear.
 *
 * Hiring gets harder as your crew grows:
 * - Each hire costs more Berries than the one before (see HIRE_COSTS).
 * - Each role wants its own trial item, like three iron swords for the swordsman.
 * - Late roles only join a crew that already has enough members.
 * - In Survival, you can only hire while standing at a finished Pirate Tavern (see CrewTavern).
 * Each role has 3 candidates to choose from (see CrewCandidates), with their own price.
 */
public class CrewHiring {
	/** Berries for your 1st, 2nd, 3rd... hire. Bosses drop about 12 to 64 Berries each. */
	private static final int[] HIRE_COSTS = {10, 20, 35, 50, 75, 100, 150, 200, 300};

	/** What hire number `hires + 1` costs. After the 9th hire the price keeps rising. */
	public static int cost(int hires) {
		if (hires < HIRE_COSTS.length) {
			return HIRE_COSTS[hires];
		}
		return HIRE_COSTS[HIRE_COSTS.length - 1] + 100 * (hires - HIRE_COSTS.length + 1);
	}

	public static Item currency() {
		return CharacterFeature.BERRY;
	}

	/**
	 * Checks everything except money, before showing or hiring candidates.
	 * Returns the crew, or null after telling the player what's wrong.
	 */
	public static Crew checkCanHire(ServerPlayer captain, CrewRole role) {
		String problem = hireProblem(captain, role);
		if (problem != null) {
			fail(captain, problem);
			return null;
		}
		return captain.getAttached(CrewAttachments.CREW);
	}

	/** Why this captain can't hire for this role right now (not counting money), or null if they can. */
	public static String hireProblem(ServerPlayer captain, CrewRole role) {
		Crew crew = captain.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			return "You need a crew first. Use /crew create <name>.";
		}
		if (crew.member(role) != null) {
			return "You already have a " + role.title() + ". Dismiss them first to make room.";
		}
		if (crew.size() < role.minCrew()) {
			return "A " + role.title() + " only joins a crew with at least " + role.minCrew()
					+ " crewmates. You have " + crew.size() + ".";
		}
		if (!captain.getAbilities().instabuild && !CrewTavern.playerIsAtTavern(captain)) {
			return "Recruits only meet captains at a Pirate Tavern. Build one (a Tavern Blueprint shows how) and stand inside it.";
		}
		return null;
	}

	/** Tries to hire candidate number `choice` (0-2) for a role. Explains what's missing in chat if they can't. */
	public static boolean hire(ServerPlayer captain, CrewRole role, int choice, Integer listCode) {
		String problem = tryHire(captain, role, choice, listCode);
		if (problem != null) {
			fail(captain, problem);
		}
		return problem == null;
	}

	/**
	 * Hires candidate number `choice` (0-2) for a role. Returns why it failed, or null if they joined.
	 * listCode is the code of the candidate list the player was looking at (null = don't check):
	 * if a new day started since then, those recruits have gone and nobody is hired by mistake.
	 */
	public static String tryHire(ServerPlayer captain, CrewRole role, int choice, Integer listCode) {
		String problem = hireProblem(captain, role);
		if (problem != null) {
			return problem;
		}
		Crew crew = captain.getAttached(CrewAttachments.CREW);
		if (listCode != null && listCode != CrewCandidates.listCode(captain, crew)) {
			return "Those recruits have moved on. A new group is waiting: open the " + role.title() + " recruits again.";
		}
		CrewCandidates.Candidate candidate = CrewCandidates.forRole(captain, crew, role).get(Math.floorMod(choice, CrewVariant.COUNT));

		int price = candidate.price();
		boolean free = captain.getAbilities().instabuild; // Creative mode hires for free, handy for testing.
		if (!free) {
			int berries = count(captain.getInventory(), currency());
			int trialItems = count(captain.getInventory(), role.trialItem());
			if (berries < price || trialItems < role.trialCount()) {
				return "To hire " + candidate.fullName() + " you need " + price + " Berries (you have " + berries + ") and "
						+ role.trialCount() + " " + itemName(role.trialItem()) + " (you have " + trialItems + ").";
			}
			take(captain.getInventory(), currency(), price);
			take(captain.getInventory(), role.trialItem(), role.trialCount());
		}

		ServerLevel level = (ServerLevel) captain.level();
		CrewmateEntity crewmate = CrewEntities.CREWMATE.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (crewmate == null) {
			return "Something went wrong. The recruit didn't show up.";
		}
		crewmate.setPos(captain.getX(), captain.getY(), captain.getZ());
		crewmate.setCaptain(captain);
		crewmate.setProfile(role, candidate.variantIndex(), candidate.personality());
		crewmate.setHealth(crewmate.getMaxHealth());
		crewmate.setCustomName(Component.literal(candidate.fullName()));
		crewmate.setCustomNameVisible(true);
		crewmate.setPersistenceRequired();
		level.addFreshEntity(crewmate);

		captain.setAttached(CrewAttachments.CREW, crew.withMember(role, crewmate.getUUID()));
		captain.sendSystemMessage(Component.literal(candidate.fullName() + " the " + candidate.personality().title() + " "
				+ candidate.variant().title() + " joined the " + crew.name() + "! ")
				.withStyle(ChatFormatting.GOLD)
				.append(Component.literal("Perk: " + role.perk() + ".").withStyle(ChatFormatting.YELLOW)));
		crewmate.chatter();
		return null;
	}

	/** How many Berries the player carries. */
	public static int berries(ServerPlayer player) {
		return count(player.getInventory(), currency());
	}

	/** Removes a crewmate from the crew and sends them away (their bag drops on the ground). */
	public static void dismiss(MinecraftServer server, UUID crewmateId) {
		// A crewmate in a part of the world that isn't loaded leaves by itself the next time it loads
		// (see CrewmateEntity.tick), because it's no longer on the crew list.
		CrewmateEntity crewmate = CrewRoster.find(server, crewmateId);
		if (crewmate != null) {
			crewmate.dropInventory();
			crewmate.discard();
		}
	}

	public static String itemName(Item item) {
		return new ItemStack(item).getHoverName().getString();
	}

	private static void fail(ServerPlayer player, String message) {
		player.sendSystemMessage(Component.literal(message).withStyle(ChatFormatting.RED));
	}

	private static int count(Inventory inventory, Item item) {
		int total = 0;
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(item)) {
				total += stack.getCount();
			}
		}
		return total;
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
