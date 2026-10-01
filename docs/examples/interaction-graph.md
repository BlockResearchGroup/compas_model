# Interaction graph

Find the neighbors of an element. The model stores the contacts between touching elements as edges in its interaction graph, and the neighbors of an element are found through the graph. Here the blocks of a masonry arch are created with `compas_dem`, which extends `compas_model` with block elements. The selected block is yellow and its neighbors are light yellow.

![Interaction graph](../assets/images/example_graph.png)

```bash
pip install "compas_model[viz]" compas_dem
```

```python
from compas.colors import Color
from compas_dem.models import BlockModel
from compas_dem.templates import ArchTemplate
from compas_viewer import Viewer

template = ArchTemplate(rise=3, span=6, thickness=0.3, depth=0.6, n=20)
model = BlockModel.from_template(template)
model.compute_contacts()

# the blocks that touch the selected block are its neighbors in the interaction graph
block = list(model.blocks())[10]
neighbors = []
for node in model.graph.neighbors(block.graphnode):
    neighbor = model.graph.node_element(node)
    neighbors.append(neighbor)

viewer = Viewer()
viewer.config.renderer.show_grid = False
modelobject = viewer.scene.add(model)

for blockobject in modelobject.children:
    if blockobject.element is block:
        blockobject.visualization_object.facecolor = Color.from_hex("#f2d500")
    elif blockobject.element in neighbors:
        blockobject.visualization_object.facecolor = Color.from_hex("#f3e9b5")

viewer.show()
```
