from compas.geometry import Polygon
from compas_model.elements import PlateElement
from compas_viewer import Viewer

# Create an element.
points : list[list[float]] = [
    [-3, -3, 0],
    [-3, 3, 0],
    [3, 3, 0],
    [3, -3, 0],

]
polygon : Polygon = Polygon(points)
plate: PlateElement = PlateElement(polygon=polygon, thickness=0.2)
plate.copy()

# Vizualize.
viewer = Viewer()
viewer.scene.add(plate.elementgeometry)
viewer.show()
