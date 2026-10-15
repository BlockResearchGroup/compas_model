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
conda env create -f environment.yml
conda activate model-dev
```

The development environment intentionally includes Coal, COMPAS OCC, and
COMPAS Viewer so the complete optional test suite can be run locally. The
standard CI matrix installs only the package and development tools from PyPI;
separate jobs verify the pip-installed viewer and the Conda-installed Coal and
COMPAS OCC backends.
