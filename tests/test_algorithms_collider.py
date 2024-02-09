from compas.geometry import Box, Frame, Polygon
from compas.datastructures import Mesh
from compas_model.algorithms import collider


def test_is_aabb_aabb_collision():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([1.0, 0, 0], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    assert collider.is_aabb_aabb_collision(box0, box1) is True


def test_is_box_box_collision_parallel_face():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([1, 0, 0], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    assert collider.is_box_box_collision(box0, box1) is True


def test_is_box_box_collision_edge():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([1, 1, 0], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    assert collider.is_box_box_collision(box0, box1) is True


def test_is_box_box_collision_vertex():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([1, 1, 1], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    assert collider.is_box_box_collision(box0, box1) is True


def test_is_box_box_collision_rotated():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([0.0, 0.85, 0.92], [1, 0, 0], [0, 0.87, 0.48])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    assert collider.is_box_box_collision(box0, box1) is False


def test_is_box_box_collision_inside():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=0.5, ysize=0.5, zsize=0.5)
    assert collider.is_box_box_collision(box0, box1) is True


def test_is_face_to_face_collision():
    frame0 = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
    frame1 = Frame([1.0, 0, 0], [1, 0, 0], [0, 1, 0])
    box0 = Box(frame=frame0, xsize=1, ysize=1, zsize=1)
    box1 = Box(frame=frame1, xsize=1, ysize=1, zsize=1)
    v0, f0 = box0.to_vertices_and_faces()
    v1, f1 = box1.to_vertices_and_faces()
    mesh0 = Mesh.from_vertices_and_faces(v0, f0)
    mesh1 = Mesh.from_vertices_and_faces(v1, f1)
    points_list_0 = mesh0.to_polygons()
    points_list_1 = mesh1.to_polygons()
    polygons0 = []
    for points in points_list_0:
        polygons0.append(Polygon(points))
    polygons1 = []
    for points in points_list_1:
        polygons1.append(Polygon(points))

    result = collider.is_face_to_face_collision(
        polygons0, polygons1, None, None, 0.01, 0.01, True
    )
    assert result[0][0] == (2, 4)


if __name__ == "__main__":
    test_is_aabb_aabb_collision()
    test_is_box_box_collision_parallel_face()
    test_is_box_box_collision_edge()
    test_is_box_box_collision_vertex()
    test_is_box_box_collision_rotated()
    test_is_box_box_collision_inside()
    test_is_face_to_face_collision()
    print("All tests passed!")
