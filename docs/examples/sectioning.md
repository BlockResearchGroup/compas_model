# Section and Clip Examples

The sectioning examples compare a geometry-only section, a retained
negative-half-space clip, and a clip whose section contains a hole.

```bash
python examples/sectioning/mesh_sections_and_clips.py
python examples/sectioning/brep_sections_and_clips.py
```

The Mesh example verifies polygon reconstruction, capped clipping, and hole
preservation. The BRep example displays polygonal section output while
retaining exact native OCC clipping results and therefore requires COMPAS OCC.

The plane frame's Z axis points toward the discarded `front` side. Clips keep
negative signed distances (`behind`). Both scripts validate areas, holes, and
retained volumes and accept `--no-viewer`.
