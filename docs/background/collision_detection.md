# Collision detection methodology

Collision detection is split into a **broad phase** and a **precise phase**.
Meshes and boundary representations (BReps) follow separate pipelines;
the implementation never converts or compares mixed representations.

## Current capability

The public queries are:

- `is_mesh_mesh_collision_fast`
- `is_brep_brep_collision_fast`
- `is_mesh_mesh_collision`
- `is_brep_brep_collision`
- `Element.is_collision(..., precision="fast")`
- `Element.is_collision(..., precision="precise")`
- `Model.collision_candidates()` and `Model.collisions(...)`

Fast queries are conservative. A `False` result means the two geometry bounds
are separated. A `True` result means only that their bounds overlap, so the
underlying geometries can still be disjoint. This distinction is intentional:
the fast query is suitable for pruning, not for proving geometric intersection.

Precise mesh collision is implemented by Coal. Precise BRep collision is
implemented for COMPAS OCC BReps using their native Open CASCADE shapes. Other
BRep backends fail explicitly rather than being tessellated or silently routed
through the mesh pipeline.

The exported `is_polyhedron_polyhedron_collision` function remains an
unimplemented legacy placeholder. Polyhedron collision semantics are outside
the mesh/BRep milestone documented here.

## Precise mesh-surface collision

`is_mesh_mesh_collision` converts each COMPAS mesh to a Coal `BVHModelOBBRSS`:

1. Faces are triangulated by `Mesh.to_vertices_and_faces(triangulated=True)`
   without mutating the source mesh.
2. Empty meshes, non-finite coordinates, and zero-area triangles are rejected.
3. Vertices and triangle indices are copied into Coal's native containers.
4. Coal builds an OBB/RSS triangle hierarchy and performs the narrow-phase
   query.

The function classifies intersections between **mesh surfaces**. A closed mesh
entirely contained in another closed mesh returns `False` if their surfaces do
not meet. General COMPAS meshes may be open and do not intrinsically define a
solid interior, so solid-volume overlap is intentionally not inferred.

Touching counts as collision. Coal contact depths for triangle meshes do not
reliably distinguish every coplanar face or edge contact from surface
penetration. For that reason, precise calls with `include_touching=False` raise
`NotImplementedError` instead of returning an ambiguous classification.

Positive tolerance is passed to Coal as its collision security margin. This
causes separated surfaces within the requested distance to count as colliding.
Negative tolerances are rejected.

Coal is optional for ordinary use. Install the collision extra or the conda
package when precise mesh queries are needed:

```bash
pip install "compas_model[collision]"
# or
conda install -c conda-forge coal
```

Standalone `is_mesh_mesh_collision` calls prepare both Coal triangle hierarchies
for that query. Elements cache their prepared hierarchy, so
`Model.collisions(precision="precise")` prepares each participating element at
most once and reuses it across candidate pairs and subsequent calls.

## Precise BRep collision

`is_brep_brep_collision` operates directly on the native shapes stored by
`compas_occ.brep.OCCBrep`; it does not tessellate them. Before a query, Open
CASCADE's shape analyzer rejects null and invalid topology.

When touching is included, `BRepExtrema_DistShapeShape` computes the minimum
distance between the two shapes. A distance less than or equal to `tolerance`
is a collision. Intersecting boundaries and solid containment both produce
zero distance, so this path detects containment as well as contact. The
effective comparison tolerance is never smaller than Open CASCADE's
`Precision::Confusion()` resolution; this absorbs kernel-level floating-point
residuals at analytically tangent curved surfaces.

When touching is excluded, both BReps must be solids. The implementation
computes their Boolean common and requires a positive-volume solid result.
This rejects face, edge, and vertex contact while accepting penetration and
containment. Positive tolerance cannot currently be combined with excluded
touching: a non-negative distance cannot express penetration depth for
arbitrary BReps, so this combination raises `NotImplementedError` rather than
guessing.

Kernel failures are reported as `RuntimeError`, and unsupported BRep backends
as `TypeError`. COMPAS OCC is not available from PyPI, so precise BRep queries
require a Conda environment:

```bash
conda create -n model -c conda-forge python=3.12 compas_occ
conda activate model
python -m pip install compas_model
```

## Bounding boxes and tolerances

Mesh bounds are computed from every mesh vertex. Mesh faces and topology do not
affect the fast result. BRep bounds come from `Brep.aabb`, allowing the active
geometry backend to account for extrema of curved faces instead of using only
BRep vertices.

Two axis-aligned bounds intersect when their closed intervals overlap on all
three coordinate axes. By default, boundary contact counts as intersection.
With `include_touching=False`, every axis must overlap by more than `tolerance`.
With `include_touching=True`, gaps no larger than `tolerance` are accepted.
Negative tolerances are rejected.

Backend-computed BRep bounds may include a small numerical padding. For example,
Open CASCADE expands bounds to preserve robustness. Therefore,
`include_touching=False` describes contact between the *computed AABBs*, not an
exact classification of contact between ideal BRep surfaces. This can create a
false positive, which is valid for a conservative broad phase.

## Model BVH

The model spatial index is a purpose-built binary bounding volume hierarchy
(BVH), independent of the COMPAS `Tree` data structure. Construction proceeds
as follows:

1. Wrap each element in a record containing its key, centroid, payload, and
   bounding points.
2. Compute the node bound around all records.
3. Select the node-box axis with the largest dimension.
4. Sort record centroids along that axis and split at the median.
5. Repeat until `leafsize` or `max_depth` stops subdivision.

This median split gives deterministic, reasonably balanced trees. It is not a
surface-area heuristic and does not claim to produce an optimal hierarchy.
Oriented nodes use a principal-component box, which is likewise not guaranteed
to be the minimum-volume oriented box.

Candidate generation traverses two trees together. Non-overlapping node pairs
are discarded. When both nodes are leaves, their object pairs are emitted;
otherwise the node with the larger bounding-box volume is descended first.
Self-comparison removes identity pairs and duplicate unordered pairs.

`Model.collisions()` normally uses this BVH pruning before dispatching each pair
to its representation-specific query. A positive tolerance can make separated
element bounds count as colliding; because the current BVH traversal has no
inflated-bound mode, the model method exhaustively checks element pairs in that
case. This preserves correctness at the cost of broad-phase performance.

## Cache behavior

The model caches its BVH, and mesh elements cache their prepared Coal collision
models. OCC BReps already retain their native kernel shapes, so no second BRep
collision cache is created. Adding or removing elements invalidates the spatial
index. Replacing or transforming element geometry, transforming the model,
adding a feature, or
adding a modifier invalidates derived geometry, prepared collision models, and
spatial indices. Invalidation currently covers all model elements because
hierarchical transformations and modifiers can propagate changes.

Direct mutation inside a mesh or direct mutation of the exposed feature list
cannot be observed automatically. Callers should replace the element geometry,
use the provided mutation methods, or explicitly trigger a model-level change
after such mutation. Dependency-aware invalidation may make the conservative
model-wide reset more selective in the future.

## Verification

The automated tests cover overlapping, separated, touching, nearly tangent,
tolerance-expanded, contained, curved, small-volume, large-coordinate,
degenerate, empty, and invalid inputs. They also verify polygon triangulation,
unique self-collision pairs, dual-tree traversal, mixed AABB/OBB traversal,
prepared-model reuse and invalidation, and explicit failures for unsupported
precise semantics. CI imports both optional backends explicitly so these tests
cannot silently disappear through dependency-based skips.

Run the checks in the development environment with:

```bash
conda run -n model-dev pytest
conda run -n model-dev pyright
conda run -n model-dev ruff check src tests
conda run -n model-dev mkdocs build --strict
```

See [References](references.md) for the underlying algorithms and backends.
