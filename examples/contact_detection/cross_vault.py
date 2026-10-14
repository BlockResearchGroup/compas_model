"""Compute and visualize contacts in the cross-vault block model.

Each named object in ``data/cross_vault.obj`` becomes one mesh element while
preserving the original polygonal faces. Blocks participating in contact are
translucent blue, isolated blocks are grey, and the computed contact-interface
meshes are opaque red.

Run with ``--no-viewer`` to compute and report the contacts without opening a
window.
"""

import sys
from pathlib import Path

from _viewer import BLUE
from _viewer import GREY
from _viewer import RED
from _viewer import show_scene

from compas.datastructures import Mesh
from compas.files import OBJ
from compas_model.elements import Element
from compas_model.models import Model

DATA = Path(__file__).parents[2] / "data" / "cross_vault.obj"
TOLERANCE = 0.01
MINIMUM_AREA = 0.01


class BlockElement(Element):
    """Mesh element used by the standalone cross-vault example."""

    def compute_elementgeometry(self, include_features=False) -> Mesh:
        geometry = self.geometry
        if not isinstance(geometry, Mesh):
            raise TypeError("BlockElement requires mesh geometry.")
        return geometry

    def compute_aabb(self, inflate=1.0):
        return self.modelgeometry.aabb()


def load_blocks(filepath=DATA) -> list[BlockElement]:
    """Load every named OBJ object as an independent block element."""
    obj = OBJ(filepath)
    objects = obj.objects
    if objects is None:
        raise ValueError(f"The OBJ file contains no named objects: {filepath}")
    blocks = []
    for name, (vertices, faces) in objects.items():
        mesh = Mesh.from_vertices_and_faces(vertices, faces)
        blocks.append(BlockElement(geometry=mesh, name=name))
    return blocks


def build_example():
    model = Model()
    blocks = model.add_elements(load_blocks())
    model.compute_contacts(tolerance=TOLERANCE, minimum_area=MINIMUM_AREA)
    contacts = list(model.contacts())
    contact_edges = [edge for edge in model.graph.edges() if model.graph.edge_attribute(edge, name="contacts")]

    assert len(blocks) == 184
    assert len(contact_edges) == 257
    assert len(contacts) == 257
    assert all(contact.size >= MINIMUM_AREA for contact in contacts)
    return model, blocks, contact_edges, contacts


def main(show=True):
    model, blocks, contact_edges, contacts = build_example()
    connected_nodes = {node for edge in contact_edges for node in edge}
    total_area = sum(contact.size for contact in contacts)

    print(f"blocks: {len(blocks)}")
    print(f"contacting pairs: {len(contact_edges)}")
    print(f"contact regions: {len(contacts)}")
    print(f"total contact area: {total_area:.3f}")

    if show:
        objects = []
        for block in blocks:
            color = BLUE if block.graphnode in connected_nodes else GREY
            objects.append((block.modelgeometry, block.name, color, 0.28))
        contact_mesh = contacts[0].mesh.copy()
        for contact in contacts[1:]:
            contact_mesh.join(contact.mesh)
        objects.append((contact_mesh, "all contact interfaces", RED, 1.0))

        labels = [
            (
                f"{len(blocks)} blocks | {len(contact_edges)} pairs | {len(contacts)} contact regions",
                (-175, -200, 190),
                RED,
            )
        ]
        show_scene("Cross vault: detected block contacts", objects, labels)

    return model


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
