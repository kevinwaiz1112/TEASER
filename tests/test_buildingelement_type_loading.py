import pytest

from teaser.data.dataclass import DataClass
from teaser.project import Project
from teaser.logic.buildingobjects.building import Building
from teaser.logic.buildingobjects.thermalzone import ThermalZone
from teaser.logic.buildingobjects.buildingphysics.outerwall import OuterWall
from teaser.logic.buildingobjects.buildingphysics.rooftop import Rooftop
from teaser.logic.buildingobjects.buildingphysics.groundfloor import GroundFloor
from teaser.logic.buildingobjects.buildingphysics.window import Window


def _zone_with_tabula_data():
    project = Project(load_data=False)
    project.data = DataClass(used_statistic="tabula_de")
    building = Building(parent=project)
    building.year_of_construction = 1850
    zone = ThermalZone(parent=building)
    return project, building, zone


@pytest.mark.parametrize("element_cls", [OuterWall, GroundFloor, Rooftop, Window])
def test_tabula_ab_1850_falls_back_to_1860(element_cls):
    _, _, zone = _zone_with_tabula_data()
    element = element_cls(parent=zone)

    with pytest.warns(UserWarning, match="closest available entry"):
        key = element.load_type_element(
            year=1850,
            construction="tabula_standard_1_AB",
        )

    assert key is not None
    assert element.building_age_group == [1860, 1918]
    assert element.inner_convection is not None
    assert element.inner_radiation is not None
    assert len(element.layer) > 0


def test_tabula_mfh_1850_keeps_exact_range_without_fallback():
    _, _, zone = _zone_with_tabula_data()
    element = OuterWall(parent=zone)

    key = element.load_type_element(
        year=1850,
        construction="tabula_standard_1_MFH",
    )

    assert key.startswith("OuterWall_[0, 1859]_tabula_standard_1_MFH")
    assert element.building_age_group == [0, 1859]
    assert element.inner_convection is not None
    assert len(element.layer) > 0


def test_missing_construction_raises_descriptive_value_error():
    _, _, zone = _zone_with_tabula_data()
    element = OuterWall(parent=zone)

    with pytest.raises(ValueError, match="No type element available"):
        element.load_type_element(
            year=1850,
            construction="does_not_exist",
        )
