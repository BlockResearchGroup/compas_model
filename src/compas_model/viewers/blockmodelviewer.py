from compas.colors import Color
from compas_viewer import Viewer

from compas_model.elements import BlockElement
from compas_model.interactions import ContactInterface
from compas_model.models import Model


class BlockModelViewer:

    def __init__(self, blockmodel: Model, show_blockfaces=True, show_interfaces=False, show_contactforces=False):
        self.viewer = Viewer()
        self.add(blockmodel, show_blockfaces=show_blockfaces, show_interfaces=show_interfaces, show_contactforces=show_contactforces)

    def show(self):
        self.viewer.show()

    def add(self, blockmodel: Model, show_blockfaces, show_interfaces, show_contactforces):
        for element in blockmodel.elements():
            element: BlockElement

            if element.is_support:
                color: Color = Color.red().lightened(50)
                show_faces = True
            else:
                color = Color(0.9, 0.9, 0.9)
                show_faces = show_blockfaces

            self.viewer.scene.add(element.geometry, show_points=False, show_faces=show_faces, facecolor=color, linecolor=color.contrast)

        for interaction in blockmodel.interactions():
            interaction: ContactInterface

            if show_interfaces:
                self.viewer.scene.add(interaction.mesh, show_points=False, facecolor=Color(0.9, 0.9, 0.9))

            if show_contactforces:
                for line in interaction.compressionforces:
                    self.viewer.scene.add(
                        line,
                        lineswidth=3,
                        linecolor=Color.blue(),
                        show_points=False,
                    )

                for line in interaction.tensionforces:
                    self.viewer.scene.add(
                        line,
                        lineswidth=3,
                        linecolor=Color.red(),
                        show_points=False,
                    )

                for line in interaction.frictionforces:
                    self.viewer.scene.add(
                        line,
                        lineswidth=3,
                        linecolor=Color.cyan(),
                        show_points=False,
                    )

                for line in interaction.resultantforce:
                    self.viewer.scene.add(
                        line,
                        lineswidth=5,
                        linecolor=Color.green(),
                        show_points=False,
                    )
