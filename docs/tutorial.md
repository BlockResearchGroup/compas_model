# Tutorial

This tutorial creates a small model using context-free element types.
`PrimitiveElement` stores a COMPAS shape and evaluates it to a Mesh.

## Create a model

```python
from compas.geometry import Box
from compas.geometry import Translation
from compas_model.elements import Group
from compas_model.elements import PrimitiveElement
from compas_model.models import Model

model = Model(name="Example")
assembly = model.add_element(Group(name="Assembly"))
left = PrimitiveElement(Box(1, 1, 1), name="Left")
right = PrimitiveElement(
    Box(1, 1, 1),
    transformation=Translation.from_vector([1, 0, 0]),
    name="Right",
)

model.add_element(left, parent=assembly)
model.add_element(right)
```

Element geometry is defined in local coordinates. The element transformation,
its ancestors' transformations, and the model transformation determine its
model-space geometry.

## Add structure and classifications

The hierarchy expresses spatial ownership. Collections are independent,
overlapping classifications.

```python
review = model.add_collection("Review set")
review.add_elements([left, right])
```

Use the interaction graph for relationships between elements:

```python
model.add_interaction(left, right)
```

## Inspect the model

```python
print([element.name for element in model.elements()])
print([element.name for element in review.elements()])
print(left.aabb)
```

The core model does not require a collision, BRep, or viewer backend. Continue
with the [examples](examples/index.md) or the
[model API reference](reference/models/model.md).
