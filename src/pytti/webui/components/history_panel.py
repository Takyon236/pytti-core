"""
Prompt History Panel for PyTTI Web UI

Provides UI for browsing and selecting from prompt history.
"""

from typing import Tuple, Optional
import gradio as gr

from pytti.history import PromptHistoryManager


class HistoryPanel:
    """
    Prompt history panel component.

    Features:
    - Dropdown with recent prompts
    - Search history
    - Favorite prompts
    - Clear history
    """

    @staticmethod
    def create_history_panel() -> Tuple[gr.Dropdown, gr.Button, gr.Button, gr.Button]:
        """
        Create prompt history panel.

        Returns:
            Tuple of (history_dropdown, search_btn, favorite_btn, clear_btn)
        """
        history_manager = PromptHistoryManager.get_instance()

        with gr.Column() as panel:
            gr.Markdown("### 📜 Prompt History")

            # Get recent prompts for dropdown
            recent_prompts = history_manager.get_recent(20)
            choices = [entry.get_display_text(60) for entry in recent_prompts]
            prompts_map = {entry.get_display_text(60): entry.prompt for entry in recent_prompts}

            history_dropdown = gr.Dropdown(
                choices=choices,
                label="Recent Prompts",
                interactive=True,
                allow_custom_value=False,
            )

            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", size="sm")
                favorites_btn = gr.Button("⭐ Favorites", size="sm")
                clear_btn = gr.Button("🗑️ Clear", size="sm")

            # Search box
            with gr.Accordion("Search History", open=False):
                search_box = gr.Textbox(
                    label="Search",
                    placeholder="Search prompts...",
                )
                search_btn = gr.Button("🔍 Search", size="sm")

        return history_dropdown, refresh_btn, favorites_btn, clear_btn, search_box, search_btn, prompts_map

    @staticmethod
    def get_history_choices() -> Tuple[list, dict]:
        """
        Get current history choices for dropdown.

        Returns:
            Tuple of (choices list, prompts_map dict)
        """
        history_manager = PromptHistoryManager.get_instance()
        recent_prompts = history_manager.get_recent(20)

        choices = [entry.get_display_text(60) for entry in recent_prompts]
        prompts_map = {entry.get_display_text(60): entry.prompt for entry in recent_prompts}

        return choices, prompts_map

    @staticmethod
    def refresh_history() -> dict:
        """
        Refresh history dropdown.

        Returns:
            Updated dropdown component
        """
        choices, prompts_map = HistoryPanel.get_history_choices()
        return gr.update(choices=choices)

    @staticmethod
    def show_favorites() -> dict:
        """
        Show only favorite prompts.

        Returns:
            Updated dropdown with favorites
        """
        history_manager = PromptHistoryManager.get_instance()
        favorites = history_manager.get_favorites()

        choices = [entry.get_display_text(60) for entry in favorites]
        return gr.update(choices=choices)

    @staticmethod
    def search_history(query: str) -> dict:
        """
        Search history and update dropdown.

        Args:
            query: Search query

        Returns:
            Updated dropdown with search results
        """
        if not query:
            return HistoryPanel.refresh_history()

        history_manager = PromptHistoryManager.get_instance()
        results = history_manager.search(query)

        choices = [entry.get_display_text(60) for entry in results]
        return gr.update(choices=choices)

    @staticmethod
    def clear_history_confirm() -> str:
        """
        Clear history (keeping favorites).

        Returns:
            Status message
        """
        history_manager = PromptHistoryManager.get_instance()
        deleted = history_manager.clear_history(keep_favorites=True)

        return f"Cleared {deleted} entries (kept favorites)"


def create_integrated_history_dropdown(prompt_textbox: gr.Textbox) -> Tuple:
    """
    Create integrated history dropdown that updates prompt textbox.

    Args:
        prompt_textbox: The prompt textbox to update

    Returns:
        Tuple of UI components
    """
    history_manager = PromptHistoryManager.get_instance()

    # Get recent prompts
    recent_prompts = history_manager.get_recent(20)
    choices = ["(Select from history)"] + [entry.get_display_text(60) for entry in recent_prompts]
    prompts_map = {entry.get_display_text(60): entry.prompt for entry in recent_prompts}

    # Create dropdown
    history_dropdown = gr.Dropdown(
        choices=choices,
        label="📜 Recent Prompts",
        value="(Select from history)",
        interactive=True,
    )

    # Wire up: selecting from history updates prompt textbox
    def select_from_history(selection: str) -> Tuple[str, str]:
        """
        Handle history selection.

        Returns:
            Tuple of (prompt_text, reset_dropdown)
        """
        if selection == "(Select from history)" or not selection:
            return "", "(Select from history)"

        # Get full prompt from map
        full_prompt = prompts_map.get(selection, selection)
        return full_prompt, "(Select from history)"

    history_dropdown.change(
        fn=select_from_history,
        inputs=[history_dropdown],
        outputs=[prompt_textbox, history_dropdown]
    )

    return history_dropdown, prompts_map


def add_prompt_to_history(prompt: str, settings: Optional[dict] = None) -> None:
    """
    Convenience function to add prompt to history.

    Args:
        prompt: Prompt text
        settings: Optional generation settings
    """
    history_manager = PromptHistoryManager.get_instance()
    history_manager.add_prompt(prompt, settings=settings)
