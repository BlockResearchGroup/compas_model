# Modifiers

Modifiers are directed operations from a source element to a target element.
The model owns each modifier through a `ModifierRecord`; records targeting the
same element have an explicit zero-based evaluation order.

Final element geometry is evaluated in four stages:

1. `base_geometry` is generated from the stored geometry or parametric element
   definition in element-local coordinates;
2. `local_geometry` copies the base geometry and applies ordered features while
   remaining in element-local coordinates;
3. `model_geometry` transforms local geometry through the element hierarchy
   and model transformation without applying modifiers;
4. `final_geometry` copies model geometry and applies directed modifiers in
   `ModifierRecord.order`.

All four stages are cached independently. This makes it possible to inspect or
render different stages without reevaluating unchanged earlier stages. The
former `elementgeometry`, `modelgeometry`, `compute_elementgeometry`, and
`compute_modelgeometry` API has been removed because `modelgeometry` combined
the transformed and modified stages.

Use `Model.add_modifier` and `Model.remove_interaction_record` to change the
stack, `Model.reorder_modifier_records` to supply its complete new order, and
`Model.replace_modifier` to replace an operation or its parameters.
These operations invalidate the target and all transitive downstream modifier
targets. Modifier cycles are rejected. A modifier must preserve the target's
Mesh or BRep representation; mixed or implicit conversions are not supported.
Concrete backend failures propagate unless that modifier explicitly defines a
stable higher-level error.

Invalidation follows the evaluation stages. Changing the stored geometry or
parametric definition clears all four stages. Changing features preserves
`base_geometry` and clears the following stages. Changing placement preserves
base and local geometry while clearing `model_geometry`, `final_geometry`, and
the model transformation for the element and its hierarchy descendants.
Adding, removing, or reordering a modifier clears only `final_geometry` for the
target and downstream modifier targets. All affected elements still receive a
new runtime geometry revision so viewer and collision caches cannot retain
stale results. `ModifierRecord.modifier` is read-only for this reason. Custom
modifier parameters should not be mutated in place; construct a replacement
and pass it through `Model.replace_modifier` so invalidation remains targeted.

## BRep difference

`BrepDifferenceModifier` subtracts the source element's fully evaluated model
geometry from the target geometry at its position in the ordered modifier
stack. Both geometries must be BReps. The implementation calls the
backend-neutral `Brep.from_boolean_difference` constructor and neither imports
COMPAS OCC nor converts Mesh geometry.

The active COMPAS BRep backend determines Boolean robustness, tolerance, and
the representation of an empty result. Any BRep returned by the backend,
including an empty BRep, is preserved. Backend exceptions propagate unchanged,
and a non-BRep result is rejected. With COMPAS OCC, touching or disjoint tools
normally leave the target volume unchanged, while a containing or identical
tool produces an empty BRep. Other kernels may differ at tolerance-sensitive
boundaries.

Empty evaluated geometry is a valid model state, not an evaluation failure.
Once a modifier empties its target, remaining modifiers are skipped. Empty
elements remain in the model and hierarchy, but are excluded from the model
BVH and therefore produce no collision candidates or contacts. Viewer caches
represent them with empty render buffers. Since empty geometry has no spatial
extent, requesting its AABB or OBB raises `ValueError` rather than constructing
an artificial zero-sized box. Generic element implementations that can produce
empty evaluated geometry should override `Element.is_empty`; the built-in Mesh
and BRep elements already do so.

The behavior can be verified with:

```bash
pytest tests/test_modifiers.py
```

::: compas_model.modifiers.brep

## Modifier

::: compas_model.modifiers.modifier
