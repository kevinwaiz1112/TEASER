# -*- coding: utf-8 -*-
# TEASER Development Team / bidirectional interzonal extension example

"""Example: export an interzonal border as a bidirectional 3R2C element.

This example reuses the multizone building from example 10.  Two adjacent
zones receive heating schedules whose order changes during the day.  The new
``bidirectional_2c`` export method keeps the physical border explicit and
exports the complete VDI 6007 wall reduction

    R1 - C1 - R3 - C2 - R2

instead of choosing the RC orientation from the setpoint hierarchy.
Horizontal interzonal floor/ceiling surfaces additionally activate the
existing temperature-dependent natural-convection model in AixLib.

Run from the TEASER repository root with::

    python -m teaser.examples.e15_bidirectional_interzonal_3r2c

An optional export directory can be passed as the first command-line argument.
"""

from __future__ import annotations

import os
import sys

from teaser.project import Project
from teaser.logic import utilities


def _find_border(zone, other_zone):
    """Return the first interzonal element between two thermal zones."""
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


def example_bidirectional_interzonal_3r2c(export_dir=None):
    """Create and export the bidirectional interzonal FiveElement example."""
    prj = Project(False)
    prj.load_project(
        utilities.get_full_path("examples/examplefiles/e10_varD.json")
    )

    building = prj.buildings[0]
    basement = building.thermal_zones[1]
    main_zone = building.thermal_zones[2]
    border = _find_border(basement, main_zone)

    # The relative setpoint order changes after 12 entries.  The export must
    # not alter its topology because of this change.
    basement.use_conditions.with_heating = True
    main_zone.use_conditions.with_heating = True
    basement.use_conditions.with_cooling = False
    main_zone.use_conditions.with_cooling = False
    basement.use_conditions.heating_profile = [299.15] * 12 + [293.15] * 12
    main_zone.use_conditions.heating_profile = [293.15] * 12 + [299.15] * 12
    basement.use_conditions.cooling_profile = [373.15] * 24
    main_zone.use_conditions.cooling_profile = [373.15] * 24

    # Only the export decision is changed.  The material enrichment method can
    # remain the established project setting.
    prj.method_interzonal_export = "bidirectional_2c"

    building.calc_building_parameter(
        number_of_elements=5,
        used_library="AixLib",
    )

    model_attr = basement.model_attr
    border_index = next(
        i
        for i, group in enumerate(model_attr.nzbs_per_nz)
        if group[0] is border
    )

    print("Bidirectional interzonal 3R2C parameters")
    print(f"  border: {basement.name} <-> {main_zone.name}")
    print(f"  nNZ: {model_attr.n_nzb}")
    print(f"  RNZ: {model_attr.r_nzb[border_index]}")
    print(f"  RNZRem: {model_attr.r_rest_nzb[border_index]}")
    print(f"  CNZ: {model_attr.c_nzb[border_index]}")
    print(f"  hCon method: {model_attr.h_con_calc_method_nzb[border_index]}")
    print(f"  surface orientation: {model_attr.surface_orientation_nzb[border_index]}")

    # Portable weather/soil files shipped with TEASER are used for the Modelica
    # export.  Dymola can then simulate the generated model with the patched
    # AixLib FiveElements implementation.
    prj.weather_file_path = utilities.get_full_path(
        "data/input/inputdata/weatherdata/"
        "DEU_BW_Mannheim_107290_TRY2010_12_Jahr_BBSR.mos"
    )
    prj.t_soil_file_path = utilities.get_full_path(
        "data/input/inputdata/weatherdata/t_soil_sample_constant_283_15.mos"
    )
    prj.name = "Example_e15_Bidirectional3R2C"

    if export_dir is not None:
        export_dir = os.path.abspath(export_dir)
        os.makedirs(export_dir, exist_ok=True)

    export_path = prj.export_aixlib(path=export_dir)
    print(f"Exported AixLib model to: {export_path}")
    return export_path


if __name__ == "__main__":
    example_bidirectional_interzonal_3r2c(
        sys.argv[1] if len(sys.argv) > 1 else None
    )
