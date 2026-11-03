from collections.abc import Sequence

from compas.data import Data
from compas_model.modifiers import Modifier

from .contact import Contact


class InteractionRecord(Data):
    """A managed relationship between two model elements.

    Parameters
    ----------
    element_a
        GUID of the first element.
    element_b
        GUID of the second element.
    name
        Optional record name.

    """

    @property
    def __data__(self) -> dict:
        return {"element_a": self.element_a, "element_b": self.element_b, "name": self.name}

    def __init__(self, element_a: str, element_b: str, name: str | None = None) -> None:
        super().__init__(name=name)
        self.element_a = element_a
        self.element_b = element_b


class ContactRecord(InteractionRecord):
    """Computed contact regions between two elements.

    Parameters
    ----------
    element_a
        GUID of the first element.
    element_b
        GUID of the second element.
    contacts
        Contact regions belonging to the element pair.
    name
        Optional record name.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["contacts"] = self.contacts
        return data

    def __init__(self, element_a: str, element_b: str, contacts: Sequence[Contact], name: str | None = None) -> None:
        super().__init__(element_a, element_b, name=name)
        self.contacts = list(contacts)


class ModifierRecord(InteractionRecord):
    """A directed modifier from a source element to a target element.

    Parameters
    ----------
    element_a
        GUID of the source element.
    element_b
        GUID of the target element.
    modifier
        The modifier applied to the target.
    order
        Zero-based evaluation order among modifiers of the same target.
    name
        Optional record name.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["modifier"] = self.modifier
        data["order"] = self.order
        return data

    def __init__(self, element_a: str, element_b: str, modifier: Modifier, order: int = 0, name: str | None = None) -> None:
        if order < 0:
            raise ValueError("Modifier order should be greater than or equal to zero.")
        super().__init__(element_a, element_b, name=name)
        self._modifier = modifier
        self._order = order

    @property
    def modifier(self) -> Modifier:
        """Modifier: Operation applied by this record."""
        return self._modifier

    def _set_modifier(self, modifier: Modifier) -> None:
        self._modifier = modifier

    @property
    def order(self) -> int:
        """int: Zero-based position in the target's modifier sequence."""
        return self._order

    def _set_order(self, order: int) -> None:
        self._order = order

    @property
    def source(self) -> str:
        """str: GUID of the source element."""
        return self.element_a

    @property
    def target(self) -> str:
        """str: GUID of the target element."""
        return self.element_b
