# References

This list records sources that inform implemented collision functionality or a
clearly identified planned precise phase. A citation does not imply that every
optimization described by the source is implemented.

## Implemented foundations

1. Gottschalk, S., Lin, M. C., and Manocha, D. (1996). “OBBTree: A Hierarchical
   Structure for Rapid Interference Detection.” *Proceedings of SIGGRAPH 1996*,
   171–180. [Project publication page](https://gamma.cs.unc.edu/SSV/obb.html).
   Background for bounding-volume hierarchies and oriented bounding boxes. The
   current tree uses median splitting, not the paper's complete construction.

2. Ericson, C. (2005). *Real-Time Collision Detection*. Morgan Kaufmann.
   [Publisher page](https://www.routledge.com/Real-Time-Collision-Detection/Ericson/p/book/9781558607323).
   Reference for separating-axis tests, bounding volumes, and BVH traversal.

3. COMPAS Association. “Brep API.”
   [COMPAS documentation](https://compas.dev/compas/latest/api/generated/compas.geometry.Brep.html).
   Defines the backend-neutral BRep interface used by the fast query.

4. Open CASCADE Technology. “Modeling Algorithms: Boolean Operations.”
   [OCCT documentation](https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html).
   Documents the common-volume operation used to distinguish solid penetration
   from boundary-only contact.

5. Open CASCADE Technology. “BRepExtrema_DistShapeShape Class Reference.”
   [OCCT API documentation](https://dev.opencascade.org/doc/refman/html/class_b_rep_extrema___dist_shape_shape.html).
   Documents the native-shape minimum-distance query used for BRep contact,
   containment, and tolerance-aware proximity.

6. Open CASCADE Technology. “BRepExtrema_ShapeProximity Class Reference.”
   [OCCT API documentation](https://dev.opencascade.org/doc/refman/html/class_b_rep_extrema___shape_proximity.html).
   Documents the tessellation-based candidate-face proximity query used by the
   current COMPAS OCC contact path.

7. Shapely contributors. “MultiPolygon.”
   [Shapely documentation](https://shapely.readthedocs.io/en/stable/reference/shapely.MultiPolygon.html).
   Documents the multi-component result type that planar contact intersection
   must support.

8. Pan, J., Chitta, S., and Manocha, D. (2012). “FCL: A General Purpose Library
   for Collision and Proximity Queries.” *IEEE International Conference on
   Robotics and Automation*, 3859–3866.
   [Author-hosted paper](https://gamma.cs.unc.edu/FCL/fcl_docs/webpage/pdfs/fcl_icra2012.pdf).
   Foundation for the triangle BVH collision backend.

9. Carpentier, J., Montaut, L., and the Coal contributors. “Coal: An Extension
   of the Flexible Collision Library.”
   [Project repository](https://github.com/coal-library/coal).
   Backend used for precise mesh-surface collision and tolerance margins.

10. Shapely contributors. “line_merge” and “unary_union.”
    [Shapely line merging documentation](https://shapely.readthedocs.io/en/stable/reference/shapely.line_merge.html)
    and [union documentation](https://shapely.readthedocs.io/en/stable/reference/shapely.unary_union.html).
    These topology operations assemble welded mesh-plane segments and combine
    coplanar triangle polygons in the mesh section backend.

11. Open CASCADE Technology. “BRepAlgoAPI_Section Class Reference.”
    [OCCT API documentation](https://dev.opencascade.org/doc/refman/html/class_b_rep_algo_a_p_i___section.html).
    Documents the native plane/shape intersection operation used by the BRep
    section backend.

12. Open CASCADE Technology. “BOPAlgo_Splitter Class Reference.”
    [OCCT API documentation](https://dev.opencascade.org/doc/refman/html/class_b_o_p_algo___splitter.html).
    Documents the native splitting operation wrapped by COMPAS OCC for retained
    BRep half-spaces.

13. Mapbox contributors. “Earcut.”
    [Algorithm repository](https://github.com/mapbox/earcut) and
    [Python bindings](https://github.com/skogler/mapbox_earcut_python).
    Provides the modified ear-clipping implementation used for triangulating
    polygonal render faces, including faces with holes.

14. Open CASCADE Technology. “BRepMesh_IncrementalMesh Class Reference.”
    [OCCT API documentation](https://dev.opencascade.org/doc/refman/html/class_b_rep_mesh___incremental_mesh.html).
    Documents the native BRep face tessellation used through COMPAS OCC's
    `to_viewmesh` infrastructure.

## Planned precise phase

15. Möller, T., and Trumbore, B. (1997). “Fast, Minimum Storage Ray-Triangle
   Intersection.” *Journal of Graphics Tools*, 2(1), 21–28.
   [Author-hosted paper](https://my.eng.utah.edu/~cs6965/papers/MT97.pdf).
   The existing ray-triangle primitive follows this method and can support
   triangle-level queries.

