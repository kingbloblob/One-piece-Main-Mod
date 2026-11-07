package com.onepiecemod.fruitdex;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.sound.ModSounds;

/**
 * The first-bite ceremony: what happens in the world when someone eats their first Devil Fruit.
 * The player's own game shows the cutscene (FirstBiteScreen); this class does the part everyone nearby
 * can see and hear: heartbeats, a burst of colored energy, and a short freeze so nothing can hit you mid-scene.
 *
 * Timeline in ticks (20 ticks = 1 second), matched to the cutscene:
 *   0  bite         20-55  heartbeats      55-85  energy spiral      70  power surge      140  done
 */
public class FirstBite {
	public static final int LENGTH = 140;

	private record Ceremony(DevilFruit fruit, int[] age) {
	}

	private static final Map<UUID, Ceremony> ACTIVE = new HashMap<>();

	static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(FirstBite::tick);
	}

	/** Called by DevilFruitItem right after a player eats their first fruit. */
	public static void start(ServerPlayer player, DevilFruit fruit) {
		FruitdexFeature.discover(player, fruit);
		ModSounds.play(player, ModSounds.FRUIT_EAT);

		// Hold still and stay safe while the scene plays.
		player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, LENGTH, 6, false, false));
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, LENGTH + 20, 4, false, false));
		player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 90, 0, false, false));

		if (ServerPlayNetworking.canSend(player, FruitdexPayloads.FirstBite.TYPE)) {
			ServerPlayNetworking.send(player, new FruitdexPayloads.FirstBite(fruit.id()));
		} else {
			// No cutscene without the mod on the client, so use the vanilla title text instead.
			player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("The sea will never embrace you again").withStyle(ChatFormatting.AQUA)));
			player.connection.send(new ClientboundSetTitleTextPacket(Component.literal(fruit.name()).withStyle(ChatFormatting.GOLD)));
		}
		ACTIVE.put(player.getUUID(), new Ceremony(fruit, new int[] {0}));
	}

	private static void tick(MinecraftServer server) {
		Iterator<Map.Entry<UUID, Ceremony>> it = ACTIVE.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<UUID, Ceremony> entry = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
			Ceremony ceremony = entry.getValue();
			int age = ++ceremony.age()[0];
			if (player == null || !player.isAlive() || age > LENGTH) {
				it.remove();
				continue;
			}
			play(player, ceremony.fruit(), age);
		}
	}

	private static void play(ServerPlayer player, DevilFruit fruit, int age) {
		ServerLevel level = (ServerLevel) player.level();
		double x = player.getX(), y = player.getY(), z = player.getZ();

		// Heartbeats, getting faster.
		if (age == 20 || age == 34 || age == 45 || age == 53) {
			sound(player, SoundEvents.WARDEN_HEARTBEAT, 1.5f, 0.8f);
		}

		// The fruit's colors swirl up around the player.
		if (age >= 55 && age <= 85) {
			DustParticleOptions main = new DustParticleOptions(fruit.color(), 1.5f);
			DustParticleOptions accent = new DustParticleOptions(fruit.accent(), 1.2f);
			for (int i = 0; i < 3; i++) {
				double angle = age * 0.45 + i * (Math.PI * 2 / 3);
				double height = (age - 55) / 30.0 * 2.2;
				double radius = 1.3 - height * 0.3;
				level.sendParticles(i == 0 ? accent : main, x + Math.cos(angle) * radius, y + height, z + Math.sin(angle) * radius, 2, 0.05, 0.05, 0.05, 0);
			}
		}
		if (age == 55) {
			sound(player, SoundEvents.ILLUSIONER_PREPARE_MIRROR, 1.0f, 0.7f);
		}

		// The power takes hold.
		if (age == 70) {
			ModSounds.play(player, ModSounds.FRUIT_AWAKEN);
			DustParticleOptions burst = new DustParticleOptions(fruit.color(), 2.0f);
			for (int i = 0; i < 40; i++) {
				double angle = i * (Math.PI * 2 / 40);
				level.sendParticles(burst, x + Math.cos(angle) * 2, y + 1, z + Math.sin(angle) * 2, 1, 0, 0.2, 0, 0);
			}
			level.sendParticles(ParticleTypes.END_ROD, x, y + 1, z, 30, 0.6, 1.0, 0.6, 0.8);
		}
	}

	private static void sound(ServerPlayer player, SoundEvent sound, float volume, float pitch) {
		player.level().playSound(null, player.blockPosition(), sound, SoundSource.PLAYERS, volume, pitch);
	}
}
