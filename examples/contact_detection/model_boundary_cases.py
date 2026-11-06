"""Visual checks of exact, tolerance-based, and absent mesh contacts.

Run with ``--no-viewer`` to execute the assertions without opening a window.
The red overlays are the contact meshes produced by ``mesh_mesh_contacts``.
"""

import sys

from _viewer import AMBER
from _viewer import BLUE
from _viewer import GREEN
from _viewer import GREY
from _viewer import RED
from _viewer import show_scene

from compas.geometry import Box
from compas.geometry import Frame
from compas_model.elements import MeshElement
from compas_model.models import Model

specifications = [
    ("exact face contact", -1.5, 0.0, 0.0, 1, GREEN),
    ("gap accepted by tolerance", 0.0, 0.0005, 0.001, 1, AMBER),
    ("gap outside tolerance", 1.5, 0.002, 0.001, 0, GREY),
]

rows = []
for label, y, gap, tolerance, expected, color in specifications:
    model = Model()
    mesh_a = Box(1, 1, 1, frame=Frame([0, y, 0])).to_polygonal_surface().to_mesh()
    mesh_b = Box(1, 1, 1, frame=Frame([1 + gap, y, 0])).to_polygonal_surface().to_mesh()
    element_a = model.add_element(MeshElement(geometry=mesh_a, name="A"))
    element_b = model.add_element(MeshElement(geometry=mesh_b, name="B"))
    model.compute_contacts(tolerance=tolerance)
    contacts = [contact for record in model.contact_records() for contact in record.contacts]

    assert len(contacts) == expected
    if contacts:
        assert contacts[0].size == 1.0

    rows.append((label, y, tolerance, element_a, element_b, contacts, color))
    print(f"{label}: tolerance={tolerance}, contacts={len(contacts)}")

if "--no-viewer" not in sys.argv:
    objects = []
    labels = []
    for label, y, tolerance, element_a, element_b, contacts, color in rows:
        objects.extend(
            [
                (element_a.final_geometry, f"{label}: A", BLUE, 0.35),
                (element_b.final_geometry, f"{label}: B", color, 0.35),
            ]
        )
        objects.extend((contact.mesh, f"{label}: contact", RED, 1.0) for contact in contacts)
        labels.append((f"{label}: {len(contacts)} contact(s), tol={tolerance:g}", (-0.6, y + 0.7, 0.7), color))
    show_scene("Model contacts: boundary and tolerance cases", objects, labels)
