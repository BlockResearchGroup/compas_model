from compas.datastructures import CellNetwork as BaseCellNetwork
from compas.datastructures import Graph
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry.transformation import Transformation
from compas.tolerance import TOL
from compas_model.elements import BeamElement  # noqa: F401
from compas_model.elements import ColumnElement  # noqa: F401
from compas_model.elements import ColumnHeadElement  # noqa: F401
from compas_model.elements import Element  # noqa: F401
from compas_model.elements import PlateElement  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.models import ElementNode  # noqa: F401
from compas_model.models import Model  # noqa: F401


class CellNetwork(BaseCellNetwork):
    @property
    def points(self):
        points: list[Point] = [Point(*self.vertex_coordinates(key)) for key in self.vertices()]
        return points

    @property
    def lines(self):
        lines: list[Line] = [Line(start, end) for start, end in self.edges_to_graph().to_lines()]
        return lines

    @property
    def polygons(self):
        polygons: list[Polygon] = []
        for face in self.faces():
            polygons.append(self.face_polygon(face))

        return polygons

    @classmethod
    def from_lines_and_surfaces(cls, column_and_beams: list[Line], floor_surfaces: list[Mesh], tolerance: int = 3) -> "CellNetwork":
        """Create a CellNetwork from lines and surfaces.

        Parameters
        ----------
        column_and_beams : list[Line]
            List of lines representing the columns and beams.

        floor_surfaces : list[Mesh]
            List of surfaces representing the floors.

        tolerance : int, optional
            The tolerance of the model

        Returns
        -------
        CellNetwork
            Cell network from all the geometrical information.
        """

        #######################################################################################################
        # Create a Graph from lines and mesh face edges.
        #######################################################################################################
        lines_from_user_input: list[Line] = []

        for line in column_and_beams:
            lines_from_user_input.append(Line(line[0], line[1]))

        for mesh in floor_surfaces:
            for line in mesh.to_lines():
                lines_from_user_input.append(Line(line[0], line[1]))

        graph: Graph = Graph.from_lines(lines_from_user_input, precision=tolerance)

        #######################################################################################################
        # Create a CellNetwork from the Graph and meshes.
        #######################################################################################################
        cell_network: CellNetwork = cls()
        cell_network_vertex_keys: dict[str, int] = {}  # Store vertex geometric keys to map faces to vertices

        # Add vertices to CellNetwork and store geometric keys
        for node in graph.nodes():
            xyz: list[float] = graph.node_attributes(node, "xyz")
            cell_network.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
            cell_network_vertex_keys[TOL.geometric_key(xyz, precision=tolerance)] = node

        # Add edges to CellNetwork and store geometric keys
        for edge in graph.edges():
            cell_network.add_edge(*edge)

        #######################################################################################################
        # Add vertex neighbors from the Graph to the CellNetwork.
        #######################################################################################################

        for vertex in cell_network.vertices():
            z0: float = graph.node_attributes(vertex, "xyz")[2]
            # Get horizontal neighbors
            neighbor_beams: list[int] = []

            for neighbor in graph.neighbors(vertex):
                if abs(z0 - graph.node_attributes(neighbor, "xyz")[2]) < 1 / max(1, tolerance):
                    neighbor_beams.append(neighbor)
            cell_network.vertex_attribute(vertex, "neighbors", neighbor_beams)

        #######################################################################################################
        # Add geometric attributes: is_column, is_beam, is_floor, is_facade, is_core and so on.
        #######################################################################################################

        # Edges - Beams and Columns
        for u, v in graph.edges():
            xyz_u: list[float] = graph.node_attributes(u, "xyz")
            xyz_v: list[float] = graph.node_attributes(v, "xyz")
            if not abs(xyz_u[2] - xyz_v[2]) < 1 / max(1, tolerance):
                cell_network.edge_attribute((u, v), "is_column", True)
            else:
                cell_network.edge_attribute((u, v), "is_beam", True)

        # Faces - Floors
        for mesh in floor_surfaces:
            gkeys: dict[int, str] = mesh.vertex_gkey(precision=tolerance)
            v: list[int] = [cell_network_vertex_keys[key] for key in gkeys.values() if key in cell_network_vertex_keys]
            cell_network.add_face(v, attr_dict={"is_floor": True})

        return cell_network


class GridModel(Model):
    """Class representing a grid model of a multi-story building.

    Parameters
    ----------
    name : str, optional
        The name of the model.

    Attributes
    ----------
    columns : list[Element]
        List of column elements.
    beams : list[Element]
        List of beam elements.
    floors : list[Element]
        List of floor elements.
    column_head_to_vertex : dict[Element, int]
        Mapping of column head elements to vertices.
    column_to_edge : dict[Element, tuple[int, int]]
        Mapping of column elements to edges.
    beam_to_edge : dict[Element, tuple[int, int]]
        Mapping of beam elements to edges.
    vertex_to_plates_and_faces : dict[int, list[tuple[Element, list[int]]]]
        Mapping of vertices to plates and faces.
    """

    @property
    def __data__(self):
        # in their data representation,
        # the element tree and the interaction graph
        # refer to model elements by their GUID, to avoid storing duplicate data representations of those elements
        # the elements are stored in a global list
        data = {
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(self.elements()),
            "materials": list(self.materials()),
            "element_material": {str(element.guid): str(element.material.guid) for element in self.elements() if element.material},
        }
        return data

    def __init__(self, name: str = None):
        super(GridModel, self).__init__(name=name)
        self.cell_network = None
        self.PRECISION = 3

        # CellNetwork attributes.
        self._reset__elements_by_type = True
        self._elements_by_type = {}

        # Storage of elements and indices to help assigning interactions.
        self.column_head_to_vertex: dict[Element, int] = {}
        self.column_to_edge: dict[Element, tuple[int, int]] = {}
        self.beam_to_edge: dict[Element, tuple[int, int]] = {}
        self.vertex_to_plates_and_faces: dict[int, list[tuple[Element, list[int]]]] = {}

    def _partition__elements_by_type(self):
        self._elements_by_type.clear()
        elements: list[Element] = list(self.elements())

        for element in elements:
            parent_class = element.__class__
            while parent_class.__bases__[0] != Element:
                parent_class = parent_class.__bases__[0]
            self._elements_by_type.setdefault(parent_class, []).append(element)

        self._reset__elements_by_type = False

    @property
    def columnheads(self):
        if self.reset_partitions:
            self._partition__elements_by_type()
        return self._elements_by_type[ColumnHeadElement]

    @property
    def columns(self):
        if self.reset_partitions:
            self._partition__elements_by_type()
        return self._elements_by_type[ColumnElement]

    @property
    def beams(self):
        if self.reset_partitions:
            self._partition__elements_by_type()
        return self._elements_by_type[BeamElement]

    @property
    def floors(self):
        if self.reset_partitions:
            self._partition__elements_by_type()
        return self._elements_by_type[PlateElement]

    @property
    def geometry(self):
        model_geometry: list[Mesh] = []
        for element in self.elements():
            model_geometry.append(element.modelgeometry)
        return model_geometry

    @classmethod
    def from_lines_and_surfaces(
        cls,
        columns_and_beams: list[Line],
        floor_surfaces: list[Mesh],
        tolerance: int = 3,
        # cutter_model: Element = None,
    ) -> "GridModel":
        """Create a grid model from a list of lines and meshes (single face quads).

        Parameters
        ----------
        columns_and_beams : list[Line]
            List of lines representing the columns and beams.
        floor_surfaces : list[Mesh]
            List of surfaces representing the floors.
        tolerance : int, optional
            The tolerance of the model

        Returns
        -------
        GridModel
            The grid model.
        """
        model = cls()
        model.PRECISION = tolerance

        model.cell_network = CellNetwork.from_lines_and_surfaces(columns_and_beams, floor_surfaces, tolerance=tolerance)
        return model

    def add_column_head(self, column_head: Element, edge: tuple[int, int] = None) -> ElementNode:
        """
        Add a column head to the model.
        NOTE This methods updates the attributes of the Element.

        Parameters
        ----------
        column_head : Element
            The column head element.
        edge : tuple[int, int], optional
            The edge where the column head is located.
        """

        # Get the top vertex of the column head and the axis of the column.
        axis: Line = self.cell_network.edge_line(edge)
        v1: int = edge[1]
        if axis[0][2] > axis[1][2]:
            axis = Line(axis[1], axis[0])
            v1 = edge[0]

        # Input for the ColumnHead class
        v: dict[int, Point] = {}
        e: list[tuple[int, int]] = []
        f: list[list[int]] = []

        v[v1] = self.cell_network.vertex_point(v1)

        for neighbor in self.cell_network.vertex_attribute(v1, "neighbors"):
            e.append([v1, neighbor])
            v[neighbor] = self.cell_network.vertex_point(neighbor)

        for floor in list(set(self.cell_network.vertex_faces(v1))):
            if "is_floor" in self.cell_network.face_attributes(floor):
                f.append(self.cell_network.face_vertices(floor))  # This would fail when faces would include vertical walls.

        # Create column head and add it to the model.
        column_head.rebuild(v, e, f)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(self.cell_network.vertex_point(v1)))
        column_head.transformation = orientation
        treenode: ElementNode = self.add_element(element=column_head)
        self.column_head_to_vertex[v1] = column_head

        return treenode

    def add_column(self, column: Element, edge: tuple[int, int] = None) -> ElementNode:
        """
        Add a column to the model.
        NOTE This methods updates the attributes of the Element.

        Parameters
        ----------
        column : Element
            The column element.
        edge : tuple[int, int], optional
            The edge where the column is located.
        """
        axis: Line = self.cell_network.edge_line(edge)
        if axis[0][2] > axis[1][2]:
            axis = Line(axis[1], axis[0])

        column.rebuild(height=axis.length)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [1, 0, 0], [0, 1, 0]))
        column.transformation = orientation

        self.column_to_edge[edge] = column
        treenode: ElementNode = self.add_element(element=column)

        return treenode

    def add_beam(self, beam: Element, edge: tuple[int, int] = None) -> ElementNode:
        """Add a beam to the model.
        NOTE This methods updates the attributes of the Element.

        Parameters
        ----------
        beam : Element
            The beam element.
        edge : tuple[int, int], optional
            The edge where the beam is located.
        """
        axis: Line = self.cell_network.edge_line(edge)
        beam.rebuild(length=axis.length)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1])))
        beam.transformation = orientation
        treenode: ElementNode = self.add_element(element=beam)
        self.beam_to_edge[edge] = beam

        return treenode

    def add_floor(self, plate: Element, face: int = None) -> ElementNode:
        """Add a floor to the model.
        NOTE This methods updates the attributes of the Element.

        Parameters
        ----------
        plate : Element
            The floor element.
        face : int, optional
            The face where the floor is located.
        """
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(self.cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0]))
        plate.transformation = orientation
        treenode: ElementNode = self.add_element(element=plate)

        for vertex in self.cell_network.face_vertices(face):
            if vertex in self.vertex_to_plates_and_faces:
                self.vertex_to_plates_and_faces[vertex].append((plate, self.cell_network.face_vertices(face)))
            else:
                self.vertex_to_plates_and_faces[vertex] = [(plate, self.cell_network.face_vertices(face))]

        return treenode
