package com.onepiecemod.pet;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Mob;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * /pets: every pet of yours nearby, with its health, bond level and ability.
 * /pets abilities: what every creature's ability does.
 */
public final class PetsCommand {
	private PetsCommand() {
	}

	static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("pets")
						.executes(context -> list(context.getSource().getPlayerOrException()))
						.then(Commands.literal("abilities").executes(context -> abilities(context.getSource().getPlayerOrException())))
						// Operators, for testing: max out the bond of every pet nearby.
						.then(Commands.literal("maxbond").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									for (Mob mob : Pets.petsOf(context.getSource().getPlayerOrException(), 32)) {
										PetBond.add(mob, PetBond.pointsFor(PetBond.MAX_LEVEL));
									}
									return 1;
								}))));
	}

	private static int list(ServerPlayer player) {
		List<Mob> pets = Pets.petsOf(player, 256);
		if (pets.isEmpty()) {
			Pets.tell(player, Component.literal("No pets nearby. Tame a creature first (feed it its favourite food)."), ChatFormatting.GRAY);
			return 0;
		}
		Pets.tell(player, Component.literal("Your pets (" + pets.size() + "):"), ChatFormatting.GOLD);
		for (Mob mob : pets) {
			Pet pet = (Pet) mob;
			PetAbilities.Ability ability = PetAbilities.of(mob);
			String line = " " + Math.round(mob.getHealth()) + "/" + Math.round(mob.getMaxHealth()) + " HP, " + PetBond.describe(pet)
					+ (pet.isStaying() ? ", waiting" : "") + (pet.getTowShip() != null ? ", pulling your ship" : "");
			player.sendSystemMessage(Component.literal("- ").append(mob.getName()).append(line).withStyle(ChatFormatting.GREEN));
			if (ability != null) {
				player.sendSystemMessage(Component.literal("   " + PetAbilities.name(mob) + ": " + ability.description())
						.withStyle(ChatFormatting.GRAY));
			}
		}
		return pets.size();
	}

	private static int abilities(ServerPlayer player) {
		Pets.tell(player, Component.literal("Pet abilities (stronger at bond level " + PetBond.EMPOWERED_LEVEL + "):"), ChatFormatting.GOLD);
		for (String kind : PetAbilities.kinds()) {
			PetAbilities.Ability ability = PetAbilities.byKind(kind);
			player.sendSystemMessage(Component.literal("- " + ability.name() + " (" + kind.replace('_', ' ') + "): " + ability.description())
					.withStyle(ChatFormatting.GRAY));
		}
		return 1;
	}
}
