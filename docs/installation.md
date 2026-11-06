# Installation

COMPAS Model requires Python 3.12 or newer. The project is continuously tested
with Python 3.12, 3.13, and 3.14.

## Minimal

```bash
pip install compas_model
```

## Viewer

```bash
pip install "compas_model[viz]"
```

The viewer is optional and is not required for model construction, geometry
algorithms, collision detection, contact detection, or headless tests.

## Precise mesh collision

Precise mesh-surface collision uses the optional Coal backend. Coal is
available from PyPI, so it can be installed through the project extra:

```bash
pip install "compas_model[collision]"
```

PyPI wheel availability depends on the Python version and operating system. A
source installation additionally requires Coal's native build dependencies.
For a predictable compiled installation across supported platforms, use
conda-forge instead:

```bash
conda install -c conda-forge coal
```

See the [Coal package on PyPI](https://pypi.org/project/coal/) for the currently
published source distribution and platform wheels.

## Precise BRep collision

Precise BRep collision operates on native Open CASCADE topology through the
optional COMPAS OCC backend. COMPAS OCC is not distributed through PyPI and
therefore is intentionally not declared as a Python package extra. Install it
from conda-forge, then install COMPAS Model with pip in the same environment:

```bash
conda create -n model -c conda-forge python=3.12 compas_occ
conda activate model
python -m pip install compas_model
```

See the [official COMPAS OCC installation
instructions](https://compas.dev/compas_occ/installation/) for supported Conda
setups.

## Complete optional setup

To use precise Mesh collision, precise BRep operations, and the viewer in one
environment:

```bash
conda create -n model -c conda-forge python=3.12 coal compas_occ
conda activate model
python -m pip install "compas_model[viz]"
```

## Development

```bash
git clone https://github.com/blockresearchgroup/compas_model.git
cd compas_model
uv sync --frozen --group dev --group docs
```

Run the same non-optional checks used by continuous integration:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright --project .github/pyright-core.json
uv run pytest
```

The core Pyright configuration covers the package source and typing consumer
examples that do not require optional backends. Executable examples under
`examples/` are checked in the separate viewer and OCC environments described
below, so every example is checked without making an optional dependency part
of the core environment.

Thin Invoke aliases remain available, for example `uv run invoke test` and
`uv run invoke docs`. The direct commands above are authoritative.

The locked core environment intentionally excludes Coal, COMPAS OCC, and
COMPAS Viewer. Add one PyPI-installable capability explicitly when working on
it:

```bash
uv sync --frozen --group dev --extra collision
uv sync --frozen --group dev --extra viz
uv run pyright --project .github/pyright-viewer.json
uv run mkdocs build --strict
```

For the native BRep integration, create the minimal Conda runtime and let uv
synchronize the Python project into that active environment:

```bash
conda env create -f environment.yml
conda activate compas-model-occ
VIRTUAL_ENV="$CONDA_PREFIX" uv sync --active --inexact --frozen --group dev --extra viz
uv pip install --python "$CONDA_PREFIX/bin/python" --no-deps ../compas_occ
VIRTUAL_ENV="$CONDA_PREFIX" uv run --active --no-sync pyright --project .github/pyright-occ.json
```

This assumes a COMPAS OCC checkout next to the COMPAS Model checkout. Conda
provides the native `pythonocc-core` dependency; uv overlays the Python package
from the local checkout. CI uses the same boundary and installs COMPAS OCC from
an exact commit instead, making the integration gate reproducible.

The standard CI matrix uses only the locked core environment. Separate jobs
verify PyPI-installed Coal and the exact COMPAS Viewer candidate. The native
BRep job combines Conda's PythonOCC runtime with the exact COMPAS OCC candidate.

Native BRep collision, contact conversion, sectioning, and clipping import
COMPAS OCC only when those capabilities are requested. Therefore, COMPAS OCC
is not required for the main model API. OCC-specific operations may provide the
required conda-forge installation command when the backend is unavailable.
