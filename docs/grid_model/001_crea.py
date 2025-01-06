from compas import json_load
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

from compas_model.elements import BeamIProfileElement
from compas_model.elements import BeamSquareElement
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import ColumnRoundElement
from compas_model.elements import ColumnSquareElement
from compas_model.elements import Element  # noqa: F401
from compas_model.elements import PlateElement
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.interactions import SlicerModifier
from compas_model.models import Model  # noqa: F401
from pathlib import Path


class CellNetwork(BaseCellNetwork):
    @classmethod
    def from_lines_and_surfaces(cls, column_and_beams: list[Line], floor_surfaces: list[Mesh], tolerance: int = 3) -> "CellNetwork":
        """Create a grid model from a list of Line and surfaces.
        You can extend user input to include facade and core surfaces.

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

    Pseudo code for the user interface:
    import compas
    from compas.scene import Scene
    from compas_grid.model import GridModel

    # Call Rhino UI.
    lines, surfaces : tuple(list[Line], list[Mesh]) = GridModel.rhino_ui()

    # Create the model.
    model = GridModel.from_lines_and_surfaces(lines, surfaces)
    model.cut()

    # Visualize the model.
    scene = Scene()
    scene.clear()
    scene.add(model)
    scene.draw()

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

    @classmethod
    def from_lines_and_surfaces(
        cls,
        columns_and_beams: list[Line],
        floor_surfaces: list[Mesh],
        tolerance: int = 3,
        column: Element = None,
        column_head: Element = None,
        beam: Element = None,
        plate: Element = None,
        cutter: Element = None,
        cutter_model: Element = None,
    ) -> "GridModel":
        """Create a grid model from a list of Line and surfaces.
        You can extend user input to include facade and core surfaces.

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

        # =============================================================================
        # Convert lines and surfaces to a CellNetwork.
        # =============================================================================
        cell_network = CellNetwork.from_lines_and_surfaces(columns_and_beams, floor_surfaces, tolerance=tolerance)

        # =============================================================================
        # Convert the CellNetwork to a GridModel.
        # =============================================================================
        cell_network_columns: list[tuple[int, int]] = list(cell_network.edges_where({"is_column": True}))  # Order as in the model
        cell_network_beams: list[tuple[int, int]] = list(cell_network.edges_where({"is_beam": True}))  # Order as in the model
        cell_network_floors: list[int] = list(cell_network.faces_where({"is_floor": True}))  # Order as in the model

        column_head_to_vertex: dict[Element, int] = {}
        column_to_edge: dict[Element, tuple[int, int]] = {}
        beam_to_edge: dict[Element, tuple[int, int]] = {}
        vertex_to_plates_and_faces: dict[int, list[tuple[Element, list[int]]]] = {}

        # =============================================================================
        # Define elements that are repetetive.
        # =============================================================================
        def add_column_head(edge):
            # Get the top vertex of the column head and the axis of the column.
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]

            # Input for the ColumnHead class
            v: dict[int, Point] = {}
            e: list[tuple[int, int]] = []
            f: list[list[int]] = []

            v[column_head_vertex] = cell_network.vertex_point(column_head_vertex)

            for neighbor in cell_network.vertex_attribute(column_head_vertex, "neighbors"):
                e.append([column_head_vertex, neighbor])
                v[neighbor] = cell_network.vertex_point(neighbor)

            for floor in list(set(cell_network.vertex_faces(column_head_vertex))):
                if "is_floor" in cell_network.face_attributes(floor):
                    f.append(cell_network.face_vertices(floor))  # This would fail when faces would include vertical walls.

            # Create column head and add it to the model.
            element_column_head: Element = column_head.rebuild(v, e, f)
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(cell_network.vertex_point(column_head_vertex)))
            element_column_head.transformation = orientation
            model.add_element(element=element_column_head)
            column_head_to_vertex[column_head_vertex] = element_column_head

        def add_column(edge):
            axis: Line = cell_network.edge_line(edge)
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])

            element_column: Element = column.rebuild(height=axis.length)
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [1, 0, 0], [0, 1, 0]))
            element_column.transformation = orientation

            model.add_element(element=element_column)
            column_to_edge[edge] = element_column

        def add_beam(edge):
            axis: Line = cell_network.edge_line(edge)
            element: Element = beam.rebuild(length=axis.length)
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1])))
            element.transformation = orientation
            model.add_element(element=element)
            beam_to_edge[edge] = element

        def add_floor(face):
            plate_element: Element = plate.copy()
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0]))
            plate_element.transformation = orientation
            print(type(plate_element))
            model.add_element(element=plate_element)

            for vertex in cell_network.face_vertices(face):
                if vertex in vertex_to_plates_and_faces:
                    vertex_to_plates_and_faces[vertex].append((plate_element, cell_network.face_vertices(face)))
                else:
                    vertex_to_plates_and_faces[vertex] = [(plate_element, cell_network.face_vertices(face))]

        def add_interaction_column_and_column_head(edge):
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            column_base_vertex: int = edge[0]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]
                column_base_vertex = edge[1]

            if column_head_vertex in column_head_to_vertex:
                interface_cutter_element: Element = cutter.copy()
                polygon = column_head_to_vertex[column_head_vertex].modelgeometry.face_polygon(0)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                polygon_frame = Frame(polygon_frame.point, polygon_frame.xaxis, -polygon_frame.yaxis)
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                interface_cutter_model: Model = cutter_model.copy()
                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, column_to_edge[edge], SlicerModifier())
                model.add_interaction(column_head_to_vertex[column_head_vertex], column_to_edge[edge], interaction=Interaction())

                interface_cutter_model: Model = cutter_model.copy()  # TODO: dont work
                interface_cutter_model_elements = []
                for element in interface_cutter_model.elements():
                    # element.transformation = orientation
                    interface_cutter_model_elements.append(element.copy())
                    interface_cutter_model_elements[-1].transformation = orientation

                model.add_element(element=interface_cutter_model_elements[0])
                model.add_interaction(interface_cutter_model_elements[0], column_to_edge[edge], SlicerModifier())
                model.add_element(element=interface_cutter_model_elements[1])
                model.add_interaction(interface_cutter_model_elements[1], column_head_to_vertex[column_head_vertex], BooleanModifier())  # Should be change to boolean difference.
                model.add_interaction(interface_cutter_model_elements[1], column_to_edge[edge], BooleanModifier())  # Should be change to boolean difference.
                model.add_interaction(column_head_to_vertex[column_head_vertex], column_to_edge[edge], interaction=Interaction())

            if column_base_vertex in column_head_to_vertex:
                interface_cutter_element: Element = cutter.copy()

                polygon = column_head_to_vertex[column_base_vertex].geometry.face_polygon(1)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, column_to_edge[edge], SlicerModifier())
                model.add_interaction(column_head_to_vertex[column_base_vertex], column_to_edge[edge], interaction=Interaction())

        def add_interaction_beam_and_column_head(edge):
            beam_element: Element = beam_to_edge[edge]

            if edge[0] in column_head_to_vertex:
                # Find face that is pointing to the beam because the mesh block has an direction attribute.
                column_head_element = column_head_to_vertex[edge[0]]
                direction = ColumnHeadCrossElement.closest_direction(cell_network.vertex_point(edge[1]) - cell_network.vertex_point(edge[0]))  # CardinalDirections
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction}))[0])

                interface_cutter_element: Element = cutter.copy()
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, beam_element, SlicerModifier())
                model.add_interaction(column_head_element, beam_element, interaction=Interaction())

            if edge[1] in column_head_to_vertex:
                column_head_element = column_head_to_vertex[edge[1]]
                direction = ColumnHeadCrossElement.closest_direction(cell_network.vertex_point(edge[0]) - cell_network.vertex_point(edge[1]))  # CardinalDirections
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction}))[0])

                interface_cutter_element: Element = cutter.copy()
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, beam_element, SlicerModifier())
                model.add_interaction(column_head_element, beam_element, interaction=Interaction())

        def add_interaction_floor_and_column_head(vertex, plates_and_faces):
            if vertex not in column_head_to_vertex:
                return

            column_head_element = column_head_to_vertex[vertex]

            for plate_element, face in plates_and_faces:
                i: int = face.index(vertex)
                prev: int = (i - 1) % len(face)
                next: int = (i + 1) % len(face)
                v0 = face[i]
                v0_prev = face[prev]
                v0_next = face[next]
                direction0 = ColumnHeadCrossElement.closest_direction(cell_network.vertex_point(v0_prev) - cell_network.vertex_point(v0))  # CardinalDirections
                direction1 = ColumnHeadCrossElement.closest_direction(cell_network.vertex_point(v0_next) - cell_network.vertex_point(v0))  # CardinalDirections
                direction_angled = ColumnHeadCrossElement.get_direction_combination(direction0, direction1)
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction_angled}))[0])

                interface_cutter_element: Element = cutter.copy()
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon.frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, plate_element, SlicerModifier())
                model.add_interaction(
                    column_head_element,  # Store the column head element in a dictionary.
                    plate_element,
                    interaction=Interaction(),
                )

        # Elements
        for edge in cell_network_columns:
            add_column_head(edge)

        for edge in cell_network_columns:
            add_column(edge)

        for edge in cell_network_beams:
            add_beam(edge)

        for face in cell_network_floors:
            add_floor(face)

        # Interactions
        # for edge in cell_network_columns:
        #     add_interaction_column_and_column_head(edge)

        # for edge in cell_network_beams:
        #     add_interaction_beam_and_column_head(edge)

        # for vertex, plates_and_faces in vertex_to_plates_and_faces.items():
        #     add_interaction_floor_and_column_head(vertex, plates_and_faces)

        return model


# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
current_dir = Path(__file__).parent
json_file_path = current_dir / "001_crea_4x4.json"

# Load the JSON file
with open(json_file_path, "r") as f:
    rhino_geometry: dict[str, list[any]] = json_load(f)

lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================

# Create Elements that will be used in the model.
column_square: ColumnSquareElement = ColumnSquareElement(width=300, depth=300)
column_round: ColumnRoundElement = ColumnRoundElement(radius=150, sides=24, height=300)
column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
beam_square: BeamSquareElement = BeamSquareElement(width=300, depth=300)
beam_i_profile: BeamIProfileElement = BeamIProfileElement(width=300, depth=300, thickness=50)
plate: PlateElement = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
slicer: SlicerModifier = SlicerModifier(Frame.worldXY())
# cutter_model: Model = CutterElement.cutter_element_model()  # A model with one screw.

# Create the Model.
# Default all elements are dirty.
model: GridModel = GridModel.from_lines_and_surfaces(
    columns_and_beams=lines, floor_surfaces=surfaces, column=column_round, column_head=column_head, beam=beam_i_profile, plate=plate, cutter=slicer
)

# Compute interactions.
# Since elements are dirty compute interactions.
geometry_interfaced: list[Mesh] = []
for element in model.elements():
    print(type(element))
    geometry_interfaced.append(element.modelgeometry)

# Change Model Elements.
# Change a column head to round, which will change the is_dirty flag to true.

# Recompute interactions model_geometry for elements with is_dirty flag.

# =============================================================================
# Visualize the model.
# =============================================================================
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()
    viewer_live.clear()
    [viewer_live.add(geometry.scaled(0.001)) for geometry in geometry_interfaced]
    # [viewer_live.add(geometry.scaled(0.001)) for geometry in compas_grid.global_property]
    viewer_live.serialize()
    viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
