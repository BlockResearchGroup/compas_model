# Development roadmap

This document records planned work that is intentionally outside the scope of
the current collision, contact, sectioning, collection, and viewer changes.
Items are unchecked until their API, documentation, and tests are complete.

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

- [ ] **Interaction data model and lifecycle**
  - Start with the smallest record model that enforces current invariants;
    defer generalized status, event, provenance, and plugin systems until
    concrete use cases require them.
  - Audit every payload currently stored as an interaction-graph edge
    attribute, including contacts, modifiers, derived-data flags, provenance,
    and user-defined attributes.
  - Replace unmanaged `contacts`, `modifiers`, `contacts_computed`, and
    `contact_edge` attributes with a typed, serializable interaction record or
    model-owned registries referenced by graph edges.
  - Give contacts, modifiers, and other interaction objects stable identities;
    do not use list position as persistent identity in the model or viewer.
  - Represent modifier source-to-target direction explicitly instead of
    relying on the incidental stored orientation of an otherwise pair-based
    graph edge.
  - Define whether multiple interaction kinds share one element-pair edge or
    are independent records, and support multiple ordered modifiers and
    multiple derived contact regions without attribute-name conventions.
  - Distinguish explicit user-authored relationships from derived contacts and
    store only the computation parameters and revision information needed for
    current invalidation and reproducibility requirements.
  - Route creation, replacement, reordering, and removal through model APIs
    that validate element ownership, update serialization, invalidate affected
    geometry and caches, and notify viewer projections.
  - Define removal semantics per payload so deleting contacts or one modifier
    cannot accidentally delete unrelated relationship data on the same pair.
  - Keep the graph responsible for connectivity and traversal while preventing
    callers from depending on raw edge-attribute storage details.
  - Prefer direct model methods and a small number of typed record classes over
    a generic interaction framework or event system.
  - Add migration support or an explicit compatibility break for models
    serialized with the current unmanaged edge attributes.
  - Add invariant, round-trip, mutation, invalidation, and partial-removal
    tests before building additional modifier functionality on this layer.
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
