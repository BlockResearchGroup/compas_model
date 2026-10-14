# General Project Instructions

This project defines a universal model for representing various constellations of elements relevant to the AEC industry.
For example, with a COMPAS model, you can represent any of the following:

- a building comprised of elements such as columns, beams, walls, floors, ...
- a composite timber wall panel,
- a formwork for concrete casting,
- a scaffolding,
- a 3DCP bridge comprised out of discrete blocks, 
- ...

This project provides the general infrastructure, while specific implementations are contained in separate, dedicated projects.

Related projects are, for example:

- `compas_dem`
- `compas_timber`

## Setup

- Support Python 3.12 and newer. The tested version matrix is defined in the GitHub Actions workflows.
- Use the `conda` environment `model-dev`.
- If the environment doesn't exist yet, create it using `environment.yml`.
- Activate the environment, and check if all requirements are available. Install the missing ones.

## Commands

- Run tests with: `pytest`
- Run type checks with: `pyright`
- Run formatting with: `ruff format`
- Run linting with: `ruff check`

## Workflow

Before editing:
- Inspect the related files and local patterns first.
- Explain the intended change briefly.
- Prefer existing COMPAS/COMPAS Model abstractions over new helpers.
- Preserve public API and runtime behavior unless explicitly asked to change it.

After editing:
- Run the narrowest relevant checks first.
- Use `pytest` for behavioral changes, `pyright` for typing changes, and `ruff check` / `ruff format` for touched Python files.
- If a check cannot be run because the environment is missing a tool, report that.
- Summarize changed files, behavior, and remaining risks.

## Computational Geometry

- Keep mesh and BRep implementations separate unless conversion between representations is explicitly requested.
- Distinguish conservative or broad-phase results from precise results in API names, docstrings, and documentation.
- Define tolerance and boundary-contact semantics explicitly, including whether touching counts as intersection.
- State false-positive and false-negative guarantees for approximate algorithms.
- Prefer established geometry kernels and libraries for precise operations when they provide suitable correctness, robustness, and performance.
- Test overlap, separation, touching, degeneracy, empty and invalid inputs, numerical tolerances, and unsupported geometry combinations where relevant.
- Document the implemented methodology, backend assumptions, numerical behavior, and known limitations of computational geometry algorithms.
- Add primary technical sources and backend documentation to `REFERENCES.md` when they inform an implementation.
- Keep methodology documentation and references synchronized with implementation changes.
