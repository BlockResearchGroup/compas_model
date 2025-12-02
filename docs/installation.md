# Installation

## Minimal

```bash
pip install compas_model
```

## Full

```bash
conda create -n model python compas compas_occ compas_viewer
conda activate model
pip install "compas_model[viz,ifc]"
```

## Development

```bash
git clone https://github.com/blockresearchgroup/compas_model.git
cd compas_model
conda env create -f environment.yml
conda activate model-dev
```