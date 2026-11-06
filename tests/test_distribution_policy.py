import importlib.util
import io
import tarfile
import zipfile
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / ".github" / "verify_distributions.py"
SPEC = importlib.util.spec_from_file_location("verify_distributions", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


METADATA = """Metadata-Version: 2.4
Name: compas_model
Version: 0.9.3
Requires-Python: >=3.12
Provides-Extra: collision
Provides-Extra: viz
Requires-Dist: compas<4,>=3.0.0
Requires-Dist: mapbox-earcut<3,>=2
Requires-Dist: numpy>=1.26
Requires-Dist: scipy>=1.11.4
Requires-Dist: shapely>=2.1
Requires-Dist: coal<4.0,>=3.0; extra == "collision"
Requires-Dist: compas-viewer; extra == "viz"
"""


def write_wheel(
    directory: Path,
    metadata: str = METADATA,
    entry_point: str = "compas_model = compas_model.plugins\n",
    *,
    filename_tag: str = "py3-none-any",
    wheel_tag: str = "py3-none-any",
    include_typing_marker: bool = True,
) -> Path:
    wheel = directory / f"compas_model-0.9.3-{filename_tag}.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("compas_model/__init__.py", "")
        archive.writestr("compas_model/plugins.py", "")
        if include_typing_marker:
            archive.writestr("compas_model/py.typed", "")
        archive.writestr("compas_model-0.9.3.dist-info/METADATA", metadata)
        archive.writestr(
            "compas_model-0.9.3.dist-info/WHEEL",
            f"Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: {wheel_tag}\n",
        )
        archive.writestr("compas_model-0.9.3.dist-info/entry_points.txt", f"[compas.plugins]\n{entry_point}")
    return wheel


def write_sdist(directory: Path, include_plugins: bool = True, include_typing_marker: bool = True) -> Path:
    sdist = directory / "compas_model-0.9.3.tar.gz"
    root = "compas_model-0.9.3"
    names = ["LICENSE", "README.md", "pyproject.toml", "src/compas_model/__init__.py"]
    if include_plugins:
        names.append("src/compas_model/plugins.py")
    if include_typing_marker:
        names.append("src/compas_model/py.typed")
    with tarfile.open(sdist, "w:gz") as archive:
        for name in names:
            data = b"test\n"
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return sdist


def test_distribution_verifier_accepts_expected_artifacts(tmp_path):
    write_wheel(tmp_path)
    write_sdist(tmp_path)

    MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_wrong_python_contract(tmp_path):
    write_wheel(tmp_path, metadata=METADATA.replace(">=3.12", ">=3.11", 1))
    write_sdist(tmp_path)

    with pytest.raises(ValueError, match="Requires-Python"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_wrong_plugin_entry_point(tmp_path):
    write_wheel(tmp_path, entry_point="compas_model = compas_model.viewer\n")
    write_sdist(tmp_path)

    with pytest.raises(ValueError, match="plugin entry point"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_non_portable_wheel_tag(tmp_path):
    write_wheel(tmp_path, filename_tag="cp312-cp312-manylinux_x86_64", wheel_tag="cp312-cp312-manylinux_x86_64")
    write_sdist(tmp_path)

    with pytest.raises(ValueError, match="filename"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_missing_typing_marker(tmp_path):
    write_wheel(tmp_path, include_typing_marker=False)
    write_sdist(tmp_path)

    with pytest.raises(ValueError, match="typing marker"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_unexpected_extra_dependency(tmp_path):
    metadata = METADATA + 'Requires-Dist: numpy; extra == "collision"\n'
    write_wheel(tmp_path, metadata=metadata)
    write_sdist(tmp_path)

    with pytest.raises(ValueError, match="collision extra dependency"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_incomplete_source_distribution(tmp_path):
    write_wheel(tmp_path)
    write_sdist(tmp_path, include_plugins=False)

    with pytest.raises(ValueError, match="required project files"):
        MODULE.verify_distributions(tmp_path)


def test_distribution_verifier_rejects_source_distribution_without_typing_marker(tmp_path):
    write_wheel(tmp_path)
    write_sdist(tmp_path, include_typing_marker=False)

    with pytest.raises(ValueError, match="required project files"):
        MODULE.verify_distributions(tmp_path)
