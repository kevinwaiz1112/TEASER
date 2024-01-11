# Importing all relevant packages
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
import math
import json
import csv
import os
import pickle
from btom.export.toTeaser import createTeaserProject
# Imports from ebcpy
from ebcpy import DymolaAPI, TimeSeriesData
from ebcpy.utils.conversion import convert_tsd_to_modelica_txt

import teaser.examples.e1_generate_archetype as e1

def main():


    ############################# Import from BTOM ##############################

    prj = e1.example_generate_archetype()

    """""
    pickleDir = 'C:\\03_Repos\sekquasens_interfaces\\Moabit-Datensatz BS2021\\'
    stepPerformed = 'teaserPrepared'
    evalId = 'aerialIrEval_20200819_1849'
    quarter = pickle.load(open(os.path.join(pickleDir,
                                            evalId + '_' + stepPerformed + '.p'),
                               'rb'))
    
    prj=createTeaserProject(quarter,
                            morschenichRealAIntRInt = 0,
                            innerWallCalcApproach ='teaser_default',
                            innerWallFactor = 0.1,
                            ensureSingleSurfaceViewFactors = True
)
    """


    ############################# Method to assign attendance profiles ##############################

    for bldg in prj.buildings:

        original_id = bldg.name


        # Die ID in das gewünschte Format umwandeln
        formatted_id = '-'.join(
            [original_id[0:11], original_id[11:15], original_id[15:19], original_id[19:23], original_id[23:35]])

        # Listen zum Speichern der extrahierten Werte aus "perc"
        perc_values = []

        # CSV-Datei öffnen und die Werte aus der "perc"-Spalte für die Ziel-Gebäude-ID speichern
        csv_file_path = r"C:\03_Repos\sekquasens_interfaces\Data\presence_times_calc_corrected.csv"
        with (open(csv_file_path, 'r') as csvfile):
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                if row['id'] == formatted_id:
                    perc_value = float(row['perc']) / 100.0  # Wert durch 100 teilen und in Float umwandeln
                    rounded_perc_value = round(perc_value, 2)  # Auf 2 Nachkommastellen runden
                    perc_values.append(rounded_perc_value)

        print(perc_values)

        for zone in bldg.thermal_zones:
            zone.use_conditions.persons_profile = perc_values




    ############################# Export ##############################

    """""
    prj.used_library_calc = 'AixLib'
    prj.number_of_elements_calc = 2
    prj.weather_file_path = utilities.get_full_path(
            os.path.join(
                "data",
                "input",
                "inputdata",
                "weatherdata",
                "DEU_BW_Mannheim_107290_TRY2010_12_Jahr_BBSR.mos"))
    """

    prj.calc_all_buildings()

    path = prj.export_aixlib(
        internal_id=None,
        path=r"C:\03_Repos\Teasermodelle")

if __name__ == '__main__':

    main()

    print("Example 10: That's it! :)")
