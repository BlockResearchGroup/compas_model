"""Visual checks of exact, tolerance-based, and absent model contacts.

Run with ``--no-viewer`` to execute the assertions without opening a window.
The red overlays are the contact meshes produced by ``Model.compute_contacts``.
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


def build_row(y, gap, tolerance):
    model = Model()
    a = model.add_element(MeshElement(geometry=Box(1, 1, 1, frame=Frame([0, y, 0])).to_mesh(), name="A"))
    b = model.add_element(MeshElement(geometry=Box(1, 1, 1, frame=Frame([1 + gap, y, 0])).to_mesh(), name="B"))
    model.compute_contacts(tolerance=tolerance)
    return a, b, list(model.contacts())


def build_example():
    rows = [
        ("exact face contact", -1.5, 0.0, 0.0, 1, GREEN),
        ("gap accepted by tolerance", 0.0, 0.0005, 0.001, 1, AMBER),
        ("gap outside tolerance", 1.5, 0.002, 0.001, 0, GREY),
    ]
    results = []
    for label, y, gap, tolerance, expected, color in rows:
        a, b, contacts = build_row(y, gap, tolerance)
        assert len(contacts) == expected
        if contacts:
            assert contacts[0].size == 1.0
        results.append((label, y, tolerance, a, b, contacts, color))
    return results


def main(show=True):
    rows = build_example()
    for label, _, tolerance, _, _, contacts, _ in rows:
        print(f"{label}: tolerance={tolerance}, contacts={len(contacts)}")

    if show:
        objects = []
        labels = []
        for label, y, tolerance, a, b, contacts, color in rows:
            objects.extend(
                [
                    (a.modelgeometry, f"{label}: A", BLUE, 0.35),
                    (b.modelgeometry, f"{label}: B", color, 0.35),
                ]
            )
            objects.extend((contact.mesh, f"{label}: contact", RED, 1.0) for contact in contacts)
            labels.append((f"{label}: {len(contacts)} contact(s), tol={tolerance:g}", (-0.6, y + 0.7, 0.7), color))
        show_scene("Model contacts: boundary and tolerance cases", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
