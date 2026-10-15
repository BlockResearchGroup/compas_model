# Contact Detection Examples

The contact examples render source geometry transparently and computed planar
contact regions in opaque red.

```bash
python examples/contact_detection/model_boundary_cases.py
python examples/contact_detection/disconnected_regions.py
python examples/contact_detection/brep_hole.py
python examples/contact_detection/cross_vault.py
```

They cover exact face contact, tolerance gaps, disconnected interface regions,
a BRep interface with a hole, and the 184-block cross-vault dataset. The
cross-vault input retains its polygonal faces; nonplanar faces are skipped as
invalid planar contact operands rather than silently triangulated.

`brep_hole.py` requires COMPAS OCC installed through Conda. Visual output
requires `compas_model[viz]`. Every script validates its result before opening
the viewer and supports `--no-viewer`.

These examples compute planar interfaces. Edge-only contact, vertex-only
contact, penetration, and arbitrary curved intersections do not necessarily
produce a contact region.
