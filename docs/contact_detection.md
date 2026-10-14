# Contact detection audit

This page records the behavior and limitations of the contact-interface code as
of October 2026. Resolved audit items are documented alongside the remaining
limitations so the implementation can be checked independently.

## Scope

Contact detection currently finds **planar face-to-face interface regions**. It
is distinct from collision detection:

- collision detection answers whether two representations overlap, touch, or
  lie within a distance tolerance;
- contact detection attempts to construct one or more oriented planar regions
  suitable for downstream equilibrium calculations;
- solid penetration, containment, edge contact, and vertex contact do not by
  themselves define a planar contact interface.

Mesh and BRep inputs follow separate paths and are never mixed.

## Current mesh methodology

`mesh_mesh_contacts` compares every face of the first mesh with every face of
the second mesh. Faces whose normals are not opposite are discarded. Each
remaining pair is fitted to a shared plane, projected to that plane, and
intersected as `PlanarRegion` geometry using Shapely. Every connected result
becomes a separate `Contact`, holes are preserved, and regions smaller than
`minimum_area` are discarded.

This is an exhaustive quadratic face-pair search. It does not yet use Coal's
triangle hierarchy or the model BVH. It is intended for polygonal planar
interfaces, not arbitrary curved or penetrating mesh surfaces.

Mesh faces are used as stored and are not triangulated by contact detection.
If a polygon's vertices deviate from its best-fit plane by more than the
absolute tolerance, that face pair produces no contact rather than aborting
the complete search. This is particularly relevant to rounded or
low-precision OBJ data: preserving nonplanar quads can produce fewer contacts
than triangulating those quads into independently planar faces.

## Current BRep methodology

`brep_brep_contacts` first calls the active BRep backend's `overlap` method. For
COMPAS OCC this meshes both shapes and uses
`BRepExtrema_ShapeProximity` to obtain candidate faces. Candidate face sets are
then cross-compared, filtered by opposite polygon normals, converted to
`PlanarRegion` geometry with their face holes, and intersected with Shapely.

Therefore, “precise BRep contact interface” currently means a planar polygon
intersection computed from selected BRep face boundaries. Candidate selection
is tessellation-based and controlled by `deflection`; it is not an exact OCC
face-face Boolean operation.

## Verified baseline

Automated tests verify mesh and OCC BRep box interfaces in all axis directions,
partial face overlaps, corner-offset overlaps, and rejection of edge-only
contact. The BRep tests had previously been disabled and are now active.

## Audit findings

### Geometry-result model

The previous single-polygon assumption has been removed. `Polygon`,
`MultiPolygon`, and polygonal `GeometryCollection` intersections now produce a
list of connected planar regions. `Contact` stores one authoritative
`PlanarRegion`; its size is net area, and its BRep and constrained Delaunay mesh
both preserve holes. Shapely 2.1 or newer is required for the constrained
triangulation.

### Candidate generation

`Model.compute_contacts` uses `ElementBVH.nearby_elements`. For each element,
the query expands its axis-aligned bounding box by the requested absolute
`tolerance` in all six directions and traverses the cached model BVH. This is a
conservative broad phase: it may return false positives, especially when BVH
leaves contain multiple elements, but it cannot reject two geometries whose
Euclidean separation is at most the tolerance. Every unordered pair is
evaluated once, in model insertion order, which makes contact orientation
deterministic. Mixed Mesh/BRep pairs are skipped rather than dispatched to an
unsupported algorithm.

The expansion is absolute and independent of element size. In particular,
small elements separated by a valid tolerance are no longer missed by the old
relative 20% search box. A negative tolerance is rejected before the BVH is
queried.

The mesh function performs all face-pair comparisons. The BRep function uses
backend proximity candidates, but loses face-pair correspondence and
cross-compares the two returned face sets.

### Tolerances and validation

One `tolerance` currently controls broad-phase proximity, face coplanarity, and
projection deviation. These are different numerical decisions and may become
explicit parameters in a future tolerance policy. Angular opposition uses a
fixed relative dot-product tolerance. Negative tolerances and minimum areas are
rejected; backend failures are not normalized into a common exception type.

### Model and interaction-graph updates

Model recomputation is transactional with respect to geometry computation: all
candidate contacts are calculated before the interaction graph is changed. If
one calculation raises, no graph contacts or edges are changed. Successful
recomputation replaces derived contacts and clears stale results, including
pairs that are no longer broad-phase candidates.

Two edge attributes record provenance. `contacts_computed` identifies a contact
value managed by recomputation; `contact_edge` identifies an interaction edge
created solely because a contact was found. A stale contact-only edge is
deleted. An explicit user-created edge is preserved with `contacts=None`, and a
generated edge is also preserved if it has acquired modifiers. Contact values
without `contacts_computed=True` are treated as user-authored and are not
cleared merely because their pair falls outside the current candidate set.

## Recommended implementation order

1. Add curved, invalid, duplicate-interface, and
   deterministic-orientation tests before exposing contact interfaces in the
   custom viewer.
2. Investigate retaining BRep face-pair correspondence from the OCC proximity
   query instead of cross-comparing candidate face sets.
3. Separate broad-phase, coplanarity, and projection tolerances if real-world
   model scales demonstrate that one tolerance is insufficient.

This order intentionally overlaps with the planned section infrastructure:
sections and contact interfaces both need robust oriented planar regions with
multiple components and holes.

## Geometry foundation

The first infrastructure step is implemented as
`compas_model.geometry.PlanarRegion` and
`intersection_planar_region_planar_region`:

- a region contains one oriented exterior and zero or more oppositely oriented
  holes;
- area is net area, with holes subtracted;
- regions are validated for coplanarity and valid polygonal topology;
- intersections return a deterministic list of connected regions;
- `Polygon`, `MultiPolygon`, and polygonal `GeometryCollection` results are
  supported, while boundary-only results are discarded;
- result frames follow the first input, preserving source-to-target contact
  orientation;
- regions support COMPAS serialization, transformations, AABBs, and OBBs.

Both contact algorithms and `Contact` now use this primitive. Compatibility
accessors still expose the exterior `polygon`, `points`, `holes`, `frame`,
`mesh`, `brep`, and `size`, while `Contact.geometry` returns the complete
planar region.

## Verification

The model-level migration is covered by tests for absolute tolerance on small
elements, unique BVH candidates, replacement of changed interfaces, removal of
stale generated edges, preservation of explicit edges, and invalid options.
Run the focused checks with:

```bash
pytest tests/test_algorithms_bvh.py tests/test_model.py tests/test_algorithms_contacts.py
```
