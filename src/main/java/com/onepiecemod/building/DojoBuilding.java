package com.onepiecemod.building;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.level.block.Blocks;

import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.haki.HakiPowers;

/**
 * Haki Dojo: a Wano-style training hall with a Training Post in the middle.
 *
 * Right-click the Training Post to spar with it: a little Armament Haki training each hit,
 * but it makes you hungry and you have to catch your breath between hits.
 * Sneak and stand still inside the dojo to meditate: a little Observation Haki every 10 seconds.
 */
public class DojoBuilding extends Multiblock {
	private static final int SPAR_COOLDOWN_TICKS = 40;
	private static final int MEDITATE_SECONDS = 10;

	private final Map<UUID, Long> lastSpar = new HashMap<>();
	private final Map<UUID, Integer> meditating = new HashMap<>();

	public DojoBuilding() {
		super("training_post", "Haki Dojo");
		fill("Tatami for the middle 3x3 of the floor", Parts.TATAMI, Parts.block("onepiece:tatami", Blocks.BIRCH_PLANKS), square(-1, 1));
		fill("planks or Tatami for the edge of the 5x5 floor", state -> Parts.PLANKS.test(state) || Parts.TATAMI.test(state),
				Parts.block("onepiece:sakura_planks", Blocks.CHERRY_PLANKS), ring(-1, 2));
		fill("logs for the corner posts (3 tall)", Parts.POST, Parts.block("onepiece:sakura_log", Blocks.CHERRY_LOG), corners(0, 2, 2));
		fill("planks, wooden slabs, stairs or roof tiles for the 5x5 roof", Parts.ROOF, Parts.block("onepiece:wano_roof_tiles", Blocks.DARK_OAK_PLANKS), square(3, 2));
		contains("Shoji Screens in the walls", Parts.SHOJI, new BlockPos(-2, 0, -2), new BlockPos(2, 2, 2), 4);
		contains("Lanterns or Paper Lanterns", Parts.LANTERN, new BlockPos(-2, 0, -2), new BlockPos(2, 2, 2), 2);

		planLine("Floor: a 5x5 square. The middle 3x3 is Tatami mats, the edge is planks (or more Tatami).");
		planLine("Posts: a log in each corner of the floor, stacked 3 high.");
		planLine("Roof: a 5x5 layer of planks, wooden slabs, stairs or Wano Roof Tiles on top of the posts.");
		planLine("Walls: at least 4 Shoji Screens. Inside: 2 Lanterns or Paper Lanterns.");
		planLine("The Training Post goes on the floor in the very middle.");
	}

	@Override
	public String purpose() {
		return "Right-click the Training Post to train Armament Haki, or sneak inside to meditate for Observation Haki.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry entry) {
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		Long last = lastSpar.get(player.getUUID());
		if (last != null && now - last < SPAR_COOLDOWN_TICKS) {
			return; // Still catching their breath.
		}
		lastSpar.put(player.getUUID(), now);
		if (player.getFoodData().getFoodLevel() <= 6) {
			player.sendSystemMessage(Component.literal("You're too hungry to train. Eat something first!").withStyle(ChatFormatting.RED));
			return;
		}
		HakiData before = HakiAttachments.get(player);
		if (before.armamentLevel() >= HakiData.MAX_LEVEL) {
			player.sendSystemMessage(Component.literal("You've mastered Armament Haki. The post can't teach you any more.").withStyle(ChatFormatting.GRAY));
			return;
		}
		HakiPowers.addArmamentXp(player, 1);
		player.causeFoodExhaustion(2.0f);
		BlockPos pos = entry.pos();
		level.playSound(null, pos, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.PLAYERS, 1.0f, 0.9f);
		level.sendParticles(ParticleTypes.CRIT, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 8, 0.3, 0.3, 0.3, 0.1);
		int xp = HakiAttachments.get(player).armamentXp();
		if (xp % 10 == 0) {
			int toNext = HakiData.xpToNext(xp);
			player.sendSystemMessage(Component.literal("Armament training: " + toNext + " more training points to the next level.")
					.withStyle(ChatFormatting.GRAY));
		}
	}

	@Override
	public void tick(ServerLevel level, BuildingRegistry.Entry entry) {
		BlockPos pos = entry.pos();
		AABB room = new AABB(Vec3.atLowerCornerOf(pos.offset(-2, 0, -2)), Vec3.atLowerCornerOf(pos.offset(3, 3, 3)));
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, room)) {
			boolean still = player.getDeltaMovement().horizontalDistanceSqr() < 0.001;
			if (!player.isCrouching() || !still) {
				meditating.remove(player.getUUID());
				continue;
			}
			int seconds = meditating.merge(player.getUUID(), 1, Integer::sum);
			level.sendParticles(ParticleTypes.ENCHANT, player.getX(), player.getY() + 1.2, player.getZ(), 4, 0.4, 0.4, 0.4, 0.5);
			if (seconds % MEDITATE_SECONDS == 0) {
				if (HakiAttachments.get(player).observationLevel() >= HakiData.MAX_LEVEL) {
					continue;
				}
				HakiPowers.addObservationXp(player, 1);
				if (seconds == MEDITATE_SECONDS) {
					player.sendSystemMessage(Component.literal("You clear your mind and feel the voices of all things... (keep sneaking to keep meditating)")
							.withStyle(ChatFormatting.AQUA));
				}
			}
		}
	}
}
