from collections.abc import Iterable
from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import Any

from compas.data import Data
from compas_model.elements import Element

if TYPE_CHECKING:
    from .model import Model


class Collection(Data):
    """Named, non-hierarchical set of model elements.

    Collections contain element references and may overlap. They do not affect
    hierarchy, transformations, spatial indices, or interaction topology.

    Parameters
    ----------
    name
        Human-readable collection name.
    element_guids
        Serialized element membership.
    attributes
        User-defined metadata.

    """

    @property
    def __data__(self) -> dict:
        return {
            "name": self.name,
            "element_guids": list(self._element_guids),
            "attributes": self.attributes,
        }

    def __init__(
        self,
        name: str | None = None,
        element_guids: Iterable[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name=name)
        self.attributes = dict(attributes or {})
        self._element_guids = dict.fromkeys(element_guids or ())
        self.model: Model | None = None

    def __len__(self) -> int:
        return len(self._element_guids)

    def __iter__(self) -> Iterator[Element]:
        return self.elements()

    @property
    def element_guids(self) -> tuple[str, ...]:
        """tuple[str, ...]: Element GUIDs in insertion order."""
        return tuple(self._element_guids)

    def elements(self) -> Iterator[Element]:
        """Iterate over member elements in insertion order."""
        model = self._require_model()
        for guid in self._element_guids:
            yield model.element_by_guid(guid)

    def add_element(self, element: Element) -> None:
        """Add an element already contained in the owning model."""
        model = self._require_model()
        if not model.has_element(element):
            raise ValueError("The element is not part of the collection's model.")
        self._element_guids[str(element.guid)] = None

    def add_elements(self, elements: Iterable[Element]) -> None:
        """Add multiple model elements."""
        for element in elements:
            self.add_element(element)

    def remove_element(self, element: Element) -> None:
        """Remove an element from this collection."""
        self._element_guids.pop(str(element.guid), None)

    def has_element(self, element: Element) -> bool:
        """Return whether the element belongs to this collection."""
        return str(element.guid) in self._element_guids

    def _require_model(self) -> "Model":
        if self.model is None:
            raise RuntimeError("The collection should be added to a model first.")
        return self.model
