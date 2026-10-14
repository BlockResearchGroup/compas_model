---
name: update-type-hints
description: Add or improve Python type hints for Python 3.12+ without changing runtime behavior or public API.
---

## Goal

Update missing or incomplete Python type hints.

## Requirements

- Preserve public API behavior.
- Do not introduce runtime dependencies.
- Use modern type hint syntax supported by Python 3.12 and newer, including `|` unions where they improve clarity.
- Prefer standard library types over typing imports: `list[tuple[...]]` instead of `List[Tuple[...]]`.
- Use `cast` only when absolutely necessary.
- Avoid broad `Any` unless unavoidable.
- Avoid importing heavy optional dependencies only for typing; use `TYPE_CHECKING` when needed.
- Do not change default values, validation behavior, or exception behavior.
