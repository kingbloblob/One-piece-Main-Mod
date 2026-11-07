package com.onepiecemod.pet;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.player.AttackEntityCallback;

import com.onepiecemod.util.Motion;

/**
 * Every tamed creature has one ability, named after something from One Piece. Some help its owner while the pet is
 * close by (within 12 blocks, or while riding it), some change how it fights, and some change what its rider can do.
 * At bond level 5 (PetBond.EMPOWERED_LEVEL) each ability gets stronger.
 *
 * The full list, in plain words, is in the pets guide and on the Pet Whistle / {@code /pets}.
 */
public final class PetAbilities {
	/** How close the owner must be to get a pet's help. */
	private static final double AURA_RANGE = 12.0;

	public record Ability(String name, String description) {
	}

	private static final Map<String, Ability> ALL = new java.util.LinkedHashMap<>();

	static {
		add("south_bird", "South Sense", "Monsters within 16 blocks of you glow, so nothing sneaks up on you.");
		add("spot_billed_duck", "Super Spot-Billed Dash", "Runs 25% faster with you on its back. You get Speed while it's near.");
		add("cotton_candy_lamb", "Sugar Rush", "When you're below half health, you slowly heal while it's near.");
		add("island_whale", "Whale Song", "In the water near it you heal and breathe.");
		add("wild_den_den_mushi", "Lucky Snail", "You get Luck while it's near (better fishing and treasure).");
		add("drum_reindeer", "Doctor's Helper", "Patches you up (4 hearts) when you drop below 40% health. Every 45 seconds.");
		add("sauropod", "Gentle Giant", "Resistance while you ride it.");
		add("fuzza", "Sky Feathers", "Flies! You fall slowly while it's near.");
		add("hiking_bear", "Mountain Manners", "Jump Boost while it's near.");
		add("long_horse", "Long Stride", "Runs 15% faster with you on its back, and gives you Speed while near.");
		add("kung_fu_dugong", "Kung-Fu Master", "While it fights near you, you get Strength. Its kicks knock foes back.");
		add("yagara_bull", "Water 7 Ferry", "Swims 20% faster with you aboard. Dolphin's Grace for you in the water near it.");
		add("fighting_bull", "Bull Charge", "Ride it into enemies to ram them. Your hits from its back send foes flying.");
		add("triceratops", "Horn Charge", "Ride it into enemies to ram them. Resistance while you ride it.");
		add("momoo", "Sea Cow Haul", "Put a Towing Harness on it to pull your ship. Conduit Power in the water near it.");
		add("circus_lion", "Fire Hoop", "Its bites set foes on fire.");
		add("komainu", "Guardian Spirit", "Resistance while it's near.");
		add("wano_wolf", "Pack Hunter", "Speed while it's near. It bites harder at whatever you're fighting.");
		add("battle_snake", "Coil", "Its bites slow foes down.");
		add("kraken", "Ink Cloud", "Whoever hurts it is blinded by ink. Water Breathing near it.");
		add("megalo", "Shark Escort", "Dolphin's Grace and Water Breathing in the water near it.");
		add("lapahn", "Snow Leap", "Jump Boost II while it's near.");
		add("bananawani", "Croc Jaws", "Its bites pin foes in place (heavy Slowness).");
		add("cerberus", "Three Heads", "Its bites wither foes. Night Vision at night while it's near.");
		add("rusukaina_gorilla", "Training Partner", "Strength while it's near, like Luffy's two years on Rusukaina.");
		add("punk_hazard_dragon", "Dragon Fire", "Flies! Fire Resistance while you ride it, and your hits from its back burn.");
		add("cave_mole", "Tunnel Sense", "Haste while it's near (faster mining).");
		add("sea_king", "King of the Deep", "Wild Sea Kings leave you alone while it's near. Harness it to pull your ship. Your hits from its back crush.");
	}

	private static void add(String id, String name, String description) {
		ALL.put(id, new Ability(name, description));
	}

	private PetAbilities() {
	}

	/** Called from Pets.initialize(). */
	public static void initialize() {
		// Riding a pet into battle: some mounts add something to your own hits.
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (!level.isClientSide() && player.getVehicle() instanceof Mob mount && mount instanceof Pet pet
					&& pet.isTamed() && target instanceof LivingEntity living) {
				riderHit(mount, pet, player, living);
			}
			return InteractionResult.PASS;
		});
	}

	public static java.util.Collection<String> kinds() {
		return ALL.keySet();
	}

	public static Ability byKind(String kind) {
		return ALL.get(kind);
	}

	public static Ability of(Mob mob) {
		return mob instanceof Pet pet ? ALL.get(pet.petKind()) : null;
	}

	/** The ability's name, with "II" once the bond is strong enough. */
	public static String name(Mob mob) {
		Ability ability = of(mob);
		if (ability == null) {
			return "none";
		}
		return PetBond.empowered((Pet) mob) ? ability.name() + " II" : ability.name();
	}

	// ---------- Helping the owner (every 2 seconds) ----------

	public static void tick(Mob mob, ServerLevel level) {
		Pet pet = (Pet) mob;
		if (!pet.isTamed() || mob.tickCount % 40 != 7) {
			return;
		}
		if (!(Pets.ownerOf(pet, level) instanceof ServerPlayer owner) || owner.isSpectator()) {
			return;
		}
		boolean riding = owner.getVehicle() == mob;
		if (!riding && mob.distanceToSqr(owner) > AURA_RANGE * AURA_RANGE) {
			return;
		}
		boolean strong = PetBond.empowered(pet);
		int amp = strong ? 1 : 0;
		switch (pet.petKind()) {
			case "south_bird" -> {
				for (Mob enemy : level.getEntitiesOfClass(Mob.class, owner.getBoundingBox().inflate(strong ? 24 : 16),
						m -> m instanceof Enemy && m.isAlive() && !(m instanceof Pet p && p.isTamed()))) {
					enemy.addEffect(new MobEffectInstance(MobEffects.GLOWING, 60, 0, true, false));
				}
			}
			case "spot_billed_duck", "long_horse", "wano_wolf" -> give(owner, MobEffects.SPEED, amp);
			case "cotton_candy_lamb" -> {
				if (owner.getHealth() < owner.getMaxHealth() * 0.5f) {
					give(owner, MobEffects.REGENERATION, amp);
				}
			}
			case "island_whale" -> {
				if (owner.isInWater()) {
					give(owner, MobEffects.REGENERATION, amp);
					give(owner, MobEffects.WATER_BREATHING, 0);
				}
			}
			case "wild_den_den_mushi" -> give(owner, MobEffects.LUCK, amp);
			case "drum_reindeer" -> {
				if (owner.getHealth() < owner.getMaxHealth() * 0.4f && cooledDown(mob, level, strong ? 450 : 900)) {
					owner.heal(strong ? 12.0f : 8.0f);
					level.sendParticles(ParticleTypes.HAPPY_VILLAGER, owner.getX(), owner.getY() + 1.0, owner.getZ(), 10, 0.4, 0.5, 0.4, 0.0);
					Pets.tell(owner, net.minecraft.network.chat.Component.empty().append(mob.getName()).append(" patched you up!"),
							net.minecraft.ChatFormatting.GREEN);
				}
			}
			case "sauropod", "triceratops" -> {
				if (riding) {
					give(owner, MobEffects.RESISTANCE, amp);
				}
			}
			case "fuzza" -> {
				if (!owner.onGround() && owner.getDeltaMovement().y < -0.3 && !riding) {
					give(owner, MobEffects.SLOW_FALLING, 0);
				}
			}
			case "hiking_bear" -> give(owner, MobEffects.JUMP_BOOST, amp);
			case "lapahn" -> give(owner, MobEffects.JUMP_BOOST, 1 + amp);
			case "kung_fu_dugong" -> {
				if (mob.getTarget() != null) {
					give(owner, MobEffects.STRENGTH, amp);
				}
			}
			case "yagara_bull" -> {
				if (owner.isInWater() && !riding) {
					give(owner, MobEffects.DOLPHINS_GRACE, 0);
				}
			}
			case "momoo" -> {
				if (owner.isInWater()) {
					give(owner, MobEffects.CONDUIT_POWER, 0);
				}
			}
			case "komainu" -> give(owner, MobEffects.RESISTANCE, amp);
			case "kraken" -> {
				if (owner.isInWater()) {
					give(owner, MobEffects.WATER_BREATHING, 0);
				}
			}
			case "megalo" -> {
				if (owner.isInWater()) {
					give(owner, MobEffects.WATER_BREATHING, 0);
					if (!riding) {
						give(owner, MobEffects.DOLPHINS_GRACE, 0);
					}
				}
			}
			case "cerberus" -> {
				long time = level.getDefaultClockTime() % 24000L;
				if (time >= 13000L && time < 23000L) {
					owner.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 320, 0, true, false, true));
				}
			}
			case "rusukaina_gorilla" -> give(owner, MobEffects.STRENGTH, amp);
			case "punk_hazard_dragon" -> {
				if (riding) {
					give(owner, MobEffects.FIRE_RESISTANCE, 0);
				}
			}
			case "cave_mole" -> give(owner, MobEffects.HASTE, amp);
			case "sea_king" -> calmWildSeaKings(mob, owner, level, strong ? 64 : 40);
			default -> {
			}
		}
	}

	private static void give(LivingEntity entity, Holder<MobEffect> effect, int amplifier) {
		entity.addEffect(new MobEffectInstance(effect, 100, amplifier, true, false, true));
	}

	/** Wild Sea Kings that are after you lose interest: your Sea King is the king of these waters. */
	private static void calmWildSeaKings(Mob mob, ServerPlayer owner, ServerLevel level, double range) {
		List<com.onepiecemod.sea.SeaKingEntity> wild = level.getEntitiesOfClass(com.onepiecemod.sea.SeaKingEntity.class,
				owner.getBoundingBox().inflate(range, 32, range),
				king -> king != mob && !king.isTamed() && !king.isSeaBoss() && !king.entityTags().contains("onepiece_sea_king_lord"));
		for (com.onepiecemod.sea.SeaKingEntity king : wild) {
			LivingEntity target = king.getTarget();
			if (target == owner || (target != null && (target.getVehicle() == mob || Pets.isOwner((Pet) mob, target)))
					|| (target != null && com.onepiecemod.ship.ShipEntity.aboard(target) != null
							&& com.onepiecemod.ship.ShipEntity.aboard(target) == com.onepiecemod.ship.ShipEntity.aboard(owner))) {
				king.setTarget(null);
				king.getNavigation().stop();
				// Swim away from your Sea King.
				Vec3 away = king.position().subtract(mob.position()).normalize().scale(1.2);
				king.getNavigation().moveTo(king.getX() + away.x * 16, king.getY(), king.getZ() + away.z * 16, 1.0);
			}
		}
	}

	/** True (and restarts the timer) when this pet's ability cooldown is over. Kept in the entity's tags-free memory. */
	private static boolean cooledDown(Mob mob, ServerLevel level, int ticks) {
		long now = level.getGameTime();
		Long last = COOLDOWNS.get(mob.getUUID());
		if (last != null && now - last < ticks) {
			return false;
		}
		COOLDOWNS.put(mob.getUUID(), now);
		return true;
	}

	private static final Map<java.util.UUID, Long> COOLDOWNS = new HashMap<>();
	private static final Map<java.util.UUID, Vec3> LAST_POS = new HashMap<>();

	// ---------- Fighting ----------

	/** The pet itself bit or struck something. */
	public static void onHit(Mob mob, Entity target) {
		Pet pet = (Pet) mob;
		if (!pet.isTamed() || !(target instanceof LivingEntity living)) {
			return;
		}
		boolean strong = PetBond.empowered(pet);
		switch (pet.petKind()) {
			case "kung_fu_dugong" -> push(mob, living, strong ? 1.4 : 0.9);
			case "circus_lion" -> living.igniteForSeconds(strong ? 6 : 4);
			case "battle_snake" -> living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, strong ? 2 : 1), mob);
			case "bananawani" -> living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, strong ? 4 : 3), mob);
			case "cerberus" -> living.addEffect(new MobEffectInstance(MobEffects.WITHER, strong ? 100 : 60, 0), mob);
			case "wano_wolf" -> {
				LivingEntity owner = Pets.ownerOf(pet, mob.level());
				if (owner != null && owner.getLastHurtMob() == living && mob.level() instanceof ServerLevel level) {
					living.hurtServer(level, mob.damageSources().mobAttack(mob), strong ? 4.0f : 2.0f);
				}
			}
			default -> {
			}
		}
	}

	/** Something hurt the pet. */
	public static void onHurt(Mob mob, DamageSource source) {
		Pet pet = (Pet) mob;
		if (pet.isTamed() && pet.petKind().equals("kraken") && source.getEntity() instanceof LivingEntity attacker
				&& !Pets.isOwner(pet, attacker) && mob.level() instanceof ServerLevel level) {
			attacker.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, PetBond.empowered(pet) ? 100 : 60, 0), mob);
			level.sendParticles(ParticleTypes.SQUID_INK, mob.getX(), mob.getY() + mob.getBbHeight() * 0.5, mob.getZ(), 20, 0.8, 0.6, 0.8, 0.05);
		}
	}

	/** The player hit something while riding their pet. */
	private static void riderHit(Mob mount, Pet pet, Player rider, LivingEntity target) {
		if (target == mount || Pets.isOwner(pet, target)) {
			return;
		}
		boolean strong = PetBond.empowered(pet);
		switch (pet.petKind()) {
			case "fighting_bull" -> push(rider, target, strong ? 1.6 : 1.1);
			case "punk_hazard_dragon" -> {
				target.igniteForSeconds(strong ? 8 : 5);
				if (mount.level() instanceof ServerLevel level) {
					level.sendParticles(ParticleTypes.FLAME, target.getX(), target.getY() + target.getBbHeight() * 0.5, target.getZ(),
							12, 0.3, 0.4, 0.3, 0.02);
				}
			}
			case "sea_king" -> {
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, strong ? 2 : 1), rider);
				push(mount, target, strong ? 1.2 : 0.8);
			}
			default -> {
			}
		}
	}

	private static void push(Entity from, LivingEntity target, double strength) {
		Vec3 away = target.position().subtract(from.position()).multiply(1, 0, 1);
		if (away.lengthSqr() < 1.0e-4) {
			away = Vec3.directionFromRotation(0, from.getYRot());
		}
		away = away.normalize().scale(strength);
		target.setDeltaMovement(target.getDeltaMovement().add(away.x, 0.35 + strength * 0.15, away.z));
		Motion.sync(target);
	}

	// ---------- Riding ----------

	/** How much faster this pet runs or swims with a rider (1 = normal). */
	public static float riddenSpeedFactor(Pet pet) {
		return switch (pet.petKind()) {
			case "spot_billed_duck" -> PetBond.empowered(pet) ? 1.35f : 1.25f;
			case "long_horse" -> PetBond.empowered(pet) ? 1.25f : 1.15f;
			case "yagara_bull" -> PetBond.empowered(pet) ? 1.3f : 1.2f;
			default -> 1.0f + 0.01f * (PetBond.level(pet) - 1); // every pet runs a little faster as your bond grows
		};
	}

	/** Bulls and triceratops ram whatever they run into while you ride them. Called every tick on the server. */
	public static void tickRam(Mob mob, ServerLevel level) {
		Pet pet = (Pet) mob;
		String kind = pet.petKind();
		if (!kind.equals("fighting_bull") && !kind.equals("triceratops")) {
			return;
		}
		if (!(mob.getControllingPassenger() instanceof Player rider)) {
			LAST_POS.remove(mob.getUUID());
			return;
		}
		// The rider's game moves it, so measure how far it went since the last check ourselves.
		Vec3 before = LAST_POS.put(mob.getUUID(), mob.position());
		if (before == null || mob.tickCount % 5 != 0) {
			if (before != null) {
				LAST_POS.put(mob.getUUID(), before); // keep the position from 5 ticks ago
			}
			return;
		}
		double moved = mob.position().subtract(before).horizontalDistance() / 5.0;
		if (moved < 0.18) {
			return;
		}
		Vec3 ahead = Vec3.directionFromRotation(0, mob.getYRot()).scale(mob.getBbWidth() * 0.6);
		List<LivingEntity> hit = level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().move(ahead).inflate(0.3),
				e -> e != mob && e != rider && e.isAlive() && !Pets.isOwner(pet, e) && !(e instanceof Pet p && p.isTamed())
						&& !com.onepiecemod.crew.CrewmateEntity.sameCrew(mob, e) && !(e instanceof Player));
		if (hit.isEmpty() || !cooledDown(mob, level, 20)) {
			return;
		}
		float damage = (float) mob.getAttributeValue(Attributes.ATTACK_DAMAGE) * (PetBond.empowered(pet) ? 1.3f : 1.0f);
		for (LivingEntity target : hit) {
			if (target.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
				push(mob, target, 1.5);
			}
		}
		level.sendParticles(ParticleTypes.CLOUD, mob.getX() + ahead.x, mob.getY() + 0.5, mob.getZ() + ahead.z, 8, 0.4, 0.3, 0.4, 0.02);
	}
}
