"""
Parameter controls for PyTTI Web UI

Provides sliders and inputs for controlling:
- Image dimensions
- Generation steps
- Learning rate
- CLIP guidance
- Output settings
"""

from __future__ import annotations

from typing import Dict, Any

import gradio as gr


def create_basic_parameters() -> Dict[str, Any]:
    """
    Create basic parameter controls

    Returns:
        Dictionary of Gradio components
    """
    components = {}

    with gr.Group():
        gr.Markdown("### 📐 Image Settings")

        with gr.Row():
            width = gr.Slider(
                label="Width",
                minimum=256,
                maximum=2048,
                step=64,
                value=1024,
                info="Image width in pixels",
            )
            components["width"] = width

            height = gr.Slider(
                label="Height",
                minimum=256,
                maximum=2048,
                step=64,
                value=1024,
                info="Image height in pixels",
            )
            components["height"] = height

        # Quick size presets
        with gr.Row():
            size_presets = gr.Radio(
                label="Quick Sizes",
                choices=[
                    "1024x1024 (Square)",
                    "1024x768 (Landscape)",
                    "768x1024 (Portrait)",
                    "1920x1080 (Full HD)",
                    "512x512 (Fast)",
                    "Custom",
                ],
                value="1024x1024 (Square)",
            )
            components["size_presets"] = size_presets

        # Update width/height when preset is selected
        def update_size_from_preset(preset):
            sizes = {
                "1024x1024 (Square)": (1024, 1024),
                "1024x768 (Landscape)": (1024, 768),
                "768x1024 (Portrait)": (768, 1024),
                "1920x1080 (Full HD)": (1920, 1080),
                "512x512 (Fast)": (512, 512),
                "Custom": (1024, 1024),
            }
            w, h = sizes.get(preset, (1024, 1024))
            return w, h

        size_presets.change(
            fn=update_size_from_preset,
            inputs=[size_presets],
            outputs=[width, height],
        )

    with gr.Group():
        gr.Markdown("### 🎯 Generation Settings")

        gr.Markdown("""
        **PyTTI uses iterative optimization** - not one-shot generation!
        More steps = more refinement and detail.
        """)

        steps_per_scene = gr.Slider(
            label="Steps per Scene",
            minimum=50,
            maximum=1000,
            step=10,
            value=200,
            info="Number of optimization steps (PyTTI's iterative refinement)",
        )
        components["steps_per_scene"] = steps_per_scene

        learning_rate = gr.Slider(
            label="Learning Rate",
            minimum=0.01,
            maximum=0.5,
            step=0.01,
            value=0.1,
            info="How fast the image changes (higher = faster changes)",
        )
        components["learning_rate"] = learning_rate

    return components


def create_clip_parameters() -> Dict[str, Any]:
    """
    Create CLIP guidance parameter controls

    Returns:
        Dictionary of Gradio components
    """
    components = {}

    with gr.Group():
        gr.Markdown("### 🔍 CLIP Guidance")

        gr.Markdown("""
        **CLIP guidance** creates PyTTI's distinctive aesthetic.
        More cutouts = stronger guidance but slower.
        """)

        with gr.Row():
            cutouts = gr.Slider(
                label="Cutouts",
                minimum=10,
                maximum=100,
                step=5,
                value=40,
                info="Number of image crops for CLIP analysis",
            )
            components["cutouts"] = cutouts

            cut_pow = gr.Slider(
                label="Cut Power",
                minimum=0.5,
                maximum=4.0,
                step=0.1,
                value=2.0,
                info="Focus on center (lower) vs edges (higher)",
            )
            components["cut_pow"] = cut_pow

    return components


def create_advanced_parameters() -> Dict[str, Any]:
    """
    Create advanced parameter controls (collapsible)

    Returns:
        Dictionary of Gradio components
    """
    components = {}

    with gr.Accordion("⚙️ Advanced Settings", open=False):

        # EMA settings
        with gr.Group():
            gr.Markdown("#### Temporal Smoothing")

            ema_val = gr.Slider(
                label="EMA Value",
                minimum=0.9,
                maximum=0.999,
                step=0.001,
                value=0.99,
                info="Exponential moving average for smooth transitions",
            )
            components["ema_val"] = ema_val

        # Animation settings
        with gr.Group():
            gr.Markdown("#### Animation")

            animation_mode = gr.Radio(
                label="Animation Mode",
                choices=["Off", "2D", "3D", "Video Source"],
                value="Off",
                info="Enable animation for video generation",
            )
            components["animation_mode"] = animation_mode

            with gr.Row(visible=False) as animation_controls:
                frames = gr.Number(
                    label="Total Frames",
                    value=100,
                    minimum=1,
                    maximum=10000,
                )
                components["frames"] = frames

                steps_per_frame = gr.Slider(
                    label="Steps per Frame",
                    minimum=10,
                    maximum=200,
                    step=5,
                    value=50,
                    info="Optimization steps for each frame",
                )
                components["steps_per_frame"] = steps_per_frame

            components["animation_controls"] = animation_controls

            # Show/hide animation controls based on mode
            def toggle_animation_controls(mode):
                return gr.update(visible=(mode != "Off"))

            animation_mode.change(
                fn=toggle_animation_controls,
                inputs=[animation_mode],
                outputs=[animation_controls],
            )

        # Output settings
        with gr.Group():
            gr.Markdown("#### Output")

            with gr.Row():
                save_every = gr.Number(
                    label="Save Every N Steps",
                    value=50,
                    minimum=1,
                    maximum=500,
                    info="Save intermediate results",
                )
                components["save_every"] = save_every

                file_namespace = gr.Textbox(
                    label="Output Name",
                    value="pytti_output",
                    info="Filename prefix for outputs",
                )
                components["file_namespace"] = file_namespace

        # Seed for reproducibility
        with gr.Group():
            gr.Markdown("#### Reproducibility")

            with gr.Row():
                seed = gr.Number(
                    label="Random Seed",
                    value=-1,
                    minimum=-1,
                    maximum=2**32 - 1,
                    info="-1 for random seed",
                )
                components["seed"] = seed

                random_seed_btn = gr.Button("🎲 Random Seed", size="sm")
                components["random_seed_btn"] = random_seed_btn

            # Generate random seed
            def generate_random_seed():
                import random
                return random.randint(0, 2**32 - 1)

            random_seed_btn.click(
                fn=generate_random_seed,
                outputs=[seed],
            )

    return components


def create_prompt_input() -> Dict[str, Any]:
    """
    Create prompt input UI

    Returns:
        Dictionary of Gradio components
    """
    components = {}

    with gr.Group():
        gr.Markdown("### ✍️ Prompt")

        prompt = gr.Textbox(
            label="Describe what you want to create",
            placeholder="a mystical forest at golden hour, ethereal lighting, highly detailed",
            lines=3,
            info="Be descriptive! PyTTI works best with detailed prompts.",
        )
        components["prompt"] = prompt

        # Example prompts
        with gr.Accordion("Example Prompts", open=False):
            example_prompts = [
                "a serene mountain landscape at sunset, cinematic lighting, oil painting style",
                "cyberpunk cityscape with neon lights, rain-soaked streets, blade runner aesthetic",
                "mystical underwater temple, bioluminescent plants, ethereal atmosphere",
                "floating islands in the sky, waterfalls, fantasy art, highly detailed",
                "abstract fractal patterns, vibrant colors, psychedelic art",
            ]

            for example in example_prompts:
                example_btn = gr.Button(f"📝 {example[:50]}...", size="sm")
                example_btn.click(
                    fn=lambda p=example: p,
                    outputs=[prompt],
                )

        # Negative prompt (optional)
        with gr.Accordion("Negative Prompt (Optional)", open=False):
            negative_prompt = gr.Textbox(
                label="What to avoid",
                placeholder="blurry, low quality, distorted",
                lines=2,
                info="Describe what you don't want in the image",
            )
            components["negative_prompt"] = negative_prompt

    return components


def load_preset_values(preset_name: str) -> Dict[str, Any]:
    """
    Load parameter values for a given preset

    Args:
        preset_name: Name of preset

    Returns:
        Dictionary of parameter values
    """
    presets = {
        "SDXL Default (Recommended)": {
            "width": 1024,
            "height": 1024,
            "steps_per_scene": 200,
            "learning_rate": 0.1,
            "cutouts": 40,
            "cut_pow": 2.0,
            "ema_val": 0.99,
            "animation_mode": "Off",
        },
        "Flux Fast": {
            "width": 1024,
            "height": 1024,
            "steps_per_scene": 100,
            "learning_rate": 0.15,
            "cutouts": 30,
            "cut_pow": 2.0,
            "ema_val": 0.99,
            "animation_mode": "Off",
        },
        "High Quality 3D": {
            "width": 1024,
            "height": 1024,
            "steps_per_scene": 300,
            "learning_rate": 0.08,
            "cutouts": 60,
            "cut_pow": 2.5,
            "ema_val": 0.995,
            "animation_mode": "3D",
        },
        "Fast Test": {
            "width": 512,
            "height": 512,
            "steps_per_scene": 100,
            "learning_rate": 0.15,
            "cutouts": 20,
            "cut_pow": 1.5,
            "ema_val": 0.99,
            "animation_mode": "Off",
        },
    }

    return presets.get(preset_name, presets["SDXL Default (Recommended)"])
