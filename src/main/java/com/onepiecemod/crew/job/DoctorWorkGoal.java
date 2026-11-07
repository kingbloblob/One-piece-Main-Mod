package com.onepiecemod.crew.job;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The doctor's job (like Chopper). The doctor turns their post into an infirmary:
 * 1. Every 2 seconds, heals anyone hurt nearby (players, crewmates, pets, villagers; never monsters)
 *    and cures Poison, Wither and Hunger.
 * 2. Makes medicine: golden carrots and glistering melon slices, using gold from a nearby chest.
 */
public class DoctorWorkGoal extends WorkGoal {
	private static final List<JobHelpers.Recipe> RECIPES = List.of(
			new JobHelpers.Recipe(Items.GOLD_NUGGET, 9, List.of(new ItemStack(Items.GOLD_INGOT))),
			new JobHelpers.Recipe(Items.GOLDEN_CARROT, 1, List.of(new ItemStack(Items.GOLD_NUGGET, 8), new ItemStack(Items.CARROT))),
			new JobHelpers.Recipe(Items.GLISTERING_MELON_SLICE, 1, List.of(new ItemStack(Items.GOLD_NUGGET, 8), new ItemStack(Items.MELON_SLICE))));

	private boolean healThisTick;

	public DoctorWorkGoal(CrewmateEntity doctor) {
		super(doctor, CrewRole.DOCTOR);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		JobHelpers.craft(worker, worker.getInventory(), RECIPES);

		healThisTick = !healThisTick; // Heal every other second.
		if (!healThisTick) {
			return;
		}
		for (LivingEntity patient : level.getEntitiesOfClass(LivingEntity.class, new AABB(post).inflate(RANGE),
				entity -> entity.isAlive() && !(entity instanceof Enemy))) {
			boolean treated = false;
			if (patient.getHealth() < patient.getMaxHealth()) {
				patient.heal(1.0f);
				treated = true;
			}
			treated |= patient.removeEffect(MobEffects.POISON);
			treated |= patient.removeEffect(MobEffects.WITHER);
			treated |= patient.removeEffect(MobEffects.HUNGER);
			if (treated) {
				level.sendParticles(ParticleTypes.HEART, patient.getX(), patient.getY() + patient.getBbHeight() + 0.3, patient.getZ(),
						1, 0.2, 0.2, 0.2, 0.0);
			}
		}
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> JobHelpers.isChest(be)
						&& JobHelpers.chestHasMissingIngredient((Container) be, worker.getInventory(), RECIPES));
	}

	// Treating a patient.
	@Override
	protected Anim workAnim() {
		return Anim.CAST;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		BlockEntity blockEntity = level.getBlockEntity(pos);
		if (JobHelpers.isChest(blockEntity)) {
			JobHelpers.takeMissingIngredients((Container) blockEntity, worker.getInventory(), RECIPES);
			blockEntity.setChanged();
		}
	}

	@Override
	protected boolean shouldStore(ItemStack stack) {
		return stack.is(Items.GOLDEN_CARROT) || stack.is(Items.GLISTERING_MELON_SLICE);
	}
}
