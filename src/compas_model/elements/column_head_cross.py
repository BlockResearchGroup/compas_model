from enum import Enum

from compas.datastructures import Mesh
from compas.geometry import Point
from compas.geometry import Vector
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from .elements import Element


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

    @classmethod
    def get_direction_combination(cls, direction1: "CardinalDirections", direction2: "CardinalDirections") -> "CardinalDirections":
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
            direction = CrossBlockShape.closest_direction(vector)
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

            face_direction: CardinalDirections = CardinalDirections.get_direction_combination(face_edge_directions[0], face_edge_directions[1])
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


class ColumnHeadCrossElement(Element):
    """Create a column head element from a quadrant.

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
        Edges starts from v0 between points v0-v1, v0-v2 and so on.
    f : list[list[int]]
        Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.
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
    shape : :class:`compas.datastructure.Mesh`
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
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(ColumnHeadCrossElement, self).__data__
        data["v"] = self.v
        data["e"] = self.e
        data["f"] = self.f
        data["width"] = self.width
        data["depth"] = self.depth
        data["height"] = self.height
        data["offset"] = self.offset
        return data

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
        name: str = "None",
    ) -> "ColumnHeadCrossElement":
        super(ColumnHeadCrossElement, self).__init__(frame=Frame.worldXY(), name=name)
        self.v = v
        self.e = e
        self.f = f
        self.width = width
        self.depth = depth
        self.height = height
        self.offset = offset
        column_head_cross_shape: CrossBlockShape = CrossBlockShape(v, e, f, width, depth, height, offset)
        self.shape: Mesh = column_head_cross_shape.mesh.copy()  # Copy because the meshes are created only once.
        self.name = self.__class__.__name__ if name is None or name == "None" else name

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self) -> Mesh:
        """Compute the shape of the column head.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        # This method is redundant unless more specific implementation is needed...
        return self.shape

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

    # =============================================================================
    # Constructors
    # =============================================================================

    def rebuild(
        self,
        v: list[Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
    ) -> "ColumnHeadCrossElement":
        """Rebuild the column with a new height.

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
        :class:`ColumnHeadCrossElement`
            The new column head cross element.
        """
        return ColumnHeadCrossElement(v=v, e=e, f=f, width=self.width, depth=self.depth, height=self.height, offset=self.offset, name=self.name)