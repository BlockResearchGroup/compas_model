from compas.geometry import Scale
from compas.colors import Color
from collections import OrderedDict
import compas

compas_view2_imported = False

if not (compas.is_rhino() or compas.is_blender()):
    try:
        from compas_view2.app import App
        from compas_view2.collections import Collection
        from compas_view2.objects import MeshObject
        from compas_view2.objects import Arrow

        compas_view2_imported = True

    except ImportError:
        print("WARNING: compas_view2 is not installed!!!")


colors = [
    Color(0.929, 0.082, 0.498),
    Color(0.129, 0.572, 0.815),
    Color(0.5, 0.5, 0.5),
    Color(0.95, 0.95, 0.95),
    Color(0, 0, 0),
]


class DisplayOptions:
    @staticmethod
    def display_schema(name):
        """display schema of the element

        Parameters
        ----------
        name : str
            name of the element

        Returns
        -------
        dict
            display schema of the element

        """

        face_color = [
            0.9,
            0.9,
            0.9,
        ]  # if not self.is_support else [0.968, 0.615, 0.517]
        lines_weight = 5
        points_weight = 20

        if str.lower(name) == "beam":
            return OrderedDict(
                [
                    ("geometry_simplified", {"is_visible": True}),
                    (
                        "geometry",
                        {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                    ),
                    ("frame", {}),
                    ("aabb", {"opacity": 0.25}),
                    ("obb", {"opacity": 0.25}),
                    ("collision_mesh", {"opacity": 0.25}),
                    (
                        "face_polygons",
                        {
                            "linewidth": lines_weight,
                            "show_faces": False,
                            "is_visible": True,
                        },
                    ),
                    ("mid_point", {"pointsize": points_weight}),
                ]
            )
        elif str.lower(name) == "block":
            return OrderedDict(
                [
                    ("geometry_simplified", {"is_visible": True}),
                    (
                        "geometry",
                        {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                    ),
                    ("frame", {}),
                    ("aabb", {"opacity": 0.25}),
                    ("obb", {"opacity": 0.25}),
                    ("collision_mesh", {"opacity": 0.25}),
                    ("face_polygons", {"linewidth": lines_weight, "show_faces": False}),
                ]
            )
        elif str.lower(name) == "interface":
            return OrderedDict(
                [
                    ("geometry_simplified", {"is_visible": True}),
                    (
                        "geometry",
                        {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                    ),
                    ("frame", {}),
                    ("aabb", {"opacity": 0.25}),
                    ("obb", {"opacity": 0.25}),
                ]
            )
        elif str.lower(name) == "plate":
            return OrderedDict(
                [
                    ("geometry_simplified", {"show_faces": False, "is_visible": True}),
                    (
                        "geometry",
                        {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                    ),
                    ("frame", {}),
                    ("aabb", {"opacity": 0.25}),
                    ("obb", {"opacity": 0.25}),
                    ("face_polygons", {"linewidth": lines_weight, "show_faces": False}),
                    ("face_frames", {"is_visible": True}),
                    (
                        "top_and_bottom_polygons",
                        {"linewidth": lines_weight, "show_faces": False},
                    ),
                ]
            )


class ViewerModel:
    @classmethod
    def show(cls, model, scale_factor=0.001, geometry=[]):
        """display the model:
        a) right side shows the tree structure and element properties
        b) left side shows its adjacency
        elements class must have display_schema method that gives instructions how to display the properties
        """

        # --------------------------------------------------------------------------
        # import viwer library
        # --------------------------------------------------------------------------
        if not compas_view2_imported:
            return

        # --------------------------------------------------------------------------
        # initialize the viewer
        # --------------------------------------------------------------------------
        viewer = App(
            show_grid=True,
            enable_sceneform=True,
            enable_propertyform=True,
            viewmode="lighted",
        )

        # --------------------------------------------------------------------------
        # create a sceneform to display a tree structure
        # --------------------------------------------------------------------------
        elements_by_type = OrderedDict()
        elements_by_guid = OrderedDict()
        ViewerModel.create_spatial_structure(
            model, viewer, scale_factor, elements_by_type, elements_by_guid
        )

        # --------------------------------------------------------------------------
        # Create the form to toggle on and off the elements
        # --------------------------------------------------------------------------
        ViewerModel.visibility_of_class_properties(viewer, elements_by_type)

        # --------------------------------------------------------------------------
        #  Display adjacency
        # --------------------------------------------------------------------------
        ViewerModel.adjacency(viewer, model, elements_by_guid)

        # --------------------------------------------------------------------------
        #  Geometry that is not part of the model
        # --------------------------------------------------------------------------
        ViewerModel.add_geometry(viewer, scale_factor, geometry)

        # --------------------------------------------------------------------------
        # run the viewer
        # --------------------------------------------------------------------------
        viewer.show()

    @classmethod
    def add_to_dictionary(cls, my_dict, key, value):
        """Helper function to add object in a list in the dictionary."""
        if key in my_dict:
            my_dict[key].append(value)
        else:
            my_dict[key] = [value]

    @classmethod
    def add_element_to_viewer(
        cls, viewer, element, scale_factor, elements_by_guid, elements_by_type, idx=0
    ):
        """add element to the viewer"""

        # --------------------------------------------------------------------------
        # Create an empty object to store the Node name
        # --------------------------------------------------------------------------
        # node_geo = viewer.add(Collection([]), name="node_" + node.name)  # type: ignore

        # --------------------------------------------------------------------------
        # object that contains all the geometry properties of the element
        # --------------------------------------------------------------------------
        element_geo = viewer.add(
            Collection([]), name="element " + str.lower(element.name) + " " + str(idx)  # type: ignore
        )
        # node_geo.add(element_geo)

        # --------------------------------------------------------------------------
        # geometrical properties of an element
        # --------------------------------------------------------------------------

        display_schema = DisplayOptions.display_schema(
            str(element.__class__.__name__)
        )  # get the display schema from the element

        for idx, attr in enumerate(display_schema.items()):
            obj_name = attr[0]  # the geometrical attribute name
            display_options = attr[1]  # the display options of the attribute
            property_value = getattr(element, obj_name)

            # --------------------------------------------------------------------------
            # display the contents of the object
            # if the geometrical propery is stored in a list add a branch to it
            # --------------------------------------------------------------------------
            if isinstance(property_value, list):
                # an additional branch
                sub_element_geo = viewer.add(Collection([]), name="property_" + obj_name)  # type: ignore
                element_geo.add(sub_element_geo)

                # individual geometry properties
                for obj in property_value:
                    ViewerModel.add_object(
                        viewer,
                        obj,
                        str.lower("property_" + type(obj).__name__),
                        display_options,
                        scale_factor,
                        sub_element_geo,
                        elements_by_guid,
                        obj_name + str(element.guid),
                        elements_by_type,
                    )

            else:
                ViewerModel.add_object(
                    viewer,
                    property_value,
                    "property_" + obj_name,
                    display_options,
                    scale_factor,
                    element_geo,
                    elements_by_guid,
                    obj_name + str(element.guid),
                    elements_by_type,
                )
        return element_geo

    @classmethod
    def create_spatial_structure(
        cls, model, viewer, scale_factor, elements_by_type, elements_by_guid
    ):
        """display spatial structure of the model"""

        def _create_spatial_structure(
            node, viewer, prev_node_geo, elements_by_type, elements_by_guid
        ):
            """recursive function to create the spatial structure of the model"""

            # --------------------------------------------------------------------------
            # Create an empty object to store the Node name
            # --------------------------------------------------------------------------
            node_geo = viewer.add(Collection([]), name="node_" + node.name)  # type: ignore

            # --------------------------------------------------------------------------
            # if object is not a root node, add it to the previous node
            # --------------------------------------------------------------------------
            if prev_node_geo:
                prev_node_geo.add(node_geo)

            # --------------------------------------------------------------------------
            # add children to the node
            # --------------------------------------------------------------------------
            if (
                node.is_leaf
                and str(type(node))
                != "<class 'compas_model.model.group_node.GroupNode'>"
            ):
                # --------------------------------------------------------------------------
                # iterate elements and display properties following the display schema
                # --------------------------------------------------------------------------
                # for idx, element in enumerate(node.elements):
                element = node.element

                # --------------------------------------------------------------------------
                # object that contains all the geometry properties of the element
                # --------------------------------------------------------------------------
                element_geo = viewer.add(Collection([]), name="element " + str.lower(element.name))  # type: ignore
                node_geo.add(element_geo)

                # --------------------------------------------------------------------------
                # geometrical properties of an element
                # --------------------------------------------------------------------------

                display_schema = DisplayOptions.display_schema(
                    str(element.__class__.__name__)
                )  # get the display schema from the element

                for idx, attr in enumerate(display_schema.items()):
                    obj_name = attr[0]  # the geometrical attribute name
                    display_options = attr[1]  # the display options of the attribute
                    property_value = getattr(element, obj_name)

                    # --------------------------------------------------------------------------
                    # display the contents of the object
                    # if the geometrical propery is stored in a list add a branch to it
                    # --------------------------------------------------------------------------
                    if isinstance(property_value, list):
                        # an additional branch
                        name = obj_name + "_" + str(element.guid)
                        elements_by_guid[str(element.guid)] = None
                        sub_element_geo = viewer.add(Collection([]), name="property_" + obj_name)  # type: ignore
                        element_geo.add(sub_element_geo)

                        # individual geometry properties
                        for obj in property_value:
                            ViewerModel.add_object(
                                viewer,
                                obj,
                                str.lower("property_" + obj_name),
                                display_options,
                                scale_factor,
                                sub_element_geo,
                                elements_by_guid,
                                name,
                                elements_by_type,
                            )

                    else:
                        name = obj_name + "_" + str(element.guid)
                        elements_by_guid[str(element.guid)] = None
                        ViewerModel.add_object(
                            viewer,
                            property_value,
                            "property_" + obj_name,
                            display_options,
                            scale_factor,
                            element_geo,
                            elements_by_guid,
                            name,
                            elements_by_type,
                        )

            # --------------------------------------------------------------------------
            # recursively add nodes
            # --------------------------------------------------------------------------
            if not node.is_leaf:
                for child_node in node.children:
                    _create_spatial_structure(
                        child_node, viewer, node_geo, elements_by_type, elements_by_guid
                    )

        # --------------------------------------------------------------------------
        # the starting point of the recursive function
        # --------------------------------------------------------------------------
        _create_spatial_structure(
            model._hierarchy.root, viewer, None, elements_by_type, elements_by_guid
        )

        # --------------------------------------------------------------------------
        # add elements that are not in the hierarchy
        # --------------------------------------------------------------------------
        for idx, element in enumerate(model.elements.values()):
            if str(element.guid) not in elements_by_guid.keys():
                ViewerModel.add_element_to_viewer(
                    viewer=viewer,
                    element=element,
                    scale_factor=scale_factor,
                    elements_by_guid=elements_by_guid,
                    elements_by_type=elements_by_type,
                    idx=idx,
                )

    @classmethod
    def add_object(
        cls,
        viewer,
        obj,
        name,
        display_options,
        scale_factor,
        sub_object,
        elements_by_guid,
        obj_name_and_guid,
        elements_by_type,
    ):
        """add object to the viewer and apply display options"""

        # --------------------------------------------------------------------------
        # hide the lines of the mesh
        # --------------------------------------------------------------------------

        # --------------------------------------------------------------------------
        # scale the object
        # --------------------------------------------------------------------------
        scale_xform = Scale.from_factors([scale_factor, scale_factor, scale_factor])

        obj_copy = obj.copy()
        obj_copy.transform(scale_xform)
        # --------------------------------------------------------------------------
        # add object to the viewer
        # ---------------------------------------------------------------------------
        # viewer = viewer.add(obj_copy, name=name, display_options)
        default_options = {
            "is_visible": False,
            "show_points": True,
            "show_lines": True,
            "show_faces": True,
            "pointcolor": [0.0, 0.0, 0.0],
            "linecolor": [0.0, 0.0, 0.0],
            "facecolor": [0.9, 0.9, 0.9],
            "linewidth": 1,
            "pointsize": 1,
            "opacity": 1.0,
        }

        for key, value in display_options.items():
            default_options[str(key)] = value

        if "force" in name:
            obj_copy = Arrow(obj_copy.start, obj_copy.end - obj_copy.start)

        viewer_obj = viewer.add(
            obj_copy,
            name=name,
            is_visible=default_options["is_visible"],
            show_points=default_options["show_points"],
            show_lines=default_options["show_lines"],
            show_faces=default_options["show_faces"],
            pointcolor=default_options["pointcolor"],
            linecolor=default_options["linecolor"],
            facecolor=default_options["facecolor"],
            linewidth=default_options["linewidth"],
            pointsize=default_options["pointsize"],
            opacity=default_options["opacity"],
        )

        # --------------------------------------------------------------------------
        # hide the lines of the mesh
        # --------------------------------------------------------------------------
        if isinstance(viewer_obj, MeshObject):
            viewer_obj.show_lines = True
            # viewer_obj.hide_coplanaredges = True

        if isinstance(viewer_obj, Arrow):
            viewer_obj.show_lines = False

        # --------------------------------------------------------------------------
        # add object to the sub_object
        # --------------------------------------------------------------------------
        sub_object.add(viewer_obj)

        # --------------------------------------------------------------------------
        # add object to the dictionary of different types
        # --------------------------------------------------------------------------
        elements_by_guid[obj_name_and_guid] = viewer_obj

        # --------------------------------------------------------------------------
        # add object to the dictionary of different types to toggle the visibility
        # --------------------------------------------------------------------------
        ViewerModel.add_to_dictionary(elements_by_type, name, viewer_obj)

        # --------------------------------------------------------------------------
        # return the oject that will be added to the tree hierarchy for the scene form
        # --------------------------------------------------------------------------
        return viewer_obj

    @classmethod
    def visibility_of_class_properties(cls, viewer, elements_by_type):
        """create a form to toggle on and off the elements properties"""

        # --------------------------------------------------------------------------
        # create a form to toggle on and off the elements properties
        # the form is displayed on the right bottom side
        # --------------------------------------------------------------------------
        dock = viewer.sidedock("Show Hide Element Properties")

        # --------------------------------------------------------------------------
        # iterate the dictionary of elements sorted by type e.g. property_geometry_simplified
        # and create the checkboxes to toggle on and off the visibility
        # --------------------------------------------------------------------------
        for key, value in elements_by_type.items():
            # get state of object
            is_visible = elements_by_type[key][0].is_visible

            @viewer.checkbox(text=key, checked=is_visible, parent=dock.content_layout)
            def check(checked, key=key):
                for obj in elements_by_type[key]:
                    obj.is_visible = checked
                    viewer.view.update()

    @classmethod
    def adjacency(cls, viewer, model, elements_by_guid):
        """create a tab on the left side to display the adjacency of the elements
        when clicked geometries are highlighted"""

        object_colors = OrderedDict()
        for obj in viewer.view.objects:
            object_colors[obj] = (obj.facecolor, obj.opacity, obj)

        def reset_colors(self, entry):
            for key, value in object_colors.items():
                value[2].facecolor = value[0]
                value[2].opacity = value[1]
            viewer.view.update()

        def show_attributes_form(self, entry):
            reset_colors(self, entry)
            entry["data"][0].facecolor = colors[0]
            entry["data"][0].opacity = 1
            for idx in range(1, len(entry["data"])):
                entry["data"][idx].facecolor = colors[1]
                entry["data"][idx].opacity = 1
            viewer.view.update()

        # --------------------------------------------------------------------------
        # vertex neighborhoods
        # --------------------------------------------------------------------------
        interactions_vertex_neighbors = model.to_nodes_and_neighbors()

        dict_guid_and_index = OrderedDict()
        counter = 0
        for key in model.elements:
            dict_guid_and_index[key] = counter
            counter = counter + 1

        my_contents_form_data = []
        for idx, node in enumerate(interactions_vertex_neighbors[0]):
            neighbors = interactions_vertex_neighbors[1][idx]

            vertex_neighbors_to_select = [elements_by_guid["geometry_" + str(node)]]
            vertex_vertex_to_select = []
            for n in neighbors:
                vertex_neighbors_to_select.append(
                    elements_by_guid["geometry_" + str(n)]
                )
                vertex_vertex_to_select.append(
                    [
                        elements_by_guid["geometry_" + str(node)],
                        elements_by_guid["geometry_" + str(n)],
                    ]
                )

            node_text = dict_guid_and_index[node]
            my_contents_form_data_current = {
                "key": node_text,
                "on_item_double_clicked": reset_colors,
                "on_item_pressed": show_attributes_form,
                "data": vertex_neighbors_to_select,
                # "attributes": {str.lower(str(interactions_readable[idx][1]))},
                "children": [],
                "attributes": OrderedDict(),
            }

            for jdx, n in enumerate(neighbors):
                neighbor_text = dict_guid_and_index[n]

                my_contents_form_data_current["children"].append(
                    {
                        "key": neighbor_text,
                        "on_item_double_clicked": reset_colors,
                        "on_item_pressed": show_attributes_form,
                        "data": vertex_vertex_to_select[jdx],
                        "children": [],
                        "attributes": OrderedDict(),
                        # "attributes": {"attribute7": 7, "attribute8": 8, "attribute9": 9},
                        # "color": (0, 0, 100),  # This assigns a color to the entrie row of this entry
                    }
                )
            my_contents_form_data.append(my_contents_form_data_current)

        # # --------------------------------------------------------------------------
        # # Define the function that will be called when an item is pressed
        # # --------------------------------------------------------------------------
        # def select(self, entry):
        #     viewer.selector.reset()
        #     entry["data"][0].is_selected = True  # here geometry is selected
        #     entry["data"][1].is_selected = True
        #     viewer.view.update()

        # # --------------------------------------------------------------------------
        # # Create the data
        # # by iterating the interactions list that contains the guids of the geometryes
        # # whereas the interactions_readable contains the names of the geometryes
        # # --------------------------------------------------------------------------
        # data = []

        # for idx, tuple_of_guids in enumerate(interactions):
        #     obj1 = elements_by_guid["geometry" + str(tuple_of_guids[0])]
        #     obj2 = elements_by_guid["geometry" + str(tuple_of_guids[1])]
        #     data.append(
        #         {
        #             "object1": str.lower(str(interactions_readable[idx][0])),
        #             "object2": str.lower(str(interactions_readable[idx][1])),
        #             "on_item_pressed": select,
        #             "data": [obj1, obj2],
        #         }
        #     )

        # --------------------------------------------------------------------------
        # Add the treeform
        # --------------------------------------------------------------------------
        viewer.treeform(
            "Adjacency", data=my_contents_form_data, show_headers=False, columns=["key"]
        )
        # viewer.treeform("Objects", location="left", data=data, show_headers=True, columns=["object1", "object2"])

    @classmethod
    def add_geometry(cls, viewer, scale_factor, geometry=[]):
        group = viewer.add(Collection([]), name="non_model_geometry")
        for obj in geometry:
            # --------------------------------------------------------------------------
            # scale the object
            # --------------------------------------------------------------------------
            scale_xform = Scale.from_factors([scale_factor, scale_factor, scale_factor])
            obj_copy = obj.copy()
            obj_copy.transform(scale_xform)
            group.add(
                obj_copy,
                name="geometry",
                facecolor=(0, 0.6, 1),
                linecolor=(0, 0, 0),
                linewidth=1,
                opacity=1,
            )
        if len(group.children) == 0:
            viewer.remove(group)
