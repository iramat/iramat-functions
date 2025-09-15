# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 11:01:28 2025

@author: adisser
"""

##########################################################
# This script has already been integrated into charts.py #
##########################################################

import pandas as pd
import ternary
import plotly_express as px
import plotly.io as pio
from urls import read_data_urls
from get_data import get_data

dt = read_data_urls(read_ref=False)
a_dataset = dt['url_data'][1] 
data = get_data(a_dataset, dt['url_reference'], log10=False)
df = data['data']

# === 2. Coefficients de conversion Élément → Oxyde ===
conversion_factors = {
    'Na': ('Na2O', 1.348),
    'Mg': ('MgO', 1.658),
    'Al': ('Al2O3', 1.889),
    'Si': ('SiO2', 2.139),
    'P':  ('P2O5', 2.291),
    'K':  ('K2O', 1.204),
    'Ca': ('CaO', 1.399),
    'Mn': ('MnO', 1.291),
    'Fe': ('FeO', 1.287)
}



# === 4. Sélection et conversion des colonnes cibles ===
element_cols = list(conversion_factors.keys())
oxide_data = {}

for elem in element_cols:
    # Conversion en float (gère les erreurs)
    df[elem] = pd.to_numeric(df[elem], errors='coerce')
    oxide_name, factor = conversion_factors[elem]
    oxide_data[oxide_name] = df[elem] * factor

# === 5. Création d’un DataFrame avec les oxydes uniquement ===
oxides_df = pd.DataFrame(oxide_data)

# === 6. Fusion facultative avec les métadonnées d’origine ===
merged_df = pd.concat([df, oxides_df], axis=1)

# === 7. Sauvegarde du résultat ===
# oxides_df.to_csv(output_file, index=False)
# print(f"Fichier sauvegardé : {output_file}")


# === 8. Normalisation des éléments du diagramme ===
cols = ['FeO', 'SiO2', 'Al2O3']
for col in cols:
    merged_df[col[0]] = merged_df[col] * 100 / merged_df[cols].sum(axis=1)
    
fig, tax = ternary.figure(scale=100)
fig.set_size_inches(5, 4.5)

tax.scatter( merged_df[['FeO', 'SiO2', 'Al2O3']].values)

# Axis labels. (See below for corner labels.)
fontsize = 14
offset = 0.08
tax.left_axis_label("Al2O3 %", fontsize=fontsize, offset=offset)
tax.right_axis_label("SiO2 %", fontsize=fontsize, offset=offset)
tax.bottom_axis_label("FeO %", fontsize=fontsize, offset=-offset)
tax.set_title("Données scories Disser et al. 2017", fontsize=20)

# Decoration.
tax.boundary(linewidth=1)
tax.gridlines(multiple=10, color="gray")
tax.ticks(axis='lbr', linewidth=1, multiple=20)
tax.get_axes().axis('off')

# tax.show()

# Alternative plotly

pio.renderers.default = 'browser'  # Ouvre dans le navigateur par défaut
Fig_plotly = px.scatter_ternary(merged_df,
                   a="FeO", b="SiO2", c="Al2O3",
                   color="site_name"
                   )

Fig_plotly.show()