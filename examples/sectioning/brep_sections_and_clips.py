"""Visually compare native OCC BRep sections with capped clips.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys
from math import isclose
from math import pi
from typing import Any
from typing import cast

from _viewer import BLUE
from _viewer import GREEN
from _viewer import GREY
from _viewer import RED
from _viewer import show_scene

from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Sphere
from compas_model.geometry import clip_brep
from compas_model.geometry import section_brep


def build_example() -> tuple[Any, Any, Any, Any, Any, Any]:
    section_source = Sphere(1, frame=Frame([-3, 0, 0])).to_brep()
    section = section_brep(section_source, Frame([-3, 0, 0]), "brep-section", curve_samples=128)

    clip_source = Sphere(1).to_brep()
    clip = clip_brep(clip_source, Frame.worldXY(), "brep-clip", curve_samples=128)

    outer = Box(4, 4, 2, frame=Frame([4, 0, 0])).to_brep()
    inner = Box(2, 2, 2, frame=Frame([4, 0, 0])).to_brep()
    tube_source = cast(Brep, outer.boolean_difference(inner))
    tube_clip = clip_brep(tube_source, Frame([4, 0, 0]), "brep-tube")

    assert section.classification == "intersecting"
    assert len(section.regions) == 1
    assert isclose(section.regions[0].area, pi, rel_tol=5e-4)
    assert clip.geometry is not None
    assert isclose(clip.geometry.volume, 2 * pi / 3)
    assert tube_clip.geometry is not None
    assert len(tube_clip.section.regions) == 1
    assert len(tube_clip.section.regions[0].holes) == 1
    assert isclose(tube_clip.section.regions[0].area, 12.0)
    assert isclose(tube_clip.geometry.volume, 12.0)

    return section_source, section, clip_source, clip, tube_source, tube_clip


def main(show=True):
    section_source, section, clip_source, clip, tube_source, tube_clip = build_example()
    clip_geometry = cast(Brep, clip.geometry)
    tube_geometry = cast(Brep, tube_clip.geometry)
    print(f"curved section: regions={len(section.regions)}, area={section.regions[0].area:.3f}")
    print(f"native capped clip: volume={clip_geometry.volume:.3f}")
    print(f"native clip with hole: holes={len(tube_clip.section.regions[0].holes)}, area={tube_clip.section.regions[0].area:.3f}, volume={tube_geometry.volume:.3f}")

    if show:
        objects = [
            (section_source, "section source", GREY, 0.20),
            (section.regions[0].to_mesh(), "sampled section face", RED, 1.00),
            (clip_source, "clip source", GREY, 0.12),
            (clip_geometry, "native capped clip", BLUE, 0.75),
            (clip.section.regions[0].to_mesh(), "sampled clip boundary", RED, 1.00),
            (tube_source, "tube source", GREY, 0.10),
            (tube_geometry, "native tube clip", GREEN, 0.75),
            (tube_clip.section.regions[0].to_mesh(), "section with hole", RED, 1.00),
        ]
        labels = [
            ("SECTION: sampled face", (-4.3, -1.5, 1.4), RED),
            ("CLIP: exact OCC half", (-1.4, -1.5, 1.4), BLUE),
            ("CLIP: hole + native cap", (2.0, -2.7, 1.4), GREEN),
        ]
        show_scene("BRep sectioning and clipping", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
