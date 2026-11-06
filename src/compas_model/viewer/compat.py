from typing import Any

SELECTED_TAB_STYLESHEET = "QTabBar::tab:selected { background: palette(highlight); color: palette(highlighted-text); font-weight: bold; }"


def highlight_active_tab(tabform: Any, current: str | None = None) -> None:
    """Make the active tab visually distinct and optionally select a tab."""
    stylesheet = tabform.widget.styleSheet()
    if "QTabBar::tab:selected" not in stylesheet:
        tabform.widget.setStyleSheet(f"{stylesheet}\n{SELECTED_TAB_STYLESHEET}".strip())
    if current is not None and current in tabform.tabs:
        tabform.set_current_tab(current)
