import compas_model.geometry as geometry


def test_geometry_public_exports_are_complete_and_resolvable():
    expected = {
        "ClipElementResult",
        "ClipResult",
        "EarcutResult",
        "NonCoplanarRegionsError",
        "PlanarRegion",
        "SectionClassification",
        "SectionElementResult",
        "SectionRepresentation",
        "SectionResult",
        "aabb_from_points",
        "clip_brep",
        "clip_mesh",
        "clip_mesh_halfspace",
        "combine_aabbs",
        "combine_obbs",
        "intersection_brep_plane",
        "intersection_mesh_plane",
        "intersection_planar_region_planar_region",
        "intersection_ray_triangle",
        "intersections_line_aabb",
        "intersections_line_box",
        "intersections_ray_aabb",
        "intersections_ray_box",
        "is_collision_poly_poly_xy",
        "is_geometry_empty",
        "is_intersection_aabb_aabb",
        "is_intersection_box_box",
        "is_intersection_line_aabb",
        "is_intersection_line_box",
        "is_intersection_ray_aabb",
        "is_intersection_ray_box",
        "is_intersection_segment_aabb",
        "is_intersection_segment_box",
        "is_intersection_sphere_aabb",
        "is_intersection_sphere_box",
        "minkowski_difference_xy",
        "minkowski_sum_xy",
        "pca_box",
        "reconstruct_planar_regions",
        "section_brep",
        "section_mesh",
        "triangulate_polygon_earcut",
    }

    assert set(geometry.__all__) == expected
    assert len(geometry.__all__) == len(expected)
    assert all(hasattr(geometry, name) for name in geometry.__all__)
