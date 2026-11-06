"""Visual check of a native BRep contact interface containing a hole.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys

from _viewer import BLUE
from _viewer import GREEN
from _viewer import RED
from _viewer import show_scene

from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Polygon
from compas_model.algorithms import brep_brep_contacts
from compas_model.geometry import PlanarRegion
from compas_model.interactions import Contact

exterior = Polygon([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]])
hole = Polygon([[1, 1, 0], [1, 3, 0], [3, 3, 0], [3, 1, 0]])

source: Brep = Contact(region=PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY())).brep
target: Brep = Polygon([[0, 4, 0], [4, 4, 0], [4, 0, 0], [0, 0, 0]]).to_brep()
contacts = brep_brep_contacts(source, target, minimum_area=0.01)

assert len(contacts) == 1
contact: Contact = contacts[0]
assert len(contact.holes) == 1
assert contact.size == 12.0
print(f"holed interface: contacts=1, holes={len(contact.holes)}, net area={contact.size}")

if "--no-viewer" not in sys.argv:
    show_scene(
        "BRep contact: interface with a hole",
        [
            (source, "source face with hole", BLUE, 0.30),
            (target, "opposing target face", GREEN, 0.20),
            (contact.mesh, "computed contact", RED, 1.0),
        ],
        [("red: computed net contact area = 12", (0, 4.5, 0.1), RED)],
    )
