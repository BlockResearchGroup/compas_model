# Generic Elements

The generic element classes distinguish geometry by representation rather than
by an AEC-specific role:

- `MeshElement` preserves Mesh geometry.
- `BrepElement` preserves native BRep geometry and creates a mesh only when a
  surface or collision mesh is explicitly requested.
- `PrimitiveElement` stores a parametric COMPAS shape and evaluates it to a
  Mesh. It does not implicitly require or select a BRep backend.

This separation makes collision, contact, section, and visualization dispatch
predictable. Mesh and BRep representations are not mixed implicitly.

::: compas_model.elements.generic
