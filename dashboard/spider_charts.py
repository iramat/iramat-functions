import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt



def api_pg_dataset_radarplot(url_dataset, url_reference_elements, order_atom_num=True, sample_idx=0, normalize_by='fe'):
    """
    Télécharge les données chimiques depuis l'API et génère un diagramme radar pour un échantillon.
    
    :param url_dataset: URL du dataset à examiner
    :param url_reference_elements: URL de la table de référence des éléments chimiques
    :param order_atom_num: Ordonner selon le numéro atomique ?
    :param sample_idx: Index de l'échantillon à visualiser
    :param normalize_by: nom de l'élément chimique à utiliser pour normaliser les teneurs des autres éléments

    """
    # Charger les données
    ref = pd.DataFrame(requests.get(url_reference_elements).json())
    df = pd.DataFrame(requests.get(url_dataset).json())
    print(df)
    
    # Calculer les valeurs normalisées au fer
    if normalize_by:
        if normalize_by in df.columns:
            df = df.div(df[normalize_by], axis=0)
    else:
        raise ValueError(f"Colonne '{normalize_by}' absente")

    # ref_column = ref["symbole"].str.lower().tolist()
    ref_column = ['na', 'mg', 'al', 'si', 'p', 'k', 'ca', 'mn', 'fe']

    if order_atom_num:
        ordered_df = df[[col for col in ref_column if col in df.columns]]
    else:
        ordered_df = df[df.columns.intersection(ref_column)]


    # Extraire les données du sample sélectionné
    sample_data = ordered_df.iloc[sample_idx]
    labels = sample_data.index.tolist()
    values = sample_data.values

    # Fermer le cercle pour le radar plot
    values = np.concatenate((values, [values[0]]))
    labels += [labels[0]]

    # Créer le radar plot
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, values, linewidth=2, linestyle='solid')
    ax.fill(angles, values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title(f"Échantillon {sample_idx} - Profil chimique", size=14)

    plt.tight_layout()
    plt.show()

    return {
        "data": df,
        "elements": ordered_df
    }

def new_func(df):
    print(df.type)