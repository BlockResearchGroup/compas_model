# Collision Detection Examples

These examples combine executable assertions with an optional COMPAS Viewer
scene. The collision result is computed before visualization; the viewer does
not participate in detection.

```bash
python examples/collision_detection/mesh_overlap.py
python examples/collision_detection/model_broad_vs_precise.py
python examples/collision_detection/brep_boundary_cases.py
```

They cover Mesh overlap, conservative AABB candidates versus precise
mesh-surface collision, and penetrating, touching, or separated native BReps.

Precise Mesh checks require Coal. BRep checks require COMPAS OCC installed
with Conda as described in the [installation guide](../installation.md).
Install `compas_model[viz]` to open the scenes.

Append `--no-viewer` to run assertions without opening a window:

```bash
python examples/collision_detection/model_broad_vs_precise.py --no-viewer
```
