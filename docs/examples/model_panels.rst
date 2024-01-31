********************************************************************************
Model Plates
********************************************************************************

.. figure:: /_images/elements_plate_application_folding.jpg
    :figclass: figure
    :class: figure-img img-fluid


Assuming you already have an algorithm for the input geometry or a file with geometry, such as .obj or .ply, you can load it into the model and define the hierarchy and interactions:

>>> top_polygons, bottom_polygons = create_folded_mesh()

Then you can create a model and add construct the plates from the top and bottom polygons:


>>> from compas_model.elements import Plate
>>> from compas_model.model import Model
>>> import elements_plate_application_folding as folding
>>> from compas_model.viewer import ViewerModel
>>> 
>>> top_polygons, bottom_polygons = folding.create_folded_mesh()
>>> model = Model()
>>> 
>>> plates = []
>>> for idx, polygon in enumerate(bottom_polygons):
>>>     plate = Plate.from_two_polygons(
>>>         polygon0=polygon,
>>>         polygon1=top_polygons[idx],
>>>     )
>>>     plates.append(plate)
>>>     model.add_element("my_plate"+str(idx), plate)
>>> 
>>> model.add_interaction("my_interaction", plates[0], plates[1])
