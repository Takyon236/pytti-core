"""
Modern Configuration Schema for PyTTI
Extends original config with support for modern AI models

Backward compatible with original config while adding new options
"""

from dataclasses import MISSING
from functools import partial
from typing import Optional, Literal
from attrs import define, field
from hydra.core.config_store import ConfigStore

# Import model registries
from pytti.model_loader import ModelRegistry


def check_input_against_list(attribute, value, valid_values):
    if value not in valid_values:
        raise ValueError(
            f"{value} is not a valid input for {attribute.name}. Valid inputs are {valid_values}"
        )


@define(auto_attribs=True)
class AudioFilterConfig:
    """Audio filter configuration (unchanged from original)"""
    variable_name: str = ""
    f_center: int = -1
    f_width: int = -1
    order: int = 5


@define(auto_attribs=True)
class ModernConfigSchema:
    """
    Modern PyTTI Configuration Schema
    Supports both legacy and modern models
    """

    #############
    ## Prompts ##
    #############
    scenes: str = ""
    scene_prefix: str = ""
    scene_suffix: str = ""

    direct_image_prompts: str = ""
    init_image: str = ""
    direct_init_weight: str = ""
    semantic_init_weight: str = ""

    ##################################
    ## Image Models (MODERNIZED) ##
    ##################################

    image_model: str = field(default="Stable Diffusion XL")

    @image_model.validator
    def check(self, attribute, value):
        valid_models = [
            # Modern diffusion models
            "Stable Diffusion 1.5",
            "Stable Diffusion XL",
            "SDXL Turbo",
            "Stable Diffusion 3.5",
            "Flux Schnell",
            "Flux Dev",
            # Legacy models (for backward compatibility)
            "VQGAN",
            "Limited Palette",
            "Unlimited Palette",
        ]
        check_input_against_list(attribute, value, valid_models)

    # Diffusion model specific settings
    diffusion_model_id: str = field(default="sdxl")  # Model ID from ModelRegistry
    diffusion_steps: int = field(default=1)  # Steps per CLIP optimization (1 for latent opt)
    guidance_scale: float = field(default=7.5)  # For diffusion guidance (if used)

    # Legacy VQGAN settings (kept for backward compatibility)
    vqgan_model: str = field(default="sflckr")

    @vqgan_model.validator
    def check(self, attribute, value):
        from pytti.image_models.vqgan import VQGAN_MODEL_NAMES
        check_input_against_list(attribute, value, valid_values=VQGAN_MODEL_NAMES)

    ##################################
    ## Depth Models (NEW) ##
    ##################################

    depth_model: str = field(default="depth_anything_v2")

    @depth_model.validator
    def check(self, attribute, value):
        valid_depth_models = [
            "depth_anything_v2",  # Recommended
            "marigold",  # High quality
            "adabins",  # Legacy
        ]
        check_input_against_list(attribute, value, valid_depth_models)

    depth_model_size: str = field(default="base")

    @depth_model_size.validator
    def check(self, attribute, value):
        valid_sizes = ["small", "base", "large"]
        check_input_against_list(attribute, value, valid_sizes)

    ##################################
    ## Segmentation (NEW) ##
    ##################################

    use_ai_rotoscoping: bool = False  # Whether to use SAM 2 for rotoscoping
    segmentation_model: str = field(default="sam2_base")

    @segmentation_model.validator
    def check(self, attribute, value):
        valid_seg_models = ["sam2_tiny", "sam2_small", "sam2_base", "sam2_large"]
        check_input_against_list(attribute, value, valid_seg_models)

    ##################################
    ## Animation Mode ##
    ##################################

    animation_mode: str = field(default="off")

    @animation_mode.validator
    def check(self, attribute, value):
        check_input_against_list(
            attribute, value, valid_values=["off", "2D", "3D", "Video Source"]
        )

    ##################################
    ## Image Dimensions ##
    ##################################

    width: int = 512  # Increased from 180 (SD works better with larger sizes)
    height: int = 512  # Increased from 112

    steps_per_scene: int = 100
    steps_per_frame: int = 50
    interpolation_steps: int = 0

    learning_rate: Optional[float] = None  # Auto-set based on image model
    reset_lr_each_frame: bool = True
    seed: str = "${now:%f}"  # microsecond component of timestamp

    ##################################
    ## CLIP Settings ##
    ##################################

    cutouts: int = 40
    cut_pow: int = 2
    cutout_border: float = 0.25
    border_mode: str = field(default="clamp")

    @border_mode.validator
    def check(self, attribute, value):
        check_input_against_list(
            attribute, value, valid_values=["clamp", "mirror", "wrap", "black", "smear"]
        )

    # Modern CLIP options
    use_modern_clip: bool = True  # Use SigLIP/EVA-CLIP instead of old CLIP
    clip_model: str = field(default="siglip")  # siglip, eva_clip, or openai_clip

    ##################################
    ## Camera (3D Mode) ##
    ##################################

    field_of_view: int = 60
    near_plane: int = 1
    far_plane: int = 10000

    ##################################
    ## Induced Motion ##
    ##################################

    input_audio: str = ""
    input_audio_offset: float = 0
    input_audio_filters: Optional[AudioFilterConfig] = None

    translate_x: str = "0"
    translate_y: str = "0"
    translate_z_3d: str = "0"
    rotate_3d: str = "[1, 0, 0, 0]"
    rotate_2d: str = "0"
    zoom_x_2d: str = "0"
    zoom_y_2d: str = "0"

    sampling_mode: str = field(default="bicubic")

    @sampling_mode.validator
    def check(self, attribute, value):
        check_input_against_list(
            attribute, value, valid_values=["nearest", "bilinear", "bicubic"]
        )

    infill_mode: str = field(default="wrap")

    @infill_mode.validator
    def check(self, attribute, value):
        check_input_against_list(
            attribute, value, valid_values=["mirror", "wrap", "black", "smear"]
        )

    pre_animation_steps: int = 100
    lock_camera: bool = True

    ##################################
    ## Limited Palette (Legacy) ##
    ##################################

    pixel_size: int = 4
    smoothing_weight: float = 0.02
    random_initial_palette: bool = False
    palette_size: int = 6
    palettes: int = 9
    gamma: int = 1
    hdr_weight: float = 0.01
    palette_normalization_weight: float = 0.2
    show_palette: bool = False
    target_palette: str = ""
    lock_palette: bool = False

    ##################################
    ## Video Output ##
    ##################################

    frames_per_second: int = 12

    ##################################
    ## Stabilization ##
    ##################################

    direct_stabilization_weight: str = ""
    semantic_stabilization_weight: str = ""
    depth_stabilization_weight: str = ""
    edge_stabilization_weight: str = ""
    flow_stabilization_weight: str = ""

    ##################################
    ## Video Source Mode ##
    ##################################

    video_path: str = ""
    frame_stride: int = 1
    reencode_each_frame: bool = True
    flow_long_term_samples: int = 1

    ##################################
    ## CLIP Models (Legacy) ##
    ##################################

    ViTB32: bool = True
    ViTB16: bool = False
    ViTL14: bool = False
    RN50: bool = False
    RN101: bool = False
    RN50x4: bool = False
    RN50x16: bool = False
    RN50x64: bool = False

    ##################################
    ## Output Settings ##
    ##################################

    file_namespace: str = "default"
    allow_overwrite: bool = False
    display_every: int = 50
    clear_every: int = 0
    display_scale: int = 1
    save_every: int = 50

    backups: int = 0
    show_graphs: bool = False
    approximate_vram_usage: bool = False
    use_tensorboard: Optional[bool] = False

    ##################################
    ## Model Paths ##
    ##################################

    # Directory for model cache
    models_parent_dir: str = "${user_cache:}"

    ##################################
    ## Performance ##
    ##################################

    gradient_accumulation_steps: int = 1

    # New performance options
    use_fp16: bool = True  # Use half precision (faster, less VRAM)
    compile_models: bool = False  # Use torch.compile (PyTorch 2.0+)
    enable_xformers: bool = True  # Use xformers for memory efficiency


def register_modern_config():
    """Register modern config schema with Hydra"""
    cs = ConfigStore.instance()
    cs.store(name="modern_config_schema", node=ModernConfigSchema)


# Auto-register
register_modern_config()


# Example configs for different use cases
@define(auto_attribs=True)
class SDXLConfig(ModernConfigSchema):
    """Preset for Stable Diffusion XL"""
    image_model: str = "Stable Diffusion XL"
    diffusion_model_id: str = "sdxl"
    width: int = 1024
    height: int = 1024
    use_fp16: bool = True


@define(auto_attribs=True)
class FluxConfig(ModernConfigSchema):
    """Preset for Flux"""
    image_model: str = "Flux Schnell"
    diffusion_model_id: str = "flux_schnell"
    width: int = 1024
    height: int = 1024
    use_fp16: bool = True


@define(auto_attribs=True)
class AIRotoscopeConfig(ModernConfigSchema):
    """Preset for AI-powered rotoscoping"""
    image_model: str = "Stable Diffusion XL"
    animation_mode: str = "Video Source"
    use_ai_rotoscoping: bool = True
    segmentation_model: str = "sam2_base"
    depth_model: str = "depth_anything_v2"
    reencode_each_frame: bool = False


@define(auto_attribs=True)
class HighQuality3DConfig(ModernConfigSchema):
    """Preset for high-quality 3D animations"""
    image_model: str = "Stable Diffusion XL"
    animation_mode: str = "3D"
    depth_model: str = "depth_anything_v2"  # or "marigold" for highest quality
    depth_model_size: str = "large"
    width: int = 1024
    height: int = 1024
    steps_per_frame: int = 100


def register_presets():
    """Register preset configurations"""
    cs = ConfigStore.instance()
    cs.store(group="preset", name="sdxl", node=SDXLConfig)
    cs.store(group="preset", name="flux", node=FluxConfig)
    cs.store(group="preset", name="ai_rotoscope", node=AIRotoscopeConfig)
    cs.store(group="preset", name="high_quality_3d", node=HighQuality3DConfig)


register_presets()
