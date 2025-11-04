"""
Text-to-Image/Video Generation Tab for PyTTI Web UI

Main interface for PyTTI's iterative CLIP-guided generation.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import threading

import gradio as gr
import torch
import numpy as np
from PIL import Image
from loguru import logger

from pytti.webui.components.shared_state import SharedState
from pytti.webui.components.model_selector import ModelSelector, create_preset_selector
from pytti.webui.components.parameters import (
    create_prompt_input,
    create_basic_parameters,
    create_clip_parameters,
    create_advanced_parameters,
    load_preset_values,
)
from pytti.webui.utils.generation import generate_image


def create_generate_tab(shared_state: SharedState) -> Dict[str, Any]:
    """
    Create the main generation tab

    Args:
        shared_state: Shared application state

    Returns:
        Dictionary of UI components
    """
    components = {}

    with gr.Row():
        # Left column: Controls
        with gr.Column(scale=1):

            # Preset selector
            preset_components = create_preset_selector()
            components.update(preset_components)

            # Model selector
            model_components = ModelSelector.create_model_selector()
            components.update(model_components)

            # Prompt input
            prompt_components = create_prompt_input()
            components.update(prompt_components)

            # Basic parameters
            basic_param_components = create_basic_parameters()
            components.update(basic_param_components)

            # CLIP parameters
            clip_param_components = create_clip_parameters()
            components.update(clip_param_components)

            # Advanced parameters
            advanced_param_components = create_advanced_parameters()
            components.update(advanced_param_components)

            # Generate button
            with gr.Row():
                generate_btn = gr.Button(
                    "🎨 Generate",
                    variant="primary",
                    size="lg",
                    scale=2,
                )
                components["generate_btn"] = generate_btn

                stop_btn = gr.Button(
                    "⏹️ Stop",
                    variant="stop",
                    size="lg",
                    scale=1,
                )
                components["stop_btn"] = stop_btn

        # Right column: Preview and output
        with gr.Column(scale=1):

            with gr.Group(elem_classes="preview-container"):
                gr.Markdown("### 🖼️ Preview")

                # Image preview
                image_output = gr.Image(
                    label="Generated Image",
                    type="pil",
                    interactive=False,
                    height=512,
                )
                components["image_output"] = image_output

                # Progress bar
                progress_bar = gr.Progress()

                # Generation info
                generation_info = gr.Markdown(
                    value="**Ready to generate!**\n\nSelect a preset and enter your prompt.",
                    visible=True,
                )
                components["generation_info"] = generation_info

                # Step counter
                step_counter = gr.Textbox(
                    label="Progress",
                    value="Not started",
                    interactive=False,
                )
                components["step_counter"] = step_counter

            # Output actions
            with gr.Group():
                gr.Markdown("### 💾 Output")

                with gr.Row():
                    download_btn = gr.Button("⬇️ Download", size="sm")
                    components["download_btn"] = download_btn

                    save_to_gallery_btn = gr.Button("📁 Save to Gallery", size="sm")
                    components["save_to_gallery_btn"] = save_to_gallery_btn

                # Output file info
                output_path_display = gr.Textbox(
                    label="Saved to",
                    value="",
                    interactive=False,
                )
                components["output_path_display"] = output_path_display

    # Wire up the generation logic
    def on_generate_click(
        preset,
        diffusion_model,
        depth_model,
        depth_model_size,
        clip_model,
        use_fp16,
        enable_xformers,
        prompt,
        negative_prompt,
        width,
        height,
        steps_per_scene,
        learning_rate,
        cutouts,
        cut_pow,
        ema_val,
        animation_mode,
        frames,
        steps_per_frame,
        save_every,
        file_namespace,
        seed,
    ):
        """Handle generate button click"""

        # Validate prompt
        if not prompt or prompt.strip() == "":
            return (
                None,
                "❌ **Error:** Please enter a prompt!",
                "Error: No prompt",
                "",
            )

        # Build configuration from UI inputs
        config = {
            "diffusion_model": diffusion_model,
            "depth_model": depth_model,
            "depth_model_size": depth_model_size,
            "clip_model": clip_model,
            "use_fp16": use_fp16,
            "enable_xformers": enable_xformers,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": int(width),
            "height": int(height),
            "steps_per_scene": int(steps_per_scene),
            "learning_rate": float(learning_rate),
            "cutouts": int(cutouts),
            "cut_pow": float(cut_pow),
            "ema_val": float(ema_val),
            "animation_mode": animation_mode,
            "frames": int(frames) if animation_mode != "Off" else 1,
            "steps_per_frame": int(steps_per_frame) if animation_mode != "Off" else 0,
            "save_every": int(save_every),
            "file_namespace": file_namespace,
            "seed": int(seed),
        }

        logger.info(f"Starting generation with config: {config}")

        # Start generation
        try:
            result_image, output_path, status_message = generate_image(
                config=config,
                shared_state=shared_state,
                progress_callback=progress_bar,
            )

            if result_image is None:
                return (
                    None,
                    f"❌ **Error:** {status_message}",
                    "Generation failed",
                    "",
                )

            # Success!
            info_text = f"""
✅ **Generation Complete!**

**Prompt:** {prompt[:100]}...

**Settings:**
- Model: {diffusion_model}
- Resolution: {width}x{height}
- Steps: {steps_per_scene}
- Learning Rate: {learning_rate}
- Cutouts: {cutouts}
"""

            return (
                result_image,
                info_text,
                f"Completed {steps_per_scene} steps",
                str(output_path),
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return (
                None,
                f"❌ **Error:** {str(e)}",
                "Generation failed",
                "",
            )

    # Connect generate button
    generate_btn.click(
        fn=on_generate_click,
        inputs=[
            components["preset"],
            components["diffusion_model"],
            components["depth_model"],
            components["depth_model_size"],
            components["clip_model"],
            components["use_fp16"],
            components["enable_xformers"],
            components["prompt"],
            components["negative_prompt"],
            components["width"],
            components["height"],
            components["steps_per_scene"],
            components["learning_rate"],
            components["cutouts"],
            components["cut_pow"],
            components["ema_val"],
            components["animation_mode"],
            components["frames"],
            components["steps_per_frame"],
            components["save_every"],
            components["file_namespace"],
            components["seed"],
        ],
        outputs=[
            components["image_output"],
            components["generation_info"],
            components["step_counter"],
            components["output_path_display"],
        ],
    )

    # Stop button
    def on_stop_click():
        """Handle stop button click"""
        shared_state.request_stop()
        return "⏹️ Stopping generation..."

    stop_btn.click(
        fn=on_stop_click,
        outputs=[components["step_counter"]],
    )

    # Load preset values when preset changes
    def on_preset_change(preset_name):
        """Load preset values"""
        if preset_name == "Custom":
            return {}

        values = load_preset_values(preset_name)
        return [
            values.get("width", 1024),
            values.get("height", 1024),
            values.get("steps_per_scene", 200),
            values.get("learning_rate", 0.1),
            values.get("cutouts", 40),
            values.get("cut_pow", 2.0),
            values.get("ema_val", 0.99),
            values.get("animation_mode", "Off"),
        ]

    components["preset"].change(
        fn=on_preset_change,
        inputs=[components["preset"]],
        outputs=[
            components["width"],
            components["height"],
            components["steps_per_scene"],
            components["learning_rate"],
            components["cutouts"],
            components["cut_pow"],
            components["ema_val"],
            components["animation_mode"],
        ],
    )

    return components
