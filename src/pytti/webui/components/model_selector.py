"""
Model selector component for PyTTI Web UI

Provides dropdowns and controls for selecting:
- Diffusion models (SDXL, Flux, etc.)
- Depth models (Depth-Anything-V2, etc.)
- CLIP models (SigLIP, OpenCLIP, etc.)
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

import gradio as gr
from loguru import logger

from pytti.model_loader import ModelRegistry, ModelType


class ModelSelector:
    """Model selection UI component"""

    @staticmethod
    def get_diffusion_model_choices() -> List[str]:
        """Get list of available diffusion models"""
        models = ModelRegistry.list_models_by_type(ModelType.DIFFUSION)
        return [model.name for model in models]

    @staticmethod
    def get_diffusion_model_info(model_name: str) -> Dict[str, Any]:
        """Get info about diffusion model"""
        models = ModelRegistry.list_models_by_type(ModelType.DIFFUSION)
        for model in models:
            if model.name == model_name:
                return {
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "recommended_size": model.metadata.get("recommended_size", "1024x1024"),
                    "speed": model.metadata.get("speed", "medium"),
                }
        return {}

    @staticmethod
    def get_depth_model_choices() -> List[str]:
        """Get list of available depth models"""
        return [
            "Depth-Anything-V2 (Recommended)",
            "Marigold (High Quality)",
            "AdaBins (Legacy)",
        ]

    @staticmethod
    def get_clip_model_choices() -> List[str]:
        """Get list of available CLIP models"""
        return [
            "SigLIP (Recommended)",
            "OpenCLIP ViT-H-14",
            "OpenCLIP ViT-L-14",
            "OpenAI CLIP ViT-L/14",
        ]

    @staticmethod
    def create_model_selector() -> Dict[str, Any]:
        """
        Create model selector UI components

        Returns:
            Dictionary of Gradio components
        """
        components = {}

        with gr.Group():
            gr.Markdown("### 🎨 Model Selection")

            # Diffusion model selector
            with gr.Row():
                diffusion_model = gr.Dropdown(
                    label="Image Model",
                    choices=ModelSelector.get_diffusion_model_choices(),
                    value="Stable Diffusion XL",
                    info="Choose the AI model for image generation",
                )
                components["diffusion_model"] = diffusion_model

            # Model info display
            model_info = gr.Markdown(
                value=ModelSelector._format_model_info("Stable Diffusion XL"),
                visible=True,
            )
            components["model_info"] = model_info

            # Advanced model settings (collapsible)
            with gr.Accordion("Advanced Model Settings", open=False):

                with gr.Row():
                    # Depth model (for 3D animations)
                    depth_model = gr.Dropdown(
                        label="Depth Model",
                        choices=ModelSelector.get_depth_model_choices(),
                        value="Depth-Anything-V2 (Recommended)",
                        info="Used for 3D camera movements",
                    )
                    components["depth_model"] = depth_model

                    depth_model_size = gr.Radio(
                        label="Depth Model Size",
                        choices=["small", "base", "large"],
                        value="base",
                        info="Larger = more accurate but slower",
                    )
                    components["depth_model_size"] = depth_model_size

                with gr.Row():
                    # CLIP model
                    clip_model = gr.Dropdown(
                        label="CLIP Model",
                        choices=ModelSelector.get_clip_model_choices(),
                        value="SigLIP (Recommended)",
                        info="Used for prompt guidance",
                    )
                    components["clip_model"] = clip_model

                    # Precision
                    use_fp16 = gr.Checkbox(
                        label="Use FP16 (Half Precision)",
                        value=True,
                        info="Reduces VRAM usage by 50%",
                    )
                    components["use_fp16"] = use_fp16

                with gr.Row():
                    enable_xformers = gr.Checkbox(
                        label="Enable xformers",
                        value=True,
                        info="Memory-efficient attention (requires xformers installed)",
                    )
                    components["enable_xformers"] = enable_xformers

            # Update model info when diffusion model changes
            diffusion_model.change(
                fn=ModelSelector._format_model_info,
                inputs=[diffusion_model],
                outputs=[model_info],
            )

        return components

    @staticmethod
    def _format_model_info(model_name: str) -> str:
        """Format model information as markdown"""
        info = ModelSelector.get_diffusion_model_info(model_name)

        if not info:
            return ""

        return f"""
**{info['name']}**

{info.get('description', '')}

- **Recommended Size:** {info.get('recommended_size', 'N/A')}
- **Speed:** {info.get('speed', 'N/A')}
"""


def create_preset_selector() -> Dict[str, Any]:
    """
    Create preset selector UI

    Returns:
        Dictionary of Gradio components
    """
    components = {}

    with gr.Group():
        gr.Markdown("### ⚡ Quick Presets")

        preset = gr.Radio(
            label="Choose a Preset",
            choices=[
                "Custom",
                "SDXL Default (Recommended)",
                "Flux Fast",
                "High Quality 3D",
                "Fast Test",
            ],
            value="SDXL Default (Recommended)",
            info="Load pre-configured settings",
        )
        components["preset"] = preset

        preset_info = gr.Markdown(
            value=_get_preset_info("SDXL Default (Recommended)"),
            visible=True,
        )
        components["preset_info"] = preset_info

        # Update info when preset changes
        preset.change(
            fn=_get_preset_info,
            inputs=[preset],
            outputs=[preset_info],
        )

    return components


def _get_preset_info(preset_name: str) -> str:
    """Get preset information"""
    presets = {
        "Custom": "Configure all parameters manually",
        "SDXL Default (Recommended)": """
**Stable Diffusion XL at 1024x1024**

Balanced quality and speed. Great for most use cases.

- Model: SDXL
- Resolution: 1024x1024
- Steps: 200
- Learning Rate: 0.1
""",
        "Flux Fast": """
**Flux Schnell for Quick Generation**

Fast, high-quality results in fewer steps.

- Model: Flux Schnell
- Resolution: 1024x1024
- Steps: 100
- Learning Rate: 0.15
""",
        "High Quality 3D": """
**Maximum Quality 3D Animation**

Best for 3D camera movements and depth effects.

- Model: SDXL
- Resolution: 1024x1024
- Steps: 300
- Depth: Large model
- Optimized for 3D
""",
        "Fast Test": """
**Quick Testing Mode**

Fast iterations for testing prompts.

- Model: SDXL Turbo
- Resolution: 512x512
- Steps: 100
- Good for experimentation
""",
    }

    return presets.get(preset_name, "")
