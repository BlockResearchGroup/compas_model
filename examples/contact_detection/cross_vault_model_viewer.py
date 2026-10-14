"""Explore cross-vault contacts with the COMPAS Model viewer infrastructure.

The example demonstrates the hierarchy, group, type, and interaction views;
multiple selection; recursive branch visibility; selection inspection; shared
render geometry; unit-aware approximation; and a contact-interface overlay.

Run with ``--no-viewer`` to validate model construction and contact metadata
without opening a window.
"""

import sys
from collections import defaultdict
from typing import cast

from _viewer import AMBER
from _viewer import BLUE
from _viewer import DARK
from cross_vault import build_example

from compas_model.models import Model
from compas_model.viewer import ModelViewer
from compas_model.viewer import RenderSettings


def prepare_model():
    """Build the contact model and add hierarchy and inspector metadata."""
    model, blocks, contact_edges, contacts = build_example()
    model.unit = "MM"

    collections = {name: model.add_collection(name) for name in ("North West", "North East", "South West", "South East")}
    neighbors = defaultdict(set)
    region_counts = defaultdict(int)

    for edge in contact_edges:
        u, v = cast(tuple[int, int], edge)
        a = model.graph.node_element(u)
        b = model.graph.node_element(v)
        regions = model.graph.edge_attribute((u, v), name="contacts") or []
        neighbors[str(a.guid)].add(str(b.guid))
        neighbors[str(b.guid)].add(str(a.guid))
        region_counts[str(a.guid)] += len(regions)
        region_counts[str(b.guid)] += len(regions)

    for block in blocks:
        x, y, _ = block.modelgeometry.centroid()
        quadrant = ("North" if y >= 0 else "South") + (" East" if x >= 0 else " West")
        collections[quadrant].add_element(block)
        block.treenode.attributes.update(
            {
                "quadrant": quadrant,
                "contacting_neighbors": len(neighbors[str(block.guid)]),
                "contact_regions": region_counts[str(block.guid)],
            }
        )

    focus = max(blocks, key=lambda block: (region_counts[str(block.guid)], len(neighbors[str(block.guid)])))
    return model, blocks, contacts, collections, focus


def create_viewer(model, blocks, focus) -> ModelViewer:
    """Create and configure the interactive model viewer."""
    controller = ModelViewer(model, settings=RenderSettings(unit="MM", quality="standard"))
    controller.viewer.config.window.title = "Cross vault: model hierarchy and contacts"

    for block in blocks:
        scene_object = controller.object_for_element(block)
        scene_object.facecolor = AMBER if block is focus else BLUE
        scene_object.edgecolor = DARK
        scene_object.opacity = 0.32

    controller.select([focus], clear=True)
    return controller


def main(show: bool = True) -> Model:
    model, blocks, contacts, collections, focus = prepare_model()

    print(f"blocks: {len(blocks)}")
    print(f"collections: {len(collections)}")
    print(f"contact regions: {len(contacts)}")
    print(f"selected block: {focus.name}")
    print(f"selected block contacts: {focus.treenode.attributes['contact_regions']}")

    if show:
        create_viewer(model, blocks, focus).show_viewer()

    return model


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
