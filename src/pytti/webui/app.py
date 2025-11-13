#!/usr/bin/env python3
"""
PyTTI Modern - Gradio Web UI

Browser-based interface for PyTTI's AI video generation.
Provides intuitive controls for text-to-image/video, 3D animation, and AI rotoscoping.

Usage:
    python -m pytti.webui.app
    python -m pytti.webui.app --share  # Create shareable link
    python -m pytti.webui.app --port 7860
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import gradio as gr
import torch
from loguru import logger

# Import PyTTI components
from pytti.model_loader import ModelRegistry, get_model_loader
from pytti.webui.tabs.generate import create_generate_tab
from pytti.webui.components.shared_state import SharedState
from pytti.webui.components.vram_monitor import VRAMMonitor
from pytti.webui.components.error_display import ErrorDisplay, StatusFormatter


class PyTTIWebUI:
    """Main PyTTI Gradio Web UI Application"""

    def __init__(self, device: Optional[torch.device] = None):
        """
        Initialize PyTTI Web UI

        Args:
            device: PyTorch device (cuda/cpu)
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.device = device
        self.shared_state = SharedState(device=device)

        logger.info(f"PyTTI Web UI initialized on {device}")

        # Check GPU memory if available
        if device.type == "cuda":
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU Memory: {memory_gb:.1f} GB")

    def build_ui(self) -> gr.Blocks:
        """
        Build the Gradio interface

        Returns:
            Gradio Blocks app
        """
        # Custom CSS for PyTTI branding
        custom_css = """
        .gradio-container {
            font-family: 'Inter', sans-serif;
        }
        .pytti-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .pytti-header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }
        .pytti-header p {
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }
        .parameter-group {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .preview-container {
            border: 2px solid #667eea;
            border-radius: 10px;
            padding: 10px;
            background: #f9f9f9;
        }
        """

        with gr.Blocks(
            title="PyTTI Modern - AI Video Generation",
            theme=gr.themes.Soft(),
            css=custom_css
        ) as app:

            # Header
            with gr.Row():
                gr.HTML("""
                <div class="pytti-header">
                    <h1>🎨 PyTTI Modern</h1>
                    <p>AI-Powered Video Generation with 3D Effects & Rotoscoping</p>
                </div>
                """)

            # Info banner and system status
            with gr.Row():
                with gr.Column(scale=3):
                    gr.Markdown("""
                    **PyTTI** uses iterative CLIP-guided optimization to create unique, evolving visuals.
                    Unlike one-shot generation, PyTTI refines over 200+ steps for distinctive results.

                    🎯 **Quick Start:** Select a preset, enter your prompt, and click Generate!
                    """)

                with gr.Column(scale=1):
                    # System status sidebar
                    gr.Markdown("### 📊 System Status")

                    # VRAM Monitor
                    vram_display = gr.Textbox(
                        label="GPU Memory",
                        value=VRAMMonitor.format_vram_display(),
                        interactive=False,
                        lines=3,
                        elem_id="vram_status"
                    )

                    with gr.Row():
                        refresh_vram_btn = gr.Button("🔄 Refresh", size="sm", scale=1)
                        clear_cache_btn = gr.Button("🧹 Clear Cache", size="sm", scale=1)

                    # Wire up VRAM monitor buttons
                    def refresh_vram():
                        return VRAMMonitor.format_vram_display()

                    def clear_vram_cache():
                        try:
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                                from pytti.managers import ClipManager
                                try:
                                    ClipManager.get_instance().cleanup()
                                except Exception:
                                    pass
                                return VRAMMonitor.format_vram_display()
                            else:
                                return VRAMMonitor.format_vram_display()
                        except Exception as e:
                            logger.error(f"Cache clear error: {e}")
                            return VRAMMonitor.format_vram_display()

                    refresh_vram_btn.click(fn=refresh_vram, outputs=vram_display)
                    clear_cache_btn.click(fn=clear_vram_cache, outputs=vram_display)

            # Main tabbed interface
            with gr.Tabs() as tabs:

                # Tab 1: Text-to-Image/Video Generation
                with gr.Tab("🖼️ Generate", elem_id="generate"):
                    generate_interface = create_generate_tab(self.shared_state)

                # Tab 2: 3D Animation (Coming Soon)
                with gr.Tab("🎬 3D Animation", elem_id="animation_3d"):
                    gr.Markdown("""
                    ## 3D Animation Controls

                    **Coming in Phase 2!**

                    This tab will feature:
                    - Depth-aware camera movements
                    - Parametric motion controls (translate X/Y/Z, rotate)
                    - Real-time 3D preview
                    - FOV and perspective controls
                    - Smooth camera paths adapting to scene depth
                    """)

                # Tab 3: AI Rotoscoping (Coming Soon)
                with gr.Tab("🎭 AI Rotoscoping", elem_id="rotoscope"):
                    gr.Markdown("""
                    ## AI-Powered Video Segmentation

                    **Coming in Phase 3!**

                    This tab will feature:
                    - Video upload and frame scrubbing
                    - SAM 2 click-and-track interface
                    - Point/box selection tools
                    - Automatic mask propagation
                    - Transformation prompts
                    - Frame-by-frame refinement
                    """)

                # Tab 4: Gallery (Coming Soon)
                with gr.Tab("🖼️ Gallery", elem_id="gallery"):
                    gr.Markdown("""
                    ## Generation Gallery

                    **Coming in Phase 2!**

                    This tab will feature:
                    - Grid view of all generations
                    - Metadata viewer (prompts, settings)
                    - Re-run with same settings
                    - Compare multiple generations
                    - Export and share
                    """)

            # Footer
            with gr.Row():
                gr.Markdown("""
                ---
                **PyTTI Modern** - Built with ❤️ by the PyTTI community
                | [GitHub](https://github.com/pytti-tools/pytti-core)
                | [Documentation](https://github.com/pytti-tools/pytti-core/blob/main/MODERNIZATION_README.md)
                | [Report Issues](https://github.com/pytti-tools/pytti-core/issues)
                """)

        return app

    def launch(
        self,
        share: bool = False,
        server_port: int = 7860,
        server_name: str = "0.0.0.0",
        inbrowser: bool = True,
    ):
        """
        Launch the Gradio web UI

        Args:
            share: Create shareable link (for remote access)
            server_port: Port to run on
            server_name: Server address
            inbrowser: Open browser automatically
        """
        app = self.build_ui()

        logger.info(f"Launching PyTTI Web UI on http://{server_name}:{server_port}")

        if share:
            logger.info("Creating shareable link (may take a moment)...")

        app.launch(
            share=share,
            server_port=server_port,
            server_name=server_name,
            inbrowser=inbrowser,
            show_error=True,
            show_api=False,  # Disable API docs to avoid schema serialization issues
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PyTTI Modern Web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch locally
  python -m pytti.webui.app

  # Create shareable link
  python -m pytti.webui.app --share

  # Custom port
  python -m pytti.webui.app --port 8080

  # CPU mode (no GPU)
  python -m pytti.webui.app --cpu
        """
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="Create shareable Gradio link (for remote access)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Server port (default: 7860)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU mode (no GPU)"
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )

    args = parser.parse_args()

    # Setup device
    if args.cpu:
        device = torch.device("cpu")
        logger.info("Running in CPU mode")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cpu":
            logger.warning("CUDA not available, using CPU mode")

    # Create and launch UI
    ui = PyTTIWebUI(device=device)

    try:
        ui.launch(
            share=args.share,
            server_port=args.port,
            server_name=args.host,
            inbrowser=not args.no_browser,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down PyTTI Web UI...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to launch UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
