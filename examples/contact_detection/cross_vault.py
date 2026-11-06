"""Compute and visualize contacts in the cross-vault block model.

Each named object in ``data/cross_vault.obj`` becomes one mesh element while
preserving the original polygonal faces. Blocks participating in contact are
translucent blue, isolated blocks are grey, and the computed contact-interface
meshes are opaque red.

Run with ``--no-viewer`` to compute and report the contacts without opening a
window.
"""

import sys

from _cross_vault import build_cross_vault
from _viewer import BLUE
from _viewer import GREY
from _viewer import RED
from _viewer import show_scene

model, blocks, contact_edges, contacts = build_cross_vault()
connected_nodes = {node for edge in contact_edges for node in edge}
total_area = sum(contact.size for contact in contacts)

print(f"blocks: {len(blocks)}")
print(f"contacting pairs: {len(contact_edges)}")
print(f"contact regions: {len(contacts)}")
print(f"total contact area: {total_area:.3f}")

if "--no-viewer" not in sys.argv:
    objects = []
    for block in blocks:
        color = BLUE if block.graphnode in connected_nodes else GREY
        objects.append((block.final_geometry, block.name, color, 0.28))
    contact_mesh = contacts[0].mesh.copy()
    for contact in contacts[1:]:
        contact_mesh.join(contact.mesh)
    objects.append((contact_mesh, "all contact interfaces", RED, 1.0))

    labels = [
        (
            f"{len(blocks)} blocks | {len(contact_edges)} pairs | {len(contacts)} contact regions",
            (-175, -200, 190),
            RED,
        )
    ]
    show_scene("Cross vault: detected block contacts", objects, labels)
