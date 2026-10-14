# ruff: noqa: F401

from .bbox import aabb_from_points
from .bbox import combine_aabbs
from .bbox import combine_obbs
from .bbox import pca_box

from .intersections import is_intersection_line_aabb
from .intersections import is_intersection_line_box
from .intersections import is_intersection_ray_aabb
from .intersections import is_intersection_ray_box
from .intersections import is_intersection_segment_aabb
from .intersections import is_intersection_segment_box
from .intersections import is_intersection_box_box
from .intersections import is_intersection_aabb_aabb
from .intersections import is_intersection_sphere_box
from .intersections import is_intersection_sphere_aabb

from .intersections import intersection_ray_triangle

from .intersections import intersections_line_aabb
from .intersections import intersections_line_box
from .intersections import intersections_ray_aabb
from .intersections import intersections_ray_box

from .minkowski2 import minkowski_sum_xy
from .minkowski2 import minkowski_difference_xy

from .gjk2 import is_collision_poly_poly_xy

from .triangulation import EarcutResult
from .triangulation import triangulate_polygon_earcut

from .planar_region import NonCoplanarRegionsError
from .planar_region import PlanarRegion
from .planar_region import intersection_planar_region_planar_region

from .section import SectionClassification
from .section import ClipElementResult
from .section import ClipResult
from .section import SectionElementResult
from .section import SectionRepresentation
from .section import SectionResult

from .mesh_section import clip_mesh_halfspace
from .mesh_section import clip_mesh
from .mesh_section import intersection_mesh_plane
from .mesh_section import reconstruct_planar_regions
from .mesh_section import section_mesh

from .brep_section import intersection_brep_plane
from .brep_section import clip_brep
from .brep_section import section_brep
