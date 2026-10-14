"""Visually compare mesh sections with negative-half-space clips.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys
from math import isclose
from typing import cast

from _viewer import BLUE
from _viewer import GREEN
from _viewer import GREY
from _viewer import RED
from _viewer import show_scene

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas_model.geometry import clip_mesh
from compas_model.geometry import section_mesh


def build_example():
    section_source = Box(2, 2, 2, frame=Frame([-4, 0, 0])).to_mesh()
    section = section_mesh(section_source, Frame([-4, 0, 0]), "mesh-section")

    clip_source = Box(2, 2, 2).to_mesh()
    clip = clip_mesh(clip_source, Frame.worldXY(), "mesh-clip")

    tube_source = Box(4, 4, 2, frame=Frame([4, 0, 0])).to_mesh()
    void = Box(2, 2, 2, frame=Frame([4, 0, 0])).to_mesh()
    void.flip_cycles()
    tube_source.join(void)
    tube_clip = clip_mesh(tube_source, Frame([4, 0, 0]), "mesh-tube")

    assert section.classification == "intersecting"
    assert len(section.regions) == 1
    assert isclose(section.regions[0].area, 4.0)
    assert clip.geometry is not None
    assert isclose(clip.geometry.volume(), 4.0)
    assert tube_clip.geometry is not None
    assert len(tube_clip.section.regions) == 1
    assert len(tube_clip.section.regions[0].holes) == 1
    assert isclose(tube_clip.section.regions[0].area, 12.0)
    assert isclose(tube_clip.geometry.volume(), 12.0)

    return section_source, section, clip_source, clip, tube_source, tube_clip


def main(show=True):
    section_source, section, clip_source, clip, tube_source, tube_clip = build_example()
    clip_geometry = cast(Mesh, clip.geometry)
    tube_geometry = cast(Mesh, tube_clip.geometry)
    print(f"section only: regions={len(section.regions)}, area={section.regions[0].area:.3f}")
    print(f"closed clip: volume={clip_geometry.volume():.3f}")
    print(f"clip with hole: holes={len(tube_clip.section.regions[0].holes)}, area={tube_clip.section.regions[0].area:.3f}, volume={tube_geometry.volume():.3f}")

    if show:
        objects = [
            (section_source, "section source", GREY, 0.20),
            (section.regions[0].to_mesh(), "section face", RED, 1.00),
            (clip_source, "clip source", GREY, 0.12),
            (clip_geometry, "retained closed clip", BLUE, 0.75),
            (clip.section.regions[0].to_mesh(), "clip boundary", RED, 1.00),
            (tube_source, "tube source", GREY, 0.10),
            (tube_geometry, "retained tube clip", GREEN, 0.75),
            (tube_clip.section.regions[0].to_mesh(), "section with hole", RED, 1.00),
        ]
        labels = [
            ("SECTION: face only", (-5.2, -1.5, 1.4), RED),
            ("CLIP: retained half", (-1.3, -1.5, 1.4), BLUE),
            ("CLIP: hole + cap", (2.2, -2.7, 1.4), GREEN),
        ]
        show_scene("Mesh sectioning and clipping", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
