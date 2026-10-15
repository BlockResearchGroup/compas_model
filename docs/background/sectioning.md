# Sectioning infrastructure

Sectioning uses the same oriented `PlanarRegion` geometry as contact detection.
The backend-independent result model and separate Mesh and native OCC BRep
backends are implemented. Representations are never mixed during sectioning.

## Oriented-plane convention

A `SectionResult` stores the cutting plane as a `Frame`. The frame Z axis is
the plane normal and establishes the two half-spaces. For a point `p` and frame
origin `o`, signed distance is computed as:

```text
(p - o) dot frame.zaxis
```

The classification rules are:

- distance greater than `tolerance`: `front`;
- distance smaller than `-tolerance`: `behind`;
- absolute distance less than or equal to `tolerance`: `coplanar`;
- geometry spanning both half-spaces, or containing points on the plane and on
  one side of it: `intersecting`.

This convention is independent of the Mesh or BRep backend. Reversing the
frame Z axis swaps front and behind.

## Sections versus clips

Sectioning and clipping are deliberately separate operations:

- a **section** contains only geometry on the cutting plane: closed faces as
  `PlanarRegion` objects and their outlines, plus any open intersection curves;
- a **clip** contains the section together with the source geometry retained in
  the negative (behind) half-space.

This distinction keeps a section independent of decisions about which side of
an object to retain. A clip always keeps the side where signed distance is
negative. Reverse the frame Z axis to keep the other side.

The public backend functions follow the same distinction:

- `section_mesh` and `section_brep` return `SectionElementResult`;
- `clip_mesh` and `clip_brep` return `ClipElementResult`.

## Result model

`SectionElementResult` stores the result for one source element:

- source element GUID and representation (`mesh` or `brep`);
- spatial classification;
- zero or more closed `PlanarRegion` section components;
- zero or more open intersection polylines;

Its `outlines` accessor contains the exterior and hole boundaries of every
closed region, followed by the open intersection curves.

`ClipElementResult` composes a `SectionElementResult` with an optional snapshot
of geometry retained behind the plane. Geometry that is wholly behind the plane
is retained without trimming. Geometry wholly in front of or coplanar with the
plane has no retained geometry.

Retained geometry must match the declared representation. Constructor inputs
are copied so later mutations of model geometry cannot silently change an
existing section result.

`SectionResult` stores the cutting frame, tolerance, and ordered section
records. It validates that every section region and open curve lies on the
cutting plane within the recorded tolerance. Convenience accessors collect
regions, outlines, open curves, and records by classification without changing
their deterministic input order.

`ClipResult` stores the same cutting frame and tolerance, ordered clip records,
and the capping choice. Its `section` accessor provides the corresponding
geometry-only `SectionResult`, while its `geometry` accessor collects retained
objects.

All four result types support COMPAS serialization and transformations.
Constructor inputs are copied, and a transformation moves the plane, section
geometry, and retained geometry together. This snapshot behavior prevents a
later mutation of source model geometry from changing an existing result.

## Mesh methodology

`intersection_mesh_plane` obtains a triangulated view of the input without
modifying it. Triangle edges are classified by signed distance, crossing points
are projected to the cutting plane, and endpoints are welded in plane-local XY
coordinates using the requested tolerance. Shapely merges the resulting line
network. Closed rings are classified by nesting depth to construct disconnected
`PlanarRegion` components and holes; unclosed chains become `Polyline` results.
Coplanar triangles are unioned as planar polygons. A completely coplanar mesh
is therefore classified `coplanar` and can still produce regions.

`section_mesh` stops after producing the planar result. `clip_mesh` additionally
calls `clip_mesh_halfspace`, which uses polygon half-space clipping on every
original mesh face and keeps the negative half-space. When the input is closed
and `cap=True`, all unfiltered section regions are triangulated and joined to
the clipped boundaries. Consequently, `minimum_area` filters the reported
regions without accidentally leaving a requested clipped solid open. Open
input meshes are never capped.

The line and polygon operations are tolerance-based. Features or gaps at or
below the welding tolerance may merge. The result may contain conservative
topological simplification at that scale. Clipping does not repair invalid,
self-intersecting, nonmanifold, or inconsistently oriented input meshes.

For a tangent cut, the element is `intersecting`, its boundary region is
reported, and the nonempty retained side is an unchanged geometry snapshot.
The zero-thickness opposite side is omitted. Entirely-behind geometry is always
copied into a clip result.

## BRep methodology

`intersection_brep_plane` requires a native COMPAS OCC BRep. Open CASCADE's
`BRepAlgoAPI_Section` computes the section edges against an infinite planar
face. Those edges remain exact in the backend result, but `PlanarRegion`
boundaries are polygonal by design. Each native edge is therefore sampled with
`curve_samples` points and passed through the same plane-local welding, ring
nesting, and open-chain reconstruction used by mesh section curves. Increasing
`curve_samples` improves curved-region area accuracy without changing the
native section operation.

`section_brep` stops after producing the planar result. `clip_brep` uses OCC
shape splitting and retains the negative half-space; reversing the plane retains
the positive side. The resulting solids are natively capped by OCC. Uncapped
intersected BRep output is currently unsupported and raises
`NotImplementedError` rather than silently returning capped geometry. A wholly
behind BRep does not require splitting and can therefore be returned regardless
of the capping option.

Half-space classification combines native section existence with BRep
topological points and a surface tessellation. The section and trimmed solids
remain native operations, but classification of pathological or very small
curved features is therefore limited by backend tessellation. The requested
`tolerance` affects signed-distance classification, coplanarity, endpoint
welding, and region validation; it does not expand the infinite plane into a
thick slab for the native OCC section operation.

Tangent sections are classified `intersecting`. A tangent edge or face may
produce a region, while an isolated tangent point has no polygonal or polyline
representation and therefore produces no section geometry. Entirely coplanar
faces are classified `coplanar`.

## Verification

The section and clip contracts are tested independently for empty and ordered
results, signed-distance classification, regions with holes, outlines, open
curves, retained geometry, snapshot behavior, serialization, transformations,
plane validation, tangent cases, whole-half-space cases, and invalid options:

```bash
pytest tests/test_geometry_section.py
pytest tests/test_geometry_mesh_section.py
pytest tests/test_geometry_brep_section.py
```
