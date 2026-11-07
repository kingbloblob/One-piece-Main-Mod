package com.onepiecemod.fx.client;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.PlayerModelType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.client.RenderGuard;
import com.onepiecemod.fx.ElementFx;

/**
 * A Logia user's body turning into their element when an attack passes through them: a glowing shell
 * in the element's color wraps the whole body, then crumbles away over about half a second
 * (textures/entity/fx/element_0..3.png have more and more holes).
 */
public class ElementLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	public static final ModelLayerLocation WIDE = new ModelLayerLocation(OnePieceMod.id("element_body"), "wide");
	public static final ModelLayerLocation SLIM = new ModelLayerLocation(OnePieceMod.id("element_body"), "slim");
	private static final Identifier[] FRAMES = {
			OnePieceMod.id("textures/entity/fx/element_0.png"), OnePieceMod.id("textures/entity/fx/element_1.png"),
			OnePieceMod.id("textures/entity/fx/element_2.png"), OnePieceMod.id("textures/entity/fx/element_3.png")};

	private final PlayerModel wide;
	private final PlayerModel slim;

	public ElementLayer(RenderLayerParent<AvatarRenderState, PlayerModel> parent, EntityRendererProvider.Context context) {
		super(parent);
		this.wide = new PlayerModel(context.bakeLayer(WIDE), false);
		this.slim = new PlayerModel(context.bakeLayer(SLIM), true);
	}

	public static LayerDefinition createLayer(boolean slim) {
		return LayerDefinition.create(PlayerModel.createMesh(new CubeDeformation(0.45f), slim), 64, 64);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		RenderGuard.run("logia body", poseStack, () -> {
			if (state.isInvisible || state.isSpectator || Minecraft.getInstance().level == null) {
				return;
			}
			Entity player = Minecraft.getInstance().level.getEntity(state.id);
			ElementFx.Flash flash = player != null ? player.getAttached(ElementFx.LOGIA_FLASH) : null;
			float age = player != null ? ElementFx.flashAge(player, state.ageInTicks % 1.0f) : -1;
			if (flash == null || age < 0) {
				return;
			}
			PlayerModel model = state.skin != null && state.skin.model() == PlayerModelType.SLIM ? slim : wide;
			model.setupAnim(state);
			int frame = Math.min(FRAMES.length - 1, (int) (age / ElementFx.FLASH_TICKS * FRAMES.length));
			renderColoredCutoutModel(model, FRAMES[frame], poseStack, collector, 0xF000F0, state, 0xFF000000 | flash.color(), 1);
		});
	}
}
