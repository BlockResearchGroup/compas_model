import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES = Path(__file__).parents[1] / "examples" / "contact_detection"


@pytest.mark.parametrize(
    ("script", "backend"),
    [
        ("model_boundary_cases.py", None),
        ("disconnected_regions.py", None),
        ("brep_hole.py", "compas_occ"),
        ("cross_vault.py", None),
        ("cross_vault_model_viewer.py", "compas_viewer"),
    ],
)
def test_contact_example_runs_headless(script, backend):
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
