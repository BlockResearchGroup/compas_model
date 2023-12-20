from compas.geometry import Polygon, Translation, Frame
from compas_model.elements import Plate
from compas_model.model import Model
from compas_model.viewer.viewer_model import ViewerModel

if __name__ == "__main__":

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Create plate from two polygons.
    # --------------------------------------------------------------------------
    polygon0 = Polygon.from_sides_and_radius_xy(6, 5)
    polygon1 = Polygon.from_sides_and_radius_xy(6, 5)
    xform = Translation.from_vector([0, 0, 0.2])
    polygon1.transform(xform)
    plate = Plate(polygon0=polygon0, polygon1=polygon1, compute_loft=True)
    plate.transform_to_frame(Frame([0, 0, 1], [1, 0, 0], [0, 1, 0.5]))

    # --------------------------------------------------------------------------
    # Or test the example file.
    # --------------------------------------------------------------------------
    plate = Plate.from_minimal_example()
    model.add_element("my_plate", plate)

    # --------------------------------------------------------------------------
    # Vizualize model.
    # --------------------------------------------------------------------------	
    ViewerModel.run(model, scale_factor=1)
