# -*- coding: utf-8 -*-
# TEASER Development Team / interzonal legacy-vs-3R2C example

"""Example: compare the historic FiveElement interzonal path with 3R2C.

The same TEASER building is evaluated with two export modes:

``setpoint_difference_0.5``
    Historic setpoint-dependent treatment.  An explicit neighbour-zone border
    uses one equivalent capacity (``nNZ = 1``).  If the setpoint hierarchy
    changes within the schedule, the historic classification can become
    ``inner`` and the explicit neighbour-zone border disappears.

``bidirectional_2c``
    Setpoint-independent treatment.  The same physical border is oriented only
    by the deterministic zone order and exported as the complete 3R2C network
    (``nNZ = 2``).

Run from the TEASER repository root with::

    python -m teaser.examples.e16_compare_legacy_and_bidirectional_interzonal

This example is intentionally parameter/export focused.  The supplied AixLib
validation models demonstrate the actual run-time heat-flow reversal.
"""

from __future__ import annotations

from teaser.project import Project
from teaser.logic import utilities


def _load_project():
    prj = Project(False)
    prj.load_project(
        utilities.get_full_path("examples/examplefiles/e10_varD.json")
    )
    return prj


def _find_border(zone, other_zone):
    matches = [
        element
        for element in zone.interzonal_elements
        if element.other_side is other_zone
    ]
    if not matches:
        raise RuntimeError(
            f"No interzonal border found between {zone.name} and {other_zone.name}."
        )
    return matches[0]


def _configure_profiles(prj, crossing):
    building = prj.buildings[0]
    zone_a = building.thermal_zones[1]
    zone_b = building.thermal_zones[2]

    zone_a.use_conditions.with_heating = True
    zone_b.use_conditions.with_heating = True
    zone_a.use_conditions.with_cooling = False
    zone_b.use_conditions.with_cooling = False

    if crossing:
        zone_a.use_conditions.heating_profile = [299.15] * 12 + [293.15] * 12
        zone_b.use_conditions.heating_profile = [293.15] * 12 + [299.15] * 12
    else:
        zone_a.use_conditions.heating_profile = [299.15] * 24
        zone_b.use_conditions.heating_profile = [293.15] * 24

    zone_a.use_conditions.cooling_profile = [373.15] * 24
    zone_b.use_conditions.cooling_profile = [373.15] * 24
    return zone_a, zone_b


def _summarize_constant_order_case(method):
    prj = _load_project()
    zone_a, zone_b = _configure_profiles(prj, crossing=False)
    border = _find_border(zone_a, zone_b)
    prj.method_interzonal_export = method

    export_type = border.interzonal_type_export
    prj.buildings[0].calc_building_parameter(
        number_of_elements=5,
        used_library="AixLib",
    )

    attr = zone_a.model_attr
    groups = [
        (i, group)
        for i, group in enumerate(attr.nzbs_per_nz)
        if border in group
    ]
    if not groups:
        return {
            "method": method,
            "export_type": export_type,
            "n_nzb": None,
            "R": None,
            "C": None,
            "R_rem": None,
        }

    index = groups[0][0]
    return {
        "method": method,
        "export_type": export_type,
        "n_nzb": attr.n_nzb,
        "R": attr.r_nzb[index],
        "C": attr.c_nzb[index],
        "R_rem": attr.r_rest_nzb[index],
    }


def example_compare_legacy_and_bidirectional():
    """Print structural differences for identical source geometry."""
    legacy = _summarize_constant_order_case("setpoint_difference_0.5")
    new = _summarize_constant_order_case("bidirectional_2c")

    print("Same physical border, constant initial ordering")
    print("Historic method:")
    print(f"  export type: {legacy['export_type']}")
    print(f"  nNZ: {legacy['n_nzb']}")
    print(f"  RNZ: {legacy['R']}")
    print(f"  RNZRem: {legacy['R_rem']}")
    print(f"  CNZ: {legacy['C']}")
    print("Bidirectional method:")
    print(f"  export type: {new['export_type']}")
    print(f"  nNZ: {new['n_nzb']}")
    print(f"  RNZ: {new['R']}")
    print(f"  RNZRem: {new['R_rem']}")
    print(f"  CNZ: {new['C']}")

    # Show the central classification difference for rotating setpoints.
    prj_legacy = _load_project()
    a_old, b_old = _configure_profiles(prj_legacy, crossing=True)
    border_old = _find_border(a_old, b_old)
    prj_legacy.method_interzonal_export = "setpoint_difference_0.5"

    prj_new = _load_project()
    a_new, b_new = _configure_profiles(prj_new, crossing=True)
    border_new = _find_border(a_new, b_new)
    prj_new.method_interzonal_export = "bidirectional_2c"

    print("\nCrossing 26/20 -> 20/26 degC schedules")
    print(
        "  historic classification: "
        f"{border_old.interzonal_type_export}"
    )
    print(
        "  bidirectional classification: "
        f"{border_new.interzonal_type_export}"
    )
    print(
        "The new mode keeps the physical border explicit; heat-flow direction "
        "is resolved by the continuous Modelica network at run time."
    )

    return legacy, new


if __name__ == "__main__":
    example_compare_legacy_and_bidirectional()
