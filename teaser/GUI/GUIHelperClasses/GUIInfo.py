# created June 2015
# by TEASER4 Development Team



class GUIInfo():
    '''
    Storage for a list of values for the GUI
    '''

    def __init__(self):
        '''
        Constructor
        '''

        # Base-Values for the Main Tab and subwindows
        self.hoursInADay = ["00:00", "01:00", "02:00", "03:00", "04:00",
                            "05:00", "06:00", "07:00", "08:00", "09:00",
                            "10:00", "11:00", "12:00", "13:00", "14:00",
                            "15:00", "16:00", "17:00", "18:00", "19:00",
                            "20:00", "21:00", "22:00", "23:00", "24:00", ]
        self.orientations = ["North", "North-East", "East", "South-East",
                             "South", "South-West", "West", "North-West",
                             "Roof", "Floor"]
        self.orientations_numbers = {0: "North", 45: "North-East",
                                     90: "East", 135: "South-East",
                                     180: "South", 225: "South-West",
                                     270: "West", 315: "North-West",
                                     - 1: "Roof", -2: "Floor"}
        self.type_buildings = ["Office", "Institute 4",
                               "Institute 8", "Institute General",
                               "Residential"]
        self.thermal_zone_types = ["Cellular office",
                                   "Group Office (between 2 and 6 employees)",
                                   "Open-plan Office (7 or more employees)",
                                   "Meeting, Conference, seminar",
                                   "Main Hall, Reception",
                                   "Retail, department store",
                                   "Retail with cooling",
                                   "Class room (school), group room \
                                   (kindergarden)", "Lecture hall, auditorium",
                                   "Bed room", "Hotel room",
                                   "Canteen", "Restaurant",
                                   "Kitchen in non-residential buildings",
                                   "Kitchen - preparations, storage",
                                   "WC and sanitary rooms in non-residential\
                                    buildings", "Further common rooms",
                                   "Auxiliary areas (without common rooms)",
                                   "Circulation area",
                                   "Stock, technical equipment, archives",
                                   "Computing center",
                                   "Commercial and industrial Halls - \
                                    heavy work, standing activity",
                                   "Commercial and industrial Halls - \
                                   medium work, standing activity",
                                   "Commercial and industrial Halls - \
                                   light work, standing activity",
                                   "Spectator area (theater and event venues)",
                                   "Foyer (theater and event venues)",
                                   "Stage (theater and event venues)",
                                   "Exhibition, congress",
                                   "Exhibition room and museum conservational\
                                    demands",
                                   "Library - reading room",
                                   "Library - open stacks",
                                   "Library - magazine and depot",
                                   "Gym (without spectator area",
                                   "Parking garages (office and private \
                                   usage)", "Parking garages (public usage)",
                                   "Sauna area", "Exercise room", "laboratory",
                                   "Examination- or treatment room",
                                   "Special maintenance aera",
                                   "Corridors in the general maintenance area",
                                   "Doctor's office, therapeutic offices",
                                   "Storehouse, logistics building",
                                   "Housing area"]

        # Base-Values for the simulation tab
        self.runtimeSimulation = "31536000"
        self.intervalOutput = "3600"
        self.solver = ["Lsodar", "dassl"]
        self.dymolaProject = "Campus.Juelich.Simulations.September3"
        self.building_model = ["AixLib.Building.LowOrder.ThermalZone",
                               "Cities.BuildingPhysics.ThermalZone",
                               "Cities.TypeBuilding",
                               "Cities.TypeBuildingRWin",
                               "Cities.HouseMultizone-Platzhalter"]
        self.ventilation_model = ["Heating", "Heating and Cooling",
                                  "Heating, Cooling and Humidification",
                                  "Heating, Cooling and HRS",
                                  "Heating, Cooling, Humidification and HRS",
                                  "Full AHU System"]
        self.avgTempOuter = "-12"
        self.innerTemp = "20"
        self.airchange_rate = ["airtight", "not as tight",
                                           "really little tight"]
        self.ahuFile = "./Tables/Melaten/AHU_Institut 4.mat"
        self.internalGainsFile = \
            "./Tables/Melaten/InternalGains_Institut 4.mat"
        self.tsetFile = "./Tables/Melaten/Tset_Institut 4.mat"
