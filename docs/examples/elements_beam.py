from compas.geometry import Line, Point
from compas_model.elements.linear import Beam
from compas_model.model import Model
from compas_model.viewer.viewer_model import ViewerModel

if __name__ == "__main__":

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Create a beam from a line and extend it and transform it.
    # --------------------------------------------------------------------------
    b0 = Beam.from_line(Line(Point(-3, 0, 0), Point(3, 0.1, 0.1)), 0.25, 0.5)
    b0.extend(0.5, 1)
    # b0.transform_to_frame(Frame([0, 0, 1], [1, 0, 0], [0, 1, 0.5]))
    model.add_elements([b0])

    # --------------------------------------------------------------------------
    # Visualize model.
    # --------------------------------------------------------------------------
    ViewerModel.run(model, scale_factor=1)
