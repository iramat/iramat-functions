# to dump from the CHIPS API into Zenodo

#%% Initiate
import json
import re
import requests
import pandas as pd

# a simple flag for dev purpose
flag="_dev_1"
# a dataset number to test the code
a_dataset = 4

ZENODO_URL = "https://sandbox.zenodo.org/api/deposit/depositions"
json_bytes = json.load(open('C:\\Users\\TH282424\\Rprojects\\iramat-dev\\credentials\\zn_sandbox_credentials.json')) 
ACCESS_TOKEN = json_bytes["token"]

# METADATA dataset API URL
urls_data = pd.read_csv("https://raw.githubusercontent.com/iramat/chips/refs/heads/hugo-files/static/data/urls_data.tsv", sep="\t")
API_URL = urls_data.loc[a_dataset, "url_data"]
DATASET_NAME = urls_data.loc[a_dataset, "dataset_name"]
# DATA dataset API URL
response = requests.get(API_URL, timeout=30)
response.raise_for_status()
data = response.json()
if not data:
    raise ValueError("The API returned no records.")
# DATA dataset
# type(data[0])
df = pd.DataFrame.from_dict(data)
# df.head()
# df.columns


#%% METADATA dataset creators

# First API record (METADATA only, metadata are the same for all records)
first_record_METADATA = data[0]
# Retrieve its reference field
reference = first_record_METADATA.get("reference")
if not reference:
    raise ValueError("The first record has no usable 'reference' field.")

def extract_author_part(reference: str) -> str:
    """
    Return the part of the reference preceding the publication year.

    Expected form:
        Given Family, Given Family (2022), Article title, ...
    """
    match = re.match(r"^(.*?)\s*\(\d{4}\)", reference)
    if not match:
        raise ValueError(
            "Could not identify an author list followed by a year "
            f"in this reference: {reference!r}"
        )
    return match.group(1).strip().rstrip(",")


def split_person_name(full_name: str) -> tuple[str, str]:
    """
    Split 'Given names Family name' into:
        (family_name, given_names)

    This assumes that the final word is the family name.
    """
    parts = full_name.strip().split()
    if len(parts) < 2:
        raise ValueError(f"Cannot split author name: {full_name!r}")
    given_names = " ".join(parts[:-1])
    family_name = parts[-1]
    return family_name, given_names

# Keep only the author section
author_part = extract_author_part(reference)

# Authors are separated by commas
author_names = [
    name.strip()
    for name in author_part.split(",")
    if name.strip()
]

creators_dataset = []

for full_name in author_names:
    family_name, given_names = split_person_name(full_name)

    creators_dataset.append({
        "name": f"{family_name}, {given_names}"
    })

print("Zenodo creators:")
print(json.dumps(creators_dataset, indent=2, ensure_ascii=False))

# %% METADATA dataset number

num_dataset=urls_data.loc[a_dataset, "dataset_num"]
# dataset_num = urls_data.get("dataset_num")
num_dataset = re.sub(r"j\.id_dataset = ", "", num_dataset)
print(f"Dataset number: {num_dataset}")

# %% METADATA dataset name (title)

name_dataset=urls_data.loc[a_dataset, "dataset_name"]
# dataset_name = urls_data.get("dataset_name")
name_dataset = name_dataset+flag
name_dataset = re.sub(r"dataset_", "", name_dataset)
dataset_title=f"CHIPS dataset {num_dataset} ({name_dataset})"
print(f"Dataset title: {dataset_title}")

# %% METADATA dataset publication URL
publication_url = first_record_METADATA.get("url")

# %% METADATA dataset description (dashborad dataset URL)

dataset_dashboard_url = f"https://iramat-apps.cnrs.fr/dash/mapview?dataset={DATASET_NAME}"

# %% METADATA dataset description (abstract)

dataset_description=urls_data.loc[a_dataset, "description_txt"]
dataset_description = f"""

<p>{dataset_description}</p>

<h2>Source</h2>

The dataset <code>{DATASET_NAME}</code> (CHIPS dataset n. {num_dataset}) was first published in: 

<ul>
<li>{reference}, <a href="{publication_url}" target="_blank">{publication_url}</a>.</li>
</ul>
  
It was added to the CHIPS database following the <a href="https://iramat.github.io/chips/docs/#data-entry" target="_blank">CHIPS data entry method</a>.  
  
<h2>Reusability</h2>

The dataset <code>{DATASET_NAME}</code> (CHIPS dataset n. {num_dataset}) is made interoperable on the IRAMAT webserver (https://iramat-apps.cnrs.fr):

<ul>
<li>on the CHIPS API <a href="{API_URL}" target="_blank">{API_URL}</a></li>
<li>on the CHIPS dashboard <a href="{dataset_dashboard_url}" target="_blank">{dataset_dashboard_url}</a></li>
</ul>
"""

# print(f"Dataset description: {dataset_description}")


# %% METADATA dataset invariant keywords list

keywords = [
    "archaeometallurgy",
    "iron archaeometallurgy",
    "archaeomaterials",
    "geochemistry",
    "chemical analysis",
    "elemental composition",
    "analytical metadata",
    "measurement uncertainty",
    "FAIR data",
    "Linked Open Data"
]

# %% METADATA dataset calculated keywords list

# Columns to inspect
method_columns = ["trace_method", "major_method"]

# Extract unique methods
methods = (
    df[method_columns]
    .stack()                # Merge both columns into one Series
    .dropna()               # Remove NaN
    .astype(str)
    .str.strip()            # Remove surrounding spaces
    .unique()               # Keep unique values
    .tolist()
)

# %% METADATA dataset invariant + calculated keywords list

# Add them to the keywords
keywords.extend(methods)

# Remove duplicates while preserving order
keywords = list(dict.fromkeys(keywords))

print(keywords)

# typology, trace_method, major_method

# %% METADATA dataset create JSON object to be pushed on Zenodo

def zn_metadata(verbose = True):
  """
  Fill a metadata template to be pushed on Zenodo from a bibtex reference stored in Postgres (table '_refbib'). This function is called after `db_refbib()`

  :param meta_data: a JSON object
  """
  
  metadata = {
      'metadata': {
          'title': dataset_title,
          'description': dataset_description,
          'upload_type': 'dataset',
          'license': 'cc-by',
        #   'subjects': [
        #                {"term": "Archaeology", "identifier": "http://data.europa.eu/bkc/005.05.01.0050", "scheme": "url"},
        #                {"term": "Archaeometry", "identifier": "http://data.europa.eu/8mn/euroscivoc/0b7ef923-ea48-47bd-a5f1-2c5b18f53d20", "scheme": "url"},
        #                {"term": "Materials science", "identifier": "http://data.europa.eu/bkc/018.01.00.0950", "scheme": "url"},
        #                {"term": "Science and technology studies", "identifier": "http://data.europa.eu/8mn/euroscivoc/c86017cb-7116-4ef6-8961-2ca63e96a048", "scheme": "url"},
        #                {"term": "Metals", "identifier": "https://id.nlm.nih.gov/mesh/D008670.html", "scheme": "url"},
        #                {"term": "Iron", "identifier": "https://id.nlm.nih.gov/mesh/D007501.html", "scheme": "url"},
        #                {"term": "Spectroscopy", "identifier": "https://id.nlm.nih.gov/mesh/D013057.html", "scheme": "url"}
        #                ],
            'subjects': [
                        # Archaeology
                        {
                            "term": "Archaeology",
                            "identifier": "http://data.europa.eu/bkc/005.05.01.0050"
                        },

                        # Archaeometry
                        {
                            "term": "Archaeometry",
                            "identifier": "http://data.europa.eu/8mn/euroscivoc/0b7ef923-ea48-47bd-a5f1-2c5b18f53d20"
                        },

                        # Materials science
                        {
                            "term": "Materials science",
                            "identifier": "http://data.europa.eu/bkc/018.01.00.0950"
                        },

                        # Analytical chemistry
                        {
                            "term": "Analytical chemistry",
                            "identifier": "http://data.europa.eu/8mn/euroscivoc/dc1b3723-476f-453c-a596-c7ccfde9b4b1"
                        },

                        # MeSH
                        {
                            "term": "Metals",
                            "identifier": "https://id.nlm.nih.gov/mesh/D008670"
                        },
                        {
                            "term": "Iron",
                            "identifier": "https://id.nlm.nih.gov/mesh/D007501"
                        },
                        {
                            "term": "Spectroscopy",
                            "identifier": "https://id.nlm.nih.gov/mesh/D013057"
                        }
                ],
        #   'method': 'IRAMAT data entry methodology',
        # 'method':'<a href="https://iramat.github.io/chips/docs/#data-entry" target="_blank">CHIPS data entry method</a>',
          'creators': creators_dataset,
          "related_identifiers": [{"identifier": publication_url,
				"relation": "isSupplementTo",
				"resource_type": "publication-article"
			}],
          # on test
        #   'communities': [{'id': 'iramat'}],
          'keywords': keywords,
        #   'dates': [{"start": meta_data[0]['year'], "end": meta_data[0]['year'], "type": "Collected", "description": "Lorem Ipsum dates"}],
      }
  }
  return(metadata)

metadata = zn_metadata()
print(json.dumps(metadata, indent=2, ensure_ascii=False))


# %% DATA create the data file to be pushed on Zenodo

df.drop(["reference", "url"], axis=1)

# %%

# the filename that will be used to push the data on Zenodo
name_file = f"{name_dataset}_chips{num_dataset}.csv"

# %%
name_file

# %%
# @title Créer le 'Bucket'

params = {'access_token': ACCESS_TOKEN}
r = requests.post(ZENODO_URL,
                   params=params,
                   json={})
print(r.status_code)
# collect the deposition id
deposition_id = r.json()['id']
print("The deposition_id is: " + str(deposition_id))

# %%
import io

csv_buffer = io.BytesIO()
df.to_csv(csv_buffer, index=False)
csv_buffer.seek(0)

files = {
    'file': ('data.csv', csv_buffer, 'text/csv')
}

# %%
# @title Ajoute les données

deposition_id = r.json()['id']
data = {'name': name_file}
# files = {'file': open(csv_file_path, 'rb')}
r = requests.post('https://sandbox.zenodo.org/api/deposit/depositions/%s/files' % deposition_id,
                   params={'access_token': ACCESS_TOKEN},
                  data=data,
                   files=files)
r.status_code
# 201
r.json()

# %%
# @title Ajoute les métadonnées

r = requests.put('%s/%s' % (ZENODO_URL, deposition_id),
                  params = {'access_token': ACCESS_TOKEN},
                  data = json.dumps(metadata)) # ,
                  # headers = headers)
r.status_code
# 200
# %%
# @title Publier
r = requests.post('%s/%s/actions/publish' % (ZENODO_URL, deposition_id),
                      params={'access_token': ACCESS_TOKEN} )
r.status_code
# 504


# %%
# @title Vérifier

r = requests.get(ZENODO_URL,
                  params={'access_token': ACCESS_TOKEN})
r.status_code
# 200
r.json()[0]['links']['html']

# # %% GET the record from Zenodo API to check the metadata

# # https://zenodo.org/records/....
# record_id = 13899578
# url = f"https://zenodo.org/api/records/{record_id}"

# r = requests.get(url)
# r.raise_for_status()

# metadata = r.json()

# field = "subjects"
# # print(metadata["metadata"])
# metadata
# # %%

# %%
