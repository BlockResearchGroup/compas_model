from enum import Enum
from typing import TYPE_CHECKING
from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_model.elements import Element
from compas_model.interactions import ContactInterface

if TYPE_CHECKING:
    from compas_model.elements import BeamElement
    from compas_model.elements import ColumnElement
    from compas_model.elements import PlateElement


class ColumnHeadElement(Element):
    """Base class for column head elements."""

    pass


class CardinalDirections(int, Enum):
    """
    Enumeration of directions where the number corresponds to the column head mesh face index.

    Attributes
    ----------
    NORTH : int
        The north direction.
    NORTH_WEST : int
        The north-west direction.
    WEST : int
        The west direction.
    SOUTH_WEST : int
        The south-west direction.
    SOUTH : int
        The south direction.
    SOUTH_EAST : int
        The south-east direction.
    EAST : int
        The east direction.
    NORTH_EAST : int
        The north-east direction.
    """

    NORTH = 0
    NORTH_WEST = 1
    WEST = 2
    SOUTH_WEST = 3
    SOUTH = 4
    SOUTH_EAST = 5
    EAST = 6
    NORTH_EAST = 7


class CrossBlockShape:
    """Generate Column Head shapes based on vertex and edge and face adjacency.
    The class is singleton, considering the dimension of the column head is fixed and created once.

    Parameters
    ----------
    width : float
        The width of the column head.
    depth : float
        The depth of the column head.
    height : float
        The height of the column head.
    offset : float
        The offset of the column head.
    v : dict[int, Point]
        The points, first one is always the origin.
    e : list[tuple[int, int]]
        Edges starts from v0 between points v0-v1, v0-v2 and so on.
    f : list[list[int]]
        Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.


    Example
    -------
    width: float = 150
    depth: float = 150
    height: float = 300
    offset: float = 210
    v: dict[int, Point] = {
        7: Point(0, 0, 0),
        5: Point(-1, 0, 0),
        6: Point(0, 1, 0),
        8: Point(0, -1, 0),
        2: Point(1, 0, 0),
    }

    e: list[tuple[int, int]] = [
        (7, 5),
        (7, 6),
        (7, 8),
        (7, 2),
    ]

    f: list[list[int]] = [[5, 7, 6, 10]]

    CrossBlockShape: CrossBlockShape = CrossBlockShape(v, e, f, width, depth, height, offset)
    mesh = CrossBlockShape.mesh.scaled(0.001)

    """

    _instance = None
    _generated_meshes = {}
    _last_mesh = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CrossBlockShape, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        v: dict[int, Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
        width: float = 150,
        depth: float = 150,
        height: float = 300,
        offset: float = 210,
    ):
        if not hasattr(self, "_initialized"):
            self._width = width
            self._depth = depth
            self._height = height
            self._offset = offset
        rules = self._generate_rules(v, e, f)
        self._generated_meshes[rules] = self._generate_mesh(rules)
        self._last_mesh = self._generated_meshes[rules]
        self._initialized = True

    def _generate_rules(self, v: dict[Point], e: list[tuple[int, int]], f: list[list[int]]) -> list[bool]:
        """
        Generate rules for generating the mesh of the column head.
        ATTENTION: edge first vertex is considered the column head origin, otherwise direction are flipped.

        Parameters
        -------
        v : dict
            The points, first one is always the origin.
        e : list
            First find nearest edges, edges starts from v0 between points v0-v1, v0-v2 and so on.
        f : list
            Faces between points v0-v1-v2-v3 and so on.

        Returns
        -------
        tuple
            The generated rules.
        """

        rules = [False, False, False, False, False, False, False, False]
        edge_directions: dict[tuple[int, int], CardinalDirections] = {}

        # Find the directions of the edges
        for edge in e:
            if edge[0] not in v:
                raise ValueError(f"Vertex {edge[0]} not found in the vertices.")
            if edge[1] not in v:
                raise ValueError(f"Vertex {edge[1]} not found in the vertices.")

            p0 = v[edge[0]]
            p1 = v[edge[1]]
            vector = p1 - p0
            direction = ColumnHeadCrossElement.closest_direction(vector)
            rules[direction] = True

            # track direction for face edge search
            edge_directions[(edge[0], edge[1])] = direction
            edge_directions[(edge[1], edge[0])] = direction

        for face in f:
            face_edge_directions = []
            for i in range(len(face)):
                v0 = face[i]
                v1 = face[(i + 1) % len(face)]

                if (v0, v1) not in edge_directions:
                    continue

                face_edge_directions.append(edge_directions[(v0, v1)])

            # Face must have two directions
            if not len(face_edge_directions) == 2:
                raise ValueError(f"Face {face} does not share two edges.")

            face_direction: CardinalDirections = ColumnHeadCrossElement.get_direction_combination(face_edge_directions[0], face_edge_directions[1])
            rules[face_direction] = True

        return tuple(rules)

    def _generate_mesh(self, rules: tuple[bool]) -> Mesh:
        """
        Generate mesh based on the rules.

        Parameters
        ----------

        rules : tuple
            The generated rules that corresponds to world direction using CardinalDirections enumerator.

        Returns
        -------
        Mesh
            The column head generated mesh.

        """

        if rules in self._generated_meshes:
            return self._generated_meshes[rules]

        ###########################################################################################
        # Generate mesh based on the rules.
        ###########################################################################################

        vertices: list[Point] = [
            # Outer ring
            Point(self._width, self._depth + self._offset, -self._height),  # 0
            Point(-self._width, self._depth + self._offset, -self._height),  # 1
            Point(-self._width - self._offset, self._depth, -self._height),  # 2
            Point(-self._width - self._offset, -self._depth, -self._height),  # 3
            Point(-self._width, -self._depth - self._offset, -self._height),  # 4
            Point(self._width, -self._depth - self._offset, -self._height),  # 5
            Point(self._width + self._offset, -self._depth, -self._height),  # 6
            Point(self._width + self._offset, self._depth, -self._height),  # 7
            # Inner quad
            Point(self._width, self._depth, -self._height),  # 8
            Point(-self._width, self._depth, -self._height),  # 9
            Point(-self._width, -self._depth, -self._height),  # 10
            Point(self._width, -self._depth, -self._height),  # 11
            # Top quad
            Point(self._width, self._depth, 0),  # 12
            Point(-self._width, self._depth, 0),  # 13
            Point(-self._width, -self._depth, 0),  # 14
            Point(self._width, -self._depth, 0),  # 15
        ]

        # Check if two floor plate has two beams else plate cannot be connected to column head.
        for i in range(4):
            if rules[i * 2 + 1]:
                if not rules[i * 2] or not rules[(i * 2 + 2) % 8]:
                    rules[i * 2 + 1] = False

        faces = [
            [8, 9, 10, 11],
            [12, 13, 14, 15],
        ]

        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)

        if rules[0]:
            mesh.add_face([0, 1, 9, 8])
            mesh.add_face([0, 1, 13, 12], attr_dict={"direction": CardinalDirections.NORTH})

        if rules[1]:
            mesh.add_face([1, 2, 9])
            mesh.add_face([1, 2, 13], attr_dict={"direction": CardinalDirections.NORTH_WEST})

        if rules[2]:
            mesh.add_face([2, 3, 10, 9])
            mesh.add_face([2, 3, 14, 13], attr_dict={"direction": CardinalDirections.WEST})

        if rules[3]:
            mesh.add_face([3, 4, 10])
            mesh.add_face([3, 4, 14], attr_dict={"direction": CardinalDirections.SOUTH_WEST})

        if rules[4]:
            mesh.add_face([4, 5, 11, 10])
            mesh.add_face([4, 5, 15, 14], attr_dict={"direction": CardinalDirections.SOUTH})

        if rules[5]:
            mesh.add_face([5, 6, 11])
            mesh.add_face([5, 6, 15], attr_dict={"direction": CardinalDirections.SOUTH_EAST})

        if rules[6]:
            mesh.add_face([6, 7, 8, 11])
            mesh.add_face([6, 7, 12, 15], attr_dict={"direction": CardinalDirections.EAST})

        if rules[7]:
            mesh.add_face([7, 0, 8])
            mesh.add_face([7, 0, 12], attr_dict={"direction": CardinalDirections.NORTH_EAST})

        # Outer ring vertical triangle faces
        from math import ceil

        for i in range(8):
            if rules[i]:
                continue

            if rules[(i - 1) % 8]:
                v0 = (i) % 8
                inner_v = int(ceil(((i + 0) % 8) * 0.5)) % 4 + 8
                v1 = inner_v
                v2 = inner_v + 4
                mesh.add_face([v0, v1, v2])

            if rules[(i + 1) % 8]:
                v0 = (i + 1) % 8
                inner_v = int(ceil(((i + 1) % 8) * 0.5)) % 4 + 8
                v1 = inner_v
                v2 = inner_v + 4
                mesh.add_face([v0, v1, v2])

        # Inner quad vertical triangle faces
        for i in range(4):
            if not rules[i * 2]:
                v0 = i + 8
                v1 = (i + 1) % 4 + 8
                v2 = v1 + 4
                v3 = v0 + 4
                mesh.add_face([v0, v1, v2, v3])

        mesh.remove_unused_vertices()
        return mesh

    @property
    def mesh(self):
        return self._last_mesh


class ColumnHeadCrossElement(ColumnHeadElement):
    """Create a cross column head element. Column head is inspired from the Crea project.
    Column head has no access to frame, because the geometry is create depending on the given directions.
    Therefore the frame is always considered as the world origin.

    Subtraction of the directions provides what type of mesh is generated:
    - HALF: 1 face
    - QUARTER: 2 faces
    - THREE_QUARTERS: 3 faces
    - FULL: 4 faces

    Parameters
    ----------
    v : dict[int, Point]
        The points, first one is always the origin.
    e : list[tuple[int, int]]
        Edges start from v0 between points v0-v1, v0-v2 and so on.
    f : list[list[int]]
        Faces between points v0-v1-v2-v3 and so on. If face vertices form already given edges, a triangle mesh face is formed.
    width : float
        The width of the column head.
    depth : float
        The depth of the column head.
    height : float
        The height of the column head.
    offset : float
        The offset of the column head.

    Returns
    -------
    :class:`ColumnHeadCrossElement`
        Column head instance

    Attributes
    ----------
    shape : :class:`compas.datastructures.Mesh`
        The base shape of the block.

    Example
    -------

    width: float = 150
    depth: float = 150
    height: float = 300
    offset: float = 210
    v: dict[int, Point] = {
        7: Point(0, 0, 0),
        5: Point(-1, 0, 0),
        6: Point(0, 1, 0),
        8: Point(0, -1, 0),
        2: Point(1, 0, 0),
    }

    e: list[tuple[int, int]] = [
        (7, 5),
        (7, 6),
        (7, 8),
        (7, 2),
    ]

    f: list[list[int]] = [[5, 7, 6, 10]]
    column_head_cross = ColumnHeadCrossElement(v=v, e=e, f=f, width=width, depth=depth, height=height, offset=offset)
    """

    @property
    def __data__(self) -> dict:
        return {
            "v": self.v,
            "e": self.e,
            "f": self.f,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "offset": self.offset,
            "is_support": self.is_support,
            "transformation": self.transformation,
            "name": self.name,
        }

    def __init__(
        self,
        v: dict[int, Point] = {
            7: Point(0, 0, 0),
            5: Point(-1, 0, 0),
            6: Point(0, 1, 0),
            8: Point(0, -1, 0),
            2: Point(1, 0, 0),
        },
        e: list[tuple[int, int]] = [
            (7, 5),
            (7, 6),
            (7, 8),
            (7, 2),
        ],
        f: list[list[int]] = [[5, 7, 6, 10]],
        width=150,
        depth=150,
        height=300,
        offset=210,
        is_support: bool = False,
        transformation: Optional[Transformation] = None,
        name: Optional[str] = None,
    ) -> "ColumnHeadCrossElement":
        super().__init__(transformation=transformation, name=name)
        self.is_support = is_support
        self.v = v
        self.e = e
        self.f = f
        self.width = width
        self.depth = depth
        self.height = height
        self.offset = offset

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the column head.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        column_head_cross_shape: CrossBlockShape = CrossBlockShape(self.v, self.e, self.f, self.width, self.depth, self.height, self.offset)
        return column_head_cross_shape.mesh.copy()  # Copy because the meshes are created only once.

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_aabb(self, inflate: float = 0.0) -> Box:
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The axis-aligned bounding box.
        """
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate: float = 0.0) -> Box:
        """Compute the oriented bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The oriented bounding box.
        """
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        from compas.geometry import convex_hull_numpy

        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    def compute_contact(self, target_element: Element, type: str = "") -> ContactInterface:
        """Computes the contact interaction of the geometry of the elements that is used in the model's add_contact method.

        Returns
        -------
        :class:`compas_model.interactions.ContactInterface`
            The ContactInteraction that is applied to the neighboring element. One pair can have one or multiple variants.
        target_element : Element
            The target element to compute the contact interaction.
        type : str, optional
            The type of contact interaction, if different contact are possible between the two elements.

        """
        # Traverse up to the class one before the Element class.add()
        # Create a function name based on the target_element class name.
        parent_class = target_element.__class__
        while parent_class.__bases__[0] != Element:
            parent_class = parent_class.__bases__[0]

        parent_class_name = parent_class.__name__.lower().replace("element", "")
        method_name = f"_compute_contact_with_{parent_class_name}"
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Unsupported target element type: {type(target_element)}")

        return method(target_element, type)

    def _compute_contact_with_column(self, target_element: "ColumnElement", type: str) -> "ContactInterface":
        # Scenario:
        # Iterate Columns edges model.cell_network.edges_where({"is_column": True})
        # Check if edge vertex is in self.column_head_to_vertex
        # If it does, model.add_contact(...)

        # From the most distance axis point find the nearest column_head frame:
        p: Point = Point(0, 0, 0).transformed(self.modeltransformation)
        axis: Point = target_element.axis.transformed(target_element.modeltransformation)
        column_head_is_closer_to_base: bool = axis.start.distance_to_point(p) > axis.end.distance_to_point(p)

        polygon: Polygon = self.modelgeometry.face_polygon(0)  # ColumnHead is on the bottom
        frame0: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], (polygon[2] - polygon[1]) * -1)
        polygon: Polygon = self.modelgeometry.face_polygon(1)  # ColumnHead is on the top
        frame1: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], (polygon[2] - polygon[1]) * 1)

        contact_frame: Frame = frame0 if column_head_is_closer_to_base else frame1

        return ContactInterface(points=[], frame=contact_frame)

    def _compute_contact_with_beam(self, target_element: "BeamElement", type: str) -> "ContactInterface":
        # Scenario:
        # Iterate Beams edges model.tcell_network.edges_where({"is_beam": True})
        # Check if the ColumnHead is on the left or right side of the beam-
        # Based on orientation compute the Cardinal axis.
        # The Cardinal axis allows to find the nearest column_head frame.
        # Lastly add the contact.

        p: Point = Point(0, 0, 0).transformed(self.modeltransformation)
        axis: Point = target_element.axis.transformed(target_element.modeltransformation)
        column_head_is_closer_to_start: bool = axis.start.distance_to_point(p) < axis.end.distance_to_point(p)

        direction: Vector = axis[1] - axis[0] if column_head_is_closer_to_start else axis[0] - axis[1]
        cardinal_direction: int = ColumnHeadCrossElement.closest_direction(direction)
        polygon: Polygon = self.modelgeometry.face_polygon(list(self.modelgeometry.faces_where(conditions={"direction": cardinal_direction}))[0])
        contact_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])

        return ContactInterface(points=[], frame=contact_frame)

    def _compute_contact_with_plate(self, target_element: "PlateElement", type: str) -> "ContactInterface":
        # Scenario:
        # Find the closest point of the plate polygon.
        # From this point take next and current point to define the CardinalDirection.
        # From the CardinalDirection create the column_head frame.

        p: Point = Point(0, 0, 0).transformed(self.modeltransformation)
        polygon: Polygon = target_element.polygon.transformed(target_element.modeltransformation)

        v0: int = -1
        distance: float = 0
        for i in range(len(polygon)):
            d = p.distance_to_point(polygon[i])
            if d < distance or distance == 0:
                distance = d
                v0 = i

        v0_prev: int = (v0 + 1) % len(polygon)
        v0_next: int = (v0 - 1) % len(polygon)

        direction0 = ColumnHeadCrossElement.closest_direction(polygon[v0_prev] - polygon[v0])  # CardinalDirections
        direction1 = ColumnHeadCrossElement.closest_direction(polygon[v0_next] - polygon[v0])  # CardinalDirections
        direction_angled = ColumnHeadCrossElement.get_direction_combination(direction0, direction1)
        polygon: Polygon = self.modelgeometry.face_polygon(list(self.modelgeometry.faces_where(conditions={"direction": direction_angled}))[0])
        contact_frame: Frame = polygon.frame.translated([0, 0, 0.1])

        return ContactInterface(points=[], frame=contact_frame)

    # =============================================================================
    # Constructors
    # =============================================================================

    def rebuild(
        self,
        v: list[Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
    ) -> "None":
        """Rebuild the column head based on the cell netowrk adjacency.

        Parameters
        ----------
        v : dict[int, Point]
            The points, first one is always the origin.
        e : list[tuple[int, int]]
            Edges starts from v0 between points v0-v1, v0-v2 and so on.
        f : list[list[int]]
            Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.

        Returns
        -------
        None
        """

        self.v = v
        self.e = e
        self.f = f

    @staticmethod
    def closest_direction(
        vector: Vector,
        directions: dict[CardinalDirections, Vector] = {
            CardinalDirections.NORTH: Vector(0, 1, 0),
            CardinalDirections.EAST: Vector(1, 0, 0),
            CardinalDirections.SOUTH: Vector(0, -1, 0),
            CardinalDirections.WEST: Vector(-1, 0, 0),
        },
    ) -> CardinalDirections:
        """
        Find the closest cardinal direction for a given vector.

        Parameters
        -------
        vector : Vector
            The vector to compare.

        directions : dict
            A dictionary of cardinal directions and their corresponding unit vectors.

        Returns
        -------
        CardinalDirections
            The closest cardinal direction.
        """
        # Unitize the given vector
        vector.unitize()

        # Compute dot products with cardinal direction vectors
        dot_products: dict[CardinalDirections, float] = {}
        for direction, unit_vector in directions.items():
            dot_product = vector.dot(unit_vector)
            dot_products[direction] = dot_product

        # Find the direction with the maximum dot product
        closest: CardinalDirections = max(dot_products, key=dot_products.get)
        return closest

    @staticmethod
    def get_direction_combination(direction1: "CardinalDirections", direction2: "CardinalDirections") -> "CardinalDirections":
        """
        Get the direction combination of two directions.

        Parameters
        -------
        direction1 : CardinalDirections
            The first direction.
        direction2 : CardinalDirections
            The second direction.

        Returns
        -------
        CardinalDirections
            The direction combination.
        """
        direction_combinations: dict[tuple[int, int], "CardinalDirections"] = {
            (CardinalDirections.NORTH, CardinalDirections.WEST): CardinalDirections.NORTH_WEST,
            (CardinalDirections.WEST, CardinalDirections.NORTH): CardinalDirections.NORTH_WEST,
            (CardinalDirections.WEST, CardinalDirections.SOUTH): CardinalDirections.SOUTH_WEST,
            (CardinalDirections.SOUTH, CardinalDirections.WEST): CardinalDirections.SOUTH_WEST,
            (CardinalDirections.SOUTH, CardinalDirections.EAST): CardinalDirections.SOUTH_EAST,
            (CardinalDirections.EAST, CardinalDirections.SOUTH): CardinalDirections.SOUTH_EAST,
            (CardinalDirections.NORTH, CardinalDirections.EAST): CardinalDirections.NORTH_EAST,
            (CardinalDirections.EAST, CardinalDirections.NORTH): CardinalDirections.NORTH_EAST,
        }
        return direction_combinations[(direction1, direction2)]
