class ElementType:
    """This class defines an enumeration of different types of :class:`compas_model.elements.ElementType`

    Use this class to define the name of an element.

    Attributes
    ----------
    block_compound : str
        Represents a compound block element.
    block : str
        Represents a basic block element.
    joint : str
        Represents a joint element.

    bar_curved : str:
        Represents a curved bar element.
    bar : str
        Represents a straight bar element.
    beam_curved : str
        Represents a curved beam element.
    beam_raw : str
        Represents a raw beam element.
    beam : str
        Represents a straight beam element.
    cable : str
        Represents a cable element.

    interface : str
        Represents an interface element.
    membrane : str
        Represents a membrane element.
    shell : str
        Represents a shell element.
    plate : str
        Represents a plate element.

    unknown : str
        Represents an unknown or unspecified element type.
    """

    BLOCK_COMPOUND = "block_compound"
    BLOCK = "block"
    JOINT = "joint"

    BAR_CURVED = "bar_curved"
    BAR = "bar"
    BEAM_CURVED = "beam_curved"
    BEAM_RAW = "beam_raw"
    BEAM = "beam"
    CABLE = "cable"

    INTERFACE = "interface"
    MEMBRANE = "membrane"
    PLATE = "plate"
    SHELL = "shell"

    UNKNOWN = "unknown"
