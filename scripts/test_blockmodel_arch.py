import compas
from compas.colors import Color
from compas_assembly.geometry import Arch
from compas_model.algorithms import blockmodel_interfaces
from compas_model.analysis import cra_penalty_solve
from compas_model.elements import BlockElement
from compas_model.interactions import ContactInterface
from compas_model.models import Model
from compas_viewer import Viewer

# =============================================================================
# Block model
# =============================================================================

template = Arch(rise=3, span=10, thickness=0.3, depth=0.5, n=30)

model = Model()

for block in template.blocks():
    model.add_element(BlockElement(shape=block))

# =============================================================================
# Interfaces
# =============================================================================

blockmodel_interfaces(model)

# =============================================================================
# Equilibrium
# =============================================================================

elements: list[BlockElement] = sorted(model.elements(), key=lambda e: e.geometry.centroid().z)[:2]

for element in elements:
    element.is_support = True

cra_penalty_solve(model)

# =============================================================================
# Export
# =============================================================================

compas.json_dump(model, "test.json")

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()

for element in model.elements():
    element: BlockElement

    if element.is_support:
        color: Color = Color.red().lightened(50)
        show_faces = True
    else:
        color = Color(0.8, 0.8, 0.8)
        show_faces = False

    viewer.scene.add(element.geometry, show_points=False, show_faces=show_faces, facecolor=color, linecolor=color.contrast)

for interaction in model.interactions():
    interaction: ContactInterface

    # viewer.scene.add(interaction.frame)

    color = Color(0.9, 0.9, 0.9)
    viewer.scene.add(interaction.mesh, show_points=False, facecolor=color)

    for line in interaction.compressionforces:
        viewer.scene.add(
            line,
            lineswidth=3,
            linecolor=Color.blue(),
            show_points=False,
        )

    for line in interaction.tensionforces:
        viewer.scene.add(
            line,
            lineswidth=3,
            linecolor=Color.red(),
            show_points=False,
        )

    for line in interaction.frictionforces:
        viewer.scene.add(
            line,
            lineswidth=3,
            linecolor=Color.cyan(),
            show_points=False,
        )

    for line in interaction.resultantforce:
        viewer.scene.add(
            line,
            lineswidth=5,
            linecolor=Color.green(),
            show_points=False,
        )


viewer.show()
