---
name: update-docstrings
description: Update Python docstrings to Numpy style for mkdocs compatibility without changing runtime behavior.
---

# Goal

Update docstrings and make them compatible with mkdocs.

## Docstring style

- Use Numpy-style docstring conventions.
- Use mkdocs-compatible syntax and conventions.
- Don't specify types of parameters if the parameters have type hints in the function signature.
- Do specify types in the return section. Otherwise descriptions of returns are interpreted as types by mkdocs.
- Use `or` instead of `Union`.
- Don't add attribute lists in class docstrings.
- Leave a blank line at the end of a docstring, unless the docstring is a one-liner.
- Remove Sphinx markup clutter if it is still present.
- Remove empty example sections.
- Do not document obvious implementation details.
- Prefer concise public API explanations over exhaustive internal narration.
- Keep examples only when they are correct, runnable, and valuable.
- Add links to relevant other parts of the documentation in a See Also section.
