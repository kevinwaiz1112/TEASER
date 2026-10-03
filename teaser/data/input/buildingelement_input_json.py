"""This module contains function to load building element classes."""

import warnings

from teaser.logic.buildingobjects.buildingphysics.layer import Layer
from teaser.logic.buildingobjects.buildingphysics.material import Material
import teaser.data.input.material_input_json as mat_input


def _range_distance(year, building_age_group):
    """Return the distance from *year* to the closest range boundary."""
    start, end = building_age_group
    if start <= year <= end:
        return 0
    if year < start:
        return start - year
    return year - end


def _select_type_element(element_binding, year, construction, element_type):
    """Select an exact or nearest type-element entry.

    Exact in-range matches retain the historical first-match behaviour. If the
    requested synthetic year is outside all ranges for the requested
    ``construction`` and ``element_type``, the candidate whose age-group
    boundary is closest to the requested year is used. This is important for
    TABULA archetypes whose class coverage does not start in year 0 (for
    example ``tabula_standard_1_AB`` starts at 1860).
    """
    candidates = []

    for order, (key, element_in) in enumerate(element_binding.items()):
        if key == "version":
            continue
        if (
            element_in["construction_type"] == construction
            and key.startswith(element_type)
        ):
            start, end = element_in["building_age_group"]
            if start <= year <= end:
                return key, element_in, False
            candidates.append((order, key, element_in))

    if not candidates:
        raise ValueError(
            "No type element available for "
            f"year={year}, construction='{construction}', "
            f"element_type='{element_type}'."
        )

    _, key, element_in = min(
        candidates,
        key=lambda item: (
            _range_distance(year, item[2]["building_age_group"]),
            item[0],
        ),
    )
    selected_range = element_in["building_age_group"]
    warnings.warn(
        "No exact type-element age range for "
        f"year={year}, construction='{construction}', "
        f"element_type='{element_type}'. Using closest available entry "
        f"key='{key}', range={selected_range}.",
        UserWarning,
    )
    return key, element_in, True


def _load_element_entry(element, element_in, data_class, reverse_layers=False):
    """Apply one type-element entry to a building element."""
    _set_basic_data(element=element, element_in=element_in)
    for id, layer_in in (
        element_in["layer"].items().__reversed__()
        if reverse_layers else element_in["layer"].items()
    ):
        layer = Layer(element)
        layer.id = id
        layer.thickness = layer_in["thickness"]
        material = Material(layer)
        mat_input.load_material_id(
            material, layer_in["material"]["material_id"], data_class
        )


def load_type_element(element, year, construction, data_class,
                      element_type=None, reverse_layers=False):
    """Load BuildingElement from json.

    Loads typical building elements according to their construction year and
    their construction type from a JSON. Exact age-range matching is preserved.
    If the requested year lies outside all ranges for the requested
    construction/type combination, the closest available age range is used and
    a warning is emitted.

    Parameters
    ----------
    element : BuildingElement()
        Instance of BuildingElement or inherited Element of TEASER

    year : int
        Year of construction

    construction : str
        Construction type, code list ('heavy', 'light', tabula, ...)

    data_class : DataClass()
        DataClass containing the bindings for TypeBuildingElement and
        Material.

    element_type : str
        Element type to load - only to specify if the data_class entry for a
        different type than type(element) is to be loaded, e.g. InnerWall
        instead of OuterWall

    reverse_layers : bool
        defines if layer list should be reversed - this is necessary for zone
        borders to maintain consistency

    Returns
    -------
    str
        Key of the selected type-element entry.
    """
    element_binding = data_class.element_bind

    if element_type is None:
        element_type = type(element).__name__

    key, element_in, _ = _select_type_element(
        element_binding=element_binding,
        year=year,
        construction=construction,
        element_type=element_type,
    )
    _load_element_entry(
        element=element,
        element_in=element_in,
        data_class=data_class,
        reverse_layers=reverse_layers,
    )
    return key


def load_type_element_by_key(element, key_str, data_class,
                             reverse_layers=False):
    """Load BuildingElement from json by key string.

    Loads typical building elements according to their key string from a JSON.

    Returns
    -------
    str
        The loaded key.
    """
    element_binding = data_class.element_bind
    element_in = element_binding[key_str]
    _load_element_entry(
        element=element,
        element_in=element_in,
        data_class=data_class,
        reverse_layers=reverse_layers,
    )
    return key_str


def _set_basic_data(element, element_in):
    """Set basic data for building elements."""
    element.building_age_group = element_in["building_age_group"]
    element.construction_type = element_in["construction_type"]
    element.inner_radiation = element_in["inner_radiation"]
    element.inner_convection = element_in["inner_convection"]

    if (
        type(element).__name__ == "OuterWall"
        or type(element).__name__ == "Rooftop"
        or type(element).__name__ == "Door"
    ):
        element.outer_radiation = element_in["outer_radiation"]
        element.outer_convection = element_in["outer_convection"]

    elif type(element).__name__ == "Window":
        element.outer_radiation = element_in["outer_radiation"]
        element.outer_convection = element_in["outer_convection"]
        element.g_value = element_in["g_value"]
        element.a_conv = element_in["a_conv"]
        element.shading_g_total = element_in["shading_g_total"]
        element.shading_max_irr = element_in["shading_max_irr"]

    if type(element).__name__.startswith("Interzonal"):
        element.outer_radiation = element_in["inner_radiation"]
        element.outer_convection = element_in["inner_convection"]
