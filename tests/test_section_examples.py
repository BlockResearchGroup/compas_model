import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES = Path(__file__).parents[1] / "examples" / "sectioning"


@pytest.mark.parametrize(
    ("script", "backend"),
    [
        ("mesh_sections_and_clips.py", None),
        ("brep_sections_and_clips.py", "compas_occ"),
    ],
)
def test_section_example_runs_headless(script, backend):
    if backend:
        pytest.importorskip(backend)
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / script), "--no-viewer"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout
