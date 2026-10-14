import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES = Path(__file__).parents[1] / "examples" / "collision_detection"


@pytest.mark.parametrize(
    ("script", "backend"),
    [
        ("mesh_overlap.py", "coal"),
        ("brep_boundary_cases.py", "compas_occ"),
        ("model_broad_vs_precise.py", "coal"),
    ],
)
def test_collision_example_runs_headless(script, backend):
    pytest.importorskip(backend)
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / script), "--no-viewer"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout


def test_collision_example_viewer_configuration_is_compatible():
    pytest.importorskip("compas_viewer")
    code = f"import sys; sys.path.insert(0, {str(EXAMPLES)!r}); from _viewer import validate_viewer_backend; validate_viewer_backend()"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
