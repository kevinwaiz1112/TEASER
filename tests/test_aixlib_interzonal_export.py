from types import SimpleNamespace

import pytest

from teaser.data.output.aixlib_output import _prepare_five_element_interzonal_export


def _zone(**overrides):
    values = dict(
        area_nzb=[],
        alpha_conv_inner_nzb=[],
        h_con_calc_method_nzb=[],
        surface_orientation_nzb=[],
        n_nzb=2,
        r_nzb=[],
        r_rest_nzb=[],
        c_nzb=[],
        other_nz_indexes=[],
    )
    values.update(overrides)
    attr = SimpleNamespace(**values)
    parent = SimpleNamespace(thermal_zones=[])
    zone = SimpleNamespace(name="Zone_1", model_attr=attr, parent=parent)
    parent.thermal_zones.append(zone)
    return zone


def test_empty_neighbour_list_exports_one_dimensionally_consistent_placeholder():
    data = _prepare_five_element_interzonal_export(_zone())

    assert data["nNZs"] == 1 == len(data["ANZ"])
    assert data["ANZ"] == [0.0]
    for key in (
        "hConNZ",
        "hConNZMethod",
        "surfaceOrientationNZ",
        "RNZRem",
        "CNZ",
        "RNZ",
        "otherNZIndex",
    ):
        assert len(data[key]) == data["nNZs"]
    assert all(len(row) == data["nNZ"] for row in data["RNZ"])
    assert all(len(row) == data["nNZ"] for row in data["CNZ"])


def test_real_neighbour_arrays_use_anz_length_as_n_nzs():
    zone = _zone(
        area_nzb=[12.0, 8.0],
        alpha_conv_inner_nzb=[1.7, 1.7],
        h_con_calc_method_nzb=[2, 3],
        surface_orientation_nzb=[1, 2],
        n_nzb=2,
        r_nzb=[[0.1, 0.2], [0.3, 0.4]],
        r_rest_nzb=[0.5, 0.6],
        c_nzb=[[1000.0, 2000.0], [3000.0, 4000.0]],
        other_nz_indexes=[1, 2],
    )

    data = _prepare_five_element_interzonal_export(zone)

    assert data["nNZs"] == 2
    assert len(data["ANZ"]) == 2
    assert len(data["hConNZ"]) == 2
    assert len(data["otherNZIndex"]) == 2
    assert data["otherNZIndex"] == [2, 3]


def test_real_neighbour_dimension_mismatch_raises():
    zone = _zone(
        area_nzb=[12.0, 8.0],
        alpha_conv_inner_nzb=[1.7],
        h_con_calc_method_nzb=[2, 3],
        surface_orientation_nzb=[1, 2],
        r_nzb=[[0.1, 0.2], [0.3, 0.4]],
        r_rest_nzb=[0.5, 0.6],
        c_nzb=[[1000.0, 2000.0], [3000.0, 4000.0]],
        other_nz_indexes=[1, 2],
    )

    with pytest.raises(ValueError, match="hConNZ has length 1"):
        _prepare_five_element_interzonal_export(zone)
