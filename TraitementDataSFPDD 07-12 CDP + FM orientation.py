# Programme pour afficher les série temporelle de FM100 + CDP + SFPDD,
# Auteur : Simon Bessançon

import csv
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np


#main

chemin_dossier_data = r"C:\Travail\CCPAR\Données Tests SFPDD\20251207 - Test CDP SAFIRE et FM GEOSPHERE ANGLE\20251207"

chemin_fichier_CDP = f"{chemin_dossier_data}\\20251207121548\\01CDP20251207121548.csv"
chemin_fichier_FM100 = f"{chemin_dossier_data}\\20251207121548\\00FM 10020251207121548.csv"
chemin_fichier_SFPDD = f"{chemin_dossier_data}\\SFPDD_251207_1215.txt"

# Paramètres pour un poster A0 (taille de police globale)
plt.rcParams.update({
    'font.size': 24,               # Taille de police par défaut
    'axes.titlesize': 28,          # Taille des titres des axes
    'axes.labelsize': 24,          # Taille des labels des axes
    'xtick.labelsize': 20,         # Taille des ticks sur l'axe X
    'ytick.labelsize': 20,         # Taille des ticks sur l'axe Y
    'legend.fontsize': 22,         # Taille de la légende
    'figure.titlesize': 30,        # Taille du titre de la figure
    'lines.linewidth': 5,          # Épaisseur des lignes (pour une meilleure visibilité)
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
        print(f"    Fin : ({self.donnees['heure'][-1]} ({self.donnees['timestamp'][-1]} secondes)")

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

def plotter_donnees_SFPDD(
    data_SFPDD,
    instruments=None,
    variable=None,
    titre_supplémentaire="",
    orientation_inlet_FM100=None,
    moyennes_par_orientation=None,
    ylim_SFPDD=None
):
    """
    Trace la vitesse du SFPDD seule ou accompagnée
    d'une même variable provenant d'un ou plusieurs instruments.
    Légende des axes en bas à gauche.
    Adapté pour un poster A0.
    """
    # ======================
    # SFPDD (axe principal)
    # ======================
    timestamps_SFPDD = [
        datetime.strptime(ts, "%H:%M:%S.%f")
        for ts in data_SFPDD['heure']
    ]
    vitesses = [float(v) for v in data_SFPDD["vitesses_grande_veine"]]

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.set_xlabel("Temps", fontsize=24, labelpad=10)
    ax.set_ylabel("Vitesse Grande Veine (m/s)", color="tab:blue", fontsize=24, labelpad=10)
    ax.plot(
        timestamps_SFPDD,
        vitesses,
        color="tab:blue",
        label="Vitesse SFPDD",
        zorder=1,
        linewidth=3
    )
    ax.tick_params(axis="y", labelcolor="tab:blue", labelsize=20)

    # Forcer l'échelle de l'axe SFPDD si ylim_SFPDD est fourni
    if ylim_SFPDD is not None:
        ax.set_ylim(ylim_SFPDD)

    # ======================
    # CAS SFPDD SEUL
    # ======================
    if instruments is None or variable is None:
        ax.legend(loc="lower left", fontsize=22)  # Légende en bas à gauche
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

    # Couleurs fixes : FM100 en rouge, CDP en vert
    colors = {
        "FM 100": "tab:red",
        "CDP": "tab:green",
        "CDP PBP": "tab:green"
    }

    # Un seul axe secondaire pour tous les instruments
    ax_instruments = ax.twinx()
    axes = [ax, ax_instruments]

    # Calcul des min/max globaux pour uniformiser les échelles
    global_min = float('inf')
    global_max = float('-inf')
    for instrument in instruments:
        if variable not in instrument.donnees:
            raise ValueError(f"La variable '{variable}' n'existe pas pour {instrument.type_instrument}")
        try:
            valeurs_instr = [float(v) for v in instrument.donnees[variable]]
        except ValueError:
            raise ValueError(f"Impossible de convertir {variable} en float pour {instrument.type_instrument}")
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

    # Tri des instruments pour tracer CDP en dernier (devant les autres)
    instruments_sorted = sorted(instruments, key=lambda x: x.type_instrument != "CDP")

    # Tracer tous les instruments sur le même axe secondaire
    for instrument in instruments_sorted:
        timestamps_instr = [
            datetime.strptime(t, "%H:%M:%S.%f")
            for t in instrument.donnees['heure']
        ]
        valeurs_instr = [float(v) for v in instrument.donnees[variable]]
        color = colors.get(instrument.type_instrument, "tab:orange")

        # zorder : CDP devant FM100
        z_order = 10 if instrument.type_instrument in ["CDP", "CDP PBP"] else 5

        ax_instruments.plot(
            timestamps_instr,
            valeurs_instr,
            color=color,
            label=f"{instrument.type_instrument} - {variable_unité}",
            zorder=z_order,
            linewidth=3
        )

    # Uniformiser l'échelle de l'axe secondaire
    ax_instruments.set_ylim(global_min, global_max)
    ax_instruments.set_ylabel(variable_unité, color="black", fontsize=24, labelpad=10)
    ax_instruments.tick_params(axis="y", labelcolor="black", labelsize=20)

    # ======================
    # ORIENTATION INLET FM100
    # ======================
    if orientation_inlet_FM100 is not None:
        for entry in orientation_inlet_FM100:
            start_time = datetime.strptime(entry["start_time"], "%H:%M:%S")
            stop_time = datetime.strptime(entry["stop_time"], "%H:%M:%S")
            orientation = entry["orientation"]
            ax.axvspan(start_time, stop_time, color="tab:gray", alpha=0.2)
            middle_time = start_time + (stop_time - start_time) / 2
            ax.text(
                middle_time,
                ax.get_ylim()[1] * 0.95,
                f"{orientation}°",
                horizontalalignment='center',
                verticalalignment='bottom',
                color="tab:gray",
                fontsize=22,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.5')
            )

    # ======================
    # FORMAT FINAL
    # ======================
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.xticks(rotation=45, fontsize=20)

    # Légende globale en bas à gauche
    handles, labels = [], []
    for a in axes:
        h, l = a.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    unique = dict(zip(labels, handles))

    noms_instruments = ", ".join([inst.type_instrument for inst in instruments])
    plt.title(f"Vitesse SFPDD (m/s) et {variable_unité} - {noms_instruments} ({titre_supplémentaire})", fontsize=30, pad=20)

    # Légende globale en bas à gauche, à l'intérieur du cadre
    fig.legend(
        unique.values(),
        unique.keys(),
        loc="upper right",
        bbox_to_anchor=(0.92, 0.85),  # À l'intérieur du cadre
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

    print(f"    Nombre de valeurs manquantes détectées et comblées : {nb_trous}")

    return nouvelles_donnees

def corrig_LWC_concentration_PAS_CDP(CDP, data_SFPDD):
    """
    Corrige la LWC du CDP en fonction de la PAS appliquée.
    Utilise une correction linéaire basée sur des données expérimentales.
    """
    data_SFPDD['timestamp'] = [int(round(ts)) for ts in data_SFPDD['timestamp']]

    # Il y a des trous dans les données SFPDD, on les comble d'abord !
    data_SFPDD = Détecter_trou_et_réparer_data_SFPDD(data_SFPDD)

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

def lecture_log_orientation_inletFM100(fichier_log):
    data_orientation_inlet_formate = []

    with open(fichier_log, "r", encoding='utf-8') as fichier:  # Ajout de l'encodage UTF-8 pour éviter les problèmes de caractères
        next(fichier)  # Ignorer la ligne d'en-tête

        for line in fichier:
            if len(line.strip()) == 0:
                continue  # Ignorer les lignes vides

            # Diviser la ligne en colonnes
            colonnes = line.split('\t')  # Supposons que les colonnes sont séparées par des tabulations
            if len(colonnes) < 4:
                colonnes = line.split()  # Si ce n'est pas des tabulations, essayer avec des espaces

            # Extraire les informations
            debut = colonnes[0].strip()
            fin = colonnes[1].strip()
            speed = colonnes[2].strip()
            angle = colonnes[3].strip()
            remarque = colonnes[4].strip() if len(colonnes) > 4 else ""

            # Nettoyer la valeur de l'angle : extraire uniquement le premier nombre
            angle_nettoye = angle.split()[0]  # Prend le premier mot (ex: "15" dans "15 nachgeholt / oublié")

            # Formater les temps au format "HH:MM:SS"
            def formater_temps(temps_str):
                temps_str = temps_str.replace("h", ":").replace("m", ":").replace("s", "")
                parties = temps_str.split(":")
                if len(parties) == 2:
                    heures, minutes = parties
                    secondes = "00"
                elif len(parties) == 3:
                    heures, minutes, secondes = parties
                else:
                    heures, minutes, secondes = "00", "00", "00"

                heures = heures.zfill(2)
                minutes = minutes.zfill(2)
                secondes = secondes.zfill(2)
                return f"{heures}:{minutes}:{secondes}"

            start_time = formater_temps(debut)
            stop_time = formater_temps(fin)

            # Ajouter au résultat
            data_orientation_inlet_formate.append({
                "orientation": angle_nettoye,  # Utiliser la valeur nettoyée
                "start_time": start_time,
                "stop_time": stop_time,
                "speed": speed,
                "remarque": remarque
            })

    return data_orientation_inlet_formate

def calcul_val_moy_par_angle(data_orientation_inlet_FM100, data_SFPDD, CDP, FM100):
    """
    Calcule la valeur moyenne de chaque instrument pour les différentes orientations de l'inlet du FM100.
    Retourne un tableau avec l'orientation, la vitesse moyenne SFPDD, et les valeurs moyennes des paramètres de CDP et FM100.
    """
    moyennes_par_orientation = []

    for entry in data_orientation_inlet_FM100:
        orientation = entry["orientation"]
        start_time = datetime.strptime(entry["start_time"], "%H:%M:%S")
        stop_time = datetime.strptime(entry["stop_time"], "%H:%M:%S")

        # Filtrer les données SFPDD dans la plage de temps
        vitesses = []
        for ts_str, vitesse_str in zip(data_SFPDD['heure'], data_SFPDD['vitesses_grande_veine']):
            ts = datetime.strptime(ts_str, "%H:%M:%S.%f")
            if start_time <= ts <= stop_time:
                vitesses.append(float(vitesse_str))
        vitesse_moyenne = sum(vitesses) / len(vitesses) if vitesses else 0.0

        # Arrondir la vitesse moyenne au multiple de 5 le plus proche
        vitesse_moy_ajusté = 5 * round(vitesse_moyenne / 5)

        # Filtrer et calculer les moyennes pour CDP
        cdp_LWC = []
        cdp_Concentration = []
        cdp_MVD = []
        cdp_ED = []
        for ts_str, lwc, conc, mvd, ed in zip(CDP.donnees['heure'], CDP.donnees['LWC'], CDP.donnees['Concentration'], CDP.donnees['MVD'], CDP.donnees['ED']):
            ts = datetime.strptime(ts_str, "%H:%M:%S.%f")
            if start_time <= ts <= stop_time:
                try:
                    cdp_LWC.append(float(lwc))
                    cdp_Concentration.append(float(conc))
                    cdp_MVD.append(float(mvd))
                    cdp_ED.append(float(ed))
                except ValueError:
                    continue

        # Filtrer et calculer les moyennes pour FM100
        fm_LWC = []
        fm_Concentration = []
        fm_MVD = []
        fm_ED = []
        for ts_str, lwc, conc, mvd, ed in zip(FM100.donnees['heure'], FM100.donnees['LWC'], FM100.donnees['Concentration'], FM100.donnees['MVD'], FM100.donnees['ED']):
            ts = datetime.strptime(ts_str, "%H:%M:%S.%f")
            if start_time <= ts <= stop_time:
                try:
                    fm_LWC.append(float(lwc))
                    fm_Concentration.append(float(conc))
                    fm_MVD.append(float(mvd))
                    fm_ED.append(float(ed))
                except ValueError:
                    continue

        # Calcul des moyennes
        cdp_moyennes = {
            'LWC': sum(cdp_LWC) / len(cdp_LWC) if cdp_LWC else 0.0,
            'Concentration': sum(cdp_Concentration) / len(cdp_Concentration) if cdp_Concentration else 0.0,
            'MVD': sum(cdp_MVD) / len(cdp_MVD) if cdp_MVD else 0.0,
            'ED': sum(cdp_ED) / len(cdp_ED) if cdp_ED else 0.0,
        }

        fm_moyennes = {
            'LWC': sum(fm_LWC) / len(fm_LWC) if fm_LWC else 0.0,
            'Concentration': sum(fm_Concentration) / len(fm_Concentration) if fm_Concentration else 0.0,
            'MVD': sum(fm_MVD) / len(fm_MVD) if fm_MVD else 0.0,
            'ED': sum(fm_ED) / len(fm_ED) if fm_ED else 0.0,
        }

        moyennes_par_orientation.append({
            'orientation': orientation,
            'vitesse_moyenne_SFPDD': vitesse_moyenne,
            'vitesse_moy_ajusté': vitesse_moy_ajusté,
            'CDP': cdp_moyennes,
            'FM100': fm_moyennes,
        })

    return moyennes_par_orientation

def tracer_graphe_polaire_par_vitesse(
    resultats,
    parametre="LWC",
    trace_efficacité=False
):
    """
    Trace un graphe polaire (demi-cercle) pour chaque vitesse ajustée, avec 0° en haut et 180° en bas.
    Titre sur 2 lignes : "Valeur moyenne de [parametre] (unité)" + "Vitesse vent = XX m/s".
    Adapté pour un poster A0.
    """
    # Dictionnaire pour les unités des paramètres
    unites = {
        "LWC": "(g/m³)",
        "Concentration": "(#/cm³)",
        "MVD": "(µm)",
        "ED": "(µm)"
    }
    unite = unites.get(parametre, "")

    # Regrouper les résultats par vitesse ajustée
    vitesses_ajustées = sorted(set(r['vitesse_moy_ajusté'] for r in resultats))

    for vitesse in vitesses_ajustées:
        # Filtrer les résultats pour cette vitesse
        data_vitesse = [r for r in resultats if r['vitesse_moy_ajusté'] == vitesse]

        # Dictionnaires pour stocker les valeurs par angle
        valeurs_CDP_par_angle = {}
        valeurs_FM100_par_angle = {}

        for r in data_vitesse:
            angle = int(r['orientation'])
            # Ignorer les angles > 180° (symétrie)
            if angle > 180:
                continue
            if angle not in valeurs_CDP_par_angle:
                valeurs_CDP_par_angle[angle] = []
                valeurs_FM100_par_angle[angle] = []

            valeurs_CDP_par_angle[angle].append(r['CDP'][parametre])
            valeurs_FM100_par_angle[angle].append(r['FM100'][parametre])

        # Calculer les moyennes par angle (uniquement pour 0° ≤ angle ≤ 180°)
        angles = sorted(valeurs_CDP_par_angle.keys())
        moyennes_CDP = [np.mean(valeurs_CDP_par_angle[angle]) for angle in angles]
        moyennes_FM100 = [np.mean(valeurs_FM100_par_angle[angle]) for angle in angles]

        # Convertir les orientations en radians pour le graphe polaire
        angles_rad = np.deg2rad(angles)

        # Créer le graphe polaire (demi-cercle)
        fig, ax = plt.subplots(figsize=(16, 16), subplot_kw={'projection': 'polar'})

        # Limiter l'affichage à 0°-180°
        ax.set_theta_offset(np.pi / 2)  # 0° en haut
        ax.set_theta_direction(-1)      # Sens horaire (180° à droite)
        ax.set_thetalim(0, np.pi)       # Afficher uniquement de 0 à 180° (en radians)

        if trace_efficacité:
            # Calculer l'efficacité en %
            efficacites = [100 * (fm / cdp) if cdp != 0 else 0 for cdp, fm in zip(moyennes_CDP, moyennes_FM100)]
            ax.plot(angles_rad, efficacites, marker='o', label=f'Efficacité FM100 - {parametre} {unite}', color='tab:green', markersize=12, linewidth=3)
            ax.set_ylim(0, 150)
            titre_ligne1 = f"Efficacité (%) du FM100 par rapport à la CDP pour {parametre} {unite}"
            titre_ligne2 = f"Vitesse vent = {vitesse} m/s"
        else:
            # Tracer les valeurs moyennes CDP et FM100
            ax.plot(angles_rad, moyennes_CDP, marker='o', label=f'CDP - {parametre} {unite}', color='tab:green', markersize=12, linewidth=3)
            ax.plot(angles_rad, moyennes_FM100, marker='o', label=f'FM100 - {parametre} {unite}', color='tab:red', markersize=12, linewidth=3)
            titre_ligne1 = f"Valeur moyenne de {parametre} {unite}"
            titre_ligne2 = f"Vitesse vent = {vitesse} m/s"

        # Définir les ticks d'angle (uniquement 0°, 45°, 90°, 135°, 180°)
        ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180]))
        ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°'], fontsize=24)

        # Titre sur 2 lignes
        ax.set_title(f"{titre_ligne1}\n{titre_ligne2}", pad=30, fontsize=28)

        # Légende
        ax.legend(loc='upper right', fontsize=22)

        plt.tight_layout()
        plt.show()

def filtrer_donnees_par_heure(donnees, heure_debut, heure_fin, cle_timestamp='timestamp', cle_heure='heure'):
    """
    Filtre les données pour ne garder que celles entre heure_debut et heure_fin (format "HH:MM").
    Retourne un dictionnaire avec les mêmes clés, mais tronqué.
    """
    # Convertir les heures de début/fin en timestamps (secondes depuis minuit)
    def heure_to_timestamp(h):
        hh, mm = map(int, h.split(':'))
        return hh * 3600 + mm * 60

    ts_debut = heure_to_timestamp(heure_debut)
    ts_fin = heure_to_timestamp(heure_fin)

    # Filtrer les indices où le timestamp est dans l'intervalle
    if cle_timestamp in donnees:
        indices = [i for i, ts in enumerate(donnees[cle_timestamp]) if ts_debut <= ts <= ts_fin]
    else:
        # Si pas de timestamp, utiliser l'heure formatée
        indices = []
        for i, h in enumerate(donnees[cle_heure]):
            ts = datetime.strptime(h, "%H:%M:%S.%f").hour * 3600 + datetime.strptime(h, "%H:%M:%S.%f").minute * 60
            if ts_debut <= ts <= ts_fin:
                indices.append(i)

    # Retourner les données filtrées
    return {k: [v[i] for i in indices] for k, v in donnees.items()}

def filtrer_orientations_par_heure(orientations, heure_debut, heure_fin):
    """
    Filtre les orientations pour ne garder que celles qui chevauchent [heure_debut, heure_fin].
    Ajuste les start_time/stop_time pour qu'elles soient dans l'intervalle.
    """
    def heure_to_datetime(h):
        # Ajouter :00 si les secondes manquent
        if len(h.split(':')) == 2:
            h += ":00"
        return datetime.strptime(h, "%H:%M:%S")

    debut = heure_to_datetime(heure_debut)
    fin = heure_to_datetime(heure_fin)

    orientations_filtrees = []
    for entry in orientations:
        start = heure_to_datetime(entry["start_time"])
        stop = heure_to_datetime(entry["stop_time"])

        # Vérifier si l'intervalle chevauche [debut, fin]
        if stop <= debut or start >= fin:
            continue  # Pas de chevauchement

        # Clipper start et stop à [debut, fin]
        new_start = max(start, debut)
        new_stop = min(stop, fin)

        orientations_filtrees.append({
            **entry,
            "start_time": new_start.strftime("%H:%M:%S"),
            "stop_time": new_stop.strftime("%H:%M:%S")
        })

    return orientations_filtrees

# ======================
# MAIN
# ======================

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
# parametre = ["LWC", "Concentration"]

# for param in parametre:
#     plotter_donnees_SFPDD(data_SFPDD, instruments, param, "Avant correction PAS CDP")

corrig_LWC_concentration_PAS_CDP(CDP, data_SFPDD)

# for param in parametre:
#     plotter_donnees_SFPDD(data_SFPDD, instruments, param, "Après correction PAS CDP")

fichier_log_SFPDD = r"C:\Travail\CCPAR\Données Tests SFPDD\20251207 - Test CDP SAFIRE et FM GEOSPHERE ANGLE\20251207\log angle Alfons.txt"
data_orientation_inlet_FM100 = lecture_log_orientation_inletFM100(fichier_log_SFPDD)

# parametre = ["LWC", "Concentration", "MVD", "ED"]
# # Tracer la vitesse du SFPDD avec la variable LWC du CDP
# for param in parametre:
#     plotter_donnees_SFPDD(data_SFPDD, instruments, param, "FM100 Inlet Angled Orientation tests", data_orientation_inlet_FM100)

vals_moy_par_angle = calcul_val_moy_par_angle(data_orientation_inlet_FM100, data_SFPDD, CDP, FM100)

# Filtrer les données entre 13:17 et 13:49
heure_debut = "13:17"
heure_fin = "13:49"

# Filtrer SFPDD
data_SFPDD_tronquee = filtrer_donnees_par_heure(data_SFPDD, heure_debut, heure_fin)

# Filtrer CDP et FM100 (utiliser la clé 'timestamp' ou 'heure')
CDP_tronque = DonneesInstrument(
    CDP.type_instrument,
    filtrer_donnees_par_heure(CDP.donnees, heure_debut, heure_fin)
)
FM100_tronque = DonneesInstrument(
    FM100.type_instrument,
    filtrer_donnees_par_heure(FM100.donnees, heure_debut, heure_fin)
)

# Filtrer les orientations entre 13:17 et 13:49
orientations_tronquees = filtrer_orientations_par_heure(
    data_orientation_inlet_FM100,
    "13:17",
    "13:49"
)


# Tracer le MVD tronqué avec les orientations tronquées
plotter_donnees_SFPDD(
    data_SFPDD_tronquee,
    instruments=[CDP_tronque, FM100_tronque],
    variable="MVD",
    titre_supplémentaire="Vitesse de vent constante de 15 m.s⁻¹",
    orientation_inlet_FM100=orientations_tronquees,
    ylim_SFPDD=(0, 20)  # <-- Échelle forcée entre 0 et 20 m/s
)

for resultat in vals_moy_par_angle:
    print(f"Orientation: {resultat['orientation']}°")
    print(f"  Vitesse moyenne SFPDD: {resultat['vitesse_moyenne_SFPDD']:.2f} m/s")
    print(f"  Vitesse moyenne ajustée: {resultat['vitesse_moy_ajusté']:.1f} m/s")
    print(f"  CDP  -  LWC: {resultat['CDP']['LWC']:.2f} g/m³, Concentration: {resultat['CDP']['Concentration']:.2f} #/cm³, MVD: {resultat['CDP']['MVD']:.2f} µm, ED: {resultat['CDP']['ED']:.2f} µm")
    print(f"  FM100 - LWC: {resultat['FM100']['LWC']:.2f} g/m³, Concentration: {resultat['FM100']['Concentration']:.2f} #/cm³, MVD: {resultat['FM100']['MVD']:.2f} µm, ED: {resultat['FM100']['ED']:.2f} µm")


# Tracer avec les moyennes
parametre = ["LWC", "Concentration", "MVD", "ED"]
for param in parametre:
    plotter_donnees_SFPDD(
        data_SFPDD,
        instruments=[CDP, FM100],
        variable=param,
        titre_supplémentaire="FM100 Inlet Angled Orientation tests",
        orientation_inlet_FM100=data_orientation_inlet_FM100,
        moyennes_par_orientation=vals_moy_par_angle
    )

parametre = ["LWC", "Concentration", "MVD", "ED"]
for param in parametre:
    tracer_graphe_polaire_par_vitesse(vals_moy_par_angle, param, trace_efficacité=False)

parametre = ["LWC", "Concentration", "MVD", "ED"]
for param in parametre:
    tracer_graphe_polaire_par_vitesse(vals_moy_par_angle, param, trace_efficacité=True)
