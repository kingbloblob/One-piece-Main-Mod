package com.onepiecemod.building;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.level.block.Blocks;

import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.MarineHunters;
import com.onepiecemod.character.CharacterEntity;

/**
 * Marine Watchtower: a lookout tower with an Alarm Bell on top.
 * Every Marine, bounty hunter and monster within 48 blocks glows, so you can see them through walls.
 * When Marines come close, the bell rings and everyone nearby gets a warning saying where from.
 */
public class WatchtowerBuilding extends Multiblock {
	private static final double RANGE = 48.0;
	private static final double WARN_RANGE = 64.0;
	private static final long ALARM_COOLDOWN_TICKS = 600; // Ring at most every 30 seconds.

	private final Map<BlockPos, Long> lastAlarm = new HashMap<>();

	public WatchtowerBuilding() {
		super("alarm_bell", "Marine Watchtower");
		fill("planks, slabs or stone for the 5x5 lookout platform under the Bell",
				state -> Parts.WOOD_DECK.test(state) || Parts.STONE.test(state) || Parts.name(state).contains("slab"),
				Blocks.SPRUCE_PLANKS.defaultBlockState(), square(-1, 2));
		fill("logs, pillars, stone or fences for the 4 tower legs (4 tall, under the platform's corners)",
				state -> Parts.POST.test(state) || Parts.STONE.test(state) || Parts.RAIL.test(state),
				Parts.block("onepiece:marine_pillar", Blocks.SPRUCE_LOG), corners(-5, -2, 2));
		atLeastAt("fences, walls or bars for the railing around the platform (at least 12 of 16)", Parts.RAIL,
				Blocks.SPRUCE_FENCE.defaultBlockState(), ring(0, 2), 12);
		contains("Lantern on the platform", Parts.LANTERN, new BlockPos(-2, 0, -2), new BlockPos(2, 2, 2), 1);

		planLine("Legs: 4 posts of logs, pillars or stone, 4 blocks tall, in the corners of a 5x5 square.");
		planLine("Platform: a 5x5 floor of planks, slabs or stone on top of the legs.");
		planLine("The Alarm Bell goes in the middle of the platform.");
		planLine("Railing: fences, walls or iron bars around the edge of the platform (leave up to 4 gaps for a ladder).");
		planLine("Light: a Lantern somewhere on the platform.");
	}

	@Override
	public String purpose() {
		return "It makes Marines and monsters within 48 blocks glow, and rings when Marines come.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry entry) {
		ServerLevel level = (ServerLevel) player.level();
		List<LivingEntity> marines = threats(level, entry.pos(), true);
		List<LivingEntity> monsters = threats(level, entry.pos(), false);
		level.playSound(null, entry.pos(), SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 0.6f, 1.2f);
		if (marines.isEmpty() && monsters.isEmpty()) {
			player.sendSystemMessage(Component.literal("Lookout report: all quiet within " + (int) RANGE + " blocks.").withStyle(ChatFormatting.GREEN));
			return;
		}
		player.sendSystemMessage(Component.literal("Lookout report: " + marines.size() + " Marines and " + monsters.size()
				+ " monsters within " + (int) RANGE + " blocks. They're glowing.").withStyle(ChatFormatting.GOLD));
		if (!marines.isEmpty()) {
			player.sendSystemMessage(Component.literal("Nearest Marine: " + RelayBuilding.direction(entry.pos(), marines.get(0).blockPosition()))
					.withStyle(ChatFormatting.YELLOW));
		}
	}

	@Override
	public void tick(ServerLevel level, BuildingRegistry.Entry entry) {
		BlockPos pos = entry.pos();
		List<LivingEntity> marines = threats(level, pos, true);
		for (LivingEntity target : marines) {
			target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 40, 0, false, false));
		}
		for (LivingEntity target : threats(level, pos, false)) {
			target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 40, 0, false, false));
		}
		if (marines.isEmpty()) {
			return;
		}
		long now = level.getGameTime();
		Long last = lastAlarm.get(pos);
		if (last != null && now - last < ALARM_COOLDOWN_TICKS) {
			return;
		}
		lastAlarm.put(pos, now);
		level.playSound(null, pos, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 3.0f, 1.0f);
		Component warning = Component.literal("DING DING DING! Your Watchtower spotted " + marines.size()
				+ (marines.size() == 1 ? " Marine " : " Marines ") + RelayBuilding.direction(pos, marines.get(0).blockPosition()) + " of it!")
				.withStyle(ChatFormatting.RED);
		for (ServerPlayer player : level.players()) {
			if (player.blockPosition().distSqr(pos) <= WARN_RANGE * WARN_RANGE) {
				player.sendSystemMessage(warning);
			}
		}
	}

	/** Marines and bounty hunters (marines = true), or other monsters, nearest first. */
	private static List<LivingEntity> threats(ServerLevel level, BlockPos pos, boolean marines) {
		Vec3 center = Vec3.atCenterOf(pos);
		AABB area = AABB.ofSize(center, RANGE * 2, RANGE * 2, RANGE * 2);
		List<LivingEntity> found = level.getEntitiesOfClass(LivingEntity.class, area, entity -> {
			if (!entity.isAlive()) {
				return false;
			}
			boolean marine = entity instanceof MarineEntity
					|| (entity instanceof CharacterEntity && entity.entityTags().contains(MarineHunters.HUNTER_TAG));
			return marines ? marine : !marine && entity instanceof Enemy;
		});
		found.sort((a, b) -> Double.compare(a.distanceToSqr(center), b.distanceToSqr(center)));
		return found;
	}
}
