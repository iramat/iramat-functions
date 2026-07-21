# to dump from the CHIPS API into Zenodo

#%% 
import json
import re
import requests
import pandas as pd

# a dataset number to test the code
API_URL = "https://iramat-apps.cnrs.fr/api/dataset_gpages22"
a_dataset = 4

urls_data = pd.read_csv("https://raw.githubusercontent.com/iramat/chips/refs/heads/hugo-files/static/data/urls_data.tsv", sep="\t")

#%% METADATA dataset creaors

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


response = requests.get(API_URL, timeout=30)
response.raise_for_status()
data = response.json()
if not data:
    raise ValueError("The API returned no records.")

# First API record (METADATA only, metadata are the same for all records)
first_record_METADATA = data[0]
# Retrieve its reference field
reference = first_record_METADATA.get("reference")
if not reference:
    raise ValueError("The first record has no usable 'reference' field.")

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

nam_dataset=urls_data.loc[a_dataset, "dataset_name"]
# dataset_name = urls_data.get("dataset_name")
nam_dataset = re.sub(r"dataset_", "", nam_dataset)
dataset_title=f"CHIPS dataset: {nam_dataset} (num. {num_dataset})"
print(f"Dataset title: {dataset_title}")

# %% METADATA dataset description (abstract)

dataset_description=urls_data.loc[a_dataset, "description_txt"]
print(f"Dataset description: {dataset_description}")

# %% METADATA dataset publication URL
publication_url = first_record_METADATA.get("url")

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
          'subjects': [{"term": "Archaeometry", "identifier": "http://id.loc.gov/authorities/subjects/sh85006517", "scheme": "url"},
                       {"term": "laboratory methods", "identifier": "https://apps.usgs.gov/thesaurus/term-simple.php?thcode=2&code=619", "scheme": "url"},
                       {"term": "chemical elements", "identifier": "https://apps.usgs.gov/thesaurus/term-simple.php?thcode=2&code=1427", "scheme": "url"}],
          'method': 'IRAMAT data entry methodology',
          'creators': creators_dataset,
          "related_identifiers": [{"identifier": publication_url,
				"relation": "isSupplementTo",
				"resource_type": "publication-article"
			}]
        #   'keywords': meta_data[0]['keywords'],
        #   'dates': [{"start": meta_data[0]['year'], "end": meta_data[0]['year'], "type": "Collected", "description": "Lorem Ipsum dates"}],
      }
  }
  return(metadata)

metadata = zn_metadata()
print(json.dumps(metadata, indent=2, ensure_ascii=False))

# %% DATA create the data file to be pushed on Zenodo

data[0]

# %%
