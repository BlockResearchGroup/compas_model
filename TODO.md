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
- [ ] **Modifier visualization and evaluation modes**
  - Add a modifier data view showing modifier ownership, direction, order,
    source and target elements, parameters, status, and failures.
  - Make individual modifiers and their tool geometry selectable and
    independently visible where meaningful.
  - Support switching between source geometry without modifiers and final
    evaluated geometry with modifiers applied, globally and per element.
  - Optionally expose intermediate geometry after each modifier for debugging
    and verification.
  - Preserve selection, visibility, hierarchy, and collection state when the
    evaluation mode changes.
  - Reuse cached source, intermediate, and final render geometry so switching
    modes does not trigger unrelated geometry evaluation.
- [ ] **Feature visualization and evaluation modes**
  - Show each element's ordered feature stack, parameters, representation
    support, evaluation status, and failures in the element inspector or a
    dedicated feature data view.
  - Make feature inputs, tool geometry, and resulting geometry selectable and
    independently visible where meaningful.
  - Support switching between base geometry without features and feature-
    evaluated geometry, globally and per element.
  - Optionally expose intermediate geometry after each feature for debugging
    and verification.
  - Define how the feature view combines with the modifier view: base geometry,
    feature-evaluated source geometry, modifier intermediates, and final model
    geometry should remain distinguishable.
  - Reuse cached base, intermediate, and evaluated render geometry when
    switching modes.

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
  - Separate explicit user-authored relationships from derived contacts and
    other computed results, with provenance, computation parameters, revision,
    validity, and failure state where relevant.
  - Route creation, replacement, reordering, and removal through model APIs
    that validate element ownership, update serialization, invalidate affected
    geometry and caches, and notify viewer projections.
  - Define removal semantics per payload so deleting contacts or one modifier
    cannot accidentally delete unrelated relationship data on the same pair.
  - Keep the graph responsible for connectivity and traversal while preventing
    callers from depending on raw edge-attribute storage details.
  - Add migration support or an explicit compatibility break for models
    serialized with the current unmanaged edge attributes.
  - Add invariant, round-trip, mutation, invalidation, and partial-removal
    tests before building additional modifier functionality on this layer.
- [ ] **Cache invalidation**
  - Centralize revision propagation for geometry, transforms, hierarchy,
    collections, interactions, sections, clips, BVHs, and render buffers.
  - Cache final evaluated element geometry after applying features and ordered
    modifiers, with cache keys or revisions covering the source geometry,
    feature sequence, modifier sequence, modifier tools, and transformations.
  - Recompute only the affected element and its downstream modifier dependants
    when an input changes.
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
  - Add basic modifiers for Boolean union, difference, and intersection;
    trimming; and plane or tool-based slicing.
  - Keep Mesh and BRep modifier implementations separate and report unsupported
    geometry/backend combinations explicitly.
  - Specify failure behavior and invalidation when elements or modifiers
    change.
  - Expose modifier relationships, tools, intermediate results, and evaluation
    status to the viewer without making viewer state part of model evaluation.
- [ ] **Generic element features**
  - Define the semantic boundary between an element-local feature and an
    interaction-driven modifier before selecting concrete feature types.
  - Identify a minimal context-free feature set applicable to `MeshElement`,
    `BrepElement`, and `PrimitiveElement`, potentially including local holes,
    pockets, cuts, offsets, or trims.
  - Define feature ordering, parameterization, representation support,
    serialization, failure behavior, and cache invalidation.
  - Expose feature inputs, intermediate results, final results, and evaluation
    status to the viewer without coupling feature evaluation to viewer state.
  - Avoid introducing domain concepts such as joints, notches, or fabrication
    operations unless they are demonstrably context-independent.

## Definition of done

For every item above:

- public behavior and failure semantics are documented;
- serialization and backward compatibility are considered;
- unit, boundary, invalid-input, and round-trip tests are included;
- Pyright, Ruff, the full Pytest suite, and strict MkDocs build pass;
- computational methods and external references are documented where relevant.
