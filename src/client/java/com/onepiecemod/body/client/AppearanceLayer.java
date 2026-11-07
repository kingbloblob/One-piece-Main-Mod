package com.onepiecemod.body.client;

import java.util.HashSet;
import java.util.Set;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.body.BodyAttachments;
import com.onepiecemod.body.Look;
import com.onepiecemod.race.Race;
import com.onepiecemod.race.RaceAttachments;

/**
 * Draws a player's race features (Mink ears and tail, Oni horns, Skypiean or Lunarian wings, Fish-Man fins,
 * Tontatta tail) and the hair, scar and outfit they picked on the body screen.
 */
public class AppearanceLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	/** The groups to show for this player this frame, like "race:mink" and "hair:spiky". */
	public static final RenderStateDataKey<Set<String>> GROUPS_KEY = RenderStateDataKey.create(() -> "onepiece:appearance_groups");
	/** The hair colour (0xFFRRGGBB). */
	public static final RenderStateDataKey<Integer> HAIR_COLOR_KEY = RenderStateDataKey.create(() -> "onepiece:hair_color");

	private static final Identifier FEATURES_TEXTURE = OnePieceMod.id("textures/entity/appearance/features.png");
	private static final Identifier HAIR_TEXTURE = OnePieceMod.id("textures/entity/appearance/hair.png");

	private static final int FULL_BRIGHT = 0xF000F0;

	private final AppearanceModel features;
	private final AppearanceModel hair;
	private final AppearanceModel glow;

	public AppearanceLayer(RenderLayerParent<AvatarRenderState, PlayerModel> parent, EntityRendererProvider.Context context) {
		super(parent);
		this.features = new AppearanceModel(context.bakeLayer(AppearanceModels.FEATURES), AppearanceModels.FEATURE_GROUPS, false);
		this.hair = new AppearanceModel(context.bakeLayer(AppearanceModels.HAIR), AppearanceModels.HAIR_GROUPS, false);
		this.glow = new AppearanceModel(context.bakeLayer(AppearanceModels.FEATURES), AppearanceModels.FEATURE_GROUPS, true);
	}

	/** Works out what to draw for this player. AvatarRendererMixin calls this while the frame is prepared. */
	public static void extract(Entity entity, AvatarRenderState state) {
		Set<String> groups = new HashSet<>();
		if (entity instanceof Player player) {
			Race race = RaceAttachments.get(player);
			if (race != null) {
				groups.add("race:" + race.id);
				groups.add("glow:" + race.id); // Lunarian back flame.
			}
		}
		Look look = BodyClient.lookFor(entity);
		boolean helmet = state.headEquipment != null && !state.headEquipment.isEmpty();
		if (!helmet) {
			groups.add("hair:" + look.hairId());
		}
		groups.add("scar:" + look.scarId());
		if (!helmet || !look.outfitOnHead()) {
			groups.add("outfit:" + look.outfitId());
		}
		((FabricRenderState) state).setData(GROUPS_KEY, groups);
		((FabricRenderState) state).setData(HAIR_COLOR_KEY, look.hairArgb());
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		if (state.isInvisible || state.isSpectator) {
			return;
		}
		Set<String> groups = ((FabricRenderState) state).getData(GROUPS_KEY);
		if (groups == null || groups.isEmpty()) {
			return;
		}
		renderColoredCutoutModel(features, FEATURES_TEXTURE, poseStack, collector, light, state, -1, 1);
		Integer color = ((FabricRenderState) state).getData(HAIR_COLOR_KEY);
		renderColoredCutoutModel(hair, HAIR_TEXTURE, poseStack, collector, light, state, color != null ? color : -1, 1);
		if (groups.contains("glow:lunarian")) {
			renderColoredCutoutModel(glow, FEATURES_TEXTURE, poseStack, collector, FULL_BRIGHT, state, -1, 1);
		}
	}
}
