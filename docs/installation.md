# Installation

COMPAS Model requires Python 3.12 or newer. The project is continuously tested
with Python 3.12, 3.13, and 3.14.

## Minimal

```bash
pip install compas_model
```

## Full

```bash
conda create -n model python=3.12 compas compas_occ compas_viewer
conda activate model
pip install "compas_model[viz,ifc]"
```

## Precise mesh collision

Precise mesh-surface collision uses the optional Coal backend.

```bash
pip install "compas_model[collision]"
```

For conda environments, install the compiled backend from conda-forge.

```bash
conda install -c conda-forge coal
```

## Precise BRep collision

Precise BRep collision operates on native Open CASCADE topology through the
optional COMPAS OCC backend.

```bash
pip install "compas_model[brep]"
```

For conda environments, install the compiled backend from conda-forge.

```bash
conda install -c conda-forge compas_occ
```

## Development

```bash
git clone https://github.com/blockresearchgroup/compas_model.git
cd compas_model
conda env create -f environment.yml
conda activate model-dev
```
