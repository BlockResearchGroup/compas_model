"""Compatibility imports for the shared example viewer helper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from viewer import AMBER  # noqa: E402,F401
from viewer import BLUE  # noqa: E402,F401
from viewer import DARK  # noqa: E402,F401
from viewer import GREEN  # noqa: E402,F401
from viewer import GREY  # noqa: E402,F401
from viewer import RED  # noqa: E402,F401
from viewer import show_scene  # noqa: E402,F401
