"""Visual check of a contact intersection with two connected components.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys

from _viewer import BLUE
from _viewer import GREEN
from _viewer import RED
from _viewer import show_scene

from compas.datastructures import Mesh
from compas_model.algorithms import mesh_mesh_contacts


def build_example():
    u_points = [(0, 0, 0), (3, 0, 0), (3, 3, 0), (2, 3, 0), (2, 1, 0), (1, 1, 0), (1, 3, 0), (0, 3, 0)]
    bar_points = [(-1, 2, 0), (-1, 2.5, 0), (4, 2.5, 0), (4, 2, 0)]
    source = Mesh.from_vertices_and_faces(u_points, [list(range(len(u_points)))])
    target = Mesh.from_vertices_and_faces(bar_points, [list(range(len(bar_points)))])
    contacts = mesh_mesh_contacts(source, target, minimum_area=0.01)

    assert len(contacts) == 2
    assert sorted(contact.size for contact in contacts) == [0.5, 0.5]
    return source, target, contacts


def main(show=True):
    source, target, contacts = build_example()
    print(f"disconnected interface: contacts={len(contacts)}, areas={[contact.size for contact in contacts]}")

    if show:
        objects = [(source, "U-shaped source", BLUE, 0.35), (target, "crossing target", GREEN, 0.35)]
        objects.extend((contact.mesh, f"contact {index}", RED, 1.0) for index, contact in enumerate(contacts, start=1))
        labels = [("two disconnected contact regions", (0.25, 3.4, 0.1), RED)]
        show_scene("Mesh contacts: disconnected regions", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
