from compas.geometry import Polygon, Translation, Frame, Transformation
from compas_model.elements import Plate
from compas_model.model import Model
from compas_model.viewer import ViewerModel


# --------------------------------------------------------------------------
# Create a plate from polygon and thickness.
# --------------------------------------------------------------------------
polygon0 = Polygon.from_sides_and_radius_xy(6, 5)
holes = Polygon.from_sides_and_radius_xy(5, 3)
plate = Plate(polygon=polygon0, thickness=1)

# --------------------------------------------------------------------------
# Create a plate from two polygons.
# --------------------------------------------------------------------------
polygon1 = polygon0.copy()
xform = Translation.from_vector([0, 0.2, 0.2])
polygon1.transform(xform)

plate = Plate.from_two_polygons(polygon0, polygon1)

# --------------------------------------------------------------------------
# Create a plate from points and vectors.
# --------------------------------------------------------------------------
plate = Plate.from_points_and_vectors(
    points=polygon0.points,
    vectors=[
        polygon1.points[i] - polygon0.points[i] for i in range(len(polygon0.points))
    ],
    thickness=1,
    offset=1,
)

# --------------------------------------------------------------------------
# Transform and copy the plate.
# --------------------------------------------------------------------------
xform = Transformation.from_frame_to_frame(
    Frame.worldXY(), Frame([0, 0, 0], [1, 0, 0], [0, 1, 0.5])
)
plate.transform(xform)
plate = plate.copy()

# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------
plate.to_json("data/plate.json", pretty=True)
plate = Plate.from_json("data/plate.json")

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_element("my_plate", plate)

# --------------------------------------------------------------------------
# Vizualize model.
# --------------------------------------------------------------------------
ViewerModel.show(model, scale_factor=1)
