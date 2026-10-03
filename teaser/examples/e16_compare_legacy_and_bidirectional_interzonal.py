# -*- coding: utf-8 -*-
# TEASER Development Team / interzonal legacy-vs-3R2C example

"""Example: compare the historic FiveElement interzonal path with 3R2C.

The same TEASER building is evaluated with two export modes:

``setpoint_difference_0.5``
    Historic setpoint-dependent treatment. An explicit neighbour-zone border
    uses one equivalent capacity (``nNZ = 1``). If the setpoint hierarchy
    changes within the schedule, the historic classification can become
    ``inner`` and the explicit neighbour-zone border disappears.

``bidirectional_2c``
    Setpoint-independent treatment. The same physical border is oriented only
    by the deterministic zone order and exported as the complete 3R2C network
    (``nNZ = 2``).

Besides the structural comparison, this example creates a diagnostic plot of
both reduced RC representations under identical boundary temperatures. The
legacy RC chain is deliberately *frozen in the initial outer_ordered
orientation* for this plot. This makes it possible to compare the historical
1C reduction and the new 2C reduction through a temperature reversal, although
an actual ``setpoint_difference_0.5`` export with a crossing schedule would
classify the border as ``inner`` already at export time.

The diagnostic starts from steady state at 26/20 degC. After 12 h the boundary
temperatures swap to 20/26 degC. Because both reductions preserve the same
steady-state total resistance, their heat flow is identical before the switch
and converges to the same opposite steady-state heat flow after the transient.
The different transient after the switch visualizes the additional thermal
state retained by the bidirectional 3R2C representation.

Run from the TEASER repository root with::

    python -m teaser.examples.e16_compare_legacy_and_bidirectional_interzonal

The plot is saved as ``e16_legacy_vs_bidirectional.png`` in the current working
directory and is shown interactively by default.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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
        "R": [float(value) for value in attr.r_nzb[index]],
        "C": [float(value) for value in attr.c_nzb[index]],
        "R_rem": float(attr.r_rest_nzb[index]),
    }


def _steady_state_capacitor_temperatures(summary, t_a, t_b):
    """Return steady-state capacitor temperatures for a serial RC chain."""
    resistances = np.asarray(summary["R"], dtype=float)
    r_rem = float(summary["R_rem"])
    r_total = float(np.sum(resistances) + r_rem)
    q_flow = (t_a - t_b) / r_total
    return t_a - q_flow * np.cumsum(resistances)


def _rc_derivative(temperatures, t_a, t_b, resistances, r_rem, capacities):
    """Temperature derivative of AixLib ExteriorWall's serial RC topology."""
    n = len(capacities)
    derivative = np.zeros(n, dtype=float)

    for i in range(n):
        if i == 0:
            q_left = (t_a - temperatures[i]) / resistances[i]
        else:
            q_left = (temperatures[i - 1] - temperatures[i]) / resistances[i]

        if i == n - 1:
            q_right = (t_b - temperatures[i]) / r_rem
        else:
            q_right = (temperatures[i + 1] - temperatures[i]) / resistances[i + 1]

        derivative[i] = (q_left + q_right) / capacities[i]

    return derivative


def _simulate_rc_chain(summary, time_s, t_a, t_b):
    """Integrate the reduced wall RC chain with RK4 and fixed boundary data."""
    resistances = np.asarray(summary["R"], dtype=float)
    capacities = np.asarray(summary["C"], dtype=float)
    r_rem = float(summary["R_rem"])

    if len(resistances) != len(capacities):
        raise ValueError("R and C vectors must have identical lengths.")
    if np.any(resistances <= 0) or r_rem <= 0 or np.any(capacities <= 0):
        raise ValueError("All RC parameters must be strictly positive.")

    temperatures = np.zeros((len(time_s), len(capacities)), dtype=float)
    q_a = np.zeros(len(time_s), dtype=float)
    q_b = np.zeros(len(time_s), dtype=float)

    temperatures[0] = _steady_state_capacitor_temperatures(
        summary,
        float(t_a[0]),
        float(t_b[0]),
    )

    for k in range(len(time_s)):
        current = temperatures[k]
        q_a[k] = (t_a[k] - current[0]) / resistances[0]
        q_b[k] = (current[-1] - t_b[k]) / r_rem

        if k == len(time_s) - 1:
            break

        dt = float(time_s[k + 1] - time_s[k])
        ta = float(t_a[k])
        tb = float(t_b[k])

        def f(state):
            return _rc_derivative(
                state,
                ta,
                tb,
                resistances,
                r_rem,
                capacities,
            )

        k1 = f(current)
        k2 = f(current + 0.5 * dt * k1)
        k3 = f(current + 0.5 * dt * k2)
        k4 = f(current + dt * k3)
        temperatures[k + 1] = current + dt * (k1 + 2*k2 + 2*k3 + k4) / 6.0

    return {
        "T_cap": temperatures,
        "Q_a": q_a,
        "Q_b": q_b,
    }


def _plot_dynamic_comparison(legacy, new, output_path=None, show=True):
    """Plot identical boundary temperatures and both reduced-wall responses."""
    switch_h = 12.0
    dt_s = 60.0
    time_s = np.arange(0.0, 24.0 * 3600.0 + dt_s, dt_s)
    time_h = time_s / 3600.0

    t_a = np.where(time_h < switch_h, 299.15, 293.15)
    t_b = np.where(time_h < switch_h, 293.15, 299.15)

    legacy_response = _simulate_rc_chain(legacy, time_s, t_a, t_b)
    new_response = _simulate_rc_chain(new, time_s, t_a, t_b)

    r_legacy = sum(legacy["R"]) + legacy["R_rem"]
    r_new = sum(new["R"]) + new["R_rem"]
    if not np.isclose(r_legacy, r_new, rtol=1e-10, atol=1e-12):
        raise AssertionError(
            "Legacy and bidirectional reductions do not preserve the same "
            f"steady-state resistance: {r_legacy} vs {r_new}."
        )

    pre_switch = time_h < switch_h
    max_pre_diff = float(np.max(np.abs(
        legacy_response["Q_a"][pre_switch] - new_response["Q_a"][pre_switch]
    )))
    final_diff = float(abs(
        legacy_response["Q_a"][-1] - new_response["Q_a"][-1]
    ))

    print("\nDynamic RC diagnostic (same boundary temperatures)")
    print(f"  total R legacy:        {r_legacy:.12g} K/W")
    print(f"  total R bidirectional: {r_new:.12g} K/W")
    print(f"  max |dQ| before 12 h:  {max_pre_diff:.6g} W")
    print(f"  |dQ| at 24 h:          {final_diff:.6g} W")
    print(
        "  Note: the legacy curve uses the initial outer_ordered 1C topology "
        "frozen through the switch; the real crossing legacy export would "
        "classify this border as inner."
    )

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

    axes[0].plot(time_h, t_a - 273.15, label="Zone A boundary")
    axes[0].plot(time_h, t_b - 273.15, label="Zone B boundary")
    axes[0].set_ylabel("Temperature [degC]")
    axes[0].set_title("Identical boundary temperatures")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(
        time_h,
        legacy_response["Q_a"],
        label="Legacy 1C (frozen initial orientation)",
    )
    axes[1].plot(
        time_h,
        new_response["Q_a"],
        label="Bidirectional 2C",
    )
    axes[1].axhline(0.0, linewidth=0.8)
    axes[1].set_ylabel("Heat flow A -> wall [W]")
    axes[1].set_title("Interzonal heat-flow response")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(
        time_h,
        legacy_response["T_cap"][:, 0] - 273.15,
        label="Legacy wall state C1",
    )
    axes[2].plot(
        time_h,
        new_response["T_cap"][:, 0] - 273.15,
        label="Bidirectional wall state C1",
    )
    axes[2].plot(
        time_h,
        new_response["T_cap"][:, 1] - 273.15,
        label="Bidirectional wall state C2",
    )
    axes[2].set_ylabel("Wall state temperature [degC]")
    axes[2].set_xlabel("Time [h]")
    axes[2].set_title("Reduced wall thermal states")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    for axis in axes:
        axis.axvline(switch_h, linestyle="--", linewidth=1.0)

    fig.suptitle(
        "TEASER interzonal reduction: legacy 1C vs bidirectional 3R2C",
        fontsize=13,
    )
    fig.tight_layout()

    if output_path is None:
        output_path = Path.cwd() / "e16_legacy_vs_bidirectional.png"
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    print(f"  plot saved to: {output_path.resolve()}")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return output_path


def example_compare_legacy_and_bidirectional(
    with_plot=True,
    show_plot=True,
    plot_path=None,
):
    """Print structural differences and optionally plot the RC response."""
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

    if with_plot:
        _plot_dynamic_comparison(
            legacy,
            new,
            output_path=plot_path,
            show=show_plot,
        )

    return legacy, new


if __name__ == "__main__":
    example_compare_legacy_and_bidirectional()
