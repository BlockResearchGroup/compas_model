from compas.geometry import Line, Point, Frame, Transformation
from compas_model.elements import BeamElement
from compas_model.model import Model


# --------------------------------------------------------------------------
# Create a beam from a line and extend it and transform it.
# --------------------------------------------------------------------------
b0 = BeamElement.from_line(
    Line(Point(-3, 0, 0), Point(3, 0.1, 0.1)),
    0.25,
    0.5,
)

# --------------------------------------------------------------------------
# Test data.
# --------------------------------------------------------------------------
b0_copy = b0.copy()
b0_copy.transform(Transformation.from_frame_to_frame(b0.frame, Frame([0, 0, 1], [1, 0, 0], [0, 0.1, 0.5])))
print(b0.dimensions)
print(b0.guid)
print(b0_copy.guid)

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_elements([b0, b0_copy])
print("Beam b0 belongs to the following ElementNode: ",  b0.tree_node)
print("Beam b0_copy belongs to the following ElementNode: ",  b0_copy.tree_node)
