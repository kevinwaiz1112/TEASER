# Importing all relevant packages
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
import math
import json
import csv
# Imports from ebcpy
from ebcpy import DymolaAPI, TimeSeriesData
from ebcpy.utils.conversion import convert_tsd_to_modelica_txt


def main(
        file_dir="C:\03_Repos\SimData",

        # Path to all packages used for this task
        Teaser_mo="C:\03_Repos\Teasermodelle\Project\package.mo",
        AixLib_mo="C:\03_Repos\AixLib\AixLib\package.mo",

        # Storage path (below)
        cd=None,
        with_plot=True
):
    # General settings, saves the results
    if cd is None:
        cd = pathlib.Path(file_dir).joinpath("Results")
    # For another storage location, enter the path below (for "cd") and also change the following lines
    else:
        cd = pathlib.Path(cd)
    file_dir = pathlib.Path(file_dir)



    dym_api = DymolaAPI(
        model_name="Project.ID_00BD9DFFD3F84FC4A4E3A3251FF201D1.ID_00BD9DFFD3F84FC4A4E3A3251FF201D1",
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
        "stop_time": 86400*365,  # in sec
        "output_interval": 60 * 60
    })

    ############################## Setup the simulation inputs ##############################

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

    ############################# Start the simulation ##############################

    result = dym_api.simulate(
        # parameters=New_values,
        # structural_parameters=[
        #         ("ArchetypeExample.ResidentialBuildingTabula.ResidentialBuildingTabula.tableInternalGains.fileName", f'"{combi_time_table_path}"'),
        #         ("ArchetypeExample.ResidentialBuildingTabula.ResidentialBuildingTabula.tableInternalGains.tableName", f'"{table_name}"'),
        #         ],
        # result_file=r"C:Repos/SekQuaSens_Interfaces/Results/Test.csv",  # Hier den Pfad zur CSV-Datei anpassen
        # inputs=tsd_input,
        # table_name=table_name,
        # file_name=combi_time_table_path,
        return_option="savepath"
    )

    ############################# Calculating additional parameters ##############################

    tsd = TimeSeriesData(result)

    ############################# Saving results into csv data ##############################

    df = pd.DataFrame(tsd)


if __name__ == '__main__':
    main(

        file_dir=r"C:\03_Repos\SimData",

        # Path to all packages used for this task
        Teaser_mo=r"C:\03_Repos\Teasermodelle\Project\package.mo",
        AixLib_mo=r"C:\03_Repos\AixLib\AixLib\package.mo",
    )
