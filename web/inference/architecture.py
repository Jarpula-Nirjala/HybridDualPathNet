"""
HybridDualPathModel architecture — EfficientNetV2-S + Swin-Tiny fusion.

Ported from the training notebook (IIITSURAT_MAJOR_PROJECT_UI22EC34.ipynb).

================================================================================
TODO: If you have customized the architecture after training, replace the
classes below with your exact model definition so state_dict keys match
your checkpoint (weights/final_model.pth).
================================================================================
"""

import torch
import torch.nn as nn
import timm


class CrossFusionAttention(nn.Module):
    """Fuses local (CNN) and global (Transformer) features adaptively."""

    def __init__(self, local_dim, global_dim, fusion_dim=512):
        super().__init__()
        self.proj_local = nn.Sequential(
            nn.Linear(local_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
        )
        self.proj_global = nn.Sequential(
            nn.Linear(global_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
        )
        self.attn = nn.MultiheadAttention(
            embed_dim=fusion_dim, num_heads=8, dropout=0.1, batch_first=True
        )
        self.gate = nn.Sequential(
            nn.Linear(fusion_dim * 2, fusion_dim),
            nn.Sigmoid(),
        )
        self.out_proj = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
        )

    def forward(self, local_feat, global_feat):
        l_proj = self.proj_local(local_feat).unsqueeze(1)
        g_proj = self.proj_global(global_feat).unsqueeze(1)
        attn_out, _ = self.attn(l_proj, g_proj, g_proj)
        attn_out = attn_out.squeeze(1)
        l_proj = l_proj.squeeze(1)
        combined = torch.cat([attn_out, l_proj], dim=-1)
        gate_val = self.gate(combined)
        fused = gate_val * attn_out + (1 - gate_val) * l_proj
        return self.out_proj(fused)


class HybridDualPathModel(nn.Module):
    """
    Path 1: EfficientNetV2-S → local spatial features
    Path 2: Swin-Tiny        → global contextual features
    Fusion: CrossFusionAttention
    """

    def __init__(self, num_classes=3, dropout=0.35, fusion_dim=512):
        super().__init__()

        self.local_encoder = timm.create_model(
            "tf_efficientnetv2_s",
            pretrained=False,
            num_classes=0,
            global_pool="avg",
        )
        local_dim = self.local_encoder.num_features

        self.global_encoder = timm.create_model(
            "swin_tiny_patch4_window7_224",
            pretrained=False,
            num_classes=0,
            global_pool="avg",
        )
        global_dim = self.global_encoder.num_features

        self.fusion = CrossFusionAttention(local_dim, global_dim, fusion_dim)

        self.classifier = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(128, num_classes),
        )

        self.aux_local = nn.Linear(local_dim, num_classes)
        self.aux_global = nn.Linear(global_dim, num_classes)

    def forward(self, x, return_features=False):
        local_feat = self.local_encoder(x)
        global_feat = self.global_encoder(x)
        fused = self.fusion(local_feat, global_feat)
        logits = self.classifier(fused)

        if return_features:
            return logits, fused

        if self.training:
            aux_l = self.aux_local(local_feat)
            aux_g = self.aux_global(global_feat)
            return logits, aux_l, aux_g

        return logits
