import os
import csv
import json

# Pfad zum Ordner mit den CSV-Dateien
ordner_pfad = r'C:\03_Repos\SimData\Export'

# Pfad zur JSON-Datei
json_datei_pfad = r'C:\03_Repos\sekquasens_interfaces\Data\Moabit-Datensatz BS2021\moabit_yearly_demand_20210120_1310.json'

# Liste für die Ergebnisse erstellen
ergebnisse = []

# JSON-Datei laden
with open(json_datei_pfad, 'r') as json_file:
    json_data = json.load(json_file)

# Alle Dateien im Ordner durchgehen
for datei_name in os.listdir(ordner_pfad):
    # Überprüfen, ob die Datei die gewünschte Form hat
    if datei_name.endswith("_Overall.csv") and datei_name.startswith("ID_"):
        # Extrahiere die ID aus dem Dateinamen
        id_gebaeude = datei_name.split("_")[1]

        # Den vollständigen Pfad zur CSV-Datei erstellen
        datei_pfad = os.path.join(ordner_pfad, datei_name)

        # CSV-Datei lesen
        try:
            with open(datei_pfad, 'r') as file:
                # Alle Zeilen in der Datei durchgehen
                for line in file:
                    # Wenn die Zeile "raw" enthält, den Wert extrahieren
                    if "raw" in line:
                        # Der Wert befindet sich wahrscheinlich nach dem letzten Leerzeichen in der Zeile
                        wert = float(line.split()[-1])

                        # Den entsprechenden Eintrag in der JSON-Datei finden
                        json_entry = json_data['buildings'].get("ID_" + id_gebaeude, {})
                        demand_std = json_entry.get('demand_std_GWh/y', None) * 1000000000
                        perc = ((wert-demand_std)/demand_std)*100

                        # Ergebnisse zur Liste hinzufügen
                        ergebnisse.append((id_gebaeude, wert, demand_std, perc))
                        break

        except Exception as e:
            print(f"Fehler beim Lesen der Datei {datei_pfad}: {e}")

# Ergebnisse in CSV-Datei speichern
csv_datei_pfad = r'C:\03_Repos\sekquasens_interfaces\TEASER\teaser\examples\ergebnisse.csv'
try:
    with open(csv_datei_pfad, 'w', newline='') as csv_datei:
        csv_writer = csv.writer(csv_datei)
        # Header schreiben
        csv_writer.writerow(['ID', 'Wert', 'demand_std_GWh/y', 'Aenderung'])
        # Ergebnisse schreiben
        csv_writer.writerows(ergebnisse)
    print(f"Ergebnisse wurden erfolgreich in {csv_datei_pfad} gespeichert.")
except Exception as e:
    print(f"Fehler beim Schreiben der CSV-Datei {csv_datei_pfad}: {e}")
