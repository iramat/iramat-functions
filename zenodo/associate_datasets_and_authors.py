#%%

import pandas as pd
import numpy as np

FOLDER_PATH = "C:\\Users\\TH282424\\Rprojects\\iramat-dev\\doc\\projects\\chips\\datasets_by_authors\\"
DEFAULT_URLS_DATA = "https://raw.githubusercontent.com/iramat/chips/refs/heads/hugo-files/static/data/urls_data.tsv"
urls_data = pd.read_csv(DEFAULT_URLS_DATA, sep="\t", dtype=str)
urls_data = urls_data[urls_data.is_reference_data != 'Y']


DEFAULT_URLS_AUTHORS = FOLDER_PATH + "listing_IN.xlsx"
df = pd.read_excel(open(DEFAULT_URLS_AUTHORS,'rb'), sheet_name = 0)

df_long = (
    df.assign(dataset_num=df["dataset_num"].str.split(","))
      .explode("dataset_num")
)
# TODO add rows having only 1 dataset_num (not in the list) to df_long

print(df_long)

# big_table = pd.concat([df_long, urls_data])

big_table = pd.merge(df_long, urls_data, on="dataset_num", how="left")

big_table = big_table.drop(["orcid", "id", "bibreference_num", "is_reference_data", "dataset_name", "description_txt", "description", "affiliation"], axis=1)
big_table = big_table[big_table.dataset_num.notnull()]

print(big_table.head(30))

big_table.to_excel(FOLDER_PATH + "authors_by_datasets_OUT.xlsx", index=False)

# %%

# print(sorted(int(x) for x in big_table['dataset_num'].unique()))

# %%
