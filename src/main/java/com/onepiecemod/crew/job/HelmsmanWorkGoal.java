package com.onepiecemod.crew.job;

import com.onepiecemod.util.Motion;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.power.DevilFruitPowers;

/**
 * The helmsman's job (like Jinbe, a fish-man who rules the sea). Set them to work next to water:
 * 1. They fish. With at least 10 water blocks nearby they catch something about every 40 seconds
 *    (fish, sometimes a Nautilus Shell, rarely a Name Tag or Saddle) and put it in a nearby chest.
 * 2. They watch the water. If the captain or a crewmate is running out of air nearby, the helmsman
 *    pulls them up and gives them Water Breathing. Devil Fruit users (who can't swim) get pulled up right away.
 */
public class HelmsmanWorkGoal extends WorkGoal {
	private static final List<JobHelpers.Weighted> CATCHES = List.of(
			new JobHelpers.Weighted(Items.COD, 50),
			new JobHelpers.Weighted(Items.SALMON, 25),
			new JobHelpers.Weighted(Items.PUFFERFISH, 12),
			new JobHelpers.Weighted(Items.TROPICAL_FISH, 5),
			new JobHelpers.Weighted(Items.LILY_PAD, 3),
			new JobHelpers.Weighted(Items.NAUTILUS_SHELL, 3),
			new JobHelpers.Weighted(Items.NAME_TAG, 1),
			new JobHelpers.Weighted(Items.SADDLE, 1));

	private int seconds;
	private int waterBlocks = -1;
	private int rescueMessageCooldown;

	public HelmsmanWorkGoal(CrewmateEntity helmsman) {
		super(helmsman, CrewRole.HELMSMAN);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		seconds++;
		if (rescueMessageCooldown > 0) {
			rescueMessageCooldown--;
		}
		rescueSwimmers(level, post);

		if (waterBlocks < 0 || seconds % 30 == 0) {
			waterBlocks = JobHelpers.count(level, post, RANGE,
					state -> state.getFluidState().is(FluidTags.WATER) && state.getFluidState().isSource());
		}
		if (waterBlocks >= 10 && level.getRandom().nextInt(40) == 0) {
			JobHelpers.putInBag(worker, worker.getInventory(), new ItemStack(JobHelpers.weightedPick(level.getRandom(), CATCHES)));
			level.playSound(null, worker.blockPosition(), SoundEvents.FISHING_BOBBER_SPLASH, SoundSource.NEUTRAL, 0.6f, 1.0f);
		}
	}

	private void rescueSwimmers(ServerLevel level, BlockPos post) {
		for (LivingEntity swimmer : level.getEntitiesOfClass(LivingEntity.class, new AABB(post).inflate(RANGE),
				entity -> entity.isUnderWater() && CrewmateEntity.sameCrew(worker, entity) && needsRescue(entity))) {
			Vec3 motion = swimmer.getDeltaMovement();
			swimmer.setDeltaMovement(motion.x, 0.6, motion.z); // Pull them up toward the surface.
			Motion.sync(swimmer);
			swimmer.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 200, 0, false, false, true));
			if (rescueMessageCooldown == 0) {
				worker.tellCaptain("Hold on! I've got " + swimmer.getName().getString() + "!");
				rescueMessageCooldown = 30;
			}
		}
	}

	// Devil Fruit users always need help in water. Everyone else only once they're running out of air.
	private static boolean needsRescue(LivingEntity swimmer) {
		if (swimmer instanceof Player player && DevilFruitPowers.hasAnyFruit(player)) {
			return true;
		}
		return swimmer.getAirSupply() < swimmer.getMaxAirSupply() / 2;
	}

	// Stay at the post by the water.
	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return awayFromPost(post) ? post : null;
	}

	// Casting a line.
	@Override
	protected Anim workAnim() {
		return Anim.THROW;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		// Back at the post.
	}

	// The whole catch goes in the chest.
	@Override
	protected boolean shouldStore(ItemStack stack) {
		return true;
	}
}
