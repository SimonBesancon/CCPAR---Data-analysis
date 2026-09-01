# Programme pour afficher les série temporelle de FM100 + CDP + SFPDD,
# Auteur : Simon Bessançon

import csv
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

#main

chemin_dossier_data = r"C:\Travail\CCPAR\Données Tests SFPDD\20251203&04 - Acquisition SFPDD FM+CDP\20251203\20251203095622"

chemin_fichier_CDP = f"{chemin_dossier_data}\\01CDP20251203095622.csv"
chemin_fichier_FM100 = f"{chemin_dossier_data}\\00FM 10020251203095622.csv"
chemin_fichier_SFPDD = f"{chemin_dossier_data}\\SFPDD_251203_0946.txt"

# Paramètres pour un poster A0 (taille de police globale)
plt.rcParams.update({
    'font.size': 24,               # Taille de police par défaut
    'axes.titlesize': 28,          # Taille des titres des axes
    'axes.labelsize': 24,          # Taille des labels des axes
    'xtick.labelsize': 20,         # Taille des ticks sur l'axe X
    'ytick.labelsize': 20,         # Taille des ticks sur l'axe Y
    'legend.fontsize': 22,         # Taille de la légende
    'figure.titlesize': 30,        # Taille du titre de la figure
    'lines.linewidth': 3,          # Épaisseur des lignes
    'lines.markersize': 10,        # Taille des marqueurs
})

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

    def get_donnee_par_index(self, index):
        if 0 <= index < len(self.donnees['bins']):
            return {
                "donnee": {k: v[index] for k, v in self.donnees.items()},
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
            # Extraire LWC, MVD, ED, concentration
            data_LWC.append(ligne[index_LWC])
            data_MVD.append(ligne[index_MVD])
            data_ED.append(ligne[index_ED])
            data_concentration.append(ligne[index_concentration])
            # Extraire le timestamp, la date et le temps
            timestamp.append(ligne[index_Seconds])
            dates.append(ligne[index_date])
            temps.append(ligne[index_temps])
            data_PAS.append(ligne[index_PAS])

        except ValueError:
            continue

    donnees = {
        'timestamp': [float(ts) for ts in timestamp],  # Conversion timestamp de str en float
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

def lecture_vitesse_SFPDD(fichier_SFPDD):
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
        'vitesses_grande_veine': vitesses_grande_veine
    }

    return data_SFPDD

def plotter_donnees_SFPDD(data_SFPDD, instruments=None, variable=None, titre_supplémentaire=""):
    """
    Trace la vitesse du SFPDD seule ou accompagnée
    d'une même variable provenant d'un ou plusieurs instruments.
    Adapté pour un poster A0.
    """
    marker = ''
    linestyle = '-'  # ou '--' pour des lignes en pointillés, ou '' pour pas de ligne

    # ======================
    # SFPDD
    # ======================
    try:
        timestamps_SFPDD = [
            datetime.strptime(ts, "%H:%M:%S.%f")
            for ts in data_SFPDD['heure']
        ]
    except ValueError:
        try:
            timestamps_SFPDD = [
                datetime.strptime(ts, "%H:%M:%S")
                for ts in data_SFPDD['heure']
            ]
        except ValueError:
            raise ValueError("Le format des heures du SFPDD n'est pas reconnu. "
                             "Attendu HH:MM:SS ou HH:MM:SS.sss")

    vitesses = [float(v) for v in data_SFPDD["vitesses_grande_veine"]]

    fig, ax = plt.subplots(figsize=(20, 10))  # Taille adaptée pour A0

    ax.set_xlabel("Temps", fontsize=24, labelpad=10)
    ax.set_ylabel("Vitesse Grande Veine (m/s)", color="tab:blue", fontsize=24, labelpad=10)
    ax.plot(
        timestamps_SFPDD,
        vitesses,
        color="tab:blue",
        marker=marker,
        linestyle=linestyle,
        label="Vitesse SFPDD",
        linewidth=3
    )
    ax.tick_params(axis="y", labelcolor="tab:blue", labelsize=20)

    # ======================
    # CAS SFPDD SEUL
    # ======================
    if instruments is None or variable is None:
        ax.legend(loc="upper right", fontsize=22)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.xticks(rotation=45, fontsize=20)
        plt.title("Vitesse SFPDD", fontsize=30, pad=20)
        plt.tight_layout()
        plt.show()
        return

    # ======================
    # INSTRUMENTS
    # ======================
    if not isinstance(instruments, (list, tuple)):
        instruments = [instruments]

    colors = ["tab:red", "tab:green", "tab:orange", "tab:purple", "tab:brown"]
    axes = [ax]

    # Récupération des valeurs min/max globales pour uniformiser les échelles
    global_min = float('inf')
    global_max = float('-inf')

    for instrument in instruments:
        if variable not in instrument.donnees:
            raise ValueError(
                f"La variable '{variable}' n'existe pas pour "
                f"{instrument.type_instrument}"
            )

        try:
            valeurs_instr = [float(v) for v in instrument.donnees[variable]]
        except ValueError:
            raise ValueError(
                f"Impossible de convertir {variable} en float pour "
                f"{instrument.type_instrument}"
            )

        current_min = min(valeurs_instr)
        current_max = max(valeurs_instr)

        if current_min < global_min:
            global_min = current_min
        if current_max > global_max:
            global_max = current_max

    # Ajout des unités aux variables
    variable_unité = ""
    if variable == "LWC":
        variable_unité = variable + " (g/m³)"
    elif variable == "Concentration":
        variable_unité = variable + " (#/cm³)"
    elif variable == "MVD":
        variable_unité = variable + " (µm)"
    elif variable == "ED":
        variable_unité = variable + " (µm)"

    # Ajout des instruments avec échelles uniformisées
    for i, instrument in enumerate(instruments):
        timestamps_instr = [
            datetime.strptime(t, "%H:%M:%S.%f")
            for t in instrument.donnees['heure']
        ]
        valeurs_instr = [float(v) for v in instrument.donnees[variable]]

        ax_i = ax.twinx()
        axes.append(ax_i)

        # Position personnalisée pour chaque instrument
        if instrument.type_instrument == "FM 100":
            ax_i.spines["right"].set_position(("outward", 10))  # FM100 : 60 pixels à droite
        elif instrument.type_instrument == "CDP":
            ax_i.spines["right"].set_position(("outward", 100))  # CDP : 120 pixels à droite
        else:
            ax_i.spines["right"].set_position(("outward", 60 * (i + 1)))  # Autres : décalage progressif

        color = colors[i % len(colors)]
        ax_i.set_ylabel(
            f"{variable_unité} ({instrument.type_instrument})",
            color=color,
            fontsize=24,
            labelpad=10
        )
        ax_i.set_ylim(global_min, global_max)
        ax_i.plot(
            timestamps_instr,
            valeurs_instr,
            color=color,
            marker=marker,
            linestyle=linestyle,
            label=f"{instrument.type_instrument}",
            linewidth=3
        )
        ax_i.tick_params(axis="y", labelcolor=color, labelsize=20)

    # ======================
    # FORMAT FINAL
    # ======================
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.xticks(rotation=45, fontsize=20)

    # Légende globale propre
    handles, labels = [], []
    for a in axes:
        h, l = a.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)

    unique = dict(zip(labels, handles))

    # Titre avec les noms des instruments
    noms_instruments = ", ".join([inst.type_instrument for inst in instruments])
    plt.title(f"Vitesse SFPDD (m/s) et {variable_unité} - {noms_instruments} {titre_supplémentaire}", fontsize=30, pad=20)

    # Légende globale en bas à gauche, à l'intérieur du cadre
    fig.legend(
        unique.values(),
        unique.keys(),
        loc="upper right",
        bbox_to_anchor=(0.86, 0.91),  # À l'intérieur du cadre
        frameon=True,
        fontsize=22,
        bbox_transform=fig.transFigure
    )

    plt.tight_layout()
    plt.show()

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
        'vitesses_grande_veine': []
    }

    nb_trous = 0  # compteur de valeurs manquantes détectées

    for i in range(len(timestamps) - 1):
        ts0 = timestamps[i]
        v0 = float(vitesses[i])

        # Ajouter le point courant
        nouvelles_donnees['timestamp'].append(ts0)
        nouvelles_donnees['vitesses_grande_veine'].append(v0)
        nouvelles_donnees['heure'].append(str(timedelta(seconds=ts0)))

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

    # Ajouter le dernier point
    ts_last = timestamps[-1]
    v_last = float(vitesses[-1])

    nouvelles_donnees['timestamp'].append(ts_last)
    nouvelles_donnees['vitesses_grande_veine'].append(v_last)
    nouvelles_donnees['heure'].append(str(timedelta(seconds=ts_last)))

    data_SFPDD['timestamp'] = nouvelles_donnees['timestamp']
    data_SFPDD['heure'] = nouvelles_donnees['heure']
    data_SFPDD['vitesses_grande_veine'] = nouvelles_donnees['vitesses_grande_veine']

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

    # Tronquer aussi les données du FM100 pour toutes les clés comme ça c'est fait
    for key in FM100.donnees:   
        FM100.donnees[key] = FM100.donnees[key][start_index_CDP:end_index_CDP + 1]

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

def calculer_efficacité_par_plage_vitesse(CDP, FM100, data_SFPDD, parametres):
    # Convertir les vitesses et timestamps en float
    data_SFPDD['vitesses_grande_veine'] = [float(v) for v in data_SFPDD['vitesses_grande_veine']]
    data_SFPDD['timestamp'] = [float(ts) for ts in data_SFPDD['timestamp']]

    # Arrondir les vitesses à 5 m/s
    data_SFPDD['vitesses_grande_veine'] = [5 * round(v / 5) for v in data_SFPDD['vitesses_grande_veine']]

    # Initialiser les listes pour les plages de vitesse
    catalogue_plages = []
    debut_categorie = data_SFPDD['timestamp'][0]
    num_categorie = 0

    # Parcourir les vitesses pour détecter les changements de plage
    for i in range(1, len(data_SFPDD['vitesses_grande_veine'])):
        v_prev = data_SFPDD['vitesses_grande_veine'][i - 1]
        v_curr = data_SFPDD['vitesses_grande_veine'][i]

        # Si on change de plage de vitesse
        if int(v_prev // 5) != int(v_curr // 5):
            catalogue_plages.append({
                'Num_catégorie': num_categorie,
                'Début_catégorie': debut_categorie,
                'Fin_catégorie': data_SFPDD['timestamp'][i - 1],
                'Vitesse': data_SFPDD['vitesses_grande_veine'][i - 1]
            })
            num_categorie += 1
            debut_categorie = data_SFPDD['timestamp'][i]

    # Ajouter la dernière plage
    catalogue_plages.append({
        'Num_catégorie': num_categorie,
        'Début_catégorie': debut_categorie,
        'Fin_catégorie': data_SFPDD['timestamp'][-1],
        'Vitesse': data_SFPDD['vitesses_grande_veine'][-1]
    })

    # Nettoyage des plages trop courtes (moins de 10 secondes)
    catalogue_plages = [plage for plage in catalogue_plages if (plage['Fin_catégorie'] - plage['Début_catégorie']) >= 10]
    # Réattribuer les numéros de catégorie après nettoyage
    for idx, plage in enumerate(catalogue_plages):
        plage['Num_catégorie'] = idx


    # Calculer l'efficacité moyenne de chauqe paramètre pour chaque plage
    # Lister les clés à traiter (exclure 'timestamp', 'date', 'heure')
    parametre = ["LWC", "Concentration", "MVD", "ED"]

    # Initialiser les résultats pour chaque plage
    résultats_plages = []

    for plage in catalogue_plages:
        début = plage['Début_catégorie']
        fin = plage['Fin_catégorie']

        # Récupérer les indices des données dans CDP et FM100 pour cette plage
        indices_CDP = [i for i, ts in enumerate(CDP.donnees['timestamp']) if début <= ts <= fin]
        indices_FM100 = [i for i, ts in enumerate(FM100.donnees['timestamp']) if début <= ts <= fin]

        # Calculer la moyenne de chaque paramètre pour CDP
        moyennes_CDP = {}
        for clé in parametre:
            valeurs = [float(CDP.donnees[clé][i]) for i in indices_CDP] if indices_CDP else []
            moyennes_CDP[clé] = sum(valeurs) / len(valeurs) if valeurs else 0

        # Calculer la moyenne de chaque paramètre pour FM100
        moyennes_FM100 = {}
        for clé in parametre:
            valeurs = [float(FM100.donnees[clé][i]) for i in indices_FM100] if indices_FM100 else []
            moyennes_FM100[clé] = sum(valeurs) / len(valeurs) if valeurs else 0

        # Calculer l'efficacité en % pour chaque paramètre (exemple avec 'LWC')
        efficacités = {}
        for clé in set(parametre) & set(parametre):
            if moyennes_CDP[clé] != 0:
                efficacités[clé] = (moyennes_FM100[clé] / moyennes_CDP[clé]) * 100
            else:
                efficacités[clé] = 0

        # Stocker les résultats pour cette plage
        résultats_plages.append({
            'Vitesse': plage['Vitesse'],
            'Moyennes_CDP': moyennes_CDP,
            'Moyennes_FM100': moyennes_FM100,
            'Efficacités': efficacités
        })

    # Afficher les résultats
    print(f"Nombre total de plages de vitesse (après nettoyage) : {len(catalogue_plages)}")
    for i, plage in enumerate(catalogue_plages):
        taille_plage = plage['Fin_catégorie'] - plage['Début_catégorie']
        print(f"\nPlage {plage['Num_catégorie'] + 1} : Taille = {taille_plage:.2f} secondes, "
              f"de {plage['Début_catégorie']} à {plage['Fin_catégorie']} secondes, "
              f"vitesse = {plage['Vitesse']} m/s")

        print("Moyennes CDP :")
        for clé, valeur in résultats_plages[i]['Moyennes_CDP'].items():
            print(f"  {clé}: {valeur:.4f}")

        print("Moyennes FM100 :")
        for clé, valeur in résultats_plages[i]['Moyennes_FM100'].items():
            print(f"  {clé}: {valeur:.4f}")

        print("Efficacités (%):")
        for clé, valeur in résultats_plages[i]['Efficacités'].items():
            print(f"  {clé}: {valeur:.2f} %")

    # Retourner les vitesses et les résultats complets
    vitesses = [plage['Vitesse'] for plage in catalogue_plages]
    return vitesses, résultats_plages

def tracer_efficacité_par_plage_vitesse(vitesses_moyennes, efficacités_moyennes, parametres):
    """Trace l'efficacité en fonction des plages de vitesses avec un subplot par paramètre."""
    fig, axes = plt.subplots(nrows=len(parametres), ncols=1, figsize=(12, 6 * len(parametres)))
    colors = ['tab:red', 'tab:green', 'tab:orange', 'tab:purple']

    if len(parametres) == 1:
        axes = [axes]  # Pour gérer le cas où il n'y a qu'un seul paramètre

    for i, (ax, param) in enumerate(zip(axes, parametres)):
        ax.plot(vitesses_moyennes, efficacités_moyennes[param], color=colors[i], label=f"{param}")
        ax.set_xlabel("Vitesse moyenne (m/s)")
        ax.set_ylabel("Efficacité (%)")
        ax.set_title(f"Efficacité pour {param}")
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    plt.show()


print("\n")
CDP = DonneesInstrument(*identifier_instrument_et_extraire_donnees(chemin_fichier_CDP))
FM100 = DonneesInstrument(*identifier_instrument_et_extraire_donnees(chemin_fichier_FM100))

CDP.afficher_infos()
FM100.afficher_infos()

data_SFPDD = lecture_vitesse_SFPDD(chemin_fichier_SFPDD)
print(f"SFPDD : Nombre de données : {len(data_SFPDD['vitesses_grande_veine'])}")
print(f"    Début : {data_SFPDD['heure'][0]} ({data_SFPDD['timestamp'][0]} secondes)")
print(f"    Fin : {data_SFPDD['heure'][-1]} ({data_SFPDD['timestamp'][-1]} secondes)")


instruments = [FM100, CDP]
parametre = ["LWC", "Concentration"]

for param in parametre:
    plotter_donnees_SFPDD(data_SFPDD, instruments, param, "Avant correction PAS CDP")

corrig_LWC_concentration_PAS_CDP(CDP, data_SFPDD)

for param in parametre:
    plotter_donnees_SFPDD(data_SFPDD, instruments, param, "Après correction PAS CDP")


parametre = ["LWC", "Concentration", "MVD", "ED"]
# Tracer la vitesse du SFPDD avec la variable LWC du CDP
for param in parametre:
    plotter_donnees_SFPDD(data_SFPDD, instruments, param)

vitesses, efficacités_moyennes = calculer_efficacité_par_plage_vitesse(CDP, FM100, data_SFPDD, parametre)

print("Vitesses moyennes par plage :")
print(vitesses)
for param in parametre:
    print(f"{param} : {efficacités_moyennes[param]}")

tracer_efficacité_par_plage_vitesse(vitesses, efficacités_moyennes, parametre)