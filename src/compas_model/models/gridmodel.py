from typing import Type

from compas.datastructures import CellNetwork as BaseCellNetwork
from compas.datastructures import Graph
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry.transformation import Transformation
from compas.tolerance import TOL
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.interactions import SlicerModifier
from compas_model.models import Model  # noqa: F401


class CellNetwork(BaseCellNetwork):
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
        _cell_network: CellNetwork = cls()
        cell_network_vertex_keys: dict[str, int] = {}  # Store vertex geometric keys to map faces to vertices

        # Add vertices to CellNetwork and store geometric keys
        for node in graph.nodes():
            xyz: list[float] = graph.node_attributes(node, "xyz")
            _cell_network.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
            cell_network_vertex_keys[TOL.geometric_key(xyz, precision=tolerance)] = node

        # Add edges to CellNetwork and store geometric keys
        for edge in graph.edges():
            _cell_network.add_edge(*edge)

        #######################################################################################################
        # Add vertex neighbors from the Graph to the CellNetwork.
        #######################################################################################################

        for vertex in _cell_network.vertices():
            z0: float = graph.node_attributes(vertex, "xyz")[2]
            # Get horizontal neighbors
            neighbor_beams: list[int] = []

            for neighbor in graph.neighbors(vertex):
                if abs(z0 - graph.node_attributes(neighbor, "xyz")[2]) < 1 / max(1, tolerance):
                    neighbor_beams.append(neighbor)
            _cell_network.vertex_attribute(vertex, "neighbors", neighbor_beams)

        #######################################################################################################
        # Add geometric attributes: is_column, is_beam, is_floor, is_facade, is_core and so on.
        #######################################################################################################

        # Edges - Beams and Columns
        for u, v in graph.edges():
            xyz_u: list[float] = graph.node_attributes(u, "xyz")
            xyz_v: list[float] = graph.node_attributes(v, "xyz")
            if not abs(xyz_u[2] - xyz_v[2]) < 1 / max(1, tolerance):
                _cell_network.edge_attribute((u, v), "is_column", True)
            else:
                _cell_network.edge_attribute((u, v), "is_beam", True)

        # Faces - Floors
        for mesh in floor_surfaces:
            gkeys: dict[int, str] = mesh.vertex_gkey(precision=tolerance)
            v: list[int] = [cell_network_vertex_keys[key] for key in gkeys.values() if key in cell_network_vertex_keys]
            _cell_network.add_face(v, attr_dict={"is_floor": True})

        return _cell_network


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

    all_geo = []

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
        self._cell_network = None
        self.PRECISION = 3
        self.all_geo = []

        # CellNetwork attributes.
        self.columns = []
        self.beams = []
        self.floors = []

        # Storage of elements and indices to assing interactions.
        self.column_head_to_vertex: dict[Element, int] = {}
        self.column_to_edge: dict[Element, tuple[int, int]] = {}
        self.beam_to_edge: dict[Element, tuple[int, int]] = {}
        self.vertex_to_plates_and_faces: dict[int, list[tuple[Element, list[int]]]] = {}

    @property
    def points(self):
        points: list[Point] = [Point(*self._cell_network.vertex_coordinates(key)) for key in self._cell_network.vertices()]
        return points

    @property
    def lines(self):
        lines: list[Line] = [Line(start, end) for start, end in self._cell_network.edges_to_graph().to_lines()]
        return lines

    @property
    def polygons(self):
        polygons: list[Polygon] = []
        for face in self._cell_network.faces():
            polygons.append(self._cell_network.face_polygon(face))

        return polygons

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

        model._cell_network = CellNetwork.from_lines_and_surfaces(columns_and_beams, floor_surfaces, tolerance=tolerance)
        model.columns = list(model._cell_network.edges_where({"is_column": True}))  # Order as in the model
        model.beams = list(model._cell_network.edges_where({"is_beam": True}))  # Order as in the model
        model.floors = list(model._cell_network.faces_where({"is_floor": True}))  # Order as in the model

        return model

    def add_column_head(self, column_head: Element, edge: tuple[int, int] = None) -> None:
        """
        Add a column head to the model.

        Parameters
        ----------
        column_head : Element
            The column head element.
        edge : tuple[int, int], optional
            The edge where the column head is located.
        """

        # Get the top vertex of the column head and the axis of the column.
        axis: Line = self._cell_network.edge_line(edge)
        v1: int = edge[1]
        if axis[0][2] > axis[1][2]:
            axis = Line(axis[1], axis[0])
            v1 = edge[0]

        # Input for the ColumnHead class
        v: dict[int, Point] = {}
        e: list[tuple[int, int]] = []
        f: list[list[int]] = []

        v[v1] = self._cell_network.vertex_point(v1)

        for neighbor in self._cell_network.vertex_attribute(v1, "neighbors"):
            e.append([v1, neighbor])
            v[neighbor] = self._cell_network.vertex_point(neighbor)

        for floor in list(set(self._cell_network.vertex_faces(v1))):
            if "is_floor" in self._cell_network.face_attributes(floor):
                f.append(self._cell_network.face_vertices(floor))  # This would fail when faces would include vertical walls.

        # Create column head and add it to the model.
        element_column_head: Element = column_head.rebuild(v, e, f)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(self._cell_network.vertex_point(v1)))
        element_column_head.transformation = orientation
        self.add_element(element=element_column_head)
        self.column_head_to_vertex[v1] = element_column_head

    def add_column(self, column: Element, edge: tuple[int, int] = None) -> None:
        """
        Add a column to the model.

        Parameters
        ----------
        column : Element
            The column element.
        edge : tuple[int, int], optional
            The edge where the column is located.
        """
        axis: Line = self._cell_network.edge_line(edge)
        if axis[0][2] > axis[1][2]:
            axis = Line(axis[1], axis[0])

        element_column: Element = column.rebuild(height=axis.length)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [1, 0, 0], [0, 1, 0]))
        element_column.transformation = orientation

        self.add_element(element=element_column)
        self.column_to_edge[edge] = element_column

    def add_beam(self, beam: Element, edge: tuple[int, int] = None) -> None:
        """Add a beam to the model.

        Parameters
        ----------
        beam : Element
            The beam element.
        edge : tuple[int, int], optional
            The edge where the beam is located.
        """
        axis: Line = self._cell_network.edge_line(edge)
        element: Element = beam.rebuild(length=axis.length)
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1])))
        element.transformation = orientation
        self.add_element(element=element)
        self.beam_to_edge[edge] = element

    def add_floor(self, plate: Element, face: int = None) -> None:
        """Add a floor to the model.

        Parameters
        ----------
        plate : Element
            The floor element.
        face : int, optional
            The face where the floor is located.
        """
        plate_element: Element = plate.copy()
        orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(self._cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0]))
        plate_element.transformation = orientation
        self.add_element(element=plate_element)

        for vertex in self._cell_network.face_vertices(face):
            if vertex in self.vertex_to_plates_and_faces:
                self.vertex_to_plates_and_faces[vertex].append((plate_element, self._cell_network.face_vertices(face)))
            else:
                self.vertex_to_plates_and_faces[vertex] = [(plate_element, self._cell_network.face_vertices(face))]

    def _sort_edge(self, edge: tuple[int, int], x=False, y=False, z=True) -> tuple[int, int]:
        """
        Sort the edge based on the axis of the edge.

        Parameters
        ----------
        edge : tuple[int, int]
            The edge to sort.
        x : bool, optional
            Sort based on x-axis.
        y : bool, optional
            Sort based on y-axis.
        z : bool, optional
            Sort based on z-axis.

        Returns
        -------
        tuple[int, int]
            The sorted edge.
        """
        axis: Line = self._cell_network.edge_line(edge)
        v1, v0 = edge[1], edge[0]

        for i, flag in enumerate([x, y, z]):
            if flag and axis[0][i] > axis[1][i]:
                axis = Line(axis[1], axis[0])
                v1, v0 = edge[0], edge[1]

        return v1, v0

    def add_interaction_columnhead_and_column(
        self, edge: tuple[int, int], modifier_type: Type[Interaction] = None, elements: list[Element] = None, apply_to_start: bool = True, apply_to_end: bool = True
    ) -> None:
        """Add an interaction between a column head and a column.

        Parameters
        ----------
        edge : tuple[int, int]
            The edge where the column is located.
        modifier_type : Type[Interaction], optional
            The type of interaction to add.
        elements : list[Element], optional
            The elements to apply the interaction to.
        apply_to_start : bool, optional
            Apply the interaction to the bottom of the column.
        apply_to_end : bool, optional
            Apply the interaction to the top of the column."""

        v1, v0 = self._sort_edge(edge, z=True)

        if v1 in self.column_head_to_vertex and apply_to_end:
            polygon = self.column_head_to_vertex[v1].modelgeometry.face_polygon(0)
            frame = Frame(polygon.centroid, polygon[1] - polygon[0], (polygon[2] - polygon[1]) * -1)
            xform = Transformation.from_frame_to_frame(Frame.worldXY(), frame)

            if issubclass(modifier_type, SlicerModifier):
                modifier: SlicerModifier = modifier_type(Plane.from_frame(frame))
                self.add_interaction(self.column_head_to_vertex[v1], self.column_to_edge[edge], modifier)
            elif issubclass(modifier_type, BooleanModifier):
                for element in elements:
                    element_copy = element.copy()
                    self.add_element(element_copy)
                    element_copy.transformation = xform
                    modifier: BooleanModifier = modifier_type()
                    self.add_interaction(element_copy, self.column_to_edge[edge], modifier)

        if v0 in self.column_head_to_vertex and apply_to_start:
            polygon = self.column_head_to_vertex[v1].modelgeometry.face_polygon(1)
            frame = Frame(polygon.centroid, polygon[1] - polygon[0], (polygon[2] - polygon[1]) * 1)
            xform = Transformation.from_frame_to_frame(Frame.worldXY(), frame)

            if issubclass(modifier_type, SlicerModifier):
                modifier: SlicerModifier = modifier_type(Plane.from_frame(frame))
                self.add_interaction(self.column_head_to_vertex[v0], self.column_to_edge[edge], modifier)
            elif issubclass(modifier_type, BooleanModifier):
                for element in elements:
                    element_copy = element.copy()
                    self.add_element(element_copy)
                    element_copy.transformation = xform
                    modifier: BooleanModifier = modifier_type()
                    self.add_interaction(element_copy, self.column_to_edge[edge], modifier)

    def add_interaction_columnhead_and_beam(
        self, edge: tuple[int, int], modifier_type: Type[Interaction] = None, elements: list[Element] = None, apply_to_start: bool = True, apply_to_end: bool = True
    ) -> None:
        """
        Add an interaction between a column head and a beam.

        Parameters
        ----------
        edge : tuple[int, int]
            The edge where the beam is located.
        modifier_type : Type[Interaction], optional
            The type of interaction to add.
        elements : list[Element], optional
            The elements to apply the interaction to.
        apply_to_start : bool, optional
            Apply the interaction to the start of the beam.
        apply_to_end : bool, optional
            Apply the interaction to the end of the beam.
        """
        beam_element: Element = self.beam_to_edge[edge]

        if edge[0] in self.column_head_to_vertex and apply_to_start:
            direction = ColumnHeadCrossElement.closest_direction(self._cell_network.vertex_point(edge[1]) - self._cell_network.vertex_point(edge[0]))  # CardinalDirections
            column_head_element = self.column_head_to_vertex[edge[0]]
            polygon: Polygon = column_head_element.modelgeometry.face_polygon(list(column_head_element.modelgeometry.faces_where(conditions={"direction": direction}))[0])
            frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
            xform = Transformation.from_frame_to_frame(Frame.worldXY(), frame)

            if issubclass(modifier_type, SlicerModifier):
                modifier: SlicerModifier = modifier_type(Plane.from_frame(frame))
                self.add_interaction(column_head_element, beam_element, SlicerModifier(Plane.from_frame(frame)))
            elif issubclass(modifier_type, BooleanModifier):
                for element in elements:
                    element_copy = element.copy()
                    self.add_element(element_copy)
                    element_copy.transformation = xform
                    modifier: BooleanModifier = modifier_type()
                    self.add_interaction(element_copy, self.column_to_edge[edge], modifier)

        if edge[1] in self.column_head_to_vertex:
            column_head_element = self.column_head_to_vertex[edge[1]]
            direction = ColumnHeadCrossElement.closest_direction(self._cell_network.vertex_point(edge[0]) - self._cell_network.vertex_point(edge[1]))  # CardinalDirections
            polygon: Polygon = column_head_element.modelgeometry.face_polygon(list(column_head_element.modelgeometry.faces_where(conditions={"direction": direction}))[0])
            frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
            xform = Transformation.from_frame_to_frame(Frame.worldXY(), frame)

            if issubclass(modifier_type, SlicerModifier):
                modifier: SlicerModifier = modifier_type(Plane.from_frame(frame))
                self.add_interaction(column_head_element, beam_element, SlicerModifier(Plane.from_frame(frame)))
            elif issubclass(modifier_type, BooleanModifier):
                for element in elements:
                    element_copy = element.copy()
                    self.add_element(element_copy)
                    element_copy.transformation = xform
                    modifier: BooleanModifier = modifier_type()
                    self.add_interaction(element_copy, self.column_to_edge[edge], modifier)

    def add_interaction_columnhead_and_floor(
        self,
        vertex: int,
        plates_and_faces: list[tuple[Element, list[int]]],
        modifier_type: Type[Interaction] = None,
        elements: list[Element] = None,
    ) -> None:
        """
        Add an interaction between a column head and a floor.

        Parameters
        ----------
        vertex : int
            The vertex where the floor is located.
        plates_and_faces : list[tuple[Element, list[int]]]
            List of plates and faces.
        modifier_type : Type[Interaction], optional
            The type of interaction to add.
        elements : list[Element], optional
            The elements to apply the interaction to.
        """
        if vertex not in self.column_head_to_vertex:
            return

        column_head_element = self.column_head_to_vertex[vertex]

        for plate_element, face in plates_and_faces:
            i: int = face.index(vertex)
            prev: int = (i - 1) % len(face)
            next: int = (i + 1) % len(face)
            v0 = face[i]
            v0_prev = face[prev]
            v0_next = face[next]
            direction0 = ColumnHeadCrossElement.closest_direction(self._cell_network.vertex_point(v0_prev) - self._cell_network.vertex_point(v0))  # CardinalDirections
            direction1 = ColumnHeadCrossElement.closest_direction(self._cell_network.vertex_point(v0_next) - self._cell_network.vertex_point(v0))  # CardinalDirections
            direction_angled = ColumnHeadCrossElement.get_direction_combination(direction0, direction1)
            polygon: Polygon = column_head_element.modelgeometry.face_polygon(list(column_head_element.modelgeometry.faces_where(conditions={"direction": direction_angled}))[0])
            frame: Frame = polygon.frame
            xform = Transformation.from_frame_to_frame(Frame.worldXY(), frame)

            if issubclass(modifier_type, SlicerModifier):
                modifier: SlicerModifier = modifier_type(Plane.from_frame(frame))
                self.add_interaction(column_head_element, plate_element, SlicerModifier(Plane.from_frame(frame)))
            elif issubclass(modifier_type, BooleanModifier):
                for element in elements:
                    element_copy = element.copy()
                    self.add_element(element_copy)
                    element_copy.transformation = xform
                    modifier: BooleanModifier = modifier_type()
                    self.add_interaction(element_copy, plate_element, modifier)
