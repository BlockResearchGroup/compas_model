import configparser
import sys
import tarfile
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

BASE_REQUIREMENTS = {
    "compas": SpecifierSet(">=3.0.0,<4"),
    "mapbox-earcut": SpecifierSet(">=2,<3"),
    "numpy": SpecifierSet(">=1.26"),
    "scipy": SpecifierSet(">=1.11.4"),
    "shapely": SpecifierSet(">=2.1"),
}
EXTRA_REQUIREMENTS = {
    "collision": {("coal", SpecifierSet(">=3.0,<4.0"))},
    "viz": {("compas-viewer", SpecifierSet())},
}


def find_distributions(directory: Path) -> tuple[Path, Path]:
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("Expected exactly one wheel and one source distribution.")
    if not wheels[0].stat().st_size or not sdists[0].stat().st_size:
        raise ValueError("Distribution files must not be empty.")
    return wheels[0], sdists[0]


def _read_wheel_metadata(archive: zipfile.ZipFile) -> Message:
    metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
    if len(metadata_names) != 1:
        raise ValueError("Wheel must contain exactly one METADATA file.")
    return BytesParser().parsebytes(archive.read(metadata_names[0]))


def _read_wheel_file(archive: zipfile.ZipFile) -> Message:
    wheel_names = [name for name in archive.namelist() if name.endswith(".dist-info/WHEEL")]
    if len(wheel_names) != 1:
        raise ValueError("Wheel must contain exactly one WHEEL file.")
    return BytesParser().parsebytes(archive.read(wheel_names[0]))


def _requirement_groups(metadata: Message) -> tuple[dict[str, Requirement], dict[str, list[Requirement]]]:
    base: dict[str, Requirement] = {}
    extras: dict[str, list[Requirement]] = {extra: [] for extra in EXTRA_REQUIREMENTS}
    for value in metadata.get_all("Requires-Dist", []):
        requirement = Requirement(value)
        name = canonicalize_name(requirement.name)
        if requirement.marker is None:
            base[name] = requirement
            continue
        for extra in extras:
            if requirement.marker.evaluate({"extra": extra}):
                extras[extra].append(requirement)
    return base, extras


def _verify_requirements(metadata: Message) -> None:
    provided_extras = set(metadata.get_all("Provides-Extra", []))
    if provided_extras != set(EXTRA_REQUIREMENTS):
        raise ValueError("Wheel must expose exactly the collision and viz extras.")

    base, extras = _requirement_groups(metadata)
    if set(base) != set(BASE_REQUIREMENTS):
        raise ValueError("Wheel has unexpected base dependencies.")
    for name, expected in BASE_REQUIREMENTS.items():
        if base[name].specifier != expected:
            raise ValueError(f"Wheel has an unexpected {name} dependency.")

    for extra, expected in EXTRA_REQUIREMENTS.items():
        actual = {(canonicalize_name(requirement.name), requirement.specifier) for requirement in extras[extra]}
        if len(actual) != len(extras[extra]) or actual != expected:
            raise ValueError(f"Wheel has an unexpected {extra} extra dependency.")


def _verify_entry_point(archive: zipfile.ZipFile) -> None:
    entry_point_names = [name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt")]
    if len(entry_point_names) != 1:
        raise ValueError("Wheel must contain exactly one entry_points.txt file.")
    parser = configparser.ConfigParser()
    parser.read_string(archive.read(entry_point_names[0]).decode("utf-8"))
    if parser.get("compas.plugins", "compas_model", fallback=None) != "compas_model.plugins":
        raise ValueError("Wheel does not contain the COMPAS Model plugin entry point.")


def verify_wheel(wheel: Path) -> None:
    if not wheel.name.endswith("-py3-none-any.whl"):
        raise ValueError("Wheel filename must declare the py3-none-any tag.")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {"compas_model/__init__.py", "compas_model/plugins.py", "compas_model/py.typed"}
        if not required.issubset(names):
            raise ValueError("Wheel is missing a required package file or typing marker.")
        metadata = _read_wheel_metadata(archive)
        wheel_metadata = _read_wheel_file(archive)
        _verify_entry_point(archive)

    if metadata["Requires-Python"] != ">=3.12":
        raise ValueError("Wheel has an unexpected Requires-Python value.")
    if wheel_metadata["Root-Is-Purelib"] != "true":
        raise ValueError("Wheel must be installed into purelib.")
    if wheel_metadata.get_all("Tag", []) != ["py3-none-any"]:
        raise ValueError("Wheel must contain exactly the py3-none-any tag.")
    _verify_requirements(metadata)


def verify_sdist(sdist: Path) -> None:
    with tarfile.open(sdist) as archive:
        names = set(archive.getnames())
    roots = {name.split("/", 1)[0] for name in names}
    if len(roots) != 1:
        raise ValueError("Source distribution must have one root directory.")
    root = roots.pop()
    required = {
        f"{root}/LICENSE",
        f"{root}/README.md",
        f"{root}/pyproject.toml",
        f"{root}/src/compas_model/__init__.py",
        f"{root}/src/compas_model/plugins.py",
        f"{root}/src/compas_model/py.typed",
    }
    if not required.issubset(names):
        raise ValueError("Source distribution is missing required project files.")


def verify_distributions(directory: Path) -> None:
    wheel, sdist = find_distributions(directory)
    verify_wheel(wheel)
    verify_sdist(sdist)


if __name__ == "__main__":
    verify_distributions(Path(sys.argv[1]))
    for additional_wheel in sys.argv[2:]:
        verify_wheel(Path(additional_wheel))
