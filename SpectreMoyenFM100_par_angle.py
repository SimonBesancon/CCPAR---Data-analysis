# Programme pour tracer le spectre moyen du FM100 par angle d'orientation
# Auteur : Simon Bessançon (adapté par Vibe Code)
# Basé sur : TraitementDataSFPDD CDP + FM orientation.py

import csv
from io import StringIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# ======================
# CHEMINS DES FICHIERS
# ======================
chemin_dossier_data = r"C:\Travail\CCPAR\Données Tests SFPDD\20251203&04 - Acquisition SFPDD FM+CDP\20251204\20251204135903"

chemin_fichier_FM100 = f"{chemin_dossier_data}\\00FM 10020251204135903.csv"
chemin_fichier_SFPDD = f"{chemin_dossier_data}\\SFPDD_251204_1359.txt"
chemin_log_SFPDD = f"{chemin_dossier_data}\\Log20251204135903.txt"

# ======================
# CLASSE DONNEES INSTRUMENT
# ======================
class DonneesInstrument:
    def __init__(self, type_instrument, donnees):
        self.type_instrument = type_instrument
        self.donnees = donnees

    def afficher_infos(self):
        print(f"Type d'instrument : {self.type_instrument}")
        print(f"    Nombre de variables : {len(self.donnees)} ({', '.join(self.donnees.keys())})")

        longueurs = {k: len(v) for k, v in self.donnees.items()}
        print(f"    Nombre de données : {next(iter(longueurs.values()))}"
              if len(set(longueurs.values())) == 1
              else "\n".join(f"    {k} : {l} données" for k, l in longueurs.items()))

        print(f"    Début : {self.donnees['heure'][0]} ({self.donnees['timestamp'][0]} secondes)")
        print(f"    Fin : {self.donnees['heure'][-1]} ({self.donnees['timestamp'][-1]} secondes)")

# ======================
# FONCTIONS DE LECTURE
# ======================
def identifier_instrument_et_extraire_donnees(fichier_csv):
    """Lit un fichier CSV CDP/FM100 et extrait les données (bins, LWC, MVD, etc.)."""
    with open(fichier_csv, 'r') as fichier:
        lignes = fichier.readlines()

    # Trouver la ligne '****'
    index_separateur = None
    for i, ligne in enumerate(lignes):
        if ligne.strip() == '****':
            index_separateur = i
            break

    if index_separateur is None:
        raise ValueError("La ligne de séparation '****' n'a pas été trouvée.")

    entete = lignes[:index_separateur]

    # Identifier l'instrument
    type_instrument = None
    for ligne in entete:
        if 'Instrument Type' in ligne:
            if 'FM 100' in ligne:
                type_instrument = 'FM 100'
                break
            elif 'CDP' in ligne:
                type_instrument = 'CDP'
                break

    if type_instrument is None:
        raise ValueError("Aucun identifiant trouvé dans l'en-tête.")

    lignes_donnees = lignes[index_separateur+1:]
    data_file = StringIO(''.join(lignes_donnees))
    reader = csv.reader(data_file)

    en_tete_donnees = next(reader, None)
    if en_tete_donnees is None:
        raise ValueError("Aucune donnée trouvée après la ligne '****'.")

    # Trouver les indices des colonnes
    colonnes_a_extraire = [col for col in en_tete_donnees if 'CDP Bin' in col or 'FM Bin' in col]
    indices_colonnes_bins = []
    for col in colonnes_a_extraire:
        try:
            num = int(col.split()[-1])
            if 1 <= num <= 30:
                indices_colonnes_bins.append(en_tete_donnees.index(col))
        except (ValueError, IndexError):
            continue

    # Indices des autres colonnes
    index_Seconds = None
    index_date = None
    index_temps = None
    index_LWC = None
    index_MVD = None
    index_ED = None
    index_PAS = None
    index_concentration = None

    for i, col in enumerate(en_tete_donnees):
        if col.startswith('End Seconds'):
            index_Seconds = i
        elif col.startswith('Date'):
            index_date = i
        elif col.startswith('Time'):
            index_temps = i
        elif col.startswith('LWC (g/m^3)'):
            index_LWC = i
        elif col.startswith('MVD (um)'):
            index_MVD = i
        elif col.startswith('ED (um)'):
            index_ED = i
        elif col.startswith('Applied PAS (m/s)'):
            index_PAS = i
        elif col.startswith('Number Conc (#/cm^3)'):
            index_concentration = i

    if index_date is None or index_temps is None:
        raise ValueError("Les colonnes 'Date' ou 'Time' n'ont pas été trouvées.")

    # Extraire les données
    data_bins = []
    data_LWC = []
    data_MVD = []
    data_ED = []
    data_PAS = []
    data_concentration = []
    timestamp = []
    dates = []
    temps = []

    for ligne in reader:
        try:
            valeurs = [float(ligne[i]) if ligne[i] else 0.0 for i in indices_colonnes_bins]
            data_bins.append(valeurs)
            data_LWC.append(ligne[index_LWC])
            data_MVD.append(ligne[index_MVD])
            data_ED.append(ligne[index_ED])
            data_concentration.append(ligne[index_concentration])
            timestamp.append(ligne[index_Seconds])
            dates.append(ligne[index_date])
            temps.append(ligne[index_temps])
            data_PAS.append(ligne[index_PAS])
        except ValueError:
            continue

    donnees = {
        'timestamp': [float(ts) for ts in timestamp],
        'date': dates,
        'heure': temps,
        'bins': data_bins,
        'LWC': data_LWC,
        'MVD': data_MVD,
        'ED': data_ED,
        'PAS': data_PAS,
        'Concentration': data_concentration
    }

    return type_instrument, donnees

# ======================
# LECTURE LOG ORIENTATION
# ======================
def lecture_log_orientation_inletFM100(fichier_log_SFPDD):
    """Extrait les périodes d'orientation de l'inlet du FM100 depuis le fichier log."""
    data_orientation_inlet_formate = []
    current_orientation = None
    start_time = None

    with open(fichier_log_SFPDD, "r") as fichier:
        for line in fichier:
            if len(line.strip()) == 0:
                continue

            heure = line[0:8].strip()
            commentaire = line[19:].strip().lower()

            if "start" in commentaire:
                if "°" in commentaire:
                    orientation = commentaire.split("°")[0].split()[-1]
                else:
                    orientation = "0"
                current_orientation = orientation
                start_time = heure

            elif "stop" in commentaire and current_orientation is not None:
                data_orientation_inlet_formate.append({
                    "orientation": current_orientation,
                    "start_time": start_time,
                    "stop_time": heure
                })
                current_orientation = None
                start_time = None

    # Corrections manuelles (à adapter selon ton fichier log)
    data_orientation_inlet_formate[0]["start_time"] = "13:59:29"
    data_orientation_inlet_formate.insert(1, {"orientation": "30", "start_time": "14:33:35", "stop_time": "14:38:41"})
    data_orientation_inlet_formate.insert(2, {"orientation": "60", "start_time": "14:44:25", "stop_time": "14:48:42"})

    return data_orientation_inlet_formate

# ======================
# TABLE DES BINS FM100
# ======================
def table_bin_tailles_fm100():
    """
    Table des tailles de bins pour le FM100.
    Le FM100 et le CDP utilisent les mêmes bins (30 bins, 1.5µm à 49µm).
    Source : Datasheet Droplet Measurement Technologies.
    """
    tableau = [
        {"Bin": 1, "upper_bin_size": 3, "median_bin_size": 1.5, "uncertainty": 1.5},
        {"Bin": 2, "upper_bin_size": 4, "median_bin_size": 3.5, "uncertainty": 0.5},
        {"Bin": 3, "upper_bin_size": 5, "median_bin_size": 4.5, "uncertainty": 0.5},
        {"Bin": 4, "upper_bin_size": 6, "median_bin_size": 5.5, "uncertainty": 0.5},
        {"Bin": 5, "upper_bin_size": 7, "median_bin_size": 6.5, "uncertainty": 0.5},
        {"Bin": 6, "upper_bin_size": 8, "median_bin_size": 7.5, "uncertainty": 0.5},
        {"Bin": 7, "upper_bin_size": 9, "median_bin_size": 8.5, "uncertainty": 0.5},
        {"Bin": 8, "upper_bin_size": 10, "median_bin_size": 9.5, "uncertainty": 0.5},
        {"Bin": 9, "upper_bin_size": 11, "median_bin_size": 10.5, "uncertainty": 0.5},
        {"Bin": 10, "upper_bin_size": 12, "median_bin_size": 11.5, "uncertainty": 0.5},
        {"Bin": 11, "upper_bin_size": 13, "median_bin_size": 12.5, "uncertainty": 0.5},
        {"Bin": 12, "upper_bin_size": 14, "median_bin_size": 13.5, "uncertainty": 0.5},
        {"Bin": 13, "upper_bin_size": 16, "median_bin_size": 15.0, "uncertainty": 1.0},
        {"Bin": 14, "upper_bin_size": 18, "median_bin_size": 17.0, "uncertainty": 1.0},
        {"Bin": 15, "upper_bin_size": 20, "median_bin_size": 19.0, "uncertainty": 1.0},
        {"Bin": 16, "upper_bin_size": 22, "median_bin_size": 21.0, "uncertainty": 1.0},
        {"Bin": 17, "upper_bin_size": 24, "median_bin_size": 23.0, "uncertainty": 1.0},
        {"Bin": 18, "upper_bin_size": 26, "median_bin_size": 25.0, "uncertainty": 1.0},
        {"Bin": 19, "upper_bin_size": 28, "median_bin_size": 27.0, "uncertainty": 1.0},
        {"Bin": 20, "upper_bin_size": 30, "median_bin_size": 29.0, "uncertainty": 1.0},
        {"Bin": 21, "upper_bin_size": 32, "median_bin_size": 31.0, "uncertainty": 1.0},
        {"Bin": 22, "upper_bin_size": 34, "median_bin_size": 33.0, "uncertainty": 1.0},
        {"Bin": 23, "upper_bin_size": 36, "median_bin_size": 35.0, "uncertainty": 1.0},
        {"Bin": 24, "upper_bin_size": 38, "median_bin_size": 37.0, "uncertainty": 1.0},
        {"Bin": 25, "upper_bin_size": 40, "median_bin_size": 39.0, "uncertainty": 1.0},
        {"Bin": 26, "upper_bin_size": 42, "median_bin_size": 41.0, "uncertainty": 1.0},
        {"Bin": 27, "upper_bin_size": 44, "median_bin_size": 43.0, "uncertainty": 1.0},
        {"Bin": 28, "upper_bin_size": 46, "median_bin_size": 45.0, "uncertainty": 1.0},
        {"Bin": 29, "upper_bin_size": 48, "median_bin_size": 47.0, "uncertainty": 1.0},
        {"Bin": 30, "upper_bin_size": 50, "median_bin_size": 49.0, "uncertainty": 1.0}
    ]
    return tableau

# ======================
# CALCUL DU SPECTRE MOYEN
# ======================
def calculer_spectre_moyen_par_angle(data_orientation, FM100):
    """
    Calcule le spectre moyen (comptages par bin) pour chaque angle d'orientation du FM100.
    Retourne un dictionnaire : {angle: [moyenne_bin1, moyenne_bin2, ...]}
    """
    spectres = {}

    for entry in data_orientation:
        orientation = entry["orientation"]
        start_time = datetime.strptime(entry["start_time"], "%H:%M:%S")
        stop_time = datetime.strptime(entry["stop_time"], "%H:%M:%S")

        # Filtrer les indices FM100 dans cette période
        indices = []
        for i, (ts_str, heure_str) in enumerate(zip(FM100.donnees['timestamp'], FM100.donnees['heure'])):
            try:
                ts = datetime.strptime(heure_str, "%H:%M:%S.%f")
                if start_time <= ts <= stop_time:
                    indices.append(i)
            except ValueError:
                continue

        # Calculer la moyenne des bins pour ces indices
        if indices:
            bins = np.array([FM100.donnees['bins'][i] for i in indices])
            spectre_moyen = np.mean(bins, axis=0)  # Moyenne par bin
            spectres[orientation] = spectre_moyen
        else:
            print(f"Aucune donnée FM100 trouvée pour l'angle {orientation}°")
            spectres[orientation] = np.zeros(len(FM100.donnees['bins'][0]))

    return spectres

# ======================
# TRACÉ DU SPECTRE MOYEN
# ======================
def tracer_spectre_moyen_par_angle(spectres, bin_sizes, normaliser=False):
    """
    Trace le spectre moyen pour chaque angle du FM100.
    :param spectres: Dictionnaire {angle: [moyenne_bin1, moyenne_bin2, ...]}
    :param bin_sizes: Liste des tailles médianes des bins (µm)
    :param normaliser: Si True, normalise chaque spectre par son maximum (pour comparer les formes)
    """
    plt.figure(figsize=(12, 8))

    # Préparer les couleurs
    colors = plt.cm.tab10.colors  # 10 couleurs distinctes
    angles = sorted(spectres.keys(), key=int)  # Trier par angle numérique

    for i, angle in enumerate(angles):
        spectre = spectres[angle]
        if normaliser:
            spectre = spectre / np.max(spectre)  # Normalisation par le max

        label = f"{angle}°"
        if normaliser:
            label += " (normalisé)"
        plt.plot(
            bin_sizes,
            spectre,
            label=label,
            color=colors[i % len(colors)],
            marker='o',
            linestyle='-',
            linewidth=2
        )

    plt.xlabel("Taille des gouttes (µm)", fontsize=12)
    plt.ylabel("Nombre de comptages (moyenne par bin)" + (" (normalisé)" if normaliser else "", fontsize=12))
    plt.title("Spectre moyen du FM100 par angle d'orientation", fontsize=14)
    plt.legend(title="Angle d'orientation", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max(bin_sizes) + 1)  # Limite X à la taille max des bins
    plt.ylim(0, None)  # Axe Y commence à 0

    # Échelle logarithmique optionnelle (décommenter si besoin)
    # plt.yscale("log")
    # plt.ylabel("Nombre de comptages (log, moyenne par bin)")

    plt.tight_layout()
    plt.show()

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    print("\n=== Chargement des données ===")

    # Charger les données FM100
    FM100 = DonneesInstrument(*identifier_instrument_et_extraire_donnees(chemin_fichier_FM100))
    FM100.afficher_infos()

    # Charger les orientations
    data_orientation = lecture_log_orientation_inletFM100(chemin_log_SFPDD)
    print(f"\nPériodes d'orientation détectées : {len(data_orientation)}")
    for entry in data_orientation:
        print(f"  {entry['start_time']} - {entry['stop_time']} : {entry['orientation']}°")

    # Calculer les spectres moyens
    print("\n=== Calcul des spectres moyens ===")
    spectres = calculer_spectre_moyen_par_angle(data_orientation, FM100)

    # Obtenir les tailles des bins
    bin_info = table_bin_tailles_fm100()
    bin_sizes = [bin["median_bin_size"] for bin in bin_info]  # Tailles médianes en µm

    # Tracer les spectres
    print("\n=== Traçage des spectres ===")
    tracer_spectre_moyen_par_angle(spectres, bin_sizes, normaliser=False)

    # Option : tracer aussi en normalisé (pour comparer les formes)
    tracer_spectre_moyen_par_angle(spectres, bin_sizes, normaliser=True)
