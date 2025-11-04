"""
VRAM Monitoring Component for PyTTI Web UI

Provides real-time GPU memory usage monitoring and display.
"""

from typing import Dict, Any, Optional
import torch
import gradio as gr


class VRAMMonitor:
    """
    Monitor and display VRAM usage in the UI.

    Provides:
    - Current VRAM usage
    - Available VRAM
    - Usage percentage
    - Formatted display strings
    """

    @staticmethod
    def get_vram_stats() -> Dict[str, Any]:
        """
        Get current VRAM statistics.

        Returns:
            Dict with VRAM stats (all values in MB)
        """
        if not torch.cuda.is_available():
            return {
                "device": "CPU",
                "available": False,
                "total_mb": 0,
                "used_mb": 0,
                "free_mb": 0,
                "percent_used": 0,
                "status": "CPU Mode (No GPU)",
                "color": "gray",
            }

        try:
            # Get VRAM stats
            allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
            reserved = torch.cuda.memory_reserved() / 1024 / 1024    # MB
            total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024

            used = reserved  # Reserved is a better indicator of actual usage
            free = total - used
            percent = (used / total) * 100 if total > 0 else 0

            # Determine status color
            if percent < 50:
                color = "green"
                status = "✅ Good"
            elif percent < 75:
                color = "yellow"
                status = "⚠️ Moderate"
            elif percent < 90:
                color = "orange"
                status = "⚠️ High"
            else:
                color = "red"
                status = "🔴 Critical"

            device_name = torch.cuda.get_device_name(0)

            return {
                "device": device_name,
                "available": True,
                "total_mb": total,
                "used_mb": used,
                "free_mb": free,
                "percent_used": percent,
                "status": status,
                "color": color,
            }

        except Exception as e:
            return {
                "device": "GPU",
                "available": True,
                "total_mb": 0,
                "used_mb": 0,
                "free_mb": 0,
                "percent_used": 0,
                "status": f"Error: {str(e)}",
                "color": "red",
            }

    @staticmethod
    def format_vram_display() -> str:
        """
        Format VRAM stats for display in UI.

        Returns:
            Formatted string with VRAM information
        """
        stats = VRAMMonitor.get_vram_stats()

        if not stats["available"]:
            return "💻 CPU Mode (No GPU detected)"

        return (
            f"🎮 {stats['device']}\n"
            f"📊 VRAM: {stats['used_mb']:.0f} / {stats['total_mb']:.0f} MB "
            f"({stats['percent_used']:.1f}%)\n"
            f"📈 Status: {stats['status']}"
        )

    @staticmethod
    def create_vram_display() -> gr.Textbox:
        """
        Create a Gradio component for VRAM display.

        Returns:
            Gradio Textbox component with VRAM stats
        """
        return gr.Textbox(
            label="GPU Memory Status",
            value=VRAMMonitor.format_vram_display(),
            interactive=False,
            lines=3,
        )

    @staticmethod
    def create_vram_monitor_ui() -> gr.Column:
        """
        Create a complete VRAM monitoring UI component.

        Returns:
            Gradio Column with VRAM monitoring widgets
        """
        with gr.Column() as vram_col:
            gr.Markdown("### 🎮 GPU Memory Monitor")

            vram_display = gr.Textbox(
                label="VRAM Usage",
                value=VRAMMonitor.format_vram_display(),
                interactive=False,
                lines=3,
            )

            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", size="sm")
                clear_cache_btn = gr.Button("🧹 Clear Cache", size="sm")

            status_msg = gr.Textbox(
                label="Status",
                value="",
                interactive=False,
                visible=False,
            )

            # Wire up refresh button
            def refresh_vram():
                return VRAMMonitor.format_vram_display(), gr.update(visible=False)

            refresh_btn.click(
                fn=refresh_vram,
                outputs=[vram_display, status_msg]
            )

            # Wire up clear cache button
            def clear_cache():
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        # Also cleanup CLIP if available
                        try:
                            from pytti.managers import ClipManager
                            ClipManager.get_instance().cleanup()
                        except Exception:
                            pass

                        return (
                            VRAMMonitor.format_vram_display(),
                            gr.update(value="✅ Cache cleared!", visible=True)
                        )
                    else:
                        return (
                            VRAMMonitor.format_vram_display(),
                            gr.update(value="ℹ️ No GPU cache to clear", visible=True)
                        )
                except Exception as e:
                    return (
                        VRAMMonitor.format_vram_display(),
                        gr.update(value=f"❌ Error: {str(e)}", visible=True)
                    )

            clear_cache_btn.click(
                fn=clear_cache,
                outputs=[vram_display, status_msg]
            )

        return vram_col


def get_vram_info() -> str:
    """
    Quick function to get VRAM info as string.

    Returns:
        Formatted VRAM information
    """
    return VRAMMonitor.format_vram_display()
