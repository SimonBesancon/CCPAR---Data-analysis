import csv
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

#main

chemin_dossier_data = r"C:\Travail\CCPAR\Données Tests SFPDD\20251009 - Test CDP SAFIRE CDP LaMP CDA AQT"

chemin_fichier_CDP = f"{chemin_dossier_data}\\01CDP20251203095622.csv"
chemin_fichier_FM100 = f"{chemin_dossier_data}\\00FM 10020251203095622.csv"
chemin_fichier_SFPDD = f"{chemin_dossier_data}\\SFPDD_251203_0946.txt"

class DonneesInstrument:
    """
    Classe pour stocker les données extraites d'un instrument.
    """

    def __init__(self, type_instrument, donnees, dates, temps):
        """
        Initialise les attributs de la classe.

        :param type_instrument: Type de l'instrument (ex: "FM100", "CDP", etc.)
        :param donnees: Données extraites (ex: liste ou tableau de valeurs)
        :param dates: Liste des dates associées aux données
        :param temps: Liste des temps ou timestamps associées aux données
        """
        self.type_instrument = type_instrument
        self.donnees = donnees
        self.dates = dates
        self.temps = temps

    def afficher_infos(self):
        """Affiche un résumé des données."""
        print(f"Type d'instrument : {self.type_instrument}")
        print(f"    Nombre de variables : {len(self.donnees)} ({', '.join(self.donnees.keys())})")

        longueurs = {k: len(v) for k, v in self.donnees.items()}
        print(f"    Nombre de données : {next(iter(longueurs.values()))}" 
        if len(set(longueurs.values())) == 1
        else "\n".join(f"    {k} : {l} données" for k, l in longueurs.items()))

        print(f"    Début : {self.dates[0]} {self.temps[0]}")
        print(f"    Fin : {self.dates[-1]} {self.temps[-1]}")

    # Tu peux ajouter d'autres méthodes utiles ici, par exemple :
    def get_donnee_par_index(self, index):
        """Retourne la donnée, la date et le temps pour un index donné."""
        if 0 <= index < len(self.donnees):
            return {
                "donnee": self.donnees[index],
                "date": self.dates[index],
                "temps": self.temps[index]
            }
        else:
            return None

def identifier_instrument_et_extraire_donnees(fichier_csv):
    with open(fichier_csv, 'r') as fichier:
        lignes = fichier.readlines()

    # Trouver l'index de la ligne '****'
    index_separateur = None
    for i, ligne in enumerate(lignes):
        if ligne.strip() == '****':
            index_separateur = i
            break

    if index_separateur is None:
        raise ValueError("La ligne de séparation '****' n'a pas été trouvée.")

    # L'en-tête est avant la ligne '****'
    entete = lignes[:index_separateur]

    # Recherche de 'CDP', 'CDP PBP' ou 'FM 100' dans l'en-tête
    type_instrument = None
    for ligne in entete:
        if 'Instrument Type' in ligne:
            if 'CDP PBP' in ligne:
                type_instrument = 'CDP PBP'
                break
            elif 'CDP' in ligne:
                type_instrument = 'CDP'
                break
            elif 'FM 100' in ligne:
                type_instrument = 'FM 100'
                break

    if type_instrument is None:
        raise ValueError("Aucun identifiant trouvé dans l'en-tête.")

    # Les données sont après la ligne '****'
    lignes_donnees = lignes[index_separateur+1:]

    # On relit uniquement les lignes de données avec csv.reader
    data_file = StringIO(''.join(lignes_donnees))
    reader = csv.reader(data_file)

    # Lire la première ligne pour identifier les colonnes
    en_tete_donnees = next(reader, None)
    if en_tete_donnees is None:
        raise ValueError("Aucune donnée trouvée après la ligne '****'.")

    # Trouver les indices des colonnes 'CDP Bin 1' à 'CDP Bin 30'
    colonnes_a_extraire = [col for col in en_tete_donnees if 'CDP Bin' in col]
    indices_colonnes_bins = []
    for col in colonnes_a_extraire:
        try:
            num = int(col.split()[-1])
            if 1 <= num <= 30:
                indices_colonnes_bins.append(en_tete_donnees.index(col))
        except (ValueError, IndexError):
            continue

    # Trouver les indices des colonnes 'Date' et 'Time'
    index_date = None
    index_temps = None
    index_LWC = None
    index_MVD = None
    index_ED = None
    index_PAS = None
    index_concentration = None
    		
    for i, col in enumerate(en_tete_donnees):
        if col.startswith('Date'):
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
            print(f"Index concentration trouvé : {index_concentration}")

    if index_date is None or index_temps is None:
        raise ValueError("Les colonnes 'Date' ou 'Time' n'ont pas été trouvées.")

    # Extraire les données des colonnes sélectionnées
    data_bins = []
    data_LWC = []
    data_MVD = []
    data_ED = []
    data_PAS = []
    data_concentration = []

    dates = []
    temps = []
    
    for ligne in reader:
        try:
            # Extraire les données des colonnes 'CDP Bin'
            valeurs = [float(ligne[i]) if ligne[i] else 0.0 for i in indices_colonnes_bins]
            data_bins.append(valeurs)
            # Extraire LWC, MVD, ED, concentration
            data_LWC.append(ligne[index_LWC])
            data_MVD.append(ligne[index_MVD])
            data_ED.append(ligne[index_ED])
            data_concentration.append(ligne[index_concentration])
            # Extraire la date et le temps
            dates.append(ligne[index_date])
            temps.append(ligne[index_temps])
            data_PAS.append(ligne[index_PAS])

        except ValueError:
            continue

    donnees = {
        'bins': data_bins, 
        'LWC': data_LWC, 
        'MVD': data_MVD,
        'ED': data_ED,
        'PAS': data_PAS,
        'Concentration': data_concentration
    }

    return type_instrument, donnees, dates, temps

def lecture_vitesse_SFPDD(fichier_SFPDD):
    timestamps = []
    vitesses_grande_veine = []

    with open(fichier_SFPDD, 'r') as fichier:
        # Lire la première ligne (en-tête) pour identifier les colonnes
        en_tete = fichier.readline().strip().split()

        # Trouver les indices des colonnes qui nous intéressent
        index_timestamp = en_tete.index("Heure[HHMMSS]")
        index_vitesse_grande_veine = en_tete.index("Vit_Gde_Veine[m/s]")

        # Lire les lignes suivantes
        for ligne in fichier:
            valeurs = ligne.strip().split()
            if len(valeurs) > max(index_timestamp, index_vitesse_grande_veine):
                timestamps.append(valeurs[index_timestamp])
                vitesses_grande_veine.append(valeurs[index_vitesse_grande_veine])
    
    # Formater les timestamps en HH:MM:SS, cad au même format que les autres instruments
    timestamps_formatés = []
    for ts in timestamps:
        ts = ts.zfill(6)  # Ajouter des zéros à gauche si nécessaire
        heures = ts[:2]
        minutes = ts[2:4]
        secondes = ts[4:6]
        timestamps_formatés.append(f"{heures}:{minutes}:{secondes}.00")

    # Retourner un dictionnaire
    data_SFPDD = {
        'timestamps': timestamps_formatés,
        'vitesses_grande_veine': vitesses_grande_veine
    }

    return data_SFPDD