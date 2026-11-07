package com.onepiecemod.weapon;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * A whetstone, gun part or Dial. Hold the weapon in your OFF hand, the upgrade in your main hand,
 * and right-click. The upgrade is used up and the weapon keeps it for good.
 */
public class UpgradeItem extends Item {
	public enum Kind {
		SKILLFUL_WHETSTONE("Raises a sword to Skillful Grade."),
		GREAT_WHETSTONE("Raises a Skillful Grade sword to Great Grade."),
		SUPREME_WHETSTONE("Raises a Great Grade sword to Supreme Grade."),
		SCOPE("Gun part: +50% range and steadier aim."),
		LONG_BARREL("Gun part: +3 damage per shot."),
		HAIR_TRIGGER("Gun part: 30% faster reload."),
		FLAME_DIAL("Fits any weapon: sets what it hits on fire."),
		IMPACT_DIAL("Fits any weapon: knocks what it hits far away.");

		private final String help;

		Kind(String help) {
			this.help = help;
		}
	}

	private final Kind kind;

	public UpgradeItem(Kind kind, Properties properties) {
		super(properties);
		this.kind = kind;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (hand != InteractionHand.MAIN_HAND) {
			return InteractionResult.PASS;
		}
		ItemStack upgrade = player.getMainHandItem();
		ItemStack weapon = player.getOffhandItem();
		if (level.isClientSide() || !(player instanceof ServerPlayer smith)) {
			return InteractionResult.SUCCESS;
		}
		String problem = apply(weapon);
		if (problem != null) {
			smith.sendOverlayMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}
		if (!player.getAbilities().instabuild) {
			upgrade.shrink(1);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.SMITHING_TABLE_USE, SoundSource.PLAYERS, 1.0f, 1.0f);
		smith.sendOverlayMessage(Component.literal("Upgraded " + weapon.getHoverName().getString() + "!").withStyle(ChatFormatting.GREEN));
		return InteractionResult.SUCCESS;
	}

	/** Puts the upgrade on the weapon. Returns null if it worked, or why it didn't. */
	private String apply(ItemStack weapon) {
		if (weapon.isEmpty()) {
			return "Hold the weapon in your off hand.";
		}
		switch (kind) {
			case SKILLFUL_WHETSTONE, GREAT_WHETSTONE, SUPREME_WHETSTONE -> {
				int target = kind.ordinal() + 1;
				if (!WeaponUpgrades.isSword(weapon)) {
					return "Whetstones only work on swords.";
				}
				int grade = WeaponUpgrades.grade(weapon);
				if (grade >= target) {
					return "This sword is already " + WeaponUpgrades.GRADE_NAMES[grade] + ".";
				}
				if (grade < target - 1) {
					return "Raise it to " + WeaponUpgrades.GRADE_NAMES[target - 1] + " first.";
				}
				WeaponUpgrades.setGrade(weapon, target);
			}
			case SCOPE, LONG_BARREL, HAIR_TRIGGER -> {
				if (!(weapon.getItem() instanceof GunItem)) {
					return "Gun parts only fit guns and slingshots.";
				}
				int part = kind == Kind.SCOPE ? WeaponUpgrades.SCOPE : kind == Kind.LONG_BARREL ? WeaponUpgrades.LONG_BARREL : WeaponUpgrades.HAIR_TRIGGER;
				if (WeaponUpgrades.hasPart(weapon, part)) {
					return "This gun already has that part.";
				}
				weapon.set(WeaponUpgrades.GUN_PARTS, weapon.getOrDefault(WeaponUpgrades.GUN_PARTS, 0) | part);
			}
			case FLAME_DIAL, IMPACT_DIAL -> {
				if (!WeaponUpgrades.canHoldDial(weapon)) {
					return "Dials fit swords, axes, guns and the mod's melee weapons.";
				}
				// A weapon holds one Dial. A new one replaces the old.
				weapon.set(WeaponUpgrades.DIAL, kind == Kind.FLAME_DIAL ? WeaponUpgrades.FLAME_DIAL : WeaponUpgrades.IMPACT_DIAL);
			}
		}
		return null;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		textConsumer.accept(Component.literal(kind.help).withStyle(ChatFormatting.GRAY));
		textConsumer.accept(Component.literal("Weapon in off hand, this in main hand, right-click.").withStyle(ChatFormatting.DARK_GRAY));
	}
}
