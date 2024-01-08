from compas.geometry import Line, Point, Frame, Transformation
from compas_model.elements import Beam
from compas_model.model import Model
from compas_model.viewer import ViewerModel


# --------------------------------------------------------------------------
# Create a beam from a line and extend it and transform it.
# --------------------------------------------------------------------------
b0 = Beam.from_line(
    Line(Point(-3, 0, 0), Point(3, 0.1, 0.1)),
    0.25,
    0.5,
    None,
)
b0.extend(0.5, 1)
b0.transform(Transformation.from_frame_to_frame(b0.frame, Frame([0, 0, 1], [1, 0, 0], [0, 0.1, 0.5])))

# --------------------------------------------------------------------------
# Test data.
# --------------------------------------------------------------------------
b0 = b0.copy()

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_elements([b0])

# --------------------------------------------------------------------------
# Visualize model.
# --------------------------------------------------------------------------
ViewerModel.show(model, scale_factor=1)
