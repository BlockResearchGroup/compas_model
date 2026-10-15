# Development roadmap

This document records planned work that is intentionally outside the scope of
the current collision, contact, sectioning, collection, and viewer changes.
Items are unchecked until their API, documentation, and tests are complete.

## Dependency architecture

- [ ] **Decouple optional computational features from the model core**
  - Keep `Model`, `Element`, hierarchy, collections, interaction graphs, and
    serialization usable with only the core dependencies installed.
  - Remove eager imports of collision, contact, section, clipping, viewer, and
    backend modules from core import paths.
  - Reclassify Shapely and Mapbox Earcut according to the capabilities that use
    them instead of requiring them solely to import or construct a model.
  - Keep convenience methods on `Model` and `Element`, but resolve their
    implementations and third-party backends only when called.
  - Add minimal-install CI coverage plus tests for clear missing-dependency
    errors from every optional capability.

## Viewer interaction

- [ ] **Isolation mode**
  - Isolate the current element, collection, type, interaction, or selection.
  - Restore the exact previous visibility state when isolation ends.
  - Define behavior for nested or repeated isolation requests.
- [ ] **Selection filters**
  - Filter viewport picking by element type, collection, interaction type, and
    result-layer type.
  - Expose the active filter in the viewer UI and provide an unfiltered reset.
  - Keep tree selection, viewport selection, and the inspector synchronized.
- [ ] **Visualization of sections and clips**
  - Add dedicated viewer layers and data-view tabs for active sections and
    clips.
  - Support visibility, selection, colors, plane display, and result metadata.
  - Keep section-only geometry distinct from clipped retained geometry.

## Model composition

- [ ] **Model merging**
  - Define GUID, name, material, collection, hierarchy, and interaction conflict
    policies.
  - Preserve Mesh/BRep representations without implicit conversion.
  - Return a mapping from source identities to merged identities.
- [ ] **Model splitting**
  - Split by explicit element sets, collections, hierarchy branches, or
    connected interaction components.
  - Define handling of interactions, collections, and materials crossing a
    split boundary.
  - Return provenance mappings for every generated model.
- [ ] **Submodel management**
  - Define owned versus referenced submodels and their transform semantics.
  - Support traversal, serialization, replacement, unloading, and nested
    submodels.
  - Specify how cross-submodel interactions and collections are represented.

## Model lifecycle and domain data

- [ ] **Cache invalidation**
  - Centralize revision propagation for geometry, transforms, hierarchy,
    collections, interactions, sections, clips, BVHs, and render buffers.
  - Document which mutations invalidate which derived data.
  - Add regression tests for direct and transitive invalidation paths.
- [ ] **Remove materials**
  - Add model-level material removal with explicit reject, unassign, and
    replacement policies for referenced materials.
  - Prevent dangling material references after removal and serialization.
- [ ] **Modifier infrastructure**
  - Define modifier ownership, direction, ordering, applicability, and
    serialization.
  - Separate source geometry, modifier tools, evaluated geometry, and cached
    results.
  - Specify failure behavior and invalidation when elements or modifiers
    change.
  - Add viewer inspection and visibility for modifier relationships and tools.

## Definition of done

For every item above:

- public behavior and failure semantics are documented;
- serialization and backward compatibility are considered;
- unit, boundary, invalid-input, and round-trip tests are included;
- Pyright, Ruff, the full Pytest suite, and strict MkDocs build pass;
- computational methods and external references are documented where relevant.
