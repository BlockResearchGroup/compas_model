# Transformations

Position elements relative to their parent. A robot arm is a chain of links, each an element and a child of the previous link in the element tree, so its `transformation` is relative to its parent. Each joint rotation therefore carries over to all links after it. The animation shows the same model created with different joint angles.

![Transformations](../assets/images/example_transformations.gif){ style="display: block; margin: 0 auto;" }

```bash
pip install "compas_model[viz]"
```

```python
from math import radians

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Rotation
from compas.geometry import Translation
from compas_model.elements import Element
from compas_model.models import Model
from compas_viewer import Viewer


class Link(Element):
    def compute_elementgeometry(self, include_features=False):
        return self.geometry.to_mesh()


# name, width, height
links = [("base", 0.6, 0.4), ("shoulder", 0.2, 1.0), ("elbow", 0.2, 1.0), ("wrist", 0.15, 0.5)]


def create_robot(angles):
    model = Model(name="robot")

    parent = None
    offset = 0.0

    for (name, width, height), angle in zip(links, angles):
        frame = Frame([0, 0, height / 2], [1, 0, 0], [0, 1, 0])
        box = Box(width, width, height, frame=frame)

        # the joint is relative to the parent link
        rotation = Rotation.from_axis_and_angle([0, 1, 0], radians(angle))
        translation = Translation.from_vector([0, 0, offset])

        link = Link(geometry=box, name=name)
        link.transformation = translation * rotation
        model.add_element(link, parent=parent)

        if parent:
            model.add_interaction(parent, link)

        parent = link
        offset = height

    return model


model = create_robot([0, 30, -50, 40])

viewer = Viewer()
viewer.scene.add(model)
viewer.show()
```
