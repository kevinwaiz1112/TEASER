# Importing all relevant packages
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
import math
import json
import h5py
import time
import csv
# Imports from ebcpy
from ebcpy import DymolaAPI, TimeSeriesData
from ebcpy.utils.conversion import convert_tsd_to_modelica_txt


# ToDO
#  Wetterdaten Prognose einbinden für den Fall, dass nur 7 Tage simuliert werden.
#  T_Soil muss an T_Air angepasst werden
#  Alle relevanten Ergebnisse zusammenstellen in Results


def main(
        file_dir="C:\03_Repos\SimData",

        # Path to all packages used for this task
        Teaser_mo="C:\03_Repos\Teasermodelle\Project\package.mo",
        AixLib_mo="C:\03_Repos\AixLib\AixLib\package.mo",

        # Storage path (below)
        cd=None,
        with_plot=True
):
    start_time = time.time()
    # General settings, saves the results
    if cd is None:
        cd = pathlib.Path(file_dir).joinpath("Results")
    # For another storage location, enter the path below (for "cd") and also change the following lines
    else:
        cd = pathlib.Path(cd)
    file_dir = pathlib.Path(file_dir)

    ############################# Extract IDs from csv ##############################

    csv_file_path = r"C:\03_Repos\sekquasens_interfaces\Data\presence_times_calc_corrected.csv"
    building_names = set()

    with open(csv_file_path, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        next(csvreader)  # Überspringe die Header-Zeile
        for row in csvreader:
            id = row['id']
            building_names.add(id)

    # building_names.remove('')

    # Überprüfen, ob jede ID nur einmal vorkommt
    unique_building_names = []
    for name in building_names:
        if name not in unique_building_names:
            unique_building_names.append(name)


    for csv_id in unique_building_names:

        # IDs in die gewünschte Schreibweise ändern
        formatted_id = csv_id.replace('-', '')

        ############################# Simulation setup ##############################


        dym_api = DymolaAPI(
            model_name="Project."+str(formatted_id)+"."+str(formatted_id),
            cd=cd,
            packages=[
                AixLib_mo,
                Teaser_mo
            ],
            show_window=False,
            equidistant_output=False
        )

        dym_api.set_sim_setup({
            "start_time": 0,
            "stop_time": 86400 * 365,  # in sec
            "output_interval": 60 * 60
        })



        ############################## Setup the simulation inputs ##############################
        combi_time_table_path = r"C:/03_Repos/Teasermodelle/Project/"+str(formatted_id)+r"/InternalGains_"+str(formatted_id)+r".txt"
        table_name = "Internals"

        time_index = np.arange(
            dym_api.sim_setup.start_time,
            dym_api.sim_setup.stop_time,
            dym_api.sim_setup.output_interval
        )

        ############################## Presence Data ##############################

        """""
        Loading the Data into the TimeTables (indirect method):
    
        In order to use the generated data for the simulation model, 
        it is necessary that you overwrite the .txt files used in these tables. 
        It is not possible to directly change the timeTable input through Python. 
        Therefore the data obtained through a .csv needs to be read and aggregated for each building 
        in a seperated python numpy list (see example below). 
        After that the lists will be used to overwrite the data in the .txt file, 
        followed by the simulation of the model itself.
    
        1. Read .csv and extract the profiles for the prospected building into a list
        2. Overwrite .txt data that is used in the model by the code below
        3. Start the simulation and save the necessary data into a .csv data
    
        """

        # Erzeuge Daten mit Spalten aus Einsen (1.0)
        data = np.ones((len(time_index), 3))  # 3 Spalten mit jeweils Einsen als Platzhalter
        #data[:, 1] *= 0.5

        # Listen zum Speichern der extrahierten Werte aus "perc"
        # Input: Die Anzahl der Personen wirkt sich auf auf Größen der Record aus:
        # specificPeople = 0.02, Anzahl der Personen pro m^2
        perc_values = []
        specificPeople = []

        # CSV-Datei öffnen und die Werte aus der "perc"-Spalte für die Ziel-Gebäude-ID speichern
        with (open(csv_file_path, 'r') as csvfile):
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                if row['id'] == csv_id:
                    perc_value = float(row['perc']) / 100.0  # Wert durch 100 teilen und in Float umwandeln
                    rounded_perc_value = round(perc_value, 2)  # Auf 2 Nachkommastellen runden
                    perc_values.append(rounded_perc_value)

        # specificPeople_per_m2=specificPeople[0]
        # print(specificPeople_per_m2)

        machines_profile = [
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
            0.5, 1.0, 0.5, 0.5, 0.5, 1.0,
            1.0, 0.5, 0.5, 0.5, 1.0, 1.0,
            1.0, 1.0, 0.5, 0.5, 0.5, 0.1
        ]
        lighting_profile = [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ]

        # Schreibe die "perc"-Werte in die zweite Spalte von data
        replicated_perc_values = np.tile(perc_values, 365)
        replicated_machine_values = np.tile(machines_profile, 365)
        replicated_lighting_values = np.tile(lighting_profile, 365)

        data[:, 0] = replicated_perc_values
        data[:, 1] = replicated_machine_values
        data[:, 2] = replicated_lighting_values

        # Erzeuge die TimeSeriesData mit den Einsen-Spalten
        tsd_input = TimeSeriesData(data, columns=[ "InternalGains1", "InternalGains2", "InternalGains3"],
                                   index=time_index)

        # To generate the input in the correct format, use the convert_tsd_to_modelica_txt function:
        filepath = convert_tsd_to_modelica_txt(
            tsd=tsd_input,
            table_name=table_name,
            save_path_file=combi_time_table_path
        )

        ############################# Inputs ##############################

        New_values = {

           # 'T_Soil': V_Air,

        }

        ############################# Start the simulation ##############################

        result = dym_api.simulate(
            # parameters=New_values,
            inputs=tsd_input,
            table_name=table_name,
            file_name=combi_time_table_path,
            return_option="savepath"
        )

        ############################# Calculating additional parameters and results ##############################

        tsd = TimeSeriesData(result)

        selected_parameters = [
            'weaDat.weaBus.TDryBul',
            'weaDat.weaBus.relHum',
            'weaDat.weaBus.HDirNor',
            'weaDat.weaBus.HDifHor',
            'weaDat.weaBus.HGloHor',
            'weaDat.weaBus.pAtm',
            'weaDat.weaBus.lon',
            'weaDat.weaBus.lat',
            'weaDat.weaBus.alt',
            'multizone.TSetHeat[1]',
            'multizone.TAir[1]',
            'multizone.zoneParam[1].TSoil',
            'multizone.PHeater[1]',
            'multizone.zone[1].zoneParam.VAir',
            'multizone.zone[1].zoneParam.AZone',
            ]

        dym_api.close()

        ############################# Saving results into csv/json data ##############################

        # Selected parameters
        selected_parameters_df = tsd[selected_parameters]
        selected_parameters_df.to_csv(pathlib.Path(file_dir).joinpath("Export", str(formatted_id) + '_Filtered_Results.csv'))

        # Annual values
        heat_provided = tsd['multizone.PHeater[1]']
        annual_heat_demand = heat_provided.sum()
        print("Annual heat demand:", annual_heat_demand)
        gesamt_waermemenge_df = pd.DataFrame({"Annual heat demand [Wh]": [annual_heat_demand]})
        gesamt_waermemenge_df.to_csv(pathlib.Path(file_dir).joinpath("Export", str(formatted_id) + '_Overall.csv'), index=False)

        # All data
        # tsd.save(file_dir.joinpath("Export", str(formatted_id) + '_All_Results.hdf'), key="Moabit")
        df = pd.DataFrame(tsd)
        df.to_csv(pathlib.Path(file_dir).joinpath("Export", str(formatted_id)+'_All_Results.csv'))

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Die Simulation hat {execution_time} Sekunden gedauert.")


if __name__ == '__main__':
    main(

        file_dir=r"C:\03_Repos\SimData",

        # Path to all packages used for this task
        Teaser_mo=r"C:\03_Repos\Teasermodelle\Project\package.mo",
        AixLib_mo=r"C:\03_Repos\AixLib\AixLib\package.mo",
    )
