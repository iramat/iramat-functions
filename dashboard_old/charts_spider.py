import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from get_data import get_data
from urls import read_data_urls


# def api_pg_dataset_radarplot(url_dataset, url_reference_elements, order_atom_num=True, sample_idx=0, normalize_by='fe'):
#     """
#     Télécharge les données chimiques depuis l'API et génère un diagramme radar pour un échantillon.
    
#     :param url_dataset: URL du dataset à examiner
#     :param url_reference_elements: URL de la table de référence des éléments chimiques
#     :param order_atom_num: Ordonner selon le numéro atomique ?
#     :param sample_idx: Index de l'échantillon à visualiser
#     :param normalize_by: nom de l'élément chimique à utiliser pour normaliser les teneurs des autres éléments

#     """
    # Charger les données
    
normalize_by='fe'
order_atom_num=True
sample_idx=0

url_dataset = "https://raw.githubusercontent.com/iramat/iramat-dev/refs/heads/main/dbs/chips/urls_data.tsv"
dataset = read_data_urls(read_ref=False)
url_data = dataset["url_data"]
url_reference = dataset["url_reference"]

response_data = requests.get(url_data[0])
data = response_data.json()
df = pd.DataFrame(data)

response_ref = requests.get(url_reference)
ref_elements = response_ref.json()
ref = pd.DataFrame(ref_elements)

# Calculer les valeurs normalisées au fer
ref_column =  ['na', 'mg', 'al', 'si', 'p', 'k', 'ca', 'mn']

if normalize_by:
	if normalize_by in df.columns:
		df[ref_column] = df[ref_column].div(df['fe'], axis=0)
else:
	raise ValueError(f"Colonne '{normalize_by}' absente")

if order_atom_num:
	ordered_df = df[[col for col in ref_column if col in df.columns]]
else:
	ordered_df = df[df.columns.intersection(ref_column)]


# Extraire les données du sample sélectionné
sample_data = ordered_df.iloc[sample_idx]
labels = sample_data.index.tolist()
values = sample_data.values

angles = np.linspace(0, 2 * np.pi, len(values), endpoint=False).tolist()
angles.append(angles[0])  # Close the circle

values = np.concatenate([values, [values[0]]])  # Close the plot

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.plot(angles, values, linewidth=2, linestyle='solid')
ax.fill(angles, values, alpha=0.25)

# ax.set_xticklabels(labels[:-1], fontsize=10)  # Use only the original labels
ax.set_xticks(angles[:-1])  # Set exact tick positions (excluding the closing angle)
ax.set_xticklabels(labels, fontsize=10)  # Set all labels

ax.set_title(f"Échantillon {sample_idx} - Profil chimique", size=14)

plt.tight_layout()
plt.show()
