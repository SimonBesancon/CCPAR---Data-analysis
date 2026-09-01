import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import csv
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import matplotlib.colors as colors


def lecture_data_AQT(chemin_fichier_AQT): 
    # === Lecture du fichier CSV ===
    fichier = chemin_fichier_AQT
    df = pd.read_csv(fichier, skipinitialspace=True)
    df.columns = df.columns.str.strip()

    # === Extraction du timestamp ===
    date_heure = pd.to_datetime(df['timestamp'], format='%Y%m%d%H%M%S')

    # === Extraction des colonnes lpc1 à lpc16 ===
    colonnes_lpc = [f"lpc{i}" for i in range(1, 17)]
    donnees_lpc = df[colonnes_lpc].to_numpy().T  # chaque ligne = un canal LPC

    # === Extraction des counts totaux ===
    total_counts = df['gb_cnt'].to_numpy() / 60  # Diviser par 60 pour obtenir le nombre de gouttes par seconde

    # Détecter les NaN et les remplacer par zéros
    donnees_lpc = np.where(np.isnan(donnees_lpc), 0, donnees_lpc)


    # Convertir les bins en taille de goutte en utilisant les tailles de bin de l'AQT
    tailles_bin_aqt = tableau_tailles_bin_AQT()
    mid_bins_µm = [bin_info['mid'] for bin_info in tailles_bin_aqt]

    print(f"Type d'instrument : AQT")
    print(f"    Nombre de variables : {len(donnees_lpc)}")
    print(f"    Début : {date_heure.iloc[0]}")
    print(f"    Fin : {date_heure.iloc[-1]}\n")

    #Calculer les secondes depuit minuit
    minuit = date_heure.dt.normalize()  # Obtenir la date sans l'heure
    secondes_depuis_minuit = (date_heure - minuit).dt.total_seconds()

    #Calculer la concentration totale : somme des bins / flux (17.86cm³/s pour l'AQT/ 60s)
    concentration_totale = np.sum(donnees_lpc, axis=0) / 17.86 / 60

    #Calculer la concentration par bin : nombre de gouttes par bin / flux (17.86cm³/s pour l'AQT/ 60s)
    concentrations_par_bin = donnees_lpc / 17.86 / 60

    #Calculer le MVD à partir des concentrations par bin et des tailles de bin milieu
    MVD = np.sum(concentrations_par_bin * np.array(mid_bins_µm)[:, np.newaxis], axis=0) / np.sum(concentrations_par_bin, axis=0)

    #Calculer le LWC à partir des concentrations par bin et des tailles de bin milieu
    LWC = np.sum(concentrations_par_bin * (4/3) * np.pi * (np.array(mid_bins_µm)[:, np.newaxis] / 2)**3 * 1e-12 * 1e6, axis=0)

    data_AQT = {
        'date_heure': date_heure,
        'lpc': donnees_lpc,
        'mid_bins_µm': mid_bins_µm,
        'timestamp': secondes_depuis_minuit,
        'concentration_totale': concentration_totale,
        'concentrations_par_bin': concentrations_par_bin,
        'MVD': MVD,
        'LWC': LWC,
        'total_counts': total_counts
    }

    return data_AQT


def tracer_graphique_AQT(data_AQT):

    date_heure = data_AQT['date_heure']
    donnees_lpc = data_AQT['lpc']
    mid_bins_µm = data_AQT['mid_bins_µm']

    # === Tracé avec heure en abscisse et tailles de goutte en ordonnée ===
    plt.figure(figsize=(12, 6))
    img = plt.imshow(donnees_lpc, aspect='auto', origin='lower',
                    extent=[mdates.date2num(date_heure.iloc[0]),
                            mdates.date2num(date_heure.iloc[-1]),
                            min(mid_bins_µm), max(mid_bins_µm)],  # Utilisation des tailles réelles
                    cmap='viridis')

    plt.colorbar(img, label='Nombre comptage')
    plt.title('Série Temporelle Acquisition AQT')
    plt.ylabel('µm (taille de goutte)')
    plt.xlabel('Heure')

    # Formatage de l’axe des temps
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def tableau_tailles_bin_AQT():
    tailles_bin_aqt = [
        {"bin": "1", "mid": 1.6407725, "low": 1.321321, "up": 1.960224},
        {"bin": "2", "mid": 2.1550115, "low": 1.960224, "up": 2.349799},
        {"bin": "3", "mid": 2.5757525, "low": 2.349799, "up": 2.801706},
        {"bin": "4", "mid": 3.0822, "low": 2.801706, "up": 3.362694},
        {"bin": "5", "mid": 3.6977285, "low": 3.362694, "up": 4.032763},
        {"bin": "6", "mid": 4.3989635, "low": 4.032763, "up": 4.765164},
        {"bin": "7", "mid": 5.388484, "low": 4.765164, "up": 6.011804},
        {"bin": "8", "mid": 6.463711, "low": 6.011804, "up": 6.915618},
        {"bin": "9", "mid": 7.585687, "low": 6.915618, "up": 8.255756},
        {"bin": "10", "mid": 9.066072, "low": 8.255756, "up": 9.876388},
        {"bin": "11", "mid": 10.842534, "low": 9.876388, "up": 11.80868},
        {"bin": "12", "mid": 12.977405, "low": 11.80868, "up": 14.14613},
        {"bin": "13", "mid": 15.626515, "low": 14.14613, "up": 17.1069},
        {"bin": "14", "mid": 19.054775, "low": 17.1069, "up": 21.00265},
        {"bin": "15", "mid": 22.950525, "low": 21.00265, "up": 24.8984},
        {"bin": "16", "mid": 27.23585, "low": 24.8984, "up": 29.5733}
    ]

    return tailles_bin_aqt

class DonneesInstrument:
    """
    Classe pour stocker les données extraites d'un instrument.
    """

    def __init__(self, type_instrument, donnees):
        """
        Initialise les attributs de la classe.

        :param type_instrument: Type de l'instrument (ex: "FM100", "CDP", etc.)
        :param donnees: Données extraites (ex: liste ou tableau de valeurs)
        :param dates: Liste des dates associées aux données
        :param temps: Liste des temps ou timestamps associées aux données
        """
        self.type_instrument = type_instrument
        self.donnees = donnees

    def afficher_infos(self):
        """Affiche un résumé des données."""
        print(f"Type d'instrument : {self.type_instrument}")
        print(f"    Nombre de variables : {len(self.donnees)} ({', '.join(self.donnees.keys())})")

        longueurs = {k: len(v) for k, v in self.donnees.items()}
        print(f"    Nombre de données : {next(iter(longueurs.values()))}" 
        if len(set(longueurs.values())) == 1
        else "\n".join(f"    {k} : {l} données" for k, l in longueurs.items()))

        print(f"    Début : {self.donnees['heure'][0]} ({self.donnees['timestamp'][0]} secondes)")
        print(f"    Fin : {self.donnees['heure'][-1]} ({self.donnees['timestamp'][-1]} secondes)\n")

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

    if index_date is None or index_temps is None:
        raise ValueError("Les colonnes 'Date' ou 'Time' n'ont pas été trouvées.")

    # Extraire les données des colonnes sélectionnées
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
            # Extraire les données des colonnes 'CDP Bin'
            valeurs = [float(ligne[i]) if ligne[i] else 0.0 for i in indices_colonnes_bins]
            data_bins.append(valeurs)

            # Convertir les colonnes numériques en float
            data_LWC.append(float(ligne[index_LWC]) if ligne[index_LWC] else np.nan)
            data_MVD.append(float(ligne[index_MVD]) if ligne[index_MVD] else np.nan)
            data_ED.append(float(ligne[index_ED]) if ligne[index_ED] else np.nan)
            data_concentration.append(float(ligne[index_concentration]) if ligne[index_concentration] else np.nan)
            data_PAS.append(float(ligne[index_PAS]) if ligne[index_PAS] else np.nan)

            # Extraire le timestamp, la date et le temps (pas besoin de conversion)
            timestamp.append(ligne[index_Seconds])
            dates.append(ligne[index_date])
            temps.append(ligne[index_temps])

        except ValueError:
            continue

    #Calcul du total_counts à partir des bins
    total_counts = [sum(bins) for bins in data_bins]

    donnees = {
        'timestamp': [float(ts) for ts in timestamp],  # Conversion timestamp de str en float
        'date': dates,
        'heure': temps,
        'bins': data_bins, 
        'LWC': data_LWC, 
        'MVD': data_MVD,
        'ED': data_ED,
        'PAS': data_PAS,
        'Concentration': data_concentration,
        'total_counts': total_counts
    }

    return type_instrument, donnees

def lecture_vitesse_SFPDD(fichier_SFPDD):

    # Extraire la date du nom du fichier (ex: "SFPDD_251009_1308.txt" -> "251009")
    nom_fichier = fichier_SFPDD.split('/')[-1]  # Prend le nom du fichier sans le chemin
    date_brute = nom_fichier.split('_')[1]  # Récupère "251009"

    # Convertir la date brute (JJMMAA) en format YYYY-MM-DD
    annee = date_brute[:2]
    mois = date_brute[2:4]
    jour = date_brute[4:]
    date_formatee = f"20{annee}-{mois}-{jour}"  # Ex: "2009-10-25"

    timestamps = []
    heuresHHMMSS = []
    vitesses_grande_veine = []

    with open(fichier_SFPDD, 'r') as fichier:
        # Lire la première ligne (en-tête) pour identifier les colonnes
        en_tete = fichier.readline().strip().split()

        # Trouver les indices des colonnes qui nous intéressent
        index_timestamp = en_tete.index("Heure[SecDuJour]")
        index_heure = en_tete.index("Heure[HHMMSS]")
        index_vitesse_grande_veine = en_tete.index("Vit_Gde_Veine[m/s]")

        # Lire les lignes suivantes
        for ligne in fichier:
            valeurs = ligne.strip().split()
            if len(valeurs) > max(index_timestamp, index_heure, index_vitesse_grande_veine):
                timestamps.append(valeurs[index_timestamp])
                heuresHHMMSS.append(valeurs[index_heure])
                vitesses_grande_veine.append(valeurs[index_vitesse_grande_veine])
    
    # Formater les heures en HH:MM:SS, cad au même format que les autres instruments
    heure_formatés = []
    for ts in heuresHHMMSS:
        ts = ts.zfill(6)  # Ajouter des zéros à gauche si nécessaire
        heures = ts[:2]
        minutes = ts[2:4]
        secondes = ts[4:6]
        heure_formatés.append(f"{heures}:{minutes}:{secondes}.00")

    # Retourner un dictionnaire
    data_SFPDD = {
        'timestamp': [float(ts) for ts in timestamps],  # Conversion timestamp de str en float
        'heure' : heure_formatés,
        'vitesses_grande_veine': vitesses_grande_veine,
        'date': [date_formatee] * len(timestamps)  # Répéter la date pour chaque entrée
    }

    return data_SFPDD

def couper_donnees_par_intervalle(AQT, CDP, data_SFPDD):
    """Coupe les données entre les timestamps de début et de fin."""

    print("Timestamps AQT : ", AQT['timestamp'][0], " à ", AQT['timestamp'].iloc[-1])
    print("Timestamps CDP : ", CDP.donnees['timestamp'][0], " à ", CDP.donnees['timestamp'][-1])
    print("Timestamps SFPDD : ", data_SFPDD['timestamp'][0], " à ", data_SFPDD['timestamp'][-1])
    début = max(min(AQT['timestamp']), min(CDP.donnees['timestamp']), min(data_SFPDD['timestamp']))
    fin = min(max(AQT['timestamp']), max(CDP.donnees['timestamp']), max(data_SFPDD['timestamp']))

    print(f"Intervalle commun : {début} à {fin}\n")

    return 

def CDP_ajouter_timestamp(CDP):
    """Ajoute une colonne 'timestamp' à l'objet CDP en combinant les colonnes 'Date' et 'Time'."""
    timestamps = []
    for date_str, time_str in zip(CDP.dates, CDP.temps):
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            timestamps.append(dt.timestamp())
        except ValueError:
            timestamps.append(None)  # ou gérer autrement les erreurs de format

    CDP.temps = timestamps  # Remplace les temps par les timestamps


def CDP_2minutes_exactes(CDP):
    """
    L'AQT fait 1min de mesure toutes les 2 minutes, tandis que le CDP mesure en continu.
    Regroupe les données du CDP par intervalles de 1 minute toutes les 2 minutes (ex: 13:00:00-13:01:00)."""

    # 1. Arrondir chaque timestamp à l'intervalle de 120 secondes pair inférieur
    intervalles_debut = np.floor(np.array(CDP.donnees['timestamp']) / 120) * 120
    intervalles_fin = intervalles_debut + 120  # Temps de fin d'intervalle


    # 2. Lister les intervalles uniques
    intervalles_uniques = np.unique(intervalles_debut)

    # 3. Initialiser les dictionnaires de sortie
    donnees_regroupees = {
        'bins': [],
        'LWC': [],
        'MVD': [],
        'ED': [],
        'PAS': [],
        'Concentration': [],
    }
    temps_regroupes = []

    # 4. Parcourir chaque intervalle unique
    for intervalle in intervalles_uniques:
        # Filtrer les indices correspondant à cet intervalle
        indices = np.where(intervalles_debut == intervalle)[0]

        # Ajouter le temps de fin d'intervalle
        temps_regroupes.append(intervalle + 60)  # On prend le temps de fin d'intervalle pour correspondre à la fin de la mesure AQT

        # Calculer la moyenne pour chaque variable
        donnees_regroupees['bins'].append(np.sum([CDP.donnees['bins'][i] for i in indices], axis=0) if indices.size > 0 else np.array([]))
        donnees_regroupees['LWC'].append(np.sum([CDP.donnees['LWC'][i] for i in indices]) if indices.size > 0 else np.nan)
        donnees_regroupees['MVD'].append(np.sum([CDP.donnees['MVD'][i] for i in indices]) if indices.size > 0 else np.nan)
        donnees_regroupees['ED'].append(np.sum([CDP.donnees['ED'][i] for i in indices]) if indices.size > 0 else np.nan)
        donnees_regroupees['PAS'].append(np.sum([CDP.donnees['PAS'][i] for i in indices]) if indices.size > 0 else np.nan)
        donnees_regroupees['Concentration'].append(np.sum([CDP.donnees['Concentration'][i] for i in indices]) if indices.size > 0 else np.nan)

    # 4. Stocker les résultats dans CDP
    CDP.donnees_regroupees_2min = donnees_regroupees
    CDP.timestamps_regroupe_2min = temps_regroupes    # Stocker les intervalles de temps regroupés

    return CDP


def tracer_graphique_AQT(data_AQT):

    date_heure = data_AQT['date_heure']
    donnees_lpc = data_AQT['lpc']
    mid_bins_µm = data_AQT['mid_bins_µm']

    # === Tracé avec heure en abscisse et tailles de goutte en ordonnée ===
    plt.figure(figsize=(12, 6))
    img = plt.imshow(donnees_lpc, aspect='auto', origin='lower',
                    extent=[mdates.date2num(date_heure.iloc[0]),
                            mdates.date2num(date_heure.iloc[-1]),
                            min(mid_bins_µm), max(mid_bins_µm)],  # Utilisation des tailles réelles
                    cmap='viridis')

    plt.colorbar(img, label='Nombre comptage')
    plt.title('Série Temporelle Acquisition AQT')
    plt.ylabel('µm (taille de goutte)')
    plt.xlabel('Heure')

    # Formatage de l’axe des temps
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def tracer_AQT_et_CDP_2min(data_AQT, CDP):
    """Trace les données AQT et CDP regroupées sur deux subplots."""

    #---------------------------
    # Tracé des données AQT 
    #---------------------------
    # 1. Préparer les données AQT
    date_heure_AQT = data_AQT['date_heure']
    donnees_lpc_AQT = data_AQT['lpc']
    mid_bins_µm_AQT = data_AQT['mid_bins_µm']

    # Remplacer les NaN par une petite valeur positive (pour éviter les problèmes de log scale)
    donnees_lpc_AQT = np.where(np.isnan(donnees_lpc_AQT), 1e-10, donnees_lpc_AQT)

    # 2. Créer la figure avec deux subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # 3. Tracer les données AQT (subplot supérieur)
    img_AQT = ax1.imshow(donnees_lpc_AQT, aspect='auto', origin='lower',
                        extent=[mdates.date2num(date_heure_AQT.iloc[0]),
                                mdates.date2num(date_heure_AQT.iloc[-1]),
                                min(mid_bins_µm_AQT), max(mid_bins_µm_AQT)],
                        cmap='viridis')
    ax1.set_title('Série Temporelle Acquisition AQT')
    ax1.set_ylabel('µm (taille de goutte)')
    plt.colorbar(img_AQT, ax=ax1, label='Nombre comptage')

        # Formatage de l’axe des temps
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Formatage de l’axe des temps pour AQT
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.tick_params(axis='x', rotation=45)

    #---------------------------
    # Tracé des données CDP 
    #---------------------------
    # 1. Préparer les données CDP regroupées
    # Combinaison des dates et temps par concatenation
    date = CDP.donnees['date'][0]  # Date du jour
    #Conversion des timestamps 2min en heure
    heure = convertir_timestamps_en_hh_mm_ss(CDP.timestamps_regroupe_2min)
    date_heure_CDP = [f"{date} {time}" for time in heure]
    # Convertir les chaînes de date_heure_CDP en objets datetime
    date_heure_CDP_datetime = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in date_heure_CDP]
    print("date_heure_CDP : ", date_heure_CDP[0], " à ", date_heure_CDP[-1])
 
    # Accéder aux données regroupées par intervalles de 2 minutes
    #L'AQT ne mesurant pas au dessus de 30µm, on ne prendra pas les bins 18 à 30 du CDP (superieur à 30µm donc) pour la comparaison
    donnees_CDP_regroupees = np.array(CDP.donnees_regroupees_2min['bins'][0:30]) 
    #Obtenir les tailles de bin milieu en µm pour les bins 1 à 17 du CDP
    mid_bins_µm_CDP = [table_bin_tailles_cdp()[i]['median_bin_size'] for i in range(30)]

    # 2. Tracer les données CDP regroupées (subplot inférieur)
    img_CDP = ax2.imshow(donnees_CDP_regroupees, aspect='auto', origin='lower',
                        extent=[mdates.date2num(date_heure_CDP_datetime[0]),
                                mdates.date2num(date_heure_CDP_datetime[-1]),
                                min(mid_bins_µm_CDP), max(mid_bins_µm_CDP)],
                        cmap='viridis')    
    ax2.set_title('Série Temporelle Acquisition CDP (regroupée par intervalles de 2 minutes)')
    ax2.set_ylabel('µm (taille de goutte)')
    plt.colorbar(img_CDP, ax=ax2, label='Nombre comptage')

    plt.show()

def tracer_AQT_et_CDP(data_AQT, CDP):
    """Trace les données AQT et CDP regroupées sur deux subplots."""

    #---------------------------
    # Tracé des données AQT 
    #---------------------------
    # 1. Préparer les données AQT
    date_heure_AQT = data_AQT['date_heure']
    donnees_lpc_AQT = data_AQT['lpc']
    mid_bins_µm_AQT = data_AQT['mid_bins_µm']

    # Remplacer les NaN par une petite valeur positive (pour éviter les problèmes de log scale)
    donnees_lpc_AQT = np.where(np.isnan(donnees_lpc_AQT), 1e-10, donnees_lpc_AQT)

    # 2. Créer la figure avec deux subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # 3. Tracer les données AQT (subplot supérieur)
    img_AQT = ax1.imshow(donnees_lpc_AQT, aspect='auto', origin='lower',
                        extent=[mdates.date2num(date_heure_AQT.iloc[0]),
                                mdates.date2num(date_heure_AQT.iloc[-1]),
                                min(mid_bins_µm_AQT), max(mid_bins_µm_AQT)],
                        cmap='viridis')
    ax1.set_title('Série Temporelle Acquisition AQT')
    ax1.set_ylabel('µm (taille de goutte)')
    plt.colorbar(img_AQT, ax=ax1, label='Nombre comptage')

        # Formatage de l’axe des temps
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Formatage de l’axe des temps pour AQT
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.tick_params(axis='x', rotation=45)

    #---------------------------
    # Tracé des données CDP 
    #---------------------------
    # 1. Préparer les données CDP regroupées
    # Combinaison des dates et temps par concatenation
    date = CDP.donnees['date'][0]  # Date du jour
    #Conversion des timestamps 2min en heure
    heure = CDP.donnees['heure']  # Les heures sont déjà au format HH:MM:SS
    date_heure_CDP = [f"{date} {time}" for time in heure]
    # Convertir les chaînes de date_heure_CDP en objets datetime
    date_heure_CDP_datetime = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f") for ts in date_heure_CDP]
    print("date_heure_CDP : ", date_heure_CDP[0], " à ", date_heure_CDP[-1])
 
    # Accéder aux données CDP
    
    donnees_CDP = np.array(CDP.donnees['bins']) 
    print("taille donnees_CDP : ", donnees_CDP.shape)


    #Obtenir les tailles de bin milieu en µm pour les bins 1 à 17 du CDP

    mid_bins_µm_CDP = [table_bin_tailles_cdp()[i]['median_bin_size'] for i in range(30)]

    # 2. Tracer les données CDP regroupées (subplot inférieur)
    img_CDP = ax2.imshow(donnees_CDP, aspect='auto', origin='lower',
                        extent=[mdates.date2num(date_heure_CDP_datetime[0]),
                                mdates.date2num(date_heure_CDP_datetime[-1]),
                                min(mid_bins_µm_CDP), max(mid_bins_µm_CDP)],
                        cmap='viridis')    
    ax2.set_title('Série Temporelle Acquisition CDP')
    ax2.set_ylabel('µm (taille de goutte)')
    plt.colorbar(img_CDP, ax=ax2, label='Nombre comptage')

    plt.show()



def convertir_timestamps_en_hh_mm_ss(timestamps):
    resultats = []
    for ts in timestamps:
        ts_entier = int(ts)  # Convertir en entier
        heures = ts_entier // 3600
        reste = ts_entier % 3600
        minutes = reste // 60
        secondes = reste % 60
        resultats.append(f"{heures:02d}:{minutes:02d}:{secondes:02d}")
    return resultats

def table_bin_tailles_cdp():
    """
    Le Bin et le upper_bin_size sont donnés par la datasheet de la CDP. Les colonnes suivantes sont calculées :
        Pour chaque bin, median_bin_size est calculé comme (upper_bin_size du bin précédent + upper_bin_size du bin actuel) / 2.
            Pour le bin 1, la taille médiane est simplement upper_bin_size / 2.
        Incertitude = (upper_bin_size[Bin] - upper_bin_size[Bin-1]) / 2
            Pour le bin 1, l’incertitude est upper_bin_size / 2.
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

def Détecter_trou_et_réparer_data_SFPDD(data_SFPDD):
    """
    Détecte les trous temporels dans les données SFPDD et les comble
    par interpolation linéaire de la vitesse.
    Reconstruit 'heure' à partir du timestamp.
    Affiche le nombre de valeurs manquantes détectées.
    """
    print("\nDétection et réparation des trous dans les données SFPDD :")

    # Sécuriser les timestamps (secondes entières)
    data_SFPDD['timestamp'] = [int(round(ts)) for ts in data_SFPDD['timestamp']]

    timestamps = data_SFPDD['timestamp']
    vitesses = data_SFPDD['vitesses_grande_veine']

    nouvelles_donnees = {
        'timestamp': [],
        'heure': [],
        'vitesses_grande_veine': [],
        'date' : []
    }

    nb_trous = 0  # compteur de valeurs manquantes détectées

    for i in range(len(timestamps) - 1):
        ts0 = timestamps[i]
        v0 = float(vitesses[i])

        # Ajouter le point courant
        nouvelles_donnees['timestamp'].append(ts0)
        nouvelles_donnees['vitesses_grande_veine'].append(v0)
        nouvelles_donnees['heure'].append(str(timedelta(seconds=ts0)))
        nouvelles_donnees['date'].append(data_SFPDD['date'][i])

        ts1 = timestamps[i + 1]
        v1 = float(vitesses[i + 1])
        dt = ts1 - ts0

        # Détection d’un trou
        if dt > 1:
            for t_missing in range(1, dt):
                nb_trous += 1  # incrémente à chaque valeur manquante

                ts_new = ts0 + t_missing
                # Interpolation linéaire
                v_interp = v0 + (v1 - v0) * (t_missing / dt)

                nouvelles_donnees['timestamp'].append(ts_new)
                nouvelles_donnees['vitesses_grande_veine'].append(v_interp)
                nouvelles_donnees['heure'].append(str(timedelta(seconds=ts_new)))
                nouvelles_donnees['date'].append(data_SFPDD['date'][i])


    # Ajouter le dernier point
    ts_last = timestamps[-1]
    v_last = float(vitesses[-1])

    nouvelles_donnees['timestamp'].append(ts_last)
    nouvelles_donnees['vitesses_grande_veine'].append(v_last)
    nouvelles_donnees['heure'].append(str(timedelta(seconds=ts_last)))
    nouvelles_donnees['date'].append(data_SFPDD['date'][-1])

    data_SFPDD['timestamp'] = nouvelles_donnees['timestamp']
    data_SFPDD['heure'] = nouvelles_donnees['heure']
    data_SFPDD['vitesses_grande_veine'] = nouvelles_donnees['vitesses_grande_veine']
    data_SFPDD['date'] = nouvelles_donnees['date']

    print(f"    Nombre de valeurs manquantes détectées et comblées : {nb_trous}")

    return

def corrig_LWC_concentration_PAS_CDP(CDP, data_SFPDD):
    """
    Corrige la LWC du CDP en fonction de la PAS appliquée.
    Utilise une correction linéaire basée sur des données expérimentales.
    """
    data_SFPDD['timestamp'] = [int(round(ts)) for ts in data_SFPDD['timestamp']]

    # Il y a des trous dans les données SFPDD, on les comble d'abord !
    Détecter_trou_et_réparer_data_SFPDD(data_SFPDD)

    print("\nCorrection de la LWC et de la Concentration du CDP en fonction de la PAS appliquée :")
    # Arrondir les timestamps du CDP pour correspondre à ceux du SFPDD
    CDP.donnees['timestamp'] = [round(ts) for ts in CDP.donnees['timestamp']]

    # Adapter les timestamps du SFPDD à ceux du CDP : 
    # Trouver les bornes de chevauchement
    start_time = max(min(data_SFPDD['timestamp']), min(CDP.donnees['timestamp']))
    end_time = min(max(data_SFPDD['timestamp']), max(CDP.donnees['timestamp']))

    print(f"    Tronquage des données entre {start_time} et {end_time} secondes.")

    # Trouver les indices de début et de fin pour chaque série
    start_index_SFPDD = next(i for i, ts in enumerate(data_SFPDD['timestamp']) if ts == start_time)
    end_index_SFPDD = next(i for i, ts in enumerate(data_SFPDD['timestamp']) if ts == end_time) - 1

    start_index_CDP = next(i for i, ts in enumerate(CDP.donnees['timestamp']) if ts == start_time)
    end_index_CDP = next(i for i, ts in enumerate(CDP.donnees['timestamp']) if ts == end_time) - 1

    # Tronquer les données de SFPDD pour toutes les clés
    for key in data_SFPDD.keys():
        data_SFPDD[key] = data_SFPDD[key][start_index_SFPDD:end_index_SFPDD + 1]

    # Tronquer les données du CDP pour toutes les clés
    for key in CDP.donnees:
        CDP.donnees[key] = CDP.donnees[key][start_index_CDP:end_index_CDP + 1]

    # Appliquer la correction LWC et Concentration en fonction de la PAS appliquée
    LWC_appliedPAS = []
    concentration_appliedPAS = []
    for lwc_str, pas_str, concentration_str, vitesse_str  in zip(
        CDP.donnees['LWC'],
        CDP.donnees['PAS'],
        CDP.donnees['Concentration'],
        data_SFPDD['vitesses_grande_veine']
    ):
        try:
            LWC = float(lwc_str)
            PAS = float(pas_str)
            concentration = float(concentration_str)
            vitesse = float(vitesse_str)
            if vitesse != 0:
                LWC_appliedPAS.append(LWC / vitesse * PAS)
                concentration_appliedPAS.append(concentration / vitesse * PAS)
            else:
            # Gérer le cas où la vitesse est 0, par exemple en ajoutant 0 ou une autre valeur par défaut
                LWC_appliedPAS.append(0)
                concentration_appliedPAS.append(0)
        except ValueError:
            LWC_appliedPAS.append(None)  # Gérer les valeurs non convertibles
            concentration_appliedPAS.append(None)

    CDP.donnees['LWC'] = LWC_appliedPAS
    CDP.donnees['Concentration'] = concentration_appliedPAS

def tracer_SFPDD_AQT_CDP(data_AQT, CDP, data_SFPDD, paramètre):
    """
    Trace la série temporelle avec trois échelles :
    - SFPDD : axe y à gauche (échelle indépendante)
    - AQT : axe y à droite (échelle partagée avec CDP)
    - CDP : axe y à droite (même échelle qu'AQT)
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # ======================
    # SFPDD (axe y à gauche)
    # ======================
    dates_SFPDD = data_SFPDD['date']
    heures_SFPDD = data_SFPDD['heure']

    timestamps_SFPDD = []
    for date, heure in zip(dates_SFPDD, heures_SFPDD):
        try:
            timestamp = datetime.strptime(f"{date} {heure}", "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                timestamp = datetime.strptime(f"{date} {heure}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError(f"Format d'heure non reconnu : {heure}. Attendu HH:MM:SS ou HH:MM:SS.sss")
        timestamps_SFPDD.append(timestamp)

    vitesses = [float(v) for v in data_SFPDD["vitesses_grande_veine"]]

    ax1.set_xlabel("Temps")
    ax1.set_ylabel("Vitesse Grande Veine (m/s)", color="tab:blue")
    ax1.plot(timestamps_SFPDD, vitesses, color="tab:blue", label="Vitesse SFPDD")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    # ======================
    # AQT (axe y à droite)
    # ======================
    ax2 = ax1.twinx()
    if paramètre in data_AQT:
        ax2.plot(data_AQT['date_heure'], data_AQT[paramètre], label='AQT', color="tab:orange")
        ax2.set_ylabel(f"{paramètre} AQT", color="tab:orange")
    if paramètre == 'concentration':
        ax2.plot(data_AQT['date_heure'], data_AQT['concentration_totale'], label='AQT (corrigé)', color="tab:orange")
        ax2.set_ylabel(f"{paramètre} AQT (Counts/cm³/sec)", color="tab:orange")
   
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    # ======================
    # CDP (même axe y qu'AQT)
    # ======================
    ax3 = ax1.twinx()
    heure_CDP = [datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S.%f") for date, time in zip(CDP.donnees['date'], CDP.donnees['heure'])]
    if paramètre in CDP.donnees:
        ax3.plot(heure_CDP, CDP.donnees[paramètre], label='CDP(corrigé)', color="tab:green")
        ax3.set_ylabel(f"{paramètre} CDP", color="tab:green")
    if paramètre == 'concentration':
        ax3.plot(heure_CDP, CDP.donnees['Concentration'], label='CDP (corrigé)', color="tab:green")
        ax3.set_ylabel(f"{paramètre} CDP (Counts/sec))", color="tab:green")
        # Décalage des axes Y

    ax3.spines["right"].set_position(("outward", 60))
    ax3.tick_params(axis="y", labelcolor="tab:green")

    #trouver le global min et max entre AQT et CDP pour ajuster les limites de l'axe y
    if paramètre == 'concentration':
        min_val = min(min(data_AQT['concentration_totale']), min(CDP.donnees['Concentration']))
        max_val = max(max(data_AQT['concentration_totale']), max(CDP.donnees['Concentration']))
    else:
        min_val = min(min(data_AQT[paramètre]), min(CDP.donnees[paramètre]))
        max_val = max(max(data_AQT[paramètre]), max(CDP.donnees[paramètre]))
    ax2.set_ylim(min_val * 0.9, max_val * 1.1)  # Ajuster les limites avec une marge de 10%
    ax3.set_ylim(min_val * 0.9, max_val * 1.1)  # Même limites pour CDP

    # ======================
    # Légende et mise en page
    # ======================
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.title(f"Série temporelle : Vitesse SFPDD vs {paramètre} AQT/CDP")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()



chemin_dossier_data = r"C:\Travail\CCPAR\Données Tests SFPDD\20251009 - Test CDP SAFIRE CDP LaMP CDA AQT"

chemin_fichier_AQT = f"{chemin_dossier_data}\\Data AQT\\aqt_20251009_1305.csv"
chemin_fichier_CDP = f"{chemin_dossier_data}\\Data CDP\\20251009\\20251009125049\\00CDP20251009125049.csv"
chemin_fichier_SFPDD = f"{chemin_dossier_data}\\Données soufflerie\\SFPDD_251009_1308.txt"

data_AQT = lecture_data_AQT(chemin_fichier_AQT)

CDP = DonneesInstrument(*identifier_instrument_et_extraire_donnees(chemin_fichier_CDP))
CDP.afficher_infos()

data_SFPDD = lecture_vitesse_SFPDD(chemin_fichier_SFPDD)
print(f"SFPDD : Nombre de données : {len(data_SFPDD['vitesses_grande_veine'])}")
print(f"    Début : {data_SFPDD['heure'][0]} ({data_SFPDD['timestamp'][0]} secondes)")
print(f"    Fin : {data_SFPDD['heure'][-1]} ({data_SFPDD['timestamp'][-1]} secondes)\n")

couper_donnees_par_intervalle(data_AQT, CDP, data_SFPDD)


corrig_LWC_concentration_PAS_CDP(CDP, data_SFPDD)

#tracer_graphique_AQT(data_AQT)

CDP = CDP_2minutes_exactes(CDP)

tracer_AQT_et_CDP(data_AQT, CDP)

tracer_AQT_et_CDP_2min(data_AQT, CDP)

tracer_SFPDD_AQT_CDP(data_AQT, CDP, data_SFPDD, 'concentration')
tracer_SFPDD_AQT_CDP(data_AQT, CDP, data_SFPDD, 'MVD')
tracer_SFPDD_AQT_CDP(data_AQT, CDP, data_SFPDD, 'LWC')
tracer_SFPDD_AQT_CDP(data_AQT, CDP, data_SFPDD, 'total_counts')
