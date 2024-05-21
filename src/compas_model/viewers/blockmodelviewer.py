from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.itertools import remap_values
from compas_viewer import Viewer
from compas_viewer.components import Button
from compas_viewer.components.slider import Slider
from compas_viewer.scene import GroupObject

from compas_model.elements import BlockElement
from compas_model.elements import BlockGeometry
from compas_model.interactions import ContactInterface
from compas_model.models import Model


def toggle_supports():
    viewer = BlockModelViewer()
    if viewer.supports:
        for obj in viewer.supports.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_blocks():
    viewer = BlockModelViewer()
    if viewer.blocks:
        for obj in viewer.blocks.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_blockfaces():
    viewer = BlockModelViewer()
    if viewer.blocks:
        for obj in viewer.blocks.descendants:
            obj.show_faces = not obj.show_faces
    viewer.renderer.update()


def toggle_interfaces():
    viewer = BlockModelViewer()
    if viewer.interfaces:
        for obj in viewer.interfaces.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_compression():
    viewer = BlockModelViewer()
    if viewer.compressionforces:
        for obj in viewer.compressionforces.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_tension():
    viewer = BlockModelViewer()
    if viewer.tensionforces:
        for obj in viewer.tensionforces.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_friction():
    viewer = BlockModelViewer()
    if viewer.frictionforces:
        for obj in viewer.frictionforces.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def toggle_resultants():
    viewer = BlockModelViewer()
    if viewer.resultantforces:
        for obj in viewer.resultantforces.descendants:
            obj.is_visible = not obj.is_visible
    viewer.renderer.update()


def scale_compression(value):
    if value <= 50:
        values = list(range(1, 51))
        values = remap_values(values, target_min=1, target_max=100)
        scale = values[value - 1] / 100
    else:
        value = value - 50
        values = list(range(0, 50))
        values = remap_values(values, target_min=1, target_max=100)
        scale = values[value - 1]

    viewer = BlockModelViewer()
    if viewer.compressionforces:
        for obj, line in zip(viewer.compressionforces.descendants, viewer._compressionforces):
            obj.geometry.start = line.midpoint - line.vector * 0.5 * scale
            obj.geometry.end = line.midpoint + line.vector * 0.5 * scale
            obj.update()
    viewer.renderer.update()


class BlockModelViewer(Viewer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.supports: GroupObject = None
        self.blocks: GroupObject = None
        self.interfaces: GroupObject = None
        self._compressionforces: list[Line] = None
        self.compressionforces: GroupObject = None
        self.tensionforces: GroupObject = None
        self.frictionforces: GroupObject = None
        self.resultantforces: GroupObject = None

        self.scale_compression = 1.0

        self.ui.sidedock.show = True
        self.ui.sidedock.add(Button(text="Toggle Supports", action=toggle_supports))
        self.ui.sidedock.add(Button(text="Toggle Blocks", action=toggle_blocks))
        self.ui.sidedock.add(Button(text="Toggle Block Faces", action=toggle_blockfaces))
        self.ui.sidedock.add(Button(text="Toggle Interfaces", action=toggle_interfaces))
        self.ui.sidedock.add(Button(text="Toggle Compression", action=toggle_compression))
        self.ui.sidedock.add(Button(text="Toggle Tension", action=toggle_tension))
        self.ui.sidedock.add(Button(text="Toggle Friction", action=toggle_friction))
        self.ui.sidedock.add(Button(text="Toggle Resultants", action=toggle_resultants))

        self.ui.sidedock.add(
            Slider(
                action=scale_compression,
                value=self.scale_compression * 50,
                min_value=1,
                max_value=100,
                step=1,
                title="Scale Compression",
            )
        )

    def add_blockmodel(
        self,
        blockmodel: Model,
        show_blockfaces=True,
        show_interfaces=False,
        show_contactforces=False,
        scale_compression=1.0,
        scale_friction=1.0,
        scale_tension=1.0,
        scale_resultant=1.0,
        color_support: Color = Color.red().lightened(50),
        color_interface: Color = Color(0.9, 0.9, 0.9),
    ):

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
                            "facecolor": Color(0.8, 0.8, 0.8),
                            "linecolor": Color(0.3, 0.3, 0.3),
                        },
                    )
                )

        self.supports = self.scene.add(
            supports,
            name="Supports",
        )
        self.blocks = self.scene.add(
            blocks,
            name="Blocks",
        )

        # add interfaces and interface forces

        interfaces: list[Mesh] = []
        self._compressionforces: list[Line] = []
        tensionforces: list[Line] = []
        frictionforces: list[Line] = []
        resultantforces: list[Line] = []

        for interaction in blockmodel.interactions():
            interaction: ContactInterface

            interfaces.append(interaction.mesh)

            self._compressionforces += interaction.compressionforces
            tensionforces += interaction.tensionforces
            frictionforces += interaction.frictionforces
            resultantforces += interaction.resultantforce

        if show_interfaces:
            self.interfaces = self.scene.add(
                interfaces,
                name="Interfaces",
                show_points=False,
                facecolor=color_interface,
                linecolor=color_interface.contrast,
            )

        if scale_compression != 1.0:
            self.scale_compression = scale_compression
            for line in self._compressionforces:
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
            self.compressionforces = self.scene.add(
                self._compressionforces,
                name="Compression",
                linewidth=3,
                linecolor=Color.blue(),
                show_points=False,
            )
            self.tensionforces = self.scene.add(
                tensionforces,
                name="Tension",
                linewidth=3,
                linecolor=Color.red(),
                show_points=False,
            )
            self.frictionforces = self.scene.add(
                frictionforces,
                name="Friction",
                linewidth=3,
                linecolor=Color.cyan(),
                show_points=False,
            )
            self.resultantforces = self.scene.add(
                resultantforces,
                name="Resultants",
                linewidth=5,
                linecolor=Color.green(),
                show_points=False,
            )
