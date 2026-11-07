package com.onepiecemod.crew;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.core.Holder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Monster;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * Every 2 seconds, each captain gets a perk from every crewmate standing within 48 blocks.
 */
public class CrewPerks {
	private static final double PERK_RANGE = 48.0;
	private static final int EFFECT_TICKS = 100; // 5 seconds, refreshed every 2, so it never runs out while they're near.

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0) {
				return;
			}
			for (ServerPlayer captain : server.getPlayerList().getPlayers()) {
				Crew crew = captain.getAttached(CrewAttachments.CREW);
				if (crew != null) {
					givePerks(captain, crew);
				}
			}
		});
	}

	private static void givePerks(ServerPlayer captain, Crew crew) {
		ServerLevel level = (ServerLevel) captain.level();
		List<CrewmateEntity> nearby = new ArrayList<>();
		for (UUID id : crew.members().values()) {
			Entity entity = level.getEntity(id);
			if (entity instanceof CrewmateEntity crewmate && crewmate.isAlive() && !crewmate.isKnockedOut()
					&& crewmate.distanceToSqr(captain) < PERK_RANGE * PERK_RANGE) {
				nearby.add(crewmate);
			}
		}

		for (CrewmateEntity crewmate : nearby) {
			if (captain.getRandom().nextInt(150) == 0) {
				crewmate.chatter(); // Now and then (about every 5 minutes) they say something in character.
			}
			switch (crewmate.getRole()) {
				case SWORDSMAN -> effect(captain, MobEffects.STRENGTH);
				case NAVIGATOR -> effect(captain, MobEffects.SPEED);
				case SNIPER -> {
					// Usopp's sharp eyes: monsters nearby glow through walls.
					for (Monster monster : level.getEntitiesOfClass(Monster.class, captain.getBoundingBox().inflate(24.0))) {
						effect(monster, MobEffects.GLOWING);
					}
				}
				case COOK -> {
					if (captain.getFoodData().needsFood()) {
						captain.getFoodData().eat(1, 0.3f);
					}
				}
				case DOCTOR -> {
					if (captain.getHealth() < captain.getMaxHealth() / 2) {
						effect(captain, MobEffects.REGENERATION);
					}
					for (CrewmateEntity patient : nearby) {
						patient.heal(1.0f);
					}
				}
				case SHIPWRIGHT -> effect(captain, MobEffects.HASTE);
				case ARCHAEOLOGIST -> effect(captain, MobEffects.LUCK);
				case MUSICIAN -> {
					// Brook's music lifts everyone's spirits.
					effect(captain, MobEffects.RESISTANCE);
					for (CrewmateEntity listener : nearby) {
						effect(listener, MobEffects.RESISTANCE);
					}
				}
				case HELMSMAN -> {
					// Jinbe keeps you safe at sea, even if you ate a Devil Fruit and can't swim.
					effect(captain, MobEffects.WATER_BREATHING);
					effect(captain, MobEffects.DOLPHINS_GRACE);
				}
			}
		}
	}

	// Level I of an effect, with no swirly particles so the screen stays clear.
	private static void effect(LivingEntity target, Holder<MobEffect> effect) {
		target.addEffect(new MobEffectInstance(effect, EFFECT_TICKS, 0, true, false, true));
	}
}
