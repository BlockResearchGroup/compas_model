import pytest
from compas.data import json_dumps
from compas.data import json_loads
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.tolerance import TOL

from compas_model.algorithms import brep_brep_contacts
from compas_model.algorithms import mesh_mesh_contacts
from compas_model.geometry import PlanarRegion
from compas_model.interactions import Contact


CONTACT_CASES = [
    ([1, 0, 0], 1),
    ([0, 1, 0], 1),
    ([0, 0, 1], 1),
    ([1, 0.5, 0], 0.5),
    ([1, 0, 0.5], 0.5),
    ([1, 0.5, 0.5], 0.25),
    ([0.5, 1, 0], 0.5),
    ([0, 1, 0.5], 0.5),
    ([0.5, 1, 0.5], 0.25),
    ([0.5, 0, 1], 0.5),
    ([0, 0.5, 1], 0.5),
    ([0.5, 0.5, 1], 0.25),
]


@pytest.mark.parametrize(("vector", "size"), CONTACT_CASES)
def test_mesh_mesh_contacts(vector, size):
    box1 = Box(1, 1, 1)
    box2 = Box(1, 1, 1)
    box2.translate(vector)

    box1_mesh = box1.to_mesh()
    box2_mesh = box2.to_mesh()
    contacts = mesh_mesh_contacts(box1_mesh, box2_mesh)

    assert len(contacts) == 1
    assert TOL.is_close(contacts[0].size, size)


@pytest.mark.parametrize(("vector", "size"), CONTACT_CASES)
def test_brep_brep_contacts(vector, size):
    pytest.importorskip("compas_occ")
    box1 = Box(1, 1, 1)
    box2 = Box(1, 1, 1)
    box2.translate(vector)

    contacts = brep_brep_contacts(box1.to_brep(), box2.to_brep())

    assert len(contacts) == 1
    assert TOL.is_close(contacts[0].size, size)


@pytest.mark.parametrize("representation", ["mesh", "brep"])
def test_contacts_exclude_edge_only_contact(representation):
    if representation == "brep":
        pytest.importorskip("compas_occ")

    box1 = Box(1, 1, 1)
    box2 = Box(1, 1, 1)
    box2.translate([1, 1, 0])

    if representation == "mesh":
        assert mesh_mesh_contacts(box1.to_mesh(), box2.to_mesh()) == []
    else:
        assert brep_brep_contacts(box1.to_brep(), box2.to_brep()) == []


def test_mesh_contacts_return_disconnected_regions_separately():
    u_points = [(0, 0, 0), (3, 0, 0), (3, 3, 0), (2, 3, 0), (2, 1, 0), (1, 1, 0), (1, 3, 0), (0, 3, 0)]
    bar_points = [(-1, 2, 0), (-1, 2.5, 0), (4, 2.5, 0), (4, 2, 0)]
    u_mesh = Mesh.from_vertices_and_faces(u_points, [list(range(len(u_points)))])
    bar_mesh = Mesh.from_vertices_and_faces(bar_points, [list(range(len(bar_points)))])

    contacts = mesh_mesh_contacts(u_mesh, bar_mesh, minimum_area=0.01)
    repeated = mesh_mesh_contacts(u_mesh, bar_mesh, minimum_area=0.01)

    assert len(contacts) == 2
    assert all(TOL.is_close(contact.size, 0.5) for contact in contacts)
    assert [contact.frame.point for contact in contacts] == [contact.frame.point for contact in repeated]
    assert {contact.frame.point.x for contact in contacts} == {0.5, 2.5}


def test_mesh_contacts_apply_coplanarity_tolerance():
    source = Mesh.from_vertices_and_faces([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [[0, 1, 2, 3]])
    target = Mesh.from_vertices_and_faces([(0, 0, 0.0005), (0, 1, 0.0005), (1, 1, 0.0005), (1, 0, 0.0005)], [[0, 1, 2, 3]])

    assert mesh_mesh_contacts(source, target, tolerance=0.0001) == []
    assert len(mesh_mesh_contacts(source, target, tolerance=0.001)) == 1


def test_mesh_contacts_skip_nonplanar_polygon_faces():
    points = [(0, 0, 0), (1, 0, 0), (1, 1, 0.1), (0, 1, 0)]
    source = Mesh.from_vertices_and_faces(points, [[0, 1, 2, 3]])
    target = Mesh.from_vertices_and_faces(points, [[3, 2, 1, 0]])

    assert mesh_mesh_contacts(source, target, tolerance=0.001) == []


def test_contact_region_is_authoritative_and_serializable():
    exterior = Polygon([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]])
    hole = Polygon([[1, 1, 0], [1, 3, 0], [3, 3, 0], [3, 1, 0]])
    contact = Contact(region=PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY()))
    restored = json_loads(json_dumps(contact))

    assert isinstance(restored, Contact)
    assert isinstance(restored.geometry, PlanarRegion)
    assert len(restored.holes) == 1
    assert TOL.is_close(restored.size, 12.0)
    assert TOL.is_close(restored.mesh.area(), 12.0)


def test_contact_brep_preserves_holes_and_net_area():
    pytest.importorskip("compas_occ")
    exterior = Polygon([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]])
    hole = Polygon([[1, 1, 0], [1, 3, 0], [3, 3, 0], [3, 1, 0]])
    contact = Contact(region=PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY()))

    assert TOL.is_close(contact.brep.area, contact.size)


def test_brep_contacts_preserve_holes_and_net_area():
    pytest.importorskip("compas_occ")
    exterior = Polygon([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]])
    hole = Polygon([[1, 1, 0], [1, 3, 0], [3, 3, 0], [3, 1, 0]])
    source = Contact(region=PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY())).brep
    target = Polygon([[0, 4, 0], [4, 4, 0], [4, 0, 0], [0, 0, 0]]).to_brep()

    contacts = brep_brep_contacts(source, target, minimum_area=0.01)

    assert len(contacts) == 1
    assert len(contacts[0].holes) == 1
    assert TOL.is_close(contacts[0].size, 12.0)
    assert TOL.is_close(contacts[0].mesh.area(), 12.0)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"tolerance": -1}, "tolerance"),
        ({"minimum_area": -1}, "minimum area"),
    ],
)
def test_contacts_reject_invalid_options(kwargs, message):
    mesh = Box(1, 1, 1).to_mesh()
    with pytest.raises(ValueError, match=message):
        mesh_mesh_contacts(mesh, mesh, **kwargs)
