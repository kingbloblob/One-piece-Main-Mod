package com.onepiecemod.lifeskill;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Prediction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CocoaBlock;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.NetherWartBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.tag.convention.v2.ConventionalBlockTags;
import net.fabricmc.fabric.api.tag.convention.v2.ConventionalItemTags;

/**
 * Where life skill XP comes from, and where the perks kick in.
 *
 * - Farming: breaking a fully grown crop.
 * - Mining: breaking an ore (not with Silk Touch), plus 1 XP for every 10 stone blocks.
 * - Cooking: taking food out of a furnace/smoker, crafting food, Ship's Galley dishes.
 * - Smithing: crafting tools, weapons and armour (better gear = more XP), smelting ingots, the
 *   Swordsmith's Forge, Seastone Workbench and Shipwright's Bench.
 *
 * Crafting is caught by the mixins in lifeskill.mixin (vanilla calls ItemStack.onCraftedBy for the
 * crafting grid, furnaces and the smithing table), and crafting stations call onStationCraft.
 */
public final class LifeSkillHooks {
	/** 1 Mining XP per this many stone blocks. */
	private static final int STONE_PER_XP = 10;
	private static final int FIELD_REPAIR_TICKS = 600;
	private static final double FERTILE_TOUCH_CHANCE = 0.15;
	private static final double FINE_CHANCE = 0.15;
	private static final String FORGED_PREFIX = "Forged by ";

	/** True while a furnace result slot is handing out items, so smelted ingots can count (crafted ones don't). */
	static boolean takingFromFurnace;

	private static final Map<UUID, Integer> STONE_BROKEN = new HashMap<>();

	private LifeSkillHooks() {
	}

	static void initialize() {
		PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
			if (player instanceof ServerPlayer serverPlayer && level instanceof ServerLevel serverLevel) {
				onBlockBroken(serverLevel, serverPlayer, pos, state, blockEntity);
			}
		});

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % FIELD_REPAIR_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				fieldRepair(player);
			}
		});

		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> STONE_BROKEN.remove(handler.player.getUUID()));
	}

	// ---- Farming and Mining ----

	private static void onBlockBroken(ServerLevel level, ServerPlayer player, BlockPos pos, BlockState state, BlockEntity blockEntity) {
		if (player.isCreative() || player.isSpectator()) {
			return;
		}
		Block block = state.getBlock();
		LifeSkills.Entry entry = LifeSkills.blockEntry(block);
		ItemStack tool = player.getMainHandItem();

		if (isCrop(state, entry)) {
			if (!isFullyGrown(state)) {
				return;
			}
			int xp = entry != null ? entry.xp() : LifeSkills.DEFAULT_CROP_XP;
			LifeSkills.addXp(player, LifeSkill.FARMING, xp);
			farmingPerks(level, player, pos, state, blockEntity, tool);
			return;
		}

		if (isOre(state, entry)) {
			if (hasSilkTouch(level, tool)) {
				return;
			}
			int xp = entry != null ? entry.xp() : LifeSkillDefaults.oreXp(LifeSkills.id(block).getPath());
			LifeSkills.addXp(player, LifeSkill.MINING, xp);
			miningPerks(level, player, pos, state, blockEntity, tool, xp);
			return;
		}

		if (state.is(BlockTags.BASE_STONE_OVERWORLD) || state.is(BlockTags.BASE_STONE_NETHER)) {
			int count = STONE_BROKEN.merge(player.getUUID(), 1, Integer::sum);
			if (count >= STONE_PER_XP) {
				STONE_BROKEN.put(player.getUUID(), 0);
				LifeSkills.addXp(player, LifeSkill.MINING, 1);
			}
		}
	}

	private static boolean isCrop(BlockState state, LifeSkills.Entry entry) {
		if (entry != null) {
			return entry.skill() == LifeSkill.FARMING;
		}
		Block block = state.getBlock();
		return block instanceof CropBlock || block instanceof NetherWartBlock || block instanceof CocoaBlock
				|| state.is(LifeSkills.FARMING_BLOCKS);
	}

	private static boolean isOre(BlockState state, LifeSkills.Entry entry) {
		if (entry != null) {
			return entry.skill() == LifeSkill.MINING;
		}
		return state.is(ConventionalBlockTags.ORES) || state.is(LifeSkills.MINING_BLOCKS)
				|| LifeSkills.id(state.getBlock()).getPath().endsWith("_ore");
	}

	/** The block's "age" property, if it has one (every vanilla crop and most modded ones). */
	private static IntegerProperty ageProperty(BlockState state) {
		for (Property<?> property : state.getProperties()) {
			if (property instanceof IntegerProperty integer && property.getName().equals("age")) {
				return integer;
			}
		}
		return null;
	}

	private static boolean isFullyGrown(BlockState state) {
		IntegerProperty age = ageProperty(state);
		if (age == null) {
			return true; // Melons and other "the whole block is the harvest" crops.
		}
		int max = 0;
		for (int value : age.getPossibleValues()) {
			max = Math.max(max, value);
		}
		return state.getValue(age) >= max;
	}

	private static void farmingPerks(ServerLevel level, ServerPlayer player, BlockPos pos, BlockState state, BlockEntity blockEntity, ItemStack tool) {
		RandomSource random = player.getRandom();
		int skill = LifeSkills.level(player, LifeSkill.FARMING);
		int rolls = skill >= 50 ? 2 : 1;
		for (int i = 0; i < rolls; i++) {
			if (random.nextDouble() < LifeSkills.bonusChance(player, LifeSkill.FARMING)) {
				Block.dropResources(state, level, pos, blockEntity, player, tool);
			}
		}
		if (skill >= 10) {
			replant(level, player, pos, state);
		}
		if (skill >= 25 && random.nextDouble() < FERTILE_TOUCH_CHANCE) {
			growNeighbours(level, pos);
		}
	}

	/** Green Thumb: put a fresh crop back, using one seed from the player's bag. */
	private static void replant(ServerLevel level, ServerPlayer player, BlockPos pos, BlockState state) {
		Block block = state.getBlock();
		if (!(block instanceof CropBlock || block instanceof NetherWartBlock) || !level.getBlockState(pos).isAir()) {
			return;
		}
		BlockState fresh = block.defaultBlockState();
		if (!fresh.canSurvive(level, pos)) {
			return;
		}
		var inventory = player.getInventory();
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (!stack.isEmpty() && stack.is(block.asItem())) {
				stack.shrink(1);
				level.setBlockAndUpdate(pos, fresh);
				return;
			}
		}
	}

	/** Fertile Touch: crops around the harvested one grow a stage. */
	private static void growNeighbours(ServerLevel level, BlockPos center) {
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-2, -1, -2), center.offset(2, 1, 2))) {
			BlockState state = level.getBlockState(pos);
			if (!(state.getBlock() instanceof CropBlock || state.getBlock() instanceof NetherWartBlock)) {
				continue;
			}
			IntegerProperty age = ageProperty(state);
			if (age != null && !isFullyGrown(state)) {
				level.setBlockAndUpdate(pos.immutable(), state.setValue(age, state.getValue(age) + 1));
			}
		}
	}

	private static boolean hasSilkTouch(ServerLevel level, ItemStack tool) {
		if (tool.isEmpty()) {
			return false;
		}
		Holder<Enchantment> silk = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.SILK_TOUCH);
		return EnchantmentHelper.getItemEnchantmentLevel(silk, tool) > 0;
	}

	private static void miningPerks(ServerLevel level, ServerPlayer player, BlockPos pos, BlockState state, BlockEntity blockEntity, ItemStack tool, int xp) {
		int skill = LifeSkills.level(player, LifeSkill.MINING);
		if (player.getRandom().nextDouble() < LifeSkills.bonusChance(player, LifeSkill.MINING)) {
			Block.dropResources(state, level, pos, blockEntity, player, tool);
			player.sendOverlayMessage(Component.literal("Lucky Strike! Double drops.").withStyle(ChatFormatting.AQUA));
		}
		if (skill >= 10) {
			player.addEffect(new MobEffectInstance(MobEffects.HASTE, 200, skill >= 25 ? 1 : 0, true, false, true));
		}
		if (skill >= 50) {
			ExperienceOrb.award(level, Vec3.atCenterOf(pos), Math.max(1, xp / 2));
		}
	}

	// ---- Cooking and Smithing ----

	/** Where a crafted item came from. */
	public enum Source {
		/** Crafting grid, smithing table, stonecutter... anything that calls ItemStack.onCraftedBy. */
		CRAFTING,
		FURNACE,
		COOKING_STATION,
		SMITHING_STATION,
		/** A station that doesn't train a skill (e.g. the Navigator's Desk): only registered items count. */
		OTHER_STATION
	}

	/** Called by the ItemStack mixin when a player takes crafted or smelted items. */
	public static void onCrafted(Player player, ItemStack stack, int count) {
		if (player instanceof ServerPlayer serverPlayer && !stack.isEmpty() && count > 0) {
			award(serverPlayer, stack, count, takingFromFurnace ? Source.FURNACE : Source.CRAFTING);
		}
	}

	/**
	 * Called by crafting stations for each item stack they make. Gives XP, the Extra Portion roll for
	 * food, and the Smithing durability bonus (it changes the stack, so call it before handing it over).
	 *
	 * @param stationId the station's id, e.g. "ships_galley" or "swordsmith_forge"
	 */
	public static void onStationCraft(ServerPlayer player, String stationId, ItemStack stack) {
		Source source = switch (stationId) {
			case "ships_galley" -> Source.COOKING_STATION;
			case "swordsmith_forge", "seastone_workbench", "shipwright_bench" -> Source.SMITHING_STATION;
			default -> Source.OTHER_STATION;
		};
		if (isGear(stack)) {
			forge(player, stack);
		}
		award(player, stack, stack.getCount(), source);
	}

	private static void award(ServerPlayer player, ItemStack stack, int count, Source source) {
		if (stack.is(LifeSkills.NO_XP_ITEMS)) {
			return;
		}
		LifeSkills.Entry entry = LifeSkills.craftEntry(stack.getItem());
		if (entry != null) {
			LifeSkills.addXp(player, entry.skill(), entry.xp() * count);
			if (entry.skill() == LifeSkill.COOKING) {
				extraPortion(player, stack, count);
			}
			return;
		}
		if (source == Source.OTHER_STATION) {
			return;
		}
		if (stack.has(DataComponents.FOOD) || stack.is(LifeSkills.COOKING_ITEMS)) {
			int each = source == Source.COOKING_STATION ? 6 : LifeSkills.DEFAULT_FOOD_XP;
			LifeSkills.addXp(player, LifeSkill.COOKING, each * count);
			extraPortion(player, stack, count);
		} else if (isGear(stack)) {
			int each = gearXp(stack);
			if (source == Source.SMITHING_STATION) {
				each = Math.max(8, each);
			}
			LifeSkills.addXp(player, LifeSkill.SMITHING, each * count);
		} else if (source == Source.FURNACE && stack.is(ConventionalItemTags.INGOTS)) {
			LifeSkills.addXp(player, LifeSkill.SMITHING, count);
		} else if (source == Source.SMITHING_STATION) {
			LifeSkills.addXp(player, LifeSkill.SMITHING, 3 * count);
		}
	}

	private static boolean isGear(ItemStack stack) {
		return stack.isDamageableItem() || stack.is(LifeSkills.SMITHING_ITEMS);
	}

	/** Wood/leather gear gives 1 XP (too cheap to farm), iron about 6, diamond about 13-39. */
	private static int gearXp(ItemStack stack) {
		Integer max = stack.getPrototype().get(DataComponents.MAX_DAMAGE);
		int durability = max != null ? max : 0;
		if (durability <= 0) {
			return LifeSkills.DEFAULT_GEAR_XP;
		}
		if (durability < 150) {
			return 1;
		}
		return Math.max(4, Math.min(40, durability / 40));
	}

	/** Cooking's Extra Portion: each item made has a chance to come with one more (two at level 50). */
	private static void extraPortion(ServerPlayer player, ItemStack stack, int count) {
		double chance = LifeSkills.bonusChance(player, LifeSkill.COOKING);
		int per = LifeSkills.level(player, LifeSkill.COOKING) >= 50 ? 2 : 1;
		int extra = 0;
		for (int i = 0; i < Math.min(count, 64); i++) {
			if (player.getRandom().nextDouble() < chance) {
				extra += per;
			}
		}
		if (extra > 0) {
			ItemStack bonus = stack.copyWithCount(extra);
			if (!player.getInventory().add(bonus)) {
				player.drop(bonus, false, Prediction.SERVER_ONLY);
			}
			player.sendOverlayMessage(Component.literal("Extra Portion! +" + extra + " " + stack.getHoverName().getString())
					.withStyle(style -> style.withColor(LifeSkill.COOKING.color)));
		}
	}

	/**
	 * Smithing's mark on crafted gear: more durability (from the item's normal durability, so a netherite
	 * upgrade gets the right number), a "Forged by" line, and at 25+ a chance to be Fine.
	 * Called by the Item mixin before the crafted stack reaches the inventory.
	 */
	public static void forge(Player player, ItemStack stack) {
		if (!(player instanceof ServerPlayer serverPlayer) || !stack.isDamageableItem()) {
			return;
		}
		int skill = LifeSkills.level(serverPlayer, LifeSkill.SMITHING);
		Integer base = stack.getPrototype().get(DataComponents.MAX_DAMAGE);
		if (base == null || base <= 0) {
			return;
		}
		int percent = skill * (skill >= 50 ? 2 : 1);
		stack.set(DataComponents.MAX_DAMAGE, base + base * percent / 100);

		ItemLore lore = stack.getOrDefault(DataComponents.LORE, ItemLore.EMPTY);
		boolean alreadyForged = false;
		List<Component> lines = new ArrayList<>();
		for (Component line : lore.lines()) {
			if (line.getString().startsWith(FORGED_PREFIX)) {
				alreadyForged = true;
			} else {
				lines.add(line);
			}
		}
		lines.add(Component.literal(FORGED_PREFIX + serverPlayer.getName().getString() + " (+" + percent + "% durability)")
				.withStyle(ChatFormatting.GRAY));
		stack.set(DataComponents.LORE, new ItemLore(lines));

		// A smithing-table upgrade keeps the old mark, so it can't be rolled again.
		if (!alreadyForged && skill >= 25 && serverPlayer.getRandom().nextDouble() < FINE_CHANCE) {
			Holder<Enchantment> unbreaking = serverPlayer.level().registryAccess().lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.UNBREAKING);
			int level = skill >= 50 ? 2 : 1;
			if (EnchantmentHelper.getItemEnchantmentLevel(unbreaking, stack) < level) {
				stack.enchant(unbreaking, level);
			}
			serverPlayer.sendSystemMessage(Component.literal("Smith's Mark: you made a Fine " + stack.getHoverName().getString() + "!")
					.withStyle(style -> style.withColor(LifeSkill.SMITHING.color)));
		}
	}

	/** Smithing 10 Field Repair: the held tool mends 1 durability every 30 seconds. */
	private static void fieldRepair(ServerPlayer player) {
		if (!player.isAlive() || LifeSkills.level(player, LifeSkill.SMITHING) < 10) {
			return;
		}
		ItemStack held = player.getMainHandItem();
		if (held.isDamageableItem() && held.getDamageValue() > 0) {
			held.setDamageValue(held.getDamageValue() - 1);
		}
	}

	/** Called by the ItemStack mixin when a player finishes eating something. */
	public static void onEat(Level level, Player player, ItemStack stack) {
		if (!(player instanceof ServerPlayer serverPlayer) || !stack.has(DataComponents.FOOD)) {
			return;
		}
		int skill = LifeSkills.level(serverPlayer, LifeSkill.COOKING);
		if (skill >= 10) {
			serverPlayer.getFoodData().eat(skill >= 50 ? 2 : 1, 0.3f);
		}
		if (skill >= 25) {
			serverPlayer.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0, true, true, true));
		}
	}
}
