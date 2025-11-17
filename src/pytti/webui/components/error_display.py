"""
Error Display Component for PyTTI Web UI

Provides user-friendly error display with helpful suggestions.
"""

from typing import Optional
import gradio as gr


class ErrorDisplay:
    """
    Display user-friendly error messages in the UI.

    Features:
    - Color-coded severity
    - Helpful suggestions
    - Collapsible technical details
    """

    @staticmethod
    def format_error_message(
        error_message: str,
        show_details: bool = True
    ) -> str:
        """
        Format an error message for display.

        Args:
            error_message: Error message to format
            show_details: Whether to show technical details

        Returns:
            Formatted error message
        """
        if not error_message:
            return ""

        # Check if this is already a formatted error (has emoji or special chars)
        if any(emoji in error_message for emoji in ["❌", "⚠️", "💡"]):
            return error_message

        # Format simple error messages
        return f"❌ {error_message}"

    @staticmethod
    def create_error_display() -> gr.Column:
        """
        Create an error display component.

        Returns:
            Gradio Column with error display widgets
        """
        with gr.Column(visible=False) as error_col:
            gr.Markdown("### ⚠️ Error Information")

            error_text = gr.Textbox(
                label="Error Message",
                value="",
                interactive=False,
                lines=5,
            )

            with gr.Accordion("Technical Details", open=False):
                error_details = gr.Textbox(
                    label="Full Error",
                    value="",
                    interactive=False,
                    lines=10,
                )

            clear_btn = gr.Button("Clear Error", size="sm")

            def clear_error():
                return (
                    gr.update(visible=False),
                    "",
                    ""
                )

            clear_btn.click(
                fn=clear_error,
                outputs=[error_col, error_text, error_details]
            )

        return error_col, error_text, error_details

    @staticmethod
    def create_status_box() -> gr.Textbox:
        """
        Create a simple status/error display box.

        Returns:
            Gradio Textbox for status messages
        """
        return gr.Textbox(
            label="Status",
            value="Ready to generate",
            interactive=False,
            lines=3,
        )

    @staticmethod
    def show_error(error_message: str) -> tuple:
        """
        Show an error in the error display.

        Args:
            error_message: Error message to show

        Returns:
            Tuple of (column_visible, error_text, error_details)
        """
        formatted = ErrorDisplay.format_error_message(error_message)

        return (
            gr.update(visible=True),  # Make error column visible
            formatted,                # Main error message
            error_message             # Technical details
        )

    @staticmethod
    def show_success(message: str) -> tuple:
        """
        Show a success message.

        Args:
            message: Success message

        Returns:
            Tuple for status display
        """
        if not message.startswith("✅"):
            message = f"✅ {message}"

        return message

    @staticmethod
    def show_warning(message: str) -> tuple:
        """
        Show a warning message.

        Args:
            message: Warning message

        Returns:
            Tuple for status display
        """
        if not message.startswith("⚠️"):
            message = f"⚠️ {message}"

        return message

    @staticmethod
    def create_progress_display() -> gr.Column:
        """
        Create a progress display component.

        Returns:
            Gradio Column with progress widgets
        """
        with gr.Column() as progress_col:
            gr.Markdown("### 📊 Generation Progress")

            progress_bar = gr.Progress()

            status_text = gr.Textbox(
                label="Current Step",
                value="Not started",
                interactive=False,
                lines=2,
            )

            with gr.Row():
                step_counter = gr.Number(
                    label="Step",
                    value=0,
                    interactive=False,
                    precision=0,
                )

                total_steps = gr.Number(
                    label="Total Steps",
                    value=0,
                    interactive=False,
                    precision=0,
                )

            eta_text = gr.Textbox(
                label="Estimated Time Remaining",
                value="N/A",
                interactive=False,
            )

        return progress_col, progress_bar, status_text, step_counter, total_steps, eta_text


class StatusFormatter:
    """Helper class to format status messages consistently."""

    @staticmethod
    def success(msg: str) -> str:
        """Format success message."""
        return f"✅ {msg}" if not msg.startswith("✅") else msg

    @staticmethod
    def error(msg: str) -> str:
        """Format error message."""
        return f"❌ {msg}" if not msg.startswith("❌") else msg

    @staticmethod
    def warning(msg: str) -> str:
        """Format warning message."""
        return f"⚠️ {msg}" if not msg.startswith("⚠️") else msg

    @staticmethod
    def info(msg: str) -> str:
        """Format info message."""
        return f"ℹ️ {msg}" if not msg.startswith("ℹ️") else msg

    @staticmethod
    def progress(step: int, total: int, desc: str = "") -> str:
        """Format progress message."""
        percent = (step / total * 100) if total > 0 else 0
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        msg = f"⏳ [{bar}] {step}/{total} ({percent:.1f}%)"
        if desc:
            msg += f" - {desc}"
        return msg
