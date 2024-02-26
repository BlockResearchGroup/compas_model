from compas.geometry import Polygon, Translation, Frame, Transformation
from compas_model.elements import PlateElement
from compas_model.model import Model

# --------------------------------------------------------------------------
# Create a plate from polygon and thickness.
# --------------------------------------------------------------------------
polygon0 = Polygon.from_sides_and_radius_xy(6, 5)

polygon0 = Polygon(points=[
    [0, 0, 0],
    [5, 0, 0],
    [5, 5, 0],
    [10, 5, 0],
    [10, 15, 0],
    [0, 10, 0],

])

# Uncomment to verify the plate is initialized correctly regardless of the polygon winding.
# polygon0.points.reverse()
plate = PlateElement(polygon=polygon0, thickness=1, compute_loft=False)

# --------------------------------------------------------------------------
# Create a plate from two polygons.
# --------------------------------------------------------------------------
plate = PlateElement.from_two_polygons(polygon0, polygon0.transformed(Translation.from_vector([0, 0.2, 0.2])))

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
plate = PlateElement.from_json("data/plate.json")

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_element(plate)
print("Beam plate belongs to the following ElementNode: ",  plate.tree_node)
