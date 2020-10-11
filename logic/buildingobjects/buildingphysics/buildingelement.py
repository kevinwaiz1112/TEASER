"""This module contains the Base class for all building elements."""

from __future__ import division
import warnings
from teaser.logic.buildingobjects.buildingphysics.layer import Layer
from teaser.logic.buildingobjects.buildingphysics.material import Material
import teaser.data.input.buildingelement_input_json as buildingelement_input
import teaser.data.input.material_input_json as material_input
import numpy as np
import random
import re


class BuildingElement(object):
    """Building element class.

    This is the base class for all building elements. Building elements are
    all physical elements that may serve as boundaries for a thermal zone or
    building.

    Parameters
    ----------

    parent : ThermalZone()
        The parent class of this object, the ThermalZone the BE belongs to.
        Allows for better control of hierarchical structures.
        Default is None.

    Attributes
    ----------

    internal_id : float
        Random id for the distinction between different elements.
    name : str
        Individual name
    construction_type : str
        Type of construction (e.g. "heavy" or "light"). Needed for
        distinction between different constructions types in the same
        building age period.
    year_of_retrofit : int
        Year of last retrofit
    year_of_construction : int
        Year of first construction
    building_age_group : list
        Determines the building age period that this building
        element belongs to [begin, end], e.g. [1984, 1994]
    area : float [m2]
        Area of building element
    tilt : float [degree]
        Tilt against horizontal
    orientation : float [degree]
        Azimuth direction of building element (0 : north, 90: east, 180: south,
        270: west)
    inner_convection : float [W/(m2*K)]
        Constant heat transfer coefficient of convection inner side (facing
        the zone)
    inner_radiation : float [W/(m2*K)]
        Constant heat transfer coefficient of radiation inner side (facing
        the zone)
    outer_convection : float [W/(m2*K)]
        Constant heat transfer coefficient of convection outer side (facing
        the ambient or adjacent zone). Currently for all InnerWalls and
        GroundFloors this value is set to 0.0
    outer_radiation : float [W/(m2*K)]
        Constant heat transfer coefficient of radiation outer side (facing
        the ambient or adjacent zone). Currently for all InnerWalls and
        GroundFloors this value is set to 0.0
    layer : list
        List of all layers of a building element (to be filled with Layer
        objects). Use element.layer = None to delete all layers of the building
        element
    view_factors : list
        view factors for half-space above (outer) surface for sky/ground/other
        buildings/surfaces with ambient temperature for use in AixLib with
        FiveElementVectorized and calculateHeatFlow. Values must already be
        corrected for cosine loss and possible directional dependance of
        absorptivity. If specified, sum should be 1. If sum is 0, default
        assumptions are used in AixLib"

    Calculated Attributes

    r1 : float [K/W]
        equivalent resistance R1 of the analogous model given in VDI 6007
    r2 : float [K/W]
        equivalent resistance R2 of the analogous model given in VDI 6007
    r3 : float [K/W]
        equivalent resistance R3 of the analogous model given in VDI 6007
    c1 : float [J/K]
        equivalent capacity C1 of the analogous model given in VDI 6007
    c2 : float [J/K]
        equivalent capacity C2 of the analogous model given in VDI 6007
    c1_korr : float [J/K]
        corrected capacity C1,korr for building elements in the case of
        asymmetrical thermal load given in VDI 6007
    u_value : float [W/m2K)
        U-Value of building element
    ua_value : float [W/K]
        UA-Value of building element (Area times U-Value)
    r_inner_conv : float [K/W]
        Convective resistance of building element on inner side (facing the
        zone)
    r_inner_rad : float [K/W]
        Radiative resistance of building element on inner side (facing the
        zone)
    r_inner_conv : float [K/W]
        Combined convective and radiative resistance of building element on
        inner side (facing the zone)
    r_outer_conv : float [K/W]
        Convective resistance of building element on outer side (facing
        the ambient or adjacent zone). Currently for all InnerWalls and
        GroundFloors this value is set to 0.0
    r_outer_rad : float [K/W]
        Radiative resistance of building element on outer side (facing
        the ambient or adjacent zone). Currently for all InnerWalls and
        GroundFloors this value is set to 0.0
    r_outer_conv : float [K/W]
        Combined convective and radiative resistance of building element on
        outer side (facing the ambient or adjacent zone). Currently for all
        InnerWalls and GroundFloors this value is set to 0.0
    wf_out : float
        Weightfactor of building element ua_value/ua_value_zone
    """

    def __init__(self, parent=None):
        """Constructor for BuildingElement
        """

        self.parent = parent

        self.internal_id = random.random()

        self.name = None
        self._construction_type = None
        self._year_of_retrofit = None
        self._year_of_construction = None
        self.building_age_group = [None, None]

        self._area = None
        self._tilt = None
        self._orientation = None
        self._idx_orientation = None
        self._inner_convection = None
        self._inner_radiation = None
        self._outer_convection = None
        self._outer_radiation = None

        self._layer = []

        self.r1 = 0.0
        self.r2 = 0.0
        self.r3 = 0.0
        self.c1 = 0.0
        self.c2 = 0.0
        self.c1_korr = 0.0
        self.ua_value = 0.0
        self.r_conduc = 0.0
        self.r_inner_conv = 0.0
        self.r_inner_rad = 0.0
        self.r_inner_comb = 0.0
        self.r_outer_conv = 0.0
        self.r_outer_rad = 0.0
        self.r_outer_comb = 0.0
        self.wf_out = 0.0

        self._view_factors = [0, 0, 0, 0]

    def calc_ua_value(self):
        """U*A value for building element.

        Calculates the U*A value and resistances for radiative and
        convective heat transfer of a building element.
        """

        self.ua_value = 0.0
        self.r_conduc = 0.0
        self.r_inner_conv = 0.0
        self.r_inner_rad = 0.0
        self.r_inner_comb = 0.0
        self.r_outer_conv = 0.0
        self.r_outer_rad = 0.0
        self.r_outer_comb = 0.0
        r_conduc = 0.0
        for count_layer in self.layer:
            r_conduc += (
                count_layer.thickness / count_layer.material.thermal_conduc) \

        self.r_conduc = r_conduc * (1 / self.area)
        self.r_inner_conv = (1 / self.inner_convection) * (1 / self.area)
        self.r_inner_rad = (1 / self.inner_radiation) * (1 / self.area)
        self.r_inner_comb = 1 / (1 / self.r_inner_conv + 1 / self.r_inner_rad)

        if self.outer_convection is not None \
                and self.outer_radiation is not None:

            self.r_outer_conv = (1 / self.outer_convection) * (1 / self.area)
            self.r_outer_rad = (1 / self.outer_radiation) * (1 / self.area)
            self.r_outer_comb = 1 / \
                (1 / self.r_outer_conv + 1 / self.r_outer_rad)

        self.ua_value = (1 / (
            self.r_inner_comb + self.r_conduc + self.r_outer_comb))
        self.u_value = self.ua_value / self.area

    def gather_element_properties(self):
        """Helper function for matrix calculation.

        Gathers all material properties of the building element and returns
        them as a np.array. Needed for the calculation of the matrix in
        equivalent_res(t_bt) especially for walls.

        Returns
        ----------
        number_of_layer : int
            number of layer (length of layer list)
        density : np.array
            Numpy array with length of number of layer, filled with density
            of each layer
        thermal_conduc : np.array
            Numpy array with length of number of layer, filled with
            thermal_conduc of each layer
        heat_capac : np.array
            Numpy array with length of number of layer, filled with heat_capac
            of each layer
        thickness : np.array
            Numpy array with length of number of layer, filled with thickness
            of each layer
        """

        number_of_layer = len(self.layer)
        density = np.zeros(number_of_layer)
        thermal_conduc = np.zeros(number_of_layer)
        heat_capac = np.zeros(number_of_layer)
        thickness = np.zeros(number_of_layer)

        range_tuple = (0, number_of_layer, 1)
        if self in self.parent.nz_borders:
            if (not self.parent.use_conditions.with_heating and
                    self.outside.use_conditions.with_heating):
                # if inner side of nz border is unheated and outer side is
                # heated, reverse layers for calculation (list of resistances
                # will be re-reversed later)
                range_tuple = (number_of_layer - 1, -1, -1)

        for i, l_i in enumerate(range(*range_tuple)):

            density[i] = self.layer[l_i].material.density
            thermal_conduc[i] = self.layer[l_i].material.thermal_conduc
            heat_capac[i] = self.layer[l_i].material.heat_capac
            thickness[i] = self.layer[l_i].thickness

        return number_of_layer, density, thermal_conduc, heat_capac, thickness

    def add_layer(self, layer, position=None):
        """Adds a layer at a certain position

        This function adds a Layer instance to the layer list at a given
        position

        Parameters
        ----------
        layer : instance of Layer
            Layer instance of TEASER
        position : int
            position in the wall starting from 0 (inner side)

        """
        ass_error_1 = "Layer has to be an instance of Layer()"

        assert isinstance(layer, Layer), ass_error_1

        if position is None:
            self._layer.append(layer)
        else:
            self._layer.insert(position, layer)

    def add_layer_list(self, layer_list):
        """Appends a layer set to the layer list

        The layer list has to be in correct order

        Parameters
        ----------
        layer_list : list
            list of sorted TEASER Layer instances
        """
        ass_error_1 = "Layer has to be an instance of Layer()"
        for lay_count in layer_list:

            assert isinstance(lay_count, Layer), ass_error_1

            self._layer.append(lay_count)

    def load_type_element(
            self,
            year,
            construction,
            data_class=None,
            element_type=None,
            reverse_layers=False,
            reset_basic_data=True,
            type_element_key=None
    ):
        """Typical element loader.

        Loads typical building elements according to their construction
        year and their construction type from a json.

        This function will only work if the parents to Building are set.

        Parameters
        ----------
        year : int
            Year of construction

        construction : str
            Construction type, code list ('heavy', 'light')

        data_class : DataClass()
            DataClass containing the bindings for TypeBuildingElement and
            Material (typically this is the data class stored in prj.data,
            but the user can individually change that. Default is
            self.parent.parent.parent.data (which is data_class in current
            project)

        element_type : str
            Element type to load - only to specify if the data_class entry for a
            different type than type(element) is to be loaded, e.g. InnerWall
            instead of OuterWall

        reverse_layers : bool
            defines if layer list should be reversed

        reset_basic_data : bool
            if True, inner_convection, outer_convection, inner_radiation, and
            outer_radiation are set to None in advance and must be set by
            buildingelement_input._set_basic_data() again afterwards

        type_element_key : str

        """

        if data_class is None:
            data_class = self.parent.parent.parent.data
        else:
            data_class = data_class

        self.layer = None
        if not reset_basic_data:
            self._inner_convection = None
            self._inner_radiation = None
            self._outer_convection = None
            self._outer_radiation = None

        if type_element_key:
            try:
                buildingelement_input.load_type_element_by_key(
                    element=self, key_str=type_element_key,
                    data_class=data_class, reverse_layers=reverse_layers
                )
            except KeyError:
                warnings.warn(
                    ('Type element ' + type_element_key + ' was not found. '
                     + 'Going back to default element for year and construction'
                     + '...')
                )
                type_element_key = None

        if not type_element_key:
            buildingelement_input.load_type_element(
                element=self, year=year, construction=construction,
                data_class=data_class, element_type=element_type,
                reverse_layers=reverse_layers
            )

    def save_type_element(self, data_class=None):
        """Typical element saver.

        Saves typical building elements according to their construction
        year and their construction type in the the json file for type building
        elements. If the Project parent is set, it automatically saves it to
        the file given in Project.data. Alternatively you can specify a path to
        a file of TypeBuildingElements. If this file does not exist,
        a new file is created.

        Parameters
        ----------

        data_class : DataClass()
            DataClass containing the bindings for TypeBuildingElement and
            Material (typically this is the data class stored in prj.data,
            but the user can individually change that. Default is
            self.parent.parent.parent.data (which is data_class in current
            project)

        """

        if data_class is None:
            data_class = self.parent.parent.parent.data
        else:
            data_class = data_class

        import teaser.data.output.buildingelement_output as \
            buildingelement_output

        buildingelement_output.save_type_element(element=self,
                                                 data_class=data_class)

    def delete_type_element(self, data_class=None):
        """Deletes typical element.

        Deletes typical building elements according to their construction
        year and their construction type in the the json file for type building
        elements. If the Project parent is set, it automatically saves it to
        the file given in Project.data. Alternatively you can specify a path to
        a file of TypeBuildingElements. If this file does not exist,
        a new file is created.

        Parameters
        ----------

        data_class : DataClass()
            DataClass containing the bindings for TypeBuildingElement and
            Material (typically this is the data class stored in prj.data,
            but the user can individually change that. Default is
            self.parent.parent.parent.data (which is data_class in current
            project)

        """

        if data_class is None:
            data_class = self.parent.parent.parent.data
        else:
            data_class = data_class

        import teaser.data.output.buildingelement_output as \
            buildingelement_output

        buildingelement_output.delete_type_element(element=self,
                                                   data_class=data_class)

    def use_layer_properties(self, layers, year=1960, data_class=None,
                             element_type=None):
        """use custom properties from layer specification

        Parameters
        ----------
        layers : list
            list of thickness - material pairs. thickness are floats. materials
            have attributes id, name, density, thermalConductivity,
            heatCapacity, solarAbsorptance, irEmissivity, transmittance which
            all may be None, but in the end density and thermal conductivity
            must be specified either by their own values or by material values
            loaded from data_class via id or name. All others are set to default
            values (heat capacity: 1 kJ/kgK, rest: default values in Material())

        year : int
            dummy value (?) because it is required to set basic values

        data_class : DataClass()
            DataClass containing the bindings for TypeBuildingElement and
            Material (typically this is the data class stored in prj.data,
            but the user can individually change that. Default is
            self.parent.parent.parent.data (which is data_class in current
            project)

        element_type : str
            Element type to load - only to specify if the data_class entry for a
            different type than type(element) is to be loaded, e.g. InnerWall
            instead of OuterWall


        Returns
        -------

        Raises
        ------
        KeyError
            if material is not sufficiently specified (density and/or thermal
            conductivity remain 0)

        """

        if data_class is None:
            data_class = self.parent.parent.parent.data
        else:
            data_class = data_class

        self.layer = None
        self._inner_convection = None
        self._inner_radiation = None
        self._outer_convection = None
        self._outer_radiation = None

        element_binding = data_class.element_bind

        if element_type is None:
            element_type = type(self).__name__

        for key, element_in in element_binding.items():
            if key != "version":
                if (
                        element_in["building_age_group"][0]
                        <= year
                        <= element_in["building_age_group"][1]
                        and key.startswith(element_type)
                ):
                    element_dict = dict(element_in)
                    element_dict["construction_type"] = "custom"
                    buildingelement_input._set_basic_data(element=self,
                                                          element_in=element_dict)
                    break

        # increasing id from inside to outside
        for id, (thickness, material_info) in enumerate(layers):
            layer = Layer(parent=self, id=id)
            layer.thickness = thickness
            material = Material(layer)
            # load default material values if available
            if material_info.id is not None:
                material_input.load_material_id(material, material_info.id,
                                                data_class)
            elif material_info.name is not None:
                material_input.load_material(material, material_info.name,
                                             data_class)
            # use single material properties of material_info
            if material_info.density is not None:
                material.density = material_info.density
            if material_info.thermalConductivity is not None:
                material.thermal_conduc = material_info.thermalConductivity
            if material_info.heatCapacity is not None:
                material.heat_capac = material_info.heatCapacity
            if material_info.solarAbsorptance is not None:
                material.solar_absorp = material_info.solarAbsorptance
            if material_info.irEmissivity is not None:
                material.ir_emissivity = material_info.irEmissivity
            if material_info.transmittance is not None:
                material.transmittance = material_info.transmittance
            if material_info.name is not None:
                material.name = material_info.name
            if material.density == 0 or material.thermal_conduc == 0:
                warnings.warn('Material not sufficiently specified.')
                raise KeyError
            if material.heat_capac == 0:
                material.heat_capac = 1.0
                warnings.warn('Material heat capacity not specified. '
                              '1.0 kJ/(kg*K) will be used.')


    def set_calc_default(self):
        """Sets all calculated values of the Building Element to zero
        """
        self.r1 = 0.0
        self.r2 = 0.0
        self.r3 = 0.0
        self.c1 = 0.0
        self.c2 = 0.0
        self.c1_korr = 0.0
        self.ua_value = 0.0
        self.r_conduc = 0.0
        self.r_inner_conv = 0.0
        self.r_inner_rad = 0.0
        self.r_inner_comb = 0.0
        self.r_outer_conv = 0.0
        self.r_outer_rad = 0.0
        self.r_outer_comb = 0.0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, str):

            if value:
                regex = re.compile('[^a-zA-z0-9]')
                self._name = regex.sub('', value)
                if self._name == "None":
                    self._name = "BuildinElement" + str(
                        random.randint(1, 500000))
        elif value is None:
            self._value = "BuildinElement" + str(random.randint(1, 500000))
        else:
            try:
                value = str(value)
                regex = re.compile('[^a-zA-z0-9]')
                self._name = regex.sub('', value)
            except ValueError:
                print("Can't convert name to string")

    @property
    def year_of_retrofit(self):
        return self._year_of_retrofit

    @year_of_retrofit.setter
    def year_of_retrofit(self, value):

        if isinstance(value, int):
            pass
        elif value is None:
            pass
        else:
            try:
                value = int(value)
            except:
                raise ValueError("Can't convert year of retrofit to float")

        if value is not None:
            if self.year_of_construction is not None:
                self._year_of_retrofit = value
            else:
                raise ValueError("Specify year of construction first")

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):

        self._orientation = value
        if type(self).__name__ == "OuterWall":
            if self.parent.parent is not None and self.area is not None:
                self.parent.parent.fill_outer_area_dict()
        elif type(self).__name__ == "Window":
            if self.parent.parent is not None and self.area is not None:
                self.parent.parent.fill_window_area_dict()

    @property
    def idx_orientation(self):
        return self._idx_orientation

    @idx_orientation.setter
    def idx_orientation(self, value):
        if int(value) == value:
            self._idx_orientation = int(value)
        else:
            self._orientation = None

    @property
    def layer(self):
        return self._layer

    @layer.setter
    def layer(self, value):

        if value is None:
            self._layer = []

        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def inner_convection(self):
        return self._inner_convection

    @inner_convection.setter
    def inner_convection(self, value):

        if isinstance(value, float):
            pass
        elif value is None:
            pass
        else:
            try:
                value = float(value)
            except:
                raise ValueError("Can't convert inner convection to float")

        if value is not None:
            self._inner_convection = value
        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def inner_radiation(self):
        return self._inner_radiation

    @inner_radiation.setter
    def inner_radiation(self, value):

        if isinstance(value, float):
            pass
        elif value is None:
            pass
        else:
            try:
                value = float(value)
            except:
                raise ValueError("Can't convert inner radiation to float")

        if value is not None:
            self._inner_radiation = value
        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def outer_convection(self):
        return self._outer_convection

    @outer_convection.setter
    def outer_convection(self, value):

        if isinstance(value, float):
            pass
        elif value is None:
            pass
        else:
            try:
                value = float(value)
            except:
                raise ValueError("Can't convert outer convection to float")

        if value is not None:
            self._outer_convection = value
        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def outer_radiation(self):
        return self._outer_radiation

    @outer_radiation.setter
    def outer_radiation(self, value):

        if isinstance(value, float):
            pass
        elif value is None:
            pass
        else:
            try:
                value = float(value)
            except:
                raise ValueError("Can't convert outer radiation to float")

        if value is not None:
            self._outer_radiation = value
        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, value):

        if isinstance(value, float):
            pass
        elif value is None:
            pass
        else:
            try:
                value = float(value)
            except:
                raise ValueError("Can't convert element area to float")

        if value is not None:
            self._area = value
        if type(self).__name__ == "OuterWall"\
                or type(self).__name__ == "Rooftop" \
                or type(self).__name__ == "GroundFloor":
            if self.parent.parent is not None and self.orientation is not None:
                self.parent.parent.fill_outer_area_dict()
        elif type(self).__name__ == "Window":
            if self.parent is not None and self.orientation is not None:
                self.parent.parent.fill_window_area_dict()
        if self.inner_convection is not None and\
                self.inner_radiation is not None and\
                self.area is not None:
            self.calc_ua_value()

    @property
    def tilt(self):
        return self._tilt

    @tilt.setter
    def tilt(self, value):

        if isinstance(value, float):
            self._tilt = value
        elif value is None:
            self._tilt = value
        else:
            try:
                value = float(value)
                self._tilt = value
            except:
                raise ValueError("Can't convert tilt to float")

    @property
    def view_factors(self):
        return self._view_factors

    @view_factors.setter
    def view_factors(self, value):
        try:
            value = list(value)
            view_factors = [0., 0., 0., 0.]
            for idx in range(4):
                view_factors[idx] += float(value[idx])
        except:
            raise ValueError("Can't convert view_factors to four-element list")
        if not (np.isclose(sum(view_factors), 1)
                or all([vf == 0 for vf in view_factors])) \
                or any([vf < 0 for vf in view_factors]):
            raise ValueError("view factors must be >= 0 and sum up to 1 or "
                             "be all 0")
        self._view_factors = view_factors

    @property
    def year_of_construction(self):
        if self._year_of_construction is None:
            return self.parent.parent.year_of_construction
        return self._year_of_construction

    @year_of_construction.setter
    def year_of_construction(self, value):

        if isinstance(value, float):
            self._year_of_construction = value
        elif value is None:
            self._year_of_construction = value
        else:
            try:
                value = int(value)
                self._year_of_construction = value
            except:
                raise ValueError("Can't convert year to int")

    @property
    def construction_type(self):
        return self._construction_type

    @construction_type.setter
    def construction_type(self, value):

        self._construction_type = value
