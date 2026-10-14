from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from PySide6.QtWidgets import QTreeWidget
from PySide6.QtWidgets import QTreeWidgetItem

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.interactions import Contact
from compas_viewer.components.container import Container

from .controller import ModelViewer


@dataclass(frozen=True, slots=True)
class InspectorSection:
    """Named collection of read-only inspector rows."""

    title: str
    rows: tuple[tuple[str, str], ...]


class InspectableInteraction(Protocol):
    """Data required by the selection inspector for an interaction."""

    @property
    def elements(self) -> tuple[Element, Element]: ...

    @property
    def contacts(self) -> tuple[Contact, ...]: ...

    @property
    def modifiers(self) -> tuple[object, ...]: ...


def inspect_elements(controller: ModelViewer, elements: Iterable[Element]) -> tuple[InspectorSection, ...]:
    """Build read-only inspector data for selected elements.

    Parameters
    ----------
    controller
        Controller containing the corresponding scene objects.
    elements
        Selected model elements.

    Returns
    -------
    tuple[InspectorSection, ...]
        Structured rows suitable for a GUI or textual report.

    """
    selected = list(elements)
    if not selected:
        return (InspectorSection("Selection", (("Status", "No elements selected"),)),)
    if len(selected) > 1:
        counts = Counter(element.__class__.__name__ for element in selected)
        visible = sum(controller.object_for_element(element).show for element in selected)
        return (
            InspectorSection(
                "Selection",
                (
                    ("Elements", str(len(selected))),
                    ("Types", ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))),
                    ("Visible", f"{visible} / {len(selected)}"),
                ),
            ),
        )

    element = selected[0]
    scene_object = controller.object_for_element(element)
    parent = element.parent
    sections = [
        InspectorSection(
            "Identity",
            (
                ("Name", element.name or ""),
                ("Type", element.__class__.__name__),
                ("GUID", str(element.guid)),
                ("Parent", "" if parent is None else parent.name or parent.__class__.__name__),
                ("Children", str(len(element.children))),
                ("Visible", str(scene_object.show)),
                ("Selected", str(scene_object.is_selected)),
            ),
        )
    ]

    parameters = tuple((str(name), _format_value(value)) for name, value in element.__data__.items() if name not in {"name", "transformation", "features", "material"})
    if parameters:
        sections.append(InspectorSection("Parameters", parameters))

    attributes = tuple((str(name), _format_value(value)) for name, value in sorted(element.treenode.attributes.items()) if name not in {"widget", "widget_item"})
    if attributes:
        sections.append(InspectorSection("Attributes", attributes))

    material = element.material
    if material is not None:
        material_rows = [("Type", material.__class__.__name__), ("GUID", str(material.guid))]
        material_rows.extend((str(name), _format_value(value)) for name, value in material.__data__.items())
        sections.append(InspectorSection("Material", tuple(material_rows)))

    sections.append(InspectorSection("Geometry", _geometry_rows(element, controller)))
    return tuple(sections)


class ElementInspector(Container):
    """Read-only inspector for selected model elements."""

    def __init__(self, controller: ModelViewer) -> None:
        super().__init__()
        self.controller = controller
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Property", "Value"])
        assert self.layout is not None
        self.layout.addWidget(self.tree)
        self.update()

    def update(self) -> None:
        """Refresh the inspector from current controller selection."""
        self.inspect([scene_object.element for scene_object in self.controller.selected])

    def inspect(self, elements: Iterable[Element]) -> None:
        """Display structured information for selected elements."""
        self.tree.clear()
        for section in inspect_elements(self.controller, elements):
            section_item = QTreeWidgetItem([section.title, ""])
            self.tree.addTopLevelItem(section_item)
            for name, value in section.rows:
                section_item.addChild(QTreeWidgetItem([name, value]))
            section_item.setExpanded(True)
        self.tree.resizeColumnToContents(0)

    def inspect_contact(self, selection: InspectableInteraction | None) -> None:
        """Display a selected contact pair or its selected regions."""
        if selection is None:
            self.inspect([])
            return
        elements = selection.elements
        contacts: tuple[Contact, ...] = selection.contacts
        modifiers: tuple[object, ...] = selection.modifiers
        self.tree.clear()
        sections = (
            InspectorSection(
                "Contact pair",
                (
                    ("Element A", elements[0].name or elements[0].__class__.__name__),
                    ("Element B", elements[1].name or elements[1].__class__.__name__),
                    ("Regions", str(len(contacts))),
                    ("Total area", _format_value(sum(contact.size for contact in contacts))),
                    ("Modifiers", str(len(modifiers))),
                ),
            ),
            *(
                InspectorSection(
                    f"Region {index + 1}",
                    (
                        ("Area", _format_value(contact.size)),
                        ("Boundary points", str(len(contact.points))),
                        ("Holes", str(len(contact.holes))),
                        ("Mesh faces", str(contact.mesh.number_of_faces())),
                    ),
                )
                for index, contact in enumerate(contacts)
            ),
            *(
                InspectorSection(
                    f"Modifier {index + 1}",
                    (("Type", modifier.__class__.__name__), ("Value", _format_value(modifier))),
                )
                for index, modifier in enumerate(modifiers)
            ),
        )
        for section in sections:
            section_item = QTreeWidgetItem([section.title, ""])
            self.tree.addTopLevelItem(section_item)
            for name, value in section.rows:
                section_item.addChild(QTreeWidgetItem([name, value]))
            section_item.setExpanded(True)
        self.tree.resizeColumnToContents(0)


def install_element_inspector(controller: ModelViewer) -> ElementInspector:
    """Add an element and interaction inspector to the viewer sidebar."""
    inspector = ElementInspector(controller)
    controller.viewer.ui.sidebar.tabform.add_tab("Selection", container=inspector)
    return inspector


def _geometry_rows(element: Element, controller: ModelViewer) -> tuple[tuple[str, str], ...]:
    if isinstance(element, Group):
        return (("Representation", "None (group)"), ("Geometry revision", str(element.geometry_revision)))

    geometry = element.modelgeometry
    rows = [("Representation", geometry.__class__.__name__), ("Geometry revision", str(element.geometry_revision))]
    if isinstance(geometry, Mesh):
        rows.extend(
            [
                ("Vertices", str(geometry.number_of_vertices())),
                ("Edges", str(geometry.number_of_edges())),
                ("Faces", str(geometry.number_of_faces())),
            ]
        )
    elif isinstance(geometry, Brep):
        rows.extend(
            [
                ("Vertices", str(len(geometry.vertices))),
                ("Edges", str(len(geometry.edges))),
                ("Faces", str(len(geometry.faces))),
            ]
        )

    render_geometry = controller.object_for_element(element).render_geometry
    if render_geometry is not None:
        rows.extend(
            [
                ("Render vertices", str(len(render_geometry.vertices))),
                ("Render triangles", str(len(render_geometry.triangles))),
                ("Boundary segments", str(len(render_geometry.line_vertices) // 2)),
            ]
        )
    return tuple(rows)


def _format_value(value: object, limit: int = 160) -> str:
    if value is None or isinstance(value, (bool, int, float, str)):
        text = str(value)
    elif isinstance(value, (list, tuple, set)):
        text = f"{value.__class__.__name__}({len(value)})"
    elif isinstance(value, dict):
        text = f"dict({len(value)})"
    else:
        text = repr(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"
