package com.onepiecemod.career;

import java.util.function.Function;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.HumanNpc;

/**
 * Careers: play as a Marine or a Revolutionary instead of a pirate. OnePieceMod calls initialize() once.
 *
 * - Join by talking to a recruiter (Koby at Shells Town, Garp, Sengoku, Tashigi for the Marines;
 *   Dragon, Sabo or Ivankov for the Revolution) or with a Revolutionary Invitation (sent to pirates at 30M).
 * - Earn Merit / Liberation from enemies, bosses and orders; rise through the ranks (Career), with boss trials
 *   for the big promotions. Daily salary, backup on call, tougher ambushes as you rise.
 * - /career shows it all; the Den Den Mushi opens the career screen.
 */
public final class CareerFeature {
	public static final Item NAVY_DEN_DEN_MUSHI = registerItem("navy_den_den_mushi", properties -> new DenDenItem(properties, Career.MARINE),
			new Item.Properties().stacksTo(1).rarity(Rarity.RARE));
	public static final Item REVOLUTIONARY_DEN_DEN_MUSHI = registerItem("revolutionary_den_den_mushi",
			properties -> new DenDenItem(properties, Career.REVOLUTIONARY), new Item.Properties().stacksTo(1).rarity(Rarity.RARE));
	public static final Item REVOLUTIONARY_INVITATION = registerItem("revolutionary_invitation", InvitationItem::new,
			new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));

	public static final ResourceKey<EntityType<?>> CAREER_ALLY_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("career_ally"));
	public static final EntityType<CareerAllyEntity> CAREER_ALLY = Registry.register(BuiltInRegistries.ENTITY_TYPE, CAREER_ALLY_KEY,
			EntityType.Builder.of(CareerAllyEntity::new, MobCategory.MISC)
					.sized(0.6f, 1.95f)
					.clientTrackingRange(10)
					.noSave()
					.build(CAREER_ALLY_KEY));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("careers"));

	/** A pirate whose bounty reaches this gets a Revolutionary Invitation (once). */
	static final long INVITE_BOUNTY = 30_000_000L;
	/** How close you must be to a boss when it dies to share the credit, like bounties. */
	private static final double CREDIT_RANGE = 32.0;

	private CareerFeature() {
	}

	public static void initialize() {
		Careers.CAREER.getClass(); // Loading Careers registers the onepiece:career attachment.
		FabricDefaultAttributeRegistry.register(CAREER_ALLY, HumanNpc.createNpcAttributes());
		CareerPayloads.initialize();
		CareerCommands.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(NAVY_DEN_DEN_MUSHI))
				.title(Component.literal("One Piece: Careers"))
				.displayItems((params, output) -> {
					output.accept(NAVY_DEN_DEN_MUSHI);
					output.accept(REVOLUTIONARY_DEN_DEN_MUSHI);
					output.accept(REVOLUTIONARY_INVITATION);
				})
				.build());

		ServerLivingEntityEvents.AFTER_DEATH.register(CareerFeature::onDeath);

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			CareerAmbush.tick(server);
			if (server.getTickCount() % 20 != 3) {
				return;
			}
			CareerMissions.tick(server);
			long today = Careers.today(server);
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				payday(player, today);
				invite(player);
			}
		});
	}

	// ---- Defeats ----

	private static void onDeath(LivingEntity entity, net.minecraft.world.damagesource.DamageSource source) {
		if (!(entity.level() instanceof ServerLevel level)) {
			return;
		}
		CareerMissions.onDeath(entity);

		if (entity instanceof CharacterEntity boss && boss.isBoss()) {
			for (ServerPlayer player : level.players()) {
				if (player.isAlive() && !player.isSpectator() && player.distanceToSqr(boss) < CREDIT_RANGE * CREDIT_RANGE) {
					bossBeaten(player, boss);
				}
			}
			return;
		}

		ServerPlayer player = creditTo(source.getEntity());
		if (player == null) {
			return;
		}
		Career career = Careers.career(player);
		if (career == Career.MARINE) {
			if (entity instanceof MarineEntity marine) {
				Careers.strike(player, "You struck down " + marine.title() + ", a fellow Marine.");
			} else if (CareerSquads.isPirate(entity)) {
				Careers.addPoints(player, npcPoints(entity), "pirate defeated", false);
			} else if (entity instanceof ServerPlayer pirate && Bounty.get(pirate) > 0) {
				long points = Math.max(5, Math.min(1000, Bounty.get(pirate) / 2_000_000L));
				Careers.addPoints(player, (int) points, "captured " + pirate.getName().getString(), true);
			}
		} else if (career == Career.REVOLUTIONARY) {
			if (entity instanceof MarineEntity) {
				Careers.addPoints(player, npcPoints(entity), "Navy soldier defeated", false);
			} else if (entity instanceof ServerPlayer marine && Careers.isMarine(marine)) {
				Careers.addPoints(player, 10 + 10 * Careers.get(marine).rank(), "defeated Marine " + marine.getName().getString(), true);
			}
		}
	}

	/** Kills by your backup soldiers count as yours. */
	private static ServerPlayer creditTo(Entity killer) {
		if (killer instanceof ServerPlayer player) {
			return player;
		}
		if (killer instanceof CareerAllyEntity ally) {
			return ally.getOwner();
		}
		return null;
	}

	/** Points for an ordinary enemy: tougher ones are worth more (a deckhand 3, a pirate captain 7). */
	private static int npcPoints(LivingEntity entity) {
		return Math.max(1, Math.round(entity.getMaxHealth() / 8f));
	}

	private static void bossBeaten(ServerPlayer player, CharacterEntity boss) {
		Career career = Careers.career(player);
		if (career == Career.PIRATE) {
			return;
		}
		String id = boss.getCharacterId();
		boolean navy = Career.NAVY_BOSSES.contains(id);
		if (career == Career.MARINE && navy) {
			player.sendSystemMessage(Component.literal("A spar with " + boss.getData().name + " earns no Merit. The Navy is watching how you fight, though.")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		if (career == Career.REVOLUTIONARY && !navy) {
			return; // Pirates aren't the Revolution's enemy. The bounty still goes up as usual.
		}
		String flag = "boss_" + id;
		CareerData data = Careers.get(player);
		long value = Math.max(5, Math.min(1500, Bounty.bossReward(id) / 1_000_000L));
		if (data.has(flag)) {
			value = Math.max(2, value / 10);
		} else {
			Careers.set(player, data.withFlag(flag));
		}
		Careers.addPoints(player, (int) value, (career == Career.MARINE ? "brought in " : "defeated ") + boss.getData().name, true);
	}

	// ---- Every in-game day ----

	private static void payday(ServerPlayer player, long today) {
		CareerData data = Careers.get(player);
		if (data.path() == Career.PIRATE || data.lastPaidDay() >= today) {
			return;
		}
		Careers.set(player, data.withPaidDay(today));
		if (data.lastPaidDay() < 0) {
			return; // Just joined: the first pay comes tomorrow.
		}
		int salary = data.currentRank().salary();
		Careers.give(player, new ItemStack(CharacterFeature.BERRY, salary));
		player.sendSystemMessage(Component.literal((data.path() == Career.MARINE ? "Payday! Your salary as " : "Supplies from the Revolutionary Army for a ")
				+ data.currentRank().name() + ": " + salary + " Berries.").withStyle(ChatFormatting.GOLD));
	}

	/** Dragon notices famous pirates. */
	private static void invite(ServerPlayer player) {
		CareerData data = Careers.get(player);
		if (data.path() != Career.PIRATE || data.has("invited") || Bounty.get(player) < INVITE_BOUNTY) {
			return;
		}
		Careers.set(player, data.withFlag("invited"));
		Careers.give(player, new ItemStack(REVOLUTIONARY_INVITATION));
		player.sendSystemMessage(Component.literal("A hooded messenger slips you a sealed letter and vanishes into the crowd...")
				.withStyle(ChatFormatting.DARK_GREEN, ChatFormatting.ITALIC));
		player.sendSystemMessage(Component.literal("(A Revolutionary Invitation. Right-click it to join the Revolutionary Army, or keep sailing as a pirate.)")
				.withStyle(ChatFormatting.GRAY));
	}

	// ---- Items ----

	/** The career's Den Den Mushi: right-click for the career screen, sneak + right-click to call backup. */
	static class DenDenItem extends Item {
		private final Career career;

		DenDenItem(Properties properties, Career career) {
			super(properties);
			this.career = career;
		}

		@Override
		public Component getName(ItemStack stack) {
			return Component.literal(career == Career.MARINE ? "Navy Den Den Mushi" : "Revolutionary Den Den Mushi").withStyle(career.color);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				if (Careers.career(player) != career) {
					player.sendSystemMessage(Component.literal("Gacha. The line is dead: this Den Den Mushi isn't for you.").withStyle(ChatFormatting.GRAY));
				} else if (player.isShiftKeyDown()) {
					CareerAllies.call(serverPlayer);
				} else {
					CareerPayloads.open(serverPlayer);
				}
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Dragon's letter: right-click to join the Revolutionary Army. */
	static class InvitationItem extends Item {
		InvitationItem(Properties properties) {
			super(properties);
		}

		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Revolutionary Invitation").withStyle(ChatFormatting.GREEN);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				String why = Careers.whyNot(serverPlayer, Career.REVOLUTIONARY);
				if (why != null) {
					player.sendSystemMessage(Component.literal(why).withStyle(ChatFormatting.GRAY));
					return InteractionResult.FAIL;
				}
				player.sendSystemMessage(Component.literal("\"The world needs changing, and you have the strength to change it. Join us.\" - Monkey D. Dragon")
						.withStyle(ChatFormatting.DARK_GREEN, ChatFormatting.ITALIC));
				player.getItemInHand(hand).shrink(1);
				Careers.join(serverPlayer, Career.REVOLUTIONARY);
			}
			return InteractionResult.SUCCESS;
		}
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}
}
