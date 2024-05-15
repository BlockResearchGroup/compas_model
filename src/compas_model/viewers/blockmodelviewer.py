from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_viewer import Viewer

from compas_model.elements import BlockElement
from compas_model.elements import BlockGeometry
from compas_model.interactions import ContactInterface
from compas_model.models import Model


class BlockModelViewer(Viewer):
    def add(
        self,
        blockmodel: Model,
        show_blockfaces=True,
        show_interfaces=False,
        show_contactforces=False,
        scale_compression=1.0,
        scale_friction=1.0,
        scale_tension=1.0,
        scale_resultant=1.0,
    ):
        color_support: Color = Color.red().lightened(50)
        color_interface: Color = Color(0.9, 0.9, 0.9)

        # add blocks and supports

        supports: list[BlockGeometry] = []
        blocks: list[BlockGeometry] = []

        for element in blockmodel.elements():
            element: BlockElement

            if element.is_support:
                supports.append(
                    (
                        element.geometry,
                        {
                            "name": f"Support_{len(supports)}",
                            "show_points": False,
                            "show_faces": True,
                            "facecolor": color_support,
                            "linecolor": color_support.contrast,
                        },
                    )
                )
            else:
                blocks.append(
                    (
                        element.geometry,
                        {
                            "name": f"Block_{len(blocks)}",
                            "show_points": False,
                            "show_faces": show_blockfaces,
                            "facecolor": color_support,
                            "linecolor": Color(0.3, 0.3, 0.3),
                        },
                    )
                )

        self.scene.add(
            supports,
            name="Supports",
        )
        self.scene.add(
            blocks,
            name="Blocks",
        )

        # add interfaces and interface forces

        interfaces: list[Mesh] = []
        compressionforces: list[Line] = []
        tensionforces: list[Line] = []
        frictionforces: list[Line] = []
        resultantforces: list[Line] = []

        for interaction in blockmodel.interactions():
            interaction: ContactInterface

            interfaces.append(interaction.mesh)

            compressionforces += interaction.compressionforces
            tensionforces += interaction.tensionforces
            frictionforces += interaction.frictionforces
            resultantforces += interaction.resultantforce

        if show_interfaces:
            self.scene.add(
                interfaces,
                name="Interfaces",
                show_points=False,
                facecolor=color_interface,
                linecolor=color_interface.contrast,
            )

        if scale_compression != 1.0:
            for line in compressionforces:
                if line.length:
                    line.start = line.midpoint - line.vector * 0.5 * scale_compression
                    line.end = line.midpoint + line.vector * 0.5 * scale_compression

        if scale_tension != 1.0:
            for line in tensionforces:
                if line.length:
                    line.start = line.midpoint - line.vector * 0.5 * scale_tension
                    line.end = line.midpoint + line.vector * 0.5 * scale_tension

        if scale_friction != 1.0:
            for line in frictionforces:
                if line.length:
                    line.start = line.midpoint - line.vector * 0.5 * scale_friction
                    line.end = line.midpoint + line.vector * 0.5 * scale_friction

        if scale_resultant != 1.0:
            for line in resultantforces:
                if line.length:
                    line.start = line.midpoint - line.vector * 0.5 * scale_resultant
                    line.end = line.midpoint + line.vector * 0.5 * scale_resultant

        if show_contactforces:
            self.scene.add(
                compressionforces,
                name="Compression",
                linewidth=3,
                linecolor=Color.blue(),
                show_points=False,
            )
            self.scene.add(
                tensionforces,
                name="Tension",
                linewidth=3,
                linecolor=Color.red(),
                show_points=False,
            )
            self.scene.add(
                frictionforces,
                name="Friction",
                linewidth=3,
                linecolor=Color.cyan(),
                show_points=False,
            )
            self.scene.add(
                resultantforces,
                name="Resultants",
                linewidth=5,
                linecolor=Color.green(),
                show_points=False,
            )
