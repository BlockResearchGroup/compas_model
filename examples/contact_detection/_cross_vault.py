"""Shared cross-vault model construction for the two vault examples."""

from pathlib import Path

from compas.datastructures import Mesh
from compas.files import read_obj_meshes
from compas_model.elements import Element
from compas_model.models import Model

DATA = Path(__file__).parents[2] / "data" / "cross_vault.obj"
TOLERANCE = 0.01
MINIMUM_AREA = 0.01


class BlockElement(Element):
    """Mesh element used by the standalone cross-vault examples."""

    def compute_base_geometry(self) -> Mesh:
        geometry = self.geometry
        if not isinstance(geometry, Mesh):
            raise TypeError("BlockElement requires mesh geometry.")
        return geometry

    def compute_aabb(self, inflate: float = 1.0):
        return self.final_geometry.aabb


def build_cross_vault():
    """Build the shared cross-vault model and compute its contacts."""
    meshes = read_obj_meshes(DATA)
    if not meshes:
        raise ValueError(f"The OBJ file contains no named objects: {DATA}")

    model = Model()
    blocks = model.add_elements([BlockElement(geometry=mesh, name=mesh.name) for mesh in meshes])
    model.compute_contacts(tolerance=TOLERANCE, minimum_area=MINIMUM_AREA)
    contacts = [contact for record in model.contact_records() for contact in record.contacts]
    contact_edges = [(model.element_by_guid(record.element_a).graphnode, model.element_by_guid(record.element_b).graphnode) for record in model.contact_records()]

    assert len(blocks) == 184
    assert len(contact_edges) == 257
    assert len(contacts) == 257
    assert all(contact.size >= MINIMUM_AREA for contact in contacts)

    return model, blocks, contact_edges, contacts
