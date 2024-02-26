import os
import json
import csv

# Pfad zur neuen JSON-Datei
json_datei_pfad = r'C:\03_Repos\SimData\Results\All_Buildings_Overall.json'

# Pfad zur JSON-Datei mit den Standardwerten
standard_json_datei_pfad = r'C:\03_Repos\sekquasens_interfaces\Data\Moabit-Datensatz BS2021\moabit_yearly_demand_20210120_1310.json'

# Liste für die Ergebnisse erstellen
ergebnisse = []

# Standard-JSON-Datei laden
with open(standard_json_datei_pfad, 'r') as json_file:
    standard_json_data = json.load(json_file)

# Neue JSON-Datei laden
with open(json_datei_pfad, 'r') as json_file:
    neue_json_data = json.load(json_file)

# Durch die neuen JSON-Daten gehen
for id_gebaeude, gebaeude_daten in neue_json_data.items():
    # ID korrigieren (entfernen der ersten und letzten Klammern)
    gebaeude_id_ohne_bindestriche = id_gebaeude.replace("-", "")  # Diese Zeile ist notwendig, wenn die IDs in der JSON-Datei in Klammern stehen.

    # Den entsprechenden Eintrag in der Standard-JSON-Datei finden
    json_entry = standard_json_data['buildings'].get(gebaeude_id_ohne_bindestriche, {})
    demand_std = json_entry.get('demand_std_GWh/y', None)
    if demand_std is not None:
        demand_std = demand_std * 1000  # Umrechnung GWh in kWh

        # Wert für 'heat_demand' aus der neuen JSON-Datei
        innere_daten = gebaeude_daten.get(id_gebaeude, {})
        wert = innere_daten.get('heat_demand [kWh]', 0)/1000

        # Prozentuale Änderung berechnen
        perc = ((wert - demand_std) / demand_std) * 100 if demand_std != 0 else 0

        # Ergebnisse zur Liste hinzufügen
        ergebnisse.append((id_gebaeude, wert, demand_std, perc))

ergebnisse.sort(key=lambda x: x[0])
# Ergebnisse in CSV-Datei speichern
csv_datei_pfad = r'C:\03_Repos\sekquasens_interfaces\TEASER\teaser\examples\ergebnisse_neu.csv'
try:
    with open(csv_datei_pfad, 'w', newline='') as csv_datei:
        csv_writer = csv.writer(csv_datei)
        # Header schreiben
        csv_writer.writerow(['ID', 'Wert', 'demand_std_MWh/y', 'Aenderung'])
        # Ergebnisse schreiben
        csv_writer.writerows(ergebnisse)
    print(f"Ergebnisse wurden erfolgreich in {csv_datei_pfad} gespeichert.")
except Exception as e:
    print(f"Fehler beim Schreiben der CSV-Datei {csv_datei_pfad}: {e}")



