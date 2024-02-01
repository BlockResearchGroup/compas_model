********************************************************************************
Model Plates
********************************************************************************

.. figure:: /_images/elements_plate_application_folding.jpg
    :figclass: figure
    :class: figure-img img-fluid


Assuming you already have an algorithm, that is provided in the documentation, you can load it into the model and define the hierarchy and interactions:

>>> from compas_model.elements import Plate
>>> from compas_model.model import Model
>>> import elements_plate_application_folding as folding
>>> from compas_model.viewer import ViewerModel
>>> 
>>> top_polygons, bottom_polygons = folding.create_folded_mesh()

Then you can create a model:

>>> model = Model()

And construct the plates from the top and bottom polygons:

>>> plates = []
>>> for idx, polygon in enumerate(bottom_polygons):
>>>     plate = Plate.from_two_polygons(polygon0=polygon, polygon1=top_polygons[idx])
>>>     plates.append(plate)
>>>     model.add_element("my_plate"+str(idx), plate)

Also you can add interactions between the plates:
 
>>> # Add interaction - first wall.
>>> model.add_interaction(plates[0], plates[1])
>>> model.add_interaction(plates[1], plates[2])
>>> >model.add_interaction(plates[2], plates[3])
>>> model.add_interaction(plates[3], plates[4])
>>> model.add_interaction(plates[4], plates[5])
>>> 
>>> # Add interactions - second wall.
>>> model.add_interaction(plates[6], plates[7])
>>> model.add_interaction(plates[7], plates[8])
>>> model.add_interaction(plates[8], plates[9])
>>> model.add_interaction(plates[9], plates[10])
>>> model.add_interaction(plates[10], plates[11])
>>> 
>>> # Add interaction - roof.
>>> model.add_interaction(plates[12], plates[13])
>>> model.add_interaction(plates[13], plates[14])
>>> model.add_interaction(plates[14], plates[15])
>>> model.add_interaction(plates[15], plates[16])
>>> model.add_interaction(plates[16], plates[17])
>>> 
>>> # rows
>>> for i in range(6):
>>>     model.add_interaction(plates[i], plates[i+6])
>>>     model.add_interaction(plates[i+6], plates[i+12])

Print the model structure:

>>> model.print()
────────────────────────────────────────────────────────────────────────────────────────────────────
HIERARCHY
<Model> with 18 elements, 18 children, 27 interactions, 18 nodes
    <ElementNode> my_plate0, <element> Plate 081008ac-0df4-4c7e-8a3b-6d0a9d34119c | Parent: root | Root: model
    <ElementNode> my_plate1, <element> Plate d8ed3914-36d1-406f-9e93-1698699644e8 | Parent: root | Root: model
    <ElementNode> my_plate2, <element> Plate 39e7e3ec-c50e-4dd8-b05e-1ea3f34a22c5 | Parent: root | Root: model
    <ElementNode> my_plate3, <element> Plate 208e5518-4a56-40f6-a102-927d1aedb708 | Parent: root | Root: model
    <ElementNode> my_plate4, <element> Plate 5314a299-049e-4df6-8243-9881d145e11d | Parent: root | Root: model
    <ElementNode> my_plate5, <element> Plate 9489c99f-13a3-4204-a43f-b2126490d4e7 | Parent: root | Root: model
    <ElementNode> my_plate6, <element> Plate 66781998-79a0-4ea5-9452-8bfff8f4d503 | Parent: root | Root: model
    <ElementNode> my_plate7, <element> Plate d08e4a05-4045-44d0-8280-2a00ddbb95fc | Parent: root | Root: model
    <ElementNode> my_plate8, <element> Plate 20c79a4a-78ad-4ba9-b79a-488d7509c8f1 | Parent: root | Root: model
    <ElementNode> my_plate9, <element> Plate 70a3b2d6-63ac-4069-bb3b-7844af6ed230 | Parent: root | Root: model
    <ElementNode> my_plate10, <element> Plate c9b40256-9757-4060-8afc-89a18dd46446 | Parent: root | Root: model
    <ElementNode> my_plate11, <element> Plate 7031bbf7-8bd6-41f0-88ba-b14b2d2e296f | Parent: root | Root: model
    <ElementNode> my_plate12, <element> Plate 2acecc4b-36bb-4bf7-a9cf-34dd1c099512 | Parent: root | Root: model
    <ElementNode> my_plate13, <element> Plate 853873d5-09c7-4023-a94b-3f31583a0c48 | Parent: root | Root: model
    <ElementNode> my_plate14, <element> Plate 751c1e8c-2b55-44ae-8449-81b0f38caf17 | Parent: root | Root: model
    <ElementNode> my_plate15, <element> Plate 06dbd623-efac-4f31-a76e-59ada9e35e81 | Parent: root | Root: model
    <ElementNode> my_plate16, <element> Plate f6170f49-3e35-40cf-a311-b343384deb96 | Parent: root | Root: model
    <ElementNode> my_plate17, <element> Plate 8a88fe08-bef8-4d41-98d5-6da9ead00b7c | Parent: root | Root: model
INTERACTIONS
<Nodes>
    081008ac-0df4-4c7e-8a3b-6d0a9d34119c
    d8ed3914-36d1-406f-9e93-1698699644e8
    39e7e3ec-c50e-4dd8-b05e-1ea3f34a22c5
    208e5518-4a56-40f6-a102-927d1aedb708
    5314a299-049e-4df6-8243-9881d145e11d
    9489c99f-13a3-4204-a43f-b2126490d4e7
    66781998-79a0-4ea5-9452-8bfff8f4d503
    d08e4a05-4045-44d0-8280-2a00ddbb95fc
    20c79a4a-78ad-4ba9-b79a-488d7509c8f1
    70a3b2d6-63ac-4069-bb3b-7844af6ed230
    c9b40256-9757-4060-8afc-89a18dd46446
    7031bbf7-8bd6-41f0-88ba-b14b2d2e296f
    2acecc4b-36bb-4bf7-a9cf-34dd1c099512
    853873d5-09c7-4023-a94b-3f31583a0c48
    751c1e8c-2b55-44ae-8449-81b0f38caf17
    06dbd623-efac-4f31-a76e-59ada9e35e81
    f6170f49-3e35-40cf-a311-b343384deb96
    8a88fe08-bef8-4d41-98d5-6da9ead00b7c
<Edges>
    081008ac-0df4-4c7e-8a3b-6d0a9d34119c d8ed3914-36d1-406f-9e93-1698699644e8
    081008ac-0df4-4c7e-8a3b-6d0a9d34119c 66781998-79a0-4ea5-9452-8bfff8f4d503
    d8ed3914-36d1-406f-9e93-1698699644e8 39e7e3ec-c50e-4dd8-b05e-1ea3f34a22c5
    d8ed3914-36d1-406f-9e93-1698699644e8 d08e4a05-4045-44d0-8280-2a00ddbb95fc
    39e7e3ec-c50e-4dd8-b05e-1ea3f34a22c5 208e5518-4a56-40f6-a102-927d1aedb708
    39e7e3ec-c50e-4dd8-b05e-1ea3f34a22c5 20c79a4a-78ad-4ba9-b79a-488d7509c8f1
    208e5518-4a56-40f6-a102-927d1aedb708 5314a299-049e-4df6-8243-9881d145e11d
    208e5518-4a56-40f6-a102-927d1aedb708 70a3b2d6-63ac-4069-bb3b-7844af6ed230
    5314a299-049e-4df6-8243-9881d145e11d 9489c99f-13a3-4204-a43f-b2126490d4e7
    5314a299-049e-4df6-8243-9881d145e11d c9b40256-9757-4060-8afc-89a18dd46446
    9489c99f-13a3-4204-a43f-b2126490d4e7 7031bbf7-8bd6-41f0-88ba-b14b2d2e296f
    66781998-79a0-4ea5-9452-8bfff8f4d503 d08e4a05-4045-44d0-8280-2a00ddbb95fc
    66781998-79a0-4ea5-9452-8bfff8f4d503 2acecc4b-36bb-4bf7-a9cf-34dd1c099512
    d08e4a05-4045-44d0-8280-2a00ddbb95fc 20c79a4a-78ad-4ba9-b79a-488d7509c8f1
    d08e4a05-4045-44d0-8280-2a00ddbb95fc 853873d5-09c7-4023-a94b-3f31583a0c48
    20c79a4a-78ad-4ba9-b79a-488d7509c8f1 70a3b2d6-63ac-4069-bb3b-7844af6ed230
    20c79a4a-78ad-4ba9-b79a-488d7509c8f1 751c1e8c-2b55-44ae-8449-81b0f38caf17
    70a3b2d6-63ac-4069-bb3b-7844af6ed230 c9b40256-9757-4060-8afc-89a18dd46446
    70a3b2d6-63ac-4069-bb3b-7844af6ed230 06dbd623-efac-4f31-a76e-59ada9e35e81
    c9b40256-9757-4060-8afc-89a18dd46446 7031bbf7-8bd6-41f0-88ba-b14b2d2e296f
    c9b40256-9757-4060-8afc-89a18dd46446 f6170f49-3e35-40cf-a311-b343384deb96
    7031bbf7-8bd6-41f0-88ba-b14b2d2e296f 8a88fe08-bef8-4d41-98d5-6da9ead00b7c
    2acecc4b-36bb-4bf7-a9cf-34dd1c099512 853873d5-09c7-4023-a94b-3f31583a0c48
    853873d5-09c7-4023-a94b-3f31583a0c48 751c1e8c-2b55-44ae-8449-81b0f38caf17
    751c1e8c-2b55-44ae-8449-81b0f38caf17 06dbd623-efac-4f31-a76e-59ada9e35e81
    06dbd623-efac-4f31-a76e-59ada9e35e81 f6170f49-3e35-40cf-a311-b343384deb96
    f6170f49-3e35-40cf-a311-b343384deb96 8a88fe08-bef8-4d41-98d5-6da9ead00b7c
────────────────────────────────────────────────────────────────────────────────────────────────────

And vizualize it:

>>> ViewerModel.show(model, scale_factor=1, geometry=model.get_interactions_lines())
