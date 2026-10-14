---
name: update-docs
description: Update project documentation, mkdocs navigation, tutorials, API reference pages, license, and changelog coverage.
---

# Goal

Update the contents of the docs folder and `mkdocs.yml` to provide full coverage of the code base in this project.

## Requirements

- Provide an overview of the package in `index.md`
- Provide installation instructions for stable releases via PyPI, and dev setups with installation from source using a local repo clone.
- Provide license info in `license.md` by referring to `LICENSE` using `--8<-- "LICENSE"`.
- Include a change log in `changelog.md` by referring to the top level `CHANGELOG.md` using `--8<-- "CHANGELOG.md"`.
- Provide a step-by-step tutorial of the basic functionality of the package.
- Provide an overview of the modules contained in the project and their functionality in an API reference.
- Use the `update-docstrings` skill to write or update docstrings where necessary.

## Computational and Numerical Functionality

When documenting computational geometry, numerical algorithms, or spatial data structures:

- Explain the implemented methodology at a level that makes its behavior independently verifiable.
- Distinguish approximate, conservative, broad-phase, and precise results.
- State tolerance and boundary semantics, false-positive and false-negative guarantees, backend assumptions, and known limitations.
- Describe relevant cache invalidation or acceleration-structure behavior when it affects correctness.
- Include commands or tests that verify the documented behavior.
- Add the primary technical sources and backend documentation that informed the implementation to the top-level `REFERENCES.md`.
- Keep claims scoped to what is actually implemented, and clearly label sources associated only with planned work.
