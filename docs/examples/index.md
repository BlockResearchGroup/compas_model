# Examples

## Visually verifying collision detection

The collision examples combine executable assertions with an interactive
COMPAS Viewer scene. Green geometry participates in a precise collision, amber
geometry illustrates boundary-only or broad-phase-only results, red geometry
is separated, and grey geometry has no reported collision.

Install the visualization and collision backends first:

```bash
pip install -e ".[viz,collision,brep]"
```

Run the examples from the repository root:

```bash
python examples/collision_detection/mesh_overlap.py
python examples/collision_detection/brep_boundary_cases.py
python examples/collision_detection/model_broad_vs_precise.py
```

The examples demonstrate:

1. A simple mesh overlap for which fast and precise checks agree.
2. Penetrating, face-touching, and narrowly separated native OCC BReps.
3. A model-level comparison in which the fast AABB query reports containment
   as a candidate while precise mesh-*surface* collision correctly rejects it.

Each script checks its expected results before opening the viewer. For CI,
headless machines, or quick terminal verification, append `--no-viewer`:

```bash
python examples/collision_detection/model_broad_vs_precise.py --no-viewer
```

The colors and labels are explanatory output only. The collision result is
computed before visualization; the viewer does not participate in detection.

## Visually verifying contact detection

The contact examples render source geometry transparently and draw the
computed contact regions in opaque red. This makes the actual output geometry,
rather than only a Boolean result, visually inspectable.

Run them from the repository root:

```bash
python examples/contact_detection/model_boundary_cases.py
python examples/contact_detection/disconnected_regions.py
python examples/contact_detection/brep_hole.py
python examples/contact_detection/cross_vault.py
```

The scenes verify three distinct parts of the implementation:

1. `model_boundary_cases.py` compares exact face contact, a small gap accepted
   by an absolute tolerance, and a gap outside that tolerance. It exercises the
   model BVH candidate search and graph-managed contacts.
2. `disconnected_regions.py` intersects a U-shaped mesh face with a crossing
   face. The result must be two independent `Contact` objects of area `0.5`.
3. `brep_hole.py` computes a planar OCC BRep interface whose exterior area is
   `16` and hole area is `4`. The displayed contact mesh must retain the hole
   and have net area `12`.
4. `cross_vault.py` loads all 184 named block objects from
   `data/cross_vault.obj`, builds a model, and runs the tolerance-aware contact
   workflow while preserving the source polygonal faces: the loaded meshes
   contain 1248 quads and 16 triangles. The three-decimal OBJ export contains
   slightly nonplanar quads. Such faces are not valid planar contact operands
   and are skipped rather than triangulated. With tolerance and minimum area
   both set to `0.01`, the current verified result is therefore 257 contacting
   block pairs and 257 contact regions. The model viewer gives every contact
   region its own selectable scene object.

As with the collision examples, every script asserts its numerical and
topological expectations before opening the viewer. Append `--no-viewer` for
headless verification:

```bash
python examples/contact_detection/model_boundary_cases.py --no-viewer
```

These examples visualize planar contact interfaces. They do not imply that
edge-only contact, vertex-only contact, penetration, or arbitrary curved
surface intersections produce a contact region.

## Visually verifying sections and clips

The sectioning examples place three cases side by side: a geometry-only
section, a retained negative-half-space clip, and a more complex clip whose
section contains a hole. Source geometry is translucent grey, computed section
faces are red, and retained clip geometry is blue or green.

Run the Mesh and native OCC BRep variants from the repository root:

```bash
python examples/sectioning/mesh_sections_and_clips.py
python examples/sectioning/brep_sections_and_clips.py
```

The Mesh example verifies polygonal intersection reconstruction, capped
half-space clipping, and preservation of a section hole. The BRep example
shows that the displayed curved section face is sampled into a polygonal
`PlanarRegion`, while the retained half-sphere and hollow box are exact native
OCC clipping results.

The frame Z axis points toward the discarded `front` side in every case. The
clip retains negative signed distances (`behind`); reversing the Z axis would
retain the other half. The translucent full source shown beside or around a
clip is explanatory context added by the example and is not part of the
returned clip geometry.

Both scripts assert expected areas, holes, and retained volumes before opening
the viewer. They can therefore also be checked headlessly:

```bash
python examples/sectioning/mesh_sections_and_clips.py --no-viewer
python examples/sectioning/brep_sections_and_clips.py --no-viewer
```

!!! note "Python 3.14 and COMPAS Viewer 2.0.1"

    The shared `examples/viewer.py` helper contains a narrowly scoped compatibility adapter
    for a configuration-annotation issue in COMPAS Viewer 2.0.1 on Python 3.14.
    It changes only viewer configuration initialization and has no effect on
    collision calculations.
